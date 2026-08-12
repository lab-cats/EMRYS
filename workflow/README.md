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
`python -I -m norad.orchestration.local_pilot.task --dispatch <absolute-json>`.
There are no native scientific outputs, directories, temporary outputs,
checkpoints, retries, or dynamic/glob discovery in the Snakemake output model.
Pre-existing verified-task markers are reusable only after NORAD revalidates
their canonical record, exact run/profile/owner/scope identity, referenced
task attempt, validation report and fresh semantic all-pass result, native
receipt, and every bound input/output size and SHA-256. A stale or copied JSON
pathname therefore cannot unlock downstream work.

## Fixed inputs

The workflow reads the reviewed profile at
[`contracts/local_cmh_v1.json`](contracts/local_cmh_v1.json). A caller must
also provide a JSON or YAML Snakemake config with this closed operational
mapping:

```yaml
run_root: /absolute/workspace/runs/run-...
execution_path: /absolute/workspace/runs/run-.../contract/normalized.json
profile_path: /absolute/workspace/runs/run-.../contract/profile.json
dispatch_paths:
  norad.stage.construct_STAR_index.v1:
    reference-id: /absolute/workspace/runs/run-.../dispatch/00a.json
```

`dispatch_paths` contains one absolute, pre-materialized dispatch path for
every owner/scope pair selected by the normalized execution contract. B3 does
not add a public run materializer or lifecycle command; those remain outside
this static projection.

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
- `cohort_slice`: the default full automatic profile (`3 + 7S + P + 2` owner
  jobs for `S` samples and `P` partitions).

For the canonical four-sample, one-partition fixture, `cohort_slice` has 34
owner jobs. Its direct owner-job edges total
`9S + S*P + 2P + 1`, or 43 for that fixture. Input-only target edges and
external dispatch files are not scientific DAG edges.

Use pinned Snakemake 9.25.1 from the locked workflow dependency group:

```bash
uv sync --locked --group workflow
uv run --locked --group workflow --no-sync snakemake \
  --workflow-profile local \
  --configfile /absolute/path/to/workflow-config.yaml \
  --dry-run reference_slice
```

An actual execution requires dispatch records whose producer and validator
commands point to the intended public owner interface. Tests use a bounded
test double and never call STAR, GATK, Picard, RSeQC, bcftools, R, or other
scientific tools.
