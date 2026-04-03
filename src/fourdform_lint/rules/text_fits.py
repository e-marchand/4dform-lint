from __future__ import annotations

import math
import platform

from ..models import Finding, FormContext
from .base import RuleDefinition, RuleOptions
from .common import element_ignores_rule


TEXT_FIT_TOLERANCE_PX = 6
DEFAULT_FONT_SIZE = 13
SUPPORTED_TEXT_TYPES = {"button", "checkbox", "radio", "text"}
BUTTON_HORIZONTAL_PADDING = {
    "regular": 18,
    "toolbar": 10,
    "bevel": 14,
    "roundedBevel": 16,
    "gradientBevel": 16,
    "texturedBevel": 16,
    "office": 14,
    "help": 4,
    "circular": 8,
    "custom": 6,
    "flat": 2,
}


def rule_text_fits(
    context: FormContext,
    severity: str,
    options: RuleOptions,
) -> list[Finding]:
    del options
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


RULE = RuleDefinition(
    rule_id="text_fits",
    default_severity="warning",
    summary="Estimate whether single-line native control text is likely to be cropped.",
    run=rule_text_fits,
)
