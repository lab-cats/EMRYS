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

## Repository-wide EXTENSION-01 impact sweep and limit

The 2026-09-22 review inventoried the 576 tracked paths in the audit worktree, searched source, tests,
documentation, configuration, scripts, packaging, and CI for Analysis and reporter boundaries,
and followed relevant owners in both directions: Step `07`/`08` inputs; provider discovery and
Project admission; Doctor and runtime binding; direct and Slurm planning; worker/validator
publication and recovery; Results and reporting; package identity; and local/hosted checks. This
is an **EXTENSION-01 impact audit across the repository**, not a line-by-line review of every file
or a general defect audit of unrelated functionality. The matrix below records material findings
from that sweep. The review did not execute an external provider, establish live Slurm or Viking
behavior, test arbitrary collaborator packages, or validate scientific/biological meaning.

| Repository surface | Reviewed for this extension | What source review still cannot prove |
| --- | --- | --- |
| Scientific producers and contracts | Step `07` selection, Step `08` sites and GTF assignment, Step `09` comparison; stage/contract tests and synthetic fixtures. | Real overlapping-gene output or a public external-Analysis result. |
| Provider and Project boundary | Entry-point discovery, owned code digest, descriptor/schema normalization, Project selection, identity and readmission. | A separately built wheel's actual installation, imports, or compatibility. |
| Execution and recovery | Doctor, direct/Slurm preview, task planning, published outputs, validator outcomes, Attempt/Result admission and continuation. | External commands' true input/read set, resource use, or live scheduler behavior. |
| Reporting and evidence | Artifact index, reporter context, run-summary and HTML transactions, retained inspection, public report command. | Rendering or recovery with the proposed external reporter. |
| Quality and operator surfaces | Packaging, `all-checks`, Make and CI contracts, pre-commit/source-dependency scope, owner documentation and accepted backlog. | A timed, passing example gate or an operator walkthrough. |

Any later execution result must name the exact commit, installed distributions, environment,
command, and retained artifact. A green core check alone cannot close an external-provider row.

## Findings matrix

| ID | Finding and current discovery | Level | Next discovery or proof |
| --- | --- | --- | --- |
| `EX-01` | The accepted row requires one independently installable Analysis and reporter through real discovery, configuration, planning, execution, independent validation, and reporting. The prior collaborator test substitutes loaders. | Observed | Trace one public path without loader substitution and preserve the mocked test's distinct checks. |
| `EX-02` | A Step `08` sites tally would count supported pre-CMH SNV allele rows after Step `07` selection, using exon-derived transcript spans; `NA` and multi-gene rows are possible. Its inclusion and edge-case policy remain open. | Observed / Proposed / Open | Freeze the inclusion policy and literal oracle; exercise a real Step `08` overlap fixture and measure resources. |
| `EX-03` | Discovery requires one package-level entry point per name and complete distribution ownership of the package tree named by that entry point. Its digest covers owned sibling files but excludes distribution metadata; one versus two example wheels remains a packaging decision. | Observed / Open | Prove real wheel ownership and missing/duplicate refusal; decide whether reporter source changes may couple to Analysis readmission. |
| `EX-04` | The planner checks all **declared** inputs and command shape, not worker ownership or the complete read set. A distinct external Step `09` owner publishes native outputs before validation; the runner's built-in owner-key special case is not reserved by descriptor admission. Both validator failure modes leave no verified task. | Observed / Inferred collision | Check installed command imports, exact consumed inputs and roster; use a distinct owner key and exercise both failure states through the public runner. |
| `EX-05` | New reporting re-admits Analysis and reporter; retained inspection checks old bytes without today's reporter but still re-admits Analysis. Reporter lookup has no module-version negotiation; variable TSV rows require snapshot reads. A late reporter install works only if the original Analysis still readmits. Separate reporting ledgers can leave Results complete and reporting blocked. | Observed / Open | Test version pairing, literal multi-row render, late installation, reporter drift, and pre/post-ledger failures for the chosen layout. |
| `EX-06` | Analysis ID, provider readmission, and Attempt runtime binding cover different facts. Selected bytes/fields are re-admitted, while descriptor output is not independently fingerprinted. The shared core admission hash includes built-in Step `09` contracts for external Runs. | Observed / Inferred | Test repeated descriptor/profile equivalence, module/byte and target-only drift; decide whether shared-core coupling is intentional. |
| `EX-07` | Doctor accepts fixed-check IDs or declared tools/files/R packages and checks reporter lookup, without installing or proving render-time dependencies. Current wheel smoke generates a temporary lock and installs despite prose that tests never do either. | Observed / Open | Resolve disposable lock/install policy and reporter dependency/version proof; choose the reporter or `--no-report` path. |
| `EX-08` | Core wheel smoke calls private report preparation; Slurm Run preview does not admit the provider, and report preview does not render HTML. Ordinary PR CI and scheduled/manual real-synthetic checks do not prove an external public Run. | Observed | Choose a tiny installed public scenario, distinguish each preview level, and retain exact-commit results. |
| `EX-09` | Provider, Project YAML, and reporting guidance are split across owners; the YAML sample is hypothetical. Guided Project creation emits the built-in Analysis, so the external route needs an authored Project and explicit index settings. Core version `0.1.0.dev0` cannot identify this PR's exact code. | Observed | Write one package-adjacent walkthrough with the tested core commit/wheel identity and complete external Project; link from owner guides after transfer review. |
| `EX-10` | No `examples/` files are tracked. A separate example adds maintained files, requiring an explicit quantified `AC-GUARD-006` exception before implementation. | Observed / Open | Inventory planned files and net lines by surface; protect unique mock assertions and propose only caller-complete retirements. |
| `EX-11` | `examples/` would be outside default Ruff, pre-commit, coverage, core-wheel, and source-import checks; conventional example tests enter unscoped collection. CI commands and Make targets have contract tests. | Observed / Open | Route explicit example checks and update affected gate contracts, with no unmeasured core coverage credit. |
| `EX-12` | Provider/configuration callbacks, planning, selected worker commands, and reporter execution run with the operator's authority; admission attributes provider code but does not sandbox commands. | Observed / Open | State the trusted-package boundary and check example command origins and owned paths without claiming a sandbox. |
| `EX-13` | **Reporting blocker:** artifact indexing registers external adapters but unconditionally applies built-in CMH Step `09` reconciliation to every complete Step `09` scope. The proposed tally has none of its four required CMH adapters. Optional external Step `10` has the same built-in assumption. | Observed source path / Open repair | Establish a bounded module-aware reconciliation decision; retain built-in defenses and prove generic external Run-summary/report admission before claiming end-to-end fit. |
| `EX-14` | Installed watch and verbose inspection assume the built-in statistical/context tail. External owners are unmapped, Step `09` is labeled paired CMH, reporting is said to follow Step `10`, and REPORT says three transactions although the owner defines two. | Observed source path / Open public effect | Exercise external Run/watch presentation and correct labels, mapping, next action, and transaction count without making scheduler text completion authority. |

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
This is a descriptor and planner fit only. The current reporting reconciliation does not admit a
generic Step `09` result as proposed; see EX-13 before claiming an end-to-end interface fit.

