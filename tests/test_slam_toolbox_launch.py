"""
ArchSynth Step 2 Unit & Regression Tests:
SLAM Toolbox ROS 2 Launch Analysis Correction

Tests:
  1. Direct LifecycleNode declaration.
  2. LifecycleNode with positional arguments.
  3. LifecycleNode with keyword arguments.
  4. LifecycleNode with LaunchConfiguration substitutions.
  5. LifecycleNode with parameter files.
  6. LifecycleNode with namespace and remappings.
  7. LifecycleNode with conditional execution.
  8. LifecycleNode inside GroupAction.
  9. LifecycleNode inside an included launch description.
  10. Node and LifecycleNode distinction.
  11. ComposableNode declaration.
  12. Unresolved dynamic launch expression.
  13. No arbitrary launch Python execution.
  14. No synthetic node insertion into source inventory.
  15. Real SLAM Toolbox analysis across all seven launch files.
  16. CMake installation distinction (lifelong_launch.py excluded).
  17. Alternative deployment profiles kept separate.
"""

import ast
import json
import tempfile
import unittest
from pathlib import Path

from src.architecture_constructor import ArchitectureConstructor
from src.launch_analyzer import (
    LaunchContext, NodeLaunchMapper, PythonLaunchParser,
    RecursiveLaunchResolver, StaticLaunchEvaluator,
    analyze_package_launches, check_launch_cmake_installed,
    parse_python_launch_file, run_phase2_launch_pipeline
)
from src.schema import (
    EntityType, EvidenceItem, EvidenceType, LaunchContainer, LaunchFile,
    LaunchInstance, LaunchMappingStatus, LaunchNode, ResolutionStatus, ROS2Node
)


