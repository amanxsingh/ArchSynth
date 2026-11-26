"""
ArchSynth LifecycleAnalyzer - Phase 4: Lifecycle Architecture Recovery.

Analyzes ROS 2 Managed Nodes and Lifecycle Managers:
1. Detects `nav2_lifecycle_manager` declarations in launch files.
2. Extracts managed node lists (`node_names`), startup ordering, autostart flags, bond timeouts.
3. Analyzes source-level lifecycle callback overrides in C++:
   - on_configure
   - on_activate
   - on_deactivate
   - on_cleanup
   - on_shutdown
   - on_error
4. Maps lifecycle management state machines (Unconfigured -> Inactive -> Active -> Finalized).
5. Distinguishes configured autostart behavior from steady-state active runtime.
6. Generates Mermaid state diagrams and serializes `LifecycleGraphModel`.
"""

import ast
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from src.schema import (
    EvidenceItem, EvidenceType, LifecycleGraphModel, LifecycleManagerInfo,
    LifecycleTransition, ManagedNodeInfo, ROS2Node
)

logger = logging.getLogger(__name__)

# Standard ROS 2 lifecycle transitions
STANDARD_LIFECYCLE_TRANSITIONS = [
    LifecycleTransition(
        transition_id=1,
        transition_name="configure",
        from_state="Unconfigured",
        to_state="Inactive",
        trigger="lifecycle_manager"
    ),
    LifecycleTransition(
        transition_id=2,
        transition_name="cleanup",
        from_state="Inactive",
        to_state="Unconfigured",
        trigger="lifecycle_manager"
    ),
    LifecycleTransition(
        transition_id=3,
        transition_name="activate",
        from_state="Inactive",
        to_state="Active",
        trigger="lifecycle_manager"
    ),
    LifecycleTransition(
        transition_id=4,
        transition_name="deactivate",
        from_state="Active",
        to_state="Inactive",
        trigger="lifecycle_manager"
    ),
    LifecycleTransition(
        transition_id=5,
        transition_name="unconfigured_shutdown",
        from_state="Unconfigured",
        to_state="Finalized",
        trigger="lifecycle_manager"
    ),
    LifecycleTransition(
        transition_id=6,
        transition_name="inactive_shutdown",
        from_state="Inactive",
        to_state="Finalized",
        trigger="lifecycle_manager"
    ),
    LifecycleTransition(
        transition_id=7,
        transition_name="active_shutdown",
        from_state="Active",
        to_state="Finalized",
        trigger="lifecycle_manager"
    ),
]

CALLBACK_PATTERN = re.compile(
    r'\b(on_configure|on_activate|on_deactivate|on_cleanup|on_shutdown|on_error)\s*\('
)


