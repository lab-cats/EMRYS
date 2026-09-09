# Engineering conventions

Use this guide to prepare a development environment and check a change.
The [workflow](WORKFLOW.md) owns scope and approval; owner contracts and tests
own current behavior, including exceptions.

## Ownership and dependencies

Keep implementation, assets, diagnostics, contracts, and tests with their
functional owner. Use [source topology](../../src/emrys/contracts/SOURCE_TOPOLOGY.md)
for import rules and the [stage map](../../src/emrys/contracts/STAGE_MAP.md) for
scientific identities and artifact dependencies. Repository tooling is not a
scientific workflow owner. Do not import a peer's private code or create a
miscellaneous utility module.

## Inputs and public entry points

Use declared inputs and explicit destinations, not hardcoded machine paths.
Never infer biological meaning, pairing, or order from names. Reject bad inputs
before expensive work and show the supported plan. Prefer `argparse`, `pathlib`,
and a guarded Python `main`; use strict, portable Bash with quoted values;
make R inputs independent of the working directory.
The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#no-write-and-publication-boundaries)
owns grouped confirmation behavior. Direct producers preview by default unless
their owner contract explicitly permits another behavior.

## Validation, publication, and recovery

Each owner defines its input/output checks, publication order, and recovery.
Similar transaction names do not prove equivalent behavior. Preserve ambiguous
outputs and evidence; follow the
[execution decision](../design/decisions/execution-evidence-and-reporting.md)
and the affected owner contract before changing a transaction.

## Dependencies and environments

| Authority | Purpose |
|---|---|
| `.Rprofile`, `renv.lock` | Opt-in R activation and the reviewed package snapshot. Activation does not restore packages or authorize lock changes. |
| `pyproject.toml`, `uv.lock` | Python package, direct dependencies, commands, tool settings, and the resolved dependency graph. |
| `.coveragerc` | Branch/subprocess coverage configuration; the [test baseline](../design/TEST_BASELINE.md) owns acceptance. |

Installation and lock changes require explicit setup or maintenance work.
Computation, validators, renderers, and tests never install packages or change
locks. Repository R activation requires `EMRYS_USE_RENV=1`; invalid values fail
and automatic snapshots stay disabled. The Runbook owns
[institution-provided R restoration](RUNBOOK.md#dependency-maintenance).

## Development validation

Run `uv sync --locked` to restore development tools. `make -s lint` checks Ruff
correctness and formatting, every tracked `.sh` file with ShellCheck, and Vulture.
CI also runs the separate Bash syntax gate and actionlint with locked ShellCheck
for workflow shell commands. [`.shellcheckrc`](../../.shellcheckrc) owns source
resolution; put any warning exception on its affected statement with a reason.

Optional staged checks use the existing locked `.venv`:

```bash
.venv/bin/pre-commit install --allow-missing-config
.venv/bin/pre-commit run
```

Installation is explicit; `--allow-missing-config` keeps older branches usable.
Hooks check staged Python under `scripts`, `src/emrys`, and `tests`, and staged
shell files. They do not rewrite files, install environments, or run scientific
tools, R checks, or test suites. Restore a missing or stale `.venv` explicitly.
To format Python, run `.venv/bin/ruff format <changed-python-paths>` and stage it.

Use focused checks while changing an owner:

```bash
.venv/bin/python -m pytest -q --tb=short <focused-test-paths>
.venv/bin/python tests/tools/source_dependencies.py --repo "$PWD"
uv lock --check
uv sync --locked --check
make -s shell-test
```

The assembled final gate is:

```bash
RSCRIPT_BIN=/absolute/path/to/Rscript make -s all-checks
```

Long suites run in CI; staged checks do not replace them. Documentation-only
work normally needs `git diff --check`, `make -s documentation-check`, and a
review of the changed-file list. Report exactly which checks ran; a focused
pass is not evidence that the full gate passed.

Update a coverage baseline only as an explicit, reviewed maintenance change.
Follow the [coverage policy](../design/TEST_BASELINE.md#python-coverage-policy),
check the current result, update the snapshot, inspect its diff, and check again:

```bash
make python-coverage-check
make python-coverage-baseline-update
git diff -- tests/baselines/python_coverage.json
make python-coverage-check
```

A passing test suite alone does not justify weaker coverage requirements.

## Slurm and reporting

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
owns Slurm transport and report orchestration. Keep one execution backend;
reporting reads admitted results and does not rerun analysis or alter upstream state.

## Applying a convention

Update owner contracts and direct tests with behavior changes. Update the
architecture inventory only when ownership or public routing changes. Follow
the workflow's approval boundaries; this guide supplies no additional authority.
