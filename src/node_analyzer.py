"""
ArchSynth NodeAnalyzer - Stage 2: Extract ROS2 nodes from Python and C++ source code.

Phase 1 Improvements:
- Fixes Python node AST visitor (eliminates duplicate node insertion)
- Extracts node names from __init__ defaults, super().__init__(), and self.node_name
- Discovers C++ ROS2 nodes (rclcpp::Node, LifecycleNode, and component registrations)
- Analyzes CMakeLists.txt to map executables and library component targets
- Assigns stable unique identifiers and separates identity from runtime name
- Classifies test nodes vs production nodes vs client/application nodes
- Preserves deterministic file:line evidence items for every entity
"""

import ast
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from collections import Counter

from src.schema import (
    ROS2Node, TopicInfo, ServiceInfo, ActionInfo, ParameterInfo,
    MessageType, EvidenceItem, EvidenceType, ValidationStatus,
    EntityType, NodeCategory, ResolutionStatus
)
from src.build_analyzer import analyze_package_cmake, PackageCMakeInfo
from src.cpp_analyzer import analyze_cpp_package, ParsedCppNode

logger = logging.getLogger(__name__)


@dataclass
class ParsedNode:
    """Intermediate representation of a parsed ROS2 Python node"""
    class_name: str
    node_name: str
    source_file: str
    package_name: str
    namespace: str = ""
    docstring: Optional[str] = None
    publishers: List[Dict[str, Any]] = field(default_factory=list)
    subscribers: List[Dict[str, Any]] = field(default_factory=list)
    services: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    remappings: Dict[str, str] = field(default_factory=dict)
    is_lifecycle: bool = False
    composition: Optional[str] = None
    definition_line: Optional[int] = None
    definition_end_line: Optional[int] = None


