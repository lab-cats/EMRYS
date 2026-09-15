"""Contract tests for the GitHub Actions CI workflow."""

from __future__ import annotations

import importlib.metadata
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
MANAGED_RUNTIME_ROOT = REPO_ROOT / "src" / "emrys" / "resources" / "runtime"
MANAGED_RUNTIME_LOCK_PATH = MANAGED_RUNTIME_ROOT / "pixi.lock"
MANAGED_RUNTIME_MANIFEST_PATH = MANAGED_RUNTIME_ROOT / "pixi.toml"
SLURM_SETUP_PATH = REPO_ROOT / "tests" / "tools" / "configure_ci_slurm.sh"
SHELL_RECEIPT_ROOT = "${RUNNER_TEMP}/emrys-python311-test-shards"
ACTION_RECEIPT_ROOT = "${{ runner.temp }}/emrys-python311-test-shards"
MANUALLY_SELECTABLE_JOB_INPUTS = {
    "workflow-lint": "workflow_static_docs_wheel",
    "static-wheel": "workflow_static_docs_wheel",
    "shell-contracts": "shell",
    "guarded-r": "guarded_r",
    "managed-runtime-userspace": "managed_runtime_golden_path",
    "managed-golden-path": "managed_runtime_golden_path",
    "python314-coverage-shards": "python314",
    "python314-coverage": "python314",
    "python311-smoke": "python311",
}


def _workflow_document() -> dict[str | bool, Any]:
    document = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _workflow_jobs() -> dict[str, Any]:
    return _workflow_document()["jobs"]


def _workflow_triggers() -> dict[str, Any]:
    document = _workflow_document()
    triggers = document.get("on", document.get(True))
    assert isinstance(triggers, dict)
    return triggers


def _named_step(job: dict[str, Any], name: str) -> dict[str, Any]:
    matches = [step for step in job["steps"] if step.get("name") == name]
    assert len(matches) == 1, f"expected exactly one CI step named {name!r}"
    return matches[0]


def _expression(value: object) -> str:
    return " ".join(str(value).split())


def test_automatic_ci_accepts_every_pr_base_but_only_master_pushes() -> None:
    triggers = _workflow_triggers()
    assert triggers["pull_request"] is None
    assert triggers["push"] == {"branches": ["master"]}
    assert "merge_group" in triggers


def test_manual_lane_triggers_are_closed_and_independently_selectable() -> None:
    triggers = _workflow_triggers()
    assert triggers["schedule"] == [
        {"cron": "17 5 * * 1-6"},
        {"cron": "17 5 * * 0"},
    ]
    inputs = triggers["workflow_dispatch"]["inputs"]
    assert set(inputs) == {
        "workflow_static_docs_wheel",
        "shell",
        "guarded_r",
        "managed_runtime_golden_path",
        "python314",
        "python311",
        "synthetic_130",
        "synthetic_100000",
    }
    for value in inputs.values():
        assert value["type"] == "boolean"
        assert value["required"] is True
        assert value["default"] is False

    jobs = _workflow_jobs()
    manual = jobs["manual-selection"]
    assert _expression(manual["if"]) == "github.event_name == 'workflow_dispatch'"
    guard = _named_step(manual, "Require at least one selected CI lane")
    assert set(guard["env"]) == {
        "RUN_WORKFLOW_STATIC_DOCS_WHEEL",
        "RUN_SHELL",
        "RUN_GUARDED_R",
        "RUN_MANAGED_RUNTIME_GOLDEN_PATH",
        "RUN_PYTHON314",
        "RUN_PYTHON311",
        "RUN_SYNTHETIC_130",
        "RUN_SYNTHETIC_100000",
    }
    assert "select at least one CI lane" in guard["run"]


def test_ordinary_jobs_keep_automatic_runs_and_support_manual_selection() -> None:
    jobs = _workflow_jobs()
    for job_id, input_name in MANUALLY_SELECTABLE_JOB_INPUTS.items():
        condition = _expression(jobs[job_id]["if"])
        assert "github.event_name != 'workflow_dispatch'" in condition
        assert "github.event_name != 'schedule'" in condition
        assert f"inputs.{input_name}" in condition


def test_static_job_uses_the_shared_gate_without_repeating_sharder_self_tests() -> None:
    step = _named_step(
        _workflow_jobs()["static-wheel"],
        "Run static, lint, documentation, and wheel checks",
    )
    assert step["shell"] == "bash"
    assert step["run"].splitlines() == [
        "set -euo pipefail",
        "make -s validation-static",
        "make -s validation-wheel-smoke",
    ]
    assert "tests/test_python_test_shards.py" not in WORKFLOW_PATH.read_text(
        encoding="utf-8"
    )


def test_long_runs_have_unique_non_cancelling_concurrency() -> None:
    concurrency = _workflow_document()["concurrency"]
    group = _expression(concurrency["group"])
    cancellation = _expression(concurrency["cancel-in-progress"])
    assert "github.event_name == 'schedule'" in group
    assert "github.event_name == 'workflow_dispatch'" in group
    assert "github.run_id" in group
    assert cancellation == (
        "${{ github.event_name != 'schedule' && "
        "github.event_name != 'workflow_dispatch' }}"
    )


def test_python311_full_suite_is_nightly_or_explicitly_selected() -> None:
    jobs = _workflow_jobs()
    for job_id in ("python311-full-shards", "python311-full"):
        condition = _expression(jobs[job_id]["if"])
        assert "github.event_name == 'schedule'" in condition
        assert (
            "github.event_name == 'workflow_dispatch' && inputs.python311" in condition
        )


