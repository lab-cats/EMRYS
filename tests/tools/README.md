# Test tools

These scripts run repository checks and produce test results; they are not
public workflow commands.

- `run_validation.py` runs static checks and non-overlapping test groups.
- `python_test_shards.py` uses recorded durations and configured xdist capacity
  to choose deterministic CI shard membership. Pytest-xdist owns actual worker
  assignment and work stealing; receipts therefore bind worker count and exact
  inventory without claiming a predicted runtime. Each shard retains pytest's
  total-runtime JUnit timing XML as a candidate for a later reviewed baseline
  update; the observation does not change the active baseline itself.
- `source_dependencies.py` checks the import rules and exact exceptions in
  `src/emrys/contracts/SOURCE_TOPOLOGY.md`.
- `real_synthetic_e2e.py` runs one explicit managed-synthetic scenario without
  installing or cleaning dependencies. `success-parity` compares clean direct
  and Slurm completion; `failure-resume` compares direct and Slurm recovery from
  a controlled pre-Task failure; `stop-resume` gates a fresh Slurm Task's real
  `samtools view` invocation, binds and stops that exact active submission, and
  resumes only after positive interruption closure; `production-like` runs the
  100,000-pair Slurm profile straight through. Run and resume submissions must
  report matching request-token stream paths in the selected log directory.
  Invalid submission paths trigger the existing emergency cleanup guard for the
  single reported job; that guard is not the public stop proof, and missing or
  ambiguous job IDs never authorize cancellation. Hosted single-node scenarios
  do not establish Viking memory policy or cross-node behavior.
  Real hosted scientific Runs derive their resource policy from the packaged
  allocation-aware defaults and resolve against the runner allocation. The tiny
  fixture lowers only repeatable-stage memory admission floors to 2048 MiB; it
  is not a production memory recommendation. Disposable Slurm requests all node
  CPUs, all node memory, and exclusive placement. These checks establish policy
  selection and resolution, not sustained utilization or performance.
- The coverage tools compare results with reviewed baselines.
