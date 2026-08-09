# Storage-inventory evidence owner

[`storage_inventory.py`](storage_inventory.py) measures explicitly declared
storage roots and records explicitly declared retention-policy state. It is
read-only with respect to measured storage: it never deletes, moves, archives,
compresses, cleans, repairs, or executes a retention decision.

The 90-line public command preserves its direct-import names, CLI, live
`outputs` hook, and interpreter-only file mode over private owners for:

- [`_storage_contract.py`](_storage_contract.py), input models and root/policy
  admission;
- [`_storage_measurement.py`](_storage_measurement.py), read-only measurement
  and deterministic evidence rendering; and
- [`_storage_publication.py`](_storage_publication.py), locked receipt-last
  publication and rollback.

No private module exceeds 212 lines, and all 12 pre-split function bodies are
AST-identical. The package adds no second command or retention action.

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
the summary passed. The committed
[`storage_roots.example.tsv`](../../../../configs/storage_roots.example.tsv) and
[`retention_policy.example.tsv`](../../../../configs/retention_policy.example.tsv)
are structural starters requiring real roots, optional quota expectations,
retention decisions, and approval records. Direct protection lives in
[`test_storage_inventory.py`](../../../../tests/evidence/storage_inventory/test_storage_inventory.py).

Dry-run, execute, and focused test are:

```bash
.venv/bin/python src/norad/evidence/storage_inventory/storage_inventory.py \
  --roots configs/storage_roots.example.tsv \
  --retention-policy configs/retention_policy.example.tsv \
  --output-root results/qc/storage

mkdir -p results/qc/storage
.venv/bin/python src/norad/evidence/storage_inventory/storage_inventory.py \
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
