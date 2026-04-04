from __future__ import annotations

from pathlib import Path

from ..models import Finding, FormContext
from .base import RuleDefinition, RuleOptions
from .common import (
    element_ignores_rule,
    method_path_is_within_form_folder,
    method_value_looks_like_file_reference,
    object_method_name,
    resolve_form_local_method_path,
)


RULE_ID = "object_method_file_exists"


def rule_object_method_file_exists(
    context: FormContext,
    severity: str,
    options: RuleOptions,
) -> list[Finding]:
    del options
    findings: list[Finding] = []

    for page in context.pages:
        for element in page.elements:
            if element_ignores_rule(element.ignores, RULE_ID):
                continue

            method_name = object_method_name(element.native_object)
            if method_name is None or not method_value_looks_like_file_reference(method_name):
                continue

            resolved_path = resolve_form_local_method_path(context.source_path, method_name)
            if not method_path_is_within_form_folder(context.source_path, method_name):
                findings.append(
                    Finding(
                        file_path=context.display_path,
                        rule_id=RULE_ID,
                        severity=severity,
                        message=_outside_form_folder_message(
                            element.element_id,
                            method_name,
                            context.source_path.parent,
                        ),
                        page_index=page.index,
                        element_ids=(element.element_id,),
                    )
                )
                continue

            if resolved_path.is_file():
                continue

            findings.append(
                Finding(
                    file_path=context.display_path,
                    rule_id=RULE_ID,
                    severity=severity,
                    message=_missing_method_file_message(
                        element.element_id,
                        method_name,
                        resolved_path,
                    ),
                    page_index=page.index,
                    element_ids=(element.element_id,),
                )
            )

    return findings


def _missing_method_file_message(element_id: str, method_name: str, resolved_path: Path) -> str:
    return (
        f"Element '{element_id}' defines file method '{method_name}' but "
        f"'{resolved_path.as_posix()}' does not exist"
    )


def _outside_form_folder_message(element_id: str, method_name: str, form_dir: Path) -> str:
    return (
        f"Element '{element_id}' defines file method '{method_name}' but it resolves outside "
        f"the form folder '{form_dir.as_posix()}'"
    )


RULE = RuleDefinition(
    rule_id=RULE_ID,
    default_severity="error",
    summary="Error when an object method points to a missing form-local .4dm file.",
    run=rule_object_method_file_exists,
)
