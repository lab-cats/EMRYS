# FASTA-sidecar stage tests

This directory protects the Step 00c shell producer, controlled two-sidecar
rollback, create-exclusive late-collision handling, foreign-sidecar
preservation, failed-rollback residue preservation, and structural
FAI/dictionary validation. It also covers unsafe run-token rejection,
older-token staging blockers, and fail-closed staging/lock cleanup faults. The
[stage owner](../../../src/norad/stages/fasta_sidecars/README.md)
owns tool selection, commands, recovery, and exact evidence limits.

The shell fixture invokes the repository producer; the Python fixture invokes
the grouped `python -I -m norad validate fasta-sidecars` route. Neither test
creates another public implementation entry point.

Fake-tool and fixture results do not prove real samtools, GATK, Java,
scheduler, cluster, or production execution.
