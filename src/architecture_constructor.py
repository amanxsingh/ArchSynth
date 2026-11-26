"""
ArchSynth SystemArchitectureConstructor - Stage 4:
Synthesizes NodeAnalyzer (Stage 2) and LaunchFileAnalyzer (Stage 3) outputs
into a hierarchical ArchitectureModel and Mermaid diagram using LLM synthesis.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from src.schema import (
    ROS2Node, LaunchFile, Subsystem, ArchitectureModel, TopicInfo, ServiceInfo, ActionInfo,
    EntityType, ResolutionStatus, InterfaceDeclaration, RuntimeInterfaceInstance,
    CommunicationGraphModel, CommunicationMatrixModel, SubsystemModel,
    LifecycleGraphModel, PluginArchitectureModel, BehaviorTreeCollectionModel,
    ArchitectureViewsModel
)
from src.llm_client import LLMClient
from src.repo_identity import (
    RepositoryIdentity,
    load_validated_json,
    attach_artifact_provenance,
    validate_artifact_provenance,
)

logger = logging.getLogger(__name__)


class ArchitectureConstructor:
    """
    Synthesizes ROS2 node models and launch file composition into a unified
    hierarchical ArchitectureModel with subsystem groupings and Mermaid diagrams.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def construct(
        self,
        nodes: List[ROS2Node],
        launch_files: List[LaunchFile],
        repo_name: str = "ROS2",
        repo_url: str = "unavailable",
        commit_hash: str = "unavailable",
        branch: str = "unavailable",
        archsynth_version: str = "2.0",
        use_llm: bool = False,
        interfaces: Optional[List[InterfaceDeclaration]] = None,
        runtime_interfaces: Optional[List[RuntimeInterfaceInstance]] = None,
        communication_graph: Optional[CommunicationGraphModel] = None,
        communication_matrix: Optional[CommunicationMatrixModel] = None,
        subsystem_model: Optional[SubsystemModel] = None,
        lifecycle_graph: Optional[LifecycleGraphModel] = None,
        plugin_architecture: Optional[PluginArchitectureModel] = None,
        behavior_tree_model: Optional[BehaviorTreeCollectionModel] = None,
        architecture_views: Optional[ArchitectureViewsModel] = None,
        package_dependency_graph: Optional[Any] = None,
    ) -> ArchitectureModel:
        """
        Build full ArchitectureModel from nodes, launch files, and Phase 4 models.
        """
        logger.info(f"Constructing architecture model for {repo_name} ({len(nodes)} nodes, {len(launch_files)} launch files)")

        # 1. Preserve source-grounded nodes inventory without fabricating synthetic nodes
        all_nodes = list(nodes)

        # 2. Collect launch instances and containers from parsed launch files
        all_instances = []
        all_containers = []
        for lfile in launch_files:
            all_instances.extend(lfile.instances)
            all_containers.extend(lfile.containers)

        # 3. Build communication graph (connections)
        topic_conns = self._build_topic_connections(all_nodes)
        service_conns = self._build_service_connections(all_nodes)
        action_conns = self._build_action_connections(all_nodes, interfaces=interfaces or [])

        # 4. Subsystems
        if subsystem_model and subsystem_model.subsystems:
            subsystems = subsystem_model.subsystems
        else:
            subsystems = self._synthesize_subsystems(all_nodes, launch_files, use_llm=use_llm)

        # 5. Generate Mermaid Diagram syntax
        if architecture_views and "subsystem_component" in architecture_views.views:
            mermaid_syntax = architecture_views.views["subsystem_component"].mermaid_diagram
        else:
            mermaid_syntax = self._generate_mermaid_diagram(all_nodes, subsystems, topic_conns)

        unresolved_launch = [
            {"launch_file": lf.file_path, "expression": expr}
            for lf in launch_files
            for expr in getattr(lf, "unresolved_expressions", [])
        ]

        # 6. Create ArchitectureModel
        model = ArchitectureModel(
            repo_name=repo_name,
            repo_url=repo_url,
            commit_hash=commit_hash,
            branch=branch,
            archsynth_version=archsynth_version,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            nodes=all_nodes,
            launch_files=launch_files,
            launch_instances=all_instances,
            launch_containers=all_containers,
            subsystems=subsystems,
            topic_connections=topic_conns,
            service_connections=service_conns,
            action_connections=action_conns,
            mermaid_diagram=mermaid_syntax,
            interfaces=interfaces or [],
            runtime_interfaces=runtime_interfaces or [],
            communication_graph=communication_graph,
            communication_matrix=communication_matrix,
            subsystem_model=subsystem_model,
            lifecycle_graph=lifecycle_graph,
            plugin_architecture=plugin_architecture,
            behavior_tree_model=behavior_tree_model,
            architecture_views=architecture_views,
            package_dependency_graph=package_dependency_graph,
            unresolved_launch_constructs=unresolved_launch,
        )

        # Build structured node inventory and run architecture consistency validation
        from src.architecture_validator import (
            build_structured_node_inventory,
            validate_architecture_consistency,
        )
        model.structured_node_inventory = build_structured_node_inventory(model)
        model.architecture_validation = validate_architecture_consistency(model)

        model.compute_stats()
        return model

    def _enrich_nodes_from_launches(self, existing_nodes: List[ROS2Node], launch_files: List[LaunchFile]) -> List[ROS2Node]:
        """
        Deprecated in Phase 2: Preserves source-grounded node inventory without synthetic node fabrication.
        Runtime launch instances are tracked separately in LaunchInstance.
        """
        return list(existing_nodes)

    def _build_topic_connections(self, nodes: List[ROS2Node]) -> List[Dict[str, Any]]:
        """Match publishers to subscribers across nodes"""
        pub_map: Dict[str, Set[str]] = {}
        sub_map: Dict[str, Set[str]] = {}

        for node in nodes:
            node_id = node.name or node.fully_qualified_name
            for pub in node.publishers:
                if pub.name:
                    pub_map.setdefault(pub.name, set()).add(node_id)
            for sub in node.subscribers:
                if sub.name:
                    sub_map.setdefault(sub.name, set()).add(node_id)

        all_topics = set(pub_map.keys()).union(set(sub_map.keys()))
        connections = []

        for topic in sorted(all_topics):
            publishers = sorted(list(pub_map.get(topic, [])))
            subscribers = sorted(list(sub_map.get(topic, [])))
            connections.append({
                "topic": topic,
                "publishers": publishers,
                "subscribers": subscribers
            })

        return connections

    def _build_service_connections(self, nodes: List[ROS2Node]) -> List[Dict[str, Any]]:
        """Match service servers to clients across nodes"""
        servers: Dict[str, Set[str]] = {}
        clients: Dict[str, Set[str]] = {}

        for node in nodes:
            node_id = node.name or node.fully_qualified_name
            for srv in node.services:
                if srv.name:
                    if srv.role == 'server':
                        servers.setdefault(srv.name, set()).add(node_id)
                    else:
                        clients.setdefault(srv.name, set()).add(node_id)

        all_srvs = set(servers.keys()).union(set(clients.keys()))
        connections = []

        for srv in sorted(all_srvs):
            connections.append({
                "service": srv,
                "servers": sorted(list(servers.get(srv, []))),
                "clients": sorted(list(clients.get(srv, [])))
            })

        return connections

    def _build_action_connections(self, nodes: List[ROS2Node], interfaces: Optional[List[InterfaceDeclaration]] = None) -> List[Dict[str, Any]]:
        """Match action servers to clients across nodes and config-declared action interfaces."""
        servers: Dict[str, Set[str]] = {}
        clients: Dict[str, Set[str]] = {}

        for node in nodes:
            node_id = node.name or node.fully_qualified_name
            for act in node.actions:
                if act.name:
                    if act.role == 'server':
                        servers.setdefault(act.name, set()).add(node_id)
                    else:
                        clients.setdefault(act.name, set()).add(node_id)

        from src.schema import CommunicationType
        for decl in (interfaces or []):
            if decl.interface_type == CommunicationType.ACTION_SERVER and decl.name_expression:
                servers.setdefault(decl.name_expression, set()).add(decl.owner_node_id)
            elif decl.interface_type == CommunicationType.ACTION_CLIENT and decl.name_expression:
                clients.setdefault(decl.name_expression, set()).add(decl.owner_node_id)

        all_acts = set(servers.keys()).union(set(clients.keys()))
        connections = []

        for act in sorted(all_acts):
            connections.append({
                "action": act,
                "servers": sorted(list(servers.get(act, []))),
                "clients": sorted(list(clients.get(act, [])))
            })

        return connections

    def _synthesize_subsystems(self, nodes: List[ROS2Node], launch_files: List[LaunchFile], use_llm: bool = False) -> List[Subsystem]:
        """
        Group nodes and launch files into logical subsystems using LLM or deterministic fallback.
        """
        # Package-based fallback grouping
        pkg_groups: Dict[str, List[str]] = {}
        pkg_launches: Dict[str, List[str]] = {}

        for node in nodes:
            pkg = node.package_name or "default"
            pkg_groups.setdefault(pkg, []).append(node.name or node.fully_qualified_name)

        for lfile in launch_files:
            pkg = lfile.package_name or "default"
            pkg_launches.setdefault(pkg, []).append(lfile.file_path)

        subsystems = []
        for pkg, node_names in pkg_groups.items():
            subsystems.append(Subsystem(
                name=pkg,
                description=f"Subsystem containing nodes and components from {pkg}",
                nodes=node_names,
                launch_files=pkg_launches.get(pkg, [])
            ))

        if not use_llm:
            return subsystems

        # Try LLM refinement if requested
        try:
            prompt_context = self._prepare_llm_summary(nodes, launch_files)
            prompt = (
                f"Analyze the following ROS2 nodes and launch files from the '{nodes[0].package_name if nodes else 'ROS2'}' software repository.\n"
                "Group them into 3 to 6 logical functional subsystems based on their component responsibilities.\n"
                "Return a JSON list of subsystem objects matching schema: name, description, nodes (array of node names).\n\n"
                f"{prompt_context}"
            )
            response_text = self.llm_client.generate_text(prompt)
            if response_text and "{" in response_text:
                # Basic json extract if LLM response is returned
                json_start = response_text.find("[")
                json_end = response_text.rfind("]") + 1
                if json_start != -1 and json_end > json_start:
                    raw_subsystems = json.loads(response_text[json_start:json_end])
                    llm_subsystems = []
                    for raw_sub in raw_subsystems:
                        if isinstance(raw_sub, dict) and "name" in raw_sub:
                            llm_subsystems.append(Subsystem(
                                name=raw_sub.get("name", ""),
                                description=raw_sub.get("description", ""),
                                nodes=raw_sub.get("nodes", []),
                                launch_files=pkg_launches.get(raw_sub.get("name", ""), [])
                            ))
                    if llm_subsystems:
                        return llm_subsystems
        except Exception as e:
            logger.warning(f"LLM subsystem synthesis fallback used due to: {e}")

        return subsystems

    def _prepare_llm_summary(self, nodes: List[ROS2Node], launch_files: List[LaunchFile]) -> str:
        """Create token-efficient summary for LLM context"""
        lines = ["Nodes:"]
        for n in nodes[:25]:
            lines.append(f"- {n.name} (Pkg: {n.package_name}, Class: {n.class_name})")

        lines.append("\nLaunch Files:")
        for lf in launch_files[:15]:
            lines.append(f"- {Path(lf.file_path).name} (Pkg: {lf.package_name}, Nodes: {len(lf.nodes)})")

        return "\n".join(lines)

    def _generate_mermaid_diagram(
        self,
        nodes: List[ROS2Node],
        subsystems: List[Subsystem],
        topic_conns: List[Dict[str, Any]]
    ) -> str:
        """Generate valid Mermaid graph TD syntax"""
        lines = ["graph TD"]

        # Subgraphs per subsystem
        for idx, sub in enumerate(subsystems):
            sub_id = f"sub_{idx}"
            clean_name = sub.name.replace("-", "_").replace(" ", "_")
            lines.append(f"    subgraph {sub_id} [\"{sub.name}\"]")

            for node_name in sub.nodes:
                clean_node = node_name.replace("-", "_").replace("/", "_").replace(" ", "_")
                if not clean_node:
                    continue
                lines.append(f"        {clean_node}[\"{node_name}\"]")

            lines.append("    end")

        # Communication edges (topics with publishers and subscribers)
        edge_count = 0
        for conn in topic_conns:
            topic = conn.get("topic", "")
            pubs = conn.get("publishers", [])
            subs = conn.get("subscribers", [])

            for pub in pubs:
                pub_clean = pub.replace("-", "_").replace("/", "_").replace(" ", "_")
                for sub_node in subs:
                    if pub == sub_node:
                        continue
                    sub_clean = sub_node.replace("-", "_").replace("/", "_").replace(" ", "_")
                    lines.append(f"    {pub_clean} -->|\"{topic}\"| {sub_clean}")
                    edge_count += 1
                    if edge_count > 30:  # Cap max edges for visual clarity
                        break
                if edge_count > 30:
                    break

        return "\n".join(lines)


