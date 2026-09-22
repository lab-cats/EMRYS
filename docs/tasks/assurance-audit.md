# ASSURANCE-01 repository-wide audit

## Scope and evidence

This is the working investigation record for `ASSURANCE-01`. Its starting source is PR #302 at commit `42d02c5a38ecffaba59e58d5d56ba0ab858eda1f`. The audit covers the entire repository: product code, tests, fixtures, scripts, configuration, documentation checks, packaging, and CI. It is **incomplete**; the entries below are discoveries from successive source passes, not a conclusion that other areas are clear.

The [backlog matrix](backlog_matrix.md) owns the accepted outcome and task status. This document records evidence and questions. It authorizes no implementation, protection removal, coverage change, or evidence deletion. `QUAL-01` owns measured test cost; `HARNESS-01` owns simulated-science harness choices; `REPORT-ROSTER-01` owns the reporting roster decision.

All `path:line` references below refer to the pinned commit. **Source reviewed** means code or documentation was inspected, without execution in this audit. **Test characterized** means a committed test explicitly asserts the behavior; that test was not rerun for this record. **Inference** identifies a conclusion still needing a focused reproduction. No product or repository test suite, institutional Slurm run, scientific review, or biological validation was performed for this pass. Focused helper reproductions are identified in their entries; they do not execute a full Run or report transaction.

## Coverage ledger for the pinned tree

The pinned commit contains 575 tracked files. The counts below inventory every top-level surface; "sampled" means specific paths were inspected for the entries in this document, not that every file in a group has been cleared. A file-by-file disposition, distinct-fault map, and any proposal to retire protection remain open.

| Surface | Tracked files | This pass | Remaining review |
|---|---:|---|---|
| `src/emrys/` | 316 | Sampled stage, analysis, evidence, ingestion, reporting, contract, library, workflow, and coordinator boundaries | Trace every candidate's callers and complete owner-level contract and test comparison |
| `tests/` | 186 | Sampled direct owners, fixtures, independent oracles, CI tests, and shared tooling | Map distinct failures, retained evidence, and measured cost before any test reduction |
| `docs/` | 35 | Sampled architecture, task, operator, design, and owner-contract text | Reconcile every affected claim and documentation gate with its source authority |
| `configs/` | 11 | Compared Viking and example profiles with packaged defaults | Check remaining profile variants and operator uses |
| `scripts/` | 6 | Reviewed documentation checks, Make quality recipes, sharding, benchmarking | Finish each script's supported caller and retirement boundary |
| `.github/` | 3 | Reviewed CI workflow jobs and their source tests | Verify branch/trigger behavior and exact hosted checks on the audit PR head |
| Other tracked paths | 18 | Sampled packaging, lockfile, Makefile, root policy, and Project templates | Complete root/support file review; legal and data templates have distinct owners |

## Findings matrix

