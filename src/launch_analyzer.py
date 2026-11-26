"""
ArchSynth LaunchFileAnalyzer - Phase 2: Complete ROS2 Launch Analysis & Resolution.

Extracts:
  - Standalone nodes (Node)
  - Composed components (ComposableNode, LoadComposableNodes)
  - Component containers (ComposableNodeContainer, rclcpp_components)
  - Recursive launch inclusions (IncludeLaunchDescription) with loop prevention
  - Scoped groups, namespaces, conditions, remappings, parameters, arguments
  - Deterministic runtime launch instances and deployment configuration profiles
  - Ambiguity-aware mapping to Phase 1 source-grounded ROS2 node inventory
"""

import ast
import json
import logging
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from src.schema import (
    DeploymentProfile, DeploymentProfileType, EntityType, EvidenceItem,
    EvidenceType, LaunchContainer, LaunchFile, LaunchInclude, LaunchInstance,
    LaunchMappingStatus, LaunchNode, NodeLaunchMapping, ResolutionStatus,
    ROS2Node
)

logger = logging.getLogger(__name__)


# ============================================================================
# Static AST Expression Evaluator (Safe, No exec/eval)
# ============================================================================

class StaticLaunchEvaluator:
    """
    Restricted, safe static evaluator for ROS2 Python launch expressions.
    Never executes arbitrary repository code. Evaluates AST expressions,
    local variables, package-share paths, and common ROS2 launch substitutions.
    """

    def __init__(
        self,
        repo_path: Optional[Path] = None,
        current_file: Optional[Path] = None,
        packages_map: Optional[Dict[str, str]] = None,
        local_vars: Optional[Dict[str, Any]] = None
    ):
        self.repo_path = repo_path
        self.current_file = current_file
        self.packages_map = packages_map or {}
        self.local_vars: Dict[str, Any] = dict(local_vars or {})

    def set_var(self, name: str, value: Any):
        self.local_vars[name] = value

    def eval_node(self, node: Optional[ast.AST]) -> Any:
        if node is None:
            return None

        # Literals & Constants
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Str):  # Python < 3.8
            return node.s
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.NameConstant):  # Python < 3.8
            return node.value

        # Variable lookup
        elif isinstance(node, ast.Name):
            if node.id in self.local_vars:
                return self.local_vars[node.id]
            # Known Python literals
            if node.id == "True":
                return True
            elif node.id == "False":
                return False
            elif node.id == "None":
                return None
            return f"${{{node.id}}}"

        # Sequences
        elif isinstance(node, ast.List):
            return [self.eval_node(el) for el in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self.eval_node(el) for el in node.elts)
        elif isinstance(node, ast.Dict):
            return {
                str(self.eval_node(k)): self.eval_node(v)
                for k, v in zip(node.keys, node.values)
                if k is not None
            }

        # Binary operations (string concat, list concat, path concat)
        elif isinstance(node, ast.BinOp):
            left = self.eval_node(node.left)
            right = self.eval_node(node.right)
            if isinstance(node.op, ast.Add):
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                elif isinstance(left, list) and isinstance(right, list):
                    return left + right
                elif isinstance(left, dict) and isinstance(right, dict):
                    merged = dict(left)
                    merged.update(right)
                    return merged
                return f"{left} + {right}"
            elif isinstance(node.op, ast.Mod):  # string format
                return f"{left} % {right}"
            return f"{left}_{right}"

        # Unary operations (not cond)
        elif isinstance(node, ast.UnaryOp):
            operand = self.eval_node(node.operand)
            if isinstance(node.op, ast.Not):
                return f"not {operand}"
            return f"-{operand}"

        # F-strings
        elif isinstance(node, ast.JoinedStr):
            parts = []
            for val in node.values:
                if isinstance(val, ast.Constant):
                    parts.append(str(val.value))
                elif isinstance(val, ast.FormattedValue):
                    parts.append(str(self.eval_node(val.value)))
            return "".join(parts)

        # Attribute access (e.g. os.path.join, pkg.launch)
        elif isinstance(node, ast.Attribute):
            val = self.eval_node(node.value)
            return f"{val}.{node.attr}" if val else node.attr

        # Subscripts (e.g. dict['key'], list[0])
        elif isinstance(node, ast.Subscript):
            val = self.eval_node(node.value)
            idx = self.eval_node(node.slice)
            if isinstance(val, (dict, list, tuple)) and isinstance(idx, (int, str)):
                try:
                    return val[idx]
                except Exception:
                    pass
            return f"{val}[{idx}]"

        # Function / Method calls
        elif isinstance(node, ast.Call):
            return self._eval_call(node)

        return None

    def _eval_call(self, node: ast.Call) -> Any:
        func_name = self._get_call_name(node)
        short_name = func_name.split(".")[-1] if func_name else ""

        # Safe dispatch for known launch / path helper calls
        if short_name in ("get_package_share_directory", "FindPackageShare"):
            pkg_name = self._get_arg_val(node, 0, "package_name") or self._get_arg_val(node, 0, "package")
            if pkg_name:
                pkg_str = str(pkg_name).strip("'\"")
                if pkg_str in self.packages_map:
                    rel_path = self.packages_map[pkg_str]
                    if self.repo_path:
                        return str((self.repo_path / rel_path).resolve()).replace("\\", "/")
                    return rel_path.replace("\\", "/")
                return f"<share:{pkg_str}>"
            return "<share:unknown>"

        elif short_name in ("join", "Path"):
            # os.path.join(*parts) or Path(*parts)
            evaluated_args = [self.eval_node(a) for a in node.args]
            valid_parts = [str(p) for p in evaluated_args if p is not None]
            if valid_parts:
                joined = "/".join(valid_parts).replace("\\", "/")
                # Collapse double slashes
                return re.sub(r"/+", "/", joined)
            return ""

        elif short_name == "PathJoinSubstitution":
            # PathJoinSubstitution([sub1, sub2, ...])
            parts = self._get_arg_val(node, 0, "substitutions")
            if isinstance(parts, (list, tuple)):
                str_parts = [str(p) for p in parts if p is not None]
                return "/".join(str_parts).replace("\\", "/")
            return str(parts) if parts else ""

        elif short_name == "PythonLaunchDescriptionSource":
            source = self._get_arg_val(node, 0, "launch_file_path") or self._get_arg_val(node, 0)
            return str(source) if source else ""

        elif short_name in ("LaunchConfiguration", "LaunchConfigAsBool"):
            var_name = self._get_arg_val(node, 0, "variable_name") or self._get_arg_val(node, 0)
            return f"${{{var_name}}}" if var_name else "${config}"

        elif short_name == "PythonExpression":
            expr = self._get_arg_val(node, 0, "expression") or self._get_arg_val(node, 0)
            if isinstance(expr, (list, tuple)):
                return "".join(str(e) for e in expr)
            return str(expr) if expr else ""

        elif short_name in ("IfCondition", "UnlessCondition"):
            cond = self._get_arg_val(node, 0, "predicate") or self._get_arg_val(node, 0)
            return f"{short_name}({cond})"

        elif short_name in ("EqualsSubstitution", "NotEqualsSubstitution"):
            left = self._get_arg_val(node, 0, "left")
            right = self._get_arg_val(node, 1, "right")
            op = "==" if short_name == "EqualsSubstitution" else "!="
            return f"({left} {op} {right})"

        elif short_name in ("ParameterFile", "RewrittenYaml"):
            source_file = (
                self._get_arg_val(node, 0, "param_file") or
                self._get_arg_val(node, 0, "source_file") or
                self._get_arg_val(node, 0)
            )
            return str(source_file) if source_file else f"{short_name}()"

        elif short_name == "EnvironmentVariable":
            name = self._get_arg_val(node, 0, "name") or self._get_arg_val(node, 0)
            default = self._get_arg_val(node, 1, "default_value")
            return f"${{env:{name}}}" if name else "${env:unknown}"

        elif short_name == "SetEnvironmentVariable":
            name = self._get_arg_val(node, 0, "name")
            val = self._get_arg_val(node, 1, "value")
            return {"env": str(name), "value": str(val)}

        elif short_name == "AndSubstitution":
            left = self._get_arg_val(node, 0, "left") or (self.eval_node(node.args[0]) if len(node.args) > 0 else "")
            right = self._get_arg_val(node, 1, "right") or (self.eval_node(node.args[1]) if len(node.args) > 1 else "")
            return f"({left} and {right})"

        elif short_name == "OrSubstitution":
            left = self._get_arg_val(node, 0, "left") or (self.eval_node(node.args[0]) if len(node.args) > 0 else "")
            right = self._get_arg_val(node, 1, "right") or (self.eval_node(node.args[1]) if len(node.args) > 1 else "")
            return f"({left} or {right})"

        elif short_name == "NotSubstitution":
            sub = self._get_arg_val(node, 0, "value") or (self.eval_node(node.args[0]) if len(node.args) > 0 else "")
            return f"not ({sub})"

        elif short_name == "TextSubstitution":
            txt = self._get_arg_val(node, 0, "text") or (self.eval_node(node.args[0]) if len(node.args) > 0 else "")
            return str(txt) if txt is not None else ""

        elif short_name == "ThisLaunchFileDir":
            if self.current_file:
                return str(self.current_file.parent.resolve()).replace("\\", "/")
            return "<this_launch_dir>"

        elif short_name == "AnonName":
            name = self._get_arg_val(node, 0, "name") or (self.eval_node(node.args[0]) if len(node.args) > 0 else "") or "anon"
            return f"{name}_anon"

        elif short_name == "items":
            # Handling dict.items()
            if isinstance(node.func, ast.Attribute):
                caller_val = self.eval_node(node.func.value)
                if isinstance(caller_val, dict):
                    return list(caller_val.items())
            return []

        # Return symbolic representation for unhandled calls without executing arbitrary code
        return f"{short_name}()"

    def _get_call_name(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            val = self.eval_node(node.func.value)
            return f"{val}.{node.func.attr}" if val else node.func.attr
        return ""

    def _get_arg_val(self, node: ast.Call, index: int, kw_name: Optional[str] = None) -> Any:
        if kw_name:
            for kw in node.keywords:
                if kw.arg == kw_name:
                    return self.eval_node(kw.value)
        if index < len(node.args):
            return self.eval_node(node.args[index])
        return None


# ============================================================================
# Launch Context Scoping
# ============================================================================

@dataclass
class LaunchContext:
    """Scoped execution environment for nested GroupActions and includes"""
    namespaces: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    remappings: Dict[str, str] = field(default_factory=dict)
    parameters: List[Any] = field(default_factory=list)
    passed_arguments: Dict[str, str] = field(default_factory=dict)
    parent_inclusion_id: Optional[str] = None
    container_name: Optional[str] = None
    deployment_profile: str = "default"

    def clone(self) -> "LaunchContext":
        return LaunchContext(
            namespaces=list(self.namespaces),
            conditions=list(self.conditions),
            remappings=dict(self.remappings),
            parameters=list(self.parameters),
            passed_arguments=dict(self.passed_arguments),
            parent_inclusion_id=self.parent_inclusion_id,
            container_name=self.container_name,
            deployment_profile=self.deployment_profile
        )

    def effective_namespace(self) -> str:
        clean = [ns.strip("/") for ns in self.namespaces if ns and str(ns).strip("/")]
        return "/".join(clean)

    def effective_condition(self) -> Optional[str]:
        clean = [c for c in self.conditions if c]
        if not clean:
            return None
        if len(clean) == 1:
            return clean[0]
        return " and ".join(f"({c})" for c in clean)

    def effective_profile(self) -> str:
        cond = self.effective_condition() or ""
        cond_lower = cond.lower()
        if "not" in cond_lower and "composition" in cond_lower:
            return "standalone"
        if "use_composition" in cond_lower and "not" not in cond_lower:
            return "composable"
        if "slam" in cond_lower:
            return "slam"
        if self.deployment_profile != "default":
            return self.deployment_profile
        return "default"


# ============================================================================
# Python Launch File Parser
# ============================================================================

class PythonLaunchParser:
    """
    AST Parser for ROS2 Python launch files.
    Extracts standalone nodes, composable nodes, containers, inclusions,
    scoped groups, and builds deterministic LaunchInstances.
    """

    def __init__(
        self,
        file_path: Path,
        package_name: str,
        repo_path: Optional[Path] = None,
        packages_map: Optional[Dict[str, str]] = None
    ):
        self.file_path = file_path
        self.package_name = package_name
        self.repo_path = repo_path.resolve() if repo_path else None
        self.packages_map = packages_map or {}

        # Relative path for evidence citations
        if self.repo_path:
            try:
                self.rel_file = str(file_path.resolve().relative_to(self.repo_path)).replace("\\", "/")
            except ValueError:
                self.rel_file = str(file_path).replace("\\", "/")
        else:
            self.rel_file = str(file_path).replace("\\", "/")

        self.launch_file = LaunchFile(
            file_path=self.rel_file,
            package_name=package_name,
            launch_type="python"
        )

        self.evaluator = StaticLaunchEvaluator(
            repo_path=repo_path,
            current_file=file_path,
            packages_map=self.packages_map
        )

        self.instances: List[LaunchInstance] = []
        self.containers: List[LaunchContainer] = []
        self.context = LaunchContext()
        self.processed_action_nodes: Set[int] = set()
        self.import_aliases: Dict[str, str] = {}
        self.call_var_names: Dict[int, str] = {}
        self.lifecycle_events: List[Dict[str, Any]] = []

    def parse(self) -> LaunchFile:
        try:
            source = self.file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source, filename=str(self.file_path))
        except Exception as e:
            logger.warning(f"Failed to parse AST for {self.file_path}: {e}")
            return self.launch_file

        # Pass 1: Collect local variable assignments, imports, and argument declarations
        self._collect_local_assignments(tree)

        # Pass 2: Traverse launch action hierarchy
        self._traverse_tree(tree, self.context)

        self.launch_file.instances = self.instances
        self.launch_file.containers = self.containers
        return self.launch_file

    def _collect_local_assignments(self, tree: ast.AST):
        """Pre-evaluate local assignments, collect import aliases, launch arguments, and lifecycle events"""
        for node in ast.walk(tree):
            # Imports and import aliases
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target_name = alias.name.split(".")[-1]
                    as_name = alias.asname or target_name
                    self.import_aliases[as_name] = target_name
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    target_name = alias.name
                    as_name = alias.asname or target_name
                    self.import_aliases[as_name] = target_name

            # Pre-evaluate DeclareLaunchArgument and collect lifecycle events
            elif isinstance(node, ast.Call):
                raw_cname = self.evaluator._get_call_name(node).split(".")[-1]
                cname = self.import_aliases.get(raw_cname, raw_cname)
                if cname in ("DeclareLaunchArgument", "DeclareLaunchArgumentList"):
                    self._handle_declare_argument(node)
                elif cname in ("EmitEvent", "RegisterEventHandler"):
                    self._collect_lifecycle_event(node)

            # Local assignments
            elif isinstance(node, ast.Assign):
                val = self.evaluator.eval_node(node.value)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.evaluator.set_var(target.id, val)
                        if isinstance(node.value, ast.Call):
                            self.call_var_names[id(node.value)] = target.id

    def _collect_lifecycle_event(self, node: ast.Call):
        """Extract EmitEvent and RegisterEventHandler lifecycle transitions"""
        raw_cname = self.evaluator._get_call_name(node).split(".")[-1]
        cname = self.import_aliases.get(raw_cname, raw_cname)
        cond = self.evaluator._get_arg_val(node, 1, "condition")
        cond_str = str(cond) if cond else None

        if cname == "EmitEvent":
            event_arg = None
            for kw in node.keywords:
                if kw.arg == "event":
                    event_arg = kw.value
            if not event_arg and len(node.args) > 0:
                event_arg = node.args[0]

            if isinstance(event_arg, ast.Call):
                self._parse_change_state_call(event_arg, cond_str)

        elif cname == "RegisterEventHandler":
            handler_arg = None
            for kw in node.keywords:
                if kw.arg in ("event_handler", "on_state_transition"):
                    handler_arg = kw.value
            if not handler_arg and len(node.args) > 0:
                handler_arg = node.args[0]

            if isinstance(handler_arg, ast.Call):
                target_var = None
                for kw in handler_arg.keywords:
                    if kw.arg == "target_lifecycle_node":
                        if isinstance(kw.value, ast.Name):
                            target_var = kw.value.id
                        else:
                            target_var = str(self.evaluator.eval_node(kw.value))
                    elif kw.arg == "condition" and not cond_str:
                        cond_val = self.evaluator.eval_node(kw.value)
                        if cond_val:
                            cond_str = str(cond_val)

                # Check nested entities inside handler (e.g. EmitEvent ChangeState activate)
                for kw in handler_arg.keywords:
                    if kw.arg == "entities" and isinstance(kw.value, (ast.List, ast.Tuple)):
                        for ent in kw.value.elts:
                            if isinstance(ent, ast.Call):
                                self._collect_lifecycle_event(ent)

                if target_var:
                    self.lifecycle_events.append({
                        "target_var": target_var,
                        "transition": "TRANSITION_ACTIVATE",
                        "condition": cond_str
                    })

    def _parse_change_state_call(self, call: ast.Call, cond_str: Optional[str]):
        """Parse ChangeState call within an EmitEvent"""
        target_var = None
        transition = None
        for kw in call.keywords:
            if kw.arg == "lifecycle_node_matcher":
                if isinstance(kw.value, ast.Call):
                    if len(kw.value.args) > 0 and isinstance(kw.value.args[0], ast.Name):
                        target_var = kw.value.args[0].id
                    elif len(kw.value.args) > 0:
                        target_var = str(self.evaluator.eval_node(kw.value.args[0]))
            elif kw.arg == "transition_id":
                if isinstance(kw.value, ast.Attribute):
                    transition = kw.value.attr
                else:
                    transition = str(self.evaluator.eval_node(kw.value))

        if target_var:
            self.lifecycle_events.append({
                "target_var": target_var,
                "transition": transition or "TRANSITION_CONFIGURE",
                "condition": cond_str
            })

    def _traverse_tree(self, tree: ast.AST, context: LaunchContext):
        """Walk AST in deterministic source order with proper lexical/function/group scoping."""
        if isinstance(tree, ast.FunctionDef):
            # Each function has its own cloned context so PushROSNamespace/SetRemap in one helper doesn't leak
            fn_ctx = context.clone()
            for child in ast.iter_child_nodes(tree):
                self._traverse_tree(child, fn_ctx)
            return

        if isinstance(tree, ast.Call):
            if id(tree) in self.processed_action_nodes:
                return
            self.processed_action_nodes.add(id(tree))

            raw_name = self.evaluator._get_call_name(tree).split(".")[-1]
            call_name = self.import_aliases.get(raw_name, raw_name)

            if call_name in ("DeclareLaunchArgument", "DeclareLaunchArgumentList"):
                self._handle_declare_argument(tree)
                return
            elif call_name == "GroupAction":
                self._handle_group_action(tree, context)
                return
            elif call_name in ("PushROSNamespace", "PushRosNamespace"):
                self._handle_push_namespace(tree, context)
                return
            elif call_name == "SetParameter":
                self._handle_set_parameter(tree, context)
                return
            elif call_name == "SetRemap":
                self._handle_set_remap(tree, context)
                return
            elif call_name == "Node":
                self._handle_node(tree, context, action_type="Node")
                return
            elif call_name == "LifecycleNode":
                self._handle_node(tree, context, action_type="LifecycleNode")
                return
            elif call_name == "ComposableNodeContainer":
                self._handle_composable_container(tree, context)
                return
            elif call_name == "LoadComposableNodes":
                self._handle_load_composable_nodes(tree, context)
                return
            elif call_name == "IncludeLaunchDescription":
                self._handle_include(tree, context)
                return
            elif call_name in ("OpaqueFunction", "ExecuteProcess", "RegisterEventHandler"):
                lno = getattr(tree, "lineno", "?")
                target_arg = self.evaluator._get_arg_val(tree, 0, "function" if call_name == "OpaqueFunction" else None)
                desc = f"{call_name}({target_arg or 'dynamic'}) at L{lno}"
                if desc not in self.launch_file.unresolved_expressions:
                    self.launch_file.unresolved_expressions.append(desc)

        for child in ast.iter_child_nodes(tree):
            self._traverse_tree(child, context)

    def _handle_declare_argument(self, node: ast.Call):
        name = self.evaluator._get_arg_val(node, 0, "name")
        default = self.evaluator._get_arg_val(node, 1, "default_value")
        desc = self.evaluator._get_arg_val(node, 2, "description")
        if name:
            self.launch_file.arguments[str(name)] = {
                "default": default,
                "description": desc
            }

    def _handle_push_namespace(self, node: ast.Call, context: LaunchContext):
        ns = self.evaluator._get_arg_val(node, 0, "namespace")
        if ns:
            context.namespaces.append(str(ns))

    def _handle_set_parameter(self, node: ast.Call, context: LaunchContext):
        name = self.evaluator._get_arg_val(node, 0, "name")
        val = self.evaluator._get_arg_val(node, 1, "value")
        if name:
            context.parameters.append({str(name): val})

    def _handle_set_remap(self, node: ast.Call, context: LaunchContext):
        src = self.evaluator._get_arg_val(node, 0, "src")
        dst = self.evaluator._get_arg_val(node, 1, "dst")
        if src and dst:
            context.remappings[str(src)] = str(dst)

    def _handle_group_action(self, node: ast.Call, context: LaunchContext):
        """Process GroupAction with scoped namespace, condition, and nested actions"""
        actions = self.evaluator._get_arg_val(node, 0, "actions")
        condition = self.evaluator._get_arg_val(node, 1, "condition")

        group_ctx = context.clone()
        if condition:
            group_ctx.conditions.append(str(condition))

        # Check if actions passed as AST node directly
        actions_list = []
        for kw in node.keywords:
            if kw.arg == "actions" and isinstance(kw.value, (ast.List, ast.Tuple)):
                actions_list = kw.value.elts
            elif kw.arg == "condition":
                cond_val = self.evaluator.eval_node(kw.value)
                if cond_val:
                    group_ctx.conditions.append(str(cond_val))

        if not actions_list and len(node.args) > 0 and isinstance(node.args[0], (ast.List, ast.Tuple)):
            actions_list = node.args[0].elts

        # Traverse nested actions inside scoped context
        for action_node in actions_list:
            if isinstance(action_node, ast.Call):
                # Mark as processed so top-level ast.walk does not re-process
                for sub in ast.walk(action_node):
                    self.processed_action_nodes.add(id(sub))

                raw_cname = self.evaluator._get_call_name(action_node).split(".")[-1]
                cname = self.import_aliases.get(raw_cname, raw_cname)
                if cname in ("PushROSNamespace", "PushRosNamespace"):
                    self._handle_push_namespace(action_node, group_ctx)
                elif cname == "SetParameter":
                    self._handle_set_parameter(action_node, group_ctx)
                elif cname == "SetRemap":
                    self._handle_set_remap(action_node, group_ctx)
                elif cname == "Node":
                    self._handle_node(action_node, group_ctx, action_type="Node")
                elif cname == "LifecycleNode":
                    self._handle_node(action_node, group_ctx, action_type="LifecycleNode")
                elif cname == "ComposableNodeContainer":
                    self._handle_composable_container(action_node, group_ctx)
                elif cname == "LoadComposableNodes":
                    self._handle_load_composable_nodes(action_node, group_ctx)
                elif cname == "IncludeLaunchDescription":
                    self._handle_include(action_node, group_ctx)
                elif cname == "GroupAction":
                    self._handle_group_action(action_node, group_ctx)

        # Track group metadata
        self.launch_file.groups.append({
            "type": "GroupAction",
            "namespace": group_ctx.effective_namespace(),
            "condition": group_ctx.effective_condition(),
            "actions_count": len(actions_list)
        })

    def _handle_node(self, node: ast.Call, context: LaunchContext, action_type: str = "Node"):
        """Extract standalone Node or LifecycleNode declaration or component container host"""
        lineno = getattr(node, "lineno", None)

        pkg = (
            self.evaluator._get_arg_val(node, 0, "package") or
            self.evaluator._get_arg_val(node, 0, "pkg") or ""
        )
        executable = (
            self.evaluator._get_arg_val(node, 1, "executable") or
            self.evaluator._get_arg_val(node, 1, "exec") or
            self.evaluator._get_arg_val(node, 1, "node_executable") or ""
        )
        name = (
            self.evaluator._get_arg_val(node, 2, "name") or
            self.evaluator._get_arg_val(node, 2, "node_name") or ""
        )
        namespace = (
            self.evaluator._get_arg_val(node, 3, "namespace") or
            self.evaluator._get_arg_val(node, 3, "node_namespace") or ""
        )
        remappings = (
            self.evaluator._get_arg_val(node, 4, "remappings") or
            self.evaluator._get_arg_val(node, 4, "remap") or []
        )
        parameters = (
            self.evaluator._get_arg_val(node, 5, "parameters") or
            self.evaluator._get_arg_val(node, 5, "params") or []
        )
        arguments = (
            self.evaluator._get_arg_val(node, 6, "arguments") or
            self.evaluator._get_arg_val(node, 6, "args") or []
        )
        respawn = self.evaluator._get_arg_val(node, 7, "respawn") or False
        output = self.evaluator._get_arg_val(node, 8, "output") or "screen"
        condition = self.evaluator._get_arg_val(node, 9, "condition")

        # Positional fallback when name was provided as sole positional arg and package was keyword
        if not name and len(node.args) == 1 and not (self.evaluator._get_arg_val(node, 0, "package")):
            name = self.evaluator.eval_node(node.args[0])

        is_lifecycle = (action_type == "LifecycleNode")

        # Build normalized remappings
        norm_remappings = dict(context.remappings)
        if isinstance(remappings, list):
            for r in remappings:
                if isinstance(r, (list, tuple)) and len(r) == 2:
                    norm_remappings[str(r[0])] = str(r[1])
                elif isinstance(r, dict):
                    norm_remappings.update({str(k): str(v) for k, v in r.items()})
        elif isinstance(remappings, dict):
            norm_remappings.update({str(k): str(v) for k, v in remappings.items()})

        # Build normalized parameters and separate parameter files vs inline parameters
        norm_params = list(context.parameters)
        if isinstance(parameters, list):
            norm_params.extend(parameters)
        elif parameters:
            norm_params.append(parameters)

        param_files: List[str] = []
        inline_params: Dict[str, Any] = {}

        def _extract_params_recursive(item: Any):
            if isinstance(item, dict):
                inline_params.update(item)
            elif isinstance(item, (list, tuple)):
                for sub in item:
                    _extract_params_recursive(sub)
            elif isinstance(item, str):
                s = item.strip()
                if s:
                    param_files.append(s)
            elif item is not None:
                param_files.append(str(item))

        for p in norm_params:
            _extract_params_recursive(p)

        # Namespace composition
        active_ns = context.effective_namespace()
        if namespace:
            active_ns = f"{active_ns}/{str(namespace).strip('/')}".strip("/")

        # Condition composition
        active_cond = context.effective_condition()
        if condition:
            active_cond = f"{active_cond} and ({condition})" if active_cond else str(condition)

        # Check if this node is a ComposableNodeContainer host (rclcpp_components host process)
        exec_str = str(executable)
        pkg_str = str(pkg)
        is_container_host = (
            pkg_str == "rclcpp_components" or
            "component_container" in exec_str
        )

        effective_name = str(name) if name else (exec_str or "unnamed_node")

        if is_container_host:
            # Component Container (Host Process)
            container_id = f"{self.rel_file}::{effective_name}#L{lineno or 0}"
            container = LaunchContainer(
                container_id=container_id,
                name=effective_name,
                package=pkg_str,
                executable=exec_str,
                launch_file=self.rel_file,
                line_number=lineno,
                namespace=active_ns,
                condition=active_cond,
                deployment_profile="composable"
            )
            self.containers.append(container)
            context.container_name = effective_name

            # Also create launch_node for schema backward compatibility
            lnode = LaunchNode(
                node_name=effective_name,
                package=pkg_str,
                executable=exec_str,
                namespace=active_ns,
                remappings=norm_remappings,
                parameters=norm_params,
                arguments=[str(a) for a in arguments] if isinstance(arguments, list) else [],
                respawn=bool(respawn),
                output=str(output),
                condition=active_cond,
                line_start=lineno,
                action_type="ComposableNodeContainer",
                is_lifecycle=False,
                parameter_files=param_files,
                inline_parameters=inline_params,
                resolution_status=ResolutionStatus.RESOLVED
            )
            self.launch_file.nodes.append(lnode)
            return

        # Normal Standalone Node or LifecycleNode Instance
        profile = context.effective_profile()
        if active_cond:
            c_low = active_cond.lower()
            if "not" in c_low and "composition" in c_low:
                profile = "standalone"
            elif "use_composition" in c_low and "not" not in c_low:
                profile = "composable"

        instance_id = (
            f"{self.rel_file}::{effective_name}#L{lineno or 0}"
            f"[ns={active_ns}|prof={profile}|parent={context.parent_inclusion_id or 'root'}]"
        )

        # Extract lifecycle transition metadata if applicable
        lifecycle_info = None
        if is_lifecycle:
            target_var = self.call_var_names.get(id(node))
            matching_events = []
            for ev in self.lifecycle_events:
                if target_var and ev.get("target_var") == target_var:
                    matching_events.append(ev)
                elif effective_name and ev.get("target_var") == effective_name:
                    matching_events.append(ev)

            transitions = list(dict.fromkeys([ev["transition"] for ev in matching_events if ev.get("transition")]))
            autostart_cond = next((ev["condition"] for ev in matching_events if ev.get("condition")), None)
            lifecycle_info = {
                "is_lifecycle": True,
                "has_lifecycle_events": bool(matching_events),
                "transitions": transitions,
                "autostart_condition": autostart_cond,
                "management_mode": "launch_event_handler" if matching_events else "external_lifecycle_manager"
            }

        # Determine declaration resolution status
        res_status = ResolutionStatus.RESOLVED
        if not pkg_str or not exec_str:
            res_status = ResolutionStatus.UNRESOLVED
        elif (
            active_ns.startswith("${") and active_ns.endswith("}") and
            active_ns[2:-1] not in self.launch_file.arguments
        ):
            res_status = ResolutionStatus.PARTIAL
        elif any(
            pf.startswith("${") and pf.endswith("}") and pf[2:-1] not in self.launch_file.arguments
            for pf in param_files
        ):
            res_status = ResolutionStatus.PARTIAL

        action_label = "LifecycleNode" if is_lifecycle else "Standalone Node"
        evidence = [
            EvidenceItem(
                file=self.rel_file,
                line_start=lineno,
                line_end=getattr(node, "end_lineno", lineno),
                evidence_type=EvidenceType.LAUNCH_NODE,
                source="launch_analyzer",
                confidence=1.0,
                explanation=f"{action_label} declared in launch: pkg='{pkg_str}', exec='{exec_str}', name='{effective_name}'"
            )
        ]

        instance = LaunchInstance(
            instance_id=instance_id,
            node_name=effective_name,
            package=pkg_str,
            executable=exec_str,
            launch_file=self.rel_file,
            line_number=lineno,
            parent_inclusion_id=context.parent_inclusion_id,
            namespace=active_ns,
            remappings=norm_remappings,
            parameters=norm_params,
            arguments=[str(a) for a in arguments] if isinstance(arguments, list) else [],
            is_composable=False,
            condition=active_cond,
            deployment_profile=profile,
            launch_arguments=dict(context.passed_arguments),
            evidence=evidence,
            repository_name=self.package_name,
            action_type=action_type,
            is_lifecycle=is_lifecycle,
            parameter_files=param_files,
            inline_parameters=inline_params,
            lifecycle_info=lifecycle_info,
            resolution_status=res_status
        )
        self.instances.append(instance)

        # LaunchNode for backward compatibility
        lnode = LaunchNode(
            node_name=effective_name,
            package=pkg_str,
            executable=exec_str,
            namespace=active_ns,
            remappings=norm_remappings,
            parameters=norm_params,
            arguments=[str(a) for a in arguments] if isinstance(arguments, list) else [],
            respawn=bool(respawn),
            output=str(output),
            is_composable=False,
            condition=active_cond,
            line_start=lineno,
            action_type=action_type,
            is_lifecycle=is_lifecycle,
            parameter_files=param_files,
            inline_parameters=inline_params,
            lifecycle_info=lifecycle_info,
            resolution_status=res_status
        )
        self.launch_file.nodes.append(lnode)

    def _handle_composable_container(self, node: ast.Call, context: LaunchContext):
        """Extract explicit ComposableNodeContainer action"""
        name = self.evaluator._get_arg_val(node, 0, "name") or "container"
        namespace = self.evaluator._get_arg_val(node, 1, "namespace") or context.effective_namespace()
        package = self.evaluator._get_arg_val(node, 2, "package") or "rclcpp_components"
        executable = self.evaluator._get_arg_val(node, 3, "executable") or "component_container"
        condition = self.evaluator._get_arg_val(node, 4, "condition") or context.effective_condition()
        lineno = getattr(node, "lineno", None)

        container_id = f"{self.rel_file}::{name}#L{lineno or 0}"
        container = LaunchContainer(
            container_id=container_id,
            name=str(name),
            package=str(package),
            executable=str(executable),
            launch_file=self.rel_file,
            line_number=lineno,
            namespace=str(namespace),
            condition=str(condition) if condition else None,
            deployment_profile="composable"
        )
        self.containers.append(container)

        # Check for composable_node_descriptions directly inside container
        for kw in node.keywords:
            if kw.arg == "composable_node_descriptions" and isinstance(kw.value, (ast.List, ast.Tuple)):
                for comp_call in kw.value.elts:
                    if isinstance(comp_call, ast.Call):
                        for sub in ast.walk(comp_call):
                            self.processed_action_nodes.add(id(sub))
                        self._extract_composable_node(comp_call, str(name), context)

    def _handle_load_composable_nodes(self, node: ast.Call, context: LaunchContext):
        """Extract LoadComposableNodes action and all contained ComposableNodes"""
        target_container = self.evaluator._get_arg_val(node, 0, "target_container")
        condition = self.evaluator._get_arg_val(node, 1, "condition")
        lineno = getattr(node, "lineno", None)

        container_str = ""
        if isinstance(target_container, (list, tuple)):
            container_str = str(target_container[-1])
        elif target_container:
            container_str = str(target_container)
        else:
            container_str = context.container_name or "container"

        # Find composable node descriptions list
        comp_nodes = []
        for kw in node.keywords:
            if kw.arg == "composable_node_descriptions" and isinstance(kw.value, (ast.List, ast.Tuple)):
                comp_nodes = kw.value.elts
            elif kw.arg == "condition":
                c = self.evaluator.eval_node(kw.value)
                if c:
                    condition = str(c)

        if not comp_nodes and len(node.args) > 1 and isinstance(node.args[1], (ast.List, ast.Tuple)):
            comp_nodes = node.args[1].elts

        for comp_call in comp_nodes:
            if isinstance(comp_call, ast.Call):
                for sub in ast.walk(comp_call):
                    self.processed_action_nodes.add(id(sub))
                self._extract_composable_node(comp_call, container_str, context, extra_cond=condition)

    def _extract_composable_node(
        self,
        node: ast.Call,
        container_name: str,
        context: LaunchContext,
        extra_cond: Optional[str] = None
    ):
        """Extract a single ComposableNode declaration"""
        package = self.evaluator._get_arg_val(node, 0, "package") or ""
        plugin = self.evaluator._get_arg_val(node, 1, "plugin") or ""
        name = self.evaluator._get_arg_val(node, 2, "name") or ""
        namespace = self.evaluator._get_arg_val(node, 3, "namespace") or ""
        parameters = self.evaluator._get_arg_val(node, 4, "parameters") or []
        remappings = self.evaluator._get_arg_val(node, 5, "remappings") or []
        condition = self.evaluator._get_arg_val(node, 6, "condition") or extra_cond
        lineno = getattr(node, "lineno", None)

        pkg_str = str(package)
        plugin_str = str(plugin)
        effective_name = str(name) if name else (plugin_str.split("::")[-1] or "unnamed_component")

        # Remappings
        norm_remappings = dict(context.remappings)
        if isinstance(remappings, list):
            for r in remappings:
                if isinstance(r, (list, tuple)) and len(r) == 2:
                    norm_remappings[str(r[0])] = str(r[1])
                elif isinstance(r, dict):
                    norm_remappings.update({str(k): str(v) for k, v in r.items()})
        elif isinstance(remappings, dict):
            norm_remappings.update({str(k): str(v) for k, v in remappings.items()})

        # Parameters and separation
        norm_params = list(context.parameters)
        if isinstance(parameters, list):
            norm_params.extend(parameters)
        elif parameters:
            norm_params.append(parameters)

        param_files: List[str] = []
        inline_params: Dict[str, Any] = {}
        for p in norm_params:
            if isinstance(p, dict):
                inline_params.update(p)
            elif isinstance(p, str):
                param_files.append(p.strip())
            elif isinstance(p, (list, tuple)):
                for sub in p:
                    if isinstance(sub, dict):
                        inline_params.update(sub)
                    elif isinstance(sub, str):
                        param_files.append(sub.strip())

        active_ns = context.effective_namespace()
        if namespace:
            active_ns = f"{active_ns}/{str(namespace).strip('/')}".strip("/")

        active_cond = context.effective_condition()
        if condition:
            active_cond = f"{active_cond} and ({condition})" if active_cond else str(condition)

        instance_id = (
            f"{self.rel_file}::{effective_name}#L{lineno or 0}"
            f"[ns={active_ns}|prof=composable|cont={container_name}|parent={context.parent_inclusion_id or 'root'}]"
        )

        evidence = [
            EvidenceItem(
                file=self.rel_file,
                line_start=lineno,
                line_end=getattr(node, "end_lineno", lineno),
                evidence_type=EvidenceType.LAUNCH_NODE,
                source="launch_analyzer",
                confidence=1.0,
                explanation=f"ComposableNode loaded into '{container_name}': pkg='{pkg_str}', plugin='{plugin_str}', name='{effective_name}'"
            )
        ]

        instance = LaunchInstance(
            instance_id=instance_id,
            node_name=effective_name,
            package=pkg_str,
            executable=None,
            plugin_class=plugin_str,
            launch_file=self.rel_file,
            line_number=lineno,
            parent_inclusion_id=context.parent_inclusion_id,
            namespace=active_ns,
            remappings=norm_remappings,
            parameters=norm_params,
            is_composable=True,
            container_name=container_name,
            condition=active_cond,
            deployment_profile="composable",
            launch_arguments=dict(context.passed_arguments),
            evidence=evidence,
            repository_name=self.package_name,
            action_type="ComposableNode",
            is_lifecycle=False,
            parameter_files=param_files,
            inline_parameters=inline_params,
            lifecycle_info=None,
            resolution_status=ResolutionStatus.RESOLVED
        )
        self.instances.append(instance)

        # Update host container with loaded component reference
        for c in self.containers:
            if c.name == container_name:
                if instance_id not in c.loaded_components:
                    c.loaded_components.append(instance_id)

        # LaunchNode for backward compatibility
        lnode = LaunchNode(
            node_name=effective_name,
            package=pkg_str,
            executable="",
            plugin=plugin_str,
            namespace=active_ns,
            remappings=norm_remappings,
            parameters=norm_params,
            is_composable=True,
            target_container=container_name,
            condition=active_cond,
            line_start=lineno,
            action_type="ComposableNode",
            is_lifecycle=False,
            parameter_files=param_files,
            inline_parameters=inline_params,
            lifecycle_info=None,
            resolution_status=ResolutionStatus.RESOLVED
        )
        self.launch_file.nodes.append(lnode)

    def _handle_include(self, node: ast.Call, context: LaunchContext):
        """Extract IncludeLaunchDescription action with target resolution"""
        source = self.evaluator._get_arg_val(node, 0, "launch_description_source") or self.evaluator._get_arg_val(node, 0)
        launch_args = self.evaluator._get_arg_val(node, 1, "launch_arguments") or {}
        condition = self.evaluator._get_arg_val(node, 2, "condition") or context.effective_condition()
        lineno = getattr(node, "lineno", None)

        file_expr = str(source) if source else ""
        norm_args: Dict[str, str] = {}
        if isinstance(launch_args, dict):
            norm_args = {str(k): str(v) for k, v in launch_args.items()}
        elif isinstance(launch_args, list):
            for item in launch_args:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    norm_args[str(item[0])] = str(item[1])

        # Resolve path against repository
        resolved_path, res_status = self._resolve_include_path(file_expr)

        include = LaunchInclude(
            file_path=file_expr,
            resolved_path=resolved_path,
            launch_arguments=norm_args,
            condition=str(condition) if condition else None,
            line_start=lineno,
            included_by=self.rel_file,
            resolution_status=res_status
        )
        self.launch_file.includes.append(include)

    def _resolve_include_path(self, file_expr: str) -> Tuple[Optional[str], ResolutionStatus]:
        """Safely resolve an included launch file expression to an actual file"""
        if not file_expr or file_expr.startswith("<share:unknown>"):
            return None, ResolutionStatus.UNRESOLVED

        # 1. Clean expression
        clean_expr = file_expr.replace("\\", "/").strip("'\"")

        # 2. Check if absolute path inside repo
        if self.repo_path:
            abs_repo = self.repo_path.resolve()
            try:
                candidate = Path(clean_expr).resolve()
                if candidate.exists() and candidate.is_file():
                    try:
                        return str(candidate.relative_to(abs_repo)).replace("\\", "/"), ResolutionStatus.RESOLVED
                    except ValueError:
                        pass
            except Exception:
                pass

            # 3. Check relative to current launch file directory
            candidate = (self.file_path.parent / clean_expr).resolve()
            if candidate.exists() and candidate.is_file():
                try:
                    return str(candidate.relative_to(abs_repo)).replace("\\", "/"), ResolutionStatus.RESOLVED
                except ValueError:
                    return str(candidate).replace("\\", "/"), ResolutionStatus.RESOLVED

            # 4. Check relative to repo root
            candidate = (abs_repo / clean_expr).resolve()
            if candidate.exists() and candidate.is_file():
                try:
                    return str(candidate.relative_to(abs_repo)).replace("\\", "/"), ResolutionStatus.RESOLVED
                except ValueError:
                    pass

            # 5. Extract filename and find across packages
            fname = Path(clean_expr).name
            if fname.endswith((".py", ".xml", ".yaml")):
                for pkg_name, pkg_rel in self.packages_map.items():
                    candidate = (abs_repo / pkg_rel / "launch" / fname).resolve()
                    if candidate.exists():
                        try:
                            return str(candidate.relative_to(abs_repo)).replace("\\", "/"), ResolutionStatus.RESOLVED
                        except ValueError:
                            pass

        return clean_expr if clean_expr else None, ResolutionStatus.UNRESOLVED