For the proposed tally, the smallest descriptor shape using the current
[`AnalysisTaskV1` and `AnalysisArtifactV1` rules](../../src/emrys/analyses/__init__.py) is:

| Surface | Proposed value or required constraint | Still to decide |
| --- | --- | --- |
| Task | One unique owner at Step `09`; `stage_memory_mb` is positive or `"workflow"`, and `minimum_threads` is at least `1`. | Owner ID and measured resource floor. |
| Predecessor | Exact Step `08` owner `emrys.stage.preprocess_and_annotate_cohort_candidates.v1`, selecting only `step08_sites_v1` for this calculation. | Add another adapter only for a named use. |
| Result | One required `tsv` with declared header `gene_id`, `candidate_count`; `results/gene-counts/{analysis_id}/{analysis_id}.candidate_gene_counts.tsv` is a candidate path. | Artifact/adapter names, final path, and whether a header-only file is valid. |
| Validation | One required `validation_report` after the result, under `products/native/`, with `{analysis_id}` and the exact seven-column core header. | Literal check IDs/order and then the exact data-row count; a header-only report cannot pass all-pass. |
| Planner | One provenance `TaskInputV1` for the sites path; installed Python producer writes its supplied `working_outputs` result, and installed Python validator reads final `outputs` and writes the report path. | Exact command arguments and whether any additional input is genuinely consumed. |
| Dependencies | No custom dependency for a standard-library-only example; reuse fixed runtime checks or declare a custom check only for an actual need. | Package requirements and measured runtime needs. |

Every declared output is required in the composed profile, even if a result table has zero data
rows. Artifact names and adapters must be unique and avoid processing-profile collisions. Each
source path template must contain `{analysis_id}`, use an allowed root, and avoid extra template
fields or traversal components. `exact_data_rows` can later pin the validation report's row count,
while its check roster/order remains the example validator's and literal tests' responsibility.

The [Step `08` annotation owner](../../src/emrys/stages/cohort_candidate_preprocessing/_step_08_annotation.R)
derives each transcript span from its exons, including introns between them, then assigns
strand-compatible overlaps and sorts and deduplicates their gene IDs. GTF `gene` or `transcript`
feature spans are not the assignment range. The
[sites contract](../../src/emrys/contracts/scientific_evidence/step08.py) admits a header-only
table and requires unique candidate IDs. Step `08` can retain intergenic candidates, and its
orientation-to-strand mapping remains provisional under the
[stage contract](../../src/emrys/stages/cohort_candidate_preprocessing/CONTRACT.md). Thus a row is
one mechanically labeled candidate, not necessarily one genomic locus or an exonic event. Two
orientation candidates at one locus remain two candidates if present.

The proposed tally's **population** also needs to be explicit.
[Step `07`](../../src/emrys/stages/partitioned_cohort_mpileup/producer.py) applies its bcftools
filter before Step `08`; [Step `08` processing](../../src/emrys/stages/cohort_candidate_preprocessing/_step_08_vcf_processing.R)
retains every supported SNV allele from that input and carries QUAL, FILTER, and depth values
without a second candidate-selection rule. The built-in
[Step `09` method](../../src/emrys/analyses/paired_cmh_candidate_ranking/CONTRACT.md) can
subsequently label rows untested or nonsignificant. A sites-only tally therefore counts
**pre-CMH candidate-to-annotation assignments across the cohort**, including rows that Step `09`
does not test or select. Decide whether all RNA changes, intronic/intergenic rows, low-depth rows,
and carried non-PASS FILTER values belong in this demonstration; never label the counts as
validated editing sites, selected discoveries, or gene-level biological activity.

**Proposed example, pending method selection:** count candidate-to-gene assignments from Step `08`
in Step `09`. A candidate with two gene IDs contributes once to each, so the sum can exceed the
number of candidate rows. The descriptor can name only the `step08_sites_v1` input adapter for this
calculation; include the input receipt or summary only if the method actually consumes it for a
stated check. The built-in provider declares the Step `08` summary as a dependency/provenance input
even though its worker and validator arguments consume sites and input receipt
([provider](../../src/emrys/analyses/paired_cmh_candidate_ranking/__init__.py),
[owner contract](../../src/emrys/analyses/paired_cmh_candidate_ranking/CONTRACT.md)). That declaration
is not evidence that this example needs the summary as a method input. The Step `08` predecessor
edge still supplies the task completion barrier. One
possible literal oracle, **if** lexicographic gene ordering and threshold `1` are selected, is
assignments `A;B`, `A`, `NA` producing UTF-8 bytes
`gene_id\tcandidate_count\nA\t2\nB\t1\nNA\t1\n`. Threshold `2` would retain only `A\t2`.
Decide whether the threshold applies to `NA`, how `NA` sorts, and whether empty input or filtering
produces a header-only TSV. A same-strand overlapping-gene fixture is needed to demonstrate a real
multi-gene Step `08` row; the existing
[stage test](../../tests/stages/cohort_candidate_preprocessing/test_step_08_vcf_preprocessing.R)
does not establish that case. A hand-authored
[scientific evidence fixture](../../tests/scientific_evidence_test_support.py) has
`gene1;gene_overlap`, but its parsing check cannot establish that a real GTF yields that row. The
Step `08` validator checks lexical and count invariants, not a fresh GTF overlap computation. The
existing `smoke-v1` GTF has only nonoverlapping transcripts; its engineered rows suggest
`GENE_PLUS=1` and `GENE_MINUS=2` as an **unexecuted** public oracle, with neither `NA` nor
multi-gene coverage. This is a descriptive computational demonstration, not an editing-site or
biological claim.

