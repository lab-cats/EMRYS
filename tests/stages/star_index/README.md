# STAR-index stage tests

This directory protects the Step 00a direct producer and explicit validator.
Producer tests cover dry-run,
arbitrary-CWD execution, declared-member publication, no-clobber behavior,
controlled rollback, and late-final/foreign-lock preservation.
The [stage owner](../../../src/emrys/stages/star_index/README.md) owns
the exact direct command, materialized inputs, recovery boundary, and evidence
limit. Whole-Run Slurm placement is protected with orchestration, not here.

Mocked producer and fixture validation do not establish real STAR indexing,
Slurm execution, cluster execution, or production reference readiness.
