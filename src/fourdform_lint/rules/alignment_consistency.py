from __future__ import annotations

from ..models import Finding, FormContext
from ..native import placement_relation
from .base import RuleDefinition, RuleOptions
from .common import element_ignores_rule


def rule_alignment_consistency(
    context: FormContext,
    severity: str,
    options: RuleOptions,
) -> list[Finding]:
    del options
    findings: list[Finding] = []
    for page in context.pages:
        element_map = {element.element_id: element for element in page.elements}
        for element in page.elements:
            if element_ignores_rule(element.ignores, "alignment_consistency"):
                continue
            relation = placement_relation(element.placement)
            if relation is None:
                continue
            placement_kind, target = relation
            if target == "parent":
                continue
            reference = element_map.get(target)
            if reference is None:
                continue
            if element_ignores_rule(reference.ignores, "alignment_consistency"):
                continue
            if placement_kind in {"below", "above"}:
                delta = element.frame.left - reference.frame.left
                if delta == 0:
                    continue
                direction = "to the right" if delta > 0 else "to the left"
                findings.append(
                    Finding(
                        file_path=context.display_path,
                        rule_id="alignment_consistency",
                        severity=severity,
                        message=(
                            f"Element '{element.element_id}' is placed {placement_kind} "
                            f"'{reference.element_id}', but its left edge is {abs(delta)} px "
                            f"{direction} (reference left={reference.frame.left}, "
                            f"element left={element.frame.left}). Align their left edges "
                            f"or ignore this rule for one of the elements."
                        ),
                        page_index=page.index,
                        element_ids=(reference.element_id, element.element_id),
                    )
                )
            elif placement_kind in {"rightOf", "leftOf"}:
                delta = element.frame.top - reference.frame.top
                if delta == 0:
                    continue
                direction = "lower" if delta > 0 else "higher"
                findings.append(
                    Finding(
                        file_path=context.display_path,
                        rule_id="alignment_consistency",
                        severity=severity,
                        message=(
                            f"Element '{element.element_id}' is placed {placement_kind} "
                            f"'{reference.element_id}', but its top edge is {abs(delta)} px "
                            f"{direction} (reference top={reference.frame.top}, "
                            f"element top={element.frame.top}). Align their top edges "
                            f"or ignore this rule for one of the elements."
                        ),
                        page_index=page.index,
                        element_ids=(reference.element_id, element.element_id),
                    )
                )
    return findings


RULE = RuleDefinition(
    rule_id="alignment_consistency",
    default_severity="warning",
    summary="Check inferred placement relationships for left-edge or top-edge alignment drift.",
    run=rule_alignment_consistency,
)
