"""
ArchSynth DriftPipeline - Commit-to-Commit Architecture Drift Orchestration

Orchestrates two ArchSynth pipeline runs (one per commit) and produces
a DriftReport comparing the recovered architectures.

Usage:
    python -m src.drift_pipeline \\
        --repo case_studies/nav2 \\
        --base-commit <hash_A> \\
        --target-commit <hash_B> \\
        --output output/drift_nav2

Or programmatically:
    from src.drift_pipeline import run_drift_pipeline
    report = run_drift_pipeline(repo_path, "commitA", "commitB", output_dir)
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Optional

from src.schema import ArchitectureModel, DriftReport, PipelineConfig

logger = logging.getLogger(__name__)


def _checkout_commit(repo_path: Path, commit_hash: str) -> bool:
    """
    Attempt to checkout a specific commit in the repository.
    Returns True if successful, False otherwise.
    """
    try:
        import git
        repo = git.Repo(str(repo_path))
        repo.git.checkout(commit_hash)
        logger.info(f"Checked out commit: {commit_hash}")
        return True
    except Exception as e:
        logger.warning(f"Could not checkout commit {commit_hash}: {e}")
        return False


def _restore_head(repo_path: Path) -> None:
    """Restore repository to HEAD after commit checkout."""
    try:
        import git
        repo = git.Repo(str(repo_path))
        repo.git.checkout("HEAD")
    except Exception as e:
        logger.warning(f"Could not restore HEAD: {e}")


def run_single_pipeline(
    repo_path: Path,
    output_dir: Path,
    commit_label: str = "current"
) -> ArchitectureModel:
    """
    Run the full ArchSynth pipeline on the current state of the repository.

    Args:
        repo_path: Repository root
        output_dir: Where to write pipeline outputs
        commit_label: Label for this run (used in metadata)

    Returns:
        ArchitectureModel
    """
    from src.node_analyzer import run_node_analysis
    from src.launch_analyzer import run_launch_analysis
    from src.architecture_constructor import run_architecture_constructor

    output_dir.mkdir(parents=True, exist_ok=True)

    nodes_json = output_dir / "nodes.json"
    launches_json = output_dir / "launches.json"
    arch_json = output_dir / "architecture.json"

    run_node_analysis(repo_path, nodes_json)
    run_launch_analysis(repo_path, launches_json)

    # Try to get actual commit hash
    commit_hash = commit_label
    try:
        import git
        git_repo = git.Repo(str(repo_path))
        commit_hash = git_repo.head.commit.hexsha[:12]
    except Exception:
        pass

    arch = run_architecture_constructor(
        nodes_json_path=nodes_json,
        launches_json_path=launches_json,
        output_path=arch_json,
        repo_name=repo_path.name
    )

    # Update commit hash in model
    arch.commit_hash = commit_hash
    with open(arch_json, "w", encoding="utf-8") as f:
        json.dump(arch.model_dump(), f, indent=2)

    return arch


def run_drift_pipeline(
    repo_path: Path,
    base_commit: Optional[str],
    target_commit: Optional[str],
    output_dir: Path,
    cleanup_checkouts: bool = True
) -> DriftReport:
    """
    Run commit-to-commit architecture drift detection.

    Strategy:
        1. If base_commit given: checkout base → run pipeline → save arch A
        2. If target_commit given: checkout target → run pipeline → save arch B
        3. If neither: compare existing arch A vs B from output_dir

    Args:
        repo_path: Path to the ROS2 repository
        base_commit: Git commit hash for base architecture
        target_commit: Git commit hash for target architecture
        output_dir: Directory for outputs
        cleanup_checkouts: Whether to restore HEAD after analysis

    Returns:
        DriftReport
    """
    from src.architecture_diff import diff_architectures

    output_dir.mkdir(parents=True, exist_ok=True)
    arch_a_dir = output_dir / "base"
    arch_b_dir = output_dir / "target"
    drift_json = output_dir / "drift_report.json"

    # Run base pipeline
    arch_a_json = arch_a_dir / "architecture.json"
    if not arch_a_json.exists() or base_commit:
        logger.info(f"Running base pipeline (commit: {base_commit or 'current'})")
        if base_commit:
            _checkout_commit(repo_path, base_commit)
        try:
            run_single_pipeline(repo_path, arch_a_dir, commit_label=base_commit or "base")
        finally:
            if base_commit and cleanup_checkouts:
                _restore_head(repo_path)

    # Run target pipeline
    arch_b_json = arch_b_dir / "architecture.json"
    if not arch_b_json.exists() or target_commit:
        logger.info(f"Running target pipeline (commit: {target_commit or 'current'})")
        if target_commit:
            _checkout_commit(repo_path, target_commit)
        try:
            run_single_pipeline(repo_path, arch_b_dir, commit_label=target_commit or "target")
        finally:
            if target_commit and cleanup_checkouts:
                _restore_head(repo_path)

    # Compute diff
    if not arch_a_json.exists():
        raise FileNotFoundError(f"Base architecture not found: {arch_a_json}")
    if not arch_b_json.exists():
        raise FileNotFoundError(f"Target architecture not found: {arch_b_json}")

    report = diff_architectures(arch_a_json, arch_b_json, output_path=drift_json)
    logger.info(f"Drift pipeline complete: {report.total_changes} changes, report at {drift_json}")

    return report


if __name__ == "__main__":
    import argparse
    import sys
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="ArchSynth Drift Pipeline")
    parser.add_argument("--repo", required=True, help="Path to ROS2 repository")
    parser.add_argument("--base-commit", default=None, help="Base Git commit hash")
    parser.add_argument("--target-commit", default=None, help="Target Git commit hash")
    parser.add_argument("--output", default="output/drift", help="Output directory")
    args = parser.parse_args()

    report = run_drift_pipeline(
        repo_path=Path(args.repo),
        base_commit=args.base_commit,
        target_commit=args.target_commit,
        output_dir=Path(args.output)
    )

    print(f"\n{report.summary}")
    print(f"\nTotal Changes: {report.total_changes}")
    print(f"  Added nodes:    {len(report.added_nodes)}")
    print(f"  Removed nodes:  {len(report.removed_nodes)}")
    print(f"  Modified nodes: {len(report.modified_nodes)}")
    print(f"  Added topics:   {len(report.added_topics)}")
    print(f"  Removed topics: {len(report.removed_topics)}")
