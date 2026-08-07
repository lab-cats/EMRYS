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
| `evidence/` | Operational/scientific evidence collection and review packaging that does not become peer computation. |
| `reporting/` | Artifact adaptation, canonical run summaries, projections, templates, styles, and static rendering. |
| `ingestion/` | External-input admission and diagnostics; no implemented orchestration runner. |

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

## Approved shared seams

| Seam | Neutral owner | Current consumers and boundary |
| --- | --- | --- |
| Validation-report publication | `libraries/validation_report.py` | Owner validators exact-load one private identity. Parsing/check rosters, evidence rows, CLI, and recovery remain owner-local. |
| BAM validation | `libraries/bam_validation.py` | Step `02`, `04`, and `05` validators only. Stage-specific checks and evidence remain local. |
| Reference contig parsing | `libraries/reference_contigs.py` | Reference provenance and Step `00c`/`05` validators. Agreement policy, reporting, and publication remain local. |
| Executable-value resolution | `libraries/executable_resolution.sh` | Step `00c`, `05`, `06`, `07`, and `08` producers. Tool precedence, version policy, commands, and failures remain local. |
| Step `08` contract | `contracts/scientific_evidence/step08.py` | Step `08`, Step `09`, Step `09c`, and artifact consumers share headers/vocabulary and input validation, not algorithms or publication. |
| Step `09` contract | `contracts/scientific_evidence/step09.py` | Step `09`, Step `09c`, and artifact consumers share the public output contract, not CMH implementation or review policy. |
| Review-package contract | `contracts/scientific_evidence/review_package.py` | Step `09c`, artifact indexing, and run-summary science share the public package roster/state reducer, not private evidence policy or recovery. |

These are the complete approved neutral implementation seams. Similar names or
two local helpers do not create sharing authority. Keep the first use local;
extract only proven equivalent behavior into the narrowest neutral owner with
independent API and consumer tests.

## Dependency direction

Invocation and artifact consumption are distinct from source imports. Public
entry points may be invoked across owners; private implementation may not be
imported across peers.

| Owner | May import | May invoke or consume | Prohibited |
| --- | --- | --- | --- |
| `contracts/` | standard/external libraries only | none | every NORAD implementation domain |
| `libraries/` | `contracts/` and lower neutral libraries in an acyclic chain | none | functional/application owners |
| `stages/`, `analyses/`, `evidence/` | `contracts/`, approved `libraries/`, owner-local code | owner-local tools and peer artifacts through contracts | peer implementation, ingestion, or reporting implementation |
| `ingestion/` | `contracts/`, approved `libraries/`, ingestion-local code | external inputs; emitted validated declarations | functional-owner implementation or execution |
| `reporting/` | `contracts/`, approved `libraries/`, reporting-local code | explicit public artifacts and summaries | functional-owner implementation, input discovery, or analysis execution |

Cross-owner data flow follows the explicit edges in `STAGE_MAP.md`. No owner
infers dependency order from numeric aliases, filenames, globs, neighboring
directories, validator imports, or historical execution order. Reporting is a
downstream projection and never promotes computational or scientific state.

## Public-interface and future boundary

Owner-specific public shell, Python, R, and SLURM entry points remain with their
functional owner. There is no installed CLI, package distribution,
orchestration engine, scheduler abstraction, descriptor loader, universal
transaction framework, or generic stage dispatcher. Those remain potential
future capabilities, not current topology.
