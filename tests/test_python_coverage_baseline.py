import configparser
import copy
import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPO_ROOT / "tests" / "tools" / "python_coverage_baseline.py"
SPEC = importlib.util.spec_from_file_location("python_coverage_baseline", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)


def summary(lines: tuple[int, int], branches: tuple[int, int]) -> dict[str, int]:
    return {
        "covered_lines": lines[0],
        "num_statements": lines[1],
        "covered_branches": branches[0],
        "num_branches": branches[1],
    }


def raw_document() -> dict[str, object]:
    files = {
        "src/norad/ingestion/sample_manifest_admission/validate_manifest.py": {
            "summary": summary((90, 100), (36, 40))
        },
        "src/norad/stages/convert_GTF_to_BED12/gtf_to_bed12.py": {
            "summary": summary((80, 100), (30, 40))
        },
        "scripts/example.py": {
            "summary": summary((30, 50), (10, 20))
        },
    }
    totals = {
        field: sum(item["summary"][field] for item in files.values())
        for field in TOOL.COUNT_FIELDS
    }
    return {
        "meta": {
            "format": 3,
            "version": TOOL.COVERAGE_VERSION,
            "timestamp": "ignored",
            "branch_coverage": True,
            "show_contexts": False,
        },
        "files": files,
        "totals": totals,
    }


def test_snapshot_is_deterministic_and_ignores_coverage_metadata() -> None:
    first = raw_document()
    second = copy.deepcopy(first)
    second["meta"]["timestamp"] = "different"
    second["files"] = dict(reversed(list(second["files"].items())))

    first_snapshot = TOOL.build_snapshot(first)
    second_snapshot = TOOL.build_snapshot(second)

    assert first_snapshot == second_snapshot
    assert json.dumps(first_snapshot, sort_keys=True) == json.dumps(
        second_snapshot, sort_keys=True
    )
    assert [item["path"] for item in first_snapshot["files"]] == sorted(
        item["path"] for item in first_snapshot["files"]
    )


def test_snapshot_requires_branch_and_subprocess_coverage() -> None:
    no_branches = raw_document()
    no_branches["meta"]["branch_coverage"] = False
    with pytest.raises(TOOL.SnapshotError, match="branch coverage"):
        TOOL.build_snapshot(no_branches)

    no_subprocess = raw_document()
    no_subprocess["files"][
        "src/norad/ingestion/sample_manifest_admission/validate_manifest.py"
    ]["summary"] = summary((0, 100), (0, 40))
    no_subprocess["totals"]["covered_lines"] -= 90
    no_subprocess["totals"]["covered_branches"] -= 36
    with pytest.raises(TOOL.SnapshotError, match="Subprocess coverage"):
        TOOL.build_snapshot(no_subprocess)


@pytest.mark.parametrize(
    ("covered_field", "amount", "message"),
    (
        ("covered_lines", 1, "line coverage regressed"),
        ("covered_branches", 1, "branch coverage regressed"),
    ),
)
def test_check_rejects_global_regression(
    covered_field: str, amount: int, message: str
) -> None:
    baseline = TOOL.build_snapshot(raw_document())
    current = copy.deepcopy(baseline)
    current["files"][0][covered_field] -= amount
    path = current["files"][0]["path"]
    counts = {
        field: current["files"][0][field] for field in TOOL.COUNT_FIELDS
    }
    current["files"][0] = TOOL.measured_file(path, counts)
    aggregate = {
        field: sum(item[field] for item in current["files"])
        for field in TOOL.COUNT_FIELDS
    }
    current["totals"] = {
        **aggregate,
        "line_rate": TOOL.rate_text(
            aggregate["covered_lines"], aggregate["num_statements"]
        ),
        "branch_rate": TOOL.rate_text(
            aggregate["covered_branches"], aggregate["num_branches"]
        ),
    }

    with pytest.raises(TOOL.SnapshotError, match=message):
        TOOL.compare_snapshots(baseline, current)


