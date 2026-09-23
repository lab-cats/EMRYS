# DOCS-01 discovery notes, fifth file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F130–F158. F130–F131 use local audit head `3ebfb2bf`, read on 2026-09-23;
F132–F133 use `935adf06`, F134–F139 use `ebc0012d`, and F140 uses `f239a91d`
on that date. F141–F143 use `1eb562f0`; F144–F145 use `f91b8303` on that
date; F146–F148 use `cc5c1f58`; F149–F153 use `a3310af6`.
F154–F158 use `3ea9c2b1`, read on 2026-09-23.
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
The glossary's unqualified “validate” and “completion” blur native transaction
completion with verified task completion. Staged checks and receipt-last order
remain real; a native receipt alone is not verified-task proof. No runtime or
reporting defect follows from this glossary wording.

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

The [architecture guide](../architecture/ARCHITECTURE.md) line 54 calls all
fourteen owners in the built-in path “scientific.” Its responsibility table at
lines 41–43 separates scientific stages/analyses from operational evidence,
and its phase table at lines 64–68 calls alignment evidence non-gating. The
[stage map](../../src/emrys/contracts/STAGE_MAP.md) lines 19–34 lists fourteen
identities: ten stages, two analyses, and two evidence collectors (canonical
BAM QC and RSeQC orientation). The total is accurate, but the adjective blurs
the guide's own evidence boundary. This is a reader-label ambiguity only; it
does not show a graph, scheduling, or scientific-result defect.

### F134 — CV-25 implementation account beside current log owners

