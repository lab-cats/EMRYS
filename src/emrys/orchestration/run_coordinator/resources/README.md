# Run-coordinator resource defaults

[`default_execution.yaml`](default_execution.yaml) uses all allocated,
process-accessible workflow CPUs and RAM, and gives STAR indexing the full
workflow allowance. Other stages retain the six-library EV/PUM1 thread,
concurrency and memory settings. Direct execution applies when no placement
override is selected; Viking initialization requests one whole node.
[Profile precedence](../CONTRACT.md#profiles-and-immutable-planning) determines
how Project settings and CLI values replace those defaults. Edit a Project's
profile to choose its resources; this packaged file is not a Project definition.

The original policy entered Git in `92863824` as
`configs/local_pilot_resources.csu_viking_ev_pum1.yaml`, moved into the execution
profile in `d6e54aff`. The current
[`execution_profile.csu_viking_ev_pum1.yaml`](../../../../../configs/execution_profile.csu_viking_ev_pum1.yaml)
now applies CV-U06's full-allocation workflow and STAR-index policy to those
historical stage settings. Git retains the original fixed 12-core policy.
Stages 09 and 10 retain their later explicit one-thread declarations.
The historical restoration addressed part of CV-U06/CV-U28; it did not satisfy
CV-U06's full-resource requirement. Allocation-based resolution now supplies
that capability. Configuration capacity is not measured utilization or speedup.
