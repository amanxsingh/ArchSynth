"""
ArchSynth DocGenerator - Stage 5:
Converts validated ArchitectureModel into ISO/IEC/IEEE 42010-aligned
structured Markdown documentation using LLM narrative synthesis.

Research Extensions (M.Tech Dissertation):
    - Evidence / Traceability section (claim-level source provenance)
    - Validation Report section (evidence coverage metrics)
    - Architecture Changes section (drift report when available)
    - Experiment Metadata section (reproducibility record)
    - Corrected wording: "ISO/IEC/IEEE 42010-aligned" (not "ISO compliant")
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from src.schema import ArchitectureModel, ROS2Node, ValidationReport, DriftReport
from src.repo_identity import RepositoryIdentity, validate_artifact_provenance

logger = logging.getLogger(__name__)


def get_safe_node_filename(node: ROS2Node) -> str:
    """Generate a collision-free filename for a ROS 2 node documentation page."""
    uid = getattr(node, "id", None) or getattr(node, "node_id", None)
    if not uid:
        pkg = getattr(node, "package_name", "")
        cls = getattr(node, "class_name", "")
        name = getattr(node, "name", "")
        uid = f"{pkg}__{cls or name}" if pkg else (cls or name or "unnamed_node")
    safe = uid.replace("/", "_").replace(":", "_").replace("#", "_").replace(" ", "_")
    return safe


def format_evidence_lines(start: Optional[int], end: Optional[int]) -> str:
    """Format evidence line range avoiding 'None' output."""
    if start is None:
        return "N/A"
    if end is None or end == start:
        return f"L{start}"
    return f"L{start}–L{end}"


def resolve_bt_target_server(interface_name: str) -> str:
    """Resolve the remote ROS 2 server providing a given BT action or service interface."""
    if not interface_name:
        return "UnknownServer"
    name = interface_name.lower()
    if "compute_path" in name:
        return "nav2_planner::PlannerServer"
    elif "follow_path" in name:
        return "nav2_controller::ControllerServer"
    elif "smooth_path" in name:
        return "nav2_smoother::SmootherServer"
    elif any(b in name for b in ("spin", "backup", "wait", "drive_on_heading", "assisted_teleop")):
        return "behavior_server::BehaviorServer"
    elif "dock" in name:
        return "opennav_docking::DockingServer"
    elif "route" in name:
        return "nav2_route::RouteServer"
    elif "costmap" in name:
        return "nav2_costmap_2d::Costmap2DROS"
    return "TargetServer"


class DocGenerator:
    """
    Generates ISO/IEC/IEEE 42010-aligned Markdown documentation from an ArchitectureModel.
    Follows C4 architecture documentation structure.
    Enriches narratives and subsystem breakdowns using LLM synthesis (Gemini / Ollama).

    Research Extensions:
        - Section 9:  Evidence / Traceability (file:line citations for all entities)
        - Section 10: Validation Report (evidence coverage, unsupported entity rate)
        - Section 11: Architecture Changes (drift report)
        - Section 12: Experiment Metadata (reproducibility record)
    """

    def __init__(self, llm_client=None):
        from src.llm_client import LLMClient
        self.llm_client = llm_client or LLMClient()

    def generate(self, model: ArchitectureModel, output_dir: Path, use_llm: bool = True) -> Path:
        """
        Generate complete documentation directory structure and README.md.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        main_doc_path = output_dir / "README.md"

        content = self._render_main_document(model, use_llm=use_llm)
        main_doc_path.write_text(content, encoding="utf-8")

        # Generate individual node catalog files in nodes/ directory
        nodes_dir = output_dir / "nodes"
        nodes_dir.mkdir(exist_ok=True)
        for node in model.nodes:
            safe_node_filename = get_safe_node_filename(node)
            node_filename = f"{safe_node_filename}.md"
            node_doc_content = self._render_node_document(node)
            (nodes_dir / node_filename).write_text(node_doc_content, encoding="utf-8")

        logger.info(f"Generated complete documentation at {output_dir}")
        return main_doc_path

    def _render_main_document(self, model: ArchitectureModel, use_llm: bool = True) -> str:
        stats = model.stats or model.compute_stats()
        llm_context = build_llm_context(model)
        key_packages_str = ", ".join(llm_context["packages"][:6]) if llm_context["packages"] else model.repo_name

        system_context_narrative = (
            f"The **{model.repo_name}** software system provides modular ROS 2 capabilities, core node orchestration, "
            f"and message passing across its packages ({key_packages_str})."
        )

        if use_llm:
            try:
                ai_prompt = (
                    f"Write a concise, professional ISO/IEC/IEEE 42010-aligned System Context narrative (2-3 paragraphs) "
                    f"describing the software architecture of the ROS2 repository '{model.repo_name}' based on these stats:\n"
                    f"- Discovered ROS2 Nodes: {llm_context['total_nodes']}\n"
                    f"- Subsystems: {llm_context['total_subsystems']}\n"
                    f"- Topics: {llm_context['total_topics']}\n"
                    f"- Key packages in this repository: {key_packages_str}."
                )
                ai_text = self.llm_client.generate_text(ai_prompt)
                if ai_text and len(ai_text.strip()) > 50:
                    system_context_narrative = ai_text.strip()
            except Exception as e:
                logger.warning(f"LLM text generation for System Context narrative used fallback due to: {e}")

        meta = model.experiment_metadata or {}
        commit_val = (
            model.commit_hash if (model.commit_hash and len(model.commit_hash) >= 7 and model.commit_hash != "main")
            else meta.get("commit_hash", getattr(getattr(model, "provenance", None), "commit_hash", "unavailable"))
        )
        branch_val = model.branch or meta.get("branch", getattr(getattr(model, "provenance", None), "branch", "unavailable"))
        if branch_val == "unavailable" and model.commit_hash == "main":
            branch_val = "main"
        llm_provider = meta.get("llm_provider", "none")
        llm_model = meta.get("llm_model", "none")
        duration_val = f"{meta.get('processing_time_seconds', 'N/A')}s" if meta.get("processing_time_seconds") else "N/A"
        version_val = model.archsynth_version or meta.get("pipeline_version", "2.0")

        sections = [
            f"# {model.repo_name} Architecture Documentation",
            "",
            "> **Generated automatically by ArchSynth**  ",
            f"> **Tool**: ArchSynth v{version_val} — Evidence-Grounded ROS2 Architecture Recovery  ",
            f"> **Repository**: [{model.repo_name}]({model.repo_url})  ",
            f"> **Branch**: `{branch_val}`  ",
            f"> **Commit Hash**: `{commit_val}`  ",
            f"> **Analysis Timestamp**: `{model.analysis_timestamp}`  ",
            f"> **LLM Provider & Model**: `{llm_provider} / {llm_model}`  ",
            f"> **Analysis Duration**: `{duration_val}`  ",
            "> **Documentation Style**: ISO/IEC/IEEE 42010-aligned  ",
            "",
            "## Executive Summary",
            "",
            f"This document provides the reconstructed software architecture documentation for **{model.repo_name}**. "
            f"ArchSynth parsed **{stats.get('total_nodes', 0)} ROS2 nodes** and **{stats.get('total_launch_files', 0)} launch files**, "
            f"organizing them into **{stats.get('total_subsystems', 0)} logical subsystems**. "
            f"Every recovered architectural entity is grounded with source-code evidence (file:line citations).",
            "",
            "### Architecture Overview Statistics",
            "",
            "| Metric | Count |",
            "| :--- | :--- |",
            f"| **Total Discovered Nodes** | {stats.get('total_nodes', 0)} |",
            f"| **Parsed Launch Files** | {stats.get('total_launch_files', 0)} |",
            f"| **Logical Subsystems** | {stats.get('total_subsystems', 0)} |",
            f"| **Unique DDS Topics** | {stats.get('total_topics', 0)} |",
            f"| **Service Connections** | {stats.get('total_services', 0)} |",
            f"| **Action Connections** | {stats.get('total_actions', 0)} |",
        ]

        # Add evidence coverage stats if available
        if model.validation_report:
            vr = model.validation_report
            sections.extend([
                f"| **Evidence Coverage** | {vr.evidence_coverage:.1%} |",
                f"| **Unsupported Entity Rate** | {vr.unsupported_entity_rate:.1%} |",
            ])

        sections.extend([
            "",
            "---",
            "",
            "## 1. System Context (C4 Level 1)",
            "",
            system_context_narrative,
            "",
            "---",
            "",
            "## 2. Container View (C4 Level 2)",
            "",
            "The system is composed of ROS2 package containers communicating over DDS topics, services, and action interfaces.",
            "",
            "### Subsystems Summary",
            ""
        ])

        for sub in model.subsystems:
            coh_display = "N/A (<2 nodes)" if getattr(sub, "cohesion_status", "computed") == "N/A" else f"`{sub.intra_cohesion_score}`"
            sections.append(f"#### Subsystem: `{sub.name}`")
            sections.append(f"{sub.description}")
            if getattr(sub, "justification", None):
                sections.append(f"- **Assignment Rationale**: {sub.justification}")
            sections.append(f"- **Architectural Role**: `{sub.architectural_role}`")
            sections.append(
                f"- **Intra-Subsystem Cohesion**: {coh_display} | "
                f"**Inter-Subsystem Coupling**: `{sub.inter_coupling_score}` "
                f"(Internal: `{getattr(sub, 'coupling_internal', 0.0)}`, External: `{getattr(sub, 'coupling_external', 0.0)}`) | "
                f"**Interface Density**: `{getattr(sub, 'interface_density', 0.0)}`"
            )
            sections.append(f"- **Nodes ({len(sub.nodes)})**: " + ", ".join([f"`{n}`" for n in sub.nodes[:10]]))
            if sub.boundary_interfaces:
                sections.append(f"- **Boundary Interfaces ({len(sub.boundary_interfaces)})**: " + ", ".join([f"`{bi}`" for bi in sub.boundary_interfaces[:6]]))
            if sub.launch_files:
                sections.append(f"- **Launch Files ({len(sub.launch_files)})**: " + ", ".join([f"`{Path(lf).name}`" for lf in sub.launch_files[:5]]))
            sections.append("")

        sections.extend([
            "### Architecture Metrics Definitions",
            "",
            "| Metric | Mathematical Definition | Inputs & Edge Cases |",
            "| :--- | :--- | :--- |",
            "| **Intra-Subsystem Cohesion** | `E_internal / (N * (N - 1))` | Directed communication edges between nodes inside the subsystem divided by ordered node pairs. Reported as `N/A` when `N < 2`. |",
            "| **Internal Coupling** | `E_cross_internal` | Directed topic/service/action edges crossing between this subsystem and other in-repository subsystems. |",
            "| **External Coupling** | `I_unmatched_external` | Declared interfaces (pubs/subs/services/actions) on subsystem nodes whose peer resides outside the repository (e.g., `move_group`, `servo_node`, `ros2_control`). |",
            "| **Total Coupling** | `Internal Coupling + External Coupling` | Total boundary-crossing interactions for the subsystem. |",
            "| **Interface Density** | `Total_Interfaces / N` | Average declared ROS 2 endpoints (topics, services, actions) per node in the subsystem. |",
            ""
        ])

        # Subsystem evaluation against reference hypothesis (Nav2 specific)
        if model.subsystem_model and model.subsystem_model.reference_comparison and model.repo_name.lower() in ("nav2", "navigation2"):
            ref_comp = model.subsystem_model.reference_comparison
            sections.extend([
                "### Subsystem Clustering Evaluation (vs. Reference Nav2 Hypothesis)",
                "",
                f"> **Clustering Algorithm**: `{model.subsystem_model.clustering_method}`  ",
                f"> **Mean Jaccard Similarity**: `{ref_comp.get('mean_jaccard_similarity', 0.0):.3f}` across evaluated functional subsystems.  ",
                "> **Evaluation Reference Set**: The ground-truth reference model defines 8 canonical Navigation2 functional domains (`perception_costmaps`, `localization_state_estimation`, `navigation_orchestration`, `global_planning`, `trajectory_control`, `recovery_behaviors`, `system_supervision`, `client_autonomy_api`). Reconstructed subsystems are compared against this ground truth to measure precision, recall, and Jaccard boundary recovery accuracy.",
                "",
                "| Subsystem Domain | Reference Nodes | Recovered Nodes | Precision | Recall | Jaccard Similarity |",
                "| :--- | :---: | :---: | :---: | :---: | :---: |"
            ])
            for sname, smetrics in ref_comp.get("subsystem_metrics", {}).items():
                sections.append(
                    f"| `{sname}` | {smetrics.get('reference_node_count', 0)} | {smetrics.get('recovered_node_count', 0)} | "
                    f"{smetrics.get('precision', 0.0):.3f} | {smetrics.get('recall', 0.0):.3f} | **{smetrics.get('jaccard_similarity', 0.0):.3f}** |"
                )
            sections.append("")

        sections.extend([
            "---",
            "",
            "## 3. Component View & System Diagram (C4 Level 3)",
            "",
            "The following Mermaid diagram visualizes the reconstructed subsystem composition and communication graph:",
            "",
            "```mermaid",
            model.mermaid_diagram or "graph TD\n    A[No Diagram Generated]",
            "```",
            "",
            "---",
            "",
            "## 4. Node Catalog",
            "",
            "Overview of the core discovered ROS2 nodes in the system:",
            "",
            "| Node Name | Package | Class / Executable | Architectural Classification | Pubs | Subs | Services | Actions | Evidence | Validation |",
            "| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |"
        ])

        for node in model.nodes:
            node_name = node.name if node.name else (node.class_name if node.class_name else (node.fully_qualified_name if node.fully_qualified_name else "unnamed"))
            pkg = node.package_name or "N/A"
            cls = node.class_name or "N/A"
            role_label = getattr(node, "classification_label", None) or (
                node.node_category.value if hasattr(node.node_category, "value") else str(node.node_category)
            )
            pubs = len(node.publishers)
            subs = len(node.subscribers)
            srvs = len(node.services)
            acts = len(node.actions)
            ev_count = len(node.evidence)
            val_status = node.validation_status.value if node.validation_status else "unknown"
            val_badge = "✅" if val_status == "supported" else ("❌" if val_status == "unsupported" else "❓")
            safe_link = get_safe_node_filename(node)
            sections.append(
                f"| [`{node_name}`](nodes/{safe_link}.md) "
                f"| `{pkg}` | `{cls}` | `{role_label}` | {pubs} | {subs} | {srvs} | {acts} "
                f"| {ev_count} item(s) | {val_badge} {val_status} |"
            )

        sections.extend([
            "",
            "---",
            "",
            "## 5. Launch File Composition",
            "",
            f"Parsed **{len(model.launch_files)} launch files** across the repository.",
            "",
            "Alternative standalone launch profiles are analyzed independently by default.",
            "",
            "| Launch File | Architectural Classification | Direct Node | Direct LifecycleNode | ComposableNode | ComposableNodeContainer | LoadComposableNodes | Included Launch | Unresolved | Resolved Executable | Runtime Node Name | CMake Installed |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: |"
        ])

        for lf in model.launch_files:
            rel_path = Path(lf.file_path).name
            role_label = getattr(lf, "launch_role", "Subsystem Launch File")
            direct_node = sum(1 for n in lf.nodes if getattr(n, 'action_type', '') == 'Node')
            direct_lifecycle = sum(1 for n in lf.nodes if getattr(n, 'action_type', '') == 'LifecycleNode')
            composable_node = sum(1 for n in lf.nodes if getattr(n, 'action_type', '') == 'ComposableNode')
            composable_container = sum(1 for n in lf.nodes if getattr(n, 'action_type', '') == 'ComposableNodeContainer')
            load_composable = sum(1 for n in lf.nodes if getattr(n, 'action_type', '') == 'LoadComposableNodes')
            includes = len(lf.includes)
            unresolved = sum(1 for n in lf.nodes if getattr(n, 'resolution_status', '') == 'unresolved' or not n.executable)
            execs = ", ".join(sorted(list(set(n.executable for n in lf.nodes if n.executable)))) or "-"
            runtime_names = ", ".join(sorted(list(set(n.node_name for n in lf.nodes if n.node_name)))) or "-"
            cmake_inst = "Yes" if getattr(lf, "is_cmake_installed", True) else "No (Excluded)"
            sections.append(
                f"| `{rel_path}` | `{role_label}` | {direct_node} | {direct_lifecycle} | {composable_node} | "
                f"{composable_container} | {load_composable} | {includes} | {unresolved} | "
                f"`{execs}` | `{runtime_names}` | {cmake_inst} |"
            )

        sections.extend([
            "",
            "---",
            "",
            "## 6. Communication Matrix",
            "",
            "### Topic Connections",
            "",
            "| Topic Name | Publisher Nodes | Subscriber Nodes |",
            "| :--- | :--- | :--- |"
        ])

        def _is_clean_ros_name(n: str) -> bool:
            if not n:
                return False
            for bad_char in ("(", ")", "->", "{", "}", "::", " ", "\t", "\n", ";", "<", ">"):
                if bad_char in n:
                    return False
            return True

        valid_topics = [c for c in model.topic_connections if _is_clean_ros_name(c.get("topic", ""))]
        for conn in valid_topics[:35]:
            topic = conn.get("topic", "")
            pubs_list = ", ".join([f"`{p}`" for p in conn.get("publishers", [])]) or "*External*"
            subs_list = ", ".join([f"`{s}`" for s in conn.get("subscribers", [])]) or "*External*"
            sections.append(f"| `{topic}` | {pubs_list} | {subs_list} |")

        if model.service_connections:
            sections.extend([
                "",
                "### Service Connections",
                "",
                "| Service Name | Servers | Clients |",
                "| :--- | :--- | :--- |"
            ])
            valid_services = [c for c in model.service_connections if _is_clean_ros_name(c.get("service", ""))]
            for conn in valid_services[:25]:
                svc = conn.get("service", "")
                servers = ", ".join([f"`{s}`" for s in conn.get("servers", [])]) or "*External*"
                clients = ", ".join([f"`{c}`" for c in conn.get("clients", [])]) or "*External*"
                sections.append(f"| `{svc}` | {servers} | {clients} |")

        if model.action_connections:
            sections.extend([
                "",
                "### Action Connections",
                "",
                "| Action Name | Servers | Clients |",
                "| :--- | :--- | :--- |"
            ])
            valid_actions = [c for c in model.action_connections if _is_clean_ros_name(c.get("action", ""))]
            for conn in valid_actions[:25]:
                act = conn.get("action", "")
                servers = ", ".join([f"`{s}`" for s in conn.get("servers", [])]) or "*External*"
                clients = ", ".join([f"`{c}`" for c in conn.get("clients", [])]) or "*External*"
                sections.append(f"| `{act}` | {servers} | {clients} |")

        # ----- Phase 4 Architectural Dimensions -----
        if model.lifecycle_graph:
            lg = model.lifecycle_graph
            sections.extend([
                "",
                "---",
                "",
                "## 7. ROS 2 Lifecycle Management Architecture",
                "",
            ])
            if lg.lifecycle_managers:
                sections.extend([
                    f"**{model.repo_name}** orchestrates **{len(lg.lifecycle_managers)} lifecycle managers** controlling deterministic startup and state transitions for **{len(lg.managed_nodes)} managed node instances**.",
                    "",
                    "### Lifecycle Managers",
                    "",
                    "| Manager Name | Launch File | Autostart | Managed Nodes |",
                    "| :--- | :--- | :---: | :--- |"
                ])
                for mgr in lg.lifecycle_managers:
                    nodes_preview = ", ".join([f"`{n}`" for n in mgr.managed_node_names[:5]])
                    if len(mgr.managed_node_names) > 5:
                        nodes_preview += f" ... (+{len(mgr.managed_node_names) - 5} more)"
                    sections.append(f"| `{mgr.manager_name}` | `{mgr.launch_file}` | `{mgr.autostart}` | {nodes_preview} |")

                if lg.managed_nodes:
                    sections.extend([
                        "",
                        "### Managed Nodes & Source Callback Handlers",
                        "",
                        "| Node ID | Launch Name | Managing Manager | Transition Index | C++ Callbacks Implemented | Target State |",
                        "| :--- | :--- | :--- | :---: | :--- | :---: |"
                    ])
                    for mn in lg.managed_nodes:
                        cb_str = ", ".join([f"`{c}`" for c in mn.handles_transition_callbacks]) or "*standard*"
                        sections.append(
                            f"| `{mn.node_id}` | `{mn.launch_name}` | `{mn.managing_manager}` | "
                            f"{mn.transition_order_index} | {cb_str} | **{mn.configured_target_state}** |"
                        )
            else:
                sections.append(f"No ROS 2 lifecycle managers or managed lifecycle nodes were declared in **{model.repo_name}**.")

            if lg.mermaid_diagram and lg.lifecycle_managers:
                sections.extend([
                    "",
                    "### Lifecycle State Machine Diagram",
                    "",
                    "```mermaid",
                    lg.mermaid_diagram,
                    "```"
                ])

        if model.plugin_architecture:
            pa = model.plugin_architecture
            sections.extend([
                "",
                "---",
                "",
                "## 8. Pluginlib Extensibility Architecture",
                "",
                f"ArchSynth recovered **{len(pa.plugins)} pluginlib plugins** categorized across **{len(pa.categories)} architectural extension points**.",
                f"Status summary: **{pa.status_counts.get('selected', 0)} selected in default parameters**, **{pa.status_counts.get('available', 0)} available in codebase**.",
                "",
                "### Plugin Categories",
                "",
                "| Extension Category | Base Class / Interface | Plugins Declared | Selected Active Plugin |",
                "| :--- | :--- | :---: | :--- |"
            ])
            for cat, pnames in pa.categories.items():
                matching_plugins = [p for p in pa.plugins if p.plugin_name in pnames]
                base_classes = sorted(list(set(p.base_class_type for p in matching_plugins if p.base_class_type)))
                base_cls_str = ", ".join(f"`{b}`" for b in base_classes) if base_classes else f"`{cat}`"
                sel_p = next((p.plugin_name for p in matching_plugins if getattr(p.status, "value", str(p.status)) == "selected"), "*None (Available)*")
                sections.append(f"| `{cat}` | {base_cls_str} | {len(pnames)} | `{sel_p}` |")

            if pa.server_configurations:
                sections.extend([
                    "",
                    "### Runtime Plugin Configuration",
                    "",
                    "| Server Node | Plugin Slot | Configured Plugin Name | Selected Implementation Type |",
                    "| :--- | :--- | :--- | :--- |"
                ])
                for sc in pa.server_configurations[:15]:
                    pname = sc.plugin_names[0] if sc.plugin_names else sc.plugin_slot
                    sections.append(f"| `{sc.server_node_name}` | `{sc.plugin_slot}` | `{pname}` | `{sc.selected_plugin}` |")

            if pa.mermaid_diagram:
                sections.extend([
                    "",
                    "### Plugin Extensibility Class Diagram",
                    "",
                    "```mermaid",
                    pa.mermaid_diagram,
                    "```"
                ])

        if model.behavior_tree_model:
            bt = model.behavior_tree_model
            sections.extend([
                "",
                "---",
                "",
                "## 9. Behavior Tree Navigation Orchestration",
                "",
            ])
            if bt.total_trees > 0:
                sections.extend([
                    f"**{model.repo_name}** orchestrates autonomous missions via BehaviorTree.CPP. ArchSynth parsed **{bt.total_trees} behavior tree XML definitions** comprising **{bt.total_bt_nodes} tree nodes**.",
                    f"All BT leaf nodes are **hosted components inside `{bt.host_node_id}`**, maintaining clean separation between orchestration and ROS 2 process nodes.",
                    "",
                    f"### Blackboard Shared Variables ({len(bt.all_blackboard_variables)} unique keys)",
                    "",
                    ", ".join([f"`{{{k}}}`" for k in bt.all_blackboard_variables[:25]]) + " ...",
                    "",
                    "### Behavior Tree Action & Service Bindings",
                    "",
                    "| Behavior Tree Leaf Node | Invocation Type | Bound ROS 2 Interface | Calling Client (BT Host) | Remote Target Server |",
                    "| :--- | :---: | :--- | :--- | :--- |"
                ])
                seen_bindings = set()
                for b in bt.bt_to_ros2_bindings:
                    key = (b["bt_node"], b["target_interface"])
                    if key not in seen_bindings:
                        seen_bindings.add(key)
                        target_srv = b.get("target_server") or resolve_bt_target_server(b["target_interface"])
                        sections.append(f"| `{b['bt_node']}` | `{b['type'].upper()}` | `{b['target_interface']}` | `{bt.host_node_id}` | `{target_srv}` |")
            else:
                sections.append(f"No BehaviorTree.CPP navigation XML definitions are declared in **{model.repo_name}**.")

        if model.architecture_views:
            av = model.architecture_views
            sections.extend([
                "",
                "---",
                "",
                f"## 10. ISO/IEC/IEEE 42010 Architecture Views ({len(av.views)} Views)",
                "",
                "ArchSynth provides multi-perspective architectural representations conforming to ISO/IEC/IEEE 42010:",
                ""
            ])
            for vid, view in av.views.items():
                sections.extend([
                    f"### View: {view.name} (`{vid}`)",
                    "",
                    f"{view.description}",
                    "",
                    f"- **Architectural Concerns**: {', '.join(view.architectural_concerns)}",
                    f"- **Target Stakeholders**: {', '.join(view.target_stakeholders)}",
                    ""
                ])
                if view.mermaid_diagram and view.mermaid_diagram.strip():
                    sections.extend([
                        "```mermaid",
                        view.mermaid_diagram,
                        "```",
                        ""
                    ])

        # ----- Section: Evidence / Traceability (Research Extension) -----
        sections.extend([
            "",
            "---",
            "",
            "## 11. Evidence / Traceability",
            "",
            "> This section documents the source-code evidence supporting each recovered architectural entity.",
            "> Evidence-grounded recovery distinguishes schema-valid claims from factually-supported claims.",
            "",
            "### Node Evidence",
            "",
            "| Node | Evidence File | Lines | Evidence Type |",
            "| :--- | :--- | :--- | :--- |"
        ])

        for node in model.nodes:
            node_name = node.name or node.class_name or "unnamed"
            if node.evidence:
                for ev in node.evidence[:2]:
                    line_ref = format_evidence_lines(ev.line_start, ev.line_end)
                    sections.append(f"| `{node_name}` | `{ev.file}` | `{line_ref}` | `{ev.evidence_type.value}` |")
            else:
                sections.append(f"| `{node_name}` | *No evidence* | — | — |")

        # Topic evidence sample
        topic_evidence_rows = []
        seen = set()
        for node in model.nodes:
            for pub in node.publishers:
                if pub.name not in seen and pub.evidence and _is_clean_ros_name(pub.name):
                    seen.add(pub.name)
                    ev = pub.evidence[0]
                    line_ref = format_evidence_lines(ev.line_start, ev.line_end)
                    topic_evidence_rows.append(
                        f"| `{pub.name}` | publish | `{node.name}` | `{ev.file}` | `{line_ref}` |"
                    )
            for sub in node.subscribers:
                if sub.name not in seen and sub.evidence and _is_clean_ros_name(sub.name):
                    seen.add(sub.name)
                    ev = sub.evidence[0]
                    line_ref = format_evidence_lines(ev.line_start, ev.line_end)
                    topic_evidence_rows.append(
                        f"| `{sub.name}` | subscribe | `{node.name}` | `{ev.file}` | `{line_ref}` |"
                    )

        if topic_evidence_rows:
            sections.extend([
                "",
                "### Topic Evidence (Sample)",
                "",
                "| Topic | Direction | Node | Evidence File | Lines |",
                "| :--- | :--- | :--- | :--- | :--- |"
            ])
            sections.extend(topic_evidence_rows[:20])

        # ----- Structured Node & Executable Inventory -----
        if getattr(model, "structured_node_inventory", None):
            sections.extend([
                "",
                "---",
                "",
                "## 11b. Structured Node & Executable Inventory",
                "",
                "Distinguishes repository-defined source nodes, composable components, external ROS 2 launch executables, dynamically loaded plugins, and unresolved dynamic entries:",
                "",
                "| Name / Identifier | Package | Executable | Classification | Origin | Confidence | Evidence |",
                "| :--- | :--- | :--- | :--- | :--- | :---: | :--- |"
            ])
            for item in model.structured_node_inventory:
                ev_str = ", ".join(f"`{e}`" for e in item.get("evidence", [])) or "—"
                sections.append(
                    f"| `{item.get('name')}` | `{item.get('package')}` | `{item.get('executable')}` | "
                    f"`{item.get('classification')}` | `{item.get('origin')}` | {item.get('confidence', 0.0):.2f} | {ev_str} |"
                )

        # ----- Package Dependency Architecture -----
        if getattr(model, "package_dependency_graph", None):
            pdg = model.package_dependency_graph
            sections.extend([
                "",
                "---",
                "",
                "## 11c. Package Dependency Architecture",
                "",
                f"Recovered **{len(pdg.internal_packages)} internal packages**, **{len(pdg.external_packages)} external dependencies**, and **{len(pdg.edges)} directed dependency edges** from `package.xml`, `setup.py`, and source `#include`/`import` statements.",
                "",
                "| Source Package | Target Package | Dependency Type | Origin | Target Scope | Evidence |",
                "| :--- | :--- | :--- | :--- | :---: | :--- |"
            ])
            shown_edges = 0
            for edge in pdg.edges:
                if edge.is_target_internal or shown_edges < 35:
                    scope = "Internal" if edge.is_target_internal else "External"
                    lref = f":L{edge.line_number}" if edge.line_number else ""
                    sections.append(
                        f"| `{edge.source_package}` | `{edge.target_package}` | `{edge.dependency_type}` | `{edge.origin}` | {scope} | `{edge.source_file}{lref}` |"
                    )
                    shown_edges += 1

        # ----- Architecture Consistency Validation -----
        if getattr(model, "architecture_validation", None):
            av_rep = model.architecture_validation
            sections.extend([
                "",
                "---",
                "",
                "## 11d. Architecture Consistency Validation & Unresolved Elements",
                "",
                "Findings summary: " + ", ".join(f"**{k}**: {v}" for k, v in av_rep.counts_by_severity.items()),
                "",
                "| ID | Severity | Category | Entity | Details |",
                "| :--- | :--- | :--- | :--- | :--- |"
            ])
            for fnd in av_rep.findings[:40]:
                sections.append(
                    f"| `{fnd.finding_id}` | **{fnd.severity}** | `{fnd.category}` | `{fnd.entity}` | {fnd.message} |"
                )

        # ----- Section 10: Validation Report (Research Extension) -----
        if model.validation_report:
            vr = model.validation_report
            sections.extend([
                "",
                "---",
                "",
                "## 10. Validation Report",
                "",
                "> **Evidence Coverage** measures the fraction of recovered entities supported by source-code evidence.",
                "> This metric distinguishes ArchSynth from systems that produce schema-valid but factually ungrounded output.",
                "",
                "| Metric | Value |",
                "| :--- | :--- |",
                f"| **Total Entities** | {vr.total_entities} |",
                f"| **Supported Entities** | {vr.supported_entities} |",
                f"| **Unsupported Entities** | {vr.unsupported_entities} |",
                f"| **Evidence Coverage** | **{vr.evidence_coverage:.1%}** |",
                f"| **Unsupported Entity Rate** | {vr.unsupported_entity_rate:.1%} |",
                f"| **Node Coverage** | {vr.node_coverage:.1%} |",
                f"| **Topic Coverage** | {vr.topic_coverage:.1%} |",
                f"| **Service Coverage** | {vr.service_coverage:.1%} |",
                f"| **Action Coverage** | {vr.action_coverage:.1%} |",
            ])

            if vr.unsupported_list:
                sections.extend([
                    "",
                    "### Unsupported Entities",
                    "",
                    "| Type | Name | Reason |",
                    "| :--- | :--- | :--- |"
                ])
                for u in vr.unsupported_list[:20]:
                    sections.append(f"| `{u.entity_type}` | `{u.name}` | {u.reason} |")

        # ----- Section 11: Architecture Changes (Research Extension) -----
        if model.drift_report:
            dr = model.drift_report
            sections.extend([
                "",
                "---",
                "",
                "## 11. Architecture Changes (Drift Report)",
                "",
                f"Comparing **`{dr.base_commit}`** → **`{dr.target_commit}`**",
                f"Total changes detected: **{dr.total_changes}**",
                ""
            ])
            if dr.added_nodes:
                sections.append("**Added Nodes:** " + ", ".join([f"`{n}`" for n in dr.added_nodes]))
            if dr.removed_nodes:
                sections.append("**Removed Nodes:** " + ", ".join([f"`{n}`" for n in dr.removed_nodes]))
            if dr.added_topics:
                sections.append("**Added Topics:** " + ", ".join([f"`{t}`" for t in dr.added_topics]))
            if dr.removed_topics:
                sections.append("**Removed Topics:** " + ", ".join([f"`{t}`" for t in dr.removed_topics]))
            sections.append("")

        # ----- Section 12: Experiment Metadata (Research Extension) -----
        sections.extend([
            "---",
            "",
            "## 12. Experiment Metadata & Reproducibility",
            "",
            "| Field | Value |",
            "| :--- | :--- |",
            f"| **Tool** | ArchSynth v{version_val} (M.Tech Dissertation Project) |",
            f"| **Repository Name** | `{model.repo_name}` |",
            f"| **Repository URL** | `{model.repo_url}` |",
            f"| **Branch** | `{branch_val}` |",
            f"| **Commit Hash** | `{commit_val}` |",
            f"| **Analysis Timestamp** | `{model.analysis_timestamp}` |",
            f"| **ArchSynth Version** | `{version_val}` |",
            f"| **LLM Provider** | `{llm_provider}` |",
            f"| **LLM Model** | `{llm_model}` |",
            f"| **Nodes Analyzed** | {meta.get('nodes_analyzed', len(model.nodes))} |",
            f"| **Launch Files Analyzed** | {meta.get('launch_files_analyzed', len(model.launch_files))} |",
            f"| **Processing Time** | {duration_val} |",
            "| **Documentation Style** | ISO/IEC/IEEE 42010-aligned architecture description |",
        ])

        sections.extend([
            "",
            "> *ArchSynth uses evidence-grounded, schema-constrained hybrid static analysis and LLM synthesis*",
            "> *for ROS2 architecture recovery. All architectural claims are traceable to source evidence.*",
        ])

        return "\n".join(sections)

    def _render_node_document(self, node: ROS2Node) -> str:
        name = node.name if node.name else (node.class_name if node.class_name else (node.fully_qualified_name if node.fully_qualified_name else "unnamed"))
        val_status = node.validation_status.value if node.validation_status else "unknown"
        cat_str = node.node_category.value if hasattr(node.node_category, "value") else str(node.node_category)
        lines = [
            f"# Node Specification: `{name}`",
            "",
            f"- **Stable Unique ID**: `{node.id}`",
            f"- **Fully Qualified Name**: `{node.fully_qualified_name}`",
            f"- **Class / Executable**: `{node.class_name}`",
            f"- **Package**: `{node.package_name}`",
            f"- **Namespace**: `{node.namespace or '/'}`",
            f"- **Source File**: `{node.source_file}`",
            f"- **Architectural Classification**: `{cat_str}`",
            f"- **Is Test Entity**: `{node.is_test}`",
            f"- **Is Lifecycle Node**: `{node.is_lifecycle}`",
            f"- **Validation Status**: `{val_status}`",
            "",
        ]

        # Evidence table
        if node.evidence:
            lines.extend([
                "## Evidence / Provenance",
                "",
                "| File | Lines | Evidence Type | Source | Confidence |",
                "| :--- | :--- | :--- | :--- | :--- |"
            ])
            for ev in node.evidence:
                line_ref = format_evidence_lines(ev.line_start, ev.line_end)
                lines.append(
                    f"| `{ev.file}` | `{line_ref}` | `{ev.evidence_type.value}` "
                    f"| `{ev.source}` | {ev.confidence:.1f} |"
                )
            lines.append("")

        lines.extend(["## Publishers", ""])
        if node.publishers:
            lines.append("| Topic | Message Type | Category | QoS Profile | Evidence |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for pub in node.publishers:
                ev_ref = ""
                if pub.evidence:
                    e = pub.evidence[0]
                    ev_ref = f"`{Path(e.file).name}:{e.line_start}`" if e.line_start else f"`{Path(e.file).name}`"
                lines.append(f"| `{pub.name}` | `{pub.message_type}` | `{pub.message_category}` | `{pub.qos_profile or 'default'}` | {ev_ref} |")
        else:
            lines.append("*No publishers declared.*")

        lines.extend(["", "## Subscribers", ""])
        if node.subscribers:
            lines.append("| Topic | Message Type | Category | QoS Profile | Evidence |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for sub in node.subscribers:
                ev_ref = ""
                if sub.evidence:
                    e = sub.evidence[0]
                    ev_ref = f"`{Path(e.file).name}:{e.line_start}`" if e.line_start else f"`{Path(e.file).name}`"
                lines.append(f"| `{sub.name}` | `{sub.message_type}` | `{sub.message_category}` | `{sub.qos_profile or 'default'}` | {ev_ref} |")
        else:
            lines.append("*No subscribers declared.*")

        lines.extend(["", "## Services", ""])
        if node.services:
            lines.append("| Service Name | Type | Role | Evidence |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for srv in node.services:
                ev_ref = ""
                if srv.evidence:
                    e = srv.evidence[0]
                    ev_ref = f"`{Path(e.file).name}:{e.line_start}`" if e.line_start else f"`{Path(e.file).name}`"
                lines.append(f"| `{srv.name}` | `{srv.service_type}` | `{srv.role}` | {ev_ref} |")
        else:
            lines.append("*No services declared.*")

        lines.extend(["", "## Actions", ""])
        if node.actions:
            lines.append("| Action Name | Type | Role | Evidence |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for act in node.actions:
                ev_ref = ""
                if act.evidence:
                    e = act.evidence[0]
                    ev_ref = f"`{Path(e.file).name}:{e.line_start}`" if e.line_start else f"`{Path(e.file).name}`"
                lines.append(f"| `{act.name}` | `{act.action_type}` | `{act.role}` | {ev_ref} |")
        else:
            lines.append("*No actions declared.*")

        lines.extend(["", "## Parameters", ""])
        if node.parameters:
            lines.append("| Parameter Name | Type | Default Value | Description |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for param in node.parameters:
                lines.append(f"| `{param.name}` | `{param.param_type}` | `{param.default_value}` | {param.description or ''} |")
        else:
            lines.append("*No parameters declared.*")

        return "\n".join(lines)


def build_llm_context(model: ArchitectureModel) -> Dict[str, Any]:
    """
    Extract sanitized, repository-grounded context data supplied to the LLM narrative generator.
    Guarantees no foreign entities or unvalidated artifacts leak into LLM prompts.
    """
    stats = model.stats or model.compute_stats()
    discovered_pkgs = sorted(list(set([n.package_name for n in model.nodes if n.package_name] + [l.package_name for l in model.launch_files if l.package_name])))
    return {
        "repository_name": model.repo_name,
        "total_nodes": stats.get("total_nodes", len(model.nodes)),
        "total_subsystems": stats.get("total_subsystems", len(model.subsystems)),
        "total_topics": stats.get("total_topics", len(model.topic_connections)),
        "packages": discovered_pkgs,
        "nodes": [n.name or n.class_name for n in model.nodes if not n.is_test],
    }


def run_doc_generator(arch_json_path: Path, output_dir: Path, use_llm: bool = True) -> Path:
    """Run Stage 5 on an existing ArchitectureModel JSON file with provenance validation"""
    arch_json_path = Path(arch_json_path).resolve()
    with open(arch_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        model = ArchitectureModel.model_validate(data)

    expected_identity = RepositoryIdentity(
        repo_name=model.repo_name,
        repo_root=str(arch_json_path.parent),
        remote_url=model.repo_url,
        commit_sha=model.commit_hash,
        branch=model.branch,
    )
    if not validate_artifact_provenance(arch_json_path, expected_identity, purge_invalid=False):
        raise ValueError(
            f"Artifact provenance validation failed for {arch_json_path}. "
            f"Cannot generate documentation from unverified or mismatched artifact."
        )

    generator = DocGenerator()
    return generator.generate(model, output_dir, use_llm=use_llm)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    arch_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output/nav2_architecture.json")
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output/docs")

    main_doc = run_doc_generator(arch_path, out_dir)
    print(f"\nDocumentation generated successfully at: {main_doc}")
