# NORAD pipeline plan

This is the authoritative current pipeline/package/evidence roadmap, status
matrix, acceptance criteria, and delivery-required branch lineage. Task
workflow status is the card's directory under [`../tasks/`](../tasks/).
Current checkout, lanes, blockers, evidence detail, and resume state belong in
[`HANDOFF.md`](../operations/HANDOFF.md); exact commands belong in
[`RUNBOOK.md`](../operations/RUNBOOK.md); frozen delivery and legacy branch
lineage belongs in
[`operations history`](../history/operations/2026-08-03-refactor-delivery-and-branch-lineage.md).

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

The cluster evidence for Steps `00a` through `06` predates their physical
source cutovers. Migration acceptance was local and did not create new runtime
or cluster proof. Steps `07` through `09` are not cluster-proven, and Step
`09c` tooling does not constitute a completed production review.

## Evidence and reporting packages

| Package family | Responsibility | Current status |
| --- | --- | --- |
| Artifact and review contracts | Public artifact, scientific-review, run-summary, report-receipt, adapter, and deterministic summary contracts | implemented and fixture-tested |
| Static report exports | Atomic self-contained HTML/PDF/summary-TSV/report-receipt publication with explicit table approvals | implemented and locally renderer-tested; no production report |
| Populated demo | Complete synthetic run with approved science-table roles and bounded HTML/PDF projections | implemented and locally renderer-tested; synthetic evidence only |
| Runtime preflight | Explicit-profile tool, R-namespace, hash, and path-visibility checks | implemented and fixture-tested; CSU batch execution pending |
| Reference provenance | Explicit reference identity, hashes, annotation provenance, and contig reconciliation | implemented and fixture-tested; production execution pending |
| Storage inventory and retention | Read-only storage measurement plus explicit policy recording | implemented and fixture-tested; production inventory and approvals pending |
| Step `00a` through `09` validation reports | Structured step-local validation, typed artifact adaptation, and summary/report propagation | implemented and locally fixture-tested; real-runtime or production evidence remains as stated in the pipeline matrix |
| Refactor audit and test baseline | Current recheck/policy routes plus immutable dated evidence | complete; current routes in [`REFACTOR_AUDIT.md`](REFACTOR_AUDIT.md) and [`TEST_BASELINE.md`](TEST_BASELINE.md) |
| Architecture, migration mechanics, and physical ownership | Fourteen semantic DAG owners, final homes, direct-migration mechanics, neutral validation-report library, and neutral artifact contracts | pipeline-owner migration complete through `MIG-03O`; artifact-contract migration complete through `MIG-04A`; remaining cross-cutting convergence is dispositioned by `PLAN-03A` |
| Documentation ownership and compression | Canonical owner map, concise root/operations/history views, and bounded remaining consolidation cards | `DOC-CONS-08A` through `DOC-CONS-08E` complete; `DOC-CONS-08F` through `DOC-CONS-08H` unselected |

Exact historical package totals, timings, branch names, checkpoints, failures,
and close evidence remain in the dated audit/testing/operations history and
completed cards rather than this current matrix.

## Active critical runway

The neutral validation-report concern and all fourteen semantic DAG owners are
physically migrated through `MIG-03O`; the required-artifact DAG contains no
unmigrated owner in that frozen topology. `MIG-04A` also moved the neutral
artifact validator, schemas, direct test, and valid fixtures to their final
homes. Reporting, evidence helpers, and shared tests remain at legacy root
paths and are not covered by those completion claims. The repository-health
runway completed its documentation-gate and lifecycle packages, preserved the
quarantined malformed local R-library entry, corrected the bounded recursive-
Make fixture issue, and reached an earlier green complete local gate without
changing dependencies. Current `renv` metadata drift is recorded in the
handoff and MIG-04A completion evidence without relabeling that history.

Documentation-only
[`DOC-CONS-08E`](../tasks/COMPLETED/DOC-CONS-08E-separate-live-state-from-history.md)
is complete. It created the indexed operations-history owner and separated
frozen narrative from the handoff, roadmap, and concurrency policy without
changing a roadmap decision, executable behavior, evidence state, or another
card's lifecycle.

