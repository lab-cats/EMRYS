# NORAD / CSU HPC RNA-seq Workflow

This repository contains code, tests, documentation, and SLURM job wrappers for a NORAD / PUM1 / rABE-related Novogene Remora RNA-seq workflow.

The project rebuilds a hardcoded legacy RNA-editing/RNA-seq workflow into maintainable research software. The rebuilt pipeline is manifest-driven, local-first, SLURM-scaled, and dry-run-first for:

* local development on macOS
* full-scale execution on CSU's SLURM cluster
* RNA-seq preprocessing
* strandedness/orientation inference
* downstream RNA-editing / variant-like site calling

The uploaded legacy workflow is treated as a protocol reference, not as production code. Local implementation stages use descendant branches, focused and repository-wide tests, a separate documentation-only commit, and a clean push gate. Runtime promotion remains upstream-first through SLURM dry-run, execute, output inspection, and evidence docpatches.

A decoupled artifact, run-summary, and HTML/PDF reporting layer is now in the
approved immediate local implementation sequence. `artifact-schema-v1` is
implemented locally at `5f4d3b4`, `artifact-adapters-v1` is implemented
locally at `4dbd32d`, `artifact-run-summary` is implemented locally at
`209bb19`, and `report-html-v1` is implemented locally at `117ba26`. Together
they define versioned contracts, build a dry-run-first explicit-input artifact
transaction, assemble its canonical JSON plus deterministic TSV/QC views, and
render that JSON as one self-contained, script-free HTML report without
rerunning computation or changing native pipeline outputs.

The pinned Quarto `1.9.38` restore and HTML renderer have 65 focused tests
passing with the real pinned renderer required. The complete Python gate has
`277 passed, 1 skipped`; the one expected skip is the opt-in real-Quarto test,
which `make report-test` executes without skipping. No production artifact
index, run summary, or report has been built. PDF, exported report TSVs, and
the final report receipt remain unimplemented. The next descendant is
`report-html-v1a-report-table-approvals`, followed by `report-exports-v1`.

## Current Status

Steps `00a`-`00c` are cluster-proven reference prep. Steps `01`-`06` are
cluster-proven across all six samples. Step `06` preserves the legacy
read-orientation split without claiming biological strand interpretation.
Step `07` is implemented locally and locally tested with mocked bcftools, but
no Step `07` cluster dry-run or execute evidence has been inspected.

The Step `09b` local-runtime package installed the official signed and
notarized Apple-silicon CRAN R `4.6.1` package after checking its published
SHA-1
`fc9f4ada15589e8e037b9bf05563d21e97181635` and installer signature. The
repository now has an opt-in `renv` `1.2.3` environment pinned to Bioconductor
`3.23`, with the eight direct Step `08` namespaces and their dependency
closure locked. Normal restore, an empty cache-disabled binary restore,
namespace loading, `BiocManager::valid()`, `renv::status()`, and headless PDF
creation pass locally.

The `step-09b1-real-r-fixes` package is implemented at `eae5eca`. Both
semantic real-R suites now pass without `SKIP` under the guarded local
environment. Step `08` already rejected overlapping partition selectors; a
generic negative-fixture message had misattributed the later failure. The
actual engine defect was silent coercion of malformed `FORMAT/DP`,
`FORMAT/AD`, and `INFO/AD` lexemes during semantic VCF parsing. Step `08` now
streams a raw-count preflight before `VariantAnnotation`, and its fixtures
assert the expected failure reason. Step `09` now checks PDF EOF signatures as
raw bytes without locale-sensitive text conversion. No Step `07`-`09` cluster
or production evidence was created, the CSU batch-visible R environment
remains unresolved, and Steps `07`-`09` are not cluster-proven.

Step `09c` is implemented locally at `b674a31`. Its explicit-input Python/shell
package validates a complete Step `08`/`09` transaction plus declared
scientific-review evidence and publishes 13 TSVs with the review summary last.
Dry-run, atomic publication, rollback, lock/cleanup, hash mutation, reserved
state, incomplete evidence, and exploratory-state behavior are fixture-tested.
This is local synthetic evidence only: no completed production scientific
review is recorded or supported by inspected evidence, and biological
interpretation readiness remains unavailable.

The `artifact-schema-v1` package is implemented locally at `5f4d3b4`. It
tracks five schema files total (one shared common schema plus four public
Draft 2020-12 record schemas), a 67-row synthetic explicit physical-artifact
inventory, a read-only contract validator, and valid synthetic fixtures.
All 58 current focused artifact-contract tests pass.

The `artifact-adapters-v1` package is implemented locally at `4dbd32d`. Its
49 registered read-only adapters cover the 67 explicit Step `00a`-`09c`
inventory rows, and all 50 focused adapter tests pass. The suite validates
native receipt/summary relationships, explicit missing and incomplete states,
stable output ordering, binary structure where applicable, immutable run
identity, revisionable inventory attempts, and receipt-last rollback
publication. This is synthetic local fixture evidence only: no production
source has been inspected or indexed, and no production run summary, report,
runtime/cluster evidence, completed production science review, or biological
readiness was generated.

