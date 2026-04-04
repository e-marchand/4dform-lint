from __future__ import annotations

from ..models import Finding, FormContext
from .base import RuleDefinition, RuleOptions
from .common import element_ignores_rule, native_event_names, object_method_name


CLICKABLE_TYPES = {"button", "checkbox", "radio"}


def rule_events_required_for_method(
    context: FormContext,
    severity: str,
    options: RuleOptions,
) -> list[Finding]:
    del options
    findings: list[Finding] = []

    for page in context.pages:
        for element in page.elements:
            if element_ignores_rule(element.ignores, "events_required_for_method"):
                continue

            method = object_method_name(element.native_object)
            if method is None:
                continue

            events = native_event_names(element.native_object)
            if not events:
                findings.append(
                    Finding(
                        file_path=context.display_path,
                        rule_id="events_required_for_method",
                        severity=severity,
                        message=(
                            f"Element '{element.element_id}' defines method '{method}' but enables "
                            "no events, so the method will never run from object events"
                        ),
                        page_index=page.index,
                        element_ids=(element.element_id,),
                    )
                )
                continue

            if element.element_type in CLICKABLE_TYPES and "onClick" not in events:
                findings.append(
                    Finding(
                        file_path=context.display_path,
                        rule_id="events_required_for_method",
                        severity=severity,
                        message=(
                            f"Clickable element '{element.element_id}' defines method '{method}' but "
                            "does not enable onClick"
                        ),
                        page_index=page.index,
                        element_ids=(element.element_id,),
                    )
                )

    return findings


RULE = RuleDefinition(
    rule_id="events_required_for_method",
    default_severity="warning",
    summary="Warn when an object method is defined without the events needed to trigger it.",
    run=rule_events_required_for_method,
)