No follow-on package is selected automatically.
`DOC-CONS-08F`, `DOC-CONS-08G`, and `DOC-CONS-08H` remain separate eligible
documentation candidates subject to live dependency review and their own
approved plans. `PROGRAM-01` remains in progress and frozen outside its
completed slices. `CONCURRENCY-03`, `TASK-EPIC-01`, `AUDIT-99`, recovered TODO
work, UNREFINED proposals, default-branch integration, and remote runtime or
cluster work remain unselected and outside this package.

Documentation-only
[`PLAN-03A`](../tasks/COMPLETED/PLAN-03A-inventory-and-sequence-residual-source-topology-convergence.md)
is published and complete as the residual source-topology documentation
package. It
changed no consumed or executable surface, selected no successor, and did not
reopen the completed fourteen-owner migration campaign.

Documentation-only
[`LIB-02F`](../tasks/COMPLETED/LIB-02F-define-shared-library-ownership.md) is
complete as the first decision package in the explicitly authorized residual
convergence campaign. It settled the two observed prohibited peer-
implementation seams. Completed
[`MIG-04A`](../tasks/COMPLETED/MIG-04A-migrate-artifact-contract-validation-to-final-neutral-owner.md)
performed the first executable move. Completed
[`LIB-02G`](../tasks/COMPLETED/LIB-02G-extract-step08-scientific-evidence-contract.md)
then extracted the bounded Step `08` neutral scientific-evidence contract. No
later package was selected at that close. The sole selected package is now
[`LIB-02H`](../tasks/IN_PROGRESS/LIB-02H-extract-step09-scientific-evidence-contract.md),
the bounded Step `09` neutral scientific-evidence contract extraction.

Select, plan, execute, validate, document, publish, and prove only one
dependency-valid package at a time. Preferred order is not blocker metadata,
and frozen proposal presence does not authorize selection or implementation.

### Residual source-topology convergence

