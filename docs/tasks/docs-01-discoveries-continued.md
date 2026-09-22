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
at verified scientific tasks. This is user-facing product text drift, not a
request to delete historical log aliases. Review watch projection and old-log
compatibility before selecting a separate product correction; scheduler text
still cannot prove admitted Run completion.

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

### F35 — FASTQ pairing in the glossary

[Glossary](../reference/GLOSSARY.md) lines 45 and 67 says EMRYS does not infer
R1/R2 pairing from filenames. Guided Init does recognize `_R1/_R2` and
`_1/_2` mates and displays detected pairs
([onboarding](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 964–1006; [Quickstart](../../quickstart.md) lines 79–81). The operator
still authors condition and biological pairing group at onboarding lines
1010–1016; the [sample manifest guide](../../configs/README.md) lines
144–170 makes those values authoritative. Clarify mate discovery versus
authored experimental pairing; this is ambiguous wording, not a demonstrated
scientific-inference defect.

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

### F43 — Print behavior in the reporting test guide

[Reporting test README](../../tests/reporting/README.md) lines 3–7 says tests
pin “print behavior.” The checked source cases assert print CSS, generated
HTML text, and an SVG height attribute, not browser or PDF layout review.
The [backlog](backlog_matrix.md) lines 291–294 still keeps REPORT-01–04 visual
or layout acceptance pending. Name source-level print rules and generated
structure in the test guide without implying rendered user acceptance.

### F44 — Internal workers described as standalone commands

The opening of the [STAR contract](../../src/emrys/stages/star_alignment/CONTRACT.md)
lines 3–6 calls its producer an explicit repository-path command. The
[RSeQC contract](../../src/emrys/evidence/rseqc_orientation/CONTRACT.md)
lines 3–8 additionally calls the operation independently runnable. Both
contracts later call their shells internal Run workers (STAR lines 65–68;
RSeQC lines 58–61), as do their adjacent READMEs (STAR lines 12–18; RSeQC
lines 11–16). The STAR shell requires runner-supplied `EMRYS_TASK_WORK_DIR`
at lines 3, 22–23, and 51–52; the RSeQC shell does likewise at lines 3,
18–19, and 43–44. Correct the opening command-ownership claims while
retaining direct `--help` for these scripts and the public grouped validators.
No standalone production or recovery route is established by the help tests.
The coordinator's `TaskBackend` and `CommandResult` docstrings
([task source](../../src/emrys/orchestration/run_coordinator/task.py) lines
100–104 and 146–154) also call delegated producer and validator commands
“public.” Correct that generic ownership label without exposing internal
producers or changing Run-owned publication.

### F45 — Watch and stop in the command-audience map

The [functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
lines 22–29 maps commands to audiences but omits `watch` and `stop`. Both
commands are registered in the public parser
([CLI](../../src/emrys/__main__.py) lines 275–288); the
[Quickstart](../../quickstart.md) lines 176–185 teaches `watch` to scientists,
and the [Runbook](../operations/RUNBOOK.md) lines 139–157 teaches exact-request
`stop` to operators. The inventory says `emrys --help` owns the complete
roster, so this is an audience-routing gap rather than a false claim about
command existence. Add those audience examples or explicitly say the table
is selective; preserve `stop`'s exact-request and evidence ceilings.

### F46 — Artifact common-schema description

The public [common artifact schema](../../src/emrys/contracts/schemas/artifacts/v1/common.schema.json)
line 5 describes definitions for “artifact-schema-v1 record contracts.” Its
[owner README](../../src/emrys/contracts/schemas/artifacts/v1/README.md)
lines 3–5 says active schemas still use these definitions after record schemas
moved to later versions. The [registry](../../src/emrys/contracts/artifacts/_artifact_contracts/schema.py)
lines 68–74 loads this file with current records, whose [index](../../src/emrys/contracts/schemas/artifacts/README.md)
lines 3–8 names artifact entries v4, Run manifest v8, and report receipt v8.
Correct only the stale description after checking schema-byte references and
compatibility; the README calls those bytes a public contract.

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
The [history compendium](../history/validation-evidence.md) lines 81–102
already retains job `605171` as manual NORAD Step 08 evidence at exact
`64b14a11`; the backlog adds that job's scheduler request and accounting
context. Preserve these as distinct aspects and do not turn either into an
EMRYS whole-Run proof.
E04/E09/E12 overlap the synthetic and actual-data observations at 258–267;
preserve operator-report attribution, the cancelled Run without terminal
receipt, and deferred visual review. The `#viking-walkthrough-findings` anchor
has live inbound links from the SITE-PARITY-01 row and CV charter. Map every
fact and both links before any transfer; dated evidence belongs in an
appropriate qualified home, while the backlog retains concise current
acceptance. The charter's closure criteria and backlog's procedure are
complementary, not safely interchangeable.
The old 5–15-minute setup guidance at backlog lines 217–219 is framed as an
earlier decision; the [CV-U05 card](cluster_verification_backlog.md) lines
393–406 and [Quickstart](../../quickstart.md) lines 161–163 carry the later
5–25-minute user request. Keep chronology dated and route current readers to
the current notice rather than call the old figure a current contract.
