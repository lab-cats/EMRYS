# Target source, contract, and test topology

This file is the canonical detailed owner for NORAD's target source ownership,
contract placement, allowed dependency direction, and mirrored test homes. It
defines topology only: the implemented current layout remains documented in
[`ARCHITECTURE.md`](../../../docs/architecture/ARCHITECTURE.md), and migration
mechanics are defined separately.

The target does not introduce packaging, descriptor loading, orchestration,
job materialization, or physical source movement.

## Top-level source owners

```text
src/norad/
├── cli/
├── orchestration/
├── scheduler/
├── contracts/
├── libraries/
├── stages/
├── analyses/
├── evidence/
├── reporting/
└── ingestion/
```

| Target owner | Responsibility |
| --- | --- |
| `cli/` | Public command interfaces and argument-to-contract translation. |
| `orchestration/` | Workflow coordination through declared contracts and owner entry points. |
| `scheduler/` | Scheduler-facing adapters and templates that delegate functional work. |
| `contracts/` | Neutral cross-stage identities, DAG and topology contracts, public schemas, and shared vocabularies. |
| `libraries/` | Proven shared implementation with an explicitly approved neutral owner; never a generic utility bucket. |
| `stages/` | Preprocessing and transformation owners keyed by the public stage slugs in [`STAGE_MAP.md`](STAGE_MAP.md#identity-map). |
| `analyses/` | First-class scientific analysis modules, distinct from preprocessing stages. |
| `evidence/` | Evidence-collection and review-package owners that do not become peer computational stages. |
| `reporting/` | Run-summary normalization and report-generation implementation and owned assets. |
| `ingestion/` | Request and external-input admission implementation; operational state remains outside source. |

Shell, R, SLURM, schemas, styles, templates, and other non-Python assets retain
their native form under the functional owner that defines their behavior.
Their future distribution is not settled here.

## Neutral contract boundary

`contracts/` is neutral: it may not import implementation from `stages/`,
`analyses/`, `evidence/`, or another runtime domain. Functional owners may
reference neutral cross-stage contracts and public schemas. An interface used
only within one functional owner remains local to that owner.

Stages, analyses, and evidence owners never import another functional owner's
implementation. Cross-owner data flow uses the explicit artifact contracts and
edges in [`STAGE_MAP.md`](STAGE_MAP.md#direct-dag-edges), while coordination
invokes public owner entry points rather than private modules.
