# Analysis modules

This directory contains downstream scientific analyses. A module is selected
by name in `project.yaml`, consumes admitted processing artifacts, and runs
inside the same immutable Run, task, validation, provenance, recovery,
logging, and reporting machinery as the built-in analysis. It is not a second
workflow engine.

The built-in module is
[`paired_cmh_candidate_ranking/`](paired_cmh_candidate_ranking/README.md).
It owns historical Step `09` and nests the bounded historical Step `10`
[`scientific_context_projection/`](paired_cmh_candidate_ranking/scientific_context_projection/README.md).
Their `CONTRACT.md` files retain the methods, inputs, assumptions, outputs,
publication rules, known limits, and evidence meaning needed for review.
Analysis output is not scientific review or biological validation.

Existing Projects may keep the flat paired-CMH Analysis shape. That
compatibility path selects `emrys.paired-cmh` internally and retains Analysis
revision v1, run-summary v2, and report-receipt v4. An explicit `module` plus
`config` uses Analysis revision v2, run-summary v3, and report-receipt v5.

## Selecting an installed module

An installed Python distribution exposes one computation provider through the
standard package entry-point mechanism:

```toml
[project.entry-points."emrys.analysis_modules"]
"org.example.differential" = "example_analysis:analysis_module_v1"
```

The scientist selects that exact ID and supplies scientific configuration:

```yaml
analyses:
  treatment_vs_control:
    module: org.example.differential
    partitions: inputs/partitions.tsv
    config:
      design: "~ condition"
      fdr: 0.05
```

Selection authorizes importing and executing that installed code. EMRYS does
not search for a substitute, install a missing module, or choose between
ambiguous providers. The distribution/version, entry point, configuration
schema, dependency declarations, and exact computation-package bytes are
persisted or bound to the Run. The normalized scientific configuration enters
Analysis identity; installation facts do not. Unselected modules do not affect
identity.

## Version 1 computation boundary

The provider returns one immutable `AnalysisModuleDescriptorV1`. It declares:

- a JSON Schema and one normalizer for scientific configuration;
- one or two tasks occupying the existing downstream Step `09` and optional
  Step `10` slots;
- typed predecessor artifacts and typed outputs, stable provenance roles,
  minimum memory and threads, a command planner, producer, and independent
  validator;
- fixed EMRYS runtime checks or exact local executable, R namespace, file, and
  package-tree dependencies; and
- one self-contained installed package subtree containing its callbacks,
  resources, and review-relevant implementation.

EMRYS derives profile edges, canonical artifact IDs, adapter records, and
evidence. Every module inherits the existing fail-closed `TaskDispatch`,
validation, publication, recovery, and logging semantics. Providers are
trusted in-process installed code; version 1 deliberately has no self-attested
trust enum or module-defined failure-policy language.

The selected dependencies are composed onto the fixed runtime profile only for
that Analysis. Doctor probes them with the existing runtime inspector; exact
files and installed package trees enter Run toolchain identity, and task-used
files are rechecked through the existing task-input boundary. Unknown,
unavailable, ambiguous, or changed dependencies block execution. The existing
resource policy supplies Step `09`/`10` threads and memory and must meet each
task's declared minimums.

Version 1 does not define arbitrary stages, dependency solving, installer
commands, GPU/disk/walltime placement, remote resources, or a second runtime
authority. The selected provider and its dependencies are installed with their
established package managers. Managed Doctor repair restores only EMRYS's fixed
uv/Pixi/renv locks; it diagnoses module dependencies and directs the operator
back to the owning package manager rather than executing provider-supplied
installation logic.

The persisted profile still carries unique `rule_name` values for historical
schema compatibility. For module tasks these identify dispatch adapters, not
literal distinct Snakemake rules; removing that backend-leaking field belongs
to a later versioned profile-contract reduction.

Processing-only reuse is module-neutral. When the exact Steps `00`–`06`
compatibility digest and existing sample/reference rules match, a downstream
Run may select a different admitted module while reusing stationary,
content-bound source artifacts. The target still owns its own downstream
tasks, evidence, Results, report transaction, and application log.

## Bespoke scientific reporting

Reporting is separate from the scientific Run identity. An installed
distribution must expose a matching report-only entry point when reporting is
enabled:

```toml
[project.entry-points."emrys.analysis_reporters"]
"org.example.differential" = "example_analysis_report:render_scientific_report"
```

Doctor admits that provider before a reporting-enabled execution. Reporting
loads it again only after admitting the completed Run and passes exact result
artifacts plus an isolated Run-summary copy. The provider owns its bespoke
scientific HTML and interpretation boundary. Its package identity is bound to
the report receipt, never Analysis or Run identity.

EMRYS retains automatic reporting by default, `--no-report`, independent
regeneration, the fixed evidence-and-operations view, HTML validation,
locking, rollback, receipt-last publication, and input rechecks. There is no
generic report schema, section DSL, artifact store, module registry, Stage
hierarchy, workflow language, or second scheduler.
