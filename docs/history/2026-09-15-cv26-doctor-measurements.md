# CV-26 Doctor measurements and decisions — 2026-09-15

This additive record transfers the September 15 hosted measurements and
decisions from [CV-26](../tasks/cluster_verification_backlog.md#cv-26-repeated-doctor-input-reads).
It was compiled against audit baseline
`3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`. The source card remains in
place. These are hosted, instrumented observations and a bounded design
decision, not a new benchmark, Viking measurement, or completed optimization.

| Source contribution | Immutable recording commit (Eastern) |
| --- | --- |
| First managed Doctor timing and fresh-check decision | `513cbd211718437191fcc460fc8b723de952f7fe` · September 15 02:38 |
| Passing-probe attribution | `b6ff0f6f95919ec67933474e0e75ebd9bc28b717` · September 15 03:40 |
| Donor/borrower invocation counters | `26f93f420deaedbcbc411b3c07412007921d34c3` · September 15 04:27 |
| Four-trial experiment and serial-probe decision | `13cd68750e4223431a594478804795905bfe9154` · September 15 13:03 |

The original [E11 report](2026-09-14-viking-walkthrough.md#e11-doctor-latency)
described a verification-only Doctor operation exceeding ten minutes, without
complete phase, read/hash, probe, queue or before/after attribution. CV-26's
original acceptance remains complete-operation attribution and comparable
measurements with no invented speedup target. The trials below cannot by
themselves close it.

## First retained setup observation

At product `2e03177747e67e8d970083e3994f3c8970d77caf`, the managed golden
path in [run 34935510824](https://github.com/lab-cats/EMRYS/actions/runs/34935510824),
artifact `emrys-managed-golden-1` ID `10382984827`, retained one complete
direct Doctor repair invocation of **175.681 seconds**:

| Phase | Seconds |
| --- | ---: |
| Initial Project/runtime inspection | 1.727 |
| Approved-input revalidation | 0.100 |
| Single-host storage qualification | 0.068 |
| Native tools and R preparation | 43.478 |
| R package restore/check | 20.146 |
| Installed-runtime discovery and verification | 55.091 |
| Final Project readiness | 54.907 |

Unrounded phases sum to 175.517 seconds, leaving 0.164 seconds outside the
named phases. Discovery and final readiness account for 62.61% of invocation
time. The source also records 71 R packages linked from cache. This was one
hosted direct managed setup, not a cold setup, borrower steady state, Slurm or
NFS run, E11 attribution, or optimization comparison.

The September 15 source decision retained fresh content checks and deferred
an invocation-local digest cache. A fixed-roster fixture had 14 executable/jar
hashes for 11 distinct files. Avoiding three reads would still require
current path, descriptor and content identity at each use; repair,
qualification and final revalidation protect different mutation boundaries.
No complete hash-byte, CPU, physical-I/O or RSS attribution came from that
fixture.

## Probe and invocation attribution

The managed golden job at product `1f4171d198cada8833f59ccd5a1bfeffab3ebaff`
in [run 34939155081](https://github.com/lab-cats/EMRYS/actions/runs/34939155081),
job `104283598944`, completed donor setup and borrower verification. Artifact
`emrys-managed-golden-1`, ID `10385365580`, was 6,756,172 bytes and its
downloaded SHA-256 matched
`df47f8cbc74141df8395c3efd87c6c9d14572a21ad080e6ae2a045e719151685`.
The overall workflow failed separate display-fixture assertions. This is
successful managed-job evidence, **not** a whole-suite success.

| Invocation / phase | Phase seconds | Timed probes | R namespace loads | Snakemake version + startup |
| --- | ---: | ---: | ---: | ---: |
| Donor discovery | 46.968 | 46.861 | 37.810 | 7.038 |
| Donor final readiness | 47.024 | 46.745 | 38.687 | 6.282 |
| Borrower diagnosis | 53.111 | 51.580 | 42.227 | 7.241 |
| Borrower final readiness | 51.887 | 51.623 | 42.159 | 7.331 |

Each qualification pass retained 26 passing observations and 24 timed child
calls; three path checks lacked a child timer. The rounded probe sums were
97.12–99.77% of their enclosing phases. Donor invocation took 140.458590
seconds, including 44.889825 seconds in package-manager phases; borrower
verification took 105.179918 seconds and had no package-manager events.
These were different workloads, not before/after optimization measurements.
Probe values had millisecond precision; deferred JSONL timestamps date their
emission, not a fresh check. The instrumented public-module scope included
imports and observer overhead rather than identical console-bootstrap timing.

[CI 34944690812](https://github.com/lab-cats/EMRYS/actions/runs/34944690812)
then passed 14 standard jobs with four configured skips at PR head
`0c2759d7479ea4a33c365f5beb3bd6d48c0f7519`. Managed job `104301191364`
uploaded artifact `emrys-managed-golden-1`, ID `10387257383`, 6,825,885 bytes;
its downloaded SHA-256 matched
`1ee51845e853ef983022b639b996d51cad8ec8b7beb46b1c3d382b8e521b7e44`.
Both records identify actual checkout
`20897a7cb8e4b2549e4a456142af2c971744bcb7`, with verified parents base
`cea7b60f1dd4164c8f8e61266f73bccbb2024caa` and that PR head. Both
controlled public invocations exited zero under Python 3.14.7.

| Measurement | Donor setup | Borrower verification |
| --- | ---: | ---: |
| Invocation wall seconds | 168.319256 | 110.727837 |
| Self CPU seconds | 4.209327 | 4.138431 |
| Waited-child CPU seconds | 205.620768 | 121.208439 |
| Self RSS high-water, KiB | 128,464 | 132,116 |
| Largest waited-child RSS high-water, KiB | 1,176,504 | 1,176,296 |
| Selected-owner completed bytes / calls | 237,833,169 / 2,330 | 457,049,108 / 2,779 |
| Selected-owner read seconds | 0.174186 | 0.254114 |
| Kernel `rchar` delta, bytes | 1,851,383,535 | 1,691,378,756 |
| Kernel `read_bytes` delta | 49,762,304 | 0 |
| Kernel `write_bytes` delta | 3,853,074,432 | 397,312 |

All selected-owner calls succeeded; their timed reads were 0.10% and 0.23%
of invocation wall time. They exclude package hashing and other Python,
semantic/gzip, Pixi and child/native reads. Kernel `rchar` includes pipes and
cached reads, while `read_bytes` is block-backed accounting rather than
measured device or NFS traffic. Self and waited-child RSS are distinct
high-water values, never additive. The donor and borrower were different
workloads, with uncontrolled cache and host state; neither physical-I/O
absence nor a speedup follows.

## Four steady-ready trials and selected decision

The selected [run 34995028343](https://github.com/lab-cats/EMRYS/actions/runs/34995028343)
passed at exact checkout `45bd9cd2b7b5dc98046aa7df862200b1b674c99d`.
[Artifact 10407268954](https://github.com/lab-cats/EMRYS/actions/runs/34995028343/artifacts/10407268954)
held all four complete diagnoses, logs and comparison records; its 9,209,702
bytes had SHA-256
`241fc3e4308b800f0c6f09c30238bb80560b20325c8709573c8c2e1e31d6d9e7`.
Every invocation exited zero with the same 26 ordered passing observations
and ten independent R namespace checks. Each made one fresh admission and
preserved borrower bytes/stable metadata and donor comparisons. Both
two-worker trials observed two
active R children and ten launches; serial launch counters were not instrumented.

| Trial | R workers | Diagnosis seconds | Self CPU seconds | Waited-child CPU seconds | Sampled process-tree peak MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | 57.403428 | 7.612158 | 60.836692 | 1201.17 |
| 2 | 2 | 41.068635 | 6.975059 | 61.601436 | 1626.86 |
| 3 | 2 | 41.998423 | 7.063463 | 62.389509 | 1641.50 |
| 4 | 1 | 57.486943 | 7.482891 | 60.859327 | 1207.46 |

Two-worker mean diagnosis was 41.533529 seconds versus 57.445185 serial,
15.911656 seconds or 27.70% lower in this hosted steady-ready workload.
Mean sampled process-tree peaks rose 429.86 MiB or 35.69%; combined measured
CPU rose 0.91%. Each invocation completed 1,227 selected-owner reads totaling
227,044,786 logical bytes in 0.150–0.160 seconds. `read_bytes` stayed zero,
which is no proof of absent physical/NFS reads. Samples may double-count
shared pages or miss peaks. These trials did not measure setup, a two-boundary
repair, queue time, Viking operation, or overall scientific performance.

The selected decision was to **retain serial R namespace checks**. A valid
profile can select one CPU and bounded memory; Doctor diagnosis has no admitted
concurrency budget before resource resolution. Unconditional parallel loading
would overcommit that supported profile and raised measured memory here.
Production interruption would also need a maintained concurrent-child owner.
The small measured read-time fraction did not justify cached admission or
weaker fresh checks. Temporary trial machinery was retired.
Canonical donor/borrower counters and native-containment checks remained.

The original and follow-up automatic PR suites had prototype-only fixture
failures (immediate SIGKILL observation, then a 0.2-second startup timeout).
They are not passing evidence. The independently selected experiment passed
its 600-second bound; retirement head
`13cd68750e4223431a594478804795905bfe9154` passed all 14 standard jobs,
with four configured skips, in
[CI 34998873917](https://github.com/lab-cats/EMRYS/actions/runs/34998873917).

The September 16 negative Viking duration report and September 21 structural
five-to-four-diagnosis reduction have later, separate dates in the current
CV-26 card. Neither changes the September 15 measurement limits. CV-26
remains Open for complete-operation phase, read/hash, probe and queue
attribution, comparable before/after measurements and institutional E11
timing. No measured whole-operation or Viking speedup is claimed here.
