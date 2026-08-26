"""Focused protection for the bounded Python source-dependency gate."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from tests.tools import source_dependencies as TOOL

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_TOPOLOGY = REPO_ROOT / "src" / "emrys" / "contracts" / "SOURCE_TOPOLOGY.md"


def write_repository(tmp_path: Path, sources: dict[str, str]) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    initialized = subprocess.run(
        ["git", "init", "-q", str(repository)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert initialized.returncode == 0, initialized.stderr
    complete_sources = {"src/emrys/__init__.py": ""}
    complete_sources.update(sources)
    for relative, source in complete_sources.items():
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    return repository


def source_snapshot(root: Path) -> tuple[tuple[str, int, int], ...]:
    return tuple(
        sorted(
            (
                path.relative_to(root).as_posix(),
                path.stat().st_size,
                path.stat().st_mtime_ns,
            )
            for path in (root / "src" / "emrys").rglob("*.py")
        )
    )


def inspect_fixture(
    repository: Path,
    *,
    transitions: tuple[TOOL.Transition, ...] = (),
    composition_seams: tuple[TOOL.CompositionSeam, ...] = (),
) -> TOOL.ValidationResult:
    return TOOL.inspect_repository(
        repository,
        transitions=transitions,
        composition_seams=composition_seams,
    )


@pytest.mark.parametrize(
    ("sources", "rule_id", "target"),
    (
        (
            {
                "src/emrys/contracts/schema.py": (
                    "from emrys.libraries import helper\n"
                ),
                "src/emrys/libraries/helper.py": "",
            },
            TOOL.RULE_CONTRACT_NEUTRAL,
            "emrys.libraries.helper",
        ),
        (
            {
                "src/emrys/libraries/helper.py": (
                    "from emrys.stages.alpha import worker\n"
                ),
                "src/emrys/stages/alpha/worker.py": "",
            },
            TOOL.RULE_LIBRARY_NEUTRAL,
            "emrys.stages.alpha.worker",
        ),
        (
            {
                "src/emrys/stages/alpha/worker.py": (
                    "from emrys.stages.beta import worker\n"
                ),
                "src/emrys/stages/beta/worker.py": "",
            },
            TOOL.RULE_FUNCTIONAL_OWNER,
            "emrys.stages.beta.worker",
        ),
        (
            {
                "src/emrys/ingestion/admit.py": (
                    "from emrys.evidence.runtime import inspector\n"
                ),
                "src/emrys/evidence/runtime/inspector.py": "",
            },
            TOOL.RULE_INGESTION_BOUNDARY,
            "emrys.evidence.runtime.inspector",
        ),
        (
            {
                "src/emrys/reporting/view.py": (
                    "from emrys.analyses.ranking import result\n"
                ),
                "src/emrys/analyses/ranking/result.py": "",
            },
            TOOL.RULE_REPORTING_DOWNSTREAM,
            "emrys.analyses.ranking.result",
        ),
        (
            {
                "src/emrys/orchestration/control.py": (
                    "from emrys.stages.alpha import worker\n"
                ),
                "src/emrys/stages/alpha/worker.py": "",
            },
            TOOL.RULE_ORCHESTRATION_BOUNDARY,
            "emrys.stages.alpha.worker",
        ),
        (
            {
                "src/emrys/__main__.py": (
                    "from emrys.reporting import _private\n"
                ),
                "src/emrys/reporting/_private.py": "",
            },
            TOOL.RULE_PRIVATE_OWNER,
            "emrys.reporting._private",
        ),
        (
            {
                "src/emrys/libraries/alpha/client.py": (
                    "from emrys.libraries.beta import _private\n"
                ),
                "src/emrys/libraries/beta/_private.py": "",
            },
            TOOL.RULE_PRIVATE_OWNER,
            "emrys.libraries.beta._private",
        ),
        (
            {
                "src/emrys/__init__.py": (
                    "from emrys.reporting import view\n"
                ),
                "src/emrys/reporting/view.py": "",
            },
            TOOL.RULE_SOURCE_CLASSIFICATION,
            "emrys.reporting.view",
        ),
        (
            {
                "src/emrys/libraries/helper.py": "import emrys.__main__\n",
                "src/emrys/__main__.py": "",
            },
            TOOL.RULE_COMPOSITION_DIRECTION,
            "emrys.__main__",
        ),
    ),
)
def test_each_durable_negative_rule_rejects_a_seeded_edge(
    tmp_path: Path,
    sources: dict[str, str],
    rule_id: str,
    target: str,
) -> None:
    repository = write_repository(tmp_path, sources)

    result = inspect_fixture(repository)

    assert len(result.problems) == 1
    problem = result.problems[0]
    assert problem.rule_id == rule_id
    assert problem.line == 1
    assert target in problem.detail
    assert problem.render().startswith(f"{problem.source_path}:1: [{rule_id}]")


def test_relative_peer_import_is_resolved_without_importing_source(
    tmp_path: Path,
) -> None:
    repository = write_repository(
        tmp_path,
        {
            "src/emrys/stages/__init__.py": "",
            "src/emrys/stages/alpha/__init__.py": "",
            "src/emrys/stages/alpha/worker.py": "from ..beta import worker\n",
            "src/emrys/stages/beta/__init__.py": "",
            "src/emrys/stages/beta/worker.py": "raise RuntimeError('must not run')\n",
        },
    )

    result = inspect_fixture(repository)

    assert len(result.problems) == 1
    assert result.problems[0].rule_id == TOOL.RULE_FUNCTIONAL_OWNER
    assert "emrys.stages.beta.worker" in result.problems[0].detail


def test_unclassified_source_domain_fails_even_without_imports(tmp_path: Path) -> None:
    repository = write_repository(
        tmp_path,
        {"src/emrys/new_domain/quiet.py": "VALUE = 1\n"},
    )

    result = inspect_fixture(repository)

    assert len(result.problems) == 1
    problem = result.problems[0]
    assert problem.source_path == "src/emrys/new_domain/quiet.py"
    assert problem.line == 0
    assert problem.rule_id == TOOL.RULE_SOURCE_CLASSIFICATION
    assert "emrys.new_domain.quiet" in problem.detail


def test_exact_public_reporting_seam_is_allowed(tmp_path: Path) -> None:
    repository = write_repository(
        tmp_path,
        {
            "src/emrys/orchestration/control.py": (
                "from emrys.reporting import transaction_validation\n"
            ),
            "src/emrys/reporting/transaction_validation.py": "",
        },
    )

    result = inspect_fixture(repository)

    assert result.problems == ()


@pytest.mark.parametrize(
    "source",
    (
        "import importlib\n"
        "importlib.import_module('emrys.stages.beta.worker')\n",
        "import importlib.util\n"
        "importlib.import_module('emrys.stages.beta.worker')\n",
        "import builtins\n"
        "builtins.__import__('emrys.stages.beta.worker')\n",
        "from importlib import import_module\n"
        "import_module('.worker', package='emrys.stages.beta')\n",
    ),
)
def test_literal_dynamic_peer_import_is_classified(
    tmp_path: Path,
    source: str,
) -> None:
    repository = write_repository(
        tmp_path,
        {
            "src/emrys/stages/alpha/worker.py": source,
            "src/emrys/stages/beta/worker.py": "",
        },
    )

    result = inspect_fixture(repository)

    assert len(result.problems) == 1
    problem = result.problems[0]
    assert problem.line == 2
    assert problem.rule_id == TOOL.RULE_FUNCTIONAL_OWNER
    assert "emrys.stages.beta.worker" in problem.detail


def test_composition_roster_admits_only_the_exact_current_seam(tmp_path: Path) -> None:
    repository = write_repository(
        tmp_path,
        {
            "src/emrys/__main__.py": (
                "from emrys.stages.alpha import algorithm, validator\n"
            ),
            "src/emrys/stages/alpha/algorithm.py": "",
            "src/emrys/stages/alpha/validator.py": "",
        },
    )
    seam = TOOL.CompositionSeam(
        "TEST-CLI-SEAM-001",
        "emrys.stages.alpha.validator",
    )

    result = inspect_fixture(repository, composition_seams=(seam,))

    assert result.composition_seam_count == 1
    assert len(result.problems) == 1
    problem = result.problems[0]
    assert problem.rule_id == TOOL.RULE_ORCHESTRATION_BOUNDARY
    assert "emrys.stages.alpha.algorithm" in problem.detail


def test_stale_composition_seam_fails_closed(tmp_path: Path) -> None:
    repository = write_repository(tmp_path, {"src/emrys/__main__.py": ""})
    seam = TOOL.CompositionSeam(
        "TEST-CLI-SEAM-STALE",
        "emrys.stages.alpha.validator",
    )

    result = inspect_fixture(repository, composition_seams=(seam,))

    assert result.composition_seam_count == 0
    assert len(result.problems) == 1
    problem = result.problems[0]
    assert problem.line == 0
    assert problem.rule_id == TOOL.RULE_ORCHESTRATION_BOUNDARY
    assert "stale current composition seam TEST-CLI-SEAM-STALE" in problem.detail


def test_transition_is_exact_and_does_not_admit_a_neighboring_submodule(
    tmp_path: Path,
) -> None:
    source_path = "src/emrys/orchestration/control.py"
    repository = write_repository(
        tmp_path,
        {
            source_path: "from emrys.stages.alpha import admitted, new_private\n",
            "src/emrys/stages/alpha/admitted.py": "",
            "src/emrys/stages/alpha/new_private.py": "",
        },
    )
    transition = TOOL.Transition(
        "TEST-TRANS-001",
        source_path,
        "emrys.stages.alpha.admitted",
        TOOL.RULE_ORCHESTRATION_BOUNDARY,
        ("TEST-SLICE",),
    )

    result = inspect_fixture(repository, transitions=(transition,))

    assert result.transition_count == 1
    assert len(result.problems) == 1
    assert "emrys.stages.alpha.new_private" in result.problems[0].detail


def test_stale_transition_fails_with_retirement_direction(tmp_path: Path) -> None:
    source_path = "src/emrys/orchestration/control.py"
    repository = write_repository(tmp_path, {source_path: ""})
    transition = TOOL.Transition(
        "TEST-TRANS-STALE",
        source_path,
        "emrys.stages.alpha.worker",
        TOOL.RULE_ORCHESTRATION_BOUNDARY,
        ("TEST-SLICE",),
    )

    result = inspect_fixture(repository, transitions=(transition,))

    assert result.transition_count == 0
    assert len(result.problems) == 1
    problem = result.problems[0]
    assert problem.line == 0
    assert problem.rule_id == TOOL.RULE_ORCHESTRATION_BOUNDARY
    assert "stale transition TEST-TRANS-STALE" in problem.detail
    assert "remove or reconcile it under TEST-SLICE" in problem.detail
    assert problem.render().startswith(
        f"{source_path}:0: [{TOOL.RULE_ORCHESTRATION_BOUNDARY}]"
    )


def test_current_transition_roster_is_exactly_bounded() -> None:
    by_rule: dict[str, list[TOOL.Transition]] = {}
    for transition in TOOL.TRANSITIONS:
        by_rule.setdefault(transition.rule_id, []).append(transition)

    assert {rule_id: len(entries) for rule_id, entries in by_rule.items()} == {
        TOOL.RULE_CONTRACT_NEUTRAL: 6,
        TOOL.RULE_ORCHESTRATION_BOUNDARY: 5,
        TOOL.RULE_PRIVATE_OWNER: 2,
    }
    assert {
        transition.target_module
        for transition in by_rule[TOOL.RULE_PRIVATE_OWNER]
    } == {
        "emrys.reporting._artifact_index.builder",
        "emrys.reporting._run_summary.builder",
    }


def test_roster_configuration_fails_closed() -> None:
    transition = TOOL.Transition(
        "TEST-TRANS-001",
        "src/emrys/orchestration/control.py",
        "emrys.stages.alpha.worker",
        TOOL.RULE_ORCHESTRATION_BOUNDARY,
        ("TEST-SLICE",),
    )
    duplicate_id = TOOL.Transition(
        transition.transition_id,
        transition.source_path,
        "emrys.stages.beta.worker",
        transition.rule_id,
        transition.successors,
    )
    unknown_rule = TOOL.Transition(
        "TEST-TRANS-UNKNOWN",
        transition.source_path,
        transition.target_module,
        "AC-DEP-UNKNOWN",
        transition.successors,
    )

    with pytest.raises(TOOL.DependencyError, match="duplicate transition identity"):
        TOOL.transition_index((transition, duplicate_id))
    with pytest.raises(TOOL.DependencyError, match="unknown transition rule"):
        TOOL.transition_index((unknown_rule,))
    with pytest.raises(TOOL.DependencyError, match="duplicate composition seam target"):
        TOOL.composition_seam_index(
            (
                TOOL.CompositionSeam("TEST-CLI-001", "emrys.reporting.report"),
                TOOL.CompositionSeam("TEST-CLI-002", "emrys.reporting.report"),
            )
        )


def test_executable_rosters_match_the_documented_topology() -> None:
    topology = SOURCE_TOPOLOGY.read_text(encoding="utf-8")
    seam_matches = re.findall(
        r"^\| `(CLI-SEAM-\d{3})` \| `([^`]+)` \|",
        topology,
        flags=re.MULTILINE,
    )
    seam_rows = {
        seam_id: target
        for seam_id, target in seam_matches
    }
    transition_rows: dict[str, tuple[str, str, str]] = {}
    transition_matches = tuple(
        re.finditer(
            r"^\| `(SRC-TRANS-\d{3})` \| `([^`]+)` → `([^`]+)` \|.*$",
            topology,
            flags=re.MULTILINE,
        )
    )
    for match in transition_matches:
        transition_rows[match.group(1)] = (
            match.group(2),
            match.group(3),
            match.group(0),
        )

    assert len(seam_matches) == len(seam_rows) == len(TOOL.COMPOSITION_SEAMS)
    assert seam_rows == {
        seam.seam_id: seam.target_module for seam in TOOL.COMPOSITION_SEAMS
    }
    assert (
        len(transition_matches)
        == len(transition_rows)
        == len(TOOL.TRANSITIONS)
    )
    assert set(transition_rows) == {
        transition.transition_id for transition in TOOL.TRANSITIONS
    }
    for transition in TOOL.TRANSITIONS:
        source, target, row = transition_rows[transition.transition_id]
        assert source == transition.source_path.removeprefix("src/emrys/")
        assert target == transition.target_module
        assert set(re.findall(r"`(AC-SLICE-\d+)`", row)) == set(
            transition.successors
        )


def test_neutral_library_cycle_fails_with_cycle_path(tmp_path: Path) -> None:
    repository = write_repository(
        tmp_path,
        {
            "src/emrys/libraries/alpha.py": "import emrys.libraries.beta\n",
            "src/emrys/libraries/beta.py": "import emrys.libraries.alpha\n",
        },
    )

    result = inspect_fixture(repository)

    assert len(result.problems) == 1
    problem = result.problems[0]
    assert problem.rule_id == TOOL.RULE_LIBRARY_ACYCLIC
    assert problem.line == 1
    assert (
        "emrys.libraries.alpha -> emrys.libraries.beta -> "
        "emrys.libraries.alpha"
    ) in problem.detail


def test_intra_owner_library_cycle_is_outside_this_gate(tmp_path: Path) -> None:
    repository = write_repository(
        tmp_path,
        {
            "src/emrys/libraries/alpha/a.py": "import emrys.libraries.alpha.b\n",
            "src/emrys/libraries/alpha/b.py": "import emrys.libraries.alpha.a\n",
        },
    )

    result = inspect_fixture(repository)

    assert result.problems == ()


def test_parse_and_repository_admission_fail_closed(tmp_path: Path) -> None:
    repository = write_repository(
        tmp_path,
        {"src/emrys/libraries/broken.py": "def broken(:\n"},
    )
    with pytest.raises(
        TOOL.DependencyError,
        match=r"could not parse src/emrys/libraries/broken\.py:1:",
    ):
        inspect_fixture(repository)

    nested = repository / "nested"
    nested.mkdir()
    with pytest.raises(TOOL.DependencyError, match="not the worktree root"):
        inspect_fixture(nested)


def test_current_repository_passes_without_source_writes() -> None:
    before = source_snapshot(REPO_ROOT)

    result = TOOL.inspect_repository(REPO_ROOT)

    assert result.problems == ()
    assert result.composition_seam_count == len(TOOL.COMPOSITION_SEAMS) == 28
    assert result.transition_count == len(TOOL.TRANSITIONS) == 13
    assert source_snapshot(REPO_ROOT) == before


def test_cli_reports_current_transition_count(
    capsys: pytest.CaptureFixture[str],
) -> None:
    TOOL.main(["--repo", str(REPO_ROOT)])

    output = capsys.readouterr().out
    assert "PASS source dependencies" in output
    assert "28 current composition seams" in output
    assert "13 transitional edges" in output
