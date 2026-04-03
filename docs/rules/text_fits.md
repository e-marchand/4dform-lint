# `text_fits`

Default severity: `warning`

Estimates whether one-line text is likely to be cropped for native `button`, `checkbox`, `radio`, and `text` objects.

The rule uses each object's explicit font settings when present, falls back to the platform default font profile otherwise, and subtracts intrinsic control padding before comparing available width.

If text is written as `xliff:KEY`, the rule scans `.xlf` and `.xliff` files under the lint working directory and checks the longest matching translation variant it can resolve.

Suppress an intentional exception with `ignore_rules: [text_fits]`.
