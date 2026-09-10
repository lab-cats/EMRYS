# Common workflow graph

[`local_cmh_v2.json`](local_cmh_v2.json) describes common owners through Step
`08`, their scopes and dependencies, and required evidence. Planning adds exactly
one validated Analysis module's typed inputs/outputs, Step `09`, and optional
Step `10`, then stores that complete canonical profile in the immutable Run.
Tasks, inspection, artifact indexing, and Snakemake read that same profile.

This base is not a complete Run or a module registry. Installed modules follow
the `emrys.analysis_modules` contract without editing this directory. Changing
the common graph requires explicit approval and checks of planning, stored Run
records, scheduling, task/inspection validation, and derived reporting inventory.

The [orchestration contract](../../contracts/orchestration/README.md)
defines schemas and serialization; [STAGE_MAP](../../contracts/STAGE_MAP.md)
defines scientific identities and dependencies. See the [workflow overview](../README.md)
for execution and profile selection.
