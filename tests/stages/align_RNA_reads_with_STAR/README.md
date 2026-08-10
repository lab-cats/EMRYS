# STAR-alignment stage tests

This directory protects the Step 01 shell producer's argument, dry-run,
failure, and direct-output behavior plus structural validator reporting. The
[stage owner](../../../src/norad/stages/align_RNA_reads_with_STAR/README.md)
owns supported commands, partial-output hazards, and exact evidence limits.

Fixtures and mocked STAR behavior do not establish alignment correctness, real
STAR execution, scheduler behavior, cluster execution, or production evidence.
