# Compression campaign closeout evidence — 2026-09-14

This additive record preserves the repository-recorded September 14 closeout and
its measured limits from the [main matrix](../tasks/backlog_matrix.md#completed-and-closed-outcomes).
It is historical evidence, not current optimization acceptance. The matrix
continues to own `COMPRESS-01` status and the transferred work; its original
closeout text remains in place while any later shortening is reviewed.

This record was compiled against source snapshot
`794a728062b1ddf73bcfdf70a2eb42c5168679ee`. Repository commits show when
the claims were recorded; the original approval exchange is not reproduced
here. GitHub run metadata was checked on 2026-09-22 for run-level
conclusion and head revision; no per-job artifact, institutional Run, or
scientific result was independently re-evaluated here.

## Source provenance

| Recorded source | Immutable commit | Recording date (Eastern) |
| --- | --- | --- |
| Earlier hosted results later cited in the matrix | `26394875761fd29898d07657ac0e432d705a4a61` and `f3a3966f157f967361e887288c294a4c1a1e68d7` | 2026-09-08 and 2026-09-09 |
| User-closeout account after integration | `ad43a56e59461f0d32998207e7450a880e7fc582` | 2026-09-14 11:45 |
| Durable matrix closeout, counts, and final hosted identities | `550b5402506730e8605dc96db48aaa86c400e3ed` | 2026-09-14 12:14 |
| Later clarification that dashboard nonretirement was a closeout-time state | `1e849511ac8447d530c1a56ee7cdc5831b4301b1` | 2026-09-22 17:13 |

## Decision and count definitions

The source records that the user closed `COMPRESS-01` on September 14 after
PR #169 merged at `2ecf7d449188ebd2e6d8b2e64a714ba269e5124b`. Of 43
CS cards, 42 were completed and CS-05 transferred to `REPORT-ROSTER-01`.
The temporary compression campaign and backlog were retired after their
unique decisions and evidence moved to existing owners. The source explicitly
states that no further compression tranche is active or implied. It also
records 93 integrated commits across PR #140 and PRs #148–168; Git and those
PRs keep the routine change and review sequence. The closeout says scientific
computation, data, provenance, current Run recovery, both reports, figures,
and the dashboard remained. It also says Codex completed source and
integration reviews; this record does not independently reconstruct those
reviews or promote their scope.

The agreed comparison starts at
`cab77a2610cecbefaaf0fb463fa7ebe1c500767c`. It counts tracked product
physical lines in `.py`, `.R`, `.sh`, `.css`, `.j2`, and `Snakefile`, including
relocated files. Generated `renv/activate.R` and tooling
`restore_r_environment.R` are excluded. The separate integration comparison
starts at pre-integration master
`446802c06ebceee8328a5cb4b542eea9fb2ed398`. They use different baselines;
the percentages cannot be substituted for one another.

| Measure | Agreed campaign baseline | Pre-integration master comparison |
| --- | ---: | ---: |
| Initial product physical lines | 69,223 | See surface delta below |
| Final product physical lines | 55,862 | See surface delta below |
| Product reduction | 13,361 lines, 19.30% | 13,480 lines, 19.44% |
| 20% campaign target | 55,378 product lines | Not this baseline's target |
| Accepted shortfall | 484 product lines | Not this baseline's target |

The pre-integration-master comparison retained seven separate surface counts:

| Surface | Net lines |
| --- | ---: |
| Product | −13,480 |
| Tests and fixtures | −12,699 |
| Documentation | +802 |
| Schemas and configuration | −2,243 |
| Tooling | +284 |
| Generated and dependency files | +106 |
| Retained evidence | 0 |
| **Total** | **−27,230** |

The arithmetic and the final tested/merged Git-tree equality were checked
against the named commits. The count classifications and 93-commit total are
the source's retained accounting; this record does not rerun the campaign's
file inventory or certify a new reduction target.

## Hosted verification and limits

| Source claim | Run and head revision | Checked here |
| --- | --- | --- |
| Ordinary hosted CI at final reviewed tree | [34857271894](https://github.com/lab-cats/EMRYS/actions/runs/34857271894), `fdc7cc79a3cf8637bb1c591c95a82020816fe863` | GitHub run metadata: completed/success at that head. |
| Selected 130-pair synthetic E2E at final reviewed tree | [34857300341](https://github.com/lab-cats/EMRYS/actions/runs/34857300341), `fdc7cc79a3cf8637bb1c591c95a82020816fe863` | GitHub run metadata: completed/success at that head. |
| Earlier CI-01, DEV-01, and CLI-VERSION-01 ordinary suite | [34306975901](https://github.com/lab-cats/EMRYS/actions/runs/34306975901), `b491aac5f198584475ba72de2cfe0894f8be81df` | GitHub run metadata: completed/success at that head. |
| Earlier implemented outcomes' applicable hosted checks | [34301289787](https://github.com/lab-cats/EMRYS/actions/runs/34301289787), `2fb8f5ef5a297f3778fd2dd7a5046eec0ab21fa5` | GitHub run metadata: completed/success at that head; the matrix calls this PR #140's integrated tree. |

The matrix says run `34306975901` included Python coverage, guarded R,
managed golden path, static/wheel, shell, and userspace checks for CI-01,
DEV-01, and CLI-VERSION-01. It says run `34301289787` covered applicable
Python, guarded-R, managed-golden, and independent-contract checks for the
other implemented outcomes below the closeout. Those are source-reported
suite scopes; run-level success metadata alone does not verify each job or
artifact.

The reviewed `fdc7cc79a3cf8637bb1c591c95a82020816fe863` and merge
`2ecf7d449188ebd2e6d8b2e64a714ba269e5124b` resolve to the same Git
tree, `6e1c67e3bf74b317e727bcd9c051cdccaa095236`. Run-level success
metadata does not identify every selected job's artifacts or independently
prove the matrix's stated suite coverage. These were hosted software and
disposable-Slurm checks. They establish no institutional site qualification,
production-data correctness, scientific review, or biological validity.

At closeout, dashboard retirement still awaited a validated replacement.
`DASHBOARD-RETIRE-01` in the [current matrix](../tasks/backlog_matrix.md)
records the later implementation and remaining CI and institutional visual
verification. The historical sentence is not a present-tense dashboard status.
This dated record changes no accepted row and authorizes no deletion of the
original closeout evidence.
