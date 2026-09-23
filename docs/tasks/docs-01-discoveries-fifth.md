# DOCS-01 discovery notes, fifth file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F130–F131. Both use local audit head `3ebfb2bf`, read on 2026-09-23.
Source and direct tests were read, not executed. These are documentation
observations, not runtime results, accepted changes, or permission to alter
retained evidence.

## Discovery notes

### F130 — Repeated test-scope paragraph across eight owner guides

The [BAM-QC](../../tests/evidence/canonical_bam_qc/README.md) and
[RSeQC](../../tests/evidence/rseqc_orientation/README.md) test guides and six
stage test guides—[STAR index](../../tests/stages/star_index/README.md),
[STAR alignment](../../tests/stages/star_alignment/README.md),
[canonical BAM](../../tests/stages/canonical_bam/README.md),
[duplicate marking](../../tests/stages/duplicate_marking/README.md),
[FASTA sidecars](../../tests/stages/fasta_sidecars/README.md), and
[split-N-cigar](../../tests/stages/split_n_cigar/README.md)—repeat the same
five physical lines at 5–9. Those 40 lines say worker cases use runner staging,
the [common runner suite](../../tests/orchestration/run_coordinator/test_task.py)
owns publication/recovery checks, validator cases keep the grouped CLI, and
shared evidence limits apply. The [stage](../../tests/stages/README.md) and
[evidence](../../tests/evidence/README.md) indexes already route to common
evidence limits; each owner's first paragraph gives its distinct coverage and
limit. The repeated paragraph is a concrete compression review surface, not
40 demonstrated deletable lines: local test scope and reader routes still
need to remain clear. Test files were inspected, not run.

### F131 — Receipt validation scope in the glossary

The [glossary](../reference/GLOSSARY.md) line 69 defines a receipt as published
after all other transaction members “validate” and says its presence marks
transaction completion. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1117–1126 distinguishes staged checks from independent validation:
Steps 08/09 validate before publication, while other scientific owners publish
native finals, including any receipt last, before the independent validator
and semantic all-pass. The [Step 07 owner contract](../../src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md)
lines 57–64 makes the second order explicit: its worker checks staged VCFs,
the runner publishes VCFs and receipt, and the independent validator checks
the visible set. A [direct task test](../../tests/orchestration/run_coordinator/test_task.py)
lines 759–776 shows a failed validation row prevents the verified-task marker.
The glossary's unqualified “validate” and “completion” blur native transaction
completion with verified task completion. Staged checks and receipt-last order
remain real; a native receipt alone is not verified-task proof. No runtime or
reporting defect follows from this glossary wording.