def test_synthetic_job_uses_locked_real_runtime_and_real_slurm() -> None:
    job = _workflow_jobs()["synthetic-e2e"]
    assert job["runs-on"] == "ubuntu-24.04"
    assert job["timeout-minutes"] == 360
    condition = _expression(job["if"])
    assert "github.event_name == 'schedule'" in condition
    assert "inputs.synthetic_130 || inputs.synthetic_100000" in condition

    seed = _named_step(job, "Seed external evidence roots for selected profiles")
    assert "${RUNNER_TEMP}/emrys-synthetic-e2e" in seed["run"]
    assert "${GITHUB_WORKSPACE}" not in seed["run"]

    paths = _named_step(job, "Select managed-runtime paths")
    assert "PIXI_WORKSPACE=%s/emrys-managed-runtime" in paths["run"]
    assert "PIXI_MANIFEST=%s/emrys-managed-runtime/pixi.toml" in paths["run"]
    assert "${RUNNER_TEMP}" in paths["run"]
    stage = _named_step(job, "Stage the reviewed runtime lock outside the checkout")
    assert "src/emrys/resources/runtime/pixi.toml" in stage["run"]
    assert "src/emrys/resources/runtime/pixi.lock" in stage["run"]
    tools = _named_step(job, "Restore locked native and R base environments")
    assert tools["uses"] == (
        "prefix-dev/setup-pixi@d3f436a425481402e6a95a1d1fc10331c708cd9e"
    )
    assert tools["with"]["pixi-version"] == "${{ env.PIXI_VERSION }}"
    assert tools["with"]["manifest-path"] == "${{ env.PIXI_MANIFEST }}"
    assert tools["with"]["environments"] == "native r"
    assert tools["with"]["activate-environment"] == "r"
    assert tools["with"]["locked"] is True
    assert "setup-micromamba" not in WORKFLOW_PATH.read_text(encoding="utf-8")

    slurm = _named_step(job, "Configure and prove one disposable Slurm node")
    assert "tests/tools/configure_ci_slurm.sh" in slurm["run"]

    authorities = _named_step(
        job, "Record exact runtime authorities outside the checkout"
    )
    assert "pixi-native-packages.json" in authorities["run"]
    assert "pixi-r-packages.json" in authorities["run"]
    assert "uv.lock" in authorities["run"]
    assert "src/emrys/renv.lock" in authorities["run"]
    assert "picard-slim-3.1.1-*/picard.jar" in authorities["run"]
    assert "*/picard-3.1.1-*/picard.jar" not in authorities["run"]

    renv_restore = _named_step(job, "Restore exact R dependency cache")
    assert renv_restore["id"] == "renv-cache"
    assert renv_restore["uses"] == (
        "actions/cache/restore@caa296126883cff596d87d8935842f9db880ef25"
    )
    renv_save = _named_step(
        job, "Save exact R dependency cache after successful restore"
    )
    assert _expression(renv_save["if"]) == (
        "steps.renv-cache.outputs.cache-hit != 'true'"
    )
    assert renv_save["uses"] == (
        "actions/cache/save@caa296126883cff596d87d8935842f9db880ef25"
    )
    assert renv_save["with"]["path"] == renv_restore["with"]["path"]
    assert renv_save["with"]["key"] == (
        "${{ steps.renv-cache.outputs.cache-primary-key }}"
    )

    profile_expectations = (
        (
            "Run the selected 130-pair real synthetic E2E",
            "--profile 130",
            "inputs.synthetic_130",
        ),
        (
            "Run the selected 100,000-pair real synthetic E2E",
            "--profile 100000",
            "inputs.synthetic_100000",
        ),
    )
    for name, profile_argument, selector in profile_expectations:
        step = _named_step(job, name)
        assert step["continue-on-error"] is True
        assert selector in _expression(step["if"])
        assert profile_argument in step["run"]
        assert "tests/tools/real_synthetic_e2e.py" in step["run"]
        assert "--slurm-partition emrys-ci" in step["run"]
        assert "--slurm-cpus" not in step["run"]
        assert "--execute" in step["run"]

    weekly = _named_step(job, "Run the selected 100,000-pair real synthetic E2E")
    assert "github.event.schedule == '17 5 * * 0'" in _expression(weekly["if"])


def test_managed_runtime_lock_has_one_linux_floor_and_exact_science_versions() -> None:
    manifest = tomllib.loads(MANAGED_RUNTIME_MANIFEST_PATH.read_text(encoding="utf-8"))
    platform = manifest["workspace"]["platforms"]
    assert platform == [
        {
            "name": "linux-x86-64-floor",
            "platform": "linux-64",
            "linux": "4.18",
            "glibc": "2.28",
        }
    ]
    assert manifest["environments"] == {"native": ["native"], "r": ["r"]}
    native_dependencies = manifest["feature"]["native"]["dependencies"]
    assert {"coreutils", "grep"} <= native_dependencies.keys()
    r_dependencies = manifest["feature"]["r"]["dependencies"]
    assert "libxml2-devel" in r_dependencies
    assert "libxml2" not in r_dependencies

    lock = yaml.safe_load(MANAGED_RUNTIME_LOCK_PATH.read_text(encoding="utf-8"))
    assert lock["platforms"] == [
        {
            "name": "p1",
            "subdir": "linux-64",
            "virtual-packages": [
                "__glibc=2.28",
                "__linux=4.18",
                "__unix=0=0",
                "__archspec=0=x86_64",
            ],
        }
    ]
    native = [
        item["conda"] for item in lock["environments"]["native"]["packages"]["p1"]
    ]
    for fragment in (
        "/star-2.7.11b-",
        "/samtools-1.19.2-",
        "/bcftools-1.21-",
        "/gatk4-4.6.1.0-",
        "/gzip-1.14-",
        "/openjdk-17.0.11-",
        "/picard-slim-3.1.1-",
        "/rseqc-5.0.4-",
    ):
        assert sum(fragment in url for url in native) == 1
    r_environment = [
        item["conda"] for item in lock["environments"]["r"]["packages"]["p1"]
    ]
    r_bases = [url for url in r_environment if "/r-base-" in url]
    assert len(r_bases) == 1
    assert "/r-base-4.6.1-" in r_bases[0]
    assert sum("/libxml2-devel-" in url for url in r_environment) == 1
    assert sum("/coreutils-" in url for url in native) == 1
    assert sum("/grep-" in url for url in native) == 1
    metadata = {row["conda"]: row for row in lock["packages"]}
    locked_environment = {*native, *r_environment}
    assert locked_environment <= metadata.keys()
    assert all(metadata[url]["sha256"] for url in locked_environment)


