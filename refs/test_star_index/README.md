# Local STAR-index fixture path

This directory preserves the local STAR-index path named by
[`configs/local_test.yaml`](../../configs/local_test.yaml) and the Step `01`
dry-run contract. The tracked README is not a valid STAR index and supplies no
runtime, cluster, scientific, or biological evidence.

The owning wrapper creates this empty directory and placeholder FASTQ inputs
for its default dry run; it does not populate a STAR index. Execute mode rejects
the complete default fixture combination. Operators must supply and inspect a
real index and real inputs before execution. Keep this fixture path distinct
from production references, and do not commit a generated STAR index here.
