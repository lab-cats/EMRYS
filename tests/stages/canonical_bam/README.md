# Canonical-BAM stage tests

This directory protects Step 02 input admission, existing-output refusal,
shell staging, create-exclusive BAM/BAI publication, and observed rollback and
cleanup states, plus structural validator behavior. Both ordinary invocation
and the accepted `--no-clobber` spelling use the same publication policy. The
[stage owner](../../../src/emrys/stages/canonical_bam/README.md) owns supported
commands, recovery hazards, and exact evidence limits. The Python tests invoke
the grouped `python -I -m emrys validate canonical-bam` route; `validator.py`
is a private implementation module.

Publication faults exercise the real shared file helpers through controlled
tool failures. Their expectations preserve foreign files and characterize
retained residue, including the persistent-anchor-removal case that releases
the lock. They do not assert universal rollback or lock retention. The
[owner contract](../../../src/emrys/stages/canonical_bam/CONTRACT.md#historical-replacement-defect)
retains the exact retired restore-loss sequence and pinned historical
source/test revision; current refusal tests protect preservation of both prior
outputs instead.

Fixtures and fake tools do not prove real samtools, scheduler, cluster,
production, scientific-review, or biological behavior.
