# Demo Walkthrough

This is a short read-only path for PI demo use. It points to the current sources of truth rather than replacing them.

## 1. Demo Goal

Show that the legacy NORAD / Novogene Remora workflow has been rebuilt into a
reproducible preprocessing and paired-CMH code path, with a clear distinction
between the cluster-proven RNA-seq preprocessing boundary and the locally
implemented Steps `07`-`09`, the local Step `09c` evidence validator, and the
locally tested artifact schema, adapter-index, canonical run-summary, and
static HTML reporting layers.

Current boundary:

```text
Steps 00a-00c cluster-proven reference prep
-> Steps 01-06 cluster-proven across all six samples
-> Step 07 implemented and locally tested with mocked bcftools; no real or cluster run
-> local signed/notarized R 4.6.1 + guarded renv/Bioconductor 3.23 checks pass
-> Step 08 and Step 09 real-R suites pass locally without SKIP after eae5eca
-> Step 09c implemented and synthetic-fixture-tested locally at b674a31
-> artifact-schema-v1 implemented and locally fixture-tested at 5f4d3b4
-> artifact-adapters-v1 implemented and focused-fixture-tested at 4dbd32d
-> artifact-run-summary implemented and focused-fixture-tested at 209bb19
-> report-html-v1 implemented and focused-fixture-tested at 117ba26
-> report-html-v1a-report-table-approvals is next, then report-exports-v1
-> no production artifact index, run summary, or report exists
-> remote validation remains paused
```

## 2. Suggested 5-10 Minute Flow

1. `README.md` - project overview and current status.
2. `docs/architecture/ARCHITECTURE.md` - visual dataflow and engineering architecture.
3. `docs/demo/PI_DEMO_REPORT.md` - PI Decision Brief plus preliminary validation and QC summary.
4. `docs/design/PIPELINE_PLAN.md` - exact step contracts and validation status.
5. Operations troubleshooting guide - Step `05` `/tmp` temp-spill failure and hardening.
6. Optional terminal evidence - Step `05` / Step `06` cluster validation
   outputs, Step `07` mocked-bcftools results, and the local R environment
   checks. The Step `08`/`09` real-R suites now pass locally, but synthetic
   fixture evidence is not production, cluster, or biological output evidence.
   The Step `09c` dry-run and fixture suite may be shown only as validator
   implementation evidence, not a completed production scientific review. The
   artifact schema validator, synthetic JSON records, and explicit 67-row
   inventory may be shown as local contract evidence only. The adapter
   `--help`, dry-run, and focused synthetic fixtures may also be shown as
   implementation evidence only; they are not a production artifact index,
   run summary, or report. The run-summary `--help`, dry-run, and synthetic
   four-file fixture transaction may also be shown as implementation evidence
   only. The HTML renderer `--help`, dry-run, and real pinned-Quarto synthetic
   render may be shown as local implementation evidence. The resulting static,
   self-contained, script-free HTML is still an incomplete fixture, not a
   production report or validation result.

   Example side-effect-free adapter dry-run:

   ```bash
   .venv/bin/python scripts/build_artifact_index.py \
     --run-id RUN_ID \
     --run-contract configs/artifact_run_contract.example.json \
     --inventory configs/artifact_inventory.example.tsv \
     --output-root results/artifacts
   ```

   Only `--execute` publishes
   `results/artifacts/<run_id>/records/<artifact_id>.json`,
   `results/artifacts/<run_id>/<run_id>.artifacts.tsv`, and the receipt-last
   `results/artifacts/<run_id>/<run_id>.artifact_receipt.tsv` for this command.

   Example side-effect-free run-summary dry-run after an adapter fixture
   transaction exists:

   ```bash
   .venv/bin/python scripts/build_run_summary.py \
     --run-id RUN_ID \
     --artifact-receipt \
       results/artifacts/RUN_ID/RUN_ID.artifact_receipt.tsv \
     --output-root results/artifacts
   ```

   Only `--execute` publishes
   `<run_id>.run_summary.json`, `<run_id>.run_summary.tsv`,
   `<run_id>.qc_summary.tsv`, and receipt-last
   `<run_id>.run_summary_receipt.tsv`. Fixture outputs are not production
   evidence.

   Restore and verify the pinned local renderer, then inspect the HTML-only
   dry-run contract:

   ```bash
   make quarto-restore

   scripts/render_run_report.sh \
     --run-summary RUN_SUMMARY_JSON \
     --output-root results/reports \
     --quarto-bin .tools/quarto/1.9.38/bin/quarto
   ```

   Add `--execute` only with an explicit fixture or approved run summary. This
   stage publishes exactly
   `results/reports/<run_id>/<run_id>.run_report.html`; PDF, exported summary
   TSV, and the report receipt remain pending `report-exports-v1`. The official
   Quarto archive is checked against SHA-256
   `47089a5020cfb41981ba0d4b46e110edfa608722aea45ef248e14efba6d6b18a`.

## 3. Talk Track

