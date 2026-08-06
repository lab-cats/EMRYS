# R environment metadata

`renv/` contains the guarded, opt-in project-local R environment metadata. It
is repository dependency lifecycle state, not a workflow stage.

Tracked files are `activate.R`, `settings.json`, this README, and the local
ignore policy; the canonical package lock is [`../renv.lock`](../renv.lock).
Project activation occurs only when `NORAD_USE_RENV=1`. Local libraries,
caches, staging, sandbox, and related restored state remain ignored.

## Restoration and cleanup

Restoration is an explicit operator action. Use the
[guarded local-R procedure](../docs/operations/RUNBOOK.md#guarded-local-r-environment)
rather than editing the library, activation script, settings, or lockfile to
silence drift. Do not blanket-clean `renv/library/` or other ignored dependency
state: it may be required for local validation and can be expensive to restore.
Local environment checks do not establish cluster or production runtime proof.
