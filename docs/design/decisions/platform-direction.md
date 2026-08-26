# Architecture rationale

## Protect behavior before structural change

Classify affected behavior as preserved contract, characterized defect,
undefined and requiring a decision, or environment-deferred. Protect preserved
behavior independently before mutation. Structural cleanup does not silently
correct a defect or authorize a public/scientific interface change.

## Ratified architectural invariant constitution

`ARCH-CONST-01` ratified this constitution on 2026-08-26 by reconciling all 27
campaign candidates to live contracts, decisions, implementation boundaries,
and representative regression protection. These rules constrain later
architecture work; they do not select a public vocabulary, command, schema,
filesystem layout, layer map, class, facade, or abstraction.

The register uses two states:

- **Preserved** means the qualified wording is already a current contract in
  its declared scope. Exact conformance still comes from live source and tests,
  not this decision record.
- **Target** means the wording is binding for the campaign but a named current
  gap remains. A target is not evidence that the capability exists.

Characterized defects and environment-deferred behavior stay visible. A
representative test route shows existing protection, not universal proof or a
new evidence level.

### Scientific invariants

| ID | Ratified invariant | State | Authority, representative protection, or gap |
|---|---|---|---|
| `AC-INV-001` | Orientation, pairing, cohorts, strata, conditions, and other biological meaning are explicit; structural discovery never invents them. | Preserved | The [scientific decision](scientific-pipeline.md), [current architecture](../../architecture/ARCHITECTURE.md), and [sample-manifest tests](../../../tests/ingestion/sample_manifest_admission/) own the implemented boundary. |
| `AC-INV-002` | A scientific transformation is deterministic only where its owner contract declares determinism; no universal byte-determinism claim is implied. | Preserved | Scientific owner contracts and the [independent contract goldens](../../../tests/contract_integration/independent_contract_goldens/) protect declared ordering and serialization. |
| `AC-INV-003` | Tools, procedures, parameters, filters, thresholds, candidate universe, count construction, and testing family are recorded sufficiently to reproduce or audit the analysis at its declared level. | Target | The scientific decision and Step 07–09 contracts own current declarations; native-receipt provenance gaps remain visible under `ARCH-01` and the scientific-audit boundary in `AC-DEC-022`. The [Step 09 oracle](../../../tests/analyses/paired_cmh_candidate_ranking/test_step_09_cmh_oracle.py) independently protects core statistics. |
| `AC-INV-004` | Reporting, orchestration, scheduling, filesystem, and performance refactoring cannot silently alter scientific results. | Preserved | The root safety guard, owner locality, [test policy](../TEST_BASELINE.md), and scientific owner suites require behavior to be preserved or changed only under separately approved scope. |
| `AC-INV-005` | Operational abstractions may hide mechanics, but scientific algorithms, parameters, assumptions, interpretation boundaries, and implementation needed for scientific review remain recognizable and inspectable. | Target | Current scientific owners remain colocated with contracts and tests. `ANALYSIS-02` and `ARCH-01` must preserve reviewability across future module and abstraction boundaries; human recognizability requires review and cannot be proved by coverage alone. |
| `AC-INV-006` | Workflow success, a computational candidate, statistical selection, scientific review, and biological validation remain distinct claims. | Preserved | The root evidence guard, [execution/evidence decision](execution-evidence-and-reporting.md), artifact contracts, and [reporting tests](../../../tests/reporting/) protect the non-promotion boundary. |

### Provenance and artifact invariants

