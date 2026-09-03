# Dated validation evidence

These are immutable historical observations migrated from the retired project
handoff. They describe the exact NORAD-era source revisions and retained
artifacts named below. They are not current-head, CSU full-Run, production,
scientific-review, or biological evidence unless a row explicitly says so.
Current state comes from live Git and checks bound to the revision under review.

## PORT-NC-01 integration replay

Tests from `fix/no-clobber` informed but did not validate the differently
implemented replay. Integrated candidate
`ebc43b4a8342b676eafb6b56492989498886ab55` passed the assembled local gate:
static preflight, installed-wheel smoke, guarded local R, shell/Slurm-wrapper
contracts, and Python behavior/coverage. The replay retained the stronger
transactions and runtime authority while admitting STAR metadata rows,
publishing Step 00b through its converter transaction, binding repository-owned
wrappers to the submitted checkout, and making staged no-clobber Step 01 the
scheduled default.

This was local integration evidence. It submitted no Slurm work, exercised no
distributed filesystem, and included no fresh-clone or full-Run proof. The later
VM run below exercised the integrated public path but does not retroactively
establish CSU, distributed-filesystem, or production-data behavior.

## Production-like synthetic VM and report evidence

NORAD science commit
`2587126e7e471b504657c9a43789e870713f8bb6` completed admitted FASTQ intake
through deterministic HTML reporting in lane
`full-cohort-public-2587126e7e47-02`. Slurm job `91` ran for `00:05:14` in one
single-node, two-CPU, 6 GiB allocation on a native ARM64 Ubuntu VM and reached
`COMPLETED/0:0`. The Run was
`run-bb36785424aba063e336ebaecdde4e78d984a4470187b8e1421fd281d3afa04f`.
All 24 declared runtime checks passed against the complete admitted VM
installation, and the lifecycle re-admitted the bound runtime profile before
Slurm submission.

The deterministic fixture used four paired-end libraries with 100,000 read
pairs each and a 5 Mb reference. It verified 34/34 scientific owner tasks across
13 automatic owners, 3/3 reporting transactions, and all 38 DAG rules. Step 09
published three CMH-ranked candidates, one passing the fixed significance
contract; the lab-owned independent Step 09 oracle matched. The retained legacy
HTML is 214,102 bytes with SHA-256
`50d4cc7bd26cd706544283ce532000ee6a900f8a8195ccb29b021809670afef8`.

The lane was sealed without rerunning science or reporting. Its portable
manifest records 861 entries: 206 directories, 655 files, and 210,401,447
regular bytes. Guest, private-host, and create-absent host-collection admission
passed. The retained tree is
`runs/full-cohort-public-2587126e7e47-02` in the Linux validation lab. The guest
seal SHA-256 is
`8c1816748725087ee7a23b7713f7853258442de4ec9d0de62199eccce5f81e72`;
the adjacent verified host-collection receipt SHA-256 is
`abd12efdf707ac54bfb66ac72479c9da6a289d0d5d9834a33bccad378c63ab8e`.

Renderer commit `441a7b0a36efb6d1c6baa43d2c4090f1f4957b3d` later published a separate
receipt-last computational-results derivative from those preserved sources
without rerunning a scientific owner. That exact commit passed the assembled
local repository gate before publication. The retained report path is:

```text
runs/full-cohort-public-2587126e7e47-02-vm-computational-report-441a7b0a36ef/
products/report/run-bb36785424aba063e336ebaecdde4e78d984a4470187b8e1421fd281d3afa04f/
run-bb36785424aba063e336ebaecdde4e78d984a4470187b8e1421fd281d3afa04f.run_report.html
```

Its HTML SHA-256 is
`ba426da9a4bdc387172f749a28e7140ec0b7dc0201d0dd74b4f59bb492e0dc30`;
the semantic-receipt SHA-256 is
`105e552768acb755f92a032ba68bdf5f05321861ff4f9a2f9335cb30fd301cce`.
It displays all three computational candidates and identifies the one
threshold-passing candidate as not scientifically adjudicated.

These observations are real-tool, synthetic, one-VM, single-node-Slurm evidence
only. They establish neither CSU Viking execution, multi-node or distributed
behavior, production-scale performance, production-data correctness, completed
scientific review, nor biological validation.

## CSU Viking manual Steps 07–09

These standalone-stage observations came from branch
`codex/license-and-retire-step09c` at exact NORAD commit
`64b14a11bf2b2371a3b8ef32ebbb642154a77b66`.

| Input | Retained identity |
|---|---|
| Paired sample manifest | `data/raw/samples.paired.tsv`; SHA-256 `b7e42c8ecc8c8202b5c3647dd84c9096780d7db19765b9c1935f11bfbd1fc126` |
| Step 07 partition manifest | `configs/step_07_partitions.primary_contigs.tsv`; SHA-256 `4346cefc23cb695aa653f2cc9c14e9ebc40f2bd09454bb5894ad0eb5f4879b6b` |
| Step 08 annotation | `refs/novogene_ref/genome.gtf`; SHA-256 `3b502426b9605a5afd433bbc69694e782221e62f7c39563323934540d70e3b07` |

