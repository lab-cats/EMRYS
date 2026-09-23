# DOCS-01 discovery notes, sixth file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F164–F172. F164–F167 compare local head `f79bc435`; F168 and the
F19/F64/F92 refinements compare `5aaa17f0`; F97/F107/F169 use `25f62591`;
F170 uses `8ef78400`, and F171–F172 use `c6ec1562`, read on 2026-09-23. The
full coordinator contract and root/operator/owner history sweeps found no
other substantial reduction. Counts are
review spans and conditional arithmetic, not verified savings or approval to
alter guides, accepted status, or evidence. No product, test, CI, or cluster
command was run.

### F164 — Optimization bounded delivery repeats workflow

The [optimization campaign](optimization_campaign.md) lines 403–416 has a
14-line Bounded delivery section. Its selection, caller review, consolidation,
owner placement, approval, accounting, and status rules substantially restate
the [workflow](../operations/WORKFLOW.md) lines 9–18, 29–45, 47–85, and 89–92.
The campaign already links that workflow at lines 9–16. Its measurement and
adoption section at 376–400 retains exact experiment identity, raw trials,
gates, and institutional evidence limits. The delivery section's useful local
points are retiring superseded scans/allocations across affected callers,
binding exact benchmark evidence to the tested revision, and refreshing old
candidate observations without a parallel status ledger. No tracked Markdown
link targets its heading. A six-to-eight-line campaign-specific section could
save roughly six to eight of the 14 lines, conditional on a draft and link
check; no saving has been verified.

### F165 — CV campaign priority history repeats delegated index

