"""
ArchSynth Subsystem Clustering Evaluation

Research module for quantitative evaluation of LLM-generated subsystem groupings
against manually-verified ground truth assignments.

Research metrics:
    - Assignment accuracy
    - Adjusted Rand Index (ARI)
    - Normalized Mutual Information (NMI)

Usage:
    python -m eval.subsystem_eval \\
        --arch output/nav2_pipeline/architecture.json \\
        --ground-truth eval/ground_truth/nav2/subsystems.json \\
        --output eval/results/subsystem_eval_nav2.json
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def load_ground_truth_subsystems(path: Path) -> Dict[str, str]:
    """
    Load ground truth subsystem assignments from JSON file.

    Expected format:
        {
            "bt_navigator": "navigation",
            "planner_server": "planning",
            "controller_server": "control",
            "amcl": "localization"
        }

    Returns:
        {node_name: subsystem_name} mapping
    """
    if not path.exists():
        raise FileNotFoundError(f"Ground truth subsystems file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected dict {{node_name: subsystem}}, got {type(data)}")

    return data


def load_predicted_subsystems(arch_path: Path) -> Dict[str, str]:
    """
    Load predicted subsystem assignments from an ArchitectureModel JSON file.

    Returns:
        {node_name: subsystem_name} mapping
    """
    if not arch_path.exists():
        raise FileNotFoundError(f"Architecture JSON not found: {arch_path}")

    with open(arch_path, "r", encoding="utf-8") as f:
        arch = json.load(f)

    from eval.metrics import build_node_to_subsystem_map
    return build_node_to_subsystem_map(arch.get("subsystems", []))


def run_subsystem_evaluation(
    arch_path: Path,
    gt_path: Path,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run full subsystem clustering evaluation.

    Args:
        arch_path: Path to architecture.json (ArchSynth output)
        gt_path: Path to ground truth subsystems.json
        output_path: Optional path to save JSON result

    Returns:
        Evaluation result dict
    """
    from eval.metrics import compute_subsystem_metrics

    predicted = load_predicted_subsystems(arch_path)
    ground_truth = load_ground_truth_subsystems(gt_path)

    metrics = compute_subsystem_metrics(predicted, ground_truth)

    # Include per-node details
    common_nodes = set(predicted.keys()) & set(ground_truth.keys())
    node_details = []
    for node in sorted(common_nodes):
        pred_sub = predicted.get(node, "?")
        gt_sub = ground_truth.get(node, "?")
        node_details.append({
            "node": node,
            "predicted_subsystem": pred_sub,
            "gt_subsystem": gt_sub,
            "correct": pred_sub == gt_sub
        })

    result = {
        "arch_file": str(arch_path),
        "ground_truth_file": str(gt_path),
        "metrics": metrics,
        "node_assignments": node_details
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        logger.info(f"Subsystem evaluation saved to {output_path}")

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="ArchSynth Subsystem Clustering Evaluation")
    parser.add_argument("--arch", required=True, help="Path to architecture.json")
    parser.add_argument("--ground-truth", required=True, help="Path to ground truth subsystems.json")
    parser.add_argument("--output", default=None, help="Path to save evaluation JSON")
    args = parser.parse_args()

    result = run_subsystem_evaluation(
        arch_path=Path(args.arch),
        gt_path=Path(args.ground_truth),
        output_path=Path(args.output) if args.output else None
    )

    print("\n=== Subsystem Clustering Evaluation ===")
    m = result["metrics"]
    print(f"Common nodes evaluated:  {m['common_nodes']}")
    print(f"Predicted nodes:         {m['predicted_nodes']}")
    print(f"Ground truth nodes:      {m['gt_nodes']}")
    print(f"Assignment Accuracy:     {m['accuracy']:.1%}")
    print(f"Adjusted Rand Index:     {m['adjusted_rand_index']:.4f}")
    print(f"Normalized Mutual Info:  {m['normalized_mutual_info']:.4f}")
