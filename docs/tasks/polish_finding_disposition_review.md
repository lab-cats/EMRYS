# Polish finding disposition review — working draft

Source snapshot: `codex/pr302-original-intent-corrections` at
`3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d` (2026-09-22).
This companion to the [backlog and campaign audit](backlog_campaign_audit.md)
holds the per-item polish review. It is not a task-status authority or
permission to implement or remove any proposal. The original
[polish campaign](polish-campaign.md) and accepted
[main matrix](backlog_matrix.md) retain their distinct roles.

**Observed:** Several original premises in the [polish campaign](polish-campaign.md)
have changed at the audit baseline. Item 7's September 7 finding said Init
preview showed only output locations; this branch dates that claim in the
source campaign. The current public preview in
[`onboarding.py`](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 1163–1258 includes libraries, Analysis/site, reference, scientific
choices, and defaults, with detailed manifests behind verbose output. That
invalidates the old "only output locations" premise but does not yet prove
full preview/publication agreement; GTF and individual paths remain in
verbose detail. Item 8
(lines 329–339) says Doctor lacks a profile selector, but
[`doctor.py`](../../src/emrys/orchestration/run_coordinator/doctor.py) lines
1976–1982 offers `--profile` and lines 484–510 select it. Item 9's old
direct-storage-plan premise (lines 341–358) is narrowed by Doctor's current
Slurm branch at lines 835–857; site behavior still needs review. Item 36
(lines 798–811) describes explicit-memory preflight as missing, while the
[current `SCHED-01` row](backlog_matrix.md#platform-operation-and-portability)
says its source is implemented and verification remains.

Item 6 is locally reproduced at this audit head: the public
[`validate_record`](../../src/emrys/contracts/orchestration/api.py) path accepts
both a valid timestamp and `finished_at: "not-a-time"` in a minimal blocked v3
Attempt receipt when run with the locked `jsonschema` 4.26.0 package. Its
optional RFC 3339 checker is absent from the lock closure, so `date-time` is
not registered. The [producer](../../src/emrys/orchestration/run_coordinator/lifecycle.py)
emits valid UTC timestamps, and [inspection](../../src/emrys/orchestration/run_coordinator/_inspection_attempts.py)
can later flag the malformed time; neither makes public admission reject it.
The current [contract test](../../tests/contracts/orchestration/test_orchestration_contracts.py)
rejects a non-string time but not a malformed string. This is a local contract
probe, with no hosted or site evidence. Other `FormatChecker` callers remain
to be reviewed before selecting a correction.
The same optional checker is used by the artifact validator. Run-summary and
report-receipt schemas declare timestamp formats, making them source-indicated
exposures that still need a direct malformed-record probe. The artifact-record
schema and the report index's own Run-contract checker have no timestamp field.
This narrows the follow-up without promoting the orchestration probe to proof
of artifact behavior.

Item 7's current preview validates a provisional Project definition and shows
the major scientific choices. When unset, it labels `sjdb_overhang` and
`genome_chr_bin_nbits` automatic at creation; the creation path derives those
values after FASTQ admission and then publishes final Project bytes. Focused
tests cover displayed choices and some published values, but no complete
preview/publication agreement oracle is retained. This is an explicit deferred
value, not a demonstrated silent mismatch. Acceptance needs a semantic rule
for exact displayed choices versus deferred values.

**Confirmed group mismatch:** Item 11 is not yet aligned:
[Quickstart](../../quickstart.md) line 44 uses
`--no-default-groups --group workflow`, while the managed golden CI lane in
[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) lines 632–638
lacks `--no-default-groups`. [`pyproject.toml`](../../pyproject.toml) makes both
`dev` and `workflow` default groups. The locked Linux/Python 3.14 dependency graph
projects 73 shared names (EMRYS plus 72 dependencies) and 17 CI-only
development packages,
including `pytest`, `coverage`, `ruff` and `pre-commit`, with no different
versions among the shared names. This offline graph comparison is not an
installed-environment manifest. The [baseline managed golden job](https://github.com/lab-cats/EMRYS/actions/runs/35770811692/job/106891764037)
passed with that broader environment, not the documented minimal one; its
later containment step runs `.venv/bin/python -m pytest`, so merely changing
the sync flags would remove a dependency of that step.

Item 12's draft versus admitted FASTQ identity question remains: the draft
rejects reused physical files by device and inode (`onboarding.py` lines
1441–1457), while Project normalization checks
path equality and caches by path
([`normalization.py`](../../src/emrys/orchestration/run_coordinator/normalization.py)
lines 359–385). This is a policy comparison, not an established defect.
The source comparison confirms that the draft helper rejects reuse of one
physical FASTQ across sample/mate roles, while Project admission checks only
same-row R1/R2 path equality; a cross-row path or hard-linked mate can pass that
specific check. Symlink handling differs at these trust boundaries; no
Run-level failure was reproduced, and one Dataset may legitimately be
used by multiple Analyses. Decide physical reuse per Dataset sample/mate roles,
separately from item 12's explicit-filename interface proposal.

Item 35's recorded Snakemake hash identifies the Python executable bytes;
version and empty-workflow probes exercise installed Snakemake but do not bind
its module-tree bytes. The lock pins an intended distribution, while fresh
Run/resume re-admission does not identify a live module-tree hash. No controlled
same-version mutation or end-to-end escape was demonstrated. Choose the needed
content guarantee before selecting a caller-complete change.

**First complete item inventory:** Each line below maps one numbered
[polish discussion](polish-campaign.md) at `3a672fdf`. "Delivered" means its
described source capability exists at this revision; it is not independent
acceptance of a larger backlog outcome or institutional proof. "Unselected"
means the campaign itself does not authorize implementation. The original
finding and any unique rationale remain available in the campaign while a
durable disposition is decided.

| Item | Audit reading at baseline | Remaining disposition or evidence |
| ---: | --- | --- |
| 1 | Validation-report recovery defect remains documented by its owner. | Keep with validation recovery and direct fault checks. |
| 2 | Storage-inventory replacement proposal is explicitly retired. | Historical rationale can be condensed after checking unique decisions. |
| 3 | Reference-provenance replacement recovery defect remains owner-documented. | Keep recovery evidence with that owner. |
| 4 | Runtime-report publication proposal is explicitly retired. | Historical rationale only after retention check. |
| 5 | Current-artifact admission through the public validator is delivered. | Avoid re-presenting it as a missing feature. |
| 6 | Public v3 Attempt receipt admission accepted `finished_at: "not-a-time"` in a source-bound local probe under the locked checker closure. Artifact Run summary and report receipt have source-indicated exposure, not a direct probe. | Select timestamp policy and maintained checker; test malformed and valid historical/current fields through public orchestration and artifact admission. |
| 7 | Init previews major choices; when unset, two STAR values are explicitly deferred until FASTQ admission, so final Project bytes can differ from provisional preview bytes. | Replace the old missing-preview premise; define and verify semantic agreement for displayed exact and deferred choices without preview input reads or writes. |
| 8 | Doctor `--profile` supports default, named, and absolute selections in source and focused tests. | Mark source delivery; keep site acceptance with CV-07. |
| 9 | Current Slurm repair planning skips the formerly alleged direct-storage plan. | Re-evaluate full placement behavior and site evidence; do not claim the old source-predicted failure persists. |
| 10 | Novice institutional walkthrough remains accepted under `SITE-PARITY-01`. | Keep its exact site evidence requirement. |
| 11 | Quickstart excludes default `dev`; managed golden CI includes it. The offline locked graph has 17 CI-only package names, while shared versions agree. | Verify an operator-minimal golden journey separately from the later `pytest` containment check; assert group selection. No install-speed or site claim. |
| 12 | Draft FASTQ physical-identity refusal differs from Project admission's same-row path check; cross-row or hard-linked reuse is source-permitted, with no Run reproduction. | Decide per-Dataset physical-reuse policy apart from the explicit-name proposal; retain legitimate cross-Analysis Dataset reuse and distinct symlink boundaries. |
| 13 | Ineffective reporting-memory control is retired. | Historical disposition only. |
| 14 | Standalone dashboard retirement is implemented; ordinary baseline software/docs CI passed, while institutional visual review remains. | Keep `DASHBOARD-RETIRE-01`, legacy readers and the separate evidence-deletion gate. |
| 15 | Per-script Bash syntax checking is delivered. | Keep owner check, not an open proposal. |
| 16 | ShellCheck is delivered under `DEV-01`. | Keep its locked-tool owner. |
| 17 | Selected Ruff correctness rules are delivered. | Do not infer all possible rules were adopted. |
| 18 | Consistent Python formatting is delivered under `DEV-01`. | Keep the accepted formatting baseline. |
| 19 | A Python type checker remains an unselected proposal. | Decide value and exact supported scope before adding a gate. |
| 20 | Optional fast local hooks are delivered under `DEV-01`. | Keep existing hook owner. |
| 21 | Local/CI validation inventory work is delivered. | Retain distinct check coverage. |
| 22 | Ordinary CI on supported stacked PRs is delivered. | Recheck effective hosted rules only if making a new policy claim. |
| 23 | The bounded CI critical-path work is delivered under `CI-01`. | Retain measured evidence rather than an assumed current duration. |
| 24 | Dependency-update bot remains an unselected tooling proposal. | Check current hosted configuration before selection. |
| 25 | Vulnerability assessment remains an unselected tooling proposal. | Identify an actual tool and maintenance owner before adding a gate. |
| 26 | Bounded R static analysis remains unselected. | Preserve distinct real-R and scientific tests. |
| 27 | Shell formatting remains unselected; a declared `SHFMT_BIN` is not a selected gate. | Prove need and scope before tooling growth. |
| 28 | Local secret detection remains an unselected gap-dependent proposal. | Require a demonstrated need and data-safe workflow. |
| 29 | External Analysis/reporter usability is accepted as Open `EXTENSION-01`. | Keep complete real discovery/installation acceptance with that row. |
| 30 | Release path is accepted as Open `RELEASE-01`. | Date-bound old distribution observations; do not claim release readiness. |
| 31 | Citation guidance remains an unselected proposal. | Decide authoritative format and owner. |
| 32 | Release dependency inventory/provenance remains an unselected proposal. | Coordinate with `RELEASE-01` before making a release artifact. |
| 33 | September 22 API recheck found the default-branch rulesets still lack required status checks; PR #312's correction-branch base returned no effective rules. | Keep hosted policy unselected; test proposed merge behavior separately before any settings change. |
| 34 | Complete R dependency closure is accepted as Open `RUNTIME-CLOSURE-01`. | Keep recursive closure and snapshot-off acceptance with the row. |
| 35 | Snakemake's recorded SHA binds Python executable bytes; version/startup probes do not bind installed Snakemake module bytes. No controlled same-version escape was demonstrated. | Decide the installed-content guarantee and test changed-package behavior through Doctor, fresh Run, resume and child entry before selecting a replacement. |
| 36 | Explicit Slurm memory preflight is implemented and its ordinary baseline software checks passed; `SCHED-01` remains Verification pending. | Date-bound the old missing-implementation premise; keep CV-11's institutional capacity limit. |
| 37 | Browser/copy/print report review remains pending under report rows 01–03. | Retain rendered visual and link acceptance separate from receipts. |
| 38 | Pre-execution cancellation policy remains unselected. | Decide expected signal/EOF behavior before changing public exits. |
| 39 | Machine-readable inspection needs a concrete consumer and remains unselected. | Preserve human inspection authority and exit meaning. |
| 40 | The documentation checker validates structure, not fenced-command behavior. | Select safe examples before adding a command check. |
| 41 | Normal inspection still favors verified report locations; scientific paths are in verbose detail. | Retain the processing-only/no-report output-location UX question. |
| 42 | Run selection still lacks sufficient admitted Analysis context. | Retain presentation proposal without treating labels as integrity proof. |
| 43 | `emrys --version` is delivered under `CLI-VERSION-01`. | Keep current source identity and foreign-directory limits. |
| 44 | Contributor/problem-reporting route remains unselected. | Choose a data-safe public route without inventing contact details. |

The five integration-scale architecture options are also unselected; the
campaign withdrew its 6,400–9,200-line estimate. Their prerequisites differ:

| Option | Required evidence before selection |
| --- | --- |
| Unified Inspect/Watch observation | One admitted observation and caller-complete selection/presentation retirement with scheduler state remaining observational. |
| Shared operation kernel | Equivalent trust and mutation boundaries across every migrated owner, with unchanged exits, claims, logs, receipts, and recovery. |
| Declarative records/scenarios | Smaller fixture surface with distinct failure modes and independent scientific/evidence oracles intact. |
| Common reporting transaction | A smaller caller-complete replacement for both publishers despite their different commit/recovery order. |
| Narrow supported surfaces | Exact consumer inventory, migration/rollback, and separate public-contract approval. |

## Polish audit and PR chronology retention map

This maps [the campaign's dated audit and overlap record](polish-campaign.md#evidence-and-selection)
by stable section and item. A Git-only candidate is a possible future shortening,
not permission to remove source evidence. Verify each proposed home and its links
before changing the campaign; retained-evidence deletion has a separate approval
and commit boundary.

| Campaign source | Unique fact or decision to retain | Git-only chronology candidate | Required transfer or verification |
| --- | --- | --- | --- |
| [Evidence and selection](polish-campaign.md#evidence-and-selection): original audit | The September 7 source revision, inspected surfaces, and absence of new product tests, benchmarks, science, or institutional execution qualify every original finding. | The then-open PR-number sequence. | Keep the pinned revision and evidence limit in the campaign or a source-dated audit record before shortening the sequence. |
| [Evidence and selection](polish-campaign.md#evidence-and-selection): documentation and audit passes | PR #130's five focused setup/Doctor tests are source-reported earlier evidence, not tests run in the integration. The second and third passes added distinct findings without installed-command, report-rendering, input-reuse, upgrade, or new product-test proof. | PR integration order and the repeated pass-by-pass narrative after each resulting finding is mapped below. | Retain the evidence limits and source revisions with a dated audit record if the campaign is retired; keep item 33's hosted-rule observation date-bound. |
| [Evidence and selection](polish-campaign.md#evidence-and-selection): integration and validation | Exact ordinary CI runs 34301289787 at 2fb8f5ef and 34306975901 at b491aac5 support bounded software claims. The 2fb8f5ef and 8034c211 commits have the same Git tree. These runs do not establish long-lane, institutional, production, scientific-review, or biological acceptance. | The PR #139/#140/#148/#169 merge route and repeated delivered-slice list. | [Dated compression evidence](../history/2026-09-14-compression-closeout.md#hosted-verification-and-limits) and the [accepted matrix](backlog_matrix.md#completed-and-closed-outcomes) already retain the run identities and limits. Recheck their exact coverage and preserve the tree-equality qualifier if it is needed for a surviving claim. |
| [Architecture options](polish-campaign.md#integration-scale-architecture-reduction-options) | The 6,400–9,200-line estimate was withdrawn. Each unselected option has its own caller, trust, recovery, test, and approval conditions; review structure alone is not product reduction. | Only the dated integration-review setup, if the comparison is preserved with its source and counts. | Keep the full option rationale in the campaign until a selected owner adopts or explicitly dismisses each option. The short table above is a navigation aid, not a replacement. |
| [Item 33](polish-campaign.md#33-make-the-required-merge-checks-explicit) and [overlap inventory](polish-campaign.md#existing-capabilities-and-overlapping-work): audit-time hosted settings | The earlier rules and CodeQL references were a dated configuration observation, not proof of every run or current merge protection. | Repeated inventory of then-present tools and capabilities once current owners are checked. | Use item 33 above for the September 22 recheck; keep the original observation explicitly dated wherever it survives. |
| [Overlap tables](polish-campaign.md#existing-capabilities-and-overlapping-work): merged PRs | Overlap dispositions prevent completed work from being selected again; PRs #128/#134 did not repair item 2. PRs #144–147 include source-identity, fixed-HTML-output, BAM-publication, and reporting-publication decisions. | The PR-by-PR merge inventory after each unique decision and unresolved limit has an owner. | Compare every row with the item table above, [reporting decisions](../design/decisions/execution-evidence-and-reporting.md#reporting-lifecycle-compression), and the [compression closeout](../history/2026-09-14-compression-closeout.md). Preserve any unmatched rationale before shortening. |
| [Overlap exceptions](polish-campaign.md#existing-capabilities-and-overlapping-work) and [campaign rule](polish-campaign.md#campaign-disposition) | The integrations do not close unrelated recovery, Doctor, browser, or scientific work. PRs #44/#45 are separate experiments, not adopted improvements. Campaign retirement requires a disposition and durable home for every proposal. | PR #150 and CS-18 sequencing after their owner decisions are verified. | Keep negative scope, evidence-retention limits, and the campaign selection rule; verify the experiments against the optimization owner before reducing this paragraph. |

**Next:** Select item 6's timestamp policy and contract checks; verify an
installed operator-minimal journey for item 11 while retaining its later test
step. Decide and test any merge policy for item 33 separately. Resolve items 7,
9, 12 and 35 with direct checks or policy decisions. The campaign's old PR
chronology can be shortened only after unique decisions and dated evidence
have a verified owner.
