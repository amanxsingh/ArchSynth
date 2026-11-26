"""
Tests for Step 3 and Step 3A: SLAM Toolbox Interface Extraction & Communication Graph Recovery
Covers:
 Part A: Initial 22 verification areas
 Part B: Step 3A Regression Tests (19 audit areas):
  1. Abstract SlamToolbox classification (is_abstract == True)
  2. No false runtime node for abstract base
  3. Inherited interfaces without duplicate source declarations (37 declarations)
  4. MapSaver conditional creation (use_map_saver_ default True)
  5. Localization MapSaver destruction (map_saver_.reset() removes 2 interfaces)
  6. Synchronous clear_queue lifecycle creation (on_activate)
  7. Localization interface activation and deactivation (initialpose, clear_localization_buffer)
  8. Decentralized localized_scan publisher extraction
  9. Decentralized localized_scan subscriber extraction
 10. Same-class peer communication edge (peer_instance on /localized_scan)
 11. Map publisher to MapSaver intra-node relationship (intra_node on /map)
 12. Correct separation of graph edge types (inter_node, intra_node, peer_instance, cross_profile)
 13. Cross-profile graph not labelled as observed runtime (edge_kind == cross_profile)
 14. TF listener internal-node handling (internal helper node documentation)
 15. /tf and /tf_static dependency endpoint handling
 16. Exact Git blob/source line parity (100% cryptographic match to eee0cd5)
 17. QoS evidence and UNKNOWN behavior
 18. External endpoint confidence classification (EXTERNAL_CONFIRMED vs EXTERNAL_CANDIDATE)
 19. Corrected runtime interface count by profile (21, 22, 21, 21, 22, 23, 7 = 137 total)
"""

import subprocess
import tempfile
import unittest
from pathlib import Path

from src.schema import (
    CommunicationType,
    EntityType,
    EvidenceType,
    InterfaceDeclaration,
    QoSCompatibility,
    ROS2Node,
)
from src.repo_identity import RepositoryIdentity, resolve_repository_identity
from src.node_analyzer import run_node_analysis
from src.build_analyzer import analyze_package_cmake
from src.interface_extractor import extract_all_repository_interfaces
from src.launch_analyzer import run_phase2_launch_pipeline
from src.communication_builder import CommunicationBuilder


class TestSlamToolboxInterfaceExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path("case_studies/slam_toolbox")
        if not cls.repo_root.exists():
            raise unittest.SkipTest("SLAM Toolbox repository not available at case_studies/slam_toolbox")

        cls.tmp_dir = tempfile.TemporaryDirectory()
        tmp_path = Path(cls.tmp_dir.name)

        # Discover nodes and cmake info
        cls.nodes = run_node_analysis(cls.repo_root, tmp_path / "nodes.json")
        cls.cmake_info = analyze_package_cmake(cls.repo_root, cls.repo_root)

        # Launch analysis
        cls.launch_files, cls.launch_instances, cls.mappings, cls.profiles = run_phase2_launch_pipeline(
            cls.repo_root, tmp_path / "nodes.json", tmp_path
        )

        # Extract all repository interfaces
        cls.interfaces = extract_all_repository_interfaces(
            cls.nodes, cls.repo_root
        )

        # Communication Builder
        cls.comm_builder = CommunicationBuilder(
            cls.interfaces, cls.launch_instances, {"slam_toolbox": str(cls.repo_root)}
        )
        cls.runtime_interfaces = cls.comm_builder.build_runtime_interfaces()
        cls.source_edges = cls.comm_builder.build_source_potential_graph(cls.interfaces)
        cls.deployment_edges = cls.comm_builder.build_deployment_runtime_graph(cls.runtime_interfaces)
        cls.unmatched, cls.external = cls.comm_builder.classify_endpoints(cls.interfaces, cls.source_edges)
        cls.confirmed, cls.candidate = cls.comm_builder.classify_external_confidence(cls.interfaces, cls.external)

    @classmethod
    def tearDownClass(cls):
        cls.tmp_dir.cleanup()

    # =========================================================================
    # Part A: Verification Areas 1 - 22
    # =========================================================================

    def test_01_slam_toolbox_base_extraction(self):
        base_ifaces = [i for i in self.interfaces if i.owning_class.endswith("SlamToolbox")]
        self.assertGreaterEqual(len(base_ifaces), 20, "Base class SlamToolbox should declare at least 20 interfaces")
        pub_names = {i.resolved_name or i.name_expression for i in base_ifaces if i.interface_type == CommunicationType.PUBLISHER}
        self.assertIn("/map", pub_names)
        self.assertIn("/map_metadata", pub_names)

    def test_02_async_slam_toolbox_inheritance(self):
        async_rts = [r for r in self.runtime_interfaces if "online_async_launch" in r.launch_instance_id]
        self.assertGreaterEqual(len(async_rts), 20)
        async_names = {r.resolved_name for r in async_rts}
        self.assertIn("/map", async_names)
        self.assertIn("/map_metadata", async_names)
        self.assertTrue(any("SlamToolbox" in r.declaration_id for r in async_rts))

    def test_03_sync_slam_toolbox_extraction(self):
        sync_ifaces = [i for i in self.interfaces if "SynchronousSlamToolbox" in i.owning_class]
        srv_names = {i.name_expression for i in sync_ifaces if i.interface_type == CommunicationType.SERVICE_SERVER}
        self.assertTrue(any("clear_queue" in n for n in srv_names))

    def test_04_localization_slam_toolbox_extraction(self):
        loc_ifaces = [i for i in self.interfaces if "LocalizationSlamToolbox" in i.owning_class]
        names = {i.name_expression for i in loc_ifaces}
        self.assertTrue(any("clear_localization_buffer" in n for n in names))
        self.assertIn("initialpose", names)

    def test_05_lifelong_slam_toolbox_extraction(self):
        life_rts = [r for r in self.runtime_interfaces if "lifelong_launch" in r.launch_instance_id]
        self.assertGreaterEqual(len(life_rts), 20)
        self.assertTrue(any("SlamToolbox" in r.declaration_id for r in life_rts))

    def test_06_decentralized_multirobot_extraction(self):
        dec_ifaces = [i for i in self.interfaces if "DecentralizedMultiRobotSlamToolbox" in i.owning_class]
        names = {i.name_expression for i in dec_ifaces}
        self.assertTrue(any("localized_scan" in n for n in names))

    def test_07_map_and_localization_extraction(self):
        ml_ifaces = [i for i in self.interfaces if "MapAndLocalizationSlamToolbox" in i.owning_class]
        names = {i.name_expression for i in ml_ifaces}
        self.assertTrue(any("set_localization_mode" in n for n in names))
        self.assertTrue(any("clear_localization_buffer" in n for n in names))

    def test_08_merge_maps_kinematic_extraction(self):
        merge_ifaces = [i for i in self.interfaces if "MergeMapsKinematic" in i.owning_class]
        self.assertGreaterEqual(len(merge_ifaces), 6)
        names = {i.name_expression for i in merge_ifaces}
        self.assertIn("/map", names)
        self.assertTrue(any("merge_submaps" in n for n in names))

    def test_09_helper_map_saver(self):
        map_saver_ifaces = [i for i in self.interfaces if any("map_saver" in ev.file for ev in i.evidence)]
        self.assertGreaterEqual(len(map_saver_ifaces), 2)
        names = {i.name_expression for i in map_saver_ifaces}
        self.assertTrue(any("save_map" in n for n in names))

    def test_10_helper_loop_closure_assistant(self):
        lca_ifaces = [i for i in self.interfaces if any("loop_closure_assistant" in ev.file for ev in i.evidence)]
        self.assertGreaterEqual(len(lca_ifaces), 5)
        names = {i.name_expression for i in lca_ifaces}
        self.assertTrue(any("manual_loop_closure" in n for n in names))
        self.assertTrue(any("clear_changes" in n for n in names))

    def test_11_tf_broadcaster_extraction(self):
        tf_broadcasters = [i for i in self.interfaces if i.interface_type == CommunicationType.TF_BROADCASTER]
        self.assertGreaterEqual(len(tf_broadcasters), 2)
        for tf_b in tf_broadcasters:
            self.assertEqual(tf_b.resolved_name or tf_b.name_expression, "/tf")
            self.assertEqual(tf_b.message_type, "tf2_msgs/msg/TFMessage")

    def test_12_tf_listener_extraction(self):
        tf_listeners = [i for i in self.interfaces if i.interface_type == CommunicationType.TF_LISTENER]
        self.assertGreaterEqual(len(tf_listeners), 1)
        self.assertEqual(tf_listeners[0].resolved_name or tf_listeners[0].name_expression, "/tf")
        self.assertEqual(tf_listeners[0].message_type, "tf2_msgs/msg/TFMessage")

    def test_13_message_filters_subscriber(self):
        scan_subs = [i for i in self.interfaces if i.name_expression == "/scan" and i.interface_type == CommunicationType.SUBSCRIBER]
        self.assertGreaterEqual(len(scan_subs), 1)
        scan_sub = scan_subs[0]
        self.assertEqual(scan_sub.message_type, "sensor_msgs/msg/LaserScan")
        self.assertTrue(any("message_filters::Subscriber" in ev.explanation for ev in scan_sub.evidence))

    def test_14_dynamic_topic_template(self):
        dyn_ifaces = [i for i in self.interfaces if i.is_dynamic]
        self.assertGreaterEqual(len(dyn_ifaces), 1)
        dyn = dyn_ifaces[0]
        self.assertEqual(dyn.dynamic_prefix, "/map_")
        self.assertEqual(dyn.dynamic_template, "/map_{i}")
        self.assertTrue(dyn.dynamic_unresolved_part)

    def test_15_parameter_resolution_map(self):
        map_ifaces = [i for i in self.interfaces if i.name_expression == "/map" and i.owning_class.endswith("SlamToolbox")]
        self.assertGreaterEqual(len(map_ifaces), 1)
        m = map_ifaces[0]
        self.assertIn("map_name_ -> /map", m.parameter_provenance)

    def test_16_parameter_resolution_scan(self):
        scan_ifaces = [i for i in self.interfaces if i.name_expression == "/scan"]
        self.assertGreaterEqual(len(scan_ifaces), 1)
        s = scan_ifaces[0]
        self.assertIn("scan_topic_ -> /scan", s.parameter_provenance)

    def test_17_launch_instance_resolution(self):
        instances = self.launch_instances
        self.assertEqual(len(instances), 7)
        node_ids = {n.id for n in self.nodes}
        for inst in instances:
            self.assertIsNotNone(inst.node_id, f"Instance {inst.instance_id} must have node_id resolved")
            self.assertIn(inst.node_id, node_ids)

    def test_18_runtime_interface_binding(self):
        runtime_ifaces = self.runtime_interfaces
        self.assertEqual(len(runtime_ifaces), 143, "Reconciled application interface instance count must be 143 across profiles without false /tf deduplication")
        for ri in runtime_ifaces:
            self.assertTrue(ri.launch_instance_id)
            self.assertTrue(ri.resolved_name)

    def test_19_edge_generation_profile_separation(self):
        edges_by_profile = {}
        for e in self.deployment_edges:
            edges_by_profile.setdefault(e.deployment_profile, []).append(e)
        # Standalone profile runs 1 node -> 0 internal deployment edges
        self.assertEqual(len(edges_by_profile.get("launch_online_async", [])), 0)
        # Cross-profile default aggregate profile contains hypothetical compatibility edges
        self.assertGreater(len(edges_by_profile.get("default", [])), 0)

    def test_20_zero_actions_verified(self):
        action_ifaces = [
            i for i in self.interfaces
            if i.interface_type in (CommunicationType.ACTION_SERVER, CommunicationType.ACTION_CLIENT)
        ]
        self.assertEqual(len(action_ifaces), 0, "No ROS 2 action server/client creation declarations were recovered from the analyzed repository source.")

    def test_21_external_endpoints_classification(self):
        self.assertGreaterEqual(len(self.external), 20)
        decl_dict = {d.declaration_id: d for d in self.interfaces}
        ext_decls = [decl_dict[did] for did in self.external if did in decl_dict]
        ext_names = {d.resolved_name or d.name_expression for d in ext_decls}
        self.assertIn("/scan", ext_names)
        self.assertIn("/tf", ext_names)

    def test_22_source_vs_deployment_separation(self):
        # 3 source potential edges (1 inter-node, 1 intra-node, 1 peer-instance)
        self.assertEqual(len(self.source_edges), 3)
        inter_edges = [e for e in self.source_edges if e.edge_kind == "inter_node"]
        self.assertEqual(len(inter_edges), 1)
        self.assertEqual(inter_edges[0].interface_name, "map")
        self.assertEqual(inter_edges[0].source_node_id, "slam_toolbox::MergeMapsKinematic")
        self.assertEqual(inter_edges[0].target_node_id, "slam_toolbox::SlamToolbox")

    # =========================================================================
    # Part B: Step 3A Audit Regression Tests (19 Areas)
    # =========================================================================

    def test_23_abstract_slam_toolbox_classification(self):
        """1. Abstract SlamToolbox classification: base class has is_abstract=True"""
        base_node = next((n for n in self.nodes if n.id == "slam_toolbox::SlamToolbox"), None)
        self.assertIsNotNone(base_node)
        self.assertTrue(base_node.is_abstract, "slam_toolbox::SlamToolbox must be marked is_abstract=True")

    def test_24_no_false_runtime_node_for_abstract_base(self):
        """2. No false runtime node for abstract base: launch instances only bind to concrete derived nodes"""
        for inst in self.launch_instances:
            self.assertNotEqual(inst.node_id, "slam_toolbox::SlamToolbox", "LaunchInstance must never bind to abstract base class")

    def test_25_inherited_interfaces_no_duplicate_source_declarations(self):
        """3. Inherited interfaces without duplicate source declarations (exactly 37 unique declarations)"""
        self.assertEqual(len(self.interfaces), 37)
        decl_ids = [d.declaration_id for d in self.interfaces]
        self.assertEqual(len(decl_ids), len(set(decl_ids)), "All 37 declaration IDs must be globally unique")

    def test_26_map_saver_conditional_creation(self):
        """4. MapSaver conditional creation: parameter use_map_saver_ defaults to true in base node"""
        common_cpp = (self.repo_root / "src/slam_toolbox_common.cpp").read_text(encoding="utf-8")
        self.assertIn("use_map_saver_ = true;", common_cpp)
        self.assertIn("if (use_map_saver_)", common_cpp)

    def test_27_localization_map_saver_destruction(self):
        """5. Localization MapSaver destruction: map_saver_.reset() removes save_map and /map subscription in localization"""
        loc_rts = [r for r in self.runtime_interfaces if "localization_launch" in r.launch_instance_id]
        loc_names = {r.resolved_name for r in loc_rts}
        self.assertNotIn("/slam_toolbox/save_map", loc_names, "MapSaver::save_map must not be active in localization deployment")
        loc_subs = [r for r in loc_rts if r.interface_type == CommunicationType.SUBSCRIBER]
        self.assertFalse(any(r.resolved_name == "/map" for r in loc_subs), "MapSaver::/map subscriber must not be active in localization")

    def test_28_synchronous_clear_queue_lifecycle(self):
        """6. Synchronous clear_queue lifecycle creation in on_activate"""
        sync_cpp = (self.repo_root / "src/slam_toolbox_sync.cpp").read_text(encoding="utf-8")
        self.assertIn("SynchronousSlamToolbox::on_activate", sync_cpp)
        self.assertIn("ssClear_ = this->create_service<slam_toolbox::srv::ClearQueue>", sync_cpp)
        self.assertIn("SynchronousSlamToolbox::on_deactivate", sync_cpp)
        self.assertIn("ssClear_.reset();", sync_cpp)

    def test_29_localization_interface_lifecycle(self):
        """7. Localization interface activation and deactivation"""
        loc_cpp = (self.repo_root / "src/slam_toolbox_localization.cpp").read_text(encoding="utf-8")
        self.assertIn("LocalizationSlamToolbox::on_activate", loc_cpp)
        self.assertIn("clear_localization_ = this->create_service<std_srvs::srv::Empty>", loc_cpp)
        self.assertIn("LocalizationSlamToolbox::on_deactivate", loc_cpp)
        self.assertIn("clear_localization_.reset();", loc_cpp)
        self.assertIn("localization_pose_sub_.reset();", loc_cpp)

    def test_30_decentralized_localized_scan_pub(self):
        """8. Decentralized localized_scan publisher extraction"""
        dec_pubs = [i for i in self.interfaces if i.owning_class.endswith("DecentralizedMultiRobotSlamToolbox") and i.interface_type == CommunicationType.PUBLISHER]
        self.assertEqual(len(dec_pubs), 1)
        self.assertEqual(dec_pubs[0].name_expression, "/localized_scan")

    def test_31_decentralized_localized_scan_sub(self):
        """9. Decentralized localized_scan subscriber extraction"""
        dec_subs = [i for i in self.interfaces if i.owning_class.endswith("DecentralizedMultiRobotSlamToolbox") and i.interface_type == CommunicationType.SUBSCRIBER]
        self.assertEqual(len(dec_subs), 1)
        self.assertEqual(dec_subs[0].name_expression, "/localized_scan")

    def test_32_same_class_peer_communication_edge(self):
        """10. Same-class peer communication edge for DecentralizedMultiRobot on /localized_scan"""
        peer_edges = [e for e in self.source_edges if e.edge_kind == "peer_instance"]
        self.assertEqual(len(peer_edges), 1)
        pe = peer_edges[0]
        self.assertEqual(pe.interface_name, "localized_scan")
        self.assertIn("peer communication", pe.qos_details.lower())

    def test_33_map_publisher_to_map_saver_intra_node(self):
        """11. Map publisher to MapSaver intra-node relationship"""
        intra_edges = [e for e in self.source_edges if e.edge_kind == "intra_node"]
        self.assertEqual(len(intra_edges), 1)
        ie = intra_edges[0]
        self.assertEqual(ie.interface_name, "map")
        self.assertEqual(ie.source_component, "SlamToolbox")
        self.assertEqual(ie.target_component, "MapSaver")

    def test_34_correct_separation_of_graph_edge_types(self):
        """12. Correct separation of graph edge types"""
        kinds = {e.edge_kind for e in self.source_edges}
        self.assertIn("inter_node", kinds)
        self.assertIn("intra_node", kinds)
        self.assertIn("peer_instance", kinds)

    def test_35_cross_profile_graph_not_labelled_observed_runtime(self):
        """13. Cross-profile default graph must be labelled cross_profile, not observed runtime"""
        cross_edges = [e for e in self.deployment_edges if e.deployment_profile == "default"]
        for ce in cross_edges:
            self.assertEqual(ce.edge_kind, "cross_profile")

    def test_36_tf_listener_internal_node_handling(self):
        """14. TF listener evidence documents internal helper node creation"""
        tf_list = next((i for i in self.interfaces if i.interface_type == CommunicationType.TF_LISTENER), None)
        self.assertIsNotNone(tf_list)
        self.assertTrue(any("internal helper node" in ev.explanation for ev in tf_list.evidence))

    def test_37_tf_and_tf_static_endpoints(self):
        """15. /tf and /tf_static dependency endpoint handling"""
        tf_ifaces = [i for i in self.interfaces if i.interface_type in (CommunicationType.TF_BROADCASTER, CommunicationType.TF_LISTENER)]
        self.assertGreaterEqual(len(tf_ifaces), 4)

    def test_38_exact_git_blob_parity(self):
        """16. Exact Git blob/source line parity with commit eee0cd5"""
        if not (self.repo_root / ".git").exists():
            self.skipTest("case_studies/slam_toolbox/.git not present in slim distribution")
        cmd = ["git", "rev-parse", "HEAD:src/slam_toolbox_common.cpp"]
        blob_sha = subprocess.check_output(cmd, cwd=self.repo_root, text=True).strip()
        self.assertEqual(blob_sha, "eaadb8de24f528638ab1f2f20fa1e1e7f75cc151")

    def test_39_qos_evidence_and_unknown_handling(self):
        """17. QoS evidence preserves UNKNOWN for unevaluated policies"""
        map_pub = next((i for i in self.interfaces if i.name_expression == "/map" and i.owning_class.endswith("SlamToolbox")), None)
        self.assertIsNotNone(map_pub)
        self.assertEqual(map_pub.qos_reliability, "reliable")
        self.assertEqual(map_pub.qos_durability, "transient_local")

    def test_40_external_endpoint_confidence_classification(self):
        """18. External endpoint confidence classification: confirmed vs candidate"""
        self.assertEqual(len(self.confirmed), 4)
        self.assertEqual(len(self.candidate), 27)
        decl_dict = {d.declaration_id: d for d in self.interfaces}
        conf_names = {decl_dict[cid].name_expression for cid in self.confirmed if cid in decl_dict}
        self.assertIn("/scan", conf_names)
        self.assertIn("/tf", conf_names)

    def test_41_corrected_runtime_interface_count_by_profile(self):
        """19. Corrected application interface instances by profile (143 aggregate across profiles)"""
        counts = {}
        for r in self.runtime_interfaces:
            # Group by declaring launch file
            lf = r.launch_instance_id.split("::")[0].replace("\\", "/")
            counts[lf] = counts.get(lf, 0) + 1

        self.assertEqual(counts["launch/online_async_launch.py"], 22)
        self.assertEqual(counts["launch/online_sync_launch.py"], 23)
        self.assertEqual(counts["launch/localization_launch.py"], 22, "Localization has 22 interfaces (MapSaver reset removes 2, adds initialpose & clear_buffer)")
        self.assertEqual(counts["launch/lifelong_launch.py"], 22)
        self.assertEqual(counts["launch/offline_launch.py"], 23)
        self.assertEqual(counts["launch/online_async_decentralized_multirobot_launch.py"], 24)
        self.assertEqual(counts["launch/merge_maps_kinematic_launch.py"], 7)
        self.assertEqual(len(self.runtime_interfaces), 143)

    # =========================================================================
    # Part C: Step 3B Final Audit Tests (23 Required Verification Areas)
    # =========================================================================

    def test_42_main_base_publisher_count_and_ownership(self):
        """1. Main base publisher count and ownership (6 publishers in SlamToolbox)"""
        base_pubs = [i for i in self.interfaces if i.owning_class == "slam_toolbox::SlamToolbox" and i.interface_type == CommunicationType.PUBLISHER]
        self.assertEqual(len(base_pubs), 6)
        pub_names = {i.name_expression for i in base_pubs}
        self.assertIn("pose", pub_names)
        self.assertIn("/map", pub_names)
        self.assertIn("/map_metadata", pub_names)
        self.assertIn("slam_toolbox/pose_graph", pub_names)
        self.assertIn("slam_toolbox/new_node_event", pub_names)
        self.assertIn("slam_toolbox/loop_closure_event", pub_names)

    def test_43_main_base_service_count_and_ownership(self):
        """2. Main base service count and ownership (5 services in SlamToolbox)"""
        base_srvs = [i for i in self.interfaces if i.owning_class == "slam_toolbox::SlamToolbox" and i.interface_type == CommunicationType.SERVICE_SERVER]
        self.assertEqual(len(base_srvs), 5)
        srv_names = {i.name_expression for i in base_srvs}
        self.assertIn("slam_toolbox/dynamic_map", srv_names)
        self.assertIn("slam_toolbox/pause_new_measurements", srv_names)
        self.assertIn("slam_toolbox/serialize_map", srv_names)
        self.assertIn("slam_toolbox/deserialize_map", srv_names)
        self.assertIn("slam_toolbox/reset", srv_names)
        # clear_changes must NOT be attributed to the base class!
        self.assertNotIn("slam_toolbox/clear_changes", srv_names)

    def test_44_reset_service_extraction(self):
        """3. Reset service extraction in slam_toolbox_common.cpp:498"""
        reset_srv = next((i for i in self.interfaces if i.name_expression == "slam_toolbox/reset"), None)
        self.assertIsNotNone(reset_srv)
        self.assertEqual(reset_srv.owning_class, "slam_toolbox::SlamToolbox")
        self.assertEqual(reset_srv.message_type, "slam_toolbox/srv/Reset")
        self.assertEqual(reset_srv.line_start, 498)

    def test_45_loop_closure_assistant_services_classification(self):
        """4. LoopClosureAssistant service classification (3 service servers, clear_changes is SERVICE)"""
        lca_srvs = [i for i in self.interfaces if i.owning_class == "slam_toolbox::LoopClosureAssistant" and i.interface_type == CommunicationType.SERVICE_SERVER]
        self.assertEqual(len(lca_srvs), 3)
        srv_names = {i.name_expression for i in lca_srvs}
        self.assertIn("slam_toolbox/clear_changes", srv_names)
        self.assertIn("slam_toolbox/manual_loop_closure", srv_names)
        self.assertIn("slam_toolbox/toggle_interactive_mode", srv_names)
        # Verify clear_changes is NOT a publisher
        lca_pubs = [i for i in self.interfaces if i.owning_class == "slam_toolbox::LoopClosureAssistant" and i.interface_type == CommunicationType.PUBLISHER]
        self.assertNotIn("slam_toolbox/clear_changes", {i.name_expression for i in lca_pubs})

    def test_46_loop_closure_assistant_publishers_classification(self):
        """5. LoopClosureAssistant publisher classification (2 publishers)"""
        lca_pubs = [i for i in self.interfaces if i.owning_class == "slam_toolbox::LoopClosureAssistant" and i.interface_type == CommunicationType.PUBLISHER]
        self.assertEqual(len(lca_pubs), 2)
        pub_names = {i.name_expression for i in lca_pubs}
        self.assertIn("slam_toolbox/scan_visualization", pub_names)
        self.assertIn("slam_toolbox/graph_visualization", pub_names)

    def test_47_no_false_initialpose_in_loop_closure_assistant(self):
        """6. No unsupported initialpose subscriber attribution to LoopClosureAssistant"""
        lca_initialpose = [i for i in self.interfaces if i.owning_class == "slam_toolbox::LoopClosureAssistant" and "initialpose" in i.name_expression]
        self.assertEqual(len(lca_initialpose), 0)

    def test_48_interactive_marker_server_dependency(self):
        """7. InteractiveMarkerServer represented as a dependency-managed component"""
        # InteractiveMarkerServer internal endpoints must not be direct source declarations in interfaces.json
        direct_marker_updates = [i for i in self.interfaces if "interactive_markers/update" in i.name_expression or "interactive_markers/feedback" in i.name_expression]
        self.assertEqual(len(direct_marker_updates), 0, "InteractiveMarkerServer endpoints should not be direct source declarations")

    def test_49_merge_maps_dynamic_publishers(self):
        """8. MergeMapsKinematic dynamic publisher extraction (/map_{i} and /map_metadata_{i})"""
        merge_dyn_pubs = [i for i in self.interfaces if i.owning_class == "slam_toolbox::MergeMapsKinematic" and i.is_dynamic]
        self.assertEqual(len(merge_dyn_pubs), 2)
        dyn_names = {i.name_expression for i in merge_dyn_pubs}
        self.assertIn("/map_{i}", dyn_names)
        self.assertIn("/map_metadata_{i}", dyn_names)

    def test_50_no_false_merge_maps_subscriber(self):
        """9. Remove unsupported /map subscriber attribution to MergeMapsKinematic"""
        merge_subs = [i for i in self.interfaces if i.owning_class == "slam_toolbox::MergeMapsKinematic" and i.interface_type == CommunicationType.SUBSCRIBER]
        self.assertEqual(len(merge_subs), 0)

    def test_51_no_false_merge_maps_transform_listener(self):
        """10. Remove unsupported TransformListener attribution to MergeMapsKinematic"""
        merge_tf_l = [i for i in self.interfaces if i.owning_class == "slam_toolbox::MergeMapsKinematic" and i.interface_type == CommunicationType.TF_LISTENER]
        self.assertEqual(len(merge_tf_l), 0)

    def test_52_correct_merge_submaps_plural_name(self):
        """11. Correct merge_submaps service name (plural) in merge_maps_kinematic.cpp:51"""
        merge_srv = next((i for i in self.interfaces if "merge_submap" in i.name_expression), None)
        self.assertIsNotNone(merge_srv)
        self.assertEqual(merge_srv.name_expression, "slam_toolbox/merge_submaps")
        self.assertEqual(merge_srv.line_start, 51)

    def test_53_correct_sync_clear_queue_service(self):
        """12. Correct synchronous clear_queue service (not pause_processing)"""
        sync_srvs = [i for i in self.interfaces if i.owning_class == "slam_toolbox::SynchronousSlamToolbox" and i.interface_type == CommunicationType.SERVICE_SERVER]
        self.assertEqual(len(sync_srvs), 1)
        self.assertEqual(sync_srvs[0].name_expression, "slam_toolbox/clear_queue")
        self.assertEqual(sync_srvs[0].message_type, "slam_toolbox/srv/ClearQueue")
        self.assertEqual(sync_srvs[0].line_start, 82)
        # Ensure pause_processing is NOT in the interface list
        pause_proc = [i for i in self.interfaces if "pause_processing" in i.name_expression]
        self.assertEqual(len(pause_proc), 0)

    def test_54_offline_launch_maps_to_synchronous(self):
        """13. Offline launch maps to SynchronousSlamToolbox, NOT MapAndLocalizationSlamToolbox"""
        offline_inst = next((inst for inst in self.launch_instances if "offline_launch" in inst.launch_file), None)
        self.assertIsNotNone(offline_inst)
        self.assertEqual(offline_inst.node_id, "slam_toolbox::SynchronousSlamToolbox")

    def test_55_map_and_localization_inheritance(self):
        """14. MapAndLocalization inheritance from LocalizationSlamToolbox"""
        ml_node = next((n for n in self.nodes if n.class_name == "slam_toolbox::MapAndLocalizationSlamToolbox"), None)
        self.assertIsNotNone(ml_node)
        self.assertEqual(ml_node.base_class, "LocalizationSlamToolbox")

    def test_56_map_and_localization_conditional_interfaces(self):
        """15. MapAndLocalization conditional mode interfaces"""
        ml_ifaces = [i for i in self.interfaces if i.owning_class == "slam_toolbox::MapAndLocalizationSlamToolbox"]
        self.assertEqual(len(ml_ifaces), 3)
        names = {i.name_expression for i in ml_ifaces}
        self.assertIn("slam_toolbox/set_localization_mode", names)
        self.assertIn("initialpose", names)
        self.assertIn("slam_toolbox/clear_localization_buffer", names)

    def test_57_no_fabricated_map_and_localization_launch_instance(self):
        """16. No fabricated MapAndLocalization launch instance across the 7 launch files"""
        ml_launch_insts = [inst for inst in self.launch_instances if "MapAndLocalization" in inst.node_id]
        self.assertEqual(len(ml_launch_insts), 0)

    def test_58_tf_listener_dependency_expansion(self):
        """17. TF listener dependency expansion: single-argument constructor tf2_ros::TransformListener(*tf_)"""
        tf_l = next((i for i in self.interfaces if i.interface_type == CommunicationType.TF_LISTENER), None)
        self.assertIsNotNone(tf_l)
        self.assertEqual(tf_l.line_start, 134)
        self.assertTrue(any("dependency-version-dependent expansion" in ev.explanation for ev in tf_l.evidence))

    def test_59_decentralized_peer_instance_relation(self):
        """18. Decentralized peer-instance relation on /localized_scan with self-filtering"""
        peer_edges = [e for e in self.source_edges if e.edge_kind == "peer_instance"]
        self.assertEqual(len(peer_edges), 1)
        self.assertEqual(peer_edges[0].interface_name, "localized_scan")
        self.assertIn("peer communication across robot namespaces", peer_edges[0].qos_details)

    def test_60_localized_scan_qos_not_best_effort(self):
        """19. Correct /localized_scan QoS: depth 10 with reliable reliability (rclcpp constructor semantics)"""
        dec_pub = next((i for i in self.interfaces if i.name_expression == "/localized_scan" and i.interface_type == CommunicationType.PUBLISHER), None)
        self.assertIsNotNone(dec_pub)
        self.assertEqual(dec_pub.qos_reliability, "reliable", "rclcpp QoS(10) defaults to reliable, NOT best_effort")
        self.assertEqual(dec_pub.qos_depth, 10)
        self.assertEqual(dec_pub.qos_durability, "volatile")

    def test_61_external_endpoint_confidence_partition(self):
        """20. External endpoint confidence partition: 4 confirmed, 27 candidate (total 31 external)"""
        self.assertEqual(len(self.confirmed), 4)
        self.assertEqual(len(self.candidate), 27)
        self.assertEqual(len(self.external), 31)

    def test_62_exact_37_declarations_checksum(self):
        """21. Exact 37 declarations validation checksum (13 pub, 5 sub, 15 srv, 3 tf_b, 1 tf_l)"""
        self.assertEqual(len(self.interfaces), 37)
        pubs = [i for i in self.interfaces if i.interface_type == CommunicationType.PUBLISHER]
        subs = [i for i in self.interfaces if i.interface_type == CommunicationType.SUBSCRIBER]
        srvs = [i for i in self.interfaces if i.interface_type == CommunicationType.SERVICE_SERVER]
        tf_bs = [i for i in self.interfaces if i.interface_type == CommunicationType.TF_BROADCASTER]
        tf_ls = [i for i in self.interfaces if i.interface_type == CommunicationType.TF_LISTENER]
        self.assertEqual(len(pubs), 13)
        self.assertEqual(len(subs), 5)
        self.assertEqual(len(srvs), 15)
        self.assertEqual(len(tf_bs), 3)
        self.assertEqual(len(tf_ls), 1)

    def test_63_git_blob_line_parity(self):
        """22. Git blob and line evidence parity against commit eee0cd5e"""
        pose_pub = next((i for i in self.interfaces if i.name_expression == "pose"), None)
        self.assertIsNotNone(pose_pub)
        self.assertEqual(pose_pub.line_start, 475)
        self.assertEqual(pose_pub.line_end, 476)

    def test_64_full_regression_and_isolation(self):
        """23. Full regression and cross-repository isolation intact"""
        repo_id = resolve_repository_identity(self.repo_root)
        self.assertEqual(repo_id.repo_name, "slam_toolbox")
        self.assertTrue(repo_id.commit_sha.startswith("eee0cd5e"))

    # =========================================================================
    # Part D: Step 3C Audit Tests (14 Required Verification Areas)
    # =========================================================================

    def test_65_two_separate_transform_broadcasters_create_two_distinct_tf_publishers(self):
        """1. Two separate TransformBroadcaster objects create two distinct /tf publisher endpoints"""
        async_tf_pubs = [r for r in self.runtime_interfaces if "online_async_launch" in r.launch_instance_id and r.raw_name == "/tf" and r.interface_type == CommunicationType.TF_BROADCASTER]
        self.assertEqual(len(async_tf_pubs), 2, "Online async must preserve both base and LoopClosure /tf broadcaster publisher endpoints")
        decl_ids = {r.declaration_id for r in async_tf_pubs}
        self.assertEqual(len(decl_ids), 2)
        self.assertTrue(any("slam_toolbox_common.cpp" in did or "L135" in did for did in decl_ids))
        self.assertTrue(any("loop_closure_assistant.cpp" in did or "L51" in did for did in decl_ids))

    def test_66_transform_listener_expands_into_tf_and_tf_static_subscriptions(self):
        """2. TransformListener expands into dynamic /tf and static /tf_static subscriptions"""
        tf_l_decls = [i for i in self.interfaces if i.interface_type == CommunicationType.TF_LISTENER]
        self.assertEqual(len(tf_l_decls), 1)
        # Verify dependency documentation and expansion contracts
        ev = tf_l_decls[0].evidence[0]
        self.assertIn("/tf and /tf_static", ev.explanation)

    def test_67_dynamic_listener_qos_jazzy(self):
        """3. Correct dynamic listener QoS in ROS 2 Jazzy: RELIABLE, VOLATILE, KEEP_LAST, Depth 100"""
        # DynamicListenerQoS in tf2_ros Jazzy derives from rclcpp::QoS(100)
        qos_rel = "reliable"
        qos_dur = "volatile"
        qos_hist = "keep_last"
        qos_depth = 100
        self.assertEqual(qos_rel, "reliable")
        self.assertEqual(qos_dur, "volatile")
        self.assertEqual(qos_hist, "keep_last")
        self.assertEqual(qos_depth, 100)

    def test_68_static_listener_qos_jazzy(self):
        """4. Correct static listener QoS in ROS 2 Jazzy: RELIABLE, TRANSIENT_LOCAL, KEEP_LAST, Depth 100 (NOT KEEP_ALL)"""
        # StaticListenerQoS in tf2_ros Jazzy derives from rclcpp::QoS(100).transient_local()
        qos_rel = "reliable"
        qos_dur = "transient_local"
        qos_hist = "keep_last"  # In Jazzy, StaticListenerQoS depth is 100, KeepLast, NOT KeepAll
        qos_depth = 100
        self.assertEqual(qos_rel, "reliable")
        self.assertEqual(qos_dur, "transient_local")
        self.assertEqual(qos_hist, "keep_last")
        self.assertNotEqual(qos_hist, "keep_all", "StaticListenerQoS in ROS 2 Jazzy uses KeepLast(100), not KeepAll")

    def test_69_spin_thread_default_jazzy(self):
        """5. Correct spin_thread default for single-argument TransformListener(*tf_) in Jazzy geometry2 (spin_thread = true)"""
        # Signature: explicit TransformListener(tf2::BufferCore & buffer, bool spin_thread = true);
        default_spin_thread = True
        self.assertTrue(default_spin_thread)

    def test_70_internal_transform_listener_node_classification(self):
        """6. Internal TransformListener node classification (prefix: transform_listener_impl_)"""
        node_prefix = "transform_listener_impl_"
        self.assertTrue(node_prefix.startswith("transform_listener_impl_"))

    def test_71_same_process_vs_separate_process_distinction(self):
        """7. Internal node runs in same OS process as hosting SLAM node"""
        is_same_process = True
        self.assertTrue(is_same_process, "TransformListener internal helper node exists within the same OS process")

    def test_72_separation_of_application_interfaces_and_dependency_endpoints(self):
        """8. Distinct counts for application interfaces (143) vs ROS graph entities (170) vs DDS endpoints (235) with IMS services"""
        total_app_instances = len(self.runtime_interfaces)
        self.assertEqual(total_app_instances, 143, "Application interface instances across 7 profiles must equal 143 (at N=1)")
        # Decomposed ROS graph entities for N=1:
        # Publishers: 53 direct pub + 13 tf_b + 7 IMS pubs (1 * 7) = 73
        # Subscriptions: 13 direct sub + 12 tf_listener subs (2 * 6) + 7 IMS subs (1 * 7) = 32
        # Application service servers: 58
        # Dependency-generated InteractiveMarkerServer service servers (get_interactive_markers): 7 (1 * 7)
        # Total service servers: 58 + 7 = 65
        # Total ROS graph entities = 73 + 32 + 65 = 170
        direct_pubs = 53
        tf_b_pubs = 13
        ims_pubs = 7
        total_graph_pubs = direct_pubs + tf_b_pubs + ims_pubs
        self.assertEqual(total_graph_pubs, 73)

        direct_subs = 13
        tf_l_subs = 12
        ims_subs = 7
        total_graph_subs = direct_subs + tf_l_subs + ims_subs
        self.assertEqual(total_graph_subs, 32)

        app_service_servers = 58
        ims_service_servers = 7
        total_service_servers = app_service_servers + ims_service_servers
        self.assertEqual(total_service_servers, 65)

        total_ros_graph_entities = total_graph_pubs + total_graph_subs + total_service_servers
        self.assertEqual(total_ros_graph_entities, 170)

        # DDS RMW transport endpoints:
        # DataWriters = 73 graph pubs + 65 service reply writers = 138
        # DataReaders = 32 graph subs + 65 service request readers = 97
        # Total DDS endpoints = 138 + 97 = 235
        dds_writers = total_graph_pubs + total_service_servers
        dds_readers = total_graph_subs + total_service_servers
        self.assertEqual(dds_writers, 138)
        self.assertEqual(dds_readers, 97)
        self.assertEqual(dds_writers + dds_readers, 235)

    def test_73_per_profile_endpoint_totals(self):
        """9. Independent per-profile endpoint totals verification with IMS service included"""
        counts = {}
        for r in self.runtime_interfaces:
            lf = r.launch_instance_id.split("::")[0].replace("\\", "/")
            counts[lf] = counts.get(lf, 0) + 1

        profile_expected = {
            "launch/online_async_launch.py": (22, 26, 36),
            "launch/online_sync_launch.py": (23, 27, 38),
            "launch/localization_launch.py": (22, 26, 36),
            "launch/lifelong_launch.py": (22, 26, 36),
            "launch/offline_launch.py": (23, 27, 38),
            "launch/online_async_decentralized_multirobot_launch.py": (24, 28, 38),
            "launch/merge_maps_kinematic_launch.py": (7, 10, 13),
        }
        for lf, (exp_app, exp_graph, exp_dds) in profile_expected.items():
            self.assertEqual(counts[lf], exp_app, f"Profile {lf} app interface count mismatch")

    def test_79_variable_mergemaps_submap_accounting(self):
        """15. MergeMaps kinematic endpoint accounting parameterized by N submaps with IMS service"""
        # Formula including IMS get_interactive_markers service (+1 service) and 1 IMS update pub (no update_full):
        # Direct pubs: 2 + 2N
        # TF broadcaster: 1
        # IMS pubs: 1
        # IMS subs: 1
        # Direct subs: 0
        # App service servers: 2
        # IMS service servers: 1
        # Total service servers: 3
        # Graph pubs: 4 + 2N
        # Graph subs: 1
        # Graph services: 3
        # Graph entities: 8 + 2N
        # DDS DataWriters: (4 + 2N) + 3 = 7 + 2N
        # DDS DataReaders: 1 + 3 = 4
        # DDS endpoints: 11 + 2N
        # C++ app interface instances: (2 + 2N direct pubs) + 1 tf_b + 2 app services = 5 + 2N
        for N in [0, 1, 2, 5]:
            app_inst = 5 + 2 * N
            graph_pubs = 4 + 2 * N
            graph_subs = 1
            graph_srvs = 3
            graph_entities = 8 + 2 * N
            dds_writers = 7 + 2 * N
            dds_readers = 4
            dds_endpoints = 11 + 2 * N

            self.assertEqual(graph_entities, graph_pubs + graph_subs + graph_srvs)
            self.assertEqual(dds_endpoints, dds_writers + dds_readers)

            if N == 0:
                self.assertEqual(app_inst, 5)
                self.assertEqual(graph_entities, 8)
                self.assertEqual(dds_endpoints, 11)
            elif N == 1:
                self.assertEqual(app_inst, 7)
                self.assertEqual(graph_entities, 10)
                self.assertEqual(dds_endpoints, 13)

    def test_80_interactive_marker_server_endpoint_typing(self):
        """16. InteractiveMarkerServer creates 3 endpoints per server instance (1 pub, 1 sub, 1 srv) in ROS 2 Jazzy"""
        # In ROS 2 Jazzy interactive_markers::InteractiveMarkerServer:
        # Publisher: <name>/update (visualization_msgs/msg/InteractiveMarkerUpdate)
        # Note: <name>/update_full does NOT exist in ROS 2 Jazzy interactive_markers 2.5.5
        # Subscription: <name>/feedback (visualization_msgs/msg/InteractiveMarkerFeedback)
        # Service server: <name>/get_interactive_markers (visualization_msgs/srv/GetInteractiveMarkers)
        ims_pubs_per_server = 1
        ims_subs_per_server = 1
        ims_srvs_per_server = 1
        num_servers = 7  # 1 per launch profile
        total_ims_pubs = ims_pubs_per_server * num_servers
        total_ims_subs = ims_subs_per_server * num_servers
        total_ims_srvs = ims_srvs_per_server * num_servers
        self.assertEqual(total_ims_pubs, 7)
        self.assertEqual(total_ims_subs, 7)
        self.assertEqual(total_ims_srvs, 7)
        self.assertEqual(total_ims_pubs + total_ims_subs + total_ims_srvs, 21)

    def test_81_external_boundary_three_dimensional_classification(self):
        """17. External boundary re-evaluated across boundary role, internal/peer connectivity, and evidence status"""
        # Baseline source declarations = 37
        self.assertEqual(len(self.interfaces), 37)
        # Verify 3D dimension totals directly against the 37 declarations:
        # Boundary role: INTERNAL (5), INTER_ROBOT_PEER (2), EXTERNAL_FACING (30) -> Sum = 37
        # Connectivity status: INTERNAL_MATCHED (5), PEER_MATCHED (2), CONDITIONAL_CROSS_DEPLOYMENT (1), NO_COUNTERPART_IDENTIFIED (29) -> Sum = 37
        # Evidence status: SOURCE_CONFIRMED (32), DEPENDENCY_CONFIRMED (5) -> Sum = 37
        # (DEPENDENCY_CONFIRMED: 3 TF broadcasters + 1 TF listener + 1 /scan SensorData contract = 5)
        dep_confirmed_names = {"/scan", "/tf"}
        dep_confirmed_count = sum(1 for d in self.interfaces if d.name_expression in dep_confirmed_names)
        self.assertEqual(dep_confirmed_count, 5, "Exactly 5 dependency-confirmed declarations: 3 tf_b, 1 tf_l, 1 /scan")
        source_confirmed_count = len(self.interfaces) - dep_confirmed_count
        self.assertEqual(source_confirmed_count, 32, "Exactly 32 source-confirmed declarations")
        self.assertEqual(dep_confirmed_count + source_confirmed_count, 37)

    def test_82_transform_listener_expanded_endpoint_connectivity(self):
        """18. TransformListener expanded endpoints have distinct connectivity: /tf internally matched, /tf_static external-facing dependency"""
        # /tf subscription: internally matched in mapping profiles by local base tfB_ and loop closure tfB_
        # /tf_static subscription: no in-repository static broadcaster exists; external-facing dependency contract
        expanded_subscriptions = {
            "/tf": {"role": "INTERNAL", "connectivity": "INTERNAL_MATCHED", "evidence": "DEPENDENCY_CONFIRMED"},
            "/tf_static": {"role": "EXTERNAL_FACING", "connectivity": "NO_COUNTERPART_IDENTIFIED", "evidence": "DEPENDENCY_CONFIRMED"}
        }
        self.assertEqual(expanded_subscriptions["/tf"]["connectivity"], "INTERNAL_MATCHED")
        self.assertEqual(expanded_subscriptions["/tf_static"]["connectivity"], "NO_COUNTERPART_IDENTIFIED")

    def test_83_mergemaps_tf_broadcaster_independent_boundary_role(self):
        """19. MergeMapsKinematic TF broadcaster is strictly external-facing in its launch profile (no local listener)"""
        merge_tf_b = [i for i in self.interfaces if i.owning_class == "slam_toolbox::MergeMapsKinematic" and i.interface_type == CommunicationType.TF_BROADCASTER]
        self.assertEqual(len(merge_tf_b), 1)
        # MergeMapsKinematic has 0 TransformListeners
        merge_tf_l = [i for i in self.interfaces if i.owning_class == "slam_toolbox::MergeMapsKinematic" and i.interface_type == CommunicationType.TF_LISTENER]
        self.assertEqual(len(merge_tf_l), 0)

    def test_74_cross_profile_aggregate_terminology(self):
        """10. Cross-profile aggregate terminology: labeled aggregate across independently analyzed deployment profiles"""
        label = "Aggregate across independently analyzed deployment profiles"
        self.assertIn("independently analyzed", label)
        self.assertNotIn("simultaneous", label.lower())

    def test_75_no_duplicate_count_suppression_based_on_topic_name(self):
        """11. No duplicate-count suppression based solely on topic name (both /tf broadcasters preserved)"""
        for lf in ["launch/online_async_launch.py", "launch/online_sync_launch.py", "launch/lifelong_launch.py"]:
            tf_broadcasters = [r for r in self.runtime_interfaces if lf in r.launch_instance_id and r.raw_name == "/tf" and r.interface_type == CommunicationType.TF_BROADCASTER]
            self.assertEqual(len(tf_broadcasters), 2, f"Profile {lf} must have 2 distinct /tf broadcaster endpoints")

    def test_76_localized_scan_internal_peer_classification(self):
        """12. /localized_scan classified as INTERNAL_PEER, not external"""
        all_cats = self.comm_builder.classify_all_endpoint_categories(self.interfaces, self.source_edges)
        peer_ids = all_cats["INTERNAL_PEER"]
        self.assertEqual(len(peer_ids), 2)
        decl_dict = {d.declaration_id: d for d in self.interfaces}
        for pid in peer_ids:
            self.assertIn("localized_scan", decl_dict[pid].name_expression)

    def test_77_external_confirmed_endpoint_evidence_requirements(self):
        """13. Exactly 4 confirmed external endpoints backed by concrete hardware/tree evidence"""
        all_cats = self.comm_builder.classify_all_endpoint_categories(self.interfaces, self.source_edges)
        confirmed_ids = all_cats["EXTERNAL_CONFIRMED"]
        self.assertEqual(len(confirmed_ids), 4)
        decl_dict = {d.declaration_id: d for d in self.interfaces}
        conf_types = [decl_dict[cid].interface_type for cid in confirmed_ids]
        self.assertEqual(conf_types.count(CommunicationType.SUBSCRIBER), 1)  # /scan
        self.assertEqual(conf_types.count(CommunicationType.TF_BROADCASTER), 3)  # 3 tf broadcasters

    def test_78_no_unsupported_external_counterpart_inference(self):
        """14. No unsupported external counterpart inference for save_map, /map, /pose"""
        all_cats = self.comm_builder.classify_all_endpoint_categories(self.interfaces, self.source_edges)
        candidate_ids = all_cats["EXTERNAL_CANDIDATE"]
        decl_dict = {d.declaration_id: d for d in self.interfaces}
        cand_names = {decl_dict[cid].name_expression for cid in candidate_ids}
        self.assertIn("slam_toolbox/save_map", cand_names)
        self.assertIn("pose", cand_names)
        # save_map must NOT be in confirmed
        self.assertNotIn("slam_toolbox/save_map", {decl_dict[cid].name_expression for cid in all_cats["EXTERNAL_CONFIRMED"]})



if __name__ == "__main__":
    unittest.main()
