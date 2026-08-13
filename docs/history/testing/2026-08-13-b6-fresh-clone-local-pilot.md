# B6 fresh-clone local-pilot proof

This frozen record preserves the exact E2E-03A proof used to write researcher
onboarding. Current commands remain in the
[`RUNBOOK`](../../operations/RUNBOOK.md), current evidence ceilings in
[`HANDOFF`](../../operations/HANDOFF.md), and current acceptance policy in
[`PIPELINE_PLAN`](../../design/PIPELINE_PLAN.md).

## Source and setup

- Date: `2026-08-13` in `America/New_York`.
- Source revision: `cbea15b7fb0178adb9a233fe1ecd4ad9f357048c`.
- Source state: ordinary clean clone created with `git clone --no-local
  --no-hardlinks` from the authoritative local checkout; clone `HEAD` matched
  the revision above and its origin was the separate source checkout.
- Interpreter: CPython `3.14.5` from the clone-local `.venv` launcher.
- Workflow engine: locked Snakemake `9.25.1`.
- Explicit setup: `uv sync --locked --group workflow --offline
  --no-python-downloads --python /absolute/path/to/reviewed/python` after the
  locked artifacts had been populated in the uv cache. The initial cache fill
  required downloading one missing locked dependency; the final pytest did not
  install or repair dependencies.

The final proof command was:

```bash
NORAD_FRESH_CLONE_E2E=1 \
NORAD_FRESH_CLONE_E2E_SOURCE_ROOT=/absolute/path/to/source-checkout \
.venv/bin/python -m pytest -q --tb=short \
  tests/orchestration/local_pilot/test_fresh_clone_e2e.py
```

Result: `2 passed in 270.17s`.

## Deterministic fixture identity

The test generated two independent copies of the same four-sample, two-paired-
stratum, one-partition fixture. Separate reference roots were required because
Step `00c` sidecars are intentionally create-exclusive. The tracked generator
is `tests/orchestration/local_pilot/fixture.py` at the source revision above.

| Relative fixture path | SHA-256 |
| --- | --- |
| `partitions.tsv` | `a22d341c7bc881ed16b08fb5f022647ece0a23e2b2a31811f4e0f12e301a8a09` |
| `reads/EV_1_R1.fastq` | `7a8b22a6bc1af7501447bdc9509a59f0bded34d0290f17b7739fef6496a644fd` |
| `reads/EV_1_R2.fastq` | `afd8ca19033a08057ac61c8a7ca7ca619fd7196c6b22fbedc662160de6be4324` |
| `reads/EV_2_R1.fastq` | `045e6ac2b5bdd6dd5d4c551344c97deb93f889a893b799bd5cc0bb4dfe9e8c1b` |
| `reads/EV_2_R2.fastq` | `3034685a51c56816d3e98bb35bca87d55e128da14c8ae8dc1a3f11314e56cb37` |
| `reads/PUM1_1_R1.fastq` | `0de32fe377cb74a66abc70d507f637730e2e28f85b2b0ce9643741b4496cc3de` |
| `reads/PUM1_1_R2.fastq` | `4f0b85699f26821bb3f845f00e5a6b1404ce54112dcb53f5de94a8cfdba19a92` |
| `reads/PUM1_2_R1.fastq` | `661eae3a002592bad58646eb6815f125b6bef80eeed8d67737e4bc3c658c1d63` |
| `reads/PUM1_2_R2.fastq` | `af10a129e3a5bbd9cc56c7525d04bf377f6e741f3560fe5dcf95c851be31cd0f` |
| `reference/genome.fa` | `4b874c99145bc8db21c444ba2b68681039cbe6039704b4ce15cfdf28e6cbf0d1` |
| `reference/genome.gtf` | `191d25ecee84e09c96a20d92c2afd76926fe2c7d759d3a02f2c0debdc349a429` |
| `request.yaml` | `b83cc8dff5227d99a568206a93f557331d54f902266bb8f0fd8bc7bec0588c44` |
| `samples.tsv` | `4a913141f7989dd1f775e9ca331f2966bdb8c4935a4d46ab563b4ce37fd5dbdc` |

The normalized execution contract independently re-read and verified twelve
unique bound input paths: eight FASTQs, two manifests, FASTA, and GTF. The
request snapshot was separately bound in each workflow attempt.

## Behaviors proved

- The top-level public parser accepts explicit test dependencies without a
  shipped fake flag or environment backdoor; production defaults are unchanged.
- The real public doctor parsed and probed the complete declared runtime roster.
  Science-tool and R observations came from clearly named availability stubs,
  so `READY` here is fixture readiness, not real-tool readiness.
- Public `run` dry-run rendered 34 owner jobs and three reporting transactions
  without creating the workspace.
- A controlled stop after the one-sample slice produced a failed terminal
  receipt with Snakemake exit `23`; public inspection derived
  `resume_available`.
- Resume planning wrote no state. Resume execution preserved every prior
  verified record, bound output, validation report byte, and mtime, completed
  the remaining jobs, and ended `local_pipeline_complete`.
- A second initial run against the same run root and resume of a completed run
  were refused.
- A separate clean workspace and separate byte-identical intake completed all
  34 owner jobs and all three reporting transactions without prior state.
- Both completed runs produced artifact-index and run-summary receipts, a
  Jinja HTML report, report summary TSV, report receipt, and semantically
  re-admitted reporting ledgers. Step `09c` remained absent and science status
  remained `evidence_incomplete`.
- The clone remained Git-clean and run evidence contained no path back to the
  authoritative source checkout despite a hostile `PYTHONPATH` value.

## Evidence ceiling

This is clean-clone, locked-setup, deterministic no-science local control-plane
evidence. It executed real intake, runtime-profile parsing, public dispatch,
Snakemake, locking, immutable attempts, producer-entry ledgers, semantic
validation, inspection, reporting transactions, failure, and resume. It did
not execute STAR, samtools, Picard, GATK, bcftools, RSeQC, R/Bioconductor,
SLURM, a VM, CSU storage/modules, production reads or references, scientific
review, validated editing-site adjudication, or biological interpretation.
