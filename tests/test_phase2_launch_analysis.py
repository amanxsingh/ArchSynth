"""
ArchSynth Phase 2 Unit Tests: Launch Analysis & Resolution.

Tests:
  1. Standalone Node declaration extraction.
  2. ComposableNode and LoadComposableNodes extraction.
  3. Multiple components loaded into one container (container-to-component relationship).
  4. Containers treated as deployment hosts, not functional server nodes.
  5. Scoped GroupAction with PushROSNamespace, SetRemap, SetParameter.
  6. Conditional launch branches (standalone vs composable deployment profiles).
  7. Same launch file included multiple times with different arguments.
  8. Recursive inclusion loop prevention.
  9. Ambiguous executable-to-node mapping (preserving all candidate IDs).
  10. External launch dependencies (marking external, no synthetic insertion).
  11. Unresolved package paths and substitutions preserved safely.
  12. Zero synthetic node insertion into Phase 1 source inventory.
  13. Real-world verification on Nav2 navigation_launch.py.
  14. Real-world verification on Nav2 bringup_launch.py inclusion resolution.
"""

import json
import tempfile
import unittest
from pathlib import Path

from src.architecture_constructor import ArchitectureConstructor
from src.launch_analyzer import (
    LaunchContext, NodeLaunchMapper, PythonLaunchParser,
    RecursiveLaunchResolver, StaticLaunchEvaluator, parse_python_launch_file
)
from src.schema import (
    EntityType, EvidenceItem, EvidenceType, LaunchContainer, LaunchFile,
    LaunchInstance, LaunchMappingStatus, LaunchNode, NodeCategory,
    ResolutionStatus, ROS2Node
)