| ID | Ratified invariant | State | Authority, representative protection, or gap |
|---|---|---|---|
| `AC-INV-007` | A result is traceable to exact inputs, scientific configuration, source/package identity, runtime/tool identity, and the execution that produced it. | Target | The fixed local lifecycle binds this chain in the [orchestration contract](../ORCHESTRATION_CONTRACT.md) and [lifecycle tests](../../../tests/orchestration/local_pilot/test_lifecycle.py). Native-owner, installed-control-plane, and site provenance gaps remain under `ARCH-01`, `RUNTIME-01`, and `OPS-02`. |
| `AC-INV-008` | Every admitted durable artifact reference binds a stable semantic identity plus exact content digest; changed bytes cannot retain admission under the old binding. | Preserved | The [artifact schemas](../../../src/emrys/contracts/artifacts/) and [artifact contract tests](../../../tests/contracts/artifacts/) keep semantic identity distinct from content identity. |
| `AC-INV-009` | Mutation of a published artifact invalidates its prior admission and is detected at every required re-admission; physical write prevention is not implied. | Target | Verified-task and reporting paths recheck content identity. Rewrite-blindness and owner transaction defects remain characterized in the test baseline and must be resolved or explicitly preserved by the applicable `ARCH-01` migration. |
| `AC-INV-010` | Every generated manifest or normalized configuration artifact that affects a run remains inspectable and source-attributed even when a user does not author it. | Preserved | The orchestration materialization contract and [materialization tests](../../../tests/orchestration/local_pilot/test_materialization.py) protect current generated artifacts; `CONFIG-01` and `SETUP-03` inherit the rule. |
| `AC-INV-011` | Each artifact class and guarantee has one declared admission chain and one final authority; this must not become one global implementation or god object. | Target | The current native publication → owner validation → verified result → explicit adapter/index flow is defined by the [current architecture](../../architecture/ARCHITECTURE.md). `ARCH-01`, `AC-DEC-010`, and `AC-DEC-025` own the generalized lifecycle and boundary decisions. |

### Execution and recovery invariants

| ID | Ratified invariant | State | Authority, representative protection, or gap |
|---|---|---|---|
| `AC-INV-012` | An execution is complete according to its contract or visibly incomplete, failed, blocked, pending, or running; engine metadata is not completion authority. | Preserved | The orchestration contract and [lifecycle state tests](../../../tests/orchestration/local_pilot/test_lifecycle.py) protect the implemented local lifecycle. |
| `AC-INV-013` | Within declared EMRYS-owned transaction and control namespaces, partial or provisional state cannot be admitted as complete; ambiguous or foreign residue fails closed. | Target | Task, lifecycle, and [reporting transaction tests](../../../tests/reporting/test_transaction_validation.py) protect current paths. Owner-local residue, rollback, and rewrite defects remain characterized until their applicable migration resolves them. |
| `AC-INV-014` | Recovery cannot produce scientifically different work under the same bound identity. | Preserved | Normalization and lifecycle compatibility checks bind scientific changes to a new run identity and reject incompatible reuse. |
| `AC-INV-015` | Resume reuses only compatible admitted work; timestamps, file presence, and workflow-engine metadata are insufficient. | Preserved | The orchestration contract and [workflow tests](../../../tests/orchestration/local_pilot/test_workflow.py) require content and contract re-admission. |
| `AC-INV-016` | Local and HPC execution must provide equivalent scientific, artifact-integrity, recovery, and evidence guarantees, not identical mechanisms; each environment requires separate proof. | Target | `OPS-02`, `RUNTIME-01`, and `DOCTOR-01` own realization. Wrapper contracts are not parity, cluster, production, or scientific proof. |
| `AC-INV-017` | An immutable plan exists internally before the first execution mutation, even when planning and execution become one conceptual user operation. | Preserved | The orchestration contract and materialization tests protect no-write planning and immutable publication; `RUN-03` may simplify the interaction without weakening the order. |
| `AC-INV-018` | Failure and every supported repair are attributable and auditable. Repair is explicit, bounded to owned safe state, precisely reported, provenance-aware where applicable, and cannot alter declared scientific inputs or invent biology or secrets. | Target | Failure attribution exists in task/lifecycle records. Supported repair does not yet exist and remains `DOCTOR-01`; production adoption of durable application logging remains `LOG-05`. |

### Evidence and reporting invariants