The `artifact-run-summary` package is implemented locally at `209bb19`. Its
dry-run-first builder consumes one exact complete adapter receipt and an
optional exact Step `09c` review-summary path, validates the complete
records/index/receipt transaction, and publishes canonical run-summary JSON,
a deterministic artifact TSV view, a deterministic QC TSV view, and a
receipt last. It preserves every expected scope and explicit
missing/incomplete/failed state without promoting computational or scientific
status. All 39 focused tests pass on synthetic fixtures. No production adapter
transaction or run summary has been created, and no production report,
runtime/cluster evidence, completed production science review, or biological
readiness was generated.

| Step / package | Purpose | Status |
| -------------- | ------- | ------ |
| `00a` | Build Novogene STAR index | cluster-proven |
| `00b` | Convert GTF to BED12 for RSeQC | cluster-proven |
| `00c` | GATK reference sidecars / reference FASTA index and sequence dictionary | cluster-proven |
| `01` | STAR alignment | complete and cluster-proven across all six samples |
| `02` | Canonical sorted/read-group/indexed BAM | hardened and cluster-proven across all six samples |
| `02b` | BAM QC with samtools | implemented and refreshed across all six final hardened Step 02 BAMs |
| `03` | Infer strandedness/orientation with RSeQC | cluster-proven across all six samples |
| `04` | Picard MarkDuplicates | cluster-proven across all six samples |
| `05` | SplitNCigarReads | implemented and cluster-proven across all six samples |
| `06` | read-orientation BAM split | cluster-proven across all six samples |
| `07` | cohort mpileup by declared partition and mechanical orientation | implemented locally; mocked-bcftools tests pass; runtime and cluster validation pending; not cluster-proven |
| `08` | deterministic VCF preprocessing and annotation | implemented locally; shell/fake-R and guarded real-R suites pass; raw count lexemes are preflighted before semantic parsing; cluster validation pending; not cluster-proven |
| `09` | paired CMH editing-site calling | implemented locally; shell/fake-R and guarded real-R suites pass; PDF fixture validation is locale-independent and byte-based; cluster validation pending; not cluster-proven |
| `09c` | explicit scientific-evidence validation and review summary | implemented locally at `b674a31`; dry-run, Python, and shell fixture suites pass; production evidence/review and cluster validation are unavailable; does not establish biological interpretation readiness |
| `artifact-run-summary` | canonical structured report input and deterministic TSV/QC views | implemented locally at `209bb19`; 39 focused synthetic-fixture tests pass; no production summary or validation claim |
| `report-html-v1` | static self-contained HTML rendering from one canonical run summary | implemented locally at `117ba26`; 65 focused tests pass with pinned Quarto `1.9.38`; no production report or validation claim |

### Local Runtime, Scientific Review, Reporting, And Validation Roadmap

The approved descendant history is:

```text
step-09-cmh
└── step-09a-roadmap-docpatch
    └── step-09b-local-r-runtime
        └── step-09b1-real-r-fixes       # local fixes and real-R acceptance complete
            └── step-09c-scientific-validation  # implemented and fixture-tested locally
                └── artifact-schema-v1          # implemented and focused-tested locally
                    └── artifact-adapters-v1    # implemented and focused-tested locally
                        └── artifact-run-summary # implemented and focused-tested locally
                            └── report-html-v1   # implemented and focused-tested locally
                                └── report-html-v1a-report-table-approvals # next
                                    └── report-exports-v1
                                        └── post09-runtime-preflight
                                            └── post09-reference-provenance
                                                └── post09-storage-inventory-retention
                                                    └── post09-validation-report-00a
                                                        └── post09-validation-report-00b
                                                            └── post09-validation-report-00c
                                                                └── post09-validation-report-01
                                                                    └── post09-validation-report-02
                                                                        └── post09-validation-report-02b
                                                                            └── post09-validation-report-03
                                                                                └── post09-validation-report-04
                                                                                    └── post09-validation-report-05
                                                                                        └── post09-validation-report-06
                                                                                            └── post09-validation-report-07
                                                                                                └── post09-validation-report-08
                                                                                                    └── post09-validation-report-09
```

The local R runtime is opt-in: `.Rprofile` activates the project library only
when `NORAD_USE_RENV=1`. Existing compute and SLURM wrappers never install or
bootstrap R packages. Use `RSCRIPT_BIN=<explicit executable>` with
`make r-restore`, `make r-check`, and `make local-real-r-test`.

`step-09c-scientific-validation` now validates explicit evidence and publishes
a synthetic-fixture-tested evidence package; it does not rerun CMH statistics
or claim production review. Its allowed science states are
`evidence_incomplete` and `science_review_complete_exploratory`.
`biological_interpretation_ready` is reserved and rejected until a separately
approved policy branch unlocks its exit criteria.

