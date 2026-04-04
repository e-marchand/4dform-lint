from __future__ import annotations

from ..native import native_event_names


def element_ignores_rule(element_ignores: set[str], rule_id: str) -> bool:
    return rule_id in element_ignores
