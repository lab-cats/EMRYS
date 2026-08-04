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
| `contracts/` | Neutral cross-stage identities, DAG and topology contracts, public schemas, shared vocabularies, and independently owned executable validation of those neutral contracts. |
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
| `collect_RSeQC_paired_orientation_evidence` | `src/norad/evidence/collect_RSeQC_paired_orientation_evidence/` | `evidence.v1.yaml` | Shell producer; Python validator; SLURM entry point | `tests/evidence/collect_RSeQC_paired_orientation_evidence/` |
| `mark_BAM_duplicates_with_Picard` | `src/norad/stages/mark_BAM_duplicates_with_Picard/` | `stage.v1.yaml` | Shell producer; Python validator; SLURM entry point | `tests/stages/mark_BAM_duplicates_with_Picard/` |
| `split_N_cigar_reads_with_GATK` | `src/norad/stages/split_N_cigar_reads_with_GATK/` | `stage.v1.yaml` | Shell producer; Python validator; SLURM entry point | `tests/stages/split_N_cigar_reads_with_GATK/` |
| `partition_BAM_by_mechanical_read_orientation` | `src/norad/stages/partition_BAM_by_mechanical_read_orientation/` | `stage.v1.yaml` | Shell producer; Python validator; SLURM entry point | `tests/stages/partition_BAM_by_mechanical_read_orientation/` |
| `generate_partitioned_cohort_mpileup_VCFs` | `src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/` | `stage.v1.yaml` | Shell producer; Python validator; SLURM entry point | `tests/stages/generate_partitioned_cohort_mpileup_VCFs/` |
| `preprocess_and_annotate_cohort_candidates` | `src/norad/stages/preprocess_and_annotate_cohort_candidates/` | `stage.v1.yaml` | Shell transaction entry point; R scientific implementation; Python validator; SLURM entry point | `tests/stages/preprocess_and_annotate_cohort_candidates/` |
| `rank_cohort_candidates_with_paired_CMH` | `src/norad/analyses/rank_cohort_candidates_with_paired_CMH/` | `analysis.v1.yaml` | Shell transaction entry point; R scientific implementation; Python validator; SLURM entry point | `tests/analyses/rank_cohort_candidates_with_paired_CMH/` |
| `assemble_scientific_review_evidence_package` | `src/norad/evidence/assemble_scientific_review_evidence_package/` | `evidence.v1.yaml` | Python validation/publication implementation; shell launcher | `tests/evidence/assemble_scientific_review_evidence_package/` |

## Cross-cutting implemented target homes

The numbered-owner roster above does not classify implemented cross-cutting
concerns. This table remains the owner of their final homes after movement;
unmigrated rows may still occupy legacy root paths. Each move uses the same
direct, one-owner mechanics without inventing a new top-level domain.

| Current functional owner | Exact target source home | Owned native assets | Mirrored test home |
| --- | --- | --- | --- |
| Artifact contract validation | `src/norad/contracts/artifacts/validate_artifact_contracts.py`; the five existing schema basenames under `src/norad/contracts/schemas/artifacts/v1/` | The five artifact JSON Schemas; no reporting template or producer-local schema | `tests/contracts/artifacts/test_artifact_schema_contracts.py`; current valid fixtures under `tests/contracts/artifacts/fixtures/artifact_schema_v1/valid/` |
| Artifact indexing, canonical run-summary assembly, and static reporting | The six existing script basenames under `src/norad/reporting/`; `src/norad/reporting/templates/{run_report.qmd,run_report_pdf.qmd}`; `src/norad/reporting/styles/run_report.css` | Artifact index and summary implementation, renderer/bundle/shell launcher, two QMD templates, and one CSS style | Existing direct suite basenames under `tests/reporting/`; fixture groups under `tests/reporting/fixtures/{artifact_adapters_v1,artifact_run_summary_v1,report_html_v1}/` |
| Reference provenance evidence | `src/norad/evidence/reference_provenance/reference_provenance.py` | The current public evidence command; shared parsers move first only if separately approved as a neutral seam | `tests/evidence/reference_provenance/test_reference_provenance.py` |
| Structured runtime inspection | `src/norad/evidence/runtime_preflight/runtime_preflight.py` | The current explicit-profile, read-only inspection command | `tests/evidence/runtime_preflight/test_runtime_preflight.py` |
| Storage evidence | `src/norad/evidence/storage_inventory/storage_inventory.py` | The current read-only inventory command; retention action remains prohibited | `tests/evidence/storage_inventory/test_storage_inventory.py` |

## Approved neutral shared seams

`LIB-02F` compared the two implemented peer-dependency leaks by full behavior,
not by name. The resulting targets are narrower than either current owner and
must be implemented bottom-up through separate JIT cards:

