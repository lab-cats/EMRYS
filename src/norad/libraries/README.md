# Internal libraries

This directory owns neutral implementation shared by multiple functional
stages. Files here are source owners, not an installed package or a declared
public Python import API; there is intentionally no `__init__.py`.

`validation_report.py` owns `ValidationError`, `Snapshot`, `fail`, `clean`,
`regular_snapshot`, `stable_text`, `render`, `validate_report`, and `publish`,
plus internal `HEADER`. The thirteen validator entry points resolve that exact
file through repeated caller-local loaders cached only as the private identity
`_norad_validation_report`. Ten loaders now live with final functional owners
through `partition_BAM_by_mechanical_read_orientation`; three remain with flat
validators. The loaders do not establish a generic loader or packaging
convention.

`bam_validation.py` owns only the behavior-preserving `run_tool` and
`parse_header` primitives used by the final `construct_canonical_BAM`, Step
`04`, and Step `05` validators. Those three callers
exact-load the file under private identity `_norad_bam_validation`, verify its
path, readiness marker, and two-callable API, preserve foreign module-cache
state and `sys.path`, and remove only a loader-owned partial after execution
failure. The file has no public CLI, package identity, stage-specific check
logic, or validation-report dependency. Loader failure is a checkout-integrity
diagnostic, not authority to add `PYTHONPATH`, install a package, or restore a
legacy validator path.

This extraction preserves, rather than fixes, the characterized same-size and
restored-mtime snapshot blindness, unordered-report acceptance, late-foreign
final deletion, incomplete rollback without a retained recovery marker,
previous/staged/lock cleanup residue, open descriptor and lock retention, and
post-publication lock cleanup behavior. See the direct library fault tests and
the dated refactor audit for the exact evidence boundary:

- [`tests/libraries/test_validation_report.py`](../../../tests/libraries/test_validation_report.py)
- [`tests/libraries/test_bam_validation.py`](../../../tests/libraries/test_bam_validation.py)
- [`2026-08-02 refactor log`](../../../docs/history/audits/2026-08-02-refactor-log.md)
