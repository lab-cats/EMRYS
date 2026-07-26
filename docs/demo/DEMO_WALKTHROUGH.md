# Demo Walkthrough

This is a short read-only path for PI demo use. It points to the current sources of truth rather than replacing them.

## 1. Demo Goal

Show that the legacy NORAD / Novogene Remora workflow has been rebuilt into a
reproducible preprocessing and paired-CMH code path, with a clear distinction
between the cluster-proven RNA-seq preprocessing boundary and the locally
implemented Steps `07`-`09` plus the local Step `09c` evidence validator.

Current boundary:

```text
Steps 00a-00c cluster-proven reference prep
-> Steps 01-06 cluster-proven across all six samples
-> Step 07 implemented and locally tested with mocked bcftools; no real or cluster run
-> local signed/notarized R 4.6.1 + guarded renv/Bioconductor 3.23 checks pass
-> Step 08 and Step 09 real-R suites pass locally without SKIP after eae5eca
-> Step 09c implemented and synthetic-fixture-tested locally at b674a31
-> remote validation paused; immediate reports are activated but not implemented
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
   implementation evidence, not a completed production scientific review.

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
  implemented at `b674a31` and fixture-tested locally; `artifact-schema-v1` is
  next. Artifact adapters/run summary, self-contained HTML and bundled-Typst
  PDF/TSV reports, read-only runtime/reference/storage foundations, and one
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
- Do not present the artifact/run-summary/report slice, the
  preflight/provenance/storage foundations, or the per-step validators as
  implemented commands yet. They are activated descendant packages.