def test_managed_runtime_userspace_matrix_proves_the_same_lock() -> None:
    job = _workflow_jobs()["managed-runtime-userspace"]
    assert job["container"]["image"] == "${{ matrix.image }}"
    assert job["strategy"]["fail-fast"] is False
    assert job["strategy"]["matrix"]["include"] == [
        {
            "label": "Rocky 8.10",
            "image": "rockylinux/rockylinux:8.10",
            "os_id": "rocky",
            "os_version": "8.10",
            "glibc": "2.28",
        },
        {
            "label": "Ubuntu 22.04",
            "image": "ubuntu:22.04",
            "os_id": "ubuntu",
            "os_version": "22.04",
            "glibc": "2.35",
        },
        {
            "label": "Debian 12",
            "image": "debian:12",
            "os_id": "debian",
            "os_version": "12",
            "glibc": "2.36",
        },
    ]
    paths = _named_step(job, "Select managed-runtime paths")
    assert "PIXI_WORKSPACE=%s/emrys-managed-runtime" in paths["run"]
    assert "PIXI_MANIFEST=%s/emrys-managed-runtime/pixi.toml" in paths["run"]
    assert "${RUNNER_TEMP}" in paths["run"]
    trust = _named_step(job, "Install the distro TLS trust bundle")
    assert "dnf --assumeyes install ca-certificates" in trust["run"]
    assert (
        "apt-get install --yes --no-install-recommends ca-certificates" in trust["run"]
    )
    setup = _named_step(
        job, "Install both managed environments from the unchanged lock"
    )
    assert setup["uses"] == (
        "prefix-dev/setup-pixi@d3f436a425481402e6a95a1d1fc10331c708cd9e"
    )
    assert setup["with"]["environments"] == "native r"
    assert setup["with"]["locked"] is True
    verify = _named_step(job, "Verify locked tools in this container userspace")
    assert "src/emrys/resources/runtime/pixi.lock" in verify["run"]
    assert 'test -e "${r_prefix}/lib/libxml2.so"' in verify["run"]
    assert '"${r_prefix}/bin/pkg-config" --exists libxml-2.0' in verify["run"]
    assert (
        'PATH="${native_prefix}/bin" "${native_prefix}/bin/STAR" --version'
        in verify["run"]
    )
    assert 'PATH="${native_prefix}/bin" "${r_prefix}/bin/Rscript"' in verify["run"]
    assert 'pixi list --locked --manifest-path "${PIXI_MANIFEST}"' in verify["run"]


def test_managed_golden_path_uses_only_the_public_direct_journey() -> None:
    job = _workflow_jobs()["managed-golden-path"]
    assert job["runs-on"] == "ubuntu-24.04"
    assert job["timeout-minutes"] == 180
    setup = _named_step(job, "Install Pixi without provisioning the scientific runtime")
    assert setup["uses"] == (
        "prefix-dev/setup-pixi@d3f436a425481402e6a95a1d1fc10331c708cd9e"
    )
    assert setup["with"]["run-install"] is False
    assert setup["with"]["cache"] is False

    prepare = _named_step(
        job, "Prepare a clean clone, environment, and synthetic Project"
    )
    cache = _named_step(job, "Cache managed golden-path R packages")
    journey = _named_step(job, "Repair and exercise the supported managed golden path")
    reuse = _named_step(job, "Seal the completed donor and verify a separate borrower")
    step_names = [step.get("name") for step in job["steps"]]
    assert step_names.index(prepare["name"]) < step_names.index(cache["name"])
    assert step_names.index(cache["name"]) < step_names.index(journey["name"])
    assert step_names.index(journey["name"]) < step_names.index(reuse["name"])
    assert step_names.index(reuse["name"]) < step_names.index(
        "Require the clean clone to remain unchanged"
    )

    assert prepare["run"].index('cd "${clean_clone}"') < prepare["run"].index(
        '"${emrys[@]}" init synthetic'
    )
    assert cache["uses"] == ("actions/cache@caa296126883cff596d87d8935842f9db880ef25")
    assert cache["with"]["path"] == (
        "${{ runner.temp }}/emrys-managed-golden/project/runtime/managed/renv/cache"
    )
    assert "src/emrys/renv.lock" in cache["with"]["key"]
    assert "src/emrys/resources/runtime/pixi.lock" in cache["with"]["key"]

    path = journey["run"]
    assert "init synthetic" not in path
    assert 'emrys=("${clean_clone}/.venv/bin/emrys")' in path
    assert 'cd "${project_root}"' in path
    assert "-m emrys" not in path
    assert "--project" not in path
    for command in (
        "doctor",
        "validate",
        "--repair --execute",
        "run",
        "inspect",
    ):
        assert command in path
    for retired in (
        "storage-qualification",
        "runtime discover",
        "execution-profile",
        "synthetic-local-pilot",
        "local-pilot-run",
        "test_fresh_clone_e2e.py",
    ):
        assert retired not in path
    borrowing = reuse["run"]
    assert 'emrys=("${clean_clone}/.venv/bin/emrys")' in borrowing
    assert 'init synthetic \\\n  --output-dir "${borrower_root}" --execute' in borrowing
    assert 'inspect --project "${borrower_root}"' in borrowing
    preview = '--from-project "${donor_root}" \\\n'
    selection = '--from-project "${donor_root}" --execute'
    verification = 'doctor --project "${borrower_root}" --repair --execute'
    assert borrowing.index(preview) < borrowing.index(selection)
    assert borrowing.index(selection) < borrowing.index(verification)
    for command, role, artifact in (
        (path, "donor_setup", "donor"),
        (borrowing, "borrower_verification", "borrower"),
    ):
        assert command.count('"${evidence_root}/measure-doctor.py"') == (
            1 if artifact == "donor" else 2
        )
        assert (
            '"${clean_clone}/.venv/bin/python" -X pycache_prefix=/dev/null -I'
            in command
        )
        assert (
            f'"${{evidence_root}}/doctor-{artifact}-measurement.json" {role}' in command
        )
    assert 'test ! -e "${borrower_root}/runtime/runtime.tsv"' in borrowing
    assert 'test ! -e "${donor_root}/runtime/shared.json"' in borrowing
    assert 'test ! -e "${donor_root}/runtime/maintenance.lock"' in borrowing
    assert "Project verification started." in borrowing
    assert "no package-manager work is needed." in borrowing
    assert 'startswith("package_manager_")' in borrowing
    assert 'borrower.rglob("package-output.log")' in borrowing
    assert 'borrower / "runtime/managed"' in borrowing
    assert "Project verification completed." in borrowing
    assert '"runtime_ready", "storage_ready"' in borrowing
    assert "admit_direct_qualification(project, reference)" in borrowing
    assert "receipts[0].qualification_id != receipts[1].qualification_id" in borrowing
    for suffix in ("namespace.tsv", "sha256"):
        for after in ("preview", "after"):
            assert (
                f'cmp "${{evidence_root}}/donor-before.{suffix}" '
                f'"${{evidence_root}}/donor-{after}.{suffix}"'
            ) in borrowing
    assert "no borrower scientific Run" in borrowing
    upload = _named_step(job, "Upload managed golden-path evidence")
    assert _expression(upload["if"]) == "always()"
    assert upload["with"]["include-hidden-files"] is True
    assert upload["with"]["if-no-files-found"] == "error"
    assert "project/runtime/profiles" in upload["with"]["path"]
    for artifact in (
        "*.sha256",
        "doctor-*-measurement.json",
        "borrower-verification.json",
        "project/runtime/shared.json",
        "project/runtime/maintenance.lock",
        "borrower/logs",
        "borrower/runtime/runtime.tsv",
        "borrower/runtime/maintenance.lock",
        "borrower/runtime/.emrys-storage-qualification",
    ):
        assert f"emrys-managed-golden/{artifact}" in upload["with"]["path"]
    assert "borrower/runtime/managed" not in upload["with"]["path"]


