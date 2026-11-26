"""
ArchSynth Evaluation Metrics

Computes all evaluation metrics for the M.Tech dissertation:

EXISTING (preserved):
    - Precision / Recall / F1 for nodes, topics, services, actions

RESEARCH EXTENSIONS:
    A. Evidence Coverage Metrics
        - evidence_coverage          = supported_entities / total_entities
        - unsupported_entity_rate    = unsupported / total
        - per-category coverage (nodes, topics, services, actions)

    B. Subsystem Clustering Metrics
        - Assignment accuracy
        - Adjusted Rand Index (ARI)
        - Normalized Mutual Information (NMI)

    C. Drift Detection Metrics
        - Drift Precision / Recall / F1
        (given ground-truth changes vs. detected changes)
"""

from typing import List, Dict, Set, Tuple, Any, Optional


# ---------------------------------------------------------------------------
# Existing: Basic Precision / Recall / F1
# ---------------------------------------------------------------------------

def fuzzy_match_names(name1: str, name2: str) -> bool:
    """
    Case-insensitive, slash-agnostic string matching for ROS2 node/topic names.
    e.g. '/bt_navigator' matches 'bt_navigator'
    """
    clean1 = name1.lower().lstrip('/')
    clean2 = name2.lower().lstrip('/')
    return clean1 == clean2 or clean1 in clean2 or clean2 in clean1


def compute_precision_recall_f1(
    predicted: List[str],
    ground_truth: List[str],
    fuzzy: bool = True
) -> Dict[str, float]:
    """
    Compute Precision, Recall, and F1 score between predicted items and ground truth items.
    """
    if not ground_truth:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    true_positives = 0
    matched_gt: Set[int] = set()

    for pred in predicted:
        for idx, gt in enumerate(ground_truth):
            if idx in matched_gt:
                continue
            if (fuzzy and fuzzy_match_names(pred, gt)) or pred == gt:
                true_positives += 1
                matched_gt.add(idx)
                break

    precision = true_positives / len(predicted) if predicted else 0.0
    recall = true_positives / len(ground_truth) if ground_truth else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "true_positives": true_positives,
        "predicted_count": len(predicted),
        "ground_truth_count": len(ground_truth)
    }


def evaluate_architecture_model(
    predicted_nodes: List[str],
    ground_truth_nodes: List[str],
    predicted_topics: List[str],
    ground_truth_topics: List[str]
) -> Dict[str, Any]:
    """
    Evaluate predicted architecture against ground truth across nodes and topics.
    """
    node_metrics = compute_precision_recall_f1(predicted_nodes, ground_truth_nodes)
    topic_metrics = compute_precision_recall_f1(predicted_topics, ground_truth_topics)

    return {
        "nodes": node_metrics,
        "topics": topic_metrics,
        "overall_f1": round((node_metrics["f1"] + topic_metrics["f1"]) / 2.0, 4)
    }


# ---------------------------------------------------------------------------
# RESEARCH EXTENSION A: Evidence Coverage Metrics
# ---------------------------------------------------------------------------

def compute_evidence_coverage(
    model_dict: Dict[str, Any]
) -> Dict[str, float]:
    """
    Compute evidence coverage metrics from an ArchitectureModel dictionary
    (or its validation_report sub-key if already validated).

    Research metric:
        Evidence Coverage = entities_with_evidence / total_entities

    Args:
        model_dict: ArchitectureModel as a dict (output of model.model_dump())

    Returns:
        Dict with evidence_coverage, unsupported_entity_rate, per-category coverages
    """
    # If validation_report already in model, use it
    vr = model_dict.get("validation_report")
    if vr and vr.get("total_entities", 0) > 0:
        return {
            "evidence_coverage": vr.get("evidence_coverage", 0.0),
            "unsupported_entity_rate": vr.get("unsupported_entity_rate", 0.0),
            "node_coverage": vr.get("node_coverage", 0.0),
            "topic_coverage": vr.get("topic_coverage", 0.0),
            "service_coverage": vr.get("service_coverage", 0.0),
            "action_coverage": vr.get("action_coverage", 0.0),
            "total_entities": vr.get("total_entities", 0),
            "supported_entities": vr.get("supported_entities", 0),
            "unsupported_entities": vr.get("unsupported_entities", 0),
        }

    # Otherwise compute from raw model
    nodes = model_dict.get("nodes", [])
    node_total = len(nodes)
    node_supported = sum(1 for n in nodes if n.get("evidence"))

    topic_total = 0
    topic_supported = 0
    service_total = 0
    service_supported = 0
    action_total = 0
    action_supported = 0

    seen_topics: Set[str] = set()
    seen_services: Set[str] = set()
    seen_actions: Set[str] = set()

    for node in nodes:
        for pub in node.get("publishers", []):
            name = pub.get("name", "")
            if name not in seen_topics:
                seen_topics.add(name)
                topic_total += 1
                if pub.get("evidence"):
                    topic_supported += 1
        for sub in node.get("subscribers", []):
            name = sub.get("name", "")
            if name not in seen_topics:
                seen_topics.add(name)
                topic_total += 1
                if sub.get("evidence"):
                    topic_supported += 1
        for srv in node.get("services", []):
            key = f"{srv.get('name', '')}:{srv.get('role', '')}"
            if key not in seen_services:
                seen_services.add(key)
                service_total += 1
                if srv.get("evidence"):
                    service_supported += 1
        for act in node.get("actions", []):
            key = f"{act.get('name', '')}:{act.get('role', '')}"
            if key not in seen_actions:
                seen_actions.add(key)
                action_total += 1
                if act.get("evidence"):
                    action_supported += 1

    total = node_total + topic_total + service_total + action_total
    supported = node_supported + topic_supported + service_supported + action_supported

    coverage = supported / total if total > 0 else 0.0
    unsupported_rate = (total - supported) / total if total > 0 else 0.0

    return {
        "evidence_coverage": round(coverage, 4),
        "unsupported_entity_rate": round(unsupported_rate, 4),
        "node_coverage": round(node_supported / node_total if node_total else 0, 4),
        "topic_coverage": round(topic_supported / topic_total if topic_total else 0, 4),
        "service_coverage": round(service_supported / service_total if service_total else 0, 4),
        "action_coverage": round(action_supported / action_total if action_total else 0, 4),
        "total_entities": total,
        "supported_entities": supported,
        "unsupported_entities": total - supported,
    }


