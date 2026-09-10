# Run coordinator

This package turns a validated Project and selected Analysis into a Run plan,
executes that plan, and reports its state. Operators use the grouped `emrys`
commands; these modules are private implementation details.

## Ordinary journey

Use the [quickstart](../../../../quickstart.md) for a first Run and the
[Runbook](../../../../docs/operations/RUNBOOK.md) for later operation and Slurm.
[The contract](CONTRACT.md) defines command confirmation, immutable records,
inspection, historical compatibility, and recovery. It is the authoritative
home for those rules; this README explains how the implementation fits together.

## Specialized setup and reuse

The [configuration guide](../../../../configs/README.md) explains manifests and
Analysis fields. The [runtime procedure](../../../../docs/operations/RUNBOOK.md#institution-provided-runtime)
explains discovery and managed/site setup. The [reuse procedure](../../../../docs/operations/RUNBOOK.md#reusable-processing)
explains how a new downstream Run uses a compatible processing Run without
changing it. Synthetic dataset choices belong in the [quickstart](../../../../quickstart.md).

## Internal boundary

| Responsibility | Existing implementation |
|---|---|
| Parse grouped commands and coordinate the requested action | `control.py` |
| Create a Project or discover inputs/runtime | `onboarding.py`, `normalization.py` |
| Diagnose runtime, storage, and resource readiness | `doctor.py`, `resource_policy.py`, `execution_profile.py` |
| Build task commands, dependencies, and their recorded plan | `materialization.py`, `run_implementation.py` |
| Run Snakemake and record Attempt success, interruption, or failure | `lifecycle.py`, `task.py` |
| Read and validate Run state and identify supported recovery | `inspection.py`, `_inspection_evidence.py` |
| Start reporting after computation or on request | `reporting_operation.py`, `reporting_boundary.py` |
| Submit the same execution backend to one Slurm allocation | `slurm_submission.py` |

Scientific algorithms, native-output publication, scientific validation,
report rendering, and package installation remain with their respective owners.
The coordinator calls them; it does not reproduce their implementation.
Doctor binds the executing installed package and rechecks its full identity
before and after repair. Managed repair uses Pixi and renv for Project-owned
native tools and R libraries; Python installation stays with the environment's
package manager. Existing site runtimes and operator execution profiles remain
outside managed repair.
[Workflow composition](../../workflow/README.md) explains the graph;
[the profile contract](CONTRACT.md#profiles-and-immutable-planning) defines resource selection.

The old CSU-oriented `dashboard.py` preview is frozen. It remains until a
replacement is implemented and validated under `DASHBOARD-RETIRE-01`;
`emrys inspect` is the authority for Run status and recovery.
