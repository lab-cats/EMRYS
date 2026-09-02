# Source ownership and dependency direction

This file owns current Python import boundaries, approved shared seams, and
exact admitted exceptions. [`STAGE_MAP.md`](STAGE_MAP.md) owns semantic
identities and artifact edges; the [platform decision](../../../docs/design/decisions/platform-direction.md#ratified-responsibility-and-dependency-model)
owns target responsibilities; the [functional-owner inventory](../../../docs/architecture/FUNCTIONAL_OWNER_INVENTORY.md)
routes high-level responsibility. Parsers, owner contracts, and direct tests
own exact commands and behavior.

## Current source domains

| Domain | Responsibility |
| --- | --- |
| Package root | `__init__.py` exposes package metadata; `__main__.py` composes the installed `emrys` command and retains direct module invocation only as an internal/test seam. |
| `contracts/` | Neutral schemas, shared scientific-evidence contracts, identities, and topology contracts. |
| `libraries/` | Narrow shared implementation proven across named consumers; never a generic utility bucket. |
| `stages/` | Preprocessing and transformation owners keyed by the slugs in `STAGE_MAP.md`. |
| `analyses/` | Public computation-provider contract/admission facade plus scientific analysis owners distinct from preprocessing stages; provider-private code remains owner-local. |
| `evidence/` | Operational and mechanical evidence collection that does not become peer computation. |
| `reporting/` | Public report-provider contract/admission facade, artifact adaptation, canonical run summaries, and static rendering; bespoke scientific views remain with their report provider. |
| `ingestion/` | External-input admission and diagnostics; no implemented orchestration runner. |
| `orchestration/` | Run-coordinator request normalization, reporting projection, content-bound task execution/reuse admission, and lifecycle application policy; no scientific implementation. Static scheduling assets live at root `workflow/`. |

Native assets stay with their behavioral owner. Root `configs/` holds explicit
starter inputs and reference tables; repository tooling under `scripts/` is not
scientific-workflow orchestration.

## Functional-owner shape

Each semantic owner has an adjacent `README.md`, `CONTRACT.md`, native assets,
and mirrored tests; the documentation gate derives these homes from
`STAGE_MAP.md`. Neutral contracts live under `tests/contracts/`, public
producer/consumer agreement under `tests/contract_integration/`, and broader
CLI, scheduler, coverage, and gate protection remains cross-owner.

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
| Executable-value resolution | `libraries/executable_resolution.sh` | Nine named Bash producers across Steps `00a`, `00c`, `01`–`10`, including evidence owners `02b` and `03`; the exact consumer roster is protected directly. Tool precedence, version policy, commands, and failures remain local. |
| Step `08` contract | `contracts/scientific_evidence/step08.py` | Step `08`, Step `09`, and artifact consumers share headers/vocabulary and input validation, not algorithms or publication. |
| Step `09` contract | `contracts/scientific_evidence/step09.py` | The Python producer, validator, artifact index, and run report share the admitted Step `09` formats and reconciliation rules; read-only consumers use `validate_step09_projection` for canonical intrinsic admission of the result trio and mutation spectrum when supplied. Artifact indexing and reporting retain their own selection, identity, snapshot, and presentation responsibilities. Upstream Step `08`, paired CMH/global BH R computation, transaction publication, and the independent oracle remain owner-local. |
| Scientific-context contract | `contracts/scientific_evidence/scientific_context.py` | The Step `10` validator, artifact index, and run report share receipt-only admission of the exact context transaction, including Step `09` binding, reference-window re-derivation, registered motif, logo/statistic semantics, hashes, and row counts. The R producer retains computation/publication; artifact indexing retains inventory graph binding; reporting retains source selection, stable snapshots, bounded display, and figure rendering. |
| Orchestration records | `contracts/orchestration/` and `orchestration/run_coordinator/inspection.py` | Contracts own parsing, closed schemas, cross-field validation, and canonical JSON. Within run coordinator, inspection owns equivalent direct-path admission of schema-named immutable run records for lifecycle, task, and reporting. Hash-reference resolution, schema-free or supplied in-memory records, publication, fsync, locking, processes, rollback, owner-specific semantic checks, and state transitions remain owner-local; functional owners do not import this seam. |
| Source and artifact-root authority | `libraries/source_authority.py` | Reporting and the local lifecycle share canonical source-checkout/package identity plus a distinct artifact-source root. Git cleanliness is lifecycle attempt policy, not a reporting-transaction success claim. |
| Controlled child startup | `libraries/process_environment.py` | Runtime-availability evidence and local orchestration share removal of inherited shell startup hooks, exact guarded R startup/environment selectors, and the selected-Java environment used for GATK. The R seam selects an existing library and never installs, restores, bootstraps, or downloads dependencies; the Java seam selects canonical `<JAVA_HOME>/bin/java` and removes ambient JVM/GATK selectors without owning tool versions or scientific commands. |
| Selected-Java GATK bridge | `libraries/gatk_invocation.sh` | Step `00c` and Step `05` share only the bound Python handoff into the controlled Java/GATK environment. Each stage retains executable precedence, minimum-version policy, arguments, transaction, validation, and scientific command ownership. |
| Installed provider identity | `libraries/installed_package_identity.py` | Runtime admission plus computation and report providers share deterministic no-follow identity for exact canonical installed package trees. Namespace/version and entry-point policy remain with each admitting owner; symlinks, special entries, and ambiguous providers fail closed. |
| Application logging | `libraries/application_logging/` | This neutral, stage-independent two-sink foundation owns resolved controls, attempt records, protected persistence, projection, and redaction primitives. The complete retained adopter roster is grouped run-coordinator `run`/`resume` execution, automatic reporting within that same log, standalone report generation, and confirmed `emrys doctor --repair`. Scheduler submission, dry-run/refusal/reuse, initialization, validation, runtime discovery, diagnosis, inspection, and debug inspection own no application log; delegated tasks open no second log. Application logs default to `<project-root>/logs/application`; scheduler OUT/ERR remain separate under `<project-root>/logs`. Each adopter retains its own computation, rollback, recovery, streams, and exit authority. The packaged-Python production-import roster is mechanically guarded. |

This table is exhaustive. Similar names do not create sharing authority;
extraction requires proven equivalent consumers and one narrow tested owner.
`libraries/alignments/bed.py` serves only Step `00b` and is not an approved
cross-owner seam.

## Dependency direction

Invocation and artifact consumption are distinct from imports. Public entry
points may cross owners; peer-private implementation may not.

| Owner | May import | May invoke or consume | Prohibited |
| --- | --- | --- | --- |
| Package metadata | standard/external libraries only | none | implementation or composition owners |
| CLI composition | The exact owner-declared composition roster plus the exact exceptions below | supported grouped public routes over those owner modules | every target outside the two explicit rosters; no seam becomes a general import API |
| `contracts/` | standard/external libraries and other contracts; only the exact exceptions below may reach implementation | none | every other EMRYS implementation dependency |
| `libraries/` | `contracts/` and lower neutral libraries in an acyclic chain | none | functional, ingestion, application, or reporting owners |
| `stages/`, `analyses/`, `evidence/` | `contracts/`, approved `libraries/`, owner-local code, and the exact analysis-module facade seam below | owner-local tools and peer artifacts through contracts | peer-private implementation, ingestion, or reporting implementation |
| `ingestion/` | `contracts/`, approved `libraries/`, ingestion-local code | external inputs; emitted validated declarations | functional-owner implementation or execution |
| `orchestration/` | `contracts/`, approved `libraries/`, orchestration-local code, and the exact capability seams and exceptions below | public owner commands/capabilities and declared artifacts | peer-private implementation, ingestion, or scientific logic outside a named seam or exception |
| `reporting/` | `contracts/`, approved `libraries/`, reporting-local code, and the exact analysis-module facade seam below | explicit public artifacts and summaries | provider-private implementation, input discovery, or analysis execution |

Scientific data flow follows `STAGE_MAP.md`; lifecycle, admission, orchestration,
and reporting follow their owner contracts. Numeric aliases, paths, validator
imports, and historical order do not create dependencies. Application
coordination has only the exact capability exceptions below; one exception does
not authorize another.

### Current CLI composition seams

The grouped `src/emrys/__main__.py` dispatcher may import only this exact roster.
The source-dependency gate rejects additions and stale entries.

| ID | Exact current target | Current grouped-CLI purpose |
|---|---|---|
| `CLI-SEAM-001` | `emrys.analyses.paired_cmh_candidate_ranking.validator` | Owner validation command |
| `CLI-SEAM-002` | `emrys.analyses.paired_cmh_candidate_ranking.scientific_context_projection.validator` | Owner validation command |
| `CLI-SEAM-003` | `emrys.contracts.artifacts.validator` | Artifact-contract validation command |
| `CLI-SEAM-004` | `emrys.evidence.canonical_bam_qc.validator` | Owner validation command |
| `CLI-SEAM-005` | `emrys.evidence.reference_provenance.reconciler` | Reference-provenance reconciliation command |
| `CLI-SEAM-006` | `emrys.evidence.rseqc_orientation.validator` | Owner validation command |
| `CLI-SEAM-007` | `emrys.evidence.runtime_availability.inspector` | Technical runtime inspection command under `emrys debug` |
| `CLI-SEAM-008` | `emrys.evidence.storage_inventory.inspector` | Technical storage inventory command under `emrys debug` |
| `CLI-SEAM-009` | `emrys.evidence.storage_inventory.qualification` | Technical storage qualification command under `emrys debug` |
| `CLI-SEAM-010` | `emrys.ingestion.sample_manifest_admission.validator` | Input-manifest admission command |
| `CLI-SEAM-011` | `emrys.libraries.source_authority` | Controlled-runtime admission behind the installed command |
| `CLI-SEAM-012` | `emrys.orchestration.run_coordinator.all_pass` | Current all-pass inspection command |
| `CLI-SEAM-013` | `emrys.orchestration.run_coordinator.doctor` | Current readiness command |
| `CLI-SEAM-014` | `emrys.orchestration.run_coordinator.control` | Current plan/execute/inspect commands |
| `CLI-SEAM-015` | `emrys.orchestration.run_coordinator.onboarding` | Current onboarding commands |
| `CLI-SEAM-016` | `emrys.orchestration.run_coordinator.synthetic_fixture` | Current synthetic-fixture command |
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

### Analysis-module capability seam

Python entry points select the exact computation and report providers named by
an admitted Analysis. Providers, orchestration, and reporting may import only
the public `emrys.analyses` facade; this is not a registry, private-code access,
or a second workflow language. Orchestration freezes the provider descriptor in
the Run; reporting reads that descriptor and declared artifacts without invoking
computation. Doctor alone may import the public `emrys.reporting` facade for
readiness.

### Fixed orchestration-to-reporting seams

Run coordination crosses into reporting only through these exact edges. The
reporting operation owns artifact-index → run-summary → HTML; no functional
owner or grouped command imports reporting internals.

| Exact source | Exact target | Purpose |
|---|---|---|
| `emrys.orchestration.run_coordinator.doctor` | `emrys.reporting` | Admit the same-ID report provider required by a reporting-enabled run |
| `emrys.orchestration.run_coordinator.lifecycle` | `emrys.reporting.transaction_validation` | Historical receipt validation during Attempt inspection |
| `emrys.orchestration.run_coordinator.reporting_boundary` | `emrys.reporting.transaction_validation` | Semantic validation before immutable reporting completion |
| `emrys.orchestration.run_coordinator.reporting_operation` | `emrys.reporting._artifact_index.context` | Prepare the first fixed reporting transaction |
| `emrys.orchestration.run_coordinator.reporting_operation` | `emrys.reporting._artifact_index.publication` | Publish the first fixed reporting transaction |
| `emrys.orchestration.run_coordinator.reporting_operation` | `emrys.reporting._artifact_index.models` | First-transaction error identity |
| `emrys.orchestration.run_coordinator.reporting_operation` | `emrys.reporting._run_summary.builder` | Prepare the second fixed reporting transaction through `prepare_context` |
| `emrys.orchestration.run_coordinator.reporting_operation` | `emrys.reporting._run_summary.publication` | Publish the second fixed reporting transaction |
| `emrys.orchestration.run_coordinator.reporting_operation` | `emrys.reporting._run_summary.models` | Second-transaction error identity |
| `emrys.orchestration.run_coordinator.reporting_operation` | `emrys.reporting.report` | Final fixed HTML transaction |
| `emrys.orchestration.run_coordinator.reporting_operation` | `emrys.reporting._run_report.publication` | Publish the final fixed HTML transaction |
| `emrys.orchestration.run_coordinator.reporting_operation` | `emrys.reporting._run_report.models` | Final-transaction error identity |

### Ratified exact import exceptions

Each stable `SRC-TRANS` identifier admits only its exact source/target pair. The
gate rejects neighboring and stale edges; none is a general import API.

| ID | Exact current import | Protected current behavior | Durable boundary justification |
|---|---|---|---|
| `SRC-TRANS-001` | `contracts/artifacts/_artifact_contracts/schema.py` → `emrys.libraries.validation` | Artifact-schema path and digest validation | Reuse the neutral path/digest implementation without transferring artifact-schema authority. |
| `SRC-TRANS-002` | `contracts/orchestration/api.py` → `emrys.libraries.source_authority` | Controlled Python argument construction and admission for the bound `python -m snakemake` command prefix | Keep one controlled-interpreter authority for the sole backend command. |
| `SRC-TRANS-003` | `contracts/scientific_evidence/step08.py` → `emrys.libraries.validation` | Shared failed-attempt normalization and file-digest mechanics | Reuse neutral validation mechanics without transferring the Step `08` contract. |
| `SRC-TRANS-004` | `contracts/scientific_evidence/step08.py` → `emrys.libraries.validation.tsv` | Strict TSV contract mechanics | Keep one strict TSV implementation while the scientific schema remains owner-local. |
| `SRC-TRANS-005` | `contracts/scientific_evidence/step08.py` → `emrys.libraries.alignments.orientation` | Fixed mechanical-orientation vocabulary and labels | Keep one neutral mechanical-orientation vocabulary. |
| `SRC-TRANS-006` | `contracts/scientific_evidence/step09.py` → `emrys.libraries.alignments.orientation` | Step `09` orientation-policy admission | Reuse that same vocabulary without transferring Step `09` policy. |
| `SRC-TRANS-007` | `orchestration/run_coordinator/doctor.py` → `emrys.evidence.runtime_availability.inspector` | Project Doctor composes the existing runtime inspection capability for diagnosis and post-repair requalification | Compose the existing capability instead of duplicating runtime inspection. |
| `SRC-TRANS-008` | `orchestration/run_coordinator/doctor.py` → `emrys.evidence.storage_inventory.qualification` | Project Doctor composes admitted final storage qualification without reimplementing storage evidence | Compose the existing capability while retaining its evidence attribution and fail-closed admission. |
| `SRC-TRANS-009` | `orchestration/run_coordinator/lifecycle.py` → `emrys.evidence.runtime_availability.inspector` | Runtime re-admission before execution/reuse | Re-admit runtime evidence at the execution trust boundary through its existing owner. |
| `SRC-TRANS-010` | `orchestration/run_coordinator/lifecycle.py` → `emrys.evidence.storage_inventory.qualification` | Storage re-admission before execution/reuse | Re-admit storage evidence at the execution trust boundary through its existing owner. |
| `SRC-TRANS-011` | `orchestration/run_coordinator/onboarding.py` → `emrys.stages.gtf_to_bed12.converter` | Reference GTF/FASTA compatibility using the current normalization implementation | Reuse the single GTF normalization authority without duplicating scientific semantics. |
| `SRC-TRANS-012` | `orchestration/run_coordinator/onboarding.py` → `emrys.evidence.runtime_availability.inspector` | Project runtime discovery and admission through the public inspection capability | Let Project orchestration admit the existing runtime-inspection result rather than duplicate its probes. |

### Automated import projection

[`tests/tools/source_dependencies.py`](../../../tests/tools/source_dependencies.py)
checks tracked source imports, owner isolation, acyclic libraries, CLI and
reporting rosters, and exact exceptions without importing product code or
writing the tree. It does not infer runtime invocation, native-code relations,
workflow scheduling, artifact flow, or scientific semantics; those remain with
`STAGE_MAP.md`, owner contracts, and direct tests.
