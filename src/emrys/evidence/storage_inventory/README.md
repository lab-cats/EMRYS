# Storage qualification

This owner checks whether the exact Project and reference filesystems support
safe execution. Storage capacity planning and retention policy are external
operator responsibilities.

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

Qualification evidence alone does not establish site approval, production
suitability, scientific review, or biological validity.
