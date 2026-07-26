# Future Planned Architecture

This page describes the activated local roadmap beyond the current compute
pipeline. Step `09c` now exists and is fixture-tested locally; the later
artifact/report, foundation, validator, and modular tooling remains planned
until each named branch is implemented. The current pipeline is documented in
`docs/architecture/ARCHITECTURE.md`: the cluster-proven boundary remains Step
`06`, and Steps `07`-`09` remain not cluster-proven.

The local runtime boundary has moved. Signed and notarized Apple-silicon CRAN
R `4.6.1` is installed, and the repository has a guarded `renv` environment
locked to Bioconductor `3.23`. Namespace, lock, headless-PDF, and empty
cache-disabled binary restore checks pass. The Step `08` and Step `09` real-R
suites now pass locally without `SKIP`. The `step-09b1-real-r-fixes`
implementation at `eae5eca` adds raw DP/AD/INFO AD lexical preflight for Step
`08` and locale-independent raw-byte PDF fixture validation for Step `09`.
Step `09c` is implemented at `b674a31` and fixture-tested locally; it has no
production review evidence. `artifact-schema-v1` is next.

## Current vs future boundary

| Area | Current state | Future direction |
| ---- | ------------- | ---------------- |
| Core preprocessing | Steps `00a`-`06` cluster-proven across six samples | Generalized manifest-driven preprocessing backbone |
| Downstream analysis | Step `07` implemented and mocked-bcftools tested locally; Steps `08` and `09` implemented at `90335d8` and `e4371de`, hardened at `eae5eca`, and guarded real-R tested; Step `09c` implemented at `b674a31` and synthetic-fixture-tested; none has production scientific or Step `07`-`09` cluster evidence | Later assay-specific modules after explicit evidence/report foundations |
| Reporting | Handwritten demo/QC docs and generated step artifacts | Activated immediate artifact schema, adapters, run summary, self-contained HTML, and bundled-Typst PDF/TSV reports; not yet implemented |
| Data sources | Lab FASTQs on ADAM | Lab FASTQs first; possible public-dataset import later |

## Ordered roadmap boundary

Standalone source: `docs/architecture/diagrams/future_roadmap_sequence.mmd`.

```mermaid
flowchart TB
    classDef current fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef docs fill:#f5f5f5,stroke:#616161,color:#424242
    classDef runtime fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef future fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    classDef deferred fill:#fafafa,stroke:#757575,color:#424242,stroke-dasharray:4 3

    s09["step-09-cmh<br/>local implementation/docpatch complete"]
    s09a["step-09a-roadmap-docpatch<br/>documentation-only"]
    rlocal["step-09b-local-r-runtime<br/>R 4.6.1 + guarded renv / Bioc 3.23"]
    rfix["step-09b1-real-r-fixes<br/>complete locally; both suites pass"]
    science09c["step-09c-scientific-validation<br/>implemented + synthetic-fixture-tested locally<br/>production evidence unavailable"]
    artifacts["artifact-schema-v1<br/>-> artifact-adapters-v1<br/>-> artifact-run-summary"]
    reports["report-html-v1<br/>-> report-exports-v1"]
    foundations["post09-runtime-preflight<br/>-> post09-reference-provenance<br/>-> post09-storage-inventory-retention"]
    validators["one validation-report branch per step<br/>00a -> 00b -> 00c -> 01 -> 02 -> 02b<br/>-> 03 -> 04 -> 05 -> 06 -> 07 -> 08 -> 09"]
    remote["remote validation resumes later<br/>07 -> 08 -> 09 -> 09c -> targeted reruns"]

    s09 --> s09a --> rlocal --> rfix --> science09c
    science09c --> artifacts --> reports --> foundations --> validators
    validators -.-> remote

    class s09,rfix,science09c current
    class s09a docs
    class rlocal runtime
    class artifacts,reports,foundations,validators future
    class remote deferred
```

