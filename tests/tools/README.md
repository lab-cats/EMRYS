# Test tools

These are test-only support, never public workflow commands:

- `run_validation.py` runs the static preflight and non-overlapping test lanes.
- `python_test_shards.py` produces deterministic duration-balanced CI shards
  and verifies receipt coverage of the exact test inventory.
- `source_dependencies.py` checks the ratified static import directions and
  exact exception rosters in `src/emrys/contracts/SOURCE_TOPOLOGY.md`.
- `real_synthetic_e2e.py` drives the retained managed-runtime synthetic Run and
  direct/Slurm checks without installing or cleaning dependencies.
- coverage tools compare current results with reviewed baselines.

Their outputs are local or hosted-CI engineering evidence, not production,
institutional-cluster, scientific-review, or biological proof.
