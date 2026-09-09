# Shared-library tests

These tests cover validation reports and inputs, BAM and reference parsers,
executable selection, shell file operations, and application logging. The
[library index](../../src/emrys/libraries/README.md) points to their production
implementations. Each consuming producer still tests its complete transaction
and recovery behavior.

## Shell publication regression

Earlier RSeQC, BAM QC, and duplicate-marking producers recorded each published
file only after the link helper returned. Local production-script probes showed
that TERM after linking, or replacement before the helper's inode check, could
leave a final file while deleting its staging file and lock. All three now use
the [shared cleanup](../../src/emrys/libraries/README.md#shell-publication-cleanup).
The BAM QC regression removes the second final file immediately after linking;
existing ownership and tool-failure tests cover the remaining shared behavior.

## Validation recovery characterization

`test_validation_report.py` demonstrates the
[validation library's known limits](../../src/emrys/libraries/validation/README.md#known-limits)
with local snapshots and injected filesystem failures. Its cases record changed
bytes hidden by restored metadata, deletion of another process's newly created
output, and predecessor bytes surviving failed restoration without a lock or
recovery marker. These tests preserve observed defects; they do not approve
that recovery behavior or establish cluster results.
