# DOCS-01 discovery notes, sixth file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F164–F187 and a recheck of F158. F164–F167 compare local head `f79bc435`; F168 and the
F19/F64/F92 refinements compare `5aaa17f0`; F97/F107/F169 use `25f62591`;
F170 uses `8ef78400`, F171–F172 use `c6ec1562`, and F173–F175 use
`286f646a`; F158/F176 use `3de8366b`, F124/F172 rechecks use
`35668cc8`, F166/F169/F175/F177–F178 rechecks use `8489836c`, and F179 uses
`ce4d22f8`, F180–F181 use `619e60b7`, F182–F184 use `c1969b84`, and
F185–F187 use `f8c49f9e`, read on 2026-09-23. The full coordinator contract
and root/operator/owner history sweeps found no other substantial reduction.
Counts are
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
main checklist. A four-to-five-line checklist route might save only three to
four lines after retaining that rule, the exact selected-profile identity,
pending hosted status, and the Viking/institutional evidence ceiling. Line 114
is shared with the preceding sentence, so this is conditional arithmetic, not
a verified saving.

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

**Dismissed after recheck at `8489836c`.** The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 289–297 defines shared labels, semantic emphasis, and unchanged plain,
redirected, dumb-terminal and `NO_COLOR` output for Runtime Discover and other
scientist-facing commands. Its Runtime Discover lines 321–324 retain unique
`READY`/`NOT READY`, no-write/admitted outcomes, verbose checks, and any shared
source seal, then repeat the common color/plain rule. Line 323 begins the
unique seal continuation; 323–324 are a review span, not two removable lines.
Only the closing color/plain clause overlaps. The local display guarantee is
useful beside the Discover outcomes, and no worthwhile reduction from the
four-line passage is established. No command result was verified.

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

### F172 — Glossary detail links bypass exact owners

At local audit head `c6ec1562`, the [glossary](../reference/GLOSSARY.md) line 61
defines PDF as a Step 09 scientific plot, but its “reporting owner” link opens
the [HTML report guide](../../src/emrys/reporting/README.md), which names no
PDF output. The [Step 09 owner](../../src/emrys/analyses/paired_cmh_candidate_ranking/README.md)
lines 8–11 names the two PDFs; its [contract](../../src/emrys/analyses/paired_cmh_candidate_ranking/CONTRACT.md)
lines 56–72 fixes the six-output roster. Glossary line 33 similarly sends CSS
readers to the broad report guide, which names no stylesheet; the
[styles owner](../../src/emrys/reporting/styles/README.md) lines 3–6 describes
the shared CSS and presentation-only limit. At `35668cc8`, the glossary's
introduction at lines 3–4 promises that each entry links the detailed owner,
but BED12 at line 22, FAI at line 43 and RG at line 72 link brief sections of
the [scientific decision](../design/decisions/scientific-pipeline.md) at 36–49.
Their exact checks instead live in the [BED12](../../src/emrys/stages/gtf_to_bed12/CONTRACT.md)
contract at 22–68, [FASTA-sidecar](../../src/emrys/stages/fasta_sidecars/CONTRACT.md)
contract at 34–45, and [canonical BAM](../../src/emrys/stages/canonical_bam/CONTRACT.md)
contract at 41–54. The decisions remain useful rationale; the definitions and
evidence ceilings remain valid. This is link and introductory-scope precision,
not a format, report or validation defect. No guide or output was changed.

### F173 — Step 05 producer read-group exactness overclaimed

At local audit head `286f646a`, the [Step 05 contract](../../src/emrys/stages/split_n_cigar/CONTRACT.md)
lines 35–38 says the producer requires exactly one matching `ID`/`SM` read
group. The [shell worker](../../src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh)
lines 87–101 counts one `@RG` line but uses substring patterns for both fields.
For sample `sample`, an `SM:sample-other` field can satisfy its `SM:sample`
pattern. The separate [BAM readiness check](../../src/emrys/libraries/alignments/bam.py)
lines 56–65 splits the header into tab-separated fields and requires exact
`ID:sample` and `SM:sample`; the [grouped validator](../../src/emrys/stages/split_n_cigar/validator.py)
lines 94–95 calls it. The [direct worker test](../../tests/stages/split_n_cigar/test_step_05_split_n_cigar_reads.sh)
lines 114–119 and 223–242 uses matching fields and no prefix challenge. The
contract overstates producer-local exactness; this does not establish that a
full Run admits malformed output or that GATK normally emits it. No worker or
validator was run in this audit.

