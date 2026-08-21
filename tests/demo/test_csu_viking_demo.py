from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
DRIVER_PATH = REPO_ROOT / "scripts/demo/csu_viking/demo_driver.py"
PROXY_PATH = REPO_ROOT / "scripts/demo/csu_viking/star_reuse.py"
ACTIVATE_PATH = REPO_ROOT / "scripts/demo/csu_viking/activate.sh"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


driver = _load("norad_csu_demo_driver", DRIVER_PATH)
proxy = _load("norad_csu_demo_star_proxy", PROXY_PATH)


def test_driver_and_proxy_use_the_same_index_roster() -> None:
    assert set(driver.INDEX_MEMBERS) == set(proxy.REQUIRED_INDEX_MEMBERS)


def _executable(path: Path, content: str = "#!/bin/sh\nexit 0\n") -> Path:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path


def _write_source_index(index: Path, fasta: Path, gtf: Path) -> None:
    index.mkdir()
    parameters = (
        "### STAR --runMode genomeGenerate\n"
        f"genomeFastaFiles {fasta}\n"
        f"sjdbGTFfile {gtf}\n"
        "sjdbOverhang 149\n"
        "genomeSAindexNbases 14\n"
        "versionGenome 2.7.11b\n"
    )
    for name in proxy.REQUIRED_INDEX_MEMBERS:
        data = parameters if name == "genomeParameters.txt" else f"{name}\n"
        (index / name).write_text(data, encoding="utf-8")
    (index / "Log.out").write_text("not admitted\n", encoding="utf-8")


def _runtime(path: Path, star: str = "/real/STAR") -> None:
    rows = [
        [
            "check_id",
            "check_type",
            "runtime_context",
            "required",
            "target",
            "probe_args",
            "expected",
            "description",
        ],
        [
            "star",
            "tool_version",
            "local",
            "true",
            star,
            '["--version"]',
            "^2[.]7[.]11b$",
            "STAR aligner and genome-index builder",
        ],
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, delimiter="\t", lineterminator="\n").writerows(rows)


