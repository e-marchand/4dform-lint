from __future__ import annotations

from ..models import Frame
from ..native import native_event_names


def element_ignores_rule(element_ignores: set[str], rule_id: str) -> bool:
    return rule_id in element_ignores


def frames_intersect(first: Frame, second: Frame) -> bool:
    return (
        first.left < second.right
        and first.right > second.left
        and first.top < second.bottom
        and first.bottom > second.top
    )