| ID | Surface | Initial reading | Basis | Next investigation or decision |
|---|---|---|---|---|
| A01-01 | Step 07 selector validation | Known all-pass result for an out-of-bounds region file | Source; test characterized | Decide the validator's selector and output semantic ceiling; trace report consumers |
| A01-02 | Project-to-Step 07 selector admission | Unicode decimal syntax differs between admission and producer | Source | Define accepted syntax and compare all caller inputs |
| A01-03 | CI whitespace check | CI checks a clean worktree diff, not committed PR changes | Source | Specify the commit range and surviving local check |
| A01-04 | Validation roster inventory | "Exact live inventory" scan misses source-owned validators | Source | Derive the inventory from an authoritative owner roster |
| A01-05 | Roster mutation cases | Many step permutations exercise a step-agnostic helper; one reorder case is vacuous | Source | Identify the smallest representative cases while retaining owner oracles |
| A01-06 | Canonical-document path and H1 gate | Presence is enforced; title identity and H1 position are not | Source; test characterized | Assess each required path's value and the intended heading rule |
| A01-07 | Markdown anchors | Tilde-fenced headings are accepted as real anchors | Source; isolated local reproduction | Preserve genuine link checking while correcting the parser boundary |
| A01-08 | Mermaid gate | Declaration and fence check has a deliberately narrow ceiling | Source | Decide whether broader syntax checking solves a distinct failure |
| A01-09 | Hosted resource fixture | Part of the expected policy is derived from production defaults | Source | Map independent literal resource oracles before changing the fixture |
| A01-10 | Reporting adapter fixture | Inventory expectations partly come from the same template as the builder | Source | Identify literal contract expectations for adapter headers and rows |
| A01-11 | Reporting validation roster | Reordered or wrong unique check IDs can still be marked complete | Source; test characterized | Route semantic decision through `REPORT-ROSTER-01`; retain characterization |
| A01-12 | Shell executable-mode tests | Three internal workers are required to remain nonexecutable | Source; test characterized | Decide whether direct invocation is supported for each script |
| A01-13 | Private reporting CLI test | A negative assertion protects absence of private parser functions | Source | Confirm public-route coverage and private invocation contract |
| A01-14 | Step 09/10 R input helpers | Equivalent safe-ID and hash-shape checks appear twice | Source | Audit all callers and negative cases; quantify a complete reduction |
| A01-15 | Validation publication | Three similar validations protect different mutation boundaries | Source; test characterized | Preserve them; map the separate recovery fault matrix |
| A01-16 | Versioned schemas and retained Attempts | Versioned paths serve active identity and re-admission contracts | Source | Check exact references before proposing any retirement |
| A01-17 | Make and static-check surfaces | Some recipe snapshots and shell checks may overlap; command contracts differ | Source | Determine operator use and the distinct failure each check catches |
| A01-18 | Dependency assertions | Source dependency literals and built-wheel metadata overlap partly | Source | Compare failures caught at each representation boundary |
| A01-19 | Step 05 operator check | Site-specific script is retained for manual checks, with bounded evidence | Source; documentation | Establish actual operator use before considering retirement |
| A01-20 | Step 07 VCF validation | Malformed REF/ALT/FORMAT content can pass the report | Source; test characterized | Decide whether the report needs a semantic check or clearer claim |
| A01-21 | Step 08 candidate validation | Arbitrary IDs and row reversal can pass its structural report | Source; test characterized | Preserve the separate real-R ordering oracle |
| A01-22 | Step 09 statistical validation | Fabricated CMH values can pass internally consistent report checks | Source; test characterized | Preserve independent numerical and guarded-R oracles |
| A01-23 | Step 00b GTF agreement | Validator reuses producer normalization | Source; contract | Keep literal converter oracle; assess report wording |
| A01-24 | Step 02b quickcheck | Producer and validator disagree on zero-exit native output | Source; test characterized | Decide admissible output, then migrate producer, validator, adapter, and tests |
| A01-25 | Canonical BAM admission | Producer and validator accept different BAM/RG cases | Source; contract | Resolve acceptance before considering Stage 02 consolidation |
| A01-26 | Reference provenance recovery | Fault test retains known publication/restoration gap | Source; test characterized | Keep recovery work with its owner; retain the fault test |
| A01-27 | Step 06 orientation validation | Report checks count arithmetic without recounting BAM flags | Source; test characterized | Preserve worker and validator cases with their distinct ceilings |
| A01-28 | Run all-pass reader | Accepts arbitrary unique passing check IDs by design | Source; tests | Preserve separate roster and all-pass boundaries |
| A01-29 | Coordinator workflow fixture | Real Snakemake scheduling uses simulated science and production-derived adapters | Source; fixture contract | Retain scheduling/recovery checks without promoting scientific proof |
| A01-30 | Slurm observation tests | A 36-case cross-product may repeat shared mechanics | Source | Measure and map faults under `QUAL-01` before reducing |
| A01-31 | Scheduler output limit | 64 KiB refusal occurs after subprocess capture | Source; contract | Keep size-admission test; do not claim bounded capture memory |
| A01-32 | Prepared-finalization continuity | Distinct-inode substitution is tested; recycled-inode substitution remains unproved | Source; contract | Preserve recovery fault checks and stated limit |
| A01-33 | Historical contexts and Task module | Old request readers and the internal module still serve live diagnostic/execution paths | Source; tests | Keep their supported fault coverage |
| A01-34 | Runtime qualification | Local startup, simulated Doctor, site checks, and Run success are different evidence | Source; tests | Preserve each layer and fixed-seal limits |
| A01-35 | Stage-map documentation gate | Counts slugs without checking identity-table keys or aliases | Source inference | Compare with machine-key tests; retain owner-presence check |
| A01-36 | Reporting Make target | Manual target omits artifact-adapter tests | Source | Define the target's promise; full suite coverage is separate |
| A01-37 | Workflow dependency group | Snakemake is declared twice at the same version | Source; local uv help | Inspect lock and caller impact before configuration reduction |
| A01-38 | Installed-wheel smoke | Wheel is built outside Git and expects unavailable commit provenance | Source; test | Preserve install proof; require separate Git-build provenance evidence |
| A01-39 | Python shard planner | Stale timing IDs block selection; complete receipt proof is separate | Source | Measure collection cost and stale-estimate policy under `QUAL-01` |
| A01-40 | Source topology parity | Test checks documented seams and transitions against executable rosters | Source; test | Retain this defense; avoid a duplicate registry |
| A01-41 | Step 07 gzip selector | Supported compressed region file is reported failed | Source; test characterized | Reconcile validator with Project and producer admission |
| A01-42 | Step 00b BED12 reporting | Reporting rejects owner-valid strand `.` | Source; owner test; isolated reader reproduction | Fix reporting parity after tracing artifact transaction |
| A01-43 | Step 04/05 read groups | Validator reports check headers, not every alignment tag | Source; fixture review | Define per-record report promise; retain producer checks |
| A01-44 | Step 05 header admission | Worker substring matching is weaker than exact validator tokens | Source inference | Decide and test exact producer header policy |
| A01-45 | Storage JSON reader | Duplicate keys and nonstandard constants pass helper parsing | Source; isolated helper reproduction | Reconcile parser policy while preserving receipt identity checks |
| A01-46 | Storage receipt generations | Unicode digit name raises raw conversion error | Source; isolated helper reproduction | Define malformed-name refusal or ignore rule |
| A01-47 | Viking execution profile | Tracked example repeats packaged resource defaults | Source | Decide whether full illustration is needed before reducing config |
| A01-48 | Print-layout tests | CSS tokens and SVG height do not prove printed-page fit | Source | Bound test claim or obtain rendered print evidence |
| A01-49 | PDF artifact reader | PDF-like bytes with a nonexistent root object pass its structure check | Source; isolated adapter reproduction | Decide required renderability without weakening existing checks |
| A01-50 | RSeQC orientation evidence | Native and validator reports have different input and interpretation ceilings | Source; contract | Retain mechanical fractions and independent manifest policy |
| A01-51 | Reporting QC parsers | Reporter duplicates flagstat/RSeQC parsing with different acceptance | Source | Map lexical reuse and artifact status before consolidation |
| A01-52 | Reference contig parsers | Raw exceptions escape shared malformed-input contract | Source; tests; focused helper reproduction | Normalize shared errors across Project, sidecar, provenance callers |
| A01-53 | Step 07 receipt parsing | Missing fields can escape controlled exit with traceback | Source; owner contract | Compare strict TSV reader after caller-boundary decision |
| A01-54 | Public manifest validator | Blank condition and unsafe sample ID pass before stricter Run admission | Source; focused fixture | Decide public validator promise; preserve Step 08 refusal |
| A01-55 | Step 00c sidecar producer | Final pair comparison can pass duplicate names absent from its contract | Source inference | Preserve ordered validator; decide producer uniqueness fault coverage |
| A01-56 | Step 04 Picard metrics | Duplicate column masks invalid value and passes report parser | Source; isolated parser reproduction | Require unique headers if promised; keep numerical checks |
| A01-57 | Validation stdout timing | Failed publication can leave printed pass rows | Source; tiny fixture reproduction | Define CLI stream claim; retain exit and persisted-report gates |
| A01-58 | BAM quickcheck expected text | Reports say empty diagnostics but check exit only | Source; fake-tool reproduction | Decide expected field or stricter rule across owners |
| A01-59 | Execution profile path | Lexical nonroot path can normalize to filesystem root | Source; regex/path reproduction | Decide admission at normalized boundary; preserve batch guard |
| A01-60 | Resource benchmark trial status | Zero-exit validator with failed rows can count as passing trial | Source; focused synthetic benchmark fixture | Define semantic status for advisory recommendation |
| A01-61 | New shared-module coverage | Elevated floor applies to manually listed paths only | Source | Define discovery obligation; retain global and owner gates |
| A01-62 | STAR mapping summary | Three percentages are range checked independently | Source; contract | Retain structural ceiling; decide whether reconciliation is needed |
| A01-63 | DICT field projection | Duplicate SN tags silently take the last value | Source; test characterized | Decide per-row field grammar while preserving ordered contigs |
| A01-64 | Benchmark mixed repetitions | A value with one failed repetition can still be recommended | Source; isolated summary reproduction | Require all planned repetitions before recommendation |
| A01-65 | Local validation lane launch | A later spawn error can leave an earlier lane running | Source; tiny two-lane reproduction | Close process groups and retain logs on launch exceptions |
| A01-66 | Storage compute receipt | Null nested root raises uncontrolled attribute error | Source; isolated helper reproduction | Validate nested shape before identity comparison |
| A01-67 | FASTQ pair helper count | Oversized positive count can wrap and report false PASS | Source; tiny shell fixture | Bound helper arithmetic without changing other worker contracts |
| A01-68 | Installed wheel assets | Exact resource oracle omits 18 packaged non-Python files | Source; inventory comparison | Preserve wheel proof; decide critical or complete asset expectation |
| A01-69 | Step 08 annotation skips | Inconsistent transcripts are warned away without structured skip count | Source; guarded test characterized | Decide failure or quantified skip with scientific owner |
| A01-70 | Step 09 recorded paths | Relative paths depend on validator working directory | Source; owner contract | Define portable summary path policy without weakening hashes |
| A01-71 | Step 08 mixed UTR inputs | One-sided generic UTR suppresses derived fallback on other side | Source inference; test gap | Decide per-side fallback policy before changing annotation |
| A01-72 | FASTQ pair helper header | Two empty headers can be reported as matching read IDs | Source; tiny shell fixture | Define minimal header identity while retaining byte behavior |

## Discovery notes

### A01-01 — Step 07 selector validation false pass

**Supported behavior and failure.** Step 07's validation report should reconcile the declared region selector with the output transaction. `src/emrys/libraries/validation/mpileup.py:130-153` checks a region-file row for a known contig but does not establish its coordinate bounds. The owner emits this as `selector_reconciliation` in `src/emrys/stages/partitioned_cohort_mpileup/validator.py:138-150`. A retained test at `tests/stages/partitioned_cohort_mpileup/test_validate_step_07_mpileup_outputs.py:424-445` explicitly expects an all-pass report for a BED end beyond the FAI bound. The owner contract at `src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md:90-103` states a limited validator ceiling.

**Surviving defenses and next step.** Project admission and the producer check selectors before work; receipt and sample checks protect other properties. Those defenses do not establish that an existing Step 07 validation report proves selector bounds. Retain the characterization. Trace every consumer of this report, then decide the owner's required validation ceiling before proposing a fix.

### A01-02 — Selector syntax differs across owners

Project admission uses `str.isdigit()` before integer conversion (`src/emrys/orchestration/run_coordinator/onboarding.py:1645-1651`); the Step 07 producer requires ASCII `[0-9]+` (`src/emrys/stages/partitioned_cohort_mpileup/producer.py:131-136`). `src/emrys/contracts/SOURCE_TOPOLOGY.md:45` records this disparity. An admitted Project selector therefore may not be accepted by the worker. This is a source-level mismatch, not a reproduced Run failure. Decide the supported coordinate syntax, inspect Project-side tests and all selector readers, and preserve producer refusal until caller-complete parity is demonstrated.

### A01-03 — CI whitespace check does not inspect committed changes

`scripts/make_quality.mk:211-219` runs `git diff --check` inside `validation-static`. The CI job first checks out the commit and runs that target (`.github/workflows/ci.yml:173-185`); the command inspects unstaged worktree changes rather than the committed PR range. The local command remains useful for local edits. The checkout at `.github/workflows/ci.yml:118-122` does not request full history. Specify an event-aware committed comparison range, fetch enough history, and verify the file types before changing the gate.

