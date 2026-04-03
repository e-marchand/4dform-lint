from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


VALID_RULE_IDS = {
    "no_overlap",
    "inside_bounds",
    "consistent_spacing",
    "alignment_consistency",
    "shared_page_required",
    "text_fits",
}
VALID_SEVERITIES = {"off", "warning", "error"}
DEFAULT_RULES = {
    "no_overlap": "error",
    "inside_bounds": "error",
    "consistent_spacing": "warning",
    "alignment_consistency": "warning",
    "shared_page_required": "off",
    "text_fits": "warning",
}
DEFAULT_ALLOWED_SPACING = [4, 8, 10, 12, 16, 24]


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class FileOverride:
    pattern: str
    rules: dict[str, str]
    allowed_spacing_values: list[int] | None
    element_ignores: dict[tuple[int, str], set[str]]


@dataclass(frozen=True)
class LoadedConfig:
    config_path: Path | None
    config_dir: Path
    rules: dict[str, str]
    allowed_spacing_values: list[int]
    file_overrides: list[FileOverride]


@dataclass(frozen=True)
class EffectiveConfig:
    rules: dict[str, str]
    allowed_spacing_values: list[int]
    element_ignores: dict[tuple[int, str], set[str]]


def discover_config_path(cwd: Path) -> Path | None:
    for name in (".4dform-lint.yaml", ".4dform-lint.yml"):
        candidate = cwd / name
        if candidate.exists():
            return candidate
    return None


def load_config(explicit_path: str | None, cwd: Path) -> LoadedConfig:
    config_path = Path(explicit_path).resolve() if explicit_path else discover_config_path(cwd)
    if config_path is None:
        return LoadedConfig(
            config_path=None,
            config_dir=cwd,
            rules=dict(DEFAULT_RULES),
            allowed_spacing_values=list(DEFAULT_ALLOWED_SPACING),
            file_overrides=[],
        )

    try:
        with config_path.open("r", encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
    except OSError as exc:
        raise ConfigError(f"Unable to read config file '{config_path}': {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in config file '{config_path}': {exc}") from exc

    if document is None:
        document = {}
    if not isinstance(document, dict):
        raise ConfigError(f"Config file '{config_path}' must contain a YAML object")
    if document.get("version") != 1:
        raise ConfigError(f"Config file '{config_path}' must set version: 1")

    rules = dict(DEFAULT_RULES)
    rules.update(parse_rules(document.get("rules"), location="config.rules"))

    allowed_spacing_values = parse_allowed_spacing(
        document.get("defaults"),
        location="config.defaults",
        default=list(DEFAULT_ALLOWED_SPACING),
    )

    file_overrides = parse_file_overrides(document.get("overrides"), location="config.overrides")
    return LoadedConfig(
        config_path=config_path,
        config_dir=config_path.parent,
        rules=rules,
        allowed_spacing_values=allowed_spacing_values,
        file_overrides=file_overrides,
    )


def parse_rules(value: Any, *, location: str) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"{location} must be a mapping of rule ids to severities")

    parsed: dict[str, str] = {}
    for rule_id, severity in value.items():
        if rule_id not in VALID_RULE_IDS:
            raise ConfigError(f"{location} contains unknown rule id '{rule_id}'")
        if severity not in VALID_SEVERITIES:
            raise ConfigError(
                f"{location}.{rule_id} must be one of: {', '.join(sorted(VALID_SEVERITIES))}"
            )
        parsed[rule_id] = severity
    return parsed


def parse_allowed_spacing(value: Any, *, location: str, default: list[int]) -> list[int]:
    if value is None:
        return list(default)
    if not isinstance(value, dict):
        raise ConfigError(f"{location} must be a mapping")
    spacing = value.get("spacing")
    if spacing is None:
        return list(default)
    if not isinstance(spacing, dict):
        raise ConfigError(f"{location}.spacing must be a mapping")
    allowed_values = spacing.get("allowed_values")
    if not isinstance(allowed_values, list) or not allowed_values:
        raise ConfigError(f"{location}.spacing.allowed_values must be a non-empty list of integers")
    if not all(isinstance(item, int) for item in allowed_values):
        raise ConfigError(f"{location}.spacing.allowed_values must contain only integers")
    return list(allowed_values)