Run-summary and reporting work is immediate, not deferred. The artifact
schema, read-only adapter indexer, canonical run-summary builder, and
self-contained script-free HTML renderer are implemented from explicit
contracts and synthetic fixtures. The normal run-summary producer currently
emits an empty `approved_report_tables` list, so
`report-html-v1a-report-table-approvals` is the next branch; it will add the
explicit producer-side authorization path before `report-exports-v1` adds
PDF, exported TSVs, and the report receipt. Summary, report, or index
generation will never be evidence of computational or biological validation.

The reporting slice is followed by read-only runtime, reference-provenance,
and storage/retention tooling, then one explicit validator branch for every
pipeline step from `00a` through `09`. Remote work is paused. After the final
local validator branch, remote promotion resumes as
`validate-step-07` -> `validate-step-08` -> `validate-step-09` ->
`validate-step-09c-scientific-evidence` -> `post09-targeted-reruns`, with a
fresh evidence/report docpatch at every gate.

### Step 07 Local Implementation

Implemented entry points:

```text
scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh
jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
tests/shell/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh
```

Partition manifests:

```text
configs/step_07_partitions.primary_contigs.tsv  # approved correction universe: 1-22, X, Y, MT
configs/step_07_partitions.pilot.tsv            # one-row pilot: 1:1-100000
configs/step_07_partitions.example.tsv          # illustrative schema/example
```

One invocation selects one declared partition, passes every sample BAM to a cohort-wide mpileup in manifest order, and produces both neutral mechanical orientations:

```text
results/mpileup/<cohort>/<partition>/
  <cohort>.<partition>.FWD_like.mpileup.vcf
  <cohort>.<partition>.REV_like.mpileup.vcf
  <cohort>.<partition>.step07_outputs.tsv
```

The receipt is published last as the output-set commit marker; downstream stages must require and validate it rather than globbing VCFs. Step `07` is dry-run-first, validates declared inputs and output structure, and uses owned locks, run-token scratch paths, validation-before-publication, cleanup, and rollback. These claims are locally tested with a fake bcftools executable only. See `docs/operations/RUNBOOK.md` for the exact CLI, SLURM variables, and future cluster-promotion sequence.

### Step 08 Local Implementation

Implemented entry points and tests:

```text
scripts/step_08_vcf_preprocessing.sh
scripts/step_08_vcf_preprocessing.R
jobs/step_08_vcf_preprocessing.slurm
tests/shell/test_step_08_vcf_preprocessing.sh
tests/r/run_step_08_vcf_preprocessing_tests.sh
tests/r/test_step_08_vcf_preprocessing.R
```

Step `08` consumes exactly the declared partition-manifest cross-product with
`FWD_like` and `REV_like`; it never discovers VCFs by glob. It verifies the
Step `07` receipts, hashes, paths, record counts, and exact manifest-ordered
sample columns before using `VariantAnnotation`, `GenomicRanges`, and
`rtracklayer` to expand alternate alleles and annotate the Novogene GTF.
Symbolic and non-SNV alleles are counted and excluded.

The orientation mapping is explicitly provisional:

```text
orientation_policy=legacy_provisional_v1
FWD_like -> compatible + transcripts -> complement genomic REF/ALT
REV_like -> compatible - transcripts -> retain genomic REF/ALT
```

This is legacy compatibility behavior, not a biologically validated strand
policy. Step `08` publishes a validated three-file transaction:

```text
results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv
results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv
results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv
```

The wide sites table has fixed metadata followed by manifest-ordered
`DP__<sample>`, `AD__<sample>`, and `AF__<sample>` columns. The inputs receipt
is published last as the commit marker. Owned locks, stable input hashes,
run-token temporary paths, validation-before-publication, cleanup, and rollback
protect the output set. The shell/fake-R suite tests that wrapper contract.
The Step `08` semantic suite now passes without `SKIP` under the guarded local
R environment. Its partition-overlap validator was already working; generic
failure text had hidden a later malformed-count case. Commit `eae5eca` adds
streaming lexical validation before `VariantAnnotation`: `FORMAT/DP` must have
one token; a `FORMAT/AD` or present `INFO/AD` value may be a single `.` when
the entire vector is missing, but otherwise must have one token per
reference-plus-alternate allele. Every token must be `.` or a non-negative
integer. This is local fixture evidence, not production or cluster evidence.

### Step 09 Local Implementation

Implemented entry points, tests, and reference pairing:

```text
scripts/step_09_cmh_editing_site_calling.sh
scripts/step_09_cmh_editing_site_calling.R
jobs/step_09_cmh_editing_site_calling.slurm
tests/shell/test_step_09_cmh_editing_site_calling.sh
tests/r/run_step_09_cmh_tests.sh
tests/r/test_step_09_cmh_editing_site_calling.R
configs/step_09_pairs.NORAD_EV_PUM1.tsv
```

The full sample manifest is the only runtime pairing source. Its optional
`replicate` column becomes required for Step `09`: each replicate must contain
exactly one control and one treatment, the two conditions must have identical
replicate sets, and at least two strata are required. The tracked Step `09`
pairing file documents the approved `2`, `3`, and `4` relationships only; it is
not a runtime overlay, and pairing is never inferred from sample names. The
same replicate-bearing sample manifest must be used before Step `07` so its
hash propagates through the complete Steps `07`-`09` chain.

