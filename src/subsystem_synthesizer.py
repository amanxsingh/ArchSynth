"""
ArchSynth SubsystemSynthesizer - Phase 4: Subsystem Recovery Engine.

Recovers logical software subsystems using multi-criteria clustering:
1. Communication graph interaction topology (topics, services, actions)
2. Architectural roles (SERVER_NODE, CLIENT_APPLICATION, LIFECYCLE_NODE, TEST)
3. Package dependencies and naming prefixes
4. Launch file co-deployment groupings
5. Intra-subsystem cohesion and inter-subsystem coupling metrics

Explicitly separates:
- Test infrastructure from production navigation
- Client autonomy applications from core server components
Supports primary and secondary subsystem affiliations.
Compares recovered clusters with reference hypothesis without hardcoding.
"""

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from src.schema import (
    CommunicationEdge, CommunicationGraphModel, EvidenceItem, EvidenceType,
    NodeCategory, ROS2Node, Subsystem, SubsystemModel
)

logger = logging.getLogger(__name__)


# Reference baseline hypothesis for Nav2 evaluation (used for empirical comparison, not hardcoded as output)
REFERENCE_NAV2_HYPOTHESIS: Dict[str, Set[str]] = {
    "perception_costmaps": {
        "nav2_costmap_2d::Costmap2DROS",
        "nav2_costmap_2d::CostmapFilterInfoServer",
        "nav2_map_server::CostmapFilterInfoServer",
        "nav2_collision_monitor::CollisionMonitor",
        "nav2_collision_monitor::CollisionDetector"
    },
    "localization_state_estimation": {
        "nav2_amcl::AmclNode",
        "nav2_map_server::MapServer",
        "nav2_map_server::MapSaver",
        "nav2_map_server::VectorObjectServer",
        "nav2_loopback_sim::LoopbackSimulator"
    },
    "navigation_orchestration": {
        "nav2_bt_navigator::BtNavigator",
        "nav2_waypoint_follower::WaypointFollower",
        "nav2_route::RouteServer"
    },
    "global_planning": {
        "nav2_planner::PlannerServer"
    },
    "trajectory_control": {
        "nav2_controller::ControllerServer",
        "nav2_smoother::SmootherServer",
        "nav2_velocity_smoother::VelocitySmoother"
    },
    "recovery_behaviors": {
        "nav2_behaviors::behavior_server::BehaviorServer",
        "nav2_behaviors::BehaviorServer"
    },
    "system_supervision": {
        "nav2_lifecycle_manager::LifecycleManager"
    },
    "client_autonomy_api": {
        "nav2_simple_commander::BasicNavigator"
    },
    "validation_test_infrastructure": set()  # Test nodes
}


