"""
Regression Test Suite for ArchSynth Web API & Central Run Resolution.
Tests:
- Central run resolution logic (aliases, canonical IDs, web runs)
- Path traversal security & input sanitization
- Markdown documentation download endpoints for all 5 repositories
- Direct load_run endpoint with alias support
- Research validation & drift diff endpoints
- Favicon endpoint
"""
import unittest
import json
from pathlib import Path
from app import app, resolve_run_dir, BASE_DIR, OUTPUT_DIR, WEB_RUNS_DIR


class TestWebApiRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    # =========================================================================
    # 1. Central Run Resolution & Path Traversal Security
    # =========================================================================

    def test_resolve_canonical_runs(self):
        canonical_runs = [
            "nav2_pipeline",
            "slam_toolbox_pipeline",
            "ros2_control_pipeline",
            "jaco2_sim_devkit_pipeline",
            "behaviortree_cpp_pipeline"
        ]
        for run_id in canonical_runs:
            target_dir, canon = resolve_run_dir(run_id)
            self.assertIsNotNone(target_dir, f"Failed to resolve canonical run: {run_id}")
            self.assertTrue(target_dir.exists(), f"Target dir does not exist: {target_dir}")
            self.assertEqual(canon, run_id)

    def test_resolve_aliases(self):
        alias_mapping = {
            "nav2": "nav2_pipeline",
            "slam_toolbox": "slam_toolbox_pipeline",
            "ros2_control": "ros2_control_pipeline",
            "jaco2": "jaco2_sim_devkit_pipeline",
            "behaviortree_cpp": "behaviortree_cpp_pipeline"
        }
        for alias, expected_canon in alias_mapping.items():
            target_dir, canon = resolve_run_dir(alias)
            self.assertIsNotNone(target_dir, f"Failed to resolve alias: {alias}")
            self.assertTrue(target_dir.exists(), f"Target dir does not exist for alias: {alias}")
            self.assertEqual(canon, expected_canon)

    def test_path_traversal_rejection(self):
        malicious_ids = [
            "../etc/passwd",
            "..\\..\\windows\\system32",
            "nav2/../../secret",
            "slam_toolbox/test",
            "ros2\0control",
            "; rm -rf /",
            "../../../output"
        ]
        for bad_id in malicious_ids:
            target_dir, canon = resolve_run_dir(bad_id)
            self.assertIsNone(target_dir, f"Security vulnerability: malicious id was not rejected: {bad_id}")
            self.assertIsNone(canon)

    def test_resolve_invalid_nonexistent_run(self):
        target_dir, canon = resolve_run_dir("non_existent_fake_run_12345")
        self.assertIsNone(target_dir)
        self.assertIsNone(canon)

    # =========================================================================
    # 2. Markdown Download Endpoint (BUG-001)
    # =========================================================================

    def test_download_all_five_repositories(self):
        runs = [
            ("nav2_pipeline", "ArchSynth_Navigation2_Architecture.md"),
            ("slam_toolbox_pipeline", "ArchSynth_SLAM_Toolbox_Architecture.md"),
            ("ros2_control_pipeline", "ArchSynth_ROS2_Control_Architecture.md"),
            ("jaco2_sim_devkit_pipeline", "ArchSynth_Kinova_Jaco2_Architecture.md"),
            ("behaviortree_cpp_pipeline", "ArchSynth_BehaviorTree_CPP_Architecture.md")
        ]
        for run_id, expected_filename in runs:
            resp = self.client.get(f"/api/download/{run_id}")
            self.assertEqual(resp.status_code, 200, f"Download failed for {run_id}")
            disp = resp.headers.get("Content-Disposition", "")
            self.assertIn("attachment", disp)
            self.assertIn(expected_filename, disp)
            self.assertEqual(resp.mimetype, "text/markdown")
            content = resp.data.decode("utf-8")
            self.assertGreater(len(content), 1000, f"Markdown file suspiciously small for {run_id}")
            self.assertTrue("# " in content, f"Markdown header missing for {run_id}")

    def test_download_via_aliases(self):
        aliases = [
            ("nav2", "ArchSynth_Navigation2_Architecture.md"),
            ("slam_toolbox", "ArchSynth_SLAM_Toolbox_Architecture.md")
        ]
        for alias, expected_filename in aliases:
            resp = self.client.get(f"/api/download/{alias}")
            self.assertEqual(resp.status_code, 200, f"Download failed for alias {alias}")
            disp = resp.headers.get("Content-Disposition", "")
            self.assertIn(expected_filename, disp)

    def test_download_nonexistent_returns_404(self):
        resp = self.client.get("/api/download/fake_nonexistent_job_999")
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertIn("error", data)

    def test_download_path_traversal_returns_404(self):
        resp = self.client.get("/api/download/..%2F..%2Fetc%2Fpasswd")
        self.assertIn(resp.status_code, [400, 404])

    # =========================================================================
    # 3. Load Run Endpoint (BUG-002)
    # =========================================================================

    def test_load_run_canonical_and_aliases(self):
        test_cases = [
            "nav2_pipeline",
            "nav2",
            "slam_toolbox_pipeline",
            "slam_toolbox",
            "ros2_control_pipeline",
            "jaco2_sim_devkit_pipeline",
            "behaviortree_cpp_pipeline"
        ]
        for run_id in test_cases:
            resp = self.client.get(f"/api/load_run/{run_id}")
            self.assertEqual(resp.status_code, 200, f"load_run failed for {run_id}")
            data = resp.get_json()
            self.assertTrue(data.get("success"))
            self.assertIn("model", data)
            self.assertIn("markdown_content", data)
            self.assertGreater(len(data["markdown_content"]), 500)

    def test_load_run_nonexistent_returns_404(self):
        resp = self.client.get("/api/load_run/fake_repo_run")
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertFalse(data.get("success"))

    # =========================================================================
    # 4. Evidence Validation & Drift Diff Endpoints (BUG-003)
    # =========================================================================

    def test_validate_precomputed_run(self):
        resp = self.client.post("/api/validate", json={"job_id": "nav2_pipeline"})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("validation_report", data)

    def test_validate_missing_payload(self):
        resp = self.client.post("/api/validate", json={})
        self.assertEqual(resp.status_code, 400)

    def test_diff_two_repositories(self):
        resp = self.client.post("/api/diff", json={
            "job_id_a": "nav2_pipeline",
            "job_id_b": "slam_toolbox_pipeline"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("drift_report", data)

    def test_diff_missing_payload(self):
        resp = self.client.post("/api/diff", json={"job_id_a": "nav2_pipeline"})
        self.assertEqual(resp.status_code, 400)

    # =========================================================================
    # 5. Favicon Endpoint (BUG-007)
    # =========================================================================

    def test_favicon_serves_svg(self):
        resp = self.client.get("/favicon.ico")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("image/svg+xml", resp.content_type)
        self.assertIn("<svg", resp.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