# ---------------------------------------------------------------------------
# RESEARCH EXTENSION B: Subsystem Clustering Metrics
# ---------------------------------------------------------------------------

def compute_subsystem_metrics(
    predicted_assignments: Dict[str, str],
    ground_truth_assignments: Dict[str, str]
) -> Dict[str, float]:
    """
    Evaluate subsystem clustering quality against ground truth.

    Args:
        predicted_assignments: {node_name: subsystem_name} from ArchSynth
        ground_truth_assignments: {node_name: subsystem_name} from ground truth

    Returns:
        Dict with accuracy, adjusted_rand_index (ARI), normalized_mutual_info (NMI)

    Research motivation:
        Subsystem recovery is a key differentiator of ArchSynth.
        ARI and NMI quantify clustering quality beyond simple node P/R/F1.
    """
    # Find common nodes (only evaluate nodes present in both)
    common_nodes = sorted(set(predicted_assignments.keys()) & set(ground_truth_assignments.keys()))

    if not common_nodes:
        return {
            "accuracy": 0.0,
            "adjusted_rand_index": 0.0,
            "normalized_mutual_info": 0.0,
            "common_nodes": 0,
            "predicted_nodes": len(predicted_assignments),
            "gt_nodes": len(ground_truth_assignments),
            "note": "No common nodes found between predicted and ground truth"
        }

    pred_labels = [predicted_assignments[n] for n in common_nodes]
    gt_labels = [ground_truth_assignments[n] for n in common_nodes]

    # Simple accuracy: fraction of nodes with same subsystem label
    accuracy = sum(p == g for p, g in zip(pred_labels, gt_labels)) / len(common_nodes)

    # ARI and NMI via sklearn (already in requirements.txt)
    ari = 0.0
    nmi = 0.0
    try:
        from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
        from sklearn.preprocessing import LabelEncoder

        le_pred = LabelEncoder()
        le_gt = LabelEncoder()
        pred_encoded = le_pred.fit_transform(pred_labels)
        gt_encoded = le_gt.fit_transform(gt_labels)

        ari = adjusted_rand_score(gt_encoded, pred_encoded)
        nmi = normalized_mutual_info_score(gt_encoded, pred_encoded)
    except ImportError:
        pass  # sklearn not available — ARI/NMI will be 0.0

    return {
        "accuracy": round(float(accuracy), 4),
        "adjusted_rand_index": round(float(ari), 4),
        "normalized_mutual_info": round(float(nmi), 4),
        "common_nodes": len(common_nodes),
        "predicted_nodes": len(predicted_assignments),
        "gt_nodes": len(ground_truth_assignments),
    }


def build_node_to_subsystem_map(
    subsystems: List[Dict[str, Any]]
) -> Dict[str, str]:
    """
    Build {node_name: subsystem_name} mapping from ArchitectureModel.subsystems list.

    Args:
        subsystems: List of Subsystem dicts (from ArchitectureModel.model_dump())

    Returns:
        Dict mapping each node name to its subsystem name
    """
    mapping: Dict[str, str] = {}
    for sub in subsystems:
        sub_name = sub.get("name", "unknown")
        for node_name in sub.get("nodes", []):
            mapping[node_name] = sub_name
    return mapping


# ---------------------------------------------------------------------------
# RESEARCH EXTENSION C: Architecture Drift / Evolution Metrics
# ---------------------------------------------------------------------------

