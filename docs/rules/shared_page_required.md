# `shared_page_required`

Default severity: `off`

Checks that the form contains both:

- shared page `0`
- visible page `1`

Forms with no pages or only one page do not satisfy this rule.

This is off by default because not every project uses that convention, but it is useful when your forms are expected to follow classic shared-page structure.
