# DOCS-01 discovery notes, fifth file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F130–F163; [sixth notes](docs-01-discoveries-sixth.md) begin at F164.
F130–F131 use local audit head `3ebfb2bf`, read on 2026-09-23;
F132–F133 use `935adf06`, F134–F139 use `ebc0012d`, and F140 uses `f239a91d`
on that date. F141–F143 use `1eb562f0`; F144–F145 use `f91b8303` on that
date; F146–F148 use `cc5c1f58`; F149–F153 use `a3310af6`.
F154–F158 use `3ea9c2b1`, read on 2026-09-23 and rechecked at `238e8035`.
F159 uses `688f7117`; F160 uses `60ec53e1`, read on 2026-09-23.
F161 uses `22972af4`, read on 2026-09-23.
F162–F163 use `f2e719c0`, read on 2026-09-23.
At `d55baa91`, read on 2026-09-23, adversarial review dismissed
F144–F146/F148–F149/F153 and narrowed F150/F159. Selected test/CI guides
yielded no separate high-confidence finding.
At `1ddd14ea`, a read-only pass compared the ingestion, shared-contract,
architecture, and decision guides with their source and direct tests. It found
no distinct new candidate; the architecture and platform decision extend F33's
existing Results/report-publication wording question. Root, Quickstart,
configuration, and smoke-guide rereads also found no distinct candidate.
F138 was dismissed on
adversarial recheck at `f239a91d`.
F130 was dismissed as a duplicate on recheck at local head `935adf06`.
Source and direct tests were read, not executed. These are documentation
observations, not runtime results, accepted changes, or permission to alter
retained evidence.

## Discovery notes

### F130 — Repeated test-scope paragraph across eight owner guides

