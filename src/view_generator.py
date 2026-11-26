"""
ArchSynth ViewGenerator - Phase 4: Architectural Views Generation.

Generates 8 structured architectural views conforming to ISO/IEC/IEEE 42010:
1. System Context View: Boundaries, external sensors, actuators, and client callers.
2. Package Dependency View: Build and runtime dependencies across Nav2 packages.
3. Subsystem / Component View: Recovered subsystems, cohesive functional clusters, roles.
4. Runtime Deployment View: Process hosts, composable node containers, launch hierarchies.
5. Communication View: Recovered pub/sub, service, and action interaction topology.
6. Lifecycle View: Managed node state machines, autostart transitions, sequencing.
7. Plugin Architecture View: Base class extension points, declared plugins, active selections.
8. Behavior Tree View: Navigation orchestration hierarchies, blackboard dataflow, server bindings.

Ensures views are distinct, self-contained, and render clean, focused Mermaid diagrams.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.schema import (
    ArchitectureView, ArchitectureViewsModel, BehaviorTreeCollectionModel,
    CommunicationGraphModel, LifecycleGraphModel, NodeLaunchMapping,
    PluginArchitectureModel, ROS2Node, SubsystemModel
)
from src.repo_identity import (
    RepositoryIdentity,
    load_validated_json,
    attach_artifact_provenance,
    validate_artifact_provenance,
)

logger = logging.getLogger(__name__)


class ViewGenerator:
    """
    Generates ISO/IEC/IEEE 42010 aligned architectural views from recovered subsystem,
    lifecycle, plugin, and behavior tree models.
    """

    def __init__(
        self,
        nodes: List[ROS2Node],
        subsystems_model: SubsystemModel,
        lifecycle_model: LifecycleGraphModel,
        plugin_model: PluginArchitectureModel,
        bt_model: BehaviorTreeCollectionModel,
        communication_graph: Optional[CommunicationGraphModel] = None,
        node_mappings: Optional[List[NodeLaunchMapping]] = None,
        repo_name: str = "ROS2",
        package_dependency_graph: Optional[Any] = None,
        launch_instances: Optional[List[Any]] = None,
        launch_containers: Optional[List[Any]] = None,
    ):
        self.nodes = nodes
        self.nodes_by_id = {n.id: n for n in nodes}
        self.subsystems_model = subsystems_model
        self.lifecycle_model = lifecycle_model
        self.plugin_model = plugin_model
        self.bt_model = bt_model
        self.communication_graph = communication_graph
        self.node_mappings = node_mappings or []
        self.repo_name = repo_name
        self.package_dependency_graph = package_dependency_graph
        self.launch_instances = launch_instances or []
        self.launch_containers = launch_containers or []

    def generate_all_views(self) -> ArchitectureViewsModel:
        """
        Synthesize all 8 architectural views.
        """
        views: Dict[str, ArchitectureView] = {}

        views["system_context"] = self._generate_system_context_view()
        views["package_dependency"] = self._generate_package_dependency_view()
        views["subsystem_component"] = self._generate_subsystem_view()
        views["runtime_deployment"] = self._generate_runtime_deployment_view()
        views["communication_topology"] = self._generate_communication_view()
        views["lifecycle_architecture"] = self._generate_lifecycle_view()
        views["plugin_architecture"] = self._generate_plugin_view()
        views["behavior_tree_orchestration"] = self._generate_behavior_tree_view()

        summary = {
            "total_views": len(views),
            "standards_alignment": "ISO/IEC/IEEE 42010",
            "view_ids": list(views.keys()),
            "subsystem_count": len(self.subsystems_model.subsystems),
            "managed_node_count": len(self.lifecycle_model.managed_nodes),
            "plugin_count": len(self.plugin_model.plugins),
            "behavior_trees_count": self.bt_model.total_trees
        }

        return ArchitectureViewsModel(
            standards_alignment="ISO/IEC/IEEE 42010",
            views=views,
            summary=summary
        )

    def _generate_system_context_view(self) -> ArchitectureView:
        """View 1: System Context View (derived strictly from recovered nodes, interfaces, and external launch peers)."""
        matched_in_pubs = set()
        matched_in_subs = set()
        if self.communication_graph:
            for e in self.communication_graph.source_potential_edges:
                matched_in_pubs.add((e.source_node_id, e.interface_name))
                matched_in_subs.add((e.target_node_id, e.interface_name))

        ext_in_topics = sorted({
            s.name for n in self.nodes for s in n.subscribers
            if s.name and (n.id, s.name) not in matched_in_subs
        })
        ext_out_topics = sorted({
            p.name for n in self.nodes for p in n.publishers
            if p.name and (n.id, p.name) not in matched_in_pubs
        })
        ext_srv_calls = sorted({
            s.name for n in self.nodes for s in n.services
            if s.name and s.role == "client" and (n.id, s.name) not in matched_in_pubs
        })
        ext_srv_provs = sorted({
            s.name for n in self.nodes for s in n.services
            if s.name and s.role == "server" and (n.id, s.name) not in matched_in_subs
        })
        ext_acts = sorted({
            a.name for n in self.nodes for a in n.actions
            if a.name
        })

        # External packages referenced in launch instances
        internal_pkgs = {n.package_name for n in self.nodes if n.package_name}
        ext_launch_pkgs = sorted({
            inst.package for inst in self.launch_instances
            if inst.package and inst.package not in internal_pkgs and "${" not in inst.package
        })

        lines = [
            "flowchart TD",
            f'    subgraph SystemBoundary ["{self.repo_name} System Boundary ({len(self.nodes)} source nodes)"]',
            f'        SystemCore["{self.repo_name} Core Nodes"]',
            "    end",
        ]
        entities = [{"name": f"{self.repo_name} Core Nodes", "type": "software_system"}]
        relationships = []

        if ext_srv_provs or ext_acts:
            iface_str = ", ".join((ext_acts or ext_srv_provs)[:4])
            lines.append('    ClientApp["External ROS 2 Callers / Clients"]')
            lines.append(f'    ClientApp -->|"{iface_str}"| SystemCore')
            entities.append({"name": "External ROS 2 Callers / Clients", "type": "external_actor"})
            relationships.append({"source": "External ROS 2 Callers / Clients", "target": f"{self.repo_name} Core Nodes", "type": "service_or_action_call"})

        if ext_in_topics:
            sub_str = ", ".join(ext_in_topics[:4])
            lines.append('    ExtSources["External Publishers / Sensors"]')
            lines.append(f'    ExtSources -->|"{sub_str}"| SystemCore')
            entities.append({"name": "External Publishers / Sensors", "type": "external_source"})
            relationships.append({"source": "External Publishers / Sensors", "target": f"{self.repo_name} Core Nodes", "type": "topic_subscription"})

        if ext_out_topics or ext_srv_calls:
            out_str = ", ".join((ext_out_topics or ext_srv_calls)[:4])
            ext_label = f"External Targets ({', '.join(ext_launch_pkgs[:3])})" if ext_launch_pkgs else "External Consumers / Servers"
            lines.append(f'    ExtTargets["{ext_label}"]')
            lines.append(f'    SystemCore -->|"{out_str}"| ExtTargets')
            entities.append({"name": ext_label, "type": "external_target"})
            relationships.append({"source": f"{self.repo_name} Core Nodes", "target": ext_label, "type": "topic_or_service_output"})

        mermaid = "\n".join(lines) + "\n"
        desc = (
            f"System boundary for {self.repo_name} derived from {len(self.nodes)} source nodes, "
            f"unmatched external-peer interfaces, and {len(ext_launch_pkgs)} external launch packages."
        )

        return ArchitectureView(
            view_id="system_context",
            name="System Context View",
            description=desc,
            architectural_concerns=["System boundaries", "External interfaces", "Operational environment"],
            target_stakeholders=["System Architects", "Robotics Integrators", "Application Engineers"],
            entities=entities,
            relationships=relationships,
            mermaid_diagram=mermaid
        )

    def _generate_package_dependency_view(self) -> ArchitectureView:
        """View 2: Package Dependency View (derived strictly from PackageDependencyGraph)."""
        if self.package_dependency_graph and self.package_dependency_graph.packages:
            pdg = self.package_dependency_graph
            lines = ["flowchart TD"]
            for p in pdg.packages:
                pid = p.name.replace("-", "_")
                lines.append(f'    {pid}["{p.name} ({p.build_type})"]')

            added_ext = set()
            seen_edges = set()
            entities = [{"name": p.name, "type": "internal_package", "build_type": p.build_type} for p in pdg.packages]
            relationships = []

            for edge in pdg.edges:
                if edge.resolution_category == "unresolved_external_library":
                    continue
                src = edge.source_package.replace("-", "_")
                tgt = edge.target_package.replace("-", "_")
                is_key_ext = edge.is_target_internal or any(
                    k in edge.target_package.lower()
                    for k in ("moveit", "ros2_control", "controller", "gazebo", "ros_gz", "nav2", "tf2", "rviz", "xacro", "behaviortree")
                )
                if not is_key_ext:
                    continue
                ekey = (edge.source_package, edge.target_package, edge.dependency_type)
                if ekey in seen_edges:
                    continue
                seen_edges.add(ekey)
                if not edge.is_target_internal and tgt not in added_ext:
                    if len(added_ext) >= 12:
                        continue
                    lines.append(f'    {tgt}["{edge.target_package} (external)"]')
                    entities.append({"name": edge.target_package, "type": "external_ros_package"})
                    added_ext.add(tgt)
                arrow = "-.->" if edge.origin == "observed_source" else "-->"
                lines.append(f'    {src} {arrow}|"{edge.dependency_type}"| {tgt}')
                relationships.append({
                    "source": edge.source_package,
                    "target": edge.target_package,
                    "type": edge.dependency_type,
                    "origin": edge.origin,
                })

            mermaid = "\n".join(lines)
            desc = (
                f"Directed package dependency graph across {len(pdg.internal_packages)} repository packages "
                f"and {len(pdg.external_packages)} external dependencies (package.xml, setup.py, and resolved source dependencies)."
            )
        else:
            pkgs = sorted(list({n.package_name for n in self.nodes if n.package_name}))
            if not pkgs:
                pkgs = [self.repo_name]
            lines = ["flowchart TD"]
            for pkg in pkgs:
                lines.append(f'    {pkg.replace("-", "_")}["{pkg}"]')
            mermaid = "\n".join(lines)
            desc = f"Structural packages discovered in {self.repo_name} (no package dependency graph provided)."
            entities = [{"name": p, "type": "internal_package"} for p in pkgs]
            relationships = []

        return ArchitectureView(
            view_id="package_dependency",
            name="Package Dependency View",
            description=desc,
            architectural_concerns=["Package coupling", "Build layering", "Modular reusability"],
            target_stakeholders=["Software Maintainers", "Build Engineers", "Component Developers"],
            entities=entities,
            relationships=relationships,
            mermaid_diagram=mermaid
        )

    def _generate_subsystem_view(self) -> ArchitectureView:
        """View 3: Subsystem / Component View (derived strictly from recovered SubsystemModel and CommunicationGraph)."""
        lines = [
            "flowchart TB",
            f'    subgraph ProductionSubsystems ["{self.repo_name} Production Stack"]'
        ]
        entities = []
        relationships = []
        node_to_sub: Dict[str, str] = {}

        for sub in self.subsystems_model.subsystems:
            for nid in sub.nodes:
                node_to_sub[nid] = sub.name
            if sub.is_test_infrastructure or sub.is_client_application:
                continue
            sub_id = sub.name.replace("-", "_")
            coh_str = "N/A" if getattr(sub, "cohesion_status", "computed") == "N/A" else f"{sub.intra_cohesion_score}"
            lines.append(f'        subgraph {sub_id} ["{sub.name.replace("_", " ").title()} (Cohesion={coh_str})"]')
            entities.append({"name": sub.name, "type": sub.architectural_role, "node_count": len(sub.nodes)})
            for n in sub.nodes[:6]:
                short_n = n.split("::")[-1]
                safe_n = short_n.replace("/", "_").replace(":", "_").replace("-", "_")
                lines.append(f'            {sub_id}_{safe_n}["{short_n}"]')
            lines.append("        end")
        lines.append("    end")

        client_subs = [s for s in self.subsystems_model.subsystems if s.is_client_application]
        for csub in client_subs:
            cid = csub.name.replace("-", "_")
            lines.append(f'    subgraph {cid} ["Client API"]')
            for n in csub.nodes[:4]:
                short_n = n.split("::")[-1]
                lines.append(f'        {cid}_{short_n}["{short_n}"]')
            lines.append("    end")
            entities.append({"name": csub.name, "type": "client_interface", "node_count": len(csub.nodes)})

        test_nodes = [n for n in self.nodes if n.is_test]
        if test_nodes:
            lines.append('    subgraph TestInfra ["Validation Test Infrastructure"]')
            lines.append(f'        Harnesses["{len(test_nodes)} Test Harnesses & Mocks"]')
            lines.append("    end")
            entities.append({"name": "validation_test_infrastructure", "type": "test_harness", "node_count": len(test_nodes)})

        # Derive inter-subsystem edges strictly from recovered communication graph
        if self.communication_graph:
            seen_sub_edges = set()
            for edge in self.communication_graph.source_potential_edges:
                s_sub = node_to_sub.get(edge.source_node_id)
                t_sub = node_to_sub.get(edge.target_node_id)
                if s_sub and t_sub and s_sub != t_sub and "test" not in s_sub and "test" not in t_sub:
                    ekey = (s_sub, t_sub, edge.communication_type)
                    if ekey not in seen_sub_edges:
                        seen_sub_edges.add(ekey)
                        lines.append(f'    {s_sub.replace("-", "_")} -->|"{edge.communication_type}: {edge.interface_name}"| {t_sub.replace("-", "_")}')
                        relationships.append({"source": s_sub, "target": t_sub, "type": edge.communication_type, "interface": edge.interface_name})

        desc = f"Recovered functional software subsystems, metrics, and inter-subsystem communication edges for {self.repo_name}."
        mermaid = "\n".join(lines)

        return ArchitectureView(
            view_id="subsystem_component",
            name="Subsystem / Component View",
            description=desc,
            architectural_concerns=["Functional decomposition", "Subsystem cohesion", "Coupling minimization"],
            target_stakeholders=["Lead Architects", "Functional Leads", "Domain Engineers"],
            entities=entities,
            relationships=relationships,
            mermaid_diagram=mermaid
        )

    def _generate_runtime_deployment_view(self) -> ArchitectureView:
        """View 4: Static Launch-Inferred Deployment View (derived strictly from LaunchContainers and LaunchInstances)."""
        entities = []
        relationships = []

        if self.launch_instances or self.launch_containers:
            lines = [
                "flowchart TD",
                f'    subgraph StaticLaunchDeployment ["Static Launch-Declared Deployment - {self.repo_name}"]'
            ]
            composed_ids = set()
            for cont in self.launch_containers[:8]:
                c_safe = cont.name.replace("/", "_").replace("-", "_").replace(":", "_")
                lines.append(f'        subgraph cont_{c_safe} ["Container: {cont.name} ({cont.executable})"]')
                entities.append({"name": cont.name, "type": "composable_container", "executable": cont.executable})
                for comp_id in cont.loaded_components[:10]:
                    composed_ids.add(comp_id)
                    short_c = comp_id.split("::")[-1].split("#")[0]
                    csafe = short_c.replace("/", "_").replace("-", "_").replace(":", "_")
                    lines.append(f'            comp_{c_safe}_{csafe}["Component: {short_c}"]')
                    entities.append({"name": short_c, "type": "composable_component", "container": cont.name})
                    relationships.append({"source": cont.name, "target": short_c, "type": "hosts_component"})
                lines.append("        end")

            seen_proc = set()
            for inst in self.launch_instances:
                if inst.instance_id in composed_ids or inst.is_composable:
                    continue
                exe = inst.executable or inst.node_name
                pkg = inst.package or "unknown"
                key = (pkg, exe)
                if key in seen_proc:
                    continue
                seen_proc.add(key)
                if len(seen_proc) > 16:
                    break
                safe_id = f"{pkg}_{exe}".replace("/", "_").replace("-", "_").replace(":", "_").replace("${", "dyn_").replace("}", "").replace(".", "_")
                label = f"{exe} [{pkg}]" if "${" not in str(exe) else f"{exe} (unresolved dynamic)"
                lines.append(f'        proc_{safe_id}["Launch Executable: {label}"]')
                entities.append({"name": exe, "package": pkg, "type": "launch_executable", "launch_file": inst.launch_file})

            if self.lifecycle_model and self.lifecycle_model.lifecycle_managers:
                for mgr in self.lifecycle_model.lifecycle_managers[:4]:
                    m_id = mgr.manager_name.replace("/", "_").replace("-", "_")
                    lines.append(f'        mgr_{m_id}["LifecycleManager: {mgr.manager_name}"]')
                    entities.append({"name": mgr.manager_name, "type": "lifecycle_manager"})

            lines.append("    end")
            mermaid = "\n".join(lines)
            desc = (
                f"Static launch-declared deployment topology for {self.repo_name} "
                f"({len(self.launch_containers)} containers, {len(self.launch_instances)} launch instances). "
                "Note: OS process hosting is inferred from launch declarations, not runtime-observed."
            )
        else:
            mermaid = f'flowchart TD\n    NoLaunch["No launch deployment instances loaded for {self.repo_name}; process topology unverified"]\n'
            desc = (
                f"No launch-declared deployment instances or containers were recovered for {self.repo_name}; "
                "deployment process topology cannot be inferred without launch or runtime observation."
            )

        return ArchitectureView(
            view_id="runtime_deployment",
            name="Runtime Deployment View",
            description=desc,
            architectural_concerns=["Process allocation", "IPC vs Intra-process communication", "Deployment efficiency"],
            target_stakeholders=["Deployment Engineers", "Embedded Systems Leads", "Performance Engineers"],
            entities=entities,
            relationships=relationships,
            mermaid_diagram=mermaid
        )

    def _generate_communication_view(self) -> ArchitectureView:
        """View 5: Communication View (derived strictly from CommunicationGraph edges or node interfaces)."""
        lines = ["flowchart LR"]
        entities = []
        relationships = []
        added_nodes = set()

        if self.communication_graph and self.communication_graph.source_potential_edges:
            for edge in self.communication_graph.source_potential_edges[:15]:
                src_val = edge.source_node_id
                tgt_val = edge.target_node_id
                iface_val = edge.interface_name
                comm_type_val = edge.communication_type

                src_short = src_val.split("::")[-1]
                tgt_short = tgt_val.split("::")[-1]
                src_id = src_short.replace("/", "_").replace(":", "_").replace("-", "_")
                tgt_id = tgt_short.replace("/", "_").replace(":", "_").replace("-", "_")
                if src_short not in added_nodes:
                    lines.append(f'    {src_id}["{src_short}"]')
                    entities.append({"name": src_short, "type": "node"})
                    added_nodes.add(src_short)
                if tgt_short not in added_nodes:
                    lines.append(f'    {tgt_id}["{tgt_short}"]')
                    entities.append({"name": tgt_short, "type": "node"})
                    added_nodes.add(tgt_short)
                lines.append(f'    {src_id} -->|"{iface_val} [{comm_type_val}]"| {tgt_id}')
                relationships.append({"source": src_short, "target": tgt_short, "interface": iface_val, "type": comm_type_val})
        else:
            prod_nodes = [n for n in self.nodes if not n.is_test]
            for n in prod_nodes[:8]:
                name = n.name or n.class_name
                safe = name.replace("/", "_").replace(":", "_").replace("-", "_")
                lines.append(f'    node_{safe}["{name}"]')
                entities.append({"name": name, "type": "node"})
                for p in n.publishers[:2]:
                    p_safe = p.name.replace("/", "_").replace(":", "_").replace("-", "_")
                    lines.append(f'    node_{safe} -->|"{p.name}"| topic_{p_safe}["{p.name}"]')
                    relationships.append({"source": name, "target": p.name, "type": "publisher"})

        mermaid = "\n".join(lines)
        desc = f"Recovered interaction topology displaying topics, services, and actions for {self.repo_name}."

        return ArchitectureView(
            view_id="communication_topology",
            name="Communication View",
            description=desc,
            architectural_concerns=["Dataflow", "Message passing latency", "Interface compatibility"],
            target_stakeholders=["Integration Engineers", "Safety Engineers", "Robotics Developers"],
            entities=entities,
            relationships=relationships,
            mermaid_diagram=mermaid
        )

    def _generate_lifecycle_view(self) -> ArchitectureView:
        """View 6: Lifecycle View (generated only when lifecycle entities exist)."""
        has_lifecycle = bool(
            self.lifecycle_model
            and (
                self.lifecycle_model.lifecycle_managers
                or self.lifecycle_model.managed_nodes
                or any(n.is_lifecycle for n in self.nodes)
            )
        )
        entities = []
        relationships = []
        if not has_lifecycle:
            mermaid = f'flowchart TD\n    NoLifecycle["No ROS 2 lifecycle managers or lifecycle nodes detected in {self.repo_name}"]\n'
            desc = (
                f"No ROS 2 lifecycle nodes, lifecycle managers, or lifecycle configurations were detected in {self.repo_name}. "
                "System-specific lifecycle diagram omitted."
            )
        else:
            mermaid = self.lifecycle_model.mermaid_diagram or f'flowchart TD\n    LifecycleNodes["Lifecycle nodes detected in {self.repo_name}"]\n'
            for mgr in self.lifecycle_model.lifecycle_managers:
                entities.append({"name": mgr.manager_name, "type": "lifecycle_manager"})
                for mn in mgr.managed_node_names:
                    relationships.append({"source": mgr.manager_name, "target": mn, "type": "manages_lifecycle"})
            desc = f"State machine sequencing and lifecycle management recovered for {self.repo_name}."

        return ArchitectureView(
            view_id="lifecycle_architecture",
            name="Lifecycle View",
            description=desc,
            architectural_concerns=["Deterministic startup", "State consistency", "Fault isolation"],
            target_stakeholders=["System Engineers", "Safety Certification Authorities", "Operations"],
            entities=entities,
            relationships=relationships,
            mermaid_diagram=mermaid
        )

    def _generate_plugin_view(self) -> ArchitectureView:
        """View 7: Plugin Architecture View (derived strictly from recovered PluginArchitectureModel)."""
        entities = []
        relationships = []
        if self.plugin_model and self.plugin_model.plugins:
            clean_lines = ["classDiagram", "    direction TB"]
            known_bases = set()
            for p in self.plugin_model.plugins[:35]:
                base_cls = p.base_class_type if p.base_class_type else "PluginInterface"
                base_id = base_cls.replace("::", "_").replace("<", "_").replace(">", "_")
                if base_id not in known_bases:
                    clean_lines.append(f"    class {base_id} {{\n        <<interface>>\n    }}")
                    known_bases.add(base_id)
                    entities.append({"name": base_cls, "type": "plugin_base_class"})
                p_id = p.class_type.replace("::", "_").replace("<", "_").replace(">", "_")
                clean_lines.append(f"    class {p_id} {{\n        package: {p.package_name}\n    }}")
                clean_lines.append(f"    {base_id} <|-- {p_id}")
                entities.append({"name": p.class_type, "package": p.package_name, "type": "plugin_implementation"})
                relationships.append({"source": base_cls, "target": p.class_type, "type": "implements"})
            mermaid = "\n".join(clean_lines)
        else:
            mermaid = "classDiagram\n    class NoPluginsDeclared\n"
        desc = f"Pluginlib extensibility patterns and implementations recovered for {self.repo_name}."

        return ArchitectureView(
            view_id="plugin_architecture",
            name="Plugin Architecture View",
            description=desc,
            architectural_concerns=["Extensibility", "Algorithm swappability", "Runtime polymorphism"],
            target_stakeholders=["Algorithm Developers", "Extension Authors", "Software Architects"],
            entities=entities,
            relationships=relationships,
            mermaid_diagram=mermaid
        )

    def _generate_behavior_tree_view(self) -> ArchitectureView:
        """View 8: Behavior Tree View (derived strictly from BehaviorTreeCollectionModel)."""
        entities = []
        relationships = []
        if self.bt_model and self.bt_model.trees:
            default_tree = self.bt_model.trees[0]
            mermaid = default_tree.mermaid_diagram
            for t in self.bt_model.trees:
                entities.append({"name": t.tree_name, "type": "behavior_tree"})
            for b in self.bt_model.bt_to_ros2_bindings:
                relationships.append({"source": b.get("bt_node", ""), "target": b.get("target_interface", ""), "type": b.get("type", "action")})
            desc = f"BehaviorTree orchestration showing control flow for {self.repo_name} ({self.bt_model.total_trees} trees)."
        else:
            mermaid = f'flowchart TD\n    NoBT["No Behavior Tree definitions declared in {self.repo_name}"]\n'
            desc = f"Behavior Tree navigation orchestration is not utilized in {self.repo_name}."

        return ArchitectureView(
            view_id="behavior_tree_orchestration",
            name="Behavior Tree View",
            description=desc,
            architectural_concerns=["Autonomous mission execution", "Reactive recovery", "Blackboard dataflow"],
            target_stakeholders=["Autonomy Engineers", "Behavior Designers", "Test Engineers"],
            entities=entities,
            relationships=relationships,
            mermaid_diagram=mermaid
        )


def run_views_generation(
    nodes_json_path: Path,
    subsystem_json_path: Path,
    lifecycle_json_path: Path,
    plugin_json_path: Path,
    bt_json_path: Path,
    comm_graph_json_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    repo_name: str = "ROS2",
    package_dependency_graph: Optional[Any] = None,
    launches_json_path: Optional[Path] = None,
) -> ArchitectureViewsModel:
    """Execute Stage 4.5 Architecture Views Generation with repository provenance verification"""
    expected_identity = RepositoryIdentity(
        repo_name=repo_name,
        repo_root=str(nodes_json_path.parent),
    )

    with open(nodes_json_path, "r", encoding="utf-8") as f:
        nodes = [ROS2Node.model_validate(n) for n in json.load(f)]

    sub_data = load_validated_json(subsystem_json_path, expected_identity, purge_invalid=False)
    if sub_data is not None:
        try:
            sub_model = SubsystemModel.model_validate(sub_data)
        except Exception as e:
            logger.warning(f"Could not validate subsystem model: {e}")
            sub_model = SubsystemModel(subsystems=[])
    else:
        sub_model = SubsystemModel(subsystems=[])

    life_data = load_validated_json(lifecycle_json_path, expected_identity, purge_invalid=False)
    if life_data is not None:
        try:
            life_model = LifecycleGraphModel.model_validate(life_data)
        except Exception as e:
            logger.warning(f"Could not validate lifecycle model: {e}")
            life_model = LifecycleGraphModel()
    else:
        life_model = LifecycleGraphModel()

    plug_data = load_validated_json(plugin_json_path, expected_identity, purge_invalid=False)
    if plug_data is not None:
        try:
            plug_model = PluginArchitectureModel.model_validate(plug_data)
        except Exception as e:
            logger.warning(f"Could not validate plugin architecture model: {e}")
            plug_model = PluginArchitectureModel()
    else:
        plug_model = PluginArchitectureModel()

    bt_data = load_validated_json(bt_json_path, expected_identity, purge_invalid=False)
    if bt_data is not None:
        try:
            bt_model = BehaviorTreeCollectionModel.model_validate(bt_data)
        except Exception as e:
            logger.warning(f"Could not validate behavior tree model: {e}")
            bt_model = BehaviorTreeCollectionModel()
    else:
        bt_model = BehaviorTreeCollectionModel()

    comm_model = None
    if comm_graph_json_path:
        comm_data = load_validated_json(comm_graph_json_path, expected_identity, purge_invalid=False)
        if comm_data is not None:
            try:
                comm_model = CommunicationGraphModel.model_validate(comm_data)
            except Exception as e:
                logger.warning(f"Could not validate communication graph model: {e}")

    launch_instances = []
    launch_containers = []
    if launches_json_path and launches_json_path.exists():
        try:
            from src.schema import LaunchFile
            with open(launches_json_path, "r", encoding="utf-8") as f:
                ldata = json.load(f)
            for lf_dict in ldata:
                lf = LaunchFile.model_validate(lf_dict)
                launch_instances.extend(lf.instances)
                launch_containers.extend(lf.containers)
        except Exception as e:
            logger.warning(f"Could not load launch instances for views: {e}")

    generator = ViewGenerator(
        nodes=nodes,
        subsystems_model=sub_model,
        lifecycle_model=life_model,
        plugin_model=plug_model,
        bt_model=bt_model,
        communication_graph=comm_model,
        repo_name=repo_name,
        package_dependency_graph=package_dependency_graph,
        launch_instances=launch_instances,
        launch_containers=launch_containers,
    )
    views_model = generator.generate_all_views()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(views_model.model_dump(), f, indent=2)
        attach_artifact_provenance(output_path, expected_identity)
        logger.info(f"Architecture views saved to {output_path}")

    return views_model

