# Demo Walkthrough

This is a short read-only path for PI demo use. It points to the current sources of truth rather than replacing them.

## 1. Demo Goal

Show that the legacy NORAD / Novogene Remora workflow has been rebuilt into a reproducible preprocessing backbone, with a clear distinction between the cluster-proven RNA-seq preprocessing boundary, the locally implemented Steps `07`-`08`, and the pending Step `09` editing-site caller.

Current boundary:

```text
Steps 00a-00c cluster-proven reference prep
-> Steps 01-06 cluster-proven across all six samples
-> Step 07 implemented and locally tested with mocked bcftools; no real or cluster run
-> Step 08 implemented and shell/fake-R tested locally; no Rscript runtime or cluster run
-> Step 09 pending and next local implementation
```

## 2. Suggested 5-10 Minute Flow

1. `README.md` - project overview and current status.
2. `docs/architecture/ARCHITECTURE.md` - visual dataflow and engineering architecture.
3. `docs/demo/PI_DEMO_REPORT.md` - PI Decision Brief plus preliminary validation and QC summary.
4. `docs/design/PIPELINE_PLAN.md` - exact step contracts and validation status.
5. Operations troubleshooting guide - Step `05` `/tmp` temp-spill failure and hardening.
6. Optional terminal evidence - Step `05` / Step `06` cluster validation outputs and Step `07` mocked-bcftools / Step `08` fake-R shell-test output if available; do not present local fixtures as real-runtime or biological output evidence.

## 3. Talk Track

- The legacy hardcoded workflow has been translated into staged, testable pipeline steps with explicit inputs and outputs.
- SLURM execution is dry-run-first, with real execution gated by explicit `EXECUTE=1`.
- Reference prep and sample preprocessing are cluster-proven through Step `06` across the six-sample cohort.
- Step `06` publishes `FWD_like` / `REV_like` mechanical read-orientation BAMs and orientation counts TSVs for all six samples.
- Step `07` is implemented locally and locally tested with mocked bcftools at commit `e68b00c`; real-bcftools and cluster validation remain pending.
- Step `08` is implemented locally at commit `90335d8`; its deterministic partition-manifest × orientation contract and wrapper reliability behavior pass shell/fake-R tests, but the real-R fixtures could not run because this workstation has no `Rscript`.
- Step `08` writes the wide sites table, complete input receipt, and preprocessing QC summary under `results/vcf_preprocessed/` and `results/qc/vcf_preprocessing/`; no real-R or cluster output is being presented.
- A real cluster failure in Step `05` was diagnosed as GATK/HTSJDK temp spill to node-local `/tmp` and hardened with project-storage temp handling.
- Biological interpretation is intentionally cautious: read-orientation labels are mechanical flag groups, and Step `08`'s `orientation_policy=legacy_provisional_v1` mapping is explicitly provisional rather than biologically validated.
- Step `09` is the next local implementation stage; later cluster promotion must still begin with Step `07`.

## 4. What Not To Claim

- Do not claim final biological editing-site results yet.
- Do not claim Step `07` has run with real bcftools, passed a cluster dry-run, executed on the cluster, produced inspected cluster VCFs, or become cluster-proven.
- Do not claim Step `08` has run in a real R runtime, passed a cluster dry-run, executed on the cluster, produced inspected candidate tables, or become cluster-proven.
- Do not describe `orientation_policy=legacy_provisional_v1` as biologically validated.
- Do not equate `FWD_like` / `REV_like` with biological strand, sense, antisense, or transcript-strand labels.