**Inferred representational limit, untested:** GTF admission requires nonempty IDs on relevant
features but does not explicitly reserve literal `NA` or `;` in gene IDs
([annotation import](../../src/emrys/stages/cohort_candidate_preprocessing/_step_08_annotation.R));
Step `08` writes missing values as `NA`, while the
[sites reader](../../src/emrys/contracts/scientific_evidence/step08.py) treats `NA` as missing and
`;` as an ID separator. Before promising arbitrary collaborator GTF compatibility for this tally,
state the supported-ID assumption or run a tiny admission/serialization test. This observation
alone does not authorize redesign of Step `08`.

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
metadata. Ownership is checked for the exact package named before `:` in the entry point, including
a dotted package name. A collaborator entry point rooted at `emrys:callable` would fail if its
distribution does not own the full core package tree; `emrys.subpackage:callable` has a narrower
tree and needs its own installed ownership proof. A dedicated example package is the simplest
candidate. Verify the chosen layout from built, non-editable wheels in the selected environment.
Include missing and duplicate entry-point refusal cases; no new registry, installer,
workflow graph, or core entry point is indicated.

**Open packaging decision:** one wheel with both entry points is the smaller initial surface, but
the Analysis provider digest covers its reporter source too. A reporter source change in that wheel
can therefore block old Analysis readmission. Two separately installed wheels would separate those
content identities while adding setup and maintained-package cost. Record the chosen tradeoff before
the example layout and compatibility tests are fixed. If two wheels are selected, each entry point
must live in a package tree fully owned by its own distribution; splitting the same selected tree across
the wheels fails [installed ownership admission](../../src/emrys/libraries/installed_package_identity.py).
Do not change core hashing to hide the tradeoff.

### EX-04 — planning, validation, and recovery

[`TaskPlanningContextV2`](../../src/emrys/analyses/__init__.py), lines 94–113, supplies admitted inputs, working and final output paths, resource
threads, and a controlled Python command builder. [`materialization.py`](../../src/emrys/orchestration/run_coordinator/materialization.py), lines 1066–1207, checks that the
returned plan includes every declared input, unique paths, and unique provenance roles. It cannot
discover an extra file that the worker actually reads but never declares, so the example test must
compare planned roles and paths with worker consumption. The core checks command argument shape,
but does not establish that the producer or validator load from the provider's installed wheel;
descriptor admission checks ownership of the provider, normalizer, and planner callables. The
example must exercise its commands outside the checkout and verify their import origin. Its
`validator_command` helper targets core
`emrys validate` routes (lines 285–295); a collaborator's own validator should use `python_command` with
its installed module. The validator must independently recompute the proposed counts and publish the
exact seven-column report header defined by [`emrys.libraries.validation`](../../src/emrys/libraries/validation/report.py), lines 13–21. The core [`all_pass.py`](../../src/emrys/orchestration/run_coordinator/all_pass.py),
lines 33–105, requires a nonempty, all-pass report with matching Step/scope and unique check IDs;
it does **not** require a fixed roster or order. Give the example a literal expected check-ID list
and order. `AnalysisArtifactV1.exact_data_rows` can pin row **count** only; it does not enforce that
list or order. The
independent validator must compute from admitted sites, rather than call the producer's count helper;
generic TSV admission checks shape and rows, not tally semantics.

