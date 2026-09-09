# Run-summary implementation

This private package turns validated artifact records into a deterministic
computational summary. The Run reporting coordinator and developer fixtures
call [`builder.prepare_context`](builder.py), then [`publication.py`](publication.py).
There is no separate public command or operator recovery interface.

| Module | Responsibility |
| --- | --- |
| [`builder.py`](builder.py) | Prepare inputs and retain validated source/artifact roots. |
| [`models.py`](models.py) | Constants, headers, errors, snapshots, paths, and context values. |
| [`inputs.py`](inputs.py) | Check explicit paths and snapshot immutable files. |
| [`transaction.py`](transaction.py) | Read input transactions and history; provide stable value helpers. |
| [`projection.py`](projection.py) | Derive computational status, summary rows, and QC rows. |
| [`validation.py`](validation.py) | Validate documents, predecessors, and receipts. |
| [`document.py`](document.py) | Assemble the canonical run-summary document. |
| [`publication.py`](publication.py) | Publish receipt last; handle rollback, recovery, and output checks. |

Preparation and publication rechecks use the same validated artifact transaction.
Parsing, serialization, and shared transaction helpers come through the private
[`_artifact_index/api.py`](../_artifact_index/api.py), without invoking artifact
context preparation. Both roots remain on `BuildContext` under the common
[source/artifact rules](../README.md#source-and-artifact-roots); publication uses
them for input and output checks without inferring or validating new roots.

Document assembly uses the Analysis form: flat paired-CMH keeps run-summary v2;
explicit modules use v3, with analysis-policy path, SHA-256, and size rather than
paired-CMH fields. This changes neither predecessor nor transaction checks.
Preparation and read-only validation still accept supported history;
[publication](../README.md#publication-and-recovery) requires absent outputs.

The frozen `RunSummaryBuildDeps` supplies input loading, producer identity,
document construction, and the final input recheck. Production uses immutable
defaults; [tests](../../../../tests/reporting/README.md#fault-injection) provide
explicit replacements. Public [`transaction_validation`](../transaction_validation.py)
owns semantic input rechecks for preparation, publication, lifecycle, and inspection;
the private publisher exposes no second interface.

All three reporting transactions share artifact contracts and error identities.
The summary records computational state, not candidate review, adjudication,
biological interpretation, approver gates, or scientific completion.
