# Scientific-review internals

This private package decomposes the Step `09c` implementation behind
[`step_09c_scientific_validation.py`](../step_09c_scientific_validation.py).
The public script remains the shared CLI and compatibility facade.

The modules retain explicit owner-local responsibilities: neutral-contract
identity, review intake and manifests, scientific audit checks, sensitivity
and candidate review, computational evidence and state assembly, and explicit
context construction. They do not form a generic stage framework or a public
library.

Locking, staging, final rereads, stable-input checks, summary-last publication,
rollback, and recovery remain in the facade. The facade imports this package
through its normal `norad.evidence` identity, including when the public CLI
bootstraps the repository `src` root.
