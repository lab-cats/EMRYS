# Project handoff

This is the canonical current takeover snapshot. The roadmap and acceptance
criteria live in [`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md);
commands live in [`RUNBOOK.md`](RUNBOOK.md).

## Checkout

- Branch:
  `codex/refactor-01z-test-sufficiency-gate`
- Parent:
  `codex/refactor-01f-independent-goldens`
- Verified parent HEAD:
  `d02717b9e577a53edf53c147924e2aca467d9ed7`
- Parent documentation commit:
  `d02717b docs: complete TEST-01F characterization`
- Current implementation commit:
  `44d3255 test: make Make oracle identity-portable`, following
  `0c64d1a test: close Phase 01 public contract gaps`
- Current documentation commit:
  `docs: record portable Phase 01 correction` (the branch commit
  containing this handoff; resolve its exact SHA from Git)
- Recorded package state: the exact `TEST-01C`, `TEST-01D`, `TEST-01E`,
  `TEST-01F`, and `TEST-01Z` local-only tranche is implemented; TEST-01Z is
  affirmative with 88/88 rows closed, and the bounded Phase `0` correction
  closes two later adversarial-review gaps
- Current package: literal Make-expansion and real-R argument-path contract
  correction plus reconciled Phase `01` evidence
- Package type: one test-only correction commit and one separate docpatch
- Remote and cluster work: paused; this branch is intentionally unpushed

This branch descends linearly from the clean, committed local `TEST-01F`
predecessor under the explicitly approved local-only tranche exception.
Publication and upstream equality remain deferred until the corrected exact tip
passes the additional Phase `0` adversarial review. The package changes tests,
literal test fixtures, and documentation only; it does not change any
production job, CLI, workflow, Makefile, schema, dependency, resource, runtime,
cluster, scientific, or biological behavior.

## Active concurrent lanes

This checkout is the sole local lane for the five-card characterization
tranche. All paused concurrency attempts and the researcher pilot remain
uninspected, unmodified, and unintegrated.
The user explicitly authorized that pilot before the fragment checkpoint was
defined; preserve that historical fact without claiming retroactive protocol
compliance.

| Lane ID | Role and owner | Worktree and branch/detached state | Base and target | Reservations and coupling | Validation or execution identity |
| --- | --- | --- | --- | --- | --- |
| `researcher-path-cards` | Frozen documentation/card sidecar; user-directed pre-checkpoint pilot | `/Users/elisteiger/dev/norad-worktrees/researcher-path-cards`; `codex/researcher-path-cards`; clean at inspection | Base `32ee4e8f2527bc0b34e69752ab96d69391e3e74c`; future integration target must be selected after protocol/infrastructure review | Exact paths listed below; substantive coupling intentionally unreviewed | Candidate `9f1dcf170549eb7960b8fa76b06040188ab0f8be`; no integration or acceptance validation |

The pilot reserves only these candidate paths:

- `docs/CORE_DOC_CHANGES.md`;
- `docs/tasks/TODO/CLI-03A-implement-local-pilot-control-plane.md`;
- `docs/tasks/TODO/E2E-03A-prove-fresh-clone-local-pilot.md`;
- `docs/tasks/TODO/INTAKE-03A-implement-yaml-tsv-run-lifecycle.md`;
- `docs/tasks/TODO/ONBOARD-03A-publish-researcher-onboarding.md`;
- `docs/tasks/TODO/PROFILE-03A-materialize-local-pilot-workflow-profile.md`;
- `docs/tasks/TODO/SETUP-03A-implement-local-pilot-dependency-profile-and-doctor.md`;
- `docs/tasks/UNREFINED/FUT-SITE-01-csu-slurm-execution-profile.md`;
- `docs/tasks/UNREFINED/FUT-SITE-02-portable-site-and-container-profiles.md`;
- `docs/tasks/UNREFINED/README.md`.

These paths were inspected only as names. Do not inspect or integrate their
content as part of this card-bootstrap package. A later integration package
must reconcile the pilot against the then-current protocol, lifecycle,
canonical owners, and combined validation requirements.

The detached worktree at `/Users/elisteiger/dev/norad-demo-report` on
`f9aef17f4d6a2aa6e88feb41f85c1364af194889` predates this policy. It is
preserved unmanaged state, not an active lane; do not reuse, move, or remove it
without separate inspection and operator direction. Future active rows must
contain or link the complete lane packet required by
[`CONCURRENT_WORK.md`](CONCURRENT_WORK.md#required-lane-packet).

## Completed boundary

The local descendant sequence has implemented:

- Steps `00a` through `09`;
- Step `09c` scientific-evidence validation;
- versioned artifact/scientific-review/run-summary/report-receipt schemas;
- explicit read-only artifact indexing;
- canonical run-summary assembly and report-table approvals;
- atomic, receipt-last HTML/PDF/summary-TSV reporting;
- `make demo-report`, which builds a complete synthetic 81-artifact,
  15-scope run with all 11 supported approved science-table roles, runs
  report dry-run before execute, and publishes beneath ignored
  `results/demo-report/`;
- a bounded, script-free HTML view with an initially open science-first
  Overview, broad native categories, and local scrolling for wide tables,
  plus a linear PDF with compact readable candidate records;
- explicit-profile, read-only runtime availability preflight;
- explicit read-only reference artifact, provenance, hash, and contig reconciliation;
- explicit read-only storage-root measurement and retention-policy recording;
- a Step `00a` STAR-index validation report, typed artifact adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `00b` BED12/GTF validation report, typed artifact adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `00c` FASTA/FAI/DICT validation report, typed artifact adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `01` STAR-output validation report, typed artifact adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `02` canonical-BAM validation report, typed artifact adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `02b` persisted BAM-QC validation report, typed artifact adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `03` RSeQC-fraction validation report, typed artifact adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `04` marked-BAM/Picard-metrics validation report, typed artifact
  adapter, and
  summary/HTML/PDF propagation fixture;
- a Step `05` split-N-cigar/reference-prerequisite validation report, typed
  artifact adapter, and
  summary/HTML/PDF propagation fixture.
- a Step `06` mechanical-orientation output/count validation report, typed
  artifact adapter, and summary/HTML/PDF propagation fixture.
- a Step `07` VCF/receipt/selector/manifest/count validation report, typed
  artifact adapter, and summary/HTML/PDF propagation fixture.
- a Step `08` three-TSV transaction/identity/schema/count validation report,
  typed artifact adapter, and summary/HTML/PDF propagation fixture.
- a Step `09` seven-check transaction/identity/semantics/subset/summary/
  spectrum/PDF validation report, typed artifact adapter, and summary/HTML/PDF
  propagation fixture.
- a pinned developer-only Python line/branch baseline, deterministic
  non-regression check, subprocess tracing, self-tests, and exhaustive
  public-contract risk-to-test matrix.
- a test-only Step `09` oracle that independently derives count-table
  estimability, the two-sided continuity-corrected stratified CMH statistic,
  p-value, common odds ratio, and one global BH family from paired DP/AD
  counts, with valid, zero-cell, all-zero, missing, low-coverage,
  infinite-odds, rounding, multi-stratum, and coordinated-corruption cases.
- a de-duplicated complete developer-validation gate with four independent
  lanes, quiet failure-first logs, explicit verbose and serial modes, bounded
  process-group cleanup, timing/result summaries, and exact coverage
  comparison.
- a test-only publication-fault matrix covering the one publisher shared by
  all 13 step validators plus the distinct provenance, preflight, and storage
  transactions, with protected success/rollback behavior and current unsafe
  recovery states clearly distinguished in test names and comments.
- a file-backed task registry with 55 cards in the current working tree,
  bounded acceptance evidence, and an explicit planning-before-implementation
  lifecycle; the legacy reciprocal dependency model remains unchanged pending
  the separately planned `TASK-REG-01` migration;
- durable architecture decisions and target constraints for behavior-first
  migration, vertical source/test ownership, semantic stages, YAML+TSV intake,
  report profiles, two-sink logging, documentation/local context, future
  analysis/public-data/package seams, the documentation-health skill,
  isolated concurrent authoring, and rolling-wave delivery;
- a version-aware task-start router with exact-revision context reuse,
  selective phase-boundary inspection, explicit expansion triggers, impact-
  directed manual documentation review, and a quiet repository-wide structural
  gate;
- an isolated concurrent-work policy with one canonical integrator, multiple
  disjoint documentation/card sidecars, at most one implementation-candidate
  or locked detached execution lane, durable lane packets, serialized frozen-
  proposal integration, combined validation, and recoverable preservation;
- four unselected follow-up cards that preserve the agreed manual integration-
  fragment protocol, later structural enforcement, nonselectable `UNREFINED`
  intake, frozen `INTEGRATION_REVIEW`, and orthogonal logical epic-index
  boundaries without implementing them;
- explicit standalone documentation-package semantics: computational
  validation is not applicable when the complete diff has no executable or
  test-affecting consumer;
- an open-choice ledger and updated future Mermaid sources. Current executable
  topology, report behavior, logging behavior, numeric stage identifiers, and
  runtime/scientific evidence remain unchanged.

## Evidence boundary

| Step/package | Verified state |
| --- | --- |
| `00a` STAR index | cluster-proven |
| `00b` GTF to BED12 | cluster-proven |
| `00c` reference sidecars | cluster-proven |
| `01` STAR alignment | cluster-proven across all six samples |
| `02` canonical BAM | cluster-proven across all six samples |
| `02b` BAM QC | refreshed across all six final Step `02` BAMs |
| `03` RSeQC orientation inference | cluster-proven across all six samples |
| `04` MarkDuplicates | cluster-proven across all six samples |
| `05` SplitNCigarReads | cluster-proven across all six samples |
| `06` mechanical orientation split | cluster-proven across all six samples |
| `07` cohort mpileup | implemented and mocked-bcftools tested locally; no real-runtime or cluster proof |
| `08` VCF preprocessing | implemented; shell/fake-R and guarded real-R tested locally; no cluster proof |
| `09` paired CMH ranking | implemented; shell/fake-R and guarded real-R tested locally; no cluster proof |
| `09c` scientific-evidence tooling | implemented and synthetic-fixture tested; no production review |
| Artifact schemas/adapters/run summary | implemented and synthetic-fixture tested; no production transaction |
| Static report bundle | HTML/PDF/summary TSV/report receipt implemented and tested with the pinned local Quarto/Typst renderer and PDF reader; no production report |
| Populated demo report | full synthetic report transaction, native broad HTML categories, bounded wide-table layout, and compact PDF candidate projection implemented and locally tested; no production data or evidence |
| Runtime preflight | explicit tool, R-namespace, SHA-256, and path-visibility probes implemented and locally fixture-tested; no CSU batch report |
| Reference provenance | explicit FASTA/FAI/DICT/GTF/BED12/STAR inventory and reconciliation implemented and locally fixture-tested; no production reference report |
| Storage inventory and retention | explicit root size/capacity measurement and retention-policy recording implemented and locally fixture-tested; no production storage report or approved production policy |
| Step `00a` structured validation | index members, source identities, ordered contig names/lengths, and `sjdbOverhang` validator implemented and locally fixture/report tested; no new production execution |
| Step `00b` structured validation | BED12 structure, sorting, blocks, uniqueness, and exact GTF normalization agreement implemented and locally fixture/report tested; no new production execution |
| Step `00c` structured validation | FASTA, FAI, and DICT structure plus exact ordered contig-name/length agreement implemented and locally fixture/report tested; no new production execution |
| Step `01` structured validation | five explicit STAR outputs, BAM container signature, final-log structure, mapping percentages, and splice-junction rows implemented and locally fixture/report tested; no new production execution |
| Step `02` structured validation | BAM/BAI containers, samtools quickcheck, coordinate sorting, matching read-group header, and alignment RG coverage implemented and locally fixture/report tested; no new production execution |
| Step `02b` structured validation | exact quickcheck marker, flagstat structure, total/mapped counts, and count reconciliation implemented and locally fixture/report tested; no new production execution |
| Step `03` structured validation | required RSeQC labels, finite paired-orientation fractions, failed-to-determine fraction, and sum reconciliation implemented and locally fixture/report tested; no new production execution |
| Step `04` structured validation | BAM/BAI containers, quickcheck, coordinate sorting, read-group preservation, and bounded Picard duplication metrics implemented and locally fixture/report tested; no new production execution |
| Step `05` structured validation | BAM/BAI containers, quickcheck, coordinate/read-group preservation, and exact FASTA/FAI/DICT agreement implemented and locally fixture/report tested; no new production execution |
| Step `06` structured validation | two BAM/BAI output pairs, exact counts-table structure, per-flag mechanical-orientation sums, assigned/unassigned totals, and assigned-fraction reconciliation implemented and locally fixture/report tested; no new production execution |
| Step `07` structured validation | exact two-row receipt, VCF structure, selector/FAI reconciliation, manifest hashes and sample order, and VCF paths/counts implemented and locally fixture/report tested; no real-bcftools or cluster execution |
| Step `08` structured validation | sites/input-receipt/summary transaction, manifest and annotation identity, ordered partition-orientation inputs, candidate uniqueness/sample fields, and aggregate counts implemented and locally fixture/report tested; no production execution |
| Step `09` structured validation | six native outputs, exact headers/basenames/shared parent/distinct files, explicit cohort and provisional policy, complete Step `08` candidate order, count-derived target/test/call/depth/AF/background plus BH-from-reported-p semantics, subset, summary, mutation spectrum, and PDFs implemented and locally fixture/report tested; CMH statistic/p-value/odds ratio and count-table estimability are not independently recomputed; no production execution |
| Guarded local R dependency | `bitops` updated from locked `1.0-9` to `1.1-0` in the repository-local environment under a one-time explicit authorization; upstream consistency tests, exact boundary-output comparison, synchronization/current-release checks, and the complete local gate passed |
| Comprehensive refactor audit | evidence inventory, ranked findings, test-first recommendations, and explicit do-not-abstract boundaries recorded; no NORAD workflow, schema, config, test, scientific method, or public-contract behavior changed |
| Phase `01` test baseline | measured developer-only Python line/branch baseline and public-contract matrix recorded in [`../design/TEST_BASELINE.md`](../design/TEST_BASELINE.md); the implementation gate passed with 432 Python tests passing, 17 expected skips, every shell suite passing, guarded R environment/current-release validation, Step `08`/`09` local real-R fixtures, and 143 pinned report-runtime tests; no production behavior or evidence state changed |
| Phase `01a` independent Step `09` oracle | 20 focused Python oracle tests and the committed real-R Step `09` corpus comparison passed; the complete implementation gate passed with 452 Python tests, 17 expected conditional skips, unchanged 80.8701% line/69.6956% branch coverage across 26 production Python modules, every shell suite, guarded R environment checks, guarded Step `08`/`09` real-R fixtures, and 143 pinned report-runtime tests; the production validator and Step `09` method were unchanged |
| Phase `01a1` populated demo report | post-rebase report gate passed with 145 pinned real-Quarto/Typst tests, the isolated wrapper contract passed, repeat publication and cleanup passed, and `make demo-report` published the ignored 81-artifact/15-scope/11-table synthetic bundle; this is local synthetic-fixture and renderer-runtime evidence only |
| Phase `01aa` validation efficiency | implementation commit `dd19f0f` passed the final serial fallback in 440.821246 seconds and three consecutive default parallel gates in 152.335875, 169.928159, and 168.979423 seconds; every run reported 463 Python passes, 17 Python skips, 17 pinned report-runtime passes, all shell and guarded-R checks passing, and exact equality across 26 coverage files, 8,542/10,551 lines, 3,074/4,404 branches, and coverage digest `a6a5f1d9c5d33de3c1fbae82bd540342298f35089df55c3a76b17d08db1abd7f`; controlled exit-7 failure and SIGINT-130 tests proved retained failure output, propagation, descendant cleanup, handler restoration, and no stale owned logs; this is developer-validation infrastructure evidence only |
| Phase `01b` validation-publication faults | implementation commit `f7e00e4` added 28 test-only fault cases: 18 for the publisher shared by all 13 step validators and 10 for provenance, preflight, and storage publishers; 56 directly affected tests passed five serial repetitions and one two-worker run, covered serial/parallel execution was exactly equal, the broader 132-test regression passed, and the canonical complete gate passed in 153.161 seconds with all Python, shell, guarded-R, and 17 pinned report-runtime checks passing; a separately retained identical Python lane recorded 491 passes, 17 skips, and 26 coverage files at 8,566/10,551 lines and 3,103/4,404 branches; production behavior and evidence state were unchanged |
| Phase `01f` independent contract goldens | implementation `dcb5dd4` plus targeted correction `1986898` add a compact producer-independent fixture family and 22 focused tests for five public schemas, six ordered headers, canonical UTF-8 JSON/TSV and report-receipt bytes, status/evidence transitions, and shared science-policy projection; deliberate schema, header, status, serializer, decision-dimension, and computational-scope mutations fail; the final complete local gate passed every static, shell, checked Python coverage, guarded-R, and pinned report-runtime lane in 180.219 seconds; production behavior and evidence state were unchanged |
| Phase `01z` behavior sufficiency | 88/88 public-entry-point, cross-cutting, and fixture rows have explicit preserved-contract, characterized-defect, or environment-deferred dispositions with zero undefined rows; the checked Python refresh passed with 843 tests, 17 expected skips, 8,585/10,551 lines (81.3667%), and 3,111/4,404 branches (70.6403%); a later Phase `0` adversarial review found unprotected Make-expansion and R-argument claims, correction `0c64d1a` closed both, and follow-up `44d3255` closed the first final review's bare-Make portability blocker; the final focused and complete gates pass, while the affirmative result still releases only four named Phase `02` planning roots and changes no production or evidence state |
| Architecture-direction documentation | task registry, decisions, open choices, target architecture, roadmap, handoff, and four future diagrams updated; documentation-only validation passed; no executable, dependency, schema, config, fixture, test-harness, scientific-method, runtime, cluster, or evidence-state change |
| Task-start context documentation | task-start router, context-freshness matrix, expansion triggers, impact-directed documentation review, and documentation-only validation semantics updated; `git diff --check`, the 71-document/51-card/6-diagram structural gate, and independent read-only consistency review passed; computational validation was not applicable because no executable, dependency, schema, config, fixture, report-template, test-harness, scientific-method, runtime, cluster, or evidence-state surface changed |
| Concurrent documentation lanes | `CONCURRENT_WORK.md`, fail-closed Git 2.54 worktree/integration/recovery commands, write authority, card/status rules, immutable-execution attribution, and final-combined validation semantics completed; `git diff --check`, the 72-document/51-card/6-diagram structural gate, and independent policy/ownership and Git/recovery audits passed; no active delivery experiment ran and computational validation was not applicable because the complete diff is non-consuming Markdown only |
| Strategy follow-up card bootstrap | Four future cards plus reciprocal dependency and canonical roadmap/decision/question/handoff references recorded; no card selected and no pilot content reviewed or integrated; `git diff --check`, the 76-document/55-card/6-diagram structural gate, and independent dependency, ownership, and handoff/roadmap audits passed; computational validation is not applicable because the complete diff is non-consuming Markdown only, and publication state remains subject to live Git verification |

The measured parent serial workflow was approximately 554 seconds from its
successful component timings. Removing duplicate Python and report execution
reduced the final serial fallback to 440.821246 seconds. Python-worker medians
for one through four workers were 200, 110, 107, and 108 seconds; two workers
were selected as the smallest candidate within 5% of the fastest and improved
the Python lane by 45%. Top-level medians for one through four lane slots were
351.760131, 216.836257, 174.101133, and 170.702626 seconds; three slots were
selected as the smallest candidate within 5% of the fastest. The final
three-run default median was 168.979423 seconds, 61.667% faster than the final
serial fallback.

Phase `01b` preserved the Phase `01aa` defaults of three top-level lane slots
and two Python workers. Its successful gate lane timings were 0.110 seconds
for static preflight, 39.724 for shell contracts, 131.618 for Python coverage,
144.052 for guarded R, and 113.317 for pinned report runtime. A retained
Python-lane measurement finished in 107.22 seconds with coverage digest
`a59ee1897b4b8a0d02881c3c5070f12f47f0a6b1067cd883624db88ad8056137`.
The tracked non-regression baseline was not rewritten. An initial restricted-
network gate attempt reached guarded R and failed only because release
metadata DNS was unavailable; the identical gate passed when network access
was available.

The fault suite confirms protected first/replacement publication, validation,
rollback, symlink rejection, input mutation, fsync/move failure, and
interruption paths. It also freezes known unsafe states for later correction:
metadata-only snapshots miss same-size rewrites with restored mtime; a late
foreign final can be deleted; incomplete restoration can leave backups without
lock/marker protection; and runtime preflight has lock-fsync/descriptor and
lock-cleanup gaps. Passing these tests characterizes those states; it does not
approve them as safe recovery behavior.

Transaction completion means only that the declared transaction reconciled. It
does not establish that every source exists or passed, nor does it promote
runtime, cluster, scientific, or biological state.

No production artifact index, run summary, report-table approval manifest,
Step `09c` evidence package, or report bundle is recorded in this checkout.
The export evidence is local synthetic-fixture and real-renderer evidence
only.

No CSU runtime profile has been populated or executed in a batch allocation.
The tracked runtime profile is an example contract. Local tests and a
successfully published preflight report would establish only the checks
recorded in their declared context, not workflow runtime validation or
cluster proof.

No production storage-root contract or retention-policy approval has been
populated. The tracked contracts use illustrative paths and pending approvals.
The inventory tool is read-only; report publication does not authorize or
perform deletion, movement, archival, compression, or cleanup.

## Cohort and preserved scientific evidence

The paired-end cohort is:

```text
EV:   ABE_EV_2, ABE_EV_3, ABE_EV4
PUM1: ABE_PUM1_2, ABE_PUM1_3, ABE_PUM1_4
```

Explicit paired strata:

```text
replicate 2: ABE_EV_2 / ABE_PUM1_2
replicate 3: ABE_EV_3 / ABE_PUM1_3
replicate 4: ABE_EV4  / ABE_PUM1_4
```

`ABE_EV4` intentionally lacks an underscore. Pairing comes from explicit
manifest metadata, never from sample names.

Step `03` found all libraries reverse-stranded / first-strand-style:

| Sample | Failed to determine | `1++,1--,2+-,2-+` | `1+-,1-+,2++,2--` |
| --- | ---: | ---: | ---: |
| `ABE_EV_2` | 0.0828 | 0.0432 | 0.8740 |
| `ABE_EV_3` | 0.0964 | 0.0420 | 0.8617 |
| `ABE_EV4` | 0.0908 | 0.0433 | 0.8658 |
| `ABE_PUM1_2` | 0.1063 | 0.0374 | 0.8562 |
| `ABE_PUM1_3` | 0.0955 | 0.0407 | 0.8639 |
| `ABE_PUM1_4` | 0.0926 | 0.0402 | 0.8672 |

The post-hardening `ABE_EV_2` Step `03` rerun matched its earlier report.
`ABE_EV_2` remains a mapping outlier, not an established pipeline failure.

The `FWD_like` and `REV_like` groups are mechanical flag groupings.
`legacy_provisional_v1` is a compatibility policy, not a validated biological
strand model.

Step `09` outputs are CMH-ranked candidates. No validated editing-site or
causal biological conclusion exists.

`science_review_complete_exploratory` remains explicitly provisional.
`biological_interpretation_ready` is reserved and rejected until a separately
approved policy defines and unlocks stricter exit criteria.

## Current blockers

- The full production `samples.tsv` is not in this checkout. Its immutable
  cluster copy, explicit replicate values, persistence, and hash require
  inspection.
- Step `07` lacks real-bcftools and cluster evidence.
- CSU batch-visible R and package availability remain unresolved.
- Storage quota, scratch capacity, and retention policy remain unresolved.
- The exact Novogene annotation release remains partially unresolved.
- No production scientific-evidence review has been completed.
- The Step `09` structured validator still does not independently recompute
  the CMH statistic, p-value, common odds ratio, or table estimability from
  DP/AD counts. Phase `01a` now supplies independent characterization evidence
  for a later separately reviewed compatible correction; it did not change
  production validation.
- Exact check rosters, all public Python/shell/R/Make command surfaces, and all
  16 SLURM/utility jobs are characterized. Shared roster-consumer defects,
  public CLI exceptions, embedded/mode-less jobs, the Bash 3.2 empty-array
  dry-run defect, default dry-run side effects, and non-uniform submit-CWD,
  module, file-mode, and output-validation policies remain labeled behavior.
  Independent critical serialized/state/evidence goldens now complete
  `TG-06`; broader integrated fixtures deliberately remain producer-coupled.
- Phase `01b` now characterizes shared and ancillary publication faults, but
  it intentionally does not correct the confirmed same-size rewrite,
  late-foreign-final, incomplete-rollback, descriptor, or stale-lock behavior.

## Immediate resume point

`TEST-01Z` remains an affirmative local decision with all 88 source rows closed
and zero `undefined — decision required` outcomes. A later Phase `0`
adversarial review invalidated two protection claims that the first review had
not caught, so publication stopped for a bounded correction rather than
treating the earlier verdict as final. No closure card was created.

The TEST-01Z checked Python refresh passed with 843 tests and 17 expected
conditional skips, measuring 26 production modules at 8,585/10,551 lines
(81.3667%) and 3,111/4,404 branches (70.6403%). It did not rewrite the tracked
baseline. TEST-01F's unchanged final executable state already passed the full
static, shell, Python, guarded-R, and pinned report-runtime gate in 180.219
seconds, so TEST-01Z did not duplicate those computational lanes.

Correction `0c64d1a` adds a committed literal default-context dry-expansion
oracle for every public Make target, proves that a recipe mutation fails, and
executes both environment-management R utilities on their real `--help` and
arbitrary-argument rejection paths without invoking no-argument restore. The
first final review blocked on a reproducible bare-`make` identity; follow-up
`44d3255` removes caller recursion state and explicitly protects bare and
absolute `make` and `gmake` forms. The corrected public-contract file passed
110 cases, the guarded local-R contract passed, and the reopened complete gate
passed every lane in 165.119 seconds.

The first correction gate stopped because the sibling's ignored R library was
incomplete. A later run exposed and corrected inherited Make-variable
contamination in the new oracle. The passing gates used a temporary ignored
`.venv` symlink and explicit `RENV_PATHS_LIBRARY` reference to the established
primary environments; the symlink was removed, and no package was installed,
restored, or updated. Preserve the sibling's pre-existing ignored R cache
material unless an operator separately directs cleanup.

After this documentation commit, the corrected exact tip must pass the
additional Phase `0` adversarial review before non-force publication. Then stop
the approved phase. The affirmative decision releases `ARCH-02A`, `RPT-01`,
`LOG-01`, and `DOC-IA-01` only for later, separately approved task starts.
TEST-01Z's partial dependencies for `CODEDOC-05` and `SIZE-07` are satisfied,
but their other blockers remain. No Phase `02` card has been selected or
started. Publication and upstream equality remain deferred for the entire
tranche.

Do not inspect or execute `CONCURRENCY-02`, `PROGRAM-01`, paused concurrency
attempts, the researcher pilot, any `TEST-01G`–`TEST-01Y` work, or Phase `02`.
Their roadmap positions are not technological blockers for the explicitly
approved five-card tranche.

The one-time Phase `00` dependency exception and this five-card authorization
are exhausted. They do not authorize future changes outside the normal
development gate. Do not change production structure before all three Phase
`02` reviews and an approved migration package. Do not begin production,
cluster, scientific-policy, or biological-interpretation work.

The authoritative continuation sequence is in
[`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md); detailed future
scope and dependencies are in [`../tasks/`](../tasks/).
