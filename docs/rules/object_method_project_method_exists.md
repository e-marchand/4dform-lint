# `object_method_project_method_exists`

Default severity: `warning`

Warns when an object defines a bare `method` name that does not resolve to a local project method file.

- Bare names such as `method: "Test"` are checked against `Project/Sources/Methods/Test.4dm`.
- Forms inside components use their own `Project/Sources/Methods` folder when present.
- Forms outside a `Project/Sources/Forms` tree are ignored because no reliable local project lookup is available.
- Missing matches are only warnings because the method may still come from another project or component that cannot be resolved from the current form alone.

Suppress an intentional exception with `ignore_rules: [object_method_project_method_exists]`.
