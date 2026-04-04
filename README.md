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
  events_required_for_method: warning
  object_onLoad_onUnload_requires_form_level: warning
  page0_cross_page_overlap: warning
  shared_page_required: off
  text_fits: warning

defaults:
  spacing:
    allowed_values: [4, 8, 10, 12, 16, 24]
```

## Rule Reference

- [`no_overlap`](docs/rules/no_overlap.md): flags intersecting element frames on the same page.
- [`inside_bounds`](docs/rules/inside_bounds.md): ensures elements stay within the root form bounds.
- [`consistent_spacing`](docs/rules/consistent_spacing.md): checks nearby aligned gaps against the configured spacing scale.
- [`alignment_consistency`](docs/rules/alignment_consistency.md): validates inferred placement alignment between related controls.
- [`events_required_for_method`](docs/rules/events_required_for_method.md): warns when an object method is configured without the events needed to trigger it.
- [`object_onLoad_onUnload_requires_form_level`](docs/rules/object_onLoad_onUnload_requires_form_level.md): warns when an object enables `onLoad` or `onUnload` without the matching form-level event.
- [`page0_cross_page_overlap`](docs/rules/page0_cross_page_overlap.md): warns when shared page `0` overlaps page-specific content on visible pages.
- [`shared_page_required`](docs/rules/shared_page_required.md): optionally enforces the shared page `0` plus visible page `1` convention.
- [`text_fits`](docs/rules/text_fits.md): estimates whether native one-line control text is likely to be cropped.

If a layout is intentional, suppress a rule for a specific element with `ignore_rules`.