def run_architecture_constructor(
    nodes_json_path: Path,
    launches_json_path: Path,
    output_path: Path,
    repo_name: str = "ROS2",
    repo_url: str = "unavailable",
    commit_hash: str = "unavailable",
    branch: str = "unavailable",
    archsynth_version: str = "2.0",
    use_llm: bool = True,
    package_dependency_graph: Optional[Any] = None,
) -> ArchitectureModel:
    """Run Stage 4 on nodes and launch files JSON output, incorporating Phase 3 outputs if present"""
    with open(nodes_json_path, "r", encoding="utf-8") as f:
        nodes_data = json.load(f)
        nodes = [ROS2Node.model_validate(n) for n in nodes_data]

    with open(launches_json_path, "r", encoding="utf-8") as f:
        launches_data = json.load(f)
        launch_files = [LaunchFile.model_validate(l) for l in launches_data]

    interfaces = None
    runtime_interfaces = None
    communication_graph = None
    communication_matrix = None

    parent_dir = output_path.parent
    expected_identity = RepositoryIdentity(
        repo_name=repo_name,
        repo_root=str(parent_dir),
        remote_url=repo_url,
        commit_sha=commit_hash,
        branch=branch,
    )

    # Validate and load intermediate artifacts with repository provenance verification
    interfaces_path = parent_dir / "interfaces.json"
    interfaces_data = load_validated_json(interfaces_path, expected_identity, purge_invalid=True)
    if interfaces_data is not None:
        try:
            interfaces = [InterfaceDeclaration.model_validate(d) for d in interfaces_data]
        except Exception as e:
            logger.warning(f"Could not validate interfaces.json: {e}")

    runtime_path = parent_dir / "runtime_interfaces.json"
    runtime_data = load_validated_json(runtime_path, expected_identity, purge_invalid=True)
    if runtime_data is not None:
        try:
            runtime_interfaces = [RuntimeInterfaceInstance.model_validate(r) for r in runtime_data]
        except Exception as e:
            logger.warning(f"Could not validate runtime_interfaces.json: {e}")

    graph_path = parent_dir / "communication_graph.json"
    graph_data = load_validated_json(graph_path, expected_identity, purge_invalid=True)
    if graph_data is not None:
        try:
            communication_graph = CommunicationGraphModel.model_validate(graph_data)
        except Exception as e:
            logger.warning(f"Could not validate communication_graph.json: {e}")

    matrix_path = parent_dir / "communication_matrix.json"
    matrix_data = load_validated_json(matrix_path, expected_identity, purge_invalid=True)
    if matrix_data is not None:
        try:
            communication_matrix = CommunicationMatrixModel.model_validate(matrix_data)
        except Exception as e:
            logger.warning(f"Could not validate communication_matrix.json: {e}")

    subsystem_model = None
    subsystem_path = parent_dir / "subsystem_model.json"
    subsystem_data = load_validated_json(subsystem_path, expected_identity, purge_invalid=True)
    if subsystem_data is not None:
        try:
            subsystem_model = SubsystemModel.model_validate(subsystem_data)
        except Exception as e:
            logger.warning(f"Could not validate subsystem_model.json: {e}")

    lifecycle_graph = None
    lifecycle_path = parent_dir / "lifecycle_graph.json"
    lifecycle_data = load_validated_json(lifecycle_path, expected_identity, purge_invalid=True)
    if lifecycle_data is not None:
        try:
            lifecycle_graph = LifecycleGraphModel.model_validate(lifecycle_data)
        except Exception as e:
            logger.warning(f"Could not validate lifecycle_graph.json: {e}")

    plugin_architecture = None
    plugin_path = parent_dir / "plugin_architecture.json"
    plugin_data = load_validated_json(plugin_path, expected_identity, purge_invalid=True)
    if plugin_data is not None:
        try:
            plugin_architecture = PluginArchitectureModel.model_validate(plugin_data)
        except Exception as e:
            logger.warning(f"Could not validate plugin_architecture.json: {e}")

    behavior_tree_model = None
    bt_path = parent_dir / "behavior_tree_model.json"
    bt_data = load_validated_json(bt_path, expected_identity, purge_invalid=True)
    if bt_data is not None:
        try:
            behavior_tree_model = BehaviorTreeCollectionModel.model_validate(bt_data)
            if behavior_tree_model.total_trees == 0:
                behavior_tree_model = None
        except Exception as e:
            logger.warning(f"Could not validate behavior_tree_model.json: {e}")

    architecture_views = None
    views_path = parent_dir / "architecture_views.json"
    views_data = load_validated_json(views_path, expected_identity, purge_invalid=True)
    if views_data is not None:
        try:
            architecture_views = ArchitectureViewsModel.model_validate(views_data)
        except Exception as e:
            logger.warning(f"Could not validate architecture_views.json: {e}")

    constructor = ArchitectureConstructor()
    model = constructor.construct(
        nodes,
        launch_files,
        repo_name=repo_name,
        repo_url=repo_url,
        commit_hash=commit_hash,
        branch=branch,
        archsynth_version=archsynth_version,
        use_llm=use_llm,
        interfaces=interfaces,
        runtime_interfaces=runtime_interfaces,
        communication_graph=communication_graph,
        communication_matrix=communication_matrix,
        subsystem_model=subsystem_model,
        lifecycle_graph=lifecycle_graph,
        plugin_architecture=plugin_architecture,
        behavior_tree_model=behavior_tree_model,
        architecture_views=architecture_views,
        package_dependency_graph=package_dependency_graph,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(model.model_dump(), f, indent=2)

    attach_artifact_provenance(output_path, expected_identity)

    logger.info(f"Architecture model saved to {output_path}")
    return model


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    nodes_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output/nav2_nodes.json")
    launches_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output/nav2_launches.json")
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("output/nav2_architecture.json")

    arch_model = run_architecture_constructor(nodes_path, launches_path, out_path)
    print(f"\nArchitecture Model Constructed successfully:")
    print(f"  - Total Nodes: {arch_model.stats.get('total_nodes')}")
    print(f"  - Total Launch Files: {arch_model.stats.get('total_launch_files')}")
    print(f"  - Subsystems: {arch_model.stats.get('total_subsystems')}")
    print(f"  - Mermaid Diagram:\n{arch_model.mermaid_diagram[:300]}...")
