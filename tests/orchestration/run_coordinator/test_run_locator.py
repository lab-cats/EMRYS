import argparse
from pathlib import Path
from types import SimpleNamespace

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

    assert (
        inspection.resolve_run_root(run_roots, "international-jackrabbit")
        == run_roots[0]
    )
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
    assert (
        control._select_project_run(project, None, interactive=False).name
        == ZERO_RUN_ID
    )

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
    assert (
        control._select_project_run(project, None, interactive=True).name
        == ALPHA_RUN_ID
    )
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
        argparse.Namespace(project=project, run=None, verbose=False)
    )

    assert result == 2
    lines = capsys.readouterr().err.splitlines()
    assert lines == [
        "emrys: error: Multiple Runs exist; select one explicitly: "
        + ", ".join(
            inspection.human_run_name(run_id) for run_id in (ZERO_RUN_ID, ALPHA_RUN_ID)
        )
    ]
    assert not (tmp_path / "logs").exists()


def test_watch_discovers_one_run_from_declared_projects_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "Projects"
    project = home / "study" / "project.yaml"
    run = project.parent / "runs" / ZERO_RUN_ID
    run.mkdir(parents=True)
    project.write_text("project\n", encoding="utf-8")
    monkeypatch.setenv("EMRYS_PROJECTS_ROOT", str(home))

    assert control._select_projects_home_run(None, interactive=False) == (project, run)
    assert control._select_projects_home_run(
        "international-jackrabbit", interactive=False
    ) == (project, run)


def test_watch_uses_picker_for_runs_across_projects_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "Projects"
    expected = []
    for name, run_id in (("alpha", ZERO_RUN_ID), ("beta", ALPHA_RUN_ID)):
        project = home / name / "project.yaml"
        run = project.parent / "runs" / run_id
        run.mkdir(parents=True)
        project.write_text("project\n", encoding="utf-8")
        expected.append((project, run))
    monkeypatch.setenv("EMRYS_PROJECTS_ROOT", str(home))

    class Menu:
        def __init__(self, choices, **_kwargs):
            assert tuple(choices)[0].startswith("alpha:")

        def show(self):
            return 1

    monkeypatch.setattr(control, "TerminalMenu", Menu)
    assert control._select_projects_home_run(None, interactive=True) == expected[1]
    with pytest.raises(control.ControlError, match="Multiple Runs are available"):
        control._select_projects_home_run(None, interactive=False)


def test_watch_routes_run_job_id_and_job_name_without_parallel_monitoring_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parser = argparse.ArgumentParser()
    control.configure_watch_parser(parser)
    captured = []

    def inspect(arguments):
        captured.append(arguments)
        return 0

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("EMRYS_PROJECTS_ROOT", raising=False)
    monkeypatch.setattr(control, "inspect_from_args", inspect)

    assert control.watch_from_args(parser.parse_args(["12345"])) == 0
    assert captured.pop().job_id == "12345"
    assert control.watch_from_args(parser.parse_args(["emrys-request-name"])) == 0
    assert captured.pop().job_name == "emrys-request-name"

    project = tmp_path / "project.yaml"
    project.write_text("project\n", encoding="utf-8")
    request = SimpleNamespace(request_root=tmp_path / "logs" / "submission-exact")
    monkeypatch.setattr(control.inspection, "project_run_roots", lambda _root: ())
    monkeypatch.setattr(
        control.slurm_submission, "submission_requests", lambda _project: (request,)
    )
    monkeypatch.setattr(
        control._submission_inspection,
        "inspect_submission_application",
        lambda _request: SimpleNamespace(run_root=None),
    )
    assert control.watch_from_args(parser.parse_args([])) == 0
    selected = captured.pop()
    assert selected.project == project
    assert selected.submission == "submission-exact"


def test_watch_selects_one_discovered_scheduler_job_without_a_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from emrys.orchestration.run_coordinator import dashboard

    parser = argparse.ArgumentParser()
    control.configure_watch_parser(parser)
    captured = []

    def inspect(arguments):
        captured.append(arguments)
        return 0

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("EMRYS_PROJECTS_ROOT", raising=False)
    monkeypatch.delenv("EMRYS_DASHBOARD_JOB_ID", raising=False)
    monkeypatch.setattr(
        dashboard,
        "scheduler_candidates",
        lambda: ({"job_id": 41},),
    )
    monkeypatch.setattr(control, "inspect_from_args", inspect)

    assert control.watch_from_args(parser.parse_args([])) == 0
    assert captured[0].job_id == "41"