| Neutral concern | Exact permanent owner | Allowed shared surface | Consumers and prohibited scope |
| --- | --- | --- | --- |
| Scientific artifact and public review-package contracts | `src/norad/contracts/scientific_evidence/`, beginning with `step08.py`, followed by separately reviewed `step09.py` and `review_package.py`; mirrored tests under `tests/contracts/scientific_evidence/` | Closed public headers/vocabularies; sample/partition and Step `08`/`09` artifact validation; public thirteen-file review-package roster and state reduction; private subordinate parsing needed by those named APIs | Step `08`, Step `09`, Step `09c`, artifact indexing, and reporting may consume the applicable public contract. The neutral owner may not import them or own review-plan/evidence-payload policy, `Artifact`, `ReviewContext`, `build_context`, publication, locking, rollback, recovery, or reporting projection. |
| Reference contig parsing | `src/norad/libraries/reference_contigs.py`; independent API tests at `tests/libraries/test_reference_contigs.py` | One parser-specific exception plus the exact ordered FASTA, FAI, and DICT contig/length parsers and their private duplicate/empty check | Reference provenance and the Step `00c`/`05` validators consume the library. Agreement decisions, per-role versus short-circuit aggregation, evidence rows, CLI, hashing, snapshots, publication, and recovery stay owner-local. |

Reporting removes its remaining Step `09c` implementation dependency with a
reporting-local reader/projection over the committed public review package and
validated artifact-index records. It does not share the evidence owner's
source-to-public reconstruction. Artifact-index reconciliation remains
independently implemented apart from consuming neutral public constants and
the closed evidence-state reduction. Step `08`/`09` shell and R checks remain
independent from the Python executable contract.

These homes do not approve descriptors, package imports, console scripts, or
distribution. Reporting must not retain its current private implementation
dependency on the Step `09c` evidence owner, and the reference-evidence move
must not leave Step `00c` or Step `05` importing a peer implementation. Any
neutral extraction needed to correct those directions is a separate reviewed
unit completed before the affected owner moves.

Public starter profiles, examples, operator selections, and reference tables
remain under root `configs/` when callers receive them as explicit inputs.
They are not owner-native implementation assets merely because one command
documents or tests them. Neutral JSON Schemas enforced as executable contracts,
private templates/styles, and other assets loaded as part of implementation
move with their final owner; public example/reference TSVs do not become
implementation assets by being schema-shaped.

Dependency restoration and repository-development commands remain explicit
repository-level interfaces under root `scripts/`. In particular, the R and
Quarto check/restore commands, their project-root `renv` surfaces, and
documentation/Git orchestration do not become runtime `cli/`, `libraries/`, or
scientific-workflow `orchestration/` implementation. A later setup design may
reconsider that boundary without creating a speculative `setup/` domain here.

## Mirrored test ownership

```text
tests/
├── stages/<public-slug>/
├── analyses/<public-slug>/
├── evidence/<public-slug>/
├── cli/
├── orchestration/
├── scheduler/
├── contracts/
├── libraries/
├── reporting/
├── ingestion/
├── contract_integration/
└── workflow_integration/
```

An owner-local test home covers that owner's public entry points, native
assets, local schemas, failure semantics, and independent fixtures. Language-
specific runners may remain below the owner home, but `tests/shell/` or
`tests/r/` is not the durable functional owner merely because it selects an
interpreter.

`tests/contracts/` independently tests neutral schemas, shared vocabularies,
and executable validation owned by the neutral contract domain.
`tests/contract_integration/` checks producer/consumer agreement at public
artifact boundaries without importing either implementation to construct
expected results. `tests/workflow_integration/` exercises multiple owners only
through their public entry points and explicit contracts.

Fixtures and goldens remain local to the narrowest test owner. A fixture moves
to a neutral contract suite only when it represents the shared public contract
rather than one producer's serialization helper. Test code and fixture
placement do not create runtime dependency edges.

The independent contract goldens and validation-roster agreement converge
under `tests/contract_integration/independent_contract_goldens/` and
`tests/contract_integration/validation_rosters/`, respectively. Cross-entry-
point public-command characterization remains a repository-development suite
because it spans Make, Git tooling, modes, and several runtime domains. The
repository-wide SLURM-wrapper characterization converges under
`tests/workflow_integration/scheduler/` only when scheduler work resumes; until
then it remains a deferred mixed suite.
Coverage enforcement, validation-gate orchestration, and documentation/Git
orchestration tests remain repository-development protections rather than
runtime-domain tests.

## CLI boundary

`cli/` owns shared user-facing command selection, argument parsing, and
translation into neutral request contracts. A CLI surface may depend on
`contracts/` and call an orchestration or functional owner's public entry
point. It may not import private stage, analysis, evidence, reporting, or
ingestion implementation or become the owner of their validation and
publication semantics.

Owner-specific public shell, Python, and R entry points remain with their
functional owner unless a later migration proves a thin compatibility wrapper
is required. This boundary does not create an installable console script or a
packaging contract.

