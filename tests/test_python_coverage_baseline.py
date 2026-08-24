import configparser
import copy
import importlib.metadata
import json
from pathlib import Path
from typing import Any

import pytest
from tests.tools import python_coverage_baseline as TOOL

REPO_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_CONTRACT_PATH = "src/emrys/contracts/scientific_evidence/_private_contract.py"
CONVERTER_PATH = "src/emrys/stages/gtf_to_bed12/converter.py"
MANIFEST_VALIDATOR_PATH = "src/emrys/ingestion/sample_manifest_admission/validator.py"


def summary(lines: tuple[int, int], branches: tuple[int, int]) -> dict[str, int]:
    return {
        "covered_lines": lines[0],
        "num_statements": lines[1],
        "covered_branches": branches[0],
        "num_branches": branches[1],
    }


def fixture_files() -> dict[str, dict[str, dict[str, int]]]:
    return {
        "src/emrys/contracts/orchestration/private_contract.py": {
            "summary": summary((90, 100), (34, 40))
        },
        "src/emrys/orchestration/local_pilot/private_control.py": {
            "summary": summary((80, 100), (28, 40))
        },
        "src/emrys/libraries/source_authority.py": {
            "summary": summary((88, 100), (34, 40))
        },
        "src/emrys/evidence/runtime_availability/private_admission.py": {
            "summary": summary((88, 100), (30, 40))
        },
        MANIFEST_VALIDATOR_PATH: {"summary": summary((90, 100), (36, 40))},
        CONVERTER_PATH: {"summary": summary((80, 100), (30, 40))},
        PRIVATE_CONTRACT_PATH: {"summary": summary((99, 100), (39, 40))},
        "src/emrys/libraries/validation/private_report.py": {
            "summary": summary((95, 100), (35, 40))
        },
        "src/emrys/libraries/alignments/private_alignment.py": {
            "summary": summary((96, 100), (36, 40))
        },
        "src/emrys/contracts/artifacts/private_receipt.py": {
            "summary": summary((80, 100), (28, 40))
        },
        "src/emrys/reporting/private_publication.py": {
            "summary": summary((70, 100), (20, 40))
        },
        "src/emrys/analyses/paired_cmh_candidate_ranking/private_validator.py": {
            "summary": summary((90, 100), (32, 40))
        },
        "scripts/example.py": {"summary": summary((30, 50), (10, 20))},
    }


def subprocess_fixture_files() -> dict[str, dict[str, dict[str, int]]]:
    return {
        CONVERTER_PATH: {"summary": summary((80, 100), (30, 40))},
        MANIFEST_VALIDATOR_PATH: {"summary": summary((90, 100), (36, 40))},
    }


def raw_document(
    files: dict[str, dict[str, dict[str, int]]] | None = None,
) -> dict[str, object]:
    measured = fixture_files() if files is None else files
    totals = {
        field: sum(item["summary"][field] for item in measured.values())
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
        "files": measured,
        "totals": totals,
    }


def snapshot() -> dict[str, Any]:
    return TOOL.build_snapshot(
        raw_document(),
        raw_document(subprocess_fixture_files()),
    )


def test_policy_is_deterministic_compact_and_ignores_coverage_metadata() -> None:
    first = raw_document()
    second = copy.deepcopy(first)
    second["meta"]["timestamp"] = "different"
    second["files"] = dict(reversed(list(second["files"].items())))

    subprocess_document = raw_document(subprocess_fixture_files())
    first_snapshot = TOOL.build_snapshot(first, subprocess_document)
    second_snapshot = TOOL.build_snapshot(second, subprocess_document)

    assert first_snapshot == second_snapshot
    assert "files" not in first_snapshot
    assert tuple(item["name"] for item in first_snapshot["critical_owners"]) == tuple(
        TOOL.CRITICAL_OWNER_GROUPS
    )
    assert tuple(item["name"] for item in first_snapshot["subprocess_routes"]) == tuple(
        TOOL.REQUIRED_SUBPROCESS_ROUTES
    )
    assert len(json.dumps(first_snapshot, indent=2).splitlines()) < 240