# ============================================================================
# XML Launch File Parser (Updated for Phase 2)
# ============================================================================

class XMLLaunchParser:
    """Parser for ROS2 XML launch files (.launch.xml)"""

    def __init__(
        self,
        file_path: Path,
        package_name: str,
        repo_path: Optional[Path] = None,
        packages_map: Optional[Dict[str, str]] = None
    ):
        self.file_path = file_path
        self.package_name = package_name
        self.repo_path = repo_path.resolve() if repo_path else None
        self.packages_map = packages_map or {}

        if self.repo_path:
            try:
                self.rel_file = str(file_path.resolve().relative_to(self.repo_path)).replace("\\", "/")
            except ValueError:
                self.rel_file = str(file_path).replace("\\", "/")
        else:
            self.rel_file = str(file_path).replace("\\", "/")

        self.launch_file = LaunchFile(
            file_path=self.rel_file,
            package_name=package_name,
            launch_type="xml"
        )
        self.instances: List[LaunchInstance] = []
        self.containers: List[LaunchContainer] = []

    def parse(self) -> LaunchFile:
        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()
            context = LaunchContext()
            self._parse_elements(root, context)
        except Exception as e:
            logger.warning(f"Error parsing XML launch {self.file_path}: {e}")

        self.launch_file.instances = self.instances
        self.launch_file.containers = self.containers
        return self.launch_file

    def _parse_elements(self, parent: ET.Element, context: LaunchContext):
        for child in parent:
            tag = child.tag.split("}")[-1]

            if tag in ("node", "lifecycle_node", "lifecycle-node"):
                is_lifecycle = tag in ("lifecycle_node", "lifecycle-node") or child.get("lifecycle") in ("true", "1")
                self._parse_node(child, context, is_lifecycle=is_lifecycle)
            elif tag in ("composable-node-container", "node_container"):
                self._parse_container(child, context)
            elif tag in ("composable-node", "load_composable_node"):
                self._parse_composable_node(child, context)
            elif tag == "include":
                self._parse_include(child, context)
            elif tag == "group":
                grp_ctx = context.clone()
                ns = child.get("ns") or child.get("namespace")
                cond = child.get("if") or child.get("unless")
                if ns:
                    grp_ctx.namespaces.append(ns)
                if cond:
                    grp_ctx.conditions.append(cond)
                self._parse_elements(child, grp_ctx)
            elif tag in ("push-ros-namespace", "push_ros_namespace"):
                ns = child.get("namespace") or child.text
                if ns:
                    context.namespaces.append(ns.strip())
            elif tag in ("arg", "declare_launch_argument"):
                name = child.get("name")
                default = child.get("default") or child.get("value")
                doc = child.get("doc") or child.get("description")
                if name:
                    self.launch_file.arguments[name] = {"default": default, "description": doc}

    def _parse_node(self, elem: ET.Element, context: LaunchContext, is_lifecycle: bool = False):
        pkg = elem.get("pkg") or elem.get("package") or ""
        exec_name = elem.get("exec") or elem.get("executable") or ""
        name = elem.get("name") or exec_name or "unnamed_node"
        ns = elem.get("namespace") or context.effective_namespace()
        cond = elem.get("if") or elem.get("unless") or context.effective_condition()

        is_container = pkg == "rclcpp_components" or "component_container" in exec_name

        if is_container:
            cid = f"{self.rel_file}::{name}"
            self.containers.append(LaunchContainer(
                container_id=cid,
                name=name,
                package=pkg,
                executable=exec_name,
                launch_file=self.rel_file,
                namespace=ns,
                condition=cond,
                deployment_profile="composable"
            ))
            return

        action_type = "LifecycleNode" if is_lifecycle else "Node"
        instance_id = f"{self.rel_file}::{name}[ns={ns}|prof=default|parent=root]"
        evidence = [
            EvidenceItem(
                file=self.rel_file,
                line_start=None,
                evidence_type=EvidenceType.LAUNCH_NODE,
                source="xml_launch_analyzer",
                confidence=1.0,
                explanation=f"XML {action_type} declared: pkg='{pkg}', exec='{exec_name}', name='{name}'"
            )
        ]

        instance = LaunchInstance(
            instance_id=instance_id,
            node_name=name,
            package=pkg,
            executable=exec_name,
            launch_file=self.rel_file,
            namespace=ns,
            condition=cond,
            deployment_profile="default",
            evidence=evidence,
            repository_name=self.package_name,
            action_type=action_type,
            is_lifecycle=is_lifecycle,
            resolution_status=ResolutionStatus.RESOLVED
        )
        self.instances.append(instance)
        self.launch_file.nodes.append(LaunchNode(
            node_name=name,
            package=pkg,
            executable=exec_name,
            namespace=ns,
            condition=cond,
            action_type=action_type,
            is_lifecycle=is_lifecycle,
            resolution_status=ResolutionStatus.RESOLVED
        ))

    def _parse_container(self, elem: ET.Element, context: LaunchContext):
        name = elem.get("name") or "container"
        pkg = elem.get("package") or "rclcpp_components"
        exec_name = elem.get("executable") or "component_container"
        ns = elem.get("namespace") or context.effective_namespace()
        cid = f"{self.rel_file}::{name}"
        container = LaunchContainer(
            container_id=cid,
            name=name,
            package=pkg,
            executable=exec_name,
            launch_file=self.rel_file,
            namespace=ns,
            deployment_profile="composable"
        )
        self.containers.append(container)
        for child in elem:
            if child.tag.split("}")[-1] in ("composable-node", "node"):
                self._parse_composable_node(child, context, container_name=name)

    def _parse_composable_node(self, elem: ET.Element, context: LaunchContext, container_name: str = "container"):
        pkg = elem.get("package") or elem.get("pkg") or ""
        plugin = elem.get("plugin") or ""
        name = elem.get("name") or plugin.split("::")[-1] or "unnamed_component"
        ns = elem.get("namespace") or context.effective_namespace()

        instance_id = f"{self.rel_file}::{name}[ns={ns}|prof=composable|cont={container_name}|parent=root]"
        evidence = [
            EvidenceItem(
                file=self.rel_file,
                line_start=None,
                evidence_type=EvidenceType.LAUNCH_NODE,
                source="xml_launch_analyzer",
                confidence=1.0,
                explanation=f"XML ComposableNode: pkg='{pkg}', plugin='{plugin}', name='{name}'"
            )
        ]

        instance = LaunchInstance(
            instance_id=instance_id,
            node_name=name,
            package=pkg,
            plugin_class=plugin,
            launch_file=self.rel_file,
            namespace=ns,
            is_composable=True,
            container_name=container_name,
            deployment_profile="composable",
            evidence=evidence
        )
        self.instances.append(instance)
        self.launch_file.nodes.append(LaunchNode(
            node_name=name,
            package=pkg,
            plugin=plugin,
            is_composable=True,
            target_container=container_name,
            namespace=ns
        ))

    def _parse_include(self, elem: ET.Element, context: LaunchContext):
        file_attr = elem.get("file") or elem.get("launch-file") or ""
        args = {child.get("name"): child.get("value") for child in elem if child.tag.split("}")[-1] == "arg" and child.get("name")}
        cond = elem.get("if") or elem.get("unless") or context.effective_condition()
        self.launch_file.includes.append(LaunchInclude(
            file_path=file_attr,
            launch_arguments=args,
            condition=cond,
            included_by=self.rel_file
        ))


