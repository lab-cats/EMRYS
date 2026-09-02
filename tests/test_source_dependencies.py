"""Focused protection for the bounded Python source-dependency gate."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from tests.tools import source_dependencies as TOOL

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_TOPOLOGY = REPO_ROOT / "src/emrys/contracts/SOURCE_TOPOLOGY.md"


def write_repository(
    tmp_path: Path,
    sources: dict[str, str],
    *,
    name: str = "repository",
    ignored: tuple[str, ...] = (),
) -> Path:
    repository = tmp_path / name
    repository.mkdir()
    initialized = subprocess.run(
        ["git", "init", "-q", str(repository)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert initialized.returncode == 0, initialized.stderr
    complete = {"src/emrys/__init__.py": "", **sources}
    for relative, source in complete.items():
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    if ignored:
        (repository / ".gitignore").write_text("\n".join(ignored) + "\n", encoding="utf-8")
    return repository


def inspect(
    repository: Path,
    *,
    transitions: tuple[tuple[str, str, str, str], ...] = (),
    seams: tuple[tuple[str, str], ...] = (),
) -> tuple[TOOL.Problem, ...]:
    return TOOL.inspect_repository(
        repository,
        transitions=transitions,
        composition_seams=seams,
    )


@pytest.mark.parametrize(
    ("source_path", "source", "target_path", "rule_id", "target", "line"),
    (
        ("src/emrys/contracts/schema.py", "from emrys.libraries import helper\n", "src/emrys/libraries/helper.py", TOOL.RULE_CONTRACT_NEUTRAL, "emrys.libraries.helper", 1),
        ("src/emrys/libraries/helper.py", "from emrys.stages.alpha import worker\n", "src/emrys/stages/alpha/worker.py", TOOL.RULE_LIBRARY_NEUTRAL, "emrys.stages.alpha.worker", 1),
        ("src/emrys/stages/alpha/worker.py", "from emrys.stages.beta import worker\n", "src/emrys/stages/beta/worker.py", TOOL.RULE_FUNCTIONAL_OWNER, "emrys.stages.beta.worker", 1),
        ("src/emrys/stages/alpha/worker.py", "from emrys.orchestration import control\n", "src/emrys/orchestration/control.py", TOOL.RULE_FUNCTIONAL_OWNER, "emrys.orchestration.control", 1),
        ("src/emrys/ingestion/admit.py", "from emrys.evidence.runtime import inspector\n", "src/emrys/evidence/runtime/inspector.py", TOOL.RULE_INGESTION_BOUNDARY, "emrys.evidence.runtime.inspector", 1),
        ("src/emrys/reporting/view.py", "from emrys.analyses.ranking import result\n", "src/emrys/analyses/ranking/result.py", TOOL.RULE_REPORTING_DOWNSTREAM, "emrys.analyses.ranking.result", 1),
        ("src/emrys/orchestration/control.py", "from emrys.stages.alpha import worker\n", "src/emrys/stages/alpha/worker.py", TOOL.RULE_ORCHESTRATION_BOUNDARY, "emrys.stages.alpha.worker", 1),
        ("src/emrys/orchestration/control.py", "from emrys.reporting import report\n", "src/emrys/reporting/report.py", TOOL.RULE_ORCHESTRATION_BOUNDARY, "emrys.reporting.report", 1),
        ("src/emrys/libraries/helper.py", "import emrys.__main__\n", "src/emrys/__main__.py", TOOL.RULE_ORCHESTRATION_BOUNDARY, "emrys.__main__", 1),
        ("src/emrys/__main__.py", "from emrys.reporting import _private\n", "src/emrys/reporting/_private.py", TOOL.RULE_PRIVATE_OWNER, "emrys.reporting._private", 1),
        ("src/emrys/libraries/alpha/client.py", "from emrys.libraries.beta import _private\n", "src/emrys/libraries/beta/_private.py", TOOL.RULE_PRIVATE_OWNER, "emrys.libraries.beta._private", 1),
        ("src/emrys/__init__.py", "from emrys.reporting import view\n", "src/emrys/reporting/view.py", TOOL.RULE_SOURCE_CLASSIFICATION, "emrys.reporting.view", 1),
        ("src/emrys/stages/alpha/worker.py", "from ..beta import worker\n", "src/emrys/stages/beta/worker.py", TOOL.RULE_FUNCTIONAL_OWNER, "emrys.stages.beta.worker", 1),
        ("src/emrys/new_domain/quiet.py", "VALUE = 1\n", None, TOOL.RULE_SOURCE_CLASSIFICATION, "emrys.new_domain.quiet", 0),
    ),
)
def test_forbidden_dependency_projection(
    tmp_path: Path,
    source_path: str,
    source: str,
    target_path: str | None,
    rule_id: str,
    target: str,
    line: int,
) -> None:
    sources = {source_path: source}
    if target_path is not None:
        sources[target_path] = "raise RuntimeError('product source must not execute')\n"
    problems = inspect(write_repository(tmp_path, sources))

    assert len(problems) == 1
    problem = problems[0]
    assert problem.rule_id == rule_id
    assert problem.line == line
    assert target in problem.detail
    assert problem.render().startswith(f"{problem.source_path}:{line}: [{rule_id}]")


def test_exact_public_reporting_seam_is_allowed(tmp_path: Path) -> None:
    repository = write_repository(
        tmp_path,
        {
            "src/emrys/orchestration/run_coordinator/reporting_boundary.py": (
                "from emrys.reporting import transaction_validation\n"
            ),
            "src/emrys/reporting/transaction_validation.py": "",
        },
    )

    assert inspect(repository) == ()


@pytest.mark.parametrize(
    ("statement", "target_path"),
    (
        (
            "from emrys.reporting._artifact_index.context import prepare_context\n",
            "src/emrys/reporting/_artifact_index/context.py",
        ),
        (
            "from emrys.reporting._artifact_index.publication import publish_context\n",
            "src/emrys/reporting/_artifact_index/publication.py",
        ),
        (
            "from emrys.reporting._run_summary.builder import prepare_context\n",
            "src/emrys/reporting/_run_summary/builder.py",
        ),
        (
            "from emrys.reporting._run_summary.publication import publish_context\n",
            "src/emrys/reporting/_run_summary/publication.py",
        ),
    ),
)
def test_exact_reporting_coordinator_private_seam_is_allowed(
    tmp_path: Path,
    statement: str,
    target_path: str,
) -> None:
    repository = write_repository(
        tmp_path,
        {
            "src/emrys/orchestration/run_coordinator/reporting_operation.py": statement,
            target_path: "",
        },
    )

    assert inspect(repository) == ()


@pytest.mark.parametrize(
    "source",
    (
        "import importlib as loader\nloader.import_module('emrys.stages.beta.worker')\n",
        "import importlib.util\nimportlib.import_module('emrys.stages.beta.worker')\n",
        "from importlib import import_module as load\nload('emrys.stages.beta.worker')\n",
        "from importlib import import_module\nimport_module('.worker', package='emrys.stages.beta')\n",
        "from importlib import import_module\nimport_module('.worker', 'emrys.stages.beta')\n",
        "from importlib import import_module\nimport_module('.', package='emrys.stages.beta')\n",
        "__import__('emrys.stages.beta.worker')\n",
        "import builtins as bi\nbi.__import__('emrys.stages.beta.worker')\n",
        "from builtins import __import__ as load\nload('emrys.stages.beta.worker')\n",
    ),
)
def test_recognized_literal_dynamic_import_forms(tmp_path: Path, source: str) -> None:
    repository = write_repository(
        tmp_path,
        {
            "src/emrys/stages/alpha/worker.py": source,
            "src/emrys/stages/beta/worker.py": "",
        },
    )

    problems = inspect(repository)
    assert len(problems) == 1
    assert problems[0].rule_id == TOOL.RULE_FUNCTIONAL_OWNER
    assert "emrys.stages.beta" in problems[0].detail


def test_composition_roster_is_exact_and_stale_failing(tmp_path: Path) -> None:
    seam = (("TEST-CLI-SEAM", "emrys.stages.alpha.validator"),)
    repository = write_repository(
        tmp_path,
        {
            "src/emrys/__main__.py": "from emrys.stages.alpha import algorithm, validator\n",
            "src/emrys/stages/alpha/algorithm.py": "",
            "src/emrys/stages/alpha/validator.py": "",
        },
    )
    problems = inspect(repository, seams=seam)
    assert len(problems) == 1
    assert "emrys.stages.alpha.algorithm" in problems[0].detail

    stale = inspect(
        write_repository(tmp_path, {"src/emrys/__main__.py": ""}, name="stale-seam"),
        seams=seam,
    )
    assert len(stale) == 1
    assert "stale current composition seam TEST-CLI-SEAM" in stale[0].detail


def test_transition_roster_is_exact_private_and_stale_failing(tmp_path: Path) -> None:
    source_path = "src/emrys/orchestration/control.py"
    transition = (("TEST-TRANS", source_path, "emrys.stages.alpha.admitted", TOOL.RULE_ORCHESTRATION_BOUNDARY),)
    repository = write_repository(
        tmp_path,
        {
            source_path: "from emrys.stages.alpha import admitted, neighbor\n",
            "src/emrys/stages/alpha/admitted.py": "",
            "src/emrys/stages/alpha/neighbor.py": "",
        },
    )
    problems = inspect(repository, transitions=transition)
    assert len(problems) == 1
    assert "emrys.stages.alpha.neighbor" in problems[0].detail

    private_path = "src/emrys/__main__.py"
    private_transition = (("TEST-PRIVATE", private_path, "emrys.reporting._private.builder", TOOL.RULE_PRIVATE_OWNER),)
    private = write_repository(
        tmp_path,
        {
            private_path: "from emrys.reporting._private import builder\n",
            "src/emrys/reporting/_private/builder.py": "",
        },
        name="private-transition",
    )
    assert inspect(private, transitions=private_transition) == ()

    stale = inspect(
        write_repository(tmp_path, {source_path: ""}, name="stale-transition"),
        transitions=transition,
    )
    assert len(stale) == 1
    assert "stale transition TEST-TRANS" in stale[0].detail
    assert "SOURCE_TOPOLOGY.md" in stale[0].detail


@pytest.mark.parametrize("cross_owner", (True, False))
def test_neutral_library_cycle_scope(tmp_path: Path, cross_owner: bool) -> None:
    if cross_owner:
        sources = {
            "src/emrys/libraries/alpha.py": "import emrys.libraries.beta\n",
            "src/emrys/libraries/beta.py": "import emrys.libraries.gamma\n",
            "src/emrys/libraries/gamma.py": "import emrys.libraries.alpha\n",
        }
    else:
        sources = {
            "src/emrys/libraries/alpha/a.py": "import emrys.libraries.alpha.b\n",
            "src/emrys/libraries/alpha/b.py": "import emrys.libraries.alpha.a\n",
        }
    problems = inspect(write_repository(tmp_path, sources))
    if cross_owner:
        assert len(problems) == 1
        assert problems[0].rule_id == TOOL.RULE_LIBRARY_NEUTRAL
        assert "emrys.libraries.alpha" in problems[0].detail
        assert "emrys.libraries.beta" in problems[0].detail
        assert "emrys.libraries.gamma" in problems[0].detail
    else:
        assert problems == ()


def test_executable_rosters_match_documented_topology() -> None:
    topology = SOURCE_TOPOLOGY.read_text(encoding="utf-8")
    seam_rows = re.findall(
        r"^\| `(CLI-SEAM-\d{3})` \| `([^`]+)` \|",
        topology,
        flags=re.MULTILINE,
    )
    transition_rows = []
    for line in topology.splitlines():
        if not line.startswith("| `SRC-TRANS-"):
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        edge = re.fullmatch(r"`([^`]+)` → `([^`]+)`", cells[1])
        assert edge is not None
        transition_rows.append((cells[0].strip("`"), edge.group(1), edge.group(2), cells[3]))

    assert len(seam_rows) == len({row[0] for row in seam_rows}) == len(TOOL.COMPOSITION_SEAMS)
    assert dict(seam_rows) == dict(TOOL.COMPOSITION_SEAMS)
    assert len(transition_rows) == len({row[0] for row in transition_rows}) == len(TOOL.TRANSITIONS)
    documented = {row[0]: row[1:] for row in transition_rows}
    assert set(documented) == {row[0] for row in TOOL.TRANSITIONS}
    for transition_id, source, target, _rule_id in TOOL.TRANSITIONS:
        documented_source, documented_target, justification = documented[transition_id]
        assert documented_source == source.removeprefix("src/emrys/")
        assert documented_target == target
        assert justification


def test_repository_admission_and_inventory(tmp_path: Path) -> None:
    broken = write_repository(
        tmp_path,
        {"src/emrys/libraries/broken.py": "def broken(:\n"},
    )
    with pytest.raises(TOOL.DependencyError, match=r"could not parse .*broken\.py:1:"):
        inspect(broken)
    nested = broken / "nested"
    nested.mkdir()
    with pytest.raises(TOOL.DependencyError, match="not the worktree root"):
        inspect(nested)

    ignored = write_repository(
        tmp_path,
        {"src/emrys/libraries/ignored.py": "def broken(:\n"},
        name="ignored",
        ignored=("src/emrys/libraries/ignored.py",),
    )
    assert inspect(ignored) == ()

    symlinked = write_repository(tmp_path, {}, name="symlinked")
    link = symlinked / "src/emrys/libraries/link.py"
    link.parent.mkdir(parents=True)
    link.symlink_to(symlinked / "src/emrys/__init__.py")
    with pytest.raises(TOOL.DependencyError, match="must be a regular file"):
        inspect(symlinked)


def test_current_repository_and_cli_are_read_only(capsys: pytest.CaptureFixture[str]) -> None:
    def snapshot() -> tuple[tuple[str, int, int], ...]:
        return tuple(
            sorted(
                (path.relative_to(REPO_ROOT).as_posix(), path.stat().st_size, path.stat().st_mtime_ns)
                for path in (REPO_ROOT / "src/emrys").rglob("*.py")
            )
        )

    before = snapshot()
    assert TOOL.inspect_repository(REPO_ROOT) == ()
    TOOL.main(["--repo", str(REPO_ROOT)])
    assert capsys.readouterr().out == "PASS source dependencies\n"
    assert snapshot() == before
