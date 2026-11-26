"""
ArchSynth Phase 4 Unit Test Suite - Architecture Synthesis and Recovery.

Validates:
1. Subsystem recovery, cohesion/coupling computation, reference hypothesis evaluation.
2. Lifecycle architecture recovery, manager discovery, managed nodes, C++ callbacks.
3. Plugin architecture recovery, category classification, status resolution.
4. Behavior tree recovery, node types, blackboard dataflow, ROS 2 interface bindings.
5. ISO/IEC/IEEE 42010 Architecture Views generation (8 distinct views).
6. Unified ArchitectureModel integration and schema roundtrip.
"""

import json
import unittest
from pathlib import Path

from src.schema import (
    ArchitectureModel, ArchitectureViewsModel, BehaviorTreeCollectionModel,
    CommunicationEdge, CommunicationGraphModel, LifecycleGraphModel,
    PluginArchitectureModel, PluginStatus, ROS2Node, SubsystemModel
)
from src.subsystem_synthesizer import SubsystemSynthesizer, run_subsystem_recovery
from src.lifecycle_analyzer import LifecycleAnalyzer, run_lifecycle_analysis
from src.plugin_analyzer import PluginAnalyzer, run_plugin_analysis
from src.bt_analyzer import BehaviorTreeAnalyzer, run_behavior_tree_analysis
from src.view_generator import ViewGenerator, run_views_generation