# ============================================================================
# Recursive Launch Resolution (Loop-Safe)
# ============================================================================

class RecursiveLaunchResolver:
    """
    Recursively resolves IncludeLaunchDescription chains across the repository.
    Enforces a cycle-prevention set to safely handle recursive inclusions.
    Propagates launch arguments, scoped namespaces, and conditions.
    """

    def __init__(
        self,
        launch_files_map: Dict[str, LaunchFile],
        repo_path: Optional[Path] = None,
        max_depth: int = 15
    ):
        self.launch_files_map = launch_files_map
        self.repo_path = repo_path
        self.max_depth = max_depth

    def resolve_all_hierarchies(self) -> List[LaunchInstance]:
        """
        Traverse inclusion trees and generate hierarchical LaunchInstances
        carrying parent inclusion context and propagated arguments.
        """
        hierarchical_instances: List[LaunchInstance] = []
        visited_inclusions: Set[Tuple[str, str]] = set()

        # Identify root launch files (files not included by any other file)
        all_included = {inc.resolved_path for lf in self.launch_files_map.values() for inc in lf.includes if inc.resolved_path}
        root_files = [path for path in self.launch_files_map if path not in all_included]

        if not root_files:
            root_files = list(self.launch_files_map.keys())

        for root_path in root_files:
            root_lf = self.launch_files_map[root_path]
            # Add root instances directly
            hierarchical_instances.extend(root_lf.instances)
            # Recurse through its inclusions
            self._recurse_includes(
                parent_lf=root_lf,
                parent_inc_id=f"root::{root_lf.file_path}",
                parent_args={},
                parent_ns="",
                parent_cond="",
                depth=0,
                visited=set(visited_inclusions),
                collector=hierarchical_instances
            )

        return hierarchical_instances

    def _recurse_includes(
        self,
        parent_lf: LaunchFile,
        parent_inc_id: str,
        parent_args: Dict[str, str],
        parent_ns: str,
        parent_cond: str,
        depth: int,
        visited: Set[Tuple[str, str]],
        collector: List[LaunchInstance]
    ):
        if depth >= self.max_depth:
            logger.warning(f"Max inclusion depth {self.max_depth} reached at {parent_lf.file_path}")
            return

        for inc in parent_lf.includes:
            target_path = inc.resolved_path
            if not target_path or target_path not in self.launch_files_map:
                continue

            # Loop detection
            pair = (parent_lf.file_path, target_path)
            if pair in visited:
                logger.debug(f"Inclusion loop prevented: {pair}")
                continue
            new_visited = set(visited)
            new_visited.add(pair)

            # Combined arguments
            combined_args = dict(parent_args)
            combined_args.update(inc.launch_arguments)

            # Scoped namespace
            combined_ns = parent_ns
            if inc.launch_arguments.get("namespace"):
                sub_ns = inc.launch_arguments["namespace"].strip("/")
                combined_ns = f"{combined_ns}/{sub_ns}".strip("/") if combined_ns else sub_ns

            # Scoped condition
            combined_cond = parent_cond
            if inc.condition:
                combined_cond = f"{combined_cond} and ({inc.condition})" if combined_cond else inc.condition

            target_lf = self.launch_files_map[target_path]
            current_inc_id = f"{parent_inc_id}->{target_path}#L{inc.line_start or 0}"

            # Create scoped child instances for this inclusion
            for base_inst in target_lf.instances:
                eff_ns = combined_ns
                if base_inst.namespace:
                    eff_ns = f"{combined_ns}/{base_inst.namespace.strip('/')}".strip("/") if combined_ns else base_inst.namespace

                eff_cond = combined_cond
                if base_inst.condition:
                    eff_cond = f"{combined_cond} and ({base_inst.condition})" if combined_cond else base_inst.condition

                eff_prof = base_inst.deployment_profile
                if combined_args.get("use_composition") in ("True", "true"):
                    eff_prof = "composable"
                elif combined_args.get("use_composition") in ("False", "false"):
                    eff_prof = "standalone"

                scoped_id = (
                    f"{base_inst.launch_file}::{base_inst.node_name}#L{base_inst.line_number or 0}"
                    f"[ns={eff_ns}|prof={eff_prof}|parent={current_inc_id}]"
                )

                child_instance = LaunchInstance(
                    instance_id=scoped_id,
                    node_name=base_inst.node_name,
                    package=base_inst.package,
                    executable=base_inst.executable,
                    plugin_class=base_inst.plugin_class,
                    launch_file=base_inst.launch_file,
                    line_number=base_inst.line_number,
                    parent_inclusion_id=current_inc_id,
                    namespace=eff_ns,
                    remappings=dict(base_inst.remappings),
                    parameters=list(base_inst.parameters),
                    arguments=list(base_inst.arguments),
                    is_composable=base_inst.is_composable,
                    container_name=base_inst.container_name,
                    condition=eff_cond,
                    deployment_profile=eff_prof,
                    launch_arguments=combined_args,
                    evidence=list(base_inst.evidence),
                    repository_name=base_inst.repository_name,
                    action_type=base_inst.action_type,
                    is_lifecycle=base_inst.is_lifecycle,
                    parameter_files=list(base_inst.parameter_files),
                    inline_parameters=dict(base_inst.inline_parameters),
                    lifecycle_info=base_inst.lifecycle_info,
                    resolution_status=base_inst.resolution_status
                )
                collector.append(child_instance)

            # Recurse deeper
            self._recurse_includes(
                parent_lf=target_lf,
                parent_inc_id=current_inc_id,
                parent_args=combined_args,
                parent_ns=combined_ns,
                parent_cond=combined_cond,
                depth=depth + 1,
                visited=new_visited,
                collector=collector
            )


