# GTF-to-BED12 tests

These cases check Step 00b conversion and validation, side-effect-free dry-run,
execution from other working directories, exclusive publication, rollback,
existing-output refusal, and blocking on interruption residue. Mocked scheduler
cases also document the later bedtools partial-publication behavior. The
[stage contract](../../../src/emrys/stages/gtf_to_bed12/CONTRACT.md)
defines commands and recovery; inputs are synthetic GTF/BED files.
