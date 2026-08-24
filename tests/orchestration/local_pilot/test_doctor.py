"""Direct contracts for the read-only local-pilot doctor."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from emrys.evidence.runtime_availability.inspector import (
    RuntimeCheck,
    RuntimeInspection,
    RuntimeInspectionError,
    RuntimeObservation,
    load_runtime_profile_contract,
)
from emrys.evidence.storage_inventory import qualification as storage_qualification
from emrys.libraries.installed_package_identity import (
    installed_package_tree_identity,
)
from emrys.libraries.process_environment import (
    gatk_subprocess_environment,
    guarded_r_environment,
    guarded_rscript_argv,
)
from emrys.libraries.source_authority import (
    SourceCheckoutError,
    SourceCheckoutIdentity,
    controlled_python_argv,
)
from emrys.orchestration.local_pilot import doctor
from emrys.orchestration.local_pilot.normalization import normalize_request

from tests.orchestration.local_pilot.fixture import build

REPO_ROOT = Path(__file__).resolve().parents[3]
PROFILE = REPO_ROOT / "workflow/contracts/local_cmh_v2.json"
EXAMPLE_RUNTIME = REPO_ROOT / "configs/local_pilot_runtime.example.tsv"


def _check(
    check_id: str,
    check_type: str,
    target: str,
    *,
    probe_args: tuple[str, ...],
    status: str = "pass",
    resolved_path: Path | None = None,
) -> RuntimeObservation:
    _policy_bytes, policy_checks = load_runtime_profile_contract(EXAMPLE_RUNTIME)
    policy = next(item for item in policy_checks if item.check_id == check_id)
    return RuntimeObservation(
        check=RuntimeCheck(
            check_id=check_id,
            check_type=check_type,
            runtime_context="local",
            required=True,
            target=target,
            probe_args=probe_args,
            expected=policy.expected,
            description=policy.description,
        ),
        status=status,
        observed="9.25.1" if check_id == "snakemake" else "observed",
        detail="test observation",
        resolved_path=resolved_path,
    )


def _inspection(tmp_path: Path, *, failing: str | None = None) -> RuntimeInspection:
    tool = tmp_path / "tool"
    tool.write_bytes(b"tool\n")
    tool.chmod(0o755)
    java = tmp_path / "java-home" / "bin" / "java"
    java.parent.mkdir(parents=True, exist_ok=True)
    java.write_bytes(b"java\n")
    java.chmod(0o755)
    jar = tmp_path / "picard.jar"
    jar.write_bytes(b"jar\n")
    renv_library = tmp_path / "renv-library"
    renv_library.mkdir(exist_ok=True)
    installed_renv = renv_library / "renv"
    installed_renv.mkdir(exist_ok=True)
    (installed_renv / "DESCRIPTION").write_text(
        "Package: renv\nVersion: 1.2.3\n", encoding="utf-8"
    )
    for _check_id, package in doctor.LOCAL_PILOT_R_PACKAGES:
        package_root = renv_library / package
        package_root.mkdir(exist_ok=True)
        (package_root / "DESCRIPTION").write_text(
            f"Package: {package}\nVersion: 1.0.0\n", encoding="utf-8"
        )
    rscript = str(tool)
    observations = [
        _check("bash", "tool_version", str(tool), probe_args=("--version",)),
        _check("python", "tool_version", sys.executable, probe_args=("--version",)),
        _check(
            "snakemake",
            "tool_version",
            sys.executable,
            probe_args=controlled_python_argv(
                sys.executable, "-m", "snakemake", "--version"
            )[1:],
        ),
        _check(
            "sha256_python",
            "hash_utility",
            sys.executable,
            probe_args=("python_hashlib",),
        ),
        _check("star", "tool_version", str(tool), probe_args=("--version",)),
        _check("samtools", "tool_version", str(tool), probe_args=("--version",)),
        _check("java", "tool_version", str(java), probe_args=("-version",)),
        _check("gatk", "tool_version", str(tool), probe_args=("--version",)),
        _check(
            "picard",
            "tool_version_exit_1",
            str(java),
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
        _check("gunzip", "tool_version", str(tool), probe_args=("--version",)),
        _check("rscript", "tool_version", rscript, probe_args=("--version",)),
        _check(
            "renv_project",
            "path_visibility",
            str(REPO_ROOT),
            probe_args=("directory_readable",),
        ),
        _check(
            "renv_library",
            "path_visibility",
            str(renv_library),
            probe_args=("directory_readable",),
        ),
    ]
    for check_id, package in doctor.LOCAL_PILOT_R_PACKAGES:
        observations.append(
            _check(
                check_id,
                "r_namespace",
                package,
                probe_args=(rscript,),
                resolved_path=(renv_library / package).resolve(strict=True),
            )
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


def _with_namespace_root(
    inspection: RuntimeInspection,
    check_id: str,
    root: Path | None,
) -> RuntimeInspection:
    return replace(
        inspection,
        observations=tuple(
            replace(item, resolved_path=root)
            if item.check.check_id == check_id
            else item
            for item in inspection.observations
        ),
    )


def _ops(
    inspection: RuntimeInspection,
    *,
    source_error: SourceCheckoutError | None = None,
    environment_log: list[dict[str, str]] | None = None,
    storage_error: storage_qualification.StorageQualificationError | None = None,
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

    def inspect_storage(
        _workspace: Path,
        _reference_fasta: Path,
    ) -> storage_qualification.QualifiedStorage:
        if storage_error is not None:
            raise storage_error
        receipt = Path(inspection.observations[0].check.target)
        return storage_qualification.QualifiedStorage(
            receipt_path=receipt,
            receipt_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
            qualification_id="b" * 64,
        )

    return doctor.DoctorOps(
        inspect_source=inspect_source,
        normalize=normalize_request,
        inspect_runtime=inspect_runtime,
        observe_snakemake=lambda _python: doctor.SNAKEMAKE_VERSION,
        load_runtime_profile=lambda _path: (
            inspection.profile_bytes,
            tuple(item.check for item in inspection.observations),
        ),
        path_access=os.access,
        inspect_storage=inspect_storage,
    )


def test_ready_doctor_is_read_only_and_guards_renv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_root = tmp_path / "request"
    request_root.mkdir()
    request = build(request_root)
    workspace = tmp_path / "future-workspace"
    runtime = tmp_path / "runtime.tsv"
    runtime.write_text("placeholder\n", encoding="utf-8")
    environment_log: list[dict[str, str]] = []
    inspection = _inspection(tmp_path)
    monkeypatch.setenv("R_LIBS_USER", "/ambient/r-library")
    monkeypatch.setenv("R_LIBS_CUSTOM", "/ambient/custom-library")
    monkeypatch.setenv("RENV_PATHS_CACHE", "/ambient/renv-cache")
    monkeypatch.setenv("RENV_CONFIG_USER_PROFILE", "/ambient/profile")
    monkeypatch.setenv("R_PROFILE_SITE", "/ambient/site-profile")
    monkeypatch.setenv("R_ENVIRON_USER", "/ambient/environ")
    monkeypatch.setenv("R_DEFAULT_PACKAGES", "hostilePackage")
    monkeypatch.setenv("BASH_ENV", "/ambient/bash-startup")
    monkeypatch.setenv("ENV", "/ambient/posix-startup")
    monkeypatch.setenv("CDPATH", "/ambient/cdpath")
    monkeypatch.setenv("GLOBIGNORE", "*")
    monkeypatch.setenv("BASH_FUNC_hostile%%", "() { false; }")
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
        gatk_subprocess_environment(
            tmp_path / "java-home" / "bin" / "java",
            base_environment=doctor.runtime_environment(
                REPO_ROOT,
                tmp_path / "renv-library",
                base_environment=os.environ,
            ),
        )
    ]
    assert not {
        "R_LIBS_CUSTOM",
        "RENV_PATHS_CACHE",
        "BASH_ENV",
        "ENV",
        "CDPATH",
        "GLOBIGNORE",
        "BASH_FUNC_hostile%%",
    }.intersection(environment_log[0])
    assert environment_log[0]["R_LIBS_USER"] == str(tmp_path / "renv-library")
    assert environment_log[0]["R_PROFILE_SITE"] == os.devnull
    assert environment_log[0]["R_ENVIRON_USER"] == os.devnull
    assert environment_log[0]["RENV_CONFIG_USER_PROFILE"] == "FALSE"
    assert environment_log[0]["R_DEFAULT_PACKAGES"] == "NULL"
    assert environment_log[0]["RENV_CONFIG_AUTOLOADER_ENABLED"] == "FALSE"
    assert environment_log[0]["RENV_AUTOLOADER_ENABLED"] == "FALSE"
    assert environment_log[0]["RENV_ACTIVATE_PROJECT"] == "FALSE"
    identities = doctor.required_tool_identities(
        result.inspection,
        bindings=result.bindings,
        python_executable=Path(sys.executable),
    )
    by_name = {item["name"]: item for item in identities}
    assert by_name["python"]["sha256"] == by_name["snakemake"]["sha256"]
    assert by_name["snakemake"]["path"] == sys.executable
    assert by_name["storage_qualification"]["version"] == "b" * 64
    assert by_name["renv_library"] == {
        "name": "renv_library",
        "version": "observed",
        "path": str(tmp_path / "renv-library"),
        "resolved_path": str(tmp_path / "renv-library"),
        "sha256": None,
    }
    after = {
        path.relative_to(tmp_path): (path.stat().st_mode, path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_required_tool_identities_reject_duplicate_runtime_binding_ids(
    tmp_path: Path,
) -> None:
    inspection = _inspection(tmp_path)
    binding = doctor.runtime_file_bindings(inspection)[0]

    with pytest.raises(doctor.DoctorInputError, match="unique check IDs"):
        doctor.required_tool_identities(
            inspection,
            bindings=(binding, binding),
            python_executable=Path(sys.executable),
        )


def test_required_tool_identities_require_storage_qualification(
    tmp_path: Path,
) -> None:
    inspection = _inspection(tmp_path)

    with pytest.raises(
        doctor.DoctorInputError,
        match="absent: storage_qualification",
    ):
        doctor.required_tool_identities(
            inspection,
            bindings=doctor.runtime_file_bindings(inspection),
            python_executable=Path(sys.executable),
        )


def test_doctor_blocks_when_storage_is_not_site_qualified(
    tmp_path: Path,
) -> None:
    request = build(tmp_path)
    runtime = tmp_path / "runtime.tsv"
    runtime.write_text("placeholder\n", encoding="utf-8")
    result = doctor.inspect_local_pilot(
        request,
        tmp_path / "workspace",
        runtime,
        source_root=REPO_ROOT,
        ops=_ops(
            _inspection(tmp_path),
            storage_error=storage_qualification.StorageQualificationError(
                "final receipt is absent"
            ),
        ),
    )

    assert not result.ready
    assert any("storage is not site-qualified" in item for item in result.blockers)


def test_guarded_r_startup_uses_reviewed_profile_without_activation_or_ambient_files(
    tmp_path: Path,
) -> None:
    rscript = shutil.which("Rscript")
    if rscript is None:
        pytest.skip("Rscript is unavailable")
    project = tmp_path / "project"
    project.mkdir()
    shutil.copy2(REPO_ROOT / ".Rprofile", project / ".Rprofile")
    activation_marker = tmp_path / "activation-marker"
    activation = project / "renv" / "activate.R"
    activation.parent.mkdir()
    activation.write_text(
        f"writeLines('activated', {json.dumps(str(activation_marker))})\n",
        encoding="utf-8",
    )
    library = tmp_path / "library"
    installed_renv = library / "renv"
    installed_renv.mkdir(parents=True)
    (installed_renv / "DESCRIPTION").write_text(
        "Package: renv\nVersion: 1.2.3\n", encoding="utf-8"
    )
    profile_marker = tmp_path / "hostile-profile-marker"
    environ_marker = tmp_path / "hostile-environ-marker"
    hostile_profile = tmp_path / "hostile.Rprofile"
    hostile_profile.write_text(
        f"writeLines('hostile', {json.dumps(str(profile_marker))})\n",
        encoding="utf-8",
    )
    hostile_environ = tmp_path / "hostile.Renviron"
    hostile_environ.write_text(
        f"R_DEFAULT_PACKAGES=utils\nHOSTILE_MARKER={environ_marker}\n",
        encoding="utf-8",
    )
    environment = guarded_r_environment(
        project,
        library,
        base_environment={
            "PATH": os.environ["PATH"],
            "R_PROFILE_SITE": str(hostile_profile),
            "R_PROFILE_USER": str(hostile_profile),
            "R_ENVIRON_SITE": str(hostile_environ),
            "R_ENVIRON_USER": str(hostile_environ),
            "RENV_PATHS_CACHE": str(tmp_path / "hostile-cache"),
            "R_DEFAULT_PACKAGES": "utils",
        },
    )
    expression = (
        "cat(normalizePath(.libPaths()[[1L]], winslash='/', mustWork=TRUE)); "
        "if (nzchar(Sys.getenv('HOSTILE_MARKER'))) "
        "writeLines('hostile', Sys.getenv('HOSTILE_MARKER'))"
    )

    completed = subprocess.run(
        guarded_rscript_argv(rscript, ("-e", expression)),
        env=environment,
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == str(library)
    assert not activation_marker.exists()
    assert not profile_marker.exists()
    assert not environ_marker.exists()


def test_default_doctor_gatk_probe_uses_declared_java_not_ambient_java(
    tmp_path: Path,
) -> None:
    selected_home = tmp_path / "selected-java"
    selected_java = selected_home / "bin" / "java"
    selected_java.parent.mkdir(parents=True)
    poison_home = tmp_path / "poison-java"
    poison_java = poison_home / "bin" / "java"
    poison_java.parent.mkdir(parents=True)
    gatk = tmp_path / "bin" / "gatk"
    gatk.parent.mkdir()
    selected_marker = tmp_path / "selected-java.marker"
    poison_marker = tmp_path / "poison-java.marker"
    gatk_environment_marker = tmp_path / "gatk-environment.marker"

    selected_java.write_text(
        "#!/bin/sh\n"
        'printf \'%s\\n\' "$*" >> "$SELECTED_JAVA_MARKER"\n'
        "printf 'openjdk version \"17.0.14\" 2026-01-01\\n' >&2\n",
        encoding="utf-8",
    )
    poison_java.write_text(
        "#!/bin/sh\n"
        "printf 'poison\\n' >> \"$POISON_JAVA_MARKER\"\n"
        "printf 'openjdk version \"99.0.0\" 2026-01-01\\n' >&2\n",
        encoding="utf-8",
    )
    gatk.write_text(
        "#!/bin/sh\n"
        'printf \'%s|%s\\n\' "$JAVA_HOME" "$(command -v java)" '
        '> "$GATK_ENVIRONMENT_MARKER"\n'
        "for name in CLASSPATH GATK_JAR GATK_LOCAL_JAR JAVA_OPTS "
        "JAVA_TOOL_OPTIONS JDK_JAVA_OPTIONS _JAVA_OPTIONS; do\n"
        '    eval "value=\\${$name-unset}"\n'
        '    printf \'%s=%s\\n\' "$name" "$value" >> "$GATK_ENVIRONMENT_MARKER"\n'
        "done\n"
        "java -version >/dev/null 2>&1\n"
        "printf 'GATK 4.6.1.0\\n'\n",
        encoding="utf-8",
    )
    for executable in (selected_java, poison_java, gatk):
        executable.chmod(0o755)

    profile = tmp_path / "runtime.tsv"
    header = (
        "check_id\tcheck_type\truntime_context\trequired\ttarget\tprobe_args\t"
        "expected\tdescription"
    )
    profile.write_text(
        "\n".join(
            (
                header,
                "\t".join(
                    (
                        "java",
                        "tool_version",
                        "local",
                        "true",
                        str(selected_java),
                        json.dumps(["-version"]),
                        '^openjdk version "17[.]',
                        "selected Java",
                    )
                ),
                "\t".join(
                    (
                        "gatk",
                        "tool_version",
                        "local",
                        "true",
                        str(gatk),
                        json.dumps(["--version"]),
                        "^GATK 4[.]6[.]1[.]0$",
                        "GATK probe",
                    )
                ),
            )
        )
        + "\n",
        encoding="utf-8",
    )
    environment = {
        "PATH": f"{poison_java.parent}{os.pathsep}{os.environ['PATH']}",
        "JAVA_HOME": str(poison_home),
        "SELECTED_JAVA_MARKER": str(selected_marker),
        "POISON_JAVA_MARKER": str(poison_marker),
        "GATK_ENVIRONMENT_MARKER": str(gatk_environment_marker),
        "CLASSPATH": "/ambient/classes",
        "GATK_JAR": "/ambient/gatk.jar",
        "GATK_LOCAL_JAR": "/ambient/local-gatk.jar",
        "JAVA_OPTS": "-Dambient.java.opts=true",
        "JAVA_TOOL_OPTIONS": "-Dambient.java.tool.options=true",
        "JDK_JAVA_OPTIONS": "-Dambient.jdk.java.options=true",
        "_JAVA_OPTIONS": "-Dambient.underscore.java.options=true",
    }

    inspection = doctor._default_runtime_inspector(profile, "local", environment)

    assert [item.status for item in inspection.observations] == ["pass", "pass"]
    assert selected_marker.read_text(encoding="utf-8").splitlines() == [
        "-version",
        "-version",
    ]
    assert not poison_marker.exists()
    assert gatk_environment_marker.read_text(encoding="utf-8").splitlines() == [
        f"{selected_home.resolve()}|{selected_java.resolve()}",
        "CLASSPATH=unset",
        "GATK_JAR=unset",
        "GATK_LOCAL_JAR=unset",
        "JAVA_OPTS=unset",
        "JAVA_TOOL_OPTIONS=unset",
        "JDK_JAVA_OPTIONS=unset",
        "_JAVA_OPTIONS=unset",
    ]


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


def test_nested_absent_workspace_is_not_ready_and_is_not_created(
    tmp_path: Path,
) -> None:
    request = build(tmp_path)
    runtime = tmp_path / "runtime.tsv"
    runtime.write_text("placeholder\n", encoding="utf-8")
    workspace = tmp_path / "absent-parent" / "workspace"

    result = doctor.inspect_local_pilot(
        request,
        workspace,
        runtime,
        source_root=REPO_ROOT,
        ops=_ops(_inspection(tmp_path)),
    )

    assert not result.ready
    assert result.blockers == (
        f"workspace immediate parent does not exist: {workspace.parent}",
    )
    assert result.remediations == (
        "Create the immediate parent as a canonical real directory first: "
        f"{workspace.parent}",
    )
    assert not workspace.parent.exists()


def test_unwritable_step00c_fasta_parent_is_not_ready_without_mutation(
    tmp_path: Path,
) -> None:
    request = build(tmp_path)
    runtime = tmp_path / "runtime.tsv"
    runtime.write_text("placeholder\n", encoding="utf-8")
    inspection = _inspection(tmp_path)
    reference_parent = tmp_path / "reference"
    before = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    defaults = _ops(inspection)

    def deny_reference_parent(path: Path, mode: int) -> bool:
        if path == reference_parent:
            assert mode == os.R_OK | os.W_OK | os.X_OK
            return False
        return os.access(path, mode)

    result = doctor.inspect_local_pilot(
        request,
        tmp_path / "workspace",
        runtime,
        source_root=REPO_ROOT,
        ops=replace(defaults, path_access=deny_reference_parent),
    )

    assert not result.ready
    assert any(
        "Step 00c stationary FASTA parent is not readable, writable, and searchable"
        in blocker
        for blocker in result.blockers
    )
    assert result.remediations == (
        "Use a canonical readable FASTA in a readable, writable, searchable parent.",
    )
    after = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_workspace_rejects_symlink_immediate_parent(tmp_path: Path) -> None:
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
            link / "workspace",
            runtime,
            source_root=REPO_ROOT,
            ops=_ops(_inspection(tmp_path)),
        )


def test_step00c_fasta_through_symlinked_parent_is_usage_error_without_mutation(
    tmp_path: Path,
) -> None:
    request = build(tmp_path)
    runtime = tmp_path / "runtime.tsv"
    runtime.write_text("placeholder\n", encoding="utf-8")
    reference = tmp_path / "reference"
    real_reference = tmp_path / "reference-real"
    reference.rename(real_reference)
    reference.symlink_to(real_reference, target_is_directory=True)
    inspection = _inspection(tmp_path)
    before = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    with pytest.raises(doctor.DoctorInputError, match="canonical real file"):
        doctor.inspect_local_pilot(
            request,
            tmp_path / "workspace",
            runtime,
            source_root=REPO_ROOT,
            ops=_ops(inspection),
        )

    after = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before


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
        load_runtime_profile=ops.load_runtime_profile,
        path_access=ops.path_access,
        inspect_storage=ops.inspect_storage,
    )
    with pytest.raises(doctor.DoctorInputError, match="invalid runtime profile"):
        doctor.inspect_local_pilot(
            request,
            tmp_path / "workspace",
            runtime,
            source_root=REPO_ROOT,
            ops=rejecting,
        )


@pytest.mark.parametrize(
    ("check_id", "change"),
    (
        ("star", "expected"),
        ("star", "probe_args"),
        ("r_variant_annotation", "target"),
    ),
)
def test_runtime_profile_cannot_weaken_fixed_probe_policy_before_probing(
    tmp_path: Path,
    check_id: str,
    change: str,
) -> None:
    request = build(tmp_path)
    runtime = tmp_path / "runtime.tsv"
    inspection = _inspection(tmp_path)
    runtime.write_bytes(inspection.profile_bytes)
    declared = [item.check for item in inspection.observations]
    index = next(
        index for index, check in enumerate(declared) if check.check_id == check_id
    )
    check = declared[index]
    if change == "expected":
        declared[index] = replace(check, expected=".*")
    elif change == "probe_args":
        declared[index] = replace(check, probe_args=("--help",))
    else:
        declared[index] = replace(check, target="IRanges")

    def unexpected_probe(
        _path: Path,
        _context: str,
        _environment: dict[str, str],
    ) -> RuntimeInspection:
        raise AssertionError("runtime probes must not run for weakened policy")

    base = _ops(inspection)
    ops = replace(
        base,
        inspect_runtime=unexpected_probe,
        load_runtime_profile=lambda _path: (
            inspection.profile_bytes,
            tuple(declared),
        ),
    )
    with pytest.raises(doctor.DoctorInputError, match="fixed.*policy"):
        doctor.inspect_local_pilot(
            request,
            tmp_path / "workspace",
            runtime,
            source_root=REPO_ROOT,
            ops=ops,
        )


@pytest.mark.parametrize(
    "change",
    ("java_target", "jar_target", "subcommand", "version_flag"),
)
def test_picard_profile_requires_exact_java_jar_and_args_before_probing(
    tmp_path: Path,
    change: str,
) -> None:
    request = build(tmp_path)
    runtime = tmp_path / "runtime.tsv"
    inspection = _inspection(tmp_path)
    runtime.write_bytes(inspection.profile_bytes)
    declared = [item.check for item in inspection.observations]
    index = next(
        index for index, check in enumerate(declared) if check.check_id == "picard"
    )
    picard = declared[index]
    if change == "java_target":
        declared[index] = replace(picard, target=str(tmp_path / "other-java"))
    elif change == "jar_target":
        declared[index] = replace(
            picard,
            probe_args=(
                "-jar",
                str(tmp_path / "other-picard.jar"),
                "MarkDuplicates",
                "--version",
            ),
        )
    elif change == "subcommand":
        declared[index] = replace(
            picard,
            probe_args=(
                picard.probe_args[0],
                picard.probe_args[1],
                "CollectInsertSizeMetrics",
                picard.probe_args[3],
            ),
        )
    else:
        declared[index] = replace(
            picard,
            probe_args=(*picard.probe_args[:3], "--help"),
        )

    def unexpected_probe(
        _path: Path,
        _context: str,
        _environment: dict[str, str],
    ) -> RuntimeInspection:
        raise AssertionError(
            "runtime probes must not run for a mismatched Picard probe"
        )

    base = _ops(inspection)
    ops = replace(
        base,
        inspect_runtime=unexpected_probe,
        load_runtime_profile=lambda _path: (
            inspection.profile_bytes,
            tuple(declared),
        ),
    )
    with pytest.raises(
        doctor.DoctorInputError,
        match="Picard version probing must use the declared Java and Picard jar",
    ):
        doctor.inspect_local_pilot(
            request,
            tmp_path / "workspace",
            runtime,
            source_root=REPO_ROOT,
            ops=ops,
        )


def test_renv_library_must_be_an_existing_canonical_real_directory(
    tmp_path: Path,
) -> None:
    request = build(tmp_path)
    runtime = tmp_path / "runtime.tsv"
    runtime.write_text("placeholder\n", encoding="utf-8")
    inspection = _inspection(tmp_path)
    real_library = tmp_path / "renv-library"
    linked_library = tmp_path / "linked-renv-library"
    linked_library.symlink_to(real_library, target_is_directory=True)
    observations = tuple(
        replace(
            item,
            check=replace(item.check, target=str(linked_library)),
        )
        if item.check.check_id == "renv_library"
        else item
        for item in inspection.observations
    )
    linked_inspection = replace(inspection, observations=observations)

    with pytest.raises(doctor.DoctorInputError, match="canonical real directory"):
        doctor.inspect_local_pilot(
            request,
            tmp_path / "workspace",
            runtime,
            source_root=REPO_ROOT,
            ops=_ops(linked_inspection),
        )


def test_installed_renv_package_entry_may_resolve_through_cache_symlink(
    tmp_path: Path,
) -> None:
    inspection = _inspection(tmp_path)
    library = tmp_path / "renv-library"
    package_entry = library / "renv"
    cache_root = tmp_path / "renv-cache"
    cache_root.mkdir()
    cached_package = cache_root / "renv-1.2.3"
    package_entry.rename(cached_package)
    package_entry.symlink_to(cached_package, target_is_directory=True)
    checks = tuple(item.check for item in inspection.observations)

    assert doctor._declared_renv_library(checks) == library
    assert package_entry.is_symlink()


def test_installed_renv_package_entry_rejects_dangling_cache_symlink(
    tmp_path: Path,
) -> None:
    inspection = _inspection(tmp_path)
    package_entry = tmp_path / "renv-library" / "renv"
    (package_entry / "DESCRIPTION").unlink()
    package_entry.rmdir()
    package_entry.symlink_to(tmp_path / "missing-renv-cache-package")
    checks = tuple(item.check for item in inspection.observations)

    with pytest.raises(
        doctor.DoctorInputError,
        match="no readable installed renv package",
    ):
        doctor._declared_renv_library(checks)


def test_installed_renv_package_entry_rejects_retarget_during_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inspection = _inspection(tmp_path)
    package_entry = tmp_path / "renv-library" / "renv"
    cache_root = tmp_path / "renv-cache"
    cache_root.mkdir()
    cached_a = cache_root / "renv-a"
    cached_b = cache_root / "renv-b"
    package_entry.rename(cached_a)
    shutil.copytree(cached_a, cached_b)
    package_entry.symlink_to(cached_a, target_is_directory=True)
    checks = tuple(item.check for item in inspection.observations)
    real_read_bytes = Path.read_bytes

    def retarget_after_read(path: Path) -> bytes:
        data = real_read_bytes(path)
        if path == cached_a / "DESCRIPTION":
            package_entry.unlink()
            package_entry.symlink_to(cached_b, target_is_directory=True)
        return data

    monkeypatch.setattr(Path, "read_bytes", retarget_after_read)

    with pytest.raises(
        doctor.DoctorInputError,
        match="Installed renv package entry changed during admission",
    ):
        doctor._declared_renv_library(checks)


def test_runtime_bindings_resolve_symlinked_installed_package_entry(
    tmp_path: Path,
) -> None:
    inspection = _inspection(tmp_path)
    check_id, package = doctor.LOCAL_PILOT_R_PACKAGES[0]
    package_entry = tmp_path / "renv-library" / package
    cache_root = tmp_path / "renv-cache"
    cache_root.mkdir()
    cached_package = cache_root / f"{package}-1.0.0"
    package_entry.rename(cached_package)
    package_entry.symlink_to(cached_package, target_is_directory=True)
    expected = installed_package_tree_identity(cached_package)
    inspection = _with_namespace_root(inspection, check_id, expected.root)

    binding = next(
        item
        for item in doctor.runtime_file_bindings(inspection)
        if item.check_id == check_id
    )

    assert binding.path == expected.root
    assert binding.resolved_path == expected.root
    assert binding.sha256 == expected.sha256
    assert package_entry.is_symlink()


def test_runtime_bindings_reject_package_retargeted_after_namespace_probe(
    tmp_path: Path,
) -> None:
    inspection = _inspection(tmp_path)
    check_id, package = doctor.LOCAL_PILOT_R_PACKAGES[0]
    package_entry = tmp_path / "renv-library" / package
    observed_root = package_entry.resolve(strict=True)
    cache_root = tmp_path / "renv-cache"
    cache_root.mkdir()
    cached_package = cache_root / f"{package}-retargeted"
    package_entry.rename(cached_package)
    package_entry.symlink_to(cached_package, target_is_directory=True)
    inspection = _with_namespace_root(inspection, check_id, observed_root)

    with pytest.raises(
        doctor.DoctorInputError,
        match=f"Loaded R namespace root changed before package binding: {check_id}",
    ):
        doctor.runtime_file_bindings(inspection)


def test_runtime_bindings_require_loaded_root_on_passing_namespace(
    tmp_path: Path,
) -> None:
    inspection = _inspection(tmp_path)
    check_id, _package = doctor.LOCAL_PILOT_R_PACKAGES[0]
    inspection = _with_namespace_root(inspection, check_id, None)

    with pytest.raises(
        doctor.DoctorInputError,
        match=f"Passing R namespace observation did not bind its loaded root: {check_id}",
    ):
        doctor.runtime_file_bindings(inspection)


def test_runtime_bindings_reject_package_entry_retargeted_during_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inspection = _inspection(tmp_path)
    check_id, package = doctor.LOCAL_PILOT_R_PACKAGES[0]
    package_entry = tmp_path / "renv-library" / package
    cache_root = tmp_path / "renv-cache"
    cache_root.mkdir()
    cached_a = cache_root / f"{package}-a"
    cached_b = cache_root / f"{package}-b"
    package_entry.rename(cached_a)
    shutil.copytree(cached_a, cached_b)
    package_entry.symlink_to(cached_a, target_is_directory=True)
    inspection = _with_namespace_root(
        inspection,
        check_id,
        cached_a.resolve(strict=True),
    )
    real_identity = doctor.installed_package_tree_identity

    def retarget_after_hash(root: Path):
        identity = real_identity(root)
        if root == cached_a.resolve(strict=True):
            package_entry.unlink()
            package_entry.symlink_to(cached_b, target_is_directory=True)
        return identity

    monkeypatch.setattr(
        doctor,
        "installed_package_tree_identity",
        retarget_after_hash,
    )

    with pytest.raises(
        doctor.DoctorInputError,
        match=f"Installed R package entry changed during admission: {check_id}",
    ):
        doctor.runtime_file_bindings(inspection)


def test_runtime_bindings_reject_broken_package_entry_symlink(
    tmp_path: Path,
) -> None:
    inspection = _inspection(tmp_path)
    check_id, package = doctor.LOCAL_PILOT_R_PACKAGES[0]
    package_entry = tmp_path / "renv-library" / package
    (package_entry / "DESCRIPTION").unlink()
    package_entry.rmdir()
    package_entry.symlink_to(tmp_path / "missing-cache-package")

    with pytest.raises(
        doctor.DoctorInputError,
        match=f"Could not resolve installed R package {check_id}",
    ):
        doctor.runtime_file_bindings(inspection)


def test_missing_installed_renv_fails_before_probe_without_bootstrap(
    tmp_path: Path,
) -> None:
    request = build(tmp_path)
    runtime = tmp_path / "runtime.tsv"
    runtime.write_text("placeholder\n", encoding="utf-8")
    inspection = _inspection(tmp_path)
    description = tmp_path / "renv-library" / "renv" / "DESCRIPTION"
    description.unlink()
    (tmp_path / "renv-library" / "renv").rmdir()
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    calls = 0
    defaults = _ops(inspection)

    def forbidden_probe(
        _path: Path,
        _context: str,
        _environment: dict[str, str],
    ) -> RuntimeInspection:
        nonlocal calls
        calls += 1
        raise AssertionError("runtime probe must not run without installed renv")

    with pytest.raises(doctor.DoctorInputError, match="no readable installed renv"):
        doctor.inspect_local_pilot(
            request,
            tmp_path / "workspace",
            runtime,
            source_root=REPO_ROOT,
            ops=replace(defaults, inspect_runtime=forbidden_probe),
        )

    assert calls == 0
    assert sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")) == before


def test_cli_statuses_and_help(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    help_result = subprocess.run(
        [sys.executable, "-I", "-m", "emrys", "doctor", "local-pilot", "--help"],
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
            load_runtime_profile=base_ops.load_runtime_profile,
            path_access=base_ops.path_access,
            inspect_storage=base_ops.inspect_storage,
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
    by_name = {row["check_id"]: row for row in rows}
    assert by_name["snakemake"]["target"] == by_name["python"]["target"]
    assert json.loads(by_name["snakemake"]["probe_args"]) == [
        "-X",
        "pycache_prefix=/dev/null",
        "-I",
        "-m",
        "snakemake",
        "--version",
    ]
    assert by_name["picard"]["target"] == by_name["java"]["target"]
    assert json.loads(by_name["picard"]["probe_args"]) == [
        "-jar",
        by_name["picard_jar"]["target"],
        "MarkDuplicates",
        "--version",
    ]
    assert by_name["picard"]["expected"] == (
        r"^Version:3[.]1[.]1(?:-16-g5b0b4c014-SNAPSHOT)?$"
    )
    assert by_name["infer_experiment"]["expected"] == (
        r"^infer_experiment[.]py 5[.]0[.]4$"
    )
    assert by_name["gatk"]["expected"] == (
        r"(?:^|\s)The Genome Analysis Toolkit [(]GATK[)] "
        r"v?4[.]6[.]1[.]0(?:\s|$)"
    )
    assert json.loads(by_name["renv_library"]["probe_args"]) == ["directory_readable"]
    assert json.loads(rows[-1]["probe_args"]) == ["/absolute/path/to/Rscript"]


@pytest.mark.parametrize(
    ("check_id", "accepted", "rejected"),
    (
        (
            "picard",
            (
                "Version:3.1.1",
                "Version:3.1.1-16-g5b0b4c014-SNAPSHOT",
            ),
            (
                "Version:3.1.2",
                "Picard Version:3.1.1",
                "Version:3.1.1-17-g000000000-SNAPSHOT",
            ),
        ),
        (
            "infer_experiment",
            ("infer_experiment.py 5.0.4",),
            (
                "RSeQC v5.0.4",
                "infer_experiment.py 5.0.5",
                "prefix infer_experiment.py 5.0.4",
            ),
        ),
    ),
)
def test_tracked_runtime_version_policies_are_strict(
    check_id: str,
    accepted: tuple[str, ...],
    rejected: tuple[str, ...],
) -> None:
    lines = EXAMPLE_RUNTIME.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    rows = [dict(zip(header, line.split("\t"), strict=True)) for line in lines[1:]]
    expected = {row["check_id"]: row["expected"] for row in rows}[check_id]

    assert all(re.search(expected, value) for value in accepted)
    assert all(re.search(expected, value) is None for value in rejected)
