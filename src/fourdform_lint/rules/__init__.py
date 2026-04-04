from __future__ import annotations

from .alignment_consistency import RULE as ALIGNMENT_CONSISTENCY_RULE
from .alignment_consistency import rule_alignment_consistency
from .base import RuleDefinition, RuleOptions
from .consistent_spacing import RULE as CONSISTENT_SPACING_RULE
from .consistent_spacing import rule_consistent_spacing
from .events_required_for_method import RULE as EVENTS_REQUIRED_FOR_METHOD_RULE
from .events_required_for_method import rule_events_required_for_method
from .inside_bounds import RULE as INSIDE_BOUNDS_RULE
from .inside_bounds import rule_inside_bounds
from .no_overlap import RULE as NO_OVERLAP_RULE
from .no_overlap import rule_no_overlap
from .object_method_file_exists import RULE as OBJECT_METHOD_FILE_EXISTS_RULE
from .object_method_file_exists import rule_object_method_file_exists
from .object_method_project_method_exists import (
    RULE as OBJECT_METHOD_PROJECT_METHOD_EXISTS_RULE,
)
from .object_method_project_method_exists import rule_object_method_project_method_exists
from .object_onLoad_onUnload_requires_form_level import (
    RULE as OBJECT_ONLOAD_ONUNLOAD_REQUIRES_FORM_LEVEL_RULE,
)
from .object_onLoad_onUnload_requires_form_level import (
    rule_object_onLoad_onUnload_requires_form_level,
)
from .page0_cross_page_overlap import RULE as PAGE0_CROSS_PAGE_OVERLAP_RULE
from .page0_cross_page_overlap import rule_page0_cross_page_overlap
from .shared_page_required import RULE as SHARED_PAGE_REQUIRED_RULE
from .shared_page_required import rule_shared_page_required
from .text_fits import RULE as TEXT_FITS_RULE
from .text_fits import estimate_text_width, rule_text_fits


RULE_DEFINITIONS: tuple[RuleDefinition, ...] = (
    NO_OVERLAP_RULE,
    INSIDE_BOUNDS_RULE,
    CONSISTENT_SPACING_RULE,
    ALIGNMENT_CONSISTENCY_RULE,
    EVENTS_REQUIRED_FOR_METHOD_RULE,
    OBJECT_METHOD_FILE_EXISTS_RULE,
    OBJECT_METHOD_PROJECT_METHOD_EXISTS_RULE,
    OBJECT_ONLOAD_ONUNLOAD_REQUIRES_FORM_LEVEL_RULE,
    PAGE0_CROSS_PAGE_OVERLAP_RULE,
    SHARED_PAGE_REQUIRED_RULE,
    TEXT_FITS_RULE,
)
RULES_BY_ID = {rule.rule_id: rule for rule in RULE_DEFINITIONS}
VALID_RULE_IDS = frozenset(RULES_BY_ID)
DEFAULT_RULES = {rule.rule_id: rule.default_severity for rule in RULE_DEFINITIONS}
RULE_SUMMARIES = {rule.rule_id: rule.summary for rule in RULE_DEFINITIONS}

__all__ = [
    "DEFAULT_RULES",
    "RULE_DEFINITIONS",
    "RULE_SUMMARIES",
    "RULES_BY_ID",
    "RuleDefinition",
    "RuleOptions",
    "VALID_RULE_IDS",
    "estimate_text_width",
    "rule_alignment_consistency",
    "rule_consistent_spacing",
    "rule_events_required_for_method",
    "rule_inside_bounds",
    "rule_no_overlap",
    "rule_object_method_file_exists",
    "rule_object_method_project_method_exists",
    "rule_object_onLoad_onUnload_requires_form_level",
    "rule_page0_cross_page_overlap",
    "rule_shared_page_required",
    "rule_text_fits",
]