### A01-04 — Validation inventory assertion misses source owners

`tests/contract_integration/validation_rosters/test_validation_check_rosters.py:84-95` says it checks the exact live validator inventory, but scans `scripts/validate_step_*.py`. The listed validators reside under `src/emrys`; the scan and its expected script subset are both empty at this commit. The test still confirms that its named paths exist and that its two lists agree. Owner tests separately compare emitted reports with literal rosters. The gap is discovery of a *new* source-owned validator. Find an existing authoritative owner roster before adding another inventory list.

### A01-05 — Central roster mutation multiplication

The same test file parametrizes generic roster mutations over all listed steps (`:98-146`). Its shared report validator has no step-specific branches (`src/emrys/libraries/validation/report.py:83-111`). Reordering a one-check roster produces the same order, so that acceptance case cannot probe an ordering defect. Candidate reduction is representative one-check and multi-check helper cases, while retaining every owner's literal expected roster and actual emitted-report assertion. First map the distinct faults and measure cost under `QUAL-01`.

### A01-06 — Canonical document names and headings

`scripts/documentation/validate_structure.py:14-34,199-206` requires 19 named documents and an H1 somewhere in each. `first_heading` (`:120-126`) accepts any nonempty H1 text, regardless of position. `tests/documentation/test_validate_structure.py:158-176` explicitly accepts a renamed Workflow title. Thus the gate protects file presence and some heading structure, not document identity or first-line placement. The test fixture mirrors the 19 names at `tests/documentation/test_validate_structure.py:17-37`, but its negative test (`:179-195`) exercises only Workflow, Runbook, and Troubleshooting, with no assertion that fixture and production rosters match. Assess each path's owner obligation and the intended heading rule. Preserve owner-directory and local-link checks that catch distinct failures.

### A01-07 — Anchor parser and tilde fences

Local link targets and anchors are checked in `scripts/documentation/validate_structure.py:164-196`. Its anchor extractor (`:129-147`) toggles fenced-code state only for backticks, although CommonMark also permits tilde fences. A heading-looking line inside a tilde fence could therefore satisfy a link to a nonexistent heading. An isolated local call to `markdown_anchors` on a temporary file containing only a tilde fence and `# phantom` returned `phantom` as an anchor. This does not establish the full documentation check's behavior under every input. Correct the parser boundary while retaining local-link validation.

### A01-08 — Mermaid gate ceiling

`scripts/documentation/validate_structure.py:235-251` verifies a standalone Mermaid declaration and rejects Markdown fences in Mermaid source. It does not parse the whole diagram. `scripts/documentation/README.md:3-18` describes this narrow role. No removal or expansion follows merely from the narrow scope. Determine whether a distinct diagram failure merits an established parser or renderer, and account for its maintenance cost.

### A01-09 — Hosted resource fixture independence

`tests/test_ci_workflow.py:411-479` executes the workflow's fixture-generating text and admits the result through production profile and resource-policy code. `tests/tools/real_synthetic_e2e.py:463-476` starts from packaged policy defaults; `tests/test_real_synthetic_e2e.py:202-220` compares much of its result with those same defaults. These are useful wiring and admission checks but not independent oracles for every default value. Inventory the literal owner-policy tests and the exact fixture claims before replacing any assertion. Hosted CI does not establish Viking utilization or performance.
### A01-10 — Reporting adapter fixture independence

`tests/reporting/fixtures/artifact_adapters_v1/build_fixture.py` derives parts of expected headers and row counts from the production adapter registry. `tests/reporting/test_artifact_adapters.py:236-250` compares inventory rows with the template the builder also reads, while retaining a literal count of 74 and registry checks. The comparison can catch builder drift but cannot independently establish that the template itself is correct. Map literal headers, row identities, and independent contract goldens before changing this fixture.

### A01-11 — Reporting roster identity defect

`tests/reporting/test_artifact_adapters.py:585-604` characterizes completion of a validation artifact after its checks are reordered or one unique ID is replaced. `src/emrys/reporting/_artifact_index/README.md:62-69` directs that these tests remain until the defect is resolved. The shared report validator also accepts reordering in `tests/contract_integration/validation_rosters/test_validation_check_rosters.py:135-146`. Retain both characterizations. `REPORT-ROSTER-01` must settle required membership and order before a fix or test retirement.

### A01-12 — Shell mode contract needs an owner decision

`tests/test_public_cli_contracts.py:147-154,860-864` requires three internal workers to remain nonexecutable and labels that condition a characterized defect. The same suite exercises their help and refusal paths through Bash (`:829-843`); the planner invokes an admitted shell route. Directly invoked helpers may have a different contract. Decide script by script whether direct execution is supported, retain real public entrypoint checks, and avoid asserting executable-bit policy solely from a file's location.

### A01-13 — Negative private reporting CLI assertion

`tests/orchestration/run_coordinator/test_reporting_boundary.py:949-951` asserts that private parser functions are absent. It does not exercise a supported command. `tests/test_public_cli_contracts.py:754-779` separately verifies that the retired public `build run-summary` route refuses without side effects. Confirm whether any supported caller directly imports the private parser before considering the negative assertion redundant; retain public CLI refusal coverage.

### A01-14 — Duplicate R lexical helpers

Step 09 and the optional projection repeat equivalent scalar safe-ID and 64-hex hash checks in `src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_common.R:108-122` and `src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/scientific_context_projection.R:131-145`. Both already source `src/emrys/libraries/input_contract.R`. A caller-complete move into that existing library may reduce maintained product code. Step 08's similar helper lacks the same scalar guard and cannot be included without a parity decision. Enumerate callers and negative R cases, preserve owner-specific scientific checks, and quantify the full change before proposing it.

### A01-15 — Publication checks protect separate boundaries

`src/emrys/libraries/validation/publication.py:41-56` validates staged bytes, an existing predecessor, and visible final bytes at distinct mutation boundaries. Tests cover malformed inputs and rollback (`tests/libraries/test_validation_report.py:331-352,431-478`). These calls are a **retain** finding, not duplicate validation. Separate retained tests (`:507-572`) characterize known recovery gaps documented in `src/emrys/libraries/validation/README.md:18-29`; they require owner-scope resolution, not removal through this audit.

### A01-16 — Versioned schema names do not establish obsolescence

The schema registry selects active files and IDs at `src/emrys/contracts/orchestration/api.py:22-71,208-249`; `src/emrys/contracts/schemas/README.md:8-19` describes the versioned resources. Contract tests reject old selectors and protect registry identity (`tests/contracts/orchestration/test_orchestration_contracts.py:438-491`). Current-version earlier Attempts and retained evidence remain meaningful under `docs/design/decisions/platform-direction.md:14-28`. Preserve these defenses. Review only concrete unregistered files or fields after tracing references.

### A01-17 — Make recipes and static checks

`tests/test_public_cli_contracts.py:876-923` inventories Make targets and dry-runs their command expansions against a large fixture. Exact operator mutation commands merit protection; an internal recipe snapshot may be more restrictive than its supported behavior. `scripts/make_quality.mk:207-233` runs a fixed shell syntax roster and all-tracked-file ShellCheck in different targets; `smoke` exposes the syntax check separately. `report-test` and `smoke` have no identified in-repository caller, which does not establish that operators do not use them. Decide each target's supported use and failure before retiring a snapshot or gate. Also inspect the unused `SHFMT_BIN` setting without adding another formatter by default.

### A01-18 — Dependency source and artifact checks

`tests/test_validation_orchestrator.py:60-90` pins source dependency declarations and group wiring. `tests/test_package_distribution.py:192-222` checks dependencies in built wheel metadata. These partly overlap but inspect different representations: the former can detect source-list drift, the latter packaging drift. Compare the exact failures caught by source literals, lockfile checks, and wheel inspection before proposing selective consolidation; retain installed-artifact protection.

### A01-19 — Manual Step 05 operator check

