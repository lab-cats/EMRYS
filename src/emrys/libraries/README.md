# Internal libraries

Libraries provide shared parsing, validation, filesystem, runtime, and logging
mechanics. Their callers keep scientific policy, check lists, commands, and
interpretation of evidence. [SOURCE_TOPOLOGY](../contracts/SOURCE_TOPOLOGY.md)
defines each library's permitted consumers and import direction; a helper's
presence does not make it a general utility. New shared code must replace
proven-equivalent implementations across its callers.

## Shell publication cleanup

`file_checks.sh::cleanup_no_clobber_outputs` handles rollback, staging cleanup,
and lock release for RSeQC, BAM QC, and duplicate marking. Each producer supplies
fixed labels and staging/final path pairs. It marks publication as started before
the first link and clears that state only after all successful-publication
staging anchors are removed. The producer still runs and validates its native tool.

After publication fails, cleanup checks every pair, including one whose link
helper did not return successfully. It removes a final file only when that file
and its staging anchor share an inode. A missing or replaced final preserves
all anchors and the owned lock; other finals with proven ownership may still
be removed. Once rollback succeeds, cleanup attempts every staging unlink.
An unlink failure retains the remaining files and lock and reports the label
and path without masking the original exit status.

Canonical BAM and split-N-cigar have additional scratch/commit cleanup;
scientific context has backups, directory syncing, and a different lock record.
They need their own cleanup. The lower-level link and inode helpers are
unchanged. [Regression evidence](../../../tests/libraries/README.md#shell-publication-regression)
explains the failure sequence this shared cleanup replaces.
