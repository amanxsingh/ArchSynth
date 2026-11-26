"""
Tests for ArchitectureDiff module.
"""
import pytest
from src.schema import ArchitectureModel, ROS2Node, TopicInfo, Subsystem
from src.architecture_diff import ArchitectureDiff


def _make_model(
    nodes=None, topic_connections=None, service_connections=None,
    action_connections=None, subsystems=None, commit="abc"
) -> ArchitectureModel:
    return ArchitectureModel(
        repo_name="test_repo",
        repo_url="",
        commit_hash=commit,
        analysis_timestamp="2026-01-01T00:00:00Z",
        nodes=nodes or [],
        topic_connections=topic_connections or [],
        service_connections=service_connections or [],
        action_connections=action_connections or [],
        subsystems=subsystems or []
    )


def _make_node(name: str, package: str = "pkg") -> ROS2Node:
    return ROS2Node(
        name=name,
        fully_qualified_name=name,
        class_name=name,
        source_file=f"{name}.py",
        package_name=package
    )


class TestArchitectureDiff:
    def test_added_nodes(self):
        arch_a = _make_model(nodes=[_make_node("nodeA")])
        arch_b = _make_model(nodes=[_make_node("nodeA"), _make_node("nodeB")])
        differ = ArchitectureDiff()
        report = differ.diff(arch_a, arch_b)
        assert "nodeB" in report.added_nodes
        assert "nodeA" not in report.added_nodes

    def test_removed_nodes(self):
        arch_a = _make_model(nodes=[_make_node("nodeA"), _make_node("nodeC")])
        arch_b = _make_model(nodes=[_make_node("nodeA")])
        differ = ArchitectureDiff()
        report = differ.diff(arch_a, arch_b)
        assert "nodeC" in report.removed_nodes

    def test_no_changes(self):
        arch_a = _make_model(nodes=[_make_node("nodeA")])
        arch_b = _make_model(nodes=[_make_node("nodeA")])
        differ = ArchitectureDiff()
        report = differ.diff(arch_a, arch_b)
        assert report.added_nodes == []
        assert report.removed_nodes == []
        assert report.total_changes == 0

    def test_added_topics(self):
        arch_a = _make_model(topic_connections=[{"topic": "/odom", "publishers": [], "subscribers": []}])
        arch_b = _make_model(topic_connections=[
            {"topic": "/odom", "publishers": [], "subscribers": []},
            {"topic": "/new_topic", "publishers": [], "subscribers": []}
        ])
        differ = ArchitectureDiff()
        report = differ.diff(arch_a, arch_b)
        assert "/new_topic" in report.added_topics

    def test_removed_services(self):
        arch_a = _make_model(service_connections=[{"service": "/old_srv", "servers": [], "clients": []}])
        arch_b = _make_model(service_connections=[])
        differ = ArchitectureDiff()
        report = differ.diff(arch_a, arch_b)
        assert "/old_srv" in report.removed_services

    def test_subsystem_changes(self):
        arch_a = _make_model(subsystems=[Subsystem(name="Perception", description="x", nodes=["camera"])])
        arch_b = _make_model(subsystems=[
            Subsystem(name="Perception", description="x", nodes=["camera"]),
            Subsystem(name="Navigation", description="y", nodes=["planner"])
        ])
        differ = ArchitectureDiff()
        report = differ.diff(arch_a, arch_b)
        added_names = [sc.subsystem_name for sc in report.subsystem_changes]
        assert "Navigation" in added_names

    def test_total_changes_computed(self):
        arch_a = _make_model(nodes=[_make_node("A"), _make_node("B")])
        arch_b = _make_model(nodes=[_make_node("A"), _make_node("C")])
        differ = ArchitectureDiff()
        report = differ.diff(arch_a, arch_b)
        assert report.total_changes >= 2  # B removed, C added

    def test_summary_not_empty(self):
        arch_a = _make_model(nodes=[_make_node("A")])
        arch_b = _make_model(nodes=[_make_node("B")])
        differ = ArchitectureDiff()
        report = differ.diff(arch_a, arch_b)
        assert len(report.summary) > 0
