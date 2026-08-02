# Engineering conventions

This document owns neutral, cross-language engineering conventions for new or
changed NORAD implementation in the currently supported workflow. It is not an
inventory of current executable behavior and does not claim that every legacy
entry point already conforms. When a convention conflicts with characterized
current behavior, the applicable colocated `CONTRACT.md` and the
[`functional-owner inventory`](../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
describe current truth; preserve that behavior until a separately approved
implementation or migration package changes it.

The root [`README.md`](../../README.md#repository-map) owns the implemented
repository map. [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md)
owns target homes and dependency direction only, while
[`MIGRATION_MECHANICS.md`](../../src/norad/contracts/MIGRATION_MECHANICS.md)
owns future relocation procedure. Neither target document describes a physical
migration already performed. Exact commands belong only in
[`RUNBOOK.md`](RUNBOOK.md), and durable rationale belongs in
[`DECISIONS.md`](../design/DECISIONS.md).

## Authority and owner boundaries

- The [functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md)
  and its linked contracts own exact current interfaces, side effects, defects,
  and legacy exceptions. Documentation must not normalize those exceptions.
- The [source topology](../../src/norad/contracts/SOURCE_TOPOLOGY.md) and
  [migration mechanics](../../src/norad/contracts/MIGRATION_MECHANICS.md) own
  target structure and movement rules, not current layout.
- The [runbook](RUNBOOK.md) owns supported invocations. This document describes
  conventions without copying commands.
- The [decision record](../design/DECISIONS.md) owns rationale and rejected
  alternatives. This document owns the resulting neutral working rules.

## Current-layout entry points

Before a separately approved physical migration, prefer new or changed
current-layout entry points shaped as:

```text
scripts/step_XX_<name>.sh
jobs/step_XX_<name>.slurm
tests/shell/test_step_XX_<name>.sh
```

These are compatibility conventions for the implemented layout, not permanent
target homes. Active tests and non-runnable future plans remain separate under
the [current repository map](../../README.md#repository-map) and the
[test-placement decision](../design/DECISIONS.md#keep-active-and-future-tests-separate).

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
[manifest decision](../design/DECISIONS.md#use-tsv-manifests).

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
executable logic belongs in tested, parameterized files under `scripts/` or its
separately approved target home.

## Dry-run and execution

New or migrated workflow producers and mature SLURM entry points are
dry-run-first unless an owner-local contract explicitly records a protected
current exception. For conforming script interfaces, omitting `--execute`
validates and prints while `--execute` publishes. Conforming SLURM interfaces
use `EXECUTE=0` for dry-run and `EXECUTE=1` for execution; every other value
fails. Dry-run must not publish final artifacts and should avoid creating output
directories when that could confuse validation. Any currently characterized
dry-run directory or logging side effect remains current truth until separately
changed.

See the [dry-run decision](../design/DECISIONS.md#default-to-dry-run), the
[functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md),
and its linked contracts for the boundary between convention and current
exceptions. Supported invocations remain in the [runbook](RUNBOOK.md).

## Validation and publication

Validate before expensive work and before publication. Multi-file publication
uses an owned lock, run-token staging, stable-input rechecks, an explicit
no-clobber rule including any owner-contract-authorized replacement boundary,
rollback and recovery, and a receipt or summary published last as the
transaction marker. The applicable contract owns exact current transaction
semantics and any characterized defect.

The durable boundaries are recorded in the
[validated-publication](../design/DECISIONS.md#publish-validated-transactions)
and [recovery-evidence](../design/DECISIONS.md#preserve-recovery-evidence)
decisions. This convention does not imply that an owner-specific validator is a
neutral shared library.

## Dependencies and R environment

Dependency restoration is an explicit operator action. Compute scripts,
validators, SLURM jobs, report renderers, and tests must not bootstrap or
install R, Quarto, system packages, or analysis dependencies.

The repository-local R environment is opt-in only through
`NORAD_USE_RENV=1`; `0` leaves normal startup unchanged and any other value
must fail. Automatic snapshots remain disabled, and lockfile changes require
review. The [R-environment decision](../design/DECISIONS.md#guard-the-repository-local-r-environment)
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

Record the loaded module state using the exact
[runbook procedure](RUNBOOK.md#module-list). Do not add an explicit memory
request without confirmation in the relevant cluster contract. The scheduler
boundary in [source topology](../../src/norad/contracts/SOURCE_TOPOLOGY.md) is
target architecture, not a claim about completed migration.

## Reporting consumers

A report renderer consumes one explicit validated canonical run summary plus
only supplemental tables authorized by exact path, hash, row count, and role.
It does not discover inputs, run analysis, install tools, or promote evidence
state. Current reporting surfaces remain in the
[functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md#cross-cutting-product-and-operational-owners);
rationale remains in the
[reporting](../design/DECISIONS.md#decouple-reporting-from-computation) and
[supplemental-table](../design/DECISIONS.md#authorize-supplemental-report-tables-explicitly)
decisions.

## Applying or changing a convention

Changing existing behavior requires the normal selected-card and
[task-delivery](TASK_DELIVERY.md#package-delivery) workflow. Update the
functional-owner inventory or applicable contract in the same coherent change
when its roster, interface, protection, or characterized exception is affected.
A source move follows the
[migration mechanics](../../src/norad/contracts/MIGRATION_MECHANICS.md); this
document does not authorize implementation or physical migration.