- The legacy hardcoded workflow has been translated into staged, testable pipeline steps with explicit inputs and outputs.
- SLURM execution is dry-run-first, with real execution gated by explicit `EXECUTE=1`.
- Reference prep and sample preprocessing are cluster-proven through Step `06` across the six-sample cohort.
- Step `06` publishes `FWD_like` / `REV_like` mechanical read-orientation BAMs and orientation counts TSVs for all six samples.
- Step `07` is implemented locally and locally tested with mocked bcftools at commit `e68b00c`; real-bcftools and cluster validation remain pending.
- Step `08` is implemented locally at commit `90335d8` and hardened at `eae5eca`; its deterministic partition-manifest × orientation contract and wrapper reliability behavior pass shell/fake-R and guarded real-R tests. Raw DP/AD/INFO AD lexemes are checked before `VariantAnnotation`; the existing partition-overlap validator was already correct.
- Step `08` writes the wide sites table, complete input receipt, and preprocessing QC summary under `results/vcf_preprocessed/` and `results/qc/vcf_preprocessing/`; no production or cluster output is being presented.
- Step `09` is implemented locally at commit `e4371de`; shell/fake-R tests cover explicit replicate pairing, Step `08` sites/input-receipt validation, Step `09` output-contract validation, threshold forwarding, six-output publication, locks, cleanup, and rollback. Its real-R suite passes without `SKIP` after `eae5eca` made PDF EOF fixture validation raw-byte and locale-independent.
- Step `09` uses only manifest-defined EV/PUM1 replicate pairs and is designed to publish all-sites, significant-sites, summary, mutation-spectrum, and depth/delta outputs under `results/editing/<analysis>/`. These are implementation contracts, not inspected biological results.
- A real cluster failure in Step `05` was diagnosed as GATK/HTSJDK temp spill to node-local `/tmp` and hardened with project-storage temp handling.
- Biological interpretation is intentionally cautious: read-orientation labels are mechanical flag groups, and the Step `08`/`09` `orientation_policy=legacy_provisional_v1` mapping is explicitly provisional rather than biologically validated.
- The signed/notarized Apple-silicon CRAN R `4.6.1` runtime and guarded
  repository `renv`/Bioconductor `3.23` environment are installed locally.
  Namespace, lock, headless-PDF, and empty cache-disabled restore checks pass;
  compute wrappers do not install packages.
- The `step-09b1-real-r-fixes` branch is complete and pushed. Step `09c` is
  implemented at `b674a31` and fixture-tested locally. `artifact-schema-v1` is
  implemented and locally fixture-tested at `5f4d3b4`: four public Draft
  2020-12 schemas share common definitions, and an explicit inventory declares
  67 expected artifacts without glob discovery. `artifact-adapters-v1` is
  implemented at `4dbd32d`: 49 exact adapters cover those 67 rows, and 50
  focused synthetic-fixture tests pass. `artifact-run-summary` is implemented
  at `209bb19`: 39 focused tests exercise canonical JSON, deterministic TSV/QC
  views, exact evidence normalization, and receipt-last publication.
  `report-html-v1` is implemented at `117ba26`: 65 focused report tests pass,
  including real pinned-Quarto renders, and the complete Python suite reports
  277 passed with one expected opt-in Quarto skip. No production index,
  summary, or report has been built. The normal run-summary builder cannot yet
  populate explicit report-table approvals, so
  `report-html-v1a-report-table-approvals` is next. Bundled-Typst PDF/TSV and
  receipt exports, read-only runtime/reference/storage foundations, and one
  validator branch per pipeline step remain unimplemented. Remote validation
  remains paused.
- Step `09c` can record `evidence_incomplete` or
  `science_review_complete_exploratory`; it rejects the reserved
  `biological_interpretation_ready` value. It validates explicit evidence,
  does not rerun CMH or infer decisions, and publishes 13 TSVs with the review
  summary last. Report generation is never evidence of computational or
  biological validation.

## 4. What Not To Claim

- Do not claim final biological editing-site results yet.
- Do not claim Step `07` has run with real bcftools, passed a cluster dry-run, executed on the cluster, produced inspected cluster VCFs, or become cluster-proven.
- The Step `08` and Step `09` real-R suites pass on synthetic local fixtures.
  Do not turn that into a claim of a cluster dry-run, production table/plot,
  biological candidate, or cluster proof.
- Do not describe `orientation_policy=legacy_provisional_v1` as biologically validated.
- Do not equate `FWD_like` / `REV_like` with biological strand, sense, antisense, or transcript-strand labels.
- Do not describe CMH-ranked `significant_up`/`significant_down` candidates as
  validated editing sites. Cluster proof, candidate review, PI approval, and
  report generation are not by themselves orthogonal biological validation.
- Do not treat `science_review_complete_exploratory` as
  `biological_interpretation_ready`; exploratory reports must show their
  provisional status and limitations.
- Do not present Step `09c` fixture output as a production scientific review,
  science-review completion, cluster proof, or biological validation.
- Do not present the implemented artifact schemas, example inventory, or
  synthetic fixtures as a production artifact index, run summary, report, or
  validation result.
- Do not present the implemented adapter CLI or synthetic transaction as a
  production index or as runtime, cluster, scientific, or biological evidence.
- Do not present the implemented run-summary CLI or synthetic transaction as a
  production summary, report, or validation evidence.
- Do not present the implemented HTML renderer or its synthetic/incomplete
  fixture output as a production report, computational validation, completed
  science review, or biological evidence.
- Do not present report-table approval production, PDF/TSV/receipt exports, the
  preflight/provenance/storage foundations, or the per-step validators as
  implemented commands yet. They are activated descendant packages.