| Stage | Retained execution and validation observation |
|---|---|
| Step 07 | The 25-partition paired set is under `results/mpileup-paired/NORAD_EV_PUM1`. Validator array `605174_[1-25]` recorded 25/25 `COMPLETED/0:0`; the aggregate reported `REPORT_COUNT=25` and `FAILED_CHECK_COUNT=0`. |
| Step 08 | Job `605171` completed `0:0` in `00:30:03` with four workers and `MaxRSS=27437560K` (about 27 GiB). Logs `logs/norad-vcf-preprocess-605171.out` and `.err` record 50 VCF inputs and 357,637 supported SNV candidates. Sites and input-receipt SHA-256 values are `81f061b66364ad82a4a2755f48b00ef131fa4fe4e0b566417524f618c06f9f2a` and `ba7c377a7674ff2c8935f47b5d77c49ddde00cad528f8756925711678fa58dac`. `results/qc/validation/08-paired/NORAD_EV_PUM1.validation.tsv` passed all five checks. |
| Step 09 | Job `605173` completed `0:0` in `00:00:49`. Logs `logs/norad-cmh-605173.out` and `.err` record 357,637 candidates, 30,816 tested candidates, and 65 significant sites. The six-output transaction is under `results/editing-paired/NORAD_EV_vs_PUM1`; `results/qc/validation/09-paired/NORAD_EV_vs_PUM1.validation.tsv` passed all seven checks. |

This establishes only manual Steps 07–09 completion and owner validation for
the declared inputs. It does not establish `emrys run` or resume, automatic
reporting, Steps 00–06 in the same Attempt, distributed or multi-node behavior,
full-site qualification, scientific adjudication, or biological validation.

## Cohort and orientation observations

The operational cohort contained three explicit paired strata:

| Replicate | EV | PUM1 |
|---|---|---|
| `2` | `ABE_EV_2` | `ABE_PUM1_2` |
| `3` | `ABE_EV_3` | `ABE_PUM1_3` |
| `4` | `ABE_EV4` | `ABE_PUM1_4` |

`ABE_EV4` intentionally lacks an underscore. Pairing came from manifest
metadata, never the sample names. Step 03 recorded:

| Sample | Failed | `1++,1--,2+-,2-+` | `1+-,1-+,2++,2--` |
|---|---:|---:|---:|
| `ABE_EV_2` | 0.0828 | 0.0432 | 0.8740 |
| `ABE_EV_3` | 0.0964 | 0.0420 | 0.8617 |
| `ABE_EV4` | 0.0908 | 0.0433 | 0.8658 |
| `ABE_PUM1_2` | 0.1063 | 0.0374 | 0.8562 |
| `ABE_PUM1_3` | 0.0955 | 0.0407 | 0.8639 |
| `ABE_PUM1_4` | 0.0926 | 0.0402 | 0.8672 |

All were classified reverse-stranded/first-strand-style. The hardened
`ABE_EV_2` rerun matched its earlier report; its mapping difference remains an
outlier, not an established pipeline defect. `FWD_like` and `REV_like` are
mechanical groupings, and `legacy_provisional_v1` is not a validated biological
strand model.

## Historical local R recovery constraint

A sibling-worktree `renv` activation once created a malformed empty
platform-qualified library path. It remained absent and was not fabricated or
automatically restored. Guarded checks bind `RENV_PATHS_LIBRARY` to the
project-library root. At the time, the installed project library used `renv`
`1.2.3` while metadata advertised `1.2.4`; dependency maintenance remained a
separate operation rather than an incidental environment mutation.

## Architecture closeout hosted CI

These runs establish bounded hosted engineering behavior for their exact
revisions. They do not establish institutional-site or multi-node execution,
production-data correctness, scientific review, or biological validity.

| Tranche | Exact revision and evidence | Established boundary |
|---|---|---|
| `ARCH-CLOSE-01` | `f85379edef0440266c1e97e97be5324e364812cb`; [ordinary CI 33630887395](https://github.com/lab-cats/EMRYS/actions/runs/33630887395); [selected 130-pair CI 33630899403](https://github.com/lab-cats/EMRYS/actions/runs/33630899403) | Managed real-tool direct journey, Rocky/Ubuntu/Debian lock installation, Python 3.11 shards, and hosted direct/disposable-Slurm success. |
| `ARCH-CLOSE-02` | `4a165038b3d164d6ace59b9e9bb21add086d07df`; [ordinary CI 33640599154](https://github.com/lab-cats/EMRYS/actions/runs/33640599154); [selected recovery CI 33640622974](https://github.com/lab-cats/EMRYS/actions/runs/33640622974) | Hosted direct/disposable-Slurm controlled failure, resume, provenance, Results, and logging parity at 130 pairs. |
| `ARCH-CLOSE-03` | `f3622f791e90fd6ed15079abcbcbe9b7003cbb6a`; [ordinary CI 33653717181](https://github.com/lab-cats/EMRYS/actions/runs/33653717181); [CodeQL 33653716112](https://github.com/lab-cats/EMRYS/actions/runs/33653716112) | Role, ownership, baseline, closeout, ordinary CI, and static-security evidence; long lanes were not selected. |