`tests/data_checks/validate_step05_outputs.sh` performs site-specific checks of existing BAM/BAI outputs, can query Slurm, writes a selected status TSV, and probes output-directory writability. `tests/data_checks/README.md:1-7` explicitly retains it and limits its evidence claim. No in-repository caller was found; that is insufficient to call an operator script obsolete. Establish whether operators still use it, which faults it alone catches, and how its outputs are retained. Do not run it as part of a local source audit.

### A01-20 — Step 07 VCF semantics are outside the report ceiling

`tests/stages/partitioned_cohort_mpileup/test_validate_step_07_mpileup_outputs.py:448-462` writes malformed REF, symbolic ALT, and broken FORMAT/sample data, then expects every validation row to pass. `src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md:90-96,115-119` limits the validator to shape and counts. This is another retained characterization of a passing report's meaning, separate from A01-01's selector bounds. Trace report consumers and decide whether a semantic admission check or clearer wording is required; do not delete the test as redundant.

### A01-21 — Step 08 candidate identity and order need a separate oracle

A test replaces candidate IDs with arbitrary unique strings and reverses rows while expecting all-pass (`tests/stages/cohort_candidate_preprocessing/test_validate_step_08_preprocessing_outputs.py:376-390`). The owner contract (`src/emrys/stages/cohort_candidate_preprocessing/CONTRACT.md:121-129,143-146`) says the Python report checks internal structure, not reconstructed IDs or deterministic order. Guarded real-R tests assert literal candidate order and worker-count byte determinism (`tests/stages/cohort_candidate_preprocessing/test_step_08_vcf_preprocessing.R:619-635,873-885`). Retain both evidence layers; a passing Python report alone does not prove the producer's scientific reconstruction.

### A01-22 — Step 09 validation does not recompute CMH statistics

`tests/analyses/paired_cmh_candidate_ranking/test_validate_step_09_cmh_outputs.py:282-335` fabricates CMH statistics, p-values, adjusted values, and odds ratios while the report passes. `src/emrys/analyses/paired_cmh_candidate_ranking/CONTRACT.md:105-113` states this ceiling. A production-independent Python oracle and guarded R corpus cover numerical behavior (`tests/analyses/paired_cmh_candidate_ranking/test_step_09_cmh_oracle.py:108-178`; `tests/analyses/paired_cmh_candidate_ranking/test_step_09_cmh_editing_site_calling.R:222-313`). Preserve the characterization and independent oracles, and avoid promoting report status to scientific proof.

### A01-23 — Step 00b agreement shares producer normalization

`src/emrys/stages/gtf_to_bed12/validator.py:48-59` calls the converter's `normalize_gtf` before comparing expected and observed BED12 lines. Its contract (`src/emrys/stages/gtf_to_bed12/CONTRACT.md:75-79`) explicitly says this is same-owner normalization, not an independent implementation. Literal converter tests (`tests/stages/gtf_to_bed12/test_gtf_to_bed12.py:65-389`) protect coordinates, names, and order independently. Keep both protections. Check report wording and actual GTF semantics before proposing another production parser.

### A01-24 — Step 02b quickcheck producer and validator disagree

On zero exit, the producer retains nonempty native `samtools quickcheck -v` output (`src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh:52-62`), while the validator accepts only the synthetic empty-success PASS line (`src/emrys/evidence/canonical_bam_qc/validator.py:47-53`). Owner tests characterize each side (`tests/evidence/canonical_bam_qc/test_step_02b_bam_qc.sh:88-93`; `tests/evidence/canonical_bam_qc/test_validate_step_02b_bam_qc.py:109-125`), and the contract (`src/emrys/evidence/canonical_bam_qc/CONTRACT.md:102-111,133-140`) records the mismatch. Decide which zero-exit output is admissible before a caller-complete producer, validator, adapter, and test change. Retain the tests until then.

### A01-25 — Canonical BAM acceptance differs across producer and validator

`src/emrys/stages/canonical_bam/CONTRACT.md:137-147,182-186` records that the validator permits a zero-record BAM and omits producer-required `LB` and `PL:ILLUMINA` fields. Neither surface proves that the BAI/CSI belongs to the BAM. These are distinct boundaries, not duplicate checks; source inspection alone does not reproduce a false pass. The contract also leaves open whether Stage 02 remains separate now that STAR normally emits canonical bytes. Resolve accepted BAM/RG semantics first; a stage-retirement proposal must trace sort, index, hard-link reuse, fan-out, artifact identities, receipts, and recovery.

### A01-26 — Reference provenance recovery fault test must remain

`tests/evidence/reference_provenance/test_reference_provenance.py:466-518` injects publication and restoration failures and characterizes surviving backups without a lock or recovery marker. The owner README (`src/emrys/evidence/reference_provenance/README.md:27-39`) and existing polish campaign (`docs/tasks/polish-campaign.md:265-274`) already route that recovery work. Preserve the fault test and its evidence limit. Do not create a duplicate ASSURANCE implementation task or retire the test because it currently documents a defect.

### A01-27 — Step 06 count checks do not recount BAMs

The producer test permits an internally inconsistent flag subcount to be emitted (`tests/stages/mechanical_orientation/test_mechanical_orientation_producer.py:248-255`); the validator test catches count arithmetic (`tests/stages/mechanical_orientation/test_validate_step_06_orientation_outputs.py:113-127`). The contract (`src/emrys/stages/mechanical_orientation/CONTRACT.md:75-80,95-99`) says validation does not recount BAMs, inspect flags, quickcheck, or establish BAM/BAI correspondence. Retain both checks for their distinct failures. A passing orientation report proves its stated container and count-table checks, not independent BAM partition semantics.

### A01-28 — All-pass is not an exact-roster oracle

`src/emrys/orchestration/run_coordinator/all_pass.py:64-111` requires a nonempty report, unique passing rows, matching step/scope, and a bound hash, but accepts arbitrary check-ID membership. `tests/orchestration/run_coordinator/test_all_pass.py:46-112` deliberately uses invented IDs. Exact owner rosters have a separate publication check (`src/emrys/libraries/validation/report.py:83-111`) and literal owner expectations. Preserve both boundaries; describe all-pass as report status and content evidence, not independent roster proof.

### A01-29 — Real workflow engine with test-owned science

`tests/orchestration/run_coordinator/fixtures/workflow.py:1,20-47` uses the real Snakefile/profile but substitutes no-science commands and builds a production-derived adapter registry. `tests/orchestration/run_coordinator/test_workflow.py:256-397,474-668` exercises scheduling, reuse, and recovery; the fixture README (`tests/orchestration/run_coordinator/fixtures/README.md:1-3`) limits its claim. Retain these orchestration fault checks. They do not prove scientific computation or institutional execution. Separately, `tests/orchestration/run_coordinator/test_profile.py:27-201,271-306` pins 13 task owners and 70 artifact templates as literal expectations and should not be retired as a duplicate of this generated fixture.

### A01-30 — Scheduler fixture case multiplication

`tests/orchestration/run_coordinator/test_slurm_submission.py:1482-1609` expands three request versions, three cluster arrangements, and four states into 36 cases around shared observation logic. Each axis represents a real contract, but every combination may not detect a distinct fault. Measure cost and map branch/fault coverage under `QUAL-01` before proposing representative cases. Preserve identity-drift and usage fault tests at `:1611-1741`.

### A01-31 — Scheduler response cap is after capture

`src/emrys/orchestration/run_coordinator/scheduler_observation.py:54-68,208-218` captures subprocess stdout before rejecting replies over 64 KiB. The coordinator contract (`src/emrys/orchestration/run_coordinator/CONTRACT.md:487-496`) acknowledges that capture memory is not strictly bounded. Oversized-byte tests (`tests/orchestration/run_coordinator/test_slurm_submission.py:1922-1956`) protect admission of a reply, not process-memory bounds. Retain that defense and do not report it as a bounded capture proof.

### A01-32 — Prepared-finalization continuity has a stated limit

`tests/orchestration/run_coordinator/test_lifecycle.py:1875-1919,2194-2256` tests distinct-inode equal-byte substitution and preview/confirmation behavior. The owner contract (`src/emrys/orchestration/run_coordinator/CONTRACT.md:1021-1027`) says inode recycling under the same UID remains indistinguishable. Retain exact-byte, device/inode, and recovery tests; their passing status cannot establish continuity through recycled-inode substitution.

