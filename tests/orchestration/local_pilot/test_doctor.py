"""Direct contracts for the read-only local-pilot doctor."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from norad.evidence.runtime_availability.inspector import (
    RuntimeCheck,
    RuntimeInspection,
    RuntimeInspectionError,
    RuntimeObservation,
)
from norad.libraries.source_authority import (
    SourceCheckoutError,
    SourceCheckoutIdentity,
)
from norad.orchestration.local_pilot import doctor
from norad.orchestration.local_pilot.normalization import normalize_request

from tests.orchestration.local_pilot.fixture import build

REPO_ROOT = Path(__file__).resolve().parents[3]
PROFILE = REPO_ROOT / "workflow/contracts/local_cmh_v1.json"
EXAMPLE_RUNTIME = REPO_ROOT / "configs/local_pilot_runtime.example.tsv"


def _check(
    check_id: str,
    check_type: str,
    target: str,
    *,
    probe_args: tuple[str, ...],
    status: str = "pass",
) -> RuntimeObservation:
    return RuntimeObservation(
        check=RuntimeCheck(
            check_id=check_id,
            check_type=check_type,
            runtime_context="local",
            required=True,
            target=target,
            probe_args=probe_args,
            expected="expected",
            description=check_id,
        ),
        status=status,
        observed="9.25.1" if check_id == "snakemake" else "observed",
        detail="test observation",
    )


def _inspection(tmp_path: Path, *, failing: str | None = None) -> RuntimeInspection:
    tool = tmp_path / "tool"
    tool.write_bytes(b"tool\n")
    tool.chmod(0o755)
    jar = tmp_path / "picard.jar"
    jar.write_bytes(b"jar\n")
    rscript = str(tool)
    observations = [
        _check("bash", "tool_version", str(tool), probe_args=("--version",)),
        _check("python", "tool_version", sys.executable, probe_args=("--version",)),
        _check("snakemake", "tool_version", str(tool), probe_args=("--version",)),
        _check("star", "tool_version", str(tool), probe_args=("--version",)),
        _check("samtools", "tool_version", str(tool), probe_args=("--version",)),
        _check("java", "tool_version", str(tool), probe_args=("-version",)),
        _check("gatk", "tool_version", str(tool), probe_args=("--version",)),
        _check(
            "picard",
            "tool_version",
            str(tool),
            probe_args=("-jar", str(jar), "MarkDuplicates", "--version"),
        ),
        _check(
            "picard_jar",
            "path_visibility",
            str(jar),
            probe_args=("file_readable",),
        ),
        _check("bcftools", "tool_version", str(tool), probe_args=("--version",)),
        _check(
            "infer_experiment",
            "tool_version",
            str(tool),
            probe_args=("--version",),
        ),
        _check("rscript", "tool_version", rscript, probe_args=("--version",)),
        _check(
            "renv_project",
            "path_visibility",
            str(REPO_ROOT),
            probe_args=("directory_readable",),
        ),
    ]
    for check_id, package in doctor.LOCAL_PILOT_R_PACKAGES:
        observations.append(
            _check(check_id, "r_namespace", package, probe_args=(rscript,))
        )
    if failing is not None:
        index = next(
            index
            for index, observation in enumerate(observations)
            if observation.check.check_id == failing
        )
        original = observations[index]
        observations[index] = RuntimeObservation(
            check=original.check,
            status="fail",
            observed="unavailable",
            detail="missing in test",
        )
    data = b"runtime profile\n"
    return RuntimeInspection(
        profile_path=tmp_path / "runtime.tsv",
        profile_sha256=hashlib.sha256(data).hexdigest(),
        profile_bytes=data,
        runtime_context="local",
        observations=tuple(observations),
        rendered_bytes=b"rendered\n",
    )


def _ops(
    inspection: RuntimeInspection,
    *,
    source_error: SourceCheckoutError | None = None,
    environment_log: list[dict[str, str]] | None = None,
) -> doctor.DoctorOps:
    def inspect_source(root: Path, _package: Path) -> SourceCheckoutIdentity:
        if source_error is not None:
            raise source_error
        return SourceCheckoutIdentity(root=root, commit="a" * 40, clean=True)

    def inspect_runtime(
        _path: Path,
        context: str,
        environment: dict[str, str],
    ) -> RuntimeInspection:
        assert context == "local"
        if environment_log is not None:
            environment_log.append(dict(environment))
        return inspection

    return doctor.DoctorOps(
        inspect_source=inspect_source,
        normalize=normalize_request,
        inspect_runtime=inspect_runtime,
        observe_snakemake=lambda _python: doctor.SNAKEMAKE_VERSION,
    )


def test_ready_doctor_is_read_only_and_guards_renv(tmp_path: Path) -> None:
    request_root = tmp_path / "request"
    request_root.mkdir()
    request = build(request_root)
    workspace = tmp_path / "future-workspace"
    runtime = tmp_path / "runtime.tsv"
    runtime.write_text("placeholder\n", encoding="utf-8")
    environment_log: list[dict[str, str]] = []
    inspection = _inspection(tmp_path)
    before = {
        path.relative_to(tmp_path): (path.stat().st_mode, path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    result = doctor.inspect_local_pilot(
        request,
        workspace,
        runtime,
        source_root=REPO_ROOT,
        ops=_ops(inspection, environment_log=environment_log),
    )

    assert result.ready
    assert result.run_id.startswith("run-")
    assert result.source_commit == "a" * 40
    assert not workspace.exists()
    assert environment_log == [
        {
            **os.environ,
            "NORAD_USE_RENV": "1",
            "RENV_PROJECT": str(REPO_ROOT),
            "R_PROFILE_USER": str(REPO_ROOT / ".Rprofile"),
            "RENV_CONFIG_SANDBOX_ENABLED": "FALSE",
            "RENV_CONFIG_AUTO_SNAPSHOT": "FALSE",
        }
    ]
    after = {
        path.relative_to(tmp_path): (path.stat().st_mode, path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_not_ready_has_exact_blocker_and_remediation(tmp_path: Path) -> None:
    request_root = tmp_path / "request"
    request_root.mkdir()
    request = build(request_root)
    runtime = tmp_path / "runtime.tsv"
    runtime.write_text("placeholder\n", encoding="utf-8")

    result = doctor.inspect_local_pilot(
        request,
        tmp_path / "workspace",
        runtime,
        source_root=REPO_ROOT,
        ops=_ops(_inspection(tmp_path, failing="star")),
    )

    assert not result.ready
    assert result.blockers == ("star: fail (unavailable)",)
    assert result.remediations == (
        f"Set star to the exact local path/version required by {runtime}.",
    )


def test_source_and_workspace_blockers_do_not_mutate(tmp_path: Path) -> None:
    request = build(tmp_path)
    runtime = tmp_path / "runtime.tsv"
    runtime.write_text("placeholder\n", encoding="utf-8")

    result = doctor.inspect_local_pilot(
        request,
        REPO_ROOT / "nested-workspace",
        runtime,
        source_root=REPO_ROOT,
        ops=_ops(
            _inspection(tmp_path),
            source_error=SourceCheckoutError("dirty checkout"),
        ),
    )

    assert not result.ready
    assert any("workspace overlaps" in blocker for blocker in result.blockers)
    assert any("dirty checkout" in blocker for blocker in result.blockers)
    assert not (REPO_ROOT / "nested-workspace").exists()


def test_workspace_rejects_symlink_nearest_existing_ancestor(tmp_path: Path) -> None:
    request = build(tmp_path)
    runtime = tmp_path / "runtime.tsv"
    runtime.write_text("placeholder\n", encoding="utf-8")
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "linked-parent"
    link.symlink_to(target, target_is_directory=True)

    with pytest.raises(doctor.DoctorInputError, match="canonical real directory"):
        doctor.inspect_local_pilot(
            request,
            link / "absent" / "workspace",
            runtime,
            source_root=REPO_ROOT,
            ops=_ops(_inspection(tmp_path)),
        )


def test_malformed_runtime_profile_is_usage_error(tmp_path: Path) -> None:
    request = build(tmp_path)
    runtime = tmp_path / "runtime.tsv"
    runtime.write_text("malformed\n", encoding="utf-8")

    def reject_runtime(
        _path: Path,
        _context: str,
        _environment: dict[str, str],
    ) -> RuntimeInspection:
        raise RuntimeInspectionError("invalid runtime profile")

    ops = _ops(_inspection(tmp_path))
    rejecting = doctor.DoctorOps(
        inspect_source=ops.inspect_source,
        normalize=ops.normalize,
        inspect_runtime=reject_runtime,
        observe_snakemake=ops.observe_snakemake,
    )
    with pytest.raises(doctor.DoctorInputError, match="invalid runtime profile"):
        doctor.inspect_local_pilot(
            request,
            tmp_path / "workspace",
            runtime,
            source_root=REPO_ROOT,
            ops=rejecting,
        )


def test_cli_statuses_and_help(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    help_result = subprocess.run(
        [sys.executable, "-I", "-m", "norad", "doctor", "local-pilot", "--help"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert help_result.returncode == 0
    assert "--runtime-profile" in help_result.stdout
    assert "--workspace" in help_result.stdout

    request = build(tmp_path)
    runtime = tmp_path / "runtime.tsv"
    runtime.write_text("placeholder\n", encoding="utf-8")
    arguments = argparse.Namespace(
        request=request,
        workspace=tmp_path / "workspace",
        runtime_profile=runtime,
    )
    ready_status = doctor.doctor_from_args(
        arguments,
        source_root=REPO_ROOT,
        ops=_ops(_inspection(tmp_path)),
    )
    ready_output = capsys.readouterr()
    assert ready_status == 0
    assert "READY: local-pilot prerequisites passed" in ready_output.out

    status = doctor.doctor_from_args(
        arguments,
        source_root=REPO_ROOT,
        ops=_ops(_inspection(tmp_path, failing="star")),
    )
    captured = capsys.readouterr()
    assert status == 1
    assert "NOT READY" in captured.out
    assert "BLOCKER: star: fail" in captured.out

    def reject_runtime(
        _path: Path,
        _context: str,
        _environment: dict[str, str],
    ) -> RuntimeInspection:
        raise RuntimeInspectionError("invalid runtime profile")

    base_ops = _ops(_inspection(tmp_path))
    malformed_status = doctor.doctor_from_args(
        arguments,
        source_root=REPO_ROOT,
        ops=doctor.DoctorOps(
            inspect_source=base_ops.inspect_source,
            normalize=base_ops.normalize,
            inspect_runtime=reject_runtime,
            observe_snakemake=base_ops.observe_snakemake,
        ),
    )
    malformed_output = capsys.readouterr()
    assert malformed_status == 2
    assert "invalid runtime profile" in malformed_output.err


def test_tracked_runtime_starter_has_exact_contract() -> None:
    lines = EXAMPLE_RUNTIME.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    rows = [dict(zip(header, line.split("\t"), strict=True)) for line in lines[1:]]
    assert (
        tuple((row["check_id"], row["check_type"]) for row in rows)
        == doctor.LOCAL_PILOT_RUNTIME_CHECKS
    )
    assert all(row["required"] == "true" for row in rows)
    assert all(row["runtime_context"] == "local" for row in rows)
    assert json.loads(rows[-1]["probe_args"]) == ["/absolute/path/to/Rscript"]