class ROS2NodeVisitor(ast.NodeVisitor):
    """
    AST visitor that extracts ROS2 node information from Python source files.
    """

    def __init__(self, source_file: str, package_name: str):
        self.source_file = source_file
        self.package_name = package_name
        self.nodes: List[ParsedNode] = []
        self.class_stack: List[ParsedNode] = []
        self.imports: Set[str] = set()
        self.base_classes: Dict[str, str] = {}

    @property
    def current_class(self) -> Optional[ParsedNode]:
        return self.class_stack[-1] if self.class_stack else None

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.add(alias.name)
            if alias.asname:
                self.base_classes[alias.asname] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            full_name = f"{module}.{alias.name}" if module else alias.name
            self.imports.add(full_name)
            if alias.asname:
                self.base_classes[alias.asname] = full_name
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        is_node_class = self._is_node_subclass(node)

        if is_node_class:
            parsed = ParsedNode(
                class_name=node.name,
                node_name="",
                source_file=self.source_file,
                package_name=self.package_name,
                docstring=ast.get_docstring(node),
                definition_line=node.lineno,
                definition_end_line=getattr(node, 'end_lineno', None),
                is_lifecycle="Lifecycle" in node.name or any("Lifecycle" in getattr(b, 'id', '') for b in node.bases if isinstance(b, ast.Name))
            )
            self.class_stack.append(parsed)
            self.generic_visit(node)
            completed = self.class_stack.pop()
            self.nodes.append(completed)
        else:
            self.generic_visit(node)

    def _is_node_subclass(self, node: ast.ClassDef) -> bool:
        """Check if class inherits from rclpy.node.Node or Node"""
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_name = base.id
                if base_name in ('Node', 'LifecycleNode'):
                    return True
                if base_name in self.base_classes:
                    imported = self.base_classes[base_name]
                    if 'rclpy.node' in imported and 'Node' in imported:
                        return True
            elif isinstance(base, ast.Attribute):
                if (isinstance(base.value, ast.Name) and
                    base.value.id == 'rclpy' and
                    base.attr == 'Node'):
                    return True
                if (isinstance(base.value, ast.Attribute) and
                    isinstance(base.value.value, ast.Name) and
                    base.value.value.id == 'rclpy' and
                    base.value.attr == 'node' and
                    base.attr == 'Node'):
                    return True
        return False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Extract default node_name / namespace from __init__ definition"""
        if self.current_class and node.name == '__init__':
            for arg, default in zip(reversed(node.args.args), reversed(node.args.defaults)):
                if arg.arg in ('node_name', 'name'):
                    val = self._eval_ast_node(default)
                    if isinstance(val, str) and val and not self.current_class.node_name:
                        self.current_class.node_name = val
                elif arg.arg == 'namespace':
                    val = self._eval_ast_node(default)
                    if isinstance(val, str) and val and not self.current_class.namespace:
                        self.current_class.namespace = val

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if not self.current_class:
            self.generic_visit(node)
            return

        func_name = self._get_call_name(node)
        if not func_name:
            self.generic_visit(node)
            return

        # Handle super().__init__() or Node.__init__()
        if func_name == '__init__':
            name_val = self._get_arg_value(node, 0, 'node_name') or self._get_arg_value(node, 0, 'name')
            if isinstance(name_val, str) and name_val and not self.current_class.node_name:
                self.current_class.node_name = name_val
            ns_val = self._get_arg_value(node, 1, 'namespace')
            if isinstance(ns_val, str) and ns_val and not self.current_class.namespace:
                self.current_class.namespace = ns_val

        elif func_name in ('create_publisher', 'create_subscription'):
            self._handle_pub_sub(node, func_name)
        elif func_name in ('create_service', 'create_client'):
            self._handle_service(node, func_name)
        elif func_name in ('create_action_server', 'create_action_client', 'ActionServer', 'ActionClient'):
            self._handle_action(node, func_name)
        elif func_name in ('declare_parameter', 'declare_parameters'):
            self._handle_parameter(node, func_name)

        self.generic_visit(node)

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _get_arg_value(self, node: ast.Call, index: int, keyword: str = None) -> Any:
        if keyword:
            for kw in node.keywords:
                if kw.arg == keyword:
                    return self._eval_ast_node(kw.value)
        if index < len(node.args):
            return self._eval_ast_node(node.args[index])
        return None

    def _eval_ast_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.List):
            return [self._eval_ast_node(el) for el in node.elts]
        elif isinstance(node, ast.Dict):
            return {
                self._eval_ast_node(k): self._eval_ast_node(v)
                for k, v in zip(node.keys, node.values)
            }
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_chain(node)
        elif isinstance(node, ast.Call):
            return self._get_call_name(node) or "call()"
        return None

    def _get_attribute_chain(self, node: ast.Attribute) -> str:
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return '.'.join(reversed(parts))

    def _handle_pub_sub(self, node: ast.Call, call_type: str):
        msg_type = self._get_arg_value(node, 0, 'msg_type')
        topic = self._get_arg_value(node, 1, 'topic')
        qos = self._get_arg_value(node, 2, 'qos_profile') or self._get_arg_value(node, 3, 'qos_profile')

        if msg_type and topic:
            info = {
                'topic': topic,
                'msg_type': msg_type,
                'qos': qos,
                'line_start': getattr(node, 'lineno', None),
                'line_end': getattr(node, 'end_lineno', None),
            }
            if call_type == 'create_publisher':
                self.current_class.publishers.append(info)
            else:
                self.current_class.subscribers.append(info)

    def _handle_service(self, node: ast.Call, call_type: str):
        srv_type = self._get_arg_value(node, 0, 'srv_type')
        srv_name = self._get_arg_value(node, 1, 'srv_name')

        if srv_type and srv_name:
            info = {
                'service': srv_name,
                'srv_type': srv_type,
                'role': 'server' if call_type == 'create_service' else 'client',
                'line_start': getattr(node, 'lineno', None),
                'line_end': getattr(node, 'end_lineno', None),
            }
            self.current_class.services.append(info)

    def _handle_action(self, node: ast.Call, call_type: str):
        if call_type in ('ActionClient', 'ActionServer'):
            action_type = self._get_arg_value(node, 1, 'action_type')
            action_name = self._get_arg_value(node, 2, 'action_name')
            role = 'server' if call_type == 'ActionServer' else 'client'
        else:
            action_type = self._get_arg_value(node, 0, 'action_type')
            action_name = self._get_arg_value(node, 1, 'action_name')
            role = 'server' if call_type == 'create_action_server' else 'client'

        if action_type and action_name:
            info = {
                'action': action_name,
                'action_type': action_type,
                'role': role,
                'line_start': getattr(node, 'lineno', None),
                'line_end': getattr(node, 'end_lineno', None),
            }
            self.current_class.actions.append(info)

    def _handle_parameter(self, node: ast.Call, call_type: str):
        if call_type == 'declare_parameter':
            name = self._get_arg_value(node, 0, 'name')
            default = self._get_arg_value(node, 1, 'default_value')
            descriptor = self._get_arg_value(node, 2, 'descriptor')
            if name:
                self.current_class.parameters.append({
                    'name': name,
                    'default': default,
                    'descriptor': descriptor
                })

    def visit_Assign(self, node: ast.Assign):
        if not self.current_class:
            self.generic_visit(node)
            return

        for target in node.targets:
            if (isinstance(target, ast.Attribute) and
                isinstance(target.value, ast.Name) and
                target.value.id == 'self' and
                target.attr in ('node_name', '_node_name', 'name')):

                value = self._eval_ast_node(node.value)
                if isinstance(value, str) and value:
                    self.current_class.node_name = value

        self.generic_visit(node)


def parse_python_file(file_path: Path, package_name: str) -> List[ParsedNode]:
    """Parse a single Python file for ROS2 nodes."""
    try:
        source = file_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.warning(f"Failed to read {file_path}: {e}")
        return []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
        return []

    visitor = ROS2NodeVisitor(str(file_path), package_name)
    visitor.visit(tree)

    # Also detect functional node instantiations outside classes:
    # e.g. node = rclpy.create_node("name") or node = rclcpp.Node("name")
    existing_names = {n.node_name for n in visitor.nodes if n.node_name}
    for ast_node in ast.walk(tree):
        if not isinstance(ast_node, ast.Call):
            continue
        full_call = ""
        if isinstance(ast_node.func, ast.Attribute):
            full_call = visitor._get_attribute_chain(ast_node.func)
        elif isinstance(ast_node.func, ast.Name):
            full_call = ast_node.func.id

        if full_call in ("rclpy.create_node", "create_node", "rclcpp.Node", "rclpy.node.Node"):
            nname = visitor._get_arg_value(ast_node, 0, "node_name")
            if isinstance(nname, str) and nname and nname not in existing_names:
                existing_names.add(nname)
                # Convert snake_case / string to PascalCase class-like label for unique ID
                cls_label = "".join(w.capitalize() for w in nname.replace("-", "_").split("_") if w) or nname
                fn_node = ParsedNode(
                    class_name=cls_label,
                    node_name=nname,
                    source_file=str(file_path),
                    package_name=package_name,
                    docstring=f"Functional ROS 2 node instantiated via {full_call}('{nname}')",
                    definition_line=getattr(ast_node, "lineno", None),
                    definition_end_line=getattr(ast_node, "end_lineno", None),
                )
                visitor.nodes.append(fn_node)

    return visitor.nodes


def find_python_files(package_path: Path) -> List[Path]:
    """Find all Python files in a package, excluding setup files and __pycache__"""
    python_files = []
    for root, dirs, files in os.walk(package_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.endswith('.py') and file != 'setup.py':
                python_files.append(Path(root) / file)
    return python_files


def analyze_package(package_path: Path, package_name: str) -> List[ParsedNode]:
    """Analyze all Python files in a ROS2 package for nodes."""
    all_nodes = []
    python_files = find_python_files(package_path)

    for py_file in python_files:
        nodes = parse_python_file(py_file, package_name)
        all_nodes.extend(nodes)

    return all_nodes


def _build_evidence_item(
    rel_file: str,
    evidence_type: EvidenceType,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
    explanation: Optional[str] = None
) -> EvidenceItem:
    return EvidenceItem(
        file=rel_file,
        line_start=line_start,
        line_end=line_end,
        evidence_type=evidence_type,
        source="python_ast_analyzer",
        confidence=1.0,
        explanation=explanation
    )


def _is_test_python(pnode: ParsedNode) -> bool:
    """Determine whether a parsed Python node is a test node"""
    pkg_lower = pnode.package_name.lower()
    file_lower = pnode.source_file.lower().replace("\\", "/")
    cls_lower = pnode.class_name.lower()

    if "test" in pkg_lower or "tests" in pkg_lower:
        return True
    if "/test/" in file_lower or "/tests/" in file_lower or "test_" in file_lower:
        return True
    if cls_lower.endswith("test") or cls_lower.endswith("tester") or cls_lower.startswith("test"):
        return True

    return False


def _categorize_message_type(msg_type: Any) -> MessageType:
    msg_str = str(msg_type).lower()
    if 'std_msgs' in msg_str:
        return MessageType.STD_MSGS
    elif 'geometry_msgs' in msg_str:
        return MessageType.GEOMETRY_MSGS
    elif 'sensor_msgs' in msg_str:
        return MessageType.SENSOR_MSGS
    elif 'nav_msgs' in msg_str:
        return MessageType.NAV_MSGS
    elif 'action_msgs' in msg_str:
        return MessageType.ACTION_MSGS
    elif '/' in msg_str:
        return MessageType.CUSTOM
    return MessageType.UNKNOWN


def _classify_node_category(package_name: str, class_name: str, is_test: bool) -> NodeCategory:
    """Assign logical subsystem category based on package and class name"""
    if is_test:
        return NodeCategory.TEST

    pkg = package_name.lower()
    cls = class_name.lower()

    if "client" in pkg or cls == "basicnavigator":
        return NodeCategory.CLIENT
    if "controller" in pkg or "control" in pkg:
        return NodeCategory.CONTROL
    if "planner" in pkg or "planning" in pkg or "navfn" in pkg or "smac" in pkg or "theta_star" in pkg:
        return NodeCategory.PLANNING
    if "amcl" in pkg or "localization" in pkg:
        return NodeCategory.LOCALIZATION
    if "bt_navigator" in pkg or "behavior" in pkg:
        return NodeCategory.BEHAVIOR
    if any(k in pkg for k in ("map_server", "costmap", "lifecycle", "collision", "smoother", "waypoint")):
        return NodeCategory.INFRASTRUCTURE

    return NodeCategory.UNKNOWN


def run_node_analysis(repo_path: Path, output_path: Path) -> List[ROS2Node]:
    """
    Run complete Phase 1 node analysis across Python and C++ source code.
    Extracts, resolves, and verifies ROS2 nodes with deterministic source evidence.
    """
    logger.info(f"Starting Phase 1 Node Discovery on: {repo_path}")
    from src.ingestor import Ingestor

    ingestor = Ingestor()
    packages = ingestor.find_ros2_packages(repo_path)
    root_path = repo_path

    all_schema_nodes: List[ROS2Node] = []

    # First pass: parse Python nodes, CMakeLists, and C++ nodes
    parsed_python_by_pkg: Dict[str, List[ParsedNode]] = {}
    cmake_info_by_pkg: Dict[str, PackageCMakeInfo] = {}
    parsed_cpp_by_pkg: Dict[str, List[ParsedCppNode]] = {}

    from src.build_analyzer import parse_setup_py
    console_scripts_by_pkg: Dict[str, Dict[str, str]] = {}

    for pkg_name, pkg_rel_path in packages.items():
        pkg_path = repo_path / pkg_rel_path

        # 1. CMakeLists analysis & setup.py console_scripts
        cmake_info = analyze_package_cmake(pkg_path, pkg_name)
        cmake_info_by_pkg[pkg_name] = cmake_info
        setup_info = parse_setup_py(pkg_path / "setup.py")
        if setup_info.get("console_scripts"):
            console_scripts_by_pkg[pkg_name] = setup_info["console_scripts"]

        # 2. Python source analysis
        py_nodes = analyze_package(pkg_path, pkg_name)
        if py_nodes:
            parsed_python_by_pkg[pkg_name] = py_nodes

        # 3. C++ source analysis
        cpp_nodes = analyze_cpp_package(pkg_path, repo_path, pkg_name)
        if cpp_nodes:
            parsed_cpp_by_pkg[pkg_name] = cpp_nodes

    # Convert Python nodes to schema
    raw_python_nodes: List[ROS2Node] = []
    for pkg_name, pnodes in parsed_python_by_pkg.items():
        for pnode in pnodes:
            try:
                rel_path = str(Path(pnode.source_file).relative_to(root_path)).replace("\\", "/")
            except ValueError:
                rel_path = pnode.source_file.replace("\\", "/")

            is_test = _is_test_python(pnode)

            # Node evidence
            evidence = []
            if pnode.definition_line is not None:
                evidence.append(_build_evidence_item(
                    rel_file=rel_path,
                    evidence_type=EvidenceType.NODE_DEFINITION,
                    line_start=pnode.definition_line,
                    line_end=pnode.definition_end_line,
                    explanation=f"Python ROS2 node class '{pnode.class_name}'"
                ))

            # Publishers & subscribers
            pubs = [TopicInfo(
                name=p.get('topic', ''),
                message_type=str(p.get('msg_type', '')),
                message_category=_categorize_message_type(p.get('msg_type', '')),
                qos_profile=str(p.get('qos')) if p.get('qos') else None,
                evidence=[_build_evidence_item(rel_path, EvidenceType.PUBLISHER_CREATION, p.get('line_start'), p.get('line_end'))]
            ) for p in pnode.publishers]

            subs = [TopicInfo(
                name=s.get('topic', ''),
                message_type=str(s.get('msg_type', '')),
                message_category=_categorize_message_type(s.get('msg_type', '')),
                qos_profile=str(s.get('qos')) if s.get('qos') else None,
                evidence=[_build_evidence_item(rel_path, EvidenceType.SUBSCRIBER_CREATION, s.get('line_start'), s.get('line_end'))]
            ) for s in pnode.subscribers]

            srvs = [ServiceInfo(
                name=s.get('service', ''),
                service_type=str(s.get('srv_type', '')),
                role=s.get('role', 'server'),
                evidence=[_build_evidence_item(rel_path, EvidenceType.SERVICE_CREATION, s.get('line_start'), s.get('line_end'))]
            ) for s in pnode.services]

            acts = [ActionInfo(
                name=a.get('action', ''),
                action_type=str(a.get('action_type', '')),
                role=a.get('role', 'server'),
                evidence=[_build_evidence_item(rel_path, EvidenceType.ACTION_CREATION, a.get('line_start'), a.get('line_end'))]
            ) for a in pnode.actions]

            # Classification
            if is_test:
                entity_type = EntityType.TEST_NODE
                node_category = NodeCategory.TEST
            elif pnode.class_name == "BasicNavigator" or "simple_commander" in pkg_name:
                entity_type = EntityType.CLIENT_APP
                node_category = NodeCategory.CLIENT
            elif pnode.is_lifecycle:
                entity_type = EntityType.LIFECYCLE_NODE
                node_category = NodeCategory.UNKNOWN
            else:
                entity_type = EntityType.ROS_NODE
                node_category = NodeCategory.UNKNOWN

            res_status = ResolutionStatus.RESOLVED if pnode.node_name else ResolutionStatus.PARTIAL

            # Match executable from setup.py console_scripts if available
            py_executable = None
            stem = Path(rel_path).stem
            for exe_name, target_ep in console_scripts_by_pkg.get(pkg_name, {}).items():
                mod_part = target_ep.split(":")[0]
                if mod_part.endswith(f".{stem}") or mod_part == stem:
                    py_executable = exe_name
                    break

            raw_python_nodes.append(ROS2Node(
                id="",  # will be assigned uniquely below
                name=pnode.node_name,
                fully_qualified_name=f"{pnode.namespace}/{pnode.node_name}".replace('//', '/') if pnode.namespace and pnode.node_name else (pnode.node_name or ""),
                class_name=pnode.class_name,
                source_file=rel_path,
                package_name=pkg_name,
                namespace=pnode.namespace,
                entity_type=entity_type,
                node_category=node_category,
                resolution_status=res_status,
                source_language="python",
                is_test=is_test,
                is_lifecycle=pnode.is_lifecycle,
                executable=py_executable,
                publishers=pubs,
                subscribers=subs,
                services=srvs,
                actions=acts,
                docstring=pnode.docstring,
                evidence=evidence,
                validation_status=ValidationStatus.SUPPORTED if evidence else ValidationStatus.UNKNOWN
            ))

    # Convert C++ nodes to schema and correlate with CMake
    raw_cpp_nodes: List[ROS2Node] = []
    for pkg_name, cnodes in parsed_cpp_by_pkg.items():
        cmake_info = cmake_info_by_pkg.get(pkg_name, PackageCMakeInfo(pkg_name, Path()))

        for cnode in cnodes:
            # Correlate with CMake executables via target source, linked libraries, or components
            matched_exec_info = cmake_info.find_executable_for_source_or_class(
                cnode.source_file, cnode.class_name, cnode.fully_qualified_class
            )
            matched_exec = matched_exec_info.name if matched_exec_info else None
            if matched_exec_info and matched_exec_info.cmake_file:
                cnode.evidence.append(EvidenceItem(
                    file=matched_exec_info.cmake_file,
                    line_start=matched_exec_info.line_number,
                    evidence_type=EvidenceType.CMAKE_TARGET,
                    source="build_analyzer",
                    confidence=1.0,
                    explanation=f"Mapped CMake executable target '{matched_exec}'"
                ))

            # Correlate with CMake component registrations
            matched_comp = cnode.component_name
            is_comp = cnode.is_component
            for comp in cmake_info.components:
                if comp.class_name in (cnode.fully_qualified_class, cnode.class_name) or \
                   comp.class_name.endswith(f"::{cnode.class_name}"):
                    is_comp = True
                    matched_comp = comp.class_name
                    cnode.evidence.append(EvidenceItem(
                        file=comp.cmake_file,
                        line_start=comp.line_number,
                        evidence_type=EvidenceType.COMPONENT_REGISTRATION,
                        source="build_analyzer",
                        confidence=1.0,
                        explanation=f"CMake component registration: rclcpp_components_register_nodes({comp.library_name} \"{comp.class_name}\")"
                    ))
                    break

            # Classification
            if cnode.is_test:
                entity_type = EntityType.TEST_NODE
                node_category = NodeCategory.TEST
            elif cnode.is_lifecycle:
                entity_type = EntityType.LIFECYCLE_NODE
                node_category = _classify_node_category(pkg_name, cnode.class_name, False)
            elif is_comp:
                entity_type = EntityType.COMPONENT
                node_category = _classify_node_category(pkg_name, cnode.class_name, False)
            elif matched_exec:
                entity_type = EntityType.EXECUTABLE
                node_category = _classify_node_category(pkg_name, cnode.class_name, False)
            else:
                entity_type = EntityType.ROS_NODE
                node_category = _classify_node_category(pkg_name, cnode.class_name, False)

            # Resolution status
            if cnode.node_name and (matched_exec or is_comp):
                res_status = ResolutionStatus.RESOLVED
            elif cnode.node_name or matched_exec:
                res_status = ResolutionStatus.PARTIAL
            else:
                res_status = ResolutionStatus.UNRESOLVED

            raw_cpp_nodes.append(ROS2Node(
                id="",  # will be assigned uniquely below
                name=cnode.node_name,
                fully_qualified_name=f"{cnode.namespace}/{cnode.node_name}".replace('//', '/') if cnode.namespace and cnode.node_name else (cnode.node_name or ""),
                class_name=cnode.fully_qualified_class,
                source_file=cnode.source_file,
                package_name=pkg_name,
                namespace=cnode.namespace,
                entity_type=entity_type,
                node_category=node_category,
                resolution_status=res_status,
                source_language="cpp",
                is_test=cnode.is_test,
                is_lifecycle=cnode.is_lifecycle,
                is_abstract=cnode.is_abstract,
                base_class=cnode.base_class,
                executable=matched_exec,
                component_registered=is_comp,
                component_name=matched_comp,
                evidence=cnode.evidence,
                validation_status=ValidationStatus.SUPPORTED if cnode.evidence else ValidationStatus.UNKNOWN
            ))

    # Combine all discovered nodes
    combined = raw_python_nodes + raw_cpp_nodes

    # Assign stable unique IDs: package::ClassName with file qualifier if duplicated
    def _compute_canonical_base_id(node: ROS2Node) -> str:
        if node.class_name.startswith(f"{node.package_name}::"):
            return node.class_name
        return f"{node.package_name}::{node.class_name}"

    id_counts = Counter(_compute_canonical_base_id(n) for n in combined)

    for node in combined:
        base_id = _compute_canonical_base_id(node)
        if id_counts[base_id] > 1:
            # Use unique path relative to package
            rel_clean = node.source_file.replace("\\", "/")
            if rel_clean.startswith(f"{node.package_name}/"):
                rel_clean = rel_clean[len(node.package_name) + 1:]
            for ext in (".py", ".cpp", ".hpp", ".h", ".cc"):
                if rel_clean.endswith(ext):
                    rel_clean = rel_clean[:-len(ext)]
            slug = rel_clean.replace("/", "__")
            node.id = f"{base_id}#{slug}"
        else:
            node.id = base_id

    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    import json
    output_data = [node.model_dump() for node in combined]
    output_path.write_text(json.dumps(output_data, indent=2))

    total_count = len(combined)
    prod_count = sum(1 for n in combined if not n.is_test)
    test_count = sum(1 for n in combined if n.is_test)
    cpp_count = sum(1 for n in combined if n.source_language == "cpp")
    py_count = sum(1 for n in combined if n.source_language == "python")
    with_ev = sum(1 for n in combined if n.evidence)

    logger.info(
        f"Phase 1 Node Analysis Complete: Discovered {total_count} nodes "
        f"({prod_count} production, {test_count} test | {cpp_count} C++, {py_count} Python | {with_ev} with evidence). "
        f"Saved to {output_path}"
    )

    return combined


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    repo_p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("case_studies/nav2")
    out_p = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output/nodes.json")

    results = run_node_analysis(repo_p, out_p)
    print(f"\nDiscovered {len(results)} nodes:")
    for n in results[:15]:
        print(f"  [{n.entity_type.value}] {n.id} | Name: '{n.name}' | Exec: {n.executable} | Lang: {n.source_language} | Test: {n.is_test}")