# ============================================================================
# Phase 1 Node Inventory Resolver & Mapping Engine
# ============================================================================

class NodeLaunchMapper:
    """
    Connects LaunchInstances with Phase 1 ROS2Node inventory.
    Enforces strict ambiguity handling:
      - RESOLVED: Single matching candidate implementation
      - AMBIGUOUS: Multiple matching candidates (preserves all candidate IDs)
      - EXTERNAL_DEPENDENCY: Package/executable belongs to external dependency
      - UNRESOLVED: In-repo entity with unresolvable source mapping
    Never fabricates synthetic ROS2Nodes in nodes inventory.
    """

    def __init__(
        self,
        nodes: List[ROS2Node],
        packages_map: Dict[str, str],
        cmake_info_map: Optional[Dict[str, Any]] = None
    ):
        self.nodes = nodes
        self.packages_map = packages_map
        self.cmake_info_map = cmake_info_map or {}

        # Index Phase 1 nodes for efficient, ambiguous-safe querying
        self.nodes_by_id: Dict[str, ROS2Node] = {n.id: n for n in nodes}
        self.nodes_by_pkg_and_class: Dict[Tuple[str, str], List[ROS2Node]] = {}
        self.nodes_by_pkg_and_exec: Dict[Tuple[str, str], List[ROS2Node]] = {}

        for n in nodes:
            # 1. Package + Class Name
            cls_key = (n.package_name, n.class_name)
            self.nodes_by_pkg_and_class.setdefault(cls_key, []).append(n)

            # Also index by short class name if qualified
            if "::" in n.class_name:
                short_cls_key = (n.package_name, n.class_name.split("::")[-1])
                if short_cls_key != cls_key:
                    self.nodes_by_pkg_and_class.setdefault(short_cls_key, []).append(n)

            # Also index by component_name if registered
            if n.component_name:
                comp_key = (n.package_name, n.component_name)
                self.nodes_by_pkg_and_class.setdefault(comp_key, []).append(n)

            # 2. Package + Executable Target
            if n.executable:
                exec_key = (n.package_name, n.executable)
                self.nodes_by_pkg_and_exec.setdefault(exec_key, []).append(n)

    def resolve_instance(self, instance: LaunchInstance) -> LaunchInstance:
        """Resolve a single LaunchInstance against Phase 1 inventory with ambiguity tracking"""
        pkg = instance.package
        is_in_repo = pkg in self.packages_map

        # Case 1: Composable Component (Plugin Class is primary key)
        if instance.is_composable and instance.plugin_class:
            candidates = self._find_composable_candidates(pkg, instance.plugin_class)
            self._apply_resolution_results(instance, candidates, is_in_repo)
            return instance

        # Case 2: Standalone Executable
        if instance.executable:
            candidates = self._find_executable_candidates(pkg, instance.executable, instance.node_name)
            self._apply_resolution_results(instance, candidates, is_in_repo)
            return instance

        # Case 3: Only Node Name provided
        if is_in_repo:
            instance.mapping_status = LaunchMappingStatus.UNRESOLVED
        else:
            instance.mapping_status = LaunchMappingStatus.EXTERNAL_DEPENDENCY
        return instance

    def _find_composable_candidates(self, pkg: str, plugin_class: str) -> List[ROS2Node]:
        """Find matching source nodes for a ComposableNode plugin declaration"""
        # Exact match (pkg, plugin_class)
        matches = self.nodes_by_pkg_and_class.get((pkg, plugin_class), [])
        if matches:
            return matches

        # Short name match
        short_plugin = plugin_class.split("::")[-1]
        matches = self.nodes_by_pkg_and_class.get((pkg, short_plugin), [])
        if matches:
            return matches

        # Cross-package match if package differs or namespaced differently
        for (p, cls), n_list in self.nodes_by_pkg_and_class.items():
            if cls == plugin_class or cls.endswith(f"::{short_plugin}"):
                return n_list

        return []

    def _find_executable_candidates(self, pkg: str, executable: str, node_name: str) -> List[ROS2Node]:
        """Find matching source nodes for an executable target with ambiguity awareness"""
        matches = list(self.nodes_by_pkg_and_exec.get((pkg, executable), []))

        # If multiple classes match this executable, check if node_name cleanly disambiguates
        if len(matches) > 1:
            exact_name_matches = [
                n for n in matches
                if n.name == node_name or n.class_name.split("::")[-1].lower() == node_name.lower()
            ]
            if len(exact_name_matches) == 1:
                return exact_name_matches
            # If still multiple or none, preserve all candidates (Ambiguity requirement)
            return matches

        if matches:
            return matches

        # Fallback: check CMake target mapping if available
        cmake_info = self.cmake_info_map.get(pkg)
        if cmake_info and hasattr(cmake_info, "executables"):
            target = cmake_info.executables.get(executable)
            if target:
                target_matches = [
                    n for n in self.nodes
                    if n.package_name == pkg and any(
                        n.source_file.endswith(s) or s.endswith(n.source_file)
                        for s in target.sources
                    )
                ]
                if target_matches:
                    return target_matches

        # Check by node_name in package
        name_matches = [
            n for n in self.nodes
            if n.package_name == pkg and (n.name == node_name or n.class_name.split("::")[-1].lower() == node_name.lower())
        ]
        return name_matches

    def _apply_resolution_results(
        self,
        instance: LaunchInstance,
        candidates: List[ROS2Node],
        is_in_repo: bool
    ):
        """Assign mapping status without arbitrary selection when ambiguous"""
        # Deduplicate candidates by unique node id
        unique_candidates = list({c.id: c for c in candidates}.values())

        if len(unique_candidates) == 1:
            instance.mapping_status = LaunchMappingStatus.RESOLVED
            instance.node_id = unique_candidates[0].id
            instance.candidate_node_ids = [unique_candidates[0].id]
        elif len(unique_candidates) > 1:
            instance.mapping_status = LaunchMappingStatus.AMBIGUOUS
            instance.node_id = None  # Do not arbitrarily select
            instance.candidate_node_ids = [c.id for c in unique_candidates]
        else:
            instance.candidate_node_ids = []
            if is_in_repo:
                instance.mapping_status = LaunchMappingStatus.UNRESOLVED
            else:
                instance.mapping_status = LaunchMappingStatus.EXTERNAL_DEPENDENCY

    def build_node_mappings(self, instances: List[LaunchInstance]) -> List[NodeLaunchMapping]:
        """Build bidirectional mapping from Phase 1 nodes to their runtime LaunchInstances"""
        # Node ID -> List of instance IDs
        inst_by_node: Dict[str, List[LaunchInstance]] = {}
        for inst in instances:
            if inst.node_id:
                inst_by_node.setdefault(inst.node_id, []).append(inst)

        mappings: List[NodeLaunchMapping] = []
        for node in self.nodes:
            insts = inst_by_node.get(node.id, [])
            inst_ids = [i.instance_id for i in insts]
            launch_files = list(set(i.launch_file for i in insts))
            profiles = list(set(i.deployment_profile for i in insts))

            status = LaunchMappingStatus.RESOLVED if insts else LaunchMappingStatus.UNRESOLVED
            mappings.append(NodeLaunchMapping(
                node_id=node.id,
                class_name=node.class_name,
                package_name=node.package_name,
                source_file=node.source_file,
                mapping_status=status,
                runtime_instances=inst_ids,
                launch_files=launch_files,
                deployment_profiles=profiles
            ))

        return mappings

    def build_deployment_profiles(
        self,
        instances: List[LaunchInstance],
        containers: List[LaunchContainer]
    ) -> List[DeploymentProfile]:
        """Aggregate deployment profiles (standalone, composable, default, conditional)"""
        profile_map: Dict[str, Dict[str, Any]] = {
            "standalone": {
                "condition": "use_composition == False",
                "description": "Standalone ROS2 executable processes",
                "instances": [],
                "containers": [],
                "args": {"use_composition": "False"}
            },
            "composable": {
                "condition": "use_composition == True",
                "description": "Composed ROS2 components hosted in component containers",
                "instances": [],
                "containers": [],
                "args": {"use_composition": "True"}
            },
            "default": {
                "condition": "unconditional",
                "description": "Always active or profile-agnostic nodes",
                "instances": [],
                "containers": [],
                "args": {}
            }
        }

        for inst in instances:
            prof = inst.deployment_profile or "default"
            if prof not in profile_map:
                profile_map[prof] = {
                    "condition": inst.condition or "custom",
                    "description": f"Custom deployment profile: {prof}",
                    "instances": [],
                    "containers": [],
                    "args": {}
                }
            profile_map[prof]["instances"].append(inst.instance_id)

            # Also track distinct launch entry point variants to keep alternative profiles separate
            if inst.launch_file:
                stem = Path(inst.launch_file).stem.replace("_launch", "")
                variant_prof = f"launch_{stem}"
                if variant_prof not in profile_map:
                    profile_map[variant_prof] = {
                        "condition": inst.condition or f"launch={Path(inst.launch_file).name}",
                        "description": f"Alternative standalone launch profile: {Path(inst.launch_file).name}, analyzed independently by default",
                        "instances": [],
                        "containers": [],
                        "args": dict(inst.launch_arguments)
                    }
                if inst.instance_id not in profile_map[variant_prof]["instances"]:
                    profile_map[variant_prof]["instances"].append(inst.instance_id)

        for cont in containers:
            prof = cont.deployment_profile or "composable"
            if prof in profile_map:
                profile_map[prof]["containers"].append(cont.container_id)

        profiles = []
        for pname, pdata in profile_map.items():
            profiles.append(DeploymentProfile(
                profile_name=pname,
                condition=pdata["condition"],
                description=pdata["description"],
                instance_ids=pdata["instances"],
                container_ids=pdata["containers"],
                configuration_args=pdata["args"]
            ))

        return profiles


