# NORAD source domains

This package tree separates neutral contracts and libraries from functional
ingestion, transformation, analysis, evidence, and reporting owners. The
canonical dependency rules live in
[`SOURCE_TOPOLOGY.md`](contracts/SOURCE_TOPOLOGY.md).

Root `pyproject.toml` installs the explicit internal packages and their named
schema/report resources. The grouped `python -I -m norad` interface exposes
only migrated owner routes; it does not expose every source directory
automatically. Functional owners join the distribution during their own
reviewed cutover.

- [`contracts/`](contracts/) — semantic identities, schemas, artifact and
  scientific-evidence contracts, and allowed source topology.
- [`libraries/`](libraries/) — neutral mechanics shared by proven consumers.
- [`stages/`](stages/) — computational transformation owners.
- [`analyses/`](analyses/) — scientific analysis owners.
- [`evidence/`](evidence/) — evidence collection, reconciliation, and review
  packaging.
- [`ingestion/`](ingestion/) — bounded external-input admission.
- [`orchestration/`](orchestration/) — read-only local-pilot normalization,
  reporting projection, and semantic all-pass admission.
- [`reporting/`](reporting/) — artifact, run-summary, and static-report
  projections.

Each functional child owns its public paths, local contract, direct tests,
diagnostics, and recovery boundary. This index creates no new command or
cross-domain import authority.
