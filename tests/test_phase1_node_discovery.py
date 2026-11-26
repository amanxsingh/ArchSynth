"""
Unit tests for ArchSynth Phase 1 Node Discovery.
Verifies:
1. Production Nav2 C++ node discovery (ControllerServer, PlannerServer, AmclNode, BtNavigator).
2. Correct Python node discovery without duplicate insertion.
3. BasicNavigator classification as client_app / client.
4. Test-node classification for integration tests.
5. Unique IDs for duplicate class names across different files.
6. Correct source evidence with exact file:line citations.
7. Executable-to-implementation mapping via CMakeLists analysis.
8. Component registration detection via macro and CMake.
9. No empty or fabricated node identities.
"""

import unittest
from pathlib import Path
import json

from src.schema import (
    ROS2Node, EntityType, NodeCategory, ResolutionStatus, EvidenceType
)
from src.build_analyzer import analyze_package_cmake, PackageCMakeInfo
from src.cpp_analyzer import analyze_cpp_package, parse_cpp_file, _mask_comments
from src.node_analyzer import (
    parse_python_file, run_node_analysis, ROS2NodeVisitor
)


class TestPythonNodeDiscovery(unittest.TestCase):
    """Tests for Python node discovery and fixes"""

    def setUp(self):
        self.repo_root = Path("case_studies/nav2")

    def test_no_duplicate_node_insertion(self):
        """Verify visitor does not insert duplicate node instances"""
        robot_nav_file = self.repo_root / "nav2_simple_commander/nav2_simple_commander/robot_navigator.py"
        if not robot_nav_file.exists():
            self.skipTest("Nav2 repo not available")

        nodes = parse_python_file(robot_nav_file, "nav2_simple_commander")
        # In robot_navigator.py, only BasicNavigator inherits from Node
        class_names = [n.class_name for n in nodes]
        self.assertEqual(class_names.count("BasicNavigator"), 1, "BasicNavigator should appear exactly once")

    def test_basic_navigator_name_and_evidence(self):
        """Verify BasicNavigator node_name is extracted from __init__ and line evidence is populated"""
        robot_nav_file = self.repo_root / "nav2_simple_commander/nav2_simple_commander/robot_navigator.py"
        if not robot_nav_file.exists():
            self.skipTest("Nav2 repo not available")

        nodes = parse_python_file(robot_nav_file, "nav2_simple_commander")
        self.assertTrue(len(nodes) >= 1)
        bnav = nodes[0]
        self.assertEqual(bnav.class_name, "BasicNavigator")
        self.assertEqual(bnav.node_name, "basic_navigator", "Node name should be extracted from __init__ default")
        self.assertIsNotNone(bnav.definition_line, "Definition line must be recorded")
        self.assertGreater(bnav.definition_line, 0)

    def test_python_test_node_classification(self):
        """Verify test nodes from nav2_system_tests are detected as test nodes"""
        test_file = self.repo_root / "nav2_system_tests/src/behaviors/backup/backup_tester.py"
        if not test_file.exists():
            self.skipTest("Nav2 repo not available")

        nodes = parse_python_file(test_file, "nav2_system_tests")
        self.assertTrue(len(nodes) >= 1)
        backup_node = nodes[0]
        self.assertEqual(backup_node.class_name, "BackupTest")
        self.assertEqual(backup_node.node_name, "backup_tester")


