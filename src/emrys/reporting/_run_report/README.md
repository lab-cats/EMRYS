# HTML-report implementation

This private package publishes the fixed report bundle through
[`context.prepare_context`](context.py) and
[`publication.publish_report`](publication.py). The Run reporting coordinator
calls it; it provides no separate command or operator recovery interface.

| Module | Responsibility |
| --- | --- |
| [`models.py`](models.py) | Immutable contract, provider, output, and two-view context values. |
| [`inputs.py`](inputs.py) | Validate the run summary and installed provider; retain stable snapshots. |
| [`context.py`](context.py) | Prepare roots, provider, outputs, history, portable links, and renderer. |
| [`view.py`](view.py) | Build the evidence view and combine it with the provider's scientific view. |
| [`validation.py`](validation.py) | Configure strict, autoescaped Jinja; validate CSS, HTML safety, meaning, and accessibility. |
| [`receipt.py`](receipt.py) | Build the deterministic summary TSV and validate v4/v5 report receipts. |
| [`publication.py`](publication.py) | Publish both HTML files and TSV with the receipt last. |
| [`transaction.py`](transaction.py) | Handle locks, snapshots, durable writes, staging, rollback, and recovery. |

The selected `emrys.analysis_reporters` provider interprets scientific inputs
and builds its view. The [built-in paired-CMH provider](../paired_cmh_candidate_ranking_report/README.md)
owns candidate display, context, and figures. Core reporting owns evidence and
operations, navigation, HTML safety, fixed output names, and publication.
[Report-output rules](../README.md#report-outputs) define schema versions and
provider provenance separately from Analysis/Run identity.

`context.prepare_context` validates explicit source and artifact roots before
report inputs, preserving the former `report.py` error order and identities.
The logical producer remains `emrys.reporting.report`. The shared
[root rules](../README.md#source-and-artifact-roots) and
[publication/recovery contract](../README.md#publication-and-recovery) apply;
preparation still reads current and historical outputs. Rendering neither reruns
analysis nor changes scientific evidence.
