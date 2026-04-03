from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..models import Finding, FormContext


@dataclass(frozen=True)
class RuleOptions:
    allowed_spacing_values: tuple[int, ...] = ()


RuleRunner = Callable[[FormContext, str, RuleOptions], list[Finding]]


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    default_severity: str
    summary: str
    run: RuleRunner
