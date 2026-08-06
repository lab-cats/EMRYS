# NORAD pipeline plan

This is the canonical current roadmap for pipeline evidence, cross-cutting
packages, approved delivery order, and package acceptance. Task lifecycle
state belongs to [`../tasks/`](../tasks/); checkout and resume state to
[`HANDOFF.md`](../operations/HANDOFF.md); commands to
[`RUNBOOK.md`](../operations/RUNBOOK.md); rationale to
[`DECISIONS.md`](DECISIONS.md); and dated delivery evidence to
[`operations history`](../history/operations/).

## Pipeline

| ID | Purpose | Acceptance boundary | Status |
| --- | --- | --- | --- |
| `00a` | Build STAR index | Source identity, contigs, index structure, and configured overhang inspected | cluster-proven |
| `00b` | Convert GTF to BED12 | BED12 structure, sorting, blocks, and GTF agreement inspected | cluster-proven |
| `00c` | Build FASTA sidecars | FASTA/FAI/DICT identity and contig agreement inspected | cluster-proven |
| `01` | STAR alignment | STAR outputs, logs, mapping summary, and BAM inspected | cluster-proven |
| `02` | Canonical BAM | BAM/BAI, coordinate sorting, read groups, and alignment RG tags inspected | cluster-proven |
| `02b` | BAM QC | quickcheck and flagstat evidence inspected | cluster-proven evidence set |
| `03` | Infer library orientation | RSeQC structure and paired-orientation fractions inspected | cluster-proven |
| `04` | Mark duplicates | BAM/BAI/metrics, sorting, RG preservation, and duplication metrics inspected | cluster-proven |
| `05` | Split N cigars | Declared output transaction and validation inspected | cluster-proven |
| `06` | Split mechanical orientations | Outputs, indexes, and count arithmetic inspected | cluster-proven |
| `07` | Cohort mpileup | Receipts, VCF structure, selectors, hashes, sample order, and counts inspected with real runtime | local mocked-runtime only |
| `08` | Preprocess and annotate VCFs | Three-output transaction, schemas, hashes, ordering, uniqueness, and counts inspected | local real-R fixtures only |
| `09` | Paired CMH ranking | Six-output transaction, statuses, subsets, mutation spectrum, and PDFs inspected | local real-R fixtures only |
| `09c` | Validate scientific evidence | Explicit production evidence reconciled and review state lawfully published | local synthetic fixtures only |

Cluster evidence for Steps `00a` through `06` predates physical source
cutover; migration did not create new runtime proof. Steps `07` through `09`
remain unproved on the cluster, and Step `09c` tooling is not a completed
production review.

## Evidence and reporting packages

| Package family | Responsibility | Current status |
| --- | --- | --- |
| Artifact and review contracts | Public artifact, scientific-review, run-summary, report-receipt, adapter, and deterministic-summary contracts | implemented and fixture-tested |
| Static report exports | Atomic HTML/PDF/summary-TSV/report-receipt publication with explicit table approvals | implemented and locally renderer-tested; no production report |
| Populated demo | Complete synthetic run with approved table roles and bounded HTML/PDF projections | implemented and locally renderer-tested; synthetic evidence only |
| Runtime preflight | Explicit-profile tool, R-namespace, hash, and path-visibility checks | implemented and fixture-tested; CSU batch execution pending |
| Reference provenance | Reference identity, hashes, annotation provenance, and contig reconciliation | implemented and fixture-tested; production execution pending |
| Storage inventory and retention | Read-only storage measurement plus explicit policy recording | implemented and fixture-tested; production inventory and approvals pending |
| Step `00a` through `09` reports | Owner-local validation, typed artifact adaptation, and summary/report propagation | implemented and locally fixture-tested; evidence ceilings remain as in the pipeline matrix |
| Refactor audit and test baseline | Current finding/recheck routes and non-regression policy | current routes in [`REFACTOR_AUDIT.md`](REFACTOR_AUDIT.md) and [`TEST_BASELINE.md`](TEST_BASELINE.md); dated evidence is historical |
| Physical ownership | Fourteen DAG owners, neutral contracts/libraries, reporting, and evidence tools in final homes | source-topology migration complete at the local/static ceiling |
| Documentation | User pipeline overview and compressed canonical owner views | [`DOC-PIPE-04`](../tasks/COMPLETED/DOC-PIPE-04-create-user-pipeline-overview.md) complete; final central reconciliation in progress |

