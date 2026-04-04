from __future__ import annotations


def element_ignores_rule(element_ignores: set[str], rule_id: str) -> bool:
    return rule_id in element_ignores


def native_event_names(native_object: dict[str, object]) -> set[str]:
    raw_events = native_object.get("events")
    if isinstance(raw_events, dict):
        raw_events = raw_events.get("events")
    if not isinstance(raw_events, list):
        return set()
    return {event for event in raw_events if isinstance(event, str) and event.strip()}
