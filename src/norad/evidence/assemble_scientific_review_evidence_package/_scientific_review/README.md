# Scientific-review internals

This private package decomposes the Step `09c` implementation behind
[`step_09c_scientific_validation.py`](../step_09c_scientific_validation.py).
The public script remains the shared CLI and compatibility facade.

The modules retain explicit owner-local responsibilities: neutral-contract
identity; intake models and support; review-plan validation; evidence-manifest
validation; scientific audit checks; sensitivity and candidate review;
computational evidence and state assembly; and explicit context construction.
`intake.py` remains the internal compatibility facade used by its siblings.
`review_analysis.py` likewise preserves its sibling-import surface over
separate sensitivity/leave-one-pair-out, candidate selection/adjudication, and
decision/limitation owners.
These modules do not form a generic stage framework or a public library.

Locking, staging, final rereads, stable-input checks, summary-last publication,
rollback, and recovery remain in the facade. The facade imports this package
through its normal `norad.evidence` identity, including when the public CLI
bootstraps the repository `src` root.
