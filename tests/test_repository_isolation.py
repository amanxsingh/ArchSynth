"""
Unit and regression tests for Repository Identity, Artifact Provenance,
and Cross-Repository Isolation (ArchSynth Step 1 & Step 1A).

Covers required Step 1A test scenarios:
1. Mismatched architecture.json is rejected.
2. Mismatched lifecycle_graph.json is rejected.
3. Mismatched plugin_architecture.json is rejected.
4. Artifacts with missing provenance are rejected.
5. SLAM Toolbox can analyze legitimate external Nav2 dependencies without importing Nav2's internal components.
6. A third, previously unknown repository cannot inherit Nav2 or SLAM Toolbox artifacts.
7. LLM context contains only validated artifacts for the current repository.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.repo_identity import (
    ArtifactProvenance,
    RepositoryIdentity,
    resolve_repository_identity,
    verify_repository_identity,
    attach_artifact_provenance,
    extract_artifact_provenance,
    validate_artifact_provenance,
    load_validated_json,
    audit_artifact_contamination,
    RepositoryMismatchError,
)
from src.schema import (
    PipelineConfig,
    ROS2Node,
    ArchitectureModel,
)
from src.main import ArchSynthPipeline
from src.architecture_constructor import ArchitectureConstructor, run_architecture_constructor
from src.view_generator import ViewGenerator, run_views_generation
from src.doc_generator import DocGenerator, run_doc_generator, build_llm_context


class TestRepositoryIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nav2_root = Path("case_studies/nav2").resolve()
        cls.slam_root = Path("case_studies/slam_toolbox").resolve()

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="archsynth_isolation_test_")
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scenario_1_nav2_followed_by_slam_toolbox_in_same_process(self):
        """Scenario 1: Nav2 analysis followed by SLAM Toolbox analysis in the same process."""
        # 1. Initialize Nav2
        config_nav2 = PipelineConfig(
            repo_path=str(self.nav2_root),
            output_dir=str(self.temp_path / "nav2_out"),
            primary_llm="gemini",
        )
        pipe_nav2 = ArchSynthPipeline(config_nav2)
        self.assertEqual(pipe_nav2.repo_identity.repo_name, "Navigation2")
        self.assertIn("ros-planning/navigation2", pipe_nav2.repo_identity.remote_url)
        self.assertEqual(len(pipe_nav2.repo_identity.commit_sha), 40)
        self.assertNotEqual(pipe_nav2.repo_identity.commit_sha, "main")

        # 2. In the same process, initialize SLAM Toolbox
        config_slam = PipelineConfig(
            repo_path=str(self.slam_root),
            output_dir=str(self.temp_path / "slam_out"),
            primary_llm="gemini",
        )
        pipe_slam = ArchSynthPipeline(config_slam)
        self.assertEqual(pipe_slam.repo_identity.repo_name, "slam_toolbox")
        self.assertIn("SteveMacenski/slam_toolbox", pipe_slam.repo_identity.remote_url)
        self.assertEqual(pipe_slam.repo_identity.branch, "ros2")
        self.assertEqual(len(pipe_slam.repo_identity.commit_sha), 40)
        self.assertNotEqual(pipe_slam.repo_identity.commit_sha, "main")

        # Verify no state bleeding between instances
        self.assertNotEqual(pipe_nav2.repo_identity.repo_name, pipe_slam.repo_identity.repo_name)
        self.assertNotEqual(pipe_nav2.repo_identity.remote_url, pipe_slam.repo_identity.remote_url)
        self.assertNotEqual(pipe_nav2.repo_identity.commit_sha, pipe_slam.repo_identity.commit_sha)

    def test_scenario_2_slam_toolbox_followed_by_nav2_in_same_process(self):
        """Scenario 2: SLAM Toolbox analysis followed by Nav2 analysis in reverse order."""
        config_slam = PipelineConfig(
            repo_path=str(self.slam_root),
            output_dir=str(self.temp_path / "slam_out"),
            primary_llm="gemini",
        )
        pipe_slam = ArchSynthPipeline(config_slam, expected_repo="slam_toolbox")
        self.assertEqual(pipe_slam.repo_identity.repo_name, "slam_toolbox")

        config_nav2 = PipelineConfig(
            repo_path=str(self.nav2_root),
            output_dir=str(self.temp_path / "nav2_out"),
            primary_llm="gemini",
        )
        pipe_nav2 = ArchSynthPipeline(config_nav2, expected_repo="Navigation2")
        self.assertEqual(pipe_nav2.repo_identity.repo_name, "Navigation2")

    def test_scenario_3_switching_between_repository_roots(self):
        """Scenario 3: Switching repository roots and verifying identity asserts."""
        # Correct expected_repo matches
        id_slam = resolve_repository_identity(self.slam_root, expected_name="slam_toolbox")
        self.assertEqual(id_slam.repo_name, "slam_toolbox")

        id_nav2 = resolve_repository_identity(self.nav2_root, expected_name="Navigation2")
        self.assertEqual(id_nav2.repo_name, "Navigation2")

        # Mismatch throws RepositoryMismatchError
        with self.assertRaises(RepositoryMismatchError):
            verify_repository_identity(self.slam_root, expected_name="Navigation2")

        with self.assertRaises(RepositoryMismatchError):
            verify_repository_identity(self.nav2_root, expected_name="slam_toolbox")

    def test_scenario_4_reusing_output_dir_purges_foreign_artifacts(self):
        """Scenario 4: Reusing an output directory containing foreign artifacts."""
        shared_out = self.temp_path / "shared_pipeline_dir"
        shared_out.mkdir(parents=True, exist_ok=True)

        # Write foreign artifacts from Navigation2
        foreign_arch = {
            "system_name": "Navigation2",
            "repo_name": "Navigation2",
            "nodes": [],
            "launches": [],
            "subsystems": [],
        }
        with open(shared_out / "architecture.json", "w", encoding="utf-8") as f:
            json.dump(foreign_arch, f)

        with open(shared_out / "behavior_tree_model.json", "w", encoding="utf-8") as f:
            json.dump({"nav2_specific": True}, f)

        self.assertTrue((shared_out / "architecture.json").exists())
        self.assertTrue((shared_out / "behavior_tree_model.json").exists())

        # Initialize SLAM Toolbox targeting the same directory
        config_slam = PipelineConfig(
            repo_path=str(self.slam_root),
            output_dir=str(shared_out),
            primary_llm="gemini",
        )
        pipe_slam = ArchSynthPipeline(config_slam)

        # Output directory isolation must have purged the foreign JSON files
        self.assertFalse((shared_out / "architecture.json").exists())
        self.assertFalse((shared_out / "behavior_tree_model.json").exists())

    def test_scenario_5_missing_or_invalid_git_metadata(self):
        """Scenario 5: Missing or invalid Git metadata must report 'unavailable', never invent or use 'main'."""
        dummy_dir = self.temp_path / "dummy_package"
        dummy_dir.mkdir(parents=True, exist_ok=True)
        (dummy_dir / "package.xml").write_text("<package><name>dummy_pkg</name></package>", encoding="utf-8")

        identity = resolve_repository_identity(dummy_dir)
        self.assertEqual(identity.repo_name, "dummy_pkg")
        self.assertEqual(identity.remote_url, "unavailable")
        self.assertEqual(identity.commit_sha, "unavailable")
        self.assertEqual(identity.branch, "unavailable")
        self.assertNotEqual(identity.commit_sha, "main")

        nodes_file = self.temp_path / "empty_nodes.json"
        launches_file = self.temp_path / "empty_launches.json"
        nodes_file.write_text(json.dumps([]), encoding="utf-8")
        launches_file.write_text(json.dumps([]), encoding="utf-8")

        arch_out = self.temp_path / "dummy_arch.json"
        model = run_architecture_constructor(
            nodes_json_path=nodes_file,
            launches_json_path=launches_file,
            output_path=arch_out,
            repo_name=identity.repo_name,
            repo_url=identity.remote_url,
            commit_hash=identity.commit_sha,
            branch=identity.branch,
        )
        self.assertEqual(model.repo_name, "dummy_pkg")
        self.assertEqual(model.repo_url, "unavailable")
        self.assertEqual(model.commit_hash, "unavailable")
        self.assertEqual(model.branch, "unavailable")
        self.assertNotEqual(model.commit_hash, "main")

    # =========================================================================
    # Step 1A Required Tests
    # =========================================================================

    def test_req1_mismatched_architecture_json_rejected(self):
        """Req 1: A mismatched architecture.json is rejected and purged."""
        test_dir = self.temp_path / "test_mismatched_arch"
        test_dir.mkdir(parents=True, exist_ok=True)
        arch_path = test_dir / "architecture.json"

        # Write foreign Nav2 architecture
        foreign_id = RepositoryIdentity(
            repo_name="Navigation2",
            repo_root="case_studies/nav2",
            remote_url="https://github.com/ros-planning/navigation2",
            commit_sha="6dbf4549ae1914188916b06dcc19dd3a8115d0a5",
        )
        arch_path.write_text(json.dumps({"repo_name": "Navigation2", "nodes": []}), encoding="utf-8")
        attach_artifact_provenance(arch_path, foreign_id)

        # Expected target is SLAM Toolbox
        slam_id = RepositoryIdentity(
            repo_name="slam_toolbox",
            repo_root="case_studies/slam_toolbox",
            remote_url="https://github.com/SteveMacenski/slam_toolbox",
            commit_sha="eee0cd5e4a161bb10f8334b5420c93876b31ca99",
        )

        # Validate with purge_invalid=True
        is_valid = validate_artifact_provenance(arch_path, slam_id, purge_invalid=True)
        self.assertFalse(is_valid, "Foreign architecture.json must be rejected for slam_toolbox")
        self.assertFalse(arch_path.exists(), "Foreign architecture.json must be purged from disk")

    def test_req2_mismatched_lifecycle_graph_rejected(self):
        """Req 2: A mismatched lifecycle_graph.json is rejected and not loaded."""
        test_dir = self.temp_path / "test_mismatched_life"
        test_dir.mkdir(parents=True, exist_ok=True)
        life_path = test_dir / "lifecycle_graph.json"

        # Foreign Nav2 lifecycle graph
        foreign_id = RepositoryIdentity(
            repo_name="Navigation2",
            repo_root="case_studies/nav2",
            remote_url="https://github.com/ros-planning/navigation2",
            commit_sha="6dbf4549ae1914188916b06dcc19dd3a8115d0a5",
        )
        life_data = {
            "lifecycle_managers": [
                {
                    "manager_name": "lifecycle_manager_navigation",
                    "launch_file": "bringup.py",
                    "autostart": True,
                    "bond_timeout": 4.0,
                    "managed_node_names": ["controller_server"],
                    "service_servers": [],
                }
            ],
            "managed_nodes": [],
            "unmanaged_nodes": [],
            "standard_transitions": [],
            "startup_sequence": [],
        }
        life_path.write_text(json.dumps(life_data), encoding="utf-8")
        attach_artifact_provenance(life_path, foreign_id)

        slam_id = RepositoryIdentity(
            repo_name="slam_toolbox",
            repo_root="case_studies/slam_toolbox",
            remote_url="https://github.com/SteveMacenski/slam_toolbox",
            commit_sha="eee0cd5e4a161bb10f8334b5420c93876b31ca99",
        )

        loaded = load_validated_json(life_path, slam_id, purge_invalid=True)
        self.assertIsNone(loaded, "Foreign lifecycle_graph.json must not be loaded for slam_toolbox")
        self.assertFalse(life_path.exists(), "Foreign lifecycle_graph.json must be purged")

    def test_req3_mismatched_plugin_architecture_rejected(self):
        """Req 3: A mismatched plugin_architecture.json is rejected and not loaded."""
        test_dir = self.temp_path / "test_mismatched_plugin"
        test_dir.mkdir(parents=True, exist_ok=True)
        plugin_path = test_dir / "plugin_architecture.json"

        foreign_id = RepositoryIdentity(
            repo_name="Navigation2",
            repo_root="case_studies/nav2",
            remote_url="https://github.com/ros-planning/navigation2",
            commit_sha="6dbf4549ae1914188916b06dcc19dd3a8115d0a5",
        )
        plugin_path.write_text(json.dumps({"plugins": [], "categories": {}}), encoding="utf-8")
        attach_artifact_provenance(plugin_path, foreign_id)

        slam_id = RepositoryIdentity(
            repo_name="slam_toolbox",
            repo_root="case_studies/slam_toolbox",
            remote_url="https://github.com/SteveMacenski/slam_toolbox",
            commit_sha="eee0cd5e4a161bb10f8334b5420c93876b31ca99",
        )

        loaded = load_validated_json(plugin_path, slam_id, purge_invalid=True)
        self.assertIsNone(loaded, "Foreign plugin_architecture.json must not be loaded for slam_toolbox")
        self.assertFalse(plugin_path.exists(), "Foreign plugin_architecture.json must be purged")

    def test_req4_artifacts_with_missing_provenance_rejected(self):
        """Req 4: Artifacts with missing provenance are rejected and not silently reused."""
        test_dir = self.temp_path / "test_missing_prov"
        test_dir.mkdir(parents=True, exist_ok=True)

        unprovenanced_files = [
            test_dir / "architecture.json",
            test_dir / "lifecycle_graph.json",
            test_dir / "plugin_architecture.json",
            test_dir / "subsystem_model.json",
            test_dir / "behavior_tree_model.json",
        ]

        for p in unprovenanced_files:
            p.write_text(json.dumps({"arbitrary_key": "arbitrary_val"}), encoding="utf-8")

        slam_id = RepositoryIdentity(
            repo_name="slam_toolbox",
            repo_root="case_studies/slam_toolbox",
            remote_url="https://github.com/SteveMacenski/slam_toolbox",
            commit_sha="eee0cd5e4a161bb10f8334b5420c93876b31ca99",
        )

        for p in unprovenanced_files:
            loaded = load_validated_json(p, slam_id, purge_invalid=True)
            self.assertIsNone(loaded, f"Artifact with missing provenance {p.name} must be rejected")
            self.assertFalse(p.exists(), f"Artifact with missing provenance {p.name} must be purged")

    def test_req5_slam_toolbox_external_nav2_dependencies_without_internal_components(self):
        """Req 5: SLAM Toolbox handles external Nav2 dependencies without importing internal components."""
        slam_out = Path("output/slam_toolbox_pipeline")
        if not slam_out.exists():
            config_slam = PipelineConfig(
                repo_path=str(self.slam_root),
                output_dir=str(slam_out),
                primary_llm="gemini",
            )
            pipe_slam = ArchSynthPipeline(config_slam)
            pipe_slam.run()

        # Audit directory contamination
        violations = audit_artifact_contamination(slam_out, target_repo_name="slam_toolbox")
        self.assertEqual(
            violations,
            [],
            f"Contamination detected in SLAM Toolbox output artifacts: {violations}"
        )

        # Verify internal nodes in nodes.json
        nodes_file = slam_out / "nodes.json"
        self.assertTrue(nodes_file.exists())
        nodes_data = json.loads(nodes_file.read_text(encoding="utf-8"))
        node_names = [n.get("name") or n.get("class_name") for n in nodes_data]

        internal_nav2_nodes = [
            "ControllerServer", "PlannerServer", "BtNavigator", "VelocitySmoother",
            "CollisionMonitor", "AmclNode", "MapServer", "BasicNavigator"
        ]
        for nav_node in internal_nav2_nodes:
            self.assertNotIn(
                nav_node,
                node_names,
                f"Nav2 internal node '{nav_node}' must not be imported into SLAM Toolbox nodes inventory!"
            )

    def test_req6_third_unknown_repository_cannot_inherit_foreign_artifacts(self):
        """Req 6: A third, previously unknown repository fixture cannot inherit Nav2 or SLAM Toolbox artifacts."""
        synthetic_dir = self.temp_path / "robot_arm_controller"
        synthetic_dir.mkdir(parents=True, exist_ok=True)
        (synthetic_dir / "package.xml").write_text(
            "<package><name>robot_arm_controller</name><version>1.0.0</version></package>",
            encoding="utf-8"
        )
        src_dir = synthetic_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "arm_node.cpp").write_text(
            """
            #include <rclcpp/rclcpp.hpp>
            class ArmControllerNode : public rclcpp::Node {
            public:
                ArmControllerNode() : Node("arm_controller") {}
            };
            """,
            encoding="utf-8"
        )

        # Set up an output directory pre-seeded with foreign Nav2 and SLAM Toolbox artifacts
        synth_out = self.temp_path / "robot_arm_out"
        synth_out.mkdir(parents=True, exist_ok=True)

        foreign_bt = {
            "trees": [],
            "host_node_id": "nav2_bt_navigator::BtNavigator",
            "_provenance": {
                "repository_name": "Navigation2",
                "repository_url": "https://github.com/ros-planning/navigation2",
                "commit_hash": "6dbf4549ae1914188916b06dcc19dd3a8115d0a5",
                "branch": "main",
                "archsynth_version": "2.0",
                "artifact_schema_version": "1.0",
            }
        }
        (synth_out / "behavior_tree_model.json").write_text(json.dumps(foreign_bt), encoding="utf-8")

        foreign_plugin = {
            "plugins": [],
            "categories": {},
            "_provenance": {
                "repository_name": "slam_toolbox",
                "repository_url": "https://github.com/SteveMacenski/slam_toolbox",
                "commit_hash": "eee0cd5e4a161bb10f8334b5420c93876b31ca99",
                "branch": "ros2",
                "archsynth_version": "2.0",
                "artifact_schema_version": "1.0",
            }
        }
        (synth_out / "plugin_architecture.json").write_text(json.dumps(foreign_plugin), encoding="utf-8")

        # Run pipeline on this previously unknown repository
        config_synth = PipelineConfig(
            repo_path=str(synthetic_dir),
            output_dir=str(synth_out),
            primary_llm="gemini",
        )
        pipeline = ArchSynthPipeline(config_synth)
        out_readme = pipeline.run()

        # Assert foreign artifacts were purged and not inherited
        arch_model = ArchitectureModel.model_validate(json.loads((synth_out / "architecture.json").read_text(encoding="utf-8")))
        self.assertEqual(arch_model.repo_name, "robot_arm_controller")
        self.assertIsNone(arch_model.behavior_tree_model, "Foreign Nav2 BT model must not be inherited")

        # Audit contamination
        violations = audit_artifact_contamination(synth_out, target_repo_name="robot_arm_controller")
        self.assertEqual(
            violations,
            [],
            f"Foreign contamination found in synthetic repository output: {violations}"
        )

        readme_text = out_readme.read_text(encoding="utf-8")
        self.assertIn("# robot_arm_controller Architecture Documentation", readme_text)
        self.assertNotIn("BasicNavigator", readme_text)
        self.assertNotIn("ControllerServer", readme_text)

    def test_req7_llm_context_contains_only_validated_artifacts(self):
        """Req 7: LLM context contains only validated artifacts for the current repository."""
        slam_arch_file = Path("output/slam_toolbox_pipeline/architecture.json")
        self.assertTrue(slam_arch_file.exists(), "SLAM Toolbox architecture.json must exist")

        arch_data = json.loads(slam_arch_file.read_text(encoding="utf-8"))
        model = ArchitectureModel.model_validate(arch_data)

        # Build LLM context
        context = build_llm_context(model)

        # Verify context belongs exclusively to slam_toolbox
        self.assertEqual(context["repository_name"], "slam_toolbox")
        for pkg in context["packages"]:
            self.assertIn(
                pkg,
                ["slam_toolbox", "karto_sdk"],
                f"Foreign package '{pkg}' found in LLM prompt context!"
            )

        forbidden_nodes = [
            "ControllerServer", "PlannerServer", "BtNavigator", "VelocitySmoother",
            "CollisionMonitor", "AmclNode", "MapServer", "BasicNavigator"
        ]
        for node in context["nodes"]:
            for forbidden in forbidden_nodes:
                self.assertNotIn(
                    forbidden,
                    node,
                    f"Forbidden node '{forbidden}' found in LLM context!"
                )


if __name__ == "__main__":
    unittest.main()