def compute_drift_metrics(
    detected_changes: Dict[str, List[str]],
    ground_truth_changes: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Evaluate drift detection quality against known ground-truth changes.

    Args:
        detected_changes: {change_type: [entity_names]}, e.g.:
            {"added_nodes": ["nodeA"], "removed_topics": ["/cmd_vel"]}
        ground_truth_changes: Same structure for verified changes

    Returns:
        Dict with precision, recall, F1 for drift detection

    Research motivation:
        Makes architecture drift detection a research experiment (measurable)
        rather than just a UI feature.
    """
    results: Dict[str, Any] = {}
    all_precisions = []
    all_recalls = []

    change_types = set(detected_changes.keys()) | set(ground_truth_changes.keys())

    for change_type in sorted(change_types):
        detected = detected_changes.get(change_type, [])
        gt = ground_truth_changes.get(change_type, [])

        metrics = compute_precision_recall_f1(detected, gt, fuzzy=True)
        results[change_type] = metrics

        if gt:  # Only average over change types that have ground truth
            all_precisions.append(metrics["precision"])
            all_recalls.append(metrics["recall"])

    # Macro-averaged metrics
    if all_precisions:
        avg_p = sum(all_precisions) / len(all_precisions)
        avg_r = sum(all_recalls) / len(all_recalls)
        avg_f1 = (2 * avg_p * avg_r) / (avg_p + avg_r) if (avg_p + avg_r) > 0 else 0.0
        results["macro_avg"] = {
            "precision": round(avg_p, 4),
            "recall": round(avg_r, 4),
            "f1": round(avg_f1, 4)
        }
    else:
        results["macro_avg"] = {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    return results


# ---------------------------------------------------------------------------
# Full Architecture Evaluation (combined)
# ---------------------------------------------------------------------------

def evaluate_full_architecture(
    predicted_model_dict: Dict[str, Any],
    ground_truth: Dict[str, Any],
    compute_subsystem: bool = True
) -> Dict[str, Any]:
    """
    Run all evaluation metrics against ground truth.

    Args:
        predicted_model_dict: ArchitectureModel.model_dump() output
        ground_truth: Dict with keys: nodes, topics, services, actions, subsystems
        compute_subsystem: Whether to compute ARI/NMI subsystem metrics

    Returns:
        Combined evaluation report with all metrics
    """
    pred_nodes = [n.get("name", n.get("fully_qualified_name", "")) for n in predicted_model_dict.get("nodes", [])]
    gt_nodes = ground_truth.get("nodes", [])

    pred_topics: Set[str] = set()
    for n in predicted_model_dict.get("nodes", []):
        for p in n.get("publishers", []):
            pred_topics.add(p.get("name", ""))
        for s in n.get("subscribers", []):
            pred_topics.add(s.get("name", ""))
    gt_topics = ground_truth.get("topics", [])

    pred_services: Set[str] = set()
    for n in predicted_model_dict.get("nodes", []):
        for s in n.get("services", []):
            pred_services.add(s.get("name", ""))
    gt_services = ground_truth.get("services", [])

    pred_actions: Set[str] = set()
    for n in predicted_model_dict.get("nodes", []):
        for a in n.get("actions", []):
            pred_actions.add(a.get("name", ""))
    gt_actions = ground_truth.get("actions", [])

    result = {
        "nodes": compute_precision_recall_f1(pred_nodes, gt_nodes),
        "topics": compute_precision_recall_f1(list(pred_topics), gt_topics),
        "services": compute_precision_recall_f1(list(pred_services), gt_services),
        "actions": compute_precision_recall_f1(list(pred_actions), gt_actions),
        "evidence": compute_evidence_coverage(predicted_model_dict),
    }

    if compute_subsystem and ground_truth.get("subsystems"):
        pred_sub_map = build_node_to_subsystem_map(predicted_model_dict.get("subsystems", []))
        gt_sub_map = ground_truth.get("subsystems", {})
        if isinstance(gt_sub_map, dict):
            result["subsystems"] = compute_subsystem_metrics(pred_sub_map, gt_sub_map)

    # Macro F1 across entity types
    f1_scores = [
        result["nodes"]["f1"],
        result["topics"]["f1"],
        result["services"]["f1"],
        result["actions"]["f1"],
    ]
    result["macro_f1"] = round(sum(f1_scores) / len(f1_scores), 4)

    return result


if __name__ == "__main__":
    preds = ["bt_navigator", "planner_server", "controller_server", "amcl"]
    truth = ["bt_navigator", "planner_server", "controller_server", "amcl", "map_server"]

    res = compute_precision_recall_f1(preds, truth)
    print("Sample Precision/Recall/F1:")
    print(res)

    # Sample subsystem metrics
    pred_sub = {"bt_navigator": "navigation", "planner_server": "planning", "amcl": "localization"}
    gt_sub = {"bt_navigator": "navigation", "planner_server": "navigation", "amcl": "localization"}
    sub_res = compute_subsystem_metrics(pred_sub, gt_sub)
    print("\nSample Subsystem Metrics:")
    print(sub_res)