class TestPhase4ArchitectureRecovery(unittest.TestCase):
    """Test suite for Phase 4 Architecture Recovery modules."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path("case_studies/nav2")
        cls.output_dir = Path("output/nav2_pipeline")

        # Ensure prerequisite outputs exist
        assert (cls.output_dir / "nodes.json").exists(), "nodes.json must exist"
        assert (cls.output_dir / "communication_graph.json").exists(), "communication_graph.json must exist"

        with open(cls.output_dir / "nodes.json", "r", encoding="utf-8") as f:
            cls.nodes = [ROS2Node.model_validate(n) for n in json.load(f)]

        with open(cls.output_dir / "communication_graph.json", "r", encoding="utf-8") as f:
            cg_data = json.load(f)
            cls.comm_graph = CommunicationGraphModel.model_validate(cg_data)
            cls.edges = cls.comm_graph.source_potential_edges

    def test_subsystem_recovery(self):
        """Test multi-criteria subsystem recovery and reference hypothesis comparison."""
        synthesizer = SubsystemSynthesizer(self.nodes, self.edges)
        sub_model = synthesizer.recover_subsystems()

        self.assertIsInstance(sub_model, SubsystemModel)
        self.assertGreaterEqual(len(sub_model.subsystems), 8)

        sub_names = {s.name for s in sub_model.subsystems}
        # Core functional domains must be represented
        self.assertIn("trajectory_control", sub_names)
        self.assertIn("navigation_orchestration", sub_names)
        self.assertIn("localization_state_estimation", sub_names)
        self.assertIn("perception_costmaps", sub_names)
        self.assertIn("client_autonomy_api", sub_names)
        self.assertIn("validation_test_infrastructure", sub_names)

        # Check client autonomy separation
        client_sub = next(s for s in sub_model.subsystems if s.name == "client_autonomy_api")
        self.assertTrue(client_sub.is_client_application)
        self.assertIn("nav2_simple_commander::BasicNavigator", client_sub.nodes)

        # Check test infrastructure separation
        test_sub = next(s for s in sub_model.subsystems if s.name == "validation_test_infrastructure")
        self.assertTrue(test_sub.is_test_infrastructure)
        self.assertGreater(len(test_sub.nodes), 30)

        # Check reference comparison metrics
        ref_comp = sub_model.reference_comparison
        self.assertIn("mean_jaccard_similarity", ref_comp)
        self.assertGreater(ref_comp["mean_jaccard_similarity"], 0.70)

    def test_lifecycle_architecture_recovery(self):
        """Test lifecycle manager discovery, managed node ordering, and C++ callbacks."""
        analyzer = LifecycleAnalyzer(self.repo_root, self.nodes)
        life_model = analyzer.recover_lifecycle_architecture()

        self.assertIsInstance(life_model, LifecycleGraphModel)
        self.assertGreaterEqual(len(life_model.lifecycle_managers), 2)

        mgr_names = {m.manager_name for m in life_model.lifecycle_managers}
        self.assertIn("lifecycle_manager_navigation", mgr_names)
        self.assertIn("lifecycle_manager_localization", mgr_names)

        # Check managed nodes in navigation manager
        nav_mgr = next(m for m in life_model.lifecycle_managers if m.manager_name == "lifecycle_manager_navigation")
        self.assertIn("controller_server", nav_mgr.managed_node_names)
        self.assertIn("planner_server", nav_mgr.managed_node_names)
        self.assertIn("bt_navigator", nav_mgr.managed_node_names)

        # Check C++ lifecycle callback extraction
        ctrl_node = next((mn for mn in life_model.managed_nodes if mn.launch_name == "controller_server"), None)
        self.assertIsNotNone(ctrl_node)
        self.assertIn("on_configure", ctrl_node.handles_transition_callbacks)
        self.assertIn("on_activate", ctrl_node.handles_transition_callbacks)
        self.assertIn("on_deactivate", ctrl_node.handles_transition_callbacks)

        # Check Mermaid diagram
        self.assertIn("stateDiagram-v2", life_model.mermaid_diagram)
        self.assertIn("Unconfigured", life_model.mermaid_diagram)
        self.assertIn("Active", life_model.mermaid_diagram)

    def test_plugin_architecture_recovery(self):
        """Test plugin manifest discovery, categorization, and selected status in params."""
        analyzer = PluginAnalyzer(self.repo_root)
        plug_model = analyzer.recover_plugin_architecture()

        self.assertIsInstance(plug_model, PluginArchitectureModel)
        self.assertGreater(len(plug_model.plugins), 50)

        categories = set(plug_model.categories.keys())
        self.assertIn("costmap_layer", categories)
        self.assertIn("global_planner", categories)
        self.assertIn("controller", categories)
        self.assertIn("recovery_behavior", categories)

        # Check status resolution
        selected_plugins = [p for p in plug_model.plugins if p.status == PluginStatus.SELECTED]
        self.assertGreater(len(selected_plugins), 10)

        selected_classes = {p.class_type for p in selected_plugins}
        self.assertIn("nav2_mppi_controller::MPPIController", selected_classes)
        self.assertIn("nav2_navfn_planner::NavfnPlanner", selected_classes)
        self.assertIn("nav2_costmap_2d::InflationLayer", selected_classes)

        # Check server configs
        self.assertGreater(len(plug_model.server_configurations), 10)
        self.assertIn("classDiagram", plug_model.mermaid_diagram)

    def test_behavior_tree_recovery(self):
        """Test Behavior Tree XML parsing, blackboard variables, and ROS 2 bindings."""
        analyzer = BehaviorTreeAnalyzer(self.repo_root)
        bt_model = analyzer.recover_behavior_trees()

        self.assertIsInstance(bt_model, BehaviorTreeCollectionModel)
        self.assertGreaterEqual(bt_model.total_trees, 15)
        self.assertGreater(bt_model.total_bt_nodes, 400)
        self.assertEqual(bt_model.host_node_id, "nav2_bt_navigator::BtNavigator")

        # Check blackboard variables
        self.assertIn("path", bt_model.all_blackboard_variables)
        self.assertIn("goal", bt_model.all_blackboard_variables)

        # Check ROS 2 bindings
        action_bindings = {b["bt_node"]: b["target_interface"] for b in bt_model.bt_to_ros2_bindings}
        self.assertIn("ComputePathToPose", action_bindings)
        self.assertEqual(action_bindings["ComputePathToPose"], "/compute_path_to_pose")
        self.assertIn("FollowPath", action_bindings)
        self.assertEqual(action_bindings["FollowPath"], "/follow_path")

    def test_architecture_views_generation(self):
        """Test generation of all 8 ISO/IEC/IEEE 42010 aligned architecture views."""
        views_model = run_views_generation(
            nodes_json_path=self.output_dir / "nodes.json",
            subsystem_json_path=self.output_dir / "subsystem_model.json",
            lifecycle_json_path=self.output_dir / "lifecycle_graph.json",
            plugin_json_path=self.output_dir / "plugin_architecture.json",
            bt_json_path=self.output_dir / "behavior_tree_model.json",
            comm_graph_json_path=self.output_dir / "communication_graph.json"
        )

        self.assertIsInstance(views_model, ArchitectureViewsModel)
        self.assertEqual(len(views_model.views), 8)

        expected_views = [
            "system_context",
            "package_dependency",
            "subsystem_component",
            "runtime_deployment",
            "communication_topology",
            "lifecycle_architecture",
            "plugin_architecture",
            "behavior_tree_orchestration"
        ]
        for vid in expected_views:
            self.assertIn(vid, views_model.views)
            v = views_model.views[vid]
            self.assertTrue(len(v.name) > 0)
            self.assertTrue(len(v.description) > 0)
            self.assertTrue(len(v.mermaid_diagram) > 0)
            self.assertGreater(len(v.architectural_concerns), 0)
            self.assertGreater(len(v.target_stakeholders), 0)

    def test_full_architecture_model_schema_roundtrip(self):
        """Test that the synthesized architecture.json strictly validates against ArchitectureModel."""
        arch_json_path = self.output_dir / "architecture.json"
        self.assertTrue(arch_json_path.exists())

        with open(arch_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        arch_model = ArchitectureModel.model_validate(data)
        self.assertEqual(arch_model.repo_name, "nav2")
        self.assertIsNotNone(arch_model.subsystem_model)
        self.assertIsNotNone(arch_model.lifecycle_graph)
        self.assertIsNotNone(arch_model.plugin_architecture)
        self.assertIsNotNone(arch_model.behavior_tree_model)
        self.assertIsNotNone(arch_model.architecture_views)
        self.assertEqual(len(arch_model.architecture_views.views), 8)


if __name__ == "__main__":
    unittest.main()

