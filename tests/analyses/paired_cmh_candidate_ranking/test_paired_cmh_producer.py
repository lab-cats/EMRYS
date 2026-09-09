"""Focused transaction tests for the private Step 09 Python producer."""

from __future__ import annotations

import os
import shutil
import signal
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from emrys.analyses.paired_cmh_candidate_ranking import producer
from tests import scientific_evidence_test_support as evidence


OUTPUTS = (
    ("all", "cmh_all_sites.tsv", "--all-sites-output"),
    ("significant", "cmh_significant_sites.tsv", "--significant-sites-output"),
    ("mutation", "mutation_spectrum.tsv", "--mutation-spectrum-output"),
    ("mutation_pdf", "mutation_spectrum.pdf", "--mutation-spectrum-pdf-output"),
    ("depth_pdf", "depth_delta.pdf", "--depth-delta-pdf-output"),
    ("summary", "cmh_summary.tsv", "--summary-output"),
)


@dataclass(frozen=True)
class Fixture:
    arguments: list[str]
    paths: dict[str, Path]
    templates: dict[str, bytes]


def _fixture(tmp_path: Path) -> Fixture:
    built = evidence.build_fixture(tmp_path / "fixture")
    step08_dir = built.step08_sites.parent / evidence.COHORT_ID
    step08_dir.mkdir()
    step08_sites = step08_dir / f"{evidence.COHORT_ID}.step08_sites.tsv"
    step08_inputs = step08_dir / f"{evidence.COHORT_ID}.step08_inputs.tsv"
    shutil.copyfile(built.step08_sites, step08_sites)
    shutil.copyfile(built.step08_inputs, step08_inputs)

    summary = built.step09_analysis_dir / (
        f"{evidence.PRIMARY_ANALYSIS_ID}.cmh_summary.tsv"
    )
    evidence.write_step09_summary(
        summary,
        evidence.PRIMARY_ANALYSIS_ID,
        built.sample_manifest,
        built.partition_manifest,
        step08_sites,
        step08_inputs,
    )
    templates = {
        name: (
            built.step09_analysis_dir / f"{evidence.PRIMARY_ANALYSIS_ID}.{suffix}"
        ).read_bytes()
        for name, suffix, _option in OUTPUTS
    }
    shutil.rmtree(built.step09_analysis_dir.parent)

    r_script = built.root / "step09.R"
    r_script.write_text("# test-owned stand-in; subprocess is injected\n")
    output = built.root / "results"
    analysis_dir = output / evidence.PRIMARY_ANALYSIS_ID
    paths = {
        "sample": built.sample_manifest,
        "partition": built.partition_manifest,
        "step08_sites": step08_sites,
        "step08_inputs": step08_inputs,
        "step08_root": step08_dir.parent,
        "r_script": r_script,
        "output": output,
        "analysis": analysis_dir,
        "lock": analysis_dir / f".{evidence.PRIMARY_ANALYSIS_ID}.step09.lock",
        **{
            name: analysis_dir / f"{evidence.PRIMARY_ANALYSIS_ID}.{suffix}"
            for name, suffix, _option in OUTPUTS
        },
    }
    arguments = [
        "--analysis-id",
        evidence.PRIMARY_ANALYSIS_ID,
        "--cohort-id",
        evidence.COHORT_ID,
        "--sample-manifest",
        str(built.sample_manifest),
        "--partition-manifest",
        str(built.partition_manifest),
        "--step08-root",
        str(step08_dir.parent),
        "--output-root",
        str(output),
        "--rscript-bin",
        "/usr/bin/true",
        "--r-script",
        str(r_script),
    ]
    return Fixture(arguments, paths, templates)


def _option(command: list[str], name: str) -> str:
    return command[command.index(name) + 1]


