"""
ArchSynth BuildAnalyzer - Parse CMakeLists.txt and package.xml for ROS2 packages.
Extracts executables, libraries, component registrations, and plugin exports.
Maps executable targets to source files and implementation classes.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CMakeExecutable:
    name: str
    sources: List[str] = field(default_factory=list)
    linked_libraries: List[str] = field(default_factory=list)
    is_test: bool = False
    package_name: str = ""
    cmake_file: str = ""
    line_number: Optional[int] = None


@dataclass
class CMakeLibrary:
    name: str
    sources: List[str] = field(default_factory=list)
    is_shared: bool = True
    package_name: str = ""
    cmake_file: str = ""
    line_number: Optional[int] = None


@dataclass
class CMakeComponent:
    library_name: str
    class_name: str
    package_name: str = ""
    cmake_file: str = ""
    line_number: Optional[int] = None


@dataclass
class CMakePlugin:
    base_package: str
    description_file: str
    package_name: str = ""
    cmake_file: str = ""
    line_number: Optional[int] = None


@dataclass
class PackageCMakeInfo:
    package_name: str
    package_path: Path
    executables: Dict[str, CMakeExecutable] = field(default_factory=dict)
    libraries: Dict[str, CMakeLibrary] = field(default_factory=dict)
    components: List[CMakeComponent] = field(default_factory=list)
    plugins: List[CMakePlugin] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)

    def find_executable_for_source_or_class(
        self,
        source_file: str,
        class_name: str,
        fully_qualified_class: str
    ) -> Optional[CMakeExecutable]:
        """
        Map an implementation class or source file to its target CMake executable.
        Checks:
        1. Executable directly compiles source file
        2. Executable links to library that compiles source file
        3. Executable links to library that registered this component class
        4. Package-level executable fallback if target name aligns with class/node
        """
        norm_source = source_file.replace("\\", "/")
        norm_stem = Path(norm_source).stem

        # 1. Direct source match
        for ex in self.executables.values():
            if any(norm_source.endswith(s) or s.endswith(norm_source) for s in ex.sources):
                return ex

        # 2. Library link match
        # Find which libraries contain this source file or header stem
        containing_libs = set()
        for lib in self.libraries.values():
            if any(norm_source.endswith(s) or s.endswith(norm_source) or norm_stem == Path(s).stem for s in lib.sources):
                containing_libs.add(lib.name)

        # Also find component libraries for this class
        comp_libs = set()
        for comp in self.components:
            if comp.class_name in (class_name, fully_qualified_class) or \
               comp.class_name.endswith(f"::{class_name}"):
                comp_libs.add(comp.library_name)
                containing_libs.add(comp.library_name)

        # First priority: executables linking a library where this class was explicitly registered as a component
        for ex in self.executables.values():
            if any(lib in ex.linked_libraries for lib in comp_libs):
                return ex

        # Second priority: executables linking libraries containing the source file, matching class name alignment
        short_cls = class_name.split("::")[-1].lower()
        for ex in self.executables.values():
            if any(lib in ex.linked_libraries for lib in containing_libs):
                ex_clean = ex.name.lower().replace("-", "_")
                if short_cls in ex_clean or ex_clean in short_cls:
                    return ex

        # 3. Executable source inspects or includes class_name or stem
        for ex in self.executables.values():
            for s in ex.sources:
                if norm_stem in s or Path(s).stem == f"{norm_stem}_node":
                    return ex

        # 3. Name heuristic: if only one non-test executable exists and name aligns with package or class
        non_test_execs = [ex for ex in self.executables.values() if not ex.is_test]
        short_cls = class_name.split("::")[-1].lower()
        for ex in non_test_execs:
            ex_lower = ex.name.lower().replace("-", "_")
            if ex_lower in short_cls or short_cls in ex_lower or ex_lower == self.package_name.lower():
                return ex

        return None


def _tokenize_cmake_arguments(arg_str: str) -> List[str]:
    """Tokenize arguments inside a CMake command, respecting quotes and spaces."""
    tokens = []
    current = []
    in_quotes = False
    escape = False

    for char in arg_str:
        if escape:
            current.append(char)
            escape = False
        elif char == '\\':
            escape = True
        elif char == '"':
            in_quotes = not in_quotes
        elif char in (' ', '\t', '\r', '\n') and not in_quotes:
            if current:
                token = "".join(current).strip()
                if token:
                    tokens.append(token)
                current = []
        else:
            current.append(char)

    if current:
        token = "".join(current).strip()
        if token:
            tokens.append(token)

    return tokens


def _resolve_variables(val: str, variables: Dict[str, str]) -> str:
    """Resolve ${VAR} references using known variables."""
    if not isinstance(val, str) or '$' not in val:
        return val

    # Iteratively replace ${VAR}
    for _ in range(5):
        match = re.search(r'\$\{([A-Za-z0-9_]+)\}', val)
        if not match:
            break
        var_name = match.group(1)
        replacement = variables.get(var_name, "")
        val = val[:match.start()] + replacement + val[match.end():]

    return val


def parse_cmake_file(
    cmake_path: Path,
    package_path: Path,
    package_name: str,
    inherited_vars: Optional[Dict[str, str]] = None,
    is_test_dir: bool = False
) -> PackageCMakeInfo:
    """Parse a single CMakeLists.txt file and return extracted declarations."""
    info = PackageCMakeInfo(
        package_name=package_name,
        package_path=package_path,
        variables=dict(inherited_vars or {})
    )
    info.variables["PROJECT_NAME"] = package_name

    if not cmake_path.exists():
        return info

    try:
        content = cmake_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Failed to read {cmake_path}: {e}")
        return info

    # Track line numbers for commands
    # Matches: command_name\s*\((.*?)\) with multiline support
    command_pattern = re.compile(r'([A-Za-z0-9_]+)\s*\((.*?)\)', re.DOTALL)
    
    in_testing_block = is_test_dir

    for match in command_pattern.finditer(content):
        cmd = match.group(1).lower()
        args_raw = match.group(2)
        start_idx = match.start()
        line_num = content[:start_idx].count('\n') + 1

        tokens = _tokenize_cmake_arguments(args_raw)
        resolved_tokens = [_resolve_variables(t, info.variables) for t in tokens]

        # 1. Project name
        if cmd == "project" and resolved_tokens:
            info.variables["PROJECT_NAME"] = resolved_tokens[0]

        # 2. Variable assignments: set(VAR VALUE...)
        elif cmd == "set" and len(resolved_tokens) >= 2:
            var_name = tokens[0]  # don't resolve variable name itself
            var_val = " ".join(resolved_tokens[1:])
            info.variables[var_name] = var_val

        # 3. Testing blocks
        elif cmd == "if" and resolved_tokens:
            cond = " ".join(resolved_tokens).upper()
            if "BUILD_TESTING" in cond or "AMENT_ENABLE_TESTING" in cond:
                in_testing_block = True
        elif cmd == "endif":
            in_testing_block = is_test_dir

        # 4. Executables: add_executable(target_name source1 source2...)
        elif cmd == "add_executable" and resolved_tokens:
            target_name = resolved_tokens[0]
            if not target_name:
                continue

            raw_sources = resolved_tokens[1:]
            sources = []
            for s in raw_sources:
                if s.upper() in ("WIN32", "MACOSX_BUNDLE", "EXCLUDE_FROM_ALL"):
                    continue
                # Skip target linkage keywords or options
                if s.startswith("-") or "${" in s:
                    continue
                # Normalize relative path to package_path
                cmake_rel_dir = cmake_path.parent.relative_to(package_path)
                source_path = cmake_rel_dir / s if str(cmake_rel_dir) != "." else Path(s)
                sources.append(str(source_path).replace("\\", "/"))

            is_test = (
                in_testing_block or
                is_test_dir or
                target_name.startswith("test_") or
                target_name.endswith("_test") or
                "test" in str(cmake_path).lower()
            )

            rel_cmake = str(cmake_path.relative_to(package_path)).replace("\\", "/")
            info.executables[target_name] = CMakeExecutable(
                name=target_name,
                sources=sources,
                is_test=is_test,
                package_name=package_name,
                cmake_file=rel_cmake,
                line_number=line_num
            )

        # 5. Libraries: add_library(target_name [STATIC|SHARED] source1 source2...)
        elif cmd == "add_library" and resolved_tokens:
            target_name = resolved_tokens[0]
            if not target_name:
                continue

            raw_sources = resolved_tokens[1:]
            sources = []
            is_shared = True
            for s in raw_sources:
                if s.upper() == "STATIC":
                    is_shared = False
                    continue
                if s.upper() in ("SHARED", "MODULE", "EXCLUDE_FROM_ALL", "INTERFACE", "OBJECT"):
                    continue
                if s.startswith("-") or "${" in s:
                    continue
                cmake_rel_dir = cmake_path.parent.relative_to(package_path)
                source_path = cmake_rel_dir / s if str(cmake_rel_dir) != "." else Path(s)
                sources.append(str(source_path).replace("\\", "/"))

            rel_cmake = str(cmake_path.relative_to(package_path)).replace("\\", "/")
            info.libraries[target_name] = CMakeLibrary(
                name=target_name,
                sources=sources,
                is_shared=is_shared,
                package_name=package_name,
                cmake_file=rel_cmake,
                line_number=line_num
            )

        # 6. Target link libraries
        elif cmd == "target_link_libraries" and len(resolved_tokens) >= 2:
            target_name = resolved_tokens[0]
            linked = []
            for t in resolved_tokens[1:]:
                if t.upper() in ("PUBLIC", "PRIVATE", "INTERFACE"):
                    continue
                if not t.startswith("-") and not t.startswith("$<"):
                    clean_t = t.split("::")[-1]
                    linked.append(clean_t)
                    if t != clean_t:
                        linked.append(t)
            if target_name in info.executables:
                info.executables[target_name].linked_libraries.extend(linked)

        # 7. Component Registration: rclcpp_components_register_nodes(lib "Class1" "Class2"...)
        elif cmd == "rclcpp_components_register_nodes" and len(resolved_tokens) >= 2:
            lib_target = resolved_tokens[0]
            for cls in resolved_tokens[1:]:
                clean_cls = cls.strip('"').strip("'")
                if clean_cls:
                    rel_cmake = str(cmake_path.relative_to(package_path)).replace("\\", "/")
                    info.components.append(CMakeComponent(
                        library_name=lib_target,
                        class_name=clean_cls,
                        package_name=package_name,
                        cmake_file=rel_cmake,
                        line_number=line_num
                    ))

        # 7. Pluginlib exports: pluginlib_export_plugin_description_file(base_pkg xml_file)
        elif cmd == "pluginlib_export_plugin_description_file" and len(resolved_tokens) >= 2:
            base_pkg = resolved_tokens[0]
            xml_file = resolved_tokens[1].strip('"').strip("'")
            rel_cmake = str(cmake_path.relative_to(package_path)).replace("\\", "/")
            info.plugins.append(CMakePlugin(
                base_package=base_pkg,
                description_file=xml_file,
                package_name=package_name,
                cmake_file=rel_cmake,
                line_number=line_num
            ))

    return info


def analyze_package_cmake(package_path: Path, package_name: str) -> PackageCMakeInfo:
    """
    Analyze all CMakeLists.txt files in a package directory, including subdirectories.
    """
    main_cmake = package_path / "CMakeLists.txt"
    if not main_cmake.exists():
        return PackageCMakeInfo(package_name=package_name, package_path=package_path)

    base_info = parse_cmake_file(main_cmake, package_path, package_name)

    # Search for nested CMakeLists.txt (e.g. in src/, test/, plugins/)
    for root, dirs, files in os.walk(package_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        if 'CMakeLists.txt' in files:
            sub_cmake = Path(root) / 'CMakeLists.txt'
            if sub_cmake != main_cmake:
                is_test_dir = 'test' in [p.lower() for p in sub_cmake.relative_to(package_path).parts]
                sub_info = parse_cmake_file(
                    sub_cmake,
                    package_path,
                    package_name,
                    inherited_vars=base_info.variables,
                    is_test_dir=is_test_dir
                )
                # Merge into base_info
                base_info.executables.update(sub_info.executables)
                base_info.libraries.update(sub_info.libraries)
                base_info.components.extend(sub_info.components)
                base_info.plugins.extend(sub_info.plugins)
                base_info.variables.update(sub_info.variables)

    return base_info


# ---------------------------------------------------------------------------
# Package.xml, setup.py, setup.cfg & Source Dependency Graph Recovery
# ---------------------------------------------------------------------------

_STDLIB_PYTHON = {
    "os", "sys", "re", "json", "math", "time", "datetime", "pathlib", "typing",
    "collections", "dataclasses", "enum", "functools", "itertools", "logging",
    "threading", "multiprocessing", "subprocess", "argparse", "curses", "copy",
    "unittest", "pytest", "ast", "xml", "yaml", "csv", "io", "shutil", "glob",
    "abc", "contextlib", "traceback", "warnings", "weakref", "asyncio", "socket",
}

_STDLIB_CPP_PREFIXES = (
    "iostream", "fstream", "sstream", "vector", "string", "memory", "map",
    "unordered_map", "set", "unordered_set", "list", "deque", "array", "tuple",
    "algorithm", "functional", "chrono", "thread", "mutex", "atomic", "future",
    "cmath", "cstdio", "cstdlib", "cstring", "cstdint", "cassert", "stdexcept",
    "utility", "optional", "variant", "any", "filesystem", "regex", "limits",
)


def parse_package_xml(pkg_xml_path: Path, repo_root: Path) -> Dict[str, Any]:
    """Parse package.xml to extract package name, build type, and typed dependencies."""
    import xml.etree.ElementTree as ET

    result: Dict[str, Any] = {
        "name": pkg_xml_path.parent.name,
        "build_type": "unknown",
        "dependencies": [],  # list of (dep_name, dep_type, line_no)
    }
    if not pkg_xml_path.exists():
        return result

    try:
        raw = pkg_xml_path.read_text(encoding="utf-8", errors="ignore")
        root = ET.fromstring(raw)
        name_el = root.find("name")
        if name_el is not None and name_el.text:
            result["name"] = name_el.text.strip()

        bt_el = root.find(".//export/build_type")
        if bt_el is not None and bt_el.text:
            result["build_type"] = bt_el.text.strip()

        dep_tags = (
            "depend", "build_depend", "buildtool_depend",
            "build_export_depend", "exec_depend", "test_depend", "doc_depend"
        )
        lines = raw.splitlines()
        for tag in dep_tags:
            for el in root.findall(tag):
                if el.text and el.text.strip():
                    dep_name = el.text.strip()
                    # Find approximate line number
                    lno = None
                    pat = f"<{tag}>{dep_name}</{tag}>"
                    for idx, l in enumerate(lines, 1):
                        if pat in l or (f"<{tag}" in l and dep_name in l):
                            lno = idx
                            break
                    result["dependencies"].append((dep_name, tag, lno))
    except Exception as e:
        logger.debug(f"Failed parsing {pkg_xml_path}: {e}")

    return result


def parse_setup_py(setup_py_path: Path) -> Dict[str, Any]:
    """Extract console_scripts and install_requires from setup.py via AST."""
    import ast
    out: Dict[str, Any] = {"console_scripts": {}, "install_requires": []}
    if not setup_py_path.exists():
        return out

    try:
        tree = ast.parse(setup_py_path.read_text(encoding="utf-8", errors="ignore"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == "install_requires" and isinstance(kw.value, ast.List):
                        for el in kw.value.elts:
                            if isinstance(el, ast.Constant) and isinstance(el.value, str):
                                out["install_requires"].append(el.value.split(">=")[0].split("==")[0].strip())
                    elif kw.arg == "entry_points" and isinstance(kw.value, ast.Dict):
                        for k, v in zip(kw.value.keys, kw.value.values):
                            if isinstance(k, ast.Constant) and k.value == "console_scripts" and isinstance(v, ast.List):
                                for item in v.elts:
                                    if isinstance(item, ast.Constant) and isinstance(item.value, str) and "=" in item.value:
                                        exe, target = item.value.split("=", 1)
                                        out["console_scripts"][exe.strip()] = target.strip()
    except Exception as e:
        logger.debug(f"Failed parsing {setup_py_path}: {e}")

    return out


_KNOWN_ROS_PACKAGES = {
    "rclpy", "rclcpp", "rclcpp_action", "rclcpp_lifecycle", "rclcpp_components",
    "geometry_msgs", "sensor_msgs", "std_msgs", "nav_msgs", "control_msgs",
    "trajectory_msgs", "moveit", "moveit_msgs", "shape_msgs", "std_srvs",
    "tf2_ros", "tf2", "pluginlib", "launch", "launch_ros", "ament_index_python",
    "nav2_common", "nav2_util", "nav2_core", "nav2_msgs", "nav2_costmap_2d",
    "behaviortree_cpp", "ros2_control", "controller_interface", "hardware_interface",
}


def _is_ros_package_name(name: str, known_internal: Set[str], declared: Set[str]) -> bool:
    return (
        name in known_internal
        or name in declared
        or name in _KNOWN_ROS_PACKAGES
        or name.endswith(("_msgs", "_srvs", "_interfaces", "_action"))
    )


def extract_source_dependencies(
    pkg_path: Path,
    repo_root: Path,
    pkg_name: str,
    known_packages: Set[str]
) -> List[Dict[str, Any]]:
    """
    Extract observed source-level dependencies from Python imports and C++ #includes.
    Captures both ROS package candidates and unresolved external library imports/includes.
    Returns list of {target, dep_type, file, line}.
    """
    import ast
    observed: List[Dict[str, Any]] = []
    seen: Set[Tuple[str, str]] = set()

    for root, dirs, files in os.walk(pkg_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'build', 'install')]
        for fname in files:
            fpath = Path(root) / fname
            try:
                rel_file = str(fpath.relative_to(repo_root)).replace("\\", "/")
            except ValueError:
                rel_file = str(fpath).replace("\\", "/")

            if fname.endswith(".py") and fname != "setup.py":
                try:
                    src = fpath.read_text(encoding="utf-8", errors="ignore")
                    tree = ast.parse(src)
                    for node in ast.walk(tree):
                        mods: List[Tuple[str, int]] = []
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                mods.append((alias.name.split(".")[0], getattr(node, "lineno", 1)))
                        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                            mods.append((node.module.split(".")[0], getattr(node, "lineno", 1)))
                        for mod, lno in mods:
                            if not mod or mod == pkg_name or mod in _STDLIB_PYTHON:
                                continue
                            key = (mod, "source_import")
                            if key not in seen:
                                seen.add(key)
                                observed.append({
                                    "target": mod,
                                    "dep_type": "source_import",
                                    "file": rel_file,
                                    "line": lno,
                                })
                except Exception:
                    pass

            elif fname.endswith((".cpp", ".hpp", ".h", ".cc")):
                try:
                    lines = fpath.read_text(encoding="utf-8", errors="ignore").splitlines()
                    for lno, line in enumerate(lines, 1):
                        m = re.match(r'^\s*#include\s*[<"]([^">]+)[">]', line)
                        if not m:
                            continue
                        inc = m.group(1)
                        if inc.startswith(_STDLIB_CPP_PREFIXES) or "/" not in inc:
                            continue
                        inc_pkg = inc.split("/")[0]
                        if inc_pkg == pkg_name or inc_pkg in (".", ".."):
                            continue
                        key = (inc_pkg, "source_include")
                        if key not in seen:
                            seen.add(key)
                            observed.append({
                                "target": inc_pkg,
                                "dep_type": "source_include",
                                "file": rel_file,
                                "line": lno,
                            })
                except Exception:
                    pass

    return observed


def build_package_dependency_graph(repo_root: Path):
    """
    Build a directed PackageDependencyGraph across all ROS 2 packages in repo_root.
    Distinguishes declared dependencies (package.xml, setup.py) from observed source dependencies.
    """
    from src.schema import PackageDependencyEdge, PackageDependencyGraph, PackageNodeInfo

    repo_root = Path(repo_root)
    pkg_xmls = [
        p for p in repo_root.rglob("package.xml")
        if not any(part.startswith(".") or part in ("build", "install", "log") for part in p.parts)
    ]

    parsed_pkgs: Dict[str, Dict[str, Any]] = {}
    for pxml in pkg_xmls:
        info = parse_package_xml(pxml, repo_root)
        info["path"] = pxml.parent
        info["rel_xml"] = str(pxml.relative_to(repo_root)).replace("\\", "/")
        parsed_pkgs[info["name"]] = info

    internal_names = set(parsed_pkgs.keys())
    all_edges: List[PackageDependencyEdge] = []
    pkg_nodes: List[PackageNodeInfo] = []
    external_names: Set[str] = set()
    undeclared_source: List[Dict[str, Any]] = []

    for pkg_name, info in sorted(parsed_pkgs.items()):
        pkg_path = info["path"]
        rel_pkg_dir = str(pkg_path.relative_to(repo_root)).replace("\\", "/")
        setup_info = parse_setup_py(pkg_path / "setup.py")

        declared_set: Set[str] = set()
        for dep_name, dep_type, lno in info["dependencies"]:
            declared_set.add(dep_name)
            is_internal = dep_name in internal_names
            if not is_internal:
                external_names.add(dep_name)
            all_edges.append(PackageDependencyEdge(
                source_package=pkg_name,
                target_package=dep_name,
                dependency_type=dep_type,
                origin="declared_manifest",
                is_target_internal=is_internal,
                resolution_category="resolved_internal_package" if is_internal else "manifest_declared_external",
                source_file=info["rel_xml"],
                line_number=lno,
            ))

        for req in setup_info["install_requires"]:
            if req not in declared_set:
                declared_set.add(req)
                is_internal = req in internal_names
                if not is_internal:
                    external_names.add(req)
                all_edges.append(PackageDependencyEdge(
                    source_package=pkg_name,
                    target_package=req,
                    dependency_type="exec_depend",
                    origin="declared_manifest",
                    is_target_internal=is_internal,
                    source_file=f"{rel_pkg_dir}/setup.py" if rel_pkg_dir != "." else "setup.py",
                ))

        observed = extract_source_dependencies(pkg_path, repo_root, pkg_name, internal_names)
        observed_set: Set[str] = set()
        for obs in observed:
            tgt = obs["target"]
            observed_set.add(tgt)
            is_internal = tgt in internal_names
            is_ros_pkg = _is_ros_package_name(tgt, internal_names, declared_set)
            if is_internal:
                res_cat = "resolved_internal_package"
            elif is_ros_pkg:
                res_cat = "resolved_ros_package"
                external_names.add(tgt)
            else:
                res_cat = "unresolved_external_library"

            all_edges.append(PackageDependencyEdge(
                source_package=pkg_name,
                target_package=tgt,
                dependency_type=obs["dep_type"],
                origin="observed_source",
                is_target_internal=is_internal,
                resolution_category=res_cat,
                source_file=obs["file"],
                line_number=obs["line"],
            ))
            # Flag undeclared internal or resolved ROS package dependencies (never unresolved third-party libs)
            if tgt not in declared_set and (is_internal or (is_ros_pkg and tgt.endswith(("_msgs", "_srvs", "_interfaces")))):
                undeclared_source.append({
                    "source_package": pkg_name,
                    "target_package": tgt,
                    "dependency_type": obs["dep_type"],
                    "file": obs["file"],
                    "line": obs["line"],
                })

        pkg_nodes.append(PackageNodeInfo(
            name=pkg_name,
            build_type=info["build_type"],
            package_path=rel_pkg_dir,
            is_internal=True,
            declared_dependencies=sorted(declared_set),
            observed_source_dependencies=sorted(observed_set),
            console_scripts=setup_info["console_scripts"],
        ))

    return PackageDependencyGraph(
        packages=pkg_nodes,
        edges=all_edges,
        internal_packages=sorted(internal_names),
        external_packages=sorted(external_names),
        undeclared_source_dependencies=undeclared_source,
    )
