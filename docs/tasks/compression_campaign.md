# Compression campaign intake

Status: **temporary discovery record**

Review progress: **233 of 393 files**

Started: **2026-09-02**

This file preserves findings discovered while reviewing the cumulative
architecture change. It is not a second backlog, a design specification, or
authority to implement a proposed change. The
[`COMPRESS-01`](backlog_matrix.md#repository-maintenance) row owns the intake;
the backlog remains the only task authority.

Examples below are evidence of recurring patterns. Repairing one cited line or
file does not resolve the finding. After the architecture campaign closes, the
complete review will be grouped into finite implementation tasks, transferred
to the backlog, and this file will be deleted.

## Campaign rules

- Prefer existing language, library, packaging, validation, and workflow tools
  before adding bespoke machinery.
- Each implementation slice must remove a meaningful amount of maintained
  product code and must not grow the product-file count unless an explicit,
  quantified exception is approved.
- Deleting tests, documentation, or evidence does not offset product growth.
- Preserve scientific meaning, immutable Run identity, provenance, publication,
  recovery, concurrency, and supported public behavior. Delete checks for
  impossible states only after their producers and mutation paths are audited.
- Exact retained evidence may be deleted only with separate user approval.
- Rename or extract code only as part of a caller-complete simplification. Do
  not perform repository-wide cosmetic churn or replace one large abstraction
  with many one-caller wrappers.
- Documentation and code must explain their purpose to the intended reader in
  common language without requiring campaign history.

## Current finding families

| Family | Representative observations | Present disposition |
|---|---|---|
| CI control and latency | CI remains slow; manual dispatch exposes only a few long lanes and cannot freely compose ordinary checks. | Manual lane selection is architecture-closeout work under `CI-01`. Measurement and substantive critical-path reduction continue after closure. |
| Reader-oriented documentation | Much of the documentation assumes complete EMRYS context or uses internal vocabulary before explaining purpose. | Record as a repository-wide future pass. Individual wording edits do not close it. |
| Documentation ownership | `configs/README.md` contains setup/runtime procedure; Architecture contains validation-status prose; Runbook contains developer CI/task-selection material; Troubleshooting contains scientific interpretation; logging and Run-coordinator contracts may mix context with exact owner behavior. | Correct clear current ownership errors during closeout. Audit every surviving document, contract, and directory guide as a future family. |
| Examples and configuration guidance | Execution-profile examples do not explain fields or top-level resource groups; `qos` is unexplained. | Audit all human-authored examples for self-explanation. Retain the standard Slurm `qos` spelling and explain Quality of Service rather than add a cosmetic schema migration. |
| Code comprehension | Names such as `executable`, `_paths`, `build_context`, and `Publication` lack useful context; fixed-position tuples and opaque mappings obscure meaning; large modules have unhelpful opening docstrings. | Future repository-wide owner audit. The Step 09 threshold tuple and `application_model.py`/`artifact_inventory.py` docstrings are examples, not the scope boundary. |
| Module size and responsibility | Processing producers and application owners may combine admission, paths, locking, execution, validation, rollback, publication, and evidence in one file. | Measure responsibility and duplication across the full owner family before splitting or sharing anything. Prefer deletion and a few cohesive owners over micro-modules. |
| Repeated protection and evidence logic | Locking, validation, evidence, publication, and defensive negative cases appear repeatedly across owners. | Compare threat models and semantics first. Share only truly identical mechanics; delete redundant or impossible-state protection; preserve distinct trust/recovery boundaries. |
| Coverage and branch surface | Run-coordinator control-plane and runtime-admission branch ratios are low. | Treat this first as a branch/complexity audit, not an instruction to add tests. Delete low-value branches, then add focused protection only for retained high-risk behavior. |
| Schema and compatibility surface | Many schema generations, confusing directory/version labels, historical artifact formats, repeated shape checks, and alternative configuration spellings remain. | Inventory every reader, writer, registry, persisted record, and compatibility requirement. Do not retire “v3” as a class: run-summary v3 is active while report-receipt v3 appears historical. Evidence deletion remains separately approval-gated. |
| Configuration normalization | Paired-CMH accepts or derives overlapping forms such as `target_change` and `rna_ref`/`rna_alt`; generated records may be revalidated after construction. | Audit external-provider and public-input boundaries before deleting normalization. Remove alternate forms and self-validation only when no supported reader requires them. |
| Scripts and historical stage language | Numeric step names, standalone owner commands, shell owners, inline/generated programs, and a site-specific Step 05 validation script remain. | Existing `OPS-03` owns caller-complete retain/migrate/retire decisions. Give semantic names only to surviving programs during real migration. |
| Contracts, READMEs, and docstrings | Some READMEs and contracts duplicate one another; others are so terse that their purpose is unclear. | Exact cross-language/public behavior remains in contracts. Implementation purpose belongs in concise docstrings. Remove duplication owner by owner rather than copying contracts into code. |
| Artifact and source topology | Artifact/schema guides do not orient a new reader; `SOURCE_TOPOLOGY.md` and its bespoke import-edge tooling duplicate detailed path rosters. | Preserve meaningful dependency direction. Later evaluate a maintained import-boundary tool and delete hand-maintained edge lists when source can be authoritative. |
| Documentation gate | `validate_structure.py` hard-codes retired paths in addition to checking current owners, links, anchors, and Mermaid structure. | Keep the anti-revival list while older stacked PRs can restore deleted files. After integration, remove that historical blacklist unless a current threat justifies it; retain only useful structural checks. |
| Analysis extension guidance | Multiple named Analyses are supported, but there is no practical walk-through for adding an external computation provider and bespoke reporter. | Retain as a future documentation deliverable based on one minimal working provider, without creating a generic workflow or report DSL. |
| Golden-path workspace behavior | The operator should not manually create required Project directories and should not need internal manifests or execution machinery. | Already a permanent Project/setup requirement. Do not add checkout-level `data/raw` or `data/full`; scientific inputs remain referenced, and filenames cannot safely infer conditions or replicates. |

## Addressed before this intake

The following cited instances no longer require work unless the remaining
review finds a broader live pattern:

- obsolete diagrams and stale architecture-index links were removed; one
  current-user pipeline diagram remains;
- the functional-owner repository exception and `docs/demo` were removed;
- the global orchestration contract and orchestration-readiness document were
  retired;
- decision records, the test baseline, engineering conventions, the
  documentation index, and paired-CMH/scientific-context READMEs were
  substantially compressed;
- the stale sitemap, rolling handoff, resource README, and path-heavy standalone
  scientific-context command were removed;
- the glossary was retained as the concise terminology authority;
- `data/test` and `refs/test_star_index` have no tracked contents; and
- `project.yaml` already supports multiple named Analyses, with one Analysis
  selected per Run.

## Rejected proposals and retained underlying concerns

| Proposal not accepted | Technical reason | Concern that remains |
|---|---|---|
| Flatten `src/emrys` into `src` | `src/` is the standard packaging root and `emrys/` is the stable import package. Flattening would destroy or fragment package identity. | Audit unnecessary package and module fragmentation within `emrys`. |
| Add repository `data/raw` and `data/full` placeholders with automatic discovery | Git cannot retain empty directories without placeholders; Projects intentionally live independently of the source checkout; filenames do not establish biological design. | `emrys init` must create all EMRYS-owned Project directories and ingestion helpers must request explicit scientific metadata. |
| Rename `qos` to a longer field | QoS is Slurm's established term, and a public-schema migration adds more surface than it removes. | Explain it in examples and user-facing help. |
| Maintain a handoff document on every commit | It would duplicate live Git, PR, check, and task state and immediately become another stale registry. | Generate a compact handoff at an actual transfer boundary when needed. |
| Rename every numeric script immediately | Names participate in callers, package data, tests, and sometimes persisted identities; cosmetic churn would not simplify execution. | Rename retained survivors semantically during `OPS-03` migration. |
| Move whole contracts into docstrings | That would hide or duplicate cross-language behavior and recovery guarantees. | Make module docstrings explain local purpose, inputs, outputs, and architectural role. |
| Replace every `row[column]` access | Declared schema iteration can be clear and appropriate. | Replace fixed-position or context-free structures where named values materially improve comprehension. |
| Retire all v3 schemas | Several v3 records remain active and “v3” spans unrelated contract families. | Audit each exact schema and historical reader before consolidation. |

## Work allowed before architecture closure

Before the cumulative architecture stack is reviewed, repaired, and merged,
implementation is limited to:

1. correctness, packaging, CI, or integration defects;
2. false or stale descriptions of the system that exists;
3. documentation/backlog ownership corrections needed to close the campaign;
4. the minimum CI controls needed to validate exact cumulative revisions; and
5. recording or dismissing newly reviewed findings here.

Broad code, schema, validation, naming, and module-structure implementation
waits until architecture closure. This prevents the review target from moving
and avoids building the next campaign against an unintegrated stack.

## Intake exit

The intake is complete only when:

1. all 393 files have been reviewed;
2. every finding has one evidenced disposition;
3. accepted findings are consolidated by root cause rather than example;
4. each implementation family has a finite outcome, acceptance criteria,
   importance, complexity, and evidence boundary in the backlog;
5. architecture-closeout PRs are reviewed and integrated; and
6. this temporary file is deleted after the transfer is verified.
