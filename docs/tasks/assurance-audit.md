# ASSURANCE-01 repository-wide audit

## Scope and evidence

This is the working investigation record for `ASSURANCE-01`. Its starting source is PR #302 at commit `42d02c5a38ecffaba59e58d5d56ba0ab858eda1f`. The audit covers the entire repository: product code, tests, fixtures, scripts, configuration, documentation checks, packaging, and CI. It is **incomplete**; the entries below are discoveries from the first pass, not a conclusion that other areas are clear.

The [backlog matrix](backlog_matrix.md) owns the accepted outcome and task status. This document records evidence and questions. It authorizes no implementation, protection removal, coverage change, or evidence deletion. `QUAL-01` owns measured test cost; `HARNESS-01` owns simulated-science harness choices; `REPORT-ROSTER-01` owns the reporting roster decision.

All `path:line` references below refer to the pinned commit. **Source reviewed** means code or documentation was inspected, without execution in this audit. **Test characterized** means a committed test explicitly asserts the behavior; that test was not rerun for this record. **Inference** identifies a conclusion still needing a focused reproduction. No local test run, institutional Slurm run, scientific review, or biological validation was performed for this pass.

## Findings matrix

| ID | Surface | Initial reading | Basis | Next investigation or decision |
|---|---|---|---|---|
| A01-01 | Step 07 selector validation | Known all-pass result for an out-of-bounds region file | Source; test characterized | Decide the validator's selector and output semantic ceiling; trace report consumers |
| A01-02 | Project-to-Step 07 selector admission | Unicode decimal syntax differs between admission and producer | Source | Define accepted syntax and compare all caller inputs |
| A01-03 | CI whitespace check | CI checks a clean worktree diff, not committed PR changes | Source | Specify the commit range and surviving local check |
| A01-04 | Validation roster inventory | "Exact live inventory" scan misses source-owned validators | Source | Derive the inventory from an authoritative owner roster |
| A01-05 | Roster mutation cases | Many step permutations exercise a step-agnostic helper; one reorder case is vacuous | Source | Identify the smallest representative cases while retaining owner oracles |
| A01-06 | Canonical-document path and H1 gate | Presence is enforced; title identity and H1 position are not | Source; test characterized | Assess each required path's value and the intended heading rule |
| A01-07 | Markdown anchors | Tilde-fenced headings may be accepted as real anchors | Source inference | Reproduce with a tiny fixture and preserve genuine link checking |
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

## Discovery notes

### A01-01 — Step 07 selector validation false pass

**Supported behavior and failure.** Step 07's validation report should reconcile the declared region selector with the output transaction. `src/emrys/libraries/validation/mpileup.py:130-153` checks a region-file row for a known contig but does not establish its coordinate bounds. The owner emits this as `selector_reconciliation` in `src/emrys/stages/partitioned_cohort_mpileup/validator.py:138-150`. A retained test at `tests/stages/partitioned_cohort_mpileup/test_validate_step_07_mpileup_outputs.py:424-445` explicitly expects an all-pass report for a BED end beyond the FAI bound. The owner contract at `src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md:90-103` states a limited validator ceiling.

**Surviving defenses and next step.** Project admission and the producer check selectors before work; receipt and sample checks protect other properties. Those defenses do not establish that an existing Step 07 validation report proves selector bounds. Retain the characterization. Trace every consumer of this report, then decide the owner's required validation ceiling before proposing a fix.

### A01-02 — Selector syntax differs across owners

Project admission uses `str.isdigit()` before integer conversion (`src/emrys/orchestration/run_coordinator/onboarding.py:1645-1651`); the Step 07 producer requires ASCII `[0-9]+` (`src/emrys/stages/partitioned_cohort_mpileup/producer.py:131-136`). `src/emrys/contracts/SOURCE_TOPOLOGY.md:45` records this disparity. An admitted Project selector therefore may not be accepted by the worker. This is a source-level mismatch, not a reproduced Run failure. Decide the supported coordinate syntax, inspect Project-side tests and all selector readers, and preserve producer refusal until caller-complete parity is demonstrated.

### A01-03 — CI whitespace check does not inspect committed changes

`scripts/make_quality.mk:211-219` runs `git diff --check` inside `validation-static`. The CI job first checks out the commit and runs that target (`.github/workflows/ci.yml:173-185`); the command inspects unstaged worktree changes rather than the committed PR range. The local command remains useful for local edits. Specify the intended CI comparison range and verify it covers the committed file types before changing the gate.

### A01-04 — Validation inventory assertion misses source owners

`tests/contract_integration/validation_rosters/test_validation_check_rosters.py:84-95` says it checks the exact live validator inventory, but scans `scripts/validate_step_*.py`. The listed validators reside under `src/emrys`; the scan and its expected script subset are both empty at this commit. The test still confirms that its named paths exist and that its two lists agree. Owner tests separately compare emitted reports with literal rosters. The gap is discovery of a *new* source-owned validator. Find an existing authoritative owner roster before adding another inventory list.

### A01-05 — Central roster mutation multiplication

The same test file parametrizes generic roster mutations over all listed steps (`:98-146`). Its shared report validator has no step-specific branches (`src/emrys/libraries/validation/report.py:83-111`). Reordering a one-check roster produces the same order, so that acceptance case cannot probe an ordering defect. Candidate reduction is representative one-check and multi-check helper cases, while retaining every owner's literal expected roster and actual emitted-report assertion. First map the distinct faults and measure cost under `QUAL-01`.

### A01-06 — Canonical document names and headings

`scripts/documentation/validate_structure.py:14-34,199-206` requires 19 named documents and an H1 somewhere in each. `first_heading` (`:120-126`) accepts any nonempty H1 text, regardless of position. `tests/documentation/test_validate_structure.py:158-176` explicitly accepts a renamed Workflow title. Thus the gate protects file presence and some heading structure, not document identity or first-line placement. Assess each hardcoded path against an owner obligation; decide whether the documented "first headings" promise needs a tighter check. Preserve owner-directory and local-link checks that catch distinct failures.

### A01-07 — Anchor parser and tilde fences

Local link targets and anchors are checked in `scripts/documentation/validate_structure.py:164-196`. Its anchor extractor (`:129-147`) toggles fenced-code state only for backticks, although CommonMark also permits tilde fences. A heading-looking line inside a tilde fence could therefore satisfy a link to a nonexistent heading. This is a source inference, with no reproduction yet. Make a tiny fixture, then fix the parser boundary if confirmed; retain local-link validation.

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

## Protections to preserve during the next pass

The initial review found no basis for blanket retirement of independent numerical oracles, literal headers and check rosters, transaction and recovery fault tests, coverage baselines, installed-wheel smoke, guarded R and native-runtime checks, or disposable Slurm evidence. Similar test names across owners do not establish equivalent inputs or faults. Coverage measures Python execution, not scientific correctness or independent expectations.

## Next repository sweep

Walk every stage, analysis, evidence, orchestration, library, reporting, runtime, contract, and public CLI owner against its supported command or input, distinct fault, protection, and evidence level. Extend the same map to fixtures, scripts, schemas, configuration, documentation checks, packaging, and each CI lane. For each proposed removal, name the surviving defense and compare its boundary before any edit. Investigate A01-01, A01-03, A01-04, and A01-11 first because their present claims can overstate what a passing check establishes. Update these entries in place as evidence develops; keep implementation and task status in their existing owners.