class TestCppNodeDiscovery(unittest.TestCase):
    """Tests for C++ node discovery and classification"""

    def setUp(self):
        self.repo_root = Path("case_studies/nav2")

    def test_mask_comments_preserves_lines(self):
        """Verify _mask_comments strips text while maintaining line count"""
        content = "Line 1\n/* Comment\nline 2 */\nLine 3 // inline comment\nLine 4"
        clean = _mask_comments(content)
        self.assertEqual(clean.count('\n'), content.count('\n'), "Line count must be identical")
        self.assertNotIn("Comment", clean)
        self.assertNotIn("inline comment", clean)
        self.assertIn("Line 1", clean)
        self.assertIn("Line 3", clean)
        self.assertIn("Line 4", clean)

    def test_controller_server_discovery(self):
        """Verify ControllerServer discovery: lifecycle, node_name, component"""
        pkg_path = self.repo_root / "nav2_controller"
        if not pkg_path.exists():
            self.skipTest("Nav2 repo not available")

        nodes = analyze_cpp_package(pkg_path, self.repo_root, "nav2_controller")
        cs_nodes = [n for n in nodes if n.class_name == "ControllerServer" or n.fully_qualified_class.endswith("::ControllerServer")]
        self.assertEqual(len(cs_nodes), 1, "ControllerServer should be discovered once")

        cs = cs_nodes[0]
        self.assertEqual(cs.node_name, "controller_server")
        self.assertTrue(cs.is_lifecycle)
        self.assertTrue(cs.is_component)
        self.assertFalse(cs.is_test)
        self.assertTrue(any(ev.evidence_type == EvidenceType.COMPONENT_REGISTRATION for ev in cs.evidence))

    def test_planner_server_discovery(self):
        """Verify PlannerServer discovery"""
        pkg_path = self.repo_root / "nav2_planner"
        if not pkg_path.exists():
            self.skipTest("Nav2 repo not available")

        nodes = analyze_cpp_package(pkg_path, self.repo_root, "nav2_planner")
        ps_nodes = [n for n in nodes if "PlannerServer" in n.class_name]
        self.assertEqual(len(ps_nodes), 1)
        ps = ps_nodes[0]
        self.assertEqual(ps.node_name, "planner_server")
        self.assertTrue(ps.is_lifecycle)
        self.assertTrue(ps.is_component)

    def test_amcl_node_discovery(self):
        """Verify AmclNode discovery"""
        pkg_path = self.repo_root / "nav2_amcl"
        if not pkg_path.exists():
            self.skipTest("Nav2 repo not available")

        nodes = analyze_cpp_package(pkg_path, self.repo_root, "nav2_amcl")
        amcl_nodes = [n for n in nodes if "AmclNode" in n.class_name]
        self.assertEqual(len(amcl_nodes), 1)
        amcl = amcl_nodes[0]
        self.assertEqual(amcl.node_name, "amcl")
        self.assertTrue(amcl.is_lifecycle)
        self.assertTrue(amcl.is_component)

    def test_bt_plugins_not_counted_as_ros_nodes(self):
        """Verify BehaviorTree.CPP action/condition/service nodes are not counted as ROS2 nodes"""
        pkg_path = self.repo_root / "nav2_behavior_tree"
        if not pkg_path.exists():
            self.skipTest("Nav2 repo not available")

        nodes = analyze_cpp_package(pkg_path, self.repo_root, "nav2_behavior_tree")
        # Should not find BtServiceNode or ClearCostmapService as standalone ROS2 nodes
        bt_plugin_nodes = [n for n in nodes if "CostmapService" in n.class_name or "BtServiceNode" in n.class_name]
        self.assertEqual(len(bt_plugin_nodes), 0, "BehaviorTree.CPP plugins must not be counted as ROS2 nodes")


class TestBuildAnalyzer(unittest.TestCase):
    """Tests for CMakeLists build analysis"""

    def setUp(self):
        self.repo_root = Path("case_studies/nav2")

    def test_controller_cmake_analysis(self):
        """Verify CMakeLists parsing for nav2_controller"""
        pkg_path = self.repo_root / "nav2_controller"
        if not pkg_path.exists():
            self.skipTest("Nav2 repo not available")

        info = analyze_package_cmake(pkg_path, "nav2_controller")
        self.assertIn("controller_server", info.executables)
        self.assertFalse(info.executables["controller_server"].is_test)

        # Check component registration
        comp_classes = [c.class_name for c in info.components]
        self.assertIn("nav2_controller::ControllerServer", comp_classes)

        # Check executable mapping
        ex = info.find_executable_for_source_or_class(
            "nav2_controller/src/controller_server.cpp",
            "ControllerServer",
            "nav2_controller::ControllerServer"
        )
        self.assertIsNotNone(ex)
        self.assertEqual(ex.name, "controller_server")


