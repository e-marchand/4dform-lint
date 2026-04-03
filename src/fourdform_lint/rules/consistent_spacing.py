from __future__ import annotations

from ..models import Finding, FormContext
from .base import RuleDefinition, RuleOptions
from .common import element_ignores_rule


SPACING_PROXIMITY_MULTIPLIER = 2


def rule_consistent_spacing(
    context: FormContext,
    severity: str,
    options: RuleOptions,
) -> list[Finding]:
    allowed_spacing_values = list(options.allowed_spacing_values)
    allowed = set(allowed_spacing_values)
    max_gap_to_compare = max(allowed_spacing_values) * SPACING_PROXIMITY_MULTIPLIER
    findings: list[Finding] = []

    for page in context.pages:
        by_left: dict[int, list] = {}
        by_top: dict[int, list] = {}
        for element in page.elements:
            by_left.setdefault(element.frame.left, []).append(element)
            by_top.setdefault(element.frame.top, []).append(element)

        for group in by_left.values():
            ordered = sorted(group, key=lambda item: item.frame.top)
            for first, second in zip(ordered, ordered[1:]):
                if element_ignores_rule(first.ignores, "consistent_spacing") or element_ignores_rule(
                    second.ignores, "consistent_spacing"
                ):
                    continue
                gap = second.frame.top - first.frame.bottom
                if gap > 0 and gap <= max_gap_to_compare and gap not in allowed:
                    findings.append(
                        Finding(
                            file_path=context.display_path,
                            rule_id="consistent_spacing",
                            severity=severity,
                            message=(
                                f"Vertical spacing {gap} between '{first.element_id}' and "
                                f"'{second.element_id}' is not in allowed values {sorted(allowed)}"
                            ),
                            page_index=page.index,
                            element_ids=(first.element_id, second.element_id),
                        )
                    )

        for group in by_top.values():
            ordered = sorted(group, key=lambda item: item.frame.left)
            for first, second in zip(ordered, ordered[1:]):
                if element_ignores_rule(first.ignores, "consistent_spacing") or element_ignores_rule(
                    second.ignores, "consistent_spacing"
                ):
                    continue
                gap = second.frame.left - first.frame.right
                if gap > 0 and gap <= max_gap_to_compare and gap not in allowed:
                    findings.append(
                        Finding(
                            file_path=context.display_path,
                            rule_id="consistent_spacing",
                            severity=severity,
                            message=(
                                f"Horizontal spacing {gap} between '{first.element_id}' and "
                                f"'{second.element_id}' is not in allowed values {sorted(allowed)}"
                            ),
                            page_index=page.index,
                            element_ids=(first.element_id, second.element_id),
                        )
                    )
    return findings


RULE = RuleDefinition(
    rule_id="consistent_spacing",
    default_severity="warning",
    summary="Check nearby gaps in aligned rows and columns against allowed spacing values.",
    run=rule_consistent_spacing,
)
