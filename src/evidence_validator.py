"""
ArchSynth EvidenceValidator - Research Module

Validates recovered architectural entities against their claimed source evidence.

Research motivation:
    Current Pydantic validation checks whether LLM output has the correct structure.
    That does NOT prove the recovered entity actually exists in the repository.

    This module adds factual validation on top of schema validation:

        Schema Validation (Pydantic)
            +
        Evidence Validation (EvidenceValidator)
            =
        Validated Architecture

Key research metrics produced:
    - Evidence Coverage  = supported_entities / total_entities
    - Unsupported Entity Rate = unsupported / total
    - Per-category coverage: nodes, topics, services, actions
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from src.schema import (
    ArchitectureModel,
    ROS2Node,
    TopicInfo,
    ServiceInfo,
    ActionInfo,
    EvidenceItem,
    ValidationStatus,
    ValidationReport,
    UnsupportedEntityRecord,
)

logger = logging.getLogger(__name__)


class EvidenceValidator:
    """
    Validates recovered architectural entities against their claimed source evidence.

    For each entity, the validator checks:
        1. Does the entity have at least one EvidenceItem?
        2. Does the referenced file exist on disk?
        3. (Optional) Does the line range contain the expected API call pattern?

    This produces a ValidationReport with evidence coverage metrics.
    """

    def __init__(self, repo_root: Optional[Path] = None):
        """
        Args:
            repo_root: Root directory of the analyzed repository.
                       Used to resolve relative file paths in evidence items.
                       If None, file-existence checks are skipped (schema-only mode).
        """
        self.repo_root = repo_root

    def validate(self, model: ArchitectureModel) -> ValidationReport:
        """
        Run full evidence validation on an ArchitectureModel.

        Returns:
            ValidationReport with evidence coverage metrics and unsupported entity list.
        """
        logger.info(f"Running evidence validation on '{model.repo_name}'...")

        unsupported_list: List[UnsupportedEntityRecord] = []

        # --- Validate nodes ---
        node_supported = 0
        node_total = len(model.nodes)

        for node in model.nodes:
            status, reason = self._validate_node(node)
            if status == ValidationStatus.SUPPORTED:
                node_supported += 1
            else:
                unsupported_list.append(UnsupportedEntityRecord(
                    entity_type="node",
                    name=node.name or node.fully_qualified_name,
                    reason=reason,
                    evidence_count=len(node.evidence)
                ))

        # --- Validate topics (from publishers and subscribers on nodes) ---
        topic_supported = 0
        topic_total = 0
        seen_topics = set()

        for node in model.nodes:
            for pub in node.publishers:
                if pub.name not in seen_topics:
                    seen_topics.add(pub.name)
                    topic_total += 1
                    status, reason = self._validate_topic_info(pub, node.name)
                    if status == ValidationStatus.SUPPORTED:
                        topic_supported += 1
                    else:
                        unsupported_list.append(UnsupportedEntityRecord(
                            entity_type="topic",
                            name=pub.name,
                            reason=reason,
                            evidence_count=len(pub.evidence)
                        ))

            for sub in node.subscribers:
                if sub.name not in seen_topics:
                    seen_topics.add(sub.name)
                    topic_total += 1
                    status, reason = self._validate_topic_info(sub, node.name)
                    if status == ValidationStatus.SUPPORTED:
                        topic_supported += 1
                    else:
                        unsupported_list.append(UnsupportedEntityRecord(
                            entity_type="topic",
                            name=sub.name,
                            reason=reason,
                            evidence_count=len(sub.evidence)
                        ))

        # --- Validate services ---
        service_supported = 0
        service_total = 0
        seen_services = set()

        for node in model.nodes:
            for srv in node.services:
                key = f"{srv.name}:{srv.role}"
                if key not in seen_services:
                    seen_services.add(key)
                    service_total += 1
                    status, reason = self._validate_service_info(srv, node.name)
                    if status == ValidationStatus.SUPPORTED:
                        service_supported += 1
                    else:
                        unsupported_list.append(UnsupportedEntityRecord(
                            entity_type="service",
                            name=srv.name,
                            reason=reason,
                            evidence_count=len(srv.evidence)
                        ))

        # --- Validate actions ---
        action_supported = 0
        action_total = 0
        seen_actions = set()

        for node in model.nodes:
            for act in node.actions:
                key = f"{act.name}:{act.role}"
                if key not in seen_actions:
                    seen_actions.add(key)
                    action_total += 1
                    status, reason = self._validate_action_info(act, node.name)
                    if status == ValidationStatus.SUPPORTED:
                        action_supported += 1
                    else:
                        unsupported_list.append(UnsupportedEntityRecord(
                            entity_type="action",
                            name=act.name,
                            reason=reason,
                            evidence_count=len(act.evidence)
                        ))

        # --- Aggregate metrics ---
        total_entities = node_total + topic_total + service_total + action_total
        total_supported = node_supported + topic_supported + service_supported + action_supported
        total_unsupported = total_entities - total_supported

        evidence_coverage = (total_supported / total_entities) if total_entities > 0 else 0.0
        unsupported_rate = (total_unsupported / total_entities) if total_entities > 0 else 0.0

        node_cov = (node_supported / node_total) if node_total > 0 else 0.0
        topic_cov = (topic_supported / topic_total) if topic_total > 0 else 0.0
        service_cov = (service_supported / service_total) if service_total > 0 else 0.0
        action_cov = (action_supported / action_total) if action_total > 0 else 0.0

        report = ValidationReport(
            repo_name=model.repo_name,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            total_entities=total_entities,
            supported_entities=total_supported,
            unsupported_entities=total_unsupported,
            partial_entities=0,
            evidence_coverage=round(evidence_coverage, 4),
            unsupported_entity_rate=round(unsupported_rate, 4),
            unsupported_list=unsupported_list,
            node_coverage=round(node_cov, 4),
            topic_coverage=round(topic_cov, 4),
            service_coverage=round(service_cov, 4),
            action_coverage=round(action_cov, 4),
        )

        logger.info(
            f"Evidence validation complete: "
            f"{total_supported}/{total_entities} entities supported "
            f"(coverage={evidence_coverage:.1%})"
        )
        return report

    # ------------------------------------------------------------------
    # Per-entity validation helpers
    # ------------------------------------------------------------------

    def _validate_node(self, node: ROS2Node) -> Tuple[ValidationStatus, str]:
        """
        Validate a single ROS2Node.

        Checks:
            1. Node has at least one EvidenceItem
            2. Referenced source file exists (if repo_root given)
        """
        if not node.evidence:
            return (
                ValidationStatus.UNSUPPORTED,
                "No evidence items — node may be launch-only (C++ executable) or LLM-inferred"
            )

        primary = node.evidence[0]
        file_ok, file_reason = self._check_file_exists(primary.file)
        if not file_ok:
            return ValidationStatus.UNSUPPORTED, file_reason

        return ValidationStatus.SUPPORTED, ""

    def _validate_topic_info(self, topic: TopicInfo, parent_node: str) -> Tuple[ValidationStatus, str]:
        """
        Validate a TopicInfo (publisher or subscriber).

        Checks:
            1. Has at least one EvidenceItem
            2. Referenced source file exists (if repo_root given)
        """
        if not topic.evidence:
            return (
                ValidationStatus.UNSUPPORTED,
                f"Topic '{topic.name}' has no evidence items (parent node: {parent_node})"
            )

        primary = topic.evidence[0]
        file_ok, file_reason = self._check_file_exists(primary.file)
        if not file_ok:
            return ValidationStatus.UNSUPPORTED, file_reason

        return ValidationStatus.SUPPORTED, ""

    def _validate_service_info(self, service: ServiceInfo, parent_node: str) -> Tuple[ValidationStatus, str]:
        """Validate a ServiceInfo"""
        if not service.evidence:
            return (
                ValidationStatus.UNSUPPORTED,
                f"Service '{service.name}' has no evidence items (parent node: {parent_node})"
            )

        primary = service.evidence[0]
        file_ok, file_reason = self._check_file_exists(primary.file)
        if not file_ok:
            return ValidationStatus.UNSUPPORTED, file_reason

        return ValidationStatus.SUPPORTED, ""

    def _validate_action_info(self, action: ActionInfo, parent_node: str) -> Tuple[ValidationStatus, str]:
        """Validate an ActionInfo"""
        if not action.evidence:
            return (
                ValidationStatus.UNSUPPORTED,
                f"Action '{action.name}' has no evidence items (parent node: {parent_node})"
            )

        primary = action.evidence[0]
        file_ok, file_reason = self._check_file_exists(primary.file)
        if not file_ok:
            return ValidationStatus.UNSUPPORTED, file_reason

        return ValidationStatus.SUPPORTED, ""

    def _check_file_exists(self, relative_path: str) -> Tuple[bool, str]:
        """
        Check whether the referenced evidence file exists on disk.
        If repo_root is not set, always returns True (schema-only mode).
        """
        if not self.repo_root or not relative_path:
            return True, ""  # Skip file check — schema-only mode

        full_path = self.repo_root / relative_path
        if full_path.exists():
            return True, ""

        # Try without leading path separator variants
        alt = self.repo_root / relative_path.lstrip("/\\")
        if alt.exists():
            return True, ""

        return False, f"Evidence file not found: {relative_path}"

    def annotate_model(self, model: ArchitectureModel, report: ValidationReport) -> ArchitectureModel:
        """
        Annotate the ArchitectureModel with per-node validation_status and
        attach the ValidationReport to model.validation_report.

        Returns the same model object (mutated in place).
        """
        # Build lookup: entity name -> unsupported reason
        unsupported_names = {r.name for r in report.unsupported_list}

        for node in model.nodes:
            node_id = node.name or node.fully_qualified_name
            if node_id in unsupported_names:
                node.validation_status = ValidationStatus.UNSUPPORTED
            elif node.evidence:
                node.validation_status = ValidationStatus.SUPPORTED
            else:
                node.validation_status = ValidationStatus.UNKNOWN

        model.validation_report = report
        return model


def run_evidence_validation(
    model: ArchitectureModel,
    repo_root: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Tuple[ArchitectureModel, ValidationReport]:
    """
    Convenience wrapper: run evidence validation and optionally save report.

    Args:
        model: ArchitectureModel to validate
        repo_root: Repository root for file-existence checks
        output_path: Optional path to save ValidationReport JSON

    Returns:
        (annotated_model, report)
    """
    import json

    validator = EvidenceValidator(repo_root=repo_root)
    report = validator.validate(model)
    model = validator.annotate_model(model, report)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report.model_dump(), indent=2),
            encoding="utf-8"
        )
        logger.info(f"Evidence validation report saved to {output_path}")

    return model, report


if __name__ == "__main__":
    import sys
    import json
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python -m src.evidence_validator <architecture.json> [repo_root] [output_report.json]")
        sys.exit(1)

    arch_path = Path(sys.argv[1])
    repo_root = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 else arch_path.parent / "validation_report.json"

    with open(arch_path, "r", encoding="utf-8") as f:
        arch_data = json.load(f)

    from src.schema import ArchitectureModel
    model = ArchitectureModel.model_validate(arch_data)

    model, report = run_evidence_validation(model, repo_root=repo_root, output_path=out_path)

    print(f"\n=== Evidence Validation Report ===")
    print(f"Repository: {report.repo_name}")
    print(f"Total Entities:       {report.total_entities}")
    print(f"Supported Entities:   {report.supported_entities}")
    print(f"Unsupported Entities: {report.unsupported_entities}")
    print(f"Evidence Coverage:    {report.evidence_coverage:.1%}")
    print(f"Node Coverage:        {report.node_coverage:.1%}")
    print(f"Topic Coverage:       {report.topic_coverage:.1%}")
    print(f"Service Coverage:     {report.service_coverage:.1%}")
    print(f"Action Coverage:      {report.action_coverage:.1%}")
    if report.unsupported_list:
        print(f"\nUnsupported Entities:")
        for u in report.unsupported_list[:10]:
            print(f"  [{u.entity_type}] {u.name}: {u.reason}")
