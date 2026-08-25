# Source ownership and dependency direction

This file owns current source-domain boundaries, approved shared seams, and
allowed implementation dependencies. The
[`architecture index`](../../../docs/architecture/README.md) organizes the
human views; [`STAGE_MAP.md`](STAGE_MAP.md) owns semantic identities and
artifact edges; the
[`functional-owner inventory`](../../../docs/architecture/FUNCTIONAL_OWNER_INVENTORY.md)
owns exact public programs, jobs, validators, and tests.

## Current source domains

| Domain | Responsibility |
| --- | --- |
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
| R input-contract mechanics | `libraries/input_contract.R` | Step `08`, `09`, and `10` R programs share named-argument parsing, file/hash guards, and strict TSV loading. Argument rosters, defaults, table policy, and scientific algorithms remain owner-local. |
| Executable-value resolution | `libraries/executable_resolution.sh` | Thirteen named Bash producers across Steps `00a`, `00c`, `01`–`10`, including evidence owners `02b` and `03`; the exact consumer roster is protected directly. Tool precedence, version policy, commands, and failures remain local. |
| Step `08` contract | `contracts/scientific_evidence/step08.py` | Step `08`, Step `09`, and artifact consumers share headers/vocabulary and input validation, not algorithms or publication. |
| Step `09` contract | `contracts/scientific_evidence/step09.py` | The validator, artifact index, and run report share `validate_step09_projection` for canonical intrinsic admission of the result trio and mutation spectrum when supplied. Artifact indexing and reporting both supply the spectrum; artifact indexing retains adapter/inventory selection, source identity, and the Step `08` path/hash/adapter/sample-order graph, while reporting retains primary-analysis/all-pass selection, source identity/snapshots, and presentation policy. Upstream Step `08`, paired CMH, global BH, PDF/publication, shell/R computation, and the independent oracle remain owner-local. |
| Scientific-context contract | `contracts/scientific_evidence/scientific_context.py` | The Step `10` validator, artifact index, and run report share receipt-only admission of the exact context transaction, including Step `09` binding, reference-window re-derivation, registered motif, logo/statistic semantics, hashes, and row counts. The R producer retains computation/publication; artifact indexing retains inventory graph binding; reporting retains source selection, stable snapshots, bounded display, and figure rendering. |
| Orchestration records | `contracts/orchestration/` and `orchestration/local_pilot/inspection.py` | Contracts own parsing, closed schemas, cross-field validation, and canonical JSON. Within local pilot, inspection owns equivalent direct-path admission of schema-named immutable run records for lifecycle, task, and reporting. Hash-reference resolution, schema-free or supplied in-memory records, publication, fsync, locking, processes, rollback, owner-specific semantic checks, and state transitions remain owner-local; functional owners do not import this seam. |
| Source and artifact-root authority | `libraries/source_authority.py` | Reporting and the local lifecycle share canonical source-checkout/package identity plus a distinct artifact-source root. Git cleanliness is lifecycle attempt policy, not a reporting-transaction success claim. |
| Controlled child startup | `libraries/process_environment.py` | Runtime-availability evidence and local orchestration share removal of inherited shell startup hooks, exact guarded R startup/environment selectors, and the selected-Java environment used for GATK. The R seam selects an existing library and never installs, restores, bootstraps, or downloads dependencies; the Java seam selects canonical `<JAVA_HOME>/bin/java` and removes ambient JVM/GATK selectors without owning tool versions or scientific commands. |
| Selected-Java GATK bridge | `libraries/gatk_invocation.sh` | Step `00c` and Step `05` share only the bound Python handoff into the controlled Java/GATK environment. Each stage retains executable precedence, minimum-version policy, arguments, transaction, validation, and scientific command ownership. |
| Installed R-package identity | `libraries/installed_package_identity.py` | Local-pilot doctor and lifecycle share deterministic no-follow identity for exact canonical installed-package trees. Namespace/version policy remains in runtime admission; symlinks and special entries fail closed. |
| Application logging | `libraries/application_logging/` | This neutral, stage-independent two-sink foundation owns resolved controls, attempt records, protected persistence, projection, and redaction primitives. No production operation consumes it yet; each operation that adopts it remains the single semantic owner of its attempt, computation, publication, rollback, recovery, streams, and exit. |

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
| `contracts/` | standard/external libraries only | none | every EMRYS implementation domain |
| `libraries/` | `contracts/` and lower neutral libraries in an acyclic chain | none | functional/application owners |
| `stages/`, `analyses/`, `evidence/` | `contracts/`, approved `libraries/`, owner-local code | owner-local tools and peer artifacts through contracts | peer implementation, ingestion, or reporting implementation |
| `ingestion/` | `contracts/`, approved `libraries/`, ingestion-local code | external inputs; emitted validated declarations | functional-owner implementation or execution |
| `orchestration/` | `contracts/`, approved `libraries/`, orchestration-local code, and the direct public `reporting.transaction_validation` completion API | public owner commands and declared artifacts only | peer-private implementation or scientific logic |
| `reporting/` | `contracts/`, approved `libraries/`, reporting-local code | explicit public artifacts and summaries | functional-owner implementation, input discovery, or analysis execution |

Cross-owner data flow follows the explicit edges in `STAGE_MAP.md`. No owner
infers dependency order from numeric aliases, filenames, globs, neighboring
directories, validator imports, or historical execution order. Reporting is a
downstream projection and never promotes computational candidates into an
external scientific or biological claim.

## Public-interface and future boundary

Owner-specific public shell, Python, R, and SLURM entry points remain with their
functional owner. The unreleased internal Python distribution packages only
explicitly migrated import owners and their named resources; it does not imply
portable repository-root semantics. Its installed `python -I -m emrys` module
interface contains explicitly migrated owner routes, the read-only semantic
all-pass/readiness checks, and the source-checkout-bound fixed-profile control
routes. `orchestration/local_pilot/control.py` and `materialization.py` are the
single public application owner for that projection; they do not import peer-
private implementations. The packaged internal task module is invoked only by
the fixed source-checkout workflow; it is not a public lifecycle command, scheduler
abstraction, universal transaction framework, or generic stage dispatcher.
The internal lifecycle consumes only reporting's direct semantic transaction
validator; it does not import `_artifact_index`, `_run_summary`, or
`_run_report` internals.
