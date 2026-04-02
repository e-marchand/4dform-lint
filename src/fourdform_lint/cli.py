from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import ConfigError, load_config
from .engine import UsageError, discover_form_files, lint_paths
from .reporting import render_json, render_sarif, render_text, summarize


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
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cwd = Path.cwd()

    try:
        loaded_config = load_config(args.config, cwd)
        paths = discover_form_files(args.paths, cwd)
        findings = lint_paths(paths, loaded_config, cwd)
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
