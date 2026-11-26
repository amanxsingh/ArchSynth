"""
Comprehensive tests for ArchSynth v2.0 technical improvements:
- Python & C++ functional/standalone node discovery & console_scripts mapping
- Action detection (Python ActionClient/ActionServer, MoveItPy/MTC, YAML controller configs)
- Package dependency graph extraction (package.xml, setup.py, C++ #include, Python import)
- Architecture metrics (N/A cohesion for N<2, internal/external coupling, interface density)
- Lifecycle diagram suppression when no lifecycle entities exist
- Plugin categorization without opaque general_plugin fallback
- Dynamic launch construct tracking (OpaqueFunction, ExecuteProcess)
- Architecture consistency validation (Confirmed, Warning, Unresolved, Potential inconsistency)
- JACO2 case study end-to-end regression
"""

import tempfile
import unittest
from pathlib import Path

from src.architecture_constructor import ArchitectureConstructor
from src.architecture_validator import build_structured_node_inventory, validate_architecture_consistency
from src.build_analyzer import build_package_dependency_graph
from src.interface_extractor import InterfaceExtractor, extract_config_declared_actions
from src.launch_analyzer import PythonLaunchParser
from src.lifecycle_analyzer import LifecycleAnalyzer
from src.main import ArchSynthPipeline
from src.node_analyzer import parse_python_file, run_node_analysis
from src.cpp_analyzer import parse_cpp_file
from src.plugin_analyzer import PluginAnalyzer
from src.schema import (
    ActionInfo,
    CommunicationEdge,
    EntityType,
    EvidenceItem,
    EvidenceType,
    NodeCategory,
    PipelineConfig,
    ROS2Node,
    TopicInfo,
)
from src.subsystem_synthesizer import SubsystemSynthesizer
from src.view_generator import ViewGenerator


