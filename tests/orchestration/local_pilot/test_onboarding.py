from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from norad import __main__ as cli
from norad.evidence.runtime_availability.inspector import load_runtime_profile_contract
from norad.orchestration.local_pilot import doctor, onboarding, synthetic_fixture

REPO_ROOT = Path(__file__).resolve().parents[3]


def _namespace(output: Path, *, execute: bool) -> argparse.Namespace:
    return argparse.Namespace(output_dir=output, execute=execute)


def _publish_synthetic(output: Path) -> None:
    assert synthetic_fixture.init_from_args(_namespace(output, execute=True)) == 0


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _executable(path: Path, content: str = "#!/bin/sh\nexit 0\n") -> Path:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path


def test_init_local_pilot_is_dry_run_first_and_receipt_last(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "starter"
    assert onboarding.init_from_args(_namespace(output, execute=False)) == 0
    assert not output.exists()
    assert "Dry-run complete" in capsys.readouterr().out

    assert onboarding.init_from_args(_namespace(output, execute=True)) == 0
    expected = {
        "request.yaml",
        "samples.tsv",
        "partitions.tsv",
        "runtime.tsv",
        "run-in-slurm.sh",
        "starter-set.manifest.tsv",
    }
    assert set(_tree_bytes(output)) == expected
    assert stat.S_IMODE((output / "run-in-slurm.sh").stat().st_mode) == 0o755
    rows = list(
        csv.DictReader(
            (output / "starter-set.manifest.tsv").open(encoding="utf-8"),
            delimiter="\t",
        )
    )
    assert [row["path"] for row in rows] == sorted(
        expected - {"starter-set.manifest.tsv"}
    )
    for row in rows:
        data = (output / row["path"]).read_bytes()
        assert int(row["size_bytes"]) == len(data)
        assert row["sha256"] == hashlib.sha256(data).hexdigest()
    request = (output / "request.yaml").read_text(encoding="utf-8")
    assert "sample_manifest: samples.tsv" in request
    assert "partition_manifest: partitions.tsv" in request


def test_init_refuses_predecessor_without_changing_it(tmp_path: Path) -> None:
    output = tmp_path / "starter"
    output.mkdir()
    predecessor = output / "owned.txt"
    predecessor.write_bytes(b"preserve me\n")

    assert onboarding.init_from_args(_namespace(output, execute=True)) == 2
    assert _tree_bytes(output) == {"owned.txt": b"preserve me\n"}


def test_synthetic_init_is_dry_run_first_and_refuses_predecessor(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "fixture"

    assert synthetic_fixture.init_from_args(_namespace(output, execute=False)) == 0
    assert not output.exists()
    assert "Dry-run complete" in capsys.readouterr().out

    output.mkdir()
    predecessor = output / "owned.txt"
    predecessor.write_bytes(b"preserve me\n")

    assert synthetic_fixture.init_from_args(_namespace(output, execute=True)) == 2
    captured = capsys.readouterr()
    assert "output directory must be absent" in captured.err
    assert _tree_bytes(output) == {"owned.txt": b"preserve me\n"}


def test_publication_re_admits_every_member_after_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "publication"
    real_write = onboarding._write_member

    def write_then_tamper(path: Path, data: bytes, mode: int) -> None:
        real_write(path, data, mode)
        if path.name == "complete.tsv":
            (path.parent / "request.yaml").write_bytes(b"changed after preparation\n")

    monkeypatch.setattr(onboarding, "_write_member", write_then_tamper)
    members = {"request.yaml": (b"original\n", 0o644)}

    with pytest.raises(
        onboarding.OnboardingError, match="member bytes changed"
    ) as failure:
        onboarding.publish_create_absent_tree(
            output,
            members,
            completion_name="complete.tsv",
            completion_bytes=b"complete\n",
        )

    assert "present-but-invalid" in str(failure.value)
    assert "presence alone is not completion proof" in str(failure.value)
    assert (output / "complete.tsv").is_file()
    assert (output / "request.yaml").read_bytes() == b"changed after preparation\n"


@pytest.mark.parametrize(
    "unsafe_name", ("../escape", "/absolute", "bad\\name", "bad\nname")
)
def test_publication_rejects_unsafe_member_paths(
    tmp_path: Path,
    unsafe_name: str,
) -> None:
    output = tmp_path / "publication"
    with pytest.raises(onboarding.OnboardingError, match="unsafe publication member"):
        onboarding.publish_create_absent_tree(
            output,
            {unsafe_name: (b"unsafe\n", 0o644)},
            completion_name="complete.tsv",
            completion_bytes=b"complete\n",
        )
    assert not output.exists()


def test_init_requires_an_absolute_external_output(tmp_path: Path) -> None:
    assert onboarding.init_from_args(_namespace(Path("relative"), execute=True)) == 2
    assert (
        onboarding.init_from_args(
            _namespace(REPO_ROOT / "forbidden-output", execute=True)
        )
        == 2
    )


def test_synthetic_fixture_is_deterministic_complete_and_normalizable(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _publish_synthetic(first)
    _publish_synthetic(second)

    assert _tree_bytes(first) == _tree_bytes(second)
    result = onboarding.validate_local_pilot_request(first / "request.yaml")
    assert result.sample_count == 4
    assert result.pair_count == 2
    assert result.partition_count == 1
    assert result.fasta_contigs == (("chrSynthetic", 100_000),)
    assert result.transcript_count == 2
    metadata = json.loads((first / "fixture.json").read_text(encoding="utf-8"))
    assert metadata["read_pairs_per_library"] == 130
    assert metadata["expected_terminal_computational_result"] == {
        "absolute_af_difference": 0.4375,
        "all_sites_rows": 3,
        "common_odds_ratio": 15.0,
        "control_af": 0.0625,
        "interpretation": "computational smoke expectation; not scientific adjudication",
        "significant_candidate_id": "REV_like|chrSynthetic|50000|A>G",
        "significant_sites_rows": 1,
        "treatment_af": 0.5,
    }
    manifest = json.loads((first / synthetic_fixture.COMPLETION_MANIFEST).read_text())
    assert set(manifest) == set(_tree_bytes(first)) - {
        synthetic_fixture.COMPLETION_MANIFEST
    }
    for relative, record in manifest.items():
        data = (first / relative).read_bytes()
        assert record["size_bytes"] == len(data)
        assert record["sha256"] == hashlib.sha256(data).hexdigest()


def test_synthetic_fastqs_have_complete_matching_mates(tmp_path: Path) -> None:
    import gzip

    output = tmp_path / "fixture"
    _publish_synthetic(output)
    for sample in synthetic_fixture.SAMPLES:
        sample_id = str(sample["sample_id"])
        with gzip.open(output / f"inputs/reads/{sample_id}_R1.fastq.gz", "rt") as r1:
            r1_lines = r1.read().splitlines()
        with gzip.open(output / f"inputs/reads/{sample_id}_R2.fastq.gz", "rt") as r2:
            r2_lines = r2.read().splitlines()
        assert (
            len(r1_lines)
            == len(r2_lines)
            == 4 * synthetic_fixture.PAIR_COUNT_PER_LIBRARY
        )
        assert [line.removesuffix("/1") for line in r1_lines[::4]] == [
            line.removesuffix("/2") for line in r2_lines[::4]
        ]
        assert all(len(sequence) == 75 for sequence in r1_lines[1::4])
        assert all(len(sequence) == 75 for sequence in r2_lines[1::4])


def test_request_validation_is_read_only(tmp_path: Path) -> None:
    output = tmp_path / "fixture"
    _publish_synthetic(output)
    before = _tree_bytes(output)

    assert (
        onboarding.validate_from_args(
            argparse.Namespace(request=output / "request.yaml")
        )
        == 0
    )

    assert _tree_bytes(output) == before


def test_request_validation_reports_invalid_request(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing_request = tmp_path / "missing-request.yaml"

    assert (
        onboarding.validate_from_args(argparse.Namespace(request=missing_request)) == 1
    )
    assert "ERROR:" in capsys.readouterr().err


def test_public_cli_routes_synthetic_init_and_request_validation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "public-fixture"
    assert (
        cli.main(
            [
                "init",
                "synthetic-local-pilot",
                "--output-dir",
                str(output),
                "--execute",
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "validate",
                "local-pilot-request",
                "--request",
                str(output / "request.yaml"),
            ]
        )
        == 0
    )
    stdout = capsys.readouterr().out
    assert "Published deterministic local-pilot fixture" in stdout
    assert "Local-pilot request validation: PASS" in stdout


@pytest.mark.parametrize(
    ("target", "old", "new", "message"),
    (
        (
            "inputs/reference/genes.gtf",
            "chrSynthetic",
            "chrAbsent",
            "contig is absent from FASTA",
        ),
        (
            "partitions.tsv",
            "primary\tregion\tchrSynthetic",
            "primary\tregion\tchrSynthetic:99999-100001",
            "outside FASTA bounds",
        ),
    ),
)
def test_request_validation_rejects_reference_incompatibility(
    tmp_path: Path,
    target: str,
    old: str,
    new: str,
    message: str,
) -> None:
    output = tmp_path / "fixture"
    _publish_synthetic(output)
    path = output / target
    path.write_text(
        path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8"
    )

    with pytest.raises(onboarding.OnboardingError, match=message):
        onboarding.validate_local_pilot_request(output / "request.yaml")


def test_request_validation_checks_regions_file_against_fasta(tmp_path: Path) -> None:
    output = tmp_path / "fixture"
    _publish_synthetic(output)
    regions = output / "regions.tsv"
    regions.write_text("chrSynthetic\t1\t100000\n", encoding="utf-8")
    (output / "partitions.tsv").write_text(
        "partition_id\tselector_type\tselector_value\n"
        "primary\tregions_file\tregions.tsv\n",
        encoding="utf-8",
    )
    result = onboarding.validate_local_pilot_request(output / "request.yaml")
    assert result.partition_count == 1

    regions.write_text("chrAbsent\t1\t2\n", encoding="utf-8")
    with pytest.raises(onboarding.OnboardingError, match="absent from FASTA"):
        onboarding.validate_local_pilot_request(output / "request.yaml")


def test_request_validation_streams_gzip_regions_file(tmp_path: Path) -> None:
    import gzip

    output = tmp_path / "fixture"
    _publish_synthetic(output)
    regions = output / "regions.tsv.gz"
    with gzip.open(regions, "wt", encoding="utf-8", newline="") as handle:
        for start in range(1, 10_001):
            handle.write(f"chrSynthetic\t{start}\t{start}\n")
    (output / "partitions.tsv").write_text(
        "partition_id\tselector_type\tselector_value\n"
        "primary\tregions_file\tregions.tsv.gz\n",
        encoding="utf-8",
    )

    result = onboarding.validate_local_pilot_request(output / "request.yaml")

    assert result.partition_count == 1


def _runtime_files(
    tmp_path: Path,
) -> tuple[dict[str, Path], Path, Path, Path, Path, Path]:
    tool_dir = tmp_path / "tools"
    tool_dir.mkdir()
    tools = {
        check_id: _executable(tool_dir / command)
        for check_id, command in onboarding.PATH_TOOL_COMMANDS.items()
    }
    java = _executable(tmp_path / "java")
    rscript = _executable(tmp_path / "Rscript")
    picard = tmp_path / "picard.jar"
    picard.write_bytes(b"synthetic jar\n")
    renv = tmp_path / "renv-library"
    renv.mkdir()
    return tools, tool_dir, java, rscript, picard, renv


def test_runtime_preparation_renders_fixed_policy_without_probes(
    tmp_path: Path,
) -> None:
    tools, tool_dir, java, rscript, picard, renv = _runtime_files(tmp_path)
    payload = onboarding.render_runtime_profile(
        java=java,
        picard_jar=picard,
        rscript=rscript,
        renv_library=renv,
        explicit_tools={check_id: None for check_id in tools},
        environment={"PATH": str(tool_dir)},
        root=REPO_ROOT,
        python_executable=Path(sys.executable),
    )
    rows = list(
        csv.DictReader(payload.decode().splitlines(), delimiter="\t", strict=True)
    )
    by_id = {row["check_id"]: row for row in rows}
    assert by_id["java"]["target"] == str(java)
    assert by_id["picard_jar"]["target"] == str(picard)
    assert by_id["renv_library"]["target"] == str(renv)
    assert json.loads(by_id["picard"]["probe_args"])[1] == str(picard)
    assert json.loads(by_id["r_variant_annotation"]["probe_args"]) == [str(rscript)]
    assert by_id["star"]["target"] == str(tools["star"])
    rendered = tmp_path / "runtime.tsv"
    rendered.write_bytes(payload)
    _profile_bytes, checks = load_runtime_profile_contract(rendered)
    doctor.validate_runtime_profile_contract(checks, REPO_ROOT)


def test_runtime_preparation_rejects_ambiguous_path_tool(tmp_path: Path) -> None:
    tools, first_dir, java, rscript, picard, renv = _runtime_files(tmp_path)
    second_dir = tmp_path / "second"
    second_dir.mkdir()
    _executable(second_dir / "STAR", "#!/bin/sh\nexit 99\n")
    explicit = {check_id: path for check_id, path in tools.items()}
    explicit["star"] = None

    with pytest.raises(onboarding.OnboardingError, match="multiple executables"):
        onboarding.render_runtime_profile(
            java=java,
            picard_jar=picard,
            rscript=rscript,
            renv_library=renv,
            explicit_tools=explicit,
            environment={"PATH": f"{first_dir}{os.pathsep}{second_dir}"},
            root=REPO_ROOT,
        )


def _wrapper_environment(
    tmp_path: Path,
    python: Path,
    module_init: Path,
) -> dict[str, str]:
    log_dir = tmp_path / "logs"
    log_dir.mkdir(exist_ok=True)
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "NORAD_SLURM_ACCOUNT": "viking-users",
        "NORAD_SLURM_PARTITION": "short",
        "NORAD_SLURM_QOS": "normal",
        "NORAD_SLURM_CPUS": "4",
        "NORAD_SLURM_MEMORY": "8G",
        "NORAD_SLURM_TIME": "00:30:00",
        "NORAD_LOG_DIR": str(log_dir),
        "NORAD_SOURCE_CHECKOUT": str(tmp_path / "checkout"),
        "NORAD_PYTHON": str(python),
        "NORAD_REQUEST": str(tmp_path / "request.yaml"),
        "NORAD_WORKSPACE": str(tmp_path / "workspace"),
        "NORAD_RUNTIME_PROFILE": str(tmp_path / "runtime.tsv"),
        "NORAD_MODULE_INIT": str(module_init),
        "NORAD_MODULES": "java/17.0.10:star/2.7.11b:samtools/1.19.2",
        "NORAD_EXECUTE": "1",
    }


def test_slurm_wrapper_head_mode_only_submits_and_prints_tail(tmp_path: Path) -> None:
    members = onboarding.starter_members(root=REPO_ROOT)
    wrapper = tmp_path / "run-in-slurm.sh"
    wrapper.write_bytes(members["run-in-slurm.sh"][0])
    wrapper.chmod(0o755)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    capture = tmp_path / "sbatch.args"
    sbatch = _executable(
        bin_dir / "sbatch",
        "#!/bin/bash\nprintf '%s\\n' \"$@\" > \"$SBATCH_CAPTURE\"\nprintf '700123\\n'\n",
    )
    assert sbatch.is_file()
    fake_python = _executable(tmp_path / "python", '#!/bin/sh\ntouch "$PYTHON_RAN"\n')
    module_init = tmp_path / "modules.sh"
    module_init.write_text('touch "$MODULE_INIT_RAN"\n', encoding="utf-8")
    (tmp_path / "checkout").mkdir()
    environment = _wrapper_environment(tmp_path, fake_python, module_init)
    environment["PATH"] = f"{bin_dir}:{environment['PATH']}"
    environment["SBATCH_CAPTURE"] = str(capture)
    environment["PYTHON_RAN"] = str(tmp_path / "python-ran")
    environment["MODULE_INIT_RAN"] = str(tmp_path / "module-init-ran")

    result = subprocess.run(
        [str(wrapper)],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "JOB_ID=700123" in result.stdout
    assert "while [[ ! -e" in result.stdout
    assert "squeue -j 700123" in result.stdout
    assert "tail -n +1 -F" in result.stdout
    assert "norad-local-pilot-700123.out" in result.stdout
    assert not (tmp_path / "python-ran").exists()
    assert not (tmp_path / "module-init-ran").exists()
    arguments = capture.read_text(encoding="utf-8").splitlines()
    assert "--account=viking-users" in arguments
    assert "--partition=short" in arguments
    assert "--qos=normal" in arguments
    assert "--nodes=1" in arguments
    assert "--ntasks=1" in arguments
    assert any(
        argument.startswith("--export=") and "NORAD_SLURM_CPUS=4" in argument
        for argument in arguments
    )
    assert str(wrapper) == arguments[-1]


@pytest.mark.parametrize("unsafe", ("bad,value", "bad\nvalue"))
def test_slurm_wrapper_rejects_unsafe_export_values(
    tmp_path: Path,
    unsafe: str,
) -> None:
    wrapper = tmp_path / "run-in-slurm.sh"
    wrapper.write_bytes(
        onboarding.starter_members(root=REPO_ROOT)["run-in-slurm.sh"][0]
    )
    wrapper.chmod(0o755)
    fake_python = _executable(tmp_path / "python")
    module_init = tmp_path / "modules.sh"
    module_init.write_text("module() { :; }\n", encoding="utf-8")
    (tmp_path / "checkout").mkdir()
    environment = _wrapper_environment(tmp_path, fake_python, module_init)
    environment["NORAD_REQUEST"] = unsafe

    result = subprocess.run(
        [str(wrapper)],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    assert result.returncode == 2
    assert "newline or comma" in result.stderr


def test_slurm_wrapper_batch_mode_loads_exact_modules_then_doctors_and_runs(
    tmp_path: Path,
) -> None:
    wrapper = tmp_path / "run-in-slurm.sh"
    wrapper.write_bytes(
        onboarding.starter_members(root=REPO_ROOT)["run-in-slurm.sh"][0]
    )
    wrapper.chmod(0o755)
    module_capture = tmp_path / "modules.log"
    python_capture = tmp_path / "python.log"
    module_init = tmp_path / "modules.sh"
    module_init.write_text(
        'module() { printf \'%s\\n\' "$*" >> "$MODULE_CAPTURE"; }\n',
        encoding="utf-8",
    )
    fake_python = _executable(
        tmp_path / "python",
        '#!/bin/bash\nprintf \'%s\\n\' "$*" >> "$PYTHON_CAPTURE"\n',
    )
    (tmp_path / "checkout").mkdir()
    environment = _wrapper_environment(tmp_path, fake_python, module_init)
    environment.update(
        {
            "SLURM_JOB_ID": "700123",
            "MODULE_CAPTURE": str(module_capture),
            "PYTHON_CAPTURE": str(python_capture),
        }
    )

    result = subprocess.run(
        [str(wrapper)],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert module_capture.read_text(encoding="utf-8").splitlines() == [
        "load java/17.0.10",
        "load star/2.7.11b",
        "load samtools/1.19.2",
    ]
    invocations = python_capture.read_text(encoding="utf-8").splitlines()
    assert len(invocations) == 3
    assert "-m norad validate local-pilot-request" in invocations[0]
    assert "-m norad doctor local-pilot" in invocations[1]
    assert "-m norad run" in invocations[2]
    assert "--threads 4" in invocations[2]
    assert invocations[2].endswith("--execute")
