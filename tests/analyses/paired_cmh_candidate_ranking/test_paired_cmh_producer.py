"""Scientific computation checks for the private Step 09 worker."""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
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
        "--all-sites-output",
        str(paths["all"]),
        "--significant-sites-output",
        str(paths["significant"]),
        "--summary-output",
        str(paths["summary"]),
        "--mutation-output",
        str(paths["mutation"]),
        "--mutation-pdf-output",
        str(paths["mutation_pdf"]),
        "--depth-pdf-output",
        str(paths["depth_pdf"]),
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


def _inject_process(
    monkeypatch: pytest.MonkeyPatch,
    fixture: Fixture,
    *,
    status: int = 0,
    mutate: Callable[[], None] | None = None,
) -> tuple[list[Any], list[dict[str, Any]]]:
    processes: list[Any] = []
    calls: list[dict[str, Any]] = []

    def run(command: list[str], **kwargs: Any) -> Any:
        if not status:
            _write_outputs(command, fixture)
            if mutate is not None:
                mutate()
        result = SimpleNamespace(command=command, returncode=status)
        processes.append(result)
        calls.append(kwargs)
        return result

    monkeypatch.setattr(producer.subprocess, "run", run)
    return processes, calls


def _finals(fixture: Fixture) -> tuple[Path, ...]:
    return tuple(fixture.paths[name] for name, _suffix, _option_name in OUTPUTS)


def _execute(
    fixture: Fixture,
    *extra: str,
) -> int:
    return producer.main([*fixture.arguments, *extra])


def test_threshold_boundaries_remain_admitted(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    parser = producer.argparse.ArgumentParser()
    producer.configure_parser(parser)
    context = producer.build_context(
        parser.parse_args(
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
    )
    assert context.thresholds == (1, 0, 1, 1.2, 1, 0.01)
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


def test_worker_preserves_exact_scientific_r_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    processes, calls = _inject_process(monkeypatch, fixture)
    assert _execute(fixture) == 0

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
        str(p["all"]),
        "--significant-sites-output",
        str(p["significant"]),
        "--summary-output",
        str(p["summary"]),
        "--mutation-spectrum-output",
        str(p["mutation"]),
        "--mutation-spectrum-pdf-output",
        str(p["mutation_pdf"]),
        "--depth-delta-pdf-output",
        str(p["depth_pdf"]),
    ]
    assert processes[0].command == expected_command
    assert len(calls) == 1
    assert calls == [{}]
    assert len({path.stat().st_ino for path in _finals(fixture)}) == 6


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
        "--all-sites-output",
        "--significant-sites-output",
        "--summary-output",
        "--mutation-output",
        "--mutation-pdf-output",
        "--depth-pdf-output",
        "--r-script",
    ):
        index = arguments.index(option) + 1
        arguments[index] = os.path.relpath(arguments[index], cwd)
    processes, _calls = _inject_process(monkeypatch, fixture)
    monkeypatch.chdir(cwd)

    assert producer.main(arguments) == 0
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


@pytest.mark.parametrize("mode", ("r-failure", "missing-summary", "bad-pdf"))
def test_worker_rejects_r_or_scientific_output_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    fixture = _fixture(tmp_path)
    mutation = None
    status = 73 if mode == "r-failure" else 0
    if mode == "missing-summary":
        mutation = lambda: fixture.paths["summary"].unlink()
    elif mode == "bad-pdf":
        mutation = lambda: fixture.paths["mutation_pdf"].write_text("not a PDF\n")
    _inject_process(monkeypatch, fixture, status=status, mutate=mutation)

    assert _execute(fixture) == 1