| ID | Ratified invariant | State | Authority, representative protection, or gap |
|---|---|---|---|
| `AC-INV-019` | Reported claims derive from admitted artifacts and recorded validation, never discovery or recalculation inside reporting. | Preserved | The execution/evidence decision, reporting contracts, and [reporting tests](../../../tests/reporting/) protect read-only adaptation and receipt-last publication. |
| `AC-INV-020` | Validation evidence is rerunnable or independently verifiable at its declared level; missing retained inputs, runtime identity, or independent verification is disclosed rather than promoted. | Target | The test baseline, independent goldens, direct validators, and scientific oracles provide bounded protection. Native provenance and validator gaps remain visible under `ARCH-01` and `AC-DEC-022`. |
| `AC-INV-021` | Scientific, evidence/provenance, and operational evidence remain distinguishable. | Target | Existing scientific and evidence HTML views provide partial separation. The complete three-purpose presentation remains `REPORT-03` and `RESULTS-01`. |
| `AC-INV-022` | Local engineering, synthetic end-to-end, runtime, cluster, production, scientific-review, and biological evidence are never promoted into one another. | Preserved | The root evidence guard, test baseline, artifact evidence schema, and reporting boundary tests own this rule. |
| `AC-INV-023` | Receipts and low-level records required by an evidence or recovery contract may be omitted from ordinary views but remain inspectable subject to explicit retention and redaction policy; expired or unavailable records are disclosed rather than treated as complete. | Target | The logging foundation and task/attempt schemas provide bounded current pieces. `LOG-05`, `OBS-01`, `OBS-02`, `FILESYSTEM-01`, `AC-DEC-013`, and `AC-DEC-017` own adoption, access, retention, and result-bundle decisions. |

### User-boundary invariants

| ID | Ratified invariant | State | Authority, representative protection, or gap |
|---|---|---|---|
| `AC-INV-024` | Developer-only knowledge is never required for an ordinary scientist task. | Target | Current onboarding still exposes checkout, configuration, wrapper, and run-root mechanics. `CONTROL-01`, `OPS-02`, `SETUP-03`, `RUNTIME-01`, `DOCTOR-01`, `RUN-03`, `OBS-02`, `RESULTS-01`, `DOC-01`, and `REVIEW-UX-03` own the role-level journey. |
| `AC-INV-025` | Defaults, site policy, project values, and CLI overrides use one documented, inspectable precedence model. Every effective operational value and source is inspectable; an override exists only where its owner defines a safe supported admission boundary. | Target | Current resource and launcher policy implement bounded precedence. `CONFIG-01`, `OPS-01`, `OPS-02`, and `AC-DEC-005` own the complete model and exact merge semantics. |
| `AC-INV-026` | The system never prints secrets or silently invents biological meaning. | Target | Biological admission is already fail-closed, and the logging foundation redacts admitted secrets. Production paths without logging adoption have no system-wide redaction promise; `SETUP-01`, `SETUP-03`, `DOCTOR-01`, and `LOG-05` own the remaining gap. |
| `AC-INV-027` | Automatic actions are bounded, observable, and reversible or recoverable where the operation permits it; irreversibility is explicit before mutation. | Preserved | Current dry-run-first publication/recovery contracts and [onboarding tests](../../../tests/orchestration/local_pilot/test_onboarding.py) protect supported mutations. `SETUP-03`, `DOCTOR-01`, `RUN-03`, and every future mutating owner inherit the rule. |

### Ratified abstraction, migration, and test guardrails

The following guardrails are binding. They do not ratify facade-first
sequencing, an exact layer map, the campaign phase order, or a public API.

1. **Inspectable, bounded operational control (`AC-GUARD-001`).** Every
   effective operational value and its source is inspectable. An override
   exists only where the owning contract explicitly supports it and defines a
   safe admission boundary; unsafe or implementation-only values are not
   promised an override.
2. **Scientific visibility (`AC-GUARD-002`).** Operational abstractions may
   hide execution, filesystem, scheduler, provenance, and transaction
   mechanics from ordinary views, but must not conceal the algorithms,
   parameters, assumptions, interpretation boundaries, or implementation
   needed for scientific review.
3. **Bounded migration (`AC-GUARD-003`).** Migration proceeds through bounded,
   independently reviewable slices rather than an unbounded rewrite. Exact
   facade use and package order remain just-in-time decisions.
4. **Replacement completion (`AC-GUARD-004`).** A replacement is not complete
   until affected callers use the intended owner and parity is established at
   the relevant behavior, fault, and evidence boundaries. Any temporary
   compatibility path has a named owner, bounded scope, parity protection, and
   explicit retirement condition; the superseded path retires when that
   condition is met.
