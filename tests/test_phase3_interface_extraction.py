"""
ArchSynth Phase 3 Unit Tests - ROS2 Interface Extraction and Communication Graph Recovery.

Tests verify:
1. Python AST interface extraction (ActionClient, ServiceClient, Publisher, Subscriber)
2. C++ regex/AST interface extraction (create_publisher, create_subscription, create_action_server, etc.)
3. Action protocol deduplication and protocol child entity tracking
4. Three-state QoS evaluation (COMPATIBLE, INCOMPATIBLE, UNKNOWN)
5. Separation of source potential graph vs deployment runtime graph
6. REP-134 name resolution and ordered remapping rules
7. External connection classification with evidence
8. Zero fabricated edges and dual-endpoint evidence validation
"""

import json
import unittest
from pathlib import Path

from src.schema import (
    CommunicationType, QoSCompatibility, RemappingRule,
    InterfaceDeclaration, RuntimeInterfaceInstance, ROS2Node,
    EntityType, NodeCategory, ResolutionStatus,
    EvidenceItem, EvidenceType
)
from src.interface_extractor import (
    InterfaceExtractor, normalize_interface_type, extract_all_repository_interfaces
)
from src.communication_builder import (
    CommunicationBuilder, resolve_ros2_name, evaluate_qos_compatibility,
    run_phase3_communication_pipeline
)