Every branch is a clean, docpatched descendant. The complete local lineage is:

```text
step-09b-local-r-runtime
-> step-09b1-real-r-fixes
-> step-09c-scientific-validation
-> artifact-schema-v1
-> artifact-adapters-v1
-> artifact-run-summary
-> report-html-v1
-> report-exports-v1
-> post09-runtime-preflight
-> post09-reference-provenance
-> post09-storage-inventory-retention
-> post09-validation-report-00a
-> post09-validation-report-00b
-> post09-validation-report-00c
-> post09-validation-report-01
-> post09-validation-report-02
-> post09-validation-report-02b
-> post09-validation-report-03
-> post09-validation-report-04
-> post09-validation-report-05
-> post09-validation-report-06
-> post09-validation-report-07
-> post09-validation-report-08
-> post09-validation-report-09
```

The `step-09b1-real-r-fixes` package was inserted after real-R execution found
one raw-count engine defect and one PDF fixture defect. The initial generic
Step `08` negative-fixture message had misattributed the later malformed-count
failure to its already-working partition-overlap validator. Step `09c` is
implemented at `b674a31`; it validates and summarizes declared evidence but
does not rerun CMH or infer review decisions. Its local fixtures are not
production review evidence. Reports move before the foundation/validator
packages and are immediate, activated work, but they remain unimplemented at
this boundary. Remote validation is paused until the final local validator
branch.

## Future modular dataflow

Standalone source: `docs/architecture/diagrams/future_modular_pipeline.mmd`.

```mermaid
flowchart LR
    classDef current fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef future fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef deferred fill:#f5f5f5,stroke:#757575,color:#424242,stroke-dasharray:4 3
    classDef contract fill:#fff8e1,stroke:#f9a825,color:#5f4300
    classDef reporting fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c

    subgraph sources["Data sources"]
        direction TB
        lab["Lab-generated FASTQs on ADAM"]
        public["Public genomics datasets<br/>deferred import"]
    end

    subgraph contracts["Configuration/contracts"]
        direction TB
        manifest["Sample manifest"]
        config["Analysis config"]
        policy_record["Versioned scientific policy<br/>review status + limitations"]
    end

    subgraph core["Core preprocessing"]
        direction TB
        backbone["Core preprocessing backbone"]
        ready["Validated analysis-ready artifacts"]
        registry["Artifact registry"]
    end

    subgraph modules["Analysis modules"]
        direction TB
        assays["Assay-specific analysis modules"]
        results["Standardized result artifacts"]
    end

    subgraph science["Scientific evidence and decision records"]
        direction TB
        declared09["Explicit Step 07-09 evidence<br/>missing/incomplete allowed"]
        science_review["Step 09c validation package<br/>implemented + fixture-tested locally"]
        decision_record["Review status + limitations<br/>ready state remains locked"]
    end

    subgraph reports["Reporting"]
        direction TB
        report_layer["Reporting layer"]
        outputs["QC reports / PI reports / candidate result reports / handoff reports"]
    end

    lab --> manifest
    public -.-> manifest
    manifest --> backbone
    config --> backbone
    manifest --> assays
    config --> assays
    policy_record --> config
    policy_record --> assays
    backbone --> ready --> assays --> results --> registry --> report_layer --> outputs
    declared09 --> science_review --> decision_record --> policy_record
    declared09 --> registry
    decision_record --> report_layer

    class lab current
    class public deferred
    class manifest,config,policy_record,decision_record,science_review contract
    class backbone,ready future
    class registry contract
    class assays,results,declared09 future
    class report_layer,outputs reporting
```

## Manifest/config contracts

Standalone source: `docs/architecture/diagrams/future_manifest_config_contracts.mmd`.

