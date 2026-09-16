# Run-coordinator resource defaults

[`default_execution.yaml`](default_execution.yaml) supplies the restored
six-library EV/PUM1 resource policy and direct execution when the Project
provides no overrides: 12 workflow cores, 524288 MiB (512 GiB), per-stage
memory allowances and concurrent sample/partition work.
[Profile precedence](../CONTRACT.md#profiles-and-immutable-planning) determines
how Project settings and CLI values replace those defaults. Edit a Project's
profile to choose its resources; this packaged file is not a Project definition.

The original policy entered Git in `92863824` as
`configs/local_pilot_resources.csu_viking_ev_pum1.yaml`, moved into the execution
profile in `d6e54aff`, and survives in
[`execution_profile.csu_viking_ev_pum1.yaml`](../../../../../configs/execution_profile.csu_viking_ev_pum1.yaml).
That retained profile is the historical reference for the packaged defaults.
Stages 09 and 10 retain their later explicit one-thread declarations.
The operator approved this historical policy as the default for CV-U06,
CV-U27 and CV-U28; restoration does not require another tuning exercise.
