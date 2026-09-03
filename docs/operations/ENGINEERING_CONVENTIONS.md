# Engineering conventions

These are neutral implementation rules for changed EMRYS code. Exact current
behavior and characterized exceptions remain in the applicable owner contract
and tests; this guide does not normalize legacy behavior by assertion.

## Ownership and dependencies

- Functional implementation, native assets, diagnostics, recovery, contract,
  and direct tests stay with one owner under `src/emrys/<domain>/<owner>/` and
  the mirrored test area.
- Cross-owner data uses explicit contracts and admitted artifacts. Do not import
  a peer's private implementation or create a generic utility bucket.
- Neutral contracts have no implementation dependencies. Neutral libraries are
  narrow, acyclic, and shared only after equivalent production reuse is proved.
- [`SOURCE_TOPOLOGY.md`](../../src/emrys/contracts/SOURCE_TOPOLOGY.md) owns
  current import direction; [`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md)
  owns scientific identities and artifact edges.
- Root scripts, Git, Make, CI, package metadata, and environments are repository
  controls, not scientific workflow owners.

## Inputs and public entry points

Declare scientific inputs; never discover them by glob or infer biological
meaning, sample order, pairing, or partitions from names. Ordered TSV manifests
retain their exact schemas. Paths come from arguments or admitted configuration,
not user-, checkout-, or machine-specific literals.

New or changed entry points should validate before expensive work, show the
effective supported plan, use explicit destinations, fail with actionable
diagnostics, work with tiny fixtures or test-owned effects, validate before
publication, and avoid hidden mutable state. Python uses `argparse`, `pathlib`,
and a guarded `main`; Bash uses strict portable syntax and quoted values; R
validates arguments and does not depend on ambient working directory.

Public producers are dry-run-first unless their owner contract records an
approved exception. Grouped `run` and `resume` display one immutable plan before
terminal confirmation; automation uses `--execute`. Slurm is placement for the
same operation, not a second owner interface.

## Validation, publication, and recovery

Validate inputs before computation and outputs before publication. A multi-file
transaction declares its roster, lock, staging, stable-input rechecks,
no-clobber rule, rollback/recovery behavior, and receipt or summary published
last. Do not assume that one owner's transaction is interchangeable with
another or extract a universal lifecycle merely because vocabulary overlaps.

Preserve foreign, partial, or ambiguous output and recovery evidence. Do not
infer success from process exit, file presence, timestamps, logs, scheduler
state, or workflow-engine metadata. Exact rules belong to the owner; durable
rationale is in the
[`execution decision`](../design/decisions/execution-evidence-and-reporting.md).

## Dependencies and environments

| Root authority | Purpose |
|---|---|
| `.Rprofile`, `renv.lock` | Opt-in, reviewed R environment. Activation does not authorize restore or lock mutation. |
| `pyproject.toml`, `uv.lock` | Python package, direct dependency, installed command, tool configuration, and exact resolved graph. |
| `.coveragerc` | Branch/subprocess coverage configuration; acceptance remains in the test baseline. |

Dependency restoration is an explicit setup or Doctor-repair action. Compute,
validators, report renderers, and tests never bootstrap packages or change
locks. `EMRYS_USE_RENV=1` is the only repository-R opt-in; invalid values fail,
automatic snapshots remain disabled, and lock changes require review.

## Development validation

Use focused tests while changing one owner:

```bash
.venv/bin/python -m pytest -q --tb=short <focused-test-paths>
.venv/bin/python tests/tools/source_dependencies.py --repo "$PWD"
uv lock --check
uv sync --locked --check
make -s shell-test
```

Run the assembled applicable gate once against the final executable state:

```bash
RSCRIPT_BIN=/absolute/path/to/Rscript make -s all-checks
```

Long suites run in CI. Documentation-only work normally needs `git diff
--check`, `make -s documentation-check`, and a review of the final changed-file
list. State exactly which checks ran and do not promote focused evidence to a
broader claim.

## Slurm and reporting

Whole-Run Slurm transport re-admits execution authority, records scheduler
provenance and streams, loads only declared modules, owns private scratch, and
delegates once to grouped control. Do not add owner-local scheduler wrappers.
Omitted site policy remains omitted; explicit resource settings must reconcile
with the allocation.

Reporting consumes one admitted canonical summary and explicitly authorized
supplemental tables. It does not discover inputs, run analysis, install tools,
mutate upstream state, or promote evidence. Module-specific scientific renderers
remain separate from fixed evidence/operations presentation.

## Applying a convention

Follow the [`workflow kernel`](WORKFLOW.md). Update the exact owner contract and
direct tests when behavior changes, and the architecture inventory only when
ownership or public routing changes. A convention does not authorize a source
move, public change, deletion, dependency installation, or execution.
