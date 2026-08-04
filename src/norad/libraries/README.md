# Internal libraries

This directory owns neutral implementation shared by multiple functional
stages. Files here are source owners, not an installed package or a declared
public Python import API; there is intentionally no `__init__.py`.

`validation_report.py` owns `ValidationError`, `Snapshot`, `fail`, `clean`,
`regular_snapshot`, `stable_text`, `render`, `validate_report`, and `publish`,
plus internal `HEADER`. The thirteen validator entry points resolve that exact
file through repeated caller-local loaders cached only as the private identity
`_norad_validation_report`. Twelve loaders now live with final functional
owners through `preprocess_and_annotate_cohort_candidates`; one remains with a
flat validator. The loaders do not establish a generic loader or packaging
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

`reference_contigs.py` owns `ReferenceContigError` and the exact ordered
`parse_fasta`, `parse_fai`, and `parse_dict` APIs, plus private failure and
duplicate/empty helpers. Reference provenance and the final Step `00c` and
Step `05` validators exact-load that file under the single private identity
`_norad_reference_contigs`, verify its path, readiness marker, error class, and
three-callable API, and preserve foreign cache state and `sys.path`. Agreement,
per-role versus short-circuit aggregation, evidence rows, CLI behavior,
hashing, snapshots, publication, locking, rollback, and recovery remain with
the three consumers. The library does not establish a public package or repair
characterized parser behavior.

The validation-report extraction preserves, rather than fixes, the
characterized same-size and
restored-mtime snapshot blindness, unordered-report acceptance, late-foreign
final deletion, incomplete rollback without a retained recovery marker,
previous/staged/lock cleanup residue, open descriptor and lock retention, and
post-publication lock cleanup behavior. See the direct library fault tests and
the dated refactor audit for the exact evidence boundary:

- [`tests/libraries/test_validation_report.py`](../../../tests/libraries/test_validation_report.py)
- [`tests/libraries/test_bam_validation.py`](../../../tests/libraries/test_bam_validation.py)
- [`tests/libraries/test_reference_contigs.py`](../../../tests/libraries/test_reference_contigs.py)
- [`2026-08-02 refactor log`](../../../docs/history/audits/2026-08-02-refactor-log.md)
