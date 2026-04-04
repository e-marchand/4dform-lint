# `object_method_file_exists`

Default severity: `error`

Errors when an object defines a file-style `method` reference that does not resolve to an existing `.4dm` file inside the form folder.

- Values containing `/` or `\`, or ending with `.4dm`, are treated as form-local file references.
- The resolved target must stay under the folder that contains the current `form.4DForm`.
- Missing files and paths that escape the form folder are both reported.

Example:

- `method: "ObjectMethods/Bouton.4dm"` must resolve relative to the form folder, such as `.../Project/Sources/Forms/Formulaire1/ObjectMethods/Bouton.4dm`.

Suppress an intentional exception with `ignore_rules: [object_method_file_exists]`.
