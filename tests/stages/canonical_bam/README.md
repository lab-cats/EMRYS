# Canonical-BAM stage tests

This directory protects Step 02 shell staging, BAM/BAI publication and
rollback states, plus structural validator behavior. The
[stage owner](../../../src/emrys/stages/canonical_bam/README.md) owns supported
commands, recovery hazards, and exact evidence limits. The Python tests invoke
the grouped `python -I -m emrys validate canonical-bam` route; `validator.py`
is a private implementation module.

Fixtures and fake tools do not prove real samtools, scheduler, cluster,
production, scientific-review, or biological behavior.