The exact 122-path current roster is owned by the
[`functional-owner inventory`](../architecture/FUNCTIONAL_OWNER_INVENTORY.md#residual-tracked-path-coverage),
and exact final homes are owned by
[`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md#cross-cutting-implemented-target-homes).
This roadmap owns only disposition and preferred JIT order. `MOVE`,
`RETAIN_ROOT`, `DEFER`, and `RETIRE` are terminal planning dispositions; none
authorizes mutation or creates a future card. The `LIB-02F` semantic comparison
is a prerequisite decision for affected `MOVE` rows, not a fifth path
disposition.

| Residual group | Disposition | JIT route or boundary |
| --- | --- | --- |
| Artifact schemas and contract validator | `MOVE` complete through [`MIG-04A`](../tasks/COMPLETED/MIG-04A-migrate-artifact-contract-validation-to-final-neutral-owner.md) | The validator, five schemas, direct test, and fixtures occupy their final neutral owners with all reviewed consumers cut over. |
| Artifact indexing, run-summary construction, and static reporting | `MOVE` through [`RPT-05A`](../tasks/TODO/RPT-05A-relocate-reporting-to-final-source-home.md) | Start only after artifact contracts and every concrete prohibited-dependency extraction it needs; move current behavior before feature work or decomposition. |
| Reference provenance evidence | `MOVE` | Start only after the approved neutral `reference_contigs` parser extraction completes. |
| Runtime preflight | `MOVE` | One evidence-owner migration card. |
| Storage inventory | `MOVE` | One evidence-owner migration card; retention action remains prohibited. |
| Independent contract goldens and validation-roster agreement | `MOVE` | Update as direct consumers during owner moves, then converge their paths under `tests/contract_integration/` near campaign close. |
| Dependency-lifecycle commands and tests | `RETAIN_ROOT` | Remain explicit repository setup/operator interfaces; revisit only through a separately approved setup-ownership decision. |
| Public config examples, operator selections, and reference schemas | `RETAIN_ROOT` | Move only if a later inspected contract proves that one is implementation-native rather than an explicit user input. |
| Documentation/Git orchestration, public-command characterization, quality gates, coverage, and root project anchors | `RETAIN_ROOT` | Repository-development and cross-entry-point protections remain outside runtime domains. |
| Legacy Step `05` data checker and pending Step `04` scaffold | `RETAIN_ROOT` | Preserve the checker's unique scheduler/status/TSV behavior and the intentional pending scaffold until a separate no-loss owner/retirement review. |
| Temporary `work/active/JIT-01.md` record | `RETIRE` through [`DOC-CONS-08H`](../tasks/TODO/DOC-CONS-08H-retire-jit-temporary-work-record.md) | Preserve its two unique cleanup entries in authorized owners before removing the record; this is documentation cleanup, not source migration. |
| Manifest admission, FASTQ pair check, and manifest wrapper | `DEFER` | Resume only with explicit ingestion work; no ingestion executor exists. |
| Root scheduler probes/template and mixed wrapper suite | `DEFER` | Resume only with explicit scheduler work. |
| Cluster/local workflow profiles | `DEFER` | Resume only with explicit runtime-orchestration/profile work; no orchestrator exists. |

Preferred one-owner order is:

1. completed `LIB-02F` settles only the two observed shared seams;
2. completed `MIG-04A` performs the neutral artifact-contract move;
3. completed `LIB-02G` extracts the neutral Step `08` contract; execute
   selected `LIB-02H`, then create later bottom-up scientific-evidence slices
   only just in time: the public review-package contract and reporting-local
   reader removal;
4. execute `RPT-05A` only after those concrete blockers close;
5. extract the neutral `reference_contigs` parser seam, then move reference
   provenance; move runtime preflight and storage inventory as separate owner
   cards;
6. converge the residual cross-owner contract tests and separately review the
   two retained legacy test/data-check paths; and
7. create one residual-layout audit only after the final executable move.

`LIB-02H` is the sole selected residual package. Later seam-extraction cards,
the final audit, and deferred domains remain uncreated or unbegun.

### Recovered proposal families

The unselected local-pilot family has three parallel inputs:
[`SETUP-03A`](../tasks/TODO/SETUP-03A-implement-local-pilot-dependency-profile-and-doctor.md),
[`INTAKE-03A`](../tasks/TODO/INTAKE-03A-implement-yaml-tsv-run-lifecycle.md),
and
[`PROFILE-03A`](../tasks/TODO/PROFILE-03A-materialize-local-pilot-workflow-profile.md).
Together they feed
[`CLI-03A`](../tasks/TODO/CLI-03A-implement-local-pilot-control-plane.md)
→ [`E2E-03A`](../tasks/TODO/E2E-03A-prove-fresh-clone-local-pilot.md)
→ [`ONBOARD-03A`](../tasks/TODO/ONBOARD-03A-publish-researcher-onboarding.md).
`INTAKE-03A` is separately blocked by the still-unavailable accepted design
from `INTAKE-02E`.

These arrows preserve reviewed interface/readiness order, not automatic
selection or invented blockers. SETUP owns local-environment readiness;
INTAKE owns admission/normalization; PROFILE owns a non-executable projection;
CLI remains thin over orchestration; E2E owns clean-clone proof; and ONBOARD
owns researcher guidance. The family excludes future analysis modules, public
acquisition, installable distribution, optional-analysis policy, and
site/container profiles.

Recovered
[`DOC-TASK-SCAN-01`](../tasks/TODO/DOC-TASK-SCAN-01-scan-documentation-for-task-intake.md)
and
[`GATE-REC-01`](../tasks/TODO/GATE-REC-01-define-machine-readable-gates-and-validation-receipts.md)
are also unselected, separately bounded TODO proposals. The eight files under
[`UNREFINED`](../tasks/UNREFINED/) are discovery records only and do not join
the roadmap until explicitly reviewed and promoted.

Documentation-package readiness remains parent-first: resolve legacy task-edge
semantics through `TASK-REG-01` or an explicit reviewed exception, correct and
review `DOC-REF-02`, then synthesize and review only `DOC-PIPE-04`-owned work on
that accepted parent. This is integration/readiness order, not a new blocker or
completion claim.

## Approved current delivery lineage

```text
MIG-03O documentation/lifecycle close 9cb4bb8
└── DOC-CONS-08E selection 9bb7a1a
    └── DOC-CONS-08E documentation/lifecycle close a8aa28b
        └── PLAN-03A registration 0e6b4cb
            └── PLAN-03A selection b84bf55
                └── PLAN-03A documentation/lifecycle close 3efe461
                    └── LIB-02F selection 3896081
                        └── LIB-02F decision/lifecycle close 96c6436
                            └── MIG-04A selection ca5497f
                                └── MIG-04A executable cutover 17090ac
                                    └── MIG-04A documentation/lifecycle close
                                        + LIB-02G registration ec0b00f
                                        └── LIB-02G selection e5f54e0
                                            └── LIB-02G executable cutover f72cc0f
                                                └── LIB-02G documentation/lifecycle close
                                                    + LIB-02H registration
                                                    d38f782
                                                    └── LIB-02H selection
                                                        (commit containing this plan)
```

The final node is the current selection tip represented by this plan. It
selects only `LIB-02H`; no implementation, later extraction, final audit,
default-branch integration, runtime, or cluster action is implied.
The complete legacy
lineage and frozen source identities are indexed in
[operations history](../history/operations/).

## Package acceptance criteria

### Documentation consolidation

- one canonical owner for each mutable fact;
- one authoritative status matrix and delivery-required lineage in this file;
- current takeover evidence only in `HANDOFF.md`;
- executable commands only in `RUNBOOK.md`;
- detailed task-start freshness, routing, and expansion rules in
  `TASK_START.md`, with concise enforcement in `AGENTS.md`;
- durable rationale only in `DECISIONS.md` and open questions only in
  `QUESTIONS.md`;
- troubleshooting owns symptom, cause, diagnosis, and fix—not roadmap;
- current topology remains in `ARCHITECTURE.md`, future constraints in
  `FUTURE_ARCHITECTURE.md`, and exact final homes in source contracts;
- standalone Mermaid sources contain no transient status;
- demos are explicitly presentation material or dated snapshots;
- every task card has one stable ID and status directory, the required
  sections, valid links, and no duplicate ID;
- new or edited active hard dependencies represent genuine technological
  blockers, remain reciprocal while both cards are mutable, and are acyclic;
- cards link canonical rationale, state, commands, and topology rather than
  duplicating them, and lifecycle moves repair every inbound link in the same
  commit;
- moving a card to `IN_PROGRESS` starts read-only planning only and requires a
  separately approved task-specific plan before implementation;
- unique scientific and validation evidence is preserved;
- no workflow, validator, schema, configuration, scientific-method, or public-
  contract behavior changes inside a documentation-only package; and
- the documentation gate passes. Computational gates apply only to executable
  or test-affecting changes.

### Concurrent authoring and serialized integration

- one canonical integration/control worktree owns accepted history and current
  state;
- at most one implementation-candidate or immutable-execution lane coexists
  with multiple disjoint documentation/card sidecars;
- every candidate has a unique branch and absolute worktree or locked detached
  execution identity, plus an exact base, target, owner, role, reservations,
  prohibited overlap, coupling, external-authority boundary, and validation;
- candidate branches and card placement remain proposals until the integration
  owner accepts them;
- only the integration owner moves canonical lifecycle or publishes lineage,
  priority, completion, and evidence;
- coupled documentation remains a draft or triggers a checkpoint and re-plan;
- final combined validation governs closure, and computational evidence is
  reusable only when Git and path classification prove executable identity;
- optional fragments grant no canonical write authority and every request and
  partial residual receives a terminal disposition; and
- conflicts, source refs, and unfinished candidates are preserved rather than
  force-integrated or automatically deleted.

### Comprehensive refactor program

- [`REFACTOR_AUDIT.md`](REFACTOR_AUDIT.md) owns current finding and recheck
  routes; immutable findings and rejected approaches remain in audit history;
- [`TEST_BASELINE.md`](TEST_BASELINE.md) owns current non-regression policy,
  evidence vocabulary, contract-risk routes, and fixture-independence rules;
- independent Step `09` characterization remains separate from the production
  validator and statistical method;
- validation orchestration preserves public Make targets, quiet failure-first
  logs, serial fallback, bounded cleanup, and exact covered-file/line/branch
  comparison;
- publication-fault characterization keeps known unsafe recovery states
  explicitly labeled rather than normalizing them into passing behavior;
- every applicable behavior remains classified as preserved, characterized
  defect, decision-required, or environment-deferred before correction work;
- logging characterization and the version-1 target contract do not silently
  change current output, scheduler, retention, or evidence behavior;
- architecture, reliability, and usability reviews correct each executable
  migration plan before implementation;
- Step `07` through `09` scientific/statistical algorithms remain unchanged
  until inspected runtime evidence and separate authorization exist; and
- `refactor-99-final-audit` requires separate selection and closes the local
  program without beginning cluster work.

### Report exports

The renderer supports explicit `html`, `pdf`, and `all` formats, defaulting to
`all`, and publishes an all-or-none HTML/PDF/deterministic-summary-TSV bundle
with the report receipt last. It uses explicit validated inputs, the canonical
run-summary/report-receipt contracts, pinned Quarto with bundled Typst, and a
pinned pure-Python PDF reader.

Validation covers PDF signatures, EOF, extractable text, page order, banners,
determinism, accessibility, isolation, lock, signal, cleanup, and rollback.
Rendering never installs software, invokes analysis, discovers inputs, or
promotes evidence state.

### Populated demo report

`make demo-report` remains a local repeatable synthetic demonstration requiring
already restored pinned tooling. It builds one 81-artifact, 15-scope run with
an exploratory Step `09c` review and all 11 approved table roles, performs a
renderer dry-run before execute, and publishes under ignored
`results/demo-report/`.

The science-first Overview retains status, CMH-ranked candidates,
adjudication, and limitations. HTML uses broad script-free native categories
and local scroll regions; PDF remains linear with compact candidate records.
The fixture is never described as production, runtime, cluster, completed
production review, or biological evidence.

### Foundation packages

- runtime preflight publishes read-only explicit-profile tool, namespace,
  hash-utility, and visibility checks and never installs software;
- reference provenance inventories FASTA, FAI, DICT, GTF, BED, STAR index,
  hashes, annotation provenance, and contig agreement and never repairs them;
  and
- storage inventory records roots, sizes, capacity/quota evidence, and policy
  without deleting, moving, compressing, or cleaning data.

### Per-step validation reports

Each validator is dry-run-first, explicit-input-only, and publishes:

```text
results/qc/validation/<step>/<scope>.validation.tsv
```

with exact columns:

```text
step_id
scope_id
check_id
status
observed
expected
detail
```

Each package retains a read-only artifact adapter and end-to-end fixture. No
generic dispatcher or job array is introduced. Checks cover:

- `00a`: index/source identity, contigs, and `sjdbOverhang`;
- `00b`: BED12 structure, sorting, blocks, and GTF agreement;
- `00c`: FASTA/FAI/DICT identity and contig agreement;
- `01`: STAR outputs, logs, BAM, and mapping summary;
- `02`: BAM/BAI, sorting, read groups, and alignment RG tags;
- `02b`: quickcheck and flagstat;
- `03`: RSeQC structure and paired-orientation fractions;
- `04`: BAM/BAI/metrics, sorting, RG preservation, and duplication metrics;
- `05`: parameterized existing output validation;
- `06`: orientation outputs and count arithmetic;
- `07`: receipts, VCF structure, selectors, hashes, order, and counts;
- `08`: three-output transaction, schemas, hashes, ordering, uniqueness, and
  counts; and
- `09`: exact headers/basenames/output-parent rules, analysis/cohort/policy
  identity, complete Step `08` candidate order, count-derived fields,
  reported-CMH type/range checks, global BH recomputation from reported
  p-values, exact subset, summary/provenance and spectrum reconciliation, and
  PDF structure.

Independent CMH statistic, p-value, odds-ratio, and estimability recomputation
from DP/AD counts remains a critical audited gap.

## Deferred remote lineage

Only after new user direction and completion of the local sequence:

```text
refactor-99-final-audit
└── validate-step-07
    └── validate-step-08
        └── validate-step-09
            └── validate-step-09c-scientific-evidence
                └── post09-targeted-reruns
```

Remote promotion is upstream-sequential. Each validation package inspects
evidence, regenerates structured summaries and reports, performs a separate
documentation patch, and reaches a clean pushed gate before the next package.

## Scientific exit boundary

Mechanical orientation, annotation provenance, statistical policy,
replicate/sensitivity evidence, candidate adjudication, and limitations require
explicit review. `science_review_complete_exploratory` remains provisional.
`biological_interpretation_ready` is reserved until a separately approved
policy defines and unlocks its stricter exits.