### F174 — Step 06 verified-marker contents overstated

At local audit head `286f646a`, the [Step 06 contract](../../src/emrys/stages/mechanical_orientation/CONTRACT.md)
lines 56–57 says tool versions and final hashes belong in the workflow
verified record. The [verified-task schema](../../src/emrys/contracts/schemas/orchestration/v1/verified_task.schema.json)
lines 7–17 and [publisher](../../src/emrys/orchestration/run_coordinator/task.py)
lines 2885–2893 put only the terminal task-attempt path and hash in that
marker. The terminal attempt's output snapshots carry hashes (same source,
lines 2406–2425); its task-start record links to the workflow Attempt, whose
`required_tools` entries contain tool versions
([workflow Attempt schema](../../src/emrys/contracts/schemas/orchestration/v1/workflow_attempt.schema.json)
lines 170–175 and [tool identity schema](../../src/emrys/contracts/schemas/orchestration/v1/common.schema.json)
lines 191–206). The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 966–972 already describes the small marker and linked attempt. This is
an evidence-location ambiguity across linked records, not missing hashes or
versions. Records were read from source definitions, not generated or checked.

### F175 — STAR gzip test scope ambiguous

**Dismissed after recheck at `8489836c`.** The [Step 01 test guide](../../tests/stages/star_alignment/README.md)
line 3 explicitly describes mocked STAR results and says both compression
modes are covered. Its [direct worker test](../../tests/stages/star_alignment/test_step_01_star_align.sh)
lines 48–49 and 68–72 copies plain FASTQ bytes into `.gz`-named files; fake
STAR at lines 20–44 records arguments and writes stand-in outputs without
reading the FASTQs. The test checks the worker's actual suffix-selected gunzip
branch and mixed suffix rejection. Genuine gzip data appears in separate [FASTQ admission](../../tests/ingestion/sample_manifest_admission/test_check_fastq_pairs.py)
lines 25–39 and 85–105 and [onboarding](../../tests/orchestration/run_coordinator/test_onboarding.py)
lines 1264–1307 tests, which have different owners. The mocked guide does not
claim decoding inside STAR, and its branch coverage matches the worker's
choice. No false scope claim or useful DOCS-01 reduction is established; no
test was executed here.

### F176 — Polish campaign closing selection paragraph repeats its opening

At local audit head `3de8366b`, the [polish campaign](polish-campaign.md)
lines 1043–1047 repeats the selection and status authority already stated in
its introduction at 3–20 and in the [workflow](../operations/WORKFLOW.md)
lines 9–29 and 69–85. Its instruction not to maintain parallel mutable status
also repeats the workflow's single-matrix rule. No tracked Markdown link
targets the `Campaign disposition` heading. The adjacent lines 1049–1052
uniquely require a terminal disposition for every proposal and verified
transfer of useful content before retirement; those rules and the heading
remain. Removing only the repeated first paragraph and its following blank
could save six physical lines, conditional on a draft and link check. This is
distinct from F140's earlier 21-line generic procedure and F160's seven-card
follow-up list. No replacement or net saving has been verified.

### F177 — CV-06 novice failure detail repeated across cards

