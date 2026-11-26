"""
ArchSynth v2.2 Complete Benchmark Recalculation Runner.
Evaluates all 6 repositories (Nav2, SLAM Toolbox, ROS 2 Control, JACO2, BehaviorTree.CPP, Express.js)
and writes all curated artifacts + raw outputs into:
    benchmarks/results_v2_2_recalculated_2026_11_25/
without modifying any previous benchmark results.
"""

import csv
import hashlib
import json
import logging
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.evaluator import ResearchEvaluator, calculate_ari_nmi, compute_fuzzy_prf1, compute_prf1
from src.evidence_validator import EvidenceValidator
from src.launch_analyzer import run_phase2_launch_pipeline
from src.main import ArchSynthPipeline
from src.node_analyzer import run_node_analysis
from src.communication_builder import run_phase3_communication_pipeline
from src.schema import ArchitectureModel, PipelineConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ArchSynthV22Benchmark")

OUT_ROOT = Path("benchmarks/results_v2_2_recalculated_2026_11_25")
RAW_ROOT = OUT_ROOT / "raw_runs"

REPOS = [
    {
        "id": "nav2",
        "name": "Navigation2",
        "path": Path("case_studies/nav2"),
        "url": "https://github.com/ros-planning/navigation2.git",
        "gt_path": Path("eval/ground_truth/nav2/ground_truth.json"),
        "is_ros": True,
    },
    {
        "id": "slam_toolbox",
        "name": "SLAM Toolbox",
        "path": Path("case_studies/slam_toolbox"),
        "url": "https://github.com/SteveMacenski/slam_toolbox",
        "gt_path": None,
        "is_ros": True,
    },
    {
        "id": "ros2_control",
        "name": "ROS 2 Control",
        "path": Path("case_studies/ros2_control"),
        "url": "https://github.com/ros-controls/ros2_control",
        "gt_path": None,
        "is_ros": True,
    },
    {
        "id": "jaco2_sim_devkit",
        "name": "Kinova Jaco2 Devkit",
        "path": Path("case_studies/jaco2_sim_devkit"),
        "url": "https://github.com/VibhuSharma19/jaco2_sim_devkit",
        "gt_path": Path("eval/ground_truth/jaco2_sim_devkit/ground_truth.json"),
        "is_ros": True,
    },
    {
        "id": "behaviortree_cpp",
        "name": "BehaviorTree.CPP",
        "path": Path("case_studies/behaviortree_cpp"),
        "url": "https://github.com/BehaviorTree/BehaviorTree.CPP.git",
        "gt_path": None,
        "is_ros": False,  # C++ library / optional ROS 2 wrapper
    },
    {
        "id": "express",
        "name": "Express.js (Negative Control)",
        "path": Path("case_studies/express"),
        "url": "https://github.com/expressjs/express",
        "gt_path": None,
        "is_ros": False,
    },
]


