# Local CMH workflow projection

This directory contains NORAD's fixed, source-checkout-bound Snakemake
projection. It schedules public owner tasks; it does not own scientific
behavior, infer a workflow from filenames, or promote Snakemake metadata to
scientific evidence.

## Implemented boundary

[`Snakefile`](Snakefile) defines exactly thirteen executable owner rules from
the automatic subset of
[`STAGE_MAP.md`](../src/norad/contracts/STAGE_MAP.md). Step `09c` remains a
separately authorized scientific-review owner and is deliberately absent. The
`02b` and `03` evidence rules are required leaves of a complete run, but they
never gate downstream scientific compute.

Every executable rule publishes only one path of this form:

```text
<run-root>/state/verified/<machine-key>/<scope-id>.json
```

The generic task runner owns production, owner validation, semantic all-pass
checking, and publication of that verified record. The Snakefile invokes it as
`python -X pycache_prefix=/dev/null -I -m
norad.orchestration.local_pilot.task --dispatch <absolute-json>
--dispatch-sha256 <expected-sha256>`. The immutable attempt-specific config
binds each dispatch path and digest before the runner stable-reads those exact
bytes again at execution time.
There are no native scientific outputs, directories, temporary outputs,
checkpoints, retries, or dynamic/glob discovery in the Snakemake output model.
Pre-existing verified-task markers are reusable only after NORAD revalidates
their canonical record, exact run/profile/owner/scope identity, referenced
task attempt, validation report and fresh semantic all-pass result, native
receipt, and every bound input/output size and SHA-256. A stale or copied JSON
pathname therefore cannot unlock downstream work.

After all 34 required owner results are verified, three non-scientific rules
run in order: `build_artifact_index`, `build_run_summary`, and
`build_html_report`. Each calls its grouped public `norad build` CLI once in
dry-run mode, publishes an immutable reporting-start record, calls the builder
with the identical arguments plus `--execute`, and finally publishes a
verified-reporting record after semantic receipt validation. Snakemake declares
only the fixed `state/reporting/<kind>/verified.json` record for each rule;
native receipts remain builder-owned semantic evidence passed as parameters.
Downstream reporting rules consume verified records, and the default input-only
`local_pipeline_slice` target ends at the HTML-report verified record. Step
`09c` is still absent, so this local pipeline can correctly report
`evidence_incomplete`; reporting never promotes scientific review.

A pre-existing reporting result is reusable only when both its start and
verified records exist and the public read-only validator reconstructs the
origin attempt and complete semantic transaction. Neither record means the
scope is pending. A lone start is entered-but-incomplete, a lone verified
record is orphaned, and either state fails closed before Snakemake admits the
graph. A native receipt pathname alone never satisfies the workflow.

## Fixed inputs

The workflow reads the reviewed profile at
[`contracts/local_cmh_v1.json`](contracts/local_cmh_v1.json). A caller must
also provide an immutable, canonical-JSON, attempt-specific Snakemake config
with this closed operational mapping:

```json
{
  "artifact_inventory_path": "/absolute/run/contract/artifact_inventory.tsv",
  "artifact_source_root": "/absolute/run",
  "dispatch_paths": {
    "norad.stage.construct_STAR_index.v1": {
      "reference-id": {
        "path": "/absolute/run/contract/dispatch/workflow-.../00a.json",
        "sha256": "<64 lowercase hex>"
      }
    }
  },
  "execution_path": "/absolute/run/contract/normalized.json",
  "python_executable": "/absolute/run-environment/bin/python",
  "primary_analysis_policy_path": "/absolute/run/contract/primary_analysis_policy.json",
  "profile_path": "/absolute/run/contract/profile.json",
  "reference_contract_path": "/absolute/run/contract/reference_contract.json",
  "reporting_run_contract_path": "/absolute/run/contract/reporting_run_contract.json",
  "run_root": "/absolute/run",
  "source_checkout": "/absolute/norad-checkout",
  "workflow_attempt_id": "workflow-YYYYMMDDTHHMMSSZ-<32 lowercase hex>"
}
```

