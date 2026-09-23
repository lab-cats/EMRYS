# CV-26 Doctor follow-up — 2026-09-21

This additive record preserves later checkpoints from
[CV-26](../tasks/cluster_verification_backlog.md#cv-26-repeated-doctor-input-reads).
It follows the separate [September 15 hosted measurement
record](2026-09-15-cv26-doctor-measurements.md); neither record replaces the
source card. The facts below were recorded in immutable commits on the audit
lineage, reviewed against baseline
`3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`:

| Checkpoint | Recording commit (Eastern) |
| --- | --- |
| Negative Viking duration report | `3c97175517aa4c3565eec21f5c900c42ebd44976` · September 16 19:15 |
| Default elapsed/slowest-phase presentation | `769b2b4b5999e56265dbfe0affa35abe37f84b5c` · September 16 20:15 |
| Slurm Doctor structural reduction | `593f6e728321f535817bcde732d263c2f86079a8` · September 21 04:19 |
| Exact hosted result recorded in the card | `1ef2edc5132d8b24319c5d9d6efa16def343ca38` · September 21 04:39 |

## September 16 operator report and attribution display

The operator reported that Doctor repair still felt too long and the broader
setup/execution walkthrough approached a full hour. No phase-resolved Viking
timings or comparable cold/warm boundary accompanied that report. It is
negative operator acceptance, not attribution of the time to package work,
runtime probes, Slurm waiting, the optional synthetic exercise, or the real
Analysis. Making the synthetic exercise optional shortened the novice route;
it did not demonstrate a faster Doctor. Repeated preview/execute work in
`runtime discover` belongs to CV-08 and retains its mutation-boundary checks.

The later presentation change added a concise default `Doctor elapsed` field
with total time, including operator confirmation, slowest phase, and outcome;
`--verbose` kept all phase times.
It removed no admission check, fresh read, probe, or mutation-boundary
verification. This made attribution more visible without measuring an
optimization benefit.

## September 21 structural decision and limits

In a successful Slurm verification, the former full `head_requalification`
between exact installed-package/Project/profile readmission and head storage
finalization was removed. The storage owner needs its admitted Project paths,
compute receipt and probes, root identity, hashes, and durability state rather
than that repeated runtime diagnosis. The complete path moved from five full
diagnoses to four; the head-node share moved from four to three. Product code
was nine net lines smaller. These are structural counts, not measured elapsed
time, read volume, or a Viking speedup.

Pre-storage readmission still refuses Project, package, and execution-profile
drift before storage mutation. The storage owner retains corruption, interruption,
receipt, finalization, and durable-evidence defenses. One final full diagnosis
still verifies runtime, package, Project, and profile readiness before Doctor
records success. A valid compute or final storage receipt may survive a later
Doctor failure; a terminal `repair_requalified` record may not. The public
fault matrix covers final runtime, Project, package, inventory, and profile
drift, storage corruption, and interrupted
finalization through simulated submission and the real storage owner.

The source card reports 116 Doctor, 55 storage-qualification, and 85
runtime-owner local tests, including all 17 public Slurm Doctor scenarios;
13 documentation-structure checks, Ruff lint/format, and whitespace checks
also passed. Its exact implementation head
`593f6e728321f535817bcde732d263c2f86079a8` passed 14 standard jobs,
with four configured skips, in source-recorded
[CI 35577392877](https://github.com/lab-cats/EMRYS/actions/runs/35577392877).
This audit did not rerun those checks or independently inspect every hosted
artifact. Simulated and hosted software checks do not establish institutional
E11 timing, comparable complete-operation before/after measurements, or
scientific performance. The original CV-26 attribution and comparison
acceptance stays with the card.

After the hosted result, `1ef2edc5` briefly called the revised structural
slice Completed. The September 22 audit baseline `3a672fdf` restored CV-26
to Open against its original complete-operation attribution and comparable
measurement acceptance. That status belongs to the card and main matrix.
