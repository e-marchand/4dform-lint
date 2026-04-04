# `page0_cross_page_overlap`

Default severity: `warning`

Warns when an element on shared page `0` overlaps an element on a visible page `1+`.

In native 4D forms, page `0` is shared across the visible pages, so a collision here can create unexpected stacked visuals or interactive controls hidden behind page-specific content.

Suppress an intentional exception with `ignore_rules: [page0_cross_page_overlap]` on either the shared-page element or the visible-page element.
