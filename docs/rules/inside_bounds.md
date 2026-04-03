# `inside_bounds`

Default severity: `error`

Checks that every element frame stays within the root form `width` and `height`.

If the form itself is missing those root dimensions, the rule reports that as a finding because bounds cannot be evaluated reliably.

Suppress an intentional exception with `ignore_rules: [inside_bounds]`.
