"""Contract tests for the GitHub Actions CI workflow."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
MANAGED_RUNTIME_ROOT = REPO_ROOT / "src" / "emrys" / "resources" / "runtime"
MANAGED_RUNTIME_LOCK_PATH = MANAGED_RUNTIME_ROOT / "pixi.lock"
MANAGED_RUNTIME_MANIFEST_PATH = MANAGED_RUNTIME_ROOT / "pixi.toml"
SLURM_SETUP_PATH = REPO_ROOT / "tests" / "tools" / "configure_ci_slurm.sh"
SHELL_RECEIPT_ROOT = "${RUNNER_TEMP}/emrys-python311-test-shards"
ACTION_RECEIPT_ROOT = "${{ runner.temp }}/emrys-python311-test-shards"
ORDINARY_JOB_IDS = (
    "workflow-lint",
    "static-wheel",
    "shell-contracts",
    "guarded-r",
    "managed-runtime-userspace",
    "managed-golden-path",
    "python314-coverage-shards",
    "python314-coverage",
    "python311-smoke",
)


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


def test_long_lane_triggers_are_closed_and_independently_selectable() -> None:
    triggers = _workflow_triggers()
    assert triggers["schedule"] == [
        {"cron": "17 5 * * 1-6"},
        {"cron": "17 5 * * 0"},
    ]
    inputs = triggers["workflow_dispatch"]["inputs"]
    assert set(inputs) == {"python311", "synthetic_130", "synthetic_100000"}
    for value in inputs.values():
        assert value["type"] == "boolean"
        assert value["required"] is True
        assert value["default"] is False

    jobs = _workflow_jobs()
    manual = jobs["manual-selection"]
    assert _expression(manual["if"]) == "github.event_name == 'workflow_dispatch'"
    guard = _named_step(manual, "Require at least one selected long lane")
    assert set(guard["env"]) == {
        "RUN_PYTHON311",
        "RUN_SYNTHETIC_130",
        "RUN_SYNTHETIC_100000",
    }
    assert "select at least one lane" in guard["run"]


def test_ordinary_jobs_do_not_run_for_schedules_or_manual_long_lanes() -> None:
    jobs = _workflow_jobs()
    for job_id in ORDINARY_JOB_IDS:
        condition = _expression(jobs[job_id]["if"])
        assert "github.event_name != 'workflow_dispatch'" in condition
        assert "github.event_name != 'schedule'" in condition


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
    assert "renv.lock" in authorities["run"]
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
        assert '"/usr/bin/srun"' in step["run"]
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
    native = [item["conda"] for item in lock["environments"]["native"]["packages"]["p1"]]
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
    assert "apt-get install --yes --no-install-recommends ca-certificates" in trust["run"]
    setup = _named_step(job, "Install both managed environments from the unchanged lock")
    assert setup["uses"] == (
        "prefix-dev/setup-pixi@d3f436a425481402e6a95a1d1fc10331c708cd9e"
    )
    assert setup["with"]["environments"] == "native r"
    assert setup["with"]["locked"] is True
    verify = _named_step(job, "Verify locked tools in this container userspace")
    assert "src/emrys/resources/runtime/pixi.lock" in verify["run"]
    assert 'test -e "${r_prefix}/lib/libxml2.so"' in verify["run"]
    assert '"${r_prefix}/bin/pkg-config" --exists libxml-2.0' in verify["run"]
    assert 'PATH="${native_prefix}/bin" "${native_prefix}/bin/STAR" --version' in verify["run"]
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

    prepare = _named_step(job, "Prepare a clean clone, environment, and synthetic Project")
    cache = _named_step(job, "Cache managed golden-path R packages")
    journey = _named_step(job, "Repair and exercise the supported managed golden path")
    step_names = [step.get("name") for step in job["steps"]]
    assert step_names.index(prepare["name"]) < step_names.index(cache["name"])
    assert step_names.index(cache["name"]) < step_names.index(journey["name"])

    assert prepare["run"].index('cd "${clean_clone}"') < prepare["run"].index(
        '"${emrys[@]}" init synthetic'
    )
    assert cache["uses"] == (
        "actions/cache@caa296126883cff596d87d8935842f9db880ef25"
    )
    assert cache["with"]["path"] == (
        "${{ runner.temp }}/emrys-managed-golden/project/runtime/managed/renv/cache"
    )
    assert "renv.lock" in cache["with"]["key"]
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
    upload = _named_step(job, "Upload managed golden-path evidence")
    assert _expression(upload["if"]) == "always()"
    assert upload["with"]["include-hidden-files"] is True
    assert upload["with"]["if-no-files-found"] == "error"
    assert "project/runtime/profiles" in upload["with"]["path"]


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
