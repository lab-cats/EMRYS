# Internal libraries

This directory owns neutral implementation shared by multiple functional
stages. Files here are source owners, not an installed package or a declared
public Python import API; there is intentionally no `__init__.py`.

`validation_report.py` owns `ValidationError`, `Snapshot`, `fail`, `clean`,
`regular_snapshot`, `stable_text`, `render`, `validate_report`, and `publish`,
plus internal `HEADER`. The thirteen legacy validator entry points resolve
that exact file through repeated caller-local loaders cached only as the
private identity `_norad_validation_report`. Those loaders leave with each
validator during its later functional-owner migration; they do not establish a
generic loader or packaging convention.

This extraction preserves, rather than fixes, the characterized same-size and
restored-mtime snapshot blindness, unordered-report acceptance, late-foreign
final deletion, incomplete rollback without a retained recovery marker,
previous/staged/lock cleanup residue, open descriptor and lock retention, and
post-publication lock cleanup behavior. See the direct library fault tests and
the dated refactor audit for the exact evidence boundary.