## Library boundary

Implementation begins inside its functional owner. Promotion to `libraries/`
requires proven equivalent reuse and the narrowest named neutral domain; it is
not justified by similar filenames or helper signatures. There is no `utils`,
generic stage dispatcher, universal transaction framework, or forced cross-
language abstraction.

A neutral library may depend on neutral contracts and on lower-level neutral
libraries with an acyclic direction. It may not depend on `stages/`,
`analyses/`, `evidence/`, or another application domain. Functional owners may
depend on a reviewed library through its public API, with independent library
and consumer tests. This topology assigns dependency direction but does not
approve any extraction candidate.

## Reporting boundary

`reporting/` owns the downstream application chain for artifact indexing,
canonical run-summary construction, view-model projection, renderers, styles,
and templates. Neutral artifact and report schemas remain under `contracts/`;
artifact semantics unique to a stage, analysis, or evidence operation remain
with that producer.

Reporting may depend on neutral contracts and libraries and may consume only
explicitly declared public artifacts from functional owners. No stage,
analysis, or evidence implementation depends on reporting. Artifact indexing,
summary construction, and rendering are consumers and are not peer nodes in
the computational DAG.

A renderer consumes one explicit validated canonical run summary plus only
supplemental tables authorized by exact contract. It does not discover inputs,
run analysis, install tools, or promote evidence state. Native report assets
remain under the reporting owner; their packaging is deferred.

## Ingestion boundary

`ingestion/` owns admission and normalization of external requests, manifests,
and input references into neutral contracts. Manifest and request schemas that
cross into orchestration remain under `contracts/`; ingestion-specific parsing
and admission behavior remain under `ingestion/`.

Ingestion may depend on neutral contracts and reviewed libraries. It hands an
explicit validated contract to orchestration and does not import functional-
owner implementation, infer sample relationships from filenames, execute
stages, or make evidence claims. Operational inboxes, run-state directories,
and acquired data remain outside source ownership.

This boundary does not choose request fields, preprocessing profiles,
acquisition policy, lifecycle directories, or an ingestion runner.

## Orchestration and scheduler boundary

`orchestration/` may depend on neutral contracts and invoke the public entry
points of stages, analyses, and evidence operations. It may not import their
private implementation modules, rewrite their local contracts, or infer order
from paths. The semantic DAG and explicitly declared run inputs are its only
ordering inputs.

Stage-, analysis-, and evidence-specific SLURM entry points and job templates
remain with their functional owner. `scheduler/` owns only neutral scheduler
submission, state, and adapter contracts shared across owners. It may consume
neutral contracts and invoke an owner's public scheduler surface; functional
owners do not import scheduler or orchestration implementation.

Repository-documentation Git orchestration and developer quality gates are not
scientific-workflow orchestration and do not move into this runtime domain.
This boundary defines ownership only and does not create an orchestrator,
generate a job, or choose an optional-stage policy.

## Dependency-direction summary

Process invocation and artifact consumption are shown separately from code
imports; invoking a public entry point does not authorize importing its private
module.

| Owner | May import | May invoke or consume | Prohibited direction |
| --- | --- | --- | --- |
| `contracts/` | no NORAD runtime domain | none | every implementation domain |
| `libraries/` | `contracts/`; lower neutral libraries in an acyclic chain | none | every functional or application owner |
| `stages/`, `analyses/`, `evidence/` | `contracts/`; reviewed `libraries/`; owner-local code | owner-local tools; peer artifacts through contracts | peer implementation; `cli/`; `orchestration/`; `scheduler/`; `reporting/`; `ingestion/` |
| `ingestion/` | `contracts/`; reviewed `libraries/` | external inputs; emit validated request/manifest contracts | functional-owner or orchestration implementation |
| `reporting/` | `contracts/`; reviewed `libraries/`; reporting-local code | explicit public artifacts and canonical summaries | functional-owner implementation; input discovery |
| `orchestration/` | `contracts/`; reviewed `libraries/`; orchestration-local code | public functional and reporting entry points | private owner implementation; path- or number-inferred order |
| `scheduler/` | `contracts/`; reviewed `libraries/`; scheduler-local code | public owner scheduler surfaces | private functional or orchestration implementation |
| `cli/` | `contracts/`; public orchestration API; CLI-local code | public owner entry points | private application or functional implementation |

## Neutral contract boundary

`contracts/` is neutral: it may not import implementation from `stages/`,
`analyses/`, `evidence/`, or another runtime domain. Functional owners may
reference neutral cross-stage contracts and public schemas. An interface used
only within one functional owner remains local to that owner.

Stages, analyses, and evidence owners never import another functional owner's
implementation. Cross-owner data flow uses the explicit artifact contracts and
edges in [`STAGE_MAP.md`](STAGE_MAP.md#direct-dag-edges), while coordination
invokes public owner entry points rather than private modules.