def parse_file_overrides(value: Any, *, location: str) -> list[FileOverride]:
    if value is None:
        return []
    if not isinstance(value, dict):
        raise ConfigError(f"{location} must be a mapping")
    files = value.get("files")
    if files is None:
        return []
    if not isinstance(files, dict):
        raise ConfigError(f"{location}.files must be a mapping of glob pattern to override")

    parsed: list[FileOverride] = []
    for pattern, override in files.items():
        if not isinstance(pattern, str) or not pattern:
            raise ConfigError(f"{location}.files contains an invalid pattern")
        if not isinstance(override, dict):
            raise ConfigError(f"{location}.files['{pattern}'] must be a mapping")
        parsed.append(
            FileOverride(
                pattern=pattern,
                rules=parse_rules(override.get("rules"), location=f"{location}.files['{pattern}'].rules"),
                allowed_spacing_values=parse_allowed_spacing(
                    override.get("defaults"),
                    location=f"{location}.files['{pattern}'].defaults",
                    default=[],
                )
                if override.get("defaults") is not None
                else None,
                element_ignores=parse_page_overrides(
                    override.get("pages"),
                    location=f"{location}.files['{pattern}'].pages",
                ),
            )
        )
    return parsed


def parse_page_overrides(value: Any, *, location: str) -> dict[tuple[int, str], set[str]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"{location} must be a mapping of page index to page override")

    parsed: dict[tuple[int, str], set[str]] = {}
    for raw_page_index, page_override in value.items():
        page_index = parse_page_index(raw_page_index, location=location)
        if not isinstance(page_override, dict):
            raise ConfigError(f"{location}[{page_index}] must be a mapping")
        elements = page_override.get("elements", {})
        if not isinstance(elements, dict):
            raise ConfigError(f"{location}[{page_index}].elements must be a mapping")
        for element_id, element_override in elements.items():
            if not isinstance(element_id, str) or not element_id:
                raise ConfigError(f"{location}[{page_index}].elements contains an invalid element id")
            if not isinstance(element_override, dict):
                raise ConfigError(
                    f"{location}[{page_index}].elements['{element_id}'] must be a mapping"
                )
            ignore_rules = element_override.get("ignore_rules", [])
            if not isinstance(ignore_rules, list) or not all(
                isinstance(rule_id, str) for rule_id in ignore_rules
            ):
                raise ConfigError(
                    f"{location}[{page_index}].elements['{element_id}'].ignore_rules must be a list of strings"
                )
            unknown = [rule_id for rule_id in ignore_rules if rule_id not in VALID_RULE_IDS]
            if unknown:
                raise ConfigError(
                    f"{location}[{page_index}].elements['{element_id}'] contains unknown rule ids: "
                    f"{', '.join(sorted(unknown))}"
                )
            parsed[(page_index, element_id)] = set(ignore_rules)
    return parsed


def parse_page_index(value: Any, *, location: str) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise ConfigError(f"{location} contains an invalid page index '{value}'")


def effective_config_for(path: Path, loaded: LoadedConfig) -> EffectiveConfig:
    rules = dict(loaded.rules)
    allowed_spacing_values = list(loaded.allowed_spacing_values)
    element_ignores: dict[tuple[int, str], set[str]] = {}

    rel_path = os.path.relpath(path, loaded.config_dir).replace(os.sep, "/")
    rel_posix = PurePosixPath(rel_path)

    for override in loaded.file_overrides:
        if rel_posix.match(override.pattern):
            rules.update(override.rules)
            if override.allowed_spacing_values is not None:
                allowed_spacing_values = list(override.allowed_spacing_values)
            for key, value in override.element_ignores.items():
                element_ignores[key] = set(value)

    return EffectiveConfig(
        rules=rules,
        allowed_spacing_values=allowed_spacing_values,
        element_ignores=element_ignores,
    )
