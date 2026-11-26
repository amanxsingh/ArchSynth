"""
ArchSynth BehaviorTreeAnalyzer - Phase 4: Behavior Tree Recovery.

Analyzes BehaviorTree.CPP navigation trees in Nav2:
1. Discovers and parses all BehaviorTree XML definitions (nav2_bt_navigator/behavior_trees/).
2. Extracts hierarchical tree structure:
   - Control nodes (PipelineSequence, RecoveryNode, Fallback, ReactiveSequence, etc.)
   - Decorator nodes (RateController, Inverter, DistanceController, etc.)
   - Action nodes (ComputePathToPose, FollowPath, Spin, Wait, BackUp, etc.)
   - Condition nodes (IsStuck, GoalReached, TransformAvailable, etc.)
3. Extracts blackboard port dataflows (keys like {path}, {goal}, {selected_planner}).
4. Maps BT Action and Service leaf nodes to their target Nav2 ROS 2 server nodes.
5. Explicitly models BT leaf nodes as components hosted inside `nav2_bt_navigator::BtNavigator`,
   preventing them from being misrepresented as standalone ROS 2 nodes.
6. Generates Mermaid flowchart diagrams and serializes BehaviorTreeCollectionModel.
"""

import json
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from src.schema import (
    BehaviorTreeCollectionModel, BehaviorTreeModel, BlackboardPort,
    BTNodeModel, BTNodeType
)

logger = logging.getLogger(__name__)

# Known BT node type categories in BehaviorTree.CPP / Nav2
CONTROL_TAGS = {
    "Sequence", "ReactiveSequence", "PipelineSequence", "SequenceWithMemory",
    "Fallback", "ReactiveFallback", "RecoveryNode", "RoundRobin", "IfThenElseNode",
    "Switch2", "Switch3", "Switch4", "Switch5", "Switch6"
}

DECORATOR_TAGS = {
    "RateController", "DistanceController", "SpeedController", "GoalUpdatedController",
    "TimeExpiredCondition", "Inverter", "ForceSuccess", "ForceFailure", "Repeat",
    "RetryUntilSuccessful", "KeepRunningUntilFailure", "SingleTrigger", "PathExpiringTimer"
}

CONDITION_TAGS = {
    "GoalReached", "IsStuck", "TransformAvailable", "DistanceTraveled", "TimeExpired",
    "IsBatteryLow", "InitialPoseReceived", "GlobalUpdatedGoal", "IsGoalNearby",
    "ValidatePath", "PathLongerOnApproach", "WouldAControllerRecoveryHelp",
    "WouldAPlannerRecoveryHelp", "AreErrorCodesPresent"
}

# Bindings from BT Action / Service names to ROS 2 interfaces and Nav2 server nodes
BT_ROS2_BINDINGS = {
    "ComputePathToPose": {
        "target_server": "nav2_planner::PlannerServer",
        "interface": "/compute_path_to_pose",
        "type": "action"
    },
    "ComputePathThroughPoses": {
        "target_server": "nav2_planner::PlannerServer",
        "interface": "/compute_path_through_poses",
        "type": "action"
    },
    "FollowPath": {
        "target_server": "nav2_controller::ControllerServer",
        "interface": "/follow_path",
        "type": "action"
    },
    "Spin": {
        "target_server": "nav2_behaviors::behavior_server::BehaviorServer",
        "interface": "/spin",
        "type": "action"
    },
    "Wait": {
        "target_server": "nav2_behaviors::behavior_server::BehaviorServer",
        "interface": "/wait",
        "type": "action"
    },
    "BackUp": {
        "target_server": "nav2_behaviors::behavior_server::BehaviorServer",
        "interface": "/backup",
        "type": "action"
    },
    "DriveOnHeading": {
        "target_server": "nav2_behaviors::behavior_server::BehaviorServer",
        "interface": "/drive_on_heading",
        "type": "action"
    },
    "AssistedTeleop": {
        "target_server": "nav2_behaviors::behavior_server::BehaviorServer",
        "interface": "/assisted_teleop",
        "type": "action"
    },
    "SmoothPath": {
        "target_server": "nav2_smoother::SmootherServer",
        "interface": "/smooth_path",
        "type": "action"
    },
    "ClearEntireCostmap": {
        "target_server": "nav2_costmap_2d::Costmap2DROS",
        "interface": "/global_costmap/clear_entirely_global_costmap",
        "type": "service"
    },
    "ClearCostmapExceptRegion": {
        "target_server": "nav2_costmap_2d::Costmap2DROS",
        "interface": "/global_costmap/clear_except_region_global_costmap",
        "type": "service"
    },
    "ClearCostmapAroundRobot": {
        "target_server": "nav2_costmap_2d::Costmap2DROS",
        "interface": "/global_costmap/clear_around_robot_global_costmap",
        "type": "service"
    },
    "DockRobot": {
        "target_server": "opennav_docking::DockingServer",
        "interface": "/dock_robot",
        "type": "action"
    },
    "UndockRobot": {
        "target_server": "opennav_docking::DockingServer",
        "interface": "/undock_robot",
        "type": "action"
    }
}

