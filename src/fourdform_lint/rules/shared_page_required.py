from __future__ import annotations

from ..models import Finding, FormContext
from .base import RuleDefinition, RuleOptions


def rule_shared_page_required(
    context: FormContext,
    severity: str,
    options: RuleOptions,
) -> list[Finding]:
    del options
    page_indexes = {page.index for page in context.pages}
    if len(context.pages) >= 2 and {0, 1}.issubset(page_indexes):
        return []
    return [
        Finding(
            file_path=context.display_path,
            rule_id="shared_page_required",
            severity=severity,
            message="Form must contain both shared page 0 and visible page 1",
        )
    ]


RULE = RuleDefinition(
    rule_id="shared_page_required",
    default_severity="off",
    summary="Require at least two pages: shared page 0 and visible page 1.",
    run=rule_shared_page_required,
)
