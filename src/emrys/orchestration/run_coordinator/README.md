# Run coordinator

This package turns a validated Project and selected Analysis into a Run plan,
executes that plan, and reports its state. Operators use the grouped `emrys`
commands; these modules are private implementation details.

## Ordinary journey

Use the [quickstart](../../../../quickstart.md) for a first Run and the
[Runbook](../../../../docs/operations/RUNBOOK.md) for later operation and Slurm.
[The contract](CONTRACT.md) defines command confirmation, immutable records,
inspection, current-version compatibility, and recovery. It is the authoritative
home for those rules; this README explains how the implementation fits together.

## Specialized setup and reuse

The [configuration guide](../../../../configs/README.md) explains manifests and
Analysis fields. The [runtime procedure](../../../../docs/operations/RUNBOOK.md#institution-provided-runtime)
explains discovery and managed/site setup. The [reuse procedure](../../../../docs/operations/RUNBOOK.md#reusable-processing)
explains how a new downstream Run uses a compatible processing Run without
changing it. Synthetic dataset choices belong in the
[quickstart](../../../../quickstart.md). `emrys setup` owns the closed
repository-root `.env` for Projects home, site and optional application-log
defaults; command-line and process values remain higher precedence.
The ordinary named initializer guides FASTQ pairing, biological assignments and
regions, then owns the resulting manifests inside the Project. The separate
manifest drafting command remains an advanced structural helper.

## Internal boundary

| Responsibility | Existing implementation |
|---|---|
| Parse grouped commands and coordinate the requested action | `control.py` |
| Create a Project or discover inputs/runtime | `onboarding.py`, `normalization.py` |
| Diagnose runtime, storage, and resource readiness | `doctor.py`, `resource_policy.py`, `execution_profile.py` |
| Build task commands, dependencies, and their recorded plan | `materialization.py`, `run_implementation.py` |
| Run Snakemake and record Attempt success, interruption, or failure | `lifecycle.py`, `task.py` |
| Read and validate Run state and identify supported recovery | `inspection.py`, `_inspection_evidence.py` |
| Present dated inspection evidence and a read-only terminal watch | `_inspection_presentation.py` |
| Start reporting after computation or on request | `reporting_operation.py`, `reporting_boundary.py` |
| Submit the same execution backend to one Slurm allocation | `slurm_submission.py` |

The runner owns native-output publication. Scientific algorithms and validation,
report rendering, and package installation stay with their existing owners.
Doctor binds the executing installed package and rechecks its full identity
before and after repair. Managed repair uses Pixi and renv for Project-owned
native tools and R libraries; Python installation stays with the environment's
package manager. A shared generation is never repaired in place: Doctor creates
a verified replacement, and dependent Projects explicitly move their current
selection while retained Attempts keep the old one. Existing site runtimes and
operator execution profiles remain outside managed repair. On a Slurm Project,
normal repair stays on the head node and submits the required runtime/storage
checks. `--compute` is the explicit advanced allocation route. Both
Project-creation commands accept `--site viking` and use the same built-in
placement; saved `EMRYS_SITE` supplies that choice when the flag is omitted.
Run, resume and standalone report execution follow the selected Project profile.
[Workflow composition](../../workflow/README.md) explains the graph;
[the profile contract](CONTRACT.md#profiles-and-immutable-planning) defines resource selection.

## Qualification evidence and limits

The [September 14 Viking walkthrough](https://github.com/lab-cats/EMRYS/blob/4348976f26c6d19dcc7786469f5873bdd8101750/docs/history/2026-09-14-viking-walkthrough.md)
combined operator-supplied output and source review; its raw site logs were
operator-held. Its selected revision was `7c427f0ca50de17bbcc9983571fa49acf167f187`, while the later campaign reviewed
`f2c0149e73a685b6f3d5b162f3804edee7c78c10`; neither identifies every installed
package, Run or Attempt. Manual setup job `614786` restored 71 R packages in 600 seconds;
the operator then reported successful head-node finalization for qualification
`cfcf7f788fd9d949f1a23f17793ecf22ba1e05f1023bc3b49065eebc0280186f`, retained
under `.emrys-storage-qualification/` in the `emrys-smoke` Project's parent.
That manual result does not qualify the later automated Doctor journey.
The operator had reported successful fresh installation and synthetic Project
validation before the first scientific Run. The [original approved slice](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/backlog_matrix.md#viking-walkthrough-findings)
allowed 750 net product lines, no new product files or receipt formats, and Rich;
that dated allowance is not a current grant. Product/tests/docs/configuration and
evidence accounting remain separate. Historical memory jobs and the E02/E10
observations live with [resource provenance](resources/README.md#resource-policy-provenance).

The first post-install qualification failure (E01) remains unexplained. After
the batch username correction, operator inspection reported a successful
synthetic resume, 151 artifacts and a 3:52 Attempt; the preceding startup failure
had retained a failed Attempt with recovery available and no completed scientific
milestones. HTML visual review was
explicitly deferred (E03/E04). Temporarily missing report receipts later
appeared without repair (E06); publication overlap and filesystem visibility
remain competing explanations. Current acceptance does not require reconstructing
E01/E06, and later success does not explain them.

The cancelled actual-data Run lacked terminal Attempt closure and remained
blocked; its replacement was still active at the last supplied observation
(E09/E12). Preserve that distinction rather than infer completion from scheduler
state. Active preparation blockers did not themselves prove failure (E05), and
manual inventory reuse was not proof of the later public sharing lifecycle
(E08). Onboarding costs, node-capacity observations and Doctor's reported
verification time over ten minutes did not attribute stage demand or latency
(E07/E10/E11). The September 16 report of a walkthrough approaching an hour also
lacked phase-resolved site measurements. These are historical evidence limits,
not a new site result or a Doctor speedup claim. E07 concerned a six-library,
three-pair study with 25 partitions, legacy-bundle inspection, a long creation
command and manual profile edit; several quiet admission minutes did not measure
hashing versus reference-check cost. The [frozen E01–E12 register](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/cluster_verification_campaign.md#evidence-register)
retains every original observation. The historical automated head-node Doctor
journey passed hosted disposable-Slurm [CI 34885186045](https://github.com/lab-cats/EMRYS/actions/runs/34885186045)
at `e25b10c6`; it was not Viking qualification or a production-profile requirement.
Remaining acceptance lives in the [cluster card groups](../../../../docs/tasks/backlog_matrix.md#cluster-card-dispositions).

Doctor's structural correction at `593f6e728321f535817bcde732d263c2f86079a8`
removed one intervening full head diagnosis: five total diagnoses became four,
while exact pre-storage readmission and final readiness remained. Source-recorded
[CI 35577392877](https://github.com/lab-cats/EMRYS/actions/runs/35577392877)
passed 14 standard jobs with four configured skips. Its fault fixtures used
simulated submission and the real storage owner; this is software protection,
not institutional timing. The [contract](CONTRACT.md#no-write-and-publication-boundaries)
retains binding-drift refusal and storage evidence after later Doctor failure.
No elapsed-time benefit was measured. Hosted measurement provenance and limits
live with the [CI owner](../../../../.github/workflows/README.md#doctor-namespace-experiment-disposition).

## Installed watch

`_inspection_presentation.py` owns the installed terminal interaction,
dated inspection/log projection, and fresh CLI action handoff. `dashboard.py`
owns scheduler-diagnostic selection, the full-history stream cache, parsing,
the overview/detail view model, and its renderer. `inspection.py` remains the
Run status and recovery authority; diagnostic text never replaces it.

The [Runbook watch procedure](../../../../docs/operations/RUNBOOK.md#watch-one-fixed-selection)
owns selectors, keys, refresh, offline use, and action previews;
[CONTRACT](CONTRACT.md#resume-inspection-results-and-reporting) owns selection,
evidence, completion, and recovery semantics. Historical scheduler names and
paths remain readable; the retired standalone dashboard is not a second owner.
