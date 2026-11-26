"""
ArchSynth CppAnalyzer - Static pattern analysis for C++ ROS2 nodes.
Extracts:
- rclcpp::Node and LifecycleNode class declarations
- Implementation classes and constructor node names
- Component registrations (RCLCPP_COMPONENTS_REGISTER_NODE)
- Source locations and deterministic file:line evidence items
- Explicitly tracks unresolved or dynamic patterns
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Any, Tuple
from dataclasses import dataclass, field

from src.schema import EvidenceItem, EvidenceType

logger = logging.getLogger(__name__)


# Standard ROS2 and Nav2 node base class keywords
NODE_BASE_CLASSES = {
    "rclcpp::Node",
    "rclcpp_lifecycle::LifecycleNode",
    "nav2::LifecycleNode",
    "nav2_util::LifecycleNode",
    "nav2_ros_common::LifecycleNode",
    "Node",
    "LifecycleNode",
}


@dataclass
class ParsedCppNode:
    """Intermediate representation of a parsed C++ ROS2 node"""
    class_name: str
    namespace: str = ""
    fully_qualified_class: str = ""
    node_name: str = ""
    base_class: str = ""
    is_lifecycle: bool = False
    is_component: bool = False
    component_name: Optional[str] = None
    source_file: str = ""
    header_file: Optional[str] = None
    package_name: str = ""
    is_test: bool = False
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    is_abstract: bool = False
    evidence: List[EvidenceItem] = field(default_factory=list)
    unresolved_patterns: List[str] = field(default_factory=list)


def _mask_comments(content: str) -> str:
    """
    Replace comment bodies with spaces/newlines so character count and line numbers
    are 100% preserved while preventing comment text from triggering false matches.
    """
    def replacer(match):
        s = match.group(0)
        if s.startswith('/*'):
            return "".join('\n' if c == '\n' else ' ' for c in s)
        elif s.startswith('//'):
            return " " * len(s)
        return s

    pattern = re.compile(r'/\*.*?\*/|//[^\r\n]*', re.DOTALL)
    return pattern.sub(replacer, content)


def _is_test_file(rel_path: str, package_name: str) -> bool:
    """Check if file is part of test code"""
    path_lower = rel_path.lower().replace("\\", "/")
    pkg_lower = package_name.lower()

    if "test" in pkg_lower or "tests" in pkg_lower:
        return True

    parts = path_lower.split("/")
    if any(p in ("test", "tests", "test_utils", "testing") for p in parts):
        return True

    filename = Path(path_lower).name
    if filename.startswith("test_") or filename.endswith("_test.cpp") or filename.endswith("_test.hpp"):
        return True

    return False


def _extract_namespace(clean_content: str, class_pos: int) -> str:
    """Extract enclosing C++ namespace for a given position in comment-masked content."""
    prefix = clean_content[:class_pos]
    open_namespaces = []

    # Find namespace declarations or braces
    tokens = re.finditer(r'(\bnamespace\s+([A-Za-z0-9_:]+)\s*\{|\{|\})', prefix)
    for m in tokens:
        val = m.group(0)
        if val.startswith("namespace"):
            ns_name = m.group(2)
            open_namespaces.append(ns_name)
        elif val == "{":
            open_namespaces.append(None)  # other scope
        elif val == "}":
            if open_namespaces:
                open_namespaces.pop()

    active_ns = [ns for ns in open_namespaces if ns is not None]
    return "::".join(active_ns)


def _extract_node_name_from_constructor(
    clean_content: str,
    class_name: str,
    known_base_names: Optional[Dict[str, str]] = None
) -> Tuple[str, Optional[int], List[str]]:
    """
    Extract literal node name from constructor initializer list.
    E.g.:
    ControllerServer::ControllerServer(const rclcpp::NodeOptions & options)
    : nav2::LifecycleNode("controller_server", "", options)
    """
    unresolved = []
    first_line_num = None

    patterns = [
        re.compile(rf'\b{re.escape(class_name)}\s*::\s*{re.escape(class_name)}\s*\([^)]*\)\s*:\s*([^;{{]+)', re.DOTALL),
        re.compile(rf'(?:explicit\s+)?\b{re.escape(class_name)}\s*\([^)]*\)\s*:\s*([^;{{]+)', re.DOTALL)
    ]

    for pat in patterns:
        for match in pat.finditer(clean_content):
            init_list = match.group(1)
            line_num = clean_content[:match.start()].count('\n') + 1
            if first_line_num is None:
                first_line_num = line_num

            # Look for literal string inside Node or LifecycleNode call
            base_init_match = re.search(
                r'(?:[A-Za-z0-9_:]*Node)\s*\(\s*"([^"]+)"',
                init_list
            )
            if base_init_match:
                return base_init_match.group(1), line_num, []

            # Check known base names (e.g. SlamToolbox -> "slam_toolbox")
            if known_base_names:
                for base_cls, def_name in known_base_names.items():
                    short_base = base_cls.split("::")[-1]
                    if re.search(rf'\b{re.escape(short_base)}\s*\(', init_list):
                        return def_name, line_num, []

            # Check if constructor passes a parameter / variable without literal string
            dyn_match = re.search(r'(?:[A-Za-z0-9_:]*Node)\s*\(\s*([A-Za-z0-9_]+)', init_list)
            if dyn_match:
                passed_arg = dyn_match.group(1)
                unresolved.append(f"Dynamic/parameterized node name via constructor argument: '{passed_arg}'")

    return "", first_line_num, unresolved


def _find_component_registration(clean_content: str, class_name: str, fully_qualified: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """Detect RCLCPP_COMPONENTS_REGISTER_NODE(Class) macro call."""
    pattern = re.compile(
        r'RCLCPP_COMPONENTS_REGISTER_NODE\s*\(\s*([A-Za-z0-9_:]+)\s*\)'
    )

    for match in pattern.finditer(clean_content):
        registered_class = match.group(1).strip()
        line_num = clean_content[:match.start()].count('\n') + 1

        if (registered_class == class_name or
            registered_class == fully_qualified or
            registered_class.endswith(f"::{class_name}")):
            return True, registered_class, line_num

    return False, None, None


def parse_cpp_file(
    file_path: Path,
    repo_root: Path,
    package_name: str,
    known_base_nodes: Optional[Dict[str, bool]] = None,
    known_base_names: Optional[Dict[str, str]] = None
) -> List[ParsedCppNode]:
    """Parse a single C++ source or header file for ROS2 nodes."""
    try:
        raw_content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Failed to read {file_path}: {e}")
        return []

    clean_content = _mask_comments(raw_content)

    try:
        rel_path = str(file_path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        rel_path = str(file_path).replace("\\", "/")

    is_test = _is_test_file(rel_path, package_name)
    nodes: List[ParsedCppNode] = []

    # Match class declarations with inheritance
    # Matches: class ClassName [final] : public ... {
    class_pattern = re.compile(
        r'\bclass\s+([A-Za-z0-9_]+)\s*(?:final\s*)?:\s*([^{]+)\{',
        re.DOTALL
    )

    for match in class_pattern.finditer(clean_content):
        class_name = match.group(1)
        bases_str = match.group(2)
        start_pos = match.start()
        line_start = clean_content[:start_pos].count('\n') + 1

        # Exclude BehaviorTree.CPP plugins / tree nodes (BtActionNode, BtServiceNode, etc.)
        if any(bt_kw in bases_str for bt_kw in ("BtServiceNode", "BtActionNode", "BtCancelActionNode", "BT::", "ActionNode", "ConditionNode", "DecoratorNode", "ControlNode", "TreeNode", "SyncActionNode")):
            continue

        # Exclude base wrapper definition itself in utility/common packages
        if class_name in ("LifecycleNode", "Node") and package_name in ("nav2_ros_common", "nav2_util", "nav2_common"):
            continue

        matched_base = ""
        is_lifecycle = False

        for base in NODE_BASE_CLASSES:
            if re.search(rf'\bpublic\s+(?:virtual\s+)?(?:[A-Za-z0-9_:]*::)?{re.escape(base)}\b', bases_str) or \
               re.search(rf'\b{re.escape(base)}\b', bases_str):
                matched_base = base
                is_lifecycle = "Lifecycle" in base or "lifecycle" in bases_str
                break

        if not matched_base and known_base_nodes and not is_test:
            for base, is_lc in known_base_nodes.items():
                short_base = base.split("::")[-1]
                if re.search(rf'\bpublic\s+(?:virtual\s+)?(?:[A-Za-z0-9_:]*::)?{re.escape(short_base)}\b', bases_str):
                    matched_base = short_base
                    is_lifecycle = is_lc
                    break

        if not matched_base:
            generic_lifecycle = re.search(r'\bpublic\s+(?:virtual\s+)?([A-Za-z0-9_:]*LifecycleNode)\b', bases_str)
            if generic_lifecycle:
                matched_base = generic_lifecycle.group(1)
                is_lifecycle = True
            else:
                generic_node = re.search(r'\bpublic\s+(?:virtual\s+)?([A-Za-z0-9_:]*Node)\b', bases_str)
                if generic_node and not any(ign in generic_node.group(1) for ign in ("Tree", "Action", "Condition", "Visitor", "Costmap")):
                    matched_base = generic_node.group(1)
                    is_lifecycle = False

        if not matched_base:
            continue

        ns = _extract_namespace(clean_content, start_pos)
        fqn_class = f"{ns}::{class_name}" if ns else class_name

        # Detect pure virtual methods indicating an abstract base class
        is_abstract = False
        remaining = clean_content[match.end():match.end() + 4000]
        if re.search(r'\bvirtual\s+[^;{}]*=\s*0\s*;', remaining):
            is_abstract = True

        node_name, constr_line, unresolved = _extract_node_name_from_constructor(clean_content, class_name, known_base_names)
        is_comp, comp_name, comp_line = _find_component_registration(clean_content, class_name, fqn_class)

        evidence = [
            EvidenceItem(
                file=rel_path,
                line_start=line_start,
                evidence_type=EvidenceType.NODE_DEFINITION,
                source="cpp_ast_analyzer",
                confidence=1.0,
                explanation=f"C++ class '{fqn_class}' inheriting from '{matched_base}'"
            )
        ]

        if is_comp and comp_line:
            evidence.append(
                EvidenceItem(
                    file=rel_path,
                    line_start=comp_line,
                    evidence_type=EvidenceType.COMPONENT_REGISTRATION,
                    source="cpp_ast_analyzer",
                    confidence=1.0,
                    explanation=f"Component registration via RCLCPP_COMPONENTS_REGISTER_NODE({comp_name})"
                )
            )

        parsed_node = ParsedCppNode(
            class_name=class_name,
            namespace=ns,
            fully_qualified_class=fqn_class,
            node_name=node_name,
            base_class=matched_base,
            is_lifecycle=is_lifecycle,
            is_component=is_comp,
            component_name=comp_name,
            source_file=rel_path,
            package_name=package_name,
            is_test=is_test,
            line_start=line_start,
            is_abstract=is_abstract,
            evidence=evidence,
            unresolved_patterns=unresolved
        )
        nodes.append(parsed_node)

    # Also detect standalone functional C++ nodes: rclcpp::Node::make_shared("name") or std::make_shared<rclcpp::Node>("name")
    existing_node_names = {n.node_name for n in nodes if n.node_name}
    if not nodes and not is_test:
        standalone_pat = re.compile(
            r'(?:(rclcpp_lifecycle::LifecycleNode|rclcpp::Node)::make_shared|std::make_shared\s*<\s*(rclcpp_lifecycle::LifecycleNode|rclcpp::Node)\s*>)\s*\(\s*"([^"]+)"',
            re.DOTALL
        )
        for m in standalone_pat.finditer(clean_content):
            base_cls = m.group(1) or m.group(2)
            nname = m.group(3)
            if nname in existing_node_names:
                continue
            existing_node_names.add(nname)
            lno = clean_content[:m.start()].count('\n') + 1
            cls_label = "".join(w.capitalize() for w in nname.replace("-", "_").split("_") if w) or nname
            is_lc = "Lifecycle" in base_cls
            nodes.append(ParsedCppNode(
                class_name=cls_label,
                namespace=_extract_namespace(clean_content, m.start()),
                fully_qualified_class=cls_label,
                node_name=nname,
                base_class=base_cls,
                is_lifecycle=is_lc,
                is_component=False,
                source_file=rel_path,
                package_name=package_name,
                is_test=is_test,
                line_start=lno,
                evidence=[
                    EvidenceItem(
                        file=rel_path,
                        line_start=lno,
                        evidence_type=EvidenceType.NODE_DEFINITION,
                        source="cpp_ast_analyzer",
                        confidence=1.0,
                        explanation=f"Standalone C++ node instantiated via {base_cls} ('{nname}')"
                    )
                ],
            ))

    return nodes


def analyze_cpp_package(package_path: Path, repo_root: Path, package_name: str) -> List[ParsedCppNode]:
    """
    Analyze all C++ source and header files in a ROS2 package.
    Merges declarations in .hpp with definitions in .cpp.
    Iteratively discovers derived node classes in the package hierarchy.
    """
    all_files: List[Path] = []
    for root, dirs, files in os.walk(package_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in ('.hpp', '.h', '.cpp', '.cc', '.cxx'):
                all_files.append(Path(root) / file)

    known_base_nodes: Dict[str, bool] = {}
    known_base_names: Dict[str, str] = {}
    header_nodes: Dict[str, ParsedCppNode] = {}
    source_nodes: Dict[str, ParsedCppNode] = {}

    # Iterative discovery: up to 3 passes until no new node classes are found
    for _ in range(3):
        discovered_new = False
        for f in all_files:
            found_nodes = parse_cpp_file(f, repo_root, package_name, known_base_nodes, known_base_names)
            ext = f.suffix.lower()

            for node in found_nodes:
                key = node.fully_qualified_class or node.class_name
                target_dict = header_nodes if ext in ('.hpp', '.h') else source_nodes
                if key not in target_dict:
                    target_dict[key] = node
                    discovered_new = True
                else:
                    if not target_dict[key].node_name and node.node_name:
                        target_dict[key].node_name = node.node_name

                if not node.is_test and key not in known_base_nodes:
                    known_base_nodes[key] = node.is_lifecycle
                    known_base_nodes[node.class_name] = node.is_lifecycle
                if not node.is_test and node.node_name:
                    known_base_names[key] = node.node_name
                    known_base_names[node.class_name] = node.node_name

        if not discovered_new:
            break

    # Correlate header nodes with .cpp implementations
    cpp_sources = [f for f in all_files if f.suffix.lower() in ('.cpp', '.cc', '.cxx')]

    for cpp_file in cpp_sources:
        try:
            raw_cpp = cpp_file.read_text(encoding="utf-8", errors="ignore")
            clean_cpp = _mask_comments(raw_cpp)
            cpp_rel = str(cpp_file.relative_to(repo_root)).replace("\\", "/")
        except Exception:
            continue

        for key, h_node in list(header_nodes.items()):
            cls_name = h_node.class_name
            fqn = h_node.fully_qualified_class

            node_name, constr_line, unresolved = _extract_node_name_from_constructor(clean_cpp, cls_name, known_base_names)
            is_comp, comp_name, comp_line = _find_component_registration(clean_cpp, cls_name, fqn)

            if constr_line or is_comp:
                if key in source_nodes:
                    s_node = source_nodes[key]
                    if node_name and not s_node.node_name:
                        s_node.node_name = node_name
                    if is_comp:
                        s_node.is_component = True
                        s_node.component_name = comp_name
                else:
                    evidence = list(h_node.evidence)
                    if constr_line:
                        evidence.append(EvidenceItem(
                            file=cpp_rel,
                            line_start=constr_line,
                            evidence_type=EvidenceType.NODE_DEFINITION,
                            source="cpp_ast_analyzer",
                            confidence=1.0,
                            explanation=f"Constructor implementation with node name '{node_name}'"
                        ))
                    if is_comp and comp_line:
                        evidence.append(EvidenceItem(
                            file=cpp_rel,
                            line_start=comp_line,
                            evidence_type=EvidenceType.COMPONENT_REGISTRATION,
                            source="cpp_ast_analyzer",
                            confidence=1.0,
                            explanation=f"Component registration via RCLCPP_COMPONENTS_REGISTER_NODE({comp_name})"
                        ))

                    merged_node = ParsedCppNode(
                        class_name=h_node.class_name,
                        namespace=h_node.namespace,
                        fully_qualified_class=h_node.fully_qualified_class,
                        node_name=node_name or h_node.node_name,
                        base_class=h_node.base_class,
                        is_lifecycle=h_node.is_lifecycle,
                        is_component=is_comp or h_node.is_component,
                        component_name=comp_name or h_node.component_name,
                        source_file=cpp_rel,
                        header_file=h_node.source_file,
                        package_name=package_name,
                        is_test=h_node.is_test or _is_test_file(cpp_rel, package_name),
                        line_start=constr_line or h_node.line_start,
                        is_abstract=h_node.is_abstract,
                        evidence=evidence,
                        unresolved_patterns=unresolved or h_node.unresolved_patterns
                    )
                    source_nodes[key] = merged_node

    final_nodes: List[ParsedCppNode] = list(source_nodes.values())
    for key, h_node in header_nodes.items():
        if key not in source_nodes:
            final_nodes.append(h_node)

    # Propagate default node names across class inheritance hierarchy
    for _ in range(3):
        known_names = {}
        for n in final_nodes:
            if n.node_name:
                known_names[n.class_name] = n.node_name
                known_names[n.fully_qualified_class] = n.node_name
                known_names[n.class_name.split("::")[-1]] = n.node_name
        for n in final_nodes:
            if not n.node_name and n.base_class:
                short_b = n.base_class.split("::")[-1]
                if short_b in known_names:
                    n.node_name = known_names[short_b]

    return final_nodes