class TestSlamToolboxLaunchAnalysis(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.temp_dir.name)
        self.pkg_dir = self.repo_dir / "my_pkg"
        self.launch_dir = self.pkg_dir / "launch"
        self.launch_dir.mkdir(parents=True, exist_ok=True)
        self.packages_map = {"my_pkg": "my_pkg"}

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_req1_direct_lifecycle_node_declaration(self):
        """Req 1: Direct LifecycleNode declaration extraction with correct action_type and is_lifecycle"""
        code = '''
from launch import LaunchDescription
from launch_ros.actions import LifecycleNode

def generate_launch_description():
    node = LifecycleNode(
        package='my_pkg',
        executable='my_lifecycle_exec',
        name='my_lifecycle_node',
        output='screen'
    )
    return LaunchDescription([node])
'''
        lf_path = self.launch_dir / "lifecycle_direct.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.instances), 1)
        inst = lfile.instances[0]
        self.assertEqual(inst.action_type, "LifecycleNode")
        self.assertTrue(inst.is_lifecycle)
        self.assertEqual(inst.node_name, "my_lifecycle_node")
        self.assertEqual(inst.package, "my_pkg")
        self.assertEqual(inst.executable, "my_lifecycle_exec")
        self.assertIn("lifecycle_direct.launch.py::my_lifecycle_node", inst.instance_id)

        # Check evidence citation
        self.assertTrue(len(inst.evidence) >= 1)
        self.assertIn("LifecycleNode declared in launch", inst.evidence[0].explanation)

    def test_req2_lifecycle_node_positional_arguments(self):
        """Req 2: LifecycleNode declared with positional arguments"""
        code = '''
from launch import LaunchDescription
from launch_ros.actions import LifecycleNode

def generate_launch_description():
    # Positional: package, executable, name, namespace
    return LaunchDescription([
        LifecycleNode('my_pkg', 'pos_exec', 'pos_node', 'pos_ns')
    ])
'''
        lf_path = self.launch_dir / "lifecycle_positional.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.instances), 1)
        inst = lfile.instances[0]
        self.assertEqual(inst.package, "my_pkg")
        self.assertEqual(inst.executable, "pos_exec")
        self.assertEqual(inst.node_name, "pos_node")
        self.assertEqual(inst.namespace, "pos_ns")
        self.assertTrue(inst.is_lifecycle)
        self.assertEqual(inst.action_type, "LifecycleNode")

    def test_req3_lifecycle_node_keyword_arguments(self):
        """Req 3: LifecycleNode declared with keyword arguments in non-standard order"""
        code = '''
from launch import LaunchDescription
from launch_ros.actions import LifecycleNode

def generate_launch_description():
    return LaunchDescription([
        LifecycleNode(
            namespace='custom_ns',
            name='kw_node',
            executable='kw_exec',
            package='my_pkg',
            output='screen'
        )
    ])
'''
        lf_path = self.launch_dir / "lifecycle_keywords.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.instances), 1)
        inst = lfile.instances[0]
        self.assertEqual(inst.package, "my_pkg")
        self.assertEqual(inst.executable, "kw_exec")
        self.assertEqual(inst.node_name, "kw_node")
        self.assertEqual(inst.namespace, "custom_ns")
        self.assertTrue(inst.is_lifecycle)

    def test_req4_lifecycle_node_launch_configuration_substitutions(self):
        """Req 4: LifecycleNode with LaunchConfiguration substitutions in parameters and arguments"""
        code = '''
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    declare_arg = DeclareLaunchArgument('use_sim_time', default_value='true')

    node = LifecycleNode(
        package='my_pkg',
        executable='subst_exec',
        name='subst_node',
        parameters=[{'use_sim_time': use_sim_time}]
    )
    return LaunchDescription([declare_arg, node])
'''
        lf_path = self.launch_dir / "lifecycle_subst.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.instances), 1)
        inst = lfile.instances[0]
        self.assertEqual(inst.inline_parameters.get("use_sim_time"), "${use_sim_time}")
        self.assertIn("use_sim_time", lfile.arguments)
        self.assertEqual(lfile.arguments["use_sim_time"]["default"], "true")

    def test_req5_lifecycle_node_parameter_files(self):
        """Req 5: LifecycleNode with ParameterFile description and inline parameters separated"""
        code = '''
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode
from launch_ros.descriptions import ParameterFile

def generate_launch_description():
    params_file = LaunchConfiguration('params_file')
    node = LifecycleNode(
        package='my_pkg',
        executable='params_exec',
        name='params_node',
        parameters=[
            ParameterFile(params_file, allow_substs=True),
            {'autostart': True, 'rate': 20.0}
        ]
    )
    return LaunchDescription([node])
'''
        lf_path = self.launch_dir / "lifecycle_params.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.instances), 1)
        inst = lfile.instances[0]
        self.assertIn("${params_file}", inst.parameter_files)
        self.assertEqual(inst.inline_parameters.get("autostart"), True)
        self.assertEqual(inst.inline_parameters.get("rate"), 20.0)

    def test_req6_lifecycle_node_namespace_and_remappings(self):
        """Req 6: LifecycleNode with namespace and topic remapping rules"""
        code = '''
from launch import LaunchDescription
from launch_ros.actions import LifecycleNode

def generate_launch_description():
    remappings = [('/scan', 'scan_filtered'), ('/tf', 'tf')]
    node = LifecycleNode(
        package='my_pkg',
        executable='remap_exec',
        name='remap_node',
        namespace='robot1',
        remappings=remappings
    )
    return LaunchDescription([node])
'''
        lf_path = self.launch_dir / "lifecycle_remap.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.instances), 1)
        inst = lfile.instances[0]
        self.assertEqual(inst.namespace, "robot1")
        self.assertEqual(inst.remappings.get("/scan"), "scan_filtered")
        self.assertEqual(inst.remappings.get("/tf"), "tf")

    def test_req7_lifecycle_node_conditional_execution(self):
        """Req 7: LifecycleNode with conditional execution expression"""
        code = '''
from launch import LaunchDescription
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode

def generate_launch_description():
    enable_node = LaunchConfiguration('enable_node')
    node = LifecycleNode(
        package='my_pkg',
        executable='cond_exec',
        name='cond_node',
        condition=IfCondition(enable_node)
    )
    return LaunchDescription([node])
'''
        lf_path = self.launch_dir / "lifecycle_cond.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.instances), 1)
        inst = lfile.instances[0]
        self.assertIn("IfCondition(${enable_node})", inst.condition)

    def test_req8_lifecycle_node_inside_group_action(self):
        """Req 8: LifecycleNode inside a scoped GroupAction with PushROSNamespace and SetRemap"""
        code = '''
from launch import LaunchDescription
from launch.actions import GroupAction
from launch_ros.actions import PushROSNamespace, SetRemap, LifecycleNode

def generate_launch_description():
    group = GroupAction([
        PushROSNamespace('fleet_robot'),
        SetRemap(src='/odom', dst='/fleet/odom'),
        LifecycleNode(
            package='my_pkg',
            executable='grouped_exec',
            name='grouped_node'
        )
    ])
    return LaunchDescription([group])
'''
        lf_path = self.launch_dir / "lifecycle_group.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.instances), 1)
        inst = lfile.instances[0]
        self.assertEqual(inst.namespace, "fleet_robot")
        self.assertEqual(inst.remappings.get("/odom"), "/fleet/odom")
        self.assertTrue(inst.is_lifecycle)

    def test_req9_lifecycle_node_inside_included_launch(self):
        """Req 9: LifecycleNode inside an included launch description resolved recursively"""
        child_code = '''
from launch import LaunchDescription
from launch_ros.actions import LifecycleNode

def generate_launch_description():
    return LaunchDescription([
        LifecycleNode(
            package='my_pkg',
            executable='child_exec',
            name='child_node'
        )
    ])
'''
        child_path = self.launch_dir / "child.launch.py"
        child_path.write_text(child_code, encoding='utf-8')

        parent_code = f'''
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource('{child_path.as_posix()}'),
            launch_arguments={{'use_sim_time': 'true'}}.items()
        )
    ])
'''
        parent_path = self.launch_dir / "parent.launch.py"
        parent_path.write_text(parent_code, encoding='utf-8')

        parent_lf = parse_python_launch_file(parent_path, "my_pkg", repo_path=self.repo_dir)
        child_lf = parse_python_launch_file(child_path, "my_pkg", repo_path=self.repo_dir)

        resolver = RecursiveLaunchResolver(
            {parent_lf.file_path: parent_lf, child_lf.file_path: child_lf},
            repo_path=self.repo_dir
        )
        resolved_instances = resolver.resolve_all_hierarchies()

        child_instances = [i for i in resolved_instances if i.node_name == "child_node"]
        self.assertEqual(len(child_instances), 1)  # Accurately resolved through hierarchical inclusion
        scoped_child = child_instances[0]
        self.assertTrue(scoped_child.is_lifecycle)
        self.assertEqual(scoped_child.action_type, "LifecycleNode")
        self.assertIn("parent.launch.py->my_pkg/launch/child.launch.py", scoped_child.parent_inclusion_id)

    def test_req10_node_and_lifecycle_node_distinction(self):
        """Req 10: Clear distinction between standard Node and LifecycleNode in the same launch file"""
        code = '''
from launch import LaunchDescription
from launch_ros.actions import Node, LifecycleNode

def generate_launch_description():
    std_node = Node(package='my_pkg', executable='standard_exec', name='std_node')
    lc_node = LifecycleNode(package='my_pkg', executable='lifecycle_exec', name='lc_node')
    return LaunchDescription([std_node, lc_node])
'''
        lf_path = self.launch_dir / "distinction.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.instances), 2)
        std_inst = next(i for i in lfile.instances if i.node_name == "std_node")
        lc_inst = next(i for i in lfile.instances if i.node_name == "lc_node")

        self.assertFalse(std_inst.is_lifecycle)
        self.assertEqual(std_inst.action_type, "Node")
        self.assertIsNone(std_inst.lifecycle_info)

        self.assertTrue(lc_inst.is_lifecycle)
        self.assertEqual(lc_inst.action_type, "LifecycleNode")
        self.assertIsNotNone(lc_inst.lifecycle_info)

    def test_req11_composable_node_declaration(self):
        """Req 11: ComposableNode declaration inside LoadComposableNodes action"""
        code = '''
from launch import LaunchDescription
from launch_ros.actions import Node, LoadComposableNodes
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    container = Node(name='my_container', package='rclcpp_components', executable='component_container')
    loader = LoadComposableNodes(
        target_container='my_container',
        composable_node_descriptions=[
            ComposableNode(package='my_pkg', plugin='my_pkg::ComponentA', name='comp_a')
        ]
    )
    return LaunchDescription([container, loader])
'''
        lf_path = self.launch_dir / "composable_test.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        self.assertEqual(len(lfile.containers), 1)
        self.assertEqual(len(lfile.instances), 1)
        comp = lfile.instances[0]
        self.assertTrue(comp.is_composable)
        self.assertFalse(comp.is_lifecycle)
        self.assertEqual(comp.action_type, "ComposableNode")
        self.assertEqual(comp.plugin_class, "my_pkg::ComponentA")
        self.assertEqual(comp.container_name, "my_container")

    def test_req12_unresolved_dynamic_launch_expression(self):
        """Req 12: Retain unresolved dynamic expressions without execution or throwing errors"""
        evaluator = StaticLaunchEvaluator(repo_path=self.repo_dir, packages_map=self.packages_map)
        expr_ast = ast.parse("int(rate) * 2", mode="eval").body
        res = evaluator.eval_node(expr_ast)
        # Should evaluate safely without executing Python eval
        self.assertIsNotNone(res)

    def test_req13_no_arbitrary_launch_python_execution(self):
        """Req 13: Absolute prohibition against executing arbitrary Python code (no eval / exec)"""
        side_effect_marker = Path(self.temp_dir.name) / "side_effect_should_never_exist.txt"
        code = f'''
import os
from launch import LaunchDescription
from launch_ros.actions import Node

# Malicious or side-effecting code that must NOT run
os.system("touch '{side_effect_marker.as_posix()}'")

def generate_launch_description():
    return LaunchDescription([
        Node(package='my_pkg', executable='safe_exec', name='safe_node')
    ])
'''
        lf_path = self.launch_dir / "malicious_test.launch.py"
        lf_path.write_text(code, encoding='utf-8')

        parser = PythonLaunchParser(lf_path, "my_pkg", repo_path=self.repo_dir, packages_map=self.packages_map)
        lfile = parser.parse()

        # The side effect file must NOT exist
        self.assertFalse(side_effect_marker.exists(), "CRITICAL: Arbitrary Python code was executed!")
        # The AST parser successfully parsed the safe node
        self.assertEqual(len(lfile.instances), 1)
        self.assertEqual(lfile.instances[0].node_name, "safe_node")

    def test_req14_no_synthetic_node_insertion_into_source_inventory(self):
        """Req 14: Never fabricate synthetic nodes in Phase 1 source node catalog"""
        source_nodes = [
            ROS2Node(
                id="my_pkg::RealNode",
                name="real_node",
                fully_qualified_name="real_node",
                class_name="my_pkg::RealNode",
                source_file="my_pkg/src/real_node.cpp",
                package_name="my_pkg",
                executable="real_exec",
                entity_type=EntityType.ROS_NODE
            )
        ]

        lfile = LaunchFile(
            file_path="launch/external.launch.py",
            package_name="my_pkg",
            launch_type="python",
            nodes=[
                LaunchNode(
                    node_name="external_only_node",
                    package="foreign_pkg",
                    executable="foreign_exec",
                    action_type="LifecycleNode",
                    is_lifecycle=True
                )
            ]
        )

        constructor = ArchitectureConstructor()
        model = constructor.construct(source_nodes, [lfile], repo_name="TestRepo")

        # Source inventory must retain exactly 1 node (zero synthetic nodes added)
        self.assertEqual(len(model.nodes), 1)
        self.assertEqual(model.nodes[0].id, "my_pkg::RealNode")

    def test_req15_slam_toolbox_all_seven_launch_files_analyzed(self):
        """Req 15: Verify all 7 SLAM Toolbox launch files on disk produce valid node declarations"""
        slam_repo = Path("case_studies/slam_toolbox")
        if not slam_repo.exists() or not (slam_repo / ".git").exists():
            self.skipTest("case_studies/slam_toolbox/.git not present in slim distribution")

        launches = analyze_package_launches(slam_repo, "slam_toolbox")
        self.assertEqual(len(launches), 7, f"Expected 7 launch files, found {len(launches)}")

        expected_files = {
            "lifelong_launch.py": ("LifecycleNode", "lifelong_slam_toolbox_node", True),
            "localization_launch.py": ("LifecycleNode", "localization_slam_toolbox_node", True),
            "merge_maps_kinematic_launch.py": ("Node", "merge_maps_kinematic", False),
            "offline_launch.py": ("LifecycleNode", "sync_slam_toolbox_node", True),
            "online_async_decentralized_multirobot_launch.py": ("LifecycleNode", "decentralized_multirobot_slam_toolbox_node", True),
            "online_async_launch.py": ("LifecycleNode", "async_slam_toolbox_node", True),
            "online_sync_launch.py": ("LifecycleNode", "sync_slam_toolbox_node", True),
        }

        for lf in launches:
            fname = Path(lf.file_path).name
            self.assertIn(fname, expected_files, f"Unexpected launch file: {fname}")
            exp_action, exp_exec, exp_lifecycle = expected_files[fname]

            self.assertEqual(len(lf.instances), 1, f"Expected 1 instance in {fname}")
            inst = lf.instances[0]
            self.assertEqual(inst.action_type, exp_action, f"Mismatch in {fname} action_type")
            self.assertEqual(inst.executable, exp_exec, f"Mismatch in {fname} executable")
            self.assertEqual(inst.is_lifecycle, exp_lifecycle, f"Mismatch in {fname} is_lifecycle")
            self.assertEqual(inst.node_name, "slam_toolbox")
            self.assertEqual(inst.package, "slam_toolbox")

    def test_req16_slam_toolbox_cmake_installed_distinction(self):
        """Req 16: Verify CMake installation distinction: lifelong_launch.py is excluded"""
        slam_repo = Path("case_studies/slam_toolbox")
        if not slam_repo.exists() or not (slam_repo / ".git").exists():
            self.skipTest("case_studies/slam_toolbox/.git not present in slim distribution")

        launches = analyze_package_launches(slam_repo, "slam_toolbox")
        cmake_installed = {Path(lf.file_path).name: lf.is_cmake_installed for lf in launches}

        # lifelong_launch.py is excluded in CMakeLists.txt line 346
        self.assertFalse(cmake_installed["lifelong_launch.py"])
        # All other 6 launch files are installed
        for fname, installed in cmake_installed.items():
            if fname != "lifelong_launch.py":
                self.assertTrue(installed, f"Expected {fname} to be CMake-installed")

    def test_req17_slam_toolbox_alternative_deployment_profiles_separated(self):
        """Req 17: Alternative launch deployment profiles are kept separate and not treated as simultaneously active"""
        slam_repo = Path("case_studies/slam_toolbox")
        if not slam_repo.exists() or not (slam_repo / ".git").exists():
            self.skipTest("case_studies/slam_toolbox/.git not present in slim distribution")

        with tempfile.TemporaryDirectory() as out_temp:
            all_lfs, instances, mappings, profiles = run_phase2_launch_pipeline(
                repo_path=slam_repo,
                nodes_json_path=Path("output/slam_toolbox_pipeline/nodes.json"),
                output_dir=Path(out_temp)
            )

            profile_names = [p.profile_name for p in profiles]
            # Must contain distinct variant profiles for alternative entry points
            self.assertIn("launch_online_async", profile_names)
            self.assertIn("launch_online_sync", profile_names)
            self.assertIn("launch_localization", profile_names)
            self.assertIn("launch_lifelong", profile_names)
            self.assertIn("launch_offline", profile_names)
            self.assertIn("launch_online_async_decentralized_multirobot", profile_names)
            self.assertIn("launch_merge_maps_kinematic", profile_names)

            # Each variant profile must contain exactly 1 instance, representing mutually exclusive entry points
            for p in profiles:
                if p.profile_name.startswith("launch_"):
                    self.assertEqual(len(p.instance_ids), 1, f"Variant profile {p.profile_name} has multiple instances")

    def test_req18_source_integrity_clean_pinned_commit(self):
        """Req 18: Verify repository working-tree is clean, HEAD commit matches, and line counts match git show HEAD"""
        import subprocess
        slam_repo = Path("case_studies/slam_toolbox")
        if not slam_repo.exists() or not (slam_repo / ".git").exists():
            self.skipTest("case_studies/slam_toolbox/.git not present in slim distribution")

        head_sha = subprocess.check_output(["git", "-C", str(slam_repo), "rev-parse", "HEAD"]).decode().strip()
        self.assertEqual(head_sha, "eee0cd5e4a161bb10f8334b5420c93876b31ca99")

        # Working tree must be clean
        status = subprocess.check_output(["git", "-C", str(slam_repo), "status", "--short"]).decode().strip()
        self.assertEqual(status, "", "Working tree is not clean")

        # Verify line counts of all 7 launch files and CMakeLists.txt against git show HEAD
        test_files = [
            ("CMakeLists.txt", 362),
            ("launch/online_async_launch.py", 96),
            ("launch/online_sync_launch.py", 96),
            ("launch/localization_launch.py", 97),
            ("launch/offline_launch.py", 71),
            ("launch/online_async_decentralized_multirobot_launch.py", 102),
            ("launch/lifelong_launch.py", 96),
            ("launch/merge_maps_kinematic_launch.py", 13),
        ]
        for rel_path, exp_lines in test_files:
            head_content = subprocess.check_output(["git", "-C", str(slam_repo), "show", f"HEAD:{rel_path}"]).decode("utf-8")
            head_lines = len(head_content.splitlines())
            self.assertEqual(head_lines, exp_lines, f"Line count mismatch for HEAD:{rel_path}")

            work_content = (slam_repo / rel_path).read_text(encoding="utf-8")
            work_lines = len(work_content.splitlines())
            self.assertEqual(work_lines, exp_lines, f"Line count mismatch for working tree {rel_path}")

    def test_req19_node_naming_and_namespaces_distinction(self):
        """Req 19: Verify distinction between local node name, namespace, and fully qualified node name"""
        slam_repo = Path("case_studies/slam_toolbox")
        if not slam_repo.exists() or not (slam_repo / ".git").exists():
            self.skipTest("case_studies/slam_toolbox/.git not present in slim distribution")

        launches = analyze_package_launches(slam_repo, "slam_toolbox")
        launch_dict = {Path(lf.file_path).name: lf for lf in launches}

        # 1. Standard launch: namespace='', name='slam_toolbox' -> FQ name: /slam_toolbox
        async_inst = launch_dict["online_async_launch.py"].instances[0]
        self.assertEqual(async_inst.node_name, "slam_toolbox")
        self.assertEqual(async_inst.namespace, "")

        # 2. Multirobot launch: namespace='${namespace}' with default='robot1' -> FQ name: /robot1/slam_toolbox
        multi_lf = launch_dict["online_async_decentralized_multirobot_launch.py"]
        multi_inst = multi_lf.instances[0]
        self.assertEqual(multi_inst.node_name, "slam_toolbox")
        self.assertEqual(multi_inst.namespace, "${namespace}")
        self.assertIn("namespace", multi_lf.arguments)
        self.assertEqual(multi_lf.arguments["namespace"]["default"], "robot1")

        # 3. Kinematic merge launch: name='slam_toolbox' (overriding C++ default 'map_merging')
        merge_inst = launch_dict["merge_maps_kinematic_launch.py"].instances[0]
        self.assertEqual(merge_inst.node_name, "slam_toolbox")
        self.assertEqual(merge_inst.executable, "merge_maps_kinematic")

    def test_req20_source_evidence_git_blob_parity(self):
        """Req 20: Verified evidence files match Git blob at HEAD byte-for-byte (after newline normalization)"""
        import subprocess, hashlib
        slam_repo = Path("case_studies/slam_toolbox")
        if not slam_repo.exists() or not (slam_repo / ".git").exists():
            self.skipTest("case_studies/slam_toolbox/.git not present in slim distribution")

        audited_files = [
            ("CMakeLists.txt", "dfed661df55a846a8e88f9145a6f69c515a69426", 362),
            ("launch/online_async_launch.py", "99f126a65f8cbe506770050ad9e2eaa7284cacb5", 96),
            ("launch/online_sync_launch.py", "f7fdf06e6a84044ff1dd31e4412f4c9486143982", 96),
            ("launch/localization_launch.py", "3407c70fe29c478d058d68b7d9646e60307a6953", 97),
            ("launch/offline_launch.py", "e76dc974d66daba96969393f2f93189406660b45", 71),
            ("launch/online_async_decentralized_multirobot_launch.py", "2607223bda03da91574653322af7e016ec0a5d7f", 102),
            ("launch/lifelong_launch.py", "0e15b03da12f3f1bb5a972f6f101b347c5937f67", 96),
            ("launch/merge_maps_kinematic_launch.py", "325d2a83956ebf744646f382318661c282517d61", 13),
        ]

        for rel_path, exp_blob_sha, exp_lines in audited_files:
            # 1. Verify Git blob SHA
            blob_sha = subprocess.check_output(["git", "-C", str(slam_repo), "rev-parse", f"HEAD:{rel_path}"]).decode().strip()
            self.assertEqual(blob_sha, exp_blob_sha, f"Blob SHA mismatch for {rel_path}")

            # 2. Verify git show HEAD content matches working tree normalized
            head_bytes = subprocess.check_output(["git", "-C", str(slam_repo), "show", f"HEAD:{rel_path}"])
            work_bytes = (slam_repo / rel_path).read_bytes()
            self.assertEqual(
                work_bytes.replace(b"\r\n", b"\n"),
                head_bytes.replace(b"\r\n", b"\n"),
                f"Working tree content does not match Git blob for {rel_path}"
            )
            self.assertEqual(len(head_bytes.splitlines()), exp_lines)

    def test_req21_provenance_and_revision_integrity(self):
        """Req 21: ArtifactProvenance matches verified commit and extracted AST line numbers match Git blob"""
        import subprocess, json
        slam_repo = Path("case_studies/slam_toolbox")
        if not slam_repo.exists() or not (slam_repo / ".git").exists():
            self.skipTest("case_studies/slam_toolbox/.git not present in slim distribution")

        from src.repo_identity import resolve_repository_identity
        repo_info = resolve_repository_identity(slam_repo)
        self.assertEqual(repo_info.commit_sha, "eee0cd5e4a161bb10f8334b5420c93876b31ca99")
        self.assertEqual(repo_info.repo_name, "slam_toolbox")

        # Verify parsed AST start line positions against actual lines in Git blob
        expected_line_ranges = {
            "online_async_launch.py": (47, 60),
            "online_sync_launch.py": (47, 60),
            "localization_launch.py": (48, 61),
            "offline_launch.py": (27, 37),
            "online_async_decentralized_multirobot_launch.py": (51, 65),
            "lifelong_launch.py": (47, 60),
            "merge_maps_kinematic_launch.py": (7, 12),
        }

        parser_results = analyze_package_launches(slam_repo, "slam_toolbox")
        for lf in parser_results:
            fname = Path(lf.file_path).name
            exp_start, exp_end = expected_line_ranges[fname]
            node = lf.nodes[0]
            self.assertEqual(node.line_start, exp_start, f"Line start mismatch for {fname}")

            # Verify that the line at exp_start in HEAD object actually declares Node/LifecycleNode
            head_content = subprocess.check_output(["git", "-C", str(slam_repo), "show", f"HEAD:launch/{fname}"]).decode("utf-8")
            target_line = head_content.splitlines()[exp_start - 1]
            self.assertTrue(
                "LifecycleNode" in target_line or "Node" in target_line,
                f"Line {exp_start} in HEAD:launch/{fname} does not contain Node/LifecycleNode: {target_line}"
            )


if __name__ == '__main__':
    unittest.main()
