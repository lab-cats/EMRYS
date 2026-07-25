# Demo Walkthrough

This is a short read-only path for PI demo use. It points to the current sources of truth rather than replacing them.

## 1. Demo Goal

Show that the legacy NORAD / Novogene Remora workflow has been rebuilt into a
reproducible preprocessing and paired-CMH code path, with a clear distinction
between the cluster-proven RNA-seq preprocessing boundary and the locally
implemented Steps `07`-`09`.

Current boundary:

```text
Steps 00a-00c cluster-proven reference prep
-> Steps 01-06 cluster-proven across all six samples
-> Step 07 implemented and locally tested with mocked bcftools; no real or cluster run
-> Step 08 implemented and shell/fake-R tested locally; no Rscript runtime or cluster run
-> Step 09 implemented and shell/fake-R tested locally; no Rscript runtime or cluster run
```

## 2. Suggested 5-10 Minute Flow

1. `README.md` - project overview and current status.
2. `docs/architecture/ARCHITECTURE.md` - visual dataflow and engineering architecture.
3. `docs/demo/PI_DEMO_REPORT.md` - PI Decision Brief plus preliminary validation and QC summary.
4. `docs/design/PIPELINE_PLAN.md` - exact step contracts and validation status.
5. Operations troubleshooting guide - Step `05` `/tmp` temp-spill failure and hardening.
6. Optional terminal evidence - Step `05` / Step `06` cluster validation outputs
   and Step `07` mocked-bcftools / Step `08`-`09` fake-R shell-test output if
   available; do not present local fixtures as real-runtime or biological
   output evidence.

## 3. Talk Track

- The legacy hardcoded workflow has been translated into staged, testable pipeline steps with explicit inputs and outputs.
- SLURM execution is dry-run-first, with real execution gated by explicit `EXECUTE=1`.
- Reference prep and sample preprocessing are cluster-proven through Step `06` across the six-sample cohort.
- Step `06` publishes `FWD_like` / `REV_like` mechanical read-orientation BAMs and orientation counts TSVs for all six samples.
- Step `07` is implemented locally and locally tested with mocked bcftools at commit `e68b00c`; real-bcftools and cluster validation remain pending.
- Step `08` is implemented locally at commit `90335d8`; its deterministic partition-manifest × orientation contract and wrapper reliability behavior pass shell/fake-R tests, but the real-R fixtures could not run because this workstation has no `Rscript`.
- Step `08` writes the wide sites table, complete input receipt, and preprocessing QC summary under `results/vcf_preprocessed/` and `results/qc/vcf_preprocessing/`; no real-R or cluster output is being presented.
- Step `09` is implemented locally at commit `e4371de`; shell/fake-R tests cover explicit replicate pairing, Step `08` sites/input-receipt validation, Step `09` output-contract validation, threshold forwarding, six-output publication, locks, cleanup, and rollback. The authored real-R fixtures cover CMH/odds-ratio direction, global BH, and strict threshold semantics, but have not run on this workstation.
- Step `09` uses only manifest-defined EV/PUM1 replicate pairs and is designed to publish all-sites, significant-sites, summary, mutation-spectrum, and depth/delta outputs under `results/editing/<analysis>/`. These are implementation contracts, not inspected biological results.
- A real cluster failure in Step `05` was diagnosed as GATK/HTSJDK temp spill to node-local `/tmp` and hardened with project-storage temp handling.
- Biological interpretation is intentionally cautious: read-orientation labels are mechanical flag groups, and the Step `08`/`09` `orientation_policy=legacy_provisional_v1` mapping is explicitly provisional rather than biologically validated.
- The Step `09` implementation/docpatch gate is complete and pushed at
  `9ac8307`. The documentation-only `step-09a-roadmap-docpatch` is the
  clean/pushed roadmap base; cluster promotion proceeds through
  `validate-step-07`, `validate-step-08`, and `validate-step-09`, with an
  evidence docpatch between each.
- Computationally cluster-proven Steps `07`-`09` will still feed a separate
  `step-09b-scientific-validation` gate for orientation, annotation,
  statistical robustness, candidate adjudication, and background policy.

## 4. What Not To Claim

- Do not claim final biological editing-site results yet.
- Do not claim Step `07` has run with real bcftools, passed a cluster dry-run, executed on the cluster, produced inspected cluster VCFs, or become cluster-proven.
- Do not claim Step `08` has run in a real R runtime, passed a cluster dry-run, executed on the cluster, produced inspected candidate tables, or become cluster-proven.
- Do not claim Step `09` has run in a real R runtime, passed a cluster dry-run, executed on the cluster, produced inspected CMH tables/plots or biological candidates, or become cluster-proven.
- Do not describe `orientation_policy=legacy_provisional_v1` as biologically validated.
- Do not equate `FWD_like` / `REV_like` with biological strand, sense, antisense, or transcript-strand labels.
- Do not describe CMH-ranked `significant_up`/`significant_down` candidates as
  validated editing sites. Cluster proof, candidate review, PI approval, and
  report generation are not by themselves orthogonal biological validation.
- Do not treat `science_review_complete_exploratory` as
  `biological_interpretation_ready`; exploratory reports must show their
  provisional status and limitations.
- Do not present the post-proof preflight, provenance, artifact, reporting,
  config, module, array, dispatcher, cleanup, or public-ingestion roadmap as
  implemented commands.