Step `09` validates the Step `08` sites table and complete input-receipt contract,
runs two-sided continuity-corrected paired CMH tests with treatment-relative-
to-control common odds ratios, and applies BH once across all successfully
tested target candidates before call-level depth/effect filtering. Defaults
are EV control, PUM1 treatment, RNA `A>G`, per-sample depth at least `1`, mean
analysis depth strictly greater than `50`, FDR strictly less than `0.05`,
common odds ratio strictly above `1.2` or below `1/1.2`, and absolute
treatment-control fraction difference strictly above `0.005`. Optional
background filtering is disabled unless an explicit, distinct condition is
provided; EV is never repurposed as a missing no-dox cohort.

One validated transaction publishes four TSVs and two 7-by-5-inch PDFs:

```text
results/editing/<analysis>/<analysis>.cmh_all_sites.tsv
results/editing/<analysis>/<analysis>.cmh_significant_sites.tsv
results/editing/<analysis>/<analysis>.cmh_summary.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.tsv
results/editing/<analysis>/<analysis>.mutation_spectrum.pdf
results/editing/<analysis>/<analysis>.depth_delta.pdf
```

The all-sites table retains missing, low-coverage, degenerate, and non-target
candidates with explicit statuses and preserves
`orientation_policy=legacy_provisional_v1`; that policy is not biologically
validated. The summary is published last as the six-output transaction commit
marker. Owned locks, immutable input hashes, run-token temporary and backup
paths, exact output reconciliation, cleanup, and rollback protect the set. The
Step `09` semantic suite now passes without `SKIP` under real R after its PDF
EOF fixture was changed to search raw bytes rather than locale-sensitive text.
This is local fixture evidence and does not establish production runtime or
cluster proof.

### Step 09c Local Scientific-Validation Tooling

Implemented entry points, example contracts, and active tests:

```text
scripts/step_09c_scientific_validation.sh
scripts/step_09c_scientific_validation.py
configs/step_09c_review_plan.example.tsv
configs/step_09c_evidence_manifest.example.tsv
configs/step_09c_evidence_schemas/
tests/fixtures/step09c/build_fixture.py
tests/test_step_09c_scientific_validation.py
tests/shell/test_step_09c_scientific_validation.sh
```

Public dry-run-first interface:

```bash
scripts/step_09c_scientific_validation.sh \
  --review-id REVIEW_ID \
  --sample-manifest SAMPLE_MANIFEST \
  --partition-manifest PARTITION_MANIFEST \
  --step08-sites STEP08_SITES \
  --step08-inputs STEP08_INPUTS \
  --step08-summary STEP08_SUMMARY \
  --step09-analysis-dir STEP09_ANALYSIS_DIR \
  --review-plan REVIEW_PLAN \
  --evidence-manifest EVIDENCE_MANIFEST \
  --output-root results/scientific_validation

# add --execute only to publish
```

Execute mode validates the explicitly named Step `08` and Step `09`
transactions, evidence paths/hashes/row counts, review policy, status
coherence, candidate/replicate/audit relationships, and immutable inputs. It
publishes one rollback-protected 13-file transaction:

```text
results/scientific_validation/<review_id>/
  <review_id>.step09c_review_plan.tsv
  <review_id>.step09c_evidence_index.tsv
  <review_id>.step09c_orientation_locus_audit.tsv
  <review_id>.step09c_annotation_audit.tsv
  <review_id>.step09c_qc_funnel.tsv
  <review_id>.step09c_replicate_effects.tsv
  <review_id>.step09c_sensitivity_matrix.tsv
  <review_id>.step09c_leave_one_pair_out.tsv
  <review_id>.step09c_candidate_selection.tsv
  <review_id>.step09c_candidate_adjudication.tsv
  <review_id>.step09c_decisions.tsv
  <review_id>.step09c_limitations.tsv
  <review_id>.step09c_review_summary.tsv
```

The summary is published last as the transaction marker. Missing and
incomplete evidence remain explicit. `science_review_complete_exploratory`
requires coherent completed evidence and decisions but remains provisional;
`biological_interpretation_ready` is always rejected by this version. Local
completion means implemented and synthetic-fixture-tested, not production
scientific review, cluster proof, or biological validation.

The normalized review contract retains human reviewer/owner names while
keeping machine IDs and policy versions constrained. Complete/incomplete
source evidence requires a date; analysis sets are disjoint and evidence
categories have explicit analysis ownership. Pending decisions cannot cite
support; recorded decisions require complete/not-applicable support and
consistent rerun fields. Passed/failed/proven computational claims require
their defined complete evidence roles; runtime and cluster roles additionally
require explicit underlying paths/hashes. Blocked/not-run states are not proof
and must not be given invented claim evidence. The tracked example declares
`local_test_status=not_run` because it attaches no local-test evidence; that
review declaration does not contradict the repository tooling's passing
fixtures.

