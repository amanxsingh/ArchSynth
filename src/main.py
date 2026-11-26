"""
ArchSynth Main Pipeline Orchestrator - Single entry point for end-to-end execution.
Executes Stage 1 (Ingestion) -> Stage 2 (Node Analysis) -> Stage 3 (Launch Analysis)
-> Stage 4 (Architecture Synthesis) -> Stage 5 (Documentation Generation).

Research Extensions (M.Tech Dissertation):
    --validate-evidence  Run evidence validation after architecture synthesis
    --eval-gt            Evaluate against ground truth directory
    --drift-report       Enable drift detection mode (requires --base-commit / --target-commit)
    --base-commit        Base Git commit for drift detection
    --target-commit      Target Git commit for drift detection
    --ablation           Run ablation study

All new flags are optional. Existing --repo / --output behavior is unchanged.
"""

import argparse
import json
import logging
import time
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.schema import PipelineConfig, AnalysisResult
from src.ingestor import Ingestor
from src.node_analyzer import run_node_analysis
from src.launch_analyzer import run_launch_analysis
from src.architecture_constructor import run_architecture_constructor, ArchitectureConstructor
from src.doc_generator import run_doc_generator, DocGenerator
from src.repo_identity import (
    resolve_repository_identity,
    verify_repository_identity,
    RepositoryMismatchError,
    RepositoryIdentity,
    attach_artifact_provenance,
    validate_artifact_provenance,
    load_validated_json,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ArchSynth")


class ArchSynthPipeline:
    """
    Orchestrates the full end-to-end ArchSynth analysis pipeline.
    """

    def __init__(self, config: PipelineConfig, expected_repo: Optional[str] = None):
        self.config = config
        repo_path = Path(config.repo_path).resolve()
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

        # Resolve repository identity & Git provenance
        self.repo_identity = resolve_repository_identity(repo_path, expected_name=expected_repo)

        # Output directory: if left default or unspecified, isolate by repository name
        if not config.output_dir or config.output_dir in ("output", "output/nav2_pipeline", "output/default"):
            self.output_dir = Path("output") / f"{self.repo_identity.repo_name.lower()}_pipeline"
        else:
            self.output_dir = Path(config.output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._enforce_output_directory_isolation()
        self._start_time = time.time()

    def _enforce_output_directory_isolation(self) -> None:
        """
        Validate all existing JSON artifacts in the output directory.
        Any artifact with missing or mismatched repository provenance is rejected and purged.
        """
        if not self.output_dir.exists():
            return

        for json_file in list(self.output_dir.glob("*.json")):
            if json_file.name.endswith(".provenance.json"):
                continue
            # Validate provenance against current repo_identity, purging stale or foreign files
            validate_artifact_provenance(json_file, self.repo_identity, purge_invalid=True)

    def run(self) -> Path:
        """
        Execute all pipeline stages sequentially.
        """
        logger.info("=== Starting ArchSynth Pipeline ===")
        repo_path = Path(self.config.repo_path)

        # Stage 1: Repo Ingestion / Path verification
        logger.info(f"[Stage 1/5] Ingesting repository at: {repo_path}")
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

        # Stage 2: Node Analysis
        logger.info("[Stage 2/5] Running NodeAnalyzer (Stage 2)...")
        nodes_json = self.output_dir / "nodes.json"
        nodes = run_node_analysis(repo_path, nodes_json)
        attach_artifact_provenance(nodes_json, self.repo_identity)
        logger.info(f"Stage 2 Complete: Discovered {len(nodes)} nodes.")

        # Stage 3: Launch File Analysis (Phase 2)
        logger.info("[Stage 3/5] Running LaunchFileAnalyzer (Stage 3)...")
        from src.launch_analyzer import run_phase2_launch_pipeline
        launches, instances, mappings, profiles = run_phase2_launch_pipeline(
            repo_path=repo_path,
            nodes_json_path=nodes_json,
            output_dir=self.output_dir
        )
        launches_json = self.output_dir / "launches.json"
        attach_artifact_provenance(launches_json, self.repo_identity)
        attach_artifact_provenance(self.output_dir / "launch_instances.json", self.repo_identity)
        attach_artifact_provenance(self.output_dir / "node_launch_mapping.json", self.repo_identity)
        attach_artifact_provenance(self.output_dir / "deployment_profiles.json", self.repo_identity)
        logger.info(
            f"Stage 3 Complete: Parsed {len(launches)} launch files, "
            f"resolved {len(instances)} instances across {len(profiles)} deployment profiles."
        )

        # Stage 3.5: ROS2 Interface Extraction & Communication Graph Recovery (Phase 3)
        logger.info("[Phase 3] Running ROS2 Interface Extraction & Communication Graph Recovery...")
        from src.communication_builder import run_phase3_communication_pipeline
        launch_instances_json = self.output_dir / "launch_instances.json"
        declarations, runtime_interfaces, comm_graph, comm_matrix = run_phase3_communication_pipeline(
            repo_path=repo_path,
            nodes_json_path=nodes_json,
            launch_instances_json_path=launch_instances_json,
            output_dir=self.output_dir
        )
        attach_artifact_provenance(self.output_dir / "interfaces.json", self.repo_identity)
        attach_artifact_provenance(self.output_dir / "runtime_interfaces.json", self.repo_identity)
        attach_artifact_provenance(self.output_dir / "communication_graph.json", self.repo_identity)
        attach_artifact_provenance(self.output_dir / "communication_matrix.json", self.repo_identity)
        logger.info(
            f"Phase 3 Complete: {len(declarations)} interfaces, {len(runtime_interfaces)} runtime instances, "
            f"{len(comm_graph.source_potential_edges)} potential edges, {len(comm_graph.deployment_runtime_edges)} runtime edges."
        )

        # Stage 4: Architecture Synthesis & Recovery (Phase 4)
        logger.info("[Phase 4.1] Running Subsystem Recovery...")
        from src.subsystem_synthesizer import run_subsystem_recovery
        sub_model = run_subsystem_recovery(
            nodes_json_path=nodes_json,
            communication_graph_path=self.output_dir / "communication_graph.json",
            launches_json_path=launches_json,
            output_path=self.output_dir / "subsystem_model.json"
        )
        attach_artifact_provenance(self.output_dir / "subsystem_model.json", self.repo_identity)

        logger.info("[Phase 4.2] Running Lifecycle Architecture Recovery...")
        from src.lifecycle_analyzer import run_lifecycle_analysis
        life_model = run_lifecycle_analysis(
            repo_root=repo_path,
            nodes_json_path=nodes_json,
            output_path=self.output_dir / "lifecycle_graph.json"
        )
        attach_artifact_provenance(self.output_dir / "lifecycle_graph.json", self.repo_identity)

        logger.info("[Phase 4.3] Running Plugin Architecture Recovery...")
        from src.plugin_analyzer import run_plugin_analysis
        plug_model = run_plugin_analysis(
            repo_root=repo_path,
            output_path=self.output_dir / "plugin_architecture.json"
        )
        if self.repo_identity.repo_name.lower() not in ("nav2", "navigation2"):
            if "nav2_core_GlobalPlanner" in (plug_model.mermaid_diagram or ""):
                plug_clean_lines = ["classDiagram", "    direction TB"]
                known_bases = set()
                for p in plug_model.plugins:
                    base_cls = p.base_class_type if p.base_class_type else "PluginInterface"
                    base_id = base_cls.replace("::", "_").replace("<", "_").replace(">", "_")
                    if base_id not in known_bases:
                        plug_clean_lines.append(f"    class {base_id} {{\n        <<interface>>\n    }}")
                        known_bases.add(base_id)
                    p_id = p.class_type.replace("::", "_").replace("<", "_").replace(">", "_")
                    plug_clean_lines.append(f"    class {p_id} {{\n        package: {p.package_name}\n    }}")
                    plug_clean_lines.append(f"    {base_id} <|-- {p_id}")
                plug_model.mermaid_diagram = "\n".join(plug_clean_lines) if len(plug_clean_lines) > 2 else ""
                with open(self.output_dir / "plugin_architecture.json", "w", encoding="utf-8") as f:
                    json.dump(plug_model.model_dump(), f, indent=2)
        attach_artifact_provenance(self.output_dir / "plugin_architecture.json", self.repo_identity)

        logger.info("[Phase 4.4] Running Behavior Tree Recovery...")
        from src.bt_analyzer import run_behavior_tree_analysis
        bt_model = run_behavior_tree_analysis(
            repo_root=repo_path,
            output_path=self.output_dir / "behavior_tree_model.json"
        )
        if bt_model.total_trees == 0:
            bt_json_file = self.output_dir / "behavior_tree_model.json"
            if bt_json_file.exists():
                bt_json_file.unlink()
            bt_prov_file = self.output_dir / "behavior_tree_model.json.provenance.json"
            if bt_prov_file.exists():
                bt_prov_file.unlink()
        else:
            attach_artifact_provenance(self.output_dir / "behavior_tree_model.json", self.repo_identity)

        logger.info("[Phase 4.45] Building Package Dependency Graph...")
        from src.build_analyzer import build_package_dependency_graph
        pkg_dep_graph = build_package_dependency_graph(repo_path)
        with open(self.output_dir / "package_dependency_graph.json", "w", encoding="utf-8") as f:
            json.dump(pkg_dep_graph.model_dump(), f, indent=2)
        attach_artifact_provenance(self.output_dir / "package_dependency_graph.json", self.repo_identity)

        logger.info("[Phase 4.5] Generating ISO/IEC/IEEE 42010 Architecture Views...")
        from src.view_generator import run_views_generation
        views_model = run_views_generation(
            nodes_json_path=nodes_json,
            subsystem_json_path=self.output_dir / "subsystem_model.json",
            lifecycle_json_path=self.output_dir / "lifecycle_graph.json",
            plugin_json_path=self.output_dir / "plugin_architecture.json",
            bt_json_path=self.output_dir / "behavior_tree_model.json",
            comm_graph_json_path=self.output_dir / "communication_graph.json",
            output_path=self.output_dir / "architecture_views.json",
            repo_name=self.repo_identity.repo_name,
            package_dependency_graph=pkg_dep_graph,
            launches_json_path=launches_json,
        )
        attach_artifact_provenance(self.output_dir / "architecture_views.json", self.repo_identity)

        # Stage 4 Consolidation: System Architecture Construction
        logger.info("[Stage 4/5] Running SystemArchitectureConstructor (Stage 4)...")
        arch_json = self.output_dir / "architecture.json"
        arch_model = run_architecture_constructor(
            nodes_json_path=nodes_json,
            launches_json_path=launches_json,
            output_path=arch_json,
            repo_name=self.repo_identity.repo_name,
            repo_url=self.repo_identity.remote_url,
            commit_hash=self.repo_identity.commit_sha,
            branch=self.repo_identity.branch,
            archsynth_version="2.0",
            package_dependency_graph=pkg_dep_graph,
        )
        logger.info(
            f"Stage 4 Complete: Synthesized {len(arch_model.subsystems)} subsystems, "
            f"{len(arch_model.architecture_views.views if arch_model.architecture_views else [])} architecture views."
        )

        # Research Extension: Evidence Validation (optional)
        if self.config.validate_evidence:
            logger.info("[Research] Running Evidence Validation...")
            from src.evidence_validator import run_evidence_validation
            validation_json = self.output_dir / "validation_report.json"
            arch_model, report = run_evidence_validation(
                arch_model,
                repo_root=repo_path,
                output_path=validation_json
            )
            # Save updated model with validation_report
            with open(arch_json, "w", encoding="utf-8") as f:
                json.dump(arch_model.model_dump(), f, indent=2)
            logger.info(
                f"Evidence Validation Complete: "
                f"coverage={report.evidence_coverage:.1%}, "
                f"unsupported={report.unsupported_entities}"
            )

        # Research Extension: Experiment Metadata Recording
        elapsed = time.time() - self._start_time
        arch_model.experiment_metadata = self._build_experiment_metadata(
            repo_path=repo_path,
            nodes_count=len(nodes),
            launches_count=len(launches),
            elapsed=elapsed
        )
        # Re-save with metadata
        with open(arch_json, "w", encoding="utf-8") as f:
            json.dump(arch_model.model_dump(), f, indent=2)
        attach_artifact_provenance(arch_json, self.repo_identity)

        # Research Extension: Evaluate against ground truth (optional)
        if self.config.ground_truth_dir:
            self._run_evaluation(arch_model, arch_json)

        # Stage 5: Documentation Generation
        logger.info("[Stage 5/5] Running DocGenerator (Stage 5)...")
        docs_dir = self.output_dir / "docs"
        main_readme = run_doc_generator(arch_json, docs_dir)
        logger.info(f"Stage 5 Complete: Documentation generated at {main_readme}")

        logger.info("=== ArchSynth Pipeline Successfully Completed ===")
        return main_readme

    def _build_experiment_metadata(
        self,
        repo_path: Path,
        nodes_count: int,
        launches_count: int,
        elapsed: float
    ) -> dict:
        """
        Build reproducibility metadata for the experiment record.
        Research requirement: every experiment must be reproducible.
        """
        return {
            "repository": str(repo_path),
            "repository_name": self.repo_identity.repo_name,
            "repository_url": self.repo_identity.remote_url,
            "branch": self.repo_identity.branch,
            "commit_hash": self.repo_identity.commit_sha,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "llm_provider": self.config.primary_llm,
            "llm_model": (
                self.config.gemini_model
                if self.config.primary_llm == "gemini"
                else self.config.ollama_model
            ),
            "temperature": 0.1,
            "nodes_analyzed": nodes_count,
            "launch_files_analyzed": launches_count,
            "processing_time_seconds": round(elapsed, 2),
            "validate_evidence": self.config.validate_evidence,
            "pipeline_version": "ArchSynth-2.0-research",
        }

    def _run_evaluation(self, arch_model, arch_json: Path) -> None:
        """Run evaluation against ground truth if provided."""
        try:
            from eval.metrics import evaluate_full_architecture

            gt_dir = Path(self.config.ground_truth_dir)
            gt: dict = {}
            for key in ["nodes", "topics", "services", "actions", "subsystems"]:
                f = gt_dir / f"{key}.json"
                if f.exists():
                    with open(f, encoding="utf-8") as fh:
                        gt[key] = json.load(fh)

            if gt:
                result = evaluate_full_architecture(arch_model.model_dump(), gt)
                eval_json = self.output_dir / "evaluation_results.json"
                eval_json.write_text(json.dumps(result, indent=2))
                logger.info(
                    f"Evaluation complete: "
                    f"Node F1={result['nodes']['f1']:.3f}, "
                    f"Topic F1={result['topics']['f1']:.3f}, "
                    f"Evidence Coverage={result['evidence']['evidence_coverage']:.1%}"
                )
        except Exception as e:
            logger.warning(f"Ground truth evaluation skipped: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="ArchSynth: Automated ROS2 Architecture Recovery & Documentation Tool"
    )

    # ---- Core arguments (unchanged) ----
    parser.add_argument(
        "--repo",
        type=str,
        default="case_studies/nav2",
        help="Path to target ROS2 repository directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Directory to save pipeline artifacts and generated docs (default: output/<repo_name>_pipeline)"
    )
    parser.add_argument(
        "--expected-repo",
        type=str,
        default=None,
        help="Expected repository name to verify against repository identity"
    )
    parser.add_argument(
        "--primary-llm",
        type=str,
        choices=["gemini", "ollama"],
        default="gemini",
        help="Primary LLM provider (default: gemini)"
    )

    # ---- Research extension arguments (all optional) ----
    parser.add_argument(
        "--validate-evidence",
        action="store_true",
        help="[Research] Run evidence validation after architecture synthesis"
    )
    parser.add_argument(
        "--eval-gt",
        type=str,
        default=None,
        metavar="GT_DIR",
        help="[Research] Path to ground truth directory for evaluation metrics"
    )
    parser.add_argument(
        "--drift-report",
        action="store_true",
        help="[Research] Enable drift detection mode (use with --base-commit / --target-commit)"
    )
    parser.add_argument(
        "--base-commit",
        type=str,
        default=None,
        help="[Research] Base Git commit hash for drift detection"
    )
    parser.add_argument(
        "--target-commit",
        type=str,
        default=None,
        help="[Research] Target Git commit hash for drift detection"
    )
    parser.add_argument(
        "--ablation",
        action="store_true",
        help="[Research] Run ablation study (baselines A, C, E)"
    )

    args = parser.parse_args()

    # ---- Drift detection mode ----
    if args.drift_report:
        logger.info("=== ArchSynth Drift Detection Mode ===")
        from src.drift_pipeline import run_drift_pipeline
        report = run_drift_pipeline(
            repo_path=Path(args.repo),
            base_commit=args.base_commit,
            target_commit=args.target_commit,
            output_dir=Path(args.output) / "drift"
        )
        print(f"\n{report.summary}")
        print(f"\n[SUCCESS] Drift report complete: {report.total_changes} changes detected")
        return

    # ---- Ablation study mode ----
    if args.ablation:
        logger.info("=== ArchSynth Ablation Study Mode ===")
        from eval.ablation import run_ablation_study
        results = run_ablation_study(
            repo_path=Path(args.repo),
            ground_truth_dir=Path(args.eval_gt) if args.eval_gt else None,
            output_dir=Path(args.output) / "ablation"
        )
        print(f"\n[SUCCESS] Ablation study complete.")
        return

    # ---- Standard pipeline mode ----
    config = PipelineConfig(
        repo_path=args.repo,
        output_dir=args.output or "",
        primary_llm=args.primary_llm,
        validate_evidence=args.validate_evidence,
        ground_truth_dir=args.eval_gt,
        base_commit=args.base_commit,
        target_commit=args.target_commit,
        drift_report=args.drift_report,
    )

    pipeline = ArchSynthPipeline(config, expected_repo=args.expected_repo)
    output_readme = pipeline.run()

    print(f"\n[SUCCESS] Pipeline Finished Successfully!")
    print(f"Output README: {output_readme.absolute()}")


if __name__ == "__main__":
    main()
