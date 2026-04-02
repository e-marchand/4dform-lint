from __future__ import annotations

import json
import os
from pathlib import Path

from .config import EffectiveConfig, LoadedConfig, effective_config_for
from .models import Finding
from .native import form_from_native
from .rules import (
    rule_alignment_consistency,
    rule_consistent_spacing,
    rule_inside_bounds,
    rule_no_overlap,
    rule_shared_page_required,
)
from .schema import load_native_form, validate_native_form


class UsageError(ValueError):
    pass


def discover_form_files(inputs: list[str], cwd: Path) -> list[Path]:
    discovered: set[Path] = set()
    for raw_input in inputs:
        candidate = Path(raw_input)
        if not candidate.is_absolute():
            candidate = (cwd / candidate).resolve()
        if not candidate.exists():
            raise UsageError(f"Input path does not exist: {raw_input}")
        if candidate.is_file():
            if candidate.suffix == ".4DForm":
                discovered.add(candidate)
            continue
        for path in candidate.rglob("*.4DForm"):
            discovered.add(path.resolve())
    return sorted(discovered, key=lambda path: path.as_posix())


def display_path(path: Path, cwd: Path) -> str:
    try:
        return os.path.relpath(path, cwd).replace(os.sep, "/")
    except ValueError:
        return path.as_posix()


def lint_paths(paths: list[Path], loaded_config: LoadedConfig, cwd: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        findings.extend(lint_file(path, loaded_config, cwd))
    return findings


def lint_file(path: Path, loaded_config: LoadedConfig, cwd: Path) -> list[Finding]:
    path_display = display_path(path, cwd)
    effective_config = effective_config_for(path, loaded_config)

    try:
        document = load_native_form(path)
    except json.JSONDecodeError as exc:
        return [
            Finding(
                file_path=path_display,
                rule_id="invalid_json",
                severity="error",
                message=f"Invalid JSON: {exc.msg}",
            )
        ]
    except OSError as exc:
        return [
            Finding(
                file_path=path_display,
                rule_id="read_error",
                severity="error",
                message=f"Unable to read file: {exc}",
            )
        ]

    schema_errors = validate_native_form(document)
    if schema_errors:
        return [
            Finding(
                file_path=path_display,
                rule_id="schema_validation",
                severity="error",
                message=message,
            )
            for message in schema_errors
        ]

    try:
        context = form_from_native(
            document=document,
            source_path=path,
            display_path=path_display,
            element_ignores=effective_config.element_ignores,
        )
    except (KeyError, TypeError, ValueError) as exc:
        return [
            Finding(
                file_path=path_display,
                rule_id="schema_validation",
                severity="error",
                message=f"Native form is missing or has an invalid layout field: {exc}",
            )
        ]
    return run_rules(context, effective_config)


def run_rules(context, effective_config: EffectiveConfig) -> list[Finding]:
    findings: list[Finding] = []
    for rule_id, severity in effective_config.rules.items():
        if severity == "off":
            continue
        if rule_id == "shared_page_required":
            findings.extend(rule_shared_page_required(context, severity))
        elif rule_id == "inside_bounds":
            findings.extend(rule_inside_bounds(context, severity))
        elif rule_id == "no_overlap":
            findings.extend(rule_no_overlap(context, severity))
        elif rule_id == "consistent_spacing":
            findings.extend(
                rule_consistent_spacing(context, severity, effective_config.allowed_spacing_values)
            )
        elif rule_id == "alignment_consistency":
            findings.extend(rule_alignment_consistency(context, severity))
    return findings
