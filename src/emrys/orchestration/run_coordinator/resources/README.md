# Run-coordinator resource defaults

[`step_07_partitions.primary_contigs.tsv`](step_07_partitions.primary_contigs.tsv)
is the maintained EV/PUM1 whole-sequence selection used only after explicit
guided Init acceptance. The historical `configs/` path links to this same file
for explicit manifest use; the installed command reads its packaged copy.

[`default_execution.yaml`](default_execution.yaml) uses all allocated,
process-accessible workflow CPUs and RAM. Repeated stages fit automatic
concurrency and CPU/memory shares to the admitted workload, and supported native
tools receive the resolved task allowances. Recovered EV/PUM1 per-task memory
values are configurable minimums for repeated stages; fixed sample/partition
concurrency and tool-thread defaults are retired. Direct execution applies when
no placement override is selected; Viking initialization requests one whole node.
[Profile precedence](../CONTRACT.md#profiles-and-immutable-planning) determines
how Project settings and CLI values replace those defaults. Edit a Project's
profile to choose its resources; this packaged file is not a Project definition.

The original fixed 12-core policy entered Git in `92863824` as
`configs/local_pilot_resources.csu_viking_ev_pum1.yaml`, moved into the execution
profile in `d6e54aff`. Git retains that policy solely as provenance; it is not
the current default, a restoration target, or a required benchmark baseline.
The current
[`execution_profile.csu_viking_ev_pum1.yaml`](../../../../../configs/execution_profile.csu_viking_ev_pum1.yaml)
applies the authoritative allocation-aware workflow, memory, concurrency and
native-tool policy selected through CV-U06/CV-U28.
The [profile guide](../../../../../configs/README.md#profile-document) describes
every stage, automatic shares and the remaining serial phases. Stages 09 and 10
retain their later explicit one-thread declarations. Future tuning is independent
optimization work, not CV-U28 acceptance. Configuration capacity is not measured
utilization or speedup.
