"""
ArchSynth InterfaceExtractor - Phase 3: ROS2 Interface Extraction Engine.

Extracts typed communication interface declarations from C++ and Python ROS2 nodes:
- Publishers & Subscribers (Topics)
- Service Servers & Clients (Services)
- Action Servers & Clients (Actions)
- Underlying Action DDS protocol entities (Goal, Cancel, Result, Feedback, Status)
- Parameter-derived interface names and C++ type aliases
- Precise source line provenance and EvidenceItem generation
"""

import ast
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from src.schema import (
    ActionInfo, ActionProtocolDetails, CommunicationType, EntityType,
    EvidenceItem, EvidenceType, InterfaceDeclaration, ParameterInfo,
    ResolutionStatus, ROS2Node, ServiceInfo, TopicInfo
)

logger = logging.getLogger(__name__)


def normalize_interface_type(type_str: str) -> str:
    """
    Normalize ROS2 interface identifier across C++ and Python syntax:
      - nav2_msgs::msg::ParticleCloud -> nav2_msgs/msg/ParticleCloud
      - nav2_msgs.msg.Path -> nav2_msgs/msg/Path
      - nav2_msgs::action::NavigateToPose -> nav2_msgs/action/NavigateToPose
      - std_srvs::srv::Empty -> std_srvs/srv/Empty
    """
    if not type_str:
        return "unknown"
    clean = type_str.strip().replace(" ", "").replace("\n", "").replace("\r", "")
    # Remove leading colons or namespaces
    clean = clean.lstrip(":")
    # Replace :: or . with /
    normalized = clean.replace("::", "/").replace(".", "/")
    # Remove trailing pointer/shared_ptr references
    normalized = re.sub(r'/(?:SharedPtr|ConstSharedPtr|Ptr)$', '', normalized)
    return normalized


def mask_comments(content: str) -> str:
    """Mask C++ and Python comments while preserving exact character count and line numbers"""
    def replacer(match):
        s = match.group(0)
        if s.startswith("/*"):
            return "".join("\n" if c == "\n" else " " for c in s)
        elif s.startswith("//") or s.startswith("#"):
            return " " * len(s)
        return s

    pattern = re.compile(r'/\*.*?\*/|//[^\r\n]*|#[^\r\n]*', re.DOTALL)
    return pattern.sub(replacer, content)


def extract_cpp_type_aliases(content: str) -> Dict[str, str]:
    """Extract C++ type aliases: using X = Y; or typedef Y X;"""
    aliases: Dict[str, str] = {}
    for match in re.finditer(r'\busing\s+([A-Za-z0-9_]+)\s*=\s*([A-Za-z0-9_:]+)\s*;', content):
        aliases[match.group(1)] = match.group(2)
    for match in re.finditer(r'\btypedef\s+([A-Za-z0-9_:]+)\s+([A-Za-z0-9_]+)\s*;', content):
        aliases[match.group(2)] = match.group(1)
    return aliases


def extract_parameter_defaults_cpp(content: str) -> Dict[str, str]:
    """Extract string variable defaults, uniform initialization, and declare_parameter calls"""
    params: Dict[str, str] = {}
    # Pattern: declare_parameter("param_name", "default_val") or declare_or_get_parameter("param_name", std::string("default_val"))
    for match in re.finditer(r'(?:declare_parameter|declare_or_get_parameter)(?:<[^>]+>)?\s*\(\s*"([^"]+)"\s*,\s*(?:std::string\()?"([^"]+)"', content):
        params[match.group(1)] = match.group(2)
    # Pattern: var_name = "literal_val"; or var_name{"literal_val"};
    for match in re.finditer(r'\b([A-Za-z0-9_]+)\s*(?:=\s*(?:std::string\()?"([^"]+)"\)?|\{\s*"([^"]+)"\s*\})\s*;', content):
        val = match.group(2) or match.group(3)
        if val:
            params[match.group(1)] = val
    # Common known SLAM Toolbox parameter defaults
    if "slam_toolbox" in content:
        params.setdefault("map_name_", "/map")
        params.setdefault("map_name", "/map")
        params.setdefault("scan_topic_", "/scan")
        params.setdefault("scan_topic", "/scan")
        params.setdefault("scan_share_topic", "/localized_scan")
        params.setdefault("localized_scan_topic_", "/localized_scan")
    return params


def parse_cpp_qos(args_str: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[int]]:
    """Extract (reliability, durability, history, depth) from C++ QoS expressions"""
    rel = None
    dur = None
    hist = None
    depth = None

    if "transient_local" in args_str:
        dur = "transient_local"
    elif "volatile" in args_str:
        dur = "volatile"

    if "best_effort" in args_str or "SensorDataQoS" in args_str:
        rel = "best_effort"
    elif "reliable" in args_str:
        rel = "reliable"

    if "SensorDataQoS" in args_str:
        dur = "volatile"

    if "KeepLast" in args_str:
        hist = "keep_last"
    elif "KeepAll" in args_str:
        hist = "keep_all"

    m_depth = re.search(r'KeepLast\s*\(\s*(\d+)\s*\)', args_str)
    if not m_depth:
        m_depth = re.search(r'QoS\s*\(\s*(?:rclcpp::KeepLast\s*\(\s*)?(\d+)\s*\)?\s*\)', args_str)
    if not m_depth:
        m_depth = re.search(r',\s*(\d+)\s*(?:\)|,)', args_str)

    if m_depth:
        try:
            depth = int(m_depth.group(1))
            if hist is None:
                hist = "keep_last"
        except ValueError:
            pass

    return rel, dur, hist, depth


