from __future__ import annotations

import math
import platform
from itertools import combinations

from .models import Finding, FormContext
from .native import placement_relation


SPACING_PROXIMITY_MULTIPLIER = 2
TEXT_FIT_TOLERANCE_PX = 6
DEFAULT_FONT_SIZE = 13
SUPPORTED_TEXT_TYPES = {"button", "checkbox", "radio", "text"}
BUTTON_HORIZONTAL_PADDING = {
    "regular": 28,
    "toolbar": 20,
    "bevel": 24,
    "roundedBevel": 26,
    "gradientBevel": 26,
    "texturedBevel": 26,
    "office": 24,
    "help": 14,
    "circular": 18,
    "custom": 16,
    "flat": 12,
}


def element_ignores_rule(element_ignores: set[str], rule_id: str) -> bool:
    return rule_id in element_ignores


def rule_shared_page_required(context: FormContext, severity: str) -> list[Finding]:
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


def rule_inside_bounds(context: FormContext, severity: str) -> list[Finding]:
    if context.width is None or context.height is None:
        return [
            Finding(
                file_path=context.display_path,
                rule_id="inside_bounds",
                severity=severity,
                message="inside_bounds requires root form width and height",
            )
        ]

    findings: list[Finding] = []
    for page in context.pages:
        for element in page.elements:
            if element_ignores_rule(element.ignores, "inside_bounds"):
                continue
            if (
                element.frame.left < 0
                or element.frame.top < 0
                or element.frame.right > context.width
                or element.frame.bottom > context.height
            ):
                findings.append(
                    Finding(
                        file_path=context.display_path,
                        rule_id="inside_bounds",
                        severity=severity,
                        message=f"Element '{element.element_id}' frame is outside form bounds",
                        page_index=page.index,
                        element_ids=(element.element_id,),
                    )
                )
    return findings


def rule_no_overlap(context: FormContext, severity: str) -> list[Finding]:
    findings: list[Finding] = []
    for page in context.pages:
        for first, second in combinations(page.elements, 2):
            if element_ignores_rule(first.ignores, "no_overlap") or element_ignores_rule(
                second.ignores, "no_overlap"
            ):
                continue
            intersects = (
                first.frame.left < second.frame.right
                and first.frame.right > second.frame.left
                and first.frame.top < second.frame.bottom
                and first.frame.bottom > second.frame.top
            )
            if intersects:
                findings.append(
                    Finding(
                        file_path=context.display_path,
                        rule_id="no_overlap",
                        severity=severity,
                        message=(
                            f"Elements '{first.element_id}' and '{second.element_id}' overlap"
                        ),
                        page_index=page.index,
                        element_ids=(first.element_id, second.element_id),
                    )
                )
    return findings


def rule_consistent_spacing(
    context: FormContext,
    severity: str,
    allowed_spacing_values: list[int],
) -> list[Finding]:
    allowed = set(allowed_spacing_values)
    max_gap_to_compare = max(allowed_spacing_values) * SPACING_PROXIMITY_MULTIPLIER
    findings: list[Finding] = []

    for page in context.pages:
        by_left: dict[int, list] = {}
        by_top: dict[int, list] = {}
        for element in page.elements:
            by_left.setdefault(element.frame.left, []).append(element)
            by_top.setdefault(element.frame.top, []).append(element)

        for group in by_left.values():
            ordered = sorted(group, key=lambda item: item.frame.top)
            for first, second in zip(ordered, ordered[1:]):
                if element_ignores_rule(first.ignores, "consistent_spacing") or element_ignores_rule(
                    second.ignores, "consistent_spacing"
                ):
                    continue
                gap = second.frame.top - first.frame.bottom
                if gap > 0 and gap <= max_gap_to_compare and gap not in allowed:
                    findings.append(
                        Finding(
                            file_path=context.display_path,
                            rule_id="consistent_spacing",
                            severity=severity,
                            message=(
                                f"Vertical spacing {gap} between '{first.element_id}' and "
                                f"'{second.element_id}' is not in allowed values {sorted(allowed)}"
                            ),
                            page_index=page.index,
                            element_ids=(first.element_id, second.element_id),
                        )
                    )

        for group in by_top.values():
            ordered = sorted(group, key=lambda item: item.frame.left)
            for first, second in zip(ordered, ordered[1:]):
                if element_ignores_rule(first.ignores, "consistent_spacing") or element_ignores_rule(
                    second.ignores, "consistent_spacing"
                ):
                    continue
                gap = second.frame.left - first.frame.right
                if gap > 0 and gap <= max_gap_to_compare and gap not in allowed:
                    findings.append(
                        Finding(
                            file_path=context.display_path,
                            rule_id="consistent_spacing",
                            severity=severity,
                            message=(
                                f"Horizontal spacing {gap} between '{first.element_id}' and "
                                f"'{second.element_id}' is not in allowed values {sorted(allowed)}"
                            ),
                            page_index=page.index,
                            element_ids=(first.element_id, second.element_id),
                        )
                    )
    return findings


