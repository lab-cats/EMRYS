# Application-logging tests

These tests cover the shared logging controls, handler, storage, helper, adoption guard, and installed-package behavior. They verify logging mechanics without granting logs authority over execution, recovery, receipts, or scientific state.

## Doctor terminal collision evidence

The September 16, 2026 operator report in commit
`3c97175517aa4c3565eec21f5c900c42ebd44976` records Viking job `621172` with
`Slurm submission-to-return wait 0:00:00` and the next `Slurm submission records:`
diagnostic joined as `0:00:00Slurm submission...`. The referenced screenshot has
no retained path or hash. This establishes an operator-reported presentation
collision, not record loss, wrong job identity or scheduler failure.

The collision fix is `b611890f016f92debabaac4e64550dd73669bca2`.
The [48-column PTY fixture](test_helpers.py) covers color and `NO_COLOR`,
diagnostic ordering, a separating line boundary and readable zero-duration
output. The source reported 418 combined progress, submission and Slurm Doctor
tests; that count is not a count of terminal fixtures.
Checkpoint `feff802057f035c8e18893ef37c4f8e69a05ac2d` passed
[ordinary CI 35174741384](https://github.com/lab-cats/EMRYS/actions/runs/35174741384):
14 active jobs passed and four configured jobs, including selected real
synthetic E2E, were skipped. These observations do not establish a fresh Viking
terminal walkthrough or selected real-Slurm result, and shorter output does not
establish a speedup.

The [Doctor contract](../../../src/emrys/orchestration/run_coordinator/CONTRACT.md#no-write-and-publication-boundaries)
owns serialization and normal/verbose output rules.
[CV-UX-01](../../../docs/tasks/backlog_matrix.md#doctor-qualification-and-presentation)
retains terminal acceptance; broader presentation and measured duration remain
separate subjects under CV-U04 and CV-26.
