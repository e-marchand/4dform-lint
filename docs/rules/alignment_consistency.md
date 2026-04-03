# `alignment_consistency`

Default severity: `warning`

Uses inferred placement relationships to check whether related controls stay aligned:

- `below(...)` and `above(...)` compare left edges.
- `rightOf(...)` and `leftOf(...)` compare top edges.

Warnings include the pixel delta and direction so the drift is easy to correct.

Suppress an intentional exception with `ignore_rules: [alignment_consistency]`.
