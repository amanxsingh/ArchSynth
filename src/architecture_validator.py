"""
ArchSynth ArchitectureValidator - Structural & Semantic Architecture Validation.

Builds a unified, classified Node & Executable Inventory and performs
cross-artifact consistency checks classifying findings as:
  - Confirmed
  - Warning
  - Unresolved
  - Potential inconsistency
"""

from collections import Counter
from typing import Any, Dict, List, Set

from src.schema import (
    ArchitectureModel,
    ArchitectureValidationFinding,
    ArchitectureValidationReport,
    EvidenceItem,
    EvidenceType,
    LaunchMappingStatus,
    ResolutionStatus,
)


def build_structured_node_inventory(model: ArchitectureModel) -> List[Dict[str, Any]]:
    """
    Build a structured, non-overlapping node/executable inventory distinguishing:
      - repository_defined_node
      - repository_test_node
      - composable_node
      - dynamically_loaded_component
      - internal_launch_instance
      - launch_composable_instance
      - external_ros_node
      - unresolved_executable
    """
    inventory: List[Dict[str, Any]] = []
    seen_keys: Set[str] = set()
    id_to_entry: Dict[str, Dict[str, Any]] = {}
    internal_pkgs = set(model.package_dependency_graph.internal_packages) if model.package_dependency_graph else {
        n.package_name for n in model.nodes if n.package_name
    }

    # 1. Source-grounded repository nodes
    for n in model.nodes:
        if n.component_registered or n.composition:
            cls_type = "composable_node"
        elif n.is_test:
            cls_type = "repository_test_node"
        else:
            cls_type = "repository_defined_node"

        ident = n.id or n.fully_qualified_name or n.name
        ev_list = [f"{e.file}:L{e.line_start or 1}" for e in n.evidence[:2]]
        entry = {
            "identifier": ident,
            "name": n.name or n.class_name,
            "package": n.package_name,
            "executable": n.executable or "(library/script)",
            "classification": cls_type,
            "origin": "repository_source",
            "language": n.source_language,
            "confidence": 1.0 if n.evidence else 0.5,
            "resolution_status": n.resolution_status.value,
            "linked_plugin_id": None,
            "evidence": ev_list,
        }
        inventory.append(entry)
        for k in (n.id, n.fully_qualified_name, n.name):
            if k:
                seen_keys.add(k.lower())
                id_to_entry[k.lower()] = entry

    # 2. Launch-declared executables, internal unmapped instances, and unresolved executables
    ext_seen: Set[tuple] = set()
    for inst in model.launch_instances:
        if inst.mapping_status == LaunchMappingStatus.RESOLVED and inst.node_id:
            continue  # Already represented as repository_defined_node

        exe_name = inst.executable or inst.plugin_class or inst.node_name
        pkg_name = inst.package or "unknown"
        key = (pkg_name, exe_name, inst.node_name)
        if key in ext_seen:
            continue
        ext_seen.add(key)

        is_dynamic = "${" in str(exe_name) or "${" in str(pkg_name) or inst.resolution_status == ResolutionStatus.UNRESOLVED
        if is_dynamic:
            cls_type = "unresolved_executable"
            conf = 0.4
        elif inst.action_type == "LoadComposableNodes":
            cls_type = "launch_composable_instance"
            conf = 0.85
        elif inst.is_composable:
            cls_type = "launch_composable_instance"
            conf = 0.9
        elif pkg_name in internal_pkgs:
            cls_type = "internal_launch_instance"
            conf = 0.85
        else:
            cls_type = "external_ros_node"
            conf = 0.95

        inventory.append({
            "identifier": inst.instance_id,
            "name": inst.node_name or exe_name,
            "package": pkg_name,
            "executable": exe_name,
            "classification": cls_type,
            "origin": "launch_declaration",
            "language": "external" if cls_type == "external_ros_node" else "internal",
            "confidence": conf,
            "resolution_status": inst.resolution_status.value,
            "linked_plugin_id": None,
            "evidence": [f"{inst.launch_file}:L{inst.line_number or 1}"],
        })

    # 3. Dynamically loaded plugins declared in pluginlib manifests (deduplicated case-insensitively)
    if model.plugin_architecture:
        for p in model.plugin_architecture.plugins:
            cand_keys = [k.lower() for k in (p.plugin_name, p.class_type) if k]
            matched_key = next((k for k in cand_keys if k in seen_keys), None)
            if matched_key:
                id_to_entry[matched_key]["linked_plugin_id"] = p.plugin_name
                continue
            pkg_val = p.package_name if p.package_name and not p.package_name.endswith(".xml") else model.repo_name
            inventory.append({
                "identifier": p.plugin_name,
                "name": p.class_type,
                "package": pkg_val,
                "executable": "(pluginlib)",
                "classification": "dynamically_loaded_component",
                "origin": "pluginlib_manifest",
                "language": "cpp",
                "confidence": 1.0,
                "resolution_status": p.status.value,
                "linked_plugin_id": p.plugin_name,
                "evidence": [f"{p.manifest_file}:L1"],
            })

    return inventory