## Active critical runway

The physical migration is complete for all fourteen semantic DAG owners,
artifact and scientific-evidence contracts, reporting, reference-contig
parsing, evidence tools, contract goldens, and validation-roster agreement.
Exact final homes live in
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md); current
public surfaces live in the
[`functional-owner inventory`](../architecture/FUNCTIONAL_OWNER_INVENTORY.md).

The approved tranche is deliberately narrow:

1. finish central documentation reconciliation;
2. complete [`SIZE-07A`](../tasks/COMPLETED/SIZE-07A-decompose-artifact-index-builder.md),
   [`SIZE-07B`](../tasks/COMPLETED/SIZE-07B-decompose-scientific-validation-tooling.md),
   [`SIZE-07D`](../tasks/TODO/SIZE-07D-decompose-run-summary-builder.md),
   [`SIZE-07E`](../tasks/TODO/SIZE-07E-resolve-step08-r-module-size.md), and
   [`SIZE-07F`](../tasks/TODO/SIZE-07F-decompose-artifact-contract-validator.md)
   in that order, each with its own outcome commit; and
3. begin `LIB-03` with one observed repeated seam only, defined just in time.

`SIZE-07A` and `SIZE-07B` are complete. The later size slices remain queued.
Each size slice owns a live refresh of only its target's size,
responsibilities, consumers, risks, and disposition; the standalone repo-wide
refresh was retired through
[`SIZE-07`](../tasks/COMPLETED/SIZE-07-refresh-large-file-inventory.md).

The recorded reciprocal `REVIEW-UX-03` task edges are not an execution blocker
for this explicitly authorized tranche; correcting general task-edge semantics
through `TASK-REG-01` is out of scope. RPT-05A and required final-owner moves
are complete. A slice must still stop if focused inspection exposes a changed
interface, schema, dependency direction, shared-infrastructure contract,
scientific meaning, evidence ceiling, or safety authority that the tranche did
not authorize. Step `08` algorithmic extraction remains specifically barred;
`SIZE-07E` must use a provably non-algorithmic seam or an explicitly approved,
time-bounded exception.

Formal [`ONBOARD-03A`](../tasks/TODO/ONBOARD-03A-publish-researcher-onboarding.md)
remains blocked on the local-pilot setup/orchestration/E2E family and must not
claim fresh-clone proof. The current root README and
[`PIPELINE_OVERVIEW.md`](../architecture/PIPELINE_OVERVIEW.md) provide the
bounded entry path for a user whose environment is already configured.

### Residual source-topology convergence

The current residual roster contains 82 tracked repository-level paths, all
`RETAIN_ROOT`. Root `jobs/` is absent; all 15 tracked SLURM files are
owner-local. The manual tool probe lives with runtime preflight, the unused
generic template and two unconsumed workflow profiles are retired, and the
mixed wrapper-contract suite remains permanent cross-owner repository
protection. There are no current residual `MOVE`, `DEFER`, or `RETIRE` groups.

This count covers only the bounded residual roots defined by the completed
source-topology audit; it is an inspection check, not a permanent repository-
size target. Final owner-local implementation and mirrored tests are excluded.
The functional-owner inventory owns the exact ledger and must change whenever
a tracked residual path changes disposition.

### Recovered proposal families

The unselected local-pilot family remains:

```text
SETUP-03A + INTAKE-03A + PROFILE-03A
                -> CLI-03A -> E2E-03A -> ONBOARD-03A
```

`INTAKE-03A` also lacks the accepted `INTAKE-02E` design. These are interface
and readiness relationships, not automatic selection. UNREFINED records and
other TODO proposals do not enter the approved runway without review and user
direction.

## Approved current delivery lineage

The current branch descends from the completed physical-owner and residual-
topology convergence campaigns. The active tranche uses sequential,
outcome-oriented commits: `DOC-PIPE-04` has its own completed commit; each of
`SIZE-07A`, `SIZE-07B`, `SIZE-07D`, `SIZE-07E`, and `SIZE-07F` must have its
own commit; the bounded `LIB-03` seam must not be bundled into a size slice.
Final applicable validation, genuinely affected central reconciliation, and
one authorized push occur after the tranche. Exact commit ancestry and dated
delivery evidence belong in Git and
[`operations history`](../history/operations/), not here.

## Package acceptance criteria

Every package must:

