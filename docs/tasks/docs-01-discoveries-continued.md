# DOCS-01 discovery notes, continued

This companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F30–F61; the [third file](docs-01-discoveries-third.md) holds F62–F99,
and the [fourth file](docs-01-discoveries-fourth.md) begins at F100.
Unless a subsection names another revision, source line
references are pinned to `3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`.
These are observations, not accepted changes or a task-status registry.

## Discovery notes

### F30 — Dashboard reporting-stage text

**Dismissed for DOCS-01 at `60659099`.** This is product-facing source copy,
not an existing guide or contract; the observation grants no product edit.
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
Current reporting instead names `run_summary` and `html_report`. The
user-facing explanations and fixture retain old wording; old log aliases and
current `cohort_slice` mapping have separate compatibility roles
(`test_dashboard.py:362–374`). Scheduler text still cannot prove admitted
Run completion.

### F31 — Historical Slurm username recovery advice

[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 65–72 mixes a current
Snakemake error and Run recovery with an undated older-submission cause,
four-variable export list, and “Update EMRYS to the submission fix.” The
[backlog incident](backlog_matrix.md) lines 243–252 and
[CV card](cluster_verification_backlog.md) lines 2392–2404 retain the original
failure and startup boundary; the [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 375–382 and [submission source](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
lines 861–870 own the exact export list, checked by direct source tests at
`tests/orchestration/run_coordinator/test_slurm_submission.py:2027–2099`.
No fixed installed release or current Slurm failure was established. Preserve
error, Run inspection/resume, and evidence; historical cause and variable list are only a review span.

### F32 — Mermaid check's stated ceiling

[Documentation test README](../../tests/documentation/README.md) lines 3–8
says cases cover “standalone Mermaid syntax.” The
[checker](../../scripts/documentation/validate_structure.py) docstring at
235–236 also says “syntax”; lines 237–251 check only a first nonblank
`flowchart` declaration and absence of Markdown
fences; its [tests](../../tests/documentation/test_validate_structure.py)
lines 290–323 exercise those refusals. The
[tool README](../../scripts/documentation/README.md) lines 3–7 correctly
describes declarations and fences but broadly says it checks first headings.
At lines 120–126 it finds an H1 anywhere, not necessarily the first
heading; lines 199–206 apply that test only to canonical pages. Other files
receive link checks. The gate neither parses Mermaid grammar nor renders it.

### F33 — Report receipt version in the scientist diagram

The linked [scientist diagram](../architecture/diagrams/current_user_pipeline.mmd)
line 15 groups summary TSV with two HTML reports and labels their receipt v4.
The [reporting owner](../../src/emrys/reporting/README.md) lines 10–16,
29–49 separates summary JSON/TSVs under artifact-summary from HTML and
`report_outputs.tsv` under Results; the [schema index](../../src/emrys/contracts/schemas/artifacts/README.md)
lines 3–8 names artifact entries v4, Run result manifest v8, and report
receipt v8. The architecture links this non-authoritative diagram at line 56.

That node also says “Read-only reporting.” Reporting leaves the successful
Run unchanged, but `emrys report --execute` creates absent owned outputs
([reporting owner](../../src/emrys/reporting/README.md) lines 3–16).
The [test baseline](../design/TEST_BASELINE.md) lines 108–111,
[glossary](../reference/GLOSSARY.md) line 71,
[architecture](../architecture/ARCHITECTURE.md) lines 19–33, and
[platform decision](../design/decisions/platform-direction.md) lines
180–188 also call reporting/Results read-only despite independent or
regenerable reports. This may mean immutable scientific inputs, but can imply
no output creation. It is one wording ambiguity, not a transaction defect
or safe deletion candidate.

### F34 — Prepared finalization in the reliability diagram

[Reliability diagram](../architecture/diagrams/reliability.mmd) lines 20–22
sends every failed/interrupted Attempt through `emrys resume` to a new
Attempt and Task. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1008–1035 permits a distinct first action: complete an exact prepared
terminal receipt on the existing Attempt. A prepared success starts no new
scientific work; an eligible failed/interrupted outcome may then continue in a
new Attempt. [Troubleshooting](../operations/TROUBLESHOOTING.md) lines 35–50
already explains this. The two paths have distinct Attempt identity and
evidence requirements; missing or ambiguous evidence grants neither.

### F35 — FASTQ pairing language

[Glossary](../reference/GLOSSARY.md) lines 45 and 67 says EMRYS does not infer
R1/R2 pairing from filenames. The [engineering guide](../operations/ENGINEERING_CONVENTIONS.md)
lines 18–20 also broadly bans inference of “pairing” from names. Guided Init
does recognize `_R1/_R2` and `_1/_2` mates and displays detected pairs
([onboarding](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 964–1006 and 1443–1466; [Quickstart](../../quickstart.md) lines 79–81).
The operator still authors condition and biological pairing group at onboarding lines
1010–1016; the [sample manifest guide](../../configs/README.md) lines
144–170 makes those values authoritative. Mate discovery and authored
experimental pairing are different; the ban on inferred biological meaning
or sample order remains. This is ambiguous wording, not a
demonstrated scientific-inference defect.

### F36 — Cross-owner history in runtime test guidance

[Runtime test README](../../tests/evidence/runtime_availability/README.md)
lines 3–13 owns current probes, Snakemake startup and site limits, but line 14
records retired report-publisher tests. Git commit `ddc828171` introduced that
sentence while removing the tests; [polish item 4](polish-campaign.md) lines
276–282 retains PR #160, the unresolved defects and preserved old reports.
The retired optional publisher differs from current public `emrys report`,
registered in [`__main__.py`](../../src/emrys/__main__.py) lines 264–267. This is a
one-line cross-owner history candidate, not measured saving or evidence-deletion
authority; the runtime guide's current scope and site limits remain distinct.

### F37 — BED12 dependency in the scientist diagram

[Scientist diagram](../architecture/diagrams/current_user_pipeline.mmd)
lines 9 and 22 combines canonical BAM QC with RSeQC mechanical orientation
under one inspection node fed only by BAM/BAI. Its legend at line 39 says
arrows are data or contract dependencies. The authoritative
[stage map](../../src/emrys/contracts/STAGE_MAP.md) lines 67–70 requires
BED12 from `convert_GTF_to_BED12` as a second RSeQC input; BAM QC has no
such fan-in. The [diagram index](../architecture/diagrams/README.md) lines
3–14 calls this view concise and non-authoritative. “Non-gating” in the stage
map at 36–43 concerns downstream computation; the diagram makes no Run
completion claim. The missing edge is a reader depiction, not a DAG defect.
The same diagram's reference node at lines 2, 18, 24–27, and 35 presents
FAI/BED12 alongside supplied FASTA/GTF, including a direct FAI continuation.
The stage map at lines 47–50 and 69–79 instead identifies FASTA/GTF as external
and Steps `00b`/`00c` as BED12/FAI producers. This is a generated-versus-supplied
provenance ambiguity in the diagram, not evidence that the DAG is wrong. The
[Step 05 contract](../../src/emrys/stages/split_n_cigar/CONTRACT.md) lines
12–14 likewise says Step 00c “supplies” FASTA with its sidecars; Step 00c
does not produce FASTA but does register that external file as an artifact
adapter. That wording alone establishes no additional dependency error.

### F38 — Slurm request in the reliability diagram

**Dismissed for DOCS-01 at `27844f15`.** The
[reliability diagram](../architecture/diagrams/reliability.mmd) lines 2–6
shows a generic compute path; the [diagram index](../architecture/diagrams/README.md)
lines 3–14 calls it a concise, non-authoritative view. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 410–449 and [Runbook](../operations/RUNBOOK.md) lines 9–25 own the
separate Slurm request and inspection path. The diagram makes no Slurm claim;
adding that branch would expand it without reducing documentation. F34's
unconditional resume edge is a distinct observation.

### F39 — Validation roster inventory claim

[Contract-integration index](../../tests/contract_integration/README.md)
lines 8–9 says roster expectations cover “every current validator.” The
[roster guide](../../tests/contract_integration/validation_rosters/README.md)
lines 3–6 means producers of ordered validation-report check IDs. The
[roster test](../../tests/contract_integration/validation_rosters/test_validation_check_rosters.py)
lines 23–41 covers all 14 current producers. The
[public CLI](../../src/emrys/__main__.py) lines 44–65 and 318–333 also exposes
all-pass, artifact-contract, and manifest validators outside that set. Only
the parent index's unqualified “validator” scope is overbroad. The fixed map's
inventory assertion at test lines 84–95 does not discover future source
owners, but neither README promises that. Literal ordered rosters remain a
distinct protection; they do not prove real-output or scientific meaning.

### F40 — Concurrency in the local workflow profile

**Dismissed after recheck at `60659099`.**
[Local profile README](../../src/emrys/workflow/profiles/local/README.md)
lines 5–7 says the Execution Plan and Attempt supply “sample concurrency.”
The current [resource schema](../../src/emrys/contracts/schemas/orchestration/v3/resource_config.schema.json)
lines 41–53 defines `stage_concurrency` for repeated stages 01–07, including
cohort partitions; [resource policy](../../src/emrys/orchestration/run_coordinator/resource_policy.py)
lines 37–48 resolves that keyed control. The Snakemake profile sets engine
defaults, not one sample-wide policy. The per-stage term does not promise
that any particular allocation will admit every task. “Sample concurrency”
is loose shorthand, not a claimed global cap or a proved contract conflict.

### F41 — Step 05 check's read-only help

[Retained Step 05 check](../../tests/data_checks/validate_step05_outputs.sh)
line 20 calls itself “Read-only validation,” but its own help at 13–18
explicitly says it writes a status TSV. Execution creates an output directory,
writes/removes a probe, and writes or replaces the TSV at 75–95. The
[owner README](../../tests/data_checks/README.md) lines 3–7 says BAM/BAI are
not mutated and lists the writes. Reading the complete help and owner guide
resolves the input-versus-output scope. The earlier contradiction claim is
dismissed; no hidden write, documentation correction, or saving is established.

### F42 — Report transfer in the coordinator test index

[Coordinator test README](../../tests/orchestration/run_coordinator/README.md)
lines 11–20 places report transfer in a table of checks, but that row links a
Runbook procedure, not a repeatable test. The [CV card](cluster_verification_backlog.md)
lines 4079–4090 records the tiny local copy/comparison observation and its
limit. The CV record is the bounded command-mechanics evidence home;
generated-bundle contents, rendering, and institutional transfer remain
pending rather than proved by a coordinator fixture.
The CV card at 4086–4090 names no exact run date, source commit, command
transcript, or retained artifact for that tiny exercise. It is an honest
current evidence home, not yet a source for a date-qualified history transfer.
The [test baseline](../design/TEST_BASELINE.md) line 15 links the test guide's
`#what-the-checks-establish` heading. The Runbook owns the procedure; the
test row itself is one physical line with no direct-test link, a plausible
one-line reduction. REPORT-01–03 and CV-27 retain separate acceptance.

### F43 — Print behavior in the reporting test guide

[Reporting test README](../../tests/reporting/README.md) lines 3–7 says tests
pin “print behavior.” The [direct test](../../tests/reporting/test_report.py)
lines 695–735 asserts print CSS rules; other cases cover generated HTML text
and an SVG height attribute. The [backlog](backlog_matrix.md) lines 291–294
keeps REPORT-01–04 visual or layout acceptance pending. The guide itself does
not claim browser or PDF review, and “print behavior” accurately describes its
source-level checks. The earlier guide-overclaim concern is dismissed; rendered
acceptance remains a separate evidence layer, with no guide edit established.

### F44 — Internal worker command ownership

**Dismissed for DOCS-01 at `d84a8c41`.** The
[STAR contract](../../src/emrys/stages/star_alignment/CONTRACT.md) lines 3–6
names its producer's repository path without promising standalone support.
The [RSeQC contract](../../src/emrys/evidence/rseqc_orientation/CONTRACT.md)
lines 3–8 says “independently runnable,” but its lines 58–61 and adjacent
[README](../../src/emrys/evidence/rseqc_orientation/README.md) lines 11–16
classify the shell as an internal Run worker. Both shells require a runner
work directory; [STAR](../../tests/stages/star_alignment/test_step_01_star_align.sh)
line 74 and [RSeQC tests](../../tests/evidence/rseqc_orientation/test_step_03_infer_strandedness_and_orientation.sh)
line 77 assert refusal without it. The
[coordinator docstrings](../../src/emrys/orchestration/run_coordinator/task.py)
at 100–104 and 146–154 and [public-CLI tests](../../tests/test_public_cli_contracts.py)
at 113–154, 829–865 use “public” for delegated workers, while the
[stage index](../../src/emrys/stages/README.md) lines 30–39 calls them internal.
These labels do not establish a supported standalone command or useful DOCS-01
reduction. Help, argument, exit, and file-mode checks remain legitimate;
no test removal or standalone publication claim follows.

### F45 — Watch and stop in the command-audience map

The [functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
at 22–29 omits `watch` and `stop`, though the public
[CLI](../../src/emrys/__main__.py) at 275–288 registers both. The
[Quickstart](../../quickstart.md) at 176–185 routes `watch`, and the
[Runbook](../operations/RUNBOOK.md) at 139–157 routes exact-request `stop`.
At recheck head `2398f144`, the inventory's opening at 3–4 explicitly makes
the map selective and assigns the complete command roster to `emrys --help`.
The omission therefore establishes no missing command or required reader
route. Dismissed as an optional navigation preference; `stop` retains its
owner-local evidence limit.

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
Only descriptive wording is at issue; the v1 file, directory, `$id`, and
references remain public schema bytes. No validator defect is inferred.

### F47 — R-probe concurrency candidate after CV-26

**Dismissed for DOCS-01 at `27844f15`.** The
[optimization candidate](optimization_campaign.md) lines 302–319 already
links [CV-26](cluster_verification_backlog.md), says its source reduction
leaves serial probes unchanged, and conditions future comparison on Doctor
and runtime-model reconciliation. CV-26 at 3979–3987 retains the measured
two-worker deferral for a supported one-CPU profile and unowned cancellation,
while allowing a separately qualified resource-aware proposal. The two
records have distinct roles; no missing selection context or useful DOCS-01
reduction remains. No new measurement was run.

### F48 — Project name lookup from the repository root

**Dismissed for DOCS-01 after recheck at `633625a7`.** The
[root guide](../../README.md) lines 77–79 permits `--project NAME_OR_PATH`
outside a Project; it does not promise lookup in the saved Projects home.
The [selector](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 270–285 resolves a bare name relative to the current directory or an
explicit path, as the [contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 35–37 and direct test at
`tests/orchestration/run_coordinator/test_onboarding.py:1929–1954` establish.
Quickstart does not instruct `--project pum1-study` from the repository root;
the [Runbook](../operations/RUNBOOK.md) lines 294–301 gives an absolute path.
The earlier finding inferred a global-name promise the guide does not make,
and no useful documentation reduction is established.

### F49 — Allocation preview needs execution-flag boundary

[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 222–225 asks a
reader with a rejected allocation or scratch path to preview the prior
submission with `--verbose </dev/null`. The prior command supplies its
operation and Project/Run selector; this is not a parser or standalone-command
defect. The [Runbook](../operations/RUNBOOK.md) lines 401–411 gives a complete
`emrys run </dev/null` preview without `--execute`. Run, resume, and report
accept `--execute` ([control parser](../../src/emrys/orchestration/run_coordinator/control.py)
lines 1800–1868); Doctor accepts it with `--repair`
(`doctor.py:1989–1996,2023–2029`). Input redirection cannot neutralize a
retained `--execute`; the no-write reading depends on the exact prior command.
No such command was exercised in this audit.

### F50 — Submission-request version in the coordinator contract

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 487–490 calls selected scheduler binding “v2/v3” and new requests v3;
lines 682–685 says stop admits only v3. Its lines 410–424 define current v4.
The [submission owner](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
lines 54–59 declares v4 current and v3/v4 named; `plan_stop` at 303–313
admits both. Its job-name observation at 239–243 covers both. A
[source test](../../tests/orchestration/run_coordinator/test_slurm_submission.py)
lines 925–934 checks both observations; its stop fixture at 113–123 uses v3,
so that fixture alone does not prove v4 stop execution. This is contract
wording and test-scope drift, not a format migration or runtime conclusion.

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
the [Runbook](../operations/RUNBOOK.md) lines 534–599 and 658–682, and
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
context. These are distinct aspects; neither is
EMRYS whole-Run proof. History's unchanged-record rule does not permit
appending the later scheduler interpretation to its frozen manual-Step section
just because the job number matches; a qualified new dated record could
cross-link it after provenance is reconstructed.
E04/E09/E12 overlap the synthetic and actual-data observations at 258–267;
operator-report attribution, the cancelled Run without terminal receipt,
and deferred visual review are separate evidence limits. The
`#viking-walkthrough-findings` anchor has live inbound links from the
SITE-PARITY-01 row and CV charter. Those facts and links constrain any
future transfer; the backlog retains current acceptance. The charter's
closure criteria and backlog's procedure are
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
source evidence. Three destinations remain distinct: current commands and
policy with owners, historical observations and former approval in dated
evidence when qualified, and status/acceptance in SITE-PARITY-01,
CLUSTER-VERIFY-01, and their delegated CV cards.
The old 5–15-minute setup guidance at backlog lines 217–219 is framed as an
earlier decision; the [CV-U05 card](cluster_verification_backlog.md) lines
393–406 and [Quickstart](../../quickstart.md) lines 161–163 carry the later
5–25-minute user request. The older figure is dated chronology, not a current
contract.

### F52 — Report regeneration wording

The [root README](../../README.md) lines 72–75 says reporting can be
“regenerated” with `emrys report [RUN] --execute`. The ratified
[platform decision](../design/decisions/platform-direction.md) lines 183–188
also calls Report “regenerable”; the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1203–1208 says reporting “regeneration” cannot invalidate science.
These may mean generation after an opted-out Run but omit the create-only
boundary. The [reporting owner](../../src/emrys/reporting/README.md) lines
3–16 says `--execute` publishes only from empty owned state; a complete bundle
is revalidated and reused (lines 102–112). The [Runbook](../operations/RUNBOOK.md)
distinguishes these cases at current lines 437–450: generation after skipped reporting,
reuse of complete bundles, and refusal of partial or blocked bundles.
[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 74–80 explicitly
forbids treating `report` as a repair or overwrite route. “Regenerated” could
imply replacement of an existing or partial bundle; no misuse is observed.
Existing recovery guidance, Run/Attempt identity, and retained evidence
still govern the boundary.

### F53 — Dependent Project in shared-runtime replacement

[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 149–159 gives
selector-free `--from-project` commands but tells readers to run them from each
dependent Project. Under that precondition they select the borrower: runtime
discovery defaults an omitted Project to the current directory's `project.yaml`
([onboarding](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 270–285, 2304–2321). Outside the borrower, a command may fail or select
another Project; source-selection and admission checks still govern mutation.
The [Runbook](../operations/RUNBOOK.md) at current lines 643–649
shows an explicit dependent selector, then a bare source-Project Doctor command.
Doctor also defaults to the current Project (`doctor.py:2041–2046`). Its own
borrower diagnostics at `doctor.py:654–659`, `698–707`, and `949–954` print
replacement commands with no borrower selector or working-directory instruction,
including after invocation with `--project` elsewhere. Preview, exact-source
checks, old generations, seals, and blocked-state evidence remain protective;
no runtime replacement was exercised.

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
lines 22–27 already names the correct return annotation. The private guide's
API description is narrower than the carrier; provider behavior and core-owned
outputs were unchanged. No provider was run.

The [paired-CMH report guide](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/README.md)
lines 22–27 also says its provider “returns scientific HTML bytes.” Its
[provider](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/provider.py)
lines 121–160 returns the same structured carrier, so F54 covers both guides.

### F55 — CI lane selection route

**Dismissed for DOCS-01 at `27844f15`.** The
[workflow README](../../.github/workflows/README.md) lines 3–6 directly
links both [`ci.yml`](../../.github/workflows/ci.yml) for exact job selection
and the [test baseline](../design/TEST_BASELINE.md#validation-lanes) lines
73–85 for lane policy and evidence limits. “Defines each lane” does not
promise that the baseline enumerates every job condition. The schedule and
Sunday 100,000-pair selection remain in `ci.yml` at 51–53 and 1385–1394.
No route is missing, no useful reduction follows, and no workflow ran.

### F56 — Synthetic driver dependency mutation claim

The [test-tool guide](../../tests/tools/README.md) lines 11–12 says
`real_synthetic_e2e.py` runs managed synthetic direct/Slurm checks “without
installing or cleaning dependencies.” The
[driver](../../tests/tools/real_synthetic_e2e.py) lines 1701–1736 invokes
`emrys doctor --project … --repair --execute` for each disposable Project.
Confirmed Doctor repair may install Project-owned dependencies through
package managers ([coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 159–166); the driver summaries at 2244–2252 and 2268–2277 promise
no *post-run* cleanup or repair. The [engineering guide](../operations/ENGINEERING_CONVENTIONS.md)
lines 50–51 separately says tests never install packages. The ordinary
`validation-wheel-smoke` [Make target](../../scripts/make_quality.mk) lines
83–85 runs [a test](../../tests/test_package_distribution.py) that creates
a temporary installer and calls `uv lock` plus offline `uv sync` into its
`.venv` (lines 250–308, 341–359); the [CI workflow](../../.github/workflows/ci.yml)
uses that target at 182–186 and 1014–1021. These are distinct controlled
installation scopes, not dependency read-only tests. Disposable Project
ownership, isolated wheel installation, and retained partial evidence are
separate boundaries.
No test or installation was run in this audit.

### F57 — Make fixture public target label

**Dismissed for DOCS-01 after recheck at `633625a7`.**
The [fixture guide](../../tests/fixtures/public_cli_contracts/README.md)
lines 3–4 calls `make_target_expansions.json` the expansion contract for
“every public Make target.” The
[test map](../../tests/test_public_cli_contracts.py) lines 182–205 also
includes `internal_lane` and `operator_mutation` targets; its assertion at
877–903 inventories all declared `.PHONY` targets. “Every public” does not
mean “only public,” so the guide does not misclassify those additional rows.
The fixture protects literal expansion without running recipes, as its guide
says at lines 10–13. No useful DOCS-01 reduction or Make execution is shown.

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
“Non-overlapping” accurately describes lane purposes but not every selected
pytest ID. [ASSURANCE-01](backlog_matrix.md) owns any future gate-selection
decision and surviving-protection evidence.

### F59 — Pre-Run submission recovery route

[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 3–4, 12–14, and
29–33 sends a reader without a Run to Project/runtime checks and says to
check an exact scheduler ID before resubmitting. A retained submission request
can exist before any Run, and its job ID may be unknown or unconfirmed. The
[Runbook](../operations/RUNBOOK.md) lines 9–26 already documents a Project
request roster with `emrys inspect` and exact `--submission` inspection.
[Control](../../src/emrys/orchestration/run_coordinator/control.py) lines
2632–2766 prints that roster before resolving a Run and handles no Runs
without treating their absence as permission to submit again. The current
first-response and no-Run prose omits retained request inspection, including
partial, malformed, `UNKNOWN`, and scheduler-independent observations. This
is a static reader-route gap, not a reproduced duplicate submission.
At `f2e719c0`, [top-level CLI help](../../src/emrys/__main__.py) lines 269–279
also labels `inspect` and `watch` only by Run/job, although both expose
`--submission` in [control](../../src/emrys/orchestration/run_coordinator/control.py)
lines 1926–1937. Detailed option help retains the route.

### F60 — Submission request promise for direct execution

The [Runbook](../operations/RUNBOOK.md) lines 9–15 says Run, resume, and
report print a `Submission request:` directory after approval without naming
placement. Run and resume schedule a request only for a Slurm profile outside
an existing job ([control](../../src/emrys/orchestration/run_coordinator/control.py)
lines 1743–1783); report does likewise at lines 2099–2149. Direct placement
executes without a Slurm request. The Runbook distinguishes direct
from Slurm in its Run plan (baseline lines 441–450; pinned revision `0cb5d507`
lines 401–411) and reporting route (baseline lines 488–493; pinned revision
`0cb5d507` lines 449–453).
The opening promise could send direct users searching for a nonexistent
request. Slurm's pre-Run request retention and uncertain-job guidance still
apply. No operation was executed here.

### F61 — Run-summary commit marker pronoun

The [Run result manifest guide](../../src/emrys/reporting/_run_summary/README.md)
lines 16–21 describes the summary JSON, then the QC TSV, then says
“Installing it last commits the two TSV projections.” The nearest noun is the
QC TSV, but the [publication owner](../../src/emrys/reporting/_artifact_index/publication.py)
orders summary TSV, QC TSV, and summary JSON (lines 94–98, 173–183); JSON is
the final commit member. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1218–1222 states that order correctly. This is pronoun ambiguity in the
owner guide, not evidence of wrong publication order. No publisher was run.
