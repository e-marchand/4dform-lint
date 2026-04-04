# 4dform-lint

Standalone linter for native 4D `.4DForm` files.

## Project Map

- CLI entrypoint: `src/fourdform_lint/cli.py`
- File discovery and rule execution: `src/fourdform_lint/engine.py`
- Native `.4DForm` loading and normalization into lint contexts: `src/fourdform_lint/schema.py` and `src/fourdform_lint/native.py`
- Shared models: `src/fourdform_lint/models.py`
- Rules: `src/fourdform_lint/rules/`
- Rule docs: `docs/rules/`
- End-to-end tests: `tests/test_cli.py`

## Rule Model

Each rule is a module in `src/fourdform_lint/rules/` that exports:

- `rule_<rule_id>(context, severity, options) -> list[Finding]`
- `RULE = RuleDefinition(...)`

Rules run on a normalized `FormContext` with pages and elements already parsed from the native JSON.

Use:

- `context.pages` for page traversal
- `element.frame` for geometry
- `element.native_object` for raw 4D properties
- `element.ignores` for per-element suppressions
- `options.allowed_spacing_values` only when the rule needs configured spacing values

Return `Finding` objects with `page_index` and `element_ids` when possible.

## How To Add A New Rule

1. Add a new module under `src/fourdform_lint/rules/<rule_id>.py`.
2. Follow the pattern used by existing rules such as `no_overlap.py` or `shared_page_required.py`.
3. If the rule supports element-level suppression, check `element.ignores` via helpers in `src/fourdform_lint/rules/common.py`.
4. Register the rule in `src/fourdform_lint/rules/__init__.py`:
   - import the module exports
   - add the `RULE` to `RULE_DEFINITIONS`
   - expose the runner in `__all__` if needed
5. Document the rule in `docs/rules/<rule_id>.md`.
6. Add the rule to the rule list in `README.md` if it is user-facing.
7. Add CLI-level tests in `tests/test_cli.py`, preferably with a small fixture in `tests/fixtures/` unless inline JSON is simpler.

## Implementation Notes

- Keep rules deterministic and side-effect free.
- Prefer normalized geometry from `Frame` over re-reading raw coordinates.
- Skip config plumbing unless the rule actually needs options.
- Default severities come from the rule's `RuleDefinition` and automatically flow into config validation.
- Unknown rule ids are rejected by config and CLI exclude parsing, so registration in `rules/__init__.py` is required.

## Validation

Prefer `uv run` for both tests and local commands so the agent uses the project's declared environment and script entrypoints.

Run the full test suite with:

```bash
uv run python -m unittest discover -s tests
```

Run the CLI against a form or folder with:

```bash
uv run 4dform-lint path/to/form.4DForm
uv run 4dform-lint path/to/forms --format json
```

If you need to execute the module directly while iterating on internals, use:

```bash
uv run python -m fourdform_lint path/to/form.4DForm
```
