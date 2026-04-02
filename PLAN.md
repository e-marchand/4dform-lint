# Standalone `4dform-lint` Package

## Summary
- Build a new standalone Python package in its own `lint` project folder, publishable to GitHub/PyPI and runnable with `uvx 4dform-lint ...`.
- Do not depend on this skill repo at runtime. Copy the needed 4D form schema and the current rule logic ideas into the package’s own code/assets.
- Scope v1 to native `.4DForm` files only. The CLI accepts one or more files or folders, recursively discovers `*.4DForm`, validates schema first, then runs layout/graphic lint rules.
- Keep screenshots out of scope for v1.

## Public Interfaces
- CLI entry point: `4dform-lint <path> [<path> ...]`
- CLI options: `--config <path>` and `--format text|json|sarif`, with `text` as default.
- Config discovery: if `--config` is not passed, load `.4dform-lint.yaml` or `.4dform-lint.yml` from the current working directory; if neither exists, use bundled defaults.
- Exit codes: `0` for no `error` findings, `1` for one or more `error` findings, `2` for CLI/config/internal failures.
- Config shape, versioned and hierarchical, with file-level overrides and page+element exceptions:
```yaml
version: 1

rules:
  no_overlap: error
  inside_bounds: error
  consistent_spacing: warning
  alignment_consistency: warning
  shared_page_required: off

defaults:
  spacing:
    allowed_values: [4, 8, 10, 12, 16, 24]

overrides:
  files:
    "Project/Sources/Forms/**/*.4DForm":
      rules:
        alignment_consistency: off
      defaults:
        spacing:
          allowed_values: [4, 8, 12, 16]
      pages:
        1:
          elements:
            fieldWhenHidden:
              ignore_rules: [no_overlap]
```
- `overrides.files` keys are glob patterns relative to the config file directory.
- Page indexes are 0-based.
- Element keys are native object ids from `pages[].objects`.
- Each finding, in text/JSON/SARIF, includes file path, rule id, severity, message, page index when known, and element id or element pair when known.

## Implementation Changes
- Package with `pyproject.toml`, `hatchling`, Python 3.11+, and a console script for `uvx`.
- Vendor the 4D JSON schema into package assets.
- Port, do not import, the minimal native-form normalization logic needed to build an internal resolved model from `.4DForm`.
- Internal model should contain: form width/height, pages, elements, stable element ids, native type/props, and resolved frame coordinates.
- Keep built-in rule ids exactly: `no_overlap`, `inside_bounds`, `consistent_spacing`, `alignment_consistency`, `shared_page_required`.
- Schema validation always runs first and cannot be disabled in v1. Graphical rules only run for files that parsed and passed schema validation.
- Merge config in this order: bundled defaults, user global `rules`/`defaults`, matching file overrides in YAML order with later matches winning, then page+element `ignore_rules`.
- Rule behavior:
  - `no_overlap`: fail when two framed elements intersect; skip a pair if either matched element ignores the rule.
  - `inside_bounds`: fail when an element frame falls outside form width/height.
  - `consistent_spacing`: check positive vertical gaps for elements sharing a left edge and positive horizontal gaps for elements sharing a top edge against `defaults.spacing.allowed_values`.
  - `alignment_consistency`: use the ported inference heuristic to detect vertical grouping and require consistent left alignment unless ignored.
  - `shared_page_required`: off by default; when enabled, require at least two pages so page 0 acts as shared chrome and page 1+ contains visible content.
- JSON output should expose a stable summary object plus per-file findings.
- SARIF output should emit one run with the `.4DForm` file as the artifact location and store page/element metadata in SARIF properties.

## Test Plan
- Unit tests for config parsing, version validation, glob matching, merge precedence, page+element override lookup, and severity handling.
- Fixture tests for each built-in rule using vendored `.4DForm` examples, including one overlap case suppressed by a config override.
- CLI tests for single-file linting, recursive folder discovery, deterministic path ordering, text output, JSON output, SARIF output, and exit codes `0/1/2`.
- Negative tests for unreadable JSON, schema violations, invalid config files, unknown severities, and unknown rule ids in config.
- Packaging test that installs/runs through the console entry point so the project works as a standalone `uvx` target without this repo present.

## Assumptions
- v1 only lints native `.4DForm`; layout JSON support is intentionally excluded.
- Default severities are: `no_overlap=error`, `inside_bounds=error`, `consistent_spacing=warning`, `alignment_consistency=warning`, `shared_page_required=off`.
- Runtime dependencies are limited to `jsonschema` and `PyYAML`.
- Native object keys are the stable element identifiers used for page+element overrides.
- Screenshots, autofix, and editor-specific integration are not part of v1.
