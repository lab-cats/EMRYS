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
    spec = importlib.util.spec_from_file_location("emrys_benchmark_stage_resources", SCRIPT_PATH)
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


def _comparison_case(**overrides: Any) -> dict[str, Any]:
    producer = [
        sys.executable,
        "-c",
        ("from pathlib import Path; import sys; Path(sys.argv[1]).write_text(sys.argv[2]); Path(sys.argv[3]).write_text(sys.argv[4])"),
        "{trial_dir}/product.txt",
        "{value}",
        "{trial_dir}/variant.txt",
        "{variant}",
    ]
    case: dict[str, Any] = {
        "name": "step06",
        "values": [2],
        "repetitions": 3,
        "warmup_repetitions": 1,
        "baseline_variant": "master",
        "setup_argv": None,
        "variants": [
            {"name": "changed", "producer_argv": producer},
            {"name": "master", "producer_argv": producer},
        ],
        "validator_argv": [
            sys.executable,
            "-c",
            "from pathlib import Path; import sys; assert Path(sys.argv[1]).read_text() == '2'",
            "{trial_dir}/product.txt",
        ],
        "artifact_paths": ["{trial_dir}/product.txt"],
    }
    case.update(overrides)
    return case


def _write_comparison_manifest(path: Path, case: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump(
            {"schema_version": BENCHMARK.COMPARISON_SCHEMA_VERSION, "cases": [case]},
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
                producer_argv=["producer", "--threads", "{value}", "{variant}"],
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
    assert "{variant}" in printed
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


@pytest.mark.parametrize(
    ("override", "message"),
    (
        ({"name": ".."}, "safe identifier"),
        ({"repetitions": 2}, "at least 3"),
        ({"warmup_repetitions": -1}, "must be nonnegative"),
        ({"baseline_variant": "missing"}, "must name a variant"),
        ({"artifact_paths": None}, "artifact_paths must be nonempty"),
    ),
)
def test_comparison_manifest_rejects_invalid_cases(tmp_path: Path, override: dict[str, Any], message: str) -> None:
    manifest = _write_comparison_manifest(tmp_path / "benchmark.yaml", _comparison_case(**override))

    with pytest.raises(BENCHMARK.BenchmarkError, match=message):
        BENCHMARK._load_comparison_manifest(manifest)


def test_comparison_dry_run_is_balanced_and_writes_nothing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert BENCHMARK._expand(("{trial_dir}", "{variant}"), value=2, trial_dir=tmp_path / "{variant}", variant="master") == (str(tmp_path / "{variant}"), "master")
    case = _comparison_case(repetitions=4, warmup_repetitions=0)
    case.pop("setup_argv")
    manifest = _write_comparison_manifest(tmp_path / "benchmark.yaml", case)
    output = tmp_path / "results"

    assert BENCHMARK.run(manifest, output, execute=False) == 0
    assert not output.exists()
    cases = [line for line in capsys.readouterr().out.splitlines() if line.startswith("CASE ")]
    assert [line.rsplit("=", 1)[-1] for line in cases] == [
        "master",
        "changed",
        "changed",
        "master",
        "master",
        "changed",
        "changed",
        "master",
    ]


def test_comparison_executes_warmups_and_explicit_baseline_pairs(
    tmp_path: Path,
) -> None:
    manifest = _write_comparison_manifest(tmp_path / "benchmark.yaml", _comparison_case())
    output = tmp_path / "results"

    assert BENCHMARK.run(manifest, output, execute=True) == 0
    rows = _read_tsv(output / "trials.tsv")
    assert len(rows) == 8
    measured = [row for row in rows if row["trial_kind"] == "measured"]
    assert [(row["repetition"], row["variant"]) for row in measured] == [
        ("1", "master"),
        ("1", "changed"),
        ("2", "changed"),
        ("2", "master"),
        ("3", "master"),
        ("3", "changed"),
    ]
    assert {row["artifact_match_baseline"] for row in rows} == {"yes"}
    assert all((Path(row["trial_dir"]) / "variant.txt").read_text() == row["variant"] for row in rows)
    summary = _read_tsv(output / "summary.tsv")
    assert {row["comparison_valid"] for row in summary} == {"yes"}
    assert {row["artifact_parity"] for row in summary} == {"yes"}
    assert {row["warmups_valid"] for row in summary} == {"yes"}
    assert {row["successful_repetitions"] for row in summary} == {"3"}
    assert {row["paired_repetitions"] for row in summary} == {"3"}
    assert all(row["median_cpu_seconds"] for row in summary)
    assert all(row["median_max_rss_kib"] for row in summary)
    assert all(row["median_paired_speedup_ratio"] for row in summary)


def test_comparison_artifact_mismatch_invalidates_summary(tmp_path: Path) -> None:
    producer = [
        sys.executable,
        "-c",
        "from pathlib import Path; import sys; Path(sys.argv[1]).write_text(sys.argv[2])",
        "{trial_dir}/product.txt",
        "{variant}",
    ]
    case = _comparison_case(
        warmup_repetitions=0,
        variants=[
            {"name": "master", "producer_argv": producer},
            {"name": "changed", "producer_argv": producer},
        ],
        validator_argv=[sys.executable, "-c", "pass"],
    )
    manifest = _write_comparison_manifest(tmp_path / "benchmark.yaml", case)
    output = tmp_path / "results"

    assert BENCHMARK.run(manifest, output, execute=True) == 1
    rows = _read_tsv(output / "trials.tsv")
    assert [row["status"] for row in rows if row["variant"] == "master"] == [
        "pass",
        "pass",
        "pass",
    ]
    assert [row["artifact_match_baseline"] for row in rows if row["variant"] == "changed"] == [
        "no",
        "no",
        "no",
    ]
    changed = next(row for row in _read_tsv(output / "summary.tsv") if row["variant"] == "changed")
    assert changed["comparison_valid"] == "no"
    assert changed["artifact_parity"] == "no"
    assert changed["median_paired_speedup_percent"] == ""


def test_comparison_rejects_artifact_drift_between_repetitions(
    tmp_path: Path,
) -> None:
    producer = [
        sys.executable,
        "-c",
        (
            "from pathlib import Path; import sys; "
            "output = Path(sys.argv[1]); "
            "output.write_text(output.parents[1].name)"
        ),
        "{trial_dir}/product.txt",
    ]
    case = _comparison_case(
        warmup_repetitions=0,
        variants=[
            {"name": "master", "producer_argv": producer},
            {"name": "changed", "producer_argv": producer},
        ],
        validator_argv=[sys.executable, "-c", "pass"],
    )
    manifest = _write_comparison_manifest(tmp_path / "benchmark.yaml", case)
    output = tmp_path / "results"

    assert BENCHMARK.run(manifest, output, execute=True) == 1
    rows = _read_tsv(output / "trials.tsv")
    assert {row["artifact_match_baseline"] for row in rows} == {"yes"}
    for variant in ("master", "changed"):
        assert [row["status"] for row in rows if row["variant"] == variant] == [
            "pass",
            "fail",
            "fail",
        ]
    summary = _read_tsv(output / "summary.tsv")
    assert {row["comparison_valid"] for row in summary} == {"no"}
    assert {row["artifact_parity"] for row in summary} == {"no"}
    assert {row["median_paired_speedup_percent"] for row in summary} == {""}


def test_comparison_failed_warmup_invalidates_measured_summary(tmp_path: Path) -> None:
    case = _comparison_case(
        setup_argv=[
            sys.executable,
            "-c",
            "import sys; raise SystemExit(7 if 'warmups' in sys.argv[1] else 0)",
            "{trial_dir}",
        ]
    )
    manifest = _write_comparison_manifest(tmp_path / "benchmark.yaml", case)
    output = tmp_path / "results"

    assert BENCHMARK.run(manifest, output, execute=True) == 1
    summary = _read_tsv(output / "summary.tsv")
    assert {row["warmups_valid"] for row in summary} == {"no"}
    assert {row["comparison_valid"] for row in summary} == {"no"}
    assert {row["median_paired_speedup_percent"] for row in summary} == {""}


def test_comparison_summary_reports_paired_speedup_and_spread(tmp_path: Path) -> None:
    case = BENCHMARK._load_comparison_manifest(_write_comparison_manifest(tmp_path / "benchmark.yaml", _comparison_case(warmup_repetitions=0)))[0]
    results = []
    for repetition, baseline in enumerate((10.0, 20.0, 30.0), start=1):
        for variant, wall in (("master", baseline), ("changed", baseline / 2)):
            results.append(
                {
                    "case": "step06",
                    "value": 2,
                    "variant": variant,
                    "trial_kind": "measured",
                    "repetition": repetition,
                    "status": "pass",
                    "producer_wall_seconds": str(wall),
                    "producer_cpu_seconds": str(wall / 2),
                    "producer_max_rss_kib": "100",
                    "producer_input_blocks": "4",
                    "producer_output_blocks": "2",
                    "artifact_match_baseline": "yes",
                }
            )
    summary = tmp_path / "summary.tsv"

    BENCHMARK._write_comparison_summary((case,), results, summary)

    changed = next(row for row in _read_tsv(summary) if row["variant"] == "changed")
    assert changed["median_wall_seconds"] == "10.000000"
    assert changed["wall_mad_seconds"] == "5.000000"
    assert changed["wall_range_seconds"] == "10.000000"
    assert changed["median_cpu_seconds"] == "5.000000"
    assert changed["median_max_rss_kib"] == "100"
    assert changed["median_input_blocks"] == "4"
    assert changed["median_output_blocks"] == "2"
    assert changed["median_paired_speedup_percent"] == "50.000000"
    assert changed["median_paired_speedup_ratio"] == "2.000000"


def test_main_reports_operator_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "results"

    assert BENCHMARK.main(
        ["--manifest", str(tmp_path / "missing.yaml"), "--output", str(output)]
    ) == 2
    assert "benchmark-stage-resources: error:" in capsys.readouterr().err
