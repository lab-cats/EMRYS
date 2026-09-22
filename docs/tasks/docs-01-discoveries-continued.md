# DOCS-01 discovery notes, continued

This companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F30 onward. Unless a subsection names another revision, source line
references are pinned to `3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`.
These are observations, not accepted changes or a task-status registry.

## Discovery notes

### F30 — Dashboard reporting-stage text

[Dashboard source](../../src/emrys/orchestration/run_coordinator/dashboard.py)
lines 183–202 tells watch readers that reporting uses three dependent
transactions and that a final workflow target follows reporting. Its rule map
at 206–214 retains old reporting aliases; the stage table renders REPORT and
FINAL rows even when unscheduled (1573–1608). Current
[reporting](../../src/emrys/reporting/README.md) lines 3–16 and
`src/emrys/orchestration/run_coordinator/reporting_boundary.py:43–44` define
two publication operations after scientific completion. The
[Snakefile](../../src/emrys/workflow/Snakefile) lines 394–397 ends the backend
at the `cohort_slice` target after verified scientific tasks. That target and
its FINAL row remain meaningful, but reporting does not precede the target.
The dashboard also says “Three dependent reporting transactions” when an
identity has reporting-memory fields (dashboard lines 974–980); its source
test at `tests/orchestration/run_coordinator/test_dashboard.py:439–443`
retains the old `artifact_index`, `run_summary`, and `html_report` keys.
Current reporting instead names `run_summary` and `html_report`. Correct both
user-facing explanations and the test fixture under a separate product
change, preserving old log aliases and current `cohort_slice` mapping
(`test_dashboard.py:362–374`). Scheduler text still cannot prove admitted
Run completion.

### F31 — Historical Slurm username recovery advice

