"""Behavior tests for the opt-in resource benchmark utility."""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "benchmark_stage_resources.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("norad_benchmark_stage_resources", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BENCHMARK = _load_script()


def _case(**overrides: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "name": "threads",
        "values": [1],
        "repetitions": 1,
        "setup_argv": None,
        "producer_argv": [sys.executable, "-c", "pass"],
        "validator_argv": [sys.executable, "-c", "pass"],
    }
    value.update(overrides)
    return value


def _write_manifest(path: Path, cases: list[dict[str, Any]]) -> Path:
    path.write_text(
        yaml.safe_dump(
            {"schema_version": BENCHMARK.SCHEMA_VERSION, "cases": cases},
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


@pytest.mark.parametrize(
    ("document", "message"),
    (
        (
            {"schema_version": BENCHMARK.SCHEMA_VERSION},
            "Benchmark manifest keys must be schema_version and cases",
        ),
        ({"schema_version": "wrong", "cases": [_case()]}, "schema_version must be"),
        (
            {"schema_version": BENCHMARK.SCHEMA_VERSION, "cases": []},
            "cases must be a nonempty array",
        ),
        (
            {"schema_version": BENCHMARK.SCHEMA_VERSION, "cases": [_case(name="bad name")]},
            "safe identifier",
        ),
        (
            {
                "schema_version": BENCHMARK.SCHEMA_VERSION,
                "cases": [_case(), _case()],
            },
            "Duplicate benchmark case name",
        ),
        (
            {"schema_version": BENCHMARK.SCHEMA_VERSION, "cases": [_case(values=[1, 1])]},
            "distinct positive integers",
        ),
        (
            {"schema_version": BENCHMARK.SCHEMA_VERSION, "cases": [_case(repetitions=0)]},
            "positive integer",
        ),
        (
            {
                "schema_version": BENCHMARK.SCHEMA_VERSION,
                "cases": [_case(producer_argv=[])],
            },
            "nonempty argv string array",
        ),
        (
            {
                "schema_version": BENCHMARK.SCHEMA_VERSION,
                "cases": [_case(artifact_paths=["outside.tsv"])],
            },
            "paths containing",
        ),
    ),
)
def test_manifest_admission_rejects_invalid_documents(
    tmp_path: Path,
    document: dict[str, Any],
    message: str,
) -> None:
    manifest = tmp_path / "benchmark.yaml"
    manifest.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    with pytest.raises(BENCHMARK.BenchmarkError, match=message):
        BENCHMARK._load_manifest(manifest)


def test_dry_run_prints_expanded_commands_without_writing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = _write_manifest(
        tmp_path / "benchmark.yaml",
        [
            _case(
                values=[2],
                setup_argv=["setup", "{trial_dir}"],
                producer_argv=["producer", "--threads", "{value}"],
                validator_argv=["validator", "{trial_dir}", "{value}"],
            )
        ],
    )
    output = tmp_path / "results"

    assert BENCHMARK.run(manifest, output, execute=False) == 0
    assert not output.exists()
    printed = capsys.readouterr().out
    assert "CASE threads value=2 repetition=1" in printed
    assert "producer --threads 2" in printed
    assert str(output / "trials" / "threads" / "2" / "rep-01") in printed
    assert "Dry-run complete; no benchmark state was written." in printed


def test_execute_records_successful_trial_and_summary(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path / "benchmark.yaml",
        [
            _case(
                values=[2],
                setup_argv=[
                    sys.executable,
                    "-c",
                    "from pathlib import Path; Path(__import__('sys').argv[1]).write_text('ready')",
                    "{trial_dir}/setup.txt",
                ],
                producer_argv=[
                    sys.executable,
                    "-c",
                    (
                        "from pathlib import Path; import sys; "
                        "assert Path(sys.argv[1]).read_text() == 'ready'; "
                        "Path(sys.argv[2]).write_text(sys.argv[3])"
                    ),
                    "{trial_dir}/setup.txt",
                    "{trial_dir}/product.txt",
                    "{value}",
                ],
                validator_argv=[
                    sys.executable,
                    "-c",
                    (
                        "from pathlib import Path; import sys; "
                        "assert Path(sys.argv[1]).read_text() == sys.argv[2]"
                    ),
                    "{trial_dir}/product.txt",
                    "{value}",
                ],
                artifact_paths=["{trial_dir}/product.txt"],
            )
        ],
    )
    output = tmp_path / "results"

    assert BENCHMARK.run(manifest, output, execute=True) == 0

    trial_rows = _read_tsv(output / "trials.tsv")
    assert len(trial_rows) == 1
    assert trial_rows[0]["status"] == "pass"
    assert trial_rows[0]["producer_exit_code"] == "0"
    assert float(trial_rows[0]["producer_wall_seconds"]) > 0
    assert float(trial_rows[0]["producer_cpu_seconds"]) >= 0
    assert int(trial_rows[0]["producer_max_rss_kib"]) > 0
    assert int(trial_rows[0]["producer_input_blocks"]) >= 0
    assert int(trial_rows[0]["producer_output_blocks"]) >= 0
    assert len(trial_rows[0]["artifact_set_sha256"]) == 64
    assert trial_rows[0]["artifact_match_baseline"] == "yes"
    trial = Path(trial_rows[0]["trial_dir"])
    assert (trial / "product.txt").read_text(encoding="utf-8") == "2"
    assert (trial / "producer.time.txt").read_text(encoding="utf-8").startswith(
        "wall_seconds\t"
    )
    artifact_rows = _read_tsv(trial / "producer.artifacts.tsv")
    assert len(artifact_rows) == 1
    assert artifact_rows[0]["path"] == str((trial / "product.txt").resolve())
    assert len(artifact_rows[0]["sha256"]) == 64

    assert _read_tsv(output / "summary.tsv") == [
        {
            "case": "threads",
            "value": "2",
            "successful_repetitions": "1",
            "median_wall_seconds": trial_rows[0]["producer_wall_seconds"],
            "median_cpu_seconds": trial_rows[0]["producer_cpu_seconds"],
            "median_max_rss_kib": trial_rows[0]["producer_max_rss_kib"],
            "median_input_blocks": trial_rows[0]["producer_input_blocks"],
            "median_output_blocks": trial_rows[0]["producer_output_blocks"],
            "recommended": "yes",
        }
    ]


def test_execute_records_setup_producer_and_validator_failures(tmp_path: Path) -> None:
    fail = lambda code: [sys.executable, "-c", f"raise SystemExit({code})"]
    manifest = _write_manifest(
        tmp_path / "benchmark.yaml",
        [
            _case(name="setup", setup_argv=fail(4)),
            _case(name="producer", producer_argv=fail(3)),
            _case(name="validator", validator_argv=fail(5)),
        ],
    )
    output = tmp_path / "results"

    assert BENCHMARK.run(manifest, output, execute=True) == 1

    rows = {row["case"]: row for row in _read_tsv(output / "trials.tsv")}
    assert {
        name: (
            row["status"],
            row["setup_exit_code"],
            row["producer_exit_code"],
            row["validator_exit_code"],
        )
        for name, row in rows.items()
    } == {
        "setup": ("fail", "4", "-1", "-1"),
        "producer": ("fail", "0", "3", "-1"),
        "validator": ("fail", "0", "0", "5"),
    }
    assert _read_tsv(output / "summary.tsv") == []


def test_summary_recommends_smallest_value_within_five_percent(tmp_path: Path) -> None:
    results = [
        {
            "case": "threads",
            "value": 1,
            "status": "pass",
            "producer_wall_seconds": "103.0",
            "producer_cpu_seconds": "90.0",
            "producer_max_rss_kib": "",
            "producer_input_blocks": "10",
            "producer_output_blocks": "20",
        },
        {
            "case": "threads",
            "value": 2,
            "status": "pass",
            "producer_wall_seconds": "100.0",
            "producer_cpu_seconds": "95.0",
            "producer_max_rss_kib": "200",
            "producer_input_blocks": "12",
            "producer_output_blocks": "22",
        },
        {
            "case": "threads",
            "value": 4,
            "status": "fail",
            "producer_wall_seconds": "90.0",
            "producer_cpu_seconds": "80.0",
            "producer_max_rss_kib": "100",
            "producer_input_blocks": "8",
            "producer_output_blocks": "18",
        },
    ]
    summary = tmp_path / "summary.tsv"

    BENCHMARK._write_summary(results, summary)

    rows = _read_tsv(summary)
    assert [row["value"] for row in rows] == ["1", "2"]
    assert [row["recommended"] for row in rows] == ["yes", "no"]
    assert rows[0]["median_max_rss_kib"] == ""
    assert rows[0]["median_cpu_seconds"] == "90.000000"
    assert rows[0]["median_input_blocks"] == "10"
    assert rows[0]["median_output_blocks"] == "20"


def test_artifact_identity_marks_changed_output_as_failed(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path / "benchmark.yaml",
        [
            _case(
                values=[1, 2],
                producer_argv=[
                    sys.executable,
                    "-c",
                    (
                        "from pathlib import Path; import sys; "
                        "Path(sys.argv[1]).write_text(sys.argv[2])"
                    ),
                    "{trial_dir}/product.txt",
                    "{value}",
                ],
                artifact_paths=["{trial_dir}/product.txt"],
            )
        ],
    )
    output = tmp_path / "results"

    assert BENCHMARK.run(manifest, output, execute=True) == 1

    rows = _read_tsv(output / "trials.tsv")
    assert [row["status"] for row in rows] == ["pass", "fail"]
    assert [row["artifact_match_baseline"] for row in rows] == ["yes", "no"]
    assert rows[0]["artifact_set_sha256"] != rows[1]["artifact_set_sha256"]


def test_run_rejects_existing_output_and_nonreal_parent(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path / "benchmark.yaml", [_case()])
    existing = tmp_path / "existing"
    existing.mkdir()

    with pytest.raises(BENCHMARK.BenchmarkError, match="must be absent"):
        BENCHMARK.run(manifest, existing, execute=False)

    parent_link = tmp_path / "parent-link"
    parent_link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(BENCHMARK.BenchmarkError, match="existing real directory"):
        BENCHMARK.run(manifest, parent_link / "results", execute=False)


def test_main_reports_operator_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "results"

    assert BENCHMARK.main(
        ["--manifest", str(tmp_path / "missing.yaml"), "--output", str(output)]
    ) == 2
    assert "benchmark-stage-resources: error:" in capsys.readouterr().err
