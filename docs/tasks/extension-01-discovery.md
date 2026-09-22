# EXTENSION-01 discovery and implementation draft

This is a working review record for [`EXTENSION-01`](backlog_matrix.md#maintainability-and-release), not another task-status or acceptance authority.
The accepted outcome remains in the [backlog matrix](backlog_matrix.md); the earlier [polish proposal](polish-campaign.md#29-document-a-minimal-external-analysis-and-reporter) is supporting context.
This record captures what a separately installed collaborator Analysis would need, what the current
source proves, and what remains to be decided or exercised. Retire or condense this working record
when the bounded outcome is accepted; move lasting behavior to its owner documentation.

## Planning baseline and evidence key

- **Target:** [PR #304](https://github.com/lab-cats/EMRYS/pull/304) head `3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`, checked against the
  open PR list and rechecked after the source audit on 2026-09-22. PR #303 is a sibling and is not
  included in this commit. Recheck the target and affected paths before implementation.
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
| `EX-03` | Discovery requires one package-level entry point per name and distribution-owned callbacks. Its digest covers owned sibling files but excludes distribution metadata; one versus two example wheels remains a packaging decision. | Observed / Open | Prove real wheel ownership and missing/duplicate refusal; decide whether reporter source changes may couple to Analysis readmission. |
| `EX-04` | The planner checks all **declared** inputs. External Step `09` publishes native outputs before validation; nonzero and nonpassing validators fail without a verified-task, and postpublication continuation is blocked. | Observed | Check exact consumed inputs and check roster; exercise both failure modes and retained state through the public runner. |
| `EX-05` | New reporting re-admits Analysis and reporter; retained inspection checks old bytes without invoking today's reporter but still re-admits Analysis. In a shared wheel, reporter source changes can alter the Analysis digest. | Observed / Open | Test new publication, retained inspection, metadata-only reporter removal, and shared-wheel source drift separately. |
| `EX-06` | Analysis ID, provider readmission, and Attempt runtime binding cover different facts. Provider bytes and selected policy fields are re-admitted; distribution-version-only drift and some dependency metadata are excluded. | Observed | Test each boundary separately, including module/byte refusal and target-only runtime drift. |
| `EX-07` | Doctor accepts fixed-check IDs or declared tools/files/R packages and checks reporter readiness, without installing. Current wheel smoke generates a temporary lock and installs despite prose that tests never do either. | Observed / Open | Resolve disposable lock/install policy and custom dependency rules; choose the reporter or `--no-report` path. |
| `EX-08` | Core wheel smoke calls private report preparation; ordinary PR CI runs a 20-minute static/wheel lane, while real-synthetic runs only on schedule/manual. Neither proves an external public Run. | Observed | Choose a tiny public execution scenario and CI lane; measure cost and retain exact-commit results. |
| `EX-09` | Provider, Project YAML, and reporting guidance are split across owners; the YAML sample is hypothetical. Core version `0.1.0.dev0` cannot identify this PR's exact code. | Observed | Write one package-adjacent walkthrough with the tested core commit/wheel identity; link from owner guides after transfer review. |
| `EX-10` | No `examples/` files are tracked. A separate example adds maintained files, requiring an explicit quantified `AC-GUARD-006` exception before implementation. | Observed / Open | Inventory planned files and net lines by surface; protect unique mock assertions and propose only caller-complete retirements. |
| `EX-11` | `examples/` would be outside current lint, coverage, and core-wheel selection; conventional example tests enter unscoped collection and shards unless routed explicitly. | Observed / Open | Specify an explicit separate build/lint/test gate and selection, with no core coverage credit. |

## Source discoveries by finding

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
distribution. A proposed example belongs outside `src/emrys`, with matching Analysis and reporter
entry-point names. Entry values must be package-level `package:callable`, resolve without ambiguity,
and load distribution-owned callbacks; producer and validator should also run from installed code
rather than leak imports from the checkout. The digest covers distribution-owned sibling files as
well as the entry package, but excludes `.dist-info` and `.egg-info`; it is not a hash of all wheel
metadata. Non-editable wheels in the selected environment are the credible discovery case. Include
missing and duplicate entry-point refusal cases; no new registry, installer, workflow graph, or
core entry point is indicated.

**Open packaging decision:** one wheel with both entry points is the smaller initial surface, but
the Analysis provider digest covers its reporter source too. A reporter source change in that wheel
can therefore block old Analysis readmission. Two separately installed wheels would separate those
content identities while adding setup and maintained-package cost. Record the chosen tradeoff before
the example layout and compatibility tests are fixed; do not change core hashing to hide it.

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
and order. `AnalysisArtifactV1.exact_data_rows` can pin row **count** only; it does not enforce that
list or order. The
independent validator must compute from admitted sites, rather than call the producer's count helper;
generic TSV admission checks shape and rows, not tally semantics.

[`task.py`](../../src/emrys/orchestration/run_coordinator/task.py), lines 1742–1758 and 2732–2782, gives prepublication validation only to named built-in
owners. External Step `09` publishes native outputs, runs its validator, then requires all-pass.
Both a nonzero validator exit and a zero-exit report with a nonpassing row can leave committed
native outputs and a failed Task attempt without a verified-task. The validation report may be
absent after a nonzero exit. The [runner's preservation contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#task-and-attempt-lifecycle) leaves postpublication failures ineligible for automatic continuation; preserve that state for operator disposition rather than promise retry or rollback. Test both failure routes through the external Step `09` path; the existing generic failed-row test does not prove it. The producer must write to supplied working/scratch paths. The independent validator must read final `outputs` and write its report at the supplied `validation_report_path`, which is excluded from producer outputs. Any other temporary writes remain within owned paths. Neither process may delegate relevant work to preexisting or remote processes.

### EX-05 — scientific reporter boundary

The selected matching reporter receives [`AnalysisReportContextV1`](../../src/emrys/reporting/__init__.py), lines 24–62, and returns
`AnalysisScientificReportV1`; the core invokes it and checks returned input identities in
[`context.py`](../../src/emrys/reporting/_run_report/context.py), lines 197–279. Core reporting owns the evidence view, publication, and receipt. Its
[`validation.py`](../../src/emrys/reporting/_run_report/validation.py), lines 362–475, checks more than nonempty HTML: doctype, language, one title and main
landmark, heading order, report identity and computational banner, safe resources, and accessible
tables. The example reporter must satisfy this contract without importing a built-in reporter's
private renderer or recalculating the scientific result.

`AnalysisScientificReportV1.inputs` may be empty. The core rechecks admitted Analysis artifacts
even when the reporter does not repeat them in that returned roster. If the reporter opens an
additional report-only file, it must return that file's `AnalysisReportInputV1` identity for
snapshot and receipt checks ([`context.py`](../../src/emrys/reporting/_run_report/context.py), lines 253–291). The proposed tally reporter should avoid extra file inputs unless the method needs them.

New publication re-admits the current Analysis and reporter. The [report context](../../src/emrys/reporting/_run_report/context.py) passes only required, present, complete artifacts whose Step, scope, hash, size, and media type match the admitted summary. The [artifact index](../../src/emrys/reporting/_artifact_index/_text_tabular.py) checks declared TSV header and row shape/count, but does not recompute the proposed tally; that remains the independent validator's job. Test malformed or missing artifacts at admission, and test the reporter only with admitted snapshots/projections. Doctor requires a matching reporter for the ordinary through-report Run, while `--no-report` allows execution before reporter installation and later reporting.

[Retained report validation](../../src/emrys/reporting/transaction_validation.py) checks the original receipt, data inputs, and HTML without invoking today's reporter. Upstream Run-summary and artifact validation still re-admits the current **Analysis** provider. If Analysis and reporter share a wheel, changing reporter source bytes changes that wheel's provider digest and can block Analysis readmission even though the renderer is never called. Removing only the reporter entry-point metadata is a different case because `.dist-info` is excluded from the provider digest; whether retained inspection succeeds must be tested with the exact remaining Analysis package and receipt. Test new publication, same-wheel source drift, and metadata-only reporter removal separately.

[Public report admission](../../src/emrys/orchestration/run_coordinator/reporting_operation.py) requires valid Run integrity, a succeeded Attempt and receipt, and complete Results. Blocked reporting or a nonempty unadmitted destination refuses generation rather than adopting present HTML; an admitted complete report is rechecked and reused. Inspect the exact Run before and after reporting, and do not count an HTML file's presence as report completion.

### EX-06 — identity and version refusal

[`module_identity_record` and `readmit_analysis_module`](../../src/emrys/analyses/__init__.py), lines 488–540, bind module ID, interface version, module version, entry point,
schema hash, selected dependency-policy fields, and installed implementation SHA. Readmission deliberately substitutes
the persisted *distribution* version before comparison. The existing [`test_module.py`](../../tests/analyses/paired_cmh_candidate_ranking/test_module.py), lines 164–173,
demonstrates that a distribution-release-number-only change with identical content can still
readmit. The example should prove changed module version and changed installed bytes are refused;
documentation must not claim that any wheel version string change is fatal. Reporter identity is a
separate report receipt fact, not a change to the immutable scientific Run.

These identities sit at different boundaries:

| Boundary | Bound facts and limit |
| --- | --- |
| [Analysis revision](../../src/emrys/contracts/orchestration/application_model.py) | Selected sample, partition, and reference facts plus module ID, interface/module versions, and normalized configuration form the scientific Analysis value. Distribution release and implementation bytes are outside this ID. |
| Persisted module policy and [Run implementation](../../src/emrys/orchestration/run_coordinator/run_implementation.py) | Provider readmission compares distribution name, entry point, schema hash, selected dependency records, and implementation SHA. A distribution-version-only change is ignored. `dependency_records` omits every description and custom executable/file/package-tree target path, so “all dependency metadata” would overstate this identity. |
| [Attempt runtime binding](../../src/emrys/orchestration/run_coordinator/lifecycle.py) | Runtime inspection and `required_tools` recheck concrete selected targets and content for an existing Attempt. Test a target-only change at this boundary; do not expect `readmit_analysis_module` alone to reject every target-field change. |

The [installed distribution digest](../../src/emrys/libraries/installed_package_identity.py) excludes `.dist-info` and `.egg-info`. It does not attest `Requires-Dist` metadata or the installed versions of external Python libraries. For a proposed standard-library-only example this is a stated identity limit, not a demonstrated need for new core machinery. A collaborator that uses external Python libraries would require a separate concrete dependency-closure decision if those versions must be bound to scientific behavior.

### EX-07 — dependency and installation authority

The [provider guide](../../src/emrys/analyses/README.md#collaborator-providers) says Doctor checks declared tools and packages and managed repair does not install
custom dependencies. Product computation, validation, and reporting must never install.
[Engineering conventions](../operations/ENGINEERING_CONVENTIONS.md#dependencies-and-environments) say installation is explicit setup work and tests never install; the current
[`test_package_distribution.py`](../../tests/test_package_distribution.py), lines 138–176 and 250–308, nevertheless builds a wheel and uses `uv` in an isolated
test environment. It also generates a temporary `uv.lock`; its build and sync commands specify
`--offline`, but the lock command does not. The repository lock is unchanged. Treat both temporary
lock generation and installation as policy questions, not automatic authority for a second setup.
A bounded test plan must say exactly who creates the disposable environment, what two wheels enter
it, and whether the convention needs clarification. Do not invent a dependency solely to make the
example look complete.

The [descriptor](../../src/emrys/analyses/__init__.py) may reuse an existing fixed runtime check by
ID or declare an executable, R namespace, file, or package-tree check. IDs must be unique and avoid
reserved/fixed-check collisions; non-R custom targets must be absolute. [Doctor](../../src/emrys/orchestration/run_coordinator/doctor.py) checks those declarations but has no Python-distribution check. Python requirements belong in wheel metadata and explicit package-manager setup; loading the installed example then exercises their availability. Doctor also checks the matching reporter by default, with `--no-report` as a documented execution route for later report generation. A standard-library-only example can avoid an unnecessary custom dependency declaration.

### EX-08 — public-path evidence gap

The [installed-wheel test](../../tests/test_package_distribution.py), lines 341–460, exercises installed core commands outside the checkout. Its report
portion, lines 486–610, uses a built-in fixture and reporter through private `prepare_context` and
`publish_report` calls, so it is not public `emrys report` evidence. The [real-synthetic driver](../../tests/tools/real_synthetic_e2e.py), lines 1652–1664,
initializes the built-in Analysis. Neither currently executes an external provider and reporter via
a public Run. A proposed proof is one tiny disposable Project with the example wheel installed
alongside the exact EMRYS wheel, followed by public validation, no-write preview, execution,
inspection, and reporting. Ordinary PR CI runs the static/wheel lane with a 20-minute cap, but the [real-synthetic job](../../.github/workflows/ci.yml),
lines 1099–1106 and 1275–1305, runs on schedule or manual dispatch. Select the narrowest complete
lane after measuring setup and runtime; green ordinary PR checks cannot close the external
execution/reporting gap. Any heavy alignment or analysis belongs in an approved compute allocation
through the whole-Run path, not a local fixture check. Local fixture, hosted real-tool, disposable
Slurm, Viking, scientific review, and biological interpretation remain separate evidence levels.

The public entry route starts with an explicit collaborator `project.yaml`: current `emrys init`
and `emrys init synthetic` select the built-in Analysis, without a module-selection option.
`emrys validate --project PATH` can then admit the external package and configuration. On a Slurm
profile, a no-write `emrys run` previews submission and returns before external task planning;
the planner runs after compute delegation. A direct-profile preview can plan tasks, subject to
Doctor and storage readiness. Record these as distinct proof levels rather than calling a Slurm
submission preview planning evidence. No public external execution has been performed here.

The smallest supplied real-tool synthetic dataset, `smoke-v1`, contains four libraries with 130
read pairs each and a 100 kb reference. It initializes a built-in Analysis and hashes a completion
manifest, so substituting an external `project.yaml` is an authored variation with its own expected
result, not the unmodified fixture's oracle. Its annotation covers only two named genes at the
intended candidate positions and does not demonstrate `NA` or a multi-gene assignment. A public
`--from-processing-run` can reuse Steps `00`–`06` but still runs Step `07` onward; it does not inject
a finished Step `08` table for Step `09` only. Keep a literal hand-authored unit oracle separate
from any later public end-to-end oracle, and budget the latter's real-tool cost.

**Proposed public proof route, after separate setup and execution authority:** author a named
external Analysis in `project.yaml` and install both exact wheels in the selected environment;
run `emrys validate --project PROJECT`, `emrys doctor --project PROJECT --analysis NAME`, and
`emrys run --project PROJECT --analysis NAME` for a read-only preview. After runtime readiness and
an approved execution location, run `emrys run --project PROJECT --analysis NAME --execute` and
`emrys inspect --project PROJECT RUN_ID`. A successful through-report Run may already contain the
report; `emrys report --project PROJECT RUN_ID` must re-admit/reuse it. If Results are complete and
reporting was deliberately skipped, preview that report command before an authorized `--execute`,
then inspect again. On Slurm, the compute delegate must see the same installed wheels, and report
generation may itself schedule work. These commands are proposed proof steps, not checks performed
for this draft.

### EX-09 — one collaborator walkthrough

[`analyses/README.md`](../../src/emrys/analyses/README.md#collaborator-providers) describes provider mechanics; [`configs/README.md`](../../configs/README.md#collaborator-analysis) has hypothetical Project YAML;
[`reporting/README.md`](../../src/emrys/reporting/README.md) describes report ownership. A package-adjacent guide should carry the installable
example, supported EMRYS revision, Project configuration, inputs/outputs, dependency and resource
declarations, worker/validator roles, report, literal expected result, and limitations. The owner
guides should link to it rather than copy its steps. Replacing the hypothetical configuration
snippet is a candidate only if the concrete example preserves its useful orientation for Project
authors. Record the exact tested EMRYS commit and wheel identity alongside interface
`emrys.analysis-module.v2`; the current core version is `0.1.0.dev0`, so a version pin alone cannot
distinguish PR heads. Choose the separate example distribution name, version, and license explicitly
rather than copying the core package's metadata by assumption.

### EX-10 — compression and footprint

The [architecture guardrails](../design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails) require a complete affected-path duplicate audit, no product-file growth by
default, and a meaningful net product-code reduction unless a quantified exception is approved.
Current source already has provider/reporter discovery, Doctor dependency checks, task
materialization, artifact admission, and report publication; a new core framework is not justified
by this example. No `examples/` file is currently tracked, so even a small separate distribution
is net new maintained product files and needs an explicit quantified `AC-GUARD-006` exception before
implementation. Candidate reductions are narrow: retire only genuinely overlapping mocked test
assertions and replace the hypothetical collaborator YAML with a link after preserving useful
Project-author guidance. The existing mock uniquely checks normalization, a thread floor, no-write
planning, input/output binding, and dispatch facts; these cannot disappear merely because a wheel
test is added. Neither prose consolidation nor test retirement offsets maintained example-code
growth. Count core code, example code, tests/protections,
scripts/gates, schema/configuration, documentation, mutable state, and retained evidence separately
before implementation approval. Evidence deletion is outside this scope.

A **proposed one-wheel file floor**, not a measured footprint or approved layout, is one external
`pyproject.toml` with both entry points; package-level callbacks in `src/<package>/__init__.py`;
producer/validator dispatch in `src/<package>/__main__.py`; one package README; one tiny fixture
with literal oracle; and one focused test. This is six new files only if the fixture and oracle share
one file. Splitting owners may be clearer and would increase that count. Quote the actual planned
file and net-line budget, including the gate changes, after method and package layout review; do
not call this floor a measured implementation reduction.

### EX-11 — example quality gate

[`make_quality.mk`](../../scripts/make_quality.mk), lines 6–7, 165–168, and 211–236, selects core source and tests for default static and
coverage checks. A package under `examples/` would be outside that selection and outside the core
wheel's `emrys*` package discovery ([`pyproject.toml`](../../pyproject.toml), lines 66–73). Independent installation is
desirable; missing lint/build protection is not. The current wheel smoke builds only a copied core
package tree, while Python shards intentionally exclude that wheel test. The [shard planner](../../tests/tools/python_test_shards.py) runs unscoped `pytest --collect-only` and ignores only two named tests, so a conventional
`examples/**/test_*.py` enters default and shard collection unless explicitly routed. Specify a separate
example-wheel build plus package-local lint and selected tests, or an approved change to the
existing gate; claim no core coverage credit for unmeasured example code. Count any new
configuration or tooling. Its package name, version, and license terms remain explicit design
decisions; do not infer them from the core distribution.

## Proposed bounded delivery sequence

1. **Refresh the review facts against the exact implementation target.** Recheck PR #304's live head,
   changed source paths, accepted backlog row, and guardrails. Revise any drifted discovery before
   treating a quoted line or contract as current.
2. **Choose one collaborator method.** Accept or replace the proposed candidate-to-annotated-gene
   tally. Confirm its full input is available from Step `08`, fits Step `09`/optional `10`, and needs
   only existing artifact kinds. Stop for separate interface review if it does not fit.
3. **Freeze literal behavior.** Specify the sites-only input or a reason for each additional
   adapter; define unique-candidate, multi-gene, `NA`, sorting, threshold, zero-row, header-only,
   newline, and UTF-8 rules. Keep a unit oracle separate from a real-tool public-Run oracle and
   state that the tally is descriptive, not biological interpretation.
4. **Quote the footprint and seek bounded authority.** Inventory planned new, changed, and retired
   files and net lines by core code, example code, tests, gates, configuration, docs, and state.
   Preserve the mock's unique checks and all exact evidence. Resolve temporary lock/install policy
   and obtain implementation plus any quantified `AC-GUARD-006` growth authority before edits.
5. **Define the external package boundary.** Choose one shared wheel or two separately installed
   wheels after accounting for reporter-source changes in the Analysis digest and the maintenance
   cost of separation. Specify names, versions, licenses, supported exact EMRYS wheel/commit, and
   standard-library or explicit Python requirements. Use package-level matching entry points and
   distribution-owned callbacks/workers; add no core registry or installer.
6. **Admit one immutable configuration.** Add a closed JSON schema and normalizer for the selected
   method. Verify unknown-key refusal, equivalent authored forms normalizing to one policy and
   Analysis ID. Test provider readmission and Attempt runtime bindings separately, including changed
   module metadata/bytes and target-only drift. State the distribution-version and dependency-field
   identity limits.
7. **Declare and plan one task.** State every input adapter and consumed path, native TSV and
   validation-report outputs, Step/scope, minimum resources, and genuinely needed dependencies.
   Use working outputs for the producer and final outputs for the validator. Verify no-write direct
   planning, provenance roles, input completeness, path safety, and resource floor.
8. **Implement separate producer and validator.** The producer writes deterministic bytes only to
   supplied working paths. The validator reads admitted sites and final published output,
   independently recomputes the tally, and writes the seven-column report to its separate path.
   Assert exact check IDs/order, both nonzero and nonpassing validator failures, retained outputs,
   failed Task attempts, and absent verified-task records. Do not infer semantic truth from a
   passing process or generic TSV shape check, or assume automatic continuation after publication.
9. **Implement one reporter.** Render only from admitted artifact snapshots/projections and return
   identities for any additional report-only files it opens; core rechecks admitted artifacts.
   Produce a scientific HTML view that satisfies core checks. Verify literal tally content,
   new-publication refusal, retained reuse, and the shared-wheel versus separate-wheel drift cases.
10. **Add the package-specific quality lane.** Choose an intentional test selection and package
    lint/format/compile/build checks. Keep the existing core wheel test and Python shard scope
    honest; do not claim core coverage for an unmeasured example or expand local checks into heavy
    science computation.
11. **Exercise the installed public route.** After disposable setup authority, test both wheels
    outside the checkout with missing/duplicate entry-point refusal and no checkout import
    leakage. After execution authority, use an explicitly authored Project for public validation,
    Doctor, preview, Run, inspect, and report. On Slurm, count preview as submission evidence only;
    require compute-delegate task planning and an admitted successful report at the exact commit.
12. **Transfer documentation and reconcile acceptance.** Put the runnable walkthrough beside the
    package; link owner guides and retire only demonstrably duplicated hypothetical prose. Compare
    literal expected bytes, tests, hosted checks, retained artifacts, and footprint against each
    matrix row. Update the accepted backlog row only after its complete outcome passes at the
    stated evidence level; leave site, scientific, and biological claims open until independently
    established.

## Open decisions before implementation

Resolve the selected example method and its expected output, the package metadata and license, the
allowed disposable-install setup, and the smallest complete CI scenario. For each new discovery,
identify its exact revision and source or executed artifact, then revise the corresponding matrix
row. A source inference stays labeled as such until an actual public-path check supplies execution
evidence.