def rule_alignment_consistency(context: FormContext, severity: str) -> list[Finding]:
    findings: list[Finding] = []
    for page in context.pages:
        element_map = {element.element_id: element for element in page.elements}
        for element in page.elements:
            if element_ignores_rule(element.ignores, "alignment_consistency"):
                continue
            relation = placement_relation(element.placement)
            if relation is None:
                continue
            placement_kind, target = relation
            if target == "parent":
                continue
            reference = element_map.get(target)
            if reference is None:
                continue
            if element_ignores_rule(reference.ignores, "alignment_consistency"):
                continue
            if placement_kind in {"below", "above"}:
                delta = element.frame.left - reference.frame.left
                if delta == 0:
                    continue
                direction = "to the right" if delta > 0 else "to the left"
                findings.append(
                    Finding(
                        file_path=context.display_path,
                        rule_id="alignment_consistency",
                        severity=severity,
                        message=(
                            f"Element '{element.element_id}' is placed {placement_kind} "
                            f"'{reference.element_id}', but its left edge is {abs(delta)} px "
                            f"{direction} (reference left={reference.frame.left}, "
                            f"element left={element.frame.left}). Align their left edges "
                            f"or ignore this rule for one of the elements."
                        ),
                        page_index=page.index,
                        element_ids=(reference.element_id, element.element_id),
                    )
                )
            elif placement_kind in {"rightOf", "leftOf"}:
                delta = element.frame.top - reference.frame.top
                if delta == 0:
                    continue
                direction = "lower" if delta > 0 else "higher"
                findings.append(
                    Finding(
                        file_path=context.display_path,
                        rule_id="alignment_consistency",
                        severity=severity,
                        message=(
                            f"Element '{element.element_id}' is placed {placement_kind} "
                            f"'{reference.element_id}', but its top edge is {abs(delta)} px "
                            f"{direction} (reference top={reference.frame.top}, "
                            f"element top={element.frame.top}). Align their top edges "
                            f"or ignore this rule for one of the elements."
                        ),
                        page_index=page.index,
                        element_ids=(reference.element_id, element.element_id),
                    )
                )
    return findings


def rule_text_fits(context: FormContext, severity: str) -> list[Finding]:
    findings: list[Finding] = []
    for page in context.pages:
        for element in page.elements:
            if element_ignores_rule(element.ignores, "text_fits"):
                continue

            raw_text = _element_text(element)
            if raw_text is None:
                continue

            text_candidates = _resolved_text_candidates(raw_text, context.translations)
            if not text_candidates:
                continue

            available_width = _available_text_width(element)
            if available_width <= 0:
                continue

            font_family = _font_family(element)
            font_size = _font_size(element)
            font_weight = _font_weight(element)
            font_style = _font_style(element)

            widest_text = ""
            widest_width = 0.0
            for candidate in text_candidates:
                width = estimate_text_width(
                    candidate,
                    font_size=font_size,
                    font_family=font_family,
                    font_weight=font_weight,
                    font_style=font_style,
                )
                if width > widest_width:
                    widest_width = width
                    widest_text = candidate

            if widest_width <= available_width + TEXT_FIT_TOLERANCE_PX:
                continue

            if _is_xliff_reference(raw_text):
                xliff_key = raw_text.split(":", 1)[1]
                message = (
                    f"Element '{element.element_id}' may crop text: longest XLIFF translation for "
                    f"'{xliff_key}' needs about {math.ceil(widest_width)} px, but only "
                    f"{available_width} px are available after intrinsic padding"
                )
            else:
                message = (
                    f"Element '{element.element_id}' may crop text {_preview_text(widest_text)}: "
                    f"needs about {math.ceil(widest_width)} px, but only {available_width} px "
                    f"are available after intrinsic padding"
                )

            findings.append(
                Finding(
                    file_path=context.display_path,
                    rule_id="text_fits",
                    severity=severity,
                    message=message,
                    page_index=page.index,
                    element_ids=(element.element_id,),
                )
            )
    return findings