def test_managed_native_containment_requires_the_provisioned_tool() -> None:
    job = _workflow_jobs()["managed-golden-path"]
    step = _named_step(
        job, "Verify Task descendant containment with the selected samtools"
    )
    names = [item.get("name") for item in job["steps"]]
    assert (
        names.index("Seal the completed donor and verify a separate borrower")
        < names.index(step["name"])
        < names.index("Require the clean clone to remain unchanged")
    )
    command = step["run"]
    assert 'test -x "${EMRYS_TEST_SAMTOOLS}"' in command
    assert '/project/runtime/managed/.pixi/envs/native/bin/samtools"' in command
    assert "test_task.py -k subreaper" in command
    assert '--junitxml="${EMRYS_TEST_NATIVE_EVIDENCE}/tests.xml"' in command
    assert 'startswith("test_task_subreaper_real_canonical_")' in command
    assert "assert len(cases) == 4" in command
    assert 'for tag in ("skipped", "failure", "error")' in command
    assert "uv sync" not in command and "pixi install" not in command
    assert (
        "emrys-managed-golden/native-containment"
        in _named_step(job, "Upload managed golden-path evidence")["with"]["path"]
    )


def _doctor_measurement_source() -> str:
    prepare = _named_step(
        _workflow_jobs()["managed-golden-path"],
        "Prepare a clean clone, environment, and synthetic Project",
    )["run"]
    return prepare.split("cat > \"${evidence_root}/measure-doctor.py\" <<'PY'\n", 1)[
        1
    ].split("\nPY\n", 1)[0]


def _doctor_measurement_driver() -> dict[str, Any]:
    namespace: dict[str, Any] = {"__name__": "ci_doctor_measurement"}
    exec(compile(_doctor_measurement_source(), str(WORKFLOW_PATH), "exec"), namespace)
    return namespace


def test_doctor_read_measurement_returns_the_exact_object_once() -> None:
    driver = _doctor_measurement_driver()
    calls, counters = [], {}
    returned = (b"contents", object())

    def read(*args, **kwargs):
        calls.append((args, kwargs))
        return returned

    # An unavailable clock leaves timing unknown and does not change the read.
    driver["clock"] = lambda: None
    observed = driver["read_observer"](read, counters)
    assert observed("path", "Fixture", nonempty=False) is returned
    assert calls == [(("path", "Fixture"), {"nonempty": False})]
    assert counters["bytes"]["elapsed_seconds"] is None
    assert counters["bytes"]["completed_bytes"] == len(returned[0])


@pytest.mark.parametrize("failure", [None, SystemExit(2), KeyboardInterrupt()])
def test_doctor_measurement_preserves_public_dispatch_and_owner_reads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, failure: BaseException | None
) -> None:
    from emrys.libraries import installed_package_identity as package
    from emrys.libraries.validation import inputs

    driver = _doctor_measurement_driver()
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    project = tmp_path / "project"
    project.mkdir()
    source = project / "input"
    source.write_bytes(b"scientific input\n")
    before = (source.read_bytes(), source.stat().st_mtime_ns)
    original_read, original_package = inputs._read_file, package._read_regular_file
    output = tmp_path / "measurement.json"
    calls = []

    def public(module, **options):
        calls.append((module, options, tuple(sys.argv)))
        # Imported public aliases still reach their defining module's read owner.
        assert inputs.read_bytes(source, "Fixture") == before[0]
        inputs.sha256_with_identity(source, "Fixture")
        assert inputs.read_suffix_with_identity(source, "Fixture", 4)[0] == b"put\n"
        assert package._read_regular_file(source, source.stat()) == before[0]
        if failure is not None:
            raise failure

    monkeypatch.setattr(driver["runpy"], "run_module", public)
    previous_argv = sys.argv
    if failure is None:
        driver["measure"](
            output, "borrower_verification", ["doctor", "--repair", "--execute"]
        )
    else:
        with pytest.raises(type(failure)) as caught:
            driver["measure"](
                output, "borrower_verification", ["doctor", "--repair", "--execute"]
            )
        assert caught.value is failure
    assert calls == [
        (
            "emrys",
            {"run_name": "__main__", "alter_sys": True},
            ("emrys", "doctor", "--repair", "--execute"),
        )
    ]
    assert inputs._read_file is original_read
    assert package._read_regular_file is original_package
    assert sys.argv is previous_argv
    assert list(project.iterdir()) == [source]
    assert (source.read_bytes(), source.stat().st_mtime_ns) == before
    measured = json.loads(output.read_text())
    assert measured["checkout_sha"] == "a" * 40
    assert str(tmp_path) not in output.read_text()
    assert measured["exit_status"] == (
        0 if failure is None else 2 if isinstance(failure, SystemExit) else None
    )
    assert measured["exception_type"] == (
        None if failure is None else type(failure).__name__
    )
    for mode, count in (
        ("bytes", len(before[0])),
        ("digest", len(before[0])),
        ("suffix", 4),
        ("package_payload", len(before[0])),
    ):
        row = measured["targeted_reads"][mode]
        assert row["completed_calls"] == 1
        assert row["completed_bytes"] == count
        assert row["failed_calls"] == 0
        assert row["elapsed_seconds"] >= 0


