from __future__ import annotations

from ..models import Finding, FormContext
from .base import RuleDefinition, RuleOptions
from .common import element_ignores_rule


def rule_inside_bounds(
    context: FormContext,
    severity: str,
    options: RuleOptions,
) -> list[Finding]:
    del options
    if context.width is None or context.height is None:
        return [
            Finding(
                file_path=context.display_path,
                rule_id="inside_bounds",
                severity=severity,
                message="inside_bounds requires root form width and height",
            )
        ]

    findings: list[Finding] = []
    for page in context.pages:
        for element in page.elements:
            if element_ignores_rule(element.ignores, "inside_bounds"):
                continue
            if (
                element.frame.left < 0
                or element.frame.top < 0
                or element.frame.right > context.width
                or element.frame.bottom > context.height
            ):
                findings.append(
                    Finding(
                        file_path=context.display_path,
                        rule_id="inside_bounds",
                        severity=severity,
                        message=f"Element '{element.element_id}' frame is outside form bounds",
                        page_index=page.index,
                        element_ids=(element.element_id,),
                    )
                )
    return findings


RULE = RuleDefinition(
    rule_id="inside_bounds",
    default_severity="error",
    summary="Ensure each element stays inside the root form bounds.",
    run=rule_inside_bounds,
)
