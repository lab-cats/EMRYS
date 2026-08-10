# FASTA-sidecar stage tests

This directory protects the Step 00c shell producer, partial-publication
states, and structural FAI/dictionary validation. The
[stage owner](../../../src/norad/stages/fasta_sidecars/README.md)
owns tool selection, commands, recovery, and exact evidence limits.

The shell fixture invokes the repository producer; the Python fixture invokes
the grouped `python -I -m norad validate fasta-sidecars` route. Neither test
creates another public implementation entry point.

Fake-tool and fixture results do not prove real samtools, GATK, Java,
scheduler, cluster, or production execution.
