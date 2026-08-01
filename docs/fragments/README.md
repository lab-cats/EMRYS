# Integration fragments

This directory is the candidate-to-integrator handoff surface for bounded
cross-owner documentation requests. A fragment is a transient coupled
proposal. It is never canonical documentation, a task card, a backlog, a lane
packet, status, evidence, or authorization to change the repository.

This README owns fragment filenames and candidate-side syntax only.
[`CONCURRENT_WORK.md`](../operations/CONCURRENT_WORK.md#integration-fragment-authority-and-lifecycle)
owns authority, handoff validity, request recheck, dispositions, lifecycle,
handback, recovery, and publication. Live lane and frozen-source identity
belong in [`HANDOFF.md`](../operations/HANDOFF.md#active-concurrent-lanes), and
commands belong in
[`RUNBOOK.md`](../operations/RUNBOOK.md#manual-integration-fragment-exchange).

## Filename and candidate boundary

- Use exactly `docs/fragments/<fragment-id>.md`; do not create subdirectories.
- `<fragment-id>` is a stable card ID or slug reserved in the lane packet. It
  uses uppercase ASCII letters, digits, and hyphens, begins with a letter, and
  contains at least one hyphen.
- One lane may own at most one fragment. Its exact path is an exclusive
  candidate write reservation; `README.md` is reserved for this schema.
- A candidate may contain its exact reserved deliverables plus zero or one
  fragment. The fragment cannot expand that write set.
- Canonical target declarations are nonexclusive integration requests, not
  candidate write reservations. Multiple lanes may name the same target; the
  integration owner serializes and rechecks them.
- Final canonical publication removes every candidate fragment. The recorded
  immutable remote source ref preserves the raw proposal; do not create a
  fragment archive or shadow backlog.

A fragment may record its candidate branch at authoring, but it cannot contain
its own commit SHA. Frozen SHA, expected commit shape, cleanliness, live remote
ref, and publication state belong only to the external handoff.

## Required fragment shape

Every fragment contains:

1. one descriptive H1 ending in `integration fragment`;
2. the metadata bullets below;
3. one or more `## Request \`<REQUEST-ID>\`` sections; and
4. no terminal disposition or canonical-state claim.

The required metadata labels are:

- `Fragment ID`;
- `Owning task`;
- `Lane ID`;
- `Candidate branch`;
- `Exact base`; and
- `Evidence and scope boundary`.

The branch value identifies the candidate at authoring; it does not supersede
the frozen source ref in `HANDOFF.md`. The boundary states what the fragment
does not establish, including applicable status and evidence limits.

## Requested-update fields

Each request ID is unique within the fragment and contains these labeled
fields:

Request IDs are nonempty and contain no line break, backtick, slash, equals
sign, or semicolon; those characters delimit headings and terminal records.
Stable subset labels used in terminal records follow the same delimiter rule.

- `Target owner`: one repository-relative canonical path;
- `Target heading or anchor`: one literal Markdown heading plus its expected
  GitHub-style anchor;
- `Target mode`: exactly `existing anchor`, `authorized-new anchor`, or
  `authorized-new owner`;
- `Requested update`: one bounded change, with stable subset labels when the
  subsets may receive different outcomes;
- `Provenance`: the exact source or task authority supporting the request;
- `Assumptions and coupling`: target authorization, conditions, overlap, and
  known conflicts that must be rechecked; and
- `Candidate disposition`: always literal `pending`.

For `existing anchor`, the owner and literal heading must exist at the recorded
base. `Authorized-new anchor` and `authorized-new owner` name the selected card
or approved scope that permits the addition. A missing target cannot silently
fall back to another mode.

Only the integration owner assigns the terminal vocabulary defined in
[`CONCURRENT_WORK.md`](../operations/CONCURRENT_WORK.md#terminal-disposition-records).
Fragment absence, deletion, or a passing documentation gate is not a
disposition.

## Candidate prohibitions

A fragment may cite source observations, but it cannot:

- publish checkout, lane, priority, lineage, blocker, task-lifecycle,
  completion, decision, or acceptance state;
- promote test, runtime, cluster, scientific, or biological evidence;
- authorize work, assign its own terminal disposition, or satisfy a required
  canonical inbound link;
- create a question, card, lifecycle location, or `UNREFINED` item merely by
  naming it; or
- require the integrator to retain the fragment in canonical history.

## Candidate template

```markdown
# <FRAGMENT-ID> integration fragment

- Fragment ID: `<FRAGMENT-ID>`
- Owning task: `<CARD-ID or bounded objective>`
- Lane ID: `<lane-id>`
- Candidate branch: `codex/<candidate-branch>`
- Exact base: `<full-canonical-base-sha>`
- Evidence and scope boundary: <explicit proposal and evidence limits>

## Request `<REQUEST-ID>`

- Target owner: `<canonical/path.md>`
- Target heading or anchor: `<literal heading>` / `<github-anchor>`
- Target mode: `<existing anchor|authorized-new anchor|authorized-new owner>`
- Requested update: <bounded request and labeled subsets when applicable>
- Provenance: <exact source or task authority>
- Assumptions and coupling: <authorization, conditions, overlap, conflicts>
- Candidate disposition: `pending`
```

## Worked example

A candidate request ends with `Candidate disposition: pending`; it does not
predict its outcome. The integration owner independently validates the frozen
handoff and current target, then records the terminal outcome outside the
fragment under the lifecycle policy. The completed CONCURRENCY-02 synthetic
exchange is indexed from
[`HANDOFF.md`](../operations/HANDOFF.md#completed-concurrency-02-synthetic-exchange);
this example defines syntax, not completion evidence.