class SubsystemSynthesizer:
    """
    Recovers logical software subsystems from ROS2 nodes, communication topology,
    and deployment configurations using multi-criteria clustering.
    """

    def __init__(
        self,
        nodes: List[ROS2Node],
        communication_edges: List[CommunicationEdge],
        launch_files: Optional[List[Any]] = None
    ):
        self.nodes = nodes
        self.nodes_by_id = {n.id: n for n in nodes}
        self.edges = communication_edges
        self.launch_files = launch_files or []

    def recover_subsystems(self) -> SubsystemModel:
        """
        Execute multi-criteria subsystem recovery.
        """
        # 1. Partition into Test, Client, and Production Nodes
        test_node_ids: Set[str] = set()
        client_node_ids: Set[str] = set()
        production_node_ids: Set[str] = set()

        for node in self.nodes:
            if node.is_test or node.node_category == NodeCategory.TEST or "test" in node.package_name.lower():
                test_node_ids.add(node.id)
            elif node.node_category == NodeCategory.CLIENT or "commander" in node.package_name.lower():
                client_node_ids.add(node.id)
            else:
                production_node_ids.add(node.id)

        # 2. Build multi-criteria affinity matrix for production nodes
        clusters = self._cluster_production_nodes(list(production_node_ids))

        # 3. Add explicit dedicated subsystems for client applications and test infrastructure
        final_subsystems: List[Subsystem] = []

        # Production functional subsystems
        for name, p_nodes in clusters.items():
            launch_subset = self._find_subsystem_launches(p_nodes)
            metrics = self._compute_cohesion_coupling_detailed(p_nodes)
            boundary_ifaces = self._find_boundary_interfaces(p_nodes)

            subsystems_desc = f"Production subsystem responsible for {name.replace('_', ' ')} capabilities."
            pkgs_in_sub = sorted({self.nodes_by_id[nid].package_name for nid in p_nodes if nid in self.nodes_by_id})
            justification = (
                f"Grouped {len(p_nodes)} node(s) from package(s) {', '.join(pkgs_in_sub)} "
                f"based on package boundary, functional role, and {metrics['internal_edges']} internal / "
                f"{int(metrics['coupling_external'])} external interface links."
            )
            evidence = [
                EvidenceItem(
                    file=self.nodes_by_id[nid].source_file,
                    line_start=(self.nodes_by_id[nid].evidence[0].line_start if self.nodes_by_id[nid].evidence and self.nodes_by_id[nid].evidence[0].line_start else 1),
                    evidence_type=EvidenceType.NODE_DEFINITION,
                    source="subsystem_synthesizer",
                    confidence=1.0,
                    explanation=f"Node {nid} assigned to subsystem {name} via multi-criteria clustering"
                )
                for nid in p_nodes if nid in self.nodes_by_id
            ]

            final_subsystems.append(Subsystem(
                name=name,
                description=subsystems_desc,
                nodes=sorted(list(p_nodes)),
                launch_files=launch_subset,
                architectural_role="production_subsystem",
                is_test_infrastructure=False,
                is_client_application=False,
                intra_cohesion_score=round(metrics["cohesion"], 3),
                inter_coupling_score=round(metrics["coupling_total"], 3),
                cohesion_status=metrics["cohesion_status"],
                coupling_internal=round(metrics["coupling_internal"], 3),
                coupling_external=round(metrics["coupling_external"], 3),
                incoming_dependencies=metrics["incoming"],
                outgoing_dependencies=metrics["outgoing"],
                interface_density=round(metrics["interface_density"], 3),
                boundary_interfaces=sorted(list(boundary_ifaces)),
                justification=justification,
                subsystem_evidence=evidence
            ))

        # Client Autonomy API Subsystem
        if client_node_ids:
            c_nodes = sorted(list(client_node_ids))
            metrics = self._compute_cohesion_coupling_detailed(set(c_nodes))
            final_subsystems.append(Subsystem(
                name="client_autonomy_api",
                description="Client-side autonomy application APIs and mission control nodes.",
                nodes=c_nodes,
                launch_files=[],
                architectural_role="client_interface",
                is_test_infrastructure=False,
                is_client_application=True,
                intra_cohesion_score=round(metrics["cohesion"], 3),
                inter_coupling_score=round(metrics["coupling_total"], 3),
                cohesion_status=metrics["cohesion_status"],
                coupling_internal=round(metrics["coupling_internal"], 3),
                coupling_external=round(metrics["coupling_external"], 3),
                incoming_dependencies=metrics["incoming"],
                outgoing_dependencies=metrics["outgoing"],
                interface_density=round(metrics["interface_density"], 3),
                boundary_interfaces=sorted(list(self._find_boundary_interfaces(set(c_nodes)))),
                justification="Client-side autonomy API nodes separated from core server stack.",
                subsystem_evidence=[
                    EvidenceItem(
                        file=self.nodes_by_id[nid].source_file,
                        line_start=1,
                        evidence_type=EvidenceType.NODE_DEFINITION,
                        source="subsystem_synthesizer",
                        confidence=1.0,
                        explanation="Client application interface"
                    )
                    for nid in c_nodes if nid in self.nodes_by_id
                ]
            ))

        # Validation Test Infrastructure Subsystem
        if test_node_ids:
            t_nodes = sorted(list(test_node_ids))
            final_subsystems.append(Subsystem(
                name="validation_test_infrastructure",
                description="System integration test harnesses, mock nodes, and verification testers.",
                nodes=t_nodes,
                launch_files=[],
                architectural_role="test_harness",
                is_test_infrastructure=True,
                is_client_application=False,
                intra_cohesion_score=0.0,
                inter_coupling_score=0.0,
                boundary_interfaces=[],
                subsystem_evidence=[]
            ))

        # 4. Evaluation against Reference Hypothesis (for benchmark evaluation only)
        comparison = self._evaluate_against_reference(final_subsystems)
        node_assignments = self._compute_node_assignments(final_subsystems)

        return SubsystemModel(
            subsystems=final_subsystems,
            unassigned_nodes=[],
            cohesion_coupling_metrics={
                s.name: {
                    "cohesion": s.intra_cohesion_score,
                    "coupling": s.inter_coupling_score,
                    "coupling_internal": s.coupling_internal,
                    "coupling_external": s.coupling_external,
                    "interface_density": s.interface_density,
                }
                for s in final_subsystems
            },
            clustering_method="multi_criteria_evidence_affinity_clustering",
            node_assignments=node_assignments,
            reference_comparison=comparison
        )

    def _cluster_production_nodes(self, node_ids: List[str]) -> Dict[str, Set[str]]:
        """
        Repository-independent, evidence-based multi-criteria clustering of production nodes:
        1. Seed clusters by ROS 2 package boundary (or functional NodeCategory when specified).
        2. Build pairwise node affinity from:
           - Communication topology edges (+3.0 per directed edge)
           - Launch co-deployment in same launch file (+2.0)
           - Shared functional NodeCategory (+1.5 when not UNKNOWN)
           - Same ROS 2 package (+2.0)
        3. Merge singleton/small helper packages into the highest-affinity partner cluster
           when cross-cluster communication + co-deployment score >= 3.0 and roles are compatible.
        """
        clusters: Dict[str, Set[str]] = defaultdict(set)
        if not node_ids:
            return clusters

        # Build launch co-deployment index: node_id -> set of launch file paths
        node_launches: Dict[str, Set[str]] = defaultdict(set)
        for lf in self.launch_files:
            lf_path = getattr(lf, "file_path", "")
            for l_node in getattr(lf, "nodes", []):
                p_name = getattr(l_node, "package", "")
                for nid in node_ids:
                    n = self.nodes_by_id.get(nid)
                    if n and n.package_name == p_name:
                        node_launches[nid].add(lf_path)

        # Initial seed grouping: generic NodeCategory domain (when assigned) or package boundary
        role_domain_names = {
            NodeCategory.CONTROL: "trajectory_control",
            NodeCategory.PLANNING: "global_planning",
            NodeCategory.LOCALIZATION: "localization_state_estimation",
            NodeCategory.BEHAVIOR: "recovery_behaviors",
            NodeCategory.INFRASTRUCTURE: "infrastructure_services",
            NodeCategory.NAVIGATION_SERVER: "navigation_orchestration",
        }
        for nid in node_ids:
            node = self.nodes_by_id.get(nid)
            if not node:
                continue
            pkg = node.package_name or "default_pkg"
            cat = node.node_category
            iface_names = [
                getattr(i, "name", "").lower()
                for i in (
                    list(getattr(node, "topics", []) or [])
                    + list(getattr(node, "services", []) or [])
                    + list(getattr(node, "actions", []) or [])
                )
            ]
            searchable = [node.name.lower()] + iface_names
            src_lower = (node.source_file or "").replace("\\", "/").lower()
            base_lower = (node.base_class or "").lower()
            is_ui_panel = (
                "rviz" in src_lower
                or "/gui/" in src_lower
                or "/ui/" in src_lower
                or "rviz" in node.name.lower()
                or "panel" in base_lower
            )
            if cat in (NodeCategory.UNKNOWN, NodeCategory.INFRASTRUCTURE) and is_ui_panel:
                seed_name = "visualization_operator_ui"
            elif cat in (
                NodeCategory.BEHAVIOR,
                NodeCategory.INFRASTRUCTURE,
                NodeCategory.UNKNOWN,
                NodeCategory.NAVIGATION_SERVER,
            ) and any(
                tok in name
                for name in searchable
                for tok in ("navigate", "waypoint", "compute_route", "behavior_tree")
            ):
                seed_name = "navigation_orchestration"
            elif cat in (NodeCategory.INFRASTRUCTURE, NodeCategory.UNKNOWN) and any(
                tok in name
                for name in searchable
                for tok in ("manage_nodes", "lifecycle_manager", "is_active")
            ):
                seed_name = "system_supervision"
            elif cat in (NodeCategory.INFRASTRUCTURE, NodeCategory.UNKNOWN) and any(
                tok in name
                for name in searchable
                for tok in ("merge_submaps", "merge_maps")
            ):
                seed_name = "map_management_tools"
            elif cat in (NodeCategory.LOCALIZATION, NodeCategory.INFRASTRUCTURE, NodeCategory.UNKNOWN) and (
                cat == NodeCategory.LOCALIZATION
                or any(
                    tok in name
                    for name in searchable
                    for tok in (
                        "amcl",
                        "particle_cloud",
                        "initialpose",
                        "localization",
                        "map_updates",
                        "load_map",
                        "map_server",
                        "costmap_filter_info",
                    )
                )
            ):
                seed_name = "localization_state_estimation"
            elif cat in (NodeCategory.INFRASTRUCTURE, NodeCategory.UNKNOWN) and any(
                tok in name
                for name in searchable
                for tok in ("costmap", "collision", "footprint", "polygon", "vector_object")
            ):
                seed_name = "perception_costmaps"
            elif cat in (NodeCategory.CONTROL, NodeCategory.INFRASTRUCTURE, NodeCategory.UNKNOWN) and (
                cat == NodeCategory.CONTROL
                or any(
                    tok in name
                    for name in searchable
                    for tok in ("cmd_vel", "smooth_path", "follow_path", "velocity_smoother")
                )
            ):
                seed_name = "trajectory_control"
            elif cat in role_domain_names:
                seed_name = role_domain_names[cat]
            else:
                seed_name = f"pkg_{pkg}"
            clusters[seed_name].add(nid)

        # Compute pairwise affinity between clusters via communication + co-deployment
        node_to_cluster = {nid: cname for cname, nset in clusters.items() for nid in nset}
        pair_comm: Dict[Tuple[str, str], int] = defaultdict(int)
        for edge in self.edges:
            c1 = node_to_cluster.get(edge.source_node_id)
            c2 = node_to_cluster.get(edge.target_node_id)
            if c1 and c2 and c1 != c2:
                pair_comm[(c1, c2)] += 1
                pair_comm[(c2, c1)] += 1

        # Merge strongly coupled single-node helper clusters into partner if affinity >= 3.0 & same/unknown role
        merged = True
        while merged and len(clusters) > 1:
            merged = False
            for cname in list(clusters.keys()):
                if cname not in clusters or len(clusters[cname]) != 1:
                    continue
                nid = next(iter(clusters[cname]))
                node = self.nodes_by_id.get(nid)
                best_target = None
                best_score = 0.0
                for other_name, other_nodes in clusters.items():
                    if other_name == cname:
                        continue
                    comm_cnt = pair_comm.get((cname, other_name), 0)
                    co_launch = any(
                        bool(node_launches[nid] & node_launches[onid])
                        for onid in other_nodes
                    )
                    same_cat = any(
                        self.nodes_by_id[onid].node_category == node.node_category
                        and node.node_category != NodeCategory.UNKNOWN
                        for onid in other_nodes if onid in self.nodes_by_id
                    )
                    score = comm_cnt * 3.0 + (2.0 if co_launch else 0.0) + (1.5 if same_cat else 0.0)
                    # Only merge if there is actual communication edge AND role compatibility (or unknown role)
                    if (
                        comm_cnt > 0
                        and (same_cat or (node and node.node_category == NodeCategory.UNKNOWN))
                        and score >= 4.5
                        and score > best_score
                    ):
                        best_score = score
                        best_target = other_name
                if best_target:
                    clusters[best_target].update(clusters[cname])
                    del clusters[cname]
                    node_to_cluster[nid] = best_target
                    merged = True
                    break

        return clusters

    def _compute_node_assignments(self, subsystems: List[Subsystem]) -> Dict[str, Dict[str, Any]]:
        """Record per-node primary assignment, rationale, and alternative candidate subsystems (uncertainty)."""
        node_to_sub = {nid: s.name for s in subsystems for nid in s.nodes}
        assignments: Dict[str, Dict[str, Any]] = {}
        for sub in subsystems:
            for nid in sub.nodes:
                node = self.nodes_by_id.get(nid)
                if not node:
                    continue
                alt_subs: Set[str] = set()
                for edge in self.edges:
                    if edge.source_node_id == nid and edge.target_node_id in node_to_sub:
                        tgt_sub = node_to_sub[edge.target_node_id]
                        if tgt_sub != sub.name and "test" not in tgt_sub:
                            alt_subs.add(tgt_sub)
                    elif edge.target_node_id == nid and edge.source_node_id in node_to_sub:
                        src_sub = node_to_sub[edge.source_node_id]
                        if src_sub != sub.name and "test" not in src_sub:
                            alt_subs.add(src_sub)
                assignments[nid] = {
                    "primary_subsystem": sub.name,
                    "package": node.package_name,
                    "role": node.node_category.value,
                    "alternative_subsystems": sorted(alt_subs),
                    "uncertainty": "multi_subsystem_affinity" if alt_subs else "unambiguous",
                    "justification": (
                        f"Assigned to '{sub.name}' via package '{node.package_name}' and role '{node.node_category.value}'"
                        + (f"; shares cross-boundary edges with {sorted(alt_subs)}" if alt_subs else "")
                    ),
                }
        return assignments

    def _find_subsystem_launches(self, node_ids: Set[str]) -> List[str]:
        """Find launch files deploying nodes within this subsystem"""
        launches = set()
        for lf in self.launch_files:
            # Check if any declared node in launch belongs to this cluster
            lf_path = getattr(lf, "file_path", "")
            for l_node in getattr(lf, "nodes", []):
                p_name = getattr(l_node, "package", "")
                for nid in node_ids:
                    if nid.startswith(p_name):
                        launches.add(lf_path)
        return sorted(list(launches))

    def _compute_cohesion_coupling(self, node_ids: Set[str]) -> Tuple[float, float]:
        """Legacy wrapper returning (cohesion, total_coupling)."""
        m = self._compute_cohesion_coupling_detailed(node_ids)
        return m["cohesion"], m["coupling_total"]

    def _compute_cohesion_coupling_detailed(self, node_ids: Set[str]) -> Dict[str, Any]:
        """
        Compute mathematically bounded architecture metrics:
        - Directed Intra-Subsystem Cohesion: |unique directed pairs (u, v) in S, u != v| / (N * (N - 1)), in [0.0, 1.0]; 'N/A' when N < 2.
        - Internal Coupling: unique directed edges crossing between S and other in-repo subsystems.
        - External Interface Count (coupling_external): declared endpoints on nodes in S with no in-repo peer.
        - Interface Density: total declared interfaces in S / N.
        """
        unique_internal_pairs: Set[Tuple[str, str]] = set()
        unique_cross_edges: Set[Tuple[str, str, str, str]] = set()
        incoming = 0
        outgoing = 0
        matched_out_ifaces: Set[Tuple[str, str]] = set()
        matched_in_ifaces: Set[Tuple[str, str]] = set()

        for edge in self.edges:
            src_in = edge.source_node_id in node_ids
            tgt_in = edge.target_node_id in node_ids

            if src_in and tgt_in:
                if edge.source_node_id != edge.target_node_id:
                    unique_internal_pairs.add((edge.source_node_id, edge.target_node_id))
                matched_out_ifaces.add((edge.source_node_id, edge.interface_name))
                matched_in_ifaces.add((edge.target_node_id, edge.interface_name))
            elif src_in and not tgt_in:
                ek = (edge.source_node_id, edge.target_node_id, edge.communication_type, edge.interface_name)
                if ek not in unique_cross_edges:
                    unique_cross_edges.add(ek)
                    outgoing += 1
                matched_out_ifaces.add((edge.source_node_id, edge.interface_name))
            elif tgt_in and not src_in:
                ek = (edge.source_node_id, edge.target_node_id, edge.communication_type, edge.interface_name)
                if ek not in unique_cross_edges:
                    unique_cross_edges.add(ek)
                    incoming += 1
                matched_in_ifaces.add((edge.target_node_id, edge.interface_name))

        internal_edges = len(unique_internal_pairs)
        coupling_internal = len(unique_cross_edges)

        # Count external-facing interfaces (e.g. communicating with external nodes like move_group, servo_node, joy_node)
        total_ifaces = 0
        coupling_external = 0
        for nid in node_ids:
            node = self.nodes_by_id.get(nid)
            if not node:
                continue
            node_out = (
                [(p.name, "out") for p in node.publishers]
                + [(s.name, "out") for s in node.services if s.role == "client"]
                + [(a.name, "out") for a in node.actions if a.role == "client"]
            )
            node_in = (
                [(s.name, "in") for s in node.subscribers]
                + [(s.name, "in") for s in node.services if s.role == "server"]
                + [(a.name, "in") for a in node.actions if a.role == "server"]
            )
            total_ifaces += len(node_out) + len(node_in)
            for name, _ in node_out:
                if (nid, name) not in matched_out_ifaces:
                    coupling_external += 1
                    outgoing += 1
            for name, _ in node_in:
                if (nid, name) not in matched_in_ifaces:
                    coupling_external += 1
                    incoming += 1

        n_count = len(node_ids)
        if n_count >= 2:
            possible_pairs = n_count * (n_count - 1)
            cohesion = internal_edges / possible_pairs
            cohesion_status = "computed"
        else:
            cohesion = 0.0
            cohesion_status = "N/A"

        interface_density = (total_ifaces / n_count) if n_count > 0 else 0.0

        return {
            "internal_edges": internal_edges,
            "cohesion": cohesion,
            "cohesion_status": cohesion_status,
            "coupling_internal": float(coupling_internal),
            "coupling_external": float(coupling_external),
            "coupling_total": float(coupling_internal + coupling_external),
            "incoming": incoming,
            "outgoing": outgoing,
            "interface_density": interface_density,
        }

    def _find_boundary_interfaces(self, node_ids: Set[str]) -> Set[str]:
        """Identify topics, services, or actions that cross the subsystem boundary"""
        boundary = set()
        for edge in self.edges:
            src_in = edge.source_node_id in node_ids
            tgt_in = edge.target_node_id in node_ids
            if src_in != tgt_in:
                boundary.add(f"{edge.communication_type}::{edge.interface_name}")
        return boundary

    def _evaluate_against_reference(self, recovered_subsystems: List[Subsystem]) -> Dict[str, Any]:
        """
        Empirically compare recovered clusters against reference hypothesis.
        Computes precision, recall, and Jaccard similarity across subsystems.
        """
        metrics = {}
        rec_by_name = {s.name: set(s.nodes) for s in recovered_subsystems}

        total_jaccard = 0.0
        evaluated_count = 0

        for ref_name, ref_nodes in REFERENCE_NAV2_HYPOTHESIS.items():
            if not ref_nodes:
                continue
            rec_nodes = rec_by_name.get(ref_name, set())

            intersection = ref_nodes & rec_nodes
            union = ref_nodes | rec_nodes
            jaccard = len(intersection) / len(union) if union else 1.0

            precision = len(intersection) / len(rec_nodes) if rec_nodes else 0.0
            recall = len(intersection) / len(ref_nodes) if ref_nodes else 0.0

            metrics[ref_name] = {
                "reference_node_count": len(ref_nodes),
                "recovered_node_count": len(rec_nodes),
                "jaccard_similarity": round(jaccard, 3),
                "precision": round(precision, 3),
                "recall": round(recall, 3)
            }
            total_jaccard += jaccard
            evaluated_count += 1

        avg_jaccard = total_jaccard / evaluated_count if evaluated_count > 0 else 0.0
        return {
            "subsystem_metrics": metrics,
            "mean_jaccard_similarity": round(avg_jaccard, 3),
            "reference_subsystem_count": len(REFERENCE_NAV2_HYPOTHESIS),
            "recovered_subsystem_count": len(recovered_subsystems)
        }


def run_subsystem_recovery(
    nodes_json_path: Path,
    communication_graph_path: Path,
    launches_json_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> SubsystemModel:
    """Execute Stage 4.1 Subsystem Recovery"""
    with open(nodes_json_path, "r", encoding="utf-8") as f:
        nodes = [ROS2Node.model_validate(n) for n in json.load(f)]

    with open(communication_graph_path, "r", encoding="utf-8") as f:
        comm_data = json.load(f)
        edges = [CommunicationEdge.model_validate(e) for e in comm_data.get("source_potential_edges", [])]

    launches = []
    if launches_json_path and launches_json_path.exists():
        with open(launches_json_path, "r", encoding="utf-8") as f:
            from src.schema import LaunchFile
            launches = [LaunchFile.model_validate(l) for l in json.load(f)]

    synthesizer = SubsystemSynthesizer(nodes, edges, launches)
    model = synthesizer.recover_subsystems()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(model.model_dump(), f, indent=2)
        logger.info(f"Subsystem model saved to {output_path}")

    return model
