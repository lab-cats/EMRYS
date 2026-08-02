# Project handoff

This is the canonical current takeover snapshot. The roadmap and acceptance
criteria live in [`../design/PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md);
commands live in [`RUNBOOK.md`](RUNBOOK.md).

## Checkout

- Branch:
  `codex/plan-02z-first-migration-readiness`
- Package base:
  `15aba53c538cabf2b7d2284575be0089b0ca90cf`
- Current documentation tip: the commit containing this handoff; resolve its
  exact SHA from live Git.
- Recorded package state: the canonical recovery integration is clean,
  published, and live-remote equal at the package base above. `PLAN-02Z` has
  completed its first rolling tranche plan; all other work remains frozen.
- Current package: documentation-only first-migration planning and review
  readiness for the neutral validation-report protocol.
- Package type: documentation-only; no executable, configuration, generation,
  schema, fixture, report-template, dependency, source-layout, public-interface,
  scientific-policy, or test-harness behavior changed.
- Remote publication and upstream equality: the package branch is not yet
  published. Final closure requires local `HEAD`, configured upstream, and the
  live remote ref to be equal. Cluster work remains paused.

This package descends directly from the verified integrated canonical tip
`15aba53c538cabf2b7d2284575be0089b0ca90cf`. It changes only Markdown
planning/review artifacts and adds no descriptor, schema, runtime, report
template, test-harness change, or integration fragment. Current executable
paths remain under the flat layout.

## Active concurrent lanes

No mutable concurrent lane shares this worktree or branch. The consolidated
recovery sidecar is immutable source evidence; semantic integration occurs only
in this canonical lane. The completed CONCURRENCY-02 synthetic exchange remains
recorded below, and unrelated candidate worktrees remain preserved and frozen.

| Lane ID | Role and owner | Worktree and branch/detached state | Base and target | Reservations and coupling | Validation or execution identity |
| --- | --- | --- | --- | --- | --- |
| `reconciliation-consolidated-01-sidecar` | Frozen, consumed documentation-recovery source | `/Users/elisteiger/dev/norad-worktrees/reconciliation-consolidated-01-sidecar`; `codex/reconciliation-consolidated-01-sidecar`; source must remain clean and unchanged | Base `44a27f033092cd42b79a9504b7fc292d3cc40f20`; canonical integration parent `0fd6348e6cfe54457fef5f65f3468bea106e61f9` | No remaining write reservation; accepted meaning is routed through the canonical owners and commit dispositions below | Source `5a35a057cd9ca259f83ee1dde3116fee63928d72`; no implementation, runtime, cluster, scientific-review, or biological evidence |

## Reconciliation recovery integration

Integration ID `RECONCILIATION-CONSOLIDATED-01` consumes immutable source
`5a35a057cd9ca259f83ee1dde3116fee63928d72` under a user-authorized recovery
exception. The 98-checkpoint source is not replayed, merged, rebased, or
cherry-picked: one direct canonical documentation commit re-materializes its
reviewed meaning against the exact current parent.

The source ledger covers 11 immutable packets, 16 underlying proposal commits,
132 per-commit changed-path rows, and 80 recovery requests. The terminal
request dispositions are 51 `accept`, two `partial`, 24 `defer`, three `stale`,
and zero `reject`; deliberate deferral is a completed reintegration decision,
not a reintegration blocker. The commit trailers preserve every disposition,
both accepted subsets, both residual dispositions, exact source provenance,
and the protocol exception.

The ledger excludes completed TEST work, corrected LOG reconciliation, final
`CONCURRENCY-02`, original LOG candidates, obsolete `CONCURRENCY-02` protocol
or synthetic candidates, `PROGRAM-01`/`ARCH-02A`/JIT work already in the
authoritative lineage, and the detached demo-report worktree. Their bodies were
not reopened for reintegration. One narrow historical HANDOFF excerpt was
checked solely to verify the preserved local `renv` warning; no TEST
implementation or excluded candidate was reintegrated.

The final tree creates eight complete TODO cards, eight nonselectable UNREFINED
proposal files, and the UNREFINED lifecycle README. The source classified a
ninth UNREFINED proposal named `DOC-CONS-08D`; canonical history already owns
that ID, so no duplicate is created and its unique dormant-demo rationale is
routed to `DOC-CONS-08G`. The integration fragment is intentionally absent.
File presence preserves an UNREFINED proposal but does not promote, select,
prioritize, block, unblock, or authorize implementation.

The current validator does not yet recognize the authorized UNREFINED
location. Final candidate validation reported exactly nine
`invalid card location` findings—the README and eight proposal files—and no
other finding, so the documentation gate is expected-only nonpassing rather
than passing. `TASK-LIFECYCLE-01` owns that future validator support; this
package neither implements it nor waives any other structural finding.
Computational, R, shell, report-runtime, and cluster suites are not applicable
to this documentation-only integration.

## Completed CONCURRENCY-02 synthetic exchange

Coordination checkpoint `a47ce4c` passed `git diff --check` and the complete
documentation gate, was pushed, and was proved upstream-equal before
provisioning the sidecar. The closed lane ID was `c02-synthetic-v2` in
`/Users/elisteiger/dev/norad-worktrees/concurrency-02-synthetic-exchange-reconciliation`
on `codex/concurrency-02-synthetic-exchange-reconciliation`. Its only candidate
write was `docs/fragments/CONCURRENCY-02-SYNTHETIC-V2.md`; every canonical
target was a nonexclusive declaration, and every other path—including pilot,
status, evidence, executable, and test paths—was prohibited.

Integration ID `CONCURRENCY-02-SYNTHETIC-V2` used candidate base
`8ba7a5cb39a7c87bc60e833eb0d061aaf758ad7c`, frozen source
`7385668edf52a5bb2db0a18ac50c7b890f596ac9`, remote source ref
`refs/heads/codex/concurrency-02-synthetic-exchange-reconciliation`, and
canonical pre-application parent
`590ba1e9981159bb5814996d41b90c333f036ccb`. The candidate was one clean
non-merge commit adding only that fragment; its `HEAD`, upstream, and live
remote ref were equal before application. Handoff state is
`consumed-source-preserved`, and package outcome was `applied`:

- `C02-SYNTH-V2-01` — `accept`; the candidate-side `pending` clarification is
  represented in [`docs/fragments/README.md`](../fragments/README.md#worked-example).
- `C02-SYNTH-V2-02` — `partial`; Subset A was routed within the declared owner
  to the authoritative
  [`integration-fragment lifecycle`](CONCURRENT_WORK.md#integration-fragment-authority-and-lifecycle),
  while Subset B was rejected because syntax can never authorize automatic
  semantic acceptance.
- `C02-SYNTH-V2-03` — `reject`; a permanent fragment archive would create the
  prohibited shadow backlog. The immutable remote candidate ref preserves the
  raw proposal instead.
- `C02-SYNTH-V2-04` — `defer`; structural enforcement remains in the existing
  [`CONCURRENCY-03`](../tasks/TODO/CONCURRENCY-03-enforce-integration-fragment-lifecycle.md)
  card. No new question, card, lifecycle state, or `UNREFINED` item was created.

The final tree removes `docs/fragments/CONCURRENCY-02-SYNTHETIC-V2.md` and
retains only the schema README under `docs/fragments/`. Source/ref and
per-request trailers in the final canonical commit are the durable terminal
record; fragment absence is not treated as evidence by itself. This exchange
tests the manual documentation handoff. The separately tested orchestration
helpers enforce only operator-supplied mechanics; neither the exchange nor the
helpers review pilot content or establish runtime, cluster, scientific, or
biological state.

Preserved local proposals `8374c96`, `823f198`, and `1afae15` remain historical
review evidence only. They were not merged, rebased, or replayed into this
lineage; their obsolete current-state claims and incomplete durability or
schema coverage are not canonical.

The earlier researcher-path pilot is now accounted for through the immutable
consolidated source and this recovery integration. Its useful card content was
re-synthesized against current owners; `CORE_DOC_CHANGES.md`, transient source
status, and incompatible or duplicate ownership were not replayed. The
original pilot ref remains historical source evidence, not an active lane or
independent integration authority.

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
- a file-backed task registry with 73 actionable cards in the current working
  tree plus eight nonselectable UNREFINED proposals,
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
- the completed manual integration-fragment protocol and synthetic exchange,
  followed by the separately authorized consolidated recovery of the reviewed
  pilot proposals and related immutable source packets;
- unselected follow-up cards for rolling-wave coordination, structural
  fragment enforcement, validator support for the authorized nonselectable
  `UNREFINED` intake, frozen `INTEGRATION_REVIEW`, and orthogonal logical epic
  indexes; none of those future mechanisms is implemented by CONCURRENCY-02;
- explicit standalone documentation-package semantics: computational
  validation is not applicable when the complete diff has no executable or
  test-affecting consumer;
- a normalized current-output inventory covering every public Python, shell,
  R, SLURM, and Make surface plus validation, documentation-gate, operational-
  check, durable-copy, and evidence-log roles; mixed streams and unsafe or
  conditional durability remain labeled behavior rather than approved design;
- a version-1 target logging contract covering direct/environment controls,
  machine/human streams, dry-run command visibility, one-writer operation
  identity, durable JSONL, receipt-safe ordering, bounded failure summaries,
  protected retention, scheduler/evidence separation, and adoption inputs;
- one canonical 14-owner semantic identity and DAG map with 15 direct artifact
  edges, explicit barriers, typed external inputs, and historical aliases;
- one target source/contract/test topology assigning every functional owner a
  unique home, versioned YAML descriptor convention, native-asset owner,
  mirrored tests, and acyclic dependency direction; and
- one reversible direct-migration procedure with temporary-wrapper criteria,
  caller order, seven-class parity matrix, rollback/removal boundaries, and a
  concrete-card checklist;
- an open-choice ledger and updated future Mermaid sources. Current executable
  topology and paths, report behavior, logging behavior, historical numeric
  aliases, and runtime/scientific evidence remain unchanged.

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
| Phase `01z` behavior sufficiency | 88/88 public-entry-point, cross-cutting, and fixture rows have explicit preserved-contract, characterized-defect, or environment-deferred dispositions with zero undefined rows; the checked Python refresh passed with 843 tests, 17 expected skips, 8,585/10,551 lines (81.3667%), and 3,111/4,404 branches (70.6403%); a later Phase `0` adversarial review found unprotected Make-expansion and R-argument claims, `0c64d1a` closed both, `44d3255` closed bare-Make portability, and `fd98244` closed ambient Make-state contamination; the final focused and complete gates plus exact-tip independent review pass, while the affirmative result still releases only four named Phase `02` planning roots and changes no production or evidence state |
| Phase `02` LOG-01 current-output characterization | every current public/runtime and validation surface maps to an explicit output profile and regression/consumer trace in [`TEST_BASELINE.md`](../design/TEST_BASELINE.md#log-01-current-output-and-log-inventory); validator mixed stdout, conditional SLURM capture, per-lane validation retention, Step `05` duplicate-tee publication, exposure limits, and application/evidence-log separation are characterized without changing executable behavior or evidence state |
| Phase `02` LOG-02 logging contract | the [version-1 target](../architecture/FUTURE_ARCHITECTURE.md#logging-target) defines `normal|verbose|debug`, direct/environment controls, dry-run command visibility, machine stdout and human stderr, one-writer operation-attempt JSONL, receipt-safe required writes, bounded failure tails, protected operator retention, conditional scheduler separation, explicit evidence authorization, and normalized cross-level equivalence without changing current executable behavior or evidence state |
| Architecture-direction documentation | task registry, decisions, open choices, target architecture, roadmap, handoff, and four future diagrams updated; documentation-only validation passed; no executable, dependency, schema, config, fixture, test-harness, scientific-method, runtime, cluster, or evidence-state change |
| Task-start context documentation | task-start router, context-freshness matrix, expansion triggers, impact-directed documentation review, and documentation-only validation semantics updated; `git diff --check`, the 71-document/51-card/6-diagram structural gate, and independent read-only consistency review passed; computational validation was not applicable because no executable, dependency, schema, config, fixture, report-template, test-harness, scientific-method, runtime, cluster, or evidence-state surface changed |
| Concurrent documentation lanes | `CONCURRENT_WORK.md`, fail-closed Git 2.54 worktree/integration/recovery commands, write authority, card/status rules, immutable-execution attribution, and final-combined validation semantics completed; `git diff --check`, the 72-document/51-card/6-diagram structural gate, and independent policy/ownership and Git/recovery audits passed; no active delivery experiment ran and computational validation was not applicable because the complete diff is non-consuming Markdown only |
| Strategy follow-up card bootstrap | Four future cards plus reciprocal dependency and canonical roadmap/decision/question/handoff references recorded; no card selected and no pilot content reviewed or integrated; `git diff --check`, the 76-document/55-card/6-diagram structural gate, and independent dependency, ownership, and handoff/roadmap audits passed; computational validation is not applicable because the complete diff is non-consuming Markdown only, and publication state remains subject to live Git verification |
| Documentation ownership and navigation | Audience routes, canonical responsibilities, exhaustive Markdown/Mermaid dispositions, semantic link roles, a no-loss move ledger, rule-by-rule `AGENTS.md` disposition, resolved overview/history/convention locations, and eight bounded consolidation cards recorded; root ownership rosters now link one owner; the final structural documentation gate and independent no-loss/dependency reviews passed; later consolidation remains unselected, computational validation is not applicable, and no executable or evidence state changed |
| Root agent-router compression | Root `AGENTS.md` reduced from 319 to 195 lines while retaining automatic approval, authority, safety, evidence, scientific, and destructive-action guards; neutral engineering conventions and the full package-delivery procedure now have dedicated owners; independent no-loss and owner-boundary reviews plus `git diff --check` and the 115-Markdown/65-card/6-diagram documentation gate passed; computational validation is not applicable, and no executable or evidence state changed |
| Root entry and priority compression | Root `README.md` retains product identity, evidence limits, minimal start, repository map, and action-point cautions while routing detail to dedicated owners; root `TODO.md` now contains only the ordinary runway priority and canonical state/blocker/task/question routes; the no-loss ledger and independent review found no orphaned fact or duplicate owner; `git diff --check` and the 115-Markdown/65-card/6-diagram documentation gate passed; computational validation is not applicable, and no executable or evidence state changed |
| Operational guidance compression | `RUNBOOK.md` now indexes exact commands, contract routes, shared validator semantics, and retained inline-program dispositions; `TROUBLESHOOTING.md` indexes diagnostics and links duplicated commands while preserving owner-specific limits and distinct transaction recovery; Step `08` parsing semantics and shared publisher recovery remain under canonical owners; independent anchor, ownership, diagnostic, and no-loss reviews plus `git diff --check` and the 115-Markdown/65-card/6-diagram documentation gate passed; computational validation is not applicable, and no executable or evidence state changed |
| Dated documentation history | `docs/history/` now indexes immutable audit and testing records with explicit event/source provenance; the 1,160-line audit and 963-line baseline snapshots remain complete while current `REFACTOR_AUDIT.md` and `TEST_BASELINE.md` are concise recheck/policy/risk routes; independent provenance, owner, anchor, and no-loss reviews plus `git diff --check` and the 120-Markdown/65-card/6-diagram documentation gate passed; computational validation is not applicable, and no executable or evidence state changed |

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

## Preserved local recovery constraint

An earlier sibling-worktree `renv` activation attempted automatic bootstrap
before failing on missing packages and may have left ignored local cache
material. Do not delete, repair, normalize, or reuse that cache without
operator review. The later successful gate referenced the already-restored
primary project library through `RENV_PATHS_LIBRARY`; it did not restore or
update packages, and its temporary Python-environment symlink was removed.

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

[`DOC-IA-01`](../tasks/COMPLETED/DOC-IA-01-define-documentation-ownership-and-navigation.md)
is complete. Its canonical result is the
[`documentation ownership and consolidation map`](../sitemap/DOCUMENTATION_OWNERSHIP.md),
and separately approved local-only documentation exceptions
[`DOC-CONS-08A`](../tasks/COMPLETED/DOC-CONS-08A-slim-root-agent-router.md)
and
[`DOC-CONS-08B`](../tasks/COMPLETED/DOC-CONS-08B-compress-root-entry-and-priority-views.md)
and
[`DOC-CONS-08C`](../tasks/COMPLETED/DOC-CONS-08C-compress-operational-guidance.md)
and
[`DOC-CONS-08D`](../tasks/COMPLETED/DOC-CONS-08D-establish-dated-documentation-history.md)
are complete. Their root and operational compression and dated-history split,
neutral
[`engineering-conventions owner`](ENGINEERING_CONVENTIONS.md), and expanded
[`task-delivery procedure`](TASK_DELIVERY.md#package-delivery), concise newcomer
entry, short current-priority route, indexed runbook, diagnostic split, and
concise current audit/baseline routes do not select the remaining
`DOC-CONS-08E`–`DOC-CONS-08H` cards or change ordinary
runway order; each still
requires separate selection, task-specific planning, and approval. Existing
`DOC-SITEMAP-01`, `DOC-README-03`, `DOC-GATE-01`, `DOC-PIPE-04`, `CODEDOC-05`,
and `TASK-EPIC-01` retain their nonoverlapping scopes.

This package changes documentation only. Its final gate is Git and repository
documentation validation; computational, R, shell, report-runtime, and cluster
suites are not applicable. It creates no runtime, cluster, scientific-review,
or biological-readiness evidence, and no dependency was installed, restored,
or updated.

[`PLAN-02Z`](../tasks/COMPLETED/PLAN-02Z-integrate-future-task-sequence.md) is
complete. It proposes
[`MIG-03A`](../tasks/TODO/MIG-03A-extract-validation-report-library.md) and a
dedicated architecture, reliability, and usability review chain. The next
action is the selected read-only `REVIEW-ARCH-03A` pass, followed by the later
reviews in order. No physical migration has begun. All other work, including
the unsliced `PROGRAM-01` remainder, remains preserved but currently dead/out
of scope until the first physical migration and explicit user reassessment.
