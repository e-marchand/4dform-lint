from __future__ import annotations

from ..models import Finding, FormContext
from .base import RuleDefinition, RuleOptions
from .common import element_ignores_rule, frames_intersect


RULE_ID = "page0_cross_page_overlap"


def rule_page0_cross_page_overlap(
    context: FormContext,
    severity: str,
    options: RuleOptions,
) -> list[Finding]:
    del options
    findings: list[Finding] = []

    shared_page = next((page for page in context.pages if page.index == 0), None)
    if shared_page is None:
        return findings

    for page in context.pages:
        if page.index < 1:
            continue
        for shared_element in shared_page.elements:
            if element_ignores_rule(shared_element.ignores, RULE_ID):
                continue
            for page_element in page.elements:
                if element_ignores_rule(page_element.ignores, RULE_ID):
                    continue
                if not frames_intersect(shared_element.frame, page_element.frame):
                    continue
                findings.append(
                    Finding(
                        file_path=context.display_path,
                        rule_id=RULE_ID,
                        severity=severity,
                        message=(
                            f"Shared page 0 element '{shared_element.element_id}' overlaps "
                            f"page {page.index} element '{page_element.element_id}'"
                        ),
                        page_index=page.index,
                        element_ids=(shared_element.element_id, page_element.element_id),
                    )
                )

    return findings


RULE = RuleDefinition(
    rule_id=RULE_ID,
    default_severity="warning",
    summary="Warn when a shared page 0 element overlaps content on a visible page.",
    run=rule_page0_cross_page_overlap,
)