class TestArchSynthImprovements(unittest.TestCase):

    def test_python_functional_node_and_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            py_file = Path(tmp) / "action_demo.py"
            py_file.write_text(
                "import rclpy\n"
                "from rclpy.action import ActionClient\n"
                "from control_msgs.action import FollowJointTrajectory\n\n"
                "def main():\n"
                "    node = rclpy.create_node('traj_runner')\n"
                "    client = ActionClient(node, FollowJointTrajectory, '/arm_controller/follow_joint_trajectory')\n",
                encoding="utf-8",
            )
            nodes = parse_python_file(py_file, "demo_pkg")
            self.assertEqual(len(nodes), 1)
            self.assertEqual(nodes[0].node_name, "traj_runner")

    def test_cpp_standalone_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cpp_file = root / "standalone.cpp"
            cpp_file.write_text(
                '#include "rclcpp/rclcpp.hpp"\n'
                "int main(int argc, char** argv) {\n"
                '  auto node = rclcpp::Node::make_shared("standalone_talker");\n'
                "  return 0;\n"
                "}\n",
                encoding="utf-8",
            )
            nodes = parse_cpp_file(cpp_file, root, "demo_cpp_pkg")
            self.assertEqual(len(nodes), 1)
            self.assertEqual(nodes[0].node_name, "standalone_talker")

    def test_package_dependency_graph_and_undeclared_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg_a = root / "pkg_a"
            pkg_b = root / "pkg_b"
            (pkg_a / "pkg_a").mkdir(parents=True)
            (pkg_b / "pkg_b").mkdir(parents=True)

            (pkg_a / "package.xml").write_text(
                "<package format='3'><name>pkg_a</name>"
                "<buildtool_depend>ament_python</buildtool_depend>"
                "<exec_depend>rclpy</exec_depend>"
                "<export><build_type>ament_python</build_type></export></package>",
                encoding="utf-8",
            )
            (pkg_a / "setup.py").write_text(
                "from setuptools import setup\n"
                "setup(name='pkg_a', entry_points={'console_scripts': ['run_a = pkg_a.node_a:main']})\n",
                encoding="utf-8",
            )
            (pkg_a / "pkg_a" / "node_a.py").write_text(
                "import rclpy\nimport pkg_b\nfrom sensor_msgs.msg import JointState\n",
                encoding="utf-8",
            )
            (pkg_b / "package.xml").write_text(
                "<package format='3'><name>pkg_b</name>"
                "<export><build_type>ament_cmake</build_type></export></package>",
                encoding="utf-8",
            )

            pdg = build_package_dependency_graph(root)
            self.assertEqual(sorted(pdg.internal_packages), ["pkg_a", "pkg_b"])
            self.assertTrue(any(e.source_package == "pkg_a" and e.target_package == "pkg_b" and e.origin == "observed_source" for e in pdg.edges))
            self.assertTrue(any(u["target_package"] == "pkg_b" for u in pdg.undeclared_source_dependencies))

    def test_subsystem_metrics_na_and_external_coupling(self):
        n1 = ROS2Node(
            id="pkg_a::NodeOne",
            name="node_one",
            fully_qualified_name="node_one",
            class_name="NodeOne",
            source_file="pkg_a/node_one.py",
            package_name="pkg_a",
            publishers=[TopicInfo(name="/cmd_out", message_type="std_msgs/msg/String")],
            subscribers=[TopicInfo(name="/ext_in", message_type="std_msgs/msg/String")],
            actions=[ActionInfo(name="/follow", action_type="control_msgs/action/FollowJointTrajectory", role="client")],
        )
        synth = SubsystemSynthesizer([n1], communication_edges=[])
        sub_model = synth.recover_subsystems()
        self.assertEqual(len(sub_model.subsystems), 1)
        sub = sub_model.subsystems[0]
        self.assertEqual(sub.cohesion_status, "N/A")
        self.assertEqual(sub.coupling_external, 3.0)
        self.assertEqual(sub.interface_density, 3.0)

    def test_lifecycle_omitted_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            n1 = ROS2Node(
                id="pkg::PlainNode",
                name="plain_node",
                fully_qualified_name="plain_node",
                class_name="PlainNode",
                source_file="plain.py",
                package_name="pkg",
                is_lifecycle=False,
            )
            la = LifecycleAnalyzer(Path(tmp), [n1])
            lg = la.recover_lifecycle_architecture()
            self.assertEqual(lg.lifecycle_managers, [])
            self.assertEqual(lg.standard_transitions, [])
            self.assertEqual(lg.mermaid_diagram, "")

    def test_plugin_categorization_avoids_general_plugin(self):
        pa = PluginAnalyzer(Path("."))
        cat = pa._categorize_plugin("kinematics::KinematicsBase", "MyIKPlugin")
        self.assertEqual(cat, "kinematics_plugin")
        cat2 = pa._categorize_plugin("custom_ns::MyInterface", "Impl")
        self.assertEqual(cat2, "custom_ns_MyInterface")

    def test_launch_tracks_opaque_function(self):
        with tempfile.TemporaryDirectory() as tmp:
            lf_path = Path(tmp) / "dyn.launch.py"
            lf_path.write_text(
                "from launch import LaunchDescription\n"
                "from launch.actions import OpaqueFunction\n"
                "def setup_fn(ctx): return []\n"
                "def generate_launch_description():\n"
                "    return LaunchDescription([OpaqueFunction(function=setup_fn)])\n",
                encoding="utf-8",
            )
            parser = PythonLaunchParser(lf_path, "demo_pkg", Path(tmp))
            lf = parser.parse()
            self.assertTrue(any("OpaqueFunction" in u for u in lf.unresolved_expressions))

    def test_yaml_controller_action_extraction_and_jaco2_regression(self):
        jaco_path = Path("case_studies/jaco2_sim_devkit")
        if not jaco_path.exists():
            self.skipTest("JACO2 case study not present on disk")

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "jaco2_test_out"
            cfg = PipelineConfig(
                repo_path=str(jaco_path),
                output_dir=str(out_dir),
                validate_evidence=True,
                generate_markdown=True,
            )
            pipeline = ArchSynthPipeline(cfg)
            readme_path = pipeline.run()
            self.assertTrue(readme_path.exists())

            import json
            arch = json.loads((out_dir / "architecture.json").read_text(encoding="utf-8"))
            # 1. Discovered functional MTC nodes (mtc_pickplace, mtc_cartesian) in addition to class-based nodes
            self.assertGreaterEqual(len(arch["nodes"]), 11)
            # 2. Structured inventory classifies external launch executables (move_group, rviz2, ros2_control_node, etc.)
            inv = arch["structured_node_inventory"]
            ext_items = [i for i in inv if i["classification"] == "external_ros_node"]
            self.assertGreaterEqual(len(ext_items), 5)
            # 3. Action connections recovered (FollowJointTrajectory from moveit_controllers/ros2_controllers & MoveItPy/MTC)
            self.assertGreater(len(arch["action_connections"]), 0)
            # 4. Package dependency graph has edges
            pdg = arch["package_dependency_graph"]
            self.assertGreater(len(pdg["edges"]), 0)
            # 5. Lifecycle view does NOT emit generic state machine
            lc_view = arch["architecture_views"]["views"]["lifecycle_architecture"]
            self.assertNotIn("stateDiagram-v2", lc_view["mermaid_diagram"])
            self.assertIn("NoLifecycle", lc_view["mermaid_diagram"])
            # 6. Subsystem metrics report N/A for 1-node subsystems and non-zero external coupling
            subs = arch["subsystems"]
            self.assertTrue(any(s["cohesion_status"] == "N/A" for s in subs))
            self.assertTrue(any(s["coupling_external"] > 0 for s in subs))
            # 7. Validation findings produced
            self.assertGreater(len(arch["architecture_validation"]["findings"]), 0)

    def test_false_positive_moveit_execute_prevented(self):
        """Importing MoveIt and calling execute() on an unrelated object must NOT infer FollowJointTrajectory."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            py_file = root / "non_moveit_exec.py"
            py_file.write_text(
                "from rclpy.node import Node\n"
                "from moveit.planning import MoveItPy\n\n"
                "class CustomNode(Node):\n"
                "    def __init__(self):\n"
                "        super().__init__('custom_node')\n"
                "        self.db_cursor = object()\n"
                "        self.db_cursor.execute('SELECT 1')\n",
                encoding="utf-8",
            )
            node = ROS2Node(
                id="pkg::CustomNode",
                name="custom_node",
                fully_qualified_name="custom_node",
                class_name="CustomNode",
                source_file="non_moveit_exec.py",
                package_name="pkg",
                source_language="python",
            )
            extractor = InterfaceExtractor(root)
            decls = extractor.extract_from_python_node(node)
            self.assertEqual(len(decls), 0)

    def test_bounded_cohesion_with_multiple_edges_between_same_nodes(self):
        """Multiple topics between A->B must deduplicate directed pairs so cohesion <= 1.0."""
        n_a = ROS2Node(id="pkg::A", name="a", fully_qualified_name="a", class_name="A", source_file="a.py", package_name="pkg")
        n_b = ROS2Node(id="pkg::B", name="b", fully_qualified_name="b", class_name="B", source_file="b.py", package_name="pkg")
        edges = [
            CommunicationEdge(edge_id=f"e{i}", graph_level="source_potential", communication_type="topic", interface_name=f"/t{i}", message_type="std_msgs/msg/String", source_node_id="pkg::A", target_node_id="pkg::B")
            for i in range(5)
        ]
        synth = SubsystemSynthesizer([n_a, n_b], communication_edges=edges)
        sub_model = synth.recover_subsystems()
        sub = sub_model.subsystems[0]
        # 1 directed pair (A->B) out of 2*(2-1)=2 ordered pairs => 0.5, NOT 2.5!
        self.assertEqual(sub.intra_cohesion_score, 0.5)
        self.assertLessEqual(sub.intra_cohesion_score, 1.0)

    def test_unresolved_external_library_not_flagged_as_missing_ros_pkg(self):
        """Third-party libraries like numpy/curses should be unresolved_external_library, not missing ROS deps."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "my_pkg"
            (pkg / "my_pkg").mkdir(parents=True)
            (pkg / "package.xml").write_text("<package format='3'><name>my_pkg</name><exec_depend>rclpy</exec_depend></package>", encoding="utf-8")
            (pkg / "my_pkg" / "app.py").write_text("import rclpy\nimport numpy\nimport scipy\n", encoding="utf-8")
            pdg = build_package_dependency_graph(root)
            cats = {e.target_package: e.resolution_category for e in pdg.edges}
            self.assertEqual(cats.get("numpy"), "unresolved_external_library")
            self.assertEqual(cats.get("scipy"), "unresolved_external_library")
            self.assertEqual(len(pdg.undeclared_source_dependencies), 0)

    def test_launch_group_namespace_scoping_does_not_leak(self):
        """PushROSNamespace inside GroupAction must not leak to sibling Nodes outside the group."""
        with tempfile.TemporaryDirectory() as tmp:
            lf_path = Path(tmp) / "scoped.launch.py"
            lf_path.write_text(
                "from launch import LaunchDescription\n"
                "from launch.actions import GroupAction\n"
                "from launch_ros.actions import Node, PushROSNamespace\n"
                "def generate_launch_description():\n"
                "    grp = GroupAction([PushROSNamespace('arm'), Node(package='p', executable='e1', name='n1')])\n"
                "    sibling = Node(package='p', executable='e2', name='n2')\n"
                "    return LaunchDescription([grp, sibling])\n",
                encoding="utf-8",
            )
            parser = PythonLaunchParser(lf_path, "p", Path(tmp))
            lf = parser.parse()
            ns_by_name = {n.node_name: n.namespace for n in lf.nodes}
            self.assertEqual(ns_by_name.get("n1"), "arm")
            self.assertEqual(ns_by_name.get("n2"), "")

    def test_architecture_validator_detects_missing_evidence_and_duplicates(self):
        from src.schema import ArchitectureModel
        n1 = ROS2Node(id="pkg::Dup", name="dup", fully_qualified_name="dup", class_name="Dup", source_file="a.py", package_name="pkg", evidence=[])
        n2 = ROS2Node(id="pkg::Dup", name="dup", fully_qualified_name="dup", class_name="Dup", source_file="a.py", package_name="pkg", evidence=[])
        model = ArchitectureModel(repo_name="test", repo_url="u", commit_hash="c", analysis_timestamp="t", nodes=[n1, n2])
        rep = validate_architecture_consistency(model)
        cats = {f.category for f in rep.findings}
        self.assertIn("duplicate_node_identity", cats)
        self.assertIn("missing_evidence", cats)


if __name__ == "__main__":
    unittest.main()