- stay within one approved owner/outcome and preserve public behavior unless a
  separately authorized decision says otherwise;
- update directly affected tests, contracts, and operational documentation;
- preserve file modes, deterministic bytes, atomic publication, rollback,
  failure behavior, and evidence vocabulary where they are contracted;
- keep stage-specific semantics with their stage and introduce a neutral seam
  only when multiple real consumers and independent tests justify it;
- record characterization as local, real-runtime, cluster, scientific-review,
  or biological-readiness evidence without promoting between levels;
- run focused checks during the tranche and the complete applicable gate on
  the final combined tree; and
- close its card in the same canonical outcome commit, repairing only links
  required by the lifecycle move.

Documentation-only work additionally requires one mutable owner per fact,
valid lifecycle links, preserved unique scientific/validation evidence, no
executable or contract behavior change, and a passing documentation gate.

### Documentation consolidation

- roadmap and evidence state stay here; current checkout state stays in
  `HANDOFF.md`; commands stay in `RUNBOOK.md`; rationale stays in
  `DECISIONS.md`; and symptoms and recovery stay in `TROUBLESHOOTING.md`;
- current topology stays in `ARCHITECTURE.md`, target constraints in
  `FUTURE_ARCHITECTURE.md`, and exact homes in source contracts;
- cards link to canonical owners instead of restating them; and
- frozen narrative, timings, hashes, branch history, and completed-package
  evidence stay in completed cards or dated history.

### Concurrent authoring and serialized integration

One integration worktree owns canonical history. Disjoint sidecars may draft
bounded work, but only the integration owner accepts it, moves lifecycle state,
runs final combined validation, and publishes. Conflicts, unfinished
candidates, and external execution identities are preserved for explicit
resolution rather than force-integrated.

### Comprehensive refactor program

- `REFACTOR_AUDIT.md` owns live findings and recheck routes;
  `TEST_BASELINE.md` owns non-regression policy and contract-risk routes;
- independent Step `09` characterization stays separate from the production
  validator and statistical implementation;
- coverage compares covered files plus covered lines and branches, with public
  Make targets and bounded cleanup preserved;
- known publication/recovery defects remain explicitly characterized until an
  authorized correction package changes them; and
- Steps `07` through `09` algorithms remain unchanged without inspected
  runtime evidence and separate scientific authorization.

### Report exports

The renderer publishes an all-or-none HTML/PDF/deterministic-summary-TSV bundle
with the report receipt last. It validates explicit inputs against canonical
contracts and never installs software, runs analysis, discovers inputs, or
promotes evidence state. Renderer tests cover determinism, accessibility,
isolation, locking, signals, cleanup, and rollback.

### Populated demo report

`make demo-report` is a repeatable local synthetic demonstration using already
restored pinned tooling. It publishes under ignored `results/demo-report/` and
must never be described as production, cluster, completed scientific review,
or biological evidence.

### Foundation packages

Runtime preflight only reports declared tools, namespaces, hash utilities, and
path visibility. Reference provenance only inventories and reconciles declared
reference identity. Storage inventory only records roots, sizes, capacity or
quota evidence, and policy. None installs, repairs, deletes, moves, compresses,
or otherwise mutates the inspected environment or data.

### Per-step validation reports

Each owner-local validator is dry-run-first, explicit-input-only, and publishes
`results/qc/validation/<step>/<scope>.validation.tsv` with columns
`step_id`, `scope_id`, `check_id`, `status`, `observed`, `expected`, and
`detail`. Each retains an independent artifact adapter and end-to-end fixture;
no generic dispatcher or job array is introduced. The pipeline matrix defines
each step's acceptance boundary. Independent CMH statistic, p-value, odds-
ratio, and estimability recomputation from DP/AD counts remains a critical
audited gap.

## Deferred remote lineage

Remote work requires new user direction after the local tranche:

```text
refactor-99-final-audit
└── validate-step-07
    └── validate-step-08
        └── validate-step-09
            └── validate-step-09c-scientific-evidence
                └── post09-targeted-reruns
```

Remote promotion is upstream-sequential and cannot inherit local or synthetic
evidence labels.

## Scientific exit boundary

Mechanical orientation, annotation provenance, statistical policy,
replicate/sensitivity evidence, candidate adjudication, and limitations require
explicit review. `science_review_complete_exploratory` remains provisional.
`biological_interpretation_ready` is reserved until a separately approved
policy defines and unlocks its stricter exits.
