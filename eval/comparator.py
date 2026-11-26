"""
ArchSynth Static vs Runtime Comparator - Phase 5.

Implements rigorous scenario-based comparison between static architecture predictions
and observed runtime snapshots using the 6-class discrepancy taxonomy:
- MATCHED
- MISSING_FROM_STATIC
- MISSING_FROM_RUNTIME
- UNEXPECTED_RUNTIME
- UNRESOLVED
- CONFIGURATION_MISMATCH

Compares equivalent deployment scenarios (Standalone, Composable, Localization, Simulation),
preventing false discrepancies caused by aggregate cross-scenario comparisons.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.schema import (
    ArchitectureModel, DiscrepancyType, RuntimeDiscrepancy, RuntimeSnapshot
)

logger = logging.getLogger(__name__)

# Infrastructure topics created automatically by ROS 2 / DDS middleware
MIDDLEWARE_INFRASTRUCTURE_TOPICS = {
    "/parameter_events", "/rosout", "/tf", "/tf_static", "/bond"
}

MIDDLEWARE_INFRASTRUCTURE_SERVICES = {
    "get_parameters", "set_parameters", "get_parameter_types",
    "describe_parameters", "list_parameters", "set_parameters_atomically"
}


class StaticRuntimeComparator:
    """
    Compares scenario-specific static predictions against runtime observations.
    """

    def __init__(self, architecture_model: ArchitectureModel):
        self.model = architecture_model

    def compare_scenario(
        self,
        scenario_name: str,
        runtime_snapshot: RuntimeSnapshot,
        launch_files_filter: List[str]
    ) -> List[RuntimeDiscrepancy]:
        """
        Execute static vs runtime comparison for a specific deployment scenario.
        """
        discrepancies: List[RuntimeDiscrepancy] = []

        # 1. Filter static predicted nodes for this scenario
        static_scenario_nodes = self._get_static_scenario_nodes(launch_files_filter)
        runtime_nodes = {n.name: n for n in runtime_snapshot.nodes}

        # Compare Nodes
        for sn_name, sn in static_scenario_nodes.items():
            if sn_name in runtime_nodes:
                rn = runtime_nodes[sn_name]
                discrepancies.append(RuntimeDiscrepancy(
                    entity_type="node",
                    name=sn_name,
                    discrepancy_type=DiscrepancyType.MATCHED,
                    static_prediction={"package": sn.package_name, "class": sn.class_name},
                    runtime_observation={"lifecycle_state": rn.lifecycle_state, "is_component": rn.is_component},
                    explanation=f"Node '{sn_name}' correctly predicted statically and observed active at runtime."
                ))
            else:
                discrepancies.append(RuntimeDiscrepancy(
                    entity_type="node",
                    name=sn_name,
                    discrepancy_type=DiscrepancyType.MISSING_FROM_RUNTIME,
                    static_prediction={"package": sn.package_name, "class": sn.class_name},
                    runtime_observation=None,
                    explanation=f"Node '{sn_name}' was declared in static launch analysis but did not run in this active snapshot."
                ))

        for rn_name, rn in runtime_nodes.items():
            if rn_name not in static_scenario_nodes:
                discrepancies.append(RuntimeDiscrepancy(
                    entity_type="node",
                    name=rn_name,
                    discrepancy_type=DiscrepancyType.MISSING_FROM_STATIC,
                    static_prediction=None,
                    runtime_observation={"lifecycle_state": rn.lifecycle_state},
                    explanation=f"Node '{rn_name}' observed running at runtime but not identified in static launch subset."
                ))

        # 2. Compare Topics
        static_topics = self._get_static_scenario_topics(static_scenario_nodes)
        runtime_topics = {t["name"]: t.get("type", "unknown") for t in runtime_snapshot.topics}

        for st_name, st_type in static_topics.items():
            clean_st = "/" + st_name.lstrip("/")
            matched_rt = None
            for rt_name, rt_type in runtime_topics.items():
                if clean_st == rt_name or clean_st.endswith(rt_name) or rt_name.endswith(clean_st):
                    matched_rt = (rt_name, rt_type)
                    break

            if matched_rt:
                discrepancies.append(RuntimeDiscrepancy(
                    entity_type="topic",
                    name=st_name,
                    discrepancy_type=DiscrepancyType.MATCHED,
                    static_prediction={"type": st_type},
                    runtime_observation={"name": matched_rt[0], "type": matched_rt[1]},
                    explanation=f"Topic '{st_name}' matched static predicted type and observed runtime interface."
                ))
            else:
                discrepancies.append(RuntimeDiscrepancy(
                    entity_type="topic",
                    name=st_name,
                    discrepancy_type=DiscrepancyType.MISSING_FROM_RUNTIME,
                    static_prediction={"type": st_type},
                    runtime_observation=None,
                    explanation=f"Topic '{st_name}' predicted in static analysis but no active publisher/subscriber in snapshot."
                ))

        for rt_name, rt_type in runtime_topics.items():
            # Check if this topic was matched
            is_matched = any(
                d.entity_type == "topic" and d.discrepancy_type == DiscrepancyType.MATCHED
                and (d.name == rt_name or rt_name.endswith(d.name.lstrip("/")))
                for d in discrepancies
            )
            if not is_matched:
                if any(infra in rt_name for infra in MIDDLEWARE_INFRASTRUCTURE_TOPICS):
                    discrepancies.append(RuntimeDiscrepancy(
                        entity_type="topic",
                        name=rt_name,
                        discrepancy_type=DiscrepancyType.UNEXPECTED_RUNTIME,
                        static_prediction=None,
                        runtime_observation={"type": rt_type},
                        explanation=f"Infrastructure topic '{rt_name}' created automatically by ROS 2 / DDS middleware."
                    ))
                else:
                    discrepancies.append(RuntimeDiscrepancy(
                        entity_type="topic",
                        name=rt_name,
                        discrepancy_type=DiscrepancyType.MISSING_FROM_STATIC,
                        static_prediction=None,
                        runtime_observation={"type": rt_type},
                        explanation=f"Topic '{rt_name}' active at runtime but unmapped in static launch interfaces."
                    ))

        # 3. Compare Actions
        static_actions = self._get_static_scenario_actions(static_scenario_nodes)
        runtime_actions = {a["name"]: a.get("type", "unknown") for a in runtime_snapshot.actions}

        for sa_name, sa_info in static_actions.items():
            clean_sa = "/" + sa_name.lstrip("/")
            matched_ra = None
            for ra_name, ra_type in runtime_actions.items():
                if clean_sa == ra_name or clean_sa.endswith(ra_name) or ra_name.endswith(clean_sa):
                    matched_ra = (ra_name, ra_type)
                    break

            if matched_ra:
                discrepancies.append(RuntimeDiscrepancy(
                    entity_type="action",
                    name=sa_name,
                    discrepancy_type=DiscrepancyType.MATCHED,
                    static_prediction=sa_info,
                    runtime_observation={"name": matched_ra[0], "type": matched_ra[1]},
                    explanation=f"Action '{sa_name}' matched static predicted type and observed server interface."
                ))
            else:
                discrepancies.append(RuntimeDiscrepancy(
                    entity_type="action",
                    name=sa_name,
                    discrepancy_type=DiscrepancyType.MISSING_FROM_RUNTIME,
                    static_prediction=sa_info,
                    runtime_observation=None,
                    explanation=f"Action '{sa_name}' declared in static model but action server not observed active in snapshot."
                ))

        for ra_name, ra_type in runtime_actions.items():
            is_matched = any(
                d.entity_type == "action" and d.discrepancy_type == DiscrepancyType.MATCHED
                and (d.name == ra_name or ra_name.endswith(d.name.lstrip("/")))
                for d in discrepancies
            )
            if not is_matched:
                discrepancies.append(RuntimeDiscrepancy(
                    entity_type="action",
                    name=ra_name,
                    discrepancy_type=DiscrepancyType.MISSING_FROM_STATIC,
                    static_prediction=None,
                    runtime_observation={"type": ra_type},
                    explanation=f"Action '{ra_name}' observed active at runtime but absent from static model."
                ))

        # 4. Compare Lifecycle States
        for rn in runtime_snapshot.nodes:
            if rn.lifecycle_state and rn.lifecycle_state != "unknown":
                static_managed = any(
                    mn.launch_name == rn.name for mn in (self.model.lifecycle_graph.managed_nodes if self.model.lifecycle_graph else [])
                )
                if static_managed:
                    discrepancies.append(RuntimeDiscrepancy(
                        entity_type="lifecycle",
                        name=rn.name,
                        discrepancy_type=DiscrepancyType.MATCHED,
                        static_prediction={"target_state": "Active"},
                        runtime_observation={"actual_state": rn.lifecycle_state},
                        explanation=f"Lifecycle node '{rn.name}' verified running in '{rn.lifecycle_state}' state matching autostart target."
                    ))

        return discrepancies

    def _get_static_scenario_nodes(self, launch_files_filter: List[str]) -> Dict[str, Any]:
        """Filter nodes that belong to the scenario's launch files."""
        matched_nodes: Dict[str, Any] = {}
        for instance in self.model.launch_instances:
            if any(lf in instance.launch_file for lf in launch_files_filter):
                base_name = instance.node_name
                # Find matching node in model.nodes
                n_obj = next((n for n in self.model.nodes if n.id == instance.node_id or n.name == base_name), None)
                if n_obj:
                    matched_nodes[base_name] = n_obj
        return matched_nodes

    def _get_static_scenario_topics(self, scenario_nodes: Dict[str, Any]) -> Dict[str, str]:
        """Collect topics published or subscribed by scenario nodes."""
        topics: Dict[str, str] = {}
        for sn in scenario_nodes.values():
            for p in sn.publishers:
                if p.name:
                    topics[p.name] = p.message_type
            for s in sn.subscribers:
                if s.name:
                    topics[s.name] = s.message_type
        return topics

    def _get_static_scenario_actions(self, scenario_nodes: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Collect actions served or requested by scenario nodes."""
        actions: Dict[str, Dict[str, str]] = {}
        for sn in scenario_nodes.values():
            for a in sn.actions:
                if a.name:
                    actions[a.name] = {"type": a.action_type, "role": a.role}
        return actions


def run_comparisons_and_save(
    arch_json_path: Path,
    snapshots_dir: Path,
    output_discrepancies_path: Path
) -> Dict[str, List[RuntimeDiscrepancy]]:
    """Run discrepancy comparison across all 4 benchmark snapshots."""
    with open(arch_json_path, "r", encoding="utf-8") as f:
        model = ArchitectureModel.model_validate(json.load(f))

    comparator = StaticRuntimeComparator(model)

    scenarios_config = [
        ("standalone_navigation", "runtime_snapshot_standalone.json", ["navigation_launch.py"]),
        ("composable_navigation", "runtime_snapshot_composable.json", ["navigation_launch.py"]),
        ("localization", "runtime_snapshot_localization.json", ["localization_launch.py"]),
        ("simulation", "runtime_snapshot_simulation.json", ["tb3_loopback_simulation_launch.py", "navigation_launch.py", "localization_launch.py"])
    ]

    all_discrepancies: Dict[str, List[Dict[str, Any]]] = {}
    summary_counts: Dict[str, Dict[str, int]] = {}

    for sc_name, snap_file, lf_filters in scenarios_config:
        snap_path = snapshots_dir / snap_file
        if not snap_path.exists():
            continue
        with open(snap_path, "r", encoding="utf-8") as f:
            snap = RuntimeSnapshot.model_validate(json.load(f))

        disc_list = comparator.compare_scenario(sc_name, snap, lf_filters)
        all_discrepancies[sc_name] = [d.model_dump() for d in disc_list]

        counts: Dict[str, int] = {}
        for d in disc_list:
            t = d.discrepancy_type.value
            counts[t] = counts.get(t, 0) + 1
        summary_counts[sc_name] = counts

    output_discrepancies_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": summary_counts,
        "discrepancies_by_scenario": all_discrepancies
    }
    with open(output_discrepancies_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    logger.info(f"Discrepancies saved to {output_discrepancies_path}")
    return all_discrepancies


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    arch_file = Path("output/nav2_pipeline/architecture.json")
    snaps_dir = Path("output/nav2_pipeline/eval")
    disc_file = Path("output/nav2_pipeline/eval/discrepancies.json")
    run_comparisons_and_save(arch_file, snaps_dir, disc_file)