def test_new_shared_module_thresholds_are_explicit() -> None:
    baseline = TOOL.build_snapshot(raw_document())
    current = copy.deepcopy(baseline)
    shared_path = "src/norad/libraries/validation_report.py"
    new_module = TOOL.measured_file(
        shared_path, summary((95, 100), (18, 20))
    )
    current["files"].append(new_module)
    current["files"].sort(key=lambda item: item["path"])
    aggregate = {
        field: sum(item[field] for item in current["files"])
        for field in TOOL.COUNT_FIELDS
    }
    current["totals"] = {
        **aggregate,
        "line_rate": TOOL.rate_text(
            aggregate["covered_lines"], aggregate["num_statements"]
        ),
        "branch_rate": TOOL.rate_text(
            aggregate["covered_branches"], aggregate["num_branches"]
        ),
    }

    assert "passed" in TOOL.compare_snapshots(
        baseline, current, [shared_path]
    )
    # The threshold remains enforceable after the reviewed snapshot promotes
    # the new owner into the tracked baseline.
    assert "passed" in TOOL.compare_snapshots(
        copy.deepcopy(current), current, [shared_path]
    )

    shared_index = next(
        index
        for index, item in enumerate(current["files"])
        if item["path"] == shared_path
    )
    current["files"][shared_index] = TOOL.measured_file(
        shared_path, summary((89, 100), (16, 20))
    )
    aggregate = {
        field: sum(item[field] for item in current["files"])
        for field in TOOL.COUNT_FIELDS
    }
    current["totals"] = {
        **aggregate,
        "line_rate": TOOL.rate_text(
            aggregate["covered_lines"], aggregate["num_statements"]
        ),
        "branch_rate": TOOL.rate_text(
            aggregate["covered_branches"], aggregate["num_branches"]
        ),
    }
    with pytest.raises(TOOL.SnapshotError, match="below 90%"):
        TOOL.compare_snapshots(baseline, current, [shared_path])

    current["files"][shared_index] = TOOL.measured_file(
        shared_path, summary((95, 100), (16, 20))
    )
    aggregate = {
        field: sum(item[field] for item in current["files"])
        for field in TOOL.COUNT_FIELDS
    }
    current["totals"] = {
        **aggregate,
        "line_rate": TOOL.rate_text(
            aggregate["covered_lines"], aggregate["num_statements"]
        ),
        "branch_rate": TOOL.rate_text(
            aggregate["covered_branches"], aggregate["num_branches"]
        ),
    }
    with pytest.raises(TOOL.SnapshotError, match="below 85%"):
        TOOL.compare_snapshots(baseline, current, [shared_path])


def test_repository_coverage_wiring_is_pinned_and_subprocess_aware() -> None:
    requirements = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert f"coverage=={TOOL.COVERAGE_VERSION}" in requirements.splitlines()

    config = configparser.ConfigParser()
    config.read(REPO_ROOT / ".coveragerc", encoding="utf-8")
    assert config.getboolean("run", "branch")
    assert config.getboolean("run", "parallel")
    assert config.getboolean("run", "relative_files")
    assert config.get("run", "source").split() == [
        "scripts",
        "src/norad",
    ]
    assert config.get("run", "patch").split() == ["subprocess"]

    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "python-coverage-measure:" in makefile
    assert "python-coverage-check:" in makefile
    assert "python-coverage-baseline-update:" in makefile
    assert "--new-shared-module scripts/git_orchestration/_common.py" in makefile
    assert (
        "--new-shared-module src/norad/contracts/scientific_evidence/step08.py"
        in makefile
    )
    assert (
        "--new-shared-module src/norad/contracts/scientific_evidence/step09.py"
        in makefile
    )
    assert (
        "--new-shared-module "
        "src/norad/contracts/scientific_evidence/review_package.py" in makefile
    )
    assert (
        "--new-shared-module src/norad/libraries/validation_report.py" in makefile
    )
    assert "compileall -q scripts src/norad tests" in makefile


def test_cli_help_build_and_check_interfaces(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as help_exit:
        TOOL.parse_args(["check", "--help"])
    assert help_exit.value.code == 0

    raw_path = tmp_path / "coverage.json"
    current_path = tmp_path / "current.json"
    baseline_path = tmp_path / "baseline.json"
    raw_path.write_text(json.dumps(raw_document()), encoding="utf-8")

    assert (
        TOOL.main(
            [
                "build",
                "--coverage-json",
                str(raw_path),
                "--output",
                str(current_path),
            ]
        )
        == 0
    )
    baseline_path.write_bytes(current_path.read_bytes())
    assert (
        TOOL.main(
            [
                "check",
                "--baseline",
                str(baseline_path),
                "--current",
                str(current_path),
            ]
        )
        == 0
    )
