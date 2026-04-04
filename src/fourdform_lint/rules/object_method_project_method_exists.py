from __future__ import annotations

from pathlib import Path

from ..models import Finding, FormContext
from .base import RuleDefinition, RuleOptions
from .common import (
    element_ignores_rule,
    method_value_looks_like_file_reference,
    object_method_name,
    project_methods_dir_for_form,
)


RULE_ID = "object_method_project_method_exists"


def rule_object_method_project_method_exists(
    context: FormContext,
    severity: str,
    options: RuleOptions,
) -> list[Finding]:
    del options
    findings: list[Finding] = []
    methods_dir = project_methods_dir_for_form(context.source_path)
    if methods_dir is None:
        return findings

    for page in context.pages:
        for element in page.elements:
            if element_ignores_rule(element.ignores, RULE_ID):
                continue

            method_name = object_method_name(element.native_object)
            if method_name is None or method_value_looks_like_file_reference(method_name):
                continue

            resolved_path = _project_method_path(methods_dir, method_name)
            if resolved_path is not None and resolved_path.is_file():
                continue

            findings.append(
                Finding(
                    file_path=context.display_path,
                    rule_id=RULE_ID,
                    severity=severity,
                    message=_missing_project_method_message(
                        element.element_id,
                        method_name,
                        resolved_path,
                    ),
                    page_index=page.index,
                    element_ids=(element.element_id,),
                )
            )

    return findings


def _project_method_path(methods_dir: Path | None, method_name: str) -> Path | None:
    if methods_dir is None:
        return None
    return methods_dir / f"{method_name}.4dm"


def _missing_project_method_message(
    element_id: str,
    method_name: str,
    resolved_path: Path,
) -> str:
    return (
        f"Element '{element_id}' defines bare method '{method_name}' but "
        f"'{resolved_path.as_posix()}' was not found; this may still come from another project "
        "or component"
    )


RULE = RuleDefinition(
    rule_id=RULE_ID,
    default_severity="warning",
    summary="Warn when a bare object method does not resolve to a local Project/Sources/Methods file.",
    run=rule_object_method_project_method_exists,
)