def estimate_text_width(
    text: str,
    *,
    font_size: int,
    font_family: str | None,
    font_weight: str | None,
    font_style: str | None,
) -> float:
    family_name = (font_family or _default_font_family()).lower()
    if any(token in family_name for token in ("mono", "courier", "menlo", "consolas", "code")):
        base_width = len(text) * font_size * 0.62
    else:
        base_width = 0.0
        for character in text:
            base_width += font_size * _character_width_factor(character)
        base_width += font_size * 0.2

    family_factor = 1.0
    if any(token in family_name for token in ("condensed", "narrow")):
        family_factor *= 0.92
    if any(token in family_name for token in ("expanded", "extended")):
        family_factor *= 1.08
    if any(token in family_name for token in ("serif", "times", "georgia")):
        family_factor *= 1.03
    if any(token in family_name for token in ("black", "impact")):
        family_factor *= 1.06

    weight_factor = 1.06 if font_weight == "bold" else 1.0
    style_factor = 1.03 if font_style == "italic" else 1.0
    return base_width * family_factor * weight_factor * style_factor


def _element_text(element) -> str | None:
    if element.element_type not in SUPPORTED_TEXT_TYPES:
        return None
    value = element.native_object.get("text")
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _resolved_text_candidates(
    raw_text: str,
    translations: dict[str, tuple[str, ...]],
) -> list[str]:
    if _is_xliff_reference(raw_text):
        key = raw_text.split(":", 1)[1]
        return [value for value in translations.get(key, ()) if value]
    return [raw_text]


def _is_xliff_reference(value: str) -> bool:
    return value.lower().startswith("xliff:")


def _available_text_width(element) -> int:
    reserved = 0

    if element.element_type == "button":
        style = element.native_object.get("style")
        if not isinstance(style, str):
            style = "regular"
        reserved += BUTTON_HORIZONTAL_PADDING.get(style, BUTTON_HORIZONTAL_PADDING["regular"])
        if element.native_object.get("defaultButton") is True:
            reserved += 6
        if element.native_object.get("popupPlacement") in {"linked", "separated"}:
            reserved += 14
        if element.native_object.get("icon"):
            text_placement = element.native_object.get("textPlacement")
            if text_placement in {None, "left", "right", "center"}:
                reserved += 20
        if style == "custom":
            custom_border_x = element.native_object.get("customBorderX")
            if isinstance(custom_border_x, int):
                reserved = max(reserved, custom_border_x * 2 + 8)
    elif element.element_type in {"checkbox", "radio"}:
        reserved += 24

    return max(0, element.frame.width - reserved)


def _font_family(element) -> str:
    family = element.native_object.get("fontFamily")
    if isinstance(family, str) and family.strip():
        return family.strip()
    return _default_font_family()


def _font_size(element) -> int:
    size = element.native_object.get("fontSize")
    if isinstance(size, int) and size > 0:
        return size
    return DEFAULT_FONT_SIZE


def _font_weight(element) -> str | None:
    value = element.native_object.get("fontWeight")
    return value if value in {"normal", "bold"} else None


def _font_style(element) -> str | None:
    value = element.native_object.get("fontStyle")
    return value if value in {"normal", "italic"} else None


def _default_font_family() -> str:
    system = platform.system()
    if system == "Darwin":
        return "SF Pro Text"
    if system == "Windows":
        return "Segoe UI"
    return "Noto Sans"


def _character_width_factor(character: str) -> float:
    if character.isspace():
        return 0.35
    if character in "ilI1|!.,:;'`":
        return 0.34
    if character in "MW@#%&QGm":
        return 0.9
    if character in "()[]{}<>/\\*^":
        return 0.45
    if character.isdigit():
        return 0.58
    if character.isupper():
        return 0.68
    if ord(character) > 127:
        return 0.78
    return 0.56


def _preview_text(value: str, limit: int = 40) -> str:
    if len(value) <= limit:
        return f"'{value}'"
    return f"'{value[: limit - 3]}...'"
