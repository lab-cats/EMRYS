# Local-pilot launcher regression test plan

Use this plan after the launcher-config implementation is committed locally.
It is a local/workstation acceptance pass only: do not invoke a real `sbatch`,
access a cluster, edit operator data, or push changes. Provision the locked
development/workflow environment before validation only with explicit local
installation authority; validation itself must run without dependency or
lockfile mutation. The package-distribution test creates an isolated temporary
environment from the existing offline lock/cache. Report that lane `BLOCKED`
rather than weakening or skipping its assertions when its exact cache is not
available.

## Required report

Record the branch, starting commit, ending commit, exact failed commands, and
the status of every phase as `PASS`, `FAIL`, `BLOCKED`, or `NOT RUN`. A blocked
check is not a pass. Stop on the first confirmed confidentiality failure,
unexpected real scheduler resolution, tracked `.env`, or source-tree mutation
outside test temporary directories. A match on a short/common `.env` value is
a review candidate, not by itself proof that tracked content discloses site
information.

## 1. Admit the checkout

From the intended repository root:

```bash
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
git diff --check
git check-ignore -v .env
```

Require `.env` to be ignored. If it exists, require a real nonsymlink file
owned by the current user with no group/other permission bits. Never print its
contents.

Check that no nonempty private `.env` value appears in tracked files or the
current tracked diff, reporting only the variable name on failure:

```bash
.venv/bin/python - <<'PY'
import os
import subprocess
from pathlib import Path

path = Path(".env")
if not path.exists():
    raise SystemExit(0)
tracked = subprocess.run(
    ["git", "grep", "-I", "-h", "--", "."],
    check=True,
    capture_output=True,
).stdout
diff = subprocess.run(
    ["git", "diff", "--no-ext-diff", "HEAD", "--", "."],
    check=True,
    capture_output=True,
).stdout
haystack = tracked + diff
failures = []
for line in path.read_text(encoding="utf-8").splitlines():
    if not line or line.startswith("#") or "=" not in line:
        continue
    name, value = line.split("=", 1)
    if value and value.encode() in haystack:
        failures.append(name)
if failures:
    raise SystemExit(
        "review exact private-value matches for variables: " + ", ".join(failures)
    )
PY
```

Classify every reported variable without printing its value. Fail the phase if
the tracked occurrence is the actual site/private value; record a benign
generic-word collision separately.

## 2. Focused contract and behavior tests

Use the already-restored locked development environment; do not run `uv sync`
as part of validation:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  -q --tb=short -p no:cacheprovider \
  tests/contracts/orchestration/test_orchestration_contracts.py \
  tests/orchestration/local_pilot/test_launcher_config.py \
  tests/orchestration/local_pilot/test_onboarding.py \
  tests/libraries/test_source_authority.py
```

Confirm the tests specifically exercise:

- packaged defaults, launcher YAML, and explicit-option precedence;
- process environment before repository-root `.env`;
- strict YAML/environment-reference and private-file rejection;
- no shell interpolation or private-value disclosure;
- ambient/authored `EMRYS_EXECUTE` cannot activate execution;
- default plan versus explicit `--execute` internal transport;
- exact inclusion/omission of `--exclusive` and `--nodelist`;
- removal of ambient `SBATCH_*` policy and ambient internal execution state;
- exact internal batch-marker admission and lexical virtualenv Python identity;
- one-node/one-task submission and sealed batch exports;
- launcher schema/default participation in source identity.

## 3. Packaging and command isolation

```bash
uv lock --check --offline
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  -q --tb=short -p no:cacheprovider tests/test_package_distribution.py
PYCACHE_ROOT="$(mktemp -d)"
.venv/bin/python -X pycache_prefix="$PYCACHE_ROOT" \
  -m compileall -q scripts src/emrys tests
rm -r -- "$PYCACHE_ROOT"
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' \
  make -s shell-test
```

The wheel test performs an offline locked install into its own temporary
directory; it must not modify `.venv`. If that isolated install is not
authorized or its cache is incomplete, mark only this lane `BLOCKED`. When it
runs, it must prove that both
`launcher_config.schema.json` and `default_launcher.yaml` are byte-identical to
their source resources. No dependency or lockfile change is expected.

## 4. Generated-starter regression

Use an absent directory under a temporary parent. First prove the dry run
writes nothing, then create the starter:

```bash
TEST_ROOT="$(mktemp -d)"
STARTER="$TEST_ROOT/starter"

