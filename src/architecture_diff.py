"""
ArchSynth ArchitectureDiff - Architecture Drift / Evolution Detection

Research module for comparing two ArchitectureModel snapshots (e.g. two Git commits)
and producing a structured DriftReport.

Research motivation:
    Existing ROS2 architecture recovery tools produce a static snapshot.
    ArchSynth extends this by tracking architecture EVOLUTION across commits,
    making drift detection a novel, measurable research contribution.

The diff operates on normalized ArchitectureModel JSON, NOT on raw Mermaid text.

Usage:
    python -m src.architecture_diff \\
        --arch-a output/nav2_commit_A/architecture.json \\
        --arch-b output/nav2_commit_B/architecture.json \\
        --output output/drift_report.json
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

from src.schema import (
    ArchitectureModel,
    DriftReport,
    NodeChange,
    TopicChange,
    SubsystemChange,
)

logger = logging.getLogger(__name__)


class ArchitectureDiff:
    """
    Compares two ArchitectureModel snapshots and produces a DriftReport.

    All comparison operates on the normalized model structure (Pydantic objects),
    NOT on raw Mermaid text strings. This makes the diff semantically meaningful.
    """

    def diff(
        self,
        arch_a: ArchitectureModel,
        arch_b: ArchitectureModel
    ) -> DriftReport:
        """
        Compute the full architecture diff between two snapshots.

        Args:
            arch_a: Base architecture snapshot
            arch_b: Target architecture snapshot

        Returns:
            DriftReport with all detected changes
        """
        logger.info(
            f"Diffing architectures: "
            f"[{arch_a.commit_hash[:8] if arch_a.commit_hash else 'base'}] -> "
            f"[{arch_b.commit_hash[:8] if arch_b.commit_hash else 'target'}]"
        )

        report = DriftReport(
            base_commit=arch_a.commit_hash or "base",
            target_commit=arch_b.commit_hash or "target",
            base_timestamp=arch_a.analysis_timestamp,
            target_timestamp=arch_b.analysis_timestamp,
            repo_name=arch_b.repo_name,
        )

        # --- Node-level diff ---
        node_changes = self._diff_nodes(arch_a, arch_b)
        report.added_nodes = node_changes["added"]
        report.removed_nodes = node_changes["removed"]
        report.modified_nodes = node_changes["modified"]

        # --- Topic-level diff ---
        topic_changes = self._diff_topics(arch_a, arch_b)
        report.added_topics = topic_changes["added"]
        report.removed_topics = topic_changes["removed"]
        report.modified_topics = topic_changes["modified"]

        # --- Service-level diff ---
        svc_changes = self._diff_services(arch_a, arch_b)
        report.added_services = svc_changes["added"]
        report.removed_services = svc_changes["removed"]

        # --- Action-level diff ---
        act_changes = self._diff_actions(arch_a, arch_b)
        report.added_actions = act_changes["added"]
        report.removed_actions = act_changes["removed"]

        # --- Subsystem diff ---
        report.subsystem_changes = self._diff_subsystems(arch_a, arch_b)

        # --- Compute totals and summary ---
        report.compute_total()
        report.summary = self._generate_summary(report)

        logger.info(f"Diff complete: {report.total_changes} total changes detected")
        return report

    # ------------------------------------------------------------------
    # Node diffing
    # ------------------------------------------------------------------

    def _diff_nodes(self, arch_a: ArchitectureModel, arch_b: ArchitectureModel) -> Dict[str, Any]:
        """Identify added, removed, and modified nodes."""
        nodes_a: Dict[str, Any] = {}
        for node in arch_a.nodes:
            key = node.name or node.fully_qualified_name
            if key:
                nodes_a[key] = node

        nodes_b: Dict[str, Any] = {}
        for node in arch_b.nodes:
            key = node.name or node.fully_qualified_name
            if key:
                nodes_b[key] = node

        names_a = set(nodes_a.keys())
        names_b = set(nodes_b.keys())

        added = sorted(names_b - names_a)
        removed = sorted(names_a - names_b)

        # Check for modifications in common nodes
        modified: List[NodeChange] = []
        for name in sorted(names_a & names_b):
            n_a = nodes_a[name]
            n_b = nodes_b[name]
            changes = self._compare_nodes(name, n_a, n_b)
            if changes:
                modified.append(changes)

        return {"added": added, "removed": removed, "modified": modified}

    def _compare_nodes(self, name: str, n_a, n_b) -> Optional[NodeChange]:
        """Compare two nodes and return a NodeChange if they differ."""
        changed_fields = []
        old_vals: Dict[str, Any] = {}
        new_vals: Dict[str, Any] = {}

        # Check namespace change
        if n_a.namespace != n_b.namespace:
            changed_fields.append("namespace")
            old_vals["namespace"] = n_a.namespace
            new_vals["namespace"] = n_b.namespace

        # Check package change
        if n_a.package_name != n_b.package_name:
            changed_fields.append("package_name")
            old_vals["package_name"] = n_a.package_name
            new_vals["package_name"] = n_b.package_name

        # Check publisher count change
        pubs_a = {p.name for p in n_a.publishers}
        pubs_b = {p.name for p in n_b.publishers}
        if pubs_a != pubs_b:
            changed_fields.append("publishers")
            old_vals["publishers"] = sorted(pubs_a)
            new_vals["publishers"] = sorted(pubs_b)

        # Check subscriber count change
        subs_a = {s.name for s in n_a.subscribers}
        subs_b = {s.name for s in n_b.subscribers}
        if subs_a != subs_b:
            changed_fields.append("subscribers")
            old_vals["subscribers"] = sorted(subs_a)
            new_vals["subscribers"] = sorted(subs_b)

        if not changed_fields:
            return None

        return NodeChange(
            node_name=name,
            changed_fields=changed_fields,
            old_values=old_vals,
            new_values=new_vals
        )

    # ------------------------------------------------------------------
    # Topic diffing
    # ------------------------------------------------------------------

    def _diff_topics(self, arch_a: ArchitectureModel, arch_b: ArchitectureModel) -> Dict[str, Any]:
        """Identify added, removed, and modified topics."""
        # Build topic inventory from topic_connections
        topics_a = self._build_topic_inventory(arch_a)
        topics_b = self._build_topic_inventory(arch_b)

        names_a = set(topics_a.keys())
        names_b = set(topics_b.keys())

        added = sorted(names_b - names_a)
        removed = sorted(names_a - names_b)

        modified: List[TopicChange] = []
        for name in sorted(names_a & names_b):
            t_a = topics_a[name]
            t_b = topics_b[name]
            change = self._compare_topics(name, t_a, t_b)
            if change:
                modified.append(change)

        return {"added": added, "removed": removed, "modified": modified}

    def _build_topic_inventory(self, arch: ArchitectureModel) -> Dict[str, Dict[str, Any]]:
        """Build {topic_name: {message_type, publishers, subscribers}} from arch model."""
        inventory: Dict[str, Dict[str, Any]] = {}

        # From topic_connections
        for conn in arch.topic_connections:
            name = conn.get("topic", "")
            if name:
                inventory[name] = {
                    "publishers": sorted(conn.get("publishers", [])),
                    "subscribers": sorted(conn.get("subscribers", [])),
                    "message_type": ""  # not in connection — look up in nodes
                }

        # Try to fill message_type from node publishers
        for node in arch.nodes:
            for pub in node.publishers:
                if pub.name in inventory:
                    inventory[pub.name]["message_type"] = pub.message_type

        return inventory

    def _compare_topics(self, name: str, t_a: Dict, t_b: Dict) -> Optional[TopicChange]:
        """Compare two topic entries and return TopicChange if different."""
        changed_fields = []
        old_vals: Dict[str, Any] = {}
        new_vals: Dict[str, Any] = {}

        if t_a.get("message_type") and t_b.get("message_type"):
            if t_a["message_type"] != t_b["message_type"]:
                changed_fields.append("message_type")
                old_vals["message_type"] = t_a["message_type"]
                new_vals["message_type"] = t_b["message_type"]

        if t_a.get("publishers", []) != t_b.get("publishers", []):
            changed_fields.append("publishers")
            old_vals["publishers"] = t_a.get("publishers", [])
            new_vals["publishers"] = t_b.get("publishers", [])

        if t_a.get("subscribers", []) != t_b.get("subscribers", []):
            changed_fields.append("subscribers")
            old_vals["subscribers"] = t_a.get("subscribers", [])
            new_vals["subscribers"] = t_b.get("subscribers", [])

        if not changed_fields:
            return None

        return TopicChange(
            topic_name=name,
            changed_fields=changed_fields,
            old_values=old_vals,
            new_values=new_vals
        )

    # ------------------------------------------------------------------
    # Service diffing
    # ------------------------------------------------------------------

    def _diff_services(self, arch_a: ArchitectureModel, arch_b: ArchitectureModel) -> Dict[str, Any]:
        """Identify added and removed services."""
        srvs_a = {c.get("service", "") for c in arch_a.service_connections}
        srvs_b = {c.get("service", "") for c in arch_b.service_connections}

        return {
            "added": sorted(srvs_b - srvs_a),
            "removed": sorted(srvs_a - srvs_b)
        }

    # ------------------------------------------------------------------
    # Action diffing
    # ------------------------------------------------------------------

    def _diff_actions(self, arch_a: ArchitectureModel, arch_b: ArchitectureModel) -> Dict[str, Any]:
        """Identify added and removed actions."""
        acts_a = {c.get("action", "") for c in arch_a.action_connections}
        acts_b = {c.get("action", "") for c in arch_b.action_connections}

        return {
            "added": sorted(acts_b - acts_a),
            "removed": sorted(acts_a - acts_b)
        }

    # ------------------------------------------------------------------
    # Subsystem diffing
    # ------------------------------------------------------------------

    def _diff_subsystems(self, arch_a: ArchitectureModel, arch_b: ArchitectureModel) -> List[SubsystemChange]:
        """Identify added, removed, and modified subsystems."""
        subs_a = {s.name: set(s.nodes) for s in arch_a.subsystems}
        subs_b = {s.name: set(s.nodes) for s in arch_b.subsystems}

        names_a = set(subs_a.keys())
        names_b = set(subs_b.keys())

        changes: List[SubsystemChange] = []

        for name in sorted(names_b - names_a):
            changes.append(SubsystemChange(
                subsystem_name=name,
                change_type="added",
                added_nodes=sorted(subs_b[name])
            ))

        for name in sorted(names_a - names_b):
            changes.append(SubsystemChange(
                subsystem_name=name,
                change_type="removed",
                removed_nodes=sorted(subs_a[name])
            ))

        for name in sorted(names_a & names_b):
            added_nodes = sorted(subs_b[name] - subs_a[name])
            removed_nodes = sorted(subs_a[name] - subs_b[name])
            if added_nodes or removed_nodes:
                changes.append(SubsystemChange(
                    subsystem_name=name,
                    change_type="modified",
                    added_nodes=added_nodes,
                    removed_nodes=removed_nodes
                ))

        return changes

    # ------------------------------------------------------------------
    # Summary generation
    # ------------------------------------------------------------------

    def _generate_summary(self, report: DriftReport) -> str:
        """Generate a human-readable architecture drift summary."""
        lines = [
            f"Architecture Drift Report",
            f"Base:   {report.base_commit}",
            f"Target: {report.target_commit}",
            f"Total changes: {report.total_changes}",
            ""
        ]

        if report.added_nodes:
            lines.append("Added Nodes:")
            for n in report.added_nodes:
                lines.append(f"  + {n}")

        if report.removed_nodes:
            lines.append("Removed Nodes:")
            for n in report.removed_nodes:
                lines.append(f"  - {n}")

        if report.modified_nodes:
            lines.append("Modified Nodes:")
            for nc in report.modified_nodes:
                lines.append(f"  ~ {nc.node_name} ({', '.join(nc.changed_fields)})")

        if report.added_topics:
            lines.append("Added Topics:")
            for t in report.added_topics:
                lines.append(f"  + {t}")

        if report.removed_topics:
            lines.append("Removed Topics:")
            for t in report.removed_topics:
                lines.append(f"  - {t}")

        if report.modified_topics:
            lines.append("Modified Topics:")
            for tc in report.modified_topics:
                lines.append(f"  ~ {tc.topic_name} ({', '.join(tc.changed_fields)})")

        if report.added_services:
            lines.append("Added Services:")
            for s in report.added_services:
                lines.append(f"  + {s}")

        if report.removed_services:
            lines.append("Removed Services:")
            for s in report.removed_services:
                lines.append(f"  - {s}")

        if report.added_actions:
            lines.append("Added Actions:")
            for a in report.added_actions:
                lines.append(f"  + {a}")

        if report.removed_actions:
            lines.append("Removed Actions:")
            for a in report.removed_actions:
                lines.append(f"  - {a}")

        if report.subsystem_changes:
            lines.append("Subsystem Changes:")
            for sc in report.subsystem_changes:
                lines.append(f"  {sc.change_type.upper()}: {sc.subsystem_name}")

        return "\n".join(lines)


def diff_architectures(
    arch_a_path: Path,
    arch_b_path: Path,
    output_path: Optional[Path] = None
) -> DriftReport:
    """
    Convenience function: load two architecture JSON files and compute diff.

    Args:
        arch_a_path: Path to base architecture.json
        arch_b_path: Path to target architecture.json
        output_path: Optional path to save DriftReport JSON

    Returns:
        DriftReport
    """
    with open(arch_a_path, "r", encoding="utf-8") as f:
        arch_a = ArchitectureModel.model_validate(json.load(f))

    with open(arch_b_path, "r", encoding="utf-8") as f:
        arch_b = ArchitectureModel.model_validate(json.load(f))

    differ = ArchitectureDiff()
    report = differ.diff(arch_a, arch_b)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report.model_dump(), indent=2),
            encoding="utf-8"
        )
        logger.info(f"Drift report saved to {output_path}")

    return report


if __name__ == "__main__":
    import sys
    import argparse
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="ArchSynth Architecture Diff")
    parser.add_argument("--arch-a", required=True, help="Path to base architecture.json")
    parser.add_argument("--arch-b", required=True, help="Path to target architecture.json")
    parser.add_argument("--output", default=None, help="Path to save drift report JSON")
    args = parser.parse_args()

    report = diff_architectures(
        arch_a_path=Path(args.arch_a),
        arch_b_path=Path(args.arch_b),
        output_path=Path(args.output) if args.output else None
    )

    print(f"\n{report.summary}")
    print(f"\nTotal Changes: {report.total_changes}")
