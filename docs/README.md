# Documentation

Start with your role below. Each component's `README.md` explains its purpose;
its `CONTRACT.md` defines exact behavior. The guides link to those details.

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
| Accepted work and completion criteria | [Findings matrix](tasks/backlog_matrix.md), delegating finite `CS-*` slices to the [temporary compression backlog](tasks/compression_backlog_matrix.md) |
| Current checkout and validation status | Live Git plus checks and retained artifacts bound to the exact commit |
| Retained historical validation observations | [Dated validation evidence](history/validation-evidence.md), never current authority |

If a guide disagrees with a schema, contract, test, or the current source,
report the disagreement; code does not silently change the contract. Git keeps
old planning and completed progress reports. Run `make -s documentation-check`
to check document structure and links.