BLACKBOARD_REGEX = re.compile(r'\{([^}]+)\}')


class BehaviorTreeAnalyzer:
    """
    Recovers and analyzes BehaviorTree XML models and maps BT leaves to ROS 2 servers.
    """

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)

    def recover_behavior_trees(self) -> BehaviorTreeCollectionModel:
        """
        Execute full Behavior Tree recovery across the repository.
        """
        trees: List[BehaviorTreeModel] = []
        all_bb_vars: Set[str] = set()
        all_bindings: List[Dict[str, str]] = []
        total_nodes = 0

        # Scan for all BT XML files
        bt_dir = self.repo_root / "nav2_bt_navigator" / "behavior_trees"
        xml_paths = list(bt_dir.glob("*.xml")) if bt_dir.exists() else []

        # Also search anywhere else in repo
        for extra_xml in self.repo_root.rglob("*.xml"):
            if "behavior_tree" in str(extra_xml).lower() and extra_xml not in xml_paths and extra_xml.name != "package.xml":
                xml_paths.append(extra_xml)

        for xml_path in xml_paths:
            try:
                tree_model = self._parse_bt_file(xml_path)
                if tree_model:
                    trees.append(tree_model)
                    all_bb_vars.update(tree_model.blackboard_variables)
                    total_nodes += len(tree_model.nodes)
                    for bt_leaf, act in tree_model.ros2_action_bindings.items():
                        all_bindings.append({
                            "tree": tree_model.tree_name,
                            "bt_node": bt_leaf,
                            "type": "action",
                            "target_interface": act
                        })
                    for bt_leaf, srv in tree_model.ros2_service_bindings.items():
                        all_bindings.append({
                            "tree": tree_model.tree_name,
                            "bt_node": bt_leaf,
                            "type": "service",
                            "target_interface": srv
                        })
            except Exception as e:
                logger.debug(f"Failed parsing BT file {xml_path}: {e}")

        return BehaviorTreeCollectionModel(
            trees=trees,
            host_node_id="nav2_bt_navigator::BtNavigator",
            all_blackboard_variables=sorted(list(all_bb_vars)),
            total_trees=len(trees),
            total_bt_nodes=total_nodes,
            bt_to_ros2_bindings=all_bindings
        )

    def _parse_bt_file(self, xml_path: Path) -> Optional[BehaviorTreeModel]:
        """
        Parse a single BehaviorTree XML file into BehaviorTreeModel.
        """
        rel_path = str(xml_path.relative_to(self.repo_root)).replace("\\", "/")
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except Exception:
            return None

        # Look for <BehaviorTree ID="..."> or root element
        bt_elem = root.find(".//BehaviorTree")
        tree_id = bt_elem.get("ID") if bt_elem is not None else xml_path.stem
        if bt_elem is None:
            bt_elem = root

        nodes: List[BTNodeModel] = []
        blackboard_vars: Set[str] = set()
        action_bindings: Dict[str, str] = {}
        service_bindings: Dict[str, str] = {}

        node_counter = 0

        def traverse(elem: ET.Element) -> Optional[str]:
            nonlocal node_counter
            tag = elem.tag
            if tag in ("root", "BehaviorTree", "TreeNodesModel"):
                # Container elements
                child_ids = []
                for child in elem:
                    cid = traverse(child)
                    if cid:
                        child_ids.append(cid)
                return child_ids[0] if child_ids else None

            node_counter += 1
            node_id = f"{tag}_{node_counter}"

            # Classify node type
            if tag in CONTROL_TAGS:
                node_type = BTNodeType.CONTROL
            elif tag in DECORATOR_TAGS:
                node_type = BTNodeType.DECORATOR
            elif tag in CONDITION_TAGS:
                node_type = BTNodeType.CONDITION
            elif tag == "SubTree":
                node_type = BTNodeType.SUBTREE
            else:
                node_type = BTNodeType.ACTION

            # Parse ports and blackboard variables
            ports: List[BlackboardPort] = []
            for attr_name, attr_val in elem.attrib.items():
                if attr_name == "name":
                    continue
                bb_matches = BLACKBOARD_REGEX.findall(attr_val)
                bb_key = bb_matches[0] if bb_matches else None
                if bb_key:
                    blackboard_vars.add(bb_key)

                # Direction heuristic
                direction = "inout"
                if "output" in attr_name.lower():
                    direction = "output"
                elif "input" in attr_name.lower() or "goal" in attr_name.lower() or "path" in attr_name.lower():
                    direction = "input"

                ports.append(BlackboardPort(
                    name=attr_name,
                    direction=direction,
                    blackboard_key=attr_val if bb_key else None,
                    description=f"Port {attr_name}={attr_val}"
                ))

            # Check ROS 2 binding
            target_server = None
            action_or_service = None
            if tag in BT_ROS2_BINDINGS:
                binding_info = BT_ROS2_BINDINGS[tag]
                target_server = binding_info["target_server"]
                action_or_service = binding_info["interface"]
                if binding_info["type"] == "action":
                    action_bindings[tag] = action_or_service
                else:
                    service_bindings[tag] = action_or_service

            # Recurse children
            child_ids: List[str] = []
            for child in elem:
                cid = traverse(child)
                if cid:
                    child_ids.append(cid)

            bt_node = BTNodeModel(
                id=node_id,
                node_type=node_type,
                class_name=tag,
                name=elem.get("name"),
                ports=ports,
                target_server=target_server,
                action_or_service=action_or_service,
                child_ids=child_ids,
                is_hosted_in_bt_navigator=True
            )
            nodes.append(bt_node)
            return node_id

        root_node_id = traverse(bt_elem) or ""

        # Generate Mermaid diagram for this tree
        mermaid_diag = self._generate_bt_mermaid(tree_id, nodes)

        return BehaviorTreeModel(
            tree_id=tree_id,
            tree_name=tree_id,
            file_path=rel_path,
            root_node_id=root_node_id,
            nodes=nodes,
            blackboard_variables=sorted(list(blackboard_vars)),
            ros2_action_bindings=action_bindings,
            ros2_service_bindings=service_bindings,
            mermaid_diagram=mermaid_diag
        )

    def _generate_bt_mermaid(self, tree_name: str, nodes: List[BTNodeModel]) -> str:
        """
        Generate Mermaid flowchart visualizing the Behavior Tree hierarchy.
        """
        lines = [
            "flowchart TD",
            f"    %% BehaviorTree: {tree_name}",
            "    subgraph BTNavigator [\"bt_navigator (Host Node)\"]"
        ]

        # Render nodes with style based on category
        for n in nodes[:25]:  # Limit top nodes to keep diagram clean and readable
            label = n.name or n.class_name
            if n.node_type == BTNodeType.CONTROL:
                lines.append(f'        {n.id}[["{label} ({n.class_name})"]]')
            elif n.node_type == BTNodeType.DECORATOR:
                lines.append(f'        {n.id}("{label} ({n.class_name})")')
            elif n.node_type == BTNodeType.CONDITION:
                lines.append(f'        {n.id}{{"{label} ({n.class_name})"}}')
            else:
                lines.append(f'        {n.id}["{label} ({n.class_name})"]')

        lines.append("    end")

        # Connect parent to children
        id_set = {n.id for n in nodes[:25]}
        for n in nodes[:25]:
            for cid in n.child_ids:
                if cid in id_set:
                    lines.append(f"    {n.id} --> {cid}")

        # Connect actions to external ROS 2 servers
        for n in nodes[:25]:
            if n.target_server:
                srv_id = n.target_server.replace("::", "_")
                lines.append(f'    {n.id} -.->|"{n.action_or_service}"| {srv_id}["{n.target_server}"]')

        return "\n".join(lines)


def run_behavior_tree_analysis(
    repo_root: Path,
    output_path: Optional[Path] = None
) -> BehaviorTreeCollectionModel:
    """Execute Stage 4.4 Behavior Tree Recovery"""
    analyzer = BehaviorTreeAnalyzer(repo_root=repo_root)
    model = analyzer.recover_behavior_trees()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(model.model_dump(), f, indent=2)
        logger.info(f"Behavior tree model saved to {output_path}")

    return model

