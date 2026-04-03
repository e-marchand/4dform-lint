from __future__ import annotations

from itertools import combinations

from ..models import Finding, FormContext
from .base import RuleDefinition, RuleOptions
from .common import element_ignores_rule


def rule_no_overlap(
    context: FormContext,
    severity: str,
    options: RuleOptions,
) -> list[Finding]:
    del options
    findings: list[Finding] = []
    for page in context.pages:
        for first, second in combinations(page.elements, 2):
            if element_ignores_rule(first.ignores, "no_overlap") or element_ignores_rule(
                second.ignores, "no_overlap"
            ):
                continue
            intersects = (
                first.frame.left < second.frame.right
                and first.frame.right > second.frame.left
                and first.frame.top < second.frame.bottom
                and first.frame.bottom > second.frame.top
            )
            if intersects:
                findings.append(
                    Finding(
                        file_path=context.display_path,
                        rule_id="no_overlap",
                        severity=severity,
                        message=f"Elements '{first.element_id}' and '{second.element_id}' overlap",
                        page_index=page.index,
                        element_ids=(first.element_id, second.element_id),
                    )
                )
    return findings


RULE = RuleDefinition(
    rule_id="no_overlap",
    default_severity="error",
    summary="Ensure two elements on the same page do not overlap.",
    run=rule_no_overlap,
)