### A01-33 — Historical records and internal Task remain supported

`src/emrys/orchestration/run_coordinator/CONTRACT.md:414-427` keeps v1-v3 submission contexts readable for historical diagnosis, with their original identity limits. `tests/orchestration/run_coordinator/test_task.py:2509-2552` exercises the internal Task module that `src/emrys/workflow/Snakefile:280` actually invokes. These tests protect distinct supported diagnostic and execution paths. Neither is obsolete merely because its name says historical or private.

### A01-34 — Runtime checks establish different evidence levels

`src/emrys/evidence/runtime_availability/README.md:3-38,106-134` separates selected tool probes, empty-Snakemake startup, Slurm compute qualification, and Run success. Real local startup coverage (`tests/evidence/runtime_availability/test_runtime_availability.py:241-300`) differs from synthetic Doctor scenarios (`tests/orchestration/run_coordinator/test_doctor.py:2553-2610`). Preserve both. The fixed-content runtime seal excludes shared libraries, shebang interpreters, transitive R dependencies, and the full managed directory (`src/emrys/evidence/runtime_availability/README.md:70-103`); neither fixture qualifies Viking. CI's managed golden path runs on PRs, while real synthetic E2E is scheduled or manually selected (`.github/workflows/ci.yml:407-414,1099-1105`).

### A01-35 — Stage-map gate checks owner presence, not full identity

`scripts/documentation/validate_structure.py:211-232` counts 14 slug rows matching a raw-line pattern anywhere in `src/emrys/contracts/STAGE_MAP.md` and requires adjacent README, CONTRACT, and test directories. It does not parse the identity table's machine-key or alias columns; matching rows in a fenced example could satisfy the count. This is a source inference, not a reproduced documentation-gate failure. Preserve owner-presence checks and compare the remaining identity obligations with existing machine-key contract tests before altering the parser.

### A01-36 — Reporting target's selected tests need a promise

`scripts/make_quality.mk:199-205` runs five reporting test files via `report-test` but omits `tests/reporting/test_artifact_adapters.py`, which protects active adapter semantics. `tests/test_validation_orchestrator.py:101-111` confirms target wiring, not completeness. The full Python suite still collects adapter tests, so this is a manual-target ceiling, not a CI omission. Define whether `report-test` promises all reporting protection or a quick subset before changing it.

### A01-37 — Duplicate Snakemake dependency declaration

`pyproject.toml:31,59-61` declares `snakemake==9.25.1` as a runtime dependency and the sole workflow-group dependency. The repository's current `uv` commands still install project dependencies when selecting the workflow group; local help inspection supports this reading, without running a sync. This is a concrete configuration-reduction candidate. Before retiring the duplicate group entry, inspect lockfile behavior, CI commands, operator instructions, and the reason for the named group. Keep the runtime dependency.

### A01-38 — Installed-wheel smoke does not prove Git-build provenance

`tests/test_package_distribution.py:138-176` builds from a staged source copy without `.git` and later expects a report receipt with `git_commit` equal to `unavailable` (`:590-600`). The test meaningfully protects built-wheel resources and installed commands. It does not prove commit provenance for a wheel built inside a Git checkout; that needs separate evidence if claimed. Retain the installed-artifact checks.

### A01-39 — Shard timing policy is separate from completeness proof

`tests/tools/python_test_shards.py:139-144` fails planning when a duration estimate names a node ID absent from collection, although estimates schedule work rather than define correctness. Each of four shards recollects the full suite (`:253-256`), and receipt verification recollects it again (`:366-371`). The verifier proves exact complete/disjoint selection (`:299-357`), not that `estimated_seconds` is a measured duration. Measure collection cost and decide whether a stale scheduling estimate should block the suite under `QUAL-01`; preserve receipt proof.

### A01-40 — Source topology has an executable parity defense

`tests/test_source_dependencies.py:476-518` parses the documented CLI seams and source transitions in `src/emrys/contracts/SOURCE_TOPOLOGY.md` and compares them with the executable rosters. This is a surviving defense against documentation/code drift, in addition to the source-direction check. An ad hoc source comparison found the 25 seams and 22 transitions agree at the pinned commit; it was not a product test run. Retain the parity test and avoid adding a parallel policy registry.

### A01-41 — Compressed Step 07 selectors are falsely failed

Project admission and the Step 07 producer read gzip region files (`src/emrys/orchestration/run_coordinator/onboarding.py:1617-1628`; `src/emrys/stages/partitioned_cohort_mpileup/producer.py:106-169`). The validator reads the gzip bytes as text in `src/emrys/libraries/validation/mpileup.py:142-153`. A retained test expects `selector_reconciliation=fail` for a valid `.bed.gz` (`tests/stages/partitioned_cohort_mpileup/test_validate_step_07_mpileup_outputs.py:397-421`), while Project and producer tests cover accepted gzip input (`tests/orchestration/run_coordinator/test_onboarding.py:2500-2534`; `tests/stages/partitioned_cohort_mpileup/test_partitioned_cohort_mpileup_producer.py:347-368`). The Run task requires semantic all-pass before verified publication (`src/emrys/orchestration/run_coordinator/task.py:2771-2807`), so source composition implies this supported path is blocked; no live Run was executed. Preserve gzip support and the characterization, then decide caller-complete selector parsing and identity binding.

### A01-42 — Reporting rejects owner-valid BED12 strand

The Step 00b converter, shared BED12 validator, and literal producer test accept strand `.` (`src/emrys/stages/gtf_to_bed12/converter.py:12,52-66`; `src/emrys/libraries/alignments/bed.py:44-49`; `tests/stages/gtf_to_bed12/test_gtf_to_bed12.py:200-206`). The registered reporting reader permits only `+` or `-` (`src/emrys/reporting/_artifact_index/_text_genomic.py:176-208`), and adapter failure marks a present source failed (`src/emrys/reporting/_artifact_index/inspection.py:200-213`). The exact reader function, executed in isolation on the owner-test BED12 row, raised `ArtifactIndexError`; a full artifact transaction was not run because local dependencies were unavailable. Preserve the owner validator; decide reporting parity and add a reporting regression at its own boundary.

### A01-43 — Read-group report checks are narrower than record tags

The shared header parser checks one exact `@RG` with matching ID/SM (`src/emrys/libraries/alignments/bam.py:56-65`); Step 04 and Step 05 validators use it without recounting alignment tags (`src/emrys/stages/duplicate_marking/validator.py:60-67,96-100`; `src/emrys/stages/split_n_cigar/validator.py:88-96,127-131`). Step 05's worker checks every record's RG count (`src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh:95-101`), while Step 04's worker does not. Validator fake samtools fixtures support quickcheck/header only, so they cannot exercise record-tag mismatch. Retain Step 02 and Step 05 worker tag defenses. Decide whether either validation report must attest per-record preservation before adding or retiring a check.

### A01-44 — Step 05 worker accepts broader header text

`src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh:84-93` uses grep and substring checks for coordinate sort and RG ID/SM, whereas `src/emrys/libraries/alignments/bam.py:56-65` requires exact tab-delimited tokens. For example, a sort token containing `SO:coordinate` as a prefix could pass the worker's header check and fail validation; other worker checks still apply. Native tests cover `SO:unknown` but not a prefix mutation (`tests/stages/split_n_cigar/test_step_05_split_n_cigar_reads.sh:238`). This is source inference, not a reproduced Run. Preserve exact validator parsing and decide the worker's admitted header grammar before adding a focused native negative case.

### A01-45 — Storage JSON parsing accepts ambiguous syntax

`src/emrys/evidence/storage_inventory/qualification.py:330-337` calls plain `json.loads` for a purportedly strict object. An isolated helper call accepted both a duplicate key and `NaN`; `tests/evidence/storage_inventory/test_storage_inventory.py:595-607` only rejects malformed JSON and non-object input. Other contract loaders reject duplicate keys and nonstandard constants. The same helper also decoded isolated UTF-16 and UTF-32 object bytes despite labeling errors "not valid UTF-8 JSON"; the writer emits ASCII JSON. Later storage receipt field, identity, and snapshot checks still protect distinct properties; this finding does not claim a complete forged receipt is admitted. Decide whether storage records require the same strict JSON grammar, then add focused reader cases without removing later checks.

