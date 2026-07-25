# Demo Walkthrough

This is a short read-only path for PI demo use. It points to the current sources of truth rather than replacing them.

## 1. Demo Goal

Show that the legacy NORAD / Novogene Remora workflow has been rebuilt into a reproducible preprocessing backbone, with a clear distinction between cluster-proven RNA-seq preprocessing, the locally implemented Step `07` mpileup stage, and the pending downstream editing-site calling stages.

Current boundary:

```text
Steps 00a-00c cluster-proven reference prep
-> Steps 01-06 cluster-proven across all six samples
-> Step 07 implemented and locally tested with mocked bcftools; no real or cluster run
-> Steps 08-09 pending editing-site workflow
```

## 2. Suggested 5-10 Minute Flow

1. `README.md` - project overview and current status.
2. `docs/architecture/ARCHITECTURE.md` - visual dataflow and engineering architecture.
3. `docs/demo/PI_DEMO_REPORT.md` - PI Decision Brief plus preliminary validation and QC summary.
4. `docs/design/PIPELINE_PLAN.md` - exact step contracts and validation status.
5. Operations troubleshooting guide - Step `05` `/tmp` temp-spill failure and hardening.
6. Optional terminal evidence - Step `05` / Step `06` cluster validation outputs and Step `07` local mocked-test output if available; do not present local fixtures as biological output evidence.

## 3. Talk Track

- The legacy hardcoded workflow has been translated into staged, testable pipeline steps with explicit inputs and outputs.
- SLURM execution is dry-run-first, with real execution gated by explicit `EXECUTE=1`.
- Reference prep and sample preprocessing are cluster-proven through Step `06` across the six-sample cohort.
- Step `06` publishes `FWD_like` / `REV_like` mechanical read-orientation BAMs and orientation counts TSVs for all six samples.
- Step `07` is implemented locally and locally tested with mocked bcftools at commit `e68b00c`; real-bcftools and cluster validation remain pending.
- A real cluster failure in Step `05` was diagnosed as GATK/HTSJDK temp spill to node-local `/tmp` and hardened with project-storage temp handling.
- Biological interpretation is intentionally cautious: read-orientation labels are mechanical flag groups, not biological strand labels.
- Step `08` is the next local implementation stage, followed by Step `09`; later cluster promotion must begin with Step `07`.

## 4. What Not To Claim

- Do not claim final biological editing-site results yet.
- Do not claim Step `07` has run with real bcftools, passed a cluster dry-run, executed on the cluster, produced inspected cluster VCFs, or become cluster-proven.
- Do not equate `FWD_like` / `REV_like` with biological strand, sense, antisense, or transcript-strand labels.
