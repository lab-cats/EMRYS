# R environment metadata

`renv/` holds the opt-in project R environment metadata: `activate.R`,
`settings.json`, and the local ignore rules. [`renv.lock`](../renv.lock) is the
package lock. Activation requires `EMRYS_USE_RENV=1`; restored libraries, caches,
staging, and sandbox files remain ignored.

## Package sources and restoration

Bioconductor 3.23 packages resolve through
`https://bioc-release.r-universe.dev`; CRAN packages use
`https://cloud.r-project.org`. Locked Bioconductor records use canonical
`Source: Bioconductor`, `RemoteType: bioconductor`, and
`Repository: Bioconductor 3.23` metadata.

`make r-restore` and managed `emrys doctor --repair` use the same restoration
script; Doctor selects its Project-owned runtime. Bootstrap restoration uses an
explicit external `RENV_PROJECT` for settings, locks, staging, and caches while
the activation script and package lock remain installed read-only inputs.
Workflow execution never
installs packages. For an operator-owned library, follow the
[runbook procedure](../../../docs/operations/RUNBOOK.md#dependency-maintenance), including
R 4.6.1, `RENV_PROJECT` and `RENV_PATHS_LIBRARY` for restoration, and the exact platform-specific
`RENV_LIBRARY` for checking. The check bypasses the renv autoloader, changes no
dependencies, and rejects lock, version, or library-identity drift.

Do not edit locks or activation settings to hide drift, or blanket-clean ignored
libraries: local validation may depend on them and restoration can be expensive.
A local environment check does not qualify a cluster or production runtime.