The completed [CV-25 card](cluster_verification_backlog.md#cv-25-log-discovery-and-readable-output)
lines 3689–3746 spends roughly 58 lines on the Task-log, started-stream, and
Run-selected log-discovery implementation and verification sequence. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 532–555, 663–671, and 1184–1196 owns current log-root precedence,
association, Task-log admission, and diagnostic limits; the [Runbook](../operations/RUNBOOK.md)
lines 17–37 gives the operator's selected-Run route. The CV card mixes current
mechanics with dated test and CI genealogy. Its original E01–E06 discovery
need, explicit-identity/no-guessed-latest acceptance, hosted-only Completed
disposition, historical Attempt/start limits, and separate institutional and
retirement boundaries remain evidence. This is a placement review, not a
verified 58-line saving or permission to delete the record.

### F135 — CV-24 repeats the current watch action protocol

The [CV-24 card](cluster_verification_backlog.md#cv-24-run-center-actions)
lines 3639–3661 describes `p`/`b`/`s` handoffs, fresh planning, refusal of
noninteractive actions, and Slurm's concurrent-resume caveat. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 644–661 owns that exact present behavior, and the
[Runbook](../operations/RUNBOOK.md) lines 121–137 gives the operator keys and
commands. The card's selected three-action disposition, fixture/CI evidence,
new-analysis choice at lines 3663–3672, hosted-only completion, and separate
CV-16/institutional and dashboard-retirement acceptance remain distinct.
Only the repeated current-protocol prose is a compression review surface;
no safe saving is established.

### F136 — Private planning-helper narration in the coordinator contract

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 852–858 states the public planning composition, then names private
`_tasks` and `_task_commands` helpers and their caller's three local results
at 854–857. [Materialization source](../../src/emrys/orchestration/run_coordinator/materialization.py)
lines 328, 891, and 1042–1059 confirms the implementation; the
[coordinator index](../../src/emrys/orchestration/run_coordinator/README.md)
lines 29–40 already maps `materialization.py` to planning. The helper names
have no evident public or recovery role. Preserve the planning contract and
special path, command, and resource guarantees around this four-line span;
no deletion is approved or measured here.

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
[REDUCE-01 row](backlog_matrix.md) line 66 owns behavior classification and
accounting for that accepted work. The campaign's tooling-only footprint
exception at lines 98–101 and separate-selection warning at 13–20 remain
specific, as does its dated source audit at 35–80. This 21-line scope is a
review surface, not a verified saving or permission to remove evidence.

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
test does not prove real entry-point discovery. The versioned-interface,
bounded Step 09/optional Step 10, and no-conformance-service language at
647–649 also needs a destination check before any reduction. The 31-line
section is a review span, not a verified saving or permission to discard
evidence.

### F143 — Unrouted reporting run-contract example

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
full replacement. These nine lines are a review span, not a verified saving.
The two failure headings may need independent instructions; preserve the
existing-inventory refusal, Doctor inspection, fresh generation verification,
old/partial evidence, and explicit migration/recovery rule.

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
at 30–36 binds artifact inputs. This ten-line review span is not
a verified saving: the stage-specific adapter IDs and consumer edges remain,
and readers must still find the promise that reports do not rerun stages.

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
720–747 is a different boundary. Review only the historical summary
within that mixed span; the safety rules and link to retained evidence remain
useful. No transfer, deletion, or saving is established.

### F147 — Computation scope in the contract-golden guides

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
“Computation” could mean HTML rendering, but the broad labels leave the
numerical boundary unclear. Preserve the literal and rendering protections;
no test failure or biological proof follows from this wording.

### F148 — Repeated synthetic-fixture guidance in three nested indexes

At local audit head `cc5c1f58`, the [artifact-fixture index](../../tests/contracts/artifacts/fixtures/README.md)
at 3–7, [historically named schema fixture guide](../../tests/contracts/artifacts/fixtures/artifact_schema_v2/README.md)
at 3–8, and [valid-example guide](../../tests/contracts/artifacts/fixtures/artifact_schema_v2/valid/README.md)
at 3–8 restate current-schema, reviewed synthetic-input, and evidence-limit
guidance across 17 physical content lines. The parent routes artifact and
receipt fixtures to the contract tests; the middle explains that its directory
name is historical; the leaf names exact examples and bars expectations
generated from production serializers. Those reader and independent-oracle
rules need to survive any compression. The span is not a measured net saving,
and no fixture or test change is authorized by this audit.

### F149 — Watch selection correction repeated across CV cards

At local audit head `a3310af6`, [CV-U13](cluster_verification_backlog.md)
at 914–924 records the September 18 correction to one bounded admitted
request/Run inventory and an explicit picker. [CV-U31](cluster_verification_backlog.md)
at 1985–1992 restates associated Runs, distinct requests, and shared watch
and inspect selection; [CV-U32](cluster_verification_backlog.md) at 2038–2049
restates Projects-home request/Run enumeration, bounded refusal, and no
scheduler query. The current selection contract is in the
[coordinator owner](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
at 56–67; the [operator route](../operations/RUNBOOK.md) is at 39–59. The
31 combined physical lines are a review span, not a saving estimate. Preserve
each card's separate operator request and status, the September 17 defect
explanations, Projects-home and 256-target limits, exact scheduler diagnostics,
focused-check scope, and pending hosted/Viking acceptance. A shared final
behavior does not make those evidence histories interchangeable.

### F150 — Named Init review roster repeated in adjacent CV cards

At local audit head `a3310af6`, [CV-U02](cluster_verification_backlog.md)
at 315–321 and adjacent [CV-U03](cluster_verification_backlog.md) at 339–343
both state the September 21 normal-review roster: strand, comparison/target,
five paired-CMH values, background state/maximum, and three STAR values, with
sample paths/assignments under verbose. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
at 202–207 already owns that current boundary. The 12 physical lines are a
review span, not a saving estimate. CV-U02's concise-versus-verbose outcome
and CV-U03's Init summary and Validate pass/fail acceptance remain different;
retain their dated refinement and pending hosted/Viking checks.

### F151 — Synthetic artifact inventory example without a named owner route

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
reporting-fixture checks; its rows and order need preservation review.
External readers and safe relocation or reduction are unverified. Seventy-five
lines are review scope, not a saving estimate.

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
resource policy. These current semantics are different from F96's unrouted
artifact-version notes. The span is not a verified net saving.

### F154 — Runtime inventory mechanics in the Runbook

At local audit head `3ea9c2b1`, the [Runbook](../operations/RUNBOOK.md)
lines 353–363 tell the operator how to approve runtime discovery, then
describes in-memory freshness checks and the 12-path, two-column inventory
policy. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 153–159 owns preview, confirmation, freshness, and publication; the
[runtime owner](../../src/emrys/evidence/runtime_availability/README.md)
lines 8–15 owns the inventory columns and derived checks. The six Runbook
lines at 355–356 and 360–363 are a review span, not a verified saving.
Preserve the operator's consent/refusal, `--execute`, success message and path,
no-install boundary, and eight-column migration/recovery at 365–369. This is
distinct from F22's cross-owner overlap and F23's Init detail.

### F155 — Runtime failure field roster in Troubleshooting

The [Troubleshooting guide](../operations/TROUBLESHOOTING.md) lines 171–179
lists `runtime_check_failed` field names that the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 350–357 already owns. Retain that event name as a log-search route, the
exact maintenance-log and scheduler-stderr paths, package-versus-qualification
distinction, log preservation, and `emrys doctor --verbose` for current checks.
The field enumeration at 173–174 is a small review span, not a proved saving or
reason to weaken recovery. F07 and F126 address different Doctor claims.

### F156 — Substitution regression narration in the coordinator contract

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1021–1027 correctly retains exact-byte/device/inode checks and the
trusted-workspace, recycled-inode, and same-UID limits. Its test-specific
clause at 1025–1027 repeats the distinct-inode regression ceiling in the
[coordinator test guide](../../tests/orchestration/run_coordinator/README.md)
line 14 and [CV-10](cluster_verification_backlog.md) lines 2968–2979. The
[test source](../../tests/orchestration/run_coordinator/test_lifecycle.py)
lines 3088–3131 exercises a distinct-inode equal-byte substitution. Roughly
two lines are under review; the contract's accepted residual limit and
required observations must remain. No test or filesystem fault was run here.

### F157 — CV-U33 current usage policy beside correction evidence

The [CV-U33 card](cluster_verification_backlog.md) lines 2082–2102 repeats
current exact-root `sstat`/`sacct`, selected-cluster, unknown-usage, and
display rules held by [SCHED-USAGE-01](backlog_matrix.md) line 88, the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 594–602, and the [Runbook](../operations/RUNBOOK.md) lines 90–94.
Preserve the card's original request and September 17 negative finding at
2073–2080, its September 18 correction and focused-check account, and pending
hosted and institutional accounting/display acceptance. The 21-line span is
for review, not an estimate of safe removal; this audit ran no scheduler command.
F149 covers watch selection across other CV cards, not this usage policy.

### F158 — Campaign delivery prose beside the closure checklist

The [CV campaign charter](cluster_verification_campaign.md) lines 126–150
repeats much of the [main matrix's closure checklist](backlog_matrix.md#cluster-verification-closure-checklist)
at 125–152 even while routing readers there. Preserve the charter's three
distinct institutional combinations at 135–140, its
[E01–E12 register](cluster_verification_campaign.md) at 88–124, and charter-owned
completion criteria at 11–17 and 173–190. The 25-line span is a placement
review, not a measured saving or authority to retire the campaign or delete
evidence.
