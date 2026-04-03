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
    if 0 in page_indexes and 1 in page_indexes:
        return []
    return [
        Finding(
            file_path=context.display_path,
            rule_id="shared_page_required",
            severity=severity,
            message="Form must contain shared page 0 and at least one visible page 1",
        )
    ]


RULE = RuleDefinition(
    rule_id="shared_page_required",
    default_severity="off",
    summary="Require shared page 0 and at least one visible page 1.",
    run=rule_shared_page_required,
)
