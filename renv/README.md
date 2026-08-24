# R environment metadata

`renv/` contains the guarded, opt-in project-local R environment metadata. It
is repository dependency lifecycle state, not a workflow stage.

Tracked files are `activate.R`, `settings.json`, this README, and the local
ignore policy; the canonical package lock is [`../renv.lock`](../renv.lock).
Project activation occurs only when `EMRYS_USE_RENV=1`. Local libraries,
caches, staging, sandbox, and related restored state remain ignored.

## Restoration and cleanup

Restoration is an explicit operator action. Use the
[explicit dependency procedure](../docs/operations/RUNBOOK.md#explicit-dependency-setup)
rather than editing the library, activation script, settings, or lockfile to
silence drift. Do not blanket-clean `renv/library/` or other ignored dependency
state: it may be required for local validation and can be expensive to restore.
Local environment checks do not establish cluster or production runtime proof.

The repository policy is fixed: Bioconductor 3.23 packages are resolved through
`https://bioc-release.r-universe.dev`, CRAN packages through
`https://cloud.r-project.org`, and every locked Bioconductor package record uses
canonical `Source: Bioconductor`, `RemoteType: bioconductor`, and
`Repository: Bioconductor 3.23` metadata.

`make r-restore` is the only route allowed to bootstrap or install. Point
`RENV_PATHS_LIBRARY` at an operator-owned library root and run it with the
explicit R 4.6.1 executable. After restoration, pass the exact existing
platform library as `RENV_LIBRARY` to `make r-check`. The check selects that
library without running the renv autoloader, changes no dependencies, and fails
on any lock, version, or library-identity drift.

