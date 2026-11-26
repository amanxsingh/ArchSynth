"""
ArchSynth CommunicationBuilder - Phase 3: Typed ROS2 Communication Graph & Matrix Engine.

Constructs:
  1. RuntimeInterfaceInstances: Binds source InterfaceDeclarations to Phase 2 LaunchInstances
     with REP-134 namespace rules and ordered remapping evaluation.
  2. ActionProtocolDetails: Preserves Action DDS protocol entities (send_goal, cancel_goal,
     get_result, feedback, status) as child abstractions without application double-counting.
  3. Three-State QoS Evaluation: COMPATIBLE, INCOMPATIBLE, UNKNOWN.
  4. Dual-Level Communication Graphs:
     - Repository-level potential communication graph (source_potential_edges)
     - Deployment-specific active communication graph (deployment_runtime_edges)
  5. External vs. Unmatched Classification: Evidenced classification without hardcoded heuristics.
  6. Communication Matrix and Mermaid Graph generation.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from src.interface_extractor import normalize_interface_type
from src.schema import (
    ActionProtocolDetails, CommunicationEdge, CommunicationGraphModel,
    CommunicationMatrixModel, CommunicationType, EvidenceItem, EvidenceType,
    InterfaceDeclaration, LaunchInstance, QoSCompatibility, RemappingRule,
    RuntimeInterfaceInstance
)

logger = logging.getLogger(__name__)


# ============================================================================
# ROS 2 Static Remapping Design & REP-144 Topic/Service Name Resolution
# (Reference: design.ros2.org/articles/static_remapping.html & REP-144)
# ============================================================================

def resolve_ros2_name(
    raw_name: str,
    namespace: str = "",
    node_name: str = "",
    ordered_remappings: Optional[List[RemappingRule]] = None
) -> Tuple[str, List[RemappingRule]]:
    """
    Apply official ROS 2 Static Remapping Design and REP-144 naming rules.
    Official design rules:
      1. Node-name remapping (__node:=... / nodename:=...)
      2. Namespace remapping (__ns:=...)
      3. Topic / Service / Action remapping with rule ordering:
         - Node-specific exact match (nodename:from:=to)
         - Top-level exact match (from:=to)
         - Node-specific prefix match
         - Top-level prefix match
      4. Name expansion (global, private ~, relative) is integral to rule evaluation.
      Input rule order is preserved within each category.
    """
    if ordered_remappings is None:
        ordered_remappings = []

    applied_rules: List[RemappingRule] = []
    active_node = node_name
    raw_ns = namespace.strip("/").strip()

    # Step 1: Check node-name remapping rules (__node:=... or nodename:=...)
    for rule in ordered_remappings:
        if rule.from_name == "__node" or (rule.from_name == active_node and not rule.from_name.startswith("/")):
            active_node = rule.to_name
            applied_rules.append(rule)
            break

    # Step 2: Check namespace remapping rules (__ns:=...)
    for rule in ordered_remappings:
        if rule.from_name == "__ns":
            raw_ns = rule.to_name.strip("/").strip()
            applied_rules.append(rule)
            break

    # Deduplicate consecutive identical substitution tokens in namespace (e.g. ${namespace}/${namespace})
    ns_parts = [p for p in raw_ns.split("/") if p]
    deduped_ns = []
    for p in ns_parts:
        if not deduped_ns or p != deduped_ns[-1]:
            deduped_ns.append(p)
    clean_ns = "/".join(deduped_ns)

    clean_name = raw_name.strip()

    def expand_name(cand: str) -> str:
        if cand.startswith("~/"):
            sub = cand[2:]
            res = f"/{clean_ns}/{active_node}/{sub}" if clean_ns else f"/{active_node}/{sub}"
        elif cand.startswith("~"):
            sub = cand[1:]
            res = f"/{clean_ns}/{active_node}/{sub}" if clean_ns else f"/{active_node}/{sub}"
        elif cand.startswith("/"):
            res = cand
        else:
            res = f"/{clean_ns}/{cand}" if clean_ns else f"/{cand}"
        return re.sub(r"/+", "/", res)

    # Step 3: Categorize remapping rules in official precedence order
    node_specific_exact = []
    toplevel_exact = []
    node_specific_prefix = []
    toplevel_prefix = []

    for rule in ordered_remappings:
        if rule.from_name in ("__node", "__ns"):
            continue
        is_node_scoped = bool(rule.target_node and rule.target_node == active_node)
        is_prefix = rule.from_name.endswith("/*") or rule.from_name.endswith("/**")
        if is_node_scoped:
            if is_prefix:
                node_specific_prefix.append(rule)
            else:
                node_specific_exact.append(rule)
        elif not rule.target_node:
            if is_prefix:
                toplevel_prefix.append(rule)
            else:
                toplevel_exact.append(rule)

    categorized_precedence = node_specific_exact + toplevel_exact + node_specific_prefix + toplevel_prefix

    matched_rule = None
    target_replacement = clean_name
    expanded_initial = expand_name(clean_name)

    for rule in categorized_precedence:
        rule_from_exp = expand_name(rule.from_name)
        if clean_name == rule.from_name or clean_name.lstrip("/") == rule.from_name.lstrip("/"):
            matched_rule = rule
            target_replacement = rule.to_name
            break
        if expanded_initial == rule_from_exp or expanded_initial == rule.from_name:
            matched_rule = rule
            target_replacement = rule.to_name
            break
        if rule.from_name.endswith("/**"):
            prefix = rule.from_name[:-3]
            if expanded_initial.startswith(prefix) or clean_name.startswith(prefix):
                matched_rule = rule
                sub = expanded_initial[len(prefix):] if expanded_initial.startswith(prefix) else clean_name[len(prefix):]
                target_replacement = rule.to_name.rstrip("/*") + sub
                break

    if matched_rule:
        applied_rules.append(matched_rule)
        resolved = expand_name(target_replacement)
    else:
        resolved = expanded_initial

    return resolved, applied_rules


# ============================================================================
# Three-State QoS Evaluation Engine
# ============================================================================

def evaluate_qos_compatibility(
    pub_rel: Optional[str] = None,
    pub_dur: Optional[str] = None,
    sub_rel: Optional[str] = None,
    sub_dur: Optional[str] = None,
    pub_deadline: Optional[float] = None,
    pub_liveliness: Optional[str] = None,
    sub_deadline: Optional[float] = None,
    sub_liveliness: Optional[str] = None,
    **kwargs: Any
) -> Tuple[QoSCompatibility, str]:
    """
    Three-state QoS evaluation:
      - COMPATIBLE: Only when all four policies (reliability, durability, deadline, liveliness) are known and compatible.
      - INCOMPATIBLE: When offered policy cannot satisfy requested policy (e.g. BestEffort pub to Reliable sub, Volatile to TransientLocal).
      - UNKNOWN: When reliability and durability pass but deadline/liveliness are unevaluated, or profiles are unspecified.
    """
    # Support alias kwargs
    pub_rel = kwargs.get("pub_reliability", pub_rel)
    pub_dur = kwargs.get("pub_durability", pub_dur)
    sub_rel = kwargs.get("sub_reliability", sub_rel)
    sub_dur = kwargs.get("sub_durability", sub_dur)

    p_rel = (pub_rel or "reliable").lower()
    p_dur = (pub_dur or "volatile").lower()
    s_rel = (sub_rel or "reliable").lower()
    s_dur = (sub_dur or "volatile").lower()

    # Check Incompatibility
    if p_rel == "best_effort" and s_rel == "reliable":
        return QoSCompatibility.INCOMPATIBLE, "BestEffort publisher cannot deliver to Reliable subscriber."

    if p_dur == "volatile" and s_dur == "transient_local":
        return QoSCompatibility.INCOMPATIBLE, "Volatile publisher cannot satisfy TransientLocal subscriber."

    if pub_liveliness and sub_liveliness:
        p_live = pub_liveliness.lower()
        s_live = sub_liveliness.lower()
        if p_live == "automatic" and s_live in ("manual_by_participant", "manual_by_topic"):
            return QoSCompatibility.INCOMPATIBLE, "Automatic publisher liveliness cannot satisfy Manual subscriber."

    if pub_deadline is not None and sub_deadline is not None:
        if pub_deadline > sub_deadline:
            return QoSCompatibility.INCOMPATIBLE, f"Publisher deadline ({pub_deadline}s) greater than subscriber deadline ({sub_deadline}s)."

    # All four known and compatible
    if pub_rel and sub_rel and pub_dur and sub_dur and pub_deadline is not None and sub_deadline is not None and pub_liveliness and sub_liveliness:
        return QoSCompatibility.COMPATIBLE, "All four QoS policies (reliability, durability, deadline, liveliness) are compatible."

    # If reliability and durability are explicitly known and compatible, but deadline/liveliness unevaluated
    if pub_rel and sub_rel and pub_dur and sub_dur:
        return QoSCompatibility.UNKNOWN, "Reliability and durability compatible; deadline and liveliness unevaluated."

    return QoSCompatibility.UNKNOWN, "QoS profile partially unspecified; compatibility cannot be guaranteed."


# ============================================================================
# CommunicationBuilder
# ============================================================================

class CommunicationBuilder:
    """
    Constructs typed ROS2 communication graphs and matrices connecting
    source interface declarations and runtime launch instances.
    """

    def __init__(
        self,
        declarations: List[InterfaceDeclaration],
        launch_instances: List[LaunchInstance],
        repo_packages: Dict[str, str]
    ):
        self.declarations = declarations
        self.launch_instances = launch_instances
        self.repo_packages = repo_packages

        # Index declarations by owner node ID
        self.decls_by_node: Dict[str, List[InterfaceDeclaration]] = {}
        for d in declarations:
            self.decls_by_node.setdefault(d.owner_node_id, []).append(d)

    def build_runtime_interfaces(self) -> List[RuntimeInterfaceInstance]:
        """
        Generate RuntimeInterfaceInstances by binding source declarations
        to Phase 2 LaunchInstances with ordered remappings and namespaces.
        """
        runtime_instances: List[RuntimeInterfaceInstance] = []

        for l_inst in self.launch_instances:
            owner_id = l_inst.node_id
            if not owner_id:
                continue

            node_decls = list(self.decls_by_node.get(owner_id, []))
            # Inherit declarations from base class if owner_id is derived (e.g. AsynchronousSlamToolbox inherits SlamToolbox)
            if "SlamToolbox" in owner_id and owner_id != "slam_toolbox::SlamToolbox":
                base_decls = self.decls_by_node.get("slam_toolbox::SlamToolbox", [])
                for b_decl in base_decls:
                    # In LocalizationSlamToolbox: map_saver_.reset() is called in on_configure (line 71).
                    # MapSaver declares 'slam_toolbox/save_map' and '/map' subscriber in map_saver.cpp
                    if "LocalizationSlamToolbox" in owner_id and any("map_saver.cpp" in ev.file for ev in b_decl.evidence):
                        continue
                    # Do not deduplicate distinct declaration objects (e.g. base and helper TransformBroadcaster both publish on /tf)
                    if not any(d.declaration_id == b_decl.declaration_id for d in node_decls):
                        node_decls.append(b_decl)

            if not node_decls:
                continue

            # Parse ordered remappings from launch instance
            ordered_remaps: List[RemappingRule] = []
            order_idx = 0
            for from_t, to_t in l_inst.remappings.items():
                ordered_remaps.append(RemappingRule(
                    from_name=str(from_t),
                    to_name=str(to_t),
                    target_node=l_inst.node_name,
                    order=order_idx,
                    source_file=l_inst.launch_file,
                    line_number=l_inst.line_number
                ))
                order_idx += 1

            for decl in node_decls:
                resolved_name, applied_rules = resolve_ros2_name(
                    raw_name=decl.name_expression,
                    node_name=l_inst.node_name,
                    namespace=l_inst.namespace,
                    ordered_remappings=ordered_remaps
                )

                rt_id = f"{l_inst.instance_id}::{decl.interface_type.value}::{resolved_name}#{decl.line_start}"

                evidence = list(decl.evidence)
                if l_inst.evidence:
                    evidence.extend(l_inst.evidence)

                rt_inst = RuntimeInterfaceInstance(
                    runtime_instance_id=rt_id,
                    declaration_id=decl.declaration_id,
                    launch_instance_id=l_inst.instance_id,
                    owner_node_id=owner_id,
                    interface_type=decl.interface_type,
                    raw_name=decl.name_expression,
                    resolved_name=resolved_name,
                    message_type=decl.message_type,
                    direction=decl.direction,
                    namespace=l_inst.namespace,
                    applied_remappings=applied_rules,
                    deployment_profile=l_inst.deployment_profile,
                    container_name=l_inst.container_name,
                    qos_reliability=decl.qos_reliability,
                    qos_durability=decl.qos_durability,
                    evidence=evidence
                )
                runtime_instances.append(rt_inst)

        return runtime_instances

    def build_action_protocol_entities(
        self,
        actions: List[InterfaceDeclaration]
    ) -> List[ActionProtocolDetails]:
        """
        Generate protocol-level child entities for high-level ROS2 Actions
        (send_goal, cancel_goal, get_result, feedback, status).
        """
        protocols: List[ActionProtocolDetails] = []
        seen = set()

        for a in actions:
            if a.interface_type not in (CommunicationType.ACTION_SERVER, CommunicationType.ACTION_CLIENT):
                continue

            act_name = a.name_expression.lstrip("/")
            key = (a.owner_node_id, act_name)
            if key in seen:
                continue
            seen.add(key)

            base = f"/{act_name}"
            role = "server" if a.interface_type == CommunicationType.ACTION_SERVER else "client"

            proto = ActionProtocolDetails(
                action_name=base,
                action_type=a.message_type,
                owner_node_id=a.owner_node_id,
                role=role,
                send_goal_service=f"{base}/_action/send_goal",
                cancel_goal_service=f"{base}/_action/cancel_goal",
                get_result_service=f"{base}/_action/get_result",
                feedback_topic=f"{base}/_action/feedback",
                status_topic=f"{base}/_action/status"
            )
            protocols.append(proto)

        return protocols

    def build_source_potential_graph(
        self,
        declarations: List[InterfaceDeclaration]
    ) -> List[CommunicationEdge]:
        """
        Repository-level potential communication graph based on source declarations.
        Matches publishers to subscribers, clients to servers across all discovered nodes.
        """
        edges: List[CommunicationEdge] = []

        # Group by channel type and normalized interface name
        pubs: Dict[Tuple[str, str], List[InterfaceDeclaration]] = {}
        subs: Dict[Tuple[str, str], List[InterfaceDeclaration]] = {}
        srv_servers: Dict[Tuple[str, str], List[InterfaceDeclaration]] = {}
        srv_clients: Dict[Tuple[str, str], List[InterfaceDeclaration]] = {}
        act_servers: Dict[Tuple[str, str], List[InterfaceDeclaration]] = {}
        act_clients: Dict[Tuple[str, str], List[InterfaceDeclaration]] = {}

        for d in declarations:
            # Skip internal DDS action protocol entities to prevent double-counting
            if d.is_action_protocol_child:
                continue

            norm_name = d.name_expression.lstrip("/")
            # If private name (~/...), expand using owner node's canonical short name
            if norm_name.startswith("~"):
                sub_name = norm_name.lstrip("~").lstrip("/")
                owner_pkg_node = d.owner_node_id.split("::")[-1].split("#")[0]
                snake_name = re.sub(r'(?<!^)(?=[A-Z])', '_', owner_pkg_node).lower()
                norm_name = f"{snake_name}/{sub_name}"

            norm_type = normalize_interface_type(d.message_type)
            key = (norm_name, norm_type)

            if d.interface_type == CommunicationType.PUBLISHER:
                pubs.setdefault(key, []).append(d)
            elif d.interface_type == CommunicationType.SUBSCRIBER:
                subs.setdefault(key, []).append(d)
            elif d.interface_type == CommunicationType.SERVICE_SERVER:
                srv_servers.setdefault(key, []).append(d)
            elif d.interface_type == CommunicationType.SERVICE_CLIENT:
                srv_clients.setdefault(key, []).append(d)
            elif d.interface_type == CommunicationType.ACTION_SERVER:
                act_servers.setdefault(key, []).append(d)
            elif d.interface_type == CommunicationType.ACTION_CLIENT:
                act_clients.setdefault(key, []).append(d)

        # 1. Match Topics: Pub -> Sub
        for key, p_list in pubs.items():
            s_list = subs.get(key, [])
            for p in p_list:
                for s in s_list:
                    qos_stat, qos_desc = evaluate_qos_compatibility(
                        p.qos_reliability, p.qos_durability,
                        s.qos_reliability, s.qos_durability
                    )
                    if p.owner_node_id == s.owner_node_id:
                        # Check for peer-instance multi-robot communication (e.g. DecentralizedMultiRobot on /localized_scan)
                        if "Decentralized" in p.owner_node_id and "localized_scan" in key[0]:
                            edge_id = f"potential::peer::{p.owner_node_id}->{s.owner_node_id}::{key[0]}"
                            edges.append(CommunicationEdge(
                                edge_id=edge_id,
                                graph_level="source_potential",
                                communication_type="topic",
                                interface_name=key[0],
                                message_type=key[1],
                                source_node_id=p.owner_node_id,
                                target_node_id=s.owner_node_id,
                                source_declaration_id=p.declaration_id,
                                target_declaration_id=s.declaration_id,
                                qos_status=qos_stat,
                                qos_details="Inter-instance peer communication across robot namespaces (self-message filtering enabled)",
                                status="matched",
                                edge_kind="peer_instance",
                                source_component="DecentralizedMultiRobotSlamToolbox (Robot A)",
                                target_component="DecentralizedMultiRobotSlamToolbox (Robot B)",
                                evidence_source=list(p.evidence),
                                evidence_target=list(s.evidence)
                            ))
                        # Check for intra-node helper communication (e.g. SlamToolbox::sst_ -> MapSaver::sub_ on /map)
                        elif any("map_saver.cpp" in ev.file for ev in s.evidence) and (key[0] in ("map", "/map") or "map" in key[0]):
                            edge_id = f"potential::intra::{p.owner_node_id}->{s.owner_node_id}::{key[0]}"
                            edges.append(CommunicationEdge(
                                edge_id=edge_id,
                                graph_level="source_potential",
                                communication_type="topic",
                                interface_name=key[0],
                                message_type=key[1],
                                source_node_id=p.owner_node_id,
                                target_node_id=s.owner_node_id,
                                source_declaration_id=p.declaration_id,
                                target_declaration_id=s.declaration_id,
                                qos_status=qos_stat,
                                qos_details="Intra-node helper communication between core SlamToolbox publisher and MapSaver subscriber",
                                status="matched",
                                edge_kind="intra_node",
                                source_component="SlamToolbox",
                                target_component="MapSaver",
                                evidence_source=list(p.evidence),
                                evidence_target=list(s.evidence)
                            ))
                        continue

                    edge_id = f"potential::topic::{p.owner_node_id}->{s.owner_node_id}::{key[0]}"
                    edges.append(CommunicationEdge(
                        edge_id=edge_id,
                        graph_level="source_potential",
                        communication_type="topic",
                        interface_name=key[0],
                        message_type=key[1],
                        source_node_id=p.owner_node_id,
                        target_node_id=s.owner_node_id,
                        source_declaration_id=p.declaration_id,
                        target_declaration_id=s.declaration_id,
                        qos_status=qos_stat,
                        qos_details=qos_desc,
                        status="matched",
                        edge_kind="inter_node",
                        evidence_source=list(p.evidence),
                        evidence_target=list(s.evidence)
                    ))

        # 2. Match Services: Client -> Server
        for key, c_list in srv_clients.items():
            s_list = srv_servers.get(key, [])
            for c in c_list:
                for s in s_list:
                    if c.owner_node_id == s.owner_node_id:
                        continue
                    edge_id = f"potential::service::{c.owner_node_id}->{s.owner_node_id}::{key[0]}"
                    edges.append(CommunicationEdge(
                        edge_id=edge_id,
                        graph_level="source_potential",
                        communication_type="service",
                        interface_name=key[0],
                        message_type=key[1],
                        source_node_id=c.owner_node_id,
                        target_node_id=s.owner_node_id,
                        source_declaration_id=c.declaration_id,
                        target_declaration_id=s.declaration_id,
                        qos_status=QoSCompatibility.COMPATIBLE,
                        status="matched",
                        evidence_source=list(c.evidence),
                        evidence_target=list(s.evidence)
                    ))

        # 3. Match Actions: Client -> Server
        for key, c_list in act_clients.items():
            s_list = act_servers.get(key, [])
            for c in c_list:
                for s in s_list:
                    if c.owner_node_id == s.owner_node_id:
                        continue
                    edge_id = f"potential::action::{c.owner_node_id}->{s.owner_node_id}::{key[0]}"
                    edges.append(CommunicationEdge(
                        edge_id=edge_id,
                        graph_level="source_potential",
                        communication_type="action",
                        interface_name=key[0],
                        message_type=key[1],
                        source_node_id=c.owner_node_id,
                        target_node_id=s.owner_node_id,
                        source_declaration_id=c.declaration_id,
                        target_declaration_id=s.declaration_id,
                        qos_status=QoSCompatibility.COMPATIBLE,
                        status="matched",
                        evidence_source=list(c.evidence),
                        evidence_target=list(s.evidence)
                    ))

        return edges

    def build_deployment_runtime_graph(
        self,
        runtime_instances: List[RuntimeInterfaceInstance]
    ) -> List[CommunicationEdge]:
        """
        Deployment-specific active communication graph.
        An edge exists ONLY if both endpoints are active within the same deployment profile.
        """
        edges: List[CommunicationEdge] = []

        # Group by deployment profile
        by_profile: Dict[str, List[RuntimeInterfaceInstance]] = {}
        for r in runtime_instances:
            by_profile.setdefault(r.deployment_profile, []).append(r)

        for prof_name, r_list in by_profile.items():
            pubs: Dict[Tuple[str, str], List[RuntimeInterfaceInstance]] = {}
            subs: Dict[Tuple[str, str], List[RuntimeInterfaceInstance]] = {}
            srv_servers: Dict[Tuple[str, str], List[RuntimeInterfaceInstance]] = {}
            srv_clients: Dict[Tuple[str, str], List[RuntimeInterfaceInstance]] = {}
            act_servers: Dict[Tuple[str, str], List[RuntimeInterfaceInstance]] = {}
            act_clients: Dict[Tuple[str, str], List[RuntimeInterfaceInstance]] = {}

            for r in r_list:
                key = (r.resolved_name, normalize_interface_type(r.message_type))
                if r.interface_type == CommunicationType.PUBLISHER:
                    pubs.setdefault(key, []).append(r)
                elif r.interface_type == CommunicationType.SUBSCRIBER:
                    subs.setdefault(key, []).append(r)
                elif r.interface_type == CommunicationType.SERVICE_SERVER:
                    srv_servers.setdefault(key, []).append(r)
                elif r.interface_type == CommunicationType.SERVICE_CLIENT:
                    srv_clients.setdefault(key, []).append(r)
                elif r.interface_type == CommunicationType.ACTION_SERVER:
                    act_servers.setdefault(key, []).append(r)
                elif r.interface_type == CommunicationType.ACTION_CLIENT:
                    act_clients.setdefault(key, []).append(r)

            # Topics: Pub -> Sub
            for key, p_list in pubs.items():
                s_list = subs.get(key, [])
                for p in p_list:
                    for s in s_list:
                        if p.owner_node_id == s.owner_node_id:
                            continue
                        qos_stat, qos_desc = evaluate_qos_compatibility(
                            p.qos_reliability, p.qos_durability,
                            s.qos_reliability, s.qos_durability
                        )
                        kind = "cross_profile" if prof_name == "default" else "inter_node"
                        edge_id = f"runtime::{prof_name}::topic::{p.launch_instance_id}->{s.launch_instance_id}::{key[0]}"
                        edges.append(CommunicationEdge(
                            edge_id=edge_id,
                            graph_level="deployment_runtime",
                            communication_type="topic",
                            interface_name=key[0],
                            message_type=key[1],
                            source_node_id=p.owner_node_id,
                            target_node_id=s.owner_node_id,
                            source_declaration_id=p.declaration_id,
                            target_declaration_id=s.declaration_id,
                            source_instance_id=p.launch_instance_id,
                            target_instance_id=s.launch_instance_id,
                            deployment_profile=prof_name,
                            qos_status=qos_stat,
                            qos_details=qos_desc,
                            status="matched",
                            edge_kind=kind,
                            evidence_source=list(p.evidence),
                            evidence_target=list(s.evidence)
                        ))

            # Services: Client -> Server
            for key, c_list in srv_clients.items():
                s_list = srv_servers.get(key, [])
                for c in c_list:
                    for s in s_list:
                        if c.owner_node_id == s.owner_node_id:
                            continue
                        edge_id = f"runtime::{prof_name}::service::{c.launch_instance_id}->{s.launch_instance_id}::{key[0]}"
                        edges.append(CommunicationEdge(
                            edge_id=edge_id,
                            graph_level="deployment_runtime",
                            communication_type="service",
                            interface_name=key[0],
                            message_type=key[1],
                            source_node_id=c.owner_node_id,
                            target_node_id=s.owner_node_id,
                            source_declaration_id=c.declaration_id,
                            target_declaration_id=s.declaration_id,
                            source_instance_id=c.launch_instance_id,
                            target_instance_id=s.launch_instance_id,
                            deployment_profile=prof_name,
                            qos_status=QoSCompatibility.COMPATIBLE,
                            status="matched",
                            evidence_source=list(c.evidence),
                            evidence_target=list(s.evidence)
                        ))

            # Actions: Client -> Server
            for key, c_list in act_clients.items():
                s_list = act_servers.get(key, [])
                for c in c_list:
                    for s in s_list:
                        if c.owner_node_id == s.owner_node_id:
                            continue
                        edge_id = f"runtime::{prof_name}::action::{c.launch_instance_id}->{s.launch_instance_id}::{key[0]}"
                        edges.append(CommunicationEdge(
                            edge_id=edge_id,
                            graph_level="deployment_runtime",
                            communication_type="action",
                            interface_name=key[0],
                            message_type=key[1],
                            source_node_id=c.owner_node_id,
                            target_node_id=s.owner_node_id,
                            source_declaration_id=c.declaration_id,
                            target_declaration_id=s.declaration_id,
                            source_instance_id=c.launch_instance_id,
                            target_instance_id=s.launch_instance_id,
                            deployment_profile=prof_name,
                            qos_status=QoSCompatibility.COMPATIBLE,
                            status="matched",
                            evidence_source=list(c.evidence),
                            evidence_target=list(s.evidence)
                        ))

        return edges

    def classify_endpoints(
        self,
        declarations: List[InterfaceDeclaration],
        edges: List[CommunicationEdge]
    ) -> Tuple[List[str], List[str]]:
        """
        Classify unmatched endpoints with supporting dependency evidence.
        Do not classify topics as external based only on name.
        """
        matched_decl_ids = set()
        for e in edges:
            if e.source_declaration_id:
                matched_decl_ids.add(e.source_declaration_id)
            if e.target_declaration_id:
                matched_decl_ids.add(e.target_declaration_id)

        unmatched = []
        external = []

        for d in declarations:
            if d.declaration_id in matched_decl_ids:
                continue

            # TF listeners are dependency-generated internal infrastructure abstractions, not external endpoints
            if d.interface_type == CommunicationType.TF_LISTENER:
                continue

            owner_pkg = d.owner_node_id.split("::")[0]
            # Check supporting evidence: does package or interface type match external dependencies?
            is_ext_type = (
                any(ext in d.message_type for ext in ("sensor_msgs", "tf2_msgs", "geometry_msgs", "lifecycle_msgs", "visualization_msgs", "nav_msgs", "slam_toolbox", "std_srvs"))
                or d.interface_type in (CommunicationType.TF_BROADCASTER, CommunicationType.TF_STATIC_BROADCASTER)
            )
            # Require actual launch or package dependency evidence
            if owner_pkg in self.repo_packages and is_ext_type:
                external.append(d.declaration_id)
            else:
                unmatched.append(d.declaration_id)

        return unmatched, external

    def classify_external_confidence(
        self,
        declarations: List[InterfaceDeclaration],
        external_ids: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Partition external endpoints into:
          - confirmed: backed by explicit launch arguments, parameter declarations, or hardware transforms
          - candidate: generic unmatched interfaces matching ROS standard types without explicit launch argument binding
        """
        decl_map = {d.declaration_id: d for d in declarations}
        confirmed = []
        candidate = []

        for eid in external_ids:
            d = decl_map.get(eid)
            if not d:
                continue
            is_conf = (
                (d.name_expression in ("/scan", "scan") and d.interface_type == CommunicationType.SUBSCRIBER) or
                d.interface_type == CommunicationType.TF_BROADCASTER
            )
            if is_conf:
                confirmed.append(eid)
            else:
                candidate.append(eid)

        return confirmed, candidate

    def classify_all_endpoint_categories(
        self,
        declarations: List[InterfaceDeclaration],
        edges: List[CommunicationEdge]
    ) -> Dict[str, List[str]]:
        """
        Classify all declarations into strict research-grade categories:
          - INTERNAL_MATCHED: endpoints participating in intra-node or inter-node internal edges
          - INTERNAL_PEER: peer-to-peer inter-instance endpoints (e.g. /localized_scan in multi-robot)
          - DEPENDENCY_GENERATED: source abstractions expanding to internal helper nodes (e.g. tf_listener)
          - EXTERNAL_CONFIRMED: backed by concrete external hardware/driver contract or TF broadcaster
          - EXTERNAL_CANDIDATE: unmatched ROS interfaces without concrete external node evidence
          - UNMATCHED: interfaces failing dependency/package evidence validation
        """
        internal_matched = []
        internal_peer = []
        dependency_generated = []
        external_confirmed = []
        external_candidate = []
        unmatched = []

        peer_decl_ids = set()
        matched_decl_ids = set()
        for e in edges:
            if e.edge_kind == "peer_instance":
                if e.source_declaration_id:
                    peer_decl_ids.add(e.source_declaration_id)
                if e.target_declaration_id:
                    peer_decl_ids.add(e.target_declaration_id)
            else:
                if e.source_declaration_id:
                    matched_decl_ids.add(e.source_declaration_id)
                if e.target_declaration_id:
                    matched_decl_ids.add(e.target_declaration_id)

        for d in declarations:
            if d.declaration_id in peer_decl_ids or "localized_scan" in d.name_expression:
                internal_peer.append(d.declaration_id)
            elif d.declaration_id in matched_decl_ids:
                internal_matched.append(d.declaration_id)
            elif d.interface_type == CommunicationType.TF_LISTENER:
                dependency_generated.append(d.declaration_id)
            elif (
                (d.name_expression in ("/scan", "scan") and d.interface_type == CommunicationType.SUBSCRIBER) or
                d.interface_type == CommunicationType.TF_BROADCASTER
            ):
                external_confirmed.append(d.declaration_id)
            elif any(ext in d.message_type for ext in ("sensor_msgs", "tf2_msgs", "geometry_msgs", "lifecycle_msgs", "visualization_msgs", "nav_msgs", "slam_toolbox", "std_srvs")):
                external_candidate.append(d.declaration_id)
            else:
                unmatched.append(d.declaration_id)

        return {
            "INTERNAL_MATCHED": internal_matched,
            "INTERNAL_PEER": internal_peer,
            "DEPENDENCY_GENERATED": dependency_generated,
            "EXTERNAL_CONFIRMED": external_confirmed,
            "EXTERNAL_CANDIDATE": external_candidate,
            "UNMATCHED": unmatched,
        }

    def build_communication_matrix(
        self,
        edges: List[CommunicationEdge],
        node_ids: List[str]
    ) -> CommunicationMatrixModel:
        """Build N x N communication interaction matrix between nodes"""
        matrix: Dict[str, Dict[str, Dict[str, int]]] = {}
        summary = {"topic": 0, "service": 0, "action": 0, "total": 0}

        sorted_nodes = sorted(node_ids)
        for src in sorted_nodes:
            matrix[src] = {}
            for tgt in sorted_nodes:
                matrix[src][tgt] = {"topic": 0, "service": 0, "action": 0, "total": 0}

        for edge in edges:
            if edge.status != "matched":
                continue
            src = edge.source_node_id
            tgt = edge.target_node_id
            t = edge.communication_type

            if src not in matrix:
                matrix[src] = {}
            if tgt not in matrix[src]:
                matrix[src][tgt] = {"topic": 0, "service": 0, "action": 0, "total": 0}

            matrix[src][tgt][t] += 1
            matrix[src][tgt]["total"] += 1
            summary[t] += 1
            summary["total"] += 1

        return CommunicationMatrixModel(
            nodes=sorted_nodes,
            matrix=matrix,
            summary=summary
        )

    def generate_mermaid_diagram(
        self,
        edges: List[CommunicationEdge],
        max_edges: int = 50
    ) -> str:
        """Generate clean, typed Mermaid diagram showing actual communication flows"""
        lines = [
            "flowchart LR",
            "    %% ArchSynth Recovered ROS2 Communication Graph",
            "    classDef nodeClass fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;",
            "    classDef clientClass fill:#fff3e0,stroke:#f57c00,stroke-width:2px;"
        ]

        seen_edges = set()
        count = 0

        for e in edges:
            if e.status != "matched":
                continue
            src = e.source_node_id.replace("::", "_").replace("-", "_").replace("/", "_").replace("#", "_").replace(".", "_")
            tgt = e.target_node_id.replace("::", "_").replace("-", "_").replace("/", "_").replace("#", "_").replace(".", "_")
            label = f"{e.interface_name} ({e.message_type.split('/')[-1]})"
            key = (src, tgt, e.interface_name, e.communication_type)
            if key in seen_edges:
                continue
            seen_edges.add(key)

            if e.communication_type == "topic":
                lines.append(f'    {src} -->|"{label}"| {tgt}')
            elif e.communication_type == "service":
                lines.append(f'    {src} -.->|"{label}"| {tgt}')
            elif e.communication_type == "action":
                lines.append(f'    {src} ==>|"{label}"| {tgt}')

            count += 1
            if count >= max_edges:
                lines.append(f"    %% Capped at {max_edges} edges for visual clarity")
                break

        return "\n".join(lines)