def _write_outputs(command: list[str], fixture: Fixture) -> None:
    for name, _suffix, option in OUTPUTS:
        destination = Path(_option(command, option))
        destination.parent.mkdir(parents=True, exist_ok=True)
        if name == "summary":
            evidence.write_step09_summary(
                destination,
                _option(command, "--analysis-id"),
                Path(_option(command, "--sample-manifest")),
                Path(_option(command, "--partition-manifest")),
                Path(_option(command, "--step08-sites")),
                Path(_option(command, "--step08-inputs")),
                min_sample_dp=_option(command, "--min-sample-dp"),
                absolute_difference_threshold=_option(
                    command, "--absolute-difference-threshold"
                ),
            )
        else:
            destination.write_bytes(fixture.templates[name])


class FakeProcess:
    pid = 42009

    def __init__(
        self,
        command: list[str],
        fixture: Fixture,
        *,
        status: int = 0,
        interrupt: bool = False,
        mutate: Callable[[], None] | None = None,
    ) -> None:
        self.command = command
        self.status = status
        self.returncode: int | None = None
        self.interrupt = interrupt
        if status == 0:
            _write_outputs(command, fixture)
            if mutate is not None:
                mutate()

    def wait(self, timeout: float | None = None) -> int:
        del timeout
        if self.interrupt:
            self.interrupt = False
            os.kill(os.getpid(), signal.SIGTERM)
        self.returncode = self.status
        return self.status

    def poll(self) -> int | None:
        return self.returncode


def _inject_process(
    monkeypatch: pytest.MonkeyPatch,
    fixture: Fixture,
    *,
    status: int = 0,
    interrupt: bool = False,
    mutate: Callable[[], None] | None = None,
    launch: Callable[[], None] | None = None,
) -> tuple[list[FakeProcess], list[dict[str, Any]]]:
    processes: list[FakeProcess] = []
    calls: list[dict[str, Any]] = []

    def popen(command: list[str], **kwargs: Any) -> FakeProcess:
        if launch is not None:
            launch()
        process = FakeProcess(
            command,
            fixture,
            status=status,
            interrupt=interrupt,
            mutate=mutate,
        )
        processes.append(process)
        calls.append(kwargs)
        return process

    monkeypatch.setattr(producer.subprocess, "Popen", popen)
    return processes, calls


def _finals(fixture: Fixture) -> tuple[Path, ...]:
    return tuple(fixture.paths[name] for name, _suffix, _option_name in OUTPUTS)


def _residue(fixture: Fixture) -> list[Path]:
    analysis = fixture.paths["analysis"]
    return (
        list(analysis.glob(f".{evidence.PRIMARY_ANALYSIS_ID}.step09.*"))
        if analysis.exists()
        else []
    )


def _execute(
    fixture: Fixture,
    *extra: str,
) -> int:
    return producer.main([*fixture.arguments, *extra, "--execute"])


