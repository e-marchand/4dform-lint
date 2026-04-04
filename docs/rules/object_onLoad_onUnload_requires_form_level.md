# `object_onLoad_onUnload_requires_form_level`

Default severity: `warning`

Warns when an object enables `onLoad` or `onUnload` but the form does not enable the same event at form level.

- If an object enables `onLoad`, the form must also enable `onLoad`.
- If an object enables `onUnload`, the form must also enable `onUnload`.
- When both object events are enabled and both are missing on the form, the rule reports them together.

This catches a 4D runtime wiring issue where object lifecycle callbacks are configured locally but can never fire because the form-level event gate was not turned on.

Suppress an intentional exception with `ignore_rules: [object_onLoad_onUnload_requires_form_level]`.
