# Validation library

`emrys.libraries.validation` provides errors, input snapshots, report rows and
schemas, TSV parsing, report publication, and dry-run/execution support.
Each validator chooses its inputs, check IDs, commands, and evidence meaning.

## Known limits

Input snapshots can miss changed bytes when file size and modification time
are restored. During report publication, rollback can delete a final file
created by another process. If restoring a predecessor fails, its backup bytes
can survive while the lock is released and no recovery marker is written.
These are existing defects, documented by
[local characterization tests](../../../../tests/libraries/README.md#validation-recovery-characterization),
not promises of safe recovery.

A fix must preserve file bytes and names, input stability, symlink and overwrite
protections, signals, recovery evidence, and unrelated files across all consumers.
This publisher is not automatically suitable for other transactions.
