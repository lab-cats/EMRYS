# Repository utilities

This directory contains repository-level operator and developer utilities that
do not belong to one scientific stage. It is an explicit integration surface,
not a general-purpose utility namespace or an installed command package.

## Owned interfaces

| Area | Public entry points | Boundary |
| --- | --- | --- |
| Manifest validation | [`validate_manifest.py`](validate_manifest.py) | Validates the sample-manifest contract and, when requested, declared FASTQ paths. It does not ingest, hash, freeze, or execute a run. |
| R environment | [`check_r_environment.R`](check_r_environment.R), [`restore_r_environment.R`](restore_r_environment.R) | Checks the guarded project R environment or explicitly restores the ignored local `renv` library from `renv.lock`. Restore is the mutating operation. |
| Quarto environment | [`restore_quarto.py`](restore_quarto.py) | Explicitly restores the checksum-pinned report renderer into ignored local tool storage. Report rendering never installs it implicitly. |
| Git and documentation mechanics | Seven commands documented in [`git_orchestration/`](git_orchestration/README.md): three `validate_*.py` validators plus `apply_fragment_candidate.sh`, `finalize_fragment_integration.sh`, `record_fragment_noop.sh`, and `publish_exact_ref.sh` | Validates or performs bounded fragment, documentation, commit, and exact-ref publication mechanics. `_common.py` and `_common.sh` are private support; none of these helpers select work, grant authority, choose content, resolve conflicts, or discard recovery state. |

Supported invocations and recovery procedures live in the
[`RUNBOOK`](../docs/operations/RUNBOOK.md) and
[`TROUBLESHOOTING`](../docs/operations/TROUBLESHOOTING.md) guides. Behavior is
protected directly by
[`test_validate_manifest.py`](../tests/test_validate_manifest.py),
[`test_quarto_restore.py`](../tests/test_quarto_restore.py),
[`test_local_r_environment.sh`](../tests/shell/test_local_r_environment.sh),
and [`tests/git_orchestration/`](../tests/git_orchestration/README.md), with
cross-entry-point coverage in
[`test_public_cli_contracts.py`](../tests/test_public_cli_contracts.py).

## State and evidence boundary

Validators and checks create no durable scientific output. Explicit restore
commands mutate only ignored dependency/tool state and can preserve recovery
material; execute-mode Git helpers can mutate repository history or publish an
exact ref. Those effects are repository mechanics, not pipeline evidence.

Success here establishes only the interface's declared local check or
operation. It does not prove ingestion, cluster availability, production
execution, scientific review, or biological validity.
