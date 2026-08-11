# Scientific-review internals

This private package decomposes the Step `09c` implementation behind
[`publisher.py`](../publisher.py). The grouped
`python -I -m norad assemble scientific-review-package` command and repository
shell launcher are the public routes; the publisher and these modules are not
additional public APIs.

The modules retain explicit owner-local responsibilities: neutral-contract
identity; cohesive intake models and shared helpers in [`intake.py`](intake.py);
specialized review-plan and evidence-manifest validation; scientific audit
checks; sensitivity and candidate review; computational evidence and state
assembly; and explicit context construction.
The public script and evidence assembly import the separate
sensitivity/leave-one-pair-out, candidate selection/adjudication, and
decision/limitation owners directly.
These modules do not form a generic stage framework or a public library.

Locking, staging, final rereads, stable-input checks, summary-last publication,
rollback, and recovery remain in the publisher. The publisher imports this
package through its normal `norad.evidence` identity.
