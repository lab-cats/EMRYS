# Engineering conventions

This document owns neutral, cross-language engineering conventions for new or
changed NORAD implementation in the currently supported workflow. It is not an
inventory of current executable behavior and does not claim that every legacy
entry point already conforms. When a convention conflicts with characterized
current behavior, the applicable colocated `CONTRACT.md` and the
[`functional-owner inventory`](../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
describe current truth; preserve that behavior until a separately approved
implementation changes it.

The [architecture index](../architecture/README.md) organizes current system
views. [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md)
owns current source domains and dependency direction. Exact commands belong in
the applicable owner README, cross-cutting commands in [`RUNBOOK.md`](RUNBOOK.md),
and durable rationale in [`DECISIONS.md`](../design/DECISIONS.md).

## Authority and owner boundaries

- The [functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
  and its linked contracts own exact current interfaces, side effects, defects,
  and legacy exceptions. Documentation must not normalize those exceptions.
- The [source topology](../../src/norad/contracts/SOURCE_TOPOLOGY.md) owns
  current source domains and dependency direction.
- Owner READMEs own exact invocations; the [runbook](RUNBOOK.md) owns only
  genuinely cross-cutting operations.
- The [decision record](../design/DECISIONS.md) owns rationale and rejected
  alternatives. This document owns the resulting neutral working rules.

## Owner-local entry points

Workflow, analysis, evidence, ingestion, and scheduler assets live with their
functional owner under `src/norad/<domain>/<owner>/`; direct tests mirror that
owner under `tests/<domain>/<owner>/`. Root `jobs/` and numbered root
`scripts/` paths are retired. Exact current names and protected exceptions
belong to the
[functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
and adjacent contracts. Non-runnable future test plans remain separate under
the [test-placement rationale](../design/decisions/repository-and-delivery.md#active-and-future-tests-remain-distinct).

## Declared inputs, manifests, and paths

The declared sample manifest owns sample identity, metadata, and order. Other
typed manifests retain their own contracts for partitions, inventory,
approvals, or evidence. Use explicit, tab-separated manifests and
manifest-driven selection; never infer pairings, sample order, or partitions
from filenames.

Use command-line arguments, explicit configuration, environment overrides, and
resolved output roots instead of user- or machine-specific paths. Scientific
and report inputs must be declared rather than discovered by glob. Exact fields
and refinements remain owner-local; the durable rationale is in the
[manifest rationale](../design/decisions/repository-and-delivery.md#explicit-manifests).

## Public entry-point design

New or changed entry points should:

- accept explicit arguments and provide useful help;
- validate inputs before expensive work;
- print resolved context and the exact command or commands it would run;
- use explicit output paths;
- fail loudly with actionable messages;
- support tiny local fixtures or mocked tools;
- validate outputs before publication; and
- avoid hidden global state.

Bash uses strict mode, portable syntax, quoted variables, and arrays where
helpful. Python uses `argparse`, `pathlib`, a guarded `main`, and separable
parsing, validation, and publication logic. R entry points validate arguments
and avoid hard-coded working directories. Owner-local contracts remain
authoritative for exact arguments and characterized behavior.

Documentation must link canonical standalone Mermaid sources rather than keep
inline copies. Keep only short supported invocations in Markdown; substantive
executable logic belongs in tested, parameterized files beside its functional
owner. Root `scripts/` remains repository-control tooling.

## Dry-run and execution

New or changed workflow producers and mature SLURM entry points are
dry-run-first unless an owner-local contract explicitly records a protected
current exception. For conforming script interfaces, omitting `--execute`
validates and prints while `--execute` publishes. Conforming SLURM interfaces
use `EXECUTE=0` for dry-run and `EXECUTE=1` for execution; every other value
fails. Dry-run must not publish final artifacts and should avoid creating output
directories when that could confuse validation. Any currently characterized
dry-run directory or logging side effect remains current truth until separately
changed.

See the [dry-run decision](../design/decisions/execution-evidence-and-reporting.md#default-to-dry-run), the
[functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md),
and its linked contracts for the boundary between convention and current
exceptions. Supported invocations remain in the applicable owner README.

## Validation and publication

Validate before expensive work and before publication. Multi-file publication
uses an owned lock, run-token staging, stable-input rechecks, an explicit
no-clobber rule including any owner-contract-authorized replacement boundary,
rollback and recovery, and a receipt or summary published last as the
transaction marker. The applicable contract owns exact current transaction
semantics and any characterized defect.

The durable boundaries are recorded in the
[validated-publication](../design/decisions/execution-evidence-and-reporting.md#publish-validated-transactions)
and [recovery-evidence](../design/decisions/execution-evidence-and-reporting.md#preserve-recovery-evidence)
decisions. This convention does not imply that an owner-specific validator is a
neutral shared library.

## Repository dependency and test configuration

Six retained root files are project/tool configuration surfaces, not workflow
stages or miscellaneous application inputs:

| Root file | Purpose and placement boundary |
| --- | --- |
| [`.Rprofile`](../../.Rprofile) | Guarded R startup hook. With the default `NORAD_USE_RENV=0`, startup is unchanged; `1` opts in and every other value fails. When opted in, the hook defaults sandboxing and automatic snapshots to disabled only when the caller has not set them; supported Make lanes set both controls false explicitly. It then sources the project `renv/activate.R`. Activation does not restore the lockfile, although the activator may bootstrap the pinned `renv` package itself if missing. R can discover this file at the project root, and Make also binds it by absolute path. |
| [`renv.lock`](../../renv.lock) | Reviewed R and Bioconductor dependency snapshot used by guarded activation plus explicit restore and status checks. Root placement is the conventional and implemented `renv` project boundary; restored libraries and caches remain ignored. See [`renv/README.md`](../../renv/README.md). |
| [`pyproject.toml`](../../pyproject.toml) | Authoritative Python package metadata: build backend, distribution identity, direct runtime dependencies, the `dev` dependency group, package discovery/resources, Ruff configuration, and the installed `norad` console entry point. Migrated commands use the grouped interface through the selected installed interpreter in isolated mode; unmigrated owner directories and commands enter the distribution only through an owner-local cutover. |
| [`uv.lock`](../../uv.lock) | Authoritative exact Python dependency graph resolved from `pyproject.toml`. `uv sync --locked` installs the project plus its default `dev` group into `.venv`; the complete gate first uses `uv sync --locked --check` as a read-only congruence check, while validation and runtime owners never mutate the lock or repair the environment. The lock contains transitive packages without making them direct project dependencies. |
| [`.coveragerc`](../../.coveragerc) | Coverage.py measurement configuration for branch, parallel/subprocess, relative-path, and source-scope behavior. Make binds the root file and coverage also supports root discovery. Acceptance thresholds and evidence belong to [`TEST_BASELINE.md`](../design/TEST_BASELINE.md), not this file. |

Presence of these files establishes configuration only. It does not prove that
dependencies were restored, tests passed, or a local, cluster, production,
scientific-review, or biological environment is ready. Moving one requires an
explicitly bounded review of every caller, discovery assumption, and direct
contract test.

Dependency restoration is an explicit operator action. Compute scripts,
validators, SLURM jobs, report renderers, and tests must not bootstrap or
install R, system packages, or analysis dependencies.

The repository-local R environment is opt-in only through
`NORAD_USE_RENV=1`; `0` leaves normal startup unchanged and any other value
must fail. Automatic snapshots remain disabled, and lockfile changes require
review. The [R-environment decision](../design/decisions/execution-evidence-and-reporting.md#guard-the-repository-local-r-environment)
owns the rationale; setup and restoration commands remain in the
[runbook](RUNBOOK.md).

## SLURM interfaces

Mature owner-specific SLURM entry points delegate to their functional
implementation, use strict shell behavior, validate execution control, record
job context plus resolved inputs and outputs in logs, and load required modules
inside the job. The current
[inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md#numbered-workflow-and-evidence-owners)
and owner-local contracts explicitly preserve jobs that embed a producer, act
as probes or scaffolding, create dry-run directories, or otherwise depart from
this convention.

Record the loaded module state as part of the cross-cutting
[cluster procedure](RUNBOOK.md#cluster-execution-and-promotion). Do not add an
explicit memory request without confirmation in the relevant cluster contract.
Current scheduler placement and dependency boundaries are described by
[source topology](../../src/norad/contracts/SOURCE_TOPOLOGY.md).

## Reporting consumers

A report renderer consumes one explicit validated canonical run summary plus
only supplemental tables authorized by exact path, hash, row count, and role.
It does not discover inputs, run analysis, install tools, or promote evidence
state. Current reporting surfaces remain in the
[functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md#cross-cutting-product-and-operational-owners);
rationale remains in the
[reporting](../design/decisions/execution-evidence-and-reporting.md#decouple-reporting-from-computation) and
[supplemental-table](../design/decisions/execution-evidence-and-reporting.md#authorize-supplemental-report-tables-explicitly)
decisions.

## Applying or changing a convention

Changing existing behavior follows the short
[workflow kernel](WORKFLOW.md). Update the
functional-owner inventory or applicable contract in the same coherent change
when its roster, interface, protection, or characterized exception is affected.
A source move requires a separately reviewed owner-boundary change; this
document does not authorize implementation.