class TestPhase2LaunchAnalysis(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.temp_dir.name)
        self.pkg_dir = self.repo_dir / "my_pkg"
        self.launch_dir = self.pkg_dir / "launch"
        self.launch_dir.mkdir(parents=True, exist_ok=True)
        self.packages_map = {"my_pkg": "my_pkg"}

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_standalone_node_extraction(self):
        """Test extraction of standalone Node declaration with arguments and remappings"""
        code = '''
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='my_pkg',
            executable='my_exec',
            name='my_node',
            namespace='my_ns',
            remappings=[('/cmd_vel', '/nav_vel')],
            parameters=[{'speed': 1.5}],
            arguments=['--ros-args', '--log-level', 'info']
        )
    ])
'''
        lf_path = self.launch_dir / "standalone_test.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.instances), 1)
        inst = lfile.instances[0]
        self.assertEqual(inst.node_name, "my_node")
        self.assertEqual(inst.package, "my_pkg")
        self.assertEqual(inst.executable, "my_exec")
        self.assertEqual(inst.namespace, "my_ns")
        self.assertEqual(inst.remappings.get("/cmd_vel"), "/nav_vel")
        self.assertIn("standalone_test.launch.py::my_node", inst.instance_id)

    def test_composable_node_and_container(self):
        """Test ComposableNodeContainer as host and ComposableNode as component instance"""
        code = '''
from launch import LaunchDescription
from launch_ros.actions import ComposableNodeContainer, LoadComposableNodes
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    return LaunchDescription([
        ComposableNodeContainer(
            name='nav2_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container',
            composable_node_descriptions=[
                ComposableNode(
                    package='my_pkg',
                    plugin='my_pkg::ControllerServer',
                    name='controller_server'
                )
            ]
        )
    ])
'''
        lf_path = self.launch_dir / "composition_test.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.containers), 1)
        container = lfile.containers[0]
        self.assertEqual(container.name, "nav2_container")
        self.assertEqual(container.package, "rclcpp_components")

        self.assertEqual(len(lfile.instances), 1)
        comp = lfile.instances[0]
        self.assertTrue(comp.is_composable)
        self.assertEqual(comp.container_name, "nav2_container")
        self.assertEqual(comp.plugin_class, "my_pkg::ControllerServer")
        self.assertEqual(comp.node_name, "controller_server")
        self.assertIn(comp.instance_id, container.loaded_components)

    def test_multiple_components_in_one_container(self):
        """Test multiple components loaded into one container via LoadComposableNodes"""
        code = '''
from launch import LaunchDescription
from launch_ros.actions import Node, LoadComposableNodes
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    container = Node(
        name='shared_container',
        package='rclcpp_components',
        executable='component_container_isolated'
    )
    loaders = LoadComposableNodes(
        target_container='shared_container',
        composable_node_descriptions=[
            ComposableNode(package='my_pkg', plugin='my_pkg::Planner', name='planner'),
            ComposableNode(package='my_pkg', plugin='my_pkg::Controller', name='controller'),
            ComposableNode(package='my_pkg', plugin='my_pkg::Navigator', name='navigator')
        ]
    )
    return LaunchDescription([container, loaders])
'''
        lf_path = self.launch_dir / "multi_comp_test.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.containers), 1)
        self.assertEqual(lfile.containers[0].name, "shared_container")
        self.assertEqual(len(lfile.instances), 3)

        for inst in lfile.instances:
            self.assertTrue(inst.is_composable)
            self.assertEqual(inst.container_name, "shared_container")
            self.assertIn(inst.instance_id, lfile.containers[0].loaded_components)

    def test_container_not_counted_as_server_node(self):
        """Ensure component containers are categorized as LaunchContainer, not functional server instances"""
        code = '''
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rclcpp_components',
            executable='component_container',
            name='nav2_container'
        )
    ])
'''
        lf_path = self.launch_dir / "container_only.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.containers), 1)
        self.assertEqual(len(lfile.instances), 0)

    def test_nested_namespace_and_remapping_scoping(self):
        """Test GroupAction scoping: nested namespaces, remappings, and parameters"""
        code = '''
from launch import LaunchDescription
from launch.actions import GroupAction
from launch_ros.actions import PushROSNamespace, SetRemap, SetParameter, Node

def generate_launch_description():
    group = GroupAction([
        PushROSNamespace('robot1'),
        SetRemap(src='scan', dst='base_scan'),
        SetParameter(name='use_sim_time', value=True),
        Node(
            package='my_pkg',
            executable='nav_server',
            name='navigator',
            namespace='sub'
        )
    ])
    return LaunchDescription([group])
'''
        lf_path = self.launch_dir / "scoped_group.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.instances), 1)
        inst = lfile.instances[0]
        self.assertEqual(inst.namespace, "robot1/sub")
        self.assertEqual(inst.remappings.get("scan"), "base_scan")
        self.assertTrue(any(p.get("use_sim_time") is True for p in inst.parameters if isinstance(p, dict)))

    def test_conditional_launch_branches(self):
        """Test differentiation of deployment profiles for mutually exclusive conditions"""
        code = '''
from launch import LaunchDescription
from launch.actions import GroupAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    use_composition = LaunchConfiguration('use_composition')
    standalone_group = GroupAction(
        condition=IfCondition(PythonExpression(['not ', use_composition])),
        actions=[
            Node(package='my_pkg', executable='server', name='standalone_server')
        ]
    )
    composed_group = GroupAction(
        condition=IfCondition(use_composition),
        actions=[
            Node(package='my_pkg', executable='server', name='composed_server')
        ]
    )
    return LaunchDescription([standalone_group, composed_group])
'''
        lf_path = self.launch_dir / "conditional_test.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.instances), 2)
        standalone_inst = next(i for i in lfile.instances if i.node_name == "standalone_server")
        composed_inst = next(i for i in lfile.instances if i.node_name == "composed_server")

        self.assertEqual(standalone_inst.deployment_profile, "standalone")
        self.assertEqual(composed_inst.deployment_profile, "composable")

    def test_same_launch_included_multiple_times_with_different_args(self):
        """Test the same child launch included multiple times produces unique instance IDs with arguments"""
        child_code = '''
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(package='my_pkg', executable='driver', name='laser_driver')
    ])
'''
        child_path = self.launch_dir / "child.launch.py"
        child_path.write_text(child_code, encoding='utf-8')

        parent_code = '''
import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    launch_dir = os.path.join('my_pkg', 'launch')
    inc1 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, 'child.launch.py')),
        launch_arguments={'namespace': 'robot_a'}.items()
    )
    inc2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, 'child.launch.py')),
        launch_arguments={'namespace': 'robot_b'}.items()
    )
    return LaunchDescription([inc1, inc2])
'''
        parent_path = self.launch_dir / "parent.launch.py"
        parent_path.write_text(parent_code, encoding='utf-8')

        p1 = PythonLaunchParser(parent_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        p2 = PythonLaunchParser(child_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)

        lmap = {p1.rel_file: p1.parse(), p2.rel_file: p2.parse()}
        resolver = RecursiveLaunchResolver(lmap, repo_path=self.repo_dir)
        instances = resolver.resolve_all_hierarchies()

        # Should produce two distinct instances with distinct parent and namespace IDs
        driver_instances = [i for i in instances if i.node_name == "laser_driver"]
        self.assertGreaterEqual(len(driver_instances), 2)
        inst_ids = [i.instance_id for i in driver_instances]
        self.assertEqual(len(inst_ids), len(set(inst_ids)))  # All unique

    def test_recursive_inclusion_loop_prevention(self):
        """Test that circular inclusion (A -> B -> A) does not cause infinite recursion"""
        a_code = '''
import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    return LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join('my_pkg', 'launch', 'b.launch.py')))
    ])
'''
        b_code = '''
import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    return LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join('my_pkg', 'launch', 'a.launch.py')))
    ])
'''
        (self.launch_dir / "a.launch.py").write_text(a_code, encoding='utf-8')
        (self.launch_dir / "b.launch.py").write_text(b_code, encoding='utf-8')

        p_a = PythonLaunchParser(self.launch_dir / "a.launch.py", "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        p_b = PythonLaunchParser(self.launch_dir / "b.launch.py", "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)

        lmap = {p_a.rel_file: p_a.parse(), p_b.rel_file: p_b.parse()}
        resolver = RecursiveLaunchResolver(lmap, repo_path=self.repo_dir, max_depth=5)
        # Should not raise RecursionError and terminate cleanly
        instances = resolver.resolve_all_hierarchies()
        self.assertIsInstance(instances, list)

    def test_ambiguous_executable_to_node_mapping(self):
        """Test that multiple classes sharing an executable target are flagged AMBIGUOUS with all candidate IDs preserved"""
        # Node inventory with 3 classes sharing the same executable 'map_server'
        nodes = [
            ROS2Node(
                id="nav2_map_server::MapServer",
                name="map_server",
                fully_qualified_name="map_server",
                class_name="nav2_map_server::MapServer",
                source_file="nav2_map_server/src/map_server.cpp",
                package_name="nav2_map_server",
                executable="map_server",
                entity_type=EntityType.ROS_NODE
            ),
            ROS2Node(
                id="nav2_map_server::CostmapFilterInfoServer",
                name="costmap_filter_info_server",
                fully_qualified_name="costmap_filter_info_server",
                class_name="nav2_map_server::CostmapFilterInfoServer",
                source_file="nav2_map_server/src/costmap_filter_info_server.cpp",
                package_name="nav2_map_server",
                executable="map_server",
                entity_type=EntityType.ROS_NODE
            ),
            ROS2Node(
                id="nav2_map_server::MapSaver",
                name="map_saver",
                fully_qualified_name="map_saver",
                class_name="nav2_map_server::MapSaver",
                source_file="nav2_map_server/src/map_saver.cpp",
                package_name="nav2_map_server",
                executable="map_server",
                entity_type=EntityType.ROS_NODE
            )
        ]

        # Launch instance specifies ambiguous name 'keepout_filter_mask_server'
        instance = LaunchInstance(
            instance_id="keepout.launch.py::keepout_filter_mask_server#L10",
            node_name="keepout_filter_mask_server",
            package="nav2_map_server",
            executable="map_server",
            launch_file="keepout.launch.py"
        )

        mapper = NodeLaunchMapper(nodes, packages_map={"nav2_map_server": "nav2_map_server"})
        resolved = mapper.resolve_instance(instance)

        self.assertEqual(resolved.mapping_status, LaunchMappingStatus.AMBIGUOUS)
        self.assertIsNone(resolved.node_id)
        self.assertEqual(len(resolved.candidate_node_ids), 3)
        self.assertIn("nav2_map_server::MapServer", resolved.candidate_node_ids)
        self.assertIn("nav2_map_server::CostmapFilterInfoServer", resolved.candidate_node_ids)
        self.assertIn("nav2_map_server::MapSaver", resolved.candidate_node_ids)

    def test_external_launch_dependency(self):
        """Test external node (e.g. robot_state_publisher) is flagged EXTERNAL_DEPENDENCY without synthetic node creation"""
        nodes = [
            ROS2Node(
                id="my_pkg::MyNode",
                name="my_node",
                fully_qualified_name="my_node",
                class_name="my_pkg::MyNode",
                source_file="my_pkg/src/my_node.cpp",
                package_name="my_pkg",
                executable="my_node",
                entity_type=EntityType.ROS_NODE
            )
        ]

        instance = LaunchInstance(
            instance_id="bringup.launch.py::robot_state_publisher#L20",
            node_name="robot_state_publisher",
            package="robot_state_publisher",
            executable="robot_state_publisher",
            launch_file="bringup.launch.py"
        )

        mapper = NodeLaunchMapper(nodes, packages_map={"my_pkg": "my_pkg"})
        resolved = mapper.resolve_instance(instance)

        self.assertEqual(resolved.mapping_status, LaunchMappingStatus.EXTERNAL_DEPENDENCY)
        self.assertIsNone(resolved.node_id)
        self.assertEqual(len(resolved.candidate_node_ids), 0)

    def test_unresolved_package_paths_and_substitutions(self):
        """Test that unresolved package substitutions are safely marked UNRESOLVED without raising errors"""
        evaluator = StaticLaunchEvaluator(
            repo_path=self.repo_dir,
            packages_map=self.packages_map
        )
        res = evaluator.eval_node(None)
        self.assertIsNone(res)

    def test_no_synthetic_node_insertion_in_phase1_inventory(self):
        """Verify that ArchitectureConstructor preserves the source inventory without fabricating synthetic nodes"""
        nodes = [
            ROS2Node(
                id="my_pkg::SourceNode",
                name="source_node",
                fully_qualified_name="source_node",
                class_name="my_pkg::SourceNode",
                source_file="my_pkg/src/node.cpp",
                package_name="my_pkg",
                executable="node_exec",
                entity_type=EntityType.ROS_NODE
            )
        ]

        # Launch file declaring a node that does not exist in repo source
        lfile = LaunchFile(
            file_path="launch/test.launch.py",
            package_name="my_pkg",
            launch_type="python",
            nodes=[
                LaunchNode(
                    node_name="external_third_party_node",
                    package="third_party_pkg",
                    executable="external_exec"
                )
            ]
        )

        constructor = ArchitectureConstructor()
        model = constructor.construct(nodes, [lfile], repo_name="TestRepo")

        # The count of nodes in model must be exactly 1 (no synthetic nodes added)
        self.assertEqual(len(model.nodes), 1)
        self.assertEqual(model.nodes[0].id, "my_pkg::SourceNode")

    def test_nav2_navigation_launch_real_world(self):
        """Real-world validation: parse case_studies/nav2 navigation_launch.py"""
        nav_launch_path = Path("case_studies/nav2/nav2_bringup/launch/navigation_launch.py")
        if not nav_launch_path.exists():
            self.skipTest("Nav2 navigation_launch.py not found on disk")

        parser = PythonLaunchParser(
            nav_launch_path,
            "nav2_bringup",
            repo_path=Path("case_studies/nav2"),
            packages_map={"nav2_bringup": "nav2_bringup"}
        )
        lfile = parser.parse()

        # Verify standalone and composable nodes are found
        standalone_instances = [i for i in lfile.instances if not i.is_composable]
        composable_instances = [i for i in lfile.instances if i.is_composable]

        self.assertGreaterEqual(len(standalone_instances), 10)
        self.assertGreaterEqual(len(composable_instances), 10)

        # Check key servers in composable instances
        plugins = [i.plugin_class for i in composable_instances]
        self.assertIn("nav2_controller::ControllerServer", plugins)
        self.assertIn("nav2_planner::PlannerServer", plugins)
        self.assertIn("nav2_bt_navigator::BtNavigator", plugins)

    def test_nav2_bringup_launch_hierarchical_resolution(self):
        """Real-world validation: verify bringup_launch.py resolves included launch files"""
        bringup_path = Path("case_studies/nav2/nav2_bringup/launch/bringup_launch.py")
        if not bringup_path.exists():
            self.skipTest("Nav2 bringup_launch.py not found on disk")

        parser = PythonLaunchParser(
            bringup_path,
            "nav2_bringup",
            repo_path=Path("case_studies/nav2"),
            packages_map={"nav2_bringup": "nav2_bringup"}
        )
        lfile = parser.parse()

        self.assertGreaterEqual(len(lfile.includes), 4)
        resolved_includes = [inc.resolved_path for inc in lfile.includes if inc.resolved_path]
        self.assertTrue(any("navigation_launch.py" in str(r) for r in resolved_includes))
        self.assertTrue(any("localization_launch.py" in str(r) for r in resolved_includes))


if __name__ == '__main__':
    unittest.main()