**Dismissed duplicate.** [F28](docs-01-discoveries.md#f28-repeated-owner-boilerplate)
already records the identical five-line paragraph in the same six stage and
two evidence test guides (40 physical lines), plus six production README copies.
F130 adds no independent finding or saving estimate. Its number remains to
trace this correction; no documentation deletion follows.

### F131 — Receipt validation scope in the glossary

**Dismissed after recheck at `71ac2272`.**
The [glossary](../reference/GLOSSARY.md) line 69 defines a receipt as published
after all other transaction members “validate” and says its presence marks
transaction completion. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1117–1126 distinguishes staged checks from independent validation:
Steps 08/09 validate before publication, while other scientific owners publish
native finals, including any receipt last, before the independent validator
and semantic all-pass. The [Step 07 owner contract](../../src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md)
lines 57–64 makes the second order explicit: its worker checks staged VCFs,
the runner publishes VCFs and receipt, and the independent validator checks
the visible set. A [direct task test](../../tests/orchestration/run_coordinator/test_task.py)
lines 759–776 shows a failed validation row prevents the verified-task marker.
The glossary explicitly says transaction completion, requires re-admission,
and links the decision that separates native publication from task completion.
It makes no verified-task promise; no useful DOCS-01 correction or reduction
is established by this wording.

### F132 — Benchmark timing scope in the Runbook

The [Runbook](../operations/RUNBOOK.md) lines 730–733 says the resource helper
measures explicitly listed setup, production, and validation commands, then
mentions wall time and peak child memory without assigning their scope. The
[helper](../../scripts/benchmark_stage_resources.py) lines 427–466 executes
setup and validation with `_run`, but times only the producer with `_run_timed`.
Its result fields at lines 41–57 and 484–499 retain setup and validator exit
codes, while elapsed, CPU, RSS, and block counts are producer-specific. The
[optimization campaign](optimization_campaign.md#measurement-and-adoption)
lines 364–374 explicitly says validator time is excluded and a producer-only
benchmark does not establish complete public-command latency. The Runbook
wording can give an operator a broader measurement expectation. Setup and
validation still execute and gate trial success; this is a documentation-scope
observation, distinct from F62's value-label issue. No benchmark was run and
no performance result follows.

### F133 — Fourteen workflow owners labeled scientific

**Dismissed for DOCS-01 at `3335b7d1`.** The [architecture guide](../architecture/ARCHITECTURE.md)
line 54 calls the built-in path's fourteen owners “scientific,” but its
responsibility table at 41–43 separates operational evidence and its nearby
phase table at 64–68 names non-gating alignment evidence. The
[stage map](../../src/emrys/contracts/STAGE_MAP.md) 19–34 confirms ten stages,
two analyses and two evidence collectors. In context the phrase is broad path
shorthand; removing one adjective saves no physical line or useful separate
correction. It implies no graph, scheduling or scientific-result defect.

### F134 — CV-25 implementation account beside current log owners

**Dismissed for DOCS-01 after recheck at `f4ba7662`.**
The completed [CV-25 card](cluster_verification_backlog.md#cv-25-log-discovery-and-readable-output)
lines 3689–3746 records three Task-log and log-discovery slices with distinct
checks and evidence limits. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 532–555, 663–671, and 1184–1196 owns current log-root precedence,
association, Task-log admission, and diagnostic limits; the [Runbook](../operations/RUNBOOK.md)
lines 17–37 gives the operator route. Neither replaces the CV card's original
E01–E06 need, selected interface, dated tests/CI, hosted-only completion, or
institutional limits. The 58 lines are history and acceptance context, not a
safe saving or permission to delete evidence.

### F135 — CV-24 repeats the current watch action protocol

**Dismissed after recheck at `f67410cb`.**
The [CV-24 card](cluster_verification_backlog.md#cv-24-run-center-actions)
lines 3639–3661 describes `p`/`b`/`s` handoffs, fresh planning, refusal of
noninteractive actions, and Slurm's concurrent-resume caveat. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 644–661 owns that exact present behavior, and the
[Runbook](../operations/RUNBOOK.md) lines 121–137 gives the operator keys and
commands. The card's selected three-action disposition, fixture/CI evidence,
new-analysis choice at lines 3663–3672, hosted-only completion, and separate
CV-16/institutional and dashboard-retirement acceptance remain distinct.
The card needs its selected interface beside hosted and pending acceptance;
no useful DOCS-01 reduction is established.

### F136 — Private planning-helper narration in the coordinator contract

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 852–858 states the public planning composition, then names private
`_tasks` and `_task_commands` helpers and their caller's three local results
at 854–857. [Materialization source](../../src/emrys/orchestration/run_coordinator/materialization.py)
lines 328, 891, and 1042–1059 confirms the implementation; the
[coordinator index](../../src/emrys/orchestration/run_coordinator/README.md)
lines 29–40 already maps `materialization.py` to planning. The helper names
have no evident public or recovery role. Only 854–857's helper narration is a
2–3-line candidate; retain public composition at 852–853 and distinct
STAR/reference/input/R construction at 857–858. No net saving is measured.

### F137 — Reporting artifact format in the coordinator contract

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1219–1222 lists manifest fields, JSON-last order, excluded record/index
files, and HTML receipt/output facts. The [reporting owner](../../src/emrys/reporting/README.md)
lines 10–20 and 38–40 owns the manifest and HTML roster; its publication
section at 66–79 owns create-only and receipt-last behavior. The
[artifact-index owner](../../src/emrys/reporting/_artifact_index/README.md)
lines 25–28 and 62–69 adds validation-result meaning and its limits.
Keep the coordinator's two-transaction sequence and independent science and
reporting admission at 1203–1218, plus its Run-root location map at 1230–1244.
The four-line overlap is a placement candidate, not a demonstrated full
saving; caller links and recovery boundaries require review before transfer.

### F138 — Reporting fault-test detail in the production guide

**Dismissed after recheck.** The [reporting owner guide](../../src/emrys/reporting/README.md)
lines 114–119 links the [test guide](../../tests/reporting/README.md#fault-injection)
for injection points; it does not repeat monkeypatch mechanics. Its brief
source-observer and input-recheck statements describe surviving production
guarantees. The test guide explains how its fixtures exercise them. The
original six-line overlap claim does not establish unnecessary detail or a
safe saving; the number remains to trace this correction.

### F139 — Storage command route in the evidence index

The [evidence index](../../src/emrys/evidence/README.md) lines 16–20 points
readers to `emrys debug storage-qualification` “for storage.” The
[storage owner](../../src/emrys/evidence/storage_inventory/README.md)
lines 32–52 calls this an advanced manual check and gives head-node
`emrys doctor --repair` as the normal path; the
[Runbook](../operations/RUNBOOK.md) lines 538–575 agrees. The index may be a
command catalog, but does not distinguish routine qualification from the
manual two-phase procedure. This is a reader-route ambiguity only. Preserve
the manual command, its phase and residue cautions, and Doctor's ordinary
qualification route; no storage command was run.

### F140 — Generic selection policy repeated in the polish campaign

The [polish campaign](polish-campaign.md) lines 87–107 gives a five-bullet,
21-line generic procedure for each selected slice: scope and caller review,
existing-owner/tool choice, separate footprint accounting, immutable Run and
evidence protection, and local/CI evidence levels. The
[workflow](../operations/WORKFLOW.md) lines 9–18, 29–65, and 69–85 already
owns this selection and delivery process; the
[architecture guardrails](../design/decisions/platform-direction.md) lines
73–108 own its permanent compression and approval boundaries. The
[REDUCE-01 row](backlog_matrix.md) line 66 owns classification for that card,
not every campaign slice. The campaign's explicit no-parallel-framework list
at 92–95, tooling-only footprint exception at 98–101, and separate-selection
warning at 13–20 remain specific, as does its dated source audit at 35–80.
An eight-to-eleven-line linked route might save 10–13 lines if it keeps those
limits; no draft or net saving is verified. Evidence deletion needs separate approval.

### F141 — Retired alpha renderer name in the report owner

At local audit head `1eb562f0`, the [paired-CMH report guide](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/README.md)
line 27 says the alpha `render_report_view` dictionary-layout interface is
retired. Lines 22–26 already describe the current template, view, and provider
roles. The [provider](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/provider.py)
at 28–33 and 96–121 uses `render_scientific_html` and returns the current
carrier. A tracked non-audit source/document search found the old symbol only
in that guide; local Git revision `ef321aa1` retains the former source and
migration. This one-line historical note is under review; external readers
were not checked, and no deletion or evidence transfer is approved.

### F142 — Collaborator acceptance repeated in the polish campaign

At local audit head `1eb562f0`, [polish item 29](polish-campaign.md) lines
620–650 marks `EXTENSION-01` as the accepted owner, then states similar
provider/reporter installation, discovery, execution, validation, reporting,
identity, and no-parallel-framework criteria at 634–641 and 643–650. The
[main matrix](backlog_matrix.md) line 70 already owns the accepted checklist.
The polish finding at 626–632 uniquely explains why its sampled composition
test does not prove real entry-point discovery. Its ban on a generic workflow
DSL and test-only production behavior at 638–639, plus the versioned-interface,
bounded Step 09/optional Step 10, and no-conformance-service limits at 647–649,
need a destination check before any reduction. Acceptance lines 634–650 form
a 17-line overlap; a shorter routed account could save about ten lines only
after those unique limits transfer. The 31-line section is not a saving estimate.

### F143 — Unrouted reporting run-contract example

**Dismissed for DOCS-01 at `a3b741bb`.**
At local audit head `1eb562f0`, the eight-line
[run-contract example](../../configs/artifact_run_contract.example.json) has no
filename-specific non-audit Markdown link or call site found. The
[config guide](../../configs/README.md) lines 7–16 groups other `.example.*`
files, and 391–394 generically mentions artifact/report examples. The
[coordinator projection](../../src/emrys/contracts/orchestration/projection.py)
at 101–127 now constructs the six-field reporting run contract; its current
validation belongs to [artifact identity](../../src/emrys/contracts/artifacts/_artifact_contracts/identity.py)
at 22–40. The example's canonical component hash matches its five components
in a static standard-library calculation. The
[artifact-index owner](../../src/emrys/reporting/_artifact_index/README.md)
at 3–7 describes direct indexing as private. No external-reader inventory or
example-file usage was established; neither deletion nor an eight-line saving
follows from the missing filename route.

### F144 — Shared-runtime replacement repeated in adjacent recovery cases

At local audit head `f91b8303`, [Troubleshooting](../operations/TROUBLESHOOTING.md)
lines 161–163 say `--replace` accepts only an existing shared selection from
the same source Project. The adjacent “Runtime inventory already exists” case
at 165–169 repeats that restriction while adding fresh verification and a
separate migration/recovery boundary. [Onboarding](../../src/emrys/orchestration/run_coordinator/onboarding.py)
at 2121–2128 and 2231–2239 implements the refusal; the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
at 326–335 and [Runbook](../operations/RUNBOOK.md) at 643–654 route the
full replacement. The two headings are independently searchable recovery
cases: one gives the shared-source replacement action; the other handles an
existing inventory, fresh verification, and migration/refusal. The same-source
restriction helps at each entry point. This concern is dismissed: nine lines
are combined context, not a useful saving. Preserve old/partial evidence.

### F145 — Downstream reporting role repeated in stage contracts

At local audit head `f91b8303`, five stage contracts repeat a two-line
downstream-consumption bullet immediately after their unique artifact-adapter
lists: [GTF to BED12](../../src/emrys/stages/gtf_to_bed12/CONTRACT.md) 91–92,
[STAR index](../../src/emrys/stages/star_index/CONTRACT.md) 117–118,
[STAR alignment](../../src/emrys/stages/star_alignment/CONTRACT.md) 127–128,
[canonical BAM](../../src/emrys/stages/canonical_bam/CONTRACT.md) 172–173,
and [FASTA sidecars](../../src/emrys/stages/fasta_sidecars/CONTRACT.md) 121–122.
The [architecture inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
at 18 routes shared reporting ownership; the
[reporting guide](../../src/emrys/reporting/README.md) at 10–20 describes
summary and report operations, while the
[artifact-index owner](../../src/emrys/reporting/_artifact_index/README.md)
at 30–36 binds artifact inputs. The local adapter IDs, reporting consumer
edges, and no-rerun promise belong beside each stage; generic reporting
guidance cannot replace those named edges. This concern is dismissed: ten
repeated physical lines do not establish useful compression.

### F146 — Scale-probe interpretation in the current coordinator contract

At local audit head `cc5c1f58`, the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
at 950–953 states current graph sharing, worker decoding, exact-byte rechecks,
and the absence of a shared mutable Attempt-manifest evidence cache. The link
and summary of the dated
local Attempt-manifest scale probe span 953–955; line 953 also finishes the
current no-cache rule. The
[evidence record](../history/validation-evidence.md#immutable-attempt-manifest-scale-probe)
at 153–174 already holds the measurement method, before/after values, and
limits. [Graph construction](../../src/emrys/workflow/Snakefile) at 217–250
and [task admission](../../src/emrys/orchestration/run_coordinator/task.py)
at 334–355 support graph/worker admission;
[inspection](../../src/emrys/orchestration/run_coordinator/_inspection_attempts.py)
at 137–160 and [reuse](../../src/emrys/orchestration/run_coordinator/control.py)
at 523–543 independently reload evidence. A pure canonical-validation cache
in the [contract API](../../src/emrys/contracts/orchestration/api.py) at
720–747 is a different boundary. The linked two-sentence interpretation
explains why the current no-cache rule matters and refuses a speedup claim;
measurements remain in history. This concern is dismissed: no unnecessary
history or saving was found.

### F147 — Computation scope in the contract-golden guides

**Dismissed for DOCS-01 at `27844f15`.**
At local audit head `cc5c1f58`, the
[contract-integration index](../../tests/contract_integration/README.md)
at 6–7 calls its goldens “computational examples,” and the
[golden guide](../../tests/contract_integration/independent_contract_goldens/README.md)
at 8–10 says they characterize “serialization and computation.” The current
[direct cases](../../tests/contract_integration/independent_contract_goldens/test_independent_contract_goldens.py)
at 178–277 protect literal schemas, headers, canonical JSON/TSV, receipt
projection, and rendered scientific/evidence HTML. Its
[rendering input](../../tests/contract_integration/independent_contract_goldens/report_html_input.json)
at 25 points to a prewritten incomplete Run summary, not a computed Step 09
result. The [test baseline](../design/TEST_BASELINE.md) at 63–65 separately
routes Step 09 statistics and estimability to the
[CMH oracle](../../tests/analyses/paired_cmh_candidate_ranking/test_step_09_cmh_oracle.py).
The guide names rendered-report digests at lines 3–6 and expressly excludes
runtime and biological evidence at 8–10. HTML rendering is computation; these
words do not claim Step 09 numerical coverage. The separate oracle route makes
the boundary clear enough without added prose or a useful reduction.

### F148 — Repeated synthetic-fixture guidance in three nested indexes

At local audit head `cc5c1f58`, the [artifact-fixture index](../../tests/contracts/artifacts/fixtures/README.md)
at 3–7, [historically named schema fixture guide](../../tests/contracts/artifacts/fixtures/artifact_schema_v2/README.md)
at 3–8, and [valid-example guide](../../tests/contracts/artifacts/fixtures/artifact_schema_v2/valid/README.md)
at 3–8 restate current-schema, reviewed synthetic-input, and evidence-limit
guidance across 17 physical content lines. The parent routes artifact and
receipt fixtures to the contract tests; the middle explains that its directory
name is historical; the leaf names exact examples and bars expectations
generated from production serializers. These are distinct parent,
historical-directory, and valid-example routes, with independent-oracle
limits at the leaf. This concern is dismissed: the 17-line combined scope
did not establish useful compression or authorize fixture/test changes.

### F149 — Watch selection correction repeated across CV cards

At local audit head `a3310af6`, [CV-U13](cluster_verification_backlog.md)
at 914–924 records the September 18 correction to one bounded admitted
request/Run inventory and an explicit picker. [CV-U31](cluster_verification_backlog.md)
at 1985–1992 restates associated Runs, distinct requests, and shared watch
and inspect selection; [CV-U32](cluster_verification_backlog.md) at 2038–2049
restates Projects-home request/Run enumeration, bounded refusal, and no
scheduler query. The current selection contract is in the
[coordinator owner](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
at 56–67; the [operator route](../operations/RUNBOOK.md) is at 39–59. These
cards retain different requests and defects: Project selection, multiple
requests for one Run, and Projects-home discovery. Their corrections add
different edge cases, local checks, and pending hosted/Viking acceptance.
This concern is dismissed: the 31 combined lines are dated card context, not
a verified saving. Shared final behavior does not merge those records.

### F150 — Named Init review roster repeated in adjacent CV cards

**Dismissed after recheck at `a3b741bb`.**
At local audit head `a3310af6`, [CV-U02](cluster_verification_backlog.md)
at 315–321 and adjacent [CV-U03](cluster_verification_backlog.md) at 339–343
both state the September 21 normal-review roster: strand, comparison/target,
five paired-CMH values, background state/maximum, and three STAR values, with
sample paths/assignments under verbose. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
at 202–207 already owns that current boundary. Repetition centers on CV-U02
315–319 and CV-U03 339–342, not their entire 12-line surrounding span. A
shorter cross-reference might be possible, but no saving is established.
CV-U02's concise-versus-verbose outcome and CV-U03's Init summary and Validate
pass/fail acceptance remain different; retain their dated refinement and
pending hosted/Viking checks.

### F151 — Synthetic artifact inventory example without a named owner route

**Dismissed for DOCS-01 at `1db7a88d`.**
At local audit head `a3310af6`, the 75-line
[artifact inventory example](../../configs/artifact_inventory.example.tsv)
contains 74 synthetic rows. The [config inventory](../../configs/README.md)
at 15 and 391–394 offers only a generic specialist-example route, not this
filename or its owner. A tracked filename search found callers only in
[profile tests](../../tests/orchestration/run_coordinator/test_profile.py)
at 25 and 309–322, [artifact-contract tests](../../tests/contracts/artifacts/test_artifact_schema_contracts.py)
at 31 and 559–585, and the [report fixture builder](../../tests/reporting/fixtures/artifact_adapters_v1/build_fixture.py)
at 38 and 192–202. All 74 example source paths use the absent
`tests/fixtures/artifact_schema_v1/source/` prefix, which that builder
deliberately rewrites to generated fixture sources at 993–1008. Current Run
inventory instead projects rows from admitted profile templates in
[orchestration projection](../../src/emrys/contracts/orchestration/projection.py)
at 116–129 and [artifact inventory](../../src/emrys/contracts/orchestration/artifact_inventory.py)
at 211–269. The file feeds adapter-roster, inventory-validation, and
reporting-fixture checks. It is an active fixture, not duplicate documentation
prose; preserve its rows, order, and test roles. External readers remain
unverified.

### F152 — Local profile promise in the config inventory

At local audit head `a3310af6`, [config inventory](../../configs/README.md)
line 14 describes `execution_profile*.yaml` as local or Slurm examples. The
only two tracked matches, [generic](../../configs/execution_profile.example.yaml)
at 7–8 and [Viking](../../configs/execution_profile.csu_viking_ev_pum1.yaml)
at 47–48, both select `kind: slurm`. The packaged
[direct default](../../src/emrys/orchestration/run_coordinator/resources/default_execution.yaml)
at 42–43 sits outside that glob; the config guide at 359–362 already explains
direct Project creation. This is one inventory-line wording/route drift, not a
missing direct-execution feature or permission to change profiles.

### F153 — Schema owner rules repeated in version indexes

At local audit head `a3310af6`, the
[orchestration schema index](../../src/emrys/contracts/schemas/orchestration/README.md)
at 3–17 names the v1/v2/v3 resource roles, common version rules, and the
canonical-validation owner. The linked [v1](../../src/emrys/contracts/schemas/orchestration/v1/README.md)
at 3–12, [v2](../../src/emrys/contracts/schemas/orchestration/v2/README.md)
at 3–8, and [v3](../../src/emrys/contracts/schemas/orchestration/v3/README.md)
at 3–9 repeat parts of that roster and owner rule across 23 content lines.
Preserve v1's Draft 2020-12 and packaged-resource distinction, v2's scientific
Attempt receipt independent of reporting, and v3's declared-versus-resolved
resource policy. These semantics differ from F96's unrouted artifact notes;
only a brief owner/back-link formula repeats. This concern is dismissed: the
23-line combined scope did not establish useful compression.

### F154 — Runtime inventory mechanics in the Runbook

**Dismissed for DOCS-01 at `1db7a88d`.**
At local audit head `3ea9c2b1`, the [Runbook](../operations/RUNBOOK.md)
lines 353–363 explain approval, freshness checks, and the 12-path,
two-column inventory. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 153–159 owns preview, confirmation, freshness, and publication; the
[runtime owner](../../src/emrys/evidence/runtime_availability/README.md)
lines 8–15 owns exact inventory columns and checks. The brief operator text
at the discovery command explains consent, freshness, no-install behavior,
and inventory meaning; no useful reduction was found. Preserve `--execute`,
success and path, and eight-column migration/recovery at 365–369. This is
distinct from F22's cross-owner overlap and F23's Init detail.

### F155 — Runtime diagnostic contents in Troubleshooting

At 171–179, the [Troubleshooting guide](../operations/TROUBLESHOOTING.md)
summarizes `runtime_check_failed` diagnostic contents in plain English. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
at 350–357 specifies the same concepts. Retain the useful summary, event name
as a log-search route, exact maintenance-log and scheduler-stderr paths,
the difference between installation and qualification, log preservation, and
`emrys doctor --verbose` for current checks.
The content summary at 173–174 helps operators read that log. This concern is
dismissed: no unnecessary detail or saving was established. F07 and F126
address different Doctor claims.

### F156 — Substitution regression narration in the coordinator contract

**Dismissed for DOCS-01 at `27844f15`.**
The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1021–1027 correctly retains exact-byte/device/inode checks and the
trusted-workspace, recycled-inode, and same-UID limits. Its test-specific
clause at 1025–1027 repeats the distinct-inode regression ceiling in the
[coordinator test guide](../../tests/orchestration/run_coordinator/README.md)
line 14 and [CV-10](cluster_verification_backlog.md) lines 2968–2979. The
[test source](../../tests/orchestration/run_coordinator/test_lifecycle.py)
lines 3088–3131 exercises a distinct-inode equal-byte substitution. The
contract's two-sentence evidence limit prevents that regression from implying
ownership proof after inode recycling, and CV-10 delegates the lasting trust
boundary to this owner. Retain the accepted limit and required observations;
the apparent two-line overlap offers no useful reduction. No test or
filesystem fault was run here.

### F157 — CV-U33 current usage policy beside correction evidence

**Dismissed after recheck at `71ac2272`.**
The [CV-U33 card](cluster_verification_backlog.md) lines 2095–2098 repeat
selected-cluster terminal accounting and local-only live `sstat` limits held
by [SCHED-USAGE-01](backlog_matrix.md) line 88, the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 594–602, and the [Runbook](../operations/RUNBOOK.md) lines 90–94.
Preserve the card's original request and September 17 negative finding at
2073–2080, its September 18 correction at 2082–2093 with exact-root,
unknown usage, and display rules, its focused-check account, and pending
hosted and institutional accounting/display acceptance. The surrounding
21-line span at 2082–2102 contains that distinct evidence; its length is not
a saving estimate. The concise current-scope paragraph also explains the
card's pending acceptance; a useful reduction is not established. No scheduler command ran.
F149 covers watch selection across other CV cards, not this usage policy.

### F158 — Campaign delivery prose beside the closure checklist

At `3de8366b`, [CV charter](cluster_verification_campaign.md) lines 128–133
restate the [main checklist](backlog_matrix.md#cluster-verification-closure-checklist)
at 125–140 despite charter links at 70 and 154–155; a one-line route might
save five lines. Closure criteria at 173–190 also repeat checklist mechanics;
the [completion recheck](docs-01-discoveries-sixth.md#completion-criteria-recheck-for-f158-at-3de8366b)
separates unique rules and estimates 8–11 more conditional lines. Retain
CV-01 and site combinations at 135–142 and E01–E12 at 88–124. Neither saving
is verified; retirement and evidence deletion need separate authority.

### F159 — Polish integration genealogy repeated in its introduction

At local audit head `688f7117`, [polish campaign](polish-campaign.md) lines
109–118 repeat PR #140/#148/#169 integration and run `34306975901` already
recorded in the [main matrix](backlog_matrix.md) at 340–355 and later campaign
dispositions. Opening 68–76 retains a distinct tested tree, hosted run
`34301289787`, and the [merged-work map](polish-campaign.md#existing-capabilities-and-overlapping-work).
This is distinct from F16's tables, F90's completed tooling sections,
F97's former selection order, and F140's generic policy list.

Preserve the exact audit/test-tree identity at 68–69 (local Git gives
`2fb8f5ef` and `8034c211` the same tree), item 22's “linked above” CI
reference at 532–533, and the no-new-test/hosted limit at 77–79. Retain source
baseline, pass changes, and original test provenance at 37–66. The
CS-20/22 correction and exact hosted revision at 117–118 recur at 286–293;
retain that evidence and 119–120's remaining-owner boundary. Item 22 at
532–533 says “run linked above”; keep its exact `34306975901` target, not the
different run at 73. A direct item-22 link and up to two bridging lines could
save 7–9 net lines; no draft, reflow, or link check verifies that estimate.
No CI or product test ran in this audit.

### F160 — Accepted follow-up scope repeated in the polish introduction

At local audit head `60ec53e1`, [polish campaign](polish-campaign.md) lines
22–33 has a “Current follow-up scope” section. Lines 24–32 enumerate the same
seven accepted cards, 600-line and 25% targets, and non-cluster-closure status
as the [main matrix](backlog_matrix.md#maintainability-and-release) lines 54–71.
The matrix at line 58, [cluster campaign](cluster_verification_campaign.md)
lines 78–80, and [repository decision](../design/decisions/repository-and-delivery.md)
line 64 link to the heading. Lines 32–33 also preserve the distinct
novice-guide/INIT-01–03 pre-closure tranche. Preserve all three links and that
separate cluster boundary; the matrix remains the sole status authority.
The ten-line span might yield five to six net lines with a four-to-five-line
local route; no drafted or verified saving exists.

### F161 — Final resource summary repeated in the configuration guide

**Dismissed after recheck at `a3b741bb`.**
At local audit head `22972af4`, the [configuration guide](../../configs/README.md)
lines 381–389 closes with a Slurm/tool resource section. Its coordinator-policy
route repeats lines 235–237 and 275–279; allocation-aware shares appear at
281–287 and the native-control owner route at 346–350. Its warning that
declarations are not measured utilization/performance echoes the no-saturation
and planning-minimum limits at 285–286 and 326–328. The
[CV-U06](cluster_verification_backlog.md) line 458 calls this heading “HPC
resource research”; the target routes onward to the primary profile contract
and the [Runbook benchmark procedure](../operations/RUNBOOK.md#resource-benchmarking).
The label is broad, but no broken route or useful reduction is established.
[F123](docs-01-discoveries-fourth.md#f123-repeated-stage-resource-defaults-in-the-configuration-guide)
covers the separate stage-default table.

### F162 — Synthetic E2E help overstates one-Run parity

At local audit head `f2e719c0`, the [test driver](../../tests/tools/real_synthetic_e2e.py)
line 2 promises real-tool direct/Slurm parity on “one synthetic EMRYS Run”;
`build_parser()` at 163–165 exposes that sentence as command help. Profile 130
selects separate direct and Slurm workspaces at 251–254, then admits and
completes a Run in each before comparison at 2126–2185. Its distinct two- and
three-Attempt histories are stated in the [test-tool guide](../../tests/tools/README.md)
lines 11–20. Profile 100000 selects only Slurm at 251–254 and returns no
direct comparison at 2184–2187. The blanket help description misstates both
profile scopes; it establishes no failure of either test. No driver or CI ran.

### F163 — Optional worker threads shown as required

At local audit head `f2e719c0`, four internal shell-worker usage blocks show
unbracketed `--threads THREADS`: [FASTA sidecars](../../src/emrys/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh)
lines 10–21, [duplicate marking](../../src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh)
lines 10–21, [SplitNCigar](../../src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh)
lines 10–21, and [BAM QC](../../src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh)
lines 9–17. Their required-argument declarations omit threads and each parser
sets `threads=1`; the respective owner contracts state the omitted default
(FASTA 56, duplicate 43, SplitNCigar 45, BAM QC 142). The usage layout can
imply the option is required, although these are internal runner workers.
No shell worker was run; execution and resource-policy behavior are untested.

## Additional reviewed overlaps without a saving claim

The [Runbook](../operations/RUNBOOK.md) lines 106–111 repeats palette and
log-styling detail from the [logging contract](../design/LOGGING_CONTRACT.md)
lines 57–64 and [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 628–635. Its Watch legend may help operators, and plain/`NO_COLOR`
labels remain important; no useful reduction was established. The
[Troubleshooting guide](../operations/TROUBLESHOOTING.md) lines 222–240 keeps
the distinct `/local/tmp` and `memory_mb: null` site-evidence limits. A full
coordinator-contract reread found no separate compression beyond recorded rows.

The [polish capability inventory](polish-campaign.md) lines 976–982 records
what already existed at its dated audit. Current owner, operator, test, and CI
routes cover those mechanisms, but the negative baseline explains selection.
It belongs with [F16](docs-01-discoveries.md#f16-polish-merged-pr-tables)'s
overlap review; this pass found no separate deletion or saving.

The configuration guide's guided-Init account at lines 77–94 overlaps the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 103–124, but Project authors may need its strandedness, comparison,
default, and inactive-background explanation. No safe saving was established.
All 49 test/fixture READMEs were reread against selected source and CI; F28,
F69, F82, F107, and F147 retain their stated evidence limits. F77/F78's
indexes made no complete-roster claim. A static eight-word paragraph screen
of 1,382 longer prose paragraphs flagged 95 cross-file pairs; short and
paraphrased repetition was outside that scan. The exact four-line Java thread
rule at [Step 04](../../src/emrys/stages/duplicate_marking/CONTRACT.md) 43–46
and [Step 05](../../src/emrys/stages/split_n_cigar/CONTRACT.md) 45–48 serves
two separate stage contracts; no extra useful reduction was established.

## Current static link check

At local head `7d29a132`, a standard-library scan of all 176 tracked Markdown
files inspected 1,837 inline-link and reference-definition destinations outside
backtick fences. No local file target or Markdown heading anchor was missing.
The extraction is narrower than the repository's CommonMark-based checker;
no dependency installation, product command, or CI ran.

At the same head, full read-only rereads of the 734-line Runbook, 271-line
Troubleshooting guide, and 1,248-line coordinator contract found no additional
high-confidence documentation issue. F09's reader-order effect remains untested;
F31's older-install recovery value is not bounded to a fixed release. F21 and
F50 remain source-backed reader/contract discrepancies, while F136 is a narrow
private-helper compression candidate. No command or runtime behavior was tested.

At `f2e719c0`, read-only review of public command help, tracked shell/R and
tool help, and all 34 tracked JSON files found F59's additional help gap and
F162–F163. Twenty schema resource titles matched their IDs/version owners;
the only stale JSON description was already F46. Script and schema behavior
was not executed; no new compression saving was established by this pass.
