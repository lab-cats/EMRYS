# HTML-report implementation

This private package publishes the fixed report bundle through
[`context.prepare_context`](context.py) and
[`publication.publish_report`](publication.py). The Run reporting coordinator
calls it; it provides no separate command or operator recovery interface.

| Module | Responsibility |
| --- | --- |
| [`models.py`](models.py) | Immutable contract, provider, output, and two-view context values. |
| [`inputs.py`](inputs.py) | Resolve explicit file paths and retain stable input snapshots. |
| [`context.py`](context.py) | Prepare roots, provider, outputs, portable links, and renderer. |
| [`validation.py`](validation.py) | Render admitted values with strict, autoescaped Jinja; check exact projected bytes and the independent HTML, TSV and receipt contracts. |
| [`run_report.html.j2`](../templates/run_report.html.j2) | Own both built-in layouts and explanatory text, using summary and scientific values directly. |
| [`receipt.py`](receipt.py) | Project the fixed output bytes and receipt together; validate current receipts. |
| [`publication.py`](publication.py) | Publish both HTML files and TSV with the receipt last. |

Both reporting publishers use [`_files.py`](../_files.py) for exclusive durable
writes, lock ownership, and verified stage removal, and [`_signals.py`](../_signals.py)
for interruption handling. Report publication retains its own receipt order,
directory lifecycle, content-aware file snapshots, input and output rechecks,
rollback, and recovery decisions.

The selected `emrys.analysis_reporters` provider interprets scientific inputs
and returns the scientific HTML bytes. The [built-in paired-CMH provider](../paired_cmh_candidate_ranking_report/README.md)
owns candidate display, context, and figures. Core reporting owns evidence and
operations, navigation, HTML safety, fixed output names, and publication.
[Report-output rules](../README.md#report-outputs) define schema versions and
provider provenance separately from Analysis/Run identity.

`context.prepare_context` admits the installed package and artifact root before
report inputs. The exact package record accompanies report provenance and is
rechecked at publication boundaries.
The logical producer remains `emrys.reporting.report`. The shared
[root rules](../README.md#code-and-artifact-roots) and
[publication/recovery contract](../README.md#publication-and-recovery) apply;
preparation reads only current outputs. Rendering neither reruns
analysis nor changes scientific evidence.

Completed reports retain the renderer recorded in their v7 receipt. Reuse checks
that receipt against the immutable ledger, then checks every recorded data input,
output and HTML contract without rendering again. The receipt records additional
provider inputs, including figure sources; template and stylesheet identities
remain producer provenance. New publication still validates its exact prepared
bytes and records the actual installed EMRYS package.

HTML preparation requires the exact prepared evidence context from the preceding
manifest operation. It carries the checked Step 09/10 scientific projections into
the reporter. It cannot independently load a summary and reconstruct admission.
Retained-report inspection checks original receipt and data hashes separately.
