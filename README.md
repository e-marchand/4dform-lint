# 4dform-lint

Standalone linter for native 4D `.4DForm` files.

## Usage

Run directly from GitHub with `uvx`:

```bash
uvx --from git+https://github.com/e-marchand/4dform-lint 4dform-lint path/to/form.4DForm
uvx --from git+https://github.com/e-marchand/4dform-lint 4dform-lint path/to/forms --format json
```

## Config

Create `.4dform-lint.yaml` in the working directory or pass `--config path/to/file.yaml`.

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
```

## Rule Notes

- `consistent_spacing` checks nearby gaps in aligned rows and columns. Large section breaks and opposite-side controls are ignored so the rule focuses on local layout rhythm.
- `alignment_consistency` follows inferred placement:
  - `below(...)` and `above(...)` compare left edges.
  - `rightOf(...)` and `leftOf(...)` compare top edges.
- Alignment warnings include the pixel delta and direction, for example `left edge is 16 px to the right` or `top edge is 2 px higher`.
- If a layout is intentional, suppress a rule for a specific element with `ignore_rules`.