```mermaid
flowchart TD
    classDef current fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef future fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef contract fill:#fff8e1,stroke:#f9a825,color:#5f4300
    classDef reporting fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c

    subgraph contracts["Manifest/config/provenance contracts"]
        direction TB
        manifest["Manifest<br/>what data exist"]
        config["Analysis config<br/>what analysis to run"]
        policy["Predeclared analysis policy<br/>contrast / orientation / thresholds"]
        review["Step 09c review record<br/>state + decisions + limitations"]
        provenance["Provenance<br/>what code/reference/tools produced results"]
        registry["Artifact registry<br/>what outputs exist and where"]
    end

    subgraph artifacts["Validated artifact inputs"]
        direction TB
        fastqs["Validated FASTQ inputs"]
        ready["Validated analysis-ready artifacts"]
        existing["Declared Step 00a-09 artifacts<br/>missing/incomplete represented explicitly"]
    end

    subgraph modules["Assay module execution"]
        direction TB
        module["Assay-specific analysis modules"]
        results["Module result artifacts"]
        adapters["Read-only artifact adapters"]
    end

    manifest --> fastqs --> ready
    manifest --> module
    config --> module
    policy --> config
    policy --> module
    ready --> module
    provenance --> module
    module --> results --> adapters --> registry
    existing --> adapters
    existing --> review
    provenance --> registry
    registry --> reports["Run-summary JSON<br/>single structured report entry point"]
    review --> reports

    class manifest,config,policy,review,provenance,registry contract
    class fastqs,existing current
    class ready,module,results,adapters future
    class reports reporting
```

## Reporting layer

Standalone source: `docs/architecture/diagrams/future_reporting_layer.mmd`.

```mermaid
flowchart TD
    classDef future fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef contract fill:#fff8e1,stroke:#f9a825,color:#5f4300
    classDef reporting fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c

    subgraph inputs["Schema-validated records"]
        direction TB
        schema["Versioned artifact schema"]
        artifacts_tsv["schema-validated artifact index"]
        qc_summary["qc_summary.tsv"]
        provenance["runtime/provenance records"]
        final_tables["explicitly approved report-table paths"]
    end

    aggregate["Run-summary aggregation"]
    run_summary["run_summary.json"]
    generator["Static QMD / Quarto renderer<br/>no analysis execution"]
    html["Self-contained HTML report"]
    exports["Bundled Typst PDF + TSV bundle"]

    subgraph review["Scientific review fields"]
        direction TB
        review_status["evidence_incomplete or<br/>science_review_complete_exploratory"]
        orientation_status["orientation policy status/version"]
        annotation_status["annotation provenance status"]
        adjudication_status["candidate adjudication status"]
        orthogonal_status["orthogonal validation status"]
        limitations["limitations"]
        review_record["Rendered review/limitations record"]
    end

    subgraph outputs["Generated reports"]
        direction TB
        qc_report["QC and funnel summary"]
        validation_report["Steps 00a-09 evidence matrix"]
        candidate_report["CMH-ranked candidate section"]
        pi_report["Status-labeled PI report"]
        handoff_report["Methods / evidence appendix"]
        pdf_output["State-bannered PDF"]
        tsv_output["Run-summary TSV"]
    end

    schema --> artifacts_tsv
    artifacts_tsv --> aggregate
    qc_summary --> aggregate
    provenance --> aggregate
    aggregate --> run_summary
    run_summary --> generator
    final_tables --> generator
    generator --> html
    html --> qc_report
    html --> validation_report
    html --> handoff_report
    html --> candidate_report
    html --> pi_report
    html --> exports
    exports --> pdf_output
    exports --> tsv_output
    review_status --> review_record
    orientation_status --> review_record
    annotation_status --> review_record
    adjudication_status --> review_record
    orthogonal_status --> review_record
    limitations --> review_record
    review_record --> candidate_report
    review_record --> pi_report
    readylock["biological_interpretation_ready<br/>reserved and rejected by Step 09c"]
    readylock -.-> review_status

    class schema,run_summary,artifacts_tsv,qc_summary,provenance,final_tables,review_status,orientation_status,annotation_status,adjudication_status,orthogonal_status,limitations,review_record,readylock contract
    class aggregate,generator,html,exports future
    class qc_report,validation_report,candidate_report,pi_report,handoff_report,pdf_output,tsv_output reporting
```