def compute_inventory_reconciliation(model: ArchitectureModel) -> Dict[str, Any]:
    """
    Compute non-overlapping entity counts reconciling source nodes, executables,
    registered/pluginlib components, launch instances, and runtime observations.
    """
    source_nodes = list(model.nodes)
    prod_nodes = [n for n in source_nodes if not n.is_test]
    test_nodes = [n for n in source_nodes if n.is_test]

    exe_targets = {
        (n.package_name or "", n.executable)
        for n in source_nodes
        if n.executable and n.executable != "(library/script)"
    }
    for inst in model.launch_instances:
        if inst.executable and "${" not in str(inst.executable):
            exe_targets.add((inst.package or "", inst.executable))

    comp_keys = {
        (n.id or n.fully_qualified_name or n.name).lower()
        for n in source_nodes
        if n.component_registered or n.composition
    }
    if model.plugin_architecture:
        for p in model.plugin_architecture.plugins:
            comp_keys.add((p.class_type or p.plugin_name).lower())

    resolved_inst = sum(1 for i in model.launch_instances if i.mapping_status == LaunchMappingStatus.RESOLVED)
    unresolved_inst = sum(1 for i in model.launch_instances if i.resolution_status == ResolutionStatus.UNRESOLVED)

    return {
        "unique_source_nodes": len(source_nodes),
        "unique_production_nodes": len(prod_nodes),
        "unique_test_nodes": len(test_nodes),
        "unique_executables": len(exe_targets),
        "unique_components": len(comp_keys),
        "unique_launch_instances": len(model.launch_instances),
        "launch_instances_resolved_to_source": resolved_inst,
        "launch_instances_unresolved": unresolved_inst,
        "runtime_observed_nodes": None,
        "runtime_observation_available": False,
    }