### A01-46 — Storage receipt generation scan can raise raw ValueError

`src/emrys/evidence/storage_inventory/qualification.py:212-232` accepts a candidate suffix with `isdigit()` and then calls `int()`. A temporary evidence directory containing `q.direct-qualified.².json` caused an isolated call to raise raw `ValueError`. Existing tests cover ordinary successors and pending publication, not malformed generation names. Decide whether malformed names fail closed or are ignored, preserving immutable receipt identity and staged-marker checks. This helper reproduction does not establish a full Doctor or Run failure.

### A01-47 — Tracked Viking profile duplicates resource defaults

`configs/execution_profile.csu_viking_ev_pum1.yaml:4-43` repeats the packaged resource policy in `src/emrys/orchestration/run_coordinator/resources/default_execution.yaml:2-41`. The resource content matches; the tracked example adds placement comments after it. A placement-only example exists (`configs/execution_profile.example.yaml:1-21`), and Project creation emits a placement-only Viking default (`src/emrys/orchestration/run_coordinator/execution_profile.py:66-89`). This is a concrete configuration-reduction candidate, not an approved edit. Establish whether the full tracked illustration serves an operator need, then preserve Viking placement and admission tests if reducing it.

### A01-48 — Static print checks do not establish printed fit

`tests/reporting/test_report.py:695-735` names a nonoverflow print-layout test but asserts CSS source substrings. `tests/reporting/test_figures.py:654-665` checks declared SVG height. These can catch removed rules and geometry declarations, but neither renders a printed page or proves pagination and overflow. Keep HTML structure, accessibility, and rendered-semantic checks (`src/emrys/reporting/_run_report/validation.py:362-475`; `tests/reporting/test_report.py:737-999`). Clarify the static evidence claim or define a separate visual/PDF oracle if print fit is accepted.

### A01-49 — PDF structure check has a narrow acceptance ceiling

`src/emrys/reporting/_artifact_index/binary_readers.py:221-265` checks a PDF header, terminal startxref/EOF, and selected xref/trailer tokens without resolving the catalog or pages. Its exact function accepted, in isolation, a 117-byte PDF-like file with `/Root 999 0 R` and no objects. The fixture proves only adapter-level acceptance, not a complete artifact transaction. Retain current signature, xref, transaction, and Step 09 numerical checks. Decide whether “complete” should assert renderability before considering a maintained parser or renderer.

### A01-50 — RSeQC reports are mechanical, not manifest policy

The Step 03 worker publishes nonempty RSeQC output; the validator checks three exact finite fractions and their sum (`src/emrys/evidence/rseqc_orientation/validator.py:59-76`). It receives no BAM, index, BED12, tool identity, or Attempt receipt, and no computational stage derives manifest strandedness from it (`src/emrys/evidence/rseqc_orientation/CONTRACT.md:18-29,72-107`). Producer and validator tests retain different malformed-output boundaries. Preserve those protections and the independent declared strandedness policy; a passing fraction report is not biological strand classification.

### A01-51 — Reporting duplicates QC lexical parsers with different results

`src/emrys/reporting/_artifact_index/inspection.py:259-294` parses flagstat and RSeQC separately from `src/emrys/libraries/evidence/qc.py:8-62`, used by their validators. The reporter rejects blank flagstat lines but overwrites duplicate total/mapped rows; the shared parser ignores blanks and reports duplicate rows. Reporter RSeQC accepts any matching fraction label, while the owner parser requires three exact labels and catches duplicates/nonfinite values. Metric projection and owner validation are different boundaries. Map artifact status and exact inputs before considering reuse of lexical parsing; do not silently unify pass/fail policy.

### A01-52 — Shared reference parsers leak raw errors

`src/emrys/libraries/references/contigs.py:27-31,65-70` raises raw `IndexError` for a whitespace-only FASTA header and raw `ValueError` for a Unicode DICT length. Tests explicitly characterize both (`tests/libraries/test_reference_contigs.py:98-102,220-228`); focused local calls reproduced them. Project admission, Step 00c validation, and reference provenance catch their declared parser error but not both raw types (`src/emrys/orchestration/run_coordinator/onboarding.py:789-796`; `src/emrys/stages/fasta_sidecars/validator.py:68-74`; `src/emrys/evidence/reference_provenance/_reference_contigs.py:105-123`). Provenance STAR-length parsing has a related `isdigit()`/`int()` path. Normalize malformed-input errors at the shared boundary or map all callers together, retaining valid contig/order semantics and controlled report behavior.

### A01-53 — Step 07 receipt parsing can escape its exit contract

`src/emrys/libraries/validation/tsv.py:51-55` uses permissive `csv.DictReader` for the Step 07 receipt, then `src/emrys/stages/partitioned_cohort_mpileup/validator.py:125-169` directly indexes and assumes field values. The owner contract (`src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md:98-103`) records that some missing-field shapes can raise `KeyError` or `AttributeError` with traceback and exit 1 instead of controlled exit 2. This is source plus contract evidence, without a new runtime reproduction. Preserve exact receipt and check identities; evaluate the existing strict TSV reader only after its behavior is compared for every caller.

### A01-54 — Public manifest pass is weaker than Run admission

The legacy public manifest validator lists `condition` as required but accepts a blank value, prints “Conditions: none,” and checks sample IDs only for nonempty uniqueness (`src/emrys/ingestion/sample_manifest_admission/validator.py:18-21,120-175`). Step 08 requires nonempty condition, replicate, and safe IDs (`src/emrys/contracts/scientific_evidence/step08.py:326-353`). Tiny temporary fixtures confirmed that blank condition and `S/1` pass the public helper but fail Step 08. The existing test named “empty required fields fail” covers sample ID and FASTQ fields, not condition (`tests/ingestion/sample_manifest_admission/test_validate_manifest.py:190-203`). Decide the public command's promised scope; preserve Step 08's stricter Run-boundary refusal and intentional optional-replicate distinction.

### A01-55 — Step 00c final pair check omits uniqueness

`src/emrys/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh:57-111,128-149` parses FAI and DICT rows, sorts their name/length pairs, and compares the multisets. It has no duplicate-name rejection, although `src/emrys/stages/fasta_sidecars/CONTRACT.md:41-45` promises unique names. The independent validator parses all three inputs and requires ordered FASTA agreement (`src/emrys/stages/fasta_sidecars/validator.py:68-100`). This is a source-level postprocessing gap, not proof that samtools or GATK emit duplicate sidecars in normal use. Retain the validator; decide whether a faulty-tool producer case should enforce the worker's uniqueness promise. Its unordered comparison is already disclosed in the contract.

### A01-56 — Duplicate Picard header can hide malformed data

`src/emrys/libraries/quality/picard.py:19-42` tests required header membership, then converts the header and row to a dictionary, so a later duplicate column overwrites the first. The isolated exact function accepted `READ_PAIRS_EXAMINED` columns containing `bogus` then `10` and returned a passing summary. Step 04 uses that result for `duplication_metrics` (`src/emrys/stages/duplicate_marking/validator.py:68-70,102-107`). Tests protect normal and reordered headers but have no duplicate-header negative (`tests/libraries/test_shared_domain_helpers.py:225-261`). Reporting has its own similarly permissive metric projection (`src/emrys/reporting/_artifact_index/_text_genomic.py:231-258`); reconcile status and lexical policy before reuse. Preserve numeric bounds and native evidence checks. The reproduction did not execute Picard or a full Run.

### A01-57 — Validation stdout can precede a failed publication

The shared `--execute` path prints report bytes before rechecking input snapshots or publishing (`src/emrys/libraries/validation/runtime.py:27-49`). An isolated in-process fixture returned exit 2 and no report while stdout already contained a `pass` row after input mutation. Step 04/05 mutation tests protect exit and predecessor preservation, but do not assert that stdout (`tests/stages/duplicate_marking/test_validate_step_04_mark_duplicates.py:257-275`; `tests/stages/split_n_cigar/test_validate_step_05_split_ncigar.py:267-284`). Run requires validator exit 0 and a retained semantic all-pass report (`src/emrys/orchestration/run_coordinator/task.py:2765-2807`), so this does not establish a Run acceptance bypass. Decide whether stdout on `--execute` is preview or evidence before changing order; printing after commit also has failure semantics. Retain the authoritative exit, file, and hash-bound task evidence.

