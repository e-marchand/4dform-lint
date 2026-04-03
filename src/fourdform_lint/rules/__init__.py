from __future__ import annotations

from .alignment_consistency import RULE as ALIGNMENT_CONSISTENCY_RULE
from .alignment_consistency import rule_alignment_consistency
from .base import RuleDefinition, RuleOptions
from .consistent_spacing import RULE as CONSISTENT_SPACING_RULE
from .consistent_spacing import rule_consistent_spacing
from .inside_bounds import RULE as INSIDE_BOUNDS_RULE
from .inside_bounds import rule_inside_bounds
from .no_overlap import RULE as NO_OVERLAP_RULE
from .no_overlap import rule_no_overlap
from .shared_page_required import RULE as SHARED_PAGE_REQUIRED_RULE
from .shared_page_required import rule_shared_page_required
from .text_fits import RULE as TEXT_FITS_RULE
from .text_fits import estimate_text_width, rule_text_fits


RULE_DEFINITIONS: tuple[RuleDefinition, ...] = (
    NO_OVERLAP_RULE,
    INSIDE_BOUNDS_RULE,
    CONSISTENT_SPACING_RULE,
    ALIGNMENT_CONSISTENCY_RULE,
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
    "rule_inside_bounds",
    "rule_no_overlap",
    "rule_shared_page_required",
    "rule_text_fits",
]
