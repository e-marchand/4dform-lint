from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import ConfigError, load_config
from .engine import UsageError, discover_form_files, lint_paths
from .reporting import render_json, render_sarif, render_text, summarize
from .rules import VALID_RULE_IDS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lint native 4D .4DForm files")
    parser.add_argument("paths", nargs="+", help="One or more .4DForm files or folders")
    parser.add_argument("--config", help="Path to a .4dform-lint YAML config file")
    parser.add_argument(
        "--format",
        choices=("text", "json", "sarif"),
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="RULE_IDS",
        help="Comma-separated rule ids to disable for this run; can be passed multiple times",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def parse_excluded_rules(values: list[str]) -> tuple[str, ...]:
    excluded_rules = []
    for value in values:
        excluded_rules.extend(part.strip() for part in value.split(","))

    normalized = tuple(dict.fromkeys(rule_id for rule_id in excluded_rules if rule_id))
    unknown = sorted(rule_id for rule_id in normalized if rule_id not in VALID_RULE_IDS)
    if unknown:
        raise UsageError(
            "Unknown rule id(s) passed to --exclude: "
            f"{', '.join(unknown)}. Valid rule ids: {', '.join(sorted(VALID_RULE_IDS))}"
        )
    return normalized


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cwd = Path.cwd()

    try:
        excluded_rules = parse_excluded_rules(args.exclude)
        loaded_config = load_config(args.config, cwd)
        paths = discover_form_files(args.paths, cwd)
        findings = lint_paths(paths, loaded_config, cwd, excluded_rules=excluded_rules)
    except (ConfigError, UsageError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"Unexpected failure: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(render_json(findings, len(paths)))
    elif args.format == "sarif":
        print(render_sarif(findings, len(paths)))
    else:
        print(render_text(findings, len(paths)))

    summary = summarize(findings, len(paths))
    return 1 if summary["errors"] > 0 else 0
