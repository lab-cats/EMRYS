# GitHub Actions workflows

[`ci.yml`](ci.yml) runs ordinary checks on pull requests. Scheduled and manually
selected lanes add longer synthetic and scheduler checks. The
[test baseline](../../docs/design/TEST_BASELINE.md#validation-lanes) defines each
lane; a green workflow supports only the claims covered by those checks.

The managed golden path also exercises Task descendant cleanup with the
samtools already selected by its synthetic Project. It requires that executable
before running the Linux process fixtures and canonical BAM checks. The job
retains their JUnit results and tiny native outputs beside its existing evidence.
This covers the hosted worker boundary; it does not establish Slurm cancellation,
lost-worker reconciliation or safe postentry retry.

The 130-pair real-synthetic lane is three independent matrix jobs:
clean direct/Slurm parity, controlled failure/resume parity, and fresh active
Slurm stop/resume. They run in parallel when capacity permits, with fail-fast
disabled and separate controller, worker, accounting database, workspace, and
evidence roots. The 100,000-pair production-like Slurm scenario remains a
separate weekly or manually selected job. One prerequisite job prepares the
lock-derived uv, Pixi, and renv dependencies for the exact `ubuntu-26.04`
runtime. Scenario jobs start only after that preparation, restore the same
image-namespaced caches without writing them, and fail rather than rebuilding a
missing R cache. A full prepared runner cannot be shared safely: GitHub-hosted
jobs receive fresh virtual machines, while reusing one runner would couple the
mutable Slurm controller, worker, accounting database, and whole-node jobs.

Every job configures a disposable single-runner Slurm service with matching
supported binaries. Setup must prove versions, readiness, cluster registration,
and exact `squeue --clusters=emrys-ci` observation before its scenario starts.
The CI-only controller allows the Task cleanup signal horizon before forced
termination and retains controller and worker file logs; this does not weaken
the resume boundary or change production Slurm policy. Stop/resume alone limits
workflow scheduling to one core so the gated native Task has no unrelated active
Task whose closure could be ambiguous; it retains whole-node exclusive Slurm
placement. The other scenarios retain allocation-wide workflow parallelism.
Private service state stays on that runner; the scenario artifact contains only
bounded operator, runtime, setup, and terminal evidence. Infrastructure
readiness alone is not proof that an active Task was cancelled or that
cross-node Viking behavior works.

## Retained integration evidence

`PORT-NC-01` candidate `ebc43b4a8342b676eafb6b56492989498886ab55` passed
assembled local static, installed-wheel, guarded-R, shell/Slurm-wrapper and
Python behavior/coverage checks. Source-branch tests informed its differently
implemented no-clobber replay; they did not validate the integrated candidate.
The replay admitted STAR metadata rows, used the converter transaction for
Step 00b, bound repository-owned wrappers to the submitted checkout, and made
staged no-clobber Step 01 the scheduled default while retaining stronger
transaction and runtime authority. This was local integration evidence: no
Slurm submission, distributed filesystem, fresh-clone or full-Run proof, or
real production scientific-tool/data execution. The [original local record](https://github.com/lab-cats/EMRYS/blob/8901c61ac87d7aebe2599cfc80adc1b501ad4ce5/docs/history/testing/2026-08-14-port-nc-01-no-clobber-replay.md)
retains the exact source-branch identity, gate timings and exclusions.

The architecture closeout retained these bounded hosted results:

| Scope | Exact revision and retained runs | Evidence ceiling |
| --- | --- | --- |
| `ARCH-CLOSE-01` | `f85379edef0440266c1e97e97be5324e364812cb`; [ordinary 33630887395](https://github.com/lab-cats/EMRYS/actions/runs/33630887395), [selected 33630899403](https://github.com/lab-cats/EMRYS/actions/runs/33630899403) | Managed real-tool direct journey, Rocky/Ubuntu/Debian lock installation, Python 3.11 shards and 130-pair direct/disposable-Slurm success. The 100,000-pair lane was not selected. |
| `ARCH-CLOSE-02` | `4a165038b3d164d6ace59b9e9bb21add086d07df`; [ordinary 33640599154](https://github.com/lab-cats/EMRYS/actions/runs/33640599154), [CodeQL 33640595166](https://github.com/lab-cats/EMRYS/actions/runs/33640595166), [selected 33640622974](https://github.com/lab-cats/EMRYS/actions/runs/33640622974) | Python 3.11 shards and 130-pair direct/disposable-Slurm controlled failure/resume, provenance, Results and logging parity. The 100,000-pair lane was not selected. |
| `ARCH-CLOSE-03` | `f3622f791e90fd6ed15079abcbcbe9b7003cbb6a`; [ordinary 33653717181](https://github.com/lab-cats/EMRYS/actions/runs/33653717181), [CodeQL 33653716112](https://github.com/lab-cats/EMRYS/actions/runs/33653716112) | Role, ownership, baseline, closeout and ordinary/static-security checks; long lanes were not selected. |

These exact-revision records are not institutional-site, multi-node,
production-data, scientific-review or biological proof. Transferring the records
does not rerun their checks or extend their scope to the current source.

## Doctor namespace experiment disposition

The temporary two-worker R namespace comparison is retired; product probes
remain serial. [Run 34995028343](https://github.com/lab-cats/EMRYS/actions/runs/34995028343)
at `45bd9cd2b7b5dc98046aa7df862200b1b674c99d` retained four valid, fresh,
read-only diagnoses of one qualified borrower in serial/two/two/serial order.
Mean wall time was 57.45/41.53 seconds and sampled root-plus-descendant RSS
1204.32/1634.18 MiB for serial/two workers. All 26 ordered observations, ten
namespace checks and owner reads matched; borrower stable bytes/metadata and
donor comparisons were preserved. Serial launch counters were not instrumented.
RSS sums can count shared pages repeatedly and miss peaks; host/cache state was
uncontrolled. This does not measure setup, repair or site performance.

[Artifact 10407268954](https://github.com/lab-cats/EMRYS/actions/runs/34995028343/artifacts/10407268954),
`emrys-managed-golden-1`, retained the four diagnoses, logs and comparisons:
9,209,702 bytes, downloaded SHA-256
`241fc3e4308b800f0c6f09c30238bb80560b20325c8709573c8c2e1e31d6d9e7`.
Higher memory demand and unproven caller-complete resource/cancellation ownership
did not justify product adoption. Earlier automatic prototype suites failed
SIGKILL-observation and 0.2-second startup fixtures; the separately selected
experiment passed its 600-second bound. Retirement head
`13cd68750e4223431a594478804795905bfe9154` passed 14 standard jobs with four
configured skips in [CI 34998873917](https://github.com/lab-cats/EMRYS/actions/runs/34998873917).
Retirement removed temporary scheduling/sampling/comparison machinery and its
fixtures; the donor/borrower measurement driver and native-containment checks
remain. Failed prototype suites are not passing evidence.

Earlier hosted Doctor observations retain distinct scopes:

| Observation | Exact source and retained artifact | Scope and limit |
| --- | --- | --- |
| Managed repair | `2e03177747e67e8d970083e3994f3c8970d77caf`; [run 34935510824](https://github.com/lab-cats/EMRYS/actions/runs/34935510824), artifact `10382984827` | One direct repair took 175.681 seconds with 71 packages linked from cache; discovery/final readiness accounted for 62.61%. No complete hash-byte, CPU, I/O or RSS attribution; not cold setup, borrower steady state, Slurm/NFS or optimization evidence. |
| Probe attribution | `1f4171d198cada8833f59ccd5a1bfeffab3ebaff`; [run 34939155081](https://github.com/lab-cats/EMRYS/actions/runs/34939155081), job `104283598944`, artifact `10385365580`; 6,756,172 bytes, SHA-256 `df47f8cbc74141df8395c3efd87c6c9d14572a21ad080e6ae2a045e719151685` | Donor/borrower probes accounted for 97.12–99.77% of their enclosing phases. The managed job succeeded; the workflow failed separate display fixtures. Different workloads, not before/after measurements. |
| Invocation counters | Archive-reported checkout `20897a7cb8e4b2549e4a456142af2c971744bcb7`, PR head `0c2759d7479ea4a33c365f5beb3bd6d48c0f7519`; [run 34944690812](https://github.com/lab-cats/EMRYS/actions/runs/34944690812), job `104301191364`, artifact `10387257383`; 6,825,885 bytes, SHA-256 `1ee51845e853ef983022b639b996d51cad8ec8b7beb46b1c3d382b8e521b7e44` | 14 standard jobs passed with four configured skips; donor/borrower invocations exited zero under Python 3.14.7. Timed selected-owner reads were 0.10%/0.23% of invocation wall time, with the exclusions below. |

The workflow's measurement driver observes one public-module invocation,
including imports and observer overhead, not identical console-bootstrap timing.
Completed logical owner bytes exclude other Python, semantic/gzip, Pixi and
child/native reads; failed partial bytes are unknown. Package-payload read time
excludes subsequent hashing. `rchar` includes pipes/cache; `read_bytes` is
block-backed accounting, not measured physical-device or NFS traffic. Self and
largest waited-child RSS are separate high-water values, never added or
subtracted. Totals do not attribute individual probe CPU, memory or I/O.
Passing-probe JSONL timestamps date deferred emission, not new observations.
Uncontrolled host/cache state and different donor/borrower work prevent speedup
or physical-I/O-absence claims; none of these hosted records explains Viking E11.
Archive hashes and outcomes above are retained observations, not a new download
or present availability check. Archive-reported checkout values are not
independent proof of the worker checkout. Full numerical tables remain discoverable in the
[frozen measurement record](https://github.com/lab-cats/EMRYS/blob/4348976f26c6d19dcc7786469f5873bdd8101750/docs/history/2026-09-15-cv26-doctor-measurements.md).