### Artifact Schema V1 Local Contract

Implemented contract files and tests:

```text
schemas/artifacts/v1/common.schema.json
schemas/artifacts/v1/artifact_record.schema.json
schemas/artifacts/v1/scientific_review_record.schema.json
schemas/artifacts/v1/run_summary.schema.json
schemas/artifacts/v1/report_receipt.schema.json
configs/artifact_inventory.example.tsv
scripts/validate_artifact_contracts.py
tests/fixtures/artifact_schema_v1/valid/
tests/test_artifact_schema_contracts.py
```

Validate the five-schema set and the 67-row synthetic explicit physical
inventory with:

```bash
.venv/bin/python scripts/validate_artifact_contracts.py \
  --check-schemas \
  --inventory configs/artifact_inventory.example.tsv

.venv/bin/python -m pytest -q tests/test_artifact_schema_contracts.py
```

The four public document types are `artifact-record`,
`scientific-review-record`, `run-summary`, and `report-receipt`; the shared
common schema is loaded with them. Artifact records remain schema `1.0.0`.
The run-summary implementation corrected the closed scientific-review,
run-summary, and report-receipt contracts to `1.1.0` so retained human review
context, decision provenance, limitations, and report input versions are
explicit rather than silently changing `1.0.0`. The validator is
explicit-input-only and read-only. It validates schema, record, inventory,
run/attempt, path/hash, typed evidence, rollup, and reserved-science-state
consistency, but it does not discover or inspect production pipeline outputs.
Artifact-index publication is implemented by `artifact-adapters-v1`, and
canonical run-summary publication is implemented by
`artifact-run-summary`. Static HTML rendering is implemented by
`report-html-v1`; report-table authorization and PDF/TSV/receipt export remain
later packages.

The current 58 focused tests are synthetic local contract evidence. They do not
establish production artifact availability, runtime validation, a cluster
dry-run or cluster proof, scientific-review completion, biological readiness,
or report generation.

### Artifact Adapters V1 Local Implementation

Implemented files and tests:

```text
configs/artifact_run_contract.example.json
scripts/build_artifact_index.py
tests/fixtures/artifact_adapters_v1/build_fixture.py
tests/test_artifact_adapters.py
```

The dry-run-first interface is:

```bash
.venv/bin/python scripts/build_artifact_index.py \
  --run-id RUN_ID \
  --run-contract RUN_CONTRACT_JSON \
  --inventory INVENTORY_TSV \
  --output-root OUTPUT_ROOT

# add --execute only to publish
```

The strict run-contract JSON contains `run_contract_sha256` plus the five
identity components: sample-manifest hash, reference-contract hash,
partition-manifest hash, primary-analysis ID, and primary-analysis-policy
hash. Those values bind `run_id`. An inventory-only revision may create a new
`adapter_attempt_id` under the same run; changing an immutable identity
component requires a new `run_id`.

Execute mode publishes:

```text
results/artifacts/<run_id>/
  records/<artifact_id>.json
  <run_id>.artifacts.tsv
  <run_id>.artifact_receipt.tsv
```

The receipt is published last. Its complete transaction state means that the
record set and index were reconciled and committed; individual records may
still explicitly report missing, incomplete, failed, externally unavailable,
or unknown evidence. Adapters never discover inputs by glob, invoke analysis
engines, or infer runtime/cluster/scientific proof from tool presence or prose.
All 50 focused adapter tests and all 108 combined schema/adapter tests pass on
synthetic fixtures. No production adapter transaction exists.

### Artifact Run Summary Local Implementation

Implemented files and tests:

```text
scripts/build_run_summary.py
scripts/_run_summary_science.py
tests/fixtures/artifact_run_summary_v1/build_fixture.py
tests/test_artifact_run_summary.py
```

The dry-run-first interface is:

```bash
.venv/bin/python scripts/build_run_summary.py \
  --run-id RUN_ID \
  --artifact-receipt ARTIFACT_RECEIPT \
  --output-root OUTPUT_ROOT \
  [--science-review-summary REVIEW_SUMMARY_TSV]

# add --execute only to publish
```

`ARTIFACT_RECEIPT` must be the exact complete receipt inside the declared
`OUTPUT_ROOT/<run_id>/` adapter transaction. The optional science-review
summary is also exact-input-only; it is never discovered automatically.
Dry-run validates inputs and prints the resolved summary plan without
creating stable outputs, locks, or scratch paths. Execute mode publishes:

```text
results/artifacts/<run_id>/
  <run_id>.run_summary.json
  <run_id>.run_summary.tsv
  <run_id>.qc_summary.tsv
  <run_id>.run_summary_receipt.tsv
```

