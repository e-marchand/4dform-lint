# `events_required_for_method`

Default severity: `warning`

Warns when an object defines a `method` but does not enable the events needed to trigger it.

- Any object with a non-empty `method` and no enabled `events` is reported.
- Native clickable controls in this schema (`button`, `checkbox`, `radio`) are also reported when they define a `method` but do not enable `onClick`.

This catches a common 4D wiring mistake where a method is configured on the object, but the matching event was never turned on.

Suppress an intentional exception with `ignore_rules: [events_required_for_method]`.
