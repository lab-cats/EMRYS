# Test tools

This directory owns test-only runners and comparators. The Python coverage
baseline tool implements the policy in the
[test baseline](../../docs/design/TEST_BASELINE.md), while `run_validation.py`
coordinates the serial static preflight and four non-overlapping owner lanes
documented by the
[operations runbook](../../docs/operations/RUNBOOK.md).

`python_test_shards.py` is the test-only CI partitioner. It uses the reviewed
duration estimates in `tests/baselines/python_test_durations.json` to build a
deterministic balanced plan, runs exact pytest node IDs with xdist work
stealing, and verifies downloaded receipts cover the current inventory once
and only once. Estimates change scheduling only, and stale estimate node IDs
fail closed.

These files support repository validation; they are not public workflow
commands or independent evidence authorities.

`real_synthetic_e2e.py` is the CI-owned retained real-runtime driver. It
initializes one public synthetic profile, prepares an exact runtime TSV from
already-provisioned paths, performs real two-phase storage qualification,
submits both the no-write plan and explicit execution through the generated
single-node Slurm wrapper, and independently checks the fixed completion
oracles. The default invocation is a no-write plan; only its explicit
`--execute` flag enters the sequence. The driver independently attests the
exact RSeQC distribution and retains a narrow version adapter; only
`--version` is normalized, while real calls execute the exact provisioned
Python and delegate. A retained GATK adapter executes the canonical Broad
launcher with the locked runtime Python, clears ambient launcher overrides, and
seals PATH/JAVA_HOME to the locked Java independently of the Slurm launcher's
PATH. A retained gunzip adapter adds explicit decompression after canonical
path admission, so a provisioned `gunzip -> gzip` link cannot silently change
STAR's read-command behavior. Adapter delegates, retained bytes, and bound
runtimes are hashed in the summary. The driver installs and cleans nothing; its
machine-readable summary remains synthetic execution evidence, never
production or biological evidence.

`retained_stage_benchmark.py` consumes the successful retained 100,000-pair
summary and runs paired Step 07 and Step 08 comparison cases against the exact
locked Python, scientific-tool, and R authorities supplied by CI. It creates
fixtures, frozen source archives, manifests, raw benchmark results, and its
machine-readable summary only beneath a create-absent external output root;
the source checkout remains read-only. The default invocation is a no-write
plan, and `--execute` is required to run the comparisons. Correctness parity
is mandatory, but timings are observational: the helper defines no speed
threshold.

In CI the benchmark output is retained beneath
`100000/retained-stage-benchmark` in the existing 100,000-pair evidence
artifact. These are hosted-runner, single-node, synthetic-data measurements.
They do not prove CSU or another real cluster, shared-filesystem behavior,
production performance, scientific review, or biological validity.