The receipt is published last. Canonical JSON is the report layer's single
structured entry point; the TSVs are deterministic views of its artifact and
QC data. The builder validates run identity, adapter transaction-member
hashes, inventory and artifact ordering, attempt lineage, prior summary
transactions, and exact optional Step `09c` evidence. It uses an owned regular
lock, run-token temporary/backup paths, validation-before-publication,
rollback/recovery, transaction-member input rechecks, and output-directory
identity checks. It carries native Step `00`-`09` source hashes recorded by
the adapter but does not rehash those native sources. A successful
summary records existing evidence; it never promotes local, runtime, cluster,
scientific, or biological status.

All 39 focused run-summary tests pass. This is synthetic/local fixture
evidence only. No production artifact transaction or summary has been built.

### Static HTML Report V1 Local Implementation

Implemented files and tests:

```text
scripts/restore_quarto.py
scripts/render_run_report.sh
scripts/render_run_report.py
reports/run_report.qmd
reports/run_report.css
tests/fixtures/report_html_v1/approved_candidates.tsv
tests/test_quarto_restore.py
tests/test_report_html_v1.py
tests/shell/test_render_run_report.sh
```

Restore the exact local renderer deliberately:

```bash
make quarto-restore
```

This installs Quarto `1.9.38` under ignored
`.tools/quarto/1.9.38/` storage only after the official macOS archive matches
SHA-256
`47089a5020cfb41981ba0d4b46e110edfa608722aea45ef248e14efba6d6b18a`.
The earlier roadmap digest was incorrect. Report rendering never downloads or
installs dependencies.

The HTML-only public interface is:

```bash
scripts/render_run_report.sh \
  --run-summary results/artifacts/RUN_ID/RUN_ID.run_summary.json \
  --output-root results/reports \
  --quarto-bin .tools/quarto/1.9.38/bin/quarto \
  [--formats html] \
  [--execute]
```

Dry-run is the default and creates no output, lock, or scratch path. The shell
wrapper prefers the repository `.venv/bin/python`, falls back to `python3`,
and honors an explicit authoritative `PYTHON_BIN_OVERRIDE`. Execute mode
validates one canonical run-summary `1.1.0` JSON plus only the TSVs explicitly
authorized in its `approved_report_tables` records, invokes Quarto with
analysis execution disabled, and atomically publishes:

```text
results/reports/<run_id>/<run_id>.run_report.html
```

The current output is a single self-contained, script-free HTML file with no
external active assets. It preserves the required scientific-state banner,
uses “CMH-ranked candidates,” and records report/input provenance without
promoting computational or scientific state. PDF, exported summary TSVs, and
the report receipt are not implemented on this branch.

The 65-test focused `make report-test` target passes with real pinned Quarto
required, including deterministic rerenders. The complete Python gate reports
`277 passed, 1 skipped`; the one expected skip is the opt-in real-Quarto test
that `make report-test` runs. Shell tests, both guarded real-R suites, and
`r-check` also pass. These are synthetic/incomplete local fixtures only. No
production run summary or report has been rendered, and there is no new
runtime, cluster, scientific-review, or biological-readiness evidence.

The existing run-summary producer emits `approved_report_tables: []`.
`report-html-v1a-report-table-approvals` is therefore the next descendant and
will add an explicit authorization-producing contract before
`report-exports-v1`; operators must not hand-edit run-summary JSON to expose
tables.

For demo details, start with `docs/demo/DEMO_WALKTHROUGH.md`, then use `docs/architecture/ARCHITECTURE.md` for the visual pipeline/dataflow architecture, `docs/demo/PI_DEMO_REPORT.md` for preliminary validation and QC summary, `docs/design/PIPELINE_PLAN.md` as the tactical map, `docs/operations/HANDOFF.md` for current state, `docs/operations/RUNBOOK.md` for safe inspection commands, the operations troubleshooting guide for known failure modes, and `TODO.md` for the next gates. Standalone Mermaid sources live under `docs/architecture/diagrams/`, including current pipeline/reliability diagrams and `future_roadmap_sequence.mmd`.

Architecture/design docs:

- `docs/architecture/FUTURE_ARCHITECTURE.md` - deferred modular target architecture for core preprocessing, analysis modules, and reporting.

## Cohort And Key Results

Known samples:

```text
ABE_EV_2
ABE_EV_3
ABE_EV4
ABE_PUM1_2
ABE_PUM1_3
ABE_PUM1_4
```

Conditions:

```text
EV:   ABE_EV_2, ABE_EV_3, ABE_EV4
PUM1: ABE_PUM1_2, ABE_PUM1_3, ABE_PUM1_4
```

All six libraries are paired-end and reverse-stranded / first-strand-style by Step `03`. Tool-specific examples that often correspond to this orientation are:

```text
featureCounts -s 2
HTSeq --stranded=reverse
Salmon paired-end convention ISR
```

Do not treat those options as universally interchangeable without naming the tool.

## Biological And Computational Goal

This repository supports RNA-seq / RNA-editing workflow reconstruction for NORAD / PUM1 / rABE-related analysis.

The intended workflow is:

