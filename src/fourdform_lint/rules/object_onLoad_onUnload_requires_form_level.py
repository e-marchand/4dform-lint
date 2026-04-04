from __future__ import annotations

from ..models import Finding, FormContext
from .base import RuleDefinition, RuleOptions
from .common import element_ignores_rule, native_event_names


RULE_ID = "object_onLoad_onUnload_requires_form_level"
OBJECT_LIFECYCLE_EVENTS = ("onLoad", "onUnload")


def rule_object_onLoad_onUnload_requires_form_level(
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

            object_events = native_event_names(element.native_object)
            missing_form_events = tuple(
                event
                for event in OBJECT_LIFECYCLE_EVENTS
                if event in object_events and event not in context.form_events
            )
            if not missing_form_events:
                continue

            findings.append(
                Finding(
                    file_path=context.display_path,
                    rule_id=RULE_ID,
                    severity=severity,
                    message=_message_for_element(element.element_id, missing_form_events),
                    page_index=page.index,
                    element_ids=(element.element_id,),
                )
            )
    return findings


def _message_for_element(element_id: str, missing_form_events: tuple[str, ...]) -> str:
    if len(missing_form_events) == 1:
        event = missing_form_events[0]
        return (
            f"Element '{element_id}' enables {event} but the form does not, "
            f"so {event} will never fire for that object"
        )

    events_label = " and ".join(missing_form_events)
    return (
        f"Element '{element_id}' enables {events_label} but the form does not, "
        "so those object events will never fire"
    )


RULE = RuleDefinition(
    rule_id=RULE_ID,
    default_severity="warning",
    summary="Warn when an object enables onLoad/onUnload without the matching form-level events.",
    run=rule_object_onLoad_onUnload_requires_form_level,
)