At local audit head `8489836c`, [CV-06](cluster_verification_backlog.md#cv-06-actual-data-onboarding)
lines 2540–2560 spends 21 physical lines recounting the September 16 guided
Viking novice-path failure. The reference/selector sequence is detailed in
[CV-U18](cluster_verification_backlog.md#cv-u18-interactive-input-list-creation)
lines 1143–1164; external FASTA/GTF and stop guidance in
[CV-U20](cluster_verification_backlog.md#cv-u20-complete-viking-values-in-quickstart)
lines 1281–1290; command grouping and creation handoff in
[CV-U11](cluster_verification_backlog.md#cv-u11-paste-ready-quickstart-commands)
lines 753–760; and optional smoke/readiness in
[CV-U08](cluster_verification_backlog.md#cv-u08-quickstart-scope-and-language)
lines 592–603 and 621–625 and [CV-U09](cluster_verification_backlog.md#cv-u09-synthetic-project-explanation)
lines 692–701. CV-06 uniquely records that these gaps failed as one guided
journey. A dated, linked 9–12-line account might save 9–12 lines, conditional
on actual wrapping. It must retain the four-gap grouping, negative
institutional evidence, and **Open** status at that checkpoint. The September
18 correction and later status at 2562–2570 are separate. The priority index
links to the CV-06 heading; no replacement or net saving was verified.

### F178 — CV-16 watch failure detail repeated across cards

At local audit head `8489836c`, [CV-16](cluster_verification_backlog.md#cv-16-monitoring-dashboard)
lines 3186–3202 spends 17 physical lines recording the combined September 16
Viking watch failures. Selection is detailed in
[CV-U13](cluster_verification_backlog.md#cv-u13-watching-progress) lines 884–891;
monocolor logs in [CV-U14](cluster_verification_backlog.md#cv-u14-dashboard-logs)
lines 943–948; navigation and bounded-tail limits in
[CV-U16](cluster_verification_backlog.md#cv-u16-dashboard-scrolling) lines 1008–1018;
and the contradictory `36/36` screenshot in
[CV-U17](cluster_verification_backlog.md#cv-u17-completion-communication)
lines 1090–1101. CV-16 uniquely says these failures together returned the
integrated card to **Open** after hosted parity. A linked account might save
6–9 lines from this 17-line span, conditional on wrapping, while keeping the
combined operator failure and the screenshot's diagnostic, not scientific,
evidence ceiling. The September 18 correction at 3204–3214 stays separate;
the priority index links to the CV-16 heading. No replacement or net saving
was verified.

### F179 — CV-01 integrated journey account under review

At local audit head `ce4d22f8`, [CV-01](cluster_verification_backlog.md#cv-01-managed-golden-path-coverage)
lines 2259–2295 uses 37 physical lines for the selected 130-pair hosted
journey, resource policy, focused fixtures, and evidence limits. The
[test-tool guide](../../tests/tools/README.md) lines 11–30 owns current driver
mechanics and fixture resources; [CV-10](cluster_verification_backlog.md#cv-10-external-cancellation-and-recovery)
lines 2732–2746 and 2886–2912 owns the recovery rule. The integrated CV-01
account is still unique: it connects pre-Run inspection, controlled failure and
resume, the gated real native child, admitted request/Task/Run, public
inspect/watch/stop, positive closure, three Slurm Attempts, and separate
two-Attempt direct parity. It also distinguishes the selected profile and
tiny-fixture floor from production capacity, controlled rejection/local stop
from site evidence, and pending exact-commit hosted from Viking acceptance.
A shorter within-card account might be possible, but no lossless draft or net
line saving is established. The current **Verification pending** status and
each evidence ceiling remain; overlap with CV-10 or the test guide does not
justify deleting this integrated account.

### F180 — Analysis provider validator independence wording

At local audit head `619e60b7`, the [analysis owner guide](../../src/emrys/analyses/README.md)
lines 12–16 says EMRYS checks a provider's “independent validator”; lines
29–32 also name it. [Descriptor admission](../../src/emrys/analyses/__init__.py)
lines 317–359 and 420–454 requires a callable planner and valid declarations.
[Task planning](../../src/emrys/orchestration/run_coordinator/materialization.py)
lines 1137–1159 requires nonempty producer and validator argv tuples, while
the [runner](../../src/emrys/orchestration/run_coordinator/task.py) lines
2697–2709 and 2732–2769 executes them separately and checks their exits.
Neither admission nor planning establishes that provider-authored validation
is semantically independent of production. The [collaborator fixture](../../tests/orchestration/run_coordinator/test_materialization.py)
lines 861–920 supplies different commands but does not prove that guarantee
for arbitrary providers. “Independent” may describe that separate execution,
so this is a wording ambiguity, not a proven false claim. The trusted provider's
semantic obligation and EMRYS's structural checks have different scopes. No
product defect, exercised failure, or line saving is established.

### F181 — Removed publisher-test history in the runtime test guide

At local audit head `619e60b7`, the [runtime test guide](../../tests/evidence/runtime_availability/README.md)
line 14 ends a current test-scope paragraph with a retired publisher-test
sentence. This is the same sentence and placement question already recorded
as F36, so F181 is dismissed as a duplicate. Removing the sentence alone saves
no physical line: the live batch-dependency caveat still occupies line 14.
The real-Snakemake and local-versus-cluster limits at lines 7–14 must remain.

### F182 — Slurm scratch cleanup wording

At local audit head `c1969b84`, the [Runbook](../operations/RUNBOOK.md)
line 589 says batch scratch is removed when the wrapper exits. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 383–387 repeat this unqualified lifetime claim at `9aaec3ac`. The
[submission owner](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
lines 756–773 creates private scratch, checks/chmods it, then installs a Bash
`EXIT` trap; lines 783–798 forward TERM and exit after the child. The
[direct test](../../tests/orchestration/run_coordinator/test_slurm_submission.py)
lines 2027–2105 observes cleanup after normal wrapper completion. Failure
between creation and trap installation, SIGKILL, or node loss can bypass it,
so the unqualified lifetime claim exceeds the source and test guarantee.
Residue is possible, not observed; site epilog
cleanup was not checked. Keep the scratch path, `TMPDIR`, no-fallback rule,
and site-capacity/lifetime warning at Runbook lines 584–598. A wording
qualification is under review; no physical-line saving is established.

### F183 — Historical change scope in the coordinator contract

At local audit head `c1969b84`, the [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 224–225 says existing CLI flags, maintenance-log modes/events,
refusals, and exits remain unchanged. Blame attributes the sentence to
`d0f4a2ada`; the dated [CV-19 card](cluster_verification_backlog.md)
lines 3317–3325 already preserves that change-scope assertion and its
acceptance limits. The contract's current Doctor repair/verification behavior
at 217–223 and Slurm elapsed-time rule at 225 are distinct and must remain.
Trimming the historical sentence may save one physical line, conditional on
reflow and preservation of the CV record; no net saving is verified.

### F184 — Runtime probe mechanics in the coordinator contract

At local audit head `c1969b84`, [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 358–363 repeats bounded empty-workflow Snakemake startup, selected
interpreter, private scratch, and no-study-task behavior. The
[runtime owner](../../src/emrys/evidence/runtime_availability/README.md)
lines 30–38 owns those probe mechanics; [probe source](../../src/emrys/evidence/runtime_availability/_probes.py)
lines 156–201 uses an empty workflow and disposable temporary directory.
The coordinator's head diagnosis, compute qualification, execution-preflight
placement and head-success limit are unique here. A concise owner route might
save two to four physical lines from this six-line span, conditional on a
lossless draft and link check. No product defect or net saving is established.

### F185 — Canonical BAM producer LB and PL exactness overclaimed

At local audit head `f8c49f9e`, the [canonical BAM contract](../../src/emrys/stages/canonical_bam/CONTRACT.md)
lines 50–54 requires exact `ID`, `SM`, `LB` and `PL:ILLUMINA` fields. The
[worker](../../src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh)
lines 69–74 and 94–107 instead search for substrings in one `@RG` line.
An otherwise valid coordinate-sorted input with `ID:sample`, `SM:sample`,
`LB:sample-extra`, `PL:ILLUMINA-extra`, and positive `RG:sample` records
appears able to take the hard-link reuse path at line 125 and pass the final
worker check. The [grouped BAM check](../../src/emrys/libraries/alignments/bam.py)
lines 56–65 requires exact `ID`/`SM` fields but omits `LB`/`PL`, as the contract
acknowledges at lines 142–147. Unlike F173's Step 05 prefix case, this mismatch
is not caught by that grouped field check. This is source inference; no
malformed Run, ordinary STAR output, or product execution was observed.

### F186 — CV-U21 superseded STAR heuristic chronology

At local audit head `f8c49f9e`, [CV-U21](cluster_verification_backlog.md#cv-u21-technical-parameter-assistance)
lines 1341–1387 spends 47 physical lines on the initial first-record FASTQ
heuristic, its local checks, the contig-selector extension, and the September
17 reversal. The current repair and STAR-default account follows at
1389–1422. A shorter dated account might save roughly 10–15 lines if it
retains the later-record failure, source-derived selector names versus
biological choice, fresh publication admission, initial local-test limits,
and the Verification pending → Open → Verification pending chronology.
The sampled origin commits `b6d2b3d50`, `d249fc5e2`, `3dc98a301`,
`0f3e1725a`, and `482f795e0` resolve locally; this does not verify the
operator walkthrough. F119/F120 concern current default or replay wording,
not this within-card history. No lossless draft or net saving was verified.

### F187 — CV campaign post-checklist context under review

At local audit head `f8c49f9e`, the [campaign Delivery approach](cluster_verification_campaign.md#delivery-approach)
lines 135–150 follow the checklist overlap at 128–133 already recorded as F158.
This distinct 16-line span reiterates [CV-01](cluster_verification_backlog.md#cv-01-managed-golden-path-coverage)
acceptance and site-evidence limits. A shorter account might save four to six
physical lines, conditional on retaining the missing-memory-plus-UID,
reuse-plus-node, and native-publication-cancellation combinations; the E01/E06
unexplained-cause boundary; INIT-02/CV-U22 original-intent decisions; and
simulation, hosted and institutional evidence ceilings. This estimate does not
include F158's separate opening. F167 covers Remaining delivery scope; F179
covers CV-01's later hosted journey. No net saving is verified.

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

## Step 02 decision recheck for F124 at `35668cc8`

The [scientific-pipeline decision](../design/decisions/scientific-pipeline.md)
lines 45–49 calls Step 02 publication “validation-first and
rollback-protected.” That has a valid worker-local reading: the [worker](../../src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh)
lines 114–131 validates its staged BAM/BAI before the runner publishes them,
as the [owner contract](../../src/emrys/stages/canonical_bam/CONTRACT.md)
lines 10–12 and 74–80 states. The independent grouped validator follows
native publication for Step 02, while Steps 08/09 validate working files
first; [runner source](../../src/emrys/orchestration/run_coordinator/task.py)
lines 1742–1747 and 2732–2782 and the [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1117–1130 establish both orders. After native commit, validation failure
preserves native outputs and failed evidence rather than rolling them back.
The decision's unqualified phrase can be read as claiming a different grouped
validation order and rollback scope. Its heading currently has glossary BAI
and RG inbound links; F172 reviews those owner routes separately. This is a
source-reading ambiguity, not an observed runtime defect or verified saving;
no worker, validator, or diagram renderer ran.

## Completion-criteria recheck for F158 at `3de8366b`

The [CV charter](cluster_verification_campaign.md) lines 173–190 spends 18
physical lines on closure criteria. The already-linked [main checklist](backlog_matrix.md#cluster-verification-closure-checklist)
lines 125–152 owns the institutional journey, exact-revision CI/site evidence,
separate reviews, card dispositions, and transfer before retirement. The
charter's opening at 11–17 still assigns campaign completion criteria to this
document, and the [main matrix](backlog_matrix.md) line 171 routes closure
through it. A shorter charter-specific criterion must retain rejection by
explicit decision, unresolved failures as findings, agreement among the
matrix/backlog/guides/contracts, and the E01–E12 and exact-result evidence here
until authorized transfer. Retirement and evidence deletion stay separately
authorized. No tracked Markdown link targets the `Completion and handoff`
heading directly. A concise route to the checklist plus these distinct rules
could save roughly 8–11 lines in that 18-line span; this is conditional, not
a drafted or verified net saving. F158's earlier statement that the full span
was distinct is narrowed accordingly.

## Stage and schema source recheck at `286f646a`

Step 00a–02 and Step 07–10 owner guides were compared with selected producers,
validators, planners, and direct tests without another distinct finding. A
standard-library structural scan found 20 packaged JSON schemas with unique
IDs and 388 internal or registered references resolving to an ID and pointer.
Artifact and orchestration registries were read against that inventory. This
checks the static reference graph, not runtime validation, historical schema
compatibility, scientific correctness, or a complete caller audit. No test,
product, CI, or cluster operation ran.

## Owner compression recheck at `3de8366b`

The 734-line Runbook, 271-line Troubleshooting guide, and full 1,248-line
coordinator contract were reread for novel duplication and developer history.
Their plausible reduction spans are already recorded under F05/F21–F23/F53,
F92/F100–F102/F128/F136–F137/F144/F146/F154–F156/F169 or retain distinct
operator recovery and admission rules. No further safe net saving was found on
this pass. Selected runtime-owner claims were crosschecked with the installed
policy: 12 choices, 26 unique fixed checks, and 30/120-second probe limits
match source constants. This is static comparison, not runtime, CI, site, or
scientific proof.

## Prose and owner-route recheck at `35668cc8`

A five-word overlap scan across non-audit Markdown found mainly the already
recorded stage-test boilerplate (F28), local resource/tool details (F128), and
owner-specific validation and recovery language. The scan can miss paraphrases
and does not prove any safe deletion. All 19 architecture, design and reference
files were reread; F124/F172 gained the only distinct audit refinements.
Non-stage test, script, and CI guides were
compared with selected direct assertions and workflow wiring without a new
strong finding. Fifteen evidence, ingestion and reporting owner READMEs were
compared with adjacent source; their relative links resolved, and apparent
overlaps were already recorded or carried distinct owner details. A broad
runtime-owner link to the Runbook was retained on review because Project
readiness spans several operator sections. No test, CI, site, or scientific
validation ran.

## Current-head reconciliation at `8489836c`

The non-audit diff from original scope revision `3a672fdf` to this head changes
only the Runbook and the DOCS-01 row in the main backlog. The approved Runbook
slice replaces 75 physical lines with 35, a net reduction of 40; F05/F21/F23/
F48/F70/F83 were rechecked against that text. F48's absolute-path citation was
narrowed to current lines 293–294; the other five retain their recorded limits.

A standard-library, read-only scan of all 177 tracked Markdown files found
2,050 inline link matches, 72 reference definitions and 621 fragments, with
no unresolved local destinations or headings under the repository's slug rule.
This scan does not parse or render CommonMark and does not replace the official
documentation check. No product, test, CI, or cluster command ran.

## Adversarial guide and owner recheck at `ce4d22f8`

Root, Quickstart, Runbook, Troubleshooting, Workflow and config routes were
compared again with selected CLI, onboarding, Doctor and runtime source; their
material overlaps remain F04/F05/F07/F70/F83/F126/F152/F154/F155. The full
1,248-line coordinator contract and selected owner guides were reread against
adjacent source and the existing reduction findings; no new safe contract
deletion emerged. Selected test, script and CI guides were compared with direct
assertions and workflow wiring; F20/F32/F56/F69/F107/F162 cover the apparent
scope or history overlaps. The platform decision's ratified public model and
the current architecture map serve different authority and reader roles;
the reporting migration record remains bounded by F25. F179 is the only new
candidate from this pass. These are read-only comparisons, not executed tests,
CI, institutional evidence review, or proof of an actual line saving. A later
regex link scan found zero unresolved local targets among 2,054 inline matches,
72 reference definitions and 624 fragments in 177 Markdown files; it is not
the parser-backed documentation gate.

## Task and history origin screen at `619e60b7`

Across the eight baseline task/history Markdown files, a read-only scan found
55 distinct commit-like hexadecimal tokens of 8–40 characters with a letter;
numeric run/job IDs and full-length digests were excluded. Fifty-two resolve
to local commit objects. The three unavailable objects are the two hosted
test merges cited by [CV-10](cluster_verification_backlog.md#cv-10-external-cancellation-and-recovery)
at lines 2859 and 2928 and the hosted checkout cited by
[CV-26](cluster_verification_backlog.md#cv-26-repeated-doctor-input-reads) at
3910. Their six named PR-head/base commits resolve locally. Object presence
does not verify the associated hosted run, artifact, test result, or scientific
claim; unavailable hosted objects do not make the citations false. Dense link
definitions at the ends of the polish and optimization campaigns point to
pinned source evidence, not disposable prose chronology. No network fetch,
artifact download, CI, or cluster execution occurred.

## Selected claim-to-source coverage at `619e60b7`

The runtime owner guide's 12 choices, 26 fixed checks, and isolated Snakemake
startup match policy constants and direct test setup. The source topology's
25 CLI seams and 22 import exceptions match the checker policy lists; the
current import graph was not executed. The hosted workflow and documentation
checker guides matched selected workflow, script, and direct-test assertions.
F180 was the only new documentation observation from these bounded checks;
F181 repeats F36 and is dismissed. This does not verify every owner, fixture,
or retained evidence claim.
A standard-library link scan of all 177 tracked Markdown files found no
unresolved local targets among 2,064 inline matches, 72 reference definitions,
and 628 fragments; it does not replace the parser-backed documentation gate.

## Inventory reconciliation at `c0c2d6a9`

The 173 non-audit Markdown/Mermaid paths partition without gaps: nine root or
operations guides, 19 architecture/design/reference files, 62 `src/emrys/`
READMEs, 15 owner contracts, 53 test/script/CI guides, eight task/history
files, and seven remaining indexes or guides (`LICENSES/README.md`,
`Projects/README.md`, `configs/README.md`, `docs/README.md`, `src/README.md`,
`src/emrys/contracts/STAGE_MAP.md`, and
`src/emrys/contracts/SOURCE_TOPOLOGY.md`). The seven remaining files
were reread without a new substantial compression candidate. The baseline has
170 Markdown and three Mermaid; the present 170 non-audit Markdown total 15,794
physical lines, 40 fewer than baseline after the approved Runbook slice.
Static path coverage does not establish claim-by-claim or retained-evidence
verification; those checks remain selective.

## Current-head reader and owner rescreen at `c0c2d6a9`

The [root route](../../README.md) lines 67–69, [configuration entry](../../configs/README.md)
lines 3–5, and [Runbook handoff](../operations/RUNBOOK.md) line 164 send a
generic own-study reader to the fixed EV/PUM1 Quickstart. Its opening and
study setup (lines 1–5 and 77–124) make the named scope clear after arrival;
the Runbook's generic continuation at 288–296 still enters its named steps.
This extends F05's inbound-route evidence, without establishing observed
reader error or a separate finding. The same source pass sharpened F08's
non-regular `.env` case and F70's configuration-guide wording; neither CLI
path was executed.

All 26 owner READMEs without a direct path link in these notes (461 lines)
and 25 previously unlinked test READMEs plus four script/CI guides were
reread. Selected claims about reference provenance, stage tools, GTF skips,
mpileup/receipt behavior, scientific-context outputs, workflow selection,
and direct-test boundaries matched adjacent source or assertions. The
repeated stage-test/execution material is already F28; other apparent overlap
retains owner-specific commands, contracts, or evidence limits. No new
substantial DOCS-01 candidate emerged from this bounded pass. Source and
tests were read, not executed; retained evidence was not validated.

## Contract and architecture rescreen at `f8c49f9e`

All 14 non-coordinator contracts (1,817 lines) were reread against selected
workers, validators and direct test source; F185 was the distinct new claim.
Architecture decisions and three Mermaid diagrams were rescreened. The
[stage map](../../src/emrys/contracts/STAGE_MAP.md) processing edges matched
the profile descriptor's 12 direct edges; its analysis tail is projected by
the analysis registry. F66 still covers the Step 08/09 QC-summary mismatch.
These are static comparisons, not executed behavior or rendered diagrams.
