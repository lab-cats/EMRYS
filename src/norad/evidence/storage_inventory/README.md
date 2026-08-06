# Storage-inventory evidence owner

[`storage_inventory.py`](storage_inventory.py) measures explicitly declared
storage roots and records explicitly declared retention-policy state. It is
read-only with respect to measured storage: it never deletes, moves, archives,
compresses, cleans, repairs, or executes a retention decision.

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

Use the [`RUNBOOK`](../../../../docs/operations/RUNBOOK.md) for invocation and
[`TROUBLESHOOTING`](../../../../docs/operations/TROUBLESHOOTING.md) for root,
measurement, policy, or transaction-lock failures. Current evidence is local
fixture evidence only; no production inventory or approved production
retention policy exists.