### A01-58 — BAM quickcheck report labels exceed the gate

`src/emrys/libraries/alignments/bam.py:32-44` treats `samtools quickcheck -v` as passing on exit 0 even with nonempty stderr, while Step 02, 04, and 05 report an expected value of "exit=0 with empty diagnostics" (`src/emrys/stages/canonical_bam/validator.py:99-104`; `src/emrys/stages/duplicate_marking/validator.py:84-89`; `src/emrys/stages/split_n_cigar/validator.py:115-120`). A fake-tool helper reproduction returned success with `warning-success` diagnostics. Step 02's contract already records this asymmetry (`src/emrys/stages/canonical_bam/CONTRACT.md:142-147`); owner success fixtures use empty stderr. Decide whether the report's expected text is descriptive or a gate across all three owners. Preserve quickcheck exit, header, and pair-container defenses.

### A01-59 — Profile nonroot pattern does not survive normalization

The v3-directory execution-profile schema's `absolute_nonroot_path` pattern accepts `/tmp/..` for `scratch_parent` and exact module init (`src/emrys/contracts/schemas/orchestration/v3/execution_profile.schema.json:17-20,37-40,120-121`). Source admission normalizes with `os.path.abspath`, producing `/` (`src/emrys/orchestration/run_coordinator/execution_profile.py:359-383`), and the placement document emits that normalized path (`src/emrys/orchestration/run_coordinator/execution_profile.py:153-172`). A standard-library regex/path reproduction confirmed the lexical transition; full profile admission was not run. The batch script independently rejects a root scratch parent before use (`src/emrys/orchestration/run_coordinator/slurm_submission.py:749-755`). Decide whether profile admission itself must reject normalized root, and whether module init has an equivalent guard. Preserve the batch refusal and path tests.

### A01-60 — Benchmark pass can mean process success only

The opt-in benchmark captures validator logs but sets trial `status=pass` from setup, producer, and validator exit codes plus optional artifact byte equality (`scripts/benchmark_stage_resources.py:461-510`). EMRYS validators can publish `status=fail` rows and return 0; Run separately invokes semantic all-pass (`src/emrys/libraries/validation/runtime.py:27-49`; `src/emrys/orchestration/run_coordinator/task.py:2765-2807`). Source composition therefore implies a benchmark manifest using an EMRYS owner validator could count a failed report in a successful repetition and recommendation. Existing benchmark tests cover nonzero exits and a passing result, not zero-exit failed rows (`tests/test_benchmark_stage_resources.py:156-264`). A tiny synthetic benchmark fixture ran the actual trial and summary code with an in-memory stub for unavailable PyYAML: validator stdout contained a failed TSV row, yet the script exited 0, wrote `status=pass`, and recommended the value. No native stage or cluster run occurred. Keep the raw trial logs and advisory-only boundary; decide whether the helper needs exact owner-report semantics or should call its result process success. `docs/operations/RUNBOOK.md:770-774` currently calls it validation status.

### A01-61 — Elevated shared-module floor is declared manually

`scripts/make_quality.mk:10-18,184-187` supplies a fixed list of six shared Python files to the elevated coverage check. `tests/tools/python_coverage_baseline.py:427-449` checks only paths passed as `--new-shared-module`; it does not discover newly added shared files. `docs/design/TEST_BASELINE.md:36-45` calls them "newly declared," which is accurate if declaration is the intended gate. The global and critical-owner nonregression checks remain (`tests/tools/python_coverage_baseline.py:407-424`). Decide who declares a new shared module and whether automation is needed before changing the floor or list. This is a gate-scope observation, not evidence of an uncovered new module.

### A01-62 — STAR mapping report does not reconcile percentages

`src/emrys/libraries/alignments/star.py:53-66` checks that each of three mapping percentages is syntactically valid and in 0..100; it does not reconcile their sum. Step 01 reports exactly that bounded claim (`src/emrys/stages/star_alignment/validator.py:105-110`), and its contract identifies the checks as container/report structure, not alignment proof (`src/emrys/stages/star_alignment/CONTRACT.md:102-106`). The all-pass fixture uses synthetic BAM bytes and a simple log (`tests/stages/star_alignment/test_validate_step_01_star_alignment.py:25-45`). Retain independent native and scientific evidence; decide whether inconsistent but individually bounded values need a distinct check. This is an evidence-ceiling and owner-decision candidate, not a demonstrated contract violation.

### A01-63 — DICT parser collapses duplicate tags within a row

`src/emrys/libraries/references/contigs.py:61-72` converts DICT `@SQ` fields to a dictionary, retaining the last value for duplicate tags. `tests/libraries/test_reference_contigs.py:29-46` explicitly characterizes `SN:old` followed by `SN:chr1` as `chr1`. This differs from the parser's separate duplicate-contig-name rejection across rows and the raw conversion errors in A01-52. Decide whether multiple `SN` or `LN` fields in one row are a supported projection or an ambiguity that should fail. Keep ordered FASTA/FAI/DICT reconciliation and caller error behavior in scope; no full provenance or Run fixture was executed for this note.

### A01-64 — Benchmark recommendation can omit failed repetitions

`scripts/benchmark_stage_resources.py:322-366` filters to passing trial rows before grouping resource values, then recommends by the passing subset's median. The exact summary helper, given one pass and one fail for the same case/value, wrote `successful_repetitions=1` and `recommended=yes`. The outer benchmark still exits nonzero when any trial fails (`scripts/benchmark_stage_resources.py:477-510`), and raw trial rows remain, so this is a misleading advisory summary rather than suppressed aggregate failure. `docs/tasks/backlog_matrix.md:173` and `docs/tasks/optimization_campaign.md:364-370` explicitly require rejecting a candidate with any failed repetition. Existing summary tests include an entirely failed value, not a mixed one (`tests/test_benchmark_stage_resources.py:267-310`). Preserve raw rows and exit behavior; condition recommendation on every planned repetition or label incomplete candidates.

### A01-65 — Launch exception can strand a local validation lane

`tests/tools/run_validation.py:269-297,391-394` starts concurrent lanes sequentially and re-raises a failed spawn. The `finally` block closes log handles and restores signal handlers but does not terminate already started process groups (`tests/tools/run_validation.py:490-495`); cancellation occurs for observed nonzero exits or interrupts (`tests/tools/run_validation.py:395-413,466-487`). A tiny two-lane fixture reproduced the gap: the second executable was missing, the call raised `FileNotFoundError`, and the first child wrote a marker afterward. Existing tests cover peer failure and SIGINT cleanup (`tests/test_validation_orchestrator.py:407-559`), not launch exceptions. Preserve current process-group termination and retained diagnostics, and define cleanup for internal launch failure. No full `make all-checks` or long lane was run.

### A01-66 — Storage compute receipt nested root can escape refusal

`src/emrys/evidence/storage_inventory/qualification.py:480-515` validates the outer compute receipt row but calls `row.get("root", {}).get("path")` without requiring `root` to be a mapping. An isolated helper call using an otherwise shaped row with `"root": null` raised raw `AttributeError`; the CLI catches only `StorageQualificationError` (`src/emrys/evidence/storage_inventory/qualification.py:881-914`). Existing malformed-receipt tests cover outer fields, execution identity, roster, role, probe and hash, but not nested root type (`tests/evidence/storage_inventory/test_storage_inventory.py:628-668`). This is a malformed retained compute-receipt path, not a full Doctor or Run reproduction. Preserve root snapshots, immutable identity, and later final-receipt checks while normalizing the nested refusal.

### A01-67 — Oversized FASTQ read count can report a false pass

The shared shell lexical check accepts any-length ASCII positive decimal (`src/emrys/libraries/file_checks.sh:50-55`). The optional pair diagnostic compares and iterates `--num-reads` using Bash integer arithmetic (`src/emrys/ingestion/sample_manifest_admission/check_fastq_pairs.sh:133-170`). Tiny one-record FASTQ fixtures showed `--num-reads 2` correctly failed, while `18446744073709551617` exited 0 and printed a PASS for that asserted count after one record. Ordinary-value tests protect mismatch and short-file behavior (`tests/ingestion/sample_manifest_admission/test_check_fastq_pairs.py:189-239`). This is a shell diagnostic false success for an extreme operator input, not a Run or scientific acceptance result. The positive-integer helper is also used by stage workers, so any bound or decimal-safe comparison needs caller range review rather than a blind shared change.

