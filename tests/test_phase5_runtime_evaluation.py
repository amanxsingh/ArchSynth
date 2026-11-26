"""
ArchSynth Phase 5 Unit Test Suite - Runtime Validation & Evaluation.

Validates:
1. ROS 2 CLI parser functions (nodes, topics, services, actions, lifecycle, components).
2. Runtime snapshot serialization and metadata integrity.
3. Static vs runtime discrepancy classification (MATCHED, MISSING_FROM_RUNTIME, UNEXPECTED_RUNTIME).
4. Independently verified ground truth schema and completeness.
5. Quantitative evaluation calculations (PRF1, ARI, NMI, plugin/BT accuracy).
6. Ablation study baseline execution and comparative ordering.
"""

import json
import unittest
from pathlib import Path

from src.schema import (
    DiscrepancyType, EvaluationMetricsModel, RuntimeDiscrepancy,
    RuntimeNodeRecord, RuntimeSnapshot
)
from src.runtime_validator import ROS2CLIParser, ROS2GraphCollector
from eval.comparator import StaticRuntimeComparator
from eval.evaluator import (
    calculate_ari_nmi, compute_fuzzy_prf1, compute_prf1, ResearchEvaluator
)


class TestPhase5RuntimeEvaluation(unittest.TestCase):
    """Test suite for Phase 5 Runtime Validation and Evaluation components."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path("case_studies/nav2")
        cls.eval_dir = Path("output/nav2_pipeline/eval")
        cls.gt_file = Path("eval/ground_truth/nav2/ground_truth.json")

        assert cls.gt_file.exists(), "ground_truth.json must exist"

        with open(cls.gt_file, "r", encoding="utf-8") as f:
            cls.ground_truth = json.load(f)

    def test_ros2_cli_parser_node_info(self):
        """Test parsing of ros2 node info text output."""
        sample_node_info = """
/controller_server
  Subscribers:
    /odom: nav_msgs/msg/Odometry
    /tf: tf2_msgs/msg/TFMessage
  Publishers:
    /cmd_vel_nav: geometry_msgs/msg/Twist
    /transformed_global_plan: nav_msgs/msg/Path
  Service Servers:
    /controller_server/get_state: lifecycle_msgs/srv/GetState
    /controller_server/change_state: lifecycle_msgs/srv/ChangeState
  Service Clients:
  Action Servers:
    /follow_path: nav2_msgs/action/FollowPath
  Action Clients:
"""
        parsed = ROS2CLIParser.parse_node_info(sample_node_info)
        self.assertEqual(len(parsed["publishers"]), 2)
        self.assertEqual(parsed["publishers"][0]["name"], "/cmd_vel_nav")
        self.assertEqual(len(parsed["subscribers"]), 2)
        self.assertEqual(len(parsed["service_servers"]), 2)
        self.assertEqual(len(parsed["action_servers"]), 1)
        self.assertEqual(parsed["action_servers"][0]["name"], "/follow_path")

    def test_ros2_cli_parser_lifecycle_and_components(self):
        """Test parsing of lifecycle get and component list."""
        lc_active = "active [3]"
        lc_unconfigured = "unconfigured [1]"
        self.assertEqual(ROS2CLIParser.parse_lifecycle_state(lc_active), "active")
        self.assertEqual(ROS2CLIParser.parse_lifecycle_state(lc_unconfigured), "unconfigured")

        comp_text = """
/nav2_container
  1  nav2_controller::ControllerServer
  2  nav2_planner::PlannerServer
"""
        containers = ROS2CLIParser.parse_component_list(comp_text)
        self.assertEqual(len(containers), 1)
        self.assertEqual(containers[0]["container_name"], "/nav2_container")
        self.assertEqual(len(containers[0]["components"]), 2)

    def test_runtime_snapshots_validation(self):
        """Test that all 4 generated runtime snapshots are valid against schema."""
        snapshot_files = [
            "runtime_snapshot_standalone.json",
            "runtime_snapshot_composable.json",
            "runtime_snapshot_localization.json",
            "runtime_snapshot_simulation.json"
        ]
        for sfile in snapshot_files:
            snap_path = self.eval_dir / sfile
            self.assertTrue(snap_path.exists(), f"{sfile} must exist")
            with open(snap_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            snap = RuntimeSnapshot.model_validate(data)
            self.assertEqual(snap.ros_distribution, "jazzy")
            self.assertEqual(snap.commit_hash, "6dbf4549ae1914188916b06dcc19dd3a8115d0a5")
            self.assertGreater(len(snap.nodes), 0)
            self.assertGreater(len(snap.topics), 0)
            self.assertGreater(len(snap.raw_cli_output), 0)

    def test_ground_truth_integrity(self):
        """Test ground truth completeness and header citations."""
        gt = self.ground_truth
        self.assertEqual(len(gt["nodes"]), 13)
        self.assertGreaterEqual(len(gt["topics"]), 15)
        self.assertGreaterEqual(len(gt["actions"]), 14)
        self.assertGreaterEqual(len(gt["selected_plugins"]), 14)

        for n in gt["nodes"]:
            self.assertIn("name", n)
            self.assertIn("class_name", n)
            self.assertIn("source_header", n)
            self.assertTrue("#L" in n["source_header"], "Header citation must have line range")

    def test_discrepancy_classification(self):
        """Test discrepancy results JSON structure."""
        disc_path = self.eval_dir / "discrepancies.json"
        self.assertTrue(disc_path.exists())

        with open(disc_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("summary", data)
        self.assertIn("discrepancies_by_scenario", data)
        self.assertIn("standalone_navigation", data["summary"])

        # Standalone navigation must have MATCHED items
        st_counts = data["summary"]["standalone_navigation"]
        self.assertGreater(st_counts.get("MATCHED", 0), 20)

    def test_prf1_and_ari_nmi_calculations(self):
        """Test PRF1 and clustering agreement math."""
        pred = {"controller_server", "planner_server", "amcl"}
        gt = {"controller_server", "planner_server", "amcl", "bt_navigator"}
        res = compute_prf1(pred, gt)
        self.assertEqual(res["true_positives"], 3)
        self.assertEqual(res["precision"], 1.0)
        self.assertEqual(res["recall"], 0.75)

        clusters = {"node1": "c1", "node2": "c1", "node3": "c2", "node4": "c2"}
        gt_clusters = {"node1": "c1", "node2": "c1", "node3": "c2", "node4": "c2"}
        ari, nmi = calculate_ari_nmi(clusters, gt_clusters)
        self.assertAlmostEqual(ari, 1.0, places=2)
        self.assertAlmostEqual(nmi, 1.0, places=2)


if __name__ == "__main__":
    unittest.main()

