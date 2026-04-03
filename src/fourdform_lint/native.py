from __future__ import annotations

import re
from pathlib import Path

from .models import ElementContext, FormContext, Frame, PageContext


PLACEMENT_RE = re.compile(r"^(below|above|rightOf|leftOf|centeredIn)\(([^)]+)\)$")


def infer_relations(
    current_frame: Frame,
    previous_elements: list[ElementContext],
    form_width: int | None,
    form_height: int | None,
) -> str | None:
    if form_width is not None and form_height is not None:
        centered_x = current_frame.left * 2 + current_frame.width == form_width
        centered_y = current_frame.top * 2 + current_frame.height == form_height
        if centered_x and centered_y:
            return "centeredIn(parent)"

    vertical_candidates: list[tuple[int, int, ElementContext]] = []
    horizontal_candidates: list[tuple[int, int, ElementContext]] = []

    for previous in previous_elements:
        previous_frame = previous.frame
        vertical_gap = current_frame.top - previous_frame.bottom
        horizontal_overlap = min(current_frame.right, previous_frame.right) - max(
            current_frame.left, previous_frame.left
        )
        if vertical_gap >= 0 and horizontal_overlap > 0:
            left_delta = abs(current_frame.left - previous_frame.left)
            vertical_candidates.append((vertical_gap, left_delta, previous))

        horizontal_gap = current_frame.left - previous_frame.right
        vertical_overlap = min(current_frame.bottom, previous_frame.bottom) - max(
            current_frame.top, previous_frame.top
        )
        if horizontal_gap >= 0 and vertical_overlap > 0:
            top_delta = abs(current_frame.top - previous_frame.top)
            horizontal_candidates.append((horizontal_gap, top_delta, previous))

    best_vertical = (
        min(vertical_candidates, key=lambda item: (item[1], item[0]))
        if vertical_candidates
        else None
    )
    best_horizontal = (
        min(horizontal_candidates, key=lambda item: (item[1], item[0]))
        if horizontal_candidates
        else None
    )

    if best_vertical is not None and best_horizontal is not None:
        vertical_gap, left_delta, vertical_reference = best_vertical
        horizontal_gap, top_delta, horizontal_reference = best_horizontal
        if left_delta < top_delta:
            return f"below({vertical_reference.element_id})"
        if top_delta < left_delta:
            return f"rightOf({horizontal_reference.element_id})"
        if vertical_gap <= horizontal_gap:
            return f"below({vertical_reference.element_id})"
        return f"rightOf({horizontal_reference.element_id})"

    if best_vertical is not None:
        _, _, reference = best_vertical
        return f"below({reference.element_id})"
    if best_horizontal is not None:
        _, _, reference = best_horizontal
        return f"rightOf({reference.element_id})"
    return None


def placement_target(placement: str | None) -> str | None:
    relation = placement_relation(placement)
    if relation is None:
        return None
    _, target = relation
    return target


def placement_relation(placement: str | None) -> tuple[str, str] | None:
    if placement is None:
        return None
    match = PLACEMENT_RE.fullmatch(placement)
    if match is None:
        return None
    relation, target = match.groups()
    return relation, target.strip()


def form_from_native(
    document: dict,
    source_path: Path,
    display_path: str,
    element_ignores: dict[tuple[int, str], set[str]],
    translations: dict[str, tuple[str, ...]] | None = None,
) -> FormContext:
    form_width = document.get("width") if isinstance(document.get("width"), int) else None
    form_height = document.get("height") if isinstance(document.get("height"), int) else None

    pages: list[PageContext] = []
    for page_index, page in enumerate(document.get("pages", [])):
        if page is None:
            continue

        previous_elements: list[ElementContext] = []
        elements: list[ElementContext] = []
        objects = page.get("objects", {})
        for element_id, native_object in objects.items():
            frame = Frame(
                top=int(native_object["top"]),
                left=int(native_object["left"]),
                width=int(native_object["width"]),
                height=int(native_object["height"]),
            )
            element = ElementContext(
                element_id=element_id,
                element_type=str(native_object["type"]),
                frame=frame,
                native_object=dict(native_object),
                ignores=set(element_ignores.get((page_index, element_id), set())),
                placement=infer_relations(frame, previous_elements, form_width, form_height),
            )
            elements.append(element)
            previous_elements.append(element)

        pages.append(PageContext(index=page_index, elements=elements))

    return FormContext(
        source_path=source_path,
        display_path=display_path,
        width=form_width,
        height=form_height,
        pages=pages,
        translations=dict(translations or {}),
    )
