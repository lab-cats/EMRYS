# Run-coordinator resource defaults

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

The current
[`execution_profile.csu_viking_ev_pum1.yaml`](../../../../../configs/execution_profile.csu_viking_ev_pum1.yaml)
applies the authoritative allocation-aware workflow, memory, concurrency and
native-tool policy selected through CV-U06/CV-U28.
The [profile guide](../../../../../configs/README.md#profile-document) describes
every stage, automatic shares and the remaining serial phases. Stages 09 and 10
retain their later explicit one-thread declarations. Future tuning is independent
optimization work, not CV-U28 acceptance. Configuration capacity is not measured
utilization or speedup.

## Resource-policy provenance

These operator-supplied Viking observations are historical, not current site
qualification or measurements of stage demand. Their [frozen source](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/backlog_matrix.md#viking-walkthrough-findings)
and [E02/E10 register](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/cluster_verification_campaign.md#evidence-register)
retain context and limits; raw cluster records remained operator-held.

| Observation | Exact identity and evidence limit |
| --- | --- |
| Original accounting | Job `605171`: `viking-users`, `long`, `normal`, four CPUs/eight hours; `ReqMem=1M` without allocated-memory accounting. `select/cons_tres`, `CR_CORE`, unlimited default/maximum per-node memory and `task/cgroup` established no process memory limit. This is the Viking E02 observation, not a same-numbered NORAD result. |
| Capacity refusal and diagnosis | Observer `c52178d2` refused absent Slurm memory metadata for a partial-node allocation. Automated Doctor job `618134` passed runtime inspection then stopped there; diagnostic job `618190` on `node009` exposed four CPUs, neither memory variable and effectively unlimited visible cgroup-v1 limits. No scheduler values were forged or allocation enlarged to bypass admission. |
| Approved fallback | The operator accepted process-visible RAM without a separate workflow budget or full-node CPU requirement, retaining observed cgroup/declared scheduler limits, CPU constraints and source attribution. The correction followed Doctor diagnostics, not an evidenced actual Run. Reported Doctor READY left science pending and did not explain the earlier generic failure. |
| Heterogeneous capacity | E10 observed 128544 MiB total/111749 MiB then available on one node and a 386627-MiB workflow ceiling on another, against a 262144-MiB index allowance. A 256-CPU exclusive request waited with 16 CPUs occupied/240 idle while the workflow used 12 cores. Capacity/configuration is not measured demand or optimal placement; scheduler memory `1` was not physical RAM. |


The September 15, 2026 reconstruction, recorded in
`354699748cedd245df653d15410e04c59811f87c`, followed an operator report of an
eight-hour pipeline instead of the expected four hours and an instruction to
restore the recovered settings without requiring another benchmark first.
That report did not establish causality or a controlled performance comparison.
The recovered six-library Viking policy was distinct from benchmark per-case
budgets, older per-stage Slurm wrappers and the `f054ddee` VM trial.

The old policy entered Git at `92863824787dde5de46de9a87bfff123783e89c0`,
moved into the execution profile at `d6e54aff2f11e8ee4eb0fce266db8fd87725f6ed`,
and its old filename was retired at `5f42c8c46216dc05fbfb2909eae432106ccb50f3`.
Its complete stage values remain recoverable from this immutable Git object:

```sh
git show d6e54aff2f11e8ee4eb0fce266db8fd87725f6ed:configs/local_pilot_resources.csu_viking_ev_pum1.yaml
```

The exact file SHA-256 is
`dab4f20a63aaf36327b471d33b1efc134c6b1e60429f3d6bdf4529f9943f3202`.
It used 12 workflow cores and 524288 MiB, with 12 STAR-index threads and
262144 MiB; the associated 256-CPU allocation request was a separate quantity.
Its inactive reporting-memory map is not a working control.

The September 21 owner decision in `593f6e728321f535817bcde732d263c2f86079a8`
superseded the fixed workflow/memory ceilings and concurrency with the current
allocation-aware policy. Historical task minima remain current only where the
active profile declares them. Fixed-policy restoration and historical timing
comparison are no longer acceptance requirements. The old configuration is
provenance, not a current prescription, safe-RSS bound or speedup claim.
[CV-U28](../../../../../docs/tasks/backlog_matrix.md#resource-selection-and-observation)
retains exact-revision institutional Doctor/Run allocation acceptance; configuration
and historical timing alone do not establish that result or measured utilization.
