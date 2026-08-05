# Top-level documentation map

- [Architecture](../architecture/) — current and target structure, boundaries,
  contracts, and diagrams.
- [Design](../design/) — decisions, plans, open questions, and design records.
- [Operations](../operations/) — task routing, handoff, commands, concurrency,
  and troubleshooting.
- [Task registry](../tasks/README.md) — bounded task scope and lifecycle.
- [Integration fragments](../fragments/README.md) — candidate-fragment format.
- [Demonstrations](../demo/) — presentation and walkthrough material.
- [History](../history/) — indexed immutable audit, testing, and operations
  evidence views.
- [Audience and ownership map](DOCUMENTATION_OWNERSHIP.md) — short reader
  routes, canonical responsibility boundaries, and no-loss dispositions.

## Temporary task-start routing

The sections below temporarily preserve conditional task-start material. Use
the exact section linked by the task-start router; do not load this entire map
for every task.

### Temporary critical runway

The one-unit-at-a-time physical-migration campaign is complete through
[`MIG-03O`](../tasks/COMPLETED/MIG-03O-migrate-assemble-scientific-review-evidence-package-owner.md).
The bounded repository-health runway and
[`DOC-CONS-08E`](../tasks/COMPLETED/DOC-CONS-08E-separate-live-state-from-history.md)
live-state compression are complete. Completed
[`MIG-04C`](../tasks/COMPLETED/MIG-04C-migrate-runtime-preflight-to-final-evidence-owner.md)
directly relocated runtime preflight and its mirrored suite into their final
evidence-owner homes. Completed
[`MIG-04D`](../tasks/COMPLETED/MIG-04D-migrate-storage-inventory-to-final-evidence-owner.md)
then directly relocated storage inventory and its mirrored suite into their
final evidence-owner homes. Completed
[`MIG-04E`](../tasks/COMPLETED/MIG-04E-converge-independent-contract-goldens.md)
then directly relocated the independent-golden owner. Completed
[`MIG-04F`](../tasks/COMPLETED/MIG-04F-converge-validation-roster-agreement.md)
then directly relocated the validation-roster owner and cut over fourteen
exact-file callers. Completed documentation-only
[`REVIEW-LEGACY-05A`](../tasks/COMPLETED/REVIEW-LEGACY-05A-confirm-step05-operational-checker-owner.md)
then confirmed the unchanged Step `05` operational checker's permanent current
repository-level owner. Completed documentation-only/non-consuming
[`REVIEW-LEGACY-04A`](../tasks/COMPLETED/REVIEW-LEGACY-04A-retire-step04-pending-test-scaffold.md)
confirmed `RETAIN_ROOT` for the intentional non-runnable Step `04` pending test
scaffold. Documentation-only/non-consuming
[`AUDIT-RESIDUAL-04A`](../tasks/COMPLETED/AUDIT-RESIDUAL-04A-confirm-residual-source-topology-convergence.md)
then reconciled the fixed 87-path roster, final owners, current callers, and
retained/deferred/separately-retired boundaries. The source-topology campaign
is complete at the local/static evidence ceiling and no package is selected.
Runtime execution, cluster, and default-branch integration remain unselected.
The remainder of
[`PROGRAM-01`](../tasks/IN_PROGRESS/PROGRAM-01-define-rolling-wave-planning-and-coordination-cohorts.md)
remains frozen outside its completed slices.
This route narrows work selection and routine context loading; it does not
weaken safety, freshness, evidence, ownership, or
[mandatory-expansion rules](../operations/TASK_START.md#mandatory-expansion-triggers).

- Select, plan, execute, validate, document, publish, and prove only one
  dependency-valid package at a time.
- Do not preload a later package, mutate runtime state, install dependencies,
  begin cluster work, or integrate the default branch merely because an
  earlier campaign was authorized.
- Every unrelated pending task, candidate, integration, branch package, and
  preserved program-design remainder remains frozen and out of scope.
- Frozen material may be inspected only when a concrete contradiction, safety
  issue, direct interface dependency, or
  [mandatory expansion trigger](../operations/TASK_START.md#mandatory-expansion-triggers)
  makes that inspection necessary for the active package.
- Validation is quiet by default. Ordinary slice close follows the
  [`TASK_DELIVERY.md` boundary](../operations/TASK_DELIVERY.md#slice-start-and-close),
  and final reconciliation uses the applicable
  [`RUNBOOK.md` gate](../operations/RUNBOOK.md#local-validation-gate). Replay or
  stream complete output only for a failure or an explicitly requested verbose
  run.

### Canonical routing

| Need | Canonical route |
| --- | --- |
| Current checkout, evidence boundary, blockers, or resume point | Applicable sections of [`HANDOFF.md`](../operations/HANDOFF.md) |
| Package status, lineage, order, or acceptance | Applicable sections of [`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md) |
| Exact setup, validation, cluster, or recovery command | Applicable heading in [`RUNBOOK.md`](../operations/RUNBOOK.md) |
| Concurrent lane roles, authority, coupling, handoff, or integration | [`CONCURRENT_WORK.md`](../operations/CONCURRENT_WORK.md) plus live lanes in `HANDOFF.md` |
| Integration-fragment filename or candidate fields | [`docs/fragments/README.md`](../fragments/README.md); authority, lifecycle, and dispositions remain in `CONCURRENT_WORK.md` |
| Durable rationale or settled constraint | Applicable decision in [`DECISIONS.md`](../design/DECISIONS.md) |
| Open operational, scientific, or design choice | Applicable entry in [`QUESTIONS.md`](../design/QUESTIONS.md) |
| Symptom, cause, diagnosis, or fix | Applicable heading in [`TROUBLESHOOTING.md`](../operations/TROUBLESHOOTING.md) |
| Current topology or contract flow | Applicable section of [`ARCHITECTURE.md`](../architecture/ARCHITECTURE.md) |
| Target topology or deferred constraint | Applicable section of [`FUTURE_ARCHITECTURE.md`](../architecture/FUTURE_ARCHITECTURE.md) |
| Task scope, dependencies, and acceptance | Selected card and [`docs/tasks/README.md`](../tasks/README.md) |
| Concise user entry point or repository map | Applicable section of [`README.md`](../../README.md) |
| Prioritized pending work | Applicable section of [`TODO.md`](../../TODO.md) |

Use repository-wide targeted search to find changed names, paths, commands,
interfaces, schema versions, evidence terms, and inbound references. Search
coverage may be repository-wide without loading every matching file in full.

### Situation matrix

| Situation | Required inspection |
| --- | --- |
| New agent or unknown prior context | [`TASK_START.md`](../operations/TASK_START.md) and selected card in full, governing instructions, live Git state, and card-routed canonical sections |
| Same task with an exact verified baseline | Changes since that baseline; reuse unchanged material while the [freshness-and-sufficiency conditions](../operations/TASK_START.md#context-freshness-and-reuse) still hold |
| New task in the same verified context | New card in full, live Git state, changes since the prior task, and newly relevant canonical sections |
| Phase boundary | Closing evidence, new phase/card, applicable lineage and acceptance sections, diff since the prior boundary, and changed or affected owners |
| Documentation patch | Complete final diff, affected sections and owners, inbound references, and affected diagrams |
| Starting a candidate lane | Assigned lane packet, absolute worktree, candidate branch or detached execution state, base, write set, prohibited overlaps, and coupling assumptions |
| Integrating a candidate | Latest canonical state, immutable candidate handoff, complete base-to-candidate diff, overlap/coupling recheck, and combined validation obligation |
| Authoring a fragment | Published packet, exclusive candidate write reservations, optional fragment path, nonexclusive target declarations, schema, base, coupling, and prohibited authority |
| Consuming a fragment | Frozen published source SHA/ref, exact fragment blob, current targets and authorizations, every request and residual disposition, routed destinations, source provenance, and final fragment removal |
| Cross-cutting or high-risk uncertainty | Every relevant canonical owner and direct consumer; broaden until the risk is resolved |
| Ownership migration, contradiction, or broad audit | Broader full-file or corpus reading as the evidence requires |

A phase boundary is an expansion signal, not an automatic instruction to read
the complete canonical corpus. Reassess ownership, interfaces, acceptance, and
changes since the prior boundary, then broaden according to impact.

### Documentation impact and validation

For every final change, use the complete diff from the package predecessor or
validated implementation commit—not only the current worktree—to identify
affected documentation and diagrams. Before commit, include staged, unstaged,
and untracked paths; after commit, compare the exact commits. Search the full
repository for each changed interface, path, command, schema, status, evidence
term, and ownership claim. Inspect the affected sections, canonical owners,
direct references, and changed diagrams. Broaden semantic reading only when an
expansion trigger applies.

Candidate-only validation is provisional. When concurrent work exists, impact
classification and closure use the final combined canonical diff after
serialized integration; no candidate branch alone can publish package status,
completion, or evidence.

For a fragment package, first validate the handoff independently from request
staleness. Then compare the frozen candidate with its recorded base and the
latest canonical targets, and inspect the final parent-to-result diff
separately. Confirm that every request and partial residual has a structured
terminal record, accepted content has one canonical owner, deferral uses an
implemented authorized destination, and no candidate fragment survives.
Fragment backlinks do not establish canonical task-registry connectivity.

Keep the automated repository-wide documentation gate. Its global link,
anchor, card, dependency, and Mermaid checks provide broad structural coverage
without loading the full corpus into agent context. Automated structure does
not replace targeted semantic comparison.

When the complete package diff contains only documentation artifacts and none
is consumed by executable, configuration, generation, schema, fixture, report-
template, or test-harness selection or execution behavior, computational
validation is not applicable. Run only the Git and documentation checks owned
by [`RUNBOOK.md`](../operations/RUNBOOK.md#local-validation-gate). Do not run
computational Python, shell, R, or report-runtime test suites.

A documentation patch following implementation may rely on that executable
state's recorded computational gate when Git proves the state unchanged. A
standalone documentation-only package records computational validation as not
applicable rather than claiming a new computational pass.
