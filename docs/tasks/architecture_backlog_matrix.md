# EMRYS Architecture Campaign Backlog Matrix

> **PROVISIONAL CAMPAIGN RANKING — NOT AN IMPLEMENTATION BACKLOG**

Last ranked: **2026-08-25**

This file is a scoped planning view of the candidate cards in the
[architecture campaign](architecture_campaign.md). It records a cursory,
provisional Architecture Priority and Indicative Complexity comparison to
support small, just-in-time slices. This preliminary scoring pass was
explicitly approved by the user on **2026-08-25**.

The [main backlog matrix](backlog_matrix.md) remains authoritative for accepted
task IDs, implementation status, required outcomes, acceptance conditions, and
dispositions. This architecture matrix does not accept a candidate into the
implementation backlog, resolve an open design decision, or authorize work.
The campaign remains authoritative for the full rationale, alternatives,
binding requirements, open decisions, and ideal end state behind each card.
The outcome and routing columns below are navigation summaries. If their
wording ever conflicts with the campaign, the campaign controls until a task is
accepted into the main backlog.

`AC-SLICE-01` completed as `ARCH-CONST-01`, and `AC-SLICE-02` completed as
`ARCH-LAYER-01`, after this ranking was recorded. Their original `5`/`3` values
and rows remain for traceability rather than implying active work or a
reranking; the main matrix owns the terminal dispositions.

`ARCH-MODEL-AUDIT-01` subsequently completed the read-only current-state
prerequisite for `AC-SLICE-03`. Per the approved recording boundary it did not
complete, accept, implement, or rerank that campaign card; the original
`5`/`4` values remain provisional.

## Scoring

Both columns use `5` as the highest value. Scores are intentionally loose and
must be reconsidered when a card is bounded or split. They help select the next
candidate for just-in-time review; they are not the final Importance and
Complexity scores later assigned to accepted tasks in the main backlog.

### Architecture Priority

| Score | Meaning in this architecture view |
|---:|---|
| `5` | Campaign-defining outcome or non-negotiable architectural direction |
| `4` | Major recurring user, operator, reliability, or strategic benefit |
| `3` | Meaningful follow-on or just-in-time enabling work |
| `2` | Useful but opportunistic work with an adequate near-term alternative |
| `1` | Retained companion work outside the architecture campaign's implementation scope |

### Indicative Complexity

Complexity estimates the remaining effort and risk needed to close the
**current card as written**, including operative realization, migration,
compatibility, and proportionate proof rather than merely drafting a design.

| Score | Meaning |
|---:|---|
| `5` | Cross-cutting public, lifecycle, runtime, recovery, scheduler, or portability migration with demanding integration evidence |
| `4` | Multi-owner interface or contract change with compatibility and integration work, or specialized high-risk review/validation requiring independent proof |
| `3` | Bounded multi-module work, architectural definition, or moderate new public surface |
| `2` | Primarily read-only or localized work with focused validation |
| `1` | Localized, straightforward change with little migration risk |

Architecture Priority and Indicative Complexity are independent. They are not
multiplied into a composite score, and neither column establishes
implementation order, dependencies, or approval.

## Campaign-card matrix

