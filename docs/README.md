# Documentation

Start with the document for your role. Exact functional behavior remains with
the implementation's adjacent `README.md` and `CONTRACT.md`; this tree should
route to those owners rather than repeat them.

| Reader | Start | Continue |
| --- | --- | --- |
| Scientist or new user | [Project overview](../README.md) | [Quickstart](../quickstart.md) and [configuration](../configs/README.md) |
| Operator | [Runbook](operations/RUNBOOK.md) | [Troubleshooting](operations/TROUBLESHOOTING.md) and the affected owner contract |
| Scientific reviewer | [Current architecture](architecture/ARCHITECTURE.md) | [Semantic stage map](../src/emrys/contracts/STAGE_MAP.md) and [external evaluation](reference/EXTERNAL_SCIENTIFIC_EVALUATION.md) |
| Maintainer | [Safety guard](../AGENTS.md) | [Workflow kernel](operations/WORKFLOW.md), [engineering conventions](operations/ENGINEERING_CONVENTIONS.md), and the selected backlog item |

## Authorities

| Subject | Authority |
| --- | --- |
| Product purpose and supported boundary | [Root README](../README.md) |
| First successful Run | [Quickstart](../quickstart.md) |
| Scientist-authored Project and configuration | [Configuration guide](../configs/README.md) |
| Current system structure | [Architecture index](architecture/README.md) |
| Semantic identities and workflow edges | [Stage map](../src/emrys/contracts/STAGE_MAP.md) |
| Source ownership and allowed dependencies | [Source topology](../src/emrys/contracts/SOURCE_TOPOLOGY.md) |
| Durable cross-cutting rationale | [Decision index](design/DECISIONS.md) |
| Run and recovery procedures | [Runbook](operations/RUNBOOK.md) and [troubleshooting](operations/TROUBLESHOOTING.md) |
| EMRYS-specific terminology | [Glossary](reference/GLOSSARY.md) |
| Test and evidence vocabulary | [Test baseline](design/TEST_BASELINE.md) |
| Accepted work and completion criteria | [Findings matrix](tasks/backlog_matrix.md) |
| Current checkout and validation status | Live Git plus checks and retained artifacts bound to the exact commit |
| Retained historical validation observations | [Dated validation evidence](history/validation-evidence.md), never current authority |

Overview prose yields to versioned schemas, owner contracts, direct tests, and
live source at the exact commit. Implementation alone does not silently amend
a declared contract; disagreement is a finding. Historical planning and
completed gate narratives remain in Git history rather than a second live
archive. `make -s documentation-check` checks structural documentation rules.
