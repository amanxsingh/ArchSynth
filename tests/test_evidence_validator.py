"""
Tests for EvidenceValidator module.
"""
import pytest
import json
from pathlib import Path
from src.schema import (
    ArchitectureModel, ROS2Node, TopicInfo, ServiceInfo, ActionInfo,
    EvidenceItem, EvidenceType, ValidationStatus
)
from src.evidence_validator import EvidenceValidator, run_evidence_validation


def _make_evidence(file: str = "test.py", line: int = 10) -> EvidenceItem:
    return EvidenceItem(
        file=file,
        line_start=line,
        line_end=line + 5,
        evidence_type=EvidenceType.NODE_DEFINITION,
        source="python_ast_analyzer"
    )


def _make_model(with_evidence: bool = True) -> ArchitectureModel:
    ev = [_make_evidence()] if with_evidence else []
    pub_ev = [EvidenceItem(
        file="test.py", line_start=20,
        evidence_type=EvidenceType.PUBLISHER_CREATION,
        source="python_ast_analyzer"
    )] if with_evidence else []

    node = ROS2Node(
        name="test_node",
        fully_qualified_name="test_node",
        class_name="TestNode",
        source_file="test.py",
        package_name="test_pkg",
        evidence=ev,
        publishers=[
            TopicInfo(name="/test_topic", message_type="std_msgs/msg/String", evidence=pub_ev)
        ]
    )
    return ArchitectureModel(
        repo_name="test_repo",
        repo_url="",
        commit_hash="abc",
        analysis_timestamp="2026-01-01T00:00:00Z",
        nodes=[node]
    )


class TestEvidenceValidator:
    def test_validation_with_evidence(self):
        """Nodes with evidence should be SUPPORTED"""
        model = _make_model(with_evidence=True)
        validator = EvidenceValidator(repo_root=None)  # No file checks
        report = validator.validate(model)
        assert report.supported_entities > 0
        assert report.evidence_coverage > 0.0

    def test_validation_without_evidence(self):
        """Nodes without evidence should be UNSUPPORTED"""
        model = _make_model(with_evidence=False)
        validator = EvidenceValidator(repo_root=None)
        report = validator.validate(model)
        assert report.unsupported_entities > 0
        assert report.unsupported_entity_rate > 0.0

    def test_evidence_coverage_range(self):
        """Evidence coverage must be in [0, 1]"""
        model = _make_model(with_evidence=True)
        validator = EvidenceValidator(repo_root=None)
        report = validator.validate(model)
        assert 0.0 <= report.evidence_coverage <= 1.0

    def test_total_equals_sum(self):
        """supported + unsupported = total"""
        model = _make_model(with_evidence=True)
        validator = EvidenceValidator(repo_root=None)
        report = validator.validate(model)
        assert report.supported_entities + report.unsupported_entities == report.total_entities

    def test_annotate_model(self):
        """annotate_model should set validation_status on nodes"""
        model = _make_model(with_evidence=True)
        validator = EvidenceValidator(repo_root=None)
        report = validator.validate(model)
        model = validator.annotate_model(model, report)
        # Node has evidence, should be SUPPORTED
        assert model.nodes[0].validation_status == ValidationStatus.SUPPORTED

    def test_annotate_model_unsupported(self):
        """Node without evidence should be UNKNOWN after annotation (no evidence, not in unsupported list)"""
        model = _make_model(with_evidence=False)
        validator = EvidenceValidator(repo_root=None)
        report = validator.validate(model)
        model = validator.annotate_model(model, report)
        # No evidence → marked UNSUPPORTED (in unsupported_list)
        assert model.nodes[0].validation_status == ValidationStatus.UNSUPPORTED

    def test_run_convenience_function(self, tmp_path):
        """run_evidence_validation convenience function saves report"""
        model = _make_model(with_evidence=True)
        out_path = tmp_path / "validation_report.json"
        result_model, report = run_evidence_validation(model, repo_root=None, output_path=out_path)
        assert out_path.exists()
        data = json.loads(out_path.read_text())
        assert "evidence_coverage" in data