| Card | Track | Architecture Priority | Indicative Complexity | Campaign outcome | Likely routing | Sizing note |
|---|---|---:|---:|---|---|---|
| `AC-SLICE-01` | Foundations | `5` | `3` | Ratified an architectural-invariants constitution against live contracts and representative tests | Completed as `ARCH-CONST-01`; broad `ARCH-01` remains Open | Original provisional ranking retained for traceability |
| `AC-SLICE-02` | Foundations | `5` | `3` | Ratified responsibility clusters, three graph semantics, forbidden authority transfers, and fast source-boundary enforcement over exact current CLI seams and transitional imports | Completed as `ARCH-LAYER-01`; broad `ARCH-01` remains Open | Original provisional ranking retained for traceability |
| `AC-SLICE-03` | Public model | `5` | `4` | Audit current representations, owners, callers, lifetimes, mutation, identity construction, protections, retained evidence, and compression opportunities without selecting any application model; only the binding meaning of Run as an immutable plan is settled | Read-only prerequisite completed as `ARCH-MODEL-AUDIT-01`; campaign card remains Open per the approved boundary | Whether Run is public, public nouns and nesting, cardinalities, Run-versus-Attempt identity, APIs, persistence, compatibility, migration, and any implementation remain Open until separate user-approved decisions |
| `AC-SLICE-04` | Scientific boundary | `3` | `4` | Decide whether a shared thin operation representation is justified and, if so, define the minimum boundary and prove it through one representative migration only after the mapping test passes | New slice; coordinate with `ANALYSIS-02` and `ARCH-01` | Paper-map diverse owners before selecting a denominator; generalize only after a second owner maps without distortion |
| `AC-SLICE-05` | Execution | `4` | `5` | Ratify the execution guarantee contract, select the minimum justified capability boundary, and prove equivalent declared guarantees across supported local and SLURM backends | New slice; enriches `OPS-02` | Cross-execution integration and parity proof drive the estimate; one API is not preselected |
| `AC-SLICE-06` | Policy ownership | `3` | `3` | Inventory duplicated policy decisions, declare their final authorities, and centralize only a selected repeated decision whose migration proves net reduction | New per-policy slices after inventory; supports `ARCH-01` | Inventory first; centralization is conditional and individual migrations may range from `2` to `5` |
| `AC-SLICE-07` | Artifact lifecycle | `4` | `5` | Define artifact-class lifecycle/admission requirements, decide whether any shared lifecycle or distinct Artifact Store is justified, and migrate one path only if the selected design requires a boundary change | New slice; supports `ARCH-01` | Separate class-specific requirements, shared-boundary decision, and any conditional representative path migration |
| `AC-SLICE-08` | Execution configuration | `4` | `4` | Define named execution profiles independently of Managed/Site/Explicit runtime modes | New slice; coordinates with `OPS-01` and `RUNTIME-01` | — |
| `AC-SLICE-09` | Inspection | `3` | `3` | Provide expert explain/inspect interfaces for effective plan, run, artifact, and evidence | New slice or expansion of `OPS-02`/`CONTROL-01` | — |
| `AC-SLICE-10` | Operations | `4` | `4` | Define high-level status and safe resume/recovery UX over existing fail-closed internals | New slice; coordinates with `OBS-02` | Recovery and fault evidence are part of closure |
| `AC-SLICE-11` | Results | `3` | `5` | Define a portable canonical Run Bundle contract | New slice; coordinates with `FILESYSTEM-01` and `RESULTS-01` | Separate the bundle contract from portability, archival, and external-artifact realization |
| `AC-SLICE-12` | Results | `4` | `3` | Formalize scientific, evidence, and operational report purposes and navigation | New slice or expansion of `REPORT-03` and `RESULTS-01` | — |
| `AC-SLICE-13` | Golden path | `5` | `5` | Deliver a supported fresh-install-to-valid-synthetic-result golden path after ratifying its capability order | New cross-cutting outcome; coordinates with setup, runtime, Doctor, run, results, and `CLEAN-01` | Capstone acceptance outcome, not an atomic implementation package |
| `AC-SLICE-14` | Measurement | `3` | `2` | Establish reproducible UX and architecture baselines plus separately interpreted product-implementation, protection/test, configuration/documentation, and retained-evidence baselines | New slice; coordinates with `REVIEW-UX-03` and `ARCH-01` | Establishes aggregate methods; mandatory category-separated accounting begins with every slice now and is not deferred to this card |
| `AC-SLICE-15` | Scientific companion | `1` | `4` | Audit the Steps 07–09 statistical contract | New scientific-review slice; not architecture evidence | Parallel scientific-review work |
| `AC-SLICE-16` | Scientific companion | `1` | `4` | Build independent numerical oracles for Steps 08 and 09 | New scientific-validation slice | Parallel scientific-validation work |
| `AC-SLICE-17` | Retirement | `3` | `5` | Retire duplicated lifecycle, validator, infrastructure, adapter, or compatibility paths after each replacement is proven; retained evidence may be deleted only after an exact scoped proposal and the user's explicit approval | Multiple bounded deletion slices; never one unbounded cleanup task | Create one retirement task per proven replacement; isolate any approved evidence deletion in its own commit and never use it to offset product growth |
| `AC-SLICE-18` | Documentation | `4` | `3` | Rewrite navigation and documentation around scientist/operator/developer journeys | Expansion or slicing of `DOC-01`; uses the accepted `DOC-02`/`DOC-03` traces and coordinates with `DOC-04`–`DOC-05` retirements | Scope follows the settled role journeys |
| `AC-SLICE-19` | Doctor | `4` | `5` | Define Doctor repair ownership, supported mutations, preview/reporting, and safety contracts | Expansion of `DOCTOR-01` reflecting the explicit override | Separate the repair constitution from each supported repair action |

`AC-SLICE-15` and `AC-SLICE-16` remain visible so the campaign does not lose
its parallel scientific-review commitments. Their `1` score is only an
Architecture Priority classification within this view; it is not a statement
about their scientific importance.

## Interpretation notes

- `AC-SLICE-13` is a high-priority capstone acceptance outcome, not an atomic
  implementation package. Its supporting capabilities require smaller bounded
  slices and separate sequencing decisions.
- The Sizing note column flags broad cards without assigning a campaign
  disposition. Candidate acceptance, revision, splitting, absorption, or
  decline remains a later explicit decision.
- A card should be promoted only after a read-only owner/caller review defines
  one observable outcome, non-goals, preserved invariants, open decisions,
  acceptance evidence, and an honest evidence ceiling; records its compression
  opportunities and proposed dispositions; classifies affected protections and
  retained evidence; and identifies every mutable exception and temporary
  compatibility path with its owner and retirement condition.
- Use the campaign's canonical
  [per-slice compression and mutation protocol](architecture_campaign.md#131-mandatory-per-slice-compression-and-mutation-protocol)
  for the register and category-separated closeout. Promotion never implies
  authority to delete retained evidence; that requires an exact proposal,
  explicit user approval, and a separate commit.
- One provisional working method is to revisit ranking just in time rather
  than require complete campaign sequencing up front. This does not resolve
  the campaign's open capability order or any individual task sequence.
