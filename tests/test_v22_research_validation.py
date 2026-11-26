"""
ArchSynth v2.2 Research Validation Tests:
  - SLAM Toolbox inappropriate-clustering detection & justification verification
  - Python keyword-argument topic/service extraction
  - C++ shared_from_this() first-argument guard
  - Structured node inventory non-overlapping reconciliation
  - Manually verified JACO2 ground-truth extraction completeness
"""

import json
import tempfile
import unittest
from pathlib import Path

from src.architecture_validator import (
    build_structured_node_inventory,
    compute_inventory_reconciliation,
)
from src.interface_extractor import InterfaceExtractor
from src.main import ArchSynthPipeline
from src.schema import (
    ArchitectureModel,
    LaunchInstance,
    LaunchMappingStatus,
    NodeCategory,
    PipelineConfig,
    PluginArchitectureModel,
    PluginDeclaration,
    ROS2Node,
    ResolutionStatus,
    ServiceInfo,
)
from src.subsystem_synthesizer import SubsystemSynthesizer


class TestV22ResearchValidation(unittest.TestCase):
    def test_slam_toolbox_separates_ui_utility_and_localization(self):
        nodes = [
            ROS2Node(
                id="slam_toolbox::Slamtoolboxplugin",
                name="SlamToolboxPlugin",
                class_name="Slamtoolboxplugin",
                fully_qualified_name="slam_toolbox::Slamtoolboxplugin",
                package_name="slam_toolbox",
                source_file="rviz_plugin/slam_toolbox_rviz_plugin.cpp",
                node_category=NodeCategory.UNKNOWN,
            ),
            ROS2Node(
                id="slam_toolbox::MergeMapsKinematic",
                name="map_merging",
                class_name="MergeMapsKinematic",
                fully_qualified_name="slam_toolbox::MergeMapsKinematic",
                package_name="slam_toolbox",
                source_file="src/merge_maps_kinematic.cpp",
                node_category=NodeCategory.UNKNOWN,
                services=[
                    ServiceInfo(
                        name="slam_toolbox/merge_submaps",
                        service_type="slam_toolbox/srv/MergeMaps",
                        role="server",
                    )
                ],
            ),
            ROS2Node(
                id="slam_toolbox::LocalizationSlamToolbox",
                name="slam_toolbox",
                class_name="LocalizationSlamToolbox",
                fully_qualified_name="slam_toolbox::LocalizationSlamToolbox",
                package_name="slam_toolbox",
                source_file="src/slam_toolbox_localization.cpp",
                node_category=NodeCategory.UNKNOWN,
                component_registered=True,
                services=[
                    ServiceInfo(
                        name="slam_toolbox/clear_localization_buffer",
                        service_type="std_srvs/srv/Empty",
                        role="server",
                    )
                ],
            ),
        ]

        model = SubsystemSynthesizer(nodes, []).recover_subsystems()
        sub_by_node = {
            nid: s.name
            for s in model.subsystems
            for nid in s.nodes
        }
        self.assertEqual(sub_by_node["slam_toolbox::Slamtoolboxplugin"], "visualization_operator_ui")
        self.assertEqual(sub_by_node["slam_toolbox::MergeMapsKinematic"], "map_management_tools")
        self.assertEqual(sub_by_node["slam_toolbox::LocalizationSlamToolbox"], "localization_state_estimation")
        self.assertEqual(len({sub_by_node[n.id] for n in nodes}), 3)
        for nid in sub_by_node:
            self.assertIn(nid, model.node_assignments)
            self.assertTrue(model.node_assignments[nid].get("justification"))

    def test_python_keyword_args_topic_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "pkg" / "node.py"
            src.parent.mkdir(parents=True)
            src.write_text(
                "from rclpy.node import Node\n"
                "from trajectory_msgs.msg import JointTrajectory\n"
                "from sensor_msgs.msg import JointState\n"
                "class Demo(Node):\n"
                "    def __init__(self):\n"
                "        self.p = self.create_publisher(msg_type=JointTrajectory, topic='arm/traj', qos_profile=10)\n"
                "        self.s = self.create_subscription(msg_type=JointState, topic='joint_commands', callback=self.cb, qos_profile=10)\n",
                encoding="utf-8",
            )
            node = ROS2Node(
                id="pkg::Demo",
                name="demo",
                class_name="Demo",
                fully_qualified_name="pkg::Demo",
                package_name="pkg",
                source_file="pkg/node.py",
                source_language="python",
            )
            decls = InterfaceExtractor(root).extract_from_python_node(node)
            names = {d.name_expression for d in decls}
            self.assertIn("arm/traj", names)
            self.assertIn("joint_commands", names)

    def test_cpp_shared_from_this_not_extracted_as_interface_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "pkg" / "mgr.cpp"
            src.parent.mkdir(parents=True)
            src.write_text(
                'manager_srv_ = nav2::interfaces::create_service<ManageLifecycleNodes>(\n'
                '  shared_from_this(),\n'
                '  get_name() + std::string("/manage_nodes"),\n'
                '  std::bind(&LifecycleManager::cb, this));\n'
                'is_active_pub_ = nav2::interfaces::create_publisher<std_msgs::msg::Bool>(\n'
                '  shared_from_this(),\n'
                '  get_name() + std::string("/managed_nodes_activated"),\n'
                '  nav2::qos::LatchedPublisherQoS());\n',
                encoding="utf-8",
            )
            node = ROS2Node(
                id="pkg::LifecycleManager",
                name="lifecycle_manager",
                class_name="LifecycleManager",
                fully_qualified_name="pkg::LifecycleManager",
                package_name="pkg",
                source_file="pkg/mgr.cpp",
                source_language="cpp",
            )
            decls = InterfaceExtractor(root).extract_from_cpp_node(node)
            names = [d.name_expression for d in decls]
            self.assertFalse(any("shared_from_this" in n for n in names), f"Unexpected shared_from_this in {names}")
            self.assertTrue(any("manage_nodes" in n for n in names))
            self.assertTrue(any("managed_nodes_activated" in n for n in names))

    def test_inventory_deduplicates_case_insensitive_plugin_and_internal_launch(self):
        model = ArchitectureModel(
            repo_name="demo",
            repo_url="local",
            commit_hash="0000",
            analysis_timestamp="2026-11-25T00:00:00Z",
            nodes=[
                ROS2Node(
                    id="slam_toolbox::Slamtoolboxplugin",
                    name="SlamToolboxPlugin",
                    class_name="Slamtoolboxplugin",
                    fully_qualified_name="slam_toolbox::Slamtoolboxplugin",
                    package_name="slam_toolbox",
                    source_file="rviz_plugin/slam_toolbox_rviz_plugin.cpp",
                )
            ],
            launch_instances=[
                LaunchInstance(
                    instance_id="inst1",
                    launch_file="launch/demo.launch.py",
                    package="slam_toolbox",
                    executable="helper_exe",
                    node_name="helper_alias",
                    mapping_status=LaunchMappingStatus.UNRESOLVED,
                    resolution_status=ResolutionStatus.RESOLVED,
                ),
                LaunchInstance(
                    instance_id="inst2",
                    launch_file="launch/demo.launch.py",
                    package="robot_state_publisher",
                    executable="robot_state_publisher",
                    node_name="robot_state_publisher",
                    mapping_status=LaunchMappingStatus.EXTERNAL_DEPENDENCY,
                    resolution_status=ResolutionStatus.RESOLVED,
                ),
            ],
            plugin_architecture=PluginArchitectureModel(
                plugins=[
                    PluginDeclaration(
                        plugin_name="slam_toolbox::SlamToolboxPlugin",
                        class_type="slam_toolbox::SlamToolboxPlugin",
                        base_class_type="rviz_common::Panel",
                        package_name="rviz_plugins.xml",
                        manifest_file="rviz_plugins.xml",
                    )
                ]
            ),
        )
        inv = build_structured_node_inventory(model)
        self.assertEqual(len(inv), 3)
        by_id = {x["identifier"]: x for x in inv}
        self.assertEqual(by_id["slam_toolbox::Slamtoolboxplugin"]["linked_plugin_id"], "slam_toolbox::SlamToolboxPlugin")
        self.assertEqual(by_id["inst1"]["classification"], "internal_launch_instance")
        self.assertEqual(by_id["inst2"]["classification"], "external_ros_node")

        rec = compute_inventory_reconciliation(model)
        self.assertEqual(rec["unique_source_nodes"], 1)
        self.assertEqual(rec["unique_components"], 1)
        self.assertEqual(rec["unique_launch_instances"], 2)
        self.assertFalse(rec["runtime_observation_available"])

    def test_jaco2_ground_truth_completeness(self):
        repo = Path("case_studies/jaco2_sim_devkit")
        if not repo.exists():
            self.skipTest("JACO2 case study not present")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "jaco2_v22"
            cfg = PipelineConfig(repo_path=str(repo), output_dir=str(out), skip_llm=True)
            ArchSynthPipeline(cfg).run()
            arch = json.loads((out / "architecture.json").read_text(encoding="utf-8"))
            iface_names = {d["name_expression"] for d in arch.get("interfaces", [])}
            self.assertIn("arm_controller/joint_trajectory", iface_names)
            self.assertIn("gripper_controller/joint_trajectory", iface_names)
            self.assertIn("joint_commands", iface_names)
            self.assertEqual(len(arch.get("nodes", [])), 11)


if __name__ == "__main__":
    unittest.main()
