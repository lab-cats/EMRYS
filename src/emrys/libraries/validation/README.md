# Validation library

`emrys.libraries.validation` provides errors, input snapshots, report rows and
schemas, TSV parsing, report publication, and dry-run/execution support.
Each validator chooses its inputs, check IDs, commands, and evidence meaning.

## Input stability

Retain both read mechanisms: they make different guarantees. `Snapshot` records
device, inode, size and modification time; equal snapshots do not prove equal
bytes. `read_bytes_with_identity` binds an open descriptor, checks mode and change
time, and rejects pathname replacement. The restored-size/mtime counterexample
remains covered by the [validation tests](../../../../tests/libraries/test_validation_report.py).
Any consolidation must first specify the required guarantee for every caller;
metadata equality cannot replace byte identity at admission or reuse boundaries.

## Known limits

During report publication, rollback can delete a final file
created by another process. If restoring a predecessor fails, its backup bytes
can survive while the lock is released and no recovery marker is written.
These are existing defects, documented by
[local characterization tests](../../../../tests/libraries/README.md#validation-recovery-characterization),
not promises of safe recovery.

A fix must preserve file bytes and names, input stability, symlink and overwrite
protections, signals, recovery evidence, and unrelated files across all consumers.
This publisher is not automatically suitable for other transactions.