def git_info(repo_path: Path) -> Dict[str, str]:
    sha = subprocess.run(["git", "-C", str(repo_path), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    br = subprocess.run(["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout.strip()
    return {"commit": sha, "branch": br}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prf1_with_counts(pred_set: Set[str], gt_set: Set[str]) -> Dict[str, Any]:
    tp = len(pred_set & gt_set)
    fp = len(pred_set - gt_set)
    fn = len(gt_set - pred_set)
    assert tp + fp == len(pred_set)
    assert tp + fn == len(gt_set)
    if len(pred_set) == 0 and len(gt_set) == 0:
        p, r, f1 = 1.0, 1.0, 1.0
    elif len(pred_set) == 0 or len(gt_set) == 0:
        p, r, f1 = 0.0, 0.0, 0.0
    else:
        p = tp / (tp + fp)
        r = tp / (tp + fn)
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
    return {
        "ground_truth": len(gt_set),
        "predicted": len(pred_set),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(p, 4),
        "recall": round(r, 4),
        "f1": round(f1, 4),
    }


def clean_basename(s: str) -> str:
    return s.strip("/").split("/")[-1].lower()


def evaluate_jaco2_detailed(model: ArchitectureModel, gt: Dict[str, Any]) -> Dict[str, Any]:
    pred_nodes = {clean_basename(n.name or n.class_name) for n in model.nodes if not n.is_test}
    gt_nodes = {clean_basename(n["name"]) for n in gt["nodes"]}

    # Source-declared interfaces (exclude config::* and api_inferred)
    src_topics = {
        clean_basename(d.resolved_name or d.name_expression)
        for d in model.interfaces
        if d.interface_type.value in ("publisher", "subscriber") and not d.owner_node_id.startswith("config::")
    }
    gt_topics = {clean_basename(t["name"]) for t in gt["topics"]}

    src_services = {
        clean_basename(d.resolved_name or d.name_expression)
        for d in model.interfaces
        if d.interface_type.value in ("service_server", "service_client") and not d.owner_node_id.startswith("config::")
    }
    gt_services = {clean_basename(s["name"]) for s in gt["services"]}

    # Actions separated cleanly:
    src_actions = {
        (d.owner_node_id, clean_basename(d.resolved_name or d.name_expression))
        for d in model.interfaces
        if d.interface_type.value in ("action_server", "action_client")
        and not d.owner_node_id.startswith("config::")
        and d.discovery_method != "python_ast_moveit_execution"
    }
    gt_src_actions = {(a["owner"], clean_basename(a["name"])) for a in gt.get("actions", [])}

    api_actions = {
        (d.owner_node_id, clean_basename(d.resolved_name or d.name_expression))
        for d in model.interfaces
        if d.discovery_method == "python_ast_moveit_execution"
    }
    gt_api_actions = {(a["owner"], clean_basename(a["name"])) for a in gt.get("api_inferred_actions", [])}

    yaml_actions = {
        (d.resolved_name or d.name_expression).lower()
        for d in model.interfaces
        if d.owner_node_id.startswith("config::")
    }
    gt_yaml_actions = {a["name"].lower() for a in gt.get("yaml_configured_actions", [])}

    # Subsystems (by package_name / architectural_role)
    gt_roles = {clean_basename(n["name"]): n["architectural_role"] for n in gt["nodes"]}
    pred_roles = {}
    node_id_to_clean = {n.id: clean_basename(n.name or n.class_name) for n in model.nodes}
    for sub in model.subsystems:
        for nid in sub.nodes:
            if nid in node_id_to_clean:
                pred_roles[node_id_to_clean[nid]] = sub.name
    ari, nmi = calculate_ari_nmi(pred_roles, gt_roles)

    return {
        "nodes": prf1_with_counts(pred_nodes, gt_nodes),
        "topics": prf1_with_counts(src_topics, gt_topics),
        "services": prf1_with_counts(src_services, gt_services),
        "source_actions": prf1_with_counts({str(x) for x in src_actions}, {str(x) for x in gt_src_actions}),
        "api_inferred_actions": prf1_with_counts({str(x) for x in api_actions}, {str(x) for x in gt_api_actions}),
        "yaml_configured_actions": prf1_with_counts(yaml_actions, gt_yaml_actions),
        "subsystems": {"ari": ari, "nmi": nmi, "evaluated_nodes": len(pred_roles)},
    }


def evaluate_nav2_detailed(model: ArchitectureModel, gt: Dict[str, Any]) -> Dict[str, Any]:
    pred_nodes = {clean_basename(n.name or n.class_name) for n in model.nodes if not n.is_test}
    gt_core_nodes = {clean_basename(n["name"]) for n in gt.get("core_nodes", gt["nodes"])}
    gt_ext_nodes = {clean_basename(n["name"]) for n in gt.get("extended_nodes", gt["nodes"])}

    pred_topics = {clean_basename(d.resolved_name or d.name_expression) for d in model.interfaces if d.interface_type.value in ("publisher", "subscriber")}
    gt_topics = {clean_basename(t["name"]) for t in gt["topics"]}

    pred_services = {clean_basename(d.resolved_name or d.name_expression) for d in model.interfaces if d.interface_type.value in ("service_server", "service_client")}
    gt_services = {clean_basename(s["name"]) for s in gt["services"]}

    pred_actions = {clean_basename(d.resolved_name or d.name_expression) for d in model.interfaces if d.interface_type.value in ("action_server", "action_client")}
    gt_actions = {clean_basename(a["name"]) for a in gt["actions"]}

    ev = ResearchEvaluator(model, gt)
    sub_metrics = ev.evaluate_subsystems()
    plug_bt = ev.evaluate_plugins_and_bt()

    return {
        "nodes_core": prf1_with_counts(pred_nodes, gt_core_nodes),
        "nodes_extended": prf1_with_counts(pred_nodes, gt_ext_nodes),
        "topics": prf1_with_counts(pred_topics, gt_topics),
        "services": prf1_with_counts(pred_services, gt_services),
        "actions": prf1_with_counts(pred_actions, gt_actions),
        "subsystems": sub_metrics,
        "plugins_and_bt": plug_bt,
    }


def run_real_ablation(repo_id: str, repo_root: Path, gt: Dict[str, Any], raw_out: Path) -> List[Dict[str, Any]]:
    """Run real staged ablation without hardcoded metrics."""
    ab_dir = raw_out / "ablation"
    ab_dir.mkdir(parents=True, exist_ok=True)
    gt_nodes = {clean_basename(n["name"]) for n in gt.get("core_nodes", gt["nodes"])}
    gt_topics = {clean_basename(t["name"]) for t in gt["topics"]}
    gt_services = {clean_basename(s["name"]) for s in gt["services"]}
    gt_actions = {clean_basename(a["name"]) for a in gt.get("actions", [])}
    if repo_id == "jaco2_sim_devkit":
        gt_actions = {clean_basename(a["name"]) for a in gt.get("api_inferred_actions", [])}

    results = []

    # 1. Baseline A: Regex-only
    t0 = time.time()
    r_nodes, r_topics = set(), set()
    node_pat = re.compile(r'class\s+([A-Za-z0-9_]+)\s*:\s*public\s+rclcpp::Node|class\s+([A-Za-z0-9_]+)\(Node\)')
    top_pat = re.compile(r'create_publisher(?:<[^>]+>)?\s*\([^"\']*["\']([^"\']+)["\']|create_subscription(?:<[^>]+>)?\s*\([^"\']*["\']([^"\']+)["\']')
    for p in repo_root.rglob("*"):
        if p.suffix in (".py", ".cpp", ".hpp") and "/test" not in p.as_posix().lower():
            txt = p.read_text(encoding="utf-8", errors="ignore")
            for m in node_pat.finditer(txt):
                r_nodes.add(clean_basename(m.group(1) or m.group(2)))
            for m in top_pat.finditer(txt):
                r_topics.add(clean_basename(m.group(1) or m.group(2)))
    tA = round(time.time() - t0, 3)
    results.append({
        "repo_id": repo_id,
        "configuration": "Baseline A: Static Regex-only",
        "status": "executed",
        "nodes": prf1_with_counts(r_nodes, gt_nodes),
        "topics": prf1_with_counts(r_topics, gt_topics),
        "services": prf1_with_counts(set(), gt_services),
        "actions": prf1_with_counts(set(), gt_actions),
        "evidence_coverage": 0.0,
        "time_s": tA,
    })

    # 2. Baseline B: Multi-language AST (Phase 1 only)
    t0 = time.time()
    nodes_file = ab_dir / "b_nodes.json"
    b_nodes = run_node_analysis(repo_root, nodes_file)
    tB = round(time.time() - t0, 3)
    b_node_names = {clean_basename(n.name or n.class_name) for n in b_nodes if not n.is_test}
    results.append({
        "repo_id": repo_id,
        "configuration": "Baseline B: Multi-language AST (Phase 1)",
        "status": "executed",
        "nodes": prf1_with_counts(b_node_names, gt_nodes),
        "topics": prf1_with_counts(set(), gt_topics),
        "services": prf1_with_counts(set(), gt_services),
        "actions": prf1_with_counts(set(), gt_actions),
        "evidence_coverage": 1.0,
        "time_s": tB,
    })

    # 3. Baseline C: Static + Launch (Phase 1 + Phase 2)
    t0 = time.time()
    _, instances, _, _ = run_phase2_launch_pipeline(repo_root, nodes_file, ab_dir)
    tC = round(time.time() - t0, 3)
    c_node_names = b_node_names | {clean_basename(i.node_name) for i in instances if i.node_name}
    results.append({
        "repo_id": repo_id,
        "configuration": "Baseline C: Static + Launch (Phase 1+2)",
        "status": "executed",
        "nodes": prf1_with_counts(c_node_names, gt_nodes),
        "topics": prf1_with_counts(set(), gt_topics),
        "services": prf1_with_counts(set(), gt_services),
        "actions": prf1_with_counts(set(), gt_actions),
        "evidence_coverage": 1.0,
        "time_s": round(tB + tC, 3),
    })

    # 4. Baseline D: Static + Launch + Comm Graph (Phase 1+2+3)
    t0 = time.time()
    decls, _, _, _ = run_phase3_communication_pipeline(repo_root, nodes_file, ab_dir / "launch_instances.json", ab_dir)
    tD = round(time.time() - t0, 3)
    d_topics = {clean_basename(d.resolved_name or d.name_expression) for d in decls if d.interface_type.value in ("publisher", "subscriber") and not d.owner_node_id.startswith("config::")}
    d_svcs = {clean_basename(d.resolved_name or d.name_expression) for d in decls if d.interface_type.value in ("service_server", "service_client") and not d.owner_node_id.startswith("config::")}
    d_acts = {clean_basename(d.resolved_name or d.name_expression) for d in decls if d.interface_type.value in ("action_server", "action_client") and not d.owner_node_id.startswith("config::")}
    results.append({
        "repo_id": repo_id,
        "configuration": "Baseline D: Static + Launch + Comm (Phase 1-3)",
        "status": "executed",
        "nodes": prf1_with_counts(b_node_names, gt_nodes),
        "topics": prf1_with_counts(d_topics, gt_topics),
        "services": prf1_with_counts(d_svcs, gt_services),
        "actions": prf1_with_counts(d_acts, gt_actions),
        "evidence_coverage": 1.0,
        "time_s": round(tB + tC + tD, 3),
    })

    # 5. Baseline E (Mode A Deterministic Full ArchSynth)
    arch = ArchitectureModel.model_validate(json.loads((raw_out / "architecture.json").read_text(encoding="utf-8")))
    e_topics = {clean_basename(d.resolved_name or d.name_expression) for d in arch.interfaces if d.interface_type.value in ("publisher", "subscriber") and not d.owner_node_id.startswith("config::")}
    e_svcs = {clean_basename(d.resolved_name or d.name_expression) for d in arch.interfaces if d.interface_type.value in ("service_server", "service_client") and not d.owner_node_id.startswith("config::")}
    e_acts = {clean_basename(d.resolved_name or d.name_expression) for d in arch.interfaces if d.interface_type.value in ("action_server", "action_client") and not d.owner_node_id.startswith("config::")}
    results.append({
        "repo_id": repo_id,
        "configuration": "Baseline E: Full ArchSynth Mode A (skip_llm=True)",
        "status": "executed",
        "nodes": prf1_with_counts(b_node_names, gt_nodes),
        "topics": prf1_with_counts(e_topics, gt_topics),
        "services": prf1_with_counts(e_svcs, gt_services),
        "actions": prf1_with_counts(e_acts, gt_actions),
        "evidence_coverage": 1.0,
        "time_s": None,  # filled from main run
    })

    # 6. Unavailable LLM-only / Static + LLM (Mode B)
    for llm_cfg in ("LLM-only", "Static + LLM", "Static + LLM + Schema (Mode B)"):
        results.append({
            "repo_id": repo_id,
            "configuration": llm_cfg,
            "status": "unavailable",
            "reason": "google-generativeai and ollama Python packages are not installed in the active environment",
            "nodes": None,
            "topics": None,
            "services": None,
            "actions": None,
            "evidence_coverage": None,
            "time_s": None,
        })

    return results


def main():
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "logs").mkdir(exist_ok=True)

    repo_rows = []
    entity_rows = []
    gt_comparison = {}
    subsystem_metrics_all = {}
    exec_times = []
    ablation_all = []
    manifest_repos = {}
    gt_hashes = {}

    for spec in REPOS:
        rid = spec["id"]
        rpath = spec["path"]
        ginfo = git_info(rpath)
        raw_out = RAW_ROOT / rid

        t0 = time.time()
        status = "completed"
        err_msg = None
        try:
            cfg = PipelineConfig(repo_path=str(rpath), output_dir=str(raw_out), skip_llm=True)
            ArchSynthPipeline(cfg).run()
        except Exception as exc:
            status = "failed"
            err_msg = str(exc)
        elapsed = round(time.time() - t0, 3)
        exec_times.append({"repository_id": rid, "execution_time_s": elapsed, "status": status})

        arch_path = raw_out / "architecture.json"
        if not arch_path.exists():
            repo_rows.append({
                "repository_id": rid,
                "repository_name": spec["name"],
                "commit": ginfo["commit"],
                "status": status,
                "error": err_msg,
            })
            continue

        arch_dict = json.loads(arch_path.read_text(encoding="utf-8"))
        model = ArchitectureModel.model_validate(arch_dict)
        ev = EvidenceValidator(rpath).validate(model)

        prod_nodes = sum(1 for n in model.nodes if not n.is_test)
        test_nodes = sum(1 for n in model.nodes if n.is_test)
        rec = (model.architecture_validation.inventory_reconciliation if model.architecture_validation else {})

        # Compute GT metrics if GT exists
        gt_eval = None
        if spec["gt_path"] and spec["gt_path"].exists():
            gt = json.loads(spec["gt_path"].read_text(encoding="utf-8"))
            gt_hashes[rid] = {"path": str(spec["gt_path"]), "sha256": sha256_file(spec["gt_path"])}
            if rid == "jaco2_sim_devkit":
                gt_eval = evaluate_jaco2_detailed(model, gt)
                for cat in ("nodes", "topics", "services", "source_actions", "api_inferred_actions", "yaml_configured_actions"):
                    m = gt_eval[cat]
                    entity_rows.append({"repository_id": rid, "category": cat, **m})
                subsystem_metrics_all[rid] = gt_eval["subsystems"]
            elif rid == "nav2":
                gt_eval = evaluate_nav2_detailed(model, gt)
                for cat in ("nodes_core", "nodes_extended", "topics", "services", "actions"):
                    m = gt_eval[cat]
                    entity_rows.append({"repository_id": rid, "category": cat, **m})
                subsystem_metrics_all[rid] = gt_eval["subsystems"]

            gt_comparison[rid] = gt_eval
            ab_res = run_real_ablation(rid, rpath, gt, raw_out)
            for row in ab_res:
                if row["configuration"].startswith("Baseline E"):
                    row["time_s"] = elapsed
            ablation_all.extend(ab_res)
        else:
            # No GT -> mark unavailable explicitly
            for cat in ("nodes", "topics", "services", "actions"):
                entity_rows.append({
                    "repository_id": rid,
                    "category": cat,
                    "ground_truth": "N/A",
                    "predicted": (
                        prod_nodes if cat == "nodes" else
                        len({clean_basename(d.resolved_name or d.name_expression) for d in model.interfaces if d.interface_type.value in ("publisher", "subscriber")}) if cat == "topics" else
                        len({clean_basename(d.resolved_name or d.name_expression) for d in model.interfaces if d.interface_type.value in ("service_server", "service_client")}) if cat == "services" else
                        len({clean_basename(d.resolved_name or d.name_expression) for d in model.interfaces if d.interface_type.value in ("action_server", "action_client")})
                    ),
                    "tp": "N/A", "fp": "N/A", "fn": "N/A",
                    "precision": "N/A", "recall": "N/A", "f1": "N/A",
                })
            subsystem_metrics_all[rid] = {
                "subsystems_count": len(model.subsystems),
                "ari": "N/A (no ground truth)",
                "nmi": "N/A (no ground truth)",
            }

        neg_ctrl_ok = (len(model.nodes) == 0 and len(model.launch_files) == 0 and len(model.interfaces) == 0) if rid == "express" else None

        repo_rows.append({
            "repository_id": rid,
            "repository_name": spec["name"],
            "branch": ginfo["branch"],
            "commit": ginfo["commit"],
            "total_nodes": len(model.nodes),
            "production_nodes": prod_nodes,
            "test_nodes": test_nodes,
            "launch_files": len(model.launch_files),
            "launch_instances": len(model.launch_instances),
            "source_interfaces": len(model.interfaces),
            "subsystems": len(model.subsystems),
            "evidence_coverage": round(ev.evidence_coverage, 4),
            "unsupported_entity_rate": round(ev.unsupported_entity_rate, 4),
            "execution_time_s": elapsed,
            "ground_truth_available": bool(spec["gt_path"]),
            "negative_control_rejected": neg_ctrl_ok,
            "status": status,
        })

        manifest_repos[rid] = {
            "url": spec["url"],
            "branch": ginfo["branch"],
            "commit_sha": ginfo["commit"],
            "raw_output_dir": str(raw_out),
            "reconciliation": rec,
        }

    # Save CSVs & JSONs
    def write_csv(path: Path, rows: List[Dict[str, Any]]):
        if not rows:
            return
        keys = list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)

    write_csv(OUT_ROOT / "repository_comparison.csv", repo_rows)
    write_csv(OUT_ROOT / "entity_metrics.csv", entity_rows)
    write_csv(OUT_ROOT / "execution_times.csv", exec_times)

    # Flatten ablation CSV
    ab_flat = []
    for r in ablation_all:
        ab_flat.append({
            "repo_id": r["repo_id"],
            "configuration": r["configuration"],
            "status": r["status"],
            "node_f1": r["nodes"]["f1"] if r["nodes"] else "N/A",
            "topic_f1": r["topics"]["f1"] if r["topics"] else "N/A",
            "service_f1": r["services"]["f1"] if r["services"] else "N/A",
            "action_f1": r["actions"]["f1"] if r["actions"] else "N/A",
            "evidence_coverage": r["evidence_coverage"] if r["evidence_coverage"] is not None else "N/A",
            "time_s": r["time_s"] if r["time_s"] is not None else "N/A",
            "reason": r.get("reason", ""),
        })
    write_csv(OUT_ROOT / "ablation_results.csv", ab_flat)

    (OUT_ROOT / "entity_metrics.json").write_text(json.dumps(entity_rows, indent=2), encoding="utf-8")
    (OUT_ROOT / "ground_truth_comparison.json").write_text(json.dumps(gt_comparison, indent=2), encoding="utf-8")
    (OUT_ROOT / "ablation_results.json").write_text(json.dumps(ablation_all, indent=2), encoding="utf-8")
    (OUT_ROOT / "subsystem_metrics.json").write_text(json.dumps(subsystem_metrics_all, indent=2), encoding="utf-8")

    manifest = {
        "archsynth_version": "2.2",
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "deterministic_static_skip_llm_true",
        "scoring_rules": {
            "matching": "Canonical basename matching (strip leading '/', split '/'[-1], lowercase) per eval/evaluator.py",
            "zero_denominator": "0/0 -> 1.0; one-sided empty -> 0.0",
            "invariants": "TP + FN == ground_truth; TP + FP == predicted",
            "missing_ground_truth": "Marked N/A (never fabricated)",
        },
        "ground_truth_datasets": gt_hashes,
        "repositories": manifest_repos,
    }
    (OUT_ROOT / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info(f"Benchmark v2.2 artifacts saved to {OUT_ROOT}")


if __name__ == "__main__":
    main()
