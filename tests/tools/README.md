# Test tools

These scripts run repository checks and produce test results; they are not
public workflow commands.

- `run_validation.py` runs static checks and non-overlapping test groups.
- `python_test_shards.py` balances CI groups using recorded durations and checks
  that their receipts cover the exact test inventory.
- `source_dependencies.py` checks the import rules and exact exceptions in
  `src/emrys/contracts/SOURCE_TOPOLOGY.md`.
- `real_synthetic_e2e.py` runs the managed synthetic workflow and direct/Slurm
  checks without installing or cleaning dependencies.
- The coverage tools compare results with reviewed baselines.