### A01-68 — Wheel resource oracle covers only part of packaged data

`pyproject.toml:75-120` currently declares package-data patterns for 61 tracked assets. The installed-wheel test's literal `RESOURCE_PATHS` lists 43, and its exact membership and source-byte comparison is limited to that list (`tests/test_package_distribution.py:46-90,192-243`). A read-only pattern expansion found 18 omitted assets, including five Step 08 R helpers and the shared R input contract. Step 08 dynamically sources those helpers (`src/emrys/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.R:314-341`). The later installed probe hashes present implementation files and checks task producer paths (`tests/test_package_distribution.py:488-502`), but does not establish that every helper child exists and matches source. Current globs include them, so no present wheel defect is demonstrated. Preserve isolated installed CLI/report tests and decide whether a complete tracked-asset expectation or exact critical-helper roster is needed.

### A01-69 — Step 08 annotation skip has no structured count

`src/emrys/stages/cohort_candidate_preprocessing/_step_08_annotation.R:83-109` warns and excludes transcripts with conflicting chromosome, strand, or gene information. A guarded R fixture explicitly expects that warning and skip (`tests/stages/cohort_candidate_preprocessing/test_step_08_vcf_preprocessing.R:823-844`). The Step 08 input receipt and summary count VCF records, alleles, supported SNVs, symbolic/non-SNV skips, and published candidates, but no annotation transcript skips (`src/emrys/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.R:27-44,183-205,252-273`). The warning can remain in task logs; this finding concerns structured transaction evidence, not a claim that all audit evidence vanishes. Decide with the scientific owner whether such input should fail or have a retained quantified skip before changing the model or its tests. No new R run was performed.

### A01-70 — Step 09 relative paths depend on consumer cwd

The Step 09 R summary records CLI input path spellings (`src/emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_output.R:44-51`). Its Python consumer resolves a relative recorded path against the consumer's current working directory before comparing explicit inputs (`src/emrys/contracts/scientific_evidence/step09.py:244-248,863-871`). The owner contract already states this retained boundary (`src/emrys/analyses/paired_cmh_candidate_ranking/CONTRACT.md:130-135`). The arbitrary-cwd validator test uses absolute fixture paths, so it does not exercise producer/consumer cwd drift (`tests/analyses/paired_cmh_candidate_ranking/test_validate_step_09_cmh_outputs.py:200-235`). Preserve hash comparison and immutable Run records; decide portable path semantics for standalone invocations without inferring a current Run failure.

### A01-71 — Generic UTR source is chosen for both sides at once

`src/emrys/stages/cohort_candidate_preprocessing/_step_08_annotation.R:133-159` uses any generic UTR ranges as the shared source for both five- and three-prime assignment; it derives exonic ranges outside CDS only when no generic UTR exists anywhere for that transcript. A one-sided generic UTR therefore leaves the opposite side without derived fallback unless it has an explicit side-specific annotation. The contract describes exonic fallback and per-side explicit precedence (`src/emrys/stages/cohort_candidate_preprocessing/CONTRACT.md:38-43`). Guarded tests cover explicit annotations on both sides and no UTR annotations, but not mixed generic/derived input (`tests/stages/cohort_candidate_preprocessing/test_step_08_vcf_preprocessing.R:209-249,846-872`). This is source inference, not a real-R reproduction or biological classification. Set the intended mixed-input policy with the scientific owner before altering the range model.

### A01-72 — Equal empty FASTQ headers are treated as matching IDs

`src/emrys/ingestion/sample_manifest_admission/check_fastq_pairs.sh:49-57,148-170` removes an optional `@` and mate suffix, then compares the two normalized strings without requiring a nonempty ID. Two tiny four-line FASTQ files with blank first lines exited 0 and printed a PASS for one matched read ID. The script's help claims matching read IDs (`src/emrys/ingestion/sample_manifest_admission/check_fastq_pairs.sh:5-25`), while the owner guide correctly limits this helper's broader sequence/quality and provenance claims (`src/emrys/ingestion/sample_manifest_admission/README.md:10-13`). Existing success tests use valid headers, and short-file tests cover row count rather than empty identity (`tests/ingestion/sample_manifest_admission/test_check_fastq_pairs.py:90-135,210-240`). Define the minimal header identity promised by this optional diagnostic, preserving its deliberate byte handling and prefix-only comparison. This does not imply that a normal Run admits the fixture.

## Reduction and retirement inventory

These are concrete search targets for a smaller maintained system, not approved removals. A candidate is only actionable after its surviving defense, callers, and evidence level are established.

| Surface | Candidate and existing authority | Boundary to preserve |
|---|---|---|
| Product code | A01-14 identifies two equivalent R scalar ID/hash helpers already sourcing `src/emrys/libraries/input_contract.R`; `REDUCE-01` and `OPS-03` own broader simplification (`docs/tasks/backlog_matrix.md:66,171`) | Move all equivalent callers together; Step 08's guard differs; quantify net product-code reduction |
| Tests | A01-30's 36 scheduler combinations and A01-39's repeated suite collection are cost candidates under `QUAL-01` (`docs/tasks/backlog_matrix.md:155`) | Keep distinct scheduler faults, independent oracles, complete/disjoint shard proof, and exact receipts |
| Scripts | A01-17 and A01-36 ask which Make checks/targets operators use; `SETUP-02` explicitly defers whole-helper retirement of `scripts/benchmark_stage_resources.py` and its tests, CLI checks, and docs (`docs/tasks/backlog_matrix.md:173`) | Until retirement, preserve raw trials, failed-repetition refusal, and advisory limits; do not replace with parallel machinery |
| Schemas | `PROFILE-CONTRACT-01` proposes deriving `owner_tasks[].rule_name` and scope selectors only during a justified profile transition (`docs/tasks/backlog_matrix.md:176`); common safe-ID/hash patterns also repeat across schema families | Active versioned `$id` values and references protect different artifacts; no unilateral deletion or version bump for cleanup |
| Configuration | A01-37 records duplicate Snakemake dependency declaration; A01-47 records repeated Viking resource defaults | Preserve installed dependencies, placement admission, generated defaults, and operator examples before trimming |
| Documentation | Seven version-directory schema READMEs total 61 lines and partly repeat family indexes (`src/emrys/contracts/schemas/artifacts/README.md:1-10`; `src/emrys/contracts/schemas/orchestration/README.md:1-17`); `DOCS-01` owns compression (`docs/tasks/backlog_matrix.md:65`) | Transfer unique semantics and links before removal; keep current contract and operator discoverability |
| Mutable state | Old sealed runtime generations and selector references merit a reachability preview (`src/emrys/evidence/runtime_availability/README.md:76-95`); `CLEANUP-01` owns any future exact cleanup (`docs/tasks/backlog_matrix.md:100`) | Retained Run/Attempt selectors, Project borrowers, and failure claims block an inferred safe class; evidence deletion has its own approval |

No schema file, test, script, document, receipt, or runtime generation has been shown safe to delete by this source pass alone.

## Protections to preserve during the next pass

The initial review found no basis for blanket retirement of independent numerical oracles, literal headers and check rosters, transaction and recovery fault tests, coverage baselines, installed-wheel smoke, guarded R and native-runtime checks, or disposable Slurm evidence. Similar test names across owners do not establish equivalent inputs or faults. Coverage measures Python execution, not scientific correctness or independent expectations.

## Next repository sweep

Walk every stage, analysis, evidence, orchestration, library, reporting, runtime, contract, and public CLI owner against its supported command or input, distinct fault, protection, and evidence level. Extend the same map to fixtures, scripts, schemas, configuration, documentation checks, packaging, and each CI lane. For each proposed removal, name the surviving defense and compare its boundary before any edit. Investigate A01-01, A01-03, A01-04, and A01-11 first because their present claims can overstate what a passing check establishes. Update these entries in place as evidence develops; keep implementation and task status in their existing owners.
