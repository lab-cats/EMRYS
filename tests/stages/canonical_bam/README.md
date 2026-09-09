# Canonical-BAM tests

These cases check Step 02 input rejection, existing-output refusal, staging,
exclusive BAM/BAI publication, and actual rollback/cleanup states. Ordinary
invocation and `--no-clobber` use the same policy. Python cases call
`python -I -m emrys validate canonical-bam`; `validator.py` remains private.

Publication faults use the real shared file helpers and controlled tool failures.
They preserve files owned by other attempts and document retained residue,
including the staging-anchor removal failure that releases the lock. They do
not promise rollback or lock retention after every failure. The
[historical replacement defect](../../../src/emrys/stages/canonical_bam/CONTRACT.md#historical-replacement-defect)
retains the retired restore-loss sequence and exact source/test revision;
current refusal cases instead check preservation of both prior outputs.