5. **Equal-or-stronger regression defense (`AC-GUARD-005`).** Direct-owner,
   adversarial, seeded-fault, and synthetic end-to-end defenses may be removed
   only through an explicit invariant-to-test mapping that establishes an
   equal-or-stronger replacement at the same declared evidence level. Coverage
   or the scientist-facing synthetic golden path alone is insufficient.

## Organize by functional owner

Keep each stage, analysis, evidence operation, reporting component, or neutral
domain with its implementation, native assets, commands, contract, diagnostics,
recovery behavior, and mirrored tests. Public starter inputs and repository
development controls remain outside runtime domains when they are not
implementation-native.

A source move goes directly to its final current owner. Compatibility paths are
exceptional, bounded, parity-protected, and removable. Placement creates no
installed package, new runtime behavior, or evidence.

## Use semantic identities and artifact edges

Each functional owner has a semantic slug and stable versioned machine key;
numeric identifiers remain historical aliases. Required produced artifacts and
declared barriers create DAG edges. Filenames, narrative order, shared
directories, validators, or one wrapper's materialization behavior do not.

Exact identities and edges live in
[`STAGE_MAP.md`](../../../src/emrys/contracts/STAGE_MAP.md). Current source and
dependency rules live in
[`SOURCE_TOPOLOGY.md`](../../../src/emrys/contracts/SOURCE_TOPOLOGY.md).

## Share only proven equivalence

Keep the first use owner-local. Compare behavior, failure, recovery,
determinism, and scientific meaning before extraction. Promote only sufficiently
complex or safety-relevant equivalent reuse, with independent API and consumer
tests, into the narrowest neutral owner. Never create a generic utility bucket,
force cross-language DRY, or let neutral code depend on a functional owner.

## Preserve inspectable boundaries

Cross-owner data passes through explicit contracts; owners do not import peer
private implementation. Reporting remains downstream of computation and
evidence. Dependency restoration, Git/documentation tooling, quality gates,
and project environments remain repository controls rather than scientific
workflow domains.

## Select a local-first orchestration boundary

The first workflow control plane uses Snakemake's local executor because the
existing semantic owners already expose the scientific operations and artifact
edges that a general-purpose workflow engine should schedule. EMRYS therefore
does not build a second scheduler, stage registry, scientific implementation,
or recovery system. One fixed profile is easier to inspect and prove than a
generic extension surface before a second real workflow exists.

Human YAML remains concise while ordered scientific records stay in TSV. A
normalizer resolves and hashes explicit inputs into canonical JSON so formatting
and caller working directory cannot determine run identity. The complete
execution contract remains distinct from the existing reporting run contract:
reporting is a downstream projection and cannot silently become lifecycle
authority.

Owner validation is evidence production rather than a process-level Boolean;
several validators intentionally publish `status=fail` with exit zero. Each
workflow task must consequently parse the persisted report and publish its own
content-bound verified record only after every row passes. This record is a
local scheduling/reuse boundary, not a scientific or cluster promotion.

Local execution precedes site execution so workflow semantics can be proven
without mixing CSU modules, storage, accounting, or scheduler policy into the
scientific graph. SLURM and the possible Linux VM remain deferred rather than
rejected. The decision-complete lifecycle and resume rules are in
[`ORCHESTRATION_CONTRACT.md`](../ORCHESTRATION_CONTRACT.md); accepted remaining
work is tracked in the [findings matrix](../../tasks/backlog_matrix.md).

The public control plane remains thin: it reruns read-only admission, prints an
exact no-write plan by default, materializes only the fixed profile under the
aggregate run lock, and delegates scientific work to public owners. It exposes
no raw Snakemake flags or automatic owner recovery.

The application-logging foundation is implemented under
[`LOGGING_CONTRACT.md`](../LOGGING_CONTRACT.md), while production-command
adoption remains `LOG-05`. Report profiles, analysis modules, public
acquisition, standalone workflow packaging, and site profiles remain designs,
not current architecture. Accepted outcomes are in the
[findings matrix](../../tasks/backlog_matrix.md); unsliced alternatives remain
in the temporary
[architecture campaign](../../tasks/architecture_campaign.md).