def test_dry_run_validates_without_writing_or_invoking_r(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    monkeypatch.setattr(
        producer.subprocess, "Popen", lambda *_a, **_k: pytest.fail("R invoked")
    )

    assert producer.main(fixture.arguments) == 0
    assert not fixture.paths["output"].exists()


def test_threshold_boundaries_remain_admitted(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    assert (
        producer.main(
            [
                *fixture.arguments,
                "--mean-dp-threshold",
                "0",
                "--fdr-threshold",
                "1",
                "--absolute-difference-threshold",
                "1",
            ]
        )
        == 0
    )
    assert not fixture.paths["output"].exists()


@pytest.mark.parametrize(
    ("option", "value"),
    (
        ("--min-sample-dp", "0"),
        ("--mean-dp-threshold", "-1"),
        ("--fdr-threshold", "1.01"),
        ("--common-or-threshold", "1"),
        ("--absolute-difference-threshold", "1.01"),
        ("--background-max-fraction", "0"),
    ),
)
def test_invalid_thresholds_fail_without_writing(
    tmp_path: Path, option: str, value: str
) -> None:
    fixture = _fixture(tmp_path)
    assert producer.main([*fixture.arguments, option, value]) == 1
    assert not fixture.paths["output"].exists()


@pytest.mark.parametrize("mode", ("missing-path", "missing-command", "non-executable"))
def test_unusable_rscript_fails_without_writing(tmp_path: Path, mode: str) -> None:
    fixture = _fixture(tmp_path)
    replacement = tmp_path / "missing-rscript"
    if mode == "missing-command":
        replacement = Path("emrys-missing-rscript")
    elif mode == "non-executable":
        replacement.write_text("#!/bin/sh\nexit 0\n")
    arguments = [
        str(replacement) if value == "/usr/bin/true" else value
        for value in fixture.arguments
    ]
    assert producer.main(arguments) == 1
    assert not fixture.paths["output"].exists()


@pytest.mark.parametrize(
    ("option", "value"),
    (
        ("--control-condition", "PUM1"),
        ("--background-condition", "EV"),
        ("--rna-alt", "A"),
        ("--background-condition", "absent"),
        ("--step08-root", "missing-step08"),
    ),
)
def test_invalid_scientific_roles_fail_without_writing(
    tmp_path: Path, option: str, value: str
) -> None:
    fixture = _fixture(tmp_path)
    if option == "--step08-root":
        value = str(tmp_path / value)
    assert producer.main([*fixture.arguments, option, value]) == 1
    assert not fixture.paths["output"].exists()


def test_exact_r_command_and_no_clobber_publish_summary_last(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    monkeypatch.setenv("EMRYS_RUN_TOKEN", "owner09")
    observed_owner: list[str] = []
    competing_status: list[int] = []

    def inspect_owner() -> None:
        observed_owner.extend(
            fixture.paths["lock"].joinpath("owner").read_text().splitlines()
        )
        competing_status.append(_execute(fixture))

    processes, calls = _inject_process(monkeypatch, fixture, launch=inspect_owner)
    links: list[tuple[str, bool]] = []
    original_link = os.link

    def record_link(source: Path, destination: Path) -> None:
        original_link(source, destination)
        links.append((Path(destination).name, Path(source).samefile(destination)))

    monkeypatch.setattr(producer.os, "link", record_link)
    assert _execute(fixture, "--no-clobber") == 0

    p = fixture.paths
    expected_command = [
        "/usr/bin/true",
        str(p["r_script"]),
        "--analysis-id",
        evidence.PRIMARY_ANALYSIS_ID,
        "--cohort-id",
        evidence.COHORT_ID,
        "--sample-manifest",
        str(p["sample"]),
        "--partition-manifest",
        str(p["partition"]),
        "--sample-manifest-sha256",
        producer.digest(p["sample"]),
        "--partition-manifest-sha256",
        producer.digest(p["partition"]),
        "--step08-sites",
        str(p["step08_sites"]),
        "--step08-inputs",
        str(p["step08_inputs"]),
        "--step08-sites-sha256",
        producer.digest(p["step08_sites"]),
        "--step08-inputs-sha256",
        producer.digest(p["step08_inputs"]),
        "--control-condition",
        "EV",
        "--treatment-condition",
        "PUM1",
        "--rna-ref",
        "A",
        "--rna-alt",
        "G",
        "--min-sample-dp",
        "1",
        "--mean-dp-threshold",
        "50",
        "--fdr-threshold",
        "0.05",
        "--common-or-threshold",
        "1.2",
        "--absolute-difference-threshold",
        "0.005",
        "--background-max-fraction",
        "0.01",
        "--all-sites-output",
        str(p["analysis"] / ".analysis_primary.step09.owner09.all.tmp.tsv"),
        "--significant-sites-output",
        str(p["analysis"] / ".analysis_primary.step09.owner09.significant.tmp.tsv"),
        "--summary-output",
        str(p["analysis"] / ".analysis_primary.step09.owner09.summary.tmp.tsv"),
        "--mutation-spectrum-output",
        str(p["analysis"] / ".analysis_primary.step09.owner09.mutation.tmp.tsv"),
        "--mutation-spectrum-pdf-output",
        str(p["analysis"] / ".analysis_primary.step09.owner09.mutation.tmp.pdf"),
        "--depth-delta-pdf-output",
        str(p["analysis"] / ".analysis_primary.step09.owner09.depth.tmp.pdf"),
    ]
    assert processes[0].command == expected_command
    assert len(calls) == 1
    assert calls[0]["start_new_session"] is True
    assert observed_owner == ["run_token\towner09", f"pid\t{os.getpid()}"]
    assert competing_status == [1]
    assert links == [
        (path.name, True)
        for path in (
            p["all"],
            p["significant"],
            p["mutation"],
            p["mutation_pdf"],
            p["depth_pdf"],
            p["summary"],
        )
    ]
    assert len({path.stat().st_ino for path in _finals(fixture)}) == 6
    assert not _residue(fixture)


def test_path_basename_and_relative_inputs_work_from_an_arbitrary_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    bin_dir, cwd = tmp_path / "bin", tmp_path / "arbitrary-cwd"
    bin_dir.mkdir()
    cwd.mkdir()
    rscript = bin_dir / "fake-r"
    rscript.write_text("#!/bin/sh\nexit 0\n")
    rscript.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    arguments = [
        "fake-r" if value == "/usr/bin/true" else value for value in fixture.arguments
    ]
    for option in (
        "--sample-manifest",
        "--partition-manifest",
        "--step08-root",
        "--output-root",
        "--r-script",
    ):
        index = arguments.index(option) + 1
        arguments[index] = os.path.relpath(arguments[index], cwd)
    processes, _calls = _inject_process(monkeypatch, fixture)
    monkeypatch.chdir(cwd)

    assert producer.main([*arguments, "--execute"]) == 0
    assert processes[0].command[0] == str(rscript)
    assert list(cwd.iterdir()) == []


def test_run_coordinator_r_command_uses_the_controlled_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    parser = producer.argparse.ArgumentParser()
    producer.configure_parser(parser)
    monkeypatch.setenv("EMRYS_LOCAL_PILOT_R", "1")
    command = producer.r_command(
        producer.build_context(parser.parse_args(fixture.arguments))
    )
    assert command[1:5] == [
        "--no-environ",
        "--no-site-file",
        "--no-restore",
        "--no-save",
    ]


def test_owner_metadata_failure_removes_unowned_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    original_write_text = Path.write_text

    def fail_owner(path: Path, *args: Any, **kwargs: Any) -> int:
        if path.parent == fixture.paths["lock"] and path.name.startswith(".owner."):
            raise OSError("injected owner write failure")
        return original_write_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_owner)
    monkeypatch.setattr(
        producer.subprocess, "Popen", lambda *_a, **_k: pytest.fail("R invoked")
    )
    assert _execute(fixture) == 1
    assert not fixture.paths["lock"].exists()
    assert not _residue(fixture)


@pytest.mark.parametrize("mode", ("r-failure", "missing-summary", "bad-pdf"))
def test_r_or_temporary_output_failure_publishes_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    fixture = _fixture(tmp_path)
    mutation = None
    status = 73 if mode == "r-failure" else 0
    if mode == "missing-summary":
        mutation = lambda: next(
            path
            for path in fixture.paths["analysis"].iterdir()
            if "summary.tmp" in path.name
        ).unlink()
    elif mode == "bad-pdf":
        mutation = lambda: next(
            path
            for path in fixture.paths["analysis"].iterdir()
            if "mutation.tmp.pdf" in path.name
        ).write_text("not a PDF\n")
    _inject_process(monkeypatch, fixture, status=status, mutate=mutation)

    assert _execute(fixture) == 1
    assert not any(path.exists() for path in _finals(fixture))
    assert not _residue(fixture)


@pytest.mark.parametrize(
    "name", ("sample", "partition", "step08_sites", "step08_inputs")
)
def test_input_mutation_during_r_refuses_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    fixture = _fixture(tmp_path)
    path = fixture.paths[name]
    _inject_process(
        monkeypatch, fixture, mutate=lambda: path.write_bytes(path.read_bytes() + b"\n")
    )

    assert _execute(fixture) == 1
    assert not any(path.exists() for path in _finals(fixture))
    assert not _residue(fixture)


def test_selected_r_program_is_not_a_transaction_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    r_script = fixture.paths["r_script"]
    _inject_process(
        monkeypatch,
        fixture,
        mutate=lambda: r_script.write_text(r_script.read_text() + "# changed\n"),
    )

    assert _execute(fixture) == 0
    header = fixture.paths["summary"].read_text().splitlines()[0].split("\t")
    assert not {"r_script_path", "r_script_sha256"} & set(header)


def test_existing_sets_are_preserved_without_r(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    _inject_process(monkeypatch, fixture)
    assert _execute(fixture) == 0
    before = {path: path.read_bytes() for path in _finals(fixture)}
    monkeypatch.setattr(
        producer.subprocess, "Popen", lambda *_a, **_k: pytest.fail("R invoked")
    )

    for flag in ((), ("--no-clobber",)):
        assert _execute(fixture, *flag) == 1
        assert {path: path.read_bytes() for path in _finals(fixture)} == before
    fixture.paths["summary"].unlink()
    remaining = {path: path.read_bytes() for path in _finals(fixture) if path.exists()}
    assert _execute(fixture) == 1
    assert {path: path.read_bytes() for path in remaining} == remaining


def test_foreign_lock_and_no_clobber_residue_are_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    lock = fixture.paths["lock"]
    lock.mkdir(parents=True)
    owner = lock / "owner"
    owner.write_text("run_token\tforeign\npid\t99\n")
    monkeypatch.setattr(
        producer.subprocess, "Popen", lambda *_a, **_k: pytest.fail("R invoked")
    )

    assert _execute(fixture) == 1
    assert owner.read_text() == "run_token\tforeign\npid\t99\n"
    owner.unlink()
    lock.rmdir()
    residue = (
        fixture.paths["analysis"]
        / ".analysis_primary.step09_all_sites.tsv.abandoned.previous"
    )
    residue.write_text("operator evidence\n")
    assert producer.main(fixture.arguments) == 1
    assert residue.read_text() == "operator evidence\n"
    assert not lock.exists()


def test_term_reaches_process_group_and_cleans_owned_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    processes, _calls = _inject_process(monkeypatch, fixture, interrupt=True)
    forwarded: list[tuple[int, signal.Signals]] = []

    def killpg(pid: int, signum: signal.Signals) -> None:
        forwarded.append((pid, signum))
        processes[0].returncode = -int(signum)

    monkeypatch.setattr(producer.os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(producer.os, "killpg", killpg)
    assert _execute(fixture) == 143
    assert forwarded == [(FakeProcess.pid, signal.SIGTERM)]
    assert not any(path.exists() for path in _finals(fixture))
    assert not _residue(fixture)


def test_final_validation_failure_removes_owned_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    _inject_process(monkeypatch, fixture)
    original_validate = producer.validate_outputs

    def fail_final(context: producer.Context, prefix: str = "") -> None:
        original_validate(context, prefix)
        if not prefix:
            raise producer.ProducerError("injected final validation failure")

    monkeypatch.setattr(producer, "validate_outputs", fail_final)
    assert _execute(fixture) == 1
    assert not any(path.exists() for path in _finals(fixture))
    assert not _residue(fixture)


@pytest.mark.parametrize("index", range(6))
@pytest.mark.parametrize("boundary", ("before", "after", "term-before", "term-after"))
def test_no_clobber_link_failure_allows_clean_rerun(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, index: int, boundary: str
) -> None:
    fixture = _fixture(tmp_path)
    _inject_process(monkeypatch, fixture)
    finals = _finals(fixture)
    roots = (fixture.paths["analysis"],)
    arguments = [*fixture.arguments, "--no-clobber", "--execute"]
    original_link = os.link

    def interrupt_link(source: Path, destination: Path) -> None:
        if Path(destination) != finals[index]:
            original_link(source, destination)
            return
        if boundary.endswith("after"):
            original_link(source, destination)
        if boundary.startswith("term"):
            os.kill(os.getpid(), signal.SIGTERM)
        raise OSError("injected link-boundary failure")

    with monkeypatch.context() as injected:
        injected.setattr(producer.os, "link", interrupt_link)
        assert producer.main(arguments) == (143 if boundary.startswith("term") else 1)
    assert not any(os.path.lexists(path) for path in finals)
    assert not any(list(root.rglob(".*")) for root in roots)
    assert producer.main(arguments) == 0
    assert all(path.is_file() for path in finals)
    assert not any(list(root.rglob(".*")) for root in roots)


@pytest.mark.parametrize(
    "fault", ("foreign-file", "foreign-symlink", "missing-anchor", "unlink")
)
def test_no_clobber_ambiguous_rollback_preserves_state_and_refuses_rerun(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    fixture = _fixture(tmp_path)
    _inject_process(monkeypatch, fixture)
    finals = _finals(fixture)
    roots = (fixture.paths["analysis"],)
    arguments = [*fixture.arguments, "--no-clobber", "--execute"]
    original_link, original_unlink = os.link, Path.unlink
    anchors: dict[Path, Path] = {}
    preserved: dict[Path, bytes] = {}
    expected_final: list[bytes] = []
    foreign = roots[0].parent / "foreign-target"

    def interrupt_second_link(source: Path, destination: Path) -> None:
        anchors[Path(destination)] = Path(source)
        if Path(destination) != finals[1]:
            original_link(source, destination)
            return
        if fault.startswith("foreign"):
            foreign.write_bytes(b"foreign output\n")
            original_unlink(finals[0])
            if fault == "foreign-symlink":
                finals[0].symlink_to(foreign)
            else:
                finals[0].write_bytes(foreign.read_bytes())
        elif fault == "missing-anchor":
            original_unlink(anchors[finals[0]])
        expected_final.append(finals[0].read_bytes())
        preserved.update(
            (path, path.read_bytes())
            for root in roots
            for path in root.rglob(".*")
            if path.is_file()
        )
        raise OSError("injected second-link failure")

    def refuse_owned_unlink(path: Path, *, missing_ok: bool = False) -> None:
        if fault == "unlink" and path == finals[0]:
            raise OSError("injected owned-final unlink failure")
        original_unlink(path, missing_ok=missing_ok)

    with monkeypatch.context() as injected:
        injected.setattr(producer.os, "link", interrupt_second_link)
        injected.setattr(Path, "unlink", refuse_owned_unlink)
        assert producer.main(arguments) == 1
    assert finals[0].is_symlink() == (fault == "foreign-symlink")
    assert finals[0].read_bytes() == expected_final[0]
    if fault == "foreign-symlink":
        assert finals[0].readlink() == foreign
    assert not any(os.path.lexists(path) for path in finals[1:])
    assert preserved and all(
        path.read_bytes() == data for path, data in preserved.items()
    )
    owner = (fixture.paths["lock"]) / "owner"
    owner_bytes, final_bytes = owner.read_bytes(), finals[0].read_bytes()
    assert producer.main(arguments) == 1
    assert owner.read_bytes() == owner_bytes and finals[0].read_bytes() == final_bytes
    assert all(path.read_bytes() == data for path, data in preserved.items())


def test_valid_looking_output_corruption_fails_hash_and_removes_owned_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    _inject_process(monkeypatch, fixture)
    original_link = os.link

    def corrupt_pdf(source: Path, destination: Path) -> None:
        original_link(source, destination)
        if Path(destination) == fixture.paths["mutation_pdf"]:
            Path(destination).write_bytes(
                Path(destination).read_bytes() + b"% valid-looking padding\n"
            )

    monkeypatch.setattr(os, "link", corrupt_pdf)
    assert _execute(fixture) == 1
    assert not any(path.exists() for path in _finals(fixture))
    assert not _residue(fixture)
