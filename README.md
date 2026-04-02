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