.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys init local-pilot \
  --output-dir "$STARTER"
test ! -e "$STARTER"

.venv/bin/python -X pycache_prefix=/dev/null -I -m emrys init local-pilot \
  --output-dir "$STARTER" \
  --execute

test -f "$STARTER/emrys.launcher.yaml"
test -x "$STARTER/run-in-slurm.sh"
test ! -e "$STARTER/.env"
test ! -e "$STARTER/.env.example"
```

Verify the starter manifest names and hashes `emrys.launcher.yaml`, and that no
generated file contains an execution field or a private `.env` value.

## 5. Workstation-only compatibility checks

Run these last. They are intentionally deferred when the current environment
lacks the locked virtual environment, actual Bash 3.2, or installed-wheel
isolation.

1. Run `bash --version` and record whether it is Bash 3.2. On an actual Bash
   3.2 host, run `bash -n "$STARTER/run-in-slurm.sh"` and the focused fake-
   `sbatch` onboarding tests.
2. Invoke the generated wrapper from a directory unrelated to either the
   source checkout or starter. The selected launcher must remain adjacent to
   the wrapper, and private values must still come only from the generation-
   bound checkout root `.env`.
3. Put a fake `sbatch` first on `PATH`; never permit the real scheduler binary.
   Verify no flag submits `--execute` except wrapper `--execute`, and placement
   flags occur at most once.
4. Build and test the wheel with the repository's offline package-distribution
   test. Confirm the generated wrapper can invoke the installed launcher helper
   under controlled Python options.
5. Run the complete local gate once:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' \
     RSCRIPT_BIN=/usr/local/bin/Rscript make -s all-checks
   ```

   This full gate includes the isolated wheel-install lane above and therefore
   requires the same explicit local installation authority.

## Current execution status

Last updated 2026-08-21 for the reporting/optimization integration based at
`0422957`. The optimization history advances from `82d991c` through `69caf2c`,
adds the workload-specific CSU policy at `41c7287`, repairs four inherited
non-reporting test defects at `926dc2e`, and prints reporting memory in the
no-write plan at `96e79da`. Reporting implementation and its reconciled Step
`10` fixture are integrated by `c37e2d2` and `0422957`.

The available host is a Linux Codex scratch environment, not the operator's
macOS checkout. The exact locked development/workflow environment was
provisioned without changing `pyproject.toml` or `uv.lock`. No real scheduler,
cluster resource, push, or remote repository mutation was used. A private root
`.env` was created locally, remains Git-ignored, is a real mode-`0600` file,
contains no execution control, and passes launcher admission without printing
its values.