def test_campaign_b_critical_owner_floors_are_independent() -> None:
    assert {
        name: TOOL.CRITICAL_OWNER_GROUPS[name]
        for name in (
            "orchestration_machine_contracts",
            "local_pilot_control_plane",
            "source_checkout_admission",
            "runtime_availability_admission",
        )
    } == {
        "orchestration_machine_contracts": ("src/emrys/contracts/orchestration/",),
        "local_pilot_control_plane": ("src/emrys/orchestration/local_pilot/",),
        "source_checkout_admission": ("src/emrys/libraries/source_authority.py",),
        "runtime_availability_admission": ("src/emrys/evidence/runtime_availability/",),
    }


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    (
        ("schema_version", "wrong", "unsupported schema_version"),
        ("tool", {"name": "other"}, "unexpected coverage tool identity"),
        ("measurement", {"branch": False}, "unexpected measurement policy"),
        ("policy", {}, "unexpected coverage policy"),
    ),
)
def test_policy_contract_fields_are_enforced(
    field: str, replacement: object, message: str
) -> None:
    policy = snapshot()
    policy[field] = replacement
    with pytest.raises(TOOL.SnapshotError, match=message):
        TOOL.validate_snapshot(policy, "fixture")


def test_measurement_requires_branches_and_subprocess_owner_coverage() -> None:
    no_branches = raw_document()
    no_branches["meta"]["branch_coverage"] = False
    with pytest.raises(TOOL.SnapshotError, match="branch coverage"):
        TOOL.build_snapshot(no_branches, raw_document(subprocess_fixture_files()))

    subprocess_files = subprocess_fixture_files()
    subprocess_files[CONVERTER_PATH]["summary"] = summary((0, 100), (0, 40))
    subprocess_files["src/emrys/stages/gtf_to_bed12/validator.py"] = {
        "summary": summary((75, 100), (25, 40))
    }
    with pytest.raises(
        TOOL.SnapshotError,
        match="Subprocess coverage is missing for route emrys.convert.gtf_to_bed12",
    ):
        TOOL.build_snapshot(raw_document(), raw_document(subprocess_files))


@pytest.mark.parametrize(
    ("covered_field", "message"),
    (
        ("covered_lines", "line coverage regressed"),
        ("covered_branches", "branch coverage regressed"),
    ),
)
def test_check_rejects_exact_aggregate_regression(
    covered_field: str, message: str
) -> None:
    baseline = snapshot()
    files = fixture_files()
    files["scripts/example.py"]["summary"][covered_field] -= 1
    current = TOOL.build_snapshot(
        raw_document(files), raw_document(subprocess_fixture_files())
    )

    with pytest.raises(TOOL.SnapshotError, match=message):
        TOOL.compare_snapshots(baseline, current)


def test_check_rejects_critical_owner_regression_with_stable_aggregate() -> None:
    baseline = snapshot()
    files = fixture_files()
    files[PRIVATE_CONTRACT_PATH]["summary"]["covered_lines"] -= 1
    files["scripts/example.py"]["summary"]["covered_lines"] += 1
    current = TOOL.build_snapshot(
        raw_document(files), raw_document(subprocess_fixture_files())
    )

    with pytest.raises(
        TOOL.SnapshotError,
        match="Critical owner emrys.contracts.scientific_evidence line coverage regressed",
    ):
        TOOL.compare_snapshots(baseline, current)


def test_check_protects_shared_scientific_primitives_as_one_owner() -> None:
    baseline = snapshot()
    files = fixture_files()
    shared_path = "src/emrys/libraries/alignments/private_alignment.py"
    files[shared_path]["summary"]["covered_lines"] -= 1
    files["scripts/example.py"]["summary"]["covered_lines"] += 1
    current = TOOL.build_snapshot(
        raw_document(files), raw_document(subprocess_fixture_files())
    )

    with pytest.raises(
        TOOL.SnapshotError,
        match=(
            "Critical owner shared_scientific_validation_primitives "
            "line coverage regressed"
        ),
    ):
        TOOL.compare_snapshots(baseline, current)


def test_private_filename_move_does_not_change_the_policy() -> None:
    baseline = snapshot()
    files = fixture_files()
    moved = files.pop(PRIVATE_CONTRACT_PATH)
    files["src/emrys/contracts/scientific_evidence/_consolidated.py"] = moved
    current = TOOL.build_snapshot(
        raw_document(files), raw_document(subprocess_fixture_files())
    )

    assert current == baseline
    assert "passed" in TOOL.compare_snapshots(baseline, current)


