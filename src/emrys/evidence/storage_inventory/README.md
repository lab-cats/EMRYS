# Storage qualification

This owner checks whether the exact Project and reference filesystems support
safe execution. Storage capacity planning and retention policy are external
operator responsibilities.

## Qualification and recovery

Doctor repair can create the single-host direct receipt after checking hard
links, `flock`, atomic rename, fsync, permissions, and identity at the exact
Project/reference roots. For Slurm, head-node Doctor repair automatically
submits the compute check and
completes [head-node finalization](../../../../docs/operations/RUNBOOK.md#slurm-setup-and-submission).
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

## Advanced manual checks

Normal setup uses head-node `emrys doctor --repair`. To investigate storage
separately, use the exact Project and reference FASTA paths printed by Doctor.
Run the compute phase as work in a real Slurm allocation:

```bash
emrys debug storage-qualification --workspace /absolute/path/to/project --reference-fasta /absolute/path/to/reference.fa --phase compute --execute
```

After that job completes, finalize from the head node outside an allocation:

```bash
emrys debug storage-qualification --workspace /absolute/path/to/project --reference-fasta /absolute/path/to/reference.fa --phase finalize --execute
```

Omit `--execute` to preview either phase. The workspace argument names the
Project, but the two-phase check probes its parent and the FASTA's parent.
Evidence remains under `.emrys-storage-qualification/` in the Project's parent.
Preserve receipts and probes on failure; repeating these manual writes is not
a recovery procedure. Doctor reuses admitted evidence and separately rechecks
the current runtime.
