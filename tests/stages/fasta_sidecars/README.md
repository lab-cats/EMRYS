# FASTA-sidecar tests

These cases check Step 00c two-file rollback, exclusive publication, preservation
of sidecars created by another process, and retained files after failed rollback.
They also cover unsafe run tokens, staging files from older tokens, lock/cleanup
failures, and structural FAI/dictionary validation.

Shell cases invoke the repository producer with fake tools; Python cases use
`python -I -m emrys validate fasta-sidecars`. Neither adds a public command.
The [stage contract](../../../src/emrys/stages/fasta_sidecars/CONTRACT.md)
defines tool selection and recovery.