The [CV campaign](cluster_verification_campaign.md) lines 29–38 spends ten
lines on priority ordering, the corrected Doctor retry account, three later
original-sequence additions, and unprioritized later observations. The
[delegated priority index](cluster_verification_backlog.md#priority-index)
lines 93–121 owns each CV-01–27 priority and status; [CV-05](cluster_verification_backlog.md#cv-05-reuse-versus-repeated-repair-work)
lines 2418–2426 records reused installation, quick R restore, and repeated
verification. The campaign's own lines 11–17 already delegate card priorities
and acceptance. A roughly four-line route might save six lines, but it must
still distinguish later-added CV-11/12/22 and unprioritized CV-U/UX records.
No replacement or net saving has been verified.

### F166 — Final-source resource policy repeated in main checklist

The [main closure checklist](backlog_matrix.md#cluster-verification-closure-checklist)
lines 114–122 is a nine-line review span; line 114 also ends the preceding
sentence. The span restates the selected test-owned profile,
allocation-derived CPU/memory, 2048 MiB fixture-only minimum, disposable
Slurm request, parallelizable-lane policy, and hosted-versus-Viking evidence
limit. The durable [test-tool guide](../../tests/tools/README.md) lines 25–30
already owns the fixture floor, allocation-aware defaults, disposable Slurm
request, and performance ceiling. [CV-U06](cluster_verification_backlog.md#cv-u06-available-resources)
lines 505–521 adds the selected-profile history and the all-visible-CPU versus
ordered-serial CI rule; that rule has no identified durable owner outside the
main checklist. A two-to-three-line checklist route could save roughly five to
six lines only if it retains that rule or routes to a durable owner, and the
exact selected-profile identity and evidence ceiling remain accessible. This
is not a verified saving.

### F167 — CV campaign remaining-delivery summary repeats matrix

The [CV campaign](cluster_verification_campaign.md) lines 55–82 uses 28
physical lines, including three blanks, to restate selected source corrections,
the main closure checklist, the CV-U06 and CV-10 limits, and other accepted or
deferred owners. The [main matrix](backlog_matrix.md#novice-setup-and-operational-follow-up)
lines 75–101 and its [closure checklist](backlog_matrix.md#cluster-verification-closure-checklist)
at 103–152 own selected outcomes, while the [CV backlog](cluster_verification_backlog.md)
lines 24–30 and 70–79 owns delegated card status. [F03](docs-01-discoveries.md#f03-init-02-in-cluster-summaries)
separately records that the summary's INIT-01–03 source-complete claim exceeds
INIT-02's Open status and explicit-manifest behavior. A nine-to-twelve-line
scope and owner route might save 16–19 lines. It must preserve the campaign's
no-new-execution claim at 68–73, the CV-U06 accounting and CV-10 trusted-workspace
exceptions, and the separate authority warning at 84–86. Its E01–E12 evidence
register and completion criteria remain distinct. The section heading is an
inbound destination from the main matrix at line 76 and CV backlog at line 24.
No drafted replacement or link check has verified a saving.

### F168 — Scheduler stream names repeated in the logging contract

**Dismissed after recheck at `65397ad9`.** This overlaps dismissed
[F22](docs-01-discoveries.md#f22-coordinator-cross-owner-detail), which already
compared [logging contract](../design/LOGGING_CONTRACT.md) lines 191–235 with
the [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 410–429, 461–468, and 691–698. The 202–213 review span repeats current
and legacy scheduler names, but also locates Project streams, separates them
from application logs, says dry-run opens neither, and limits scheduler identity
to correlation metadata. Coordinator request admission and logging diagnostics
serve distinct readers. This entry's proposed five-to-seven-line saving added
no new evidence to reverse F22's conclusion; no useful reduction is established.

### F169 — Runtime Discover display rule repeated in the coordinator contract

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 289–297 defines shared labels, semantic emphasis, and unchanged plain,
redirected, dumb-terminal and `NO_COLOR` output for Runtime Discover and other
scientist-facing commands. Its Runtime Discover lines 321–324 retain unique
`READY`/`NOT READY`, no-write/admitted outcomes, verbose checks, and any shared
source seal, then repeat the common color/plain rule. Line 323 begins the
unique seal continuation; 323–324 are a review span, not two removable lines.
A two-line account of 321–324 might save two physical lines after reflow while
keeping the unique outcomes and seal. No draft, net saving, or command result
was verified.

### F170 — First-watch log controls before a Run exists

At local audit head `8ef78400`, [Quickstart](../../quickstart.md) lines 176–185
shows `emrys watch` after submitting, then says Up scrolls back and `G` follows
new log lines. The [watch presenter](../../src/emrys/orchestration/run_coordinator/_inspection_presentation.py)
lines 1163–1167 instead opens overview for a retained request without a Run;
it opens evidence/log view directly for an explicit Run without a request.
The same source at 45–59 and 168–201 maps `3`/`v` to evidence view and Up/G to
scroll/follow within the active view. The [Runbook control table](../operations/RUNBOOK.md#watch-one-fixed-selection)
lines 96–104 already names `3`/`v`. Thus the novice queued-request path needs a
view choice before those keys act on log lines. This is a conditional reader
ambiguity, not a missing watch capability or proof of a runtime defect. No
interactive watch was run and no line saving was established.

### F171 — Processing reuse link opens the contract at its top

At local audit head `c6ec1562`, the [optimization campaign](optimization_campaign.md)
line 326 labels a link “Processing reuse,” but its reference definition at
line 441 targets the coordinator `CONTRACT.md` without a section anchor. That
file has 1,248 lines; its [processing reuse and provider boundary](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#processing-reuse-and-provider-boundary)
begins at line 882 and describes the compatible upstream Run and exact artifact
admission. The campaign's historical measurement context remains distinct.
This is a reader route into the wrong part of a large owner contract, not a
claim that reuse or performance is defective. No guide was changed or Run
executed.

### F172 — Glossary format links bypass exact owners

At local audit head `c6ec1562`, the [glossary](../reference/GLOSSARY.md) line 61
defines PDF as a Step 09 scientific plot, but its “reporting owner” link opens
the [HTML report guide](../../src/emrys/reporting/README.md), which names no
PDF output. The [Step 09 owner](../../src/emrys/analyses/paired_cmh_candidate_ranking/README.md)
lines 8–11 names the two PDFs; its [contract](../../src/emrys/analyses/paired_cmh_candidate_ranking/CONTRACT.md)
lines 56–72 fixes the six-output roster. Glossary line 33 similarly sends CSS
readers to the broad report guide, which names no stylesheet; the
[styles owner](../../src/emrys/reporting/styles/README.md) lines 3–6 describes
the shared CSS and presentation-only limit. Both existing glossary statements
retain their evidence ceilings. This is link ownership, not a format or report
behavior defect; no file or rendered report was changed.

## Other focused source comparisons at `8ef78400`

The current root and operator guides were reread against CLI/coordinator source
and selected direct tests; runtime, resource, configuration, reporting,
storage, reference, CI, test-tool, and history guides received focused source
or retained-Git checks. Existing records cover the material overlaps in these
scopes, including Quickstart F04/F05, Doctor F07/F126, evidence F18/F19,
test tooling F56/F162, and resources/reporting F54/F70/F72/F109/F152.
Project schema v1 requires one dataset, one reference, and at least one named
Analysis, consistent with the architecture's public model. Full source and
retained-evidence comparison remain open. These were static comparisons, not
executed CLI, CI, hosted-artifact review, institutional proof, or scientific
review.

## Link-route recheck at `c6ec1562`

A read-only scan of all 170 tracked non-audit Markdown files found no exact
inbound Markdown destination to the headings claimed unlinked in F19, F25,
F64, and F164, nor to the five file-level targets in F96 and F129. This
rechecked nine destination/anchor pairs; it does not account for external
bookmarks or non-Markdown readers. Focused operator, design, owner, task,
history, test, and CI routes found F171–F172 and already recorded F21/F59/F161.
Existing links were read at their destinations, not rendered or exercised.
