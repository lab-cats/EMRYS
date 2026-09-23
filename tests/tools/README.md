# Test tools

These scripts run repository checks and produce test results; they are not
public workflow commands.

- `run_validation.py` runs static checks and non-overlapping test groups.
- `python_test_shards.py` balances CI groups using recorded durations and checks
  that their receipts cover the exact test inventory.
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
  do not establish Viking memory policy or cross-node behavior. The disposable
  CI controller's 300-second `KillWait` matches the Task cleanup signal horizon;
  it does not change production scheduler policy or permit resume without an
  admitted interruption boundary.
  Real hosted scientific Runs derive their resource policy from the packaged
  allocation-aware defaults and resolve against the runner allocation. The tiny
  fixture lowers only repeatable-stage memory admission floors to 2048 MiB; it
  is not a production memory recommendation. Disposable Slurm requests all node
  CPUs, all node memory, and exclusive placement. These checks establish policy
  selection and resolution, not sustained utilization or performance.
- The coverage tools compare results with reviewed baselines.
