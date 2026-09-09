# Storage-inventory evidence owner

This owner has two jobs: measure declared storage roots and qualify filesystem
behavior for execution. Inventory records `retain`, `archive`, or
`review_then_delete` policy; it never carries out those actions.

## Inventory use and outputs

Prepare [storage roots](../../../../configs/storage_roots.example.tsv) and
[retention policy](../../../../configs/retention_policy.example.tsv) using the
example formats. Replace their values with your explicit paths and policy, then
preview without publication:

```bash
emrys debug storage-inventory \
  --roots /absolute/path/to/storage_roots.tsv \
  --retention-policy /absolute/path/to/retention_policy.tsv \
  --output-root /absolute/existing/output-directory
```

Measurement does not follow symlinks. Add `--execute` to publish
`storage_inventory.tsv`, `retention_policy.tsv`, and
`storage_retention_summary.tsv`, with the summary last.

## Qualification and recovery

Doctor repair can create the single-host direct receipt after checking hard
links, `flock`, atomic rename, fsync, permissions, and identity at the exact
Project/reference roots. Slurm instead needs the
[compute and head-node finalize procedure](../../../../docs/operations/RUNBOOK.md#2-qualify-the-exact-storage-roots).
The compute phase creates private probes in the allocation; finalize checks
them again, publishes the bound receipt, and removes only those probe directories.

Both routes make the final receipt durable before removing its staged name and
probes. A final-link or first directory-fsync failure preserves the staged
receipt and probes. Any staged marker still blocks admission and re-execution.
Once the final receipt is durable and the staged name is removed, probe-cleanup
failure leaves final authority intact, even if cleanup is partial. Keep any
remaining evidence; an error does not authorize deletion, replacement, or adoption.

The two-phase receipt binds canonical paths, inode and UID/GID observations,
mount source/type, capacity, locking, rename visibility, and durability after
the allocation ends. Device numbers are diagnostic and may differ by node.
Failure never authorizes staging around an unqualified shared filesystem.

## Known inventory-publication limits

Inventory replacement is separate from qualification. Its
[publisher](_storage_publication.py) validates and moves each predecessor to a
`.previous` path before entering the final-publication rollback handler. A
failure during those moves can leave earlier files backed up without restoration.
If publication and subsequent restoration fail, cleanup can release the lock
while backups and an incomplete final set remain, without a recovery marker.
A restoration error can replace the original publication exception; a later
cleanup failure may prevent remaining cleanup steps.

The [owner tests](../../../../tests/evidence/storage_inventory/test_storage_inventory.py)
characterize incomplete restoration. Preserve finals, staging, backups, and
locks together. Neither inventory nor qualification receipt presence alone
establishes site approval, production suitability, retention authorization,
scientific review, or biological validity.