def validate_architecture_consistency(model: ArchitectureModel) -> ArchitectureValidationReport:
    """
    Run structural and semantic architecture validation checks across the recovered model.
    """
    findings: List[ArchitectureValidationFinding] = []
    idx = 0

    def _add(category: str, severity: str, entity: str, msg: str, ev: List[EvidenceItem] = None):
        nonlocal idx
        idx += 1
        findings.append(ArchitectureValidationFinding(
            finding_id=f"VAL-{idx:03d}",
            category=category,
            severity=severity,
            entity=entity,
            message=msg,
            evidence=ev or [],
        ))

    internal_pkgs = set(model.package_dependency_graph.internal_packages) if model.package_dependency_graph else {
        n.package_name for n in model.nodes if n.package_name
    }

    # 1. Duplicate node identities
    id_counts = Counter(n.id for n in model.nodes if n.id)
    for nid, cnt in id_counts.items():
        if cnt > 1:
            _add(
                "duplicate_node_identity",
                "Potential inconsistency",
                nid,
                f"Node ID '{nid}' appears {cnt} times in nodes inventory.",
            )

    # 2. Missing evidence on source nodes
    for n in model.nodes:
        if not n.evidence:
            _add(
                "missing_evidence",
                "Potential inconsistency",
                n.id or n.name,
                f"Source node '{n.name}' has no attached source file:line evidence.",
            )

    # 3. Launch-referenced executables vs source packages
    seen_ext: Set[str] = set()
    for inst in model.launch_instances:
        if inst.mapping_status == LaunchMappingStatus.RESOLVED:
            continue
        exe = inst.executable or inst.node_name
        pkg = inst.package
        ev = [EvidenceItem(
            file=inst.launch_file,
            line_start=inst.line_number or 1,
            evidence_type=EvidenceType.LAUNCH_NODE,
            source="architecture_validator",
            confidence=1.0,
            explanation=f"Declared in {inst.launch_file}",
        )]
        if "${" in str(exe) or "${" in str(pkg):
            _add(
                "unresolved_launch_substitution",
                "Unresolved",
                f"{pkg}::{exe}",
                f"Launch executable '{exe}' in {inst.launch_file} depends on unresolved launch argument/substitution.",
                ev,
            )
        elif pkg in internal_pkgs:
            _add(
                "launch_node_mismatch",
                "Warning",
                f"{pkg}::{exe}",
                f"Launch file {inst.launch_file} invokes '{exe}' in internal package '{pkg}', which was not matched to a parsed node class.",
                ev,
            )
        else:
            key = f"{pkg}::{exe}"
            if key not in seen_ext:
                seen_ext.add(key)
                _add(
                    "external_launch_executable",
                    "Confirmed",
                    key,
                    f"External ROS 2 executable '{exe}' from external package '{pkg}' declared in {inst.launch_file}.",
                    ev,
                )

    # 4. Source-defined nodes not referenced by any analyzed launch file
    launched_node_ids = {inst.node_id for inst in model.launch_instances if inst.node_id}
    for n in model.nodes:
        if n.is_test:
            continue
        if n.id not in launched_node_ids:
            _add(
                "unlaunched_source_node",
                "Warning",
                n.id or n.name,
                f"Source node '{n.name}' ({n.source_file}) is not referenced by any analyzed launch file (may be invoked directly via ros2 run or library API).",
                n.evidence[:1],
            )

    # 5. Unmatched topics, services, and actions
    for tc in model.topic_connections:
        pubs = tc.get("publishers", [])
        subs = tc.get("subscribers", [])
        topic = tc.get("topic", "")
        if pubs and not subs:
            _add(
                "publisher_without_subscriber",
                "Unresolved",
                topic,
                f"Topic '{topic}' has internal publisher(s) {pubs} with no in-repo subscriber (likely consumed by external nodes such as move_group, servo_node, or gazebo).",
            )
        elif subs and not pubs:
            _add(
                "subscriber_without_publisher",
                "Unresolved",
                topic,
                f"Topic '{topic}' has internal subscriber(s) {subs} with no in-repo publisher (likely published by external drivers/sensors such as joy_node or camera bridge).",
            )

    for sc in model.service_connections:
        srvs = sc.get("servers", [])
        clts = sc.get("clients", [])
        sname = sc.get("service", "")
        if clts and not srvs:
            _add(
                "unresolved_service_client",
                "Unresolved",
                sname,
                f"Service '{sname}' is called by {clts} with no in-repo server (provided by external ROS 2 package).",
            )

    for ac in model.action_connections:
        srvs = ac.get("servers", [])
        clts = ac.get("clients", [])
        aname = ac.get("action", "")
        if clts and not srvs:
            _add(
                "unresolved_action_client",
                "Unresolved",
                aname,
                f"Action '{aname}' has client(s) {clts} with no in-repo server (provided by external controller/MoveIt node).",
            )

    # 6. Missing message/interface types
    for decl in model.interfaces:
        if "unknown" in (decl.message_type or "").lower():
            _add(
                "missing_interface_type",
                "Warning",
                decl.name_expression,
                f"Interface '{decl.name_expression}' in {decl.source_file} has unresolved message type '{decl.message_type}'.",
                decl.evidence[:1],
            )

    # 7. Undeclared source package dependencies
    if model.package_dependency_graph:
        for udep in model.package_dependency_graph.undeclared_source_dependencies:
            _add(
                "missing_package_dependency",
                "Potential inconsistency",
                f"{udep['source_package']} -> {udep['target_package']}",
                f"Source file {udep['file']}:L{udep['line']} uses '{udep['target_package']}' ({udep['dependency_type']}), which is not declared in package.xml.",
            )

    # 8. Unresolved dynamic launch constructs (OpaqueFunction, ExecuteProcess, etc.)
    for lf in model.launch_files:
        for expr in getattr(lf, "unresolved_expressions", []):
            _add(
                "unresolved_launch_construct",
                "Unresolved",
                lf.file_path,
                f"Dynamic/opaque launch construct in {lf.file_path}: {expr}",
            )

    counts = dict(Counter(f.severity for f in findings))
    return ArchitectureValidationReport(
        findings=findings,
        counts_by_severity=counts,
        inventory_reconciliation=compute_inventory_reconciliation(model),
    )
