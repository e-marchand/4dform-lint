from __future__ import annotations

from itertools import combinations

from .models import Finding, FormContext
from .native import placement_relation


SPACING_PROXIMITY_MULTIPLIER = 2


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
