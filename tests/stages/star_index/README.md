# STAR-index stage tests

This directory protects the Step 00a scheduler-independent producer, legacy
scheduler delegation, and explicit validator. Producer tests cover dry-run,
arbitrary-CWD execution, declared-member publication, no-clobber behavior,
controlled rollback, and late-final/foreign-lock preservation.
The [stage owner](../../../src/norad/stages/star_index/README.md) owns
the exact local and submission commands, fixed wrapper inputs, recovery
boundary, and evidence limit.

Mocked-job and fixture validation do not establish real STAR indexing,
scheduler execution, cluster execution, or production reference readiness.
