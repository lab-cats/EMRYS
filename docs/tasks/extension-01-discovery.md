# EXTENSION-01 discovery and implementation draft

This is a working review record for [`EXTENSION-01`](backlog_matrix.md#maintainability-and-release), not another task-status or acceptance authority.
The accepted outcome remains in the [backlog matrix](backlog_matrix.md); the earlier [polish proposal](polish-campaign.md#29-document-a-minimal-external-analysis-and-reporter) is supporting context.
This record captures what a separately installed collaborator Analysis would need, what the current
source proves, and what remains to be decided or exercised. Retire or condense this working record
when the bounded outcome is accepted; move lasting behavior to its owner documentation.

## Planning baseline and evidence key

- **Target:** [PR #304](https://github.com/lab-cats/EMRYS/pull/304) head `3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`, checked against the
  open PR list on 2026-09-22. PR #303 is a sibling and is not included in this commit. Recheck the
  target and affected paths before implementation.
- **Authority:** this is a documentation draft and discovery review. Extension implementation,
  package installation, cluster execution, publication, and evidence promotion require separate
  authority under the [workflow](../operations/WORKFLOW.md).
- **Evidence:** the entries below are source and documentation inspection at the pinned commit. No
  example wheel, public Run, synthetic or site exercise, scientific review, or biological
  interpretation was performed for this record. `Observed` means the cited source states or
  implements the behavior; `Proposed` is a design candidate; `Open` requires a decision or execution
  evidence.

## Findings matrix

| ID | Finding and current discovery | Level | Next discovery or proof |
| --- | --- | --- | --- |
| `EX-01` | The accepted row requires one independently installable Analysis and reporter through real discovery, configuration, planning, execution, independent validation, and reporting. The prior collaborator test substitutes loaders. | Observed | Trace one public path without loader substitution and preserve the mocked test's distinct checks. |
| `EX-02` | Step `08` sites permit a descriptive candidate-to-annotated-gene tally from transcript-span assignments, with `NA` and multi-gene rows. Only the sites adapter is needed for that calculation; method and edge-case policy remain open. | Observed / Proposed / Open | Select the method; freeze a literal oracle, input adapters, threshold, `NA`, ordering, and header-only semantics before coding. |
| `EX-03` | Discovery requires one package-level entry point per name and distribution-owned package callbacks; identity excludes distribution metadata files. No separately packaged example is present. | Observed | Build a separate non-editable wheel; prove both entries and callbacks resolve from its owned files, including missing/duplicate refusal. |
| `EX-04` | The planner checks all **declared** inputs, while an external Step `09` publishes native outputs before independent validation. Core all-pass does not enforce a fixed check roster. | Observed | Check exact consumed inputs and validator roster; exercise success and failed-validation preservation through the public runner. |
| `EX-05` | The reporter uses a fixed public carrier and core report transaction. Its HTML must satisfy the core safety, identity, and accessibility checks. | Observed | Render and re-admit a real example report through public commands, with literal expected content. |
| `EX-06` | Run readmission binds module metadata and implementation bytes, but ignores a distribution-release-number-only change when content and module semantics remain identical. | Observed | Test refusal for changed module version or bytes; state distribution version behavior accurately. |
| `EX-07` | Doctor checks declared dependencies and never installs them. The installed-wheel test already creates a disposable `uv` environment although engineering prose says tests never install. | Observed / Open | Decide and explicitly authorize the isolated two-wheel test setup; clarify the policy wording without adding product-time installation. |
| `EX-08` | Wheel smoke covers installed core commands and the built-in reporter; scheduled/manual real-synthetic CI initializes the built-in Analysis. Neither currently proves an external provider's full public path. | Observed | Choose a bounded public execution scenario and CI lane; measure its cost and retain exact-commit results. |
| `EX-09` | Provider, Project YAML, and reporting guidance exist in different owners, but no practical end-to-end walkthrough exists. | Observed | Write one package-adjacent walkthrough and link from the owner guides, retiring duplicate hypothetical prose only after transfer review. |
| `EX-10` | A separate example adds maintained code even if core product files do not change. No new core framework is indicated by the inspected path. | Observed / Open | Quantify files and net lines by surface, audit duplicate callers and retirement candidates, and seek any required growth exception before implementation. |
| `EX-11` | Default static and coverage gates target `scripts`, `src/emrys`, and `tests`; an `examples/` package would fall outside their current source selection. | Observed / Open | Specify package-local lint, build, and tests or an approved gate change; account for any new tooling surface. |

## First discovery pass

### EX-01 — accepted outcome versus existing composition proof

The [backlog row](backlog_matrix.md#maintainability-and-release) owns the complete collaborator outcome. [Polish item 29](polish-campaign.md#29-document-a-minimal-external-analysis-and-reporter) records the concrete gap:
the sampled test constructs a provider identity and replaces both loader functions. In
[`test_materialization.py`](../../tests/orchestration/run_coordinator/test_materialization.py), lines 861–994, this still protects normalized configuration, the thread minimum,
no-write planning, and the input/output binding. It cannot establish entry-point discovery,
installed-package identity, worker execution, or reporter publication. A later real-package test
should replace only genuinely overlapping assertions; unique planning checks survive.

### EX-02 — method and Step boundary

[`AnalysisModuleDescriptorV1`](../../src/emrys/analyses/__init__.py), lines 244–275 and 317–364, admits one Step `09` task and optional `10`, exactly one
validation-report output per task, declared resource limits, and the current PDF/TSV/validation
artifact kinds and path prefixes. A result TSV plus validation TSV fits without a new kind. The
built-in provider demonstrates a Step `09` dependency on Step `08` sites, input receipt, and summary
in [`paired_cmh_candidate_ranking/__init__.py`](../../src/emrys/analyses/paired_cmh_candidate_ranking/__init__.py), lines 358–376. Step `08` gives each candidate `gene_ids` as `NA` or a
semicolon-delimited, duplicate-free list ([`step08.py`](../../src/emrys/contracts/scientific_evidence/step08.py), lines 64–87 and 267–299).

The [Step `08` annotation owner](../../src/emrys/stages/cohort_candidate_preprocessing/_step_08_annotation.R) assigns those IDs from strand-compatible **transcript-span** overlaps, including introns, then sorts and deduplicates them. The [sites contract](../../src/emrys/contracts/scientific_evidence/step08.py) admits a header-only table and requires unique candidate IDs. Step `08` can retain intergenic candidates, and its orientation-to-strand mapping remains provisional under the [stage contract](../../src/emrys/stages/cohort_candidate_preprocessing/CONTRACT.md). Thus a row is one mechanically labeled candidate, not necessarily one genomic locus or an exonic event. Two orientation candidates at one locus remain two candidates if present.

**Proposed example, pending method selection:** count candidate-to-gene assignments from Step `08`
in Step `09`. A candidate with two gene IDs contributes once to each, so the sum can exceed the
number of candidate rows. The descriptor can name only the `step08_sites_v1` input adapter for this
calculation; include the input receipt or summary only if the method actually consumes it for a
stated check. The Step `08` predecessor edge still supplies the task completion barrier. One
possible literal oracle, **if** lexicographic gene ordering and threshold `1` are selected, is
assignments `A;B`, `A`, `NA` producing UTF-8 bytes
`gene_id\tcandidate_count\nA\t2\nB\t1\nNA\t1\n`. Threshold `2` would retain only `A\t2`.
Decide whether the threshold applies to `NA`, how `NA` sorts, and whether empty input or filtering
produces a header-only TSV. A same-strand overlapping-gene fixture is needed to demonstrate a real
multi-gene Step `08` row; the existing [stage test](../../tests/stages/cohort_candidate_preprocessing/test_step_08_vcf_preprocessing.R) does not establish that case. This is a descriptive computational demonstration, not an editing-site or biological claim.

The [configuration admission boundary](../../src/emrys/analyses/__init__.py) validates authored JSON,
passes a canonical copy and path-neutral Project facts to the normalizer, validates the normalized
result again, then canonicalizes it. Planning later supplies an immutable projection. A proposed
`minimum_count` default must come from that admission context, not from opening a Step `08` output
during Project admission. Test that equivalent authored forms yield the same normalized policy and
Analysis ID, and that unknown keys fail. If a real collaborator method needs an earlier stage,
another task slot, or an unsupported artifact, document that concrete gap and stop before changing
the public interface.

### EX-03 — separate package and real discovery

The core wheel declares built-in `emrys.analysis_modules` and `emrys.analysis_reporters` entries in
[`pyproject.toml`](../../pyproject.toml), lines 42–46. [`admit_installed_provider`](../../src/emrys/libraries/installed_package_identity.py), lines 345–438, selects exactly one package-level entry
point and binds installed distribution-owned files. The repository has no separate example
distribution. A proposed example belongs outside `src/emrys`, with both matching entry-point names
in its own package metadata. Entry values must be package-level `package:callable`, resolve without
ambiguity, and load package-owned descriptor callbacks; provider, reporter, producer, and validator
should live in that distribution rather than leak imports from the checkout. Its content digest
excludes `.dist-info` and `.egg-info`, so it must not be described as a hash of all wheel metadata.
A non-editable wheel in the selected environment is the credible discovery case. Include missing
and duplicate entry-point refusal cases; no new registry, installer, workflow graph, or core entry
point is indicated.

### EX-04 — planning, validation, and recovery

[`TaskPlanningContextV2`](../../src/emrys/analyses/__init__.py), lines 94–113, supplies admitted inputs, working and final output paths, resource
threads, and a controlled Python command builder. [`materialization.py`](../../src/emrys/orchestration/run_coordinator/materialization.py), lines 1066–1207, checks that the
returned plan includes every declared input, unique paths, and unique provenance roles. It cannot
discover an extra file that the worker actually reads but never declares, so the example test must
compare planned roles and paths with worker consumption. Its `validator_command` helper targets core
`emrys validate` routes (lines 285–295); a collaborator's own validator should use `python_command` with
its installed module. The validator must independently recompute the proposed counts and publish the
exact seven-column report header defined by [`emrys.libraries.validation`](../../src/emrys/libraries/validation/report.py), lines 13–21. The core [`all_pass.py`](../../src/emrys/orchestration/run_coordinator/all_pass.py),
lines 33–105, requires a nonempty, all-pass report with matching Step/scope and unique check IDs;
it does **not** require a fixed roster or order. Give the example a literal expected check-ID list
and order, and consider `AnalysisArtifactV1.exact_data_rows` for a fixed validation roster. The
independent validator must compute from admitted sites, rather than call the producer's count helper;
generic TSV admission checks shape and rows, not tally semantics.

[`task.py`](../../src/emrys/orchestration/run_coordinator/task.py), lines 1742–1758 and 2732–2782, gives prepublication validation only to named built-in
owners. External Step `09` publishes native outputs, runs its validator, then requires all-pass.
Failed validation therefore leaves evidence and output state under the [runner's preservation contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#task-and-attempt-lifecycle). The example
validator must read final `outputs` and write its own validation report at the supplied
`validation_report_path`; that report is excluded from producer outputs. The example must not write
outside supplied working and scratch paths or delegate work to preexisting or remote processes.

### EX-05 — scientific reporter boundary

The selected matching reporter receives [`AnalysisReportContextV1`](../../src/emrys/reporting/__init__.py), lines 24–62, and returns
`AnalysisScientificReportV1`; the core invokes it and checks returned input identities in
[`context.py`](../../src/emrys/reporting/_run_report/context.py), lines 197–279. Core reporting owns the evidence view, publication, and receipt. Its
[`validation.py`](../../src/emrys/reporting/_run_report/validation.py), lines 362–475, checks more than nonempty HTML: doctype, language, one title and main
landmark, heading order, report identity and computational banner, safe resources, and accessible
tables. The example reporter must satisfy this contract without importing a built-in reporter's
private renderer or recalculating the scientific result.

### EX-06 — identity and version refusal

[`module_identity_record` and `readmit_analysis_module`](../../src/emrys/analyses/__init__.py), lines 488–540, bind module ID, interface version, module version, entry point,
schema/dependency metadata, and installed implementation SHA. Readmission deliberately substitutes
the persisted *distribution* version before comparison. The existing [`test_module.py`](../../tests/analyses/paired_cmh_candidate_ranking/test_module.py), lines 164–173,
demonstrates that a distribution-release-number-only change with identical content can still
readmit. The example should prove changed module version and changed installed bytes are refused;
documentation must not claim that any wheel version string change is fatal. Reporter identity is a
separate report receipt fact, not a change to the immutable scientific Run.

### EX-07 — dependency and installation authority

The [provider guide](../../src/emrys/analyses/README.md#collaborator-providers) says Doctor checks declared tools and packages and managed repair does not install
custom dependencies. Product computation, validation, and reporting must never install.
[Engineering conventions](../operations/ENGINEERING_CONVENTIONS.md#dependencies-and-environments) say installation is explicit setup work and tests never install; the current
[`test_package_distribution.py`](../../tests/test_package_distribution.py), lines 138–176 and 250–308, nevertheless builds a wheel and uses `uv` in an isolated
test environment. Treat that as a policy question, not automatic authority for a second
installation. A bounded test plan must say exactly who creates the disposable environment, what two
wheels enter it, and whether the convention needs clarification. Do not invent a dependency solely
to make the example look complete.

### EX-08 — public-path evidence gap

The [installed-wheel test](../../tests/test_package_distribution.py), lines 341–460, exercises installed core commands outside the checkout. Its report
portion, lines 486–610, uses a built-in fixture and reporter. The [real-synthetic driver](../../tests/tools/real_synthetic_e2e.py), lines 1652–1664,
initializes the built-in Analysis. Neither currently executes an external provider and reporter via
a public Run. A proposed proof is one tiny disposable Project with the example wheel installed
alongside the exact EMRYS wheel, followed by public validation, no-write preview, execution,
inspection, and reporting. Ordinary PR CI includes installed-wheel smoke, but the [real-synthetic job](../../.github/workflows/ci.yml),
lines 1099–1106 and 1275–1305, runs on schedule or manual dispatch. Select the narrowest complete
lane after measuring setup and runtime; green ordinary PR checks cannot close the external
execution/reporting gap. Any heavy alignment or analysis belongs in an approved compute allocation
through the whole-Run path, not a local fixture check. Local fixture, hosted real-tool, disposable
Slurm, Viking, scientific review, and biological interpretation remain separate evidence levels.

### EX-09 — one collaborator walkthrough

[`analyses/README.md`](../../src/emrys/analyses/README.md#collaborator-providers) describes provider mechanics; [`configs/README.md`](../../configs/README.md#collaborator-analysis) has hypothetical Project YAML;
[`reporting/README.md`](../../src/emrys/reporting/README.md) describes report ownership. A package-adjacent guide should carry the installable
example, supported EMRYS revision, Project configuration, inputs/outputs, dependency and resource
declarations, worker/validator roles, report, literal expected result, and limitations. The owner
guides should link to it rather than copy its steps. Replacing the hypothetical configuration
snippet is a candidate only if the concrete example preserves its useful orientation for Project
authors.

### EX-10 — compression and footprint

The [architecture guardrails](../design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails) require a complete affected-path duplicate audit, no product-file growth by
default, and a meaningful net product-code reduction unless a quantified exception is approved.
Current source already has provider/reporter discovery, Doctor dependency checks, task
materialization, artifact admission, and report publication; a new core framework is not justified
by this example. Candidate reductions are narrow: retire truly overlapping mocked test assertions
and consolidate duplicated collaborator prose. Neither removes a distinct trust-boundary check, and
neither offsets maintained example-code growth. Count core code, example code, tests/protections,
scripts/gates, schema/configuration, documentation, mutable state, and retained evidence separately
before implementation approval. Evidence deletion is outside this scope.

### EX-11 — example quality gate

[`make_quality.mk`](../../scripts/make_quality.mk), lines 6–7, 165–168, and 211–236, selects core source and tests for default static and
coverage checks. A package under `examples/` would be outside that selection and outside the core
wheel's `emrys*` package discovery ([`pyproject.toml`](../../pyproject.toml), lines 66–73). Independent installation is
desirable; missing lint/build protection is not. Decide whether a package-local check suffices or
the existing gate should include the example, and count any new configuration or tooling. Its
package name, version, and license terms remain explicit design decisions; do not infer them from
the core distribution.

## Proposed bounded delivery sequence

1. **Freeze the intended method.** Review the proposed candidate-to-gene tally or substitute a named
   collaborator use case. Write literal tiny inputs and expected TSV and report facts, then confirm
   Step `09`/optional `10` fit. Stop for an unmet interface need.
2. **Quote the footprint.** Inventory exact planned files and line budget by the categories above,
   identify caller-complete consolidation, and resolve the disposable-install policy. Obtain
   implementation and any quantified growth/install authority before editing product or example
   code.
3. **Build one external distribution.** Use existing entry points, a strict configuration
   schema/normalizer, a declared task with exact paths/resources/dependencies, separate producer and
   validator, and one bespoke reporter. Keep the core package, schemas, workflow rules, and public
   commands unchanged unless a separately reviewed gap is proven.
4. **Exercise the complete public route.** Use an installed wheel outside the checkout for real
   discovery and admission, then a tiny public Run for execution and report publication. Check
   literal result bytes, exact identity/refusal cases, failed-validation preservation, and report
   re-admission without science rerun.
5. **Consolidate and verify.** Transfer lasting contract details to owner guides, review every
   retained mock check and documentation link, run focused local checks, and use the applicable
   hosted lanes at the exact final commit. Update the backlog row only when its full acceptance
   passes at the stated evidence level.

## Next review pass

Resolve the selected example method and its expected output, the package metadata and license, the
allowed disposable-install setup, and the smallest complete CI scenario. For each new discovery,
identify its exact revision and source or executed artifact, then revise the corresponding matrix
row. A source inference stays labeled as such until an actual public-path check supplies execution
evidence.
