# Concurrent work

This document owns NORAD's policy for isolated concurrent repository work. It
defines roles, authority, coupling, handoff, and integration. Live lanes belong
only in [`HANDOFF.md`](HANDOFF.md#active-concurrent-lanes), and exact commands
belong only in
[`RUNBOOK.md`](RUNBOOK.md#concurrent-worktrees-and-serialized-integration).
Candidate integration-fragment filenames and fields are defined in
[`docs/fragments/README.md`](../fragments/README.md); that schema owns no lane
authority, disposition, lifecycle, or publication state.

Sequential work in one authoritative worktree is the default. Use concurrency
only when independent work materially outweighs isolation, handoff, integration,
and recovery cost. Concurrency does not relax task planning, evidence, safety,
review, or publication gates. A lane packet coordinates approved work but never
authorizes a task by itself.

## Non-negotiable model

- One primary worktree and branch is the canonical integration/control lane.
- At most one implementation-candidate or immutable-execution lane may be
  active beside the canonical lane.
- Multiple documentation/card sidecars may be active when their worktrees,
  branches, card IDs, and write sets are disjoint.
- Every authoring candidate uses a unique sibling worktree and branch. An
  immutable-execution lane instead uses a locked detached worktree at the exact
  recorded pushed commit. Agent identity does not isolate a shared filesystem.
- Candidate branches are proposals. The integration owner serializes accepted
  changes into one canonical linear history.
- No lane merges, rebases, force-pushes, or deletes another lane. Candidate
  work is preserved until accepted publication or an explicit operator
  decision.
- Read-only reviewers may inspect any lane but must not mutate its worktree.

The required post-`CONCURRENCY-01` first-use strategy condition is satisfied
when the current handoff says so. Its dated completion belongs in
[`operations history`](../history/operations/2026-08-03-refactor-delivery-and-branch-lineage.md#frozen-coordination-and-recovery-identities),
not this durable policy. Satisfying that condition removes only the discussion
pause: it does not select work, accept candidate content, or relax lane-packet,
integration, validation, or publication requirements.

## Lane roles

| Lane | Cardinality | Purpose | Publication authority |
| --- | --- | --- | --- |
| Canonical integration/control | Exactly one | Own accepted history, coordination, integration, current state, and final validation | Sole authoritative publisher |
| Implementation candidate | At most one, mutually exclusive with immutable execution | Implement one approved package in isolation | Proposal only |
| Immutable execution | At most one, mutually exclusive with implementation | Run an approved command or job against a pinned commit and declared inputs | Produces evidence attributed only to that commit and inputs |
| Independent documentation/card sidecar | Multiple | Create disjoint stable cards or documentation that does not affect an active contract or result | May land as a reviewed standalone documentation commit |
| Coupled documentation draft | Multiple when disjoint | Prepare documentation tied to unsettled implementation, acceptance, architecture, test, or evidence state | Cannot land independently |

An implementation lane may draft its directly required documentation when
that write set is reserved to it. Source-code comments are source changes, not
documentation-sidecar work, even when they do not alter runtime behavior.

No persistent-intake lane role is currently authorized. The preserved
[`TASK-INTAKE-01`](../tasks/UNREFINED/TASK-INTAKE-01-design-persistent-task-inbox.md)
proposal cannot create one. If that proposal is explicitly reviewed and
promoted later, its owning package must amend this policy with privacy,
retention, backup, timestamp/authorship, review cadence, scheduling, expiry or
reset, and fail-closed boundaries. Such a lane could prepare append-only notes
and reviewed dispositions but could not own live state, promotion, integration,
publication, or wholesale merge.

## Required lane packet

Before any concurrent mutation, the integration owner records each lane under
[`HANDOFF.md`](HANDOFF.md#active-concurrent-lanes). A lane packet contains:

| Field | Requirement |
| --- | --- |
| Lane ID and type | Stable short identity and one role from the table above |
| Owner | Responsible agent or maintainer |
| Worktree | Resolved absolute path |
| Branch or detached state | Unique candidate branch, or detached `HEAD` at the exact execution commit |
| Base | Exact canonical commit from which the lane starts |
| Integration target | Canonical branch and intended landing boundary |
| Task/card | Selected task, or bounded objective if no card exists |
| Approval envelope | Exact approved plan or durable reference from which this packet is projected |
| Candidate write reservations | Exact new card IDs and paths the candidate may edit, including exact deliverables plus zero or one fragment path |
| Declared canonical targets | For a fragment, each target owner, heading or anchor, mode, and authorization the integration owner must recheck |
| Prohibited overlap | Active cards, paths, contracts, and owners the lane must not change |
| Coupling | Independent, coupled draft, implementation candidate, or immutable execution |
| Allowed actions and local commits | Mutations and commit shape expressly allowed inside the envelope |
| External-authority boundary | Push, network, production, cluster, install, destructive, or other high-impact actions expressly allowed; everything else remains prohibited |
| Exclusions and unresolved choices | Work and decisions preserved outside the packet |
| Stop conditions | Exact boundaries at which the lane hands off or returns to planning |
| Validation | Focused candidate checks justified by risk and the final combined gate required |
| Execution identity | For execution only: commit, command/job identity, inputs, configuration, and output/log locations |

Candidate write reservations use exact paths or narrow rooted patterns, never
an unbounded `docs/**` or repository-wide claim. They are exclusive: the
integration owner resolves duplicate card IDs and write overlaps before
provisioning a sidecar. Fragment target declarations are nonexclusive requests,
not reservations or delegated authority. Several lanes may name one canonical
target; the integration owner serializes them and rechecks the target after
every landing. A target declaration that overlaps another lane's write
reservation creates coupling and integration order, not shared write access.

One approved envelope may project into several disjoint packets, but no packet
may expand its scope or authority. The packet coordinates in-envelope work; it
does not create approval. Routine packet work may proceed without renewed
approval only while every envelope boundary remains true. Preferred order and
pending integration are sequence state, not technological blockers.

When another authoring or execution lane will rely on the packet, publish it as
a canonical coordination checkpoint before that lane starts. This is a narrow
exception to default batch publication: one documentation-only commit containing
only the active packets and directly required coordination facts. It runs the
documentation gate, is pushed, and is proved upstream-equal before a relying
lane is provisioned. It records planning state only—not implementation evidence,
package completion, card lifecycle, or permission to bypass task-specific
approval.

## Write authority

Only the integration owner finalizes:

- checkout, active-lane, blocker, and resume state in `HANDOFF.md`;
- live package status and authoritative lineage in `PIPELINE_PLAN.md`;
- immediate priority in `TODO.md`;
- explicit card lifecycle, completion records, and evidence claims;
- accepted changes to `AGENTS.md`, `TASK_START.md`, this policy, registry
  lifecycle rules, and integration/recovery commands; and
- conflict resolution across canonical owners.

A sidecar may author new stable `planned` cards and explicitly reserved
documentation. It cannot select, approve, review, complete, or retire its own
card. A
sidecar may draft an integration-owner path only when the packet labels it
coupled. The integration owner then decides whether and how it enters the
canonical package. A sidecar may also author its exact reserved deliverables
plus at most one integration fragment. The fragment never grants candidate
write authority over its declared canonical targets.

Two concurrently mutable lanes must never edit the same path, card ID, current-
state claim, or contract boundary. At handoff the candidate freezes at its
recorded commit; only then may write authority for its reserved paths transfer
to the integration owner. Any later candidate movement invalidates the handoff.
When overlap appears before transfer, both proposals are preserved and
integration stops until ownership and order are re-planned.

## Independent or coupled

Documentation is independent only when all of these are true:

- it can land or be reverted without changing the active lane's code, inputs,
  outputs, tests, contract, acceptance criteria, or evidence interpretation;
- it does not depend on an unsettled decision or result from the active lane;
- its complete write set is disjoint from every other mutating lane; and
- it does not publish current status, priority, completion, or evidence.

Documentation is coupled when any condition fails, including when it changes
or relies on an active public interface, architecture decision, acceptance
criterion, test behavior, scientific/evidence claim, or canonical current-
state owner.

A coupled draft stays on its sidecar until the governing result is stable. If
it reveals that the active implementation's approved contract or acceptance
criteria must change, the integration owner checkpoints the active lane and
returns that task to planning. The change is never silently absorbed as a
status-only follow-up or incidental documentation edit.

## Authoring and handoff lifecycle

1. The integration owner verifies the canonical lane's exact base and clean
   state, then records disjoint lane packets. A remote-equal checkpoint is
   required only when another lane must fetch or prove that base.
2. Each mutating candidate is created from its packet's exact base in its own
   sibling worktree. The lane verifies path, branch, and `HEAD` before editing.
3. A sidecar edits only its reserved write set. New child or follow-up cards
   use reserved stable paths and remain `planned`. An optional fragment is one reserved path;
   its target declarations do not expand that set.
4. A documentation sidecar hands off exactly one clean review-ready commit
   after its base, the complete diff, validation result, and remaining
   coupling. Before canonical application, its frozen SHA must be reachable
   from the exact recorded remote source ref. An implementation candidate hands
   off one semantic commit containing implementation, tests, and directly
   affected documentation; an independently authored coupled draft may follow
   only when its separate lane was explicitly reserved. Candidate publication
   requires normal user authority.
5. The integration owner rechecks coupling and overlap against the latest
   canonical tree, then accepts one candidate at a time.
6. The integration owner creates a fresh canonical descendant and applies one
   frozen candidate commit with provenance. It integrates any separately
   reserved coupled draft, makes only subject-triggered canonical-owner or card
   changes, and keeps the result semantic rather than creating status receipts.
7. The integration owner runs the final combined applicable gate, publishes the
   canonical tranche when authorized, proves the intended ref and upstream
   equality, and only then closes affected lanes. Card completion depends on
   its acceptance contract, not routine lane closure.

Selection and candidate authoring do not change card state. Only the
integration owner may set an explicit card state to `review`, and only when a
valid exact frozen candidate will await asynchronous integration beyond the
current unpublished package. No candidate or sidecar may make that state
canonical, and exact SHA, ref, worktree, checks, fragment, and lane identity
remain solely in `HANDOFF.md`.

No scope or candidate byte may change while a card is in `review`. An approved
correction first returns it to `planned`. Acceptance sets it to `completed` only
when its acceptance evidence and completion record are satisfied; review state
alone is never completion evidence.

Exact creation, inspection, integration, verification, and optional cleanup
commands are in the runbook. Merge, rebase, and automatic conflict resolution
are not part of this workflow.

## Integration-fragment authority and lifecycle

An integration fragment is optional. Use one when an otherwise valid candidate
needs the integration owner to distribute bounded requests across canonical
owners. The candidate may contain its exact reserved deliverables plus at most
one fragment; it remains governed by its ordinary candidate contract. Only the
integration owner writes declared canonical targets, assigns dispositions,
publishes current state or evidence, and closes lanes.

The external frozen handoff in `HANDOFF.md`, not the fragment, records:

- handoff and lane IDs;
- candidate base, full frozen SHA, and immutable published source ref;
- expected commit shape and exact candidate diff;
- candidate validation, cleanliness, and remaining coupling; and
- handoff state.

A handoff is valid only when the SHA and recorded ref still agree, its
base/ancestry and commit shape match the packet, the base is an ancestor of the
current canonical parent, its complete diff is within the candidate write
reservations, and any fragment satisfies the candidate-side schema. A moved
ref, mismatched identity, invalid ancestry, unexpected path, or malformed
fragment invalidates the entire handoff. Do not apply it or assign request
dispositions; record the handback and require a replacement packet, worktree,
branch, frozen SHA, and handoff identity. The invalid source stays immutable.

Ordinary canonical advancement through descendants of the candidate base is
valid and is not itself staleness. After handoff validation, recheck each
request independently against the latest canonical tree. A request is `stale`
only when its owner, heading or anchor, target authorization, provenance,
coupling, or material assumption has drifted enough that it cannot be evaluated
or applied as written. An unrelated commit, target edit, or duplicate target
declaration is not automatically stale. One stale request does not invalidate
separable unaffected requests. Revising a stale request requires a new frozen
candidate; never amend the old source.

The manual lifecycle is:

1. **Reserve.** Publish the lane packet with exclusive candidate write
   reservations and nonexclusive canonical target declarations.
2. **Author.** The candidate writes only its deliverables and optional one
   fragment. Every fragment request remains `pending`.
3. **Publish and freeze.** Push the exact candidate ref, record its immutable
   handoff, and stop candidate mutation.
4. **Validate the handoff.** Recheck identity, remote ref, ancestry, commit
   shape, write set, cleanliness, fragment syntax, and coupling.
5. **Recheck requests.** Inspect each current target, authorization,
   assumption, provenance, and overlap without treating normal descendant
   advancement as stale.
6. **Assign dispositions.** Give every request and every partial residual its
   required terminal outcome before removing a fragment.
7. **Apply when needed.** Apply only a valid frozen candidate. An all-reject,
   all-defer, or all-stale package does not need its fragment applied.
8. **Route accepted content.** The integration owner writes accepted material
   and any authorized deferral destination in its proper canonical owner.
9. **Remove the fragment.** No candidate fragment survives the final tree;
   absence alone does not establish disposition.
10. **Record terminal outcomes.** Put structured source and per-request
    trailers in the canonical integration commit.
11. **Validate the final tip.** Amend first, then run the complete applicable
    gate and independent review against that exact commit.
12. **Publish canonically.** Push the exact reviewed SHA with an exact expected-
    remote lease, prove the intended remote ref and upstream equality, and
    preserve evidence boundaries. Recheck the immutable source ref afterward;
    a concurrent source-ref violation leaves publication in recovery, not
    closed.
13. **Close the lane.** Keep the immutable source ref remotely reachable by
    default. Later cleanup requires explicit operator authority and proof of
    equivalent durable recovery.

## Terminal disposition records

Only the integration owner assigns these outcomes:

| Disposition | Required terminal record |
| --- | --- |
| `accept` | The whole request is incorporated or already satisfied; record the exact destination and effect |
| `partial` | Record every accepted subset and destination, then give every residual subset its own `reject`, `defer`, or `stale` record; nested `partial` is prohibited |
| `reject` | Make no requested change and record the terminal reason |
| `defer` | Make no current incorporation and name an exact existing or simultaneously authorized canonical destination |
| `stale` | Make no requested change and record the exact request-local drift |

`Defer` does not authorize a new question, card, directory, lifecycle state, or
`UNREFINED` item. If no implemented destination is already in the approved
write set, stop or choose another valid disposition; expanding the package
requires renewed planning.

Every canonical integration commit records:

- `Fragment-Integration-ID`;
- `Fragment-Source-SHA` and `Fragment-Source-Ref`;
- `Fragment-Base-SHA` and `Integration-Parent-SHA`;
- `Fragment-Package-Outcome`, exactly `applied` or `no-op`;
- one `Fragment-Request-Disposition` for every request; and
- for `partial`, one `Fragment-Accepted-Subset` and one
  `Fragment-Residual-Disposition` for every labeled subset.

Package `no-op` is not a request disposition. If no accepted candidate
deliverable or routed canonical update changes the tree, create an explicit
empty canonical integration commit with the same provenance and terminal
trailers. Fragment deletion, source preservation, or validation success never
substitutes for those records. Longer rationale belongs in an existing
canonical owner only when it remains useful beyond the exchange.

If a normal cherry-pick conflicts, inspect it, abort, and prove exact parent
restoration and cleanliness. If failure occurs after a successful application,
do not reset, clean, stash, amend, delete, or overwrite recovery state. Record
the pre-application parent, current branch and `HEAD`, staged and unstaged
diffs, untracked paths, and failure; preserve or lock that worktree; and restart
only on a newly authorized branch/worktree from the recorded parent. The
published candidate remains immutable throughout handback and recovery.

## Implementation after independent documentation lands

An implementation candidate may begin at canonical commit `B` while one or
more independent documentation sidecars land serially as canonical commits
`D1`, `D2`, and so on. The implementation remains a proposal based on `B`.
After its candidate checks pass, the integration owner applies the reviewed
semantic commit onto the latest canonical descendant, then integrates any
separately reserved coupled documentation draft. Final applicable validation
runs against that combined state.

Computational evidence may be reused only when path classification and Git
comparison prove every intervening change is non-executable documentation with
no configuration, schema, fixture, report-template, or test-harness consumer,
and the integrated executable/test-affecting tree is identical to the tested
candidate. If that proof is incomplete, rerun the applicable computational
gate. Documentation validation always runs on the final combined tree.

## Immutable execution

An immutable-execution lane is an approved local process, validation run,
runtime job, or cluster job whose evidence is bound to one exact repository
commit plus declared inputs, configuration, command/job identity, and output
or log locations. It does not grant production or cluster authority.

Concurrent documentation can clarify later interpretation but cannot change
which revision ran. If code, inputs, configuration, or execution semantics
must change, stop or supersede the run under a new identity; never relabel old
evidence as if it came from the new state.

## Validation and recovery

Each candidate checks its own clean diff and task-specific requirements. A
self-contained independent sidecar passes its applicable focused or
documentation checks; actionable cards do not require an external inbound
status link.

The integration owner may run a focused check after a risky landing when it is
needed to catch a bad boundary early, and runs one final combined gate before
publication. Only the canonical result can close a package or support evidence
claims.

On a handoff-identity failure, application conflict, unexpected candidate
write, dirty shared worktree, or failed validation:

1. stop integration and further mutation on the affected paths;
2. preserve candidate commits, worktrees, logs, and execution attribution;
3. abort only the normal in-progress cherry-pick using the reviewed runbook
   command;
4. classify the conflict as independent, coupled, or contract-changing; and
5. revise the lane packet or return the governing task to planning before
   continuing.

Request-local staleness inside an otherwise valid fragment follows the
per-request rules above; it does not automatically return unaffected requests.

Do not force integration, move unique files manually between worktrees, or
delete a candidate to make status look clean. Worktree cleanup is optional and
explicitly authorized. A checkout may be retired only after proving it has no
unique uncommitted filesystem state; committed raw-fragment history is
intentionally unique and remains reachable from the preserved remote source
ref. Candidate branches are preserved by default.
