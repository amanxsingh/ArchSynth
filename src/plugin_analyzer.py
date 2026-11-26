"""
ArchSynth PluginAnalyzer - Phase 4: Plugin Architecture Recovery.

Analyzes pluginlib architecture in ROS 2 / Nav2:
1. Discovers and parses all `pluginlib` XML manifest files (*plugins*.xml, *plugin*.xml).
2. Extracts plugin class types, base classes, packages, descriptions, and library paths.
3. Categorizes plugins into architectural extension points:
   - costmap_layer (nav2_costmap_2d::Layer)
   - global_planner (nav2_core::GlobalPlanner)
   - controller (nav2_core::Controller)
   - smoother (nav2_core::Smoother)
   - behavior (nav2_core::Behavior)
   - navigator (nav2_core::Navigator)
   - waypoint_task (nav2_core::WaypointTaskExecutor)
   - goal_checker / progress_checker
4. Correlates with runtime parameter configuration (nav2_params.yaml) to identify active selections.
5. Classifies plugin status (REGISTERED, AVAILABLE, CONFIGURED, SELECTED, RUNTIME_LOADED).
6. Generates Mermaid diagram and serializes PluginArchitectureModel.
"""

import json
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

from src.schema import (
    EvidenceItem, EvidenceType, PluginArchitectureModel, PluginDeclaration,
    PluginStatus, ServerPluginConfiguration
)

logger = logging.getLogger(__name__)