@pytest.mark.parametrize(
    ("lines", "branches", "message"),
    (
        ((89, 100), (18, 20), "below 90%"),
        ((95, 100), (16, 20), "below 85%"),
    ),
)
def test_new_shared_module_thresholds_remain_explicit(
    lines: tuple[int, int], branches: tuple[int, int], message: str
) -> None:
    path = "src/emrys/libraries/new_shared.py"
    passing_files = fixture_files()
    passing_files[path] = {"summary": summary((95, 100), (18, 20))}
    TOOL.validate_new_shared_modules(raw_document(passing_files), [path])

    failing_files = fixture_files()
    failing_files[path] = {"summary": summary(lines, branches)}
    with pytest.raises(TOOL.SnapshotError, match=message):
        TOOL.validate_new_shared_modules(raw_document(failing_files), [path])


def test_repository_coverage_wiring_is_pinned_and_subprocess_aware() -> None:
    assert importlib.metadata.version("coverage") == TOOL.COVERAGE_VERSION

    config = configparser.ConfigParser()
    config.read(REPO_ROOT / ".coveragerc", encoding="utf-8")
    assert config.getboolean("run", "branch")
    assert config.getboolean("run", "parallel")
    assert config.getboolean("run", "relative_files")
    assert config.get("run", "source").split() == ["scripts", "src/emrys"]
    assert config.get("run", "patch").split() == ["subprocess"]

    makefile = (REPO_ROOT / "scripts" / "make_quality.mk").read_text(encoding="utf-8")
    assert "python-coverage-measure:" in makefile
    assert "python-coverage-check:" in makefile
    assert "python-coverage-baseline-update:" in makefile
    assert "PYTHON_COVERAGE_NEW_SHARED_MODULES ?=" in makefile
    assert '--coverage-json "$(PYTHON_COVERAGE_RAW)"' in makefile
    assert '--subprocess-coverage-json "$(PYTHON_SUBPROCESS_COVERAGE_RAW)"' in makefile
    for subprocess_test in TOOL.SUBPROCESS_TEST_COMMAND[4:]:
        assert subprocess_test in makefile
    for shared_module in (
        "src/emrys/libraries/installed_package_identity.py",
        "src/emrys/libraries/process_environment.py",
    ):
        assert shared_module in makefile
    assert "compileall -q scripts src/emrys tests" in makefile


def test_check_is_read_only_and_baseline_update_is_explicit(tmp_path: Path) -> None:
    raw_path = tmp_path / "coverage.json"
    subprocess_raw_path = tmp_path / "subprocess-coverage.json"
    current_path = tmp_path / "current.json"
    baseline_path = tmp_path / "baseline.json"
    raw_path.write_text(json.dumps(raw_document()), encoding="utf-8")
    subprocess_raw_path.write_text(
        json.dumps(raw_document(subprocess_fixture_files())),
        encoding="utf-8",
    )

    assert (
        TOOL.main(
            [
                "build",
                "--coverage-json",
                str(raw_path),
                "--subprocess-coverage-json",
                str(subprocess_raw_path),
                "--output",
                str(current_path),
            ]
        )
        == 0
    )
    baseline_path.write_bytes(current_path.read_bytes())
    accepted = baseline_path.read_bytes()

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
    assert baseline_path.read_bytes() == accepted
    makefile = (REPO_ROOT / "scripts" / "make_quality.mk").read_text(encoding="utf-8")
    update = makefile.split("python-coverage-baseline-update:", maxsplit=1)[1]
    assert 'cp "$(PYTHON_COVERAGE_CURRENT)" "$(PYTHON_COVERAGE_BASELINE)"' in update


def test_check_requires_raw_measurement_for_new_module(capsys: Any) -> None:
    with pytest.raises(SystemExit) as help_exit:
        TOOL.parse_args(["check", "--help"])
    assert help_exit.value.code == 0

    result = TOOL.main(
        [
            "check",
            "--baseline",
            "unused-baseline.json",
            "--current",
            "unused-current.json",
            "--new-shared-module",
            "src/emrys/libraries/new_shared.py",
        ]
    )
    assert result == 2
    assert "--coverage-json is required" in capsys.readouterr().err