# ============================================================================
# Main Orchestrator and API Functions
# ============================================================================

def find_launch_files(package_path: Path) -> List[Path]:
    """Find all ROS2 launch files in a directory/package"""
    launch_files: List[Path] = []
    launch_dirs = ["launch", "launches"]
    launch_extensions = (".launch.py", ".launch.xml", ".launch.yaml", ".launch.yml")

    for root, dirs, files in os.walk(package_path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        rel_root = Path(root).relative_to(package_path)
        is_launch_dir = any(part in launch_dirs for part in rel_root.parts)

        for file in files:
            file_lower = file.lower()
            if file_lower.endswith(launch_extensions):
                launch_files.append(Path(root) / file)
            elif is_launch_dir and file_lower.endswith("_launch.py"):
                launch_files.append(Path(root) / file)
            elif is_launch_dir and file_lower.endswith(".py"):
                try:
                    content = (Path(root) / file).read_text(encoding="utf-8", errors="ignore")
                    if "LaunchDescription" in content or "from launch" in content:
                        launch_files.append(Path(root) / file)
                except Exception:
                    pass

    launch_files.sort(key=lambda p: (0 if any(part in launch_dirs for part in p.parts) else 1, str(p)))
    return launch_files


def parse_python_launch_file(
    file_path: Path,
    package_name: str,
    repo_path: Optional[Path] = None,
    packages_map: Optional[Dict[str, str]] = None
) -> LaunchFile:
    """Parse a single Python launch file (.launch.py / *_launch.py)"""
    parser = PythonLaunchParser(file_path, package_name, repo_path=repo_path, packages_map=packages_map)
    return parser.parse()


def parse_xml_launch_file(
    file_path: Path,
    package_name: str,
    repo_path: Optional[Path] = None,
    packages_map: Optional[Dict[str, str]] = None
) -> LaunchFile:
    """Parse a single XML launch file (.launch.xml)"""
    parser = XMLLaunchParser(file_path, package_name, repo_path=repo_path, packages_map=packages_map)
    return parser.parse()


def parse_yaml_launch_file(file_path: Path, package_name: str) -> LaunchFile:
    """Parse a single YAML launch file (.launch.yaml)"""
    import yaml
    launch_file = LaunchFile(
        file_path=str(file_path),
        package_name=package_name,
        launch_type="yaml"
    )
    try:
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            launch_file.arguments = data.get("args", {})
    except Exception as e:
        logger.warning(f"Error parsing YAML launch {file_path}: {e}")
    return launch_file


def analyze_launch_file(
    file_path: Path,
    package_name: str,
    repo_path: Optional[Path] = None,
    packages_map: Optional[Dict[str, str]] = None
) -> LaunchFile:
    """Parse a single launch file based on its extension"""
    suffix = file_path.suffix.lower()
    if suffix == ".py":
        return parse_python_launch_file(file_path, package_name, repo_path, packages_map)
    elif suffix == ".xml":
        return parse_xml_launch_file(file_path, package_name, repo_path, packages_map)
    elif suffix in (".yaml", ".yml"):
        return parse_yaml_launch_file(file_path, package_name)
    else:
        return LaunchFile(
            file_path=str(file_path),
            package_name=package_name,
            launch_type="python"
        )


def check_launch_cmake_installed(pkg_path: Path, launch_file_path: Path) -> bool:
    """
    Check if a launch file is installed via CMakeLists.txt.
    Distinguishes source-present files from CMake-installed files.
    """
    cmakelists = pkg_path / "CMakeLists.txt"
    if not cmakelists.exists():
        return True
    try:
        content = cmakelists.read_text(encoding="utf-8", errors="ignore")
        file_name = launch_file_path.name
        # Check for PATTERN ... EXCLUDE
        pattern_exclude = re.findall(
            r'PATTERN\s+["\']?([^"\'\s]+)["\']?\s+EXCLUDE',
            content,
            re.IGNORECASE
        )
        for pat in pattern_exclude:
            if pat == file_name or (pat.startswith("*") and file_name.endswith(pat[1:])):
                return False
        # Check if launch directory or file is explicitly installed
        has_dir = bool(re.search(r'install\s*\(\s*DIRECTORY\s+.*launch', content, re.IGNORECASE))
        has_file = bool(re.search(r'install\s*\(\s*FILES\s+.*' + re.escape(file_name), content, re.IGNORECASE))
        return has_dir or has_file
    except Exception:
        return True


def analyze_package_launches(
    package_path: Path,
    package_name: str,
    repo_path: Optional[Path] = None,
    packages_map: Optional[Dict[str, str]] = None
) -> List[LaunchFile]:
    """Analyze all launch files in a ROS2 package"""
    launch_files = find_launch_files(package_path)
    results = []
    for lf in launch_files:
        try:
            res = analyze_launch_file(lf, package_name, repo_path, packages_map)
            res.repository_name = package_name
            res.is_cmake_installed = check_launch_cmake_installed(package_path, lf)
            results.append(res)
        except Exception as e:
            logger.warning(f"Failed to parse {lf}: {e}")
    return results


def build_inclusion_graph(launch_files: List[LaunchFile]) -> Dict[str, List[str]]:
    """Build directed inclusion graph of which launch file includes which"""
    graph: Dict[str, List[str]] = {}
    for lf in launch_files:
        includes = []
        for inc in lf.includes:
            if inc.resolved_path:
                includes.append(inc.resolved_path)
            elif inc.file_path:
                includes.append(inc.file_path)
        graph[lf.file_path] = includes
    return graph


def run_launch_analysis(
    repo_path: Path,
    output_path: Path,
    nodes_path: Optional[Path] = None
) -> List[LaunchFile]:
    """
    Backwards-compatible API for Stage 3 execution.
    Analyzes launch files and saves launches.json.
    """
    from src.ingestor import Ingestor

    packages = Ingestor().find_ros2_packages(repo_path)
    all_launch_files: List[LaunchFile] = []

    for pkg_name, pkg_rel in packages.items():
        pkg_path = repo_path / pkg_rel
        launches = analyze_package_launches(pkg_path, pkg_name, repo_path=repo_path, packages_map=packages)
        all_launch_files.extend(launches)

    # Save output
    output_data = [lf.model_dump() for lf in all_launch_files]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Analyzed {len(all_launch_files)} launch files, saved to {output_path}")

    # Also save inclusion graph
    graph = build_inclusion_graph(all_launch_files)
    graph_path = output_path.with_name(output_path.stem + "_graph.json")
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    return all_launch_files


def run_phase2_launch_pipeline(
    repo_path: Path,
    nodes_json_path: Path,
    output_dir: Path
) -> Tuple[List[LaunchFile], List[LaunchInstance], List[NodeLaunchMapping], List[DeploymentProfile]]:
    """
    Complete Phase 2 Pipeline execution:
      1. Parses all launch files (Node, ComposableNode, Container, Groups, Includes)
      2. Performs recursive launch resolution with loop prevention
      3. Maps LaunchInstances to Phase 1 node inventory with ambiguity handling
      4. Synthesizes deployment profiles (standalone vs composable)
      5. Writes all 4 expected JSON output files
    """
    from src.ingestor import Ingestor
    from src.build_analyzer import PackageCMakeInfo

    # 1. Discover packages
    packages = Ingestor().find_ros2_packages(repo_path)
    logger.info(f"Phase 2: Discovered {len(packages)} packages in {repo_path}")

    # 2. Parse all launch files
    all_launch_files: List[LaunchFile] = []
    launch_map: Dict[str, LaunchFile] = {}

    for pkg_name, pkg_rel in packages.items():
        pkg_path = repo_path / pkg_rel
        launches = analyze_package_launches(pkg_path, pkg_name, repo_path=repo_path, packages_map=packages)
        for lf in launches:
            all_launch_files.append(lf)
            launch_map[lf.file_path] = lf

    # 3. Recursive resolution of inclusion hierarchies
    resolver = RecursiveLaunchResolver(launch_map, repo_path=repo_path)
    all_hierarchical_instances = resolver.resolve_all_hierarchies()

    # If no hierarchical instances found, fallback to direct instances
    if not all_hierarchical_instances:
        for lf in all_launch_files:
            all_hierarchical_instances.extend(lf.instances)

    # De-duplicate instances by instance_id
    seen_ids: Set[str] = set()
    unique_instances: List[LaunchInstance] = []
    for inst in all_hierarchical_instances:
        if inst.instance_id not in seen_ids:
            seen_ids.add(inst.instance_id)
            unique_instances.append(inst)

    # Collect containers
    all_containers: List[LaunchContainer] = []
    for lf in all_launch_files:
        all_containers.extend(lf.containers)

    # 4. Load Phase 1 Nodes Inventory
    nodes: List[ROS2Node] = []
    if nodes_json_path.exists():
        with open(nodes_json_path, "r", encoding="utf-8") as f:
            nodes_data = json.load(f)
            nodes = [ROS2Node.model_validate(n) for n in nodes_data]
        logger.info(f"Loaded {len(nodes)} Phase 1 nodes from {nodes_json_path}")
    else:
        logger.warning(f"Phase 1 nodes file not found at {nodes_json_path}")

    # 5. Map LaunchInstances to Phase 1 inventory with ambiguity tracking
    mapper = NodeLaunchMapper(nodes, packages_map=packages)
    resolved_instances: List[LaunchInstance] = []
    for inst in unique_instances:
        resolved_inst = mapper.resolve_instance(inst)
        resolved_instances.append(resolved_inst)

    node_mappings = mapper.build_node_mappings(resolved_instances)
    deployment_profiles = mapper.build_deployment_profiles(resolved_instances, all_containers)

    # 6. Save all 4 required JSON outputs
    output_dir.mkdir(parents=True, exist_ok=True)

    launches_out = output_dir / "launches.json"
    with open(launches_out, "w", encoding="utf-8") as f:
        json.dump([lf.model_dump() for lf in all_launch_files], f, indent=2)

    instances_out = output_dir / "launch_instances.json"
    with open(instances_out, "w", encoding="utf-8") as f:
        json.dump([inst.model_dump() for inst in resolved_instances], f, indent=2)

    mapping_out = output_dir / "node_launch_mapping.json"
    with open(mapping_out, "w", encoding="utf-8") as f:
        json.dump([m.model_dump() for m in node_mappings], f, indent=2)

    profiles_out = output_dir / "deployment_profiles.json"
    with open(profiles_out, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in deployment_profiles], f, indent=2)

    try:
        from src.repo_identity import resolve_repository_identity, attach_artifact_provenance
        repo_info = resolve_repository_identity(repo_path)
        attach_artifact_provenance(launches_out, repo_info)
        attach_artifact_provenance(instances_out, repo_info)
        attach_artifact_provenance(mapping_out, repo_info)
        attach_artifact_provenance(profiles_out, repo_info)
    except Exception as e:
        logger.warning(f"Could not attach provenance to launch artifacts: {e}")

    logger.info(
        f"Phase 2 Complete:\n"
        f"  - Parsed {len(all_launch_files)} launch files -> {launches_out}\n"
        f"  - Resolved {len(resolved_instances)} launch instances -> {instances_out}\n"
        f"  - Mapped {len(node_mappings)} nodes -> {mapping_out}\n"
        f"  - Generated {len(deployment_profiles)} deployment profiles -> {profiles_out}"
    )

    return all_launch_files, resolved_instances, node_mappings, deployment_profiles


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    repo_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("case_studies/nav2")
    nodes_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output/nav2_pipeline/nodes.json")
    out_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("output/phase2")

    run_phase2_launch_pipeline(repo_dir, nodes_file, out_dir)
