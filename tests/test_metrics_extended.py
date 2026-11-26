"""
Tests for extended evaluation metrics (evidence coverage, subsystem clustering, drift).
"""
import pytest
from eval.metrics import (
    compute_precision_recall_f1,
    compute_evidence_coverage,
    compute_subsystem_metrics,
    compute_drift_metrics,
    build_node_to_subsystem_map,
    evaluate_full_architecture,
)


class TestPrecisionRecallF1:
    """Existing tests — verify these still work"""

    def test_perfect_match(self):
        preds = ["nodeA", "nodeB"]
        truth = ["nodeA", "nodeB"]
        result = compute_precision_recall_f1(preds, truth)
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0

    def test_empty_predictions(self):
        result = compute_precision_recall_f1([], ["nodeA"])
        assert result["precision"] == 0.0
        assert result["recall"] == 0.0

    def test_empty_ground_truth(self):
        result = compute_precision_recall_f1(["nodeA"], [])
        assert result["f1"] == 0.0


class TestEvidenceCoverageMetric:
    def _make_model_dict(self, with_evidence: bool):
        ev = [{"file": "f.py", "evidence_type": "node_definition", "source": "ast"}] if with_evidence else []
        pub_ev = [{"file": "f.py", "evidence_type": "publisher_creation", "source": "ast"}] if with_evidence else []
        return {
            "nodes": [{
                "name": "test_node",
                "evidence": ev,
                "publishers": [{"name": "/test", "evidence": pub_ev}],
                "subscribers": [],
                "services": [],
                "actions": []
            }]
        }

    def test_full_coverage(self):
        model = self._make_model_dict(with_evidence=True)
        result = compute_evidence_coverage(model)
        assert result["evidence_coverage"] == 1.0
        assert result["unsupported_entity_rate"] == 0.0

    def test_zero_coverage(self):
        model = self._make_model_dict(with_evidence=False)
        result = compute_evidence_coverage(model)
        assert result["evidence_coverage"] == 0.0
        assert result["unsupported_entity_rate"] == 1.0

    def test_coverage_range(self):
        model = self._make_model_dict(with_evidence=True)
        result = compute_evidence_coverage(model)
        assert 0.0 <= result["evidence_coverage"] <= 1.0

    def test_from_validation_report(self):
        """If validation_report already in model, use it directly"""
        model = {
            "nodes": [],
            "validation_report": {
                "total_entities": 10,
                "supported_entities": 8,
                "unsupported_entities": 2,
                "evidence_coverage": 0.8,
                "unsupported_entity_rate": 0.2,
                "node_coverage": 0.9,
                "topic_coverage": 0.7,
                "service_coverage": 0.8,
                "action_coverage": 0.8,
            }
        }
        result = compute_evidence_coverage(model)
        assert result["evidence_coverage"] == 0.8


class TestSubsystemMetrics:
    def test_perfect_assignment(self):
        pred = {"nodeA": "nav", "nodeB": "loc"}
        gt = {"nodeA": "nav", "nodeB": "loc"}
        result = compute_subsystem_metrics(pred, gt)
        assert result["accuracy"] == 1.0

    def test_wrong_assignment(self):
        pred = {"nodeA": "nav", "nodeB": "nav"}
        gt = {"nodeA": "nav", "nodeB": "loc"}
        result = compute_subsystem_metrics(pred, gt)
        assert result["accuracy"] == 0.5

    def test_no_common_nodes(self):
        pred = {"nodeA": "nav"}
        gt = {"nodeB": "loc"}
        result = compute_subsystem_metrics(pred, gt)
        assert result["common_nodes"] == 0
        assert result["accuracy"] == 0.0

    def test_build_node_to_subsystem_map(self):
        subsystems = [
            {"name": "Navigation", "nodes": ["planner", "controller"]},
            {"name": "Localization", "nodes": ["amcl"]}
        ]
        mapping = build_node_to_subsystem_map(subsystems)
        assert mapping["planner"] == "Navigation"
        assert mapping["amcl"] == "Localization"


class TestDriftMetrics:
    def test_perfect_drift_detection(self):
        detected = {"added_nodes": ["nodeA"], "removed_topics": ["/old"]}
        gt = {"added_nodes": ["nodeA"], "removed_topics": ["/old"]}
        result = compute_drift_metrics(detected, gt)
        assert result["added_nodes"]["f1"] == 1.0
        assert result["removed_topics"]["f1"] == 1.0

    def test_false_positive_in_drift(self):
        detected = {"added_nodes": ["nodeA", "fakeNode"]}
        gt = {"added_nodes": ["nodeA"]}
        result = compute_drift_metrics(detected, gt)
        assert result["added_nodes"]["precision"] < 1.0

    def test_macro_avg_computed(self):
        detected = {"added_nodes": ["nodeA"]}
        gt = {"added_nodes": ["nodeA"]}
        result = compute_drift_metrics(detected, gt)
        assert "macro_avg" in result
        assert result["macro_avg"]["f1"] == 1.0