class TestNodeInventoryResolution(unittest.TestCase):
    """End-to-end node inventory resolution and serialization tests"""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path("case_studies/nav2")
        cls.output_path = Path("output/test_phase1_inventory.json")
        if cls.repo_root.exists():
            cls.nodes = run_node_analysis(cls.repo_root, cls.output_path)
        else:
            cls.nodes = []

    def test_production_nodes_discovered(self):
        """Verify core production Nav2 nodes exist in final output"""
        if not self.nodes:
            self.skipTest("Nav2 repo not available")

        prod_names = {n.name for n in self.nodes if not n.is_test and n.name}
        expected = {
            "controller_server", "planner_server", "bt_navigator",
            "amcl", "map_server", "lifecycle_manager", "behavior_server",
            "basic_navigator", "collision_monitor", "velocity_smoother"
        }
        for exp in expected:
            self.assertIn(exp, prod_names, f"Expected production node '{exp}' was not found in inventory")

    def test_basic_navigator_classification(self):
        """Verify BasicNavigator is classified as client_app with client role"""
        if not self.nodes:
            self.skipTest("Nav2 repo not available")

        bnav_nodes = [n for n in self.nodes if n.class_name == "BasicNavigator"]
        self.assertEqual(len(bnav_nodes), 1)
        bnav = bnav_nodes[0]
        self.assertEqual(bnav.entity_type, EntityType.CLIENT_APP)
        self.assertEqual(bnav.node_category, NodeCategory.CLIENT)
        self.assertFalse(bnav.is_test)
        self.assertEqual(bnav.name, "basic_navigator")

    def test_test_nodes_classified(self):
        """Verify test nodes have is_test=True and TEST_NODE entity type"""
        if not self.nodes:
            self.skipTest("Nav2 repo not available")

        test_nodes = [n for n in self.nodes if n.package_name == "nav2_system_tests"]
        self.assertGreater(len(test_nodes), 0)
        for tn in test_nodes:
            self.assertTrue(tn.is_test, f"Node {tn.id} must have is_test=True")
            self.assertEqual(tn.entity_type, EntityType.TEST_NODE)

    def test_duplicate_class_disambiguation(self):
        """Verify duplicate class names across different files get distinct stable IDs"""
        if not self.nodes:
            self.skipTest("Nav2 repo not available")

        nav_testers = [n for n in self.nodes if "NavTester" in n.class_name]
        self.assertGreater(len(nav_testers), 1, "There should be multiple NavTester classes in system tests")
        ids = [n.id for n in nav_testers]
        # Verify all IDs are unique
        self.assertEqual(len(ids), len(set(ids)), f"Duplicate IDs detected among NavTester instances: {ids}")
        for nid in ids:
            self.assertIn("#", nid, "Disambiguated ID must contain '#' qualifier")

    def test_canonical_ids_no_duplicate_package(self):
        """Verify IDs do not have duplicate package prefix e.g. nav2_amcl::nav2_amcl::AmclNode"""
        if not self.nodes:
            self.skipTest("Nav2 repo not available")

        for n in self.nodes:
            self.assertNotIn("::nav2_", n.id[n.id.find("::") + 2:], f"Malformed duplicate package ID: {n.id}")

    def test_evidence_coverage_in_serialized_json(self):
        """Verify serialized JSON has valid evidence items for all nodes"""
        self.assertTrue(self.output_path.exists())
        with open(self.output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertGreater(len(data), 0)
        for item in data:
            self.assertTrue(item.get("id"), f"Node missing ID: {item}")
            self.assertNotEqual(item.get("id"), "unnamed")
            self.assertGreater(len(item.get("evidence", [])), 0, f"Node {item['id']} has no evidence")
            ev = item["evidence"][0]
            self.assertTrue(ev.get("file"), f"Evidence missing file in {item['id']}")
            self.assertIsNotNone(ev.get("line_start"), f"Evidence missing line_start in {item['id']}")


if __name__ == "__main__":
    unittest.main()