```text
FASTQ(.gz)
    ->
STAR alignment
    ->
canonical sorted/read-group/indexed BAM
    ->
BAM QC
    ->
RSeQC strandedness/orientation inference
    ->
Picard duplicate marking
    ->
GATK reference sidecar validation
    ->
GATK SplitNCigarReads
    ->
read-orientation BAM splitting
    ->
bcftools mpileup
    ->
VCF preprocessing
    ->
CMH/editing-site calling
    ->
scientific evidence and decision gate
```

This is not currently a simple gene-count differential-expression workflow. The downstream reference workflow points toward RNA-editing / variant-like site analysis.

Step `06` splits Step `05` BAMs into `FWD_like` and `REV_like` read-orientation groups using the legacy mechanical flag groups and writes an orientation counts TSV. These labels are not biological sense/antisense claims.

The final arrow is a review gate, not another computational pipeline step.
Cluster execution can produce CMH-ranked candidate sites, but it does not by
itself validate the provisional orientation mapping or establish biological
truth.

## Development Model

The intended development loop is:

```text
create the stage branch from the latest clean docpatched predecessor
    ->
implement only that stage
    ->
run focused and complete local validation
    ->
commit implementation and tests
    ->
reread project docs and perform the repository-wide docpatch
    ->
commit documentation separately, require a clean worktree, and push
    ->
create the next descendant local stage when explicitly approved
    ->
promote runtime stages upstream-first through SLURM dry-run and execute
    ->
inspect logs and outputs, then commit the validation docpatch
    ->
proceed to next step
```

The cluster login node should not be used for heavy computation. It is for editing, Git operations, small file transfers, light checks, file inspection, and submitting jobs.

Full analysis should run through SLURM jobs in `jobs/`.

## Quick Start: Local Development

Clone the repo:

```bash
git clone https://github.com/Glen-Cocoa/norad.git
cd norad
```

Create and activate a local Python environment if needed:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Record dependency or tooling changes in `requirements.txt`, `environment.yml`, or another project setup document rather than leaving them implicit.

Restore and check the opt-in local R environment with the explicit CRAN R
`4.6.1` executable:

```bash
NORAD_USE_RENV=1 make r-restore \
  RSCRIPT_BIN=/usr/local/bin/Rscript
NORAD_USE_RENV=1 make r-check \
  RSCRIPT_BIN=/usr/local/bin/Rscript
NORAD_USE_RENV=1 make local-real-r-test \
  RSCRIPT_BIN=/usr/local/bin/Rscript
```

The repository-local library is activated only when `NORAD_USE_RENV=1`.
`r-restore` is an explicit setup action; workflow and SLURM entry points never
install packages.

Restore the pinned local Quarto renderer once before report testing:

```bash
make quarto-restore
```

This setup target is separate from rendering; report commands never install
their own dependencies.

Run the local validation gate:

```bash
git diff --check
bash -n scripts/*.sh
bash -n jobs/*.slurm
.venv/bin/python -m compileall scripts tests
.venv/bin/python -m pytest
make shell-test
NORAD_USE_RENV=1 make r-check RSCRIPT_BIN=/usr/local/bin/Rscript
NORAD_USE_RENV=1 make local-real-r-test RSCRIPT_BIN=/usr/local/bin/Rscript
make report-test
git status --short
git diff --name-status
```

Bare `python` is absent on the current workstation, so the passing Python gate
uses the existing `.venv`. At the `report-html-v1` implementation boundary,
the complete Python suite reports `277 passed, 1 skipped`; the one expected
skip is the optional real-Quarto test. `make report-test` requires the pinned
renderer and passes all 65 focused tests without that skip. All shell tests,
both Step `08` and Step `09` real-R runners, the aggregate local R target, and
the R environment check also pass. These checks use synthetic fixtures and do
not constitute production input inspection or publication, a production run
summary/report, cluster validation, production scientific-review completion,
or biological readiness.

Shortcut for the Makefile-covered checks:

```bash
make all-checks
```

`make all-checks` now includes `make report-test`, so run
`make quarto-restore` first.

Validate the example manifest:

```bash
python scripts/validate_manifest.py \
  --manifest samples.example.tsv
```

To also check file existence:

```bash
python scripts/validate_manifest.py \
  --manifest samples.example.tsv \
  --base-dir . \
  --check-files
```

## Quick Start: Cluster Execution

On the cluster:

```bash
cd ~/norad
git pull
git status --short
mkdir -p logs
```

Run a dry-run job first:

```bash
sbatch jobs/<step>.slurm
```

