# Source ownership and dependency direction

This file owns the descriptive current Python source-import graph, approved
shared seams, and exact bounded import transitions. It does not turn the
current package tree into the target responsibility model. The
[`architecture index`](../../../docs/architecture/README.md) organizes the
human views; the
[`platform-direction decision`](../../../docs/design/decisions/platform-direction.md#ratified-responsibility-and-dependency-model)
owns target responsibilities and forbidden authority transfers;
[`STAGE_MAP.md`](STAGE_MAP.md) owns semantic identities and artifact edges; the
[`functional-owner inventory`](../../../docs/architecture/FUNCTIONAL_OWNER_INVENTORY.md)
owns exact public programs, jobs, validators, and tests.

## Current source domains

| Domain | Responsibility |
| --- | --- |
| Package root | `__init__.py` exposes package metadata; `__main__.py` is the current grouped CLI composition root, not the future application model. |
| `contracts/` | Neutral schemas, shared scientific-evidence contracts, identities, and topology contracts. |
| `libraries/` | Narrow shared implementation proven across named consumers; never a generic utility bucket. |
| `stages/` | Preprocessing and transformation owners keyed by the slugs in `STAGE_MAP.md`. |
| `analyses/` | Scientific analysis owners distinct from preprocessing stages. |
| `evidence/` | Operational and mechanical evidence collection that does not become peer computation. |
| `reporting/` | Artifact adaptation, canonical run summaries, projections, templates, styles, and static rendering. |
| `ingestion/` | External-input admission and diagnostics; no implemented orchestration runner. |
| `orchestration/` | Local-pilot request normalization, reporting projection, content-bound task execution/reuse admission, and lifecycle application policy; no scientific implementation. Static scheduling assets live at root `workflow/`. |

Native Python, shell, R, SLURM, schema, style, template, and fixture assets stay
with the owner whose behavior they implement. Root `configs/` remains the
public home for explicit starter inputs and reference tables. Repository Git,
documentation, quality-gate, dependency-restoration, and environment tooling
under `scripts/` is not scientific-workflow orchestration.

## Functional-owner shape

Every semantic stage, analysis, or evidence owner has one directory under its
domain, an operator `README.md`, an adjacent `CONTRACT.md`, owned native assets,
and a mirrored test directory. The documentation gate derives these expected
homes from `STAGE_MAP.md`.

Owner-local tests protect public entry points, local schemas, failure behavior,
and fixtures. `tests/contracts/` protects neutral contracts;
`tests/contract_integration/` checks producer/consumer agreement using public
artifacts; repository-wide scheduler, CLI, coverage, and validation-gate tests
remain cross-owner development protection.

## Owner cutovers

A physical ownership move is one semantic package: final-owner implementation,
mirrored direct tests, affected callers, contracts, owner documentation, and
coverage or tooling configuration move together. Capture the old public
boundary first, including faults, then prove the final path preserves declared
bytes, streams, exits, modes, arbitrary-CWD behavior, side effects,
transactions, recovery, and unrelated files.

An accepted cutover leaves one live implementation. Remove the embedded or old
helper in the same package; do not retain a temporary re-export, forwarding
wrapper, duplicate test owner, or compatibility shadow unless that exact public
surface is separately approved as a continuing contract. Rollback is the
coherent semantic package, not a mixture of old and final owners.

## Approved shared seams

| Seam | Neutral owner | Current consumers and boundary |
| --- | --- | --- |
| Validation-report publication | `libraries/validation/` | Owner validators import the shared facade; errors, snapshots, rows, publication, and runtime lifecycle have separate modules. Parsing/check rosters, evidence rows, and CLI remain owner-local. |
| BAM validation | `libraries/alignments/bam.py` | Step `01`, `02`, `04`, `05`, and `06` validators. Stage-specific checks and evidence remain local. |
| STAR output parsing | `libraries/alignments/star.py` | Step `00a` and `01` validators plus artifact indexing share structural parsing and declared STAR member names. Owner checks and reporting evidence remain local. |
| Mechanical-orientation formats | `libraries/alignments/orientation.py` | Step `08`/`09` contracts, Step `06`–`09` validators, and artifact indexing share fixed labels, policy admission, and count parsing. Scientific interpretation and publication remain owner-local. |
| Reference contig parsing | `libraries/references/contigs.py` | Reference provenance and Step `00c`/`05` validators. Agreement policy, reporting, and publication remain local. |
| Step `07` mpileup formats and input parsing | `libraries/validation/mpileup.py` | The Step `07` producer and validator share strict sample/partition manifest admission, FAI and selector mechanics, and fixed receipt/VCF vocabulary. The Step `08` producer and artifact-index consumers reuse only the fixed format vocabulary. Scientific commands, transaction/publication, output validation, reconciliation, and reporting policy remain owner-local. |
| R input-contract mechanics | `libraries/input_contract.R` | Step `08`, `09`, and `10` R programs share named-argument parsing, file/hash guards, and strict TSV loading. Argument rosters, defaults, table policy, and scientific algorithms remain owner-local. |
| Executable-value resolution | `libraries/executable_resolution.sh` | Eleven named Bash producers across Steps `00a`, `00c`, `01`–`10`, including evidence owners `02b` and `03`; the exact consumer roster is protected directly. Tool precedence, version policy, commands, and failures remain local. |
| Step `08` contract | `contracts/scientific_evidence/step08.py` | Step `08`, Step `09`, and artifact consumers share headers/vocabulary and input validation, not algorithms or publication. |
| Step `09` contract | `contracts/scientific_evidence/step09.py` | The validator, artifact index, and run report share `validate_step09_projection` for canonical intrinsic admission of the result trio and mutation spectrum when supplied. Artifact indexing and reporting both supply the spectrum; artifact indexing retains adapter/inventory selection, source identity, and the Step `08` path/hash/adapter/sample-order graph, while reporting retains primary-analysis/all-pass selection, source identity/snapshots, and presentation policy. Upstream Step `08`, paired CMH, global BH, PDF/publication, shell/R computation, and the independent oracle remain owner-local. |
| Scientific-context contract | `contracts/scientific_evidence/scientific_context.py` | The Step `10` validator, artifact index, and run report share receipt-only admission of the exact context transaction, including Step `09` binding, reference-window re-derivation, registered motif, logo/statistic semantics, hashes, and row counts. The R producer retains computation/publication; artifact indexing retains inventory graph binding; reporting retains source selection, stable snapshots, bounded display, and figure rendering. |
| Orchestration records | `contracts/orchestration/` and `orchestration/local_pilot/inspection.py` | Contracts own parsing, closed schemas, cross-field validation, and canonical JSON. Within local pilot, inspection owns equivalent direct-path admission of schema-named immutable run records for lifecycle, task, and reporting. Hash-reference resolution, schema-free or supplied in-memory records, publication, fsync, locking, processes, rollback, owner-specific semantic checks, and state transitions remain owner-local; functional owners do not import this seam. |
| Source and artifact-root authority | `libraries/source_authority.py` | Reporting and the local lifecycle share canonical source-checkout/package identity plus a distinct artifact-source root. Git cleanliness is lifecycle attempt policy, not a reporting-transaction success claim. |
| Controlled child startup | `libraries/process_environment.py` | Runtime-availability evidence and local orchestration share removal of inherited shell startup hooks, exact guarded R startup/environment selectors, and the selected-Java environment used for GATK. The R seam selects an existing library and never installs, restores, bootstraps, or downloads dependencies; the Java seam selects canonical `<JAVA_HOME>/bin/java` and removes ambient JVM/GATK selectors without owning tool versions or scientific commands. |
| Selected-Java GATK bridge | `libraries/gatk_invocation.sh` | Step `00c` and Step `05` share only the bound Python handoff into the controlled Java/GATK environment. Each stage retains executable precedence, minimum-version policy, arguments, transaction, validation, and scientific command ownership. |
| Installed R-package identity | `libraries/installed_package_identity.py` | Local-pilot doctor and lifecycle share deterministic no-follow identity for exact canonical installed-package trees. Namespace/version policy remains in runtime admission; symlinks and special entries fail closed. |
| Application logging | `libraries/application_logging/` | This neutral, stage-independent two-sink foundation owns resolved controls, attempt records, protected persistence, projection, and redaction primitives. Grouped local-pilot `run`/`resume` control is the first production adopter: an execute owns exactly one compute-side application attempt, while scheduler submission transport and valid dry-run own none. Confirmed `emrys doctor --repair` is the bounded maintenance adopter; diagnosis, preview, refusal, and pre-authority interruption own no log. Application logs default to `<project-root>/logs/application`; scheduler OUT/ERR remain separate under `<project-root>/logs`. Each adopter retains its own computation, rollback, recovery, streams, and exit authority. The packaged-Python production-import roster is mechanically guarded. |

These are the complete approved neutral implementation seams. Similar names or
two local helpers do not create sharing authority. Keep the first use local;
extract only proven equivalent behavior into the narrowest neutral owner with
independent API and consumer tests.

`libraries/alignments/bed.py` currently serves only the Step `00b` validator and
is not an approved cross-owner seam. Its present placement does not authorize a
second consumer or generic BED API; any relocation or reuse requires a bounded
consolidation decision.

## Dependency direction

Invocation and artifact consumption are distinct from source imports. Public
entry points may be invoked across owners; private implementation may not be
imported across peers.

| Owner | May import | May invoke or consume | Prohibited |
| --- | --- | --- | --- |
| Package metadata | standard/external libraries only | none | implementation or composition owners |
| CLI composition | The exact owner-declared current composition roster plus the exact transitions below | supported grouped public routes over those owner modules | every target outside the two explicit rosters; no seam becomes a general import API |
| `contracts/` | standard/external libraries and other contracts; only the exact transitions below may reach implementation | none | every other EMRYS implementation dependency |
| `libraries/` | `contracts/` and lower neutral libraries in an acyclic chain | none | functional, ingestion, application, or reporting owners |
| `stages/`, `analyses/`, `evidence/` | `contracts/`, approved `libraries/`, owner-local code | owner-local tools and peer artifacts through contracts | peer implementation, ingestion, or reporting implementation |
| `ingestion/` | `contracts/`, approved `libraries/`, ingestion-local code | external inputs; emitted validated declarations | functional-owner implementation or execution |
| `orchestration/` | `contracts/`, approved `libraries/`, orchestration-local code, and the exact reporting seams and transitions below | public owner commands/capabilities and declared artifacts | peer-private implementation, ingestion, or scientific logic outside a named seam or transition |
| `reporting/` | `contracts/`, approved `libraries/`, reporting-local code | explicit public artifacts and summaries | functional-owner implementation, input discovery, or analysis execution |

Scientific functional-owner data flow follows the explicit semantic DAG edges
in `STAGE_MAP.md`; lifecycle, admission, reporting, and orchestration flows
remain with their artifact and owner contracts and the current architecture.
No owner infers dependency order from numeric aliases, filenames, globs,
neighboring directories, validator imports, or historical execution order.
Reporting is a downstream projection and never promotes computational
candidates into an external scientific or biological claim.

Application coordination is intentionally not given blanket import permission
to functional owners. Its current direct calls are exact transitions while
`AC-SLICE-03` through `AC-SLICE-05` decide whether the final capability boundary
uses imports, injected callables, commands, or another representation. One
transition cannot be copied to justify another edge.

### Current CLI composition seams

The grouped `src/emrys/__main__.py` dispatcher may import only this exact
current roster. The roster is
descriptive current behavior, not the future application API. A new target or
a stale target fails the source-dependency gate so owner privacy and public CLI
composition are reviewed together.

| ID | Exact current target | Current grouped-CLI purpose |
|---|---|---|
| `CLI-SEAM-001` | `emrys.analyses.paired_cmh_candidate_ranking.validator` | Owner validation command |
| `CLI-SEAM-002` | `emrys.analyses.scientific_context_projection.validator` | Owner validation command |
| `CLI-SEAM-003` | `emrys.contracts.artifacts.validator` | Artifact-contract validation command |
| `CLI-SEAM-004` | `emrys.evidence.canonical_bam_qc.validator` | Owner validation command |
| `CLI-SEAM-005` | `emrys.evidence.reference_provenance.reconciler` | Reference-provenance reconciliation command |
| `CLI-SEAM-006` | `emrys.evidence.rseqc_orientation.validator` | Owner validation command |
| `CLI-SEAM-007` | `emrys.evidence.runtime_availability.inspector` | Runtime inspection command |
| `CLI-SEAM-008` | `emrys.evidence.storage_inventory.inspector` | Storage inventory command |
| `CLI-SEAM-009` | `emrys.evidence.storage_inventory.qualification` | Storage qualification command |
| `CLI-SEAM-010` | `emrys.ingestion.sample_manifest_admission.validator` | Input-manifest admission command |
| `CLI-SEAM-011` | `emrys.libraries.source_authority` | Controlled-runtime admission for grouped dispatch |
| `CLI-SEAM-012` | `emrys.orchestration.local_pilot.all_pass` | Current all-pass inspection command |
| `CLI-SEAM-013` | `emrys.orchestration.local_pilot.doctor` | Current readiness command |
| `CLI-SEAM-014` | `emrys.orchestration.local_pilot.control` | Current plan/execute/inspect commands |
| `CLI-SEAM-015` | `emrys.orchestration.local_pilot.onboarding` | Current onboarding commands |
| `CLI-SEAM-016` | `emrys.orchestration.local_pilot.synthetic_fixture` | Current synthetic-fixture command |
| `CLI-SEAM-018` | `emrys.stages.canonical_bam.validator` | Owner validation command |
| `CLI-SEAM-019` | `emrys.stages.cohort_candidate_preprocessing.validator` | Owner validation command |
| `CLI-SEAM-020` | `emrys.stages.duplicate_marking.validator` | Owner validation command |
| `CLI-SEAM-021` | `emrys.stages.fasta_sidecars.validator` | Owner validation command |
| `CLI-SEAM-022` | `emrys.stages.gtf_to_bed12.converter` | Owner conversion command |
| `CLI-SEAM-023` | `emrys.stages.gtf_to_bed12.validator` | Owner validation command |
| `CLI-SEAM-024` | `emrys.stages.mechanical_orientation.validator` | Owner validation command |
| `CLI-SEAM-025` | `emrys.stages.partitioned_cohort_mpileup.validator` | Owner validation command |
| `CLI-SEAM-026` | `emrys.stages.split_n_cigar.validator` | Owner validation command |
| `CLI-SEAM-027` | `emrys.stages.star_alignment.validator` | Owner validation command |
| `CLI-SEAM-028` | `emrys.stages.star_index.validator` | Owner validation command |

### Fixed orchestration-to-reporting seams

The local-pilot application may cross into reporting only through these exact
edges. Lifecycle and historical inspection validate receipts; the dedicated
reporting operation owns the fixed artifact-index → run-summary → HTML sequence.
No functional owner or grouped command imports reporting internals directly.

| Exact source | Exact target | Purpose |
|---|---|---|
| `emrys.orchestration.local_pilot.lifecycle` | `emrys.reporting.transaction_validation` | Historical receipt validation during Attempt inspection |
| `emrys.orchestration.local_pilot.reporting_boundary` | `emrys.reporting.transaction_validation` | Semantic validation before immutable reporting completion |
| `emrys.orchestration.local_pilot.reporting_operation` | `emrys.reporting._artifact_index.context` | Prepare the first fixed reporting transaction |
| `emrys.orchestration.local_pilot.reporting_operation` | `emrys.reporting._artifact_index.publication` | Publish the first fixed reporting transaction |
| `emrys.orchestration.local_pilot.reporting_operation` | `emrys.reporting._artifact_index.models` | First-transaction error identity |
| `emrys.orchestration.local_pilot.reporting_operation` | `emrys.reporting._run_summary.builder` | Prepare the second fixed reporting transaction through `prepare_context` |
| `emrys.orchestration.local_pilot.reporting_operation` | `emrys.reporting._run_summary.publication` | Publish the second fixed reporting transaction |
| `emrys.orchestration.local_pilot.reporting_operation` | `emrys.reporting._run_summary.models` | Second-transaction error identity |
| `emrys.orchestration.local_pilot.reporting_operation` | `emrys.reporting.report` | Final fixed HTML transaction |
| `emrys.orchestration.local_pilot.reporting_operation` | `emrys.reporting._run_report.publication` | Publish the final fixed HTML transaction |
| `emrys.orchestration.local_pilot.reporting_operation` | `emrys.reporting._run_report.models` | Final-transaction error identity |

### Bounded current import transitions

These exceptions preserve observed current behavior while preventing the
exception roster from becoming the target architecture. The source-dependency
ratchet admits only the exact source/target pair, rejects any neighboring edge,
and fails when an entry becomes stale. Resolution means either removing the
edge after its successor design supplies the final boundary or recording an
explicit permanent justification in the durable owner.

| ID | Exact current import | Protected current behavior | Successor and exit condition |
|---|---|---|---|
| `SRC-TRANS-001` | `contracts/artifacts/_artifact_contracts/schema.py` → `emrys.libraries.validation` | Artifact-schema path and digest validation | `AC-SLICE-07`: remove the upward contract dependency after lifecycle/admission ownership is selected, or justify the final neutral placement. |
| `SRC-TRANS-002` | `contracts/orchestration/api.py` → `emrys.libraries.source_authority` | Controlled Python argument construction and admission for the bound `python -m snakemake` command prefix | `AC-SLICE-05`: move command construction behind the selected execution/mechanism boundary or justify the final neutral placement. |
| `SRC-TRANS-003` | `contracts/scientific_evidence/step08.py` → `emrys.libraries.validation` | Shared failed-attempt normalization and file-digest mechanics | `AC-SLICE-04` and `AC-SLICE-07`: settle operation and artifact-integrity ownership, then remove or permanently justify the dependency. |
| `SRC-TRANS-004` | `contracts/scientific_evidence/step08.py` → `emrys.libraries.validation.tsv` | Strict TSV contract mechanics | `AC-SLICE-04`: retain strict parsing while selecting the final operation/contract boundary. |
| `SRC-TRANS-005` | `contracts/scientific_evidence/step08.py` → `emrys.libraries.alignments.orientation` | Fixed mechanical-orientation vocabulary and labels | `AC-SLICE-04`: retain the semantic vocabulary while selecting its final neutral owner. |
| `SRC-TRANS-006` | `contracts/scientific_evidence/step09.py` → `emrys.libraries.alignments.orientation` | Step `09` orientation-policy admission | `AC-SLICE-04`: preserve the single orientation authority without broadening the dependency. |
| `SRC-TRANS-007` | `orchestration/local_pilot/doctor.py` → `emrys.evidence.runtime_availability.inspector` | Project Doctor composes the existing runtime inspection capability for diagnosis and post-repair requalification | `AC-SLICE-19` preserves this exact public capability seam rather than duplicating inspection. Reconsider only with a concrete generalized capability/API simplification. |
| `SRC-TRANS-008` | `orchestration/local_pilot/doctor.py` → `emrys.evidence.storage_inventory.qualification` | Project Doctor composes admitted final storage qualification without reimplementing storage evidence | `AC-SLICE-19` preserves this exact public capability seam. Any future placement change must retain evidence attribution and fail-closed qualification. |
| `SRC-TRANS-009` | `orchestration/local_pilot/lifecycle.py` → `emrys.evidence.runtime_availability.inspector` | Runtime re-admission before execution/reuse | `AC-SLICE-03`, `AC-SLICE-05`, and `AC-SLICE-08`: preserve re-admission and evidence attribution while selecting the final boundary. |
| `SRC-TRANS-010` | `orchestration/local_pilot/lifecycle.py` → `emrys.evidence.storage_inventory.qualification` | Storage re-admission before execution/reuse | `AC-SLICE-05` and `AC-SLICE-06`: preserve fail-closed qualification and recovery while selecting the final boundary. |
| `SRC-TRANS-011` | `orchestration/local_pilot/onboarding.py` → `emrys.stages.gtf_to_bed12.converter` | Reference GTF/FASTA compatibility using the current normalization implementation | `AC-SLICE-03` and `AC-SLICE-04`: select a public capability/contract boundary without duplicating GTF semantics. |
| `SRC-TRANS-012` | `orchestration/local_pilot/onboarding.py` → `emrys.evidence.runtime_availability.inspector` | Project runtime discovery and admission through the public inspection capability | `AC-SLICE-08` and `RUNTIME-01`: preserve one runtime-inspection authority while Project orchestration owns admission. |

### Automated import projection

[`tests/tools/source_dependencies.py`](../../../tests/tools/source_dependencies.py)
uses the standard-library AST and Git's tracked-plus-untracked, non-ignored
inventory to check statically declared imports and recognized literal
standard-library dynamic import forms without importing product modules or
writing the tree. It enforces the stable negative directions above,
functional-owner isolation, exact current CLI composition, private-module
isolation, acyclicity between neutral library owners, explicit classification
for every product source domain, the exact fixed reporting seams,
and the exact transition roster. Focused tests keep the executable
seam/transition rosters equal to the tables above.

The checker deliberately does not perform general dynamic-import data-flow
inference or infer runtime invocation, native shell/R relationships, workflow
scheduling, artifact flow, scientific semantics, or authority from an import
alone. Those remain with the current architecture, `STAGE_MAP.md`, owner
contracts, and direct tests. It does not require future `project`, `run`,
`stage`, `execution`, `policy`, or `artifact_store` packages.

## Public-interface and future boundary

Owner-specific public shell, Python, R, and SLURM entry points remain with their
functional owner. The unreleased internal Python distribution packages only
explicitly migrated import owners and their named resources; it does not imply
portable repository-root semantics. Its installed `python -I -m emrys` module
interface contains explicitly migrated owner routes, the read-only semantic
all-pass/readiness checks, and the source-checkout-bound fixed-profile control
routes. `orchestration/local_pilot/control.py` and `materialization.py` are the
single public application owner for that projection. The dedicated
`reporting_operation.py` coordinator is the only owner allowed to compose the
three fixed reporting producers; the grouped command does not expose those
producers separately. The packaged internal task module is invoked only by the
fixed source-checkout workflow; it is not a public lifecycle command, scheduler
abstraction, universal transaction framework, or generic stage dispatcher.
