# Scientific-review internals

This private package decomposes the Step `09c` implementation behind
[`step_09c_scientific_validation.py`](../step_09c_scientific_validation.py).
The public script remains the exact-file CLI and compatibility facade.

The modules retain explicit owner-local responsibilities: neutral-contract
identity, review intake and manifests, scientific audit checks, sensitivity
and candidate review, computational evidence and state assembly, and explicit
context construction. They do not form a generic stage framework or a public
library.

Locking, staging, final rereads, stable-input checks, summary-last publication,
rollback, and recovery remain in the facade so the existing fault-injection
bindings stay live. The facade exact-loads this package under one validated
private identity without changing `sys.path`, including when callers load the
public script by exact file path.
