# CV-UX-01 Doctor terminal collision — 2026-09-16

This additive record preserves the September 16 operator report from
[CV-UX-01](../tasks/cluster_verification_backlog.md#cv-ux-01-doctor-live-progress-output-collision),
entered in immutable commit `3c97175517aa4c3565eec21f5c900c42ebd44976`.
The collision-specific software response is commit
`b611890f016f92debabaac4e64550dd73669bca2`. A later integrated card
checkpoint, `d249fc5e23514f42c5a0139506be89b264e80fd6`, is not a separate
collision fix. This record was compiled
against audit baseline `3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`;
the source card remains in place.

## Operator observation and limit

During `emrys doctor --repair` on Viking, the live
`Slurm submission-to-return wait 0:00:00` phase and the next
`Slurm submission records:` diagnostic occupied the same terminal row,
producing `0:00:00Slurm submission...` without a separating line boundary.
The captured output then named retained submission stdout/stderr paths and
Slurm job `621172`. The source refers to a screenshot but gives no retained
screenshot path or hash. This supports an operator-reported presentation
collision; it does not establish record loss, incorrect job identity, or a
scheduler failure.

At that checkpoint CV-U04 returned to Open for the broader Doctor presentation
acceptance. The operator's separate report that Doctor repair took too long
belongs to CV-26's measured phase attribution. Shorter output was not evidence
of a speedup.

## Same-day software response and remaining acceptance

The shared live-progress owner routed ordinary stdout/stderr through Rich's
active display. Doctor suppressed submission transcript and scheduler-log paths
in normal output while retaining them under `--verbose`. A local 48-column PTY
fixture covered color and `NO_COLOR`, diagnostic ordering, a separate line
boundary and readable zero-duration timing. The card reported 418 focused
local progress, submission and Slurm Doctor tests.

Implementation checkpoint `feff802057f035c8e18893ef37c4f8e69a05ac2d`
passed [ordinary CI 35174741384](https://github.com/lab-cats/EMRYS/actions/runs/35174741384):
14 active jobs succeeded and four configured jobs, including the selected real
synthetic E2E lane, were skipped. This is hosted software evidence, not a
fresh Viking terminal walkthrough or selected real-Slurm result. CV-UX-01's
current normal/verbose, narrow color and plain PTY, zero-duration readability,
and Viking terminal acceptance remain with the source card. Its final status
is Verification pending. The September 17 styling refinement is a separate
dated change in that card and adds no higher evidence.