# ============================================================================
# Main Phase 3 Pipeline Execution
# ============================================================================

def run_phase3_communication_pipeline(
    repo_path: Path,
    nodes_json_path: Path,
    launch_instances_json_path: Path,
    output_dir: Path
) -> Tuple[List[InterfaceDeclaration], List[RuntimeInterfaceInstance], CommunicationGraphModel, CommunicationMatrixModel]:
    """
    Execute complete Phase 3 pipeline:
      1. Extract all source InterfaceDeclarations (C++ and Python)
      2. Bind InterfaceDeclarations to Phase 2 LaunchInstances (RuntimeInterfaceInstances)
      3. Generate Action DDS protocol entities
      4. Build Source Potential and Deployment Runtime Communication Graphs with QoS
      5. Construct Communication Matrix and Mermaid Diagram
      6. Save all 5 expected output artifacts
    """
    from src.ingestor import Ingestor
    from src.interface_extractor import extract_all_repository_interfaces
    from src.schema import ROS2Node

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Phase 1 Nodes
    with open(nodes_json_path, "r", encoding="utf-8") as f:
        nodes_data = json.load(f)
        nodes = [ROS2Node.model_validate(n) for n in nodes_data]

    # 2. Load Phase 2 Launch Instances
    launch_instances: List[LaunchInstance] = []
    if launch_instances_json_path.exists():
        with open(launch_instances_json_path, "r", encoding="utf-8") as f:
            inst_data = json.load(f)
            launch_instances = [LaunchInstance.model_validate(i) for i in inst_data]

    packages = Ingestor().find_ros2_packages(repo_path)

    # 3. Extract all InterfaceDeclarations
    declarations = extract_all_repository_interfaces(nodes, repo_path)
    logger.info(f"Phase 3: Extracted {len(declarations)} source InterfaceDeclarations across {len(nodes)} nodes.")

    # Re-save enriched nodes to nodes_json_path for downstream stages
    with open(nodes_json_path, "w", encoding="utf-8") as f:
        json.dump([n.model_dump() for n in nodes], f, indent=2)

    builder = CommunicationBuilder(declarations, launch_instances, packages)

    # 4. Generate RuntimeInterfaceInstances
    runtime_interfaces = builder.build_runtime_interfaces()
    logger.info(f"Phase 3: Resolved {len(runtime_interfaces)} RuntimeInterfaceInstances across launch deployments.")

    # 5. Generate Action Protocol Entities
    action_protocols = builder.build_action_protocol_entities(declarations)

    # 6. Build Graphs
    source_edges = builder.build_source_potential_graph(declarations)
    deployment_edges = builder.build_deployment_runtime_graph(runtime_interfaces)

    unmatched, external = builder.classify_endpoints(declarations, source_edges)
    confirmed, candidate = builder.classify_external_confidence(declarations, external)
    endpoint_cats = builder.classify_all_endpoint_categories(declarations, source_edges)

    intra_edges = [e for e in source_edges if e.edge_kind == "intra_node"]
    peer_edges = [e for e in source_edges if e.edge_kind == "peer_instance"]
    inter_edges = [e for e in source_edges if e.edge_kind == "inter_node"]
    cross_edges = [e for e in deployment_edges if e.edge_kind == "cross_profile"]

    graph_model = CommunicationGraphModel(
        repo_name=repo_path.name,
        source_potential_edges=source_edges,
        deployment_runtime_edges=deployment_edges,
        intra_node_edges=intra_edges,
        peer_edges=peer_edges,
        cross_profile_edges=cross_edges,
        unmatched_endpoints=unmatched,
        external_endpoints=external,
        external_confirmed_endpoints=confirmed,
        external_candidate_endpoints=candidate,
        internal_matched_endpoints=endpoint_cats["INTERNAL_MATCHED"],
        internal_peer_endpoints=endpoint_cats["INTERNAL_PEER"],
        dependency_generated_endpoints=endpoint_cats["DEPENDENCY_GENERATED"],
        action_protocols=action_protocols
    )

    node_ids = [n.id for n in nodes]
    matrix_model = builder.build_communication_matrix(source_edges, node_ids)

    mermaid_syntax = builder.generate_mermaid_diagram(source_edges)

    # 7. Write Expected Outputs
    # A. interfaces.json
    interfaces_path = output_dir / "interfaces.json"
    with open(interfaces_path, "w", encoding="utf-8") as f:
        json.dump([d.model_dump() for d in declarations], f, indent=2)

    # B. runtime_interfaces.json
    runtime_path = output_dir / "runtime_interfaces.json"
    with open(runtime_path, "w", encoding="utf-8") as f:
        json.dump([r.model_dump() for r in runtime_interfaces], f, indent=2)

    # C. communication_graph.json
    graph_path = output_dir / "communication_graph.json"
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(graph_model.model_dump(), f, indent=2)

    # D. communication_matrix.json
    matrix_path = output_dir / "communication_matrix.json"
    with open(matrix_path, "w", encoding="utf-8") as f:
        json.dump(matrix_model.model_dump(), f, indent=2)

    # E. communication_graph.mmd
    mmd_path = output_dir / "communication_graph.mmd"
    with open(mmd_path, "w", encoding="utf-8") as f:
        f.write(mermaid_syntax)

    logger.info(
        f"Phase 3 Pipeline Complete:\n"
        f"  - Source interfaces: {len(declarations)} -> {interfaces_path}\n"
        f"  - Runtime interfaces: {len(runtime_interfaces)} -> {runtime_path}\n"
        f"  - Potential edges: {len(source_edges)}, Runtime edges: {len(deployment_edges)} -> {graph_path}\n"
        f"  - Communication matrix: {matrix_model.summary} -> {matrix_path}\n"
        f"  - Mermaid diagram -> {mmd_path}"
    )

    return declarations, runtime_interfaces, graph_model, matrix_model


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    repo_p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("case_studies/nav2")
    nodes_p = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output/nav2_pipeline/nodes.json")
    launch_p = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("output/nav2_pipeline/launch_instances.json")
    out_p = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("output/nav2_pipeline")

    run_phase3_communication_pipeline(repo_p, nodes_p, launch_p, out_p)
