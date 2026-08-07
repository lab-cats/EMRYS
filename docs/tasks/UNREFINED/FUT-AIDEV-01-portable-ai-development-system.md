# FUT-AIDEV-01 — Explore a portable AI-development operating system

State: [`UNREFINED` proposal](README.md). This is low-urgency information
preservation, not a platform plan or authority to change NORAD.

## Proposal

Explore a small, project-agnostic, file-first system for AI-assisted software
development by extracting only practices proven in NORAD and a materially
different second repository. NORAD is an incubator and reference
implementation, not the generic product.

The candidate model has three layers:

| Layer | Responsibility | Candidate contents |
| --- | --- | --- |
| Generic kernel | Reusable mechanics and invariants | Stable task identity, lifecycle and dependency semantics, intake, context routing, proportional gates, validation receipts, ownership rules, generated views, concurrency reservations, and approval boundaries |
| Project profile | Repository and domain policy | Layout, commands, gates, documentation owners, safety and evidence vocabulary, runtime environments, toolchain, branch policy, and publication authority |
| Live project state | Inspectable state for one project | Cards, decisions, questions, tranche, handoff, blockers, branches, evidence, receipts, and lane reservations |

Human-readable files and Git remain canonical. A reusable library and CLI may
own shared schemas and deterministic operations; skills, MCP, plugins,
dashboards, and other adapters consume that same state rather than becoming a
fourth owner.

## Why preserve it

Conversational context is temporary, compacted, and hard to share safely.
Adding unowned prose can increase duplication and inconsistency. The working
hypothesis is that good infrastructure exposes the smallest authoritative
context needed for a decision while preserving complete, inspectable,
versioned knowledge. Efficiency comes from removing duplicate work and state,
never from omitting necessary evidence, reasoning, review, or validation.

## Settled boundaries

- This proposal authorizes no extraction, implementation, package, template
  repository, library, CLI, MCP server, plugin, NORAD change, or decomposition
  into implementation cards.
- Mutable facts keep one authoritative owner; generated indexes and dashboards
  are deterministic projections.
- Work remains coarse until selected and is planned just in time. Bounded
  autonomy does not transfer canonical decision or integration authority.
- Project-specific rules configure generic mechanics rather than leaking into
  the kernel. NORAD biology, tools, stage identities, CSU HPC and SLURM rules,
  R environment, report and artifact schemas, evidence language, scientific
  interpretation, live paths, branches, commands, counts, and blockers remain
  in the NORAD profile or live state.
- Extract a practice only after evidence shows it works and removes more manual
  state than it adds.

## Candidate mechanisms worth retaining

Task and work management:

- stable card identities and paths with small lifecycle metadata;
- nonselectable intake, selectable TODO work, frozen integration review,
  completed history, logical epics, and tranche views without conflating them;
- one authored dependency direction with generated reverse and unblock views;
- technological blockers separated from context, order, approval, environment,
  repository state, and in-card checklist requirements;
- a persistent freeform inbox with reviewed batch classification;
- a disposition vocabulary that distinguishes documentation changes, process
  changes, card amendments, new actionable work, unrefined preservation, open
  choices, absorption, and rejection; and
- rolling-wave planning, bounded tranche approval, and generated tranche views.

Context and documentation:

- concise revision-aware task-start routing, diff-first reuse, and explicit
  risk or ownership expansion triggers;
- targeted search and tests as selected evidence rather than universal startup
  reading;
- separate owners for current state, roadmap, architecture, target
  architecture, commands, validation, decisions, questions, and diagnosis;
- a minimal handoff containing only current executable state, active work,
  genuine blockers, evidence boundary, and resume point;
- semantic retention classes with unique rationale, invariants, failure modes,
  scientific cautions, and legacy behavior preserved at a named owner; and
- shallow local READMEs, glossaries, descriptive names, and no-loss
  documentation review before gap scans or physical consolidation.

Validation, evidence, concurrency, and authority:

- risk-proportional gates, focused feedback, and one applicable final gate;
- no computational rerun for non-consuming documentation-only changes;
- receipts bound to validation subject, gate definition, inputs, environment,
  result, time, and evidence class, with reuse only after equivalence proof;