@pytest.mark.parametrize("failure", [OSError("unavailable"), KeyboardInterrupt()])
def test_doctor_measurement_keeps_one_failed_read_and_unknown_partial_bytes(
    failure: BaseException,
) -> None:
    driver = _doctor_measurement_driver()
    calls, counters = [], {}

    def read(*args, **kwargs):
        calls.append((args, kwargs))
        raise failure

    observed = driver["read_observer"](read, counters)
    with pytest.raises(type(failure)) as caught:
        observed("input", "Fixture", digest_only=True)
    assert caught.value is failure
    assert calls == [(("input", "Fixture"), {"digest_only": True})]
    row = counters["digest"]
    assert row["completed_calls"] == row["completed_bytes"] == 0
    assert row["failed_calls"] == 1
    assert row["failed_partial_bytes"] is None


def test_doctor_measurement_output_failure_does_not_replace_command_exit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    driver = _doctor_measurement_driver()
    existing = tmp_path / "measurement.json"
    existing.write_bytes(b"retained")
    failure = SystemExit(7)

    def public(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr(driver["runpy"], "run_module", public)
    with pytest.raises(SystemExit) as caught:
        driver["measure"](existing, "donor_setup", ["doctor", "--repair", "--execute"])
    assert caught.value is failure
    assert existing.read_bytes() == b"retained"
    assert "Doctor measurement unavailable: FileExistsError" in capsys.readouterr().err


def test_doctor_measurement_uses_real_controlled_public_parser(tmp_path: Path) -> None:
    try:
        importlib.metadata.distribution("emrys-rna-workflow")
    except importlib.metadata.PackageNotFoundError:
        pytest.skip("requires the installed EMRYS environment used by CI")
    script, output = tmp_path / "measure.py", tmp_path / "measurement.json"
    script.write_text(_doctor_measurement_source())
    result = subprocess.run(
        (
            sys.executable,
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            str(script),
            str(output),
            "donor_setup",
            "doctor",
            "--execute",
        ),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "--execute requires --repair" in result.stderr
    measured = json.loads(output.read_text())
    assert measured["exit_status"] == 2
    assert measured["exception_type"] == "SystemExit"
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "measure.py",
        "measurement.json",
    ]


def test_synthetic_evidence_is_always_uploaded_with_hidden_state() -> None:
    job = _workflow_jobs()["synthetic-e2e"]
    upload_names = (
        "Upload retained 130-pair evidence",
        "Upload retained 100,000-pair evidence",
        "Upload shared runtime and Slurm evidence",
    )
    for name in upload_names:
        step = _named_step(job, name)
        assert "always()" in _expression(step["if"])
        assert step["continue-on-error"] is True
        assert step["uses"] == (
            "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02"
        )
        assert step["with"]["if-no-files-found"] == "error"
        assert step["with"]["include-hidden-files"] is True
        assert step["with"]["retention-days"] == 14

    final = _named_step(
        job, "Require every selected synthetic lane and evidence upload to pass"
    )
    assert "steps.synthetic-130.outcome" in final["env"]["OUTCOME_130"]
    assert "steps.synthetic-100000.outcome" in final["env"]["OUTCOME_100000"]
    assert "UPLOAD_INFRASTRUCTURE" in final["run"]


def test_ci_slurm_setup_is_guarded_real_and_diagnostic() -> None:
    script = SLURM_SETUP_PATH.read_text(encoding="utf-8")
    assert "GITHUB_ACTIONS" in script
    assert "AuthType=auth/munge" in script
    assert "ProctrackType=proctrack/linuxproc" in script
    assert "TaskPlugin=task/none" in script
    assert "PartitionName=emrys-ci" in script
    assert "node_record=\"${node_probe%%$'\\n'*}\"" in script
    assert "node_probe%% UpTime=" not in script
    assert "scontrol ping" in script
    assert '[[ "$state" =~ ^[[:space:]]*idle[[:space:]]*$ ]]' in script
    assert "idle([*~+#-])?" not in script
    assert "single-node CI Slurm partition did not become idle" in script
    assert "journalctl" in script
    assert "slurmdbd" not in script
    assert "mariadb" not in script


def test_python311_shard_receipts_round_trip_outside_source_checkout() -> None:
    jobs = _workflow_jobs()
    shard_job = jobs["python311-full-shards"]
    aggregate_job = jobs["python311-full"]

    run_step = _named_step(
        shard_job, "Run complete-suite shard with live slow-test timings"
    )
    run_command = run_step["run"]
    assert '--repo-root "${GITHUB_WORKSPACE}"' in run_command
    assert f'--receipt "{SHELL_RECEIPT_ROOT}/python-test-shard-' in run_command
    assert "${GITHUB_WORKSPACE}/.test-shards" not in run_command

    upload_step = _named_step(shard_job, "Upload selection receipt")
    upload_inputs = upload_step["with"]
    assert upload_inputs["path"] == (f"{ACTION_RECEIPT_ROOT}/python-test-shard-*.json")
    assert upload_inputs["if-no-files-found"] == "error"

    download_step = _named_step(
        aggregate_job, "Download every Python 3.11 shard receipt"
    )
    download_inputs = download_step["with"]
    assert download_inputs["pattern"] == "python311-test-shard-*"
    assert download_inputs["path"] == f"{ACTION_RECEIPT_ROOT}/merged"
    assert download_inputs["merge-multiple"] is True

    verify_step = _named_step(
        aggregate_job, "Verify complete and disjoint shard receipts"
    )
    assert f'--receipt-dir "{SHELL_RECEIPT_ROOT}/merged"' in verify_step["run"]


def _namespace_experiment_checks(tmp_path):
    from emrys.evidence.runtime_availability._runtime_model import RuntimeCheck

    library = tmp_path / "library"
    library.mkdir()
    launcher = tmp_path / "Rscript"
    launcher.write_text(
        f"#!{sys.executable}\n"
        "import os, pathlib, sys, time\n"
        "if sys.argv[-1] == '--version':\n"
        " print('1.2.3'); sys.exit(0)\n"
        "name, root = sys.argv[-2], pathlib.Path(sys.argv[-1])\n"
        "(root / (name + '.pid')).write_text(str(os.getpid()))\n"
        "if name.startswith('slow'): time.sleep(30)\n"
        "if name == 'exit124': sys.exit(124)\n"
        "if name == 'loader':\n"
        " print('fixture namespace dependency unavailable', file=sys.stderr); sys.exit(42)\n"
        "time.sleep(0.03)\n"
        "version = '9.0.0' if (root / 'drift').exists() else '1.2.3'\n"
        "print(version + '::emrys-root-utf8-hex::' + str(root / name).encode().hex(), end='')\n"
    )
    launcher.chmod(0o755)

    def check(name):
        return RuntimeCheck(name, "r_namespace", name, (str(launcher),), r"^1[.]2[.]3$")

    environment = {"EMRYS_LOCAL_PILOT_R": "1", "EMRYS_RENV_LIBRARY": str(library)}
    return library, check, environment


def _observation_semantics(values):
    import re

    return [
        (
            item.check,
            item.status,
            item.observed,
            item.resolved_path,
            re.sub(
                r"elapsed_seconds=[0-9]+[.][0-9]+",
                "elapsed_seconds=<observed>",
                item.detail,
            ),
        )
        for item in values
    ]


def test_namespace_experiment_preserves_calls_order_failures_and_fresh_boundaries(
    tmp_path,
):
    import threading
    from emrys.evidence.runtime_availability import _probes, inspector
    from emrys.evidence.runtime_availability._runtime_model import RuntimeCheck

    driver = _doctor_measurement_driver()
    library, check, environment = _namespace_experiment_checks(tmp_path)
    path = RuntimeCheck(
        "path", "path_visibility", str(library), ("directory_readable",), ".*"
    )
    launcher = Path(check("first").probe_args[0])
    java = tmp_path / "java-home/bin/java"
    java.parent.mkdir(parents=True)
    java.write_bytes(launcher.read_bytes())
    java.chmod(0o755)
    checks = (
        path,
        RuntimeCheck("java", "tool_version", str(java), ("--version",), r"1[.]2[.]3"),
        check("first"),
        check("loader"),
        check("third"),
        RuntimeCheck(
            "gatk", "tool_version", str(launcher), ("--version",), r"1[.]2[.]3"
        ),
        path,
        check("last"),
    )
    original_popen, original_checks, original_probes = (
        subprocess.Popen,
        inspector.run_checks,
        _probes.PROBES,
    )
    sequences = []
    for workers in (1, 2):
        calls, mutex = [], threading.Lock()

        def runner(argv, stdin, env, timeout):
            with mutex:
                calls.append((tuple(argv), stdin, dict(env), timeout))
            return _probes._run_command(argv, stdin, env, timeout)

        with driver["namespace_concurrency"](workers, observe=True) as metrics:
            before = inspector.run_checks(
                checks, environment=environment, command_runner=runner
            )
            (library / "drift").write_bytes(b"changed between admissions")
            after = inspector.run_checks(
                checks, environment=environment, command_runner=runner
            )
        (library / "drift").unlink()
        assert len(calls) == 12
        assert all(
            call[3] == (30 if call[0][-1] == "--version" else 120) for call in calls
        )
        assert all(
            item.status == "fail"
            for item in after
            if item.check.check_type == "r_namespace"
        )
        assert [item.check for item in before] == list(checks)
        assert len(metrics["admissions"]) == 2
        assert metrics["observation_failures"] == 0
        if workers == 2:
            assert metrics["r_launches"] == 8
            assert metrics["maximum_active_r_children"] == 2
        sequences.append(
            (
                _observation_semantics(before),
                _observation_semantics(after),
                sorted(calls),
            )
        )
        assert subprocess.Popen is original_popen
        assert inspector.run_checks is original_checks
        assert _probes.PROBES is original_probes
    assert sequences[0] == sequences[1]


@pytest.mark.parametrize("workers", (1, 2))
def test_namespace_experiment_retains_real_timeout_and_exit124(tmp_path, workers):
    from emrys.evidence.runtime_availability import _probes, inspector

    driver = _doctor_measurement_driver()
    library, check, environment = _namespace_experiment_checks(tmp_path)
    calls = []

    def shortened_timeout(argv, stdin, env, timeout):
        calls.append(timeout)
        # Exercise the real timeout/kill/wait path without a two-minute fixture.
        return _probes._run_command(argv, stdin, env, 0.15)

    with driver["namespace_concurrency"](workers):
        results = inspector.run_checks(
            (check("slow_timeout"), check("exit124")),
            environment=environment,
            command_runner=shortened_timeout,
        )
    assert calls == [120, 120]
    assert "probe timed out" in results[0].detail
    assert "exit_status=124" in results[1].detail
    assert "timed out" not in results[1].detail
    assert all(item.status == "fail" for item in results)
    import psutil

    for path in library.glob("*.pid"):
        assert not psutil.pid_exists(int(path.read_text()))


@pytest.mark.parametrize("kill_error", (False, True))
def test_namespace_experiment_interrupt_stops_both_children_and_queued_launch(
    tmp_path, monkeypatch, kill_error
):
    import os
    import signal
    import threading
    import time
    import psutil
    from emrys.evidence.runtime_availability import _probes, inspector

    driver = _doctor_measurement_driver()
    library, check, environment = _namespace_experiment_checks(tmp_path)
    attempts = []
    if kill_error:

        class KillFailure(subprocess.Popen):
            def kill(self):
                super().kill()
                attempts.append(self.pid)
                if len(attempts) == 1:
                    raise OSError("fixture observer cleanup fault after actual kill")

        monkeypatch.setattr(subprocess, "Popen", KillFailure)
    original_popen, original_checks, original_probes = (
        subprocess.Popen,
        inspector.run_checks,
        _probes.PROBES,
    )
    interrupted = threading.Event()

    def interrupt_when_running():
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if all((library / f"slow_{name}.pid").exists() for name in ("one", "two")):
                interrupted.set()
                os.kill(os.getpid(), signal.SIGINT)
                return
            time.sleep(0.01)

    sender = threading.Thread(target=interrupt_when_running)
    sender.start()
    started = time.monotonic()
    with pytest.raises(KeyboardInterrupt):
        with driver["namespace_concurrency"](2) as metrics:
            inspector.run_checks(
                (check("slow_one"), check("slow_two"), check("queued")),
                environment=environment,
            )
    sender.join(timeout=6)
    assert interrupted.is_set()
    assert metrics["cleanup_failures"] == int(kill_error)
    if kill_error:
        assert len(attempts) == 2
    assert time.monotonic() - started < 5
    assert not (library / "queued.pid").exists()
    assert all(
        not psutil.pid_exists(int(path.read_text())) for path in library.glob("*.pid")
    )
    assert subprocess.Popen is original_popen
    assert inspector.run_checks is original_checks
    assert _probes.PROBES is original_probes


def test_namespace_experiment_launch_failure_retains_other_observations(
    tmp_path, monkeypatch
):
    import psutil
    from emrys.evidence.runtime_availability import inspector

    driver = _doctor_measurement_driver()
    library, check, environment = _namespace_experiment_checks(tmp_path)
    original_popen = subprocess.Popen

    class LaunchFailure(original_popen):
        def __init__(self, argv, *args, **kwargs):
            if argv[-2] == "launch_failure":
                raise OSError("fixture launch refusal")
            super().__init__(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", LaunchFailure)
    with driver["namespace_concurrency"](2):
        results = inspector.run_checks(
            (check("first"), check("launch_failure"), check("last")),
            environment=environment,
        )
    assert [item.status for item in results] == ["pass", "fail", "pass"]
    assert "fixture launch refusal" in results[1].observed
    assert "exit_status=127" in results[1].detail
    assert all(
        not psutil.pid_exists(int(path.read_text())) for path in library.glob("*.pid")
    )
    assert subprocess.Popen is LaunchFailure


@pytest.mark.skipif(
    sys.platform != "linux", reason="requires hosted Linux process visibility"
)
def test_doctor_process_tree_sampler_observes_simultaneous_descendants():
    driver = _doctor_measurement_driver()
    sampler = driver["ProcessTreeSamples"]()
    sampler.thread.start()
    try:
        command = [
            sys.executable,
            "-c",
            "import time; data = bytearray(2000000); time.sleep(.3)",
        ]
        with subprocess.Popen(command) as first, subprocess.Popen(command) as second:
            assert first.wait(timeout=5) == second.wait(timeout=5) == 0
    finally:
        values = sampler.finish()
    assert values["samples"] >= 2
    assert values["maximum_sampled_descendants"] >= 2
    assert (
        values["peak_sampled_rss_bytes"]
        >= values["peak_sampled_descendant_rss_bytes"]
        > 0
    )
    assert len(values["processes"]) >= 3
    assert "short-lived" in values["scope"]
    assert not sampler.thread.is_alive()


@pytest.mark.skipif(
    sys.platform != "linux", reason="CI process-group supervisor is Linux-only"
)
@pytest.mark.parametrize("failure", ("timeout", "surviving_child"))
def test_doctor_experiment_supervisor_rejects_and_cleans_failed_groups(
    tmp_path, failure
):
    import psutil

    driver = _doctor_measurement_driver()
    pidfile = tmp_path / "child.pid"
    command = [
        sys.executable,
        "-c",
        "import pathlib, subprocess, sys, time; "
        "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); "
        f"pathlib.Path({str(pidfile)!r}).write_text(str(p.pid)); "
        + ("time.sleep(30)" if failure == "timeout" else "time.sleep(.05)"),
    ]
    with pytest.raises(
        subprocess.TimeoutExpired if failure == "timeout" else RuntimeError
    ):
        driver["supervised_trial"](command, tmp_path / "trial.log", timeout_seconds=0.2)
    child = (
        psutil.Process(int(pidfile.read_text()))
        if psutil.pid_exists(int(pidfile.read_text()))
        else None
    )
    if child is not None:
        assert child.status() == psutil.STATUS_ZOMBIE


def test_doctor_experiment_keeps_canonical_baseline_and_existing_ci_selection():
    reuse = _named_step(
        _workflow_jobs()["managed-golden-path"],
        "Seal the completed donor and verify a separate borrower",
    )["run"]
    assert reuse.index('"borrower-verification.json"') < reuse.index(
        '--compare "${evidence_root}"'
    )
    assert "snapshot_donor comparison" in reuse
    assert (
        "donor-comparison.namespace.tsv" in reuse and "donor-comparison.sha256" in reuse
    )
    source = _doctor_measurement_source()
    assert "enumerate((1, 2, 2, 1), 1)" in source
    assert "compare four complete steady-ready" in source.lower()
    assert "snapshot() == frozen" in source
    assert "observe=sample_tree" in source
    assert (
        "github.event_name" in reuse and "inputs.managed_runtime_golden_path" in reuse
    )


def test_doctor_measurement_concurrent_counter_updates_do_not_serialize_reads():
    import threading
    from concurrent.futures import ThreadPoolExecutor

    driver = _doctor_measurement_driver()
    gate = threading.Barrier(2, timeout=5)
    returned, counters = (b"shared", object()), {}

    def read(*args, **kwargs):
        gate.wait()
        return returned

    observed = driver["read_observer"](read, counters)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(observed, ("one", "two")))
    assert all(result is returned for result in results)
    assert counters["bytes"]["completed_calls"] == 2
    assert counters["bytes"]["completed_bytes"] == 12


@pytest.mark.parametrize(
    "mutation",
    (
        None,
        "same_bytes_replacement",
        "mtime",
        "root_namespace",
        "unavailable_elapsed",
        "nonfinite_elapsed",
    ),
)
def test_doctor_comparison_rejects_no_write_drift_and_keeps_whole_argv(
    tmp_path, mutation
):
    import os

    driver = _doctor_measurement_driver()
    driver["__file__"] = "fixture-driver.py"
    borrower = tmp_path / "borrower"
    borrower.mkdir()
    source = borrower / "input"
    source.write_bytes(b"retained bytes")
    calls = []

    def trial(command, output):
        calls.append(command)
        assert command[-3:] == ["doctor", "--project", str(borrower)]
        marker = command.index("--trial")
        workers = int(command[marker + 3])
        Path(command[marker + 1]).write_text(
            json.dumps(
                {
                    "exit_status": 0,
                    "elapsed_seconds": {
                        "unavailable_elapsed": None,
                        "nonfinite_elapsed": float("inf"),
                    }.get(mutation, 1.0),
                    "process_tree": {"samples": 1},
                    "namespace_execution": {
                        "admissions": [
                            [
                                {
                                    "detail": f"elapsed_seconds={len(calls)}.000",
                                    "observed": "1.2.3",
                                }
                            ]
                        ],
                        "observation_failures": 0,
                        "cleanup_failures": 0,
                        "r_launches": 2 if workers == 2 else 0,
                        "maximum_active_r_children": workers,
                    },
                }
            )
        )
        if mutation == "same_bytes_replacement":
            replacement = tmp_path / "replacement"
            replacement.write_bytes(source.read_bytes())
            os.replace(replacement, source)
        elif mutation == "root_namespace":
            temporary = borrower / "temporary"
            temporary.write_bytes(b"removed before the final snapshot")
            temporary.unlink()
        elif mutation == "mtime":
            state = source.stat()
            os.utime(source, ns=(state.st_atime_ns, state.st_mtime_ns + 1_000_000_000))

    driver["supervised_trial"] = trial
    if mutation is not None:
        with pytest.raises(AssertionError):
            driver["compare_borrower"](tmp_path)
        assert len(calls) == 1
        assert not (tmp_path / "doctor-comparison-measurement.json").exists()
    else:
        driver["compare_borrower"](tmp_path)
        assert [int(call[call.index("--trial") + 3]) for call in calls] == [1, 2, 2, 1]
        summary = json.loads(
            (tmp_path / "doctor-comparison-measurement.json").read_text()
        )
        assert summary["matching_ordered_observations"] is True
        assert len(summary["trials"]) == 4


def test_namespace_observation_failure_keeps_actual_check_result(tmp_path):
    from emrys.evidence.runtime_availability import inspector

    driver = _doctor_measurement_driver()
    _library, check, environment = _namespace_experiment_checks(tmp_path)

    def unavailable(_value):
        raise ValueError("fixture observation fault")

    driver["asdict"] = unavailable
    with driver["namespace_concurrency"](2, observe=True) as metrics:
        results = inspector.run_checks((check("valid"),), environment=environment)
    assert results[0].status == "pass"
    assert metrics["admissions"] == []
    assert metrics["observation_failures"] == 1


def test_doctor_supervisor_does_not_signal_when_child_ownership_is_lost(
    tmp_path, monkeypatch
):
    import os
    import signal

    driver = _doctor_measurement_driver()
    calls = []

    class Process:
        pid = 321

        def __init__(self, *args, **kwargs):
            pass

        def wait(self, **kwargs):
            calls.append("wait")
            return 0

    def lost(*args):
        raise ChildProcessError("fixture ECHILD")

    monkeypatch.setattr(subprocess, "Popen", Process)
    monkeypatch.setattr(os, "waitid", lost, raising=False)
    for name in ("P_PID", "WEXITED", "WNOWAIT", "WNOHANG"):
        monkeypatch.setattr(os, name, 1, raising=False)
    monkeypatch.setattr(signal, "getsignal", lambda _signum: signal.SIG_DFL)
    monkeypatch.setattr(os, "killpg", lambda *args: calls.append("signal"))
    with pytest.raises(ChildProcessError):
        driver["supervised_trial"](["fixture"], tmp_path / "trial.log")
    assert calls == []


@pytest.mark.parametrize("status", (None, 0, 2))
def test_namespace_guard_checks_successful_system_exit_and_preserves_failure(status):
    driver = _doctor_measurement_driver()
    child = None
    expected = RuntimeError if status in (None, 0) else SystemExit
    failure = SystemExit(status)
    try:
        with pytest.raises(expected) as caught:
            with driver["namespace_concurrency"](2):
                child = subprocess.Popen([sys.executable, "-c", "pass"])
                child.wait(timeout=5)
                # Intentionally omit the Popen context exit until the outer finally.
                # Successful public dispatch also arrives as SystemExit(0).
                raise failure
        if status == 2:
            assert caught.value is failure
        else:
            assert "retained unreaped direct children" in str(caught.value)
    finally:
        if child is not None:
            child.__exit__(None, None, None)
