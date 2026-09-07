# Run-coordinator orchestration boundary

This private application owner connects the public Project model to immutable
Run planning, direct or whole-Run Slurm execution, Attempt lifecycle, status,
recovery, and downstream reporting. Scientific algorithms, native artifact
publication, validation meaning, report rendering, and package management stay
with their own owners.

## Ordinary journey

Create or enter a Project, then use the path-light public commands:

```bash
emrys init PROJECT_NAME
cd PROJECT_NAME
emrys validate
emrys doctor
emrys run [--analysis NAME] [--profile NAME|ABSOLUTE_PATH]
emrys inspect [RUN]
emrys resume [RUN]
emrys report [RUN]
```

`init` and `runtime discover` are dry-run-first; publication requires
`--execute`. `run` and `resume` display one frozen plan and ask before terminal
execution. Noninteractive mutation requires `--execute`. Refusal, EOF, or
interruption before authority writes nothing, submits nothing, and opens no
application log.

Omitting the Analysis is valid only for a singleton Project. Omitted Run
selection chooses the sole Run or offers a terminal picker. Automation supplies
an unambiguous two-word Run name, full ID, or unique ID prefix; EMRYS never
infers the latest Run. Omitted execution profile reads
`runtime/profiles/default.yaml`; a safe name reads the matching Project-local
file, and an absolute path is exact. There is no site/global registry.

Full Runs invoke reporting after scientific completion unless `--no-report` is
selected. `emrys report` can regenerate or reuse the reporting transaction
independently. Reporting creates neither a Run nor an Attempt.

## Specialized setup and reuse

```bash
emrys init manifests ...
emrys init synthetic [--dataset-profile smoke-v1|production-like-v1]
emrys runtime discover [--execute]
emrys doctor --repair [--execute]
emrys run --through processing
emrys run --from-processing-run PROCESSING_RUN
```

Manifest initialization requires explicit biological assignments and never
infers pairing metadata from names. Synthetic initialization produces either
the small 130-pair fixture or the separately selected 100,000-pair/5-Mb fixture;
neither is production or biological evidence. Runtime discovery admits the
active environment into `runtime/runtime.tsv` without installing or loading
modules. Doctor repair is separately confirmed, delegates dependency solving
to `uv`, Pixi, and `renv`, mutates only declared EMRYS-owned locations, and
requalifies.

A processing Run closes the evidence-complete Steps 00–06 boundary and has no
report. A downstream Run may reuse those stationary artifacts only after exact
same-Project, Reference, processing-policy, sample-subset, receipt, and content
admission. It owns its Steps 07 onward, Results, reports, Attempts, and logs;
the source Run remains unchanged.

## Internal boundary

The coordinator admits closed Project, runtime, profile, analysis-module, and
storage inputs; composes the processing profile with one selected module tail;
materializes exact task dispatches; and invokes the single Snakemake backend.
Each task records entry, runs one public owner producer and validator, requires
semantic all-pass, and publishes a verified record only after success. The
lifecycle serializes Attempts, retains failure and interruption evidence,
publishes the terminal scientific receipt last, and allows resume only across a
fully admitted between-task boundary.

Direct and whole-Run single-node Slurm placement share the same backend and
scientific graph. Scheduler and engine state are operational observations, not
completion authority. Each execution Attempt owns one application log;
scheduler submission and no-write plans own none. Read-only inspection derives
Run integrity, scientific state, Results, reporting, and recovery from EMRYS
records rather than timestamps, logs, or `.snakemake` metadata.

The adjacent dashboard is a stale CSU-oriented preview. It is not a supported
status, Results, or recovery authority and remains frozen under
`DASHBOARD-RETIRE-01` pending its separately approved retirement.

The exact public admission, mutation, filesystem, lock, signal, resume,
historical-compatibility, and evidence contract is in [`CONTRACT.md`](CONTRACT.md).
Workflow composition is summarized in
[`workflow/README.md`](../../../../workflow/README.md); configuration and
resource precedence are in [`configs/README.md`](../../../../configs/README.md).