class PluginAnalyzer:
    """
    Recovers pluginlib extension points, declarations, and runtime configurations.
    """

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)

    def recover_plugin_architecture(self) -> PluginArchitectureModel:
        """
        Execute full plugin architecture recovery.
        """
        # 1. Discover and parse all pluginlib XML manifests
        plugins = self._discover_plugins()

        # 2. Parse runtime YAML parameters
        server_configs, configured_types, selected_types = self._parse_runtime_params()

        # 3. Update plugin statuses based on configuration
        for p in plugins:
            p_class = p.class_type
            p_name = p.plugin_name
            if p_class in selected_types or p_name in selected_types:
                p.status = PluginStatus.SELECTED
            elif p_class in configured_types or p_name in configured_types:
                p.status = PluginStatus.CONFIGURED
            else:
                p.status = PluginStatus.AVAILABLE

        # 4. Group by category
        categories: Dict[str, List[str]] = {}
        for p in plugins:
            categories.setdefault(p.plugin_category, []).append(p.plugin_name)

        # 5. Status counts
        status_counts = {
            PluginStatus.REGISTERED.value: sum(1 for p in plugins if p.status == PluginStatus.REGISTERED),
            PluginStatus.AVAILABLE.value: sum(1 for p in plugins if p.status == PluginStatus.AVAILABLE),
            PluginStatus.CONFIGURED.value: sum(1 for p in plugins if p.status == PluginStatus.CONFIGURED),
            PluginStatus.SELECTED.value: sum(1 for p in plugins if p.status == PluginStatus.SELECTED),
            PluginStatus.RUNTIME_LOADED.value: 0,
            PluginStatus.UNKNOWN.value: 0,
        }

        # 6. Generate Mermaid diagram
        mermaid_diag = self._generate_plugin_mermaid(plugins, server_configs)

        return PluginArchitectureModel(
            plugins=plugins,
            categories=categories,
            server_configurations=server_configs,
            status_counts=status_counts,
            mermaid_diagram=mermaid_diag
        )

    def _discover_plugins(self) -> List[PluginDeclaration]:
        """
        Scan repository for all pluginlib XML export manifests.
        """
        declarations: List[PluginDeclaration] = []
        seen_keys: Set[Tuple[str, str]] = set()

        for xml_path in self.repo_root.rglob("*.xml"):
            if xml_path.name == "package.xml":
                continue
            rel_path = str(xml_path.relative_to(self.repo_root)).replace("\\", "/")

            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
            except Exception:
                continue

            # Look for <library> or <class> elements
            # Both <class_libraries> root and <library> / <class> can appear
            libraries = root.findall(".//library")
            classes_to_process: List[Tuple[ET.Element, Optional[str]]] = []

            if libraries:
                for lib in libraries:
                    lib_path = lib.get("path")
                    for cls_elem in lib.findall("class"):
                        classes_to_process.append((cls_elem, lib_path))
            elif root.tag == "class":
                classes_to_process.append((root, None))
            else:
                for cls_elem in root.findall(".//class"):
                    classes_to_process.append((cls_elem, None))

            # Derive package name from directory path
            pkg_name = xml_path.parts[len(self.repo_root.parts)] if len(xml_path.parts) > len(self.repo_root.parts) else "unknown"

            for cls_elem, lib_path in classes_to_process:
                class_type = cls_elem.get("type") or cls_elem.get("name")
                base_class = cls_elem.get("base_class_type")
                lookup_name = cls_elem.get("name") or class_type

                if not class_type or not base_class:
                    continue

                key = (rel_path, class_type)
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                desc_elem = cls_elem.find("description")
                desc_text = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else None

                cat = self._categorize_plugin(base_class, class_type)

                evidence = [
                    EvidenceItem(
                        file=rel_path,
                        line_start=1,
                        evidence_type=EvidenceType.PACKAGE_MANIFEST,
                        source="plugin_analyzer",
                        confidence=1.0,
                        explanation=f"Declared plugin '{class_type}' extending base class '{base_class}'"
                    )
                ]

                declarations.append(PluginDeclaration(
                    plugin_name=lookup_name,
                    class_type=class_type,
                    base_class_type=base_class,
                    package_name=pkg_name,
                    manifest_file=rel_path,
                    library_path=lib_path,
                    description=desc_text,
                    plugin_category=cat,
                    status=PluginStatus.AVAILABLE,
                    evidence=evidence
                ))

        return declarations

    def _categorize_plugin(self, base_class: str, class_type: str) -> str:
        """Categorize plugin into Nav2 architectural extension category."""
        base_lower = base_class.lower()
        class_lower = class_type.lower()

        if "layer" in base_lower or "costmap" in base_lower:
            return "costmap_layer"
        if "globalplanner" in base_lower or "planner" in base_lower:
            return "global_planner"
        if "controller" in base_lower or "localplanner" in base_lower:
            return "controller"
        if "smoother" in base_lower:
            return "smoother"
        if "behavior" in base_lower or "recovery" in base_lower:
            return "recovery_behavior"
        if "navigator" in base_lower:
            return "navigator"
        if "waypointtaskexecutor" in base_lower:
            return "waypoint_task_executor"
        if "goalchecker" in base_lower:
            return "goal_checker"
        if "progresschecker" in base_lower:
            return "progress_checker"
        if "critic" in base_lower:
            return "trajectory_critic"
        if "dock" in base_lower:
            return "dock_plugin"
        if "route" in base_lower:
            return "route_plugin"
        if "kinematics" in base_lower:
            return "kinematics_plugin"
        # Use declared base class instead of opaque 'general_plugin'
        clean_base = base_class.strip().replace("::", "_")
        return clean_base if clean_base else "unclassified_plugin"

    def _parse_runtime_params(self) -> Tuple[List[ServerPluginConfiguration], Set[str], Set[str]]:
        """
        Parse nav2_params.yaml to recover configured and selected plugins across Nav2 servers.
        """
        server_configs: List[ServerPluginConfiguration] = []
        configured_types: Set[str] = set()
        selected_types: Set[str] = set()

        yaml_path = self.repo_root / "nav2_bringup" / "params" / "nav2_params.yaml"
        if not yaml_path.exists():
            return server_configs, configured_types, selected_types

        rel_yaml = str(yaml_path.relative_to(self.repo_root)).replace("\\", "/")
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            return server_configs, configured_types, selected_types

        # Recursively search for plugin keys in param dictionary
        def scan_dict(node_name: str, d: Dict[str, Any]):
            for k, v in d.items():
                if isinstance(v, dict):
                    if "plugin" in v:
                        ptype = v.get("plugin")
                        if isinstance(ptype, str):
                            selected_types.add(ptype)
                            configured_types.add(ptype)
                            server_configs.append(ServerPluginConfiguration(
                                server_node_name=node_name,
                                plugin_slot=k,
                                plugin_names=[k],
                                plugin_types=[ptype],
                                selected_plugin=ptype,
                                parameter_file=rel_yaml
                            ))
                    scan_dict(node_name, v)
                elif "plugins" in k.lower() and isinstance(v, list):
                    for item in v:
                        if isinstance(item, str):
                            configured_types.add(item)
                            # Check if item itself has a plugin type entry in parent dict
                            if item in d and isinstance(d[item], dict) and "plugin" in d[item]:
                                ptype = d[item]["plugin"]
                                selected_types.add(ptype)
                                configured_types.add(ptype)

        for top_key, top_val in data.items():
            if isinstance(top_val, dict):
                scan_dict(top_key, top_val)

        return server_configs, configured_types, selected_types

    def _generate_plugin_mermaid(
        self,
        plugins: List[PluginDeclaration],
        server_configs: List[ServerPluginConfiguration]
    ) -> str:
        """
        Generate Mermaid class diagram of plugin extension architecture.
        """
        lines = [
            "classDiagram",
            "    direction TB",
            "    class nav2_core_GlobalPlanner {",
            "        <<interface>>",
            "        +createPlan()",
            "    }",
            "    class nav2_core_Controller {",
            "        <<interface>>",
            "        +computeVelocityCommands()",
            "    }",
            "    class nav2_costmap_2d_Layer {",
            "        <<interface>>",
            "        +updateBounds()",
            "        +updateCosts()",
            "    }",
            "    class nav2_core_Smoother {",
            "        <<interface>>",
            "        +smooth()",
            "    }",
            "    class nav2_core_Behavior {",
            "        <<interface>>",
            "        +onRun()",
            "        +onCycleUpdate()",
            "    }",
            ""
        ]

        # Add implementations for selected plugins
        for p in plugins:
            if p.status == PluginStatus.SELECTED:
                safe_name = p.class_type.replace("::", "_").replace("<", "_").replace(">", "_")
                base_safe = p.base_class_type.replace("::", "_").replace("<", "_").replace(">", "_")
                lines.append(f"    class {safe_name} {{")
                lines.append(f"        <<SELECTED>>")
                lines.append(f"        package: {p.package_name}")
                lines.append(f"    }}")
                if "Layer" in base_safe:
                    lines.append(f"    nav2_costmap_2d_Layer <|-- {safe_name}")
                elif "Controller" in base_safe:
                    lines.append(f"    nav2_core_Controller <|-- {safe_name}")
                elif "GlobalPlanner" in base_safe:
                    lines.append(f"    nav2_core_GlobalPlanner <|-- {safe_name}")
                elif "Smoother" in base_safe:
                    lines.append(f"    nav2_core_Smoother <|-- {safe_name}")
                elif "Behavior" in base_safe:
                    lines.append(f"    nav2_core_Behavior <|-- {safe_name}")

        return "\n".join(lines)


def run_plugin_analysis(
    repo_root: Path,
    output_path: Optional[Path] = None
) -> PluginArchitectureModel:
    """Execute Stage 4.3 Plugin Architecture Analysis"""
    analyzer = PluginAnalyzer(repo_root=repo_root)
    model = analyzer.recover_plugin_architecture()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(model.model_dump(), f, indent=2)
        logger.info(f"Plugin architecture model saved to {output_path}")

    return model