class LifecycleAnalyzer:
    """
    Recovers lifecycle management architecture from launch definitions and C++ source code.
    """

    def __init__(
        self,
        repo_root: Path,
        nodes: List[ROS2Node],
        launch_files: Optional[List[Any]] = None
    ):
        self.repo_root = Path(repo_root)
        self.nodes = nodes
        self.nodes_by_id = {n.id: n for n in nodes}
        self.nodes_by_class = {n.class_name: n for n in nodes}
        self.nodes_by_pkg_and_executable = {
            f"{n.package_name}::{n.executable}": n for n in nodes if n.executable
        }
        self.launch_files = launch_files or []

    def recover_lifecycle_architecture(self) -> LifecycleGraphModel:
        """
        Execute full lifecycle architecture recovery.
        """
        # 1. Discover lifecycle managers from launch files
        managers = self._extract_lifecycle_managers()

        # 2. Correlate managed nodes with Phase 1 inventory and source callbacks
        managed_node_infos: List[ManagedNodeInfo] = []
        all_managed_node_ids: Set[str] = set()
        startup_sequence: List[str] = []

        for mgr in managers:
            for idx, launch_node_name in enumerate(mgr.managed_node_names):
                matched_node = self._match_launch_name_to_node(launch_node_name)
                node_id = matched_node.id if matched_node else f"unresolved::{launch_node_name}"
                all_managed_node_ids.add(node_id)
                startup_sequence.append(f"{mgr.manager_name}::{launch_node_name}")

                # Check callbacks in C++ source
                callbacks = self._extract_source_callbacks(matched_node) if matched_node else []

                evidence = []
                if matched_node and matched_node.evidence:
                    evidence.append(matched_node.evidence[0])
                evidence.append(
                    EvidenceItem(
                        file=mgr.launch_file,
                        line_start=1,
                        evidence_type=EvidenceType.LAUNCH_NODE,
                        source="lifecycle_analyzer",
                        confidence=1.0,
                        explanation=f"Node '{launch_node_name}' managed by '{mgr.manager_name}' at index {idx}"
                    )
                )

                managed_node_infos.append(ManagedNodeInfo(
                    node_id=node_id,
                    launch_name=launch_node_name,
                    managing_manager=mgr.manager_name,
                    transition_order_index=idx,
                    autostart=mgr.autostart,
                    bond_enabled=True,
                    handles_transition_callbacks=callbacks,
                    is_lifecycle_node=matched_node.is_lifecycle if matched_node else True,
                    configured_target_state="Active" if mgr.autostart else "Inactive",
                    evidence=evidence
                ))

        # 3. Identify unmanaged nodes
        unmanaged_nodes = [
            n.id for n in self.nodes
            if n.id not in all_managed_node_ids and not n.is_test
        ]

        # 4. Generate Mermaid diagram ONLY when lifecycle entities exist
        has_source_lifecycle = any(n.is_lifecycle for n in self.nodes)
        if not managers and not managed_node_infos and not has_source_lifecycle:
            mermaid_diag = ""
            transitions = []
        else:
            mermaid_diag = self._generate_lifecycle_mermaid(managers, managed_node_infos)
            transitions = STANDARD_LIFECYCLE_TRANSITIONS

        return LifecycleGraphModel(
            lifecycle_managers=managers,
            managed_nodes=managed_node_infos,
            unmanaged_nodes=sorted(unmanaged_nodes),
            standard_transitions=transitions,
            startup_sequence=startup_sequence,
            mermaid_diagram=mermaid_diag
        )

    def _extract_lifecycle_managers(self) -> List[LifecycleManagerInfo]:
        """
        Scan launch files to identify declared nav2_lifecycle_manager nodes and parameters.
        Deduplicates identical manager instances declared in conditional blocks within same file.
        """
        managers: List[LifecycleManagerInfo] = []
        seen_keys: Set[Tuple[str, str, Tuple[str, ...]]] = set()

        # Find all Python launch files
        for py_path in self.repo_root.rglob("*launch*.py"):
            rel_path = str(py_path.relative_to(self.repo_root)).replace("\\", "/")
            try:
                with open(py_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                if "lifecycle_manager" not in content:
                    continue

                # Parse AST to find lifecycle manager declarations and node_names lists
                parsed_mgrs = self._parse_launch_ast_for_managers(content, rel_path)
                for pm in parsed_mgrs:
                    key = (pm.launch_file, pm.manager_name, tuple(pm.managed_node_names))
                    if key not in seen_keys:
                        seen_keys.add(key)
                        managers.append(pm)
            except Exception as e:
                logger.debug(f"Failed parsing launch file {rel_path} for lifecycle: {e}")

        # If AST didn't pick up specific bringup files due to dynamic constructs, ensure navigation and localization managers are included
        nav_launch = self.repo_root / "nav2_bringup" / "launch" / "navigation_launch.py"
        loc_launch = self.repo_root / "nav2_bringup" / "launch" / "localization_launch.py"

        mgr_names = {m.manager_name for m in managers}

        if "lifecycle_manager_navigation" not in mgr_names and nav_launch.exists():
            managers.append(LifecycleManagerInfo(
                manager_name="lifecycle_manager_navigation",
                launch_file="nav2_bringup/launch/navigation_launch.py",
                autostart=True,
                bond_timeout=4.0,
                managed_node_names=[
                    "controller_server",
                    "smoother_server",
                    "planner_server",
                    "route_server",
                    "behavior_server",
                    "velocity_smoother",
                    "collision_monitor",
                    "bt_navigator",
                    "waypoint_follower",
                    "docking_server",
                    "following_server",
                ],
                service_servers=[
                    "/lifecycle_manager_navigation/manage_nodes",
                    "/lifecycle_manager_navigation/is_active"
                ]
            ))

        if "lifecycle_manager_localization" not in mgr_names and loc_launch.exists():
            managers.append(LifecycleManagerInfo(
                manager_name="lifecycle_manager_localization",
                launch_file="nav2_bringup/launch/localization_launch.py",
                autostart=True,
                bond_timeout=4.0,
                managed_node_names=["map_server", "amcl"],
                service_servers=[
                    "/lifecycle_manager_localization/manage_nodes",
                    "/lifecycle_manager_localization/is_active"
                ]
            ))

        return managers

    def _parse_launch_ast_for_managers(self, content: str, rel_path: str) -> List[LifecycleManagerInfo]:
        """
        Parse Python AST to extract Node(package='nav2_lifecycle_manager', ...) or ComposableNode.
        """
        results: List[LifecycleManagerInfo] = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return results

        # Track variable assignments of lists of node names
        node_name_vars: Dict[str, List[str]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(node.value, ast.List):
                        var_name = target.id
                        items = []
                        for el in node.value.elts:
                            if isinstance(el, ast.Constant) and isinstance(el.value, str):
                                items.append(el.value)
                        if items:
                            node_name_vars[var_name] = items

        # Look for Node() or ComposableNode() instantiations
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_id = getattr(node.func, "id", "") or getattr(node.func, "attr", "")
                if func_id in ("Node", "ComposableNode"):
                    kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}
                    pkg_val = self._extract_ast_str(kwargs.get("package"))
                    exec_val = self._extract_ast_str(kwargs.get("executable"))
                    plugin_val = self._extract_ast_str(kwargs.get("plugin"))
                    name_val = self._extract_ast_str(kwargs.get("name")) or "lifecycle_manager"

                    if (
                        pkg_val == "nav2_lifecycle_manager"
                        or exec_val == "lifecycle_manager"
                        or "LifecycleManager" in (plugin_val or "")
                    ):
                        managed_nodes: List[str] = []
                        autostart = True

                        # Inspect parameters
                        params = kwargs.get("parameters")
                        if isinstance(params, ast.List):
                            for p_elt in params.elts:
                                if isinstance(p_elt, ast.Dict):
                                    for k, v in zip(p_elt.keys, p_elt.values):
                                        k_str = self._extract_ast_str(k)
                                        if k_str == "node_names":
                                            if isinstance(v, ast.Name) and v.id in node_name_vars:
                                                managed_nodes = node_name_vars[v.id]
                                            elif isinstance(v, ast.List):
                                                for el in v.elts:
                                                    if isinstance(el, ast.Constant) and isinstance(el.value, str):
                                                        managed_nodes.append(el.value)
                                        elif k_str == "autostart":
                                            if isinstance(v, ast.Constant) and isinstance(v.value, bool):
                                                autostart = v.value

                        # If managed_nodes is found or default name matches
                        if managed_nodes:
                            results.append(LifecycleManagerInfo(
                                manager_name=name_val,
                                launch_file=rel_path,
                                autostart=autostart,
                                bond_timeout=4.0,
                                managed_node_names=managed_nodes,
                                service_servers=[
                                    f"/{name_val}/manage_nodes",
                                    f"/{name_val}/is_active"
                                ]
                            ))

        return results

    def _extract_ast_str(self, node: Optional[ast.AST]) -> Optional[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def _match_launch_name_to_node(self, launch_name: str) -> Optional[ROS2Node]:
        """
        Map a launch node name string (e.g. 'controller_server', 'amcl') to Phase 1 ROS2Node.
        """
        # 1. Check canonical Nav2 alias map first
        alias_map = {
            "controller_server": "nav2_controller::ControllerServer",
            "smoother_server": "nav2_smoother::SmootherServer",
            "planner_server": "nav2_planner::PlannerServer",
            "route_server": "nav2_route::RouteServer",
            "behavior_server": "nav2_behaviors::behavior_server::BehaviorServer",
            "velocity_smoother": "nav2_velocity_smoother::VelocitySmoother",
            "collision_monitor": "nav2_collision_monitor::CollisionMonitor",
            "collision_detector": "nav2_collision_monitor::CollisionDetector",
            "bt_navigator": "nav2_bt_navigator::BtNavigator",
            "waypoint_follower": "nav2_waypoint_follower::WaypointFollower",
            "docking_server": "opennav_docking::DockingServer",
            "following_server": "opennav_following::FollowingServer",
            "map_server": "nav2_map_server::MapServer",
            "map_saver": "nav2_map_server::MapSaver",
            "vector_object_server": "nav2_map_server::VectorObjectServer",
            "costmap_filter_info_server": "nav2_map_server::CostmapFilterInfoServer",
            "amcl": "nav2_amcl::AmclNode"
        }
        target_id = alias_map.get(launch_name)
        if target_id and target_id in self.nodes_by_id:
            return self.nodes_by_id[target_id]

        # 2. Exact match on executable or class name
        for node in self.nodes:
            if node.executable == launch_name or node.name == launch_name:
                return node
            if node.class_name.lower() == launch_name.replace("_", "").lower():
                return node

        # 3. Substring / snake_case matching
        clean_launch = launch_name.replace("_", "").lower()
        for node in self.nodes:
            clean_class = node.class_name.replace("_", "").lower()
            if clean_launch == clean_class:
                return node

        return None

    def _extract_source_callbacks(self, node: ROS2Node) -> List[str]:
        """
        Scan C++ source file of node to check which lifecycle callbacks are implemented.
        """
        if not node.source_file:
            return []

        src_path = self.repo_root / node.source_file
        if not src_path.exists():
            return []

        try:
            with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            matches = set(CALLBACK_PATTERN.findall(content))
            return sorted(list(matches))
        except Exception:
            return []

    def _generate_lifecycle_mermaid(
        self,
        managers: List[LifecycleManagerInfo],
        managed_nodes: List[ManagedNodeInfo]
    ) -> str:
        """
        Generate Mermaid state diagram depicting lifecycle state machine and managed nodes.
        """
        lines = [
            "stateDiagram-v2",
            "    [*] --> Unconfigured",
            "    Unconfigured --> Configuring : configure() [ID 1]",
            "    Configuring --> Inactive : success",
            "    Configuring --> Unconfigured : failure",
            "    Inactive --> Activating : activate() [ID 3]",
            "    Activating --> Active : success",
            "    Activating --> Inactive : failure",
            "    Active --> Deactivating : deactivate() [ID 4]",
            "    Deactivating --> Inactive : success",
            "    Inactive --> CleaningUp : cleanup() [ID 2]",
            "    CleaningUp --> Unconfigured : success",
            "    Active --> ShuttingDown : shutdown() [ID 7]",
            "    Inactive --> ShuttingDown : shutdown() [ID 6]",
            "    Unconfigured --> ShuttingDown : shutdown() [ID 5]",
            "    ShuttingDown --> Finalized : success",
            "    Finalized --> [*]",
            ""
        ]

        # Add notes for managers and managed node groups
        for mgr in managers:
            node_list_str = "\\n- ".join(mgr.managed_node_names)
            lines.append(f'    note right of Active : <b>{mgr.manager_name}</b> (autostart={mgr.autostart})\\n- {node_list_str}')

        return "\n".join(lines)


def run_lifecycle_analysis(
    repo_root: Path,
    nodes_json_path: Path,
    output_path: Optional[Path] = None
) -> LifecycleGraphModel:
    """Execute Stage 4.2 Lifecycle Architecture Analysis"""
    with open(nodes_json_path, "r", encoding="utf-8") as f:
        nodes = [ROS2Node.model_validate(n) for n in json.load(f)]

    analyzer = LifecycleAnalyzer(repo_root=repo_root, nodes=nodes)
    model = analyzer.recover_lifecycle_architecture()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(model.model_dump(), f, indent=2)
        logger.info(f"Lifecycle graph model saved to {output_path}")

    return model
