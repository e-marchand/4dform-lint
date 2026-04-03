from __future__ import annotations

import json
import os
from pathlib import Path

from .config import EffectiveConfig, LoadedConfig, effective_config_for
from .models import Finding
from .native import form_from_native
from .rules import RULES_BY_ID, RuleOptions
from .schema import load_native_form, validate_native_form
from .xliff import load_translation_catalog


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


def lint_paths(
    paths: list[Path],
    loaded_config: LoadedConfig,
    cwd: Path,
    *,
    excluded_rules: tuple[str, ...] = (),
) -> list[Finding]:
    translations = load_translation_catalog(paths)
    findings: list[Finding] = []
    for path in paths:
        findings.extend(
            lint_file(
                path,
                loaded_config,
                cwd,
                translations,
                excluded_rules=excluded_rules,
            )
        )
    return findings


def lint_file(
    path: Path,
    loaded_config: LoadedConfig,
    cwd: Path,
    translations: dict[str, tuple[str, ...]] | None = None,
    *,
    excluded_rules: tuple[str, ...] = (),
) -> list[Finding]:
    path_display = display_path(path, cwd)
    effective_config = effective_config_for(path, loaded_config, excluded_rules=excluded_rules)

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
            translations=translations,
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
    options = RuleOptions(allowed_spacing_values=tuple(effective_config.allowed_spacing_values))
    for rule_id, severity in effective_config.rules.items():
        if severity == "off":
            continue
        rule = RULES_BY_ID.get(rule_id)
        if rule is None:
            continue
        findings.extend(rule.run(context, severity, options))
    return findings
