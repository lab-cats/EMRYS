# Run-coordinator tests

These tests protect the public Project-to-Results journey and the coordinator's internal boundaries: onboarding, normalization, profiles and resources, Doctor, materialization, task execution, lifecycle and resume, Slurm submission, inspection, reporting, and the installed watch surface.

Test-owned fixtures and injected failures exercise production contracts without creating alternate production inputs or execution modes.

## What the checks establish

These are fixture boundaries, not a record of new execution or current CI results.

| Check | Capability and limit |
| --- | --- |
| [Submission usage](test_slurm_submission.py) | Argument-sensitive replies check selected-cluster terminal accounting and local-only live samples, including identical job numbers on different clusters. These in-memory transports establish query/identity behavior, not scheduler or institutional execution. |
| [Prepared-finalization substitution](test_lifecycle.py) | Equal-byte replacement uses a different inode. It does not prove continuity after inode recycling; the [trusted-workspace limitation](../../../src/emrys/orchestration/run_coordinator/CONTRACT.md#task-and-attempt-lifecycle) remains accepted. |
| [Public native cancellation](test_materialization.py) | Real backend and native-process behavior is exercised with substituted scientific effects, readiness and scheduler replies. It does not establish controller or institutional behavior. |
| [CI Slurm setup configuration](../../test_ci_workflow.py) | `test_ci_slurm_setup_is_guarded_real_and_diagnostic` asserts script text; it does not execute Slurm. The separately selected [real-Slurm journey](../../tools/README.md) requires its own exact-revision result and retained interruption/resume evidence. |
| [Reporting publication and inspection](test_materialization.py) | Actual report publishers and separate public readers exercise transaction boundaries with doubled scientific inputs. This is reporting-transaction evidence, not scientific validation. |
| [Input mutation](test_onboarding.py) | The same-size FASTQ test performs an actual rewrite, restores the modification time and lets production admission reject it. It is not a replacement validation rule. |
| [Runtime reuse](test_onboarding.py) | Tests call the supported production reuse API in [onboarding](../../../src/emrys/orchestration/run_coordinator/onboarding.py). Its existence and use do not establish institutional two-Project accessibility. |
| [Report transfer procedure](../../../docs/operations/RUNBOOK.md#retrieve-reports-from-a-terminal) | The retained tiny-directory copy/comparison check establishes command mechanics only. Generated-bundle portability, relative links, rendering and institutional transfer require separate evidence. |

The [test baseline](../../../docs/design/TEST_BASELINE.md) defines the shared
evidence vocabulary. Test reduction must preserve distinct production risks
and evidence levels rather than treating every fixture as equivalent proof.