Inspect the job:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS,NodeList
tail -120 logs/<log-prefix>-<JOBID>.out
tail -120 logs/<log-prefix>-<JOBID>.err
```

If the dry-run looks correct, run execute mode:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

Then inspect outputs before proceeding.

## Operator Checklist

- **Default dry-run:** Workflow shell scripts and SLURM wrappers default to dry-run. Submit a dry-run first to verify resolved inputs, printed commands, and logs.
- **Submit execute jobs explicitly:** Use `EXECUTE=1` when ready, e.g.:

```bash
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/<step>.slurm
```

- **Script-level execution flag:** Workflow shell scripts use `--execute` to run tool commands; include all required step arguments when invoking a script directly.
- **Validation locations:** Use `docs/operations/RUNBOOK.md` for per-step dry-run/execute checks, `docs/design/PIPELINE_PLAN.md` for step status, and the design decisions log for execution policy.
- **Quick checks after execute:** Confirm expected outputs under `results/`, inspect SLURM logs under `logs/`, and use `sacct` for job state.

## Repository Layout

```text
scripts/        # Python, shell, and R scripts
jobs/           # SLURM job wrappers
tests/          # local tests and pending test plans
configs/        # optional config files
data/test/      # tiny local test fixtures only
data/raw/       # large/raw data symlinks; not committed
data/full/      # optional full-scale data paths; not committed
results/        # generated outputs; not committed
logs/           # SLURM stdout/stderr logs; not committed
docs/           # project documentation
```

Large data files and generated outputs should stay out of Git.

## Important Documentation Files

```text
docs/operations/       handoff, runbook, and troubleshooting
docs/design/           pipeline plan, questions, and decisions
docs/demo/             PI demo walkthrough and report
docs/architecture/     visual pipeline/dataflow architecture and diagrams
TODO.md                tactical next work
README.md              entrypoint / overview
```

## Data And Reference Locations

### Local repo

```text
/Users/elisteiger/dev/norad
```

### Cluster repo

```text
~/norad
/mnt/stor-pool-01/users/2609214/norad
```

### Raw data symlink on cluster

```text
data/raw/novogene_remora -> /mnt/stor-pool-01/users/2832917/Novogene_Remora_raw_data
```

FASTQs live under:

```text
data/raw/novogene_remora/01.RawData/*.fq.gz
```

### Reference files

Prepared reference files:

```text
refs/novogene_ref/genome.fa
refs/novogene_ref/genome.fa.fai
refs/novogene_ref/genome.gtf
refs/novogene_ref/genome.bed
refs/novogene_ref/genome.dict
refs/novogene_star_index/
```

Reference notes:

* Novogene-provided GRCh38-like reference.
* Chromosome names are numeric-style, for example `1`, `2`, `3`, not `chr1`, `chr2`, `chr3`.
* FASTA and GTF chromosome names match.
* STAR index was built with `sjdbOverhang=149` for 150 bp reads.
* BED12 annotation was generated from the GTF for RSeQC.
* Step `00c` formalizes GATK sidecar prep with `scripts/step_00c_prepare_gatk_reference.sh` and `jobs/step_00c_prepare_gatk_reference.slurm`; it is cluster-proven.

## Confirmed Tools On CSU

Known modules/tools:

```text
star/2.7.11b
samtools/1.19.2
bedtools/2.31.1
picard/3.1.1
python39
java/17.0.10
GATK 4.6.1.0: /cm/shared/apps/gatk/gatk-4.6.1.0/gatk
bcftools 1.21: /cm/shared/apps/cbi-soft/bcftools-1.21/bin/bcftools
```

Picard is exposed through the jar path set by the module. Step `04` validates the selected Java executable and actual runtime version before Picard starts.

RSeQC is available through the project virtual environment:

```text
.venv/bin/infer_experiment.py
```

GATK and bcftools were validated on compute node `node002`; the tool probe completed successfully with exit code `0:0`.

Resolved for local development:

```text
R 4.6.1: /usr/local/bin/Rscript
renv 1.2.3
Bioconductor 3.23
```

Still unresolved on CSU compute/batch nodes:

```text
R / Rscript
```

The local lock contains the eight direct Step `08` namespaces and their
dependency closure. A separately operator-validated batch-visible `Rscript`
and restore/package check remain required before cluster promotion. Step `09`
otherwise uses base R, including `stats`, `graphics`, and `grDevices`. The
implemented compute wrappers do not install packages or guess an R module.

## Beginner Glossary

`FASTQ` / `.fastq.gz`: raw sequencing reads. For paired-end data, `R1` is the first read and `R2` is the second read.

`SAM`: human-readable alignment format.

`BAM`: compressed binary alignment format.

`BAI`: BAM index file.

`STAR`: splice-aware RNA-seq aligner used here to align FASTQs to the reference.

`samtools`: alignment-file toolkit used for sorting, indexing, filtering, and inspecting BAMs.

`Picard`: preprocessing/QC toolkit; current use here is duplicate marking with `MarkDuplicates`.

`GATK`: genomics toolkit; Step `05` uses `SplitNCigarReads` for RNA-seq preprocessing after duplicate marking.

`R`: downstream analysis, statistics, visualization, and tables.

## Git And Data Policy

Use Git for:

* source code
* SLURM job wrappers
* configuration files
* documentation
* small safe test fixtures

Do not commit:

* FASTQ / FASTQ.GZ
* SAM / BAM / CRAM / BAI
* large TSV/CSV outputs
* logs
* results directories
* credentials or tokens
* `.env` files
* private SSH keys
* large raw reference/data files

Tiny test fixtures may be committed only if they are small, safe, and non-sensitive.