[`task.py`](../../src/emrys/orchestration/run_coordinator/task.py), lines 1742–1758 and 2732–2782, gives prepublication validation to two hard-coded built-in
owner keys. A **distinct** external Step `09` owner publishes native outputs, runs its validator,
then requires all-pass. Descriptor admission checks safe and unique owner keys but does not reserve
those two names. A collaborator that reused the built-in CMH key could enter that special route;
this is a source inference, not an executed example. Require the proposed owner key to be distinct
and decide separately whether core should reject reserved keys for arbitrary external providers.
Both a nonzero validator exit and a zero-exit report with a nonpassing row can leave committed
native outputs and a failed Task attempt without a verified-task. The validation report may be
absent after a nonzero exit. The
[runner's preservation contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#task-and-attempt-lifecycle)
leaves postpublication failures ineligible for automatic continuation; preserve that state for
operator disposition rather than promise retry or rollback. Test both failure routes through the
external Step `09` path; the existing generic failed-row test does not prove it. The producer must
write to supplied working/scratch paths. The independent validator must read final `outputs` and
write its report at the supplied `validation_report_path`, which is excluded from producer outputs.
Any other temporary writes remain within owned paths. Neither process may delegate relevant work
to preexisting or remote processes. These are trusted-worker obligations, not behavior proved by
structural admission or a filesystem/network sandbox.

### EX-05 — scientific reporter boundary

The selected matching reporter receives [`AnalysisReportContextV1`](../../src/emrys/reporting/__init__.py), lines 24–62, and returns
`AnalysisScientificReportV1`; the core invokes it and checks returned input identities in
[`context.py`](../../src/emrys/reporting/_run_report/context.py), lines 197–279. Core reporting owns the evidence view, publication, and receipt. Its
[`validation.py`](../../src/emrys/reporting/_run_report/validation.py), lines 362–475, checks more than nonempty HTML: doctype, language, one title and main
landmark, heading order, report identity and computational banner, safe resources, and accessible
tables. The example reporter must satisfy this contract without importing a built-in reporter's
private renderer or recalculating the scientific result.

Prove the generic return and HTML boundaries with a literal installed reporter: valid multi-row
content must pass; malformed renderer or figure metadata, an unbound extra input, or an invalid
HTML shell must refuse publication. A nonempty HTML byte string is not sufficient.

Reporter selection and Doctor readiness are keyed only by module ID
([`reporting/__init__.py`](../../src/emrys/reporting/__init__.py),
[`doctor.py`](../../src/emrys/orchestration/run_coordinator/doctor.py)). There is no separate core
negotiation of a reporter version against the admitted Analysis module version, and
`AnalysisReportContextV1` does not carry that version as a direct field. The Run summary binds the
Analysis policy file by path and hash rather than copying its module-version value into the reporter
context. If a separately versioned reporter reads that policy to refuse an unsupported pair, it
must declare the additional read through `AnalysisReportInputV1` and recheck its identity. Freeze
and test the example's supported Analysis/reporter pairing; decide whether the existing context is
sufficient for the selected one- or two-wheel layout before promising wrong-version refusal.
Doctor's successful lookup does not prove compatibility.

`AnalysisScientificReportV1.inputs` may be empty. The core rechecks admitted Analysis artifacts
even when the reporter does not repeat them in that returned roster. If the reporter opens an
additional report-only file, it must return that file's `AnalysisReportInputV1` identity for
snapshot and receipt checks ([`context.py`](../../src/emrys/reporting/_run_report/context.py), lines 253–291). The proposed tally reporter should avoid extra file inputs unless the method needs them.
For a variable-length tally TSV, generic
[TSV inspection](../../src/emrys/reporting/_artifact_index/_text_tabular.py) provides row count and
limited metadata, not a full row projection. The reporter must open the admitted artifact snapshot
to render every count; core rechecks the admitted bytes after rendering. Test multiple literal
result rows and changed-input refusal rather than assuming projected rows contain the whole tally.

New publication re-admits the current Analysis and reporter. The [report context](../../src/emrys/reporting/_run_report/context.py) passes only required, present, complete artifacts whose Step, scope, hash, size, and media type match the admitted summary. The [artifact index](../../src/emrys/reporting/_artifact_index/_text_tabular.py) checks declared TSV header and row shape/count, but does not recompute the proposed tally; that remains the independent validator's job. Test malformed or missing artifacts at admission, and test the reporter only with admitted snapshots/projections. Doctor requires a matching reporter for the ordinary through-report Run; `--no-report` permits scientific execution before reporter installation, with later reporting subject to Analysis readmission.

That late-report path is conditional: the original Analysis must still readmit when reporting
starts. Adding reporter source to the same wheel after the Run changes its distribution-owned
bytes and can block that readmission. A separately installed reporter wheel avoids this particular
coupling; adding only entry-point metadata with unchanged package bytes is a different case, not a
general upgrade promise. Exercise the chosen late-install route explicitly, including refusal when
the Analysis identity changes.

[Retained report validation](../../src/emrys/reporting/transaction_validation.py) checks the original receipt, data inputs, and HTML without invoking today's reporter. Upstream Run-summary and artifact validation still re-admits the current **Analysis** provider. If Analysis and reporter share a wheel, changing reporter source bytes changes that wheel's provider digest and can block Analysis readmission even though the renderer is never called. Removing only the reporter entry-point metadata is a different case because `.dist-info` is excluded from the provider digest; whether retained inspection succeeds must be tested with the exact remaining Analysis package and receipt. For the chosen layout, test new publication and retained inspection with reporter source drift; test metadata-only entry-point removal separately.

[Public report admission](../../src/emrys/orchestration/run_coordinator/reporting_operation.py) requires valid Run integrity, a succeeded Attempt and receipt, and complete Results. Blocked reporting or a nonempty unadmitted destination refuses generation rather than adopting present HTML; an admitted complete report is rechecked and reused. Inspect the exact Run before and after reporting, and do not count an HTML file's presence as report completion.

Automatic reporting begins only after the scientific Attempt succeeds. A reporter or publication
failure returns a reporting failure while leaving complete scientific Results intact
([`control.py`](../../src/emrys/orchestration/run_coordinator/control.py)). The
[reporting operation](../../src/emrys/orchestration/run_coordinator/reporting_operation.py)
publishes a Run-summary transaction before the HTML transaction. Each has a separate immutable
start and verified marker; once a start exists,
[publication refuses a second start](../../src/emrys/orchestration/run_coordinator/reporting_boundary.py).
The example's recovery checks must distinguish reporter/HTML preparation failing before HTML ledger
entry, after a successful Run-summary transaction, from a failure after HTML start. Record the
admitted status, ledgers, outputs, and next action in each case; do not promise rerun, cleanup, or
adoption of partial files.

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

The persisted module identity does not fingerprint the descriptor's task roster, input/output
declarations, or resource floors separately from installed bytes. Project admission composes a
profile once; materialization later readmits and invokes a fresh descriptor
([`materialization.py`](../../src/emrys/orchestration/run_coordinator/materialization.py)).
Identical package bytes with environment-dependent descriptor output could therefore change those
declarations without a direct descriptor-to-profile equality check. This is an **inferred trusted
provider limit**, not a reproduced defect. Keep the example descriptor deterministic and test
repeat admission/profile equivalence; a general descriptor-binding change needs separate review.

The [Run implementation identity](../../src/emrys/orchestration/run_coordinator/run_implementation.py)
also hashes a shared artifact-admission closure containing the entire
`contracts/scientific_evidence` tree, including built-in Step `09` evidence code. The
[materializer](../../src/emrys/orchestration/run_coordinator/materialization.py) includes that
shared component in an external module Run as well. A change to the built-in CMH evidence contract
can therefore change an unrelated external Run's implementation identity. This is source-derived
coupling, not an observed public failure or grounds for silently narrowing the core hash. Decide
whether that broad admission authority is intentional before promising module-isolated reuse.

### EX-07 — dependency and installation authority

The [provider guide](../../src/emrys/analyses/README.md#collaborator-providers) says Doctor checks declared tools and packages and managed repair does not install
custom dependencies. Product computation, validation, and reporting must never install.
[Engineering conventions](../operations/ENGINEERING_CONVENTIONS.md#dependencies-and-environments) say installation is explicit setup work and tests never install; the current
[`test_package_distribution.py`](../../tests/test_package_distribution.py), lines 138–176 and 250–308, nevertheless builds a wheel and uses `uv` in an isolated
test environment. It also generates a temporary `uv.lock`; its build and sync commands specify
`--offline`, but the lock command does not. The repository lock is unchanged. Treat both temporary
lock generation and installation as policy questions, not automatic authority for a second setup.
A bounded test plan must say exactly who creates the disposable environment, which core and example
wheels enter it, and whether the convention needs clarification. Do not invent a dependency solely
to make the example look complete.

The [descriptor](../../src/emrys/analyses/__init__.py) may reuse an existing fixed runtime check by
ID or declare an executable, R namespace, file, or package-tree check. IDs must be unique and avoid
reserved/fixed-check collisions; non-R custom targets must be absolute. [Doctor](../../src/emrys/orchestration/run_coordinator/doctor.py) checks those declarations but has no Python-distribution check. Python requirements belong in wheel metadata and explicit package-manager setup; loading the installed example then exercises their availability. Doctor also checks the matching reporter by default, with `--no-report` as a documented execution route for later report generation. A standard-library-only example can avoid an unnecessary custom dependency declaration.

The reporter entry point has no dependency-declaration interface of its own; Doctor's reporter
readiness check only loads and attributes that callable. A lazy or render-only reporter dependency
can pass Doctor and fail during HTML preparation. Keep the example reporter within explicit wheel
requirements and exercise its actual render path in the installed package proof.

### EX-08 — public-path evidence gap

The [installed-wheel test](../../tests/test_package_distribution.py), lines 341–460, exercises installed core commands outside the checkout. Its report
portion, lines 486–610, uses a built-in fixture and reporter through private `prepare_context` and
`publish_report` calls, so it is not public `emrys report` evidence. The [real-synthetic driver](../../tests/tools/real_synthetic_e2e.py), lines 1652–1664,
initializes the built-in Analysis. Neither currently executes an external provider and reporter via
a public Run. A proposed proof is one tiny disposable Project with the selected example wheel(s)
installed alongside the exact EMRYS wheel, followed by public validation, no-write preview, execution,
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
that preview checks Project YAML and the selected Analysis name but does **not** load the external
provider. Provider admission and planning occur after compute delegation. A direct-profile preview
can plan tasks, subject to
Doctor and storage readiness. Record these as distinct proof levels rather than calling a Slurm
submission preview planning evidence. No public external execution has been performed here.

| Public exercise | Evidence it can supply | Limit |
| --- | --- | --- |
| `emrys validate --project` | Installed Analysis discovery and normalized Project admission. | No Doctor readiness, task plan, or execution. |
| `emrys doctor --project --analysis` | Selected runtime dependency and reporter readiness. | No worker or validator result. |
| Direct-profile no-write `emrys run` | Full task planning when Doctor and storage admission pass. | No native publication or report. |
| Slurm-profile no-write `emrys run` | Project shape/selection and scheduler submission preview. | External provider admission and task planner have not run. |
| `emrys report` without `--execute` for complete Results and absent reporting | Run-summary preparation and evidence-index preflight. | Does not invoke the selected reporter or render/check its HTML. |
| `emrys report --execute` with complete Results and absent reporting | Invokes the reporter and attempts HTML publication; inspection must then admit a complete report. | A reporting failure leaves scientific Results complete and requires state-specific disposition. |
| `emrys report` on an already complete report | Re-admits and reuses retained reporting. | Returns before fresh Run-summary preparation and does not invoke today's reporter. |
| Approved grouped Run, exact `inspect`, and `report` | Execution and report claims only when retained Task, Result, and report admissions pass at the tested commit. | No site, scientific-review, or biological claim. |

The smallest supplied real-tool synthetic dataset, `smoke-v1`, contains four libraries with 130
read pairs each and a 100 kb reference. It initializes a built-in Analysis and hashes a completion
manifest, so substituting an external `project.yaml` is an authored variation with its own expected
result, not the unmodified fixture's oracle. Its annotation covers only two named genes at the
intended candidate positions and does not demonstrate `NA` or a multi-gene assignment. A public
`--from-processing-run` can reuse Steps `00`–`06` but still runs Step `07` onward; it does not inject
a finished Step `08` table for Step `09` only. Keep a literal hand-authored unit oracle separate
from any later public end-to-end oracle, and budget the latter's real-tool cost.

The current [real-synthetic driver](../../tests/tools/real_synthetic_e2e.py) also replaces the
generated default execution profile with a direct CI resource document that lowers repeated-stage
memory floors for tiny fixtures, and writes separate Slurm settings. An external `smoke-v1` proof
needs its own explicit profile/resource policy and should record that edited Project/profile as an
authored fixture variation. A direct profile can support no-write planning; real alignment,
sorting, mpileup, and analysis need a measured grouped whole-Run Slurm allocation. Installing the
external wheel alone does not establish that the stock fixture is a feasible tiny CI Run.

**Proposed public proof route, after separate setup and execution authority:** author a named
external Analysis in `project.yaml` and install the exact core and selected example wheel(s) in the
selected environment; run `emrys validate --project PROJECT`,
`emrys doctor --project PROJECT --analysis NAME`, and
`emrys run --project PROJECT --analysis NAME` for a read-only preview. After runtime readiness and
an approved grouped whole-Run Slurm allocation, run
`emrys run --project PROJECT --analysis NAME --execute` and
`emrys inspect --project PROJECT RUN_ID`. A successful through-report Run may already contain the
report; `emrys report --project PROJECT RUN_ID` must re-admit/reuse it. If Results are complete and
reporting was deliberately skipped, preview that report command before an authorized `--execute`,
then inspect again. On Slurm, the compute delegate must see the same installed wheels, and report
generation may itself schedule work. These commands are proposed proof steps, not checks performed
for this draft. Report preview is only Run-summary preflight; executed reporting is needed to test
the selected reporter. Doctor checks reporter discovery and ownership, not rendered content.

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

Guided [`emrys init`](../../src/emrys/orchestration/run_coordinator/onboarding.py) emits the
built-in paired-CMH Analysis fields and previews them against that module. It does not author the
external `module`/`config` mapping. The collaborator guide must supply a complete hand-authored
external Project, or a precise edit of a generated Project, with `partitions`, sample/reference
paths, and an execution profile. Hand-authored Projects must set numeric `sjdb_overhang` and
`genome_sa_index_nbases`; an omitted `genome_chr_bin_nbits` normalizes to `18`. Derive or measure
values for the tiny reference/read length instead of copying a stock study's index settings.

The current [Analysis owner guide](../../src/emrys/analyses/README.md) says core checks the
producer and independent validator. The source establishes command-shape admission and runner
supervision but cannot prove validator independence, code origin, or complete reads. Correct that
wording during owner-document transfer once the installed example supplies narrower evidence.

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

| Maintained surface | Reduction or consolidation candidate from this review |
| --- | --- |
| Core product code | Reuse the existing provider, reporter, registry, and one artifact-index reconciliation owner. EX-13 needs an owner-local dispatch decision; no safe core-code deletion is yet demonstrated. |
| Example product code | Keep one bounded package tree if its identity coupling is acceptable; count any second wheel separately. No preexisting example code can be retired. |
| Tests and protections | Compare the [mocked composition test](../../tests/orchestration/run_coordinator/test_materialization.py) assertion by assertion with the installed proof; retire only exact overlap and preserve its unique planning checks. Preserve built-in Step `09`/`10` reconciliation defenses. |
| Scripts and CI gates | Reuse an existing static/wheel lane if its measured runtime fits; no duplicate new runner script or safe script retirement has been identified. |
| Schemas and configuration | Reuse the current provider schema, Project selection, and profile composition. The hypothetical [configuration sample](../../configs/README.md) may become a link to the tested package; no core schema/config retirement has been shown. |
| Documentation | Keep one runnable package-adjacent walkthrough and link from owner guides, removing only duplicate hypothetical instructions after transfer review. |
| Mutable state and evidence | Add no plugin registry, store, or recovery state. No existing state retirement has been demonstrated; retained exact evidence is preserved. |

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
existing gate; otherwise uninstalled example imports can fail core collection, or example tests
can silently enter the core shard/timing baseline. Run package-local tests in the disposable
installed-wheel lane and claim no core coverage credit for unmeasured example code. Count any new
configuration or tooling. Its package name, version, and license terms remain explicit design
decisions; do not infer them from the core distribution.

The [pre-commit hooks](../../.pre-commit-config.yaml) also name only `src/`, `tests/`, `scripts/`,
and `setup.py` for Python checks. The [source-dependency gate](../../tests/tools/source_dependencies.py)
checks `src/emrys`, so it will not police private-owner imports in an external example tree.
[`test_ci_workflow.py`](../../tests/test_ci_workflow.py) fixes the CI static/wheel command roster and
manual inputs, while [`test_public_cli_contracts.py`](../../tests/test_public_cli_contracts.py)
classifies every Make target and compares its command expansion to a golden. If a new gate or Make
target is chosen, update these protections deliberately. [`all-checks`](../../tests/tools/run_validation.py)
preflights the exact locked development environment and four lanes; installing a separate example
wheel into that environment is not an implicit route. Use a disposable package-proof environment
after resolving the setup policy in EX-07. Keep the external validator's literal ordered check
roster with its package tests: the existing central Step `09` [roster expectation](../../tests/contract_integration/validation_rosters/validation_roster_expectations.py)
is for the built-in Analysis, not a universal external Step `09` registry. Any change to generic
roster authority belongs to the separate [`REPORT-ROSTER-01`](backlog_matrix.md) decision, not this
example by default.

### EX-12 — trusted extension code

[`admit_installed_provider`](../../src/emrys/libraries/installed_package_identity.py) imports an
entry point; [`load_analysis_module` and `admit_configuration`](../../src/emrys/analyses/__init__.py)
call collaborator-supplied provider and normalizer code during Project admission. Planning calls
the provider's planner, execution runs its commands, and new report publication calls its
reporter. Distribution ownership and content identity make selected code attributable; they do
not make it safe to execute or confine its filesystem/network effects. The [worker contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#task-and-attempt-lifecycle)
explicitly assumes trusted code that keeps relevant work in descendants and owned paths.

The example walkthrough must tell operators to install a trusted, reviewed distribution in the
selected environment. An example-specific test can check command arguments, installed import
origins outside the checkout, and observed fixture writes. Review the example worker source for
undeclared reads, subprocesses, and services; report that assessment for the tested revision. No
ordinary fixture test establishes a complete read set or a filesystem/network sandbox for other
providers.

### EX-13 — reporting reconciliation blocks generic Step 09

The [artifact registry](../../src/emrys/reporting/_artifact_index/registry.py) adds outputs from the
selected external descriptor. But [native reconciliation](../../src/emrys/reporting/_artifact_index/reconciliation.py)
dispatches solely by Step ID: every complete Step `09` scope goes to the built-in
[`reconcile_step09`](../../src/emrys/reporting/_artifact_index/reconcile_step09.py), which uses
unconditional `next(...)` lookups for four paired-CMH adapters. A one-task tally declares its own
result and validation adapters, so a complete tally scope has none of those four. Source review
therefore predicts `StopIteration` during Run-summary preparation; that exception is outside the
operation's handled `ArtifactIndexError` path. This is a **source-derived blocker**, not an observed
external-Run failure. It affects report preview before the external reporter runs, new publication,
and the retained Run-summary admission path. Generic adapter registration alone does not close it.

The same Step-only dispatch applies the built-in
[`reconcile_step10`](../../src/emrys/reporting/_artifact_index/reconcile_step10.py) to any complete
external Step `10` scope. It requires the built-in context receipt, three built-in CMH Step `09`
sources, reference inputs, and four built-in context outputs. The proposed single-task example
avoids Step `10`, so this is a documented limit unless the accepted outcome later requires an
external Step `10` example. Do not claim optional external Step `10` is reportable from the current
source. [Materialization](../../src/emrys/orchestration/run_coordinator/materialization.py) also
labels every Step `10` lock `scientific-context` and adds `.previous` residue checks regardless of
the selected module. An unrelated external Step `10` needs a naming and residue-policy review
before its lock behavior is called compatible.

**Open owner-local design decision:** use the admitted Analysis descriptor/profile to select when
the existing CMH and context reconcilers apply, while still admitting declared external artifacts
and independent validation. Preserve the built-in Step `09` source/hash/sample-order defense and
Step `10` receipt graph defense at equal strength; do not globally remove them or create a parallel
artifact registry. Audit all first-publication and retained-inspection callers, add built-in parity
and generic-external tests, and count core-code/test/gate growth under EX-10 before approval. A
public external Run-summary/report result is necessary to close this row.

The selected module is already admitted in
[`prepare_context`](../../src/emrys/reporting/_artifact_index/context.py) before reconciliation,
and retained [Run-summary validation](../../src/emrys/reporting/transaction_validation.py) calls
that same preparation path. These are the design candidates to review, not implementation
authority:

| Candidate | Expected effect | Review condition |
| --- | --- | --- |
| Select native Step `09`/`10` reconcilers from the admitted module identity, keeping Steps `00c`–`08` common. | Existing paired-CMH and context checks remain attached to their owner; external declared outputs use generic artifact and scope checks plus their independent validator. | Preferred source-level candidate. Check first publication and retained validation together, and confirm no built-in source/hash/sample-order or receipt-graph defense is weakened. |
| Infer the owner from whether CMH adapters happen to be present. | Smaller-looking dispatch, but a missing built-in adapter could select the generic route and bypass the very check meant to catch it. | Do not use without an independent, exact built-in roster check; currently no demonstrated net advantage. |
| Add a provider-supplied reconciliation callback or second artifact registry. | Lets each provider run custom report-time checks. | No concrete need in this one-task example; it expands the public interface and maintained authority. |

| Required proof before closing EX-13 | Expected observation |
| --- | --- |
| Built-in Step `09`/`10` valid fixture and existing mutation cases | Same complete results and same failure propagation for changed CMH source/hash/sample order, significant subset, spectrum, context receipt, and context outputs. A missing built-in adapter must fail, not enter a generic fallback. |
| External Step `09` valid result and validation report with distinct adapter IDs | Run-summary preview/preparation, executed publication, reporter HTML, and retained admission complete without a built-in CMH projection. |
| External missing or malformed result, changed native bytes, or mismatched inventory | Generic admission and scope/receipt checks refuse or mark incomplete at the relevant boundary; no uncaught `StopIteration`, adopted output, or promoted report claim. |
| Retained Run summary and HTML after original publication | Re-enter the corrected common artifact-index path, bind original bytes and ledgers, and avoid invoking today's reporter during reuse. |

These proofs must use a genuinely installed external provider for the acceptance claim. A
private artifact-index fixture can isolate the reconciliation decision first, but cannot close
public discovery, Run execution, or reporting on its own.

The existing generic index checks the exact adapter roster for each inventory scope it sees,
adapter shape and validation-report status, then propagates incomplete required scopes. It does
not independently recompute an external tally or prove that all expected scopes appear in a
hand-authored inventory. The public materialized inventory and Attempt binding, plus the package's
independent validator, must supply those distinct checks. Retained validation compares recorded
source, availability, and completion facts against a fresh context; a fallback that skips built-in
native checks could falsely retain an old CMH result.

### EX-14 — installed watch assumes the built-in tail

The installed [dashboard](../../src/emrys/orchestration/run_coordinator/dashboard.py) labels Step
`09` as paired-CMH ranking and Step `10` as scientific context, with built-in method descriptions
and an R-process resource description. Its default owner-key map names the
built-in providers. Although `parse_workflow` accepts an override, the production
[_inspection presentation](../../src/emrys/orchestration/run_coordinator/_inspection_presentation.py)
does not supply one. The dashboard also says reporting begins after Step `10`, which is false for
the proposed Step `09`-only descriptor. The source suggests an external `analysis_owner` may appear
unmapped while the overview gives a CMH label; no external Run/watch trace was executed here.
Test the public display with the installed example and select the smallest owner-local correction
for truthful labels, stage detail, resources, and next action. Scheduler text remains diagnostic,
not completion evidence.

Additional source-level display mismatches: the shared inspection/watch milestone calls Steps
`09`/`10` “Statistical/context processing,” even when the selected method is a descriptive tally;
the REPORT stage describes **three** transactions and its resource text repeats that count, while
the [reporting boundary](../../src/emrys/orchestration/run_coordinator/reporting_boundary.py) and
[owner contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#resume-inspection-results-and-reporting)
define two. This count is wrong for built-in Runs as well.

| Owner-local candidate | Evidence to preserve or add |
| --- | --- |
| Derive external `owner_key` to Step mapping from the admitted Run/task roster and pass it to the existing parser; before a Run is admitted, leave unknown log rules unknown. | External active/completed owner trace maps to `09` only when bound to that Run; built-in and unrelated log behavior remains unchanged. Scheduler text never becomes completion authority. |
| Use generic Step `09`/`10` titles and resource wording for external methods, retaining CMH/context wording only when the admitted built-in module is selected. Use the selected task roster for next-unlock text. | Step `09`-only external overview, detail, and verbose `inspect` do not promise CMH or Step `10`; the built-in presentation stays accurate. No new provider display-title API or report-time provider invocation is needed. |
| Correct REPORT stage descriptions to the owner's two transactions. | Both built-in and external public snapshots agree with the Run-summary and HTML ledgers, without treating a report file as scientific completion. |

The [watch Runbook](../operations/RUNBOOK.md#watch-one-fixed-selection) already owns selection
and diagnostics. The runnable collaborator instructions belong in the package guide under EX-09,
with a short owner link where needed.

## Proposed bounded delivery sequence

1. **Refresh the review facts against the exact implementation target.** Recheck PR #304's live head,
   changed source paths, accepted backlog row, and guardrails. Revise any drifted discovery before
   treating a quoted line or contract as current.
2. **Choose one collaborator method.** Accept or replace the proposed candidate-to-annotated-gene
   tally. Define the pre-CMH population after Step `07` selection and decide inclusion of `NA`,
   intronic/intergenic, low-depth, non-PASS, and untested rows. Confirm its full input is available
   from Step `08` and needs only existing artifact kinds. The descriptor fits Step `09`, but EX-13
   blocks Run-summary/report admission. Review a bounded module-aware reconciliation choice,
   including first publication and retained inspection, before claiming end-to-end fit. Preserve
   built-in CMH and Step `10` defenses; leave optional external Step `10` open unless separately
   demonstrated. Stop for interface review if the selected method needs a new task boundary.
3. **Freeze literal behavior.** Specify the sites-only input or a reason for each additional
   adapter; define unique-candidate, multi-gene, `NA`, sorting, threshold, zero-row, header-only,
   newline, UTF-8, and supported GTF-ID rules. Keep a unit oracle, a real Step `08` same-strand
   overlap fixture, and a real-tool public-Run oracle as distinct proofs. State that the tally is
   descriptive, not biological interpretation.
4. **Quote the footprint and seek bounded authority.** Inventory planned new, changed, and retired
   files and net lines by core code, example code, tests, gates, configuration, docs, and state.
   Include the reporting reconciliation and watch-presentation candidates, preserve the mock's
   unique checks and all exact evidence, and resolve temporary lock/install policy. Obtain
   implementation plus any quantified `AC-GUARD-006` growth authority before edits.
5. **Define the external package boundary.** Choose one shared wheel or two separately installed
    wheels after accounting for reporter-source changes in the Analysis digest and the maintenance
    cost of separation. Specify names, versions, licenses, supported exact EMRYS wheel/commit, and
    standard-library or explicit Python requirements. Use a dedicated distribution-owned package tree,
    matching package-level entry points, and distribution-owned callbacks/workers; state that
    installing and admitting the selected package
   executes trusted code and that admission is not a sandbox. Add no core registry or installer.
6. **Admit one immutable configuration.** Add a closed JSON schema and normalizer for the selected
   method. Verify unknown-key refusal, equivalent authored forms normalizing to one policy and
   Analysis ID. Keep descriptor construction deterministic and check repeated admission/profile
   equivalence. Test provider readmission and Attempt runtime bindings separately, including
   changed module metadata/bytes and target-only drift. State the distribution-version,
   dependency-field, and descriptor-output identity limits.
7. **Declare and plan one task.** State every input adapter and consumed path, native TSV and
    validation-report outputs, Step/scope, minimum resources, and genuinely needed dependencies.
    Choose a distinct owner key outside the built-in prepublication special case.
   Use working outputs for the producer and final outputs for the validator. Verify no-write direct
   planning, provenance roles, input completeness, path safety, installed command origins, and
   resource floor. Do not count Slurm submission preview as provider admission or task planning.
8. **Implement separate producer and validator.** The producer writes deterministic bytes only to
   supplied working paths. The validator reads admitted sites and final published output,
   independently recomputes the tally, and writes the seven-column report to its separate path.
   Assert exact check IDs/order, both nonzero and nonpassing validator failures, retained outputs,
   failed Task attempts, and absent verified-task records. Do not infer semantic truth from a
   passing process or generic TSV shape check, or assume automatic continuation after publication.
9. **Implement one reporter.** Render only from admitted artifact snapshots/projections and return
   identities for any additional report-only files it opens; core rechecks admitted artifacts.
   Read the variable-length tally through its admitted snapshot; the generic projection does not
   contain every row. Produce a scientific HTML view that satisfies core checks. Verify literal
   multi-row content, supported Analysis/reporter pairing, new-publication refusal, retained reuse,
   and source/metadata drift for the chosen wheel layout.
   Exercise failure before and after HTML ledger start, keeping scientific Results and reporting
   status separate; report preview does not prove the reporter.
10. **Add the package-specific quality lane.** Choose an intentional test selection and package
    lint/format/compile/build checks. Route pre-commit and source-import checks as appropriate;
    update CI-command and Make-target contract tests for any changed gate. Keep the locked
    development environment, existing core wheel test, and Python shard scope honest; do not
    claim core coverage for an unmeasured example or expand local checks into heavy science
    computation.
11. **Exercise the installed public route.** After disposable setup authority, test the core and
    selected example wheels outside the checkout with missing/duplicate entry-point refusal and no
    checkout import leakage. Record the exact wheel identities and core commit. After execution
    authority, use an explicitly authored `smoke-v1` Project. A direct resource profile may prove
    no-write planning; real-tool execution uses a measured grouped Slurm profile in an approved
    allocation. Validate and run Doctor against the selected venue. Count Slurm preview as
    submission evidence only; require compute-delegate provider admission and task planning.
    Count report preview as Run-summary preflight only; require executed reporting and an admitted
    successful report at the exact commit. Exercise installed watch with the external owner and
    Step `09`-only tail; correct misleading CMH/Step `10` presentation without making diagnostic
    text a completion authority.
12. **Transfer documentation and reconcile acceptance.** Put the runnable walkthrough beside the
    package; link owner guides and retire only demonstrably duplicated hypothetical prose. Compare
    literal expected bytes, tests, hosted checks, retained artifacts, and footprint against each
    matrix row. Update the accepted backlog row only after its complete outcome passes at the
    stated evidence level; leave site, scientific, and biological claims open until independently
    established.

## Open decisions before implementation

Resolve the Step `09` reporting reconciliation blocker and built-in parity; the selected method's
edge cases and expected output; one shared wheel versus separate Analysis/reporter wheels and
their version pairing; whether core reserves built-in owner keys; watch presentation; package
metadata and license; the quantified growth
exception and disposable lock/install policy; and the smallest complete CI scenario. For each new discovery,
identify its exact revision and source or executed artifact, then revise the corresponding matrix
row. A source inference stays labeled as such until an actual public-path check supplies execution
evidence.
