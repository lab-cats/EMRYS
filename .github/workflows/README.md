# GitHub Actions workflows

[`ci.yml`](ci.yml) runs ordinary checks on pull requests. Scheduled and manually
selected lanes add longer synthetic and scheduler checks. The
[test baseline](../../docs/design/TEST_BASELINE.md#validation-lanes) defines each
lane; a green workflow supports only the claims covered by those checks.

The managed golden path also exercises Task descendant cleanup with the
samtools already selected by its synthetic Project. It requires that executable
before running the Linux process fixtures and canonical BAM checks. The job
retains their JUnit results and tiny native outputs beside its existing evidence.
This covers the hosted worker boundary; it does not establish Slurm cancellation,
lost-worker reconciliation or safe postentry retry.
