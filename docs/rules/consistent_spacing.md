# `consistent_spacing`

Default severity: `warning`

Checks nearby gaps in aligned rows and columns against the configured spacing scale.

Only local neighbors are compared. Large section breaks and distant controls are ignored so the rule focuses on layout rhythm rather than every possible gap on the page.

Configure the scale with:

```yaml
defaults:
  spacing:
    allowed_values: [4, 8, 10, 12, 16, 24]
```

Suppress an intentional exception with `ignore_rules: [consistent_spacing]`.
