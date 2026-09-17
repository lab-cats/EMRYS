# Run-coordinator resource defaults

[`default_execution.yaml`](default_execution.yaml) uses all allocated,
process-accessible workflow CPUs and RAM, and shares them across all stages according to admitted workload.
Recovered EV/PUM1 per-task memory values are configurable minimums for repeated
stages; fixed sample/partition concurrency and tool-thread defaults are retired. Direct execution applies when no placement
override is selected; Viking initialization requests one whole node.
[Profile precedence](../CONTRACT.md#profiles-and-immutable-planning) determines
how Project settings and CLI values replace those defaults. Edit a Project's
profile to choose its resources; this packaged file is not a Project definition.

The original policy entered Git in `92863824` as
`configs/local_pilot_resources.csu_viking_ev_pum1.yaml`, moved into the execution
profile in `d6e54aff`. The current
[`execution_profile.csu_viking_ev_pum1.yaml`](../../../../../configs/execution_profile.csu_viking_ev_pum1.yaml)
now applies CV-U06's allocation-aware workflow and stage sharing policy.
The [profile guide](../../../../../configs/README.md#profile-document) describes
every stage, automatic shares and the remaining serial phases. Git retains the original fixed 12-core policy.
Stages 09 and 10 retain their later explicit one-thread declarations.
The historical restoration addressed part of CV-U06/CV-U28; it did not satisfy
CV-U06's full-resource requirement. Allocation-based resolution now supplies
that capability. Configuration capacity is not measured utilization or speedup.
