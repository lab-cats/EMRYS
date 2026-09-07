import argparse
from pathlib import Path

import pytest

from emrys.orchestration.run_coordinator import control, inspection

ZERO_RUN_ID = f"run-{'0' * 64}"
ONE_RUN_ID = f"run-{'0' * 63}1"
ALPHA_RUN_ID = f"run-{'a' * 64}"


def test_project_run_roots_are_cheap_canonical_and_stable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    for run_id in (ALPHA_RUN_ID, ZERO_RUN_ID):
        (runs / run_id).mkdir()
    (runs / f"run-{'B' * 64}").mkdir()
    (runs / "run-short").mkdir()
    (runs / ONE_RUN_ID).write_text("not a directory", encoding="utf-8")
    (runs / f"run-{'c' * 64}").symlink_to(runs / ZERO_RUN_ID)
    monkeypatch.setattr(
        inspection,
        "inspect_run",
        lambda *_args, **_kwargs: pytest.fail("locator admitted Run evidence"),
    )

    run_roots = inspection.project_run_roots(tmp_path)

    assert [root.name for root in run_roots] == [ZERO_RUN_ID, ALPHA_RUN_ID]
    assert inspection.human_run_name(run_roots[0].name) == "international-jackrabbit"
    assert run_roots[0] == runs / ZERO_RUN_ID


def test_project_run_locator_handles_absence_and_rejects_invalid_layout(
    tmp_path: Path,
) -> None:
    assert inspection.project_run_roots(tmp_path) == ()
    (tmp_path / "runs").write_text("not a directory", encoding="utf-8")

    with pytest.raises(inspection.InspectionError, match="real directory"):
        inspection.project_run_roots(tmp_path)
    with pytest.raises(inspection.InspectionError, match="Invalid Run ID"):
        inspection.human_run_name("run-short")


def test_run_locator_resolves_name_id_and_unique_id_prefix(tmp_path: Path) -> None:
    run_roots = (tmp_path / ZERO_RUN_ID, tmp_path / ALPHA_RUN_ID)

    assert inspection.resolve_run_root(run_roots, "international-jackrabbit") == run_roots[0]
    assert inspection.resolve_run_root(run_roots, ALPHA_RUN_ID) == run_roots[1]
    assert inspection.resolve_run_root(run_roots, "run-a") == run_roots[1]


@pytest.mark.parametrize("selector", ["shared-name", "run-0"])
def test_run_locator_rejects_name_collisions_and_ambiguous_prefixes(
    tmp_path: Path, selector: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_roots = (tmp_path / ZERO_RUN_ID, tmp_path / ONE_RUN_ID)
    monkeypatch.setattr(inspection, "human_run_name", lambda _run_id: "shared-name")

    with pytest.raises(inspection.InspectionError, match="Ambiguous"):
        inspection.resolve_run_root(run_roots, selector)


def test_run_locator_rejects_unknown_selector(tmp_path: Path) -> None:
    run_roots = (tmp_path / ZERO_RUN_ID,)
    for selector in ("missing", "run", "run-"):
        with pytest.raises(inspection.InspectionError, match="No Project Run"):
            inspection.resolve_run_root(run_roots, selector)


def test_followup_uses_full_id_only_when_friendly_name_collides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runs = tmp_path / "runs"
    target = runs / ZERO_RUN_ID
    target.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(inspection, "human_run_name", lambda _run_id: "shared-name")

    assert control._run_followup("resume", target, ZERO_RUN_ID) == (
        "emrys resume shared-name"
    )

    (runs / ONE_RUN_ID).mkdir()
    assert control._run_followup("resume", target, ZERO_RUN_ID) == (
        f"emrys resume {ZERO_RUN_ID}"
    )


def test_control_selects_zero_one_and_multiple_project_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project.yaml"
    project.write_text("project\n", encoding="utf-8")
    with pytest.raises(control.ControlError, match="has no Runs"):
        control._select_project_run(project, None, interactive=False)

    runs = tmp_path / "runs"
    (runs / ZERO_RUN_ID).mkdir(parents=True)
    assert control._select_project_run(project, None, interactive=False).name == ZERO_RUN_ID

    (runs / ALPHA_RUN_ID).mkdir()
    with pytest.raises(control.ControlError, match="select one explicitly") as failure:
        control._select_project_run(project, None, interactive=False)
    assert "international-jackrabbit" in str(failure.value)

    monkeypatch.setattr(inspection, "human_run_name", lambda _run_id: "shared-name")
    with pytest.raises(control.ControlError) as collision:
        control._select_project_run(project, None, interactive=False)
    run_roots = (runs / ZERO_RUN_ID, runs / ALPHA_RUN_ID)
    for run_id in (ZERO_RUN_ID, ALPHA_RUN_ID):
        assert f"shared-name ({run_id})" in str(collision.value)
        assert inspection.resolve_run_root(run_roots, run_id) == runs / run_id


def test_control_terminal_selection_and_cancel_are_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project.yaml"
    project.write_text("project\n", encoding="utf-8")
    runs = tmp_path / "runs"
    for run_id in (ZERO_RUN_ID, ALPHA_RUN_ID):
        (runs / run_id).mkdir(parents=True, exist_ok=True)

    class Menu:
        selection: int | None = 1
        choices: tuple[str, ...] = ()

        def __init__(self, choices: tuple[str, ...], **_kwargs: object) -> None:
            Menu.choices = tuple(choices)

        def show(self) -> int | None:
            return self.selection

    monkeypatch.setattr(control, "TerminalMenu", Menu)
    assert control._select_project_run(project, None, interactive=True).name == ALPHA_RUN_ID
    assert Menu.choices == tuple(
        inspection.human_run_name(run_id) for run_id in (ZERO_RUN_ID, ALPHA_RUN_ID)
    )

    Menu.selection = None
    with pytest.raises(control._RunSelectionCancelled, match="nothing was changed"):
        control._select_project_run(project, None, interactive=True)
    assert not (tmp_path / "logs").exists()


def test_noninteractive_multiple_runs_prints_readable_human_names(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "project.yaml"
    project.write_text("project\n", encoding="utf-8")
    for run_id in (ZERO_RUN_ID, ALPHA_RUN_ID):
        (tmp_path / "runs" / run_id).mkdir(parents=True, exist_ok=True)

    result = control.inspect_from_args(
        argparse.Namespace(project=project, run=None, detail="normal")
    )

    assert result == 2
    lines = capsys.readouterr().err.splitlines()
    assert lines == [
        "emrys: error: Multiple Runs exist; select one explicitly: "
        + ", ".join(
            inspection.human_run_name(run_id)
            for run_id in (ZERO_RUN_ID, ALPHA_RUN_ID)
        )
    ]
    assert not (tmp_path / "logs").exists()