| Phase | Status | Evidence and remaining boundary |
| --- | --- | --- |
| Checkout admission | PASS | The intended branch was clean at admission and after each commit. `.env` is ignored, owner-only, and admitted; `git diff --check` passes. No private operator path is tracked. |
| Focused launcher contract | PASS | Launcher-config, onboarding, capacity, resource-policy, and lifecycle selection passes: 170 tests. |
| Resource-policy regression | PASS | Capacity, resource-policy, and onboarding allocation-boundary selection passes: 72 tests. This includes missing/invalid/ambiguous Slurm allocation variables, whole-workflow oversubscription, and unchanged CPU/memory propagation into request validation, doctor, and execution. |
| CSU EV/PUM1 policy | PASS | The tracked resource profile resolves at 12 workflow cores and 524,288 MiB inside the exclusive 256-CPU node allocation, with effective-policy SHA-256 `3f5767f4878cbc9878d21798ef385daea850a1e539fba66b80e8537cdfa2a2e8`. Its raw SHA-256 is `dd629f5d6d0072a2ccfa7f9114a85f13e8a2fef00f561db0831cf464fb1720c1`; the matching no-explicit-memory launcher SHA-256 is `4f3f408a31fcb147601b602ae692b900b119be9e2893940d57127ab7ba3cde50`. The 12-hour launcher walltime is conservative operator headroom, not benchmark evidence. |
| Generated starter | PASS | The onboarding suite passes 50 tests. A separate create-absent starter was invoked from an unrelated directory with fake `sbatch`; explicit `--exclusive` and `--nodelist` appeared exactly once, while the default case emitted neither. |
| Static and shell gates | PASS | Ruff, vulture, documentation validation, compilation, `git diff --check`, and `make -s shell-test` pass. The shell gate includes 202 Slurm-wrapper tests; direct R checks were skipped because `Rscript` is unavailable. |
| Lock and environment check | PASS | `.venv` contains the exact locked dev/workflow groups: Python 3.12.13 and Snakemake 9.25.1. An offline locked sync check reports that it would make no changes. |
| Isolated wheel | PASS | The isolated wheel build/install and package-distribution test passes. A disposable UV cache was primed once with explicit network authority; the final validation lane then passed offline without source, lockfile, or `.venv` mutation. |
| Real Snakemake workflow tests | PASS | Actual Snakemake 9.25.1 DAG/execution/resume coverage passed 37 tests at optimization head `69caf2c`. Current integration head additionally passes six selected real-Snakemake DAG/resource/failure-resume cases in 5m08s. Scientific executables are replaced by repository test doubles. |
| Historical broad regression | PASS | The optimization integration passed 1,564 non-reporting tests with 8 skips and one deliberately deselected already-proven long failure/resume case before reporting was merged. This remains a historical baseline rather than a claim that the current integrated tree reran the full aggregate gate. |
| Bash 3.2 compatibility | BLOCKED | The available shell is GNU Bash 5.2.21. The fake-scheduler behavior passes here, but syntax and behavior still require an actual Bash 3.2 host. |
| Scientific-tool workstation checks | BLOCKED | `Rscript`, STAR, samtools, bcftools, GATK, Picard, and RSeQC are absent on this host. Java is present. Their direct version/runtime checks remain environment acceptance, not Python dependency checks. |
| Complete `all-checks` gate | BLOCKED | The current host lacks `Rscript`. The four inherited non-reporting failures and the reporting fixture mismatch are integrated; the guarded real-R lane still requires its intended runtime before the aggregate gate can be claimed. |

The reporting implementation is now part of the integrated source history.
Its scientific-runtime claims remain bounded by the guarded real-R lane rather
than inferred from this host's Python-only validation.

Global `pytest-xdist` is not an accepted aggregate mode for this repository's
real-Snakemake fixtures: an exploratory four-worker run showed shared-fixture
interference and was stopped. Use the serial project targets and the dedicated
workflow selection above for acceptance.

## CSU EV/PUM1 handoff files

After generating the matched external input directory, install the reviewed
tracked profiles beside its wrapper:

```bash
cp configs/local_pilot_launcher.csu_viking_ev_pum1.yaml \
  "$EMRYS_INPUT_DIR/emrys.launcher.yaml"
cp configs/local_pilot_resources.csu_viking_ev_pum1.yaml \
  "$EMRYS_INPUT_DIR/emrys.resources.yaml"
```

The private source-checkout root `.env` supplies only account, partition, QOS,
node selection, log directory, workspace, and scratch parent. Before the first
submission, create the configured log directory, confirm
`runtime.selected.tsv` exists beside the request, verify both copied file
hashes, and run the wrapper without `--execute`. The resulting compute job must
print the full effective workflow and reporting resource profile before the
execution submission is allowed.

## Deferred environment acceptance

Keep these checks last and do not claim them from test doubles:

- run the generated wrapper under actual Bash 3.2 on the operator workstation;
- run direct R and scientific-tool readiness checks in the intended runtime;
- verify the scheduler accepts account, partition, QOS, `--exclusive`, and
  `--nodelist`, omits an explicit memory request, and exposes the full-node CPU
  allocation plus process-visible memory to the batch process;
- verify module loading, node-local scratch, NFS behavior, timeout/OOM handling,
  and retained logs on a disposable synthetic allocation;
- measure the configured stage concurrency, total CPU use, and peak memory on
  the retained synthetic and benchmark inputs.
