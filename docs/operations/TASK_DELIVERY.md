# Task delivery

Task selection and context routing remain in
[`TASK_START.md`](TASK_START.md), with conditional routes in the
[top-level sitemap](../sitemap/TOP_LEVEL.md#temporary-task-start-routing).

## Default delivery

Sequential work in one authoritative worktree is the default. A homogeneous
tranche may contain several bounded packages or slices on one branch without a
push, lifecycle transition, broad impact analysis, or full gate between them.
At tranche start, establish the common affected-owner boundary, direct
consumers, shared risks, and final aggregate gate once. Reassess only when a
slice crosses that boundary or a mandatory expansion trigger appears.

For each package or slice:

1. State `Outcome`, `Touches`, and `Stop`, then implement only that bounded
   result and its directly required contracts.
2. Add or update direct tests and use focused checks when they provide useful
   feedback, protect a risky boundary, or are required by the next slice.
3. Update canonical documentation only for subjects the slice actually
   changes. Include any real card-state or completion change here.
4. Review the combined code, tests, and documentation as one semantic unit and
   commit it once.
5. Continue to the next in-envelope slice without status bookkeeping or broad
   revalidation unless the prior result is unsafe to build on.

One semantic commit per package or slice is the default. Split a package only
when its parts are independently reviewable and reversible, have genuinely
different evidence or authority boundaries, or cannot safely exist in one
commit. Do not split implementation, tests, direct documentation, and card
completion merely to preserve an old commit shape. Do not create selection,
deselection, progress, path-repair, or gate-receipt commits.

## Proportional validation

Focused checks are implementation feedback, not mandatory ceremony at every
slice boundary. Run them according to changed behavior and risk. At the end of
the homogeneous tranche, inspect the complete predecessor-to-tip diff and run
one de-duplicated complete applicable gate against that final combined state.
If a later change alters executable behavior, consumed configuration,
dependencies, schemas, fixtures, templates, Make targets, or test-harness
semantics after the gate, rerun only the invalidated evidence.

A standalone documentation-only package uses one documentation commit. When
its complete diff changes no executable or consumed configuration, generation,
schema, fixture, report-template, dependency, or test-harness behavior,
computational validation is not applicable. Run Git and documentation checks;
do not fabricate an implementation commit or run computational Python, shell,
R, report-runtime, full-suite, or cluster validation.

Pytest is quiet by default and retains captured output for failures. Use the
quiet Make and log-capture procedures in the
[`RUNBOOK.md` local validation gate](RUNBOOK.md#local-validation-gate); full
output is for failures or an explicitly requested verbose run.

## Subject-triggered documentation

Documentation changes when its subject changes, not whenever work advances.
Use the final semantic diff, targeted search, and the
[documentation ownership map](../sitemap/DOCUMENTATION_OWNERSHIP.md) to update
only affected owners and direct references:

| Changed subject | Update |
| --- | --- |
| Card scope, dependency, explicit lifecycle state, acceptance, retirement, or completion evidence | The stable card; ordinary selection and execution do not change it |
| Non-reconstructable checkout state, active concurrent lane, external blocker, recovery fact, or evidence boundary | `HANDOFF.md` |
| Durable roadmap order, package acceptance policy, or approved runway | `PIPELINE_PLAN.md` |
| Supported command or operator procedure | `RUNBOOK.md` |
| Durable rationale or settled constraint | `DECISIONS.md` and its topic owner |
| Immediate user-visible priority | `TODO.md` |
| Documentation responsibility or consolidation routing | `DOCUMENTATION_OWNERSHIP.md` |
| Public interface, path, schema, limitation, diagram, scientific claim, or evidence meaning | Its canonical contract or documentation owner |

A commit, branch, test run, card selection, pause, resume, or repeated unchanged
fact is not by itself a documentation trigger. `HANDOFF.md` is not a commit
receipt, `PIPELINE_PLAN.md` is not a per-slice log, and stable card paths remove
the need for inbound status-link repair. Use the repository-wide documentation
gate for structural coverage; broaden semantic inspection only for cross-
cutting change, ownership change, contradiction, or an unbounded impact.

## Publication boundary

Local commits do not imply publication authority. By default, publish a
coherent accepted tranche in one batch after final review, aggregate validation,
clean-worktree inspection, and history inspection. Then prove the intended
remote ref and upstream equality once. Push earlier only when another approved
lane or operator action genuinely depends on a durable remote checkpoint.

Runtime and cluster promotion remain upstream-sequential, including during an
approved local-only descendant sequence. Never promote a downstream stage
before its prerequisite runtime gates pass.

## Neutral cleanup capture

During an active slice, a cleanup-queue entry contains only the slice ID, the
touched source or path, and a neutral observation. Creating an entry performs
no ownership, destination, impact, or solution discovery. An unrelated
observation cannot expand the active card.

## Delayed movement

Misplaced information directly implicated by the active work becomes a move
candidate. Movement occurs only during cleanup: move the information, repair
its references, and remove the old copy. Do not copy information into a second
owner.

## Cleanup classification

An observation remains inside the active card only when resolving it is
necessary to satisfy that card's already-approved objective and contract. If it
expands the contract, has a different owner or gate, or can safely be deferred,
route it to separately selectable follow-up work. Route unrelated ideas to
durable intake. During the active slice, continue to capture collateral
observations neutrally without investigating ownership, destination, or a
solution.

During cleanup, inspect one queue entry only until one disposition is possible,
then stop discovery:

- `FIX_NOW_REQUIRED` — leaving the item unresolved would make current
  information incorrect, broken, unsafe, contradictory, or misleading.
- `FIX_NOW_TRIVIAL` — semantics are settled, the owner is obvious, scope is
  tiny and bounded, and correction is lower effort and risk than later intake.
  Decision-bearing public, scientific, schema, safety, or evidence changes are
  not trivial.
- `KNOWN_CARD` — the exact card is already known from authorized active
  context. Do not search for alternatives, and update that card only when the
  active scope authorizes it.
- `TASK_INTAKE` — every other potential task. Do not search the task registry
  during cleanup, and preserve the item until it has a durable intake
  destination.
- `NO_CHANGE` — the observation requires no repository change.

## Input-dependent decision records

When a noncritical disposition still requires user input, retain its active
record as a decision artifact until the disposition is durable. Retention does
not expand the active card, authorize related work, or by itself prevent close
of an otherwise accepted card.

## Slice start and close

Start a slice with exactly three lines labeled `Outcome`, `Touches`, and
`Stop`: one outcome, one bounded owner or path area, and one stopping
condition. If the charter needs multiple outcomes or stopping conditions,
split it again.

A slice closes when the bounded result exists, collateral observations are in
the cleanup queue, its directly affected documentation is current, and the
semantic result is committed. Focused validation is optional feedback unless
continuing would be unsafe or a later slice directly depends on the unverified
behavior. Ordinary slice close performs no broad canonical reconciliation,
lifecycle maintenance, full gate, or publication.

## Card close

After feature or procedure work freezes, close a card only if acceptance or
lifecycle is part of the package subject:

1. **Review** — semantically assess the final change and its affected owners.
2. **Validation** — run the applicable automated structural or behavioral
   checks.
3. **Verification** — prove the acceptance and lifecycle conditions. Record
   `State: completed` and a non-placeholder completion record in the same
   semantic commit. Publication is required only when the card's acceptance
   explicitly says so.

If the work merely selected, paused, resumed, or declined a card, there is no
card-close mutation. A `retired` card records a rationale and successor or
explicitly says that no successor exists.

Exact commands remain in the
[`RUNBOOK.md` local validation gate](RUNBOOK.md#local-validation-gate). This
procedure neither copies those commands nor introduces another validation
framework. Change the existing validator only if its tooling makes the
procedure impossible.
