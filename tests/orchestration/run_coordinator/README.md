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

## Containment and retry evidence

These retained September 15, 2026 software observations are tied to the exact
revisions below, not the current checkout or institutional cancellation.
The [Task and Attempt contract](../../../src/emrys/orchestration/run_coordinator/CONTRACT.md#task-and-attempt-lifecycle)
owns descendant closure, immutable retry references and current retry admission.

| Source-bound result | Exact identity and retained limit |
| --- | --- |
| Native descendant containment | [CI 34993805649](https://github.com/lab-cats/EMRYS/actions/runs/34993805649) passed 32 selected cases, including 17 Linux/native cases, with 14 standard jobs passing and four configured skips. The native job tested merge `f28a829ca894674f4e17d9e6f4bf618b7296ea1e`, containing product head `21992c732b44392cfe63528633a0e147b7979f85` and base `94a13fbea639d769fb22b1e443ccdb78b536fdd7`. [Artifact 10407865575](https://github.com/lab-cats/EMRYS/actions/runs/34993805649/artifacts/10407865575) has SHA-256 `8e53347a597b2f6b081e9c965ab5259d6621674d2e1af3009a44ae0d1151bb3a`. |
| Public cancellation and retry checkpoint | Product `79d45fb8a974d34572aca5da1ec22a4e4cdbac74` passed its real-Snakemake cancellation, read-only preview and distinct successful resume journey in 238.76 seconds at [CI job 104486782385](https://github.com/lab-cats/EMRYS/actions/runs/35000308100/job/104486782385). The overall run failed; its managed golden job passed 47 selected containment cases with zero skips, including ten abort-proof modes and four real samtools cases. Tested merge `3aa865b1c42d710f40b2a698045db2eed9438bcf` contained that head and base `13cd68750e4223431a594478804795905bfe9154`. [Artifact 10410455801](https://github.com/lab-cats/EMRYS/actions/runs/35000308100/artifacts/10410455801) has SHA-256 `a8b0e166cd0d1b5f1a898cd8abb32eb91b2b418582ea2342ed7926ba1fd0f258`. |
| Corrected complete-suite result | The first complete suite failed four older fixture assumptions about Task labels, retained origins and immutable resource policy. After corrections that kept the refusal predicates, final product head `a947b8fca04eb052c3829e897f255b046b002087` passed all 14 standard jobs, with four configured skips, in [CI 35002451860](https://github.com/lab-cats/EMRYS/actions/runs/35002451860). Its stronger public cancellation/resume journey passed in 282.22 seconds; all 47 native cases passed without skips. [Artifact 10411245477](https://github.com/lab-cats/EMRYS/actions/runs/35002451860/artifacts/10411245477) has SHA-256 `7f691245b22bf4b24cd479745b041adfdcc9d11b662f0455ff1ceebde6d16985`. |

Real `sort` cancellation deliberately stopped an observed native process before
escalation; both real cancellation output rosters were empty. Synthetic
cases retained partial bytes. Only the fully closed abort mode earned positive
closure; nine refused modes retained null closure. This is stopped-native
fixture evidence, not ordinary unpaused Viking cancellation. Lost workers,
preexisting services, remote delegation and ambiguous historical Tasks remain
outside that positive claim.

The [September 23 archive audit](../../../docs/tasks/docs-01-discoveries-seventh.md#retained-hosted-archive-inspection-at-496846d5)
checked the first two artifacts' bytes and selected logs; it did not inspect
artifact `10411245477`. Archive-reported checkout values do not independently
prove the worker checkout. Later timeout-warning and prepared-finalization
extensions have separate evidence. These results neither explain nor recover
the original E09 Run, and do not establish institutional cancellation/recovery.
[CV-10](../../../docs/tasks/cluster_verification_backlog.md#cv-10-external-cancellation-and-recovery)
retains the outstanding campaign acceptance; unclosed historical Runs remain untouched.
