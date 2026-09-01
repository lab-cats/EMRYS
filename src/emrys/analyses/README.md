# Analysis modules

This directory contains downstream scientific analyses. An analysis module is
selected by name in `project.yaml`; it consumes admitted upstream artifacts and
runs inside the same immutable Run, task, validation, provenance, recovery,
logging, and reporting machinery as the built-in analysis. It is not a second
workflow engine.

The built-in modules are:

- [`paired_cmh_candidate_ranking/`](paired_cmh_candidate_ranking/README.md)
  — physical/package owner of semantic
  `rank_cohort_candidates_with_paired_CMH`, the paired-stratum CMH candidate
  ranking analysis for historical Step `09`.
- [`scientific_context_projection/`](scientific_context_projection/README.md)
  — physical/package owner of semantic
  `project_candidate_scientific_context`, the bounded post-Step09 reference,
  known-motif, logo-value, and enrichment projection for historical Step `10`.

Each child `CONTRACT.md` owns method, inputs, outputs, publication, known
limits, and evidence meaning; its README owns operator commands and focused
test routes. Analysis output is not scientific review or biological
validation.

## Selecting an installed module

An installed Python distribution exposes one provider through the standard
package entry-point mechanism:

```toml
[project.entry-points."emrys.analysis_modules"]
"org.example.differential" = "example_analysis:analysis_module_v1"
```

The scientist selects that exact ID and supplies only scientific
configuration:

```yaml
analyses:
  treatment_vs_control:
    module: org.example.differential
    partitions: inputs/partitions.tsv
    config:
      design: "~ condition"
      fdr: 0.05
```

Selection explicitly authorizes importing and executing that installed code.
EMRYS does not search for a substitute, install a missing module, or resolve an
ambiguous ID. Built-in versus external trust, distribution/version,
entry-point value, configuration-schema hash, runtime requirements, and the
selected implementation-package identity are persisted or bound to the Run.
Unselected installed modules do not affect its identity.

## Version 1 boundary

The provider returns one immutable `AnalysisModuleDescriptorV1`. It declares:

- a JSON Schema and normalizer for scientific configuration;
- one or two single-core tasks occupying the existing downstream Step `09`
  and optional Step `10` slots;
- each task's owner identity, minimum memory, typed predecessor adapters,
  typed outputs, planner, producer command, validator command, and complete
  input paths;
- one installed package containing the review-relevant implementation;
- required check IDs from the admitted EMRYS runtime profile; and
- one scientific-report renderer receiving the admitted Run summary and the
  module's exact result artifacts and returning a self-contained HTML document
  with its interpretation boundary.

EMRYS derives the profile edges, canonical artifact IDs, adapter registry,
and evidence records. A module owns its bespoke scientific presentation;
EMRYS owns automatic invocation, opt-out, independent regeneration, the fixed
evidence-and-operations view, validation, locking, rollback, receipt, and
publication. There is no generic report schema, section DSL, or second artifact
authority. Every declared task has one standard validation report and uses the
existing atomic task publication and failure/recovery semantics.

V1 intentionally does not define arbitrary stages, a workflow language,
parallel resource shapes, installation/repair behavior, or new native runtime
checks. Python/package dependencies belong to the installed implementation
package; native tools must already have compatible check IDs in the selected
runtime profile. Expanding those limits requires a later interface version,
not an ad hoc exception in one module.