- machine-readable gate selection only after policy stabilizes;
- quiet success, durable failure logs, explicit evidence ceilings, and
  independent oracles that do not import producer expectations;
- unique branches and worktrees with explicit bases, write reservations, and
  proposal-versus-canonical separation;
- immutable execution attribution, preservation of conflicts and unique work,
  and one canonical integration owner; and
- bounded approval envelopes that still stop on scope expansion, destructive
  action, external publication, new authority, or unresolved architectural or
  scientific meaning.

Reusable tooling may include narrowly proven review, intake, context, gate, and
validation skills. Specialized roles should default to bounded skills or
review modes rather than hidden persistent state. Semantic risk determines
review depth; cheap mechanical output still requires independent verification.

## Adapter and distribution boundary

An MCP server could expose bounded reads, searches, context packets, draft
proposals, or deterministic generated views, but it is only an adapter over the
same file-backed library and CLI. It begins read-only or draft-producing.
Promotion, completion, evidence publication, worktree or branch mutation,
merge, rebase, push, deletion, and production or scientific state changes stay
privileged or excluded unless a later reviewed design provides narrow schemas,
explicit authorization, dry-run, audit records, and fail-closed behavior.

Any index must be stateless or fully rebuildable, work locally without a
service, remain optional, and use explicit schema and capability versions.
Template repositories, libraries, CLIs, plugins, and MCP servers are possible
distribution forms, not decisions. Current platform capabilities must be
reverified when this proposal is refined.

## Antipatterns and adversarial checks

- Do not front-load an entire tranche, make conversation the only memory, or
  optimize token counts past correctness and semantic sufficiency.
- Do not make generated views editable truth, handoffs historical databases,
  cards journals, runbooks program stores, or Git recoverability a substitute
  for discoverability.
- Do not automate unsettled gate policy, confuse pass totals with sufficiency,
  call producer-derived expectations independent, or mix fixture, runtime,
  cluster, scientific, and biological evidence.
- Do not treat agent identity as filesystem isolation, integrate concurrent
  unresolved writes, encode sequence as blockers, or force integration because
  effort was spent.
- Do not recreate a project-management product in Markdown, generalize from
  one repository, add infrastructure that costs more than it saves, or let
  meta-work displace product delivery.
- Require a complete project profile, deterministic regeneration, explicit
  source labeling, optional concurrency, small schemas, replaceable standards,
  and a materially different portability pilot.

## Evaluation contract to retain

- Any later prototype must include conformance fixtures for schemas, lifecycle
  transitions, gate selection, and deterministic generated views.
- Measure time from idea to executable task, mandatory files read,
  administrative edits, repeated validation avoided, approval interruptions,
  integration conflicts, stale mutable facts detected, and user-visible
  behavior delivered. Correctness and semantic sufficiency override every
  efficiency measure.
- Add an MCP surface only after it demonstrates incremental value over the same
  files and CLI; keep concurrency optional and threshold-driven; retain
  noncurrent knowledge only for a named consumer or refactor purpose.

## Questions before refinement

- What is the smallest agent-neutral kernel, and which conventions are truly
  mandatory?
- Should Markdown or YAML be primary, where do profiles live, and how are
  schema migrations handled?
- Are generated views committed or produced on demand?
- Where does intake live, and how do external issue trackers interoperate
  without duplicating truth?
- Can receipts be trustworthy without a service or database?
- Which adapter operations may mutate, under what identity and permission
  model, and with what audit and fail-closed behavior?
- What value, if any, do persistent personas add beyond bounded roles? That
  distinct question belongs to `FUT-AGENT-01`.
- What measurements demonstrate lower friction without hiding omitted context,
  and which second repository supplies the portability test?

## Promotion conditions

- Relevant NORAD practices are stable and evidenced by completed use.
- The mechanism demonstrably removes more friction and manual state than it
  introduces without displacing product work.
- NORAD-specific assumptions separate cleanly into a project profile.
- A materially different repository provides a plausible portability test.
- Review the smallest kernel, exclusions, authority model, conformance
  evidence, measurements, and time-boxed evaluation boundary before creating a
  complete TODO card.