def test_watch_offers_discovered_scheduler_jobs_in_existing_picker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from emrys.orchestration.run_coordinator import dashboard

    parser = argparse.ArgumentParser()
    control.configure_watch_parser(parser)
    captured = []

    def inspect(arguments):
        captured.append(arguments)
        return 0

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("EMRYS_PROJECTS_ROOT", raising=False)
    monkeypatch.delenv("EMRYS_DASHBOARD_JOB_ID", raising=False)
    monkeypatch.setattr(control.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(control.sys.stderr, "isatty", lambda: True)
    monkeypatch.setattr(
        dashboard,
        "scheduler_candidates",
        lambda: ({"job_id": 41}, {"job_id": 42}),
    )

    class Menu:
        def __init__(self, choices, **_kwargs):
            assert tuple(choices) == ("Job 41", "Job 42")

        def show(self):
            return 1

    monkeypatch.setattr(control, "TerminalMenu", Menu)
    monkeypatch.setattr(control, "inspect_from_args", inspect)

    assert control.watch_from_args(parser.parse_args([])) == 0
    assert captured[0].job_id == "42"


def test_watch_refuses_ambiguous_scheduler_jobs_without_a_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from emrys.orchestration.run_coordinator import dashboard

    parser = argparse.ArgumentParser()
    control.configure_watch_parser(parser)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("EMRYS_PROJECTS_ROOT", raising=False)
    monkeypatch.delenv("EMRYS_DASHBOARD_JOB_ID", raising=False)
    monkeypatch.setattr(control.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(
        dashboard,
        "scheduler_candidates",
        lambda: ({"job_id": 41}, {"job_id": 42}),
    )
    monkeypatch.setattr(
        control,
        "inspect_from_args",
        lambda _arguments: pytest.fail("ambiguous jobs must not open the dashboard"),
    )

    assert control.watch_from_args(parser.parse_args([])) == 2
    assert "Multiple scheduler jobs are available; select one: Job 41, Job 42" in (
        capsys.readouterr().err
    )


def test_watch_ignores_submission_already_associated_with_sole_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project.yaml"
    project.write_text("project\n", encoding="utf-8")
    run = tmp_path / "runs" / ZERO_RUN_ID
    run.mkdir(parents=True)
    request = SimpleNamespace(request_root=tmp_path / "logs" / "submission-exact")
    monkeypatch.setattr(
        control.slurm_submission, "submission_requests", lambda _project: (request,)
    )
    monkeypatch.setattr(
        control._submission_inspection,
        "inspect_submission_application",
        lambda _request: SimpleNamespace(run_root=run),
    )

    assert control._select_project_watch_target(project, interactive=False) == (
        "run",
        run,
    )


def test_watch_requires_choice_between_historical_run_and_new_submission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project.yaml"
    project.write_text("project\n", encoding="utf-8")
    run = tmp_path / "runs" / ZERO_RUN_ID
    run.mkdir(parents=True)
    request = SimpleNamespace(
        request_root=tmp_path / "logs" / "submission-new", recorded_job_id="42"
    )
    monkeypatch.setattr(
        control.slurm_submission, "submission_requests", lambda _project: (request,)
    )
    monkeypatch.setattr(
        control._submission_inspection,
        "inspect_submission_application",
        lambda _request: SimpleNamespace(run_root=None),
    )

    with pytest.raises(control.ControlError, match="Multiple monitoring targets"):
        control._select_project_watch_target(project, interactive=False)

    class Menu:
        def __init__(self, choices, **_kwargs):
            assert tuple(choices)[1].startswith("Submission:")

        def show(self):
            return 1

    monkeypatch.setattr(control, "TerminalMenu", Menu)
    assert control._select_project_watch_target(project, interactive=True) == (
        "submission",
        request,
    )


def test_public_watch_command_routes_to_the_inspection_owner() -> None:
    from emrys import __main__ as cli

    selected = cli.build_parser().parse_args(["watch", "12345"])
    assert selected._command_handler is control.watch_from_args
    assert selected.watch is True and selected.run == "12345"
