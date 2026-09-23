# DOCS-01 discovery notes, seventh file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F188–F189 and an F182 recheck at local audit head `9aaec3ac`, plus an
F76 recheck and coverage screens at `16a98be5`, read on 2026-09-23. Review
spans and proposed line savings are conditional;
no guide, product source, test, or retained evidence was changed, and no
product, CI, or cluster command ran.

### F188 — Retired storage publisher history in polish item 2

The [polish campaign](polish-campaign.md#2-make-storage-inventory-replacement-recoverable)
lines 251–263 spends 13 physical lines on the retired capacity-and-retention
publisher, its unresolved backup/restoration/cleanup hazards, and PR
chronology. The current [storage owner](../../src/emrys/evidence/storage_inventory/README.md)
places capacity planning and retention policy outside EMRYS; its source tree
retains qualification, not that publisher. The campaign's overlap table at
line 1008 already records PR #128/#134, while Git retains routine PR order.
Retirement commit `c751bb5f` removed the command, code, examples and tests;
its CS-27 record preserved qualification and retained evidence. A private
nine-line accounting sketch suggests four local lines could be saved if it
retains the partial-predecessor, lock-release and obscured-original-error
risks; the fact that PR #115/#128/#134 did not repair them; the PR #158/CS-27
retirement merged through PR #169; and surviving storage qualification,
reports and recovery files. Retirement closes the repair proposal without
proving repair. No guide edit or net saving was verified. F88 concerns
another polish item; F90 concerns other completed tooling sections.

### F189 — CV campaign Related work repeats current owner map

**Dismissed after recheck at `88827e73`.** The [CV campaign](cluster_verification_campaign.md#related-work)
lines 192–210 maps five distinct relationships. The [main matrix](backlog_matrix.md#platform-operation-and-portability)
and [delegated CV backlog](cluster_verification_backlog.md#verified-scope-and-remaining-evidence)
retain selected status detail, but do not replace this campaign relationship
map. The watch acceptance, pending site verification, CV-26 attribution and
no-speedup limit, and evidence-deletion boundary are all meaningful here.
The earlier 19-to-16-line sketch suggested only three local lines and no useful
standalone saving once those limits and all five relationships remain. F158,
F187, F165, and F167 address separate campaign sections. No guide edit or net
saving was verified.

## Focused rescreens at `9aaec3ac`

The full 734-line Runbook and 271-line Troubleshooting guide were reread with
root/Quickstart routes and selected operator owners. Their apparent command,
recovery and prose overlaps are already recorded in F02/F05–F09/F23/F31/
F52/F53/F70/F72/F83/F89/F92/F104/F119/F123/F126/F132/F144/F154/F155/
F170/F182; report transfer and trusted-workspace warnings serve distinct
operator needs. Reporting, reference, runtime, logging, Step 09/10, BAM QC
and RSeQC owners were compared with selected source and direct-test text;
apparent mismatches were existing findings or owner-specific boundaries.
These were static reads, not executed commands, hosted or site evidence.

All 1,248 lines of the coordinator contract, including its 632-line no-write
and publication section, were reread against selected owners, source and
tests. Existing findings cover the apparent overlap and private detail;
F182 now also names its scratch-cleanup claim at lines 383–387. No separate
safe reduction was established by this recheck.

## Cross-repository duplicate and claim screen at `16a98be5`

Across 170 non-audit Markdown files, a paragraph screen found 2,739 text
blocks; 1,341 non-table blocks of 30–250 words entered a word-weighted,
cross-file similarity comparison. I inspected pairs scoring about 0.28 or
higher, plus repeated non-table lines of at least 70 characters. The strongest
overlaps involved config and Runbook batch setup, coordinator and
Troubleshooting recovery, coordinator and decision reporting, resource policy
and its dated history, and submission and logging identity. Existing findings
or distinct reader roles account for them. This screen cannot rule out every
paraphrase or establish a safe line saving.

A simple scan of inline and reference-style Markdown path links, excluding
temporary audit notes as sources, found 41 non-audit files without an inbound
link. All are directory `README.md` files, not demonstrated orphans. The
[task index](README.md) is explicitly required by the documentation checker.
The license and scientific-context resource indexes retain distinct local
obligations. The scan does not account for directory browsing or external
bookmarks and establishes no deletion or line saving.

All 53 test, script and CI Markdown guides (692 physical lines) were reread
against selected assertions, driver behavior and workflow wiring. Selected
strong guarantees about Init FASTQ reads, STAR members, Step 06/07 validation,
reporting, and Slurm scratch were traced to source. Apparent gaps were already
F182/F185 or expressly limited by source; no new high-confidence finding
emerged. These were static comparisons, not executed checks or hosted evidence.

## F76 historical-sentence recheck at `16a98be5`

The [Step 07 test guide](../../tests/stages/partitioned_cohort_mpileup/README.md)
lines 10–11 also narrates retired shell-suite fixed primary/pilot counts,
introduced at `76acb9c5f`. The current [producer test](../../tests/stages/partitioned_cohort_mpileup/test_partitioned_cohort_mpileup_producer.py)
lines 239–293 checks fixture arguments and the final-path receipt; the
[stage contract](../../src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md)
does not make those old counts a production requirement. The guide's line 12
fixture-VCF scientific ceiling remains useful. Whether the retired-count
sentence has any distinct current reader value or physical-line saving is
unverified; Git retains its provenance. This remains part of F76's guide
review, not a separate behavior or scientific finding.

## Adversarial matrix recheck at `6e58835d`

F01–F189 and their detail notes were reread in three partitions against
selected cited guides, source, tests and workflow paths. F86 is dismissed:
the Step 02b contract's direct operation and the ordinary Run graph make
different, accurate scheduling statements. F187 and F189 now preserve the
CV campaign's combined institutional scenarios and its distinct optimization
and polish relationships; their prior line-saving estimates were withdrawn.
No other material correction emerged from this selected source recheck.
It did not execute tests or validate hosted, institutional or scientific evidence.

A separate static link scan at that head covered all 178 tracked Markdown files,
including these audit notes: 2,172 inline/image/reference link candidates and
1,987 repository-local targets. It found no missing local file, heading anchor
or repository-boundary violation. Regex extraction can miss unusual CommonMark
syntax and did not check external URLs; `markdown_it` is unavailable here, so
this does not pass the repository's parser-based documentation gate.

### F190 — Source-topology reporting-internal import boundary

At local audit head `bc6f971f`, the apparent conflict was that
[SOURCE_TOPOLOGY](../../src/emrys/contracts/SOURCE_TOPOLOGY.md#ratified-exact-import-exceptions)
lines 133–135 forbids functional-owner imports of reporting internals while
its table permits seven exact `run_coordinator/reporting_operation.py` imports.
Adversarial recheck at `7d0fceb1` dismissed that reading: the guide's
dependency table at lines 64–79 separates `stages/`, `analyses/`, and
`evidence/` from `orchestration/`; the [source checker](../../tests/tools/source_dependencies.py)
at lines 427–440 uses `functional` only for the first three and classifies Run
coordination as `orchestration`. Its seven imports are the listed exceptions
`SRC-TRANS-016`–`018` and `021`–`024`. The
[architecture owner table](../architecture/ARCHITECTURE.md#responsibility-boundaries)
groups responsibilities but does not redefine the import checker's taxonomy.
No unauthorized import, useful compression, or necessary wording correction
is established. This was a static read; the checker was not run.

## Owner and operator source rescreen at `bc6f971f`

Root README, Quickstart, Runbook, Troubleshooting, all 1,248 coordinator-contract
lines, and 51 non-stage owner Markdown files were reread against selected CLI,
coordinator, reporting, evidence, analysis, schema, and direct-test source.
F190 was the only apparent new finding and was later dismissed. The repeated contract test
ceiling and reporting-consumer sentences are already F28 and dismissed F145;
their local links and owner-specific limits prevent an unverified saving claim.
No product commands, tests, CI, cluster operation, or hosted evidence were run in this
static rescreen; remaining claim-to-source and evidence checks are selective.

### F191 — Console detail tiers in the execution decision

At local audit head `f3dc7749`, the [execution decision](../design/decisions/execution-evidence-and-reporting.md#console-logs-and-status)
lines 265–268 says verbose and debug progressively expose console detail.
The [logging contract](../design/LOGGING_CONTRACT.md#sinks-controls-and-streams)
lines 36–38 and 51–55 makes `--verbose` the sole public detail switch and has
only normal and verbose console rows. [Argument registration](../../src/emrys/libraries/application_logging/controls.py)
lines 58–64 adds only `--verbose`; [projection](../../src/emrys/libraries/application_logging/handler.py)
lines 544–549 shows both `verbose` and `debug` event classes when it is on.
The [direct test](../../tests/libraries/application_logging/test_handler.py)
lines 215–259 expects those two classes together. “Debug” is an internal event
class, not a separate progressively broader public view. The decision can
mislead a reader about available controls; the durable JSONL log and the
promise that projection does not change behavior or exits remain intact.
This is a static source/test comparison, not an executed CLI result.

## Architecture, test, and task-record rescreen at `f3dc7749`

All 16 architecture/design Markdown and Mermaid files and 53 test/script/CI
guides were reread against selected current source, workflow configuration,
direct tests and owners. Six principal task/evidence records were screened by
heading and status; relevant sections were compared with current owner records
and selected local Git history. F191 and the F10 expansion were the distinct
changes. Existing findings cover the remaining apparent diagram, test-lane,
owner-status and campaign-history issues. Polish item 30's earlier Quickstart
account is explicitly dated context, not a current guide claim. Tests, CI,
institutional work and scientific review were not run or promoted by these
static reads.

## Hosted provenance and stage-contract rescreen at `2722ae30`

Read-only GitHub commit data confirmed the parent order for [CV-10 merge
`f28a829c`](https://github.com/lab-cats/EMRYS/commit/f28a829ca894674f4e17d9e6f4bf618b7296ea1e),
[CV-10 merge `3aa865b1`](https://github.com/lab-cats/EMRYS/commit/3aa865b1c42d710f40b2a698045db2eed9438bcf),
and [CV-26 merge `20897a7c`](https://github.com/lab-cats/EMRYS/commit/20897a7cb8e4b2549e4a456142af2c971744bcb7).
Associated [run 34993805649](https://github.com/lab-cats/EMRYS/actions/runs/34993805649)
and [run 34944690812](https://github.com/lab-cats/EMRYS/actions/runs/34944690812)
succeeded. [Run 35000308100](https://github.com/lab-cats/EMRYS/actions/runs/35000308100)
failed overall while its managed golden job passed, a distinction the CV-10
card already makes. Run metadata names the PR head rather than a merge SHA;
commit parentage plus run/job status does not prove actual worker checkout,
case counts, timing, or artifact bytes and hashes. No artifact was downloaded.

All ten stage contracts, adjacent guides, current validators and selected
workers/tests were compared read-only. All 52 documented check IDs match
source; existing F173/F185 producer exactness limits remain. The STAR-index
guide's reference/settings summary accurately describes its path, contig and
settings checks; it does not claim byte-for-byte index derivation, so no new
finding was added. A separate challenge of 14 larger or uncertain line-saving
estimates found no material overstatement. They remain conditional on the
content-preservation limits in their existing notes. No product command, test,
CI, cluster operation, or dependency install ran.

## Artifact metadata, link gate, and F76 recheck at `13a6a7aa`

Read-only GitHub metadata for [artifact 10407865575](https://api.github.com/repos/lab-cats/EMRYS/actions/artifacts/10407865575),
[10410455801](https://api.github.com/repos/lab-cats/EMRYS/actions/artifacts/10410455801),
and [10387257383](https://api.github.com/repos/lab-cats/EMRYS/actions/artifacts/10387257383)
matches the cited run associations, names and SHA-256 digests. The last record
also matches the documented 6,825,885-byte size. All three were marked
unexpired on 2026-09-23, with September 29 expiry dates. Service metadata is
not a local digest of downloaded bytes; no archive, case result, or historical
download claim was verified. The earlier worker-checkout limit also remains.

The repository's own documentation checker passed on 178 tracked Markdown
files and three Mermaid sources using an existing Python interpreter with
`markdown_it`; no environment was created or installed. It checks canonical
ownership, local links/anchors and Mermaid declarations, not external URLs,
factual accuracy or visual rendering. Bytecode writes were disabled.

F76's “dataset promotion” was traced to the retired Step 07 operational gate
for the EV/PUM1 primary set, not biological promotion of VCF candidates.
Historical README and shell-test text at `3199ea86^` names an approved paired
manifest and 25 receipts/50 VCFs; current Step 08 only requires every declared
partition. The test guide's current contract route still lacks the promised
study-wide criterion, while its fixture-VCF caveat remains correct.

## Retained hosted archive inspection at `496846d5`

Four cited GitHub Actions artifacts were downloaded to temporary storage on
2026-09-23 and inspected read-only. Each ZIP passed an integrity check; its
locally computed byte size and SHA-256 matched the exact value in the cited CV
card. None was added to the repository.

| Archive | Selected contents compared with the CV card |
| --- | --- |
| [CV-10 10407865575](https://github.com/lab-cats/EMRYS/actions/runs/34993805649/artifacts/10407865575), 7,461,300 bytes | Native log records 32 passed, 93 deselected; real one/two-thread success BAM/BAI outputs and both cancellation records with signal 15 and empty output rosters are present. |
| [CV-10 10410455801](https://github.com/lab-cats/EMRYS/actions/runs/35000308100/artifacts/10410455801), 7,696,940 bytes | Native log records 47 passed, 96 deselected; the two real-sort cancellation records again contain empty output rosters. The later final artifact 10411245477 was not inspected. |
| [CV-26 10387257383](https://github.com/lab-cats/EMRYS/actions/runs/34944690812/artifacts/10387257383), 6,825,885 bytes | Donor/borrower measurement JSONs report zero exits and wall times of 168.319256/110.727837 seconds, matching the card; the checkout is a value reported by the files. |
| [CV-26 10407268954](https://github.com/lab-cats/EMRYS/actions/runs/34995028343/artifacts/10407268954), 9,209,702 bytes | Four per-trial records agree with the combined record: one/two/two/one workers, zero exits, 26 ordered passing observations and ten R checks each. Serial/two-worker wall means recompute to 57.445185/41.533529 seconds; sampled peak means to 1204.316406/1634.177734 MiB. Donor hash lists match across before, preview, comparison and after. |

These archive bytes support only the named hosted, instrumented observations.
Archive self-reported checkout values and run metadata do not independently
prove the worker checkout; sampled memory may miss peaks and count shared pages,
and zero block-backed read accounting does not prove absent physical I/O. These
records do not establish Viking cancellation, later recovery, scientific or
biological outcomes. The hosted artifacts have finite retention; future
availability and any operator-held copies remain unverified. No CI, product
test, cluster run, push, or dependency installation occurred in this pass.

## Coordinator and polish rescreen at `0985adca`

The full 1,248-line coordinator contract, 734-line Runbook, and 271-line
Troubleshooting guide were reread against existing DOCS-01 entries and selected
source. Apparent allocation-ceiling overlap at coordinator lines 721–727 and
761–764 would save about two local lines only by merging its general capacity
rule with later exact Slurm-variable behavior; the two locations serve that
reading sequence, so no useful standalone reduction is established. The
remaining apparent repeats already have findings or retain distinct admission,
recovery, and evidence boundaries. This was a static read, not execution.

[F13](docs-01-discoveries.md#f13-doctor-profile-proposal)'s 11-line polish
item 8 can be reviewed as a five-to-six-line dated owner route: CV-07 and the
coordinator contract now own default, named, and absolute profile selection,
binding, no-fallback errors, and no-write diagnosis. The original audit tense
and heading must remain; no draft, link check or net saving is verified.
[F114](docs-01-discoveries-fourth.md#f114-older-novice-route-in-site-parity-item)'s
17-line item 10 might become a seven-to-nine-line dated route to SITE-PARITY-01
and current Quickstart/Runbook guidance. Keep Doctor's storage checks, separate
cluster authority, exact-revision site limits, and open novice acceptance.
Eight to ten local lines are conditional, not a verified saving.

### F192 — Release acceptance repeated in polish item 30

The [polish campaign](polish-campaign.md#30-establish-a-reviewed-alpha-release-path)
lines 683–710 spends 28 physical lines on release outcome and acceptance already
summarized by [`RELEASE-01`](backlog_matrix.md#maintainability-and-release) at
line 71. Its three distinct alpha questions still need a home or concise
retention: whether the wheel promises full standalone, selected, or paired-
checkout operation with arbitrary-directory installed-command evidence;
whether the released lock or wider metadata dependency ranges are supported;
and how current-format/older-Run refusal preserves data without migration.
Lines 654–681 separately retain the dated no-release observation, PR #157/#169
packaging change, dependency-range evidence limit, and approved version policy.
Publication and new platform support still require separate authority. A
16–18-line owner route might save about 10–12 local lines from 683–710, but no
lossless replacement, link check, or net saving was verified.

### F193 — R dependency closure repeated in polish item 34

[Polish item 34](polish-campaign.md#34-cover-the-complete-admitted-r-dependency-closure)
lines 759–773 spends 15 physical lines restating the accepted
[`RUNTIME-CLOSURE-01`](backlog_matrix.md#reliability-and-qualification) scope at
line 163: derive and bind the recursive scientific R package closure, preserve
normal `renv` cache links, and disable automatic snapshots. Item 34 uniquely
records its omission from the first campaign pass, that Doctor's namespace-
tree hashes do not derive recursive roots, and that fewer R probes cannot
substitute for complete dependency identification. A seven-to-nine-line
owner route could save about six to eight local lines only with those facts
retained. No draft, source change, or net saving was verified.

### F194 — Rendered report review repeated in polish item 37

[Polish item 37](polish-campaign.md#37-verify-reports-in-browsers-copied-results-and-print)
lines 815–833 spends 19 physical lines on review scope also accepted by
[`REPORT-01`–`03`](backlog_matrix.md#reporting-and-results) and the
[shared report criteria](backlog_matrix.md#shared-report-acceptance). Its
structural-test ceiling and absence of an observed defect are distinct; the
review names keyboard access, zoom/reflow, links into closed sections,
screen-reader meaning, print completeness, copied-bundle links, supported
browsers, and evidence bound to an exact revision. Retain the no-third-renderer
and no-scientific-proof limits. A 12–14-line owner route might save five to
seven local lines only if those review cases and limits stay accessible.
No rendered review, guide edit, link check, or net saving occurred here.

## Owner and operator rescreen at `99fe2d5a`

The full 734-line Runbook and 271-line Troubleshooting guide, main matrix and
polish campaign were reread against existing findings. All ten stage READMEs
and contracts, the evidence contracts, paired-CMH/Step 10 contracts, and
selected reporting, runtime, storage, reference, ingestion, library, `renv`,
and workflow owners were compared with adjacent source. Existing entries cover
the apparent operator overlaps and owner-specific input, validation, recovery,
and evidence limits. The architecture, decision, reference, and root guides
received a targeted history and policy reread. No independent new finding was
established in those areas. No product source has changed since the initial
`3a672fdf` audit base; this was static review, not execution.

### Reporting history rescreen for F25

The [reporting decision](../design/decisions/execution-evidence-and-reporting.md#reporting-lifecycle-compression)
lines 216–225 inventories retired private operation records, the
`ReceiptValidationOps` testing interface, `report.py`, and later
`RunSummaryBuildDeps`. These are retired production interfaces; the
[source-dependency test](../../tests/test_source_dependencies.py) fabricates
the old `report.py` path as a forbidden-import case.
Git retains their chronology. The adjacent lines 210–214 preserve
PR #146's predecessor tree and replacement-failure limit; the later combined
summary retirement came with `9e8eafba`, not that predecessor revision.
Current source admission, logical producer identity, retained source observers
and input rechecks, and combined manifest/summary publication are covered by
the [reporting owner](../../src/emrys/reporting/README.md#implementation-and-fault-tests),
the [private report owner](../../src/emrys/reporting/_run_report/README.md),
the [artifact-index owner](../../src/emrys/reporting/_artifact_index/README.md),
the [summary owner](../../src/emrys/reporting/_run_summary/README.md), and the
[fault-test guide](../../tests/reporting/README.md#fault-injection).
A six-to-eight-line account of this ten-line subspan suggests two to four
conditional local lines; Markdown links or preservation wording may erase
that saving. No guide rewrite or net saving was verified. F25's full-section
reduction remains dismissed, and retained evidence deletion is not authorized.

## CV backlog and prose-overlap rescreen at `24b8853b`

All 4,107 lines of the delegated CV backlog and all 53 test, script, and CI
Markdown guides were reread against the current matrix and selected owners.
The test guides' repeated runner paragraph is F28; the long CV card overlaps
either have existing findings or retain distinct dated evidence and acceptance.
A rough cross-file scan of 1,278 longer prose paragraphs surfaced 71 similar
pairs: stage/evidence test boilerplate, owner-local validator contracts, and a
short decision/coordinator reporting overlap already reviewed. It omitted
lists and code and cannot rule out differently worded duplication. No product
test, CI, cluster operation, or product-guide edit occurred in this pass.

### F195 — CV-21 acceptance history repeats its current boundary

The [CV-21 card](cluster_verification_backlog.md#cv-21-reporting-in-progress-and-visibility)
lines 3529–3545 uses 17 physical lines to recount its September 17 return to
Open and September 21 move to Verification pending. Its current acceptance at
3473–3483 and the [campaign summary](cluster_verification_backlog.md#verified-scope-and-remaining-evidence)
at 70–79 already state that E06 remains unexplained, causal reconstruction is
not required, and ordinary institutional execution remains pending. The dated
reversal is still material: controlled overlap and finalization fixtures did
not identify E06's cause; the owner later removed cause-finding from acceptance.
Retain both dated status decisions, the truthful transaction states, verified
report-location gate, fail-closed committed-output admission, public producer
boundary and finalization-fault protections, and exact-revision institutional
proof still pending. A nine-to-eleven-line account might save six to eight
local lines, but no lossless replacement or net saving is verified.
This is separate from F118's normal-versus-verbose table claim and grants no
authority to delete dated evidence.

The local documentation structure check passed on this audit draft (178
Markdown files, three Mermaid sources). It validates these links, not any
hypothetical shortened CV-21 prose or product behavior.
