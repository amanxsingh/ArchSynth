"""
Regression and Consistency Tests for Nav2 Documentation Accuracy & Evidence Reconciliation
Verifies that all architectural discrepancies reported in the Nav2 audit have been permanently resolved.
"""

import json
import re
import unittest
from pathlib import Path


class TestNav2AccuracyReconciliation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corrected_dir = Path("output/nav2_corrected_pipeline")
        cls.docs_dir = cls.corrected_dir / "docs"
        cls.nodes_dir = cls.docs_dir / "nodes"

        # Load artifacts
        with open(cls.corrected_dir / "architecture.json", encoding="utf-8") as f:
            cls.arch = json.load(f)
        with open(cls.corrected_dir / "nodes.json", encoding="utf-8") as f:
            cls.nodes = json.load(f)
        with open(cls.corrected_dir / "launches.json", encoding="utf-8") as f:
            cls.launches = json.load(f)
        with open(cls.corrected_dir / "interfaces.json", encoding="utf-8") as f:
            cls.interfaces = json.load(f)
        with open(cls.corrected_dir / "lifecycle_graph.json", encoding="utf-8") as f:
            cls.lifecycle = json.load(f)
        with open(cls.corrected_dir / "plugin_architecture.json", encoding="utf-8") as f:
            cls.plugins = json.load(f)
        with open(cls.corrected_dir / "behavior_tree_model.json", encoding="utf-8") as f:
            cls.bt = json.load(f)
        with open(cls.corrected_dir / "consistency_validation_report.json", encoding="utf-8") as f:
            cls.report = json.load(f)
        cls.readme_text = (cls.docs_dir / "README.md").read_text(encoding="utf-8")

    def test_git_provenance_and_pinned_commit(self):
        """Verify repository provenance records the exact 40-character Git SHA and branch main."""
        expected_commit = "6dbf4549ae1914188916b06dcc19dd3a8115d0a5"
        self.assertEqual(self.arch["commit_hash"], expected_commit)
        self.assertEqual(self.arch["branch"], "main")
        self.assertIn("6dbf4549ae1914188916b06dcc19dd3a8115d0a5", self.readme_text)
        self.assertIn("> **Branch**: `main`", self.readme_text)
        self.assertNotIn("> **Commit Hash**: `main`", self.readme_text)
        self.assertNotIn("> **Commit Hash**: `unavailable`", self.readme_text)

    def test_node_inventory_and_unique_identity(self):
        """Verify all 66 nodes have unique stable IDs and unique documentation files."""
        self.assertEqual(len(self.nodes), 66)
        node_ids = [n["id"] for n in self.nodes]
        self.assertEqual(len(node_ids), len(set(node_ids)), "Duplicate node IDs detected in nodes.json")

        # Verify documentation files on disk
        doc_files = list(self.nodes_dir.glob("*.md"))
        self.assertEqual(len(doc_files), 66, "Exactly 66 node documentation files must exist on disk")

    def test_node_documentation_links_resolution(self):
        """Verify every node link in README.md resolves to an existing documentation file on disk."""
        linked_files = re.findall(r"nodes/([a-zA-Z0-9_\-\.]+)\.md", self.readme_text)
        self.assertGreaterEqual(len(linked_files), 66)
        for link in set(linked_files):
            file_path = self.nodes_dir / f"{link}.md"
            self.assertTrue(file_path.exists(), f"Broken link in README.md to {file_path}")

    def test_node_classification_breakdown(self):
        """Verify the 66 nodes are explicitly classified into production, client, helper, and test."""
        classifications = [n.get("classification_label") for n in self.nodes]
        counts = {c: classifications.count(c) for c in set(classifications)}

        self.assertEqual(counts.get("Production ROS 2 Node"), 20)
        self.assertEqual(counts.get("Client/Library Component"), 1)
        self.assertEqual(counts.get("Helper Component"), 1)
        self.assertEqual(counts.get("Test Harness"), 12)
        self.assertEqual(counts.get("Test Node"), 32)
        self.assertEqual(sum(counts.values()), 66)

    def test_line_range_validity_no_none(self):
        """Verify zero evidence items or documentation files contain invalid '57–None' ranges."""
        self.assertNotIn("–None", self.readme_text)
        self.assertNotIn("-None", self.readme_text)
        self.assertNotIn(":None", self.readme_text)

        for doc in self.nodes_dir.glob("*.md"):
            content = doc.read_text(encoding="utf-8")
            self.assertNotIn("–None", content, f"Invalid line range in {doc.name}")
            self.assertNotIn("-None", content, f"Invalid line range in {doc.name}")

    def test_launch_inventory_and_classification(self):
        """Verify all 41 launch files are classified and substitution utilities are marked non-runnable."""
        self.assertEqual(len(self.launches), 41)
        runnable = [lf for lf in self.launches if lf.get("is_runnable_entry_point")]
        utils = [lf for lf in self.launches if not lf.get("is_runnable_entry_point")]

        self.assertEqual(len(runnable), 37)
        self.assertEqual(len(utils), 4)

        util_names = {Path(lf["file_path"]).name for lf in utils}
        expected_utils = {"has_node_params.py", "launch_config_as_bool.py", "replace_string.py", "rewritten_yaml.py"}
        self.assertEqual(util_names, expected_utils)

    def test_lifecycle_architecture_completeness(self):
        """Verify all 23 lifecycle managers and 43 managed nodes are fully listed without truncation."""
        managers = self.lifecycle.get("lifecycle_managers", [])
        managed = self.lifecycle.get("managed_nodes", [])

        self.assertEqual(len(managers), 23)
        self.assertEqual(len(managed), 43)

        # Verify all 23 manager names appear in README.md
        for mgr in managers:
            self.assertIn(f"`{mgr['manager_name']}`", self.readme_text)

    def test_plugin_strict_base_class_mapping(self):
        """Verify plugins are strictly partitioned by base class, eliminating general_plugin bucket."""
        categories = self.plugins.get("categories", {})
        self.assertNotIn("general_plugin", categories)

        # Verify AMCL MotionModel is its own distinct category
        self.assertIn("nav2_amcl::MotionModel", categories)
        self.assertEqual(len(categories["nav2_amcl::MotionModel"]), 2)

        # Verify PathHandler is its own distinct category
        self.assertIn("nav2_core::PathHandler", categories)
        self.assertEqual(len(categories["nav2_core::PathHandler"]), 1)

        # Verify 123 total plugins across 24 base-class extension points
        self.assertEqual(len(self.plugins.get("plugins", [])), 123)
        self.assertEqual(len(categories), 24)

    def test_communication_interface_cleanliness(self):
        """Verify invalid AST leakages are purged from topics, services, and actions."""
        bad_patterns = ["(", ")", "->", "{", "}", "::", "params_->", "shared_from_this"]

        for t in self.arch.get("topic_connections", []):
            topic = t.get("topic", "")
            for bad in bad_patterns:
                self.assertNotIn(bad, topic, f"Malformed topic name: {topic}")

        for s in self.arch.get("service_connections", []):
            svc = s.get("service", "")
            for bad in bad_patterns:
                self.assertNotIn(bad, svc, f"Malformed service name: {svc}")

        for a in self.arch.get("action_connections", []):
            act = a.get("action", "")
            for bad in bad_patterns:
                self.assertNotIn(bad, act, f"Malformed action name: {act}")

        self.assertEqual(len(self.arch.get("topic_connections", [])), 56)
        self.assertEqual(len(self.arch.get("service_connections", [])), 31)
        self.assertEqual(len(self.arch.get("action_connections", [])), 17)

    def test_behavior_tree_client_server_grounding(self):
        """Verify BtNavigator is mapped as calling client and action servers are accurately mapped."""
        bindings = self.bt.get("bt_to_ros2_bindings", [])
        self.assertGreater(len(bindings), 0)

        for b in bindings:
            self.assertEqual(b.get("client_node"), "nav2_bt_navigator::BtNavigator")
            if b.get("target_interface") == "/compute_path_to_pose":
                self.assertEqual(b.get("target_server"), "nav2_planner::PlannerServer")
            elif b.get("target_interface") == "/follow_path":
                self.assertEqual(b.get("target_server"), "nav2_controller::ControllerServer")
            elif b.get("target_interface") == "/smooth_path":
                self.assertEqual(b.get("target_server"), "nav2_smoother::SmootherServer")
            elif b.get("target_interface") in ("/spin", "/wait", "/backup"):
                self.assertEqual(b.get("target_server"), "behavior_server::BehaviorServer")

    def test_subsystem_clustering_and_jaccard_metrics(self):
        """Verify subsystem clustering retains verified reference comparison (Mean Jaccard 0.867)."""
        ref_comp = self.arch.get("subsystem_model", {}).get("reference_comparison", {})
        self.assertAlmostEqual(ref_comp.get("mean_jaccard_similarity", 0.0), 0.867, places=3)
        self.assertEqual(len(ref_comp.get("subsystem_metrics", {})), 8)

    def test_consistency_report_validation_status(self):
        """Verify machine-readable consistency report asserts VALIDATED_CONSISTENT."""
        self.assertEqual(self.report.get("overall_status"), "VALIDATED_CONSISTENT")
        self.assertEqual(self.report["evidence_integrity"]["line_ranges_with_none"], 0)
        self.assertEqual(self.report["evidence_integrity"]["link_resolution_rate"], 1.0)
        self.assertEqual(len(self.report["evidence_integrity"]["unresolved_node_doc_links"]), 0)

    def test_explicit_delivered_markdown_files(self):
        """Verify explicit delivered Markdown exists at output/nav2_corrected_pipeline/NAV2_CORRECTED_ARCHITECTURE.md."""
        delivered_file = self.corrected_dir / "NAV2_CORRECTED_ARCHITECTURE.md"
        self.assertTrue(delivered_file.exists(), f"Missing deliverable: {delivered_file}")
        content = delivered_file.read_text(encoding="utf-8")
        self.assertEqual(content, self.readme_text)
        self.assertIn("6dbf4549ae1914188916b06dcc19dd3a8115d0a5", content)
        self.assertIn("Architectural Classification", content)
        self.assertIn("Mean Jaccard Similarity", content)


if __name__ == "__main__":
    unittest.main()
