# Storage-inventory evidence owner

The grouped command
`python -I -m norad inspect storage-inventory` measures explicitly declared
storage roots and records explicitly declared retention-policy state. Its
private [`inspector.py`](inspector.py) coordinates private owners for:

- [`_storage_contract.py`](_storage_contract.py), input models and root/policy
  admission;
- [`_storage_measurement.py`](_storage_measurement.py), read-only measurement
  and deterministic evidence rendering; and
- [`_storage_publication.py`](_storage_publication.py), locked receipt-last
  publication and rollback.

The inspector is private and adds no second command or retention action. The
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

Dry-run, execute, and focused test are:

```bash
.venv/bin/python -I -m norad inspect storage-inventory \
  --roots configs/storage_roots.example.tsv \
  --retention-policy configs/retention_policy.example.tsv \
  --output-root results/qc/storage

mkdir -p results/qc/storage
.venv/bin/python -I -m norad inspect storage-inventory \
  --roots /explicit/path/to/storage_roots.tsv \
  --retention-policy /explicit/path/to/retention_policy.tsv \
  --output-root results/qc/storage \
  --execute

.venv/bin/python -m pytest -q \
  tests/evidence/storage_inventory/test_storage_inventory.py
```

Use [`TROUBLESHOOTING`](../../../../docs/operations/TROUBLESHOOTING.md) for
root, measurement, policy, or transaction-lock failures. Current evidence is
local fixture evidence only; no production inventory or approved production
retention policy exists.
