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

`source_dependencies.py` is the read-only Python import-graph gate used by the
static preflight. It classifies current source owners, scans declared imports
and recognized literal standard-library dynamic import forms, enforces only
the ratified negative dependency rules, rejects cycles between neutral library
owners, and contains exact stale-failing rosters for current CLI composition
and known transitional edges. It does not perform general dynamic-import
data-flow inference or infer shell/R invocation, artifact flow, scientific
semantics, future package placement, or a general architecture framework.

`real_synthetic_e2e.py` is the CI-owned retained real-runtime driver. It
initializes one public synthetic profile, discovers the already-provisioned
runtime into the Project-owned admitted profile, performs real two-phase
storage qualification,
submits both the no-write plan and explicit execution through grouped Run
control with the single-node Slurm execution profile, and independently checks
the fixed completion oracles. The default invocation is a no-write plan; only
its explicit `--execute` flag enters the sequence. The driver independently
attests the exact RSeQC distribution and retains a narrow version adapter; only
`--version` is normalized, while real calls execute the exact provisioned
Python and delegate. A retained GATK adapter executes the canonical Broad
launcher with the locked runtime Python, clears ambient launcher overrides, and
seals PATH/JAVA_HOME to the locked Java independently of the private Slurm
transport's PATH. A retained gunzip adapter adds explicit decompression after
canonical path admission, so a provisioned `gunzip -> gzip` link cannot
silently change STAR's read-command behavior. For the 130-pair profile, the
CI driver supplies an absent Snakemake profile once per placement, causing a
deterministic engine-admission failure before task entry while leaving admitted
inputs unchanged. It then proves failed direct and Slurm Attempts followed by
public `resume`. The 100,000-pair profile remains an uninterrupted success-only
path. Adapter delegates, retained bytes, and bound runtimes are hashed in the
summary. The driver installs and cleans nothing; its machine-readable summary
remains synthetic execution evidence, never production or biological evidence.
