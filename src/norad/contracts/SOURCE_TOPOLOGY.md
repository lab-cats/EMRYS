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

## Mature stage-local contract

Every mature preprocessing or transformation stage has this predictable
target shape:

```text
src/norad/stages/<public-slug>/
├── README.md
├── CONTRACT.md
├── stage.v1.yaml
├── contracts/
│   └── <stage-local-interface>.v1.schema.json
└── <owned implementation, validation, and scheduler assets>
```

`README.md` is the human entry point and links to the detailed `CONTRACT.md`
when the two documents remain distinct. `stage.v1.yaml` is the only machine
descriptor for that stage version; executables, validators, languages, and job
templates do not receive competing descriptors.

The descriptor uses this fixed envelope:

```yaml
$schema: ../../contracts/schemas/stage_descriptor.v1.schema.json
descriptor_version: v1
kind: stage
machine_key: norad.stage.<public-slug>.v1
slug: <public-slug>
display_title: <display-title>
historical_aliases: [<historical-alias>]
documentation: README.md
interfaces:
  - role: <input-or-output-role>
    schema: <relative-path-to-versioned-json-schema>
```

The envelope schema is neutral because every stage shares it. An interface
used only within one stage references that stage's
`contracts/<name>.v1.schema.json`; a public or cross-stage interface references
a versioned JSON Schema under `src/norad/contracts/schemas/`. The descriptor
references schemas and never copies their field definitions.

The descriptor version governs this YAML envelope. It does not alter the
frozen identity key, implement descriptor loading, or establish a packaging or
distribution version.

## Analysis-module contract

Scientific analyses remain first-class modules rather than being placed under
`stages/`:

```text
src/norad/analyses/<public-slug>/
├── README.md
├── CONTRACT.md
├── analysis.v1.yaml
├── contracts/
│   └── <analysis-local-interface>.v1.schema.json
└── <owned implementation, validation, and scheduler assets>
```

`analysis.v1.yaml` uses the same fixed identity, documentation, and interface-
reference fields as the stage envelope, with
`$schema: ../../contracts/schemas/analysis_descriptor.v1.schema.json`,
`kind: analysis`, and the frozen `norad.analysis.<public-slug>.v1` key. Local
analysis schemas remain under the analysis owner; cross-stage inputs and
public analysis outputs reference neutral versioned schemas.

An analysis consumes declared stage artifacts through those contracts. It does
not import a stage implementation or become a child of the final preprocessing
stage that happens to precede it in the current DAG.

## Evidence-operation contract

Evidence collection and scientific-review packaging use their own functional
owner rather than becoming computational stages:

```text
src/norad/evidence/<public-slug>/
├── README.md
├── CONTRACT.md
├── evidence.v1.yaml
├── contracts/
│   └── <evidence-local-interface>.v1.schema.json
└── <owned implementation, validation, and scheduler assets>
```

`evidence.v1.yaml` uses the shared envelope fields with
`$schema: ../../contracts/schemas/evidence_descriptor.v1.schema.json`,
`kind: evidence`, and the frozen `norad.evidence.<public-slug>.v1` key.
Evidence-local schemas remain with the owner; public review packages and
cross-owner evidence interfaces reference neutral versioned schemas.

Evidence owners consume declared artifacts or separately supplied evidence
through explicit contracts. They do not import stage or analysis
implementations, and their presence in the DAG does not by itself make them a
computational gate.

## Functional-owner target homes

The identity map remains canonical in [`STAGE_MAP.md`](STAGE_MAP.md). This
roster assigns each identity one target home without copying titles, keys,
aliases, interfaces, or DAG edges. Native-asset classes describe functional
ownership only; no listed file is moved by this topology contract.

| Public slug | Target source home | Descriptor | Owned native assets | Mirrored test home |
| --- | --- | --- | --- | --- |
| `construct_STAR_index` | `src/norad/stages/construct_STAR_index/` | `stage.v1.yaml` | SLURM producer; Python validator | `tests/stages/construct_STAR_index/` |
| `convert_GTF_to_BED12` | `src/norad/stages/convert_GTF_to_BED12/` | `stage.v1.yaml` | Python producer and validator; SLURM entry point | `tests/stages/convert_GTF_to_BED12/` |
| `construct_FASTA_sidecars` | `src/norad/stages/construct_FASTA_sidecars/` | `stage.v1.yaml` | Shell producer; Python validator; SLURM entry point | `tests/stages/construct_FASTA_sidecars/` |
| `align_RNA_reads_with_STAR` | `src/norad/stages/align_RNA_reads_with_STAR/` | `stage.v1.yaml` | Shell producer; Python validator; SLURM entry point | `tests/stages/align_RNA_reads_with_STAR/` |
| `construct_canonical_BAM` | `src/norad/stages/construct_canonical_BAM/` | `stage.v1.yaml` | Shell producer; Python validator; SLURM entry point | `tests/stages/construct_canonical_BAM/` |
| `collect_canonical_BAM_QC_evidence` | `src/norad/evidence/collect_canonical_BAM_QC_evidence/` | `evidence.v1.yaml` | Shell producer; Python validator; SLURM entry point | `tests/evidence/collect_canonical_BAM_QC_evidence/` |

## Neutral contract boundary

`contracts/` is neutral: it may not import implementation from `stages/`,
`analyses/`, `evidence/`, or another runtime domain. Functional owners may
reference neutral cross-stage contracts and public schemas. An interface used
only within one functional owner remains local to that owner.

Stages, analyses, and evidence owners never import another functional owner's
implementation. Cross-owner data flow uses the explicit artifact contracts and
edges in [`STAGE_MAP.md`](STAGE_MAP.md#direct-dag-edges), while coordination
invokes public owner entry points rather than private modules.