def _config(tmp_path: Path):
    seed = tmp_path / "seed"
    reference = seed / "inputs/reference"
    reference.mkdir(parents=True)
    fasta = reference / "genome.fa"
    gtf = reference / "annotation.gtf"
    fasta.write_text(">1\nA\n", encoding="utf-8")
    gtf.write_text("1\tt\texon\t1\t1\t.\t+\t.\tgene_id \"g\";\n", encoding="utf-8")
    (reference / "genome.fa.fai").write_text("1\t1\t3\t1\t2\n", encoding="utf-8")
    (reference / "genome.dict").write_text("@HD\tVN:1.6\n", encoding="utf-8")
    (seed / "request.yaml").write_text(
        "label: original\nreference:\n  fasta: inputs/reference/genome.fa\n"
        "  gtf: inputs/reference/annotation.gtf\n",
        encoding="utf-8",
    )
    (seed / "samples.tsv").write_text("sample_id\nS1\n", encoding="utf-8")
    (seed / "partitions.tsv").write_text(
        "partition_id\tselector_type\tselector_value\n1\tregion\t1\n",
        encoding="utf-8",
    )
    _runtime(seed / "runtime.selected.tsv")

    source_run = tmp_path / "runs/run-source"
    source_index = source_run / "results/star/novogene_reference/index"
    source_index.parent.mkdir(parents=True)
    _write_source_index(source_index, fasta, gtf)
    (source_run / "contract").mkdir()
    (source_run / "contract/artifact_inventory.tsv").write_text(
        "artifact\n", encoding="utf-8"
    )
    report = source_run / "products/report/run-source"
    report.mkdir(parents=True)
    for suffix in ("scientific_report.html", "evidence_report.html"):
        (report / f"run-source.{suffix}").write_text("<html/>\n", encoding="utf-8")
    attempt = source_run / "attempts/workflow-source"
    attempt.mkdir(parents=True)
    (attempt / "attempt-receipt.json").write_text(
        json.dumps(
            {
                "schema_version": "norad.attempt-receipt.v1",
                "run_id": "run-source",
                "workflow_attempt_id": "workflow-source",
                "status": "succeeded",
                "local_pipeline_complete": True,
                "snakemake_exit_code": 0,
                "termination_signal": None,
                "blockers": [],
                "verified_tasks": [{} for _ in range(driver.SOURCE_OWNER_JOBS)],
                "reporting_completion_records": {
                    name: {} for name in driver.SOURCE_REPORTING_KINDS
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    real_star = _executable(tmp_path / "STAR", "#!/bin/sh\nprintf '2.7.11b\\n'\n")
    return driver.Config(
        repo=REPO_ROOT,
        python=Path("/usr/bin/python3"),
        session="test-session",
        seed_input=seed,
        source_run=source_run,
        source_index=source_index,
        real_star=real_star,
        input_dir=tmp_path / "demo-input",
        workspace_parent=tmp_path / "demo-workspace-parent",
        workspace=tmp_path / "demo-workspace-parent/workspace",
        log_dir=tmp_path / "logs",
        state_file=tmp_path / "state.json",
        job_env_file=tmp_path / "job.env",
        account="viking-users",
        partition="long",
        qos="normal",
        nodelist="node002",
        qualification_partition="short",
        scratch_parent=tmp_path,
    )


def test_activation_is_explicit_and_selects_a_shell_function(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    activation = checkout / "scripts/demo/csu_viking/activate.sh"
    activation.parent.mkdir(parents=True)
    activation.write_bytes(ACTIVATE_PATH.read_bytes())
    (checkout / ".venv/bin").mkdir(parents=True)
    _executable(checkout / ".venv/bin/python")
    command = (
        f"unset NORAD_DEMO_ACTIVE; source {activation}; "
        "printf 'TYPE=%s\\n' \"$(type -t norad)\""
    )
    result = subprocess.run(
        ("bash", "--noprofile", "--norc", "-c", command),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "NORAD CSU VIKING DEMO MODE" in result.stdout
    assert "TYPE=function" in result.stdout


def test_proxy_links_only_the_exact_roster(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    destination = workspace / "runs/run/results/star/ref/.index.tmp"
    destination.mkdir(parents=True)
    fasta = tmp_path / "genome.fa"
    gtf = tmp_path / "genome.gtf"
    fasta.write_text(">1\nA\n", encoding="utf-8")
    gtf.write_text("gtf\n", encoding="utf-8")
    source = tmp_path / "source-index"
    _write_source_index(source, fasta, gtf)
    before = {path.name: path.read_bytes() for path in source.iterdir()}

    proxy.populate_index(
        source_index=source,
        destination=destination,
        source_fasta=fasta,
        source_gtf=gtf,
        workspace=workspace,
    )

    assert {path.name for path in destination.iterdir()} == set(
        proxy.REQUIRED_INDEX_MEMBERS
    )
    for name in proxy.REQUIRED_INDEX_MEMBERS:
        assert os.path.samefile(source / name, destination / name)
    assert {path.name: path.read_bytes() for path in source.iterdir()} == before


def test_proxy_refuses_wrong_generation_without_writes(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    destination = workspace / "staging"
    destination.mkdir(parents=True)
    fasta = tmp_path / "genome.fa"
    gtf = tmp_path / "genome.gtf"
    fasta.write_text(">1\nA\n", encoding="utf-8")
    gtf.write_text("gtf\n", encoding="utf-8")
    source = tmp_path / "source"
    _write_source_index(source, fasta, gtf)
    star = _executable(tmp_path / "STAR")
    arguments = [
        "--real-star",
        str(star),
        "--real-star-sha256",
        hashlib.sha256(star.read_bytes()).hexdigest(),
        "--source-index",
        str(source),
        "--source-fasta",
        str(fasta),
        "--source-gtf",
        str(gtf),
        "--workspace",
        str(workspace),
        "--expected-threads",
        "12",
        "--",
        "--runThreadN",
        "11",
        "--runMode",
        "genomeGenerate",
        "--genomeDir",
        str(destination),
        "--genomeFastaFiles",
        str(fasta),
        "--sjdbGTFfile",
        str(gtf),
        "--sjdbOverhang",
        "149",
        "--genomeSAindexNbases",
        "14",
    ]
    assert proxy.main(arguments) == 2
    assert list(destination.iterdir()) == []


def test_proxy_delegates_version_exactly(tmp_path: Path) -> None:
    star = _executable(tmp_path / "STAR", "#!/bin/sh\nprintf '2.7.11b\\n'\n")
    command = [
        "/usr/bin/python3",
        str(PROXY_PATH),
        "--real-star",
        str(star),
        "--real-star-sha256",
        hashlib.sha256(star.read_bytes()).hexdigest(),
        "--source-index",
        str(tmp_path / "unused"),
        "--source-fasta",
        str(tmp_path / "unused.fa"),
        "--source-gtf",
        str(tmp_path / "unused.gtf"),
        "--workspace",
        str(tmp_path / "unused-workspace"),
        "--expected-threads",
        "12",
        "--",
        "--version",
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    assert result.returncode == 0
    assert result.stdout == "2.7.11b\n"
    assert result.stderr == ""


def test_selected_executable_accepts_one_stable_symlink(tmp_path: Path) -> None:
    target = _executable(tmp_path / "python-real")
    selected = tmp_path / "python"
    selected.symlink_to(target)
    assert driver._selected_executable(selected, "test Python") == selected


def test_source_preflight_requires_latest_success_receipt(tmp_path: Path) -> None:
    config = _config(tmp_path)
    receipt = config.source_run / "attempts/workflow-source/attempt-receipt.json"
    value = json.loads(receipt.read_text(encoding="utf-8"))
    value["status"] = "failed"
    value["local_pipeline_complete"] = False
    receipt.write_text(json.dumps(value) + "\n", encoding="utf-8")
    with pytest.raises(driver.DemoError, match="not a successful complete pipeline"):
        driver._preflight_source(config)


def test_state_rejects_a_symlink(tmp_path: Path) -> None:
    config = _config(tmp_path)
    target = tmp_path / "state-target.json"
    target.write_text("{}\n", encoding="utf-8")
    config.state_file.symlink_to(target)
    with pytest.raises(driver.DemoError, match="private real file"):
        driver._state(config)


def test_init_execute_preserves_generated_wrapper_and_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config = _config(tmp_path)

    def fake_cli(_config, *arguments):
        assert arguments[-1] == "--execute"
        config.input_dir.mkdir(mode=0o700)
        (config.input_dir / "run-in-slurm.sh").write_bytes(b"new wrapper\n")
        (config.input_dir / "run-in-slurm.sh").chmod(0o755)
        (config.input_dir / "starter-set.manifest.tsv").write_bytes(b"new manifest\n")
        for name in (
            "request.yaml",
            "samples.tsv",
            "partitions.tsv",
            "runtime.tsv",
            "norad.launcher.yaml",
            "norad.resources.yaml",
        ):
            (config.input_dir / name).write_bytes(b"starter\n")
        return subprocess.CompletedProcess(
            arguments,
            0,
            stdout=(
                f"Published matched local-pilot starter set: {config.input_dir}\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(driver, "_real_cli", fake_cli)
    driver.init_demo(config, execute=True)

    assert (config.input_dir / "run-in-slurm.sh").read_bytes() == b"new wrapper\n"
    assert (config.input_dir / "starter-set.manifest.tsv").read_bytes() == (
        b"new manifest\n"
    )
    request = (config.input_dir / "request.yaml").read_text(encoding="utf-8")
    assert "DEMO ONLY" in request
    assert f"fasta: {config.source_fasta}" in request
    assert f"gtf: {config.source_gtf}" in request
    rows = list(
        csv.DictReader(config.runtime_profile.open(encoding="utf-8"), delimiter="\t")
    )
    assert rows[0]["target"] == str(config.input_dir / "STAR.demo")
    assert (config.input_dir / "norad.launcher.yaml").read_bytes() == (
        REPO_ROOT / "configs/local_pilot_launcher.csu_viking_ev_pum1.yaml"
    ).read_bytes()
    assert config.workspace_parent.is_dir()
    assert config.log_dir.is_dir()
    assert not config.workspace.exists()
    assert driver.PASS_INIT in capsys.readouterr().out


def _initialized(config) -> None:
    config.input_dir.mkdir(mode=0o700)
    config.workspace_parent.mkdir(mode=0o700)
    config.log_dir.mkdir(mode=0o700)
    _executable(config.wrapper)
    config.runtime_profile.write_text("runtime\n", encoding="utf-8")
    for name in (
        "request.yaml",
        "samples.tsv",
        "partitions.tsv",
        "norad.launcher.yaml",
        "norad.resources.yaml",
        "STAR.demo",
    ):
        path = config.input_dir / name
        if name == "STAR.demo":
            _executable(path)
        else:
            path.write_text(f"{name}\n", encoding="utf-8")
    driver._write_state(config, initialized=True)


def test_storage_execute_submits_compute_without_memory_then_finalizes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(tmp_path)
    _initialized(config)
    capture = tmp_path / "sbatch.args"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    sbatch = _executable(
        fake_bin / "sbatch",
        """#!/bin/bash
set -eu
printf '%s\n' "$@" > "$CAPTURE"
for arg in "$@"; do
  case "$arg" in
    --output=*) out=${arg#--output=} ;;
    --error=*) err=${arg#--error=} ;;
  esac
done
out=${out//%j/700123}
err=${err//%j/700123}
printf 'Published compute qualification receipt: receipt.json\n' > "$out"
: > "$err"
printf '700123\n'
""",
    )
    environment = os.environ.copy()
    environment["PATH"] = f"{fake_bin}:{environment.get('PATH', '')}"
    environment["CAPTURE"] = str(capture)
    monkeypatch.setattr(os, "environ", environment)
    monkeypatch.setattr(driver.shutil, "which", lambda name: str(sbatch))

    finalized: list[tuple[str, bool]] = []

    def fake_storage(_config, phase, *, execute):
        finalized.append((phase, execute))
        return subprocess.CompletedProcess(
            (),
            0,
            stdout="Published final storage qualification receipt: final.json\n",
            stderr="",
        )

    monkeypatch.setattr(driver, "_storage_cli", fake_storage)
    driver.storage_demo(config, execute=True)

    arguments = capture.read_text(encoding="utf-8").splitlines()
    assert "--wait" in arguments
    assert "--cpus-per-task=1" in arguments
    assert not any(argument.startswith("--mem") for argument in arguments)
    assert finalized == [("finalize", True)]
    assert driver._state(config)["storage_qualified"] is True


def test_workflow_dry_run_then_execution_submission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config = _config(tmp_path)
    _initialized(config)
    driver._write_state(config, storage_qualified=True)
    stdout = config.log_dir / "norad-local-pilot-800001.out"
    stderr = config.log_dir / "norad-local-pilot-800001.err"
    run_id = "run-" + "b" * 64
    receipt = tmp_path / "storage.qualified.json"
    receipt.write_text("{}\n", encoding="utf-8")
    receipt_sha = hashlib.sha256(receipt.read_bytes()).hexdigest()
    runtime_sha = hashlib.sha256(config.runtime_profile.read_bytes()).hexdigest()
    stdout.write_text(
        "Local-pilot request validation: PASS\n"
        f"Run ID: {run_id}\n"
        f"Workspace: {config.workspace}\n"
        "Source commit: " + "a" * 40 + "\n"
        f"Runtime profile SHA-256: {runtime_sha}\n"
        f"Storage qualification: {receipt}\n"
        f"Storage qualification SHA-256: {receipt_sha}\n"
        "READY: local-pilot prerequisites passed.\n"
        "Operation: execute\n"
        f"Run ID: {run_id}\n"
        f"Run root: {config.workspace}/runs/{run_id}\n"
        "Owner jobs: 73\n"
        "Dry-run complete; no workspace state was written.\n",
        encoding="utf-8",
    )
    stderr.write_text("", encoding="utf-8")
    calls: list[tuple[str, ...]] = []

    def fake_run(command, **_kwargs):
        calls.append(tuple(command))
        job_id = "800001" if "--execute" not in command else "800002"
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                f"JOB_ID={job_id}\n"
                f"OUT={config.log_dir}/norad-local-pilot-{job_id}.out\n"
                f"ERR={config.log_dir}/norad-local-pilot-{job_id}.err\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(driver, "_run", fake_run)
    monkeypatch.setattr(driver, "_wait_terminal", lambda *_args: ("COMPLETED", "0:0"))
    monkeypatch.setattr(driver, "_repo_commit", lambda _config: "a" * 40)
    driver.execute_demo(config, execute=False)
    assert driver._state(config)["workflow_dry_run"] is True
    assert driver.PASS_WORKFLOW_DRY in capsys.readouterr().out

    monkeypatch.setattr(driver, "_slurm_state", lambda _job: ("PENDING", ""))
    driver.execute_demo(config, execute=True)
    job_environment = config.job_env_file.read_text(encoding="utf-8")
    assert f"SESSION={config.session}" in job_environment
    assert "JOB_ID=800002" in job_environment
    assert f"LOG_DIR={config.log_dir}" in job_environment
    assert "--execute" in calls[-1]
    assert driver.PASS_SUBMISSION in capsys.readouterr().out
