# CV-U28 resource-policy provenance — 2026-09-15

This additive record transfers the September 15 reconstruction in
[CV-U28](../tasks/cluster_verification_backlog.md#cv-u28-allocation-aware-resource-policy-and-historical-provenance).
The source first recorded it in immutable commit
`354699748cedd245df653d15410e04c59811f87c` on September 15. This record
was compiled against audit baseline
`3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`; the original card remains
in place. It preserves why the old policy was restored at that checkpoint,
not a current resource prescription or a new performance measurement.

## Report and recovered source

The operator reported an **eight-hour pipeline instead of the expected four
hours** and attributed the change to historical per-stage configuration. This
was an operator report and restoration instruction, not a controlled before/
after benchmark or a proved causal attribution. The September 15 decision did
not require a new benchmark before restoring the recovered configuration.

The source review counted all 78 remote `perf` branch heads: 72 retained the
same EMRYS resource blob and six older NORAD heads retained the conservative
example. No tracked history was found for the unqualified
`configs/local_pilot_resources.yaml`. The desired Viking-specific policy was
introduced at `92863824787dde5de46de9a87bfff123783e89c0` on August 21 as
`configs/local_pilot_resources.csu_viking_ev_pum1.yaml`. Its computational
values moved into the execution profile at
`d6e54aff2f11e8ee4eb0fce266db8fd87725f6ed`; commit
`5f42c8c46216dc05fbfb2909eae432106ccb50f3` retired the old filename.
The last old-file content survives as the immutable Git object
`5f42c8c4^:configs/local_pilot_resources.csu_viking_ev_pum1.yaml`, with
SHA-256 `dab4f20a63aaf36327b471d33b1efc134c6b1e60429f3d6bdf4529f9943f3202`.

That fixed policy used 12 workflow cores, 524288 MiB workflow memory, 12
STAR-index threads and 262144 MiB STAR-index memory. The associated profile
requested 256 CPUs outside the workflow; requested allocation and workflow
ceiling were different quantities. The retired file's complete stage values
are below; a dash means that file declared no value for that stage/field, not
that execution had no limit.

| Stage | Concurrency | Threads | Memory MiB |
| --- | ---: | ---: | ---: |
| 00a | — | 12 | 262144 |
| 00b | — | — | 16384 |
| 00c | — | — | 16384 |
| 01 | 6 | 2 | 40960 |
| 02 | 6 | 1 | 4096 |
| 02b | 6 | — | 2048 |
| 03 | 6 | — | 4096 |
| 04 | 4 | — | 32768 |
| 05 | 6 | — | 16384 |
| 06 | 6 | 1 | 4096 |
| 07 | 12 | — | 8192 |
| 08 | — | 4 | 65536 |
| 09 | — | — | 16384 |
| 10 | — | — | 32768 |

The retired `reporting_memory_mb` map declared `artifact_index: 8192`,
`run_summary: 16384` and `html_report: 16384`; it was inactive and was not
reintroduced as a working control.

The 46 `perf` branches that carried the benchmark harness held 11 harness
versions. Their per-case budgets were a separate measurement scope, not an
alternative whole-Run policy. Older per-stage Slurm wrappers and the VM trial
at `f054ddee` were also distinct execution contexts. The September 15
restoration used the six-library Viking provenance rather than combining
these contexts. It changed packaged defaults at that checkpoint; the old
Viking file and later selected execution profile are separate artifacts.

## Later policy boundary

The September 16 allocation-aware source changes and September 21 owner
decision, recorded in `593f6e728321f535817bcde732d263c2f86079a8`,
superseded the fixed workflow/memory ceilings and concurrency and introduced
allocation-aware shares. The current card and
[profile](../../configs/execution_profile.csu_viking_ev_pum1.yaml) own that
behavior. Some historical Stage 01–07 memory values survive as current
configurable minima where the active profile declares them. The old fixed
ceilings and eight/four-hour report remain provenance, not a current default
or a speedup claim. Exact institutional Doctor and Run
allocation acceptance remains pending; no comparable whole-operation timing,
safe-RSS conclusion or utilization proof follows from this reconstruction.
