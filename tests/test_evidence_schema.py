"""
Tests for ArchSynth schema research extensions.
Verifies backward compatibility and new evidence/provenance structures.
"""
import pytest
from src.schema import (
    EvidenceItem, EvidenceType, ValidationStatus, ValidationReport,
    UnsupportedEntityRecord, DriftReport, NodeChange, TopicChange,
    SubsystemChange, TopicInfo, ServiceInfo, ActionInfo, ROS2Node,
    ArchitectureModel, MessageType
)


class TestEvidenceItem:
    def test_basic_creation(self):
        ev = EvidenceItem(
            file="nav2_planner/src/planner_server.cpp",
            line_start=100,
            line_end=115,
            evidence_type=EvidenceType.NODE_DEFINITION,
            source="python_ast_analyzer",
        )
        assert ev.file == "nav2_planner/src/planner_server.cpp"
        assert ev.line_start == 100
        assert ev.evidence_type == EvidenceType.NODE_DEFINITION
        assert ev.confidence == 1.0  # default

    def test_optional_fields(self):
        """Evidence item with minimal required fields"""
        ev = EvidenceItem(
            file="some/file.py",
            evidence_type=EvidenceType.PUBLISHER_CREATION,
            source="python_ast_analyzer"
        )
        assert ev.line_start is None
        assert ev.line_end is None
        assert ev.explanation is None

    def test_confidence_bounds(self):
        with pytest.raises(Exception):
            EvidenceItem(
                file="f.py",
                evidence_type=EvidenceType.LAUNCH_NODE,
                source="launch_analyzer",
                confidence=1.5  # Out of bounds
            )


class TestValidationStatus:
    def test_all_statuses(self):
        assert ValidationStatus.SUPPORTED == "supported"
        assert ValidationStatus.UNSUPPORTED == "unsupported"
        assert ValidationStatus.PARTIAL == "partial"
        assert ValidationStatus.UNKNOWN == "unknown"


class TestBackwardCompatibility:
    """Verify existing architecture.json files still deserialize correctly"""

    def test_topic_info_without_evidence(self):
        """Old TopicInfo without evidence field should still work"""
        ti = TopicInfo.model_validate({
            "name": "/cmd_vel",
            "message_type": "geometry_msgs/msg/Twist",
            "message_category": "geometry_msgs"
        })
        assert ti.evidence == []  # default empty list

    def test_service_info_without_evidence(self):
        si = ServiceInfo.model_validate({
            "name": "/navigate_to_pose",
            "service_type": "nav2_msgs/action/NavigateToPose",
            "role": "server"
        })
        assert si.evidence == []

    def test_action_info_without_evidence(self):
        ai = ActionInfo.model_validate({
            "name": "/follow_path",
            "action_type": "nav2_msgs/action/FollowPath",
            "role": "server"
        })
        assert ai.evidence == []

    def test_ros2node_without_evidence(self):
        node = ROS2Node.model_validate({
            "name": "bt_navigator",
            "fully_qualified_name": "bt_navigator",
            "class_name": "BtNavigator",
            "source_file": "nav2_bt_navigator/src/bt_navigator.cpp",
            "package_name": "nav2_bt_navigator"
        })
        assert node.evidence == []
        assert node.validation_status == ValidationStatus.UNKNOWN

    def test_architecture_model_without_research_fields(self):
        """Old ArchitectureModel JSON without research fields should still parse"""
        model = ArchitectureModel.model_validate({
            "repo_name": "nav2",
            "repo_url": "https://github.com/ros-planning/navigation2",
            "commit_hash": "abc123",
            "analysis_timestamp": "2026-09-23T00:00:00Z",
            "nodes": [],
            "launch_files": [],
            "subsystems": [],
            "topic_connections": [],
            "service_connections": [],
            "action_connections": [],
        })
        assert model.validation_report is None
        assert model.experiment_metadata is None
        assert model.drift_report is None


class TestTopicInfoWithEvidence:
    def test_topic_with_evidence(self):
        ev = EvidenceItem(
            file="controller.py",
            line_start=50,
            evidence_type=EvidenceType.PUBLISHER_CREATION,
            source="python_ast_analyzer"
        )
        ti = TopicInfo(
            name="/cmd_vel",
            message_type="geometry_msgs/msg/Twist",
            evidence=[ev]
        )
        assert len(ti.evidence) == 1
        assert ti.evidence[0].line_start == 50


class TestDriftReport:
    def test_compute_total(self):
        report = DriftReport(
            added_nodes=["nodeA", "nodeB"],
            removed_nodes=["nodeC"],
            added_topics=["/new_topic"],
            removed_topics=[],
            added_services=[],
            removed_services=[],
            added_actions=[],
            removed_actions=[],
        )
        total = report.compute_total()
        assert total == 4  # 2 added + 1 removed nodes + 1 added topic

    def test_empty_drift_report(self):
        report = DriftReport()
        report.compute_total()
        assert report.total_changes == 0


class TestValidationReport:
    def test_evidence_coverage_fields(self):
        report = ValidationReport(
            total_entities=50,
            supported_entities=47,
            unsupported_entities=3,
            evidence_coverage=0.94,
            unsupported_entity_rate=0.06
        )
        assert report.evidence_coverage == 0.94
        assert report.unsupported_entities == 3
