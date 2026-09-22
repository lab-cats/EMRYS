# Test tools

These scripts run repository checks and produce test results; they are not
public workflow commands.

- `run_validation.py` runs static checks and non-overlapping test groups.
- `python_test_shards.py` balances CI groups using recorded durations and checks
  that their receipts cover the exact test inventory.
- `source_dependencies.py` checks the import rules and exact exceptions in
  `src/emrys/contracts/SOURCE_TOPOLOGY.md`.
- `real_synthetic_e2e.py` runs the managed synthetic workflow and direct/Slurm
  checks without installing or cleaning dependencies. Run and resume submissions
  must report matching request-token stream paths in the selected log directory.
  The selected 130-pair Slurm journey also gates a Task's real `samtools view`
  invocation by substituting a blocking FIFO for its input. It binds the exact
  resume request to that admitted active native Task, observes it through public
  inspection and watch, issues one public controller-filtered stop, and resumes
  only after closed interruption evidence. It retains separate three-Attempt
  Slurm and two-Attempt direct histories before comparing final real-tool Results
  and reports. Invalid submission paths trigger the existing emergency cleanup
  guard for the single reported job; that guard is not the public stop proof,
  and missing or ambiguous
  job IDs never authorize cancellation. This hosted single-node journey does not
  establish Viking memory policy or cross-node behavior.
  Real hosted scientific Runs derive their resource policy from the packaged
  allocation-aware defaults and resolve against the runner allocation. The tiny
  fixture lowers only repeatable-stage memory admission floors to 2048 MiB; it
  is not a production memory recommendation. Disposable Slurm requests all node
  CPUs, all node memory, and exclusive placement. These checks establish policy
  selection and resolution, not sustained utilization or performance.
- The coverage tools compare results with reviewed baselines.