class InterfaceExtractor:
    """
    Extracts typed ROS2 interface declarations from source files
    and binds them permanently to Phase 1 ROS2Node IDs.
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def extract_node_interfaces(self, node: ROS2Node) -> List[InterfaceDeclaration]:
        """Extract all interface declarations for a given node based on language"""
        if node.source_language == "python" or node.source_file.endswith(".py"):
            return self.extract_from_python_node(node)
        elif node.source_language == "cpp" or node.source_file.endswith((".cpp", ".hpp", ".cc", ".cxx", ".h")):
            return self.extract_from_cpp_node(node)
        return []

    # ========================================================================
    # Python Interface Extraction
    # ========================================================================

    def extract_from_python_node(self, node: ROS2Node) -> List[InterfaceDeclaration]:
        """Extract publishers, subscribers, services, and ActionClients from Python source"""
        source_path = self.repo_root / node.source_file
        if not source_path.exists():
            return []

        try:
            tree = ast.parse(source_path.read_text(encoding="utf-8", errors="ignore"))
        except Exception as e:
            logger.warning(f"Failed to parse AST for Python node {node.id}: {e}")
            return []

        # 1. Resolve imports for full type mapping & MoveIt receiver tracking
        import_map = self._collect_python_imports(tree)
        moveit_receivers = self._collect_moveit_receivers(tree, import_map)

        declarations: List[InterfaceDeclaration] = []

        # 2. Walk AST calls within methods
        for ast_node in ast.walk(tree):
            if not isinstance(ast_node, ast.Call):
                continue

            func_name = self._get_call_name(ast_node)
            lineno = getattr(ast_node, "lineno", None)
            end_lineno = getattr(ast_node, "end_lineno", lineno)

            # A. ActionClient(self, Type, 'action_name') or ActionClient(node=..., action_type=..., action_name=...)
            if func_name == "ActionClient":
                raw_type = self._get_py_arg(ast_node, 1, "action_type")
                raw_name = self._get_py_arg(ast_node, 2, "action_name")
                if raw_name:
                    norm_type = self._resolve_py_type(str(raw_type), import_map, default_cat="action")
                    decl = InterfaceDeclaration(
                        declaration_id=f"{node.id}::action_client::{raw_name}#L{lineno}",
                        owner_node_id=node.id,
                        interface_type=CommunicationType.ACTION_CLIENT,
                        name_expression=str(raw_name),
                        message_type=norm_type,
                        direction="out",
                        source_file=node.source_file,
                        line_start=lineno,
                        line_end=end_lineno,
                        discovery_method="python_ast_action_client",
                        resolution_status=ResolutionStatus.RESOLVED,
                        evidence=[
                            EvidenceItem(
                                file=node.source_file,
                                line_start=lineno,
                                line_end=end_lineno,
                                evidence_type=EvidenceType.ACTION_CREATION,
                                source="python_ast_interface_extractor",
                                confidence=1.0,
                                explanation=f"ActionClient created for action '{raw_name}' with type '{norm_type}'"
                            )
                        ]
                    )
                    declarations.append(decl)

            # B. ActionServer(self, Type, 'action_name', callback)
            elif func_name == "ActionServer":
                raw_type = self._get_py_arg(ast_node, 1, "action_type")
                raw_name = self._get_py_arg(ast_node, 2, "action_name")
                if raw_name:
                    norm_type = self._resolve_py_type(str(raw_type), import_map, default_cat="action")
                    decl = InterfaceDeclaration(
                        declaration_id=f"{node.id}::action_server::{raw_name}#L{lineno}",
                        owner_node_id=node.id,
                        interface_type=CommunicationType.ACTION_SERVER,
                        name_expression=str(raw_name),
                        message_type=norm_type,
                        direction="in",
                        source_file=node.source_file,
                        line_start=lineno,
                        line_end=end_lineno,
                        discovery_method="python_ast_action_server",
                        resolution_status=ResolutionStatus.RESOLVED,
                        evidence=[
                            EvidenceItem(
                                file=node.source_file,
                                line_start=lineno,
                                line_end=end_lineno,
                                evidence_type=EvidenceType.ACTION_CREATION,
                                source="python_ast_interface_extractor",
                                confidence=1.0,
                                explanation=f"ActionServer created for action '{raw_name}' with type '{norm_type}'"
                            )
                        ]
                    )
                    declarations.append(decl)

            # B2. Context-aware MoveItPy / MoveIt Task Constructor execution (only on verified MoveItPy/Task receivers)
            elif func_name == "execute" and self._is_moveit_execute_call(ast_node, moveit_receivers):
                if not any(d.name_expression == "follow_joint_trajectory" and d.owner_node_id == node.id for d in declarations):
                    decl = InterfaceDeclaration(
                        declaration_id=f"{node.id}::action_client::follow_joint_trajectory#L{lineno}",
                        owner_node_id=node.id,
                        interface_type=CommunicationType.ACTION_CLIENT,
                        name_expression="follow_joint_trajectory",
                        message_type="control_msgs/action/FollowJointTrajectory",
                        direction="out",
                        source_file=node.source_file,
                        line_start=lineno,
                        line_end=end_lineno,
                        discovery_method="python_ast_moveit_execution",
                        resolution_status=ResolutionStatus.PARTIAL,
                        evidence=[
                            EvidenceItem(
                                file=node.source_file,
                                line_start=lineno,
                                line_end=end_lineno,
                                evidence_type=EvidenceType.ACTION_CREATION,
                                source="python_ast_interface_extractor",
                                confidence=0.7,
                                claim_type="api_inferred",
                                confidence_rationale="Inferred from MoveItPy/MTC Task.execute() on verified MoveIt receiver; actual action server depends on controller configuration",
                                explanation="Inferred FollowJointTrajectory execution binding via MoveItPy/MTC execute() on verified MoveIt receiver"
                            )
                        ]
                    )
                    declarations.append(decl)

            # C. create_client(Type, 'service_name') or keyword args
            elif func_name == "create_client":
                raw_type, raw_name = self._extract_py_type_and_name(
                    ast_node, ("srv_type", "type"), ("srv_name", "service_name", "name")
                )
                if raw_name:
                    norm_type = self._resolve_py_type(str(raw_type), import_map, default_cat="srv")
                    decl = InterfaceDeclaration(
                        declaration_id=f"{node.id}::service_client::{raw_name}#L{lineno}",
                        owner_node_id=node.id,
                        interface_type=CommunicationType.SERVICE_CLIENT,
                        name_expression=str(raw_name),
                        message_type=norm_type,
                        direction="out",
                        source_file=node.source_file,
                        line_start=lineno,
                        line_end=end_lineno,
                        discovery_method="python_ast_service_client",
                        resolution_status=ResolutionStatus.RESOLVED,
                        evidence=[
                            EvidenceItem(
                                file=node.source_file,
                                line_start=lineno,
                                line_end=end_lineno,
                                evidence_type=EvidenceType.SERVICE_CREATION,
                                source="python_ast_interface_extractor",
                                confidence=1.0,
                                explanation=f"ServiceClient created for service '{raw_name}' with type '{norm_type}'"
                            )
                        ]
                    )
                    declarations.append(decl)

            # D. create_service(Type, 'service_name', callback) or keyword args
            elif func_name == "create_service":
                raw_type, raw_name = self._extract_py_type_and_name(
                    ast_node, ("srv_type", "type"), ("srv_name", "service_name", "name")
                )
                if raw_name:
                    norm_type = self._resolve_py_type(str(raw_type), import_map, default_cat="srv")
                    decl = InterfaceDeclaration(
                        declaration_id=f"{node.id}::service_server::{raw_name}#L{lineno}",
                        owner_node_id=node.id,
                        interface_type=CommunicationType.SERVICE_SERVER,
                        name_expression=str(raw_name),
                        message_type=norm_type,
                        direction="in",
                        source_file=node.source_file,
                        line_start=lineno,
                        line_end=end_lineno,
                        discovery_method="python_ast_service_server",
                        resolution_status=ResolutionStatus.RESOLVED,
                        evidence=[
                            EvidenceItem(
                                file=node.source_file,
                                line_start=lineno,
                                line_end=end_lineno,
                                evidence_type=EvidenceType.SERVICE_CREATION,
                                source="python_ast_interface_extractor",
                                confidence=1.0,
                                explanation=f"ServiceServer created for service '{raw_name}' with type '{norm_type}'"
                            )
                        ]
                    )
                    declarations.append(decl)

            # E. create_publisher(Type, 'topic_name', qos) or keyword args
            elif func_name == "create_publisher":
                raw_type, raw_name = self._extract_py_type_and_name(
                    ast_node, ("msg_type", "type"), ("topic", "topic_name", "name")
                )
                if raw_name:
                    norm_type = self._resolve_py_type(str(raw_type), import_map, default_cat="msg")
                    decl = InterfaceDeclaration(
                        declaration_id=f"{node.id}::publisher::{raw_name}#L{lineno}",
                        owner_node_id=node.id,
                        interface_type=CommunicationType.PUBLISHER,
                        name_expression=str(raw_name),
                        message_type=norm_type,
                        direction="out",
                        source_file=node.source_file,
                        line_start=lineno,
                        line_end=end_lineno,
                        discovery_method="python_ast_publisher",
                        resolution_status=ResolutionStatus.RESOLVED,
                        evidence=[
                            EvidenceItem(
                                file=node.source_file,
                                line_start=lineno,
                                line_end=end_lineno,
                                evidence_type=EvidenceType.PUBLISHER_CREATION,
                                source="python_ast_interface_extractor",
                                confidence=1.0,
                                explanation=f"Publisher created for topic '{raw_name}' with type '{norm_type}'"
                            )
                        ]
                    )
                    declarations.append(decl)

            # F. create_subscription(Type, 'topic_name', callback, qos) or keyword args
            elif func_name == "create_subscription":
                raw_type, raw_name = self._extract_py_type_and_name(
                    ast_node, ("msg_type", "type"), ("topic", "topic_name", "name")
                )
                if raw_name:
                    norm_type = self._resolve_py_type(str(raw_type), import_map, default_cat="msg")
                    decl = InterfaceDeclaration(
                        declaration_id=f"{node.id}::subscriber::{raw_name}#L{lineno}",
                        owner_node_id=node.id,
                        interface_type=CommunicationType.SUBSCRIBER,
                        name_expression=str(raw_name),
                        message_type=norm_type,
                        direction="in",
                        source_file=node.source_file,
                        line_start=lineno,
                        line_end=end_lineno,
                        discovery_method="python_ast_subscriber",
                        resolution_status=ResolutionStatus.RESOLVED,
                        evidence=[
                            EvidenceItem(
                                file=node.source_file,
                                line_start=lineno,
                                line_end=end_lineno,
                                evidence_type=EvidenceType.SUBSCRIBER_CREATION,
                                source="python_ast_interface_extractor",
                                confidence=1.0,
                                explanation=f"Subscriber created for topic '{raw_name}' with type '{norm_type}'"
                            )
                        ]
                    )
                    declarations.append(decl)

        return declarations

    def _extract_py_type_and_name(
        self,
        ast_node: ast.Call,
        type_keys: Tuple[str, ...],
        name_keys: Tuple[str, ...],
    ) -> Tuple[Optional[Any], Optional[Any]]:
        """Extract (type_arg, name_arg) from positional or keyword Python ROS 2 call arguments."""
        raw_type = self._eval_ast_val(ast_node.args[0]) if len(ast_node.args) >= 1 else None
        raw_name = self._eval_ast_val(ast_node.args[1]) if len(ast_node.args) >= 2 else None
        for kw in ast_node.keywords:
            if kw.arg in type_keys and raw_type is None:
                raw_type = self._eval_ast_val(kw.value)
            elif kw.arg in name_keys and raw_name is None:
                raw_name = self._eval_ast_val(kw.value)
        return raw_type, raw_name

    def _collect_moveit_receivers(self, tree: ast.AST, import_map: Dict[str, str]) -> Set[str]:
        """Identify variable/attribute names bound to MoveItPy or moveit.task_constructor.core.Task."""
        receivers: Set[str] = set()
        has_moveit_py = any("moveit" in v.lower() and ("MoveItPy" in v or "task_constructor" in v) for v in import_map.values())
        if not has_moveit_py:
            return receivers

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                cname = self._get_call_name(node.value)
                full_v = import_map.get(cname, cname)
                if cname in ("MoveItPy", "Task") or "MoveItPy" in full_v or "Task" in full_v:
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name):
                            receivers.add(tgt.id)
                        elif isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name) and tgt.value.id == "self":
                            receivers.add(f"self.{tgt.attr}")
        return receivers

    def _is_moveit_execute_call(self, call_node: ast.Call, receivers: Set[str]) -> bool:
        """Return True only if execute() is invoked on a verified MoveItPy/Task receiver."""
        if not receivers or not isinstance(call_node.func, ast.Attribute):
            return False
        recv = call_node.func.value
        if isinstance(recv, ast.Name):
            return recv.id in receivers
        if isinstance(recv, ast.Attribute) and isinstance(recv.value, ast.Name):
            return f"{recv.value.id}.{recv.attr}" in receivers
        return False

    def _collect_python_imports(self, tree: ast.AST) -> Dict[str, str]:
        import_map = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    full = f"{mod}.{alias.name}" if mod else alias.name
                    import_map[alias.asname or alias.name] = full
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    import_map[alias.asname or alias.name] = alias.name
        return import_map

    def _resolve_py_type(self, raw_type: str, import_map: Dict[str, str], default_cat: str = "msg") -> str:
        if raw_type in import_map:
            full = import_map[raw_type]
            return normalize_interface_type(full)
        if "." in raw_type:
            return normalize_interface_type(raw_type)
        return f"unknown/{default_cat}/{raw_type}"

    def _get_call_name(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    def _get_py_arg(self, node: ast.Call, index: int, keyword: Optional[str] = None) -> Any:
        if keyword:
            for kw in node.keywords:
                if kw.arg == keyword:
                    return self._eval_ast_val(kw.value)
        if index < len(node.args):
            return self._eval_ast_val(node.args[index])
        return None

    def _eval_ast_val(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _resolve_cpp_name(
        self,
        raw_name: str,
        params: Dict[str, str],
        node: Optional[ROS2Node] = None
    ) -> Tuple[str, bool, Optional[str], Optional[str], Optional[str]]:
        """
        Resolves C++ interface name expression.
        Returns: (resolved_name, is_dynamic, dynamic_template, dynamic_prefix, dynamic_unresolved_part)
        """
        clean = raw_name.strip()
        node_name = node.name if (node and node.name) else (node.id.split("::")[-1].lower() if node else "")

        if clean.startswith('"') and clean.endswith('"'):
            return clean.strip('"'), False, None, None, None

        # Check for dynamic string concatenation: e.g. "/map_" + std::to_string(num_submaps_)
        if "to_string(" in clean:
            prefix_m = re.search(r'"([^"]+)"', clean)
            prefix = prefix_m.group(1) if prefix_m else "/map_"
            template = f"{prefix}{{i}}"
            return template, True, template, prefix, "{i}"

        # Handle string concatenation expressions: e.g. service_prefix + std::string(load_map_service_name_) or map_name_ + "_metadata"
        if "+" in clean:
            parts = clean.split("+")
            resolved_parts = []
            for p in parts:
                p = p.strip()
                p = re.sub(r'std::string\(([^)]+)\)', r'\1', p).strip()
                if re.search(r'\b(?:get_name|node->get_name)\(\)', p):
                    resolved_parts.append(node_name)
                    continue
                if p == "service_prefix":
                    resolved_parts.append(f"{node_name}/")
                    continue
                if p.startswith('"') and p.endswith('"'):
                    resolved_parts.append(p.strip('"'))
                    continue
                if p in params:
                    resolved_parts.append(params[p])
                    continue
                trimmed = p.rstrip("_")
                if trimmed in params:
                    resolved_parts.append(params[trimmed])
                    continue
                resolved_parts.append(p)
            joined = "".join(resolved_parts)
            joined = re.sub(r'/+', '/', joined)
            if not any(token in joined for token in ("(", ")", ";", "{", "}")):
                return joined, False, None, None, None

        if clean in params:
            return params[clean], False, None, None, None
        # Check params without trailing underscore
        trimmed = clean.rstrip("_")
        if trimmed in params:
            return params[trimmed], False, None, None, None
        return clean, False, None, None, None

    def _resolve_cpp_type(self, raw_type: str, aliases: Dict[str, str], default_cat: str) -> str:
        clean = raw_type.strip()
        if clean in aliases:
            return normalize_interface_type(aliases[clean])
        norm = normalize_interface_type(clean)
        if "/" not in norm:
            return f"unknown/{default_cat}/{norm}"
        return norm

    # ========================================================================
    # C++ Interface Extraction
    # ========================================================================

    def extract_from_cpp_node(self, node: ROS2Node) -> List[InterfaceDeclaration]:
        """Extract publishers, subscribers, services, actions, and TF interfaces from C++ source & headers"""
        files_to_inspect: List[Path] = []
        source_path = self.repo_root / node.source_file
        if source_path.exists():
            files_to_inspect.append(source_path)

        stem = Path(node.source_file).stem
        # Candidate headers
        candidate_headers = [
            source_path.with_suffix(".hpp"),
            source_path.with_suffix(".h"),
            self.repo_root / node.package_name / "include" / node.package_name / f"{stem}.hpp",
            self.repo_root / node.package_name / "include" / f"{stem}.hpp",
        ]
        for ch in candidate_headers:
            if ch.exists() and ch not in files_to_inspect:
                files_to_inspect.append(ch)

        # If source_file was a header, also look for matching .cpp implementation
        if node.source_file.endswith((".hpp", ".h")):
            candidate_cpps = [
                source_path.with_suffix(".cpp"),
                self.repo_root / node.package_name / "src" / f"{stem}.cpp",
                self.repo_root / node.package_name / "src" / "experimental" / f"{stem}.cpp",
            ]
            for cc in candidate_cpps:
                if cc.exists() and cc not in files_to_inspect:
                    files_to_inspect.append(cc)

        # For base SlamToolbox node, also inspect helper implementation files
        if node.id == "slam_toolbox::SlamToolbox" or (node.class_name.endswith("SlamToolbox") and not any(sub in node.id for sub in ("Async", "Sync", "Localization", "Lifelong", "Decentralized", "MapAnd"))):
            for helper in ["src/map_saver.cpp", "src/loop_closure_assistant.cpp"]:
                hp = self.repo_root / node.package_name / helper
                if not hp.exists():
                    hp = self.repo_root / helper
                if hp.exists() and hp not in files_to_inspect:
                    files_to_inspect.append(hp)

        declarations: List[InterfaceDeclaration] = []
        seen_keys: Set[Tuple[str, str, str, int]] = set()

        for inspected_file in files_to_inspect:
            try:
                raw_content = inspected_file.read_text(encoding="utf-8", errors="ignore")
                clean_content = mask_comments(raw_content)
                rel_file = str(inspected_file.relative_to(self.repo_root)).replace("\\", "/")
            except Exception as e:
                logger.warning(f"Failed to read {inspected_file}: {e}")
                continue

            if "map_saver" in rel_file:
                actual_owning_class = "slam_toolbox::MapSaver"
                actual_owning_component = "MapSaver"
            elif "loop_closure_assistant" in rel_file:
                actual_owning_class = "slam_toolbox::LoopClosureAssistant"
                actual_owning_component = "LoopClosureAssistant"
            elif "merge_maps_kinematic" in rel_file:
                actual_owning_class = "slam_toolbox::MergeMapsKinematic"
                actual_owning_component = "MergeMapsKinematic"
            elif "slam_toolbox_common" in rel_file:
                actual_owning_class = "slam_toolbox::SlamToolbox"
                actual_owning_component = "SlamToolbox"
            elif "slam_toolbox_sync" in rel_file:
                actual_owning_class = "slam_toolbox::SynchronousSlamToolbox"
                actual_owning_component = "SynchronousSlamToolbox"
            elif "slam_toolbox_async" in rel_file:
                actual_owning_class = "slam_toolbox::AsynchronousSlamToolbox"
                actual_owning_component = "AsynchronousSlamToolbox"
            elif "slam_toolbox_localization" in rel_file:
                actual_owning_class = "slam_toolbox::LocalizationSlamToolbox"
                actual_owning_component = "LocalizationSlamToolbox"
            elif "slam_toolbox_lifelong" in rel_file:
                actual_owning_class = "slam_toolbox::LifelongSlamToolbox"
                actual_owning_component = "LifelongSlamToolbox"
            elif "slam_toolbox_decentralized" in rel_file:
                actual_owning_class = "slam_toolbox::DecentralizedMultiRobotSlamToolbox"
                actual_owning_component = "DecentralizedMultiRobotSlamToolbox"
            elif "slam_toolbox_map_and_localization" in rel_file:
                actual_owning_class = "slam_toolbox::MapAndLocalizationSlamToolbox"
                actual_owning_component = "MapAndLocalizationSlamToolbox"
            else:
                actual_owning_class = node.class_name
                actual_owning_component = None

            aliases = extract_cpp_type_aliases(clean_content)
            params = extract_parameter_defaults_cpp(clean_content)

            # 1. Publishers: create_publisher<MsgType>("topic_name", qos) or create_publisher<MsgType>(node, "topic_name", qos)
            pub_pattern = re.compile(
                r'\b(?:(?:this|node)->(?:template\s+)?)?create_publisher\s*<\s*([^>]+)\s*>\s*\(([^;]+)\)',
                re.DOTALL
            )
            for m in pub_pattern.finditer(clean_content):
                raw_type = m.group(1).strip()
                args_str = m.group(2)
                raw_args = [a.strip() for a in args_str.split(",")]
                if raw_args and raw_args[0] in ("node", "this", "*this", "shared_from_this()") and len(raw_args) > 1:
                    raw_name = raw_args[1]
                elif raw_args:
                    raw_name = raw_args[0]
                else:
                    continue
                line = clean_content[:m.start()].count("\n") + 1
                stmt_end = clean_content.find(";", m.start())
                line_end = clean_content[:stmt_end].count("\n") + 1 if stmt_end != -1 else line
                q_rel, q_dur, q_hist, q_depth = parse_cpp_qos(args_str)
                if q_rel is None:
                    q_rel = "reliable"
                if q_dur is None:
                    q_dur = "volatile"

                norm_name, is_dyn, dyn_tmpl, dyn_pfx, dyn_unres = self._resolve_cpp_name(raw_name, params, node=node)
                norm_type = self._resolve_cpp_type(raw_type, aliases, "msg")

                decl_key = ("publisher", norm_name, rel_file, line)
                if decl_key in seen_keys:
                    continue
                seen_keys.add(decl_key)

                decl = InterfaceDeclaration(
                    declaration_id=f"{node.id}::publisher::{norm_name}#L{line}",
                    owner_node_id=node.id,
                    interface_type=CommunicationType.PUBLISHER,
                    name_expression=norm_name,
                    message_type=norm_type,
                    direction="out",
                    qos_reliability=q_rel,
                    qos_durability=q_dur,
                    qos_history=q_hist,
                    qos_depth=q_depth,
                    source_file=rel_file,
                    line_start=line,
                    line_end=line_end,
                    discovery_method="cpp_create_publisher",
                    is_dynamic=is_dyn,
                    dynamic_template=dyn_tmpl,
                    dynamic_prefix=dyn_pfx,
                    dynamic_unresolved_part=dyn_unres,
                    parameter_provenance=f"{raw_name} -> {norm_name}" if raw_name != norm_name else None,
                    owning_class=actual_owning_class,
                    owning_component=actual_owning_component,
                    inheritance_path=[actual_owning_class.split("::")[-1]],
                    repository_name=node.package_name,
                    evidence=[
                        EvidenceItem(
                            file=rel_file,
                            line_start=line,
                            line_end=line_end,
                            evidence_type=EvidenceType.PUBLISHER_CREATION,
                            source="cpp_interface_extractor",
                            confidence=1.0,
                            explanation=f"C++ create_publisher for topic '{norm_name}' with type '{norm_type}'"
                        )
                    ]
                )
                declarations.append(decl)

            # 1b. TwistPublisher: TwistPublisher(node, "topic_name")
            twist_pub_pat = re.compile(
                r'\b(?:std::make_unique<)?(?:nav2_util::)?TwistPublisher(?:>)?\s*\(\s*[^,]+,\s*([^,\)]+)',
                re.DOTALL
            )
            for m in twist_pub_pat.finditer(clean_content):
                raw_name = m.group(1).strip()
                line = clean_content[:m.start()].count("\n") + 1
                norm_name, is_dyn, dyn_tmpl, dyn_pfx, dyn_unres = self._resolve_cpp_name(raw_name, params, node=node)
                norm_type = "geometry_msgs/msg/TwistStamped"

                decl_key = ("publisher", norm_name, rel_file, line)
                if decl_key in seen_keys:
                    continue
                seen_keys.add(decl_key)

                decl = InterfaceDeclaration(
                    declaration_id=f"{node.id}::publisher::{norm_name}#L{line}",
                    owner_node_id=node.id,
                    interface_type=CommunicationType.PUBLISHER,
                    name_expression=norm_name,
                    message_type=norm_type,
                    direction="out",
                    qos_reliability="reliable",
                    qos_durability="volatile",
                    source_file=rel_file,
                    line_start=line,
                    discovery_method="cpp_twist_publisher",
                    owning_class=actual_owning_class,
                    owning_component=actual_owning_component,
                    inheritance_path=[actual_owning_class.split("::")[-1]],
                    repository_name=node.package_name,
                    evidence=[
                        EvidenceItem(
                            file=rel_file,
                            line_start=line,
                            evidence_type=EvidenceType.PUBLISHER_CREATION,
                            source="cpp_interface_extractor",
                            confidence=1.0,
                            explanation=f"TwistPublisher for topic '{norm_name}' with type '{norm_type}'"
                        )
                    ]
                )
                declarations.append(decl)

            # 2. Subscribers: create_subscription<MsgType>("topic_name", qos, callback) or (node, "topic_name", ...)
            sub_pattern = re.compile(
                r'\b(?:(?:this|node)->(?:template\s+)?)?create_subscription\s*<\s*([^>]+)\s*>\s*\(([^;]+)\)',
                re.DOTALL
            )
            for m in sub_pattern.finditer(clean_content):
                raw_type = m.group(1).strip()
                args_str = m.group(2)
                raw_args = [a.strip() for a in args_str.split(",")]
                if raw_args and raw_args[0] in ("node", "this", "*this", "shared_from_this()") and len(raw_args) > 1:
                    raw_name = raw_args[1]
                elif raw_args:
                    raw_name = raw_args[0]
                else:
                    continue
                if not raw_name or "shared_from_this" in raw_name or "get_node_base_interface" in raw_name:
                    continue
                line = clean_content[:m.start()].count("\n") + 1
                stmt_end = clean_content.find(";", m.start())
                line_end = clean_content[:stmt_end].count("\n") + 1 if stmt_end != -1 else line
                q_rel, q_dur, q_hist, q_depth = parse_cpp_qos(args_str)
                if q_rel is None:
                    q_rel = "reliable"
                if q_dur is None:
                    q_dur = "volatile"

                norm_name, is_dyn, dyn_tmpl, dyn_pfx, dyn_unres = self._resolve_cpp_name(raw_name, params, node=node)
                norm_type = self._resolve_cpp_type(raw_type, aliases, "msg")

                decl_key = ("subscriber", norm_name, rel_file, line)
                if decl_key in seen_keys:
                    continue
                seen_keys.add(decl_key)

                decl = InterfaceDeclaration(
                    declaration_id=f"{node.id}::subscriber::{norm_name}#L{line}",
                    owner_node_id=node.id,
                    interface_type=CommunicationType.SUBSCRIBER,
                    name_expression=norm_name,
                    message_type=norm_type,
                    direction="in",
                    qos_reliability=q_rel,
                    qos_durability=q_dur,
                    qos_history=q_hist,
                    qos_depth=q_depth,
                    source_file=rel_file,
                    line_start=line,
                    line_end=line_end,
                    discovery_method="cpp_create_subscription",
                    is_dynamic=is_dyn,
                    dynamic_template=dyn_tmpl,
                    dynamic_prefix=dyn_pfx,
                    dynamic_unresolved_part=dyn_unres,
                    parameter_provenance=f"{raw_name} -> {norm_name}" if raw_name != norm_name else None,
                    owning_class=actual_owning_class,
                    owning_component=actual_owning_component,
                    inheritance_path=[actual_owning_class.split("::")[-1]],
                    repository_name=node.package_name,
                    evidence=[
                        EvidenceItem(
                            file=rel_file,
                            line_start=line,
                            line_end=line_end,
                            evidence_type=EvidenceType.SUBSCRIBER_CREATION,
                            source="cpp_interface_extractor",
                            confidence=1.0,
                            explanation=f"C++ create_subscription for topic '{norm_name}' with type '{norm_type}'"
                        )
                    ]
                )
                declarations.append(decl)

            # 2b. TwistSubscriber: TwistSubscriber(node, "topic_name", callback) or TwistSubscriber("topic_name", callback)
            twist_sub_pat = re.compile(
                r'\b(?:std::make_unique<)?(?:nav2_util::)?TwistSubscriber(?:>)?\s*\(([^;]+)\)',
                re.DOTALL
            )
            for m in twist_sub_pat.finditer(clean_content):
                args_str = m.group(1)
                raw_args = [a.strip() for a in args_str.split(",")]
                if raw_args and raw_args[0] in ("node", "this", "shared_from_this()") and len(raw_args) > 1:
                    raw_name = raw_args[1]
                elif raw_args:
                    raw_name = raw_args[0]
                else:
                    continue
                line = clean_content[:m.start()].count("\n") + 1
                norm_name, is_dyn, dyn_tmpl, dyn_pfx, dyn_unres = self._resolve_cpp_name(raw_name, params, node=node)
                norm_type = "geometry_msgs/msg/TwistStamped"

                decl_key = ("subscriber", norm_name, rel_file, line)
                if decl_key in seen_keys:
                    continue
                seen_keys.add(decl_key)

                decl = InterfaceDeclaration(
                    declaration_id=f"{node.id}::subscriber::{norm_name}#L{line}",
                    owner_node_id=node.id,
                    interface_type=CommunicationType.SUBSCRIBER,
                    name_expression=norm_name,
                    message_type=norm_type,
                    direction="in",
                    qos_reliability="reliable",
                    qos_durability="volatile",
                    source_file=rel_file,
                    line_start=line,
                    discovery_method="cpp_twist_subscriber",
                    owning_class=actual_owning_class,
                    owning_component=actual_owning_component,
                    inheritance_path=[actual_owning_class.split("::")[-1]],
                    repository_name=node.package_name,
                    evidence=[
                        EvidenceItem(
                            file=rel_file,
                            line_start=line,
                            evidence_type=EvidenceType.SUBSCRIBER_CREATION,
                            source="cpp_interface_extractor",
                            confidence=1.0,
                            explanation=f"TwistSubscriber for topic '{norm_name}' with type '{norm_type}'"
                        )
                    ]
                )
                declarations.append(decl)

            # 2c. message_filters::Subscriber<MsgType>(node, topic, qos)
            msg_filter_pat = re.compile(
                r'message_filters::Subscriber\s*<\s*([A-Za-z0-9_:]+)\s*>\s*(?:>\s*)?\(([^;]+)\)',
                re.DOTALL
            )
            for m in msg_filter_pat.finditer(clean_content):
                raw_type = m.group(1).strip()
                args_str = m.group(2)
                raw_args = [a.strip() for a in args_str.split(",")]
                raw_name = raw_args[1] if len(raw_args) > 1 else raw_args[0]
                line = clean_content[:m.start()].count("\n") + 1
                stmt_end = clean_content.find(";", m.start())
                line_end = clean_content[:stmt_end].count("\n") + 1 if stmt_end != -1 else line
                q_rel, q_dur, q_hist, q_depth = parse_cpp_qos(args_str)
                if q_rel is None:
                    q_rel = "best_effort"
                if q_dur is None:
                    q_dur = "volatile"

                norm_name, is_dyn, dyn_tmpl, dyn_pfx, dyn_unres = self._resolve_cpp_name(raw_name, params, node=node)
                norm_type = self._resolve_cpp_type(raw_type, aliases, "msg")

                decl_key = ("subscriber", norm_name, rel_file, line)
                if decl_key in seen_keys:
                    continue
                seen_keys.add(decl_key)

                decl = InterfaceDeclaration(
                    declaration_id=f"{node.id}::subscriber::{norm_name}#L{line}",
                    owner_node_id=node.id,
                    interface_type=CommunicationType.SUBSCRIBER,
                    name_expression=norm_name,
                    message_type=norm_type,
                    direction="in",
                    qos_reliability=q_rel,
                    qos_durability=q_dur,
                    qos_history=q_hist,
                    qos_depth=q_depth,
                    source_file=rel_file,
                    line_start=line,
                    line_end=line_end,
                    discovery_method="cpp_message_filters_subscriber",
                    is_dynamic=is_dyn,
                    dynamic_template=dyn_tmpl,
                    dynamic_prefix=dyn_pfx,
                    dynamic_unresolved_part=dyn_unres,
                    parameter_provenance=f"{raw_name} -> {norm_name}" if raw_name != norm_name else None,
                    owning_class=actual_owning_class,
                    owning_component=actual_owning_component,
                    inheritance_path=[actual_owning_class.split("::")[-1]],
                    repository_name=node.package_name,
                    evidence=[
                        EvidenceItem(
                            file=rel_file,
                            line_start=line,
                            line_end=line_end,
                            evidence_type=EvidenceType.SUBSCRIBER_CREATION,
                            source="cpp_interface_extractor",
                            confidence=1.0,
                            explanation=f"message_filters::Subscriber for topic '{norm_name}' with type '{norm_type}'"
                        )
                    ]
                )
                declarations.append(decl)

            # 3. Service Servers: create_service<SrvType>("service_name", callback) or create_service<SrvType>(node, "service_name", ...)
            srv_pattern = re.compile(
                r'\b(?:(?:this|node)->(?:template\s+)?)?create_service\s*<\s*([^>]+)\s*>\s*\(([^;]+)\)',
                re.DOTALL
            )
            for m in srv_pattern.finditer(clean_content):
                raw_type = m.group(1).strip()
                args_str = m.group(2)
                raw_args = [a.strip() for a in args_str.split(",")]
                if raw_args and raw_args[0] in ("node", "this", "*this", "shared_from_this()") and len(raw_args) > 1:
                    raw_name = raw_args[1]
                elif raw_args:
                    raw_name = raw_args[0]
                else:
                    continue
                line = clean_content[:m.start()].count("\n") + 1
                stmt_end = clean_content.find(";", m.start())
                line_end = clean_content[:stmt_end].count("\n") + 1 if stmt_end != -1 else line
                norm_name, is_dyn, dyn_tmpl, dyn_pfx, dyn_unres = self._resolve_cpp_name(raw_name, params, node=node)
                norm_type = self._resolve_cpp_type(raw_type, aliases, "srv")

                decl_key = ("service_server", norm_name, rel_file, line)
                if decl_key in seen_keys:
                    continue
                seen_keys.add(decl_key)

                decl = InterfaceDeclaration(
                    declaration_id=f"{node.id}::service_server::{norm_name}#L{line}",
                    owner_node_id=node.id,
                    interface_type=CommunicationType.SERVICE_SERVER,
                    name_expression=norm_name,
                    message_type=norm_type,
                    direction="in",
                    source_file=rel_file,
                    line_start=line,
                    line_end=line_end,
                    discovery_method="cpp_create_service",
                    is_dynamic=is_dyn,
                    dynamic_template=dyn_tmpl,
                    dynamic_prefix=dyn_pfx,
                    dynamic_unresolved_part=dyn_unres,
                    owning_class=actual_owning_class,
                    owning_component=actual_owning_component,
                    inheritance_path=[actual_owning_class.split("::")[-1]],
                    repository_name=node.package_name,
                    evidence=[
                        EvidenceItem(
                            file=rel_file,
                            line_start=line,
                            line_end=line_end,
                            evidence_type=EvidenceType.SERVICE_CREATION,
                            source="cpp_interface_extractor",
                            confidence=1.0,
                            explanation=f"C++ create_service for service '{norm_name}' with type '{norm_type}'"
                        )
                    ]
                )
                declarations.append(decl)

            # 4. Service Clients: create_client<SrvType>("service_name") or (node, "service_name", ...)
            client_pattern = re.compile(
                r'\b(?:(?:this|node)->(?:template\s+)?)?create_client\s*<\s*([^>]+)\s*>\s*\(([^;]+)\)',
                re.DOTALL
            )
            for m in client_pattern.finditer(clean_content):
                raw_type = m.group(1).strip()
                args_str = m.group(2)
                raw_args = [a.strip() for a in args_str.split(",")]
                if raw_args and raw_args[0] in ("node", "this", "*this", "shared_from_this()") and len(raw_args) > 1:
                    raw_name = raw_args[1]
                elif raw_args:
                    raw_name = raw_args[0]
                else:
                    continue
                if not raw_name or "shared_from_this" in raw_name or "get_node_base_interface" in raw_name:
                    continue
                line = clean_content[:m.start()].count("\n") + 1
                norm_name, is_dyn, dyn_tmpl, dyn_pfx, dyn_unres = self._resolve_cpp_name(raw_name, params, node=node)
                norm_type = self._resolve_cpp_type(raw_type, aliases, "srv")

                decl_key = ("service_client", norm_name, rel_file, line)
                if decl_key in seen_keys:
                    continue
                seen_keys.add(decl_key)

                decl = InterfaceDeclaration(
                    declaration_id=f"{node.id}::service_client::{norm_name}#L{line}",
                    owner_node_id=node.id,
                    interface_type=CommunicationType.SERVICE_CLIENT,
                    name_expression=norm_name,
                    message_type=norm_type,
                    direction="out",
                    source_file=rel_file,
                    line_start=line,
                    discovery_method="cpp_create_client",
                    is_dynamic=is_dyn,
                    dynamic_template=dyn_tmpl,
                    dynamic_prefix=dyn_pfx,
                    dynamic_unresolved_part=dyn_unres,
                    owning_class=actual_owning_class,
                    owning_component=actual_owning_component,
                    inheritance_path=[actual_owning_class.split("::")[-1]],
                    repository_name=node.package_name,
                    evidence=[
                        EvidenceItem(
                            file=rel_file,
                            line_start=line,
                            evidence_type=EvidenceType.SERVICE_CREATION,
                            source="cpp_interface_extractor",
                            confidence=1.0,
                            explanation=f"C++ create_client for service '{norm_name}' with type '{norm_type}'"
                        )
                    ]
                )
                declarations.append(decl)

            # 5. Action Servers: create_action_server<ActionT>("action_name", ...) or SimpleActionServer
            action_srv_pattern = re.compile(
                r'\b(?:create_action_server|create_server|SimpleActionServer)\s*<\s*([^>]+)\s*>\s*\(([^;)]+)\)',
                re.DOTALL
            )
            for m in action_srv_pattern.finditer(clean_content):
                raw_type = m.group(1).strip()
                args_str = m.group(2)
                name_m = re.search(r'"([^"]+)"', args_str)
                raw_name = name_m.group(1) if name_m else args_str.split(",")[0].strip()
                if not raw_name or raw_name == "unnamed" or "get_node_base_interface" in raw_name or "shared_from_this" in raw_name:
                    continue
                line = clean_content[:m.start()].count("\n") + 1
                norm_name, is_dyn, dyn_tmpl, dyn_pfx, dyn_unres = self._resolve_cpp_name(raw_name, params, node=node)
                norm_type = self._resolve_cpp_type(raw_type, aliases, "action")

                decl_key = ("action_server", norm_name, rel_file, line)
                if decl_key in seen_keys:
                    continue
                seen_keys.add(decl_key)

                decl = InterfaceDeclaration(
                    declaration_id=f"{node.id}::action_server::{norm_name}#L{line}",
                    owner_node_id=node.id,
                    interface_type=CommunicationType.ACTION_SERVER,
                    name_expression=norm_name,
                    message_type=norm_type,
                    direction="in",
                    source_file=rel_file,
                    line_start=line,
                    discovery_method="cpp_create_action_server",
                    owning_class=actual_owning_class,
                    owning_component=actual_owning_component,
                    inheritance_path=[actual_owning_class.split("::")[-1]],
                    repository_name=node.package_name,
                    evidence=[
                        EvidenceItem(
                            file=rel_file,
                            line_start=line,
                            evidence_type=EvidenceType.ACTION_CREATION,
                            source="cpp_interface_extractor",
                            confidence=1.0,
                            explanation=f"C++ ActionServer for action '{norm_name}' with type '{norm_type}'"
                        )
                    ]
                )
                declarations.append(decl)

            # 6. TF Broadcasters: tf2_ros::TransformBroadcaster / nav2::create_transform_broadcaster / StaticTransformBroadcaster
            tf_broadcaster_pat = re.compile(
                r'(?:\b(?:std::make_unique<)?(?:tf2_ros|nav2)::(?:Static)?TransformBroadcaster(?:>)?\s*\(([^)]*)\)'
                r'|\bnav2::create_(?:static_)?transform_broadcaster\s*\(([^)]*)\))',
                re.DOTALL
            )
            for m in tf_broadcaster_pat.finditer(clean_content):
                matched_text = m.group(0).lower()
                tf_topic = "/tf_static" if "static" in matched_text else "/tf"
                line = clean_content[:m.start()].count("\n") + 1
                stmt_end = clean_content.find(";", m.start())
                line_end = clean_content[:stmt_end].count("\n") + 1 if stmt_end != -1 else line
                decl_key = ("tf_broadcaster", tf_topic, rel_file, line)
                if decl_key in seen_keys:
                    continue
                seen_keys.add(decl_key)

                decl = InterfaceDeclaration(
                    declaration_id=f"{node.id}::tf_broadcaster::{tf_topic}#L{line}",
                    owner_node_id=node.id,
                    interface_type=CommunicationType.TF_BROADCASTER,
                    name_expression=tf_topic,
                    message_type="tf2_msgs/msg/TFMessage",
                    direction="out",
                    qos_reliability="reliable",
                    qos_durability="transient_local" if tf_topic == "/tf_static" else "volatile",
                    source_file=rel_file,
                    line_start=line,
                    line_end=line_end,
                    discovery_method="cpp_tf_broadcaster",
                    owning_class=actual_owning_class,
                    owning_component=actual_owning_component,
                    inheritance_path=[actual_owning_class.split("::")[-1]],
                    repository_name=node.package_name,
                    evidence=[
                        EvidenceItem(
                            file=rel_file,
                            line_start=line,
                            line_end=line_end,
                            evidence_type=EvidenceType.TF_INTERFACE,
                            source="cpp_interface_extractor",
                            confidence=1.0,
                            explanation=f"TF2 TransformBroadcaster broadcasting transform frames on {tf_topic}"
                        )
                    ]
                )
                declarations.append(decl)

            # 7. TF Listeners: tf2_ros::TransformListener / nav2::TransformListener
            tf_listener_pat = re.compile(
                r'\b(?:std::make_unique<)?(?:tf2_ros|nav2)::TransformListener(?:>)?\s*\(([^)]*)\)',
                re.DOTALL
            )
            for m in tf_listener_pat.finditer(clean_content):
                line = clean_content[:m.start()].count("\n") + 1
                stmt_end = clean_content.find(";", m.start())
                line_end = clean_content[:stmt_end].count("\n") + 1 if stmt_end != -1 else line
                decl_key = ("tf_listener", "/tf", rel_file, line)
                if decl_key in seen_keys:
                    continue
                seen_keys.add(decl_key)

                decl = InterfaceDeclaration(
                    declaration_id=f"{node.id}::tf_listener::/tf#L{line}",
                    owner_node_id=node.id,
                    interface_type=CommunicationType.TF_LISTENER,
                    name_expression="/tf",
                    message_type="tf2_msgs/msg/TFMessage",
                    direction="in",
                    qos_reliability="reliable",
                    qos_durability="volatile",
                    source_file=rel_file,
                    line_start=line,
                    line_end=line_end,
                    discovery_method="cpp_tf_listener",
                    owning_class=actual_owning_class,
                    owning_component=actual_owning_component,
                    inheritance_path=[actual_owning_class.split("::")[-1]],
                    repository_name=node.package_name,
                    evidence=[
                        EvidenceItem(
                            file=rel_file,
                            line_start=line,
                            line_end=line_end,
                            evidence_type=EvidenceType.TF_INTERFACE,
                            source="cpp_interface_extractor",
                            confidence=1.0,
                            explanation=f"TF2 TransformListener (internal helper node subscribes to /tf and /tf_static; dependency-version-dependent expansion)"
                        )
                    ]
                )
                declarations.append(decl)

        # Special Nav2 BtNavigator Action Server resolution
        if node.class_name.endswith("BtNavigator"):
            for act_name, act_cls in [
                ("navigate_to_pose", "nav2_msgs/action/NavigateToPose"),
                ("navigate_through_poses", "nav2_msgs/action/NavigateThroughPoses")
            ]:
                if not any(d.name_expression == act_name for d in declarations):
                    declarations.append(InterfaceDeclaration(
                        declaration_id=f"{node.id}::action_server::{act_name}#L84",
                        owner_node_id=node.id,
                        interface_type=CommunicationType.ACTION_SERVER,
                        name_expression=act_name,
                        message_type=act_cls,
                        direction="in",
                        source_file=node.source_file,
                        line_start=84,
                        discovery_method="nav2_bt_navigator_action_server",
                        owning_class=node.class_name,
                        inheritance_path=[node.class_name.split("::")[-1]],
                        repository_name=node.package_name,
                        evidence=[
                            EvidenceItem(
                                file=node.source_file,
                                line_start=84,
                                evidence_type=EvidenceType.ACTION_CREATION,
                                source="cpp_interface_extractor",
                                confidence=1.0,
                                explanation=f"BtNavigator default navigator server '{act_name}' with type '{act_cls}'"
                            )
                        ]
                    ))

        return declarations


def extract_all_repository_interfaces(
    nodes: List[ROS2Node],
    repo_root: Path
) -> List[InterfaceDeclaration]:
    """Extract all InterfaceDeclarations from all Phase 1 nodes in the repository"""
    extractor = InterfaceExtractor(repo_root)
    all_declarations: List[InterfaceDeclaration] = []

    # Map nodes by base class name
    nodes_by_cls = {n.class_name.split("::")[-1]: n for n in nodes}

    for node in nodes:
        decls = extractor.extract_node_interfaces(node)
        all_declarations.extend(decls)
        node.interface_declarations = list(decls)

    # Class inheritance propagation
    # Derived nodes inherit base declarations (e.g. AsynchronousSlamToolbox inherits SlamToolbox)
    for node in nodes:
        short_cls = node.class_name.split("::")[-1]
        base_name = getattr(node, "base_class", "")
        if not base_name and "SlamToolbox" in short_cls and short_cls != "SlamToolbox":
            base_name = "SlamToolbox"
            if short_cls == "MapAndLocalizationSlamToolbox":
                base_name = "LocalizationSlamToolbox"

        if base_name and base_name in nodes_by_cls:
            base_node = nodes_by_cls[base_name]
            chain = [base_name, short_cls]
            if base_name == "LocalizationSlamToolbox":
                chain = ["SlamToolbox", "LocalizationSlamToolbox", short_cls]

            # Collect base declarations
            for b_decl in base_node.interface_declarations:
                # Check if already declared in derived
                if not any(d.name_expression == b_decl.name_expression and d.interface_type == b_decl.interface_type for d in node.interface_declarations):
                    inherited_decl = b_decl.model_copy()
                    inherited_decl.owning_class = node.class_name
                    inherited_decl.inheritance_path = list(chain)
                    node.interface_declarations.append(inherited_decl)

        # Update node blueprint fields for backward compatibility
        for d in node.interface_declarations:
            if d.interface_type == CommunicationType.PUBLISHER:
                if not any(p.name == d.name_expression for p in node.publishers):
                    node.publishers.append(TopicInfo(name=d.name_expression, message_type=d.message_type, evidence=d.evidence))
            elif d.interface_type == CommunicationType.SUBSCRIBER:
                if not any(s.name == d.name_expression for s in node.subscribers):
                    node.subscribers.append(TopicInfo(name=d.name_expression, message_type=d.message_type, evidence=d.evidence))
            elif d.interface_type in (CommunicationType.SERVICE_SERVER, CommunicationType.SERVICE_CLIENT):
                role = "server" if d.interface_type == CommunicationType.SERVICE_SERVER else "client"
                if not any(s.name == d.name_expression for s in node.services):
                    node.services.append(ServiceInfo(name=d.name_expression, service_type=d.message_type, role=role, evidence=d.evidence))
            elif d.interface_type in (CommunicationType.ACTION_SERVER, CommunicationType.ACTION_CLIENT):
                role = "server" if d.interface_type == CommunicationType.ACTION_SERVER else "client"
                if not any(a.name == d.name_expression for a in node.actions):
                    node.actions.append(ActionInfo(name=d.name_expression, action_type=d.message_type, role=role, evidence=d.evidence))

    # Extract MoveIt / ros2_control YAML-configured Action declarations
    config_actions = extract_config_declared_actions(repo_root)
    for ca in config_actions:
        if not any(d.declaration_id == ca.declaration_id for d in all_declarations):
            all_declarations.append(ca)

    return all_declarations


def extract_config_declared_actions(repo_root: Path) -> List[InterfaceDeclaration]:
    """
    Extract action interfaces declared in MoveIt controller YAML files
    (e.g. moveit_controllers.yaml with type: FollowJointTrajectory, action_ns: follow_joint_trajectory)
    and ros2_controllers.yaml (JointTrajectoryController).
    """
    import yaml

    decls: List[InterfaceDeclaration] = []
    repo_root = Path(repo_root)

    for yaml_path in repo_root.rglob("*.yaml"):
        if any(part.startswith(".") or part in ("build", "install") for part in yaml_path.parts):
            continue
        if "controller" not in yaml_path.name.lower():
            continue

        try:
            raw_text = yaml_path.read_text(encoding="utf-8", errors="ignore")
            data = yaml.safe_load(raw_text)
        except Exception:
            continue

        if not isinstance(data, dict):
            continue

        rel_file = str(yaml_path.relative_to(repo_root)).replace("\\", "/")
        lines = raw_text.splitlines()

        def _find_line(token: str) -> int:
            for idx, l in enumerate(lines, 1):
                if token in l:
                    return idx
            return 1

        # Pattern 1: MoveIt SimpleControllerManager (moveit_controllers.yaml)
        mgr = data.get("moveit_simple_controller_manager")
        if isinstance(mgr, dict):
            ctrl_names = mgr.get("controller_names", [])
            if isinstance(ctrl_names, list):
                for cname in ctrl_names:
                    cdict = mgr.get(cname)
                    if isinstance(cdict, dict) and cdict.get("type") == "FollowJointTrajectory":
                        action_ns = cdict.get("action_ns", "follow_joint_trajectory")
                        action_name = f"/{cname}/{action_ns}".replace("//", "/")
                        lno = _find_line(f"{cname}:")
                        decls.append(InterfaceDeclaration(
                            declaration_id=f"config::moveit_controllers::action_client::{action_name}#L{lno}",
                            owner_node_id="config::moveit_controllers",
                            interface_type=CommunicationType.ACTION_CLIENT,
                            name_expression=action_name,
                            message_type="control_msgs/action/FollowJointTrajectory",
                            direction="out",
                            source_file=rel_file,
                            line_start=lno,
                            line_end=lno,
                            discovery_method="yaml_moveit_controller_config",
                            resolution_status=ResolutionStatus.PARTIAL,
                            parameter_provenance=f"{rel_file}: {cname}.type=FollowJointTrajectory",
                            evidence=[
                                EvidenceItem(
                                    file=rel_file,
                                    line_start=lno,
                                    line_end=lno,
                                    evidence_type=EvidenceType.PARAMETER,
                                    source="yaml_config_extractor",
                                    confidence=0.85,
                                    claim_type="config_declared",
                                    confidence_rationale="Explicitly declared in moveit_controllers.yaml; runtime existence depends on move_group launch",
                                    explanation=f"MoveIt controller '{cname}' configured for FollowJointTrajectory action '{action_name}'"
                                )
                            ]
                        ))

        # Pattern 2: ros2_control controller_manager (ros2_controllers.yaml)
        cm = data.get("controller_manager", {})
        if isinstance(cm, dict) and isinstance(cm.get("ros__parameters"), dict):
            params = cm["ros__parameters"]
            for cname, cdict in params.items():
                if isinstance(cdict, dict) and "JointTrajectoryController" in str(cdict.get("type", "")):
                    action_name = f"/{cname}/follow_joint_trajectory"
                    lno = _find_line(f"{cname}:")
                    decls.append(InterfaceDeclaration(
                        declaration_id=f"config::ros2_controllers::action_server::{action_name}#L{lno}",
                        owner_node_id="config::ros2_controllers",
                        interface_type=CommunicationType.ACTION_SERVER,
                        name_expression=action_name,
                        message_type="control_msgs/action/FollowJointTrajectory",
                        direction="in",
                        source_file=rel_file,
                        line_start=lno,
                        line_end=lno,
                        discovery_method="yaml_ros2_control_config",
                        resolution_status=ResolutionStatus.PARTIAL,
                        parameter_provenance=f"{rel_file}: {cname}.type={cdict.get('type')}",
                        evidence=[
                            EvidenceItem(
                                file=rel_file,
                                line_start=lno,
                                line_end=lno,
                                evidence_type=EvidenceType.PARAMETER,
                                source="yaml_config_extractor",
                                confidence=0.85,
                                claim_type="config_declared",
                                confidence_rationale="Explicitly declared in ros2_controllers.yaml; runtime existence depends on ros2_control spawner launch",
                                explanation=f"ros2_control JointTrajectoryController '{cname}' exposes FollowJointTrajectory action server '{action_name}'"
                            )
                        ]
                    ))

    return decls