class TestPhase3InterfaceExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path("case_studies/nav2")

    def test_normalize_interface_type(self):
        """Test normalization of ROS2 message and service types across C++ and Python syntax"""
        self.assertEqual(normalize_interface_type("nav2_msgs::msg::Path"), "nav2_msgs/msg/Path")
        self.assertEqual(normalize_interface_type("nav2_msgs.msg.Path"), "nav2_msgs/msg/Path")
        self.assertEqual(normalize_interface_type("nav2_msgs::action::NavigateToPose"), "nav2_msgs/action/NavigateToPose")
        self.assertEqual(normalize_interface_type("std_srvs::srv::Empty"), "std_srvs/srv/Empty")
        self.assertEqual(normalize_interface_type("geometry_msgs::msg::Twist::SharedPtr"), "geometry_msgs/msg/Twist")

    def test_python_basic_navigator_interfaces(self):
        """Verify Python AST interface extraction on BasicNavigator (ActionClients and ServiceClients)"""
        nav_file = "nav2_simple_commander/nav2_simple_commander/robot_navigator.py"
        full_path = self.repo_root / nav_file
        if not full_path.exists():
            self.skipTest(f"Nav2 file not found: {full_path}")

        node = ROS2Node(
            id="nav2_simple_commander::BasicNavigator",
            name="basic_navigator",
            fully_qualified_name="/basic_navigator",
            class_name="BasicNavigator",
            package_name="nav2_simple_commander",
            entity_type=EntityType.ROS_NODE,
            node_category=NodeCategory.CLIENT,
            source_language="python",
            is_test=False,
            is_lifecycle=False,
            source_file=nav_file,
            evidence=[EvidenceItem(file=nav_file, line_start=40, evidence_type=EvidenceType.NODE_DEFINITION, source="test")]
        )

        extractor = InterfaceExtractor(self.repo_root)
        decls = extractor.extract_node_interfaces(node)

        # BasicNavigator should have at least 15 action clients and 10 service clients
        action_clients = [d for d in decls if d.interface_type == CommunicationType.ACTION_CLIENT]
        service_clients = [d for d in decls if d.interface_type == CommunicationType.SERVICE_CLIENT]

        self.assertGreaterEqual(len(action_clients), 15, "BasicNavigator should have at least 15 action clients")
        self.assertGreaterEqual(len(service_clients), 10, "BasicNavigator should have at least 10 service clients")

        # Verify key actions exist
        action_names = {d.name_expression for d in action_clients}
        self.assertIn("navigate_to_pose", action_names)
        self.assertIn("navigate_through_poses", action_names)
        self.assertIn("follow_path", action_names)
        self.assertIn("compute_path_to_pose", action_names)

        # Verify all declarations carry evidence
        for d in decls:
            self.assertGreater(len(d.evidence), 0)
            self.assertEqual(d.owner_node_id, node.id)

    def test_cpp_controller_server_interfaces(self):
        """Verify C++ interface extraction on ControllerServer (publishers, subscribers, action server)"""
        ctrl_file = "nav2_controller/src/controller_server.cpp"
        full_path = self.repo_root / ctrl_file
        if not full_path.exists():
            self.skipTest(f"Nav2 file not found: {full_path}")

        node = ROS2Node(
            id="nav2_controller::nav2_controller::ControllerServer",
            name="controller_server",
            fully_qualified_name="/controller_server",
            class_name="ControllerServer",
            package_name="nav2_controller",
            entity_type=EntityType.LIFECYCLE_NODE,
            node_category=NodeCategory.CONTROL,
            source_language="cpp",
            is_test=False,
            is_lifecycle=True,
            source_file=ctrl_file,
            evidence=[EvidenceItem(file=ctrl_file, line_start=34, evidence_type=EvidenceType.NODE_DEFINITION, source="test")]
        )

        extractor = InterfaceExtractor(self.repo_root)
        decls = extractor.extract_node_interfaces(node)

        # ControllerServer hosts follow_path action server and cmd_vel publisher
        action_servers = [d for d in decls if d.interface_type == CommunicationType.ACTION_SERVER]
        publishers = [d for d in decls if d.interface_type == CommunicationType.PUBLISHER]

        act_names = {d.name_expression for d in action_servers}
        self.assertIn("follow_path", act_names)

        pub_names = {d.name_expression for d in publishers}
        self.assertTrue("transformed_global_plan" in pub_names or "tracking_feedback" in pub_names)

    def test_cpp_planner_server_interfaces(self):
        """Verify C++ interface extraction on PlannerServer (action server compute_path_to_pose)"""
        planner_file = "nav2_planner/src/planner_server.cpp"
        full_path = self.repo_root / planner_file
        if not full_path.exists():
            self.skipTest(f"Nav2 file not found: {full_path}")

        node = ROS2Node(
            id="nav2_planner::nav2_planner::PlannerServer",
            name="planner_server",
            fully_qualified_name="/planner_server",
            class_name="PlannerServer",
            package_name="nav2_planner",
            entity_type=EntityType.LIFECYCLE_NODE,
            node_category=NodeCategory.PLANNING,
            source_language="cpp",
            is_test=False,
            is_lifecycle=True,
            source_file=planner_file,
            evidence=[EvidenceItem(file=planner_file, line_start=38, evidence_type=EvidenceType.NODE_DEFINITION, source="test")]
        )

        extractor = InterfaceExtractor(self.repo_root)
        decls = extractor.extract_node_interfaces(node)

        action_servers = [d for d in decls if d.interface_type == CommunicationType.ACTION_SERVER]
        act_names = {d.name_expression for d in action_servers}
        self.assertIn("compute_path_to_pose", act_names)

    def test_action_protocol_deduplication(self):
        """Verify that high-level actions produce 5 underlying DDS protocol entities without double-counting"""
        decl = InterfaceDeclaration(
            declaration_id="test::Server::action_server::navigate_to_pose#L50",
            owner_node_id="nav2_bt_navigator::BtNavigator",
            interface_type=CommunicationType.ACTION_SERVER,
            name_expression="navigate_to_pose",
            message_type="nav2_msgs/action/NavigateToPose",
            direction="in",
            source_file="nav2_bt_navigator/src/bt_navigator.cpp",
            line_start=50,
            discovery_method="test",
            evidence=[EvidenceItem(file="nav2_bt_navigator/src/bt_navigator.cpp", line_start=50, evidence_type=EvidenceType.ACTION_CREATION, source="test")]
        )

        builder = CommunicationBuilder([decl], [], {"nav2_bt_navigator"})
        protocols = builder.build_action_protocol_entities([decl])

        self.assertEqual(len(protocols), 1)
        proto = protocols[0]
        self.assertEqual(proto.action_name, "/navigate_to_pose")
        self.assertEqual(proto.send_goal_service, "/navigate_to_pose/_action/send_goal")
        self.assertEqual(proto.cancel_goal_service, "/navigate_to_pose/_action/cancel_goal")
        self.assertEqual(proto.get_result_service, "/navigate_to_pose/_action/get_result")
        self.assertEqual(proto.feedback_topic, "/navigate_to_pose/_action/feedback")
        self.assertEqual(proto.status_topic, "/navigate_to_pose/_action/status")

        # Verify potential graph does NOT produce topic/service edges for protocol internals
        edges = builder.build_source_potential_graph([decl])
        # Only high-level actions matched when counterpart exists; protocol entities are never high-level edges
        for edge in edges:
            self.assertNotIn("/_action/", edge.interface_name)

    def test_three_state_qos_evaluation(self):
        """Verify QoSCompatibility: COMPATIBLE, INCOMPATIBLE, and UNKNOWN"""
        # Compatible: all 4 policies known and compatible
        status1, _ = evaluate_qos_compatibility(
            pub_reliability="reliable", pub_durability="transient_local",
            sub_reliability="reliable", sub_durability="transient_local",
            pub_deadline=1.0, sub_deadline=1.0,
            pub_liveliness="automatic", sub_liveliness="automatic"
        )
        self.assertEqual(status1, QoSCompatibility.COMPATIBLE)

        # Incompatible: Best effort publisher to Reliable subscriber
        status3, _ = evaluate_qos_compatibility(
            pub_reliability="best_effort", pub_durability="volatile",
            sub_reliability="reliable", sub_durability="volatile"
        )
        self.assertEqual(status3, QoSCompatibility.INCOMPATIBLE)

        # Incompatible: Volatile publisher to Transient Local subscriber
        status4, _ = evaluate_qos_compatibility(
            pub_reliability="reliable", pub_durability="volatile",
            sub_reliability="reliable", sub_durability="transient_local"
        )
        self.assertEqual(status4, QoSCompatibility.INCOMPATIBLE)

        # Unknown: Reliability and durability compatible, but deadline and liveliness unevaluated
        status_uneval, msg_uneval = evaluate_qos_compatibility(
            pub_reliability="reliable", pub_durability="volatile",
            sub_reliability="reliable", sub_durability="volatile"
        )
        self.assertEqual(status_uneval, QoSCompatibility.UNKNOWN)
        self.assertIn("deadline and liveliness unevaluated", msg_uneval)

        # Unknown: Missing QoS specs
        status5, _ = evaluate_qos_compatibility(
            pub_reliability=None, pub_durability=None,
            sub_reliability=None, sub_durability=None
        )
        self.assertEqual(status5, QoSCompatibility.UNKNOWN)

    def test_ros2_static_remapping_and_name_resolution(self):
        """Verify ROS 2 Static Remapping Design & REP-144 name resolution with namespaces and ordered rules"""
        # Global name
        res, _ = resolve_ros2_name("/global/topic", "/ns", "node")
        self.assertEqual(res, "/global/topic")

        # Private name
        res, _ = resolve_ros2_name("~/private_topic", "/ns", "my_node")
        self.assertEqual(res, "/ns/my_node/private_topic")

        # Relative name
        res, _ = resolve_ros2_name("scan", "/robot1", "node")
        self.assertEqual(res, "/robot1/scan")
        res, _ = resolve_ros2_name("scan", "", "node")
        self.assertEqual(res, "/scan")

        # Ordered remappings
        rules = [
            RemappingRule(from_name="cmd_vel", to_name="cmd_vel_nav", order=0),
            RemappingRule(from_name="scan", to_name="base_scan", order=1),
        ]
        res1, _ = resolve_ros2_name("cmd_vel", "", "controller", rules)
        self.assertEqual(res1, "/cmd_vel_nav")

        # Node-specific remapping rule
        node_rules = [
            RemappingRule(from_name="cmd_vel", to_name="cmd_vel_nav", target_node="controller", order=0),
            RemappingRule(from_name="cmd_vel", to_name="cmd_vel_teleop", target_node="teleop", order=1),
        ]
        res_ctrl, _ = resolve_ros2_name("cmd_vel", "", "controller", node_rules)
        res_tele, _ = resolve_ros2_name("cmd_vel", "", "teleop", node_rules)
        self.assertEqual(res_ctrl, "/cmd_vel_nav")
        self.assertEqual(res_tele, "/cmd_vel_teleop")

    def test_source_potential_vs_deployment_runtime_graph_separation(self):
        """Verify BasicNavigator client edges exist in source potential graph but NOT in bringup deployment graph"""
        # Client declaration (BasicNavigator)
        client_decl = InterfaceDeclaration(
            declaration_id="client::nav2_simple_commander::BasicNavigator::action_client::navigate_to_pose#L100",
            owner_node_id="nav2_simple_commander::BasicNavigator",
            interface_type=CommunicationType.ACTION_CLIENT,
            name_expression="navigate_to_pose",
            message_type="nav2_msgs/action/NavigateToPose",
            direction="out",
            source_file="nav2_simple_commander/nav2_simple_commander/robot_navigator.py",
            line_start=100,
            discovery_method="test",
            evidence=[EvidenceItem(file="robot_navigator.py", line_start=100, evidence_type=EvidenceType.ACTION_CREATION, source="test")]
        )

        # Server declaration (BtNavigator)
        server_decl = InterfaceDeclaration(
            declaration_id="server::nav2_bt_navigator::BtNavigator::action_server::navigate_to_pose#L50",
            owner_node_id="nav2_bt_navigator::nav2_bt_navigator::BtNavigator",
            interface_type=CommunicationType.ACTION_SERVER,
            name_expression="navigate_to_pose",
            message_type="nav2_msgs/action/NavigateToPose",
            direction="in",
            source_file="nav2_bt_navigator/src/bt_navigator.cpp",
            line_start=50,
            discovery_method="test",
            evidence=[EvidenceItem(file="bt_navigator.cpp", line_start=50, evidence_type=EvidenceType.ACTION_CREATION, source="test")]
        )

        builder = CommunicationBuilder([client_decl, server_decl], [], {"nav2_simple_commander", "nav2_bt_navigator"})

        # In source potential graph, this edge MUST exist
        source_edges = builder.build_source_potential_graph([client_decl, server_decl])
        self.assertEqual(len(source_edges), 1)
        self.assertEqual(source_edges[0].interface_name, "navigate_to_pose")
        self.assertEqual(source_edges[0].graph_level, "source_potential")

        # But in bringup deployment runtime graph, BasicNavigator is NOT launched!
        # Only BtNavigator is deployed in bringup
        server_runtime = RuntimeInterfaceInstance(
            runtime_instance_id="runtime::bringup::server::navigate_to_pose",
            declaration_id=server_decl.declaration_id,
            launch_instance_id="bringup::bt_navigator",
            owner_node_id=server_decl.owner_node_id,
            interface_type=CommunicationType.ACTION_SERVER,
            raw_name="navigate_to_pose",
            resolved_name="/navigate_to_pose",
            message_type="nav2_msgs/action/NavigateToPose",
            direction="in",
            namespace="",
            deployment_profile="bringup",
            evidence=server_decl.evidence
        )
        runtime_edges = builder.build_deployment_runtime_graph([server_runtime])
        # Since BasicNavigator has no runtime instance in bringup, runtime_edges must be 0!
        self.assertEqual(len(runtime_edges), 0, "BasicNavigator client must not appear in bringup deployment graph")

    def test_evidence_presence_on_all_matched_edges(self):
        """Verify that every matched edge contains both source and target evidence items"""
        pub_decl = InterfaceDeclaration(
            declaration_id="pub::nodeA::topic::data#L10",
            owner_node_id="pkgA::NodeA",
            interface_type=CommunicationType.PUBLISHER,
            name_expression="data",
            message_type="std_msgs/msg/String",
            direction="out",
            source_file="pkgA/nodeA.cpp",
            line_start=10,
            discovery_method="test",
            evidence=[EvidenceItem(file="pkgA/nodeA.cpp", line_start=10, evidence_type=EvidenceType.PUBLISHER_CREATION, source="test")]
        )
        sub_decl = InterfaceDeclaration(
            declaration_id="sub::nodeB::topic::data#L20",
            owner_node_id="pkgB::NodeB",
            interface_type=CommunicationType.SUBSCRIBER,
            name_expression="data",
            message_type="std_msgs/msg/String",
            direction="in",
            source_file="pkgB/nodeB.cpp",
            line_start=20,
            discovery_method="test",
            evidence=[EvidenceItem(file="pkgB/nodeB.cpp", line_start=20, evidence_type=EvidenceType.SUBSCRIBER_CREATION, source="test")]
        )

        builder = CommunicationBuilder([pub_decl, sub_decl], [], {"pkgA", "pkgB"})
        edges = builder.build_source_potential_graph([pub_decl, sub_decl])

        self.assertEqual(len(edges), 1)
        edge = edges[0]
        self.assertGreater(len(edge.evidence_source), 0, "Source evidence must be present")
        self.assertGreater(len(edge.evidence_target), 0, "Target evidence must be present")
        self.assertEqual(edge.evidence_source[0].file, "pkgA/nodeA.cpp")
        self.assertEqual(edge.evidence_target[0].file, "pkgB/nodeB.cpp")

    def test_service_connections_recovery(self):
        """Verify service client/server matching across Python client and C++ server"""
        client_decl = InterfaceDeclaration(
            declaration_id="client::nav2_simple_commander::BasicNavigator::service_client::collision_monitor/toggle#L100",
            owner_node_id="nav2_simple_commander::BasicNavigator",
            interface_type=CommunicationType.SERVICE_CLIENT,
            name_expression="collision_monitor/toggle",
            message_type="nav2_msgs/srv/Toggle",
            direction="out",
            source_file="nav2_simple_commander/robot_navigator.py",
            line_start=100,
            discovery_method="test",
            evidence=[EvidenceItem(file="nav2_simple_commander/robot_navigator.py", line_start=100, evidence_type=EvidenceType.SERVICE_CREATION, source="test")]
        )
        server_decl = InterfaceDeclaration(
            declaration_id="server::nav2_collision_monitor::CollisionMonitor::service_server::~/toggle#L50",
            owner_node_id="nav2_collision_monitor::CollisionMonitor",
            interface_type=CommunicationType.SERVICE_SERVER,
            name_expression="~/toggle",
            message_type="nav2_msgs/srv/Toggle",
            direction="in",
            source_file="nav2_collision_monitor/collision_monitor.cpp",
            line_start=50,
            discovery_method="test",
            evidence=[EvidenceItem(file="nav2_collision_monitor/collision_monitor.cpp", line_start=50, evidence_type=EvidenceType.SERVICE_CREATION, source="test")]
        )

        builder = CommunicationBuilder([client_decl, server_decl], [], {"nav2_simple_commander", "nav2_collision_monitor"})
        edges = builder.build_source_potential_graph([client_decl, server_decl])

        self.assertEqual(len(edges), 1)
        srv_edge = edges[0]
        self.assertEqual(srv_edge.communication_type, "service")
        self.assertEqual(srv_edge.source_node_id, "nav2_simple_commander::BasicNavigator")
        self.assertEqual(srv_edge.target_node_id, "nav2_collision_monitor::CollisionMonitor")
        self.assertEqual(srv_edge.interface_name, "collision_monitor/toggle")
        self.assertEqual(srv_edge.message_type, "nav2_msgs/srv/Toggle")


if __name__ == "__main__":
    unittest.main()
