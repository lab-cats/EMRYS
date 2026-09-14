# Report template

[`run_report.html.j2`](run_report.html.j2) is the packaged template for both
scientific and evidence-and-operations HTML. Python view builders supply each
view's title, banner context, introduction, sections, and end note. The template
lays out accessible navigation, tables, figures, ranked candidate cards, detailed
records, and other blocks using one bounded set of macros rather than fragments.
Scientific content stays expanded for reading and printing, with no `details`
elements; evidence categories keep their limited disclosure controls.

Validated scientific SVGs, including multi-panel candidate figures, arrive as
base64 data URIs. The artifact-availability SVG appears only when the evidence
view requests it. Manifest-paired candidate evidence is grouped in four-pair
batches, each with its candidate heading, so printing retains record identity
and does not split a replicate card. The [stylesheet](../styles/README.md)
defines the remaining print layout.

Jinja uses HTML autoescaping and `StrictUndefined`. Only validated packaged CSS
is trusted raw content: summaries, identifiers, paths, computational text, issues,
limitations, and table data never use `safe`. SVG URI attributes remain escaped.
There are no scripts, includes, remote assets, sidecars, or executable analysis.
[Report tests](../../../../tests/reporting/test_report.py) and isolated-wheel
render smoke check these guarantees.
