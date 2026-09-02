# Storage-inventory evidence owner

The grouped command
`emrys debug storage-inventory` measures explicitly declared
storage roots and records explicitly declared retention-policy state. Its
private [`inspector.py`](inspector.py) coordinates private owners for:

- [`_storage_contract.py`](_storage_contract.py), input models and root/policy
  admission;
- [`_storage_measurement.py`](_storage_measurement.py), read-only measurement
  and deterministic evidence rendering;
- [`_storage_publication.py`](_storage_publication.py), locked receipt-last
  publication and rollback; and
- [`qualification.py`](qualification.py), single-host direct probing plus
  two-phase site-semantic probing and receipt admission.

Doctor's explicit repair owns the create-absent direct receipt used by ordinary
single-host placement. It probes hard links, advisory `flock`, atomic rename,
and fsync at the exact Project/reference roots under the current host and
numeric identity, then removes only its private probe directories. It makes no
cross-node, head/compute-consistency, or post-allocation durability claim.

The sibling grouped command
`emrys debug storage-qualification` owns the narrow two-phase
site check required for Slurm. Its compute phase
creates private probes in the workflow parent and Step `00c` sidecar parent;
its head-node finalize phase re-admits those probes after the allocation,
publishes one content-bound qualification receipt, and removes only the exact
private probe directories. It tests hard links, advisory `flock` contention,
atomic rename visibility, write/fsync, numeric UID/GID consistency, mount
identity/capacity, and post-allocation durability. A failed or interrupted
phase publishes no final qualification and leaves evidence for inspection.
The receipt records each observed Linux device number for diagnosis and uses
it for same-node hard-link proof, but does not require `st_dev` to be identical
across nodes because one shared mount may receive different node-local device
numbers. Canonical path, inode, UID/GID, and mount source/type remain stable
cross-node identity requirements.

The inventory inspector is private and performs no retention action. Its
inspection is read-only with respect to measured storage: it never deletes,
moves, archives, compresses, cleans, repairs, or executes a retention decision.

The public interface accepts roots and retention-policy TSVs plus an output
root, which must already exist in execute mode. Dry run is the default: it
performs the declared measurements and writes nothing. The owner counts bytes,
files, directories, and symlinks without following symlinks, and records
filesystem capacity. Policy actions are closed to `retain`, `archive`, and
`review_then_delete`; approval states are recorded, not acted upon. Execute
mode publishes:

- `storage_inventory.tsv`
- `retention_policy.tsv`
- `storage_retention_summary.tsv`, published last

Exit zero means measurement and any requested publication completed, not that
the summary passed. Publication retains the characterized recovery gap: a
failed restoration can leave hidden predecessor files and an incomplete visible
output set without a recovery marker. The committed
[`storage_roots.example.tsv`](../../../../configs/storage_roots.example.tsv) and
[`retention_policy.example.tsv`](../../../../configs/retention_policy.example.tsv)
are structural starters requiring real roots, optional quota expectations,
retention decisions, and approval records. Direct protection lives in
[`test_storage_inventory.py`](../../../../tests/evidence/storage_inventory/test_storage_inventory.py).


Site qualification is dry-run-first. Run the compute phase inside the selected
allocation, then run finalize on the head node only after that allocation ends:

```bash
emrys debug storage-qualification \
  --workspace /absolute/path/to/future-workspace \
  --reference-fasta /absolute/path/to/reference.fa \
  --phase compute --execute

emrys debug storage-qualification \
  --workspace /absolute/path/to/future-workspace \
  --reference-fasta /absolute/path/to/reference.fa \
  --phase finalize --execute
```

The receipt path is derived from the two canonical storage roots, so Run needs
no ambient selector. Network storage is supported for Slurm only after this
exact check passes. Node-local storage that is not visible and durable on the
head node cannot finalize and therefore cannot admit Slurm; this owner does not
copy or stage data around that failure. Lifecycle semantically re-admits the
placement-appropriate receipt and both qualified roots before delegation and
after the workflow child terminates; the Attempt is blocked if either
observation differs from its immutable storage identity. Historical Attempts
without placement retain the two-phase requirement.

Dry-run, execute, and focused test are:

```bash
emrys debug storage-inventory \
  --roots configs/storage_roots.example.tsv \
  --retention-policy configs/retention_policy.example.tsv \
  --output-root results/qc/storage

mkdir -p results/qc/storage
emrys debug storage-inventory \
  --roots /explicit/path/to/storage_roots.tsv \
  --retention-policy /explicit/path/to/retention_policy.tsv \
  --output-root results/qc/storage \
  --execute

.venv/bin/python -m pytest -q \
  tests/evidence/storage_inventory/test_storage_inventory.py
```

Use [`TROUBLESHOOTING`](../../../../docs/operations/TROUBLESHOOTING.md) for
root, measurement, policy, or transaction-lock failures. Current evidence is local fixture evidence only; no Viking site qualification,
production inventory, or approved production retention policy is claimed until
its retained receipt is produced and admitted.