The attempt ID resolves to
`<run-root>/attempts/<workflow-attempt-id>/attempt.json`. That immutable record
binds the attempt-specific workflow-config path and SHA-256, the normalized
execution and profile, and the source checkout. The four reporting projection
paths must exactly match the normalized execution's path and digest references.
`artifact_source_root` is the run root; `source_checkout` is the executing
canonical NORAD Git checkout. `dispatch_paths` is closed over every automatic
owner/scope pair and transitively binds the exact producer, validator, inputs,
and outputs through each dispatch digest. A completed task keeps the exact
predecessor dispatch reference already bound in its verified record; a resume
attempt materializes new dispatches only for pending tasks. Every pending
dispatch must bind the current workflow-attempt ID, and every dispatch must
place task evidence at
`attempts/<dispatch-attempt-id>/tasks/<machine-key>/<scope-id>/{task-attempt.json,stdout.log,stderr.log}`.
Replacing a completed task's dispatch with semantically different argv is a
hard admission failure, even if Snakemake would otherwise consider the output
current.
The configured absolute Python launcher must be the exact lexical executable
running Snakemake (a virtual-environment symlink is permitted) and must match
the attempt's normalizer plus both the Python and Snakemake required-tool
identities. Before admitting the graph, the child also attests that its loaded
NORAD package bytes equal the declared checkout working tree and that the
checkout HEAD still equals the attempt's declared commit. It refuses the graph
before any rule if those identities disagree.

`state/verified` is a closed filesystem roster. If it exists, it may contain
only expected real owner directories and exact regular JSON marker files;
unexpected files, directories, symlinks, and deeper paths fail before the DAG
is admitted. `state/reporting` is likewise closed over exactly
`artifact_index`, `run_summary`, and `html_report`, with only `start.json` and
`verified.json` permitted in each real ledger directory.

The checked-in local workflow profile is
[`profiles/local/profile.v9+.yaml`](profiles/local/profile.v9+.yaml). It uses
Snakemake's local executor with one core, the greedy scheduler, zero retries,
incomplete-output preservation, printed shell commands, and failed-log
display.

## Reviewable slices

The three input-only targets expose bounded closures without changing owner
dependencies:

- `reference_slice`: the three reference-scoped owners (`3` owner jobs).
- `one_sample_slice`: reference preparation plus the first manifest sample
  through `02b`, `03`, and `06` (`10` owner jobs).
- `cohort_slice`: the full automatic profile (`3 + 7S + P + 2` owner
  jobs for `S` samples and `P` partitions).
- `local_pipeline_slice`: the default full automatic profile plus the three
  ordered reporting transactions.

For the canonical four-sample, one-partition fixture, `cohort_slice` has 34
owner jobs. Its direct owner-job edges total
`9S + S*P + 2P + 1`, or 43 for that fixture. Input-only target edges and
external dispatch files are not scientific DAG edges.

Install pinned Snakemake 9.25.1 from the locked workflow dependency group:

```bash
uv sync --locked --group workflow
```

B5 exposes the supported dry-run-first public `norad run`, `norad resume`, and
`norad inspect local-pilot-run` commands documented in the
[runbook](../docs/operations/RUNBOOK.md#local-pilot-execution). There remains no
supported manual Snakemake invocation. The internal lifecycle binds a
materialized run, the exact Python
launcher, checked-in Snakefile, absolute profile file, attempt-specific config,
run directory, and target in one admitted argv. Running bare `snakemake`, using
a profile name relative to the current directory, or constructing an ad hoc
config bypasses that boundary. The reproducible fresh-clone transcript and root
README onboarding remain B6 work.

Resume is a lifecycle-owned operation, not an ad hoc Snakemake recovery
command. It uses exactly `--rerun-triggers input --ignore-incomplete` after
NORAD has re-admitted verified and reporting records. The second flag is
required by pinned Snakemake 9.25.1 when engine metadata still marks an output
incomplete even though NORAD's semantic validator proves it complete. NORAD
does not use `--rerun-incomplete`, force, unlock, or metadata cleanup to bypass
that boundary.

Tests use a bounded no-science artifact producer to execute all 34 owner jobs
and the real artifact-index, run-summary, and Jinja HTML transactions. They
never call STAR, GATK, Picard, RSeQC, bcftools, R, or other scientific tools.