## Design principles

* Core preprocessing should produce validated reusable artifacts.
* Assay modules should contain assay-specific scientific logic.
* Reporting should consume standardized artifact indexes rather than guessing file paths.
* Artifact schemas and read-only adapters should precede native emitter
  retrofits.
* Missing, failed, incomplete, and externally unavailable evidence should be
  represented explicitly, never omitted by glob discovery.
* Operational/QC reports may describe computational evidence. Candidate
  reports may consume an exploratory review record only when they render that
  state and limitations explicitly. Step `09c` rejects the reserved
  `biological_interpretation_ready` state until a separate approved policy
  branch unlocks its exit criteria.
* Report generation never establishes computational validation, scientific
  review completion, or biological truth.
* Public datasets should enter through the same manifest/config/provenance model as lab-generated data.
* Invalid states should be refused loudly, especially missing contrasts, missing replicate structure, missing orientation policy, or inconsistent strandedness assumptions.
* Strand/orientation interpretation should stay explicit and PI-approved.

The current Step `08` reproduction uses `orientation_policy=legacy_provisional_v1`: `FWD_like` selects compatible `+` transcripts and complements genomic REF/ALT into RNA-normalized alleles, while `REV_like` selects compatible `-` transcripts and retains genomic REF/ALT. This is an implemented legacy-preservation contract, not a biologically validated policy or a future generalized module interface.

Activated local packages (Step `09b1` is complete; Step `09c` is implemented
and synthetic-fixture-tested locally; `artifact-schema-v1` and every later
package remain unimplemented until their own branches; dependency order
fixed):

```text
step-09b1-real-r-fixes
-> step-09c-scientific-validation
-> artifact-schema-v1
-> artifact-adapters-v1
-> artifact-run-summary
-> report-html-v1
-> report-exports-v1
-> post09-runtime-preflight
-> post09-reference-provenance
-> post09-storage-inventory-retention
-> post09-validation-report-00a
-> post09-validation-report-00b
-> post09-validation-report-00c
-> post09-validation-report-01
-> post09-validation-report-02
-> post09-validation-report-02b
-> post09-validation-report-03
-> post09-validation-report-04
-> post09-validation-report-05
-> post09-validation-report-06
-> post09-validation-report-07
-> post09-validation-report-08
-> post09-validation-report-09
```

The preflight, reference inventory, and storage inventory are read-only; no
automatic installation, repair, or cleanup is implied. Each step validator
uses explicit inputs and its own branch; no generic dispatcher or job array is
part of this sequence. Analysis config, module extraction, generalized
orchestration, public-data ingestion, and broad refactors remain deferred.

When remote work resumes after `post09-validation-report-09`, promotion remains
upstream-sequential through `validate-step-07`, `validate-step-08`,
`validate-step-09`, and `validate-step-09c-scientific-evidence`, followed only
by targeted reruns. Every remote evidence branch regenerates the structured
run summary and reports after evidence inspection.

## Implementation-boundary note

The local R environment, `step-09b1-real-r-fixes`, and Step `09c` are
implemented at this boundary. Environment/restore checks, both Step `08` and
Step `09` semantic real-R suites, and the Step `09c` Python/shell fixtures pass
locally; there is no production Step `07`-`09` or Step `09c` review evidence
and no downstream cluster proof. `artifact-schema-v1` is next, and the
remaining activated packages above are plans, not runnable commands. Reports
are immediate work, but no generated report may be presented as production
evidence or biological interpretation. Do not preempt the branch sequence
with remote validation, generic dispatchers, arrays, broad helper extraction,
automatic R-package installation in compute wrappers, cleanup/lock deletion,
report globbing/recomputation, moved compute CLIs, or public-data import.