[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 65–72 tells a reader
with Snakemake's `No username set in the environment` to “Update EMRYS to the
submission fix,” without identifying a fixed revision or distinguishing a
current installation. The [backlog incident](backlog_matrix.md) lines 243–252
records the original failure and fix; current
[submission code](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
lines 861–870 preserves four login-name variables, with direct source tests
at `tests/orchestration/run_coordinator/test_slurm_submission.py:2027–2099`.
Keep the incident and safe resume/evidence advice. Current recovery should
first identify the installed revision and actual submission diagnostic;
this audit has not reproduced a current Slurm failure.

### F32 — Mermaid check's stated ceiling

[Documentation test README](../../tests/documentation/README.md) lines 3–8
says cases cover “standalone Mermaid syntax.” The
[checker](../../scripts/documentation/validate_structure.py) lines 235–251
checks only a first nonblank `flowchart` declaration and absence of Markdown
fences; its [tests](../../tests/documentation/test_validate_structure.py)
lines 290–323 exercise those refusals. The
[tool README](../../scripts/documentation/README.md) lines 3–7 correctly
describes declarations and fences but broadly says it checks first headings.
The checker at lines 199–206 checks H1 only for required canonical pages;
other Markdown files receive link checks, not an H1 requirement. Narrow both
guides: this gate does not parse Mermaid grammar or verify rendering.

### F33 — Report receipt version in the scientist diagram

The linked [scientist-facing diagram](../architecture/diagrams/current_user_pipeline.mmd)
line 15 groups summary TSV with two HTML reports and says a validated v4
receipt comes last. [Reporting](../../src/emrys/reporting/README.md) lines
10–16 and 29–49 separates summary JSON/TSVs in the artifact-summary
publication from HTML and `report_outputs.tsv` under Results. The
[artifact schema index](../../src/emrys/contracts/schemas/artifacts/README.md)
lines 3–8 identify artifact entries v4, Run result manifest v8, and report
receipt v8. Correct the diagram's grouping and receipt label without
conflating these separate formats. The diagram is non-authoritative, but it is the
architecture's linked reader path at `docs/architecture/ARCHITECTURE.md:56`.
The same node says “Read-only reporting.” Reporting reads and does not change
the successful scientific Run, but `emrys report --execute` creates absent
owned outputs ([reporting owner](../../src/emrys/reporting/README.md) lines
3–16). Clarify read-only scientific inputs versus create-only report
publication so the diagram does not imply no files are written.
The [test baseline](../design/TEST_BASELINE.md) lines 108–111 also lists
“report read-only behavior” without naming the input boundary. Narrow that
checklist phrase to immutable scientific inputs and create-only report
publication alongside the diagram correction; this is a documentation
ambiguity, not a report transaction defect.

### F34 — Prepared finalization in the reliability diagram

[Reliability diagram](../architecture/diagrams/reliability.mmd) lines 20–22
sends every failed/interrupted Attempt through `emrys resume` to a new
Attempt and Task. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1008–1035 permits a distinct first action: complete an exact prepared
terminal receipt on the existing Attempt. A prepared success starts no new
scientific work; an eligible failed/interrupted outcome may then continue in a
new Attempt. [Troubleshooting](../operations/TROUBLESHOOTING.md) lines 35–50
already explains this. Show both paths without implying that missing or
ambiguous evidence can authorize finalization.

### F35 — FASTQ pairing language

[Glossary](../reference/GLOSSARY.md) lines 45 and 67 says EMRYS does not infer
R1/R2 pairing from filenames. The [engineering guide](../operations/ENGINEERING_CONVENTIONS.md)
lines 18–20 also broadly bans inference of “pairing” from names. Guided Init
does recognize `_R1/_R2` and `_1/_2` mates and displays detected pairs
([onboarding](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 964–1006; [Quickstart](../../quickstart.md) lines 79–81). The operator
still authors condition and biological pairing group at onboarding lines
1010–1016; the [sample manifest guide](../../configs/README.md) lines
144–170 makes those values authoritative. Clarify mate discovery in both
guides versus authored experimental pairing; retain the ban on inferred
biological meaning or sample order. This is ambiguous wording, not a
demonstrated scientific-inference defect.

### F36 — Cross-owner history in runtime test guidance

[Runtime test README](../../tests/evidence/runtime_availability/README.md)
lines 3–13 describes runtime probes, Snakemake startup, and their site limit.
Line 14 then says tests solely for a retired report publisher were removed;
that sentence does not describe a runtime test in this directory. Trace whether
it preserves unique evidence, then keep current runtime test scope here. Place
any durable reporting context with its
actual owner. This is a placement candidate, not permission to discard evidence.

### F37 — BED12 dependency in the scientist diagram

[Scientist diagram](../architecture/diagrams/current_user_pipeline.mmd)
lines 9 and 22 combines canonical BAM QC with RSeQC mechanical orientation
under one inspection node fed only by BAM/BAI. Its legend at line 39 says
arrows are data or contract dependencies. The authoritative
[stage map](../../src/emrys/contracts/STAGE_MAP.md) lines 67–70 requires
BED12 from `convert_GTF_to_BED12` as a second RSeQC input; BAM QC has no
such fan-in. Add the annotation dependency or split the evidence branches.
Do not turn either non-gating evidence branch into a Run completion gate.

### F38 — Slurm request in the reliability diagram

[Reliability diagram](../architecture/diagrams/reliability.mmd) lines 2–6
draws approval straight to Attempt creation. For whole-Run Slurm placement,
the [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 410–418 and 431–449 creates and synchronizes a retained submission
request before `sbatch`; a request can exist before any Run or Attempt. The
[Runbook](../operations/RUNBOOK.md) lines 9–25 gives that request its own
inspection route. Show request/submission and compute-side Run admission as
distinct from direct execution; scheduler status cannot supply Run truth.

### F39 — Validation roster inventory claim

[Contract-integration index](../../tests/contract_integration/README.md)
lines 8–9 says roster expectations cover “every current validator.” The
[roster guide](../../tests/contract_integration/validation_rosters/README.md)
lines 3–6 claims producer inventory coverage. At the pinned revision there
are 16 source `validator.py` owners; the
[roster test](../../tests/contract_integration/validation_rosters/test_validation_check_rosters.py)
lines 23–41 lists 14 grouped validation-report producers. Its inventory
assertion at 84–95 checks that fixed map's paths and discovers only legacy
`scripts/validate_step_*.py`, so a new source-owner validator is not
automatically found. Name the narrower producer scope and maintenance limit;
artifact-contract and sample-manifest validators have different contracts.
The fixed map does cover all 14 currently enumerated validation-report
producers, and literal ordered rosters remain an independent protection.
The public CLI catalog (`src/emrys/__main__.py:44–65,318–333`) also exposes
`all-pass`, artifact-contract, and manifest validation outside those 14.
Retain owner real-output assertions, including Step 10's direct one-row
case at `tests/analyses/paired_cmh_candidate_ranking/scientific_context_projection/test_validator.py:80–99`;
central synthetic roster checks alone cannot establish actual output meaning.

### F40 — Concurrency in the local workflow profile

[Local profile README](../../src/emrys/workflow/profiles/local/README.md)
lines 5–7 says the Execution Plan and Attempt supply “sample concurrency.”
The current [resource schema](../../src/emrys/contracts/schemas/orchestration/v3/resource_config.schema.json)
lines 41–53 defines `stage_concurrency` for repeated stages 01–07, including
cohort partitions; [resource policy](../../src/emrys/orchestration/run_coordinator/resource_policy.py)
lines 37–48 resolves that keyed control. The Snakemake profile sets engine
defaults, not one sample-wide policy. Use the current per-stage term without
promising that any particular allocation will admit every task.

### F41 — Step 05 check's read-only help

[Retained Step 05 check](../../tests/data_checks/validate_step05_outputs.sh)
line 20 calls itself “Read-only validation,” while its own help at 13–18
names a status TSV. Execution creates an output directory, writes/removes a
probe, and writes or replaces the TSV at 75–95. The
[owner README](../../tests/data_checks/README.md) lines 3–7 correctly says
BAM/BAI are not mutated and lists the writes. Narrow script help to read-only
*inputs* and disclose output mutation, including existing TSV replacement.
Do not alter this retained operator check's behavior under DOCS-01.

### F42 — Report transfer in the coordinator test index

[Coordinator test README](../../tests/orchestration/run_coordinator/README.md)
lines 11–20 places report transfer in a table of checks, but that row links a
Runbook procedure, not a repeatable test. The [CV card](cluster_verification_backlog.md)
lines 4079–4090 records the tiny local copy/comparison observation and its
limit. Route this historical command-mechanics evidence to the CV record;
generated-bundle contents, rendering, and institutional transfer remain
pending rather than proved by a coordinator fixture.
The CV card at 4086–4090 names no exact run date, source commit, command
transcript, or retained artifact for that tiny exercise. It is an honest
current evidence home, not yet a source for a date-qualified history transfer.
The [test baseline](../design/TEST_BASELINE.md) line 15 links the test guide's
`#what-the-checks-establish` heading, so keep that section and its real test
rows; reclassify only the transfer row or route it to CV-27 outside the checks
table. Preserve the Runbook transfer anchor, which Quickstart and CV-27 also
use. REPORT-01–03 and CV-27 retain their separate acceptance requirements.

### F43 — Print behavior in the reporting test guide

[Reporting test README](../../tests/reporting/README.md) lines 3–7 says tests
pin “print behavior.” The checked source cases assert print CSS, generated
HTML text, and an SVG height attribute, not browser or PDF layout review.
The [backlog](backlog_matrix.md) lines 291–294 still keeps REPORT-01–04 visual
or layout acceptance pending. Name source-level print rules and generated
structure in the test guide without implying rendered user acceptance.

### F44 — Internal worker command ownership

The opening of the [STAR contract](../../src/emrys/stages/star_alignment/CONTRACT.md)
lines 3–6 calls its producer an explicit repository-path command, which is
literally how the Run invokes it and does not itself promise standalone
support. The [RSeQC contract](../../src/emrys/evidence/rseqc_orientation/CONTRACT.md)
lines 3–8 additionally calls the operation independently runnable, an ambiguous
supported-command claim. Both contracts later call their shells internal Run
workers (STAR lines 65–68;
RSeQC lines 58–61), as do their adjacent READMEs (STAR lines 12–18; RSeQC
lines 11–16). The STAR shell requires runner-supplied `EMRYS_TASK_WORK_DIR`
at lines 3, 22–23, and 51–52; the RSeQC shell does likewise at lines 3,
18–19, and 43–44. Their shell tests supply runner-like paths and assert
refusal without them (`tests/stages/star_alignment/test_step_01_star_align.sh:11,74`;
`tests/evidence/rseqc_orientation/test_step_03_infer_strandedness_and_orientation.sh:11,77`).
That establishes the internal interface, not supported standalone publication
or recovery. Clarify the RSeQC opening while retaining explicit script paths,
direct `--help`, and public grouped validators.
The coordinator's `TaskBackend` and `CommandResult` docstrings
([task source](../../src/emrys/orchestration/run_coordinator/task.py) lines
100–104 and 146–154) also call delegated producer and validator commands
“public.” This is the definite ownership error. Call them delegated/recorded
commands while retaining exact argv and exit evidence and Run-owned publication.
The [public-CLI tests](../../tests/test_public_cli_contracts.py) lines 113–154
also group ten shell workers as entry points and label three nonexecutable
scripts `INTERPRETER_ONLY_SHELL_DEFECTS`; lines 829–865 call their modes
“public shell” defects. The [stage index](../../src/emrys/stages/README.md)
lines 30–39 and RSeQC, duplicate-marking, and split-N-cigar contracts instead
classify these producers as internal Run workers. Git records the three modes
as `100644`, but that alone does not make them defects in a public CLI. Review
the test classification and names against supported command ownership;
preserve useful `--help`, arbitrary-working-directory, missing-argument,
file-mode, argv, and exit protections. No test removal follows from this
wording question.

### F45 — Watch and stop in the command-audience map

The [functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
lines 22–29 maps commands to audiences but omits `watch` and `stop`. Both
commands are registered in the public parser
([CLI](../../src/emrys/__main__.py) lines 275–288); the
[Quickstart](../../quickstart.md) lines 176–185 teaches `watch` to scientists,
and the [Runbook](../operations/RUNBOOK.md) lines 139–157 teaches exact-request
`stop` to operators. The inventory says `emrys --help` owns the complete
roster, so this is an audience-routing gap rather than a false claim about
command existence. Its opening at lines 3–4 already says the inventory is
selective, so a nonexhaustive label adds little. Add these audience examples,
preserving `stop`'s exact-request and evidence ceilings.

### F46 — Artifact common-schema description

The public [common artifact schema](../../src/emrys/contracts/schemas/artifacts/v1/common.schema.json)
line 5 describes definitions for “artifact-schema-v1 record contracts.” Its
[owner README](../../src/emrys/contracts/schemas/artifacts/v1/README.md)
lines 3–5 says active schemas still use these definitions after record schemas
moved to later versions. The [registry](../../src/emrys/contracts/artifacts/_artifact_contracts/schema.py)
lines 68–74 loads this file with current records, whose [index](../../src/emrys/contracts/schemas/artifacts/README.md)
lines 3–8 names artifact entries v4, Run manifest v8, and report receipt v8.
Only the description is stale: the common file's v1 `$id` and title remain
correct resource identities. Current record schemas still reference that `$id`,
and [schema rules](../../src/emrys/contracts/schemas/README.md) lines 8–16
distinguish directory/resource versions from record-format versions. The
independent golden pins the common `$id` at
`tests/contract_integration/independent_contract_goldens/schema_contracts.json:17–20`.
Correct the description only after schema-byte compatibility review; do not
rename the v1 file, directory, `$id`, or references. The README calls those
bytes a public contract; this is no evidence of a validator defect.

### F47 — R-probe concurrency candidate after CV-26

The [optimization campaign](optimization_campaign.md) lines 292–319 still
proposes comparing bounded concurrency of independent R namespace probes.
The [CV-26 record](cluster_verification_backlog.md) lines 3949–3987 already
retains a four-trial serial/two-worker hosted steady-ready comparison and a
decision to retain serial checks: a one-CPU profile is supported, diagnosis
has no admitted concurrency budget, and concurrent-child cancellation is not
owned. The campaign links CV-26 for a different source reduction, so this is
a candidate-selection context gap, not proof that a new resource-aware study
is forbidden. Link the measured disposition at the proposal before any new
selection; complete Doctor-path attribution and cancellation proof remain open.

### F48 — Project name lookup from the repository root

The [root guide](../../README.md) lines 77–79 says an operator outside a
Project root can select it with `--project NAME_OR_PATH`. The
[selector](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 270–285 resolves a bare name relative to the current directory; the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 35–37 promises no parent or global lookup. The source test at
`tests/orchestration/run_coordinator/test_onboarding.py:1929–1954` pins that
boundary. From the Quickstart's repository root, `--project pum1-study` does
not select its `Projects/pum1-study` child. Explain when a bare name works and
show `--project Projects/pum1-study` from that root or an exact absolute path.
This is a guide correction, not a proposed new discovery behavior.
Saved `EMRYS_PROJECTS_ROOT` affects named Init's destination
(`onboarding.py:1261–1269`) and the outside-Project picker, but the exact
Project selector at `onboarding.py:270–285` does not consult it. The
[Runbook](../operations/RUNBOOK.md) lines 294–301 already gives an absolute
`project.yaml` example for Project-aware commands. Keep that distinction in
the root route rather than promising a global name lookup after setup.

### F49 — Incomplete allocation-recovery command

[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 222–225 tells a
reader with a rejected allocation or scratch path to preview the submission
with only `--verbose </dev/null`. This fragment names neither an `emrys`
operation nor its Project/Run selector. `--verbose` belongs to the relevant
leaf parser; the failed submission may be Run, resume, report, or Doctor
repair. The [control parser](../../src/emrys/orchestration/run_coordinator/control.py)
lines 1800–1868 shows command-specific controls. Give a complete no-write
example for the intended operation or tell the reader to repeat its exact
preview command with `--verbose` and no `--execute`. This is an actionability
gap, not a demonstrated parser failure.
The [Runbook](../operations/RUNBOOK.md) lines 441–450 supplies a complete
`emrys run </dev/null` preview. Run, resume, and report each accept
`--execute` (`control.py:1800–1868`); Doctor accepts it only with `--repair`
(`doctor.py:1989–1996,2023–2029`). Redirecting stdin to `/dev/null` does not
undo an explicit `--execute`. Any replacement instruction must name the failed
operation and omit that flag when it promises no writes.

### F50 — Submission-request version in the coordinator contract

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 487–490 describes selected scheduler binding as “v2/v3” and calls new
requests v3. Its own lines 410–424 define new `emrys.submission-request.v4`
requests. The [submission owner](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
lines 54–59 declares v4 current and v3/v4 named requests; lines 110–111,
182–185, and 239–243 require and observe the bound job name for both. A
[source test](../../tests/orchestration/run_coordinator/test_slurm_submission.py)
lines 925–934 likewise exercises both versions. Align the present-tense
inspection wording with v4 while preserving the v2/v3 historical observation
rules. This is a documentation discrepancy, not a request-format migration.

### F51 — Viking walkthrough history in the active backlog

The [main backlog](backlog_matrix.md) lines 182–276 retains the dated Viking
walkthrough inside the active status authority. The
[CV evidence register](cluster_verification_campaign.md) lines 90–117 overlaps
some observations but points back to the backlog for earlier exact evidence.
Backlog lines 191–205 uniquely retain the first checkout, job `614786`,
qualification ID, receipt location, and the approved allowance of up to 750
net additional product lines, with no new product files or receipt formats
and Rich as the terminal library. Lines 223–256 retain jobs `605171`,
`618134`, `618190`, commit `c52178d2`,
node/account/resource observations, and the four login-name variables. Lines
269–276 retain hosted run `34885186045` and its disposable-Slurm ceiling.
This block is not uniformly historical: lines 207–222 state selected/current
head-node Doctor, progress, log, and temporary-file behavior; 235–239 says
the shared capacity observer now applies the approved RAM fallback; 248–251
states the current four-variable submission export. The current owners include
the [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 155–178, 225–253, and 752–765, its adjacent README lines 40–66,
the [Runbook](../operations/RUNBOOK.md) lines 574–639 and 698–722, and
[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 232–242. Current
Viking placement requests an exclusive whole node with `memory_mb: 0`
(`--mem=0`); the older partial-node missing-metadata observation and approved
process-visible RAM fallback are separate historical and capacity-policy
facts. The fallback remains in `capacity.py:141–180`, not evidence that the
older partial-node request is today's Viking default.
The 750-line allowance at 201–205 is bounded by 184–189 to that earlier
slice, not a standing exception for future product growth.
The [history compendium](../history/validation-evidence.md) lines 81–102
already retains job `605171` as manual NORAD Step 08 evidence at exact
`64b14a11`; the backlog adds that job's scheduler request and accounting
context. Preserve these as distinct aspects and do not turn either into an
EMRYS whole-Run proof. History's unchanged-record rule does not permit
appending the later scheduler interpretation to its frozen manual-Step section
just because the job number matches; a qualified new dated record could
cross-link it after provenance is reconstructed.
E04/E09/E12 overlap the synthetic and actual-data observations at 258–267;
preserve operator-report attribution, the cancelled Run without terminal
receipt, and deferred visual review. The `#viking-walkthrough-findings` anchor
has live inbound links from the SITE-PARITY-01 row and CV charter. Map every
fact and both links before any transfer; dated evidence belongs in an
appropriate qualified home, while the backlog retains concise current
acceptance. The charter's closure criteria and backlog's procedure are
complementary, not safely interchangeable.
The first successful manual setup at 191–199 is distinct from the CV register's
E01 failed qualification. Source commits for this backlog block
(`cf9c18ad9`, `4d8c7a059`, `9b439d433`, `1ea21855a`) date documentation
edits, not operator runs. The [CV register](cluster_verification_campaign.md)
lines 90–105 says raw logs and artifacts remain with the operator; its
`f2c0149` is reviewed code, not the exact installed package for each attempt.
Checked-in summaries do not bind every reported Viking observation to an
installed package, Run, Attempt, profile, input, and runtime identity. That
gap prevents a lossless, date-qualified history transfer under the current
[history rules](../history/README.md#record-rules) without reconstructing
source evidence. Preserve three destinations separately: current commands and
policy with owners, historical observations and former approval in dated
evidence when qualified, and status/acceptance in SITE-PARITY-01,
CLUSTER-VERIFY-01, and their delegated CV cards.
The old 5–15-minute setup guidance at backlog lines 217–219 is framed as an
earlier decision; the [CV-U05 card](cluster_verification_backlog.md) lines
393–406 and [Quickstart](../../quickstart.md) lines 161–163 carry the later
5–25-minute user request. Keep chronology dated and route current readers to
the current notice rather than call the old figure a current contract.

### F52 — Report regeneration wording

The [root README](../../README.md) lines 72–75 says reporting can be
“regenerated” with `emrys report [RUN] --execute`. The ratified
[platform decision](../design/decisions/platform-direction.md) lines 183–188
also calls Report “regenerable” and says it can regenerate independently;
that may mean generation after an opted-out Run, but does not specify the
current create-only boundary. The
[reporting owner](../../src/emrys/reporting/README.md) lines 3–16 says
`--execute` publishes only from empty owned state, while a complete bundle is
revalidated and reused (lines 102–112). The [Runbook](../operations/RUNBOOK.md)
lines 477–490 correctly distinguishes generation after skipped reporting,
reuse of complete bundles, and refusal of partial or blocked bundles.
[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 74–80 explicitly
forbids treating `report` as a repair or overwrite route. “Regenerated” could
lead a reader to expect replacement of an existing or partial bundle; no
actual misuse is observed. Clarify absent-output generation and complete-bundle
reuse in both the root overview and decision wording, with partial-bundle
recovery routed to existing operator guidance. Preserve the decision's
Run/Attempt identity boundary, create-only publication, and retained evidence.

### F53 — Dependent Project in shared-runtime replacement

[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 149–159 says to
preview and apply a sealed-runtime replacement from each dependent Project,
but both pasteable commands specify only `--from-project` and omit the
borrower's `--project`. Runtime discovery resolves an omitted Project to
`project.yaml` in the current working directory
([onboarding](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 270–285 and 2304–2321). From outside the dependent Project, those
commands can fail or select another current Project for inspection; the
separate source-selection and admission checks still govern any mutation.
The [Runbook](../operations/RUNBOOK.md) lines 683–693 already shows the exact
dependent `--project /absolute/dependent/project.yaml` selector for the same
replacement. Its preceding lines 683–685 describe source-Project Doctor
repair with bare `emrys doctor --repair`, immediately after a borrower Doctor
example. Doctor likewise defaults to the current directory's Project
(`doctor.py:2041–2046`). Name the source Project explicitly there, and add
the borrower selector to both recovery commands or state the required working
directory. Preserve preview before `--execute`, exact-source replacement,
the old managed generation, seals, claims, and blocked-state evidence. This
is a static reader-route finding; no runtime replacement was exercised.

### F54 — Analysis reporter return shape

The [private report guide](../../src/emrys/reporting/_run_report/README.md)
lines 24–26 says the selected `emrys.analysis_reporters` provider “returns
the scientific HTML bytes.” The public
[carrier](../../src/emrys/reporting/__init__.py) lines 57–63 is
`AnalysisScientificReportV1`: it holds `html_bytes` plus input, renderer, and
figure evidence. [Context admission](../../src/emrys/reporting/_run_report/context.py)
lines 225–252 rejects a bare bytes return and validates the carrier; the
[built-in provider](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/provider.py)
lines 121–160 returns that carrier. The [reporting owner](../../src/emrys/reporting/README.md)
lines 22–27 already names the correct return annotation. Clarify the private
guide's API shape without changing provider behavior or core-owned fixed
outputs. This is a source-level wording mismatch; no provider was run.

The [paired-CMH report guide](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/README.md)
lines 22–27 also says its provider “returns scientific HTML bytes.” Its
[provider](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/provider.py)
lines 121–160 returns the same structured carrier, so F54 covers both guides.

### F55 — CI lane selection route

The [workflow README](../../.github/workflows/README.md) lines 3–6 says the
[test baseline](../design/TEST_BASELINE.md#validation-lanes) “defines each
lane.” That section at lines 73–85 describes the assembled local gate,
verified CI shards, broad long-lane categories, and trigger limits, but does
not enumerate each hosted job or its exact selection. The
[workflow](../../.github/workflows/ci.yml) owns those job conditions (for
example, lines 109–114) and the schedule plus Sunday 100,000-pair selection
(lines 51–53 and 1385–1394). Point readers to `ci.yml` for exact current
lanes and retain the baseline for test policy and evidence ceilings. This
does not imply a CI failure or that a green workflow proves cluster or
scientific acceptance; no workflow was run in this pass.

### F56 — Synthetic driver dependency mutation claim

The [test-tool guide](../../tests/tools/README.md) lines 11–12 says
`real_synthetic_e2e.py` runs managed synthetic direct/Slurm checks “without
installing or cleaning dependencies.” The
[driver](../../tests/tools/real_synthetic_e2e.py) lines 1701–1736 invokes
`emrys doctor --project … --repair --execute` for each disposable Project.
Confirmed Doctor repair may install Project-owned dependencies through the
selected package managers
([coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 159–166). The driver's retained summary at lines 2244–2252 says no
*post-run* cleanup or repair; the failed summary at 2268–2277 makes the
same post-failure claim. Narrow the guide to the actual controlled Doctor
repair and no-post-run-cleanup boundaries so an operator does not infer the
long lane is dependency read-only. Preserve explicit repair, disposable
Project ownership, and retained partial evidence. This static comparison
does not establish that an installation occurred in any particular run.

### F57 — Make fixture public target label

The [fixture guide](../../tests/fixtures/public_cli_contracts/README.md)
lines 3–4 calls `make_target_expansions.json` the expansion contract for
“every public Make target.” The
[test map](../../tests/test_public_cli_contracts.py) lines 182–205 includes
`internal_lane` targets such as `validation-static` and
`python-coverage-shard`, plus `operator_mutation` targets such as `r-restore`
and `python-coverage-baseline-update`. Its inventory assertion at 877–903
requires all declared `.PHONY` targets, not just supported public commands.
Call this the complete Make target expansion inventory and preserve the
explicit applicability classes. The fixture still protects literal command
expansion and runs no recipe, as its guide correctly states at lines 10–13.
No Make target was run for this finding.

### F58 — Nonoverlapping validation lane claim

The [test-tool guide](../../tests/tools/README.md) line 6 says
`run_validation.py` runs “non-overlapping test groups,” and the
[driver](../../tests/tools/run_validation.py) lines 167–174 calls its four
lanes non-overlapping. The Python sharder collects all pytest node IDs except
two explicitly ignored files
([sharder](../../tests/tools/python_test_shards.py) lines 19–24 and 93–100),
so its selection can include
`tests/analyses/paired_cmh_candidate_ranking/scientific_context_projection/test_real_r_projection.py`.
The guarded-R lane calls the
[real-R wrapper](../../tests/analyses/paired_cmh_candidate_ranking/scientific_context_projection/run_scientific_context_projection_tests.sh)
lines 66–68, which selects that same file explicitly; the
[Make routing](../../scripts/make_quality.mk) lines 87–90 and 112–124
connects it to the guarded lane. The same pytest IDs can therefore be
selected in both lanes when their prerequisites are available. No lane was
run here, so duplicate execution in a particular CI run is unverified.
Narrow “non-overlapping” to the distinct lane purposes. Any selection change
belongs with [ASSURANCE-01](backlog_matrix.md) and needs proof that Python
coverage, guarded real-R comparison, and separate failure detection survive.

### F59 — Pre-Run submission recovery route

[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 3–4, 12–14, and
29–33 sends a reader without a Run to Project/runtime checks and says to
check an exact scheduler ID before resubmitting. A retained submission request
can exist before any Run, and its job ID may be unknown or unconfirmed. The
[Runbook](../operations/RUNBOOK.md) lines 9–26 already documents a Project
request roster with `emrys inspect` and exact `--submission` inspection.
[Control](../../src/emrys/orchestration/run_coordinator/control.py) lines
2632–2766 prints that roster before resolving a Run and handles no Runs
without treating their absence as permission to submit again. Route the
first response and no-Run paragraph through retained request inspection
before any new submission; preserve partial, malformed, `UNKNOWN`, and
scheduler-independent observations. This is a static reader-route gap, not
a reproduced duplicate submission.

### F60 — Submission request promise for direct execution

The [Runbook](../operations/RUNBOOK.md) lines 9–15 says Run, resume, and
report print a `Submission request:` directory after approval without naming
placement. Run and resume schedule a request only for a Slurm profile outside
an existing job ([control](../../src/emrys/orchestration/run_coordinator/control.py)
lines 1743–1783); report does likewise at lines 2099–2149. Direct placement
executes without a Slurm request. The Runbook already distinguishes direct
from Slurm in its Run plan (lines 441–450) and reporting route (488–493).
Scope the opening promise to Slurm submissions so direct users do not search
for a nonexistent request. Keep the exact pre-Run request retention and
uncertain-job guidance for Slurm. No operation was executed here.

### F61 — Run-summary commit marker pronoun

The [Run result manifest guide](../../src/emrys/reporting/_run_summary/README.md)
lines 16–21 describes the summary JSON, then the QC TSV, then says
“Installing it last commits the two TSV projections.” The nearest noun is the
QC TSV, but the [publication owner](../../src/emrys/reporting/_artifact_index/publication.py)
orders summary TSV, QC TSV, and summary JSON (lines 94–98, 173–183); JSON is
the final commit member. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1218–1222 states that order correctly. This is pronoun ambiguity in the
owner guide, not evidence of wrong publication order. No publisher was run.
