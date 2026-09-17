from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from rich.ansi import AnsiDecoder
from rich.text import Text

from emrys import __main__ as cli
from emrys.contracts.orchestration import api as contracts
from emrys.contracts.scientific_evidence import step08
from emrys.evidence.runtime_availability.inspector import RuntimeInspection
from emrys.libraries.validation.tsv import tsv_bytes
from emrys.libraries import exclusive_publication
from emrys.libraries.source_authority import PACKAGE_ROOT
from emrys.orchestration.run_coordinator import (
    control,
    doctor,
    execution_profile,
    normalization,
    onboarding,
    synthetic_fixture,
)
from tests.orchestration.run_coordinator.fixture import build


class _Terminal(io.StringIO):
    def isatty(self) -> bool:
        return True


def _decoded_terminal(value: str) -> Text:
    return AnsiDecoder().decode_line(value)


def _namespace(
    output: Path,
    *,
    execute: bool,
    dataset_profile: str = synthetic_fixture.DEFAULT_DATASET_PROFILE,
) -> argparse.Namespace:
    return argparse.Namespace(
        output_dir=output,
        execute=execute,
        dataset_profile=dataset_profile,
    )


def _publish_synthetic(output: Path) -> None:
    assert synthetic_fixture.init_from_args(_namespace(output, execute=True)) == 0


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _executable(path: Path, content: str = "#!/bin/sh\nexit 0\n") -> Path:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path


def _fastqs(
    root: Path, *sample_ids: str, mate_marker: str = "R", suffix: str = ".fastq.gz"
) -> list[Path]:
    paths = [
        root / f"{sample}_{mate_marker}{mate}{suffix}"
        for sample in sample_ids
        for mate in (1, 2)
    ]
    for path in paths:
        path.write_bytes(b"not inspected by structural drafting\n")
    return paths


def _manifest_command(
    output: Path,
    fastqs: list[Path] | tuple[Path, ...],
    *,
    samples: tuple[tuple[str, str, str, str], ...] = (),
    partitions: tuple[tuple[str, str, str], ...] = (),
    execute: bool = False,
) -> list[str]:
    command = [
        "init",
        "manifests",
        "--output-dir",
        str(output),
        "--fastq",
        *(str(path) for path in fastqs),
    ]
    for sample in samples:
        command.extend(("--sample", *sample))
    for option, name, value in partitions:
        command.extend((option, name, value))
    if execute:
        command.append("--execute")
    return command


def _project_arguments(
    tmp_path: Path, output: Path, *, execute: bool
) -> argparse.Namespace:
    source = tmp_path / "source"
    project = build(source)
    definition = yaml.safe_load(project.read_text(encoding="utf-8"))
    table, _sample_ids, rows = step08.validate_sample_manifest(source / "samples.tsv")
    for row in rows:
        row["r1_fastq"] = str((source / row["r1_fastq"]).resolve())
        row["r2_fastq"] = str((source / row["r2_fastq"]).resolve())
    sample_manifest = tmp_path / "samples.absolute.tsv"
    sample_manifest.write_bytes(tsv_bytes(table.header, rows))
    analysis_name = "guided-analysis"
    analysis = definition["analyses"]["primary"]
    reference = definition["reference"]
    return argparse.Namespace(
        project_name=output.name,
        sample_manifest=sample_manifest,
        partition_manifest=source / "partitions.tsv",
        reference_fasta=(source / reference["fasta"]).resolve(),
        reference_gtf=(source / reference["gtf"]).resolve(),
        sjdb_overhang=reference["star_index"]["sjdb_overhang"],
        genome_sa_index_nbases=reference["star_index"]["genome_sa_index_nbases"],
        analysis_name=analysis_name,
        control_condition=analysis["control_condition"],
        treatment_condition=analysis["treatment_condition"],
        target_change=analysis["target_change"],
        min_sample_dp=analysis["min_sample_dp"],
        mean_dp_threshold=analysis["mean_dp_threshold"],
        fdr_threshold=analysis["fdr_threshold"],
        common_or_threshold=analysis["common_or_threshold"],
        absolute_difference_threshold=analysis["absolute_difference_threshold"],
        background_condition=analysis["background_condition"],
        background_max_fraction=analysis["background_max_fraction"],
        execute=execute,
    )


def test_setup_prompts_for_and_publishes_closed_cli_defaults(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "checkout"
    projects = root / "Projects"
    projects.mkdir(parents=True)
    (root / ".git").mkdir()
    (root / "src/emrys").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname='emrys'\n")
    for key in ("EMRYS_PROJECTS_ROOT", "EMRYS_SITE", "EMRYS_LOG_ROOT"):
        monkeypatch.setenv(key, "")  # Track restoration even when initially absent.
        monkeypatch.delenv(key, raising=False)
    stderr = _Terminal()
    monkeypatch.chdir(projects)
    monkeypatch.setattr(onboarding.sys, "stdin", _Terminal("\n\n\n"))
    monkeypatch.setattr(onboarding.sys, "stderr", stderr)

    assert cli.main(["setup", "--execute"]) == 0

    saved = root / ".env"
    assert saved.read_text() == (
        f"EMRYS_ENV_VERSION=1\nEMRYS_PROJECTS_ROOT={projects}\nEMRYS_SITE=viking\n"
    )
    assert stat.S_IMODE(saved.stat().st_mode) == 0o600
    rendered = _decoded_terminal(stderr.getvalue()).plain
    assert "Projects home" in rendered
    assert "site (Press ENTER for viking)" in rendered
    assert "log root (optional)" in rendered
    loaded: dict[str, str] = {}
    assert onboarding.load_saved_cli_environment(projects, loaded) == saved
    assert loaded == {
        "EMRYS_PROJECTS_ROOT": str(projects),
        "EMRYS_SITE": "viking",
    }


def test_saved_cli_defaults_preserve_process_values_and_supply_log_root(
    tmp_path: Path,
) -> None:
    projects = tmp_path / "Projects"
    log_root = tmp_path / "central logs"
    nested = projects / "study"
    nested.mkdir(parents=True)
    (nested / ".env").write_text("UNRELATED=value\n", encoding="utf-8")
    saved = tmp_path / ".env"
    saved.write_text(
        "EMRYS_ENV_VERSION=1\n"
        f"EMRYS_PROJECTS_ROOT={projects}\n"
        "EMRYS_SITE=viking\n"
        f"EMRYS_LOG_ROOT={log_root}\n",
        encoding="utf-8",
    )
    environment = {"EMRYS_PROJECTS_ROOT": "/process/projects"}

    assert onboarding.load_saved_cli_environment(nested, environment) == saved
    assert environment == {
        "EMRYS_PROJECTS_ROOT": "/process/projects",
        "EMRYS_SITE": "viking",
        "EMRYS_LOG_ROOT": str(log_root),
    }


def test_saved_cli_defaults_reject_unknown_keys_before_loading(
    tmp_path: Path,
) -> None:
    saved = tmp_path / ".env"
    saved.write_text(
        "EMRYS_ENV_VERSION=1\n"
        f"EMRYS_PROJECTS_ROOT={tmp_path}\n"
        "EMRYS_SITE=viking\n"
        "TOKEN=secret\n",
        encoding="utf-8",
    )
    environment: dict[str, str] = {}

    with pytest.raises(onboarding.OnboardingError, match="invalid saved CLI setting"):
        onboarding.load_saved_cli_environment(tmp_path, environment)
    assert environment == {}


def test_saved_site_defaults_existing_site_arguments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EMRYS_SITE", "viking")
    parser = cli.build_parser()

    synthetic = parser.parse_args(
        ["init", "synthetic", "--output-dir", str(tmp_path / "project")]
    )
    profile = parser.parse_args(["profile", "create", "cluster"])

    assert synthetic.site == "viking"
    assert profile.site == "viking"


def test_setup_is_dry_run_first_and_preserves_an_existing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "checkout"
    projects = root / "Projects"
    projects.mkdir(parents=True)
    (root / ".git").mkdir()
    (root / "src/emrys").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname='emrys'\n")
    for key in ("EMRYS_PROJECTS_ROOT", "EMRYS_SITE", "EMRYS_LOG_ROOT"):
        monkeypatch.setenv(key, "")  # Track restoration even when initially absent.
        monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(root)

    log_root = root / "central logs"
    command = [
        "setup",
        "--projects-root",
        str(projects),
        "--site",
        "viking",
        "--log-root",
        str(log_root),
    ]
    assert cli.main(command) == 0
    assert not (root / ".env").exists()
    assert cli.main([*command, "--execute"]) == 0
    before = (root / ".env").read_bytes()
    assert f"EMRYS_LOG_ROOT={log_root}\n".encode() in before
    assert cli.main([*command, "--execute"]) == 2
    assert (root / ".env").read_bytes() == before


def test_init_project_is_dry_run_first_and_creates_only_the_project_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projects = tmp_path / "projects"
    projects.mkdir()
    output = projects / "my-study"
    monkeypatch.chdir(projects)
    arguments = _project_arguments(tmp_path, output, execute=False)
    arguments.sample_manifest = tmp_path / "source/samples.tsv"
    arguments.site = "viking"
    input_files = _tree_bytes(tmp_path / "source")
    manifest_bytes = arguments.sample_manifest.read_bytes()
    command = ["init", arguments.project_name]
    for name, value in vars(arguments).items():
        if name not in {"project_name", "execute"} and value is not None:
            command.extend((f"--{name.replace('_', '-')}", str(value)))

    assert cli.main(command) == 0
    assert not output.exists()
    assert list(projects.iterdir()) == []
    preview = capsys.readouterr()
    assert "Preview complete; Project not created." in preview.out
    assert "Next action: copy and run the complete command below." in preview.out
    assert "Reading and hashing Project inputs" not in preview.err
    assert f"Output directory: {output}" in preview.out
    assert "Libraries (4):" in preview.out
    assert f"Analysis: {arguments.analysis_name}; site: viking" in preview.out
    assert "Partitions: 1" in preview.out
    assert (
        f"Comparison: {arguments.control_condition} -> "
        f"{arguments.treatment_condition}; target {arguments.target_change}"
    ) in preview.out
    assert "Detailed study review" not in preview.out
    phases = (
        "Reading and hashing Project inputs",
        "Checking reference and partition compatibility",
    )

    assert cli.main([*command, "--execute"]) == 0
    created = capsys.readouterr()
    assert "Project ready:" in created.out
    for phase in phases:
        assert re.search(rf"{phase}: complete \(\d+m \d{{2}}s\)", created.err)
    assert set(_tree_bytes(output)) == {
        "partitions.tsv",
        "project.yaml",
        "runtime/profiles/default.yaml",
        "samples.tsv",
    }
    assert (output / "runtime/profiles/default.yaml").read_bytes() == (
        execution_profile.project_default_profile_bytes("viking")
    )
    directories = {path.name for path in output.iterdir() if path.is_dir()}
    assert directories == {"logs", "runs", "runtime"}
    assert all(
        stat.S_IMODE((output / name).stat().st_mode) == 0o700 for name in directories
    )
    definition = yaml.safe_load((output / "project.yaml").read_text(encoding="utf-8"))
    assert definition["schema_version"] == "emrys.project.v1"
    assert definition["dataset"]["samples"] == "samples.tsv"
    assert (
        definition["analyses"][arguments.analysis_name]["partitions"]
        == "partitions.tsv"
    )
    assert definition["reference"]["fasta"] == str(arguments.reference_fasta)
    assert definition["reference"]["gtf"] == str(arguments.reference_gtf)
    assert definition["analyses"][arguments.analysis_name]["target_change"] == "A>G"
    assert not list(output.rglob("*.fastq"))
    assert onboarding.validate_project(output / "project.yaml").sample_count == 4
    assert _tree_bytes(tmp_path / "source") == input_files
    assert arguments.sample_manifest.read_bytes() == manifest_bytes


def test_project_preview_skips_fastq_hashing_and_creation_hashes_each_fastq_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "my-study"
    monkeypatch.chdir(tmp_path)
    arguments = _project_arguments(tmp_path, output, execute=False)
    _, _, rows = step08.validate_sample_manifest(arguments.sample_manifest)
    fastqs = {Path(row[mate]) for row in rows for mate in ("r1_fastq", "r2_fastq")}
    counts = {path: 0 for path in fastqs}
    real_hash = normalization.sha256_with_identity

    def count_hash(
        path: Path, label: str, **kwargs: object
    ) -> tuple[str, os.stat_result]:
        admitted = Path(path)
        if admitted in counts:
            counts[admitted] += 1
        return real_hash(path, label, **kwargs)

    monkeypatch.setattr(normalization, "sha256_with_identity", count_hash)

    assert onboarding.init_project_from_args(arguments) == 0
    assert set(counts.values()) == {0}
    arguments.execute = True
    assert onboarding.init_project_from_args(arguments) == 0
    assert set(counts.values()) == {1}


def test_guided_project_creation_writes_its_manifests_inside_the_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "guided-study"
    arguments = _project_arguments(tmp_path, output, execute=True)
    reads = tmp_path / "source" / "reads"
    arguments.sample_manifest = None
    arguments.partition_manifest = None
    arguments.fastq = []
    arguments.sample = []
    arguments.regions_file = []
    arguments.region = []
    arguments.sjdb_overhang = None
    arguments.genome_sa_index_nbases = None
    reference_fasta = arguments.reference_fasta
    reference_gtf = arguments.reference_gtf
    arguments.reference_fasta = None
    arguments.reference_gtf = None
    terminal = _Terminal(
        "\n".join(
            (
                str(reference_fasta),
                str(reference_gtf),
                str(reads),
                "EV",
                "pair_1",
                "unstranded",
                "EV",
                "pair_2",
                "unstranded",
                "PUM1",
                "pair_1",
                "unstranded",
                "PUM1",
                "pair_2",
                "unstranded",
                "",
                "chrSynthetic",
                "",
                "",
                "",
            )
        )
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(onboarding.sys, "stdin", terminal)
    terminal_output = _Terminal()
    monkeypatch.setattr(onboarding.sys, "stderr", terminal_output)
    reference_reads = []
    read_reference = onboarding._reference_contigs

    def count_reference(path: Path) -> tuple[tuple[str, int], ...]:
        reference_reads.append(path)
        return read_reference(path)

    monkeypatch.setattr(onboarding, "_reference_contigs", count_reference)

    assert onboarding.init_project_from_args(arguments) == 0
    assert reference_reads == [reference_fasta]
    assert (output / "samples.tsv").is_file()
    assert (output / "partitions.tsv").is_file()
    definition = yaml.safe_load((output / "project.yaml").read_text(encoding="utf-8"))
    assert definition["dataset"]["samples"] == "samples.tsv"
    assert (
        definition["analyses"][arguments.analysis_name]["partitions"]
        == "partitions.tsv"
    )
    prompts = terminal_output.getvalue()
    plain_prompts = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", prompts)
    assert prompts.index("reference fasta") < prompts.index("FASTQ directory")
    assert (
        "Choose a regions file, or press Enter to type FASTA names/regions." in prompts
    )
    assert f"FASTA names/regions from {Path(reference_fasta).name}" in prompts
    assert "Accepted FASTA names (1): chrSynthetic" in plain_prompts


def test_guided_project_rejects_selector_absent_from_supplied_fasta(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arguments = _project_arguments(tmp_path, tmp_path / "guided", execute=False)
    _table, _sample_ids, rows = step08.validate_sample_manifest(
        arguments.sample_manifest
    )
    arguments.sample_manifest = None
    arguments.partition_manifest = None
    arguments.fastq = [
        Path(row[mate]) for row in rows for mate in ("r1_fastq", "r2_fastq")
    ]
    arguments.sample = [
        [row["sample_id"], row["condition"], row["replicate"], row["strandedness"]]
        for row in rows
    ]
    arguments.regions_file = []
    arguments.region = []
    monkeypatch.setattr(onboarding.sys, "stdin", _Terminal("\nnot-a-contig\n"))
    monkeypatch.setattr(onboarding.sys, "stderr", _Terminal())

    with pytest.raises(
        onboarding.OnboardingError, match="absent from the reference FASTA"
    ):
        onboarding._guided_manifest_members(
            arguments, reference_contigs=(("chrSynthetic", 12),)
        )


@pytest.mark.parametrize("site", (None, "viking"))
def test_guided_project_preview_replays_exact_answers_without_new_prompts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    site: str | None,
) -> None:
    study = tmp_path / "lab's study inputs"
    study.mkdir()
    projects = tmp_path / "scientist's Projects; retained"
    projects.mkdir()
    output = projects / "reviewed-study"
    arguments = _project_arguments(study, output, execute=False)
    arguments.site = site
    monkeypatch.delenv("EMRYS_SITE", raising=False)
    arguments.target_change = None
    arguments.mean_dp_threshold = None
    table, _, samples = step08.validate_sample_manifest(arguments.sample_manifest)
    for sample in samples:
        sample["replicate"] = f"matched-{sample['replicate']}"
    original = Path(samples[0]["r1_fastq"])
    renamed = original.with_name("instrument batch alpha.fastq")
    original.rename(renamed)
    samples[0]["r1_fastq"] = str(renamed)
    if site is not None:
        arguments.background_condition = "background"
        background = {
            **samples[0],
            "sample_id": "background_library",
            "condition": "background",
            "replicate": "background-1",
            "strandedness": "unknown",
        }
        for mate in ("r1_fastq", "r2_fastq"):
            path = study / f"background_{mate}.fastq"
            path.write_bytes(Path(background[mate]).read_bytes())
            background[mate] = str(path)
        samples.append(background)
        regions = study / "scientist's target regions.bed"
        regions.write_text("chrSynthetic\t0\t12\n", encoding="utf-8")
        arguments.partition_manifest.write_bytes(
            tsv_bytes(
                step08.PARTITION_MANIFEST_HEADER,
                [
                    {
                        "partition_id": "p1",
                        "selector_type": "regions_file",
                        "selector_value": str(regions),
                    }
                ],
            )
        )
    arguments.sample_manifest.write_bytes(tsv_bytes(table.header, samples))
    command = ["init", arguments.project_name, "--verbose"]
    for name, value in vars(arguments).items():
        if name not in {"project_name", "execute"} and value is not None:
            command.extend((f"--{name.replace('_', '-')}", str(value)))
    before = _tree_bytes(tmp_path)
    monkeypatch.chdir(projects)
    monkeypatch.setattr(onboarding.sys, "stdin", _Terminal("c>t\n71.5\n"))
    monkeypatch.setattr(onboarding.sys, "stderr", _Terminal())

    assert cli.main(command) == 0

    preview = capsys.readouterr().out
    assert _tree_bytes(tmp_path) == before
    assert not output.exists()
    assert "target change: C>T" in preview
    assert "mean dp threshold: 71.5" in preview
    assert (
        f"background condition: {arguments.background_condition or 'none'}" in preview
    )
    assert f"Analysis: {arguments.analysis_name}; site: {site or 'direct'}" in preview
    for sample in samples:
        assert (
            f"{sample['sample_id']}: condition={sample['condition']}; "
            f"pairing group={sample['replicate']}; strandedness={sample['strandedness']}"
        ) in preview
        for mate in ("r1_fastq", "r2_fastq"):
            assert sample[mate] in preview
    for path in (arguments.reference_fasta, arguments.reference_gtf):
        assert str(path) in preview
    assert "SHA-256" not in preview
    replay = next(line for line in preview.splitlines() if line.startswith("cd "))
    tokens = shlex.split(replay)
    assert tokens[:4] == ["cd", str(projects), "&&", sys.executable]
    assert tokens[-1] == "--execute"

    assert cli.main(tokens[tokens.index("emrys") + 1 :]) == 0
    assert "Project ready:" in capsys.readouterr().out
    expected = yaml.safe_load(
        (study / "source/project.yaml").read_text(encoding="utf-8")
    )
    expected["dataset"]["samples"] = "samples.tsv"
    expected["reference"].update(
        fasta=str(arguments.reference_fasta), gtf=str(arguments.reference_gtf)
    )
    analysis = expected["analyses"].pop("primary")
    analysis.update(
        partitions="partitions.tsv",
        target_change="C>T",
        mean_dp_threshold=71.5,
        background_condition=arguments.background_condition,
    )
    expected["analyses"][arguments.analysis_name] = analysis
    assert (
        yaml.safe_load((output / "project.yaml").read_text(encoding="utf-8"))
        == expected
    )
    assert (output / "runtime/profiles/default.yaml").read_bytes() == (
        execution_profile.project_default_profile_bytes(site)
    )
    assert _tree_bytes(study) == {
        name.removeprefix(f"{study.name}/"): data
        for name, data in before.items()
        if name.startswith(f"{study.name}/")
    }
    validated = onboarding.validate_project(output / "project.yaml")
    actual_samples = validated.project.select_analysis().workflow_inputs["samples"][
        "rows"
    ]
    for expected_sample, actual in zip(samples, actual_samples, strict=True):
        for name in ("sample_id", "condition", "replicate", "strandedness"):
            assert actual[name] == expected_sample[name]
        for mate in ("r1_fastq", "r2_fastq"):
            assert actual[mate]["path"] == expected_sample[mate]


@pytest.mark.parametrize("error", (onboarding.OnboardingError, KeyboardInterrupt))
@pytest.mark.parametrize(
    ("boundary", "phase"),
    (
        ("_admit_project_data", "Reading and hashing Project inputs"),
        (
            "validate_project_admission",
            "Checking reference and partition compatibility",
        ),
    ),
)
def test_init_progress_preserves_failed_or_interrupted_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: type[BaseException],
    boundary: str,
    phase: str,
) -> None:
    output = tmp_path / "my-study"
    monkeypatch.chdir(tmp_path)
    arguments = _project_arguments(tmp_path, output, execute=True)
    before = _tree_bytes(tmp_path)

    def fail(*_args: object, **_kwargs: object) -> None:
        raise error("injected validation failure")

    monkeypatch.setattr(onboarding, boundary, fail)
    if error is KeyboardInterrupt:
        with pytest.raises(KeyboardInterrupt):
            onboarding.init_project_from_args(arguments)
    else:
        assert onboarding.init_project_from_args(arguments) == 2

    after = _tree_bytes(tmp_path)
    assert all(after[path] == data for path, data in before.items())
    assert after == before
    assert not output.exists()
    captured = capsys.readouterr()
    assert f"{phase}: interrupted or failed" in captured.err
    assert f"{phase}: complete" not in captured.err
    assert "Project ready:" not in captured.out


def test_init_rejects_input_changed_during_publication_before_project_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "my-study"
    monkeypatch.chdir(tmp_path)
    arguments = _project_arguments(tmp_path, output, execute=True)

    def changed(_admission: object) -> None:
        raise contracts.ContractValidationError("Project input changed after admission")

    monkeypatch.setattr(
        normalization.ProjectAdmission, "require_inputs_unchanged", changed
    )

    assert onboarding.init_project_from_args(arguments) == 2
    assert output.is_dir()
    assert not (output / "project.yaml").exists()


def test_init_project_refuses_predecessor_without_changing_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "project"
    monkeypatch.chdir(tmp_path)
    arguments = _project_arguments(tmp_path, output, execute=True)
    output.mkdir()
    predecessor = output / "owned.txt"
    predecessor.write_bytes(b"preserve me\n")

    assert onboarding.init_project_from_args(arguments) == 2
    assert _tree_bytes(output) == {"owned.txt": b"preserve me\n"}


def test_init_project_requires_every_noninteractive_answer(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["init", "experiment"]) == 2
    error = capsys.readouterr().err
    assert "missing Project setup answers: --reference-fasta, --reference-gtf" in error


def test_init_project_prompts_and_requires_explicit_suggestion_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arguments = _project_arguments(tmp_path, tmp_path / "project", execute=False)
    arguments.target_change = None
    arguments.min_sample_dp = None
    terminal_input = _Terminal("C>T\n\n")
    terminal_output = _Terminal()
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr(onboarding.sys, "stdin", terminal_input)
    monkeypatch.setattr(onboarding.sys, "stderr", terminal_output)

    answers = onboarding._collect_project_answers(arguments, {}, tmp_path / "project")

    assert answers["target_change"] == "C>T"
    assert answers["min_sample_dp"] == 1
    assert "target change:" in terminal_output.getvalue()
    assert "min sample dp (Press ENTER for 1):" in terminal_output.getvalue()


def test_init_prompt_colors_label_and_dims_explicit_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    terminal_output = _Terminal()
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.setattr(onboarding.sys, "stdin", _Terminal("\n"))
    monkeypatch.setattr(onboarding.sys, "stderr", terminal_output)

    assert onboarding._prompt("min sample dp", "1") == "1"
    rendered = terminal_output.getvalue()
    assert "\x1b[" in rendered
    decoded = _decoded_terminal(rendered)
    assert decoded.plain == "min sample dp (Press ENTER for 1): "
    styles = {
        decoded.plain[span.start : span.end]: str(span.style) for span in decoded.spans
    }
    assert styles["min sample dp"] == "bold color(6)"
    assert styles[" (Press ENTER for 1)"] == "dim"


def test_init_project_rejects_eof_instead_of_accepting_a_suggestion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arguments = _project_arguments(tmp_path, tmp_path / "project", execute=False)
    arguments.min_sample_dp = None
    monkeypatch.setattr(onboarding.sys, "stdin", _Terminal())
    monkeypatch.setattr(onboarding.sys, "stderr", _Terminal())

    with pytest.raises(onboarding.OnboardingError, match="ended before min sample dp"):
        onboarding._collect_project_answers(arguments, {}, tmp_path / "project")


def test_init_project_suggests_star_values_from_declared_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "project"
    arguments = _project_arguments(tmp_path, output, execute=False)
    arguments.sjdb_overhang = None
    arguments.genome_sa_index_nbases = None
    members = onboarding._copied_manifest_members(arguments, output)
    terminal_output = _Terminal()
    monkeypatch.setattr(onboarding.sys, "stdin", _Terminal("\n\n"))
    monkeypatch.setattr(onboarding.sys, "stderr", terminal_output)

    answers = onboarding._collect_project_answers(arguments, members, output)

    assert answers["sjdb_overhang"] == 3
    assert answers["genome_sa_index_nbases"] == 1
    rendered = _decoded_terminal(terminal_output.getvalue()).plain
    assert "first complete record in each declared FASTQ" in rendered
    assert "maximum 4 bases" in rendered
    assert "12-base reference" in rendered
    assert "sjdb overhang (Press ENTER for 3):" in rendered
    assert "genome sa index nbases (Press ENTER for 1):" in rendered


def test_init_project_uses_derived_star_values_noninteractively(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "project"
    arguments = _project_arguments(tmp_path, output, execute=False)
    arguments.sjdb_overhang = None
    arguments.genome_sa_index_nbases = None
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(onboarding.sys, "stdin", io.StringIO())
    monkeypatch.setattr(onboarding.sys, "stderr", io.StringIO())

    assert onboarding.init_project_from_args(arguments) == 0
    assert not output.exists()


def test_star_read_length_inspection_accepts_gzip_and_stops_after_one_record(
    tmp_path: Path,
) -> None:
    fastq = tmp_path / "reads.fastq.gz"
    with gzip.open(fastq, "wt", encoding="ascii") as destination:
        destination.write("@first\nACGTAC\n+\nIIIIII\nmalformed trailing data")

    assert onboarding._first_fastq_read_length(fastq) == 6


@pytest.mark.parametrize(
    ("mate_marker", "suffix"),
    (("R", ".fastq.gz"), ("", ".fq.gz"), ("R", ".fq"), ("", ".fastq")),
)
def test_manifest_init_is_deterministic_validated_and_dry_run_first(
    tmp_path: Path,
    mate_marker: str,
    suffix: str,
) -> None:
    fastqs = _fastqs(
        tmp_path, "sample_b", "sample_a", mate_marker=mate_marker, suffix=suffix
    )
    regions = tmp_path / "targets.bed"
    regions.write_text("chr1\t0\t1\n", encoding="utf-8")
    output = tmp_path / "drafts"
    arguments = _manifest_command(
        output,
        tuple(reversed(fastqs)),
        samples=(
            ("sample_b", "treated", "pair_2", "reverse"),
            ("sample_a", "control", "pair_1", "forward"),
        ),
        partitions=(("--regions-file", "targets", str(regions)),),
    )

    assert cli.main(arguments) == 0
    assert not output.exists()
    assert cli.main([*arguments, "--execute"]) == 0
    assert set(_tree_bytes(output)) == {"samples.tsv", "partitions.tsv"}
    sample_table, sample_ids, _ = step08.validate_sample_manifest(
        output / "samples.tsv"
    )
    partitions = step08.validate_partition_manifest(output / "partitions.tsv")
    assert sample_table.header == step08.SAMPLE_MANIFEST_REQUIRED
    assert sample_ids == ["sample_a", "sample_b"]
    for row in sample_table.rows:
        for mate in (1, 2):
            assert row[f"r{mate}_fastq"] == str(
                tmp_path / f"{row['sample_id']}_{mate_marker}{mate}{suffix}"
            )
    assert [row["partition_id"] for row in partitions.rows] == ["targets"]

    sample_only = tmp_path / "sample-only"
    assert (
        cli.main(
            _manifest_command(
                sample_only,
                tuple(fastqs[:2]),
                samples=(("sample_b", "treated", "pair_2", "reverse"),),
                execute=True,
            )
        )
        == 0
    )
    assert set(_tree_bytes(sample_only)) == {"samples.tsv"}


def test_manifest_init_creates_six_vendor_libraries_and_25_chromosomes(
    tmp_path: Path,
) -> None:
    assignments = (
        ("ABE_EV_2", "EV", "replicate_2"),
        ("ABE_PUM1_2", "PUM1", "replicate_2"),
        ("ABE_EV_3", "EV", "replicate_3"),
        ("ABE_PUM1_3", "PUM1", "replicate_3"),
        ("ABE_EV4", "EV", "replicate_4"),
        ("ABE_PUM1_4", "PUM1", "replicate_4"),
    )
    fastqs = _fastqs(
        tmp_path, *(row[0] for row in assignments), mate_marker="", suffix=".fq.gz"
    )
    chromosomes = [str(number) for number in range(1, 23)] + ["X", "Y", "MT"]
    output = tmp_path / "drafts"
    command = _manifest_command(
        output,
        tuple(reversed(fastqs)),
        samples=tuple((*assignment, "reverse") for assignment in assignments),
        partitions=tuple(
            ("--region", chromosome, chromosome) for chromosome in reversed(chromosomes)
        ),
    )
    original = _tree_bytes(tmp_path)

    assert cli.main(command) == 0
    assert _tree_bytes(tmp_path) == original
    assert cli.main([*command, "--execute"]) == 0
    table, _, _ = step08.validate_sample_manifest(output / "samples.tsv")
    assert table.rows == [
        {
            "sample_id": sample,
            "r1_fastq": str(tmp_path / f"{sample}_1.fq.gz"),
            "r2_fastq": str(tmp_path / f"{sample}_2.fq.gz"),
            "strandedness": "reverse",
            "condition": condition,
            "replicate": replicate,
        }
        for sample, condition, replicate in sorted(assignments)
    ]
    partitions = step08.validate_partition_manifest(output / "partitions.tsv")
    assert partitions.rows == [
        dict(partition_id=value, selector_type="region", selector_value=value)
        for value in sorted(chromosomes)
    ]
    published = _tree_bytes(tmp_path)
    assert cli.main([*command, "--execute"]) == 2
    assert _tree_bytes(tmp_path) == published


@pytest.mark.parametrize(
    ("names", "message"),
    (
        (("sample_R1.fq.gz", "sample_1.fq.gz", "sample_2.fq.gz"), "duplicate R1"),
        (("sample_1.fq.gz", "sample_2.fq.gz", "sample_R2.fq.gz"), "duplicate R2"),
        (("sample_1.fq.gz", "sample_2.fq"), "different compression"),
        (("sample_1.fq.gz", "sample_3.fq.gz"), "FASTQ names must end"),
    ),
)
def test_manifest_init_rejects_ambiguous_or_invalid_vendor_mates(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    names: tuple[str, ...],
    message: str,
) -> None:
    fastqs = [tmp_path / name for name in names]
    for path in fastqs:
        path.write_bytes(b"structural drafting fixture\n")
    output = tmp_path / "drafts"
    before = _tree_bytes(tmp_path)
    assert (
        cli.main(
            _manifest_command(
                output,
                tuple(fastqs),
                samples=(("sample", "control", "pair_1", "reverse"),),
                execute=True,
            )
        )
        == 2
    )
    assert message in capsys.readouterr().err
    assert _tree_bytes(tmp_path) == before


@pytest.mark.parametrize(
    ("first", "second", "duplicate"),
    (
        ("--region", "--region", True),
        ("--regions-file", "--regions-file", True),
        ("--regions-file", "--region", True),
        ("--region", "--regions-file", False),
    ),
)
def test_manifest_init_partition_forms_share_one_unique_id_namespace(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    first: str,
    second: str,
    duplicate: bool,
) -> None:
    fastqs = _fastqs(tmp_path, "sample", mate_marker="")
    regions = tmp_path / "targets.bed"
    regions.write_text("chr2\t0\t1\n", encoding="utf-8")
    output = tmp_path / "drafts"
    partition_options = (
        (first, "p1"),
        (second, "p1" if duplicate else "p2"),
    )
    command = _manifest_command(
        output,
        tuple(fastqs),
        samples=(("sample", "control", "pair_1", "reverse"),),
        partitions=tuple(
            (
                option,
                name,
                str(regions) if option == "--regions-file" else "chr1",
            )
            for option, name in partition_options
        ),
        execute=True,
    )
    before = _tree_bytes(tmp_path)
    assert cli.main(command) == (2 if duplicate else 0)
    if duplicate:
        assert "duplicate" in capsys.readouterr().err
        assert _tree_bytes(tmp_path) == before
    else:
        table = step08.validate_partition_manifest(output / "partitions.tsv")
        assert table.rows == [
            dict(partition_id="p1", selector_type="region", selector_value="chr1"),
            dict(
                partition_id="p2",
                selector_type="regions_file",
                selector_value=str(regions),
            ),
        ]


@pytest.mark.parametrize(
    ("region", "valid"),
    (("chrSynthetic", True), ("missing", False), ("chrSynthetic:0-3", False)),
)
def test_manifest_init_output_passes_through_project_reference_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    region: str,
    valid: bool,
) -> None:
    project = tmp_path / "manifest-study"
    arguments = _project_arguments(tmp_path, project, execute=True)
    _, _, samples = step08.validate_sample_manifest(arguments.sample_manifest)
    drafts = tmp_path / "drafts"
    fastqs = []
    for row in samples:
        for mate in (1, 2):
            original = Path(row[f"r{mate}_fastq"])
            renamed = original.with_name(f"{row['sample_id']}_{mate}.fastq")
            original.rename(renamed)
            fastqs.append(str(renamed))
    command = _manifest_command(
        drafts,
        tuple(Path(path) for path in fastqs),
        samples=tuple(
            (
                row["sample_id"],
                row["condition"],
                row["replicate"],
                row["strandedness"],
            )
            for row in samples
        ),
        partitions=(("--region", "primary", region),),
        execute=True,
    )
    assert cli.main(command) == 0
    arguments.sample_manifest = drafts / "samples.tsv"
    arguments.partition_manifest = drafts / "partitions.tsv"
    before = _tree_bytes(tmp_path)
    monkeypatch.chdir(tmp_path)
    command = ["init", arguments.project_name]
    for name, value in vars(arguments).items():
        if name not in {"project_name", "execute"} and value is not None:
            command.extend((f"--{name.replace('_', '-')}", str(value)))

    assert cli.main([*command, "--execute"]) == (0 if valid else 2)
    if valid:
        assert cli.main(["validate", "--project", str(project)]) == 0
        admitted = onboarding.validate_project(project / "project.yaml")
        assert admitted.sample_count == 4
    else:
        assert "partition region" in capsys.readouterr().err
        assert not project.exists()
        assert _tree_bytes(tmp_path) == before


@pytest.mark.parametrize("mate_marker", ("R", ""))
def test_manifest_init_lists_missing_biology_and_writes_nothing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    mate_marker: str,
) -> None:
    fastqs = _fastqs(tmp_path, "sample_b", "sample_a", mate_marker=mate_marker)
    output = tmp_path / "drafts"

    assert cli.main(_manifest_command(output, tuple(fastqs), execute=True)) == 2
    assert not output.exists()
    error = capsys.readouterr().err
    assert "--sample sample_a CONDITION REPLICATE STRANDEDNESS" in error
    assert "--sample sample_b CONDITION REPLICATE STRANDEDNESS" in error


@pytest.mark.parametrize("mate_marker", ("R", ""))
def test_manifest_init_rejects_unpaired_fastq_without_writing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    mate_marker: str,
) -> None:
    r1 = _fastqs(tmp_path, "sample_a", mate_marker=mate_marker)[0]
    output = tmp_path / "drafts"
    result = cli.main(
        _manifest_command(
            output,
            (r1,),
            samples=(("sample_a", "control", "pair_1", "unknown"),),
            execute=True,
        )
    )

    assert result == 2
    assert not output.exists()
    assert "unpaired FASTQ sample: sample_a" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("unsafe_name", "message"),
    (("[literal]", "explicit normalized path"), ('literal"path', "raw TSV field")),
)
def test_manifest_init_rejects_paths_the_project_cannot_consume(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    unsafe_name: str,
    message: str,
) -> None:
    unsafe_directory = tmp_path / unsafe_name
    unsafe_directory.mkdir()
    fastqs = _fastqs(unsafe_directory, "sample_a")
    output = tmp_path / "drafts"

    assert (
        cli.main(
            _manifest_command(
                output,
                tuple(fastqs),
                samples=(("sample_a", "control", "pair_1", "forward"),),
                execute=True,
            )
        )
        == 2
    )
    assert not output.exists()
    assert message in capsys.readouterr().err


def test_manifest_init_rejects_a_condition_that_requires_tsv_quoting(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fastqs = _fastqs(tmp_path, "sample_a")
    output = tmp_path / "drafts"

    assert (
        cli.main(
            _manifest_command(
                output,
                tuple(fastqs),
                samples=(("sample_a", "bad\tcondition", "pair_1", "forward"),),
                execute=True,
            )
        )
        == 2
    )
    assert not output.exists()
    assert "condition must match" in capsys.readouterr().err


@pytest.mark.parametrize("mate_marker", ("R", ""))
def test_manifest_init_pairs_by_the_admitted_file_not_a_symlink_alias(
    tmp_path: Path,
    mate_marker: str,
) -> None:
    canonical = _fastqs(tmp_path, "actual", mate_marker=mate_marker)
    aliases = [tmp_path / f"alias_R{mate}.fastq.gz" for mate in (1, 2)]
    aliases[0].symlink_to(canonical[1])
    aliases[1].symlink_to(canonical[0])
    output = tmp_path / "drafts"

    assert (
        cli.main(
            _manifest_command(
                output,
                tuple(aliases),
                samples=(("actual", "control", "pair_1", "forward"),),
                execute=True,
            )
        )
        == 0
    )
    rows = step08.validate_sample_manifest(output / "samples.tsv")[0].rows
    assert rows[0]["r1_fastq"] == str(canonical[0])
    assert rows[0]["r2_fastq"] == str(canonical[1])


@pytest.mark.parametrize("mate_marker", ("R", ""))
def test_manifest_init_rejects_hard_linked_fastq_reuse(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    mate_marker: str,
) -> None:
    r1 = tmp_path / f"sample_a_{mate_marker}1.fastq.gz"
    r2 = tmp_path / f"sample_a_{mate_marker}2.fastq.gz"
    r1.write_bytes(b"same file\n")
    r2.hardlink_to(r1)
    output = tmp_path / "drafts"

    assert (
        cli.main(
            _manifest_command(
                output,
                (r1, r2),
                samples=(("sample_a", "control", "pair_1", "forward"),),
                execute=True,
            )
        )
        == 2
    )
    assert not output.exists()
    assert "one FASTQ file is reused" in capsys.readouterr().err


def test_synthetic_init_is_dry_run_first_and_refuses_predecessor(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "fixture"

    assert synthetic_fixture.init_from_args(_namespace(output, execute=False)) == 0
    assert not output.exists()
    assert "Dry-run complete" in capsys.readouterr().out

    output.mkdir()
    predecessor = output / "owned.txt"
    predecessor.write_bytes(b"preserve me\n")

    assert synthetic_fixture.init_from_args(_namespace(output, execute=True)) == 2
    captured = capsys.readouterr()
    assert "output directory must be absent" in captured.err
    assert _tree_bytes(output) == {"owned.txt": b"preserve me\n"}


def test_publication_re_admits_every_member_after_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "publication"
    real_write = onboarding._write_member

    def write_then_tamper(path: Path, data: bytes, mode: int) -> None:
        real_write(path, data, mode)
        if path.name == "complete.tsv":
            (path.parent / "project.yaml").write_bytes(b"changed after preparation\n")

    monkeypatch.setattr(onboarding, "_write_member", write_then_tamper)
    members = {"project.yaml": (b"original\n", 0o644)}

    with pytest.raises(
        onboarding.OnboardingError, match="member bytes changed"
    ) as failure:
        onboarding.publish_create_absent_tree(
            output,
            members,
            completion_name="complete.tsv",
            completion_bytes=b"complete\n",
        )

    assert "present-but-invalid" in str(failure.value)
    assert "presence alone is not completion proof" in str(failure.value)
    assert (output / "complete.tsv").is_file()
    assert (output / "project.yaml").read_bytes() == b"changed after preparation\n"


@pytest.mark.parametrize(
    "unsafe_name", ("../escape", "/absolute", "bad\\name", "bad\nname")
)
def test_publication_rejects_unsafe_member_paths(
    tmp_path: Path,
    unsafe_name: str,
) -> None:
    output = tmp_path / "publication"
    with pytest.raises(onboarding.OnboardingError, match="unsafe publication member"):
        onboarding.publish_create_absent_tree(
            output,
            {unsafe_name: (b"unsafe\n", 0o644)},
            completion_name="complete.tsv",
            completion_bytes=b"complete\n",
        )
    assert not output.exists()


@pytest.mark.parametrize("name", ("project", "manifests", "synthetic", "../escape"))
def test_init_rejects_reserved_or_unsafe_project_names(name: str) -> None:
    with pytest.raises(SystemExit) as raised:
        cli.main(["init", name])
    assert raised.value.code == 2


def test_project_lookup_is_exact_current_named_or_explicit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "experiment"
    project_root.mkdir()
    project = project_root / "project.yaml"
    project.write_text("project\n", encoding="utf-8")

    monkeypatch.chdir(project_root)
    assert onboarding.project_definition_path() == project
    monkeypatch.chdir(tmp_path)
    assert onboarding.project_definition_path("experiment") == project
    assert onboarding.project_definition_path(project) == project

    alias = tmp_path / "project-alias"
    alias.symlink_to(project_root, target_is_directory=True)
    with pytest.raises(onboarding.OnboardingError, match="unavailable"):
        onboarding.project_definition_path(alias)

    (tmp_path / "project.yaml").write_text("parent\n", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    monkeypatch.chdir(nested)
    with pytest.raises(onboarding.OnboardingError, match="unavailable"):
        onboarding.project_definition_path()


def test_synthetic_fixture_is_deterministic_complete_and_normalizable(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _publish_synthetic(first)
    _publish_synthetic(second)

    assert _tree_bytes(first) == _tree_bytes(second)
    assert {
        path.relative_to(first).as_posix() for path in first.rglob("*") if path.is_dir()
    } >= {"logs", "runs", "runtime"}
    assert all(
        stat.S_IMODE((first / name).stat().st_mode) == 0o700
        for name in onboarding.PROJECT_DIRECTORIES
    )
    assert not (first / "emrys.execution.yaml").exists()
    validation = onboarding.validate_project(first / "project.yaml")
    analysis = validation.project.select_analysis()
    source = analysis.workflow_inputs
    control = source["analysis"]["policy"]["configuration"]["control_condition"]
    assert validation.sample_count == 4
    assert analysis.name == "primary"
    assert (
        len(
            {
                row["replicate"]
                for row in source["samples"]["rows"]
                if row["condition"] == control
            }
        )
        == 2
    )
    assert len(source["partitions"]["rows"]) == 1
    assert validation.fasta_contigs == (("chrSynthetic", 100_000),)
    assert validation.transcript_count == 2
    metadata = json.loads((first / "fixture.json").read_text(encoding="utf-8"))
    assert metadata["schema_version"] == "emrys.synthetic-local-pilot.v2"
    assert metadata["dataset_profile"] == "smoke-v1"
    assert metadata["fixture_id"] == "deterministic-science-smoke-v1"
    assert metadata["read_pairs_per_library"] == 130
    assert metadata["core_read_pairs_per_library"] == 130
    assert metadata["neutral_background"]["pair_count_per_library"] == 0
    assert metadata["expected_terminal_computational_result"] == {
        "absolute_af_difference": 0.4375,
        "all_sites_rows": 3,
        "common_odds_ratio": 15.0,
        "control_af": 0.0625,
        "interpretation": "computational smoke expectation; not scientific adjudication",
        "significant_candidate_id": "REV_like|chrSynthetic|50000|A>G",
        "significant_sites_rows": 1,
        "treatment_af": 0.5,
    }
    assert metadata["expected_terminal_workflow"] == {
        "interpretation": (
            "synthetic functional expectation; not production, scientific-review, "
            "or biological evidence"
        ),
        "last_scientific_step": "10",
        "reporting_complete": True,
        "scientific_results_complete": True,
    }
    manifest = json.loads((first / synthetic_fixture.COMPLETION_MANIFEST).read_text())
    assert set(manifest) == set(_tree_bytes(first)) - {
        synthetic_fixture.COMPLETION_MANIFEST
    }
    for relative, record in manifest.items():
        data = (first / relative).read_bytes()
        assert record["size_bytes"] == len(data)
        assert record["sha256"] == hashlib.sha256(data).hexdigest()


def test_project_validation_reports_dataset_size_before_analysis_subset(
    tmp_path: Path,
) -> None:
    project_path = build(tmp_path / "project", replicate_count=3)
    definition = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    definition["analyses"]["a-subset"] = {
        **definition["analyses"].pop("primary"),
        "sample_ids": ["EV_2", "PUM1_2", "EV_3", "PUM1_3"],
    }
    project_path.write_text(
        yaml.safe_dump(definition, sort_keys=False),
        encoding="utf-8",
    )

    result = onboarding.validate_project(project_path, root=PACKAGE_ROOT)

    assert result.sample_count == 6
    selected_rows = result.project.select_analysis().workflow_inputs["samples"]["rows"]
    assert len(selected_rows) == 4


def test_production_like_profile_is_explicit_and_dry_run_skips_generation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "production-like"

    def fail_if_generated(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("dry-run generated production-like fixture members")

    monkeypatch.setattr(synthetic_fixture, "fixture_members", fail_if_generated)
    assert (
        synthetic_fixture.init_from_args(
            _namespace(
                output,
                execute=False,
                dataset_profile=synthetic_fixture.PRODUCTION_LIKE_DATASET_PROFILE,
            )
        )
        == 0
    )
    assert not output.exists()
    stdout = capsys.readouterr().out
    assert "Dataset profile: production-like-v1" in stdout
    assert "Read pairs per library: 100000" in stdout
    assert "Neutral unique/duplicate pairs per library: 89883/9987" in stdout
    assert "Reference length: 5000000" in stdout

    profile = synthetic_fixture.DATASET_PROFILES["production-like-v1"]
    metadata = synthetic_fixture.fixture_metadata(profile)
    assert metadata["fixture_id"] == "deterministic-production-like-v1"
    assert metadata["dataset_profile"] == "production-like-v1"
    assert metadata["seed"] == 20260814
    assert metadata["contig_length"] == 5_000_000
    assert metadata["read_pairs_per_library"] == 100_000
    assert metadata["core_read_pairs_per_library"] == 130
    assert metadata["neutral_background"] == {
        "deliberate_duplicate_pair_count_per_library": 9_987,
        "fragment_start_interval_0_based_half_open": [100_000, 4_999_776],
        "pair_count_per_library": 99_870,
        "placement_seed": 20260814,
        "reserved_core_region_1_based_closed": [1, 100_000],
        "unique_template_pair_count_per_library": 89_883,
    }
    assert metadata["star"] == {
        "genome_sa_index_nbases": 10,
        "sjdb_overhang": 74,
    }
    assert metadata["expected_terminal_computational_result"] == {
        "absolute_af_difference": 0.4375,
        "all_sites_rows": 3,
        "common_odds_ratio": 15.0,
        "control_af": 0.0625,
        "interpretation": (
            "computational production-like expectation; not scientific adjudication"
        ),
        "significant_candidate_id": "REV_like|chrSynthetic|50000|A>G",
        "significant_sites_rows": 1,
        "treatment_af": 0.5,
    }
    assert metadata["expected_terminal_workflow"]["last_scientific_step"] == "10"
    assert metadata["expected_terminal_workflow"]["scientific_results_complete"] is True
    assert metadata["expected_terminal_workflow"]["reporting_complete"] is True
    project = yaml.safe_load(synthetic_fixture._project_definition(profile))
    assert project["schema_version"] == "emrys.project.v1"
    assert project["dataset"] == {"samples": "samples.tsv"}
    assert project["reference"]["star_index"]["genome_sa_index_nbases"] == 10
    assert project["analyses"]["primary"]["partitions"] == "partitions.tsv"
    assert project["analyses"]["primary"]["target_change"] == "A>G"


def test_production_like_neutral_plan_is_globally_disjoint_and_guarded() -> None:
    profile = synthetic_fixture.DATASET_PROFILES["production-like-v1"]
    starts_by_sample: list[set[int]] = []
    for sample_index in range(len(synthetic_fixture.SAMPLES)):
        starts = {
            synthetic_fixture._neutral_unique_start(
                profile,
                sample_index,
                unique_index,
            )
            for unique_index in range(
                profile.neutral_unique_template_pair_count_per_library
            )
        }
        assert len(starts) == 89_883
        assert min(starts) >= 100_000
        assert max(starts) + synthetic_fixture.FRAGMENT_LENGTH <= 5_000_000
        starts_by_sample.append(starts)

        duplicate_sources = {
            synthetic_fixture._neutral_duplicate_source_index(
                profile,
                sample_index,
                duplicate_index,
            )
            for duplicate_index in range(
                profile.neutral_duplicate_pair_count_per_library
            )
        }
        assert len(duplicate_sources) == 9_987
        assert all(0 <= source_index < 89_883 for source_index in duplicate_sources)

    assert len(set().union(*starts_by_sample)) == 4 * 89_883
    guarded_positions = (30_000 - 1, 50_000 - 1, 50_010 - 1)
    assert all(
        not any(
            start <= position < start + synthetic_fixture.FRAGMENT_LENGTH
            for position in guarded_positions
        )
        for starts in starts_by_sample
        for start in starts
    )


def _tiny_neutral_profile() -> synthetic_fixture.DatasetProfile:
    return synthetic_fixture.DatasetProfile(
        name="test-neutral-v1",
        fixture_id="test-neutral-v1",
        seed=17,
        contig_length=52_500,
        pair_count_per_library=133,
        neutral_unique_template_pair_count_per_library=2,
        neutral_duplicate_pair_count_per_library=1,
        neutral_start_zero_based=51_900,
        genome_sa_index_nbases=3,
    )


def test_tiny_neutral_profile_exercises_unique_and_duplicate_records() -> None:
    profile = _tiny_neutral_profile()
    reference = synthetic_fixture._reference(profile)
    r1_records = list(
        synthetic_fixture._fastq_records(
            reference,
            synthetic_fixture.SAMPLES[0],
            0,
            profile,
            mate=1,
        )
    )
    r2_records = list(
        synthetic_fixture._fastq_records(
            reference,
            synthetic_fixture.SAMPLES[0],
            0,
            profile,
            mate=2,
        )
    )

    assert len(r1_records) == len(r2_records) == 133
    neutral_r1 = r1_records[-3:]
    neutral_r2 = r2_records[-3:]
    assert all(":NEUTRAL_UNIQUE:" in record for record in neutral_r1[:2])
    assert ":NEUTRAL_DUPLICATE:" in neutral_r1[2]
    source_index = synthetic_fixture._neutral_duplicate_source_index(profile, 0, 0)
    assert neutral_r1[2].splitlines()[1] == neutral_r1[source_index].splitlines()[1]
    assert neutral_r2[2].splitlines()[1] == neutral_r2[source_index].splitlines()[1]
    assert all(
        len(record.splitlines()[1]) == 75 for record in (*neutral_r1, *neutral_r2)
    )


def test_synthetic_streaming_helpers_fail_closed_and_flush(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = _tiny_neutral_profile()
    reference = "A" * profile.contig_length
    with pytest.raises(ValueError, match="FASTQ mate"):
        list(
            synthetic_fixture._fastq_records(
                reference,
                synthetic_fixture.SAMPLES[0],
                0,
                profile,
                mate=3,
            )
        )

    monkeypatch.setattr(
        synthetic_fixture,
        "_core_pairs",
        lambda *_args, **_kwargs: iter(()),
    )
    monkeypatch.setattr(
        synthetic_fixture,
        "_neutral_pairs",
        lambda *_args, **_kwargs: iter(()),
    )
    with pytest.raises(onboarding.OnboardingError, match="produced 0 pairs"):
        list(
            synthetic_fixture._fastq_records(
                reference,
                synthetic_fixture.SAMPLES[0],
                0,
                profile,
                mate=1,
            )
        )

    monkeypatch.setattr(synthetic_fixture, "GZIP_WRITE_BUFFER_SIZE", 5)
    assert (
        gzip.decompress(synthetic_fixture._gzip_records(iter(("abc", "defghij", "k"))))
        == b"abcdefghijk"
    )
    assert gzip.decompress(synthetic_fixture._gzip_records(iter(()))) == b""


def test_synthetic_profile_primitives_and_closed_selector_failures(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    profile = _tiny_neutral_profile()
    assert (
        synthetic_fixture._neutral_start_capacity(synthetic_fixture.DEFAULT_PROFILE)
        == 0
    )
    assert synthetic_fixture._coprime_step(1, profile.seed) == 1
    with pytest.raises(ValueError, match="modulus must be positive"):
        synthetic_fixture._coprime_step(0, profile.seed)
    with pytest.raises(ValueError, match="invalid sample index"):
        synthetic_fixture._neutral_unique_start(profile, -1, 0)
    with pytest.raises(ValueError, match="invalid neutral unique-template index"):
        synthetic_fixture._neutral_unique_start(profile, 0, 2)
    with pytest.raises(ValueError, match="invalid sample index"):
        synthetic_fixture._neutral_duplicate_source_index(profile, 4, 0)
    with pytest.raises(ValueError, match="invalid neutral duplicate index"):
        synthetic_fixture._neutral_duplicate_source_index(profile, 0, 1)

    output = tmp_path / "unsupported-profile"
    assert (
        synthetic_fixture.init_from_args(
            _namespace(output, execute=False, dataset_profile="not-a-profile")
        )
        == 2
    )
    assert not output.exists()
    assert "unsupported synthetic dataset profile" in capsys.readouterr().err


def test_synthetic_fastqs_have_complete_matching_mates(tmp_path: Path) -> None:
    import gzip

    output = tmp_path / "fixture"
    _publish_synthetic(output)
    for sample in synthetic_fixture.SAMPLES:
        sample_id = str(sample["sample_id"])
        with gzip.open(output / f"inputs/reads/{sample_id}_R1.fastq.gz", "rt") as r1:
            r1_lines = r1.read().splitlines()
        with gzip.open(output / f"inputs/reads/{sample_id}_R2.fastq.gz", "rt") as r2:
            r2_lines = r2.read().splitlines()
        assert (
            len(r1_lines)
            == len(r2_lines)
            == 4 * synthetic_fixture.PAIR_COUNT_PER_LIBRARY
        )
        assert [line.removesuffix("/1") for line in r1_lines[::4]] == [
            line.removesuffix("/2") for line in r2_lines[::4]
        ]
        assert all(len(sequence) == 75 for sequence in r1_lines[1::4])
        assert all(len(sequence) == 75 for sequence in r2_lines[1::4])


def test_project_validation_is_read_only(tmp_path: Path) -> None:
    output = tmp_path / "fixture"
    _publish_synthetic(output)
    before = _tree_bytes(output)

    assert (
        onboarding.validate_from_args(
            argparse.Namespace(project=output / "project.yaml")
        )
        == 0
    )

    assert _tree_bytes(output) == before


def test_project_validation_summary_is_analysis_module_neutral(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_path = tmp_path / "project.yaml"
    project_path.write_text("project: fixture\n", encoding="utf-8")
    analysis = SimpleNamespace(
        name="collaborator",
        workflow_inputs={
            "samples": {"rows": [{"sample_id": "sample"}]},
            "partitions": {"rows": [{"partition_id": "all"}]},
            "reference": {"fasta": {"path": "/reference.fa"}},
        },
    )
    result = onboarding.ProjectValidation(
        project=SimpleNamespace(
            source_path=project_path,
            source_sha256="0" * 64,
            analyses=(analysis,),
        ),
        fasta_contigs=(("chr1", 1),),
        transcript_count=1,
        sample_count=1,
        gtf_warnings=("fixture normalization warning",),
    )
    monkeypatch.setattr(onboarding, "validate_project", lambda _path: result)

    assert (
        onboarding.validate_from_args(
            argparse.Namespace(project=project_path, verbose=False)
        )
        == 0
    )
    normal = capsys.readouterr().out
    assert normal.splitlines() == ["Project validation: PASS"]
    assert (
        onboarding.validate_from_args(
            argparse.Namespace(project=project_path, verbose=True)
        )
        == 0
    )
    verbose = capsys.readouterr().out
    assert "collaborator: 1 samples, 1 partitions" in verbose
    assert "fixture normalization warning" in verbose


def test_project_validation_reports_invalid_project(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing_request = tmp_path / "missing-project.yaml"

    assert (
        onboarding.validate_from_args(argparse.Namespace(project=missing_request)) == 1
    )
    assert (
        "Project validation: FAIL — Project definition is unavailable"
        in capsys.readouterr().err
    )


@pytest.mark.parametrize("invocation_directory", ("checkout", "projects_parent"))
def test_public_cli_routes_synthetic_init_and_project_validation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    invocation_directory: str,
) -> None:
    projects = tmp_path / "projects"
    projects.mkdir()
    output = projects / "public-fixture"
    monkeypatch.chdir(
        Path(__file__).resolve().parents[3]
        if invocation_directory == "checkout"
        else projects
    )
    command = ["init", "synthetic", "--output-dir", str(output), "--site", "viking"]
    assert cli.main(command) == 0
    assert not output.exists()
    assert list(projects.iterdir()) == []
    assert cli.main([*command, "--execute"]) == 0
    assert (
        cli.main(
            [
                "validate",
                "--project",
                str(output),
            ]
        )
        == 0
    )
    assert (output / "runtime/profiles/default.yaml").read_bytes() == (
        execution_profile.project_default_profile_bytes("viking")
    )
    stdout = capsys.readouterr().out
    assert "Published deterministic synthetic Project" in stdout
    assert "Project validation: PASS" in stdout
    assert "Analysis revision:" not in stdout


@pytest.mark.parametrize(
    ("target", "old", "new", "message"),
    (
        (
            "inputs/reference/genes.gtf",
            "chrSynthetic",
            "chrAbsent",
            "contig is absent from FASTA",
        ),
        (
            "partitions.tsv",
            "primary\tregion\tchrSynthetic",
            "primary\tregion\tchrSynthetic:99999-100001",
            "outside FASTA bounds",
        ),
    ),
)
def test_project_validation_rejects_reference_incompatibility(
    tmp_path: Path,
    target: str,
    old: str,
    new: str,
    message: str,
) -> None:
    output = tmp_path / "fixture"
    _publish_synthetic(output)
    path = output / target
    path.write_text(
        path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8"
    )

    with pytest.raises(onboarding.OnboardingError, match=message):
        onboarding.validate_project(output / "project.yaml")


def test_project_validation_checks_regions_file_against_fasta(tmp_path: Path) -> None:
    output = tmp_path / "fixture"
    _publish_synthetic(output)
    regions = output / "regions.tsv"
    regions.write_text("chrSynthetic\t1\t100000\n", encoding="utf-8")
    (output / "partitions.tsv").write_text(
        "partition_id\tselector_type\tselector_value\n"
        "primary\tregions_file\tregions.tsv\n",
        encoding="utf-8",
    )
    result = onboarding.validate_project(output / "project.yaml")
    assert (
        len(result.project.select_analysis().workflow_inputs["partitions"]["rows"]) == 1
    )

    regions.write_text("chrAbsent\t1\t2\n", encoding="utf-8")
    with pytest.raises(onboarding.OnboardingError, match="absent from FASTA"):
        onboarding.validate_project(output / "project.yaml")


def test_project_validation_streams_gzip_regions_file(tmp_path: Path) -> None:
    import gzip

    output = tmp_path / "fixture"
    _publish_synthetic(output)
    regions = output / "regions.tsv.gz"
    with gzip.open(regions, "wt", encoding="utf-8", newline="") as handle:
        for start in range(1, 10_001):
            handle.write(f"chrSynthetic\t{start}\t{start}\n")
    (output / "partitions.tsv").write_text(
        "partition_id\tselector_type\tselector_value\n"
        "primary\tregions_file\tregions.tsv.gz\n",
        encoding="utf-8",
    )

    result = onboarding.validate_project(output / "project.yaml")

    assert (
        len(result.project.select_analysis().workflow_inputs["partitions"]["rows"]) == 1
    )


def test_project_validation_rejects_truncated_gzip_regions_file(
    tmp_path: Path,
) -> None:
    output = tmp_path / "fixture"
    _publish_synthetic(output)
    regions = output / "regions.tsv.gz"
    regions.write_bytes(gzip.compress(b"chrSynthetic\t1\t2\n")[:-4])
    (output / "partitions.tsv").write_text(
        "partition_id\tselector_type\tselector_value\n"
        "primary\tregions_file\tregions.tsv.gz\n",
        encoding="utf-8",
    )

    with pytest.raises(onboarding.OnboardingError, match="not valid UTF-8 text"):
        onboarding.validate_project(output / "project.yaml")


def _runtime_environment(tmp_path: Path) -> tuple[dict[str, str], Path]:
    tool_dir = tmp_path / "tools"
    tool_dir.mkdir()
    for command in onboarding.PATH_TOOL_COMMANDS.values():
        _executable(tool_dir / command)
    rscript = _executable(tmp_path / "Rscript")
    picard = tmp_path / "picard.jar"
    picard.write_bytes(b"synthetic jar\n")
    renv = tmp_path / "renv-library"
    renv.mkdir()
    return (
        {
            "PATH": str(tool_dir),
            "EMRYS_PICARD_JAR": str(picard),
            "EMRYS_RSCRIPT": str(rscript),
            "EMRYS_RENV_LIBRARY": str(renv),
        },
        tool_dir,
    )


def _project_with_owned_runtime(tmp_path: Path) -> Path:
    project = build(tmp_path)
    authored = tmp_path / "project.yaml"
    project.rename(authored)
    (tmp_path / "runtime").mkdir(mode=0o700, exist_ok=True)
    return authored


@pytest.mark.parametrize("mode", ("direct", "viking", "slurm"))
@pytest.mark.parametrize("resources", (False, True))
def test_profile_creation_previews_exact_settings_without_scientific_reads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mode: str,
    resources: bool,
) -> None:
    project = build(tmp_path / "Project's space")
    for path in (project.parent / "reads").iterdir():
        path.unlink()
    for path in (project.parent / "reference").iterdir():
        path.unlink()
    before = _tree_bytes(project.parent)
    monkeypatch.setattr(
        onboarding,
        "validate_project",
        lambda *_a, **_k: pytest.fail("Project validation is not profile authoring"),
    )
    monkeypatch.setattr(
        onboarding,
        "sha256_with_identity",
        lambda *_a, **_k: pytest.fail("scientific input hashing"),
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_a, **_k: pytest.fail("profile authoring executed a subprocess"),
    )
    arguments = ["profile", "create", "reviewed", "--project", str(project)]
    arguments += ["--site", "viking"] if mode == "viking" else ["--placement", mode]
    if mode != "direct":
        arguments += [
            "--cpus-per-task",
            "32",
            "--memory-mb",
            "1048576",
            "--time",
            "02:03:04",
            "--scratch-parent",
            str(tmp_path / "scratch's space"),
            "--account",
            "other-account",
            "--partition",
            "compute",
            "--qos",
            "normal",
            "--nodelist",
            "node[01-02]",
            "--exclusive",
            "--module-init",
            str(tmp_path / "modules.sh"),
            "--module",
            "compiler/1.2",
            "--module",
            "MPI/4.1",
        ]
    if resources:
        arguments += [
            "--workflow-cores",
            "16",
            "--workflow-memory-mb",
            "524288",
            "--step-threads",
            "00a=2",
            "--stage-memory-mb",
            "00a=1024",
            "--stage-concurrency",
            "01=1",
        ]
    assert cli.main(arguments) == 0
    preview = capsys.readouterr().out
    assert "Dry-run complete; no files were written" in preview
    assert _tree_bytes(project.parent) == before
    assert cli.main([*arguments, "--execute"]) == 0
    executed = capsys.readouterr().out
    assert preview.split("Dry-run complete")[0] == executed.split("Profile created.")[0]
    selected = execution_profile.project_execution_profile_path(project, "reviewed")
    profile = execution_profile.load_execution_profile(selected)
    defaults = execution_profile.load_execution_profile()
    assert (
        profile.resource_policy.default_sha256
        == defaults.resource_policy.default_sha256
    )
    assert profile.computational_resources_explicit is resources
    assert profile.resource_policy.declaration.workflow_cores == (
        16 if resources else "allocation"
    )
    assert profile.resource_policy.config_sha256 == (
        hashlib.sha256(selected.read_bytes()).hexdigest() if resources else None
    )
    if mode == "direct":
        assert profile.placement.document() == {"kind": "direct"}
    else:
        assert profile.placement.document() == {
            "kind": "slurm",
            "account": "other-account",
            "partition": "compute",
            "qos": "normal",
            "cpus_per_task": 32,
            "memory_mb": 1048576,
            "time": "02:03:04",
            "exclusive": True,
            "nodelist": "node[01-02]",
            "scratch_parent": str(tmp_path / "scratch's space"),
            "modules": {
                "mode": "exact",
                "init": str(tmp_path / "modules.sh"),
                "load": ["compiler/1.2", "MPI/4.1"],
            },
        }
        assert "compiler/1.2, MPI/4.1" in preview
        assert repr(str(tmp_path / "scratch's space")) in preview
    assert _tree_bytes(project.parent) == {
        **before,
        "runtime/profiles/reviewed.yaml": selected.read_bytes(),
    }
    saved = selected.stat(), selected.read_bytes()
    assert cli.main([*arguments, "--execute"]) == 2
    assert (selected.stat(), selected.read_bytes()) == saved


@pytest.mark.parametrize(
    "extra",
    (
        ["--placement", "direct", "--exclusive"],
        ["--placement", "direct", "--module-init", ""],
        ["--placement", "slurm"],
        ["--site", "viking", "--cpus-per-task", "0"],
        ["--site", "viking", "--cpus-per-task", "3", "--step-threads", "00a=4"],
        ["--site", "viking", "--memory-mb", "4096", "--workflow-memory-mb", "8192"],
        ["--site", "viking", "--memory-mb", "4096", "--stage-memory-mb", "00a=8192"],
        ["--site", "viking", "--module", "compiler/1.2"],
        ["--site", "viking", "--nodelist", "node;false"],
        ["--site", "viking", "--workflow-cores", "1", "--step-threads", "unknown=1"],
        ["--site", "viking", "--step-threads", "01=1", "--step-threads", "01=2"],
    ),
)
def test_profile_creation_rejects_invalid_choices_without_writes(
    tmp_path: Path, extra: list[str]
) -> None:
    project = build(tmp_path)
    before = _tree_bytes(tmp_path)
    assert (
        cli.main(
            ["profile", "create", "new", "--project", str(project), *extra, "--execute"]
        )
        == 2
    )
    assert _tree_bytes(tmp_path) == before


def test_profile_creation_authors_whole_node_and_symbolic_tool_limits(
    tmp_path: Path,
) -> None:
    project = build(tmp_path)
    original = (project.parent / "runtime/profiles/default.yaml").read_bytes()
    assert (
        cli.main(
            [
                "profile",
                "create",
                "full-node",
                "--project",
                str(project),
                "--site",
                "viking",
                "--cpus-per-task",
                "node",
                "--memory-mb",
                "0",
                "--workflow-cores",
                "allocation",
                "--workflow-memory-mb",
                "allocation",
                "--step-threads",
                "00a=workflow",
                "--stage-memory-mb",
                "00a=workflow",
                "--execute",
            ]
        )
        == 0
    )
    selected = execution_profile.load_execution_profile(
        project.parent / "runtime/profiles/full-node.yaml"
    )
    assert selected.placement.cpus_per_task == "node"
    assert selected.placement.memory_mb == 0
    assert selected.resource_policy.declaration.workflow_cores == "allocation"
    assert dict(selected.resource_policy.declaration.step_threads)["00a"] == "workflow"
    assert (project.parent / "runtime/profiles/default.yaml").read_bytes() == original


@pytest.mark.parametrize(
    "boundary", ("absolute", "nested", "symlink", "dangling", "directory", "parent")
)
def test_profile_creation_preserves_unsafe_or_occupied_destinations(
    tmp_path: Path, boundary: str
) -> None:
    project = build(tmp_path / "project")
    parent = project.parent / "runtime/profiles"
    destination = parent / "new.yaml"
    name = "new"
    if boundary == "absolute":
        name = str(tmp_path / "outside.yaml")
    elif boundary == "nested":
        name = "nested/new"
    elif boundary in {"symlink", "dangling"}:
        destination.symlink_to(
            parent / ("default.yaml" if boundary == "symlink" else "absent.yaml")
        )
    elif boundary == "directory":
        destination.mkdir()
    else:
        displaced = parent.with_name("preserved-profiles")
        parent.rename(displaced)
        parent.symlink_to(displaced, target_is_directory=True)
    before = _tree_bytes(tmp_path)
    assert (
        cli.main(
            [
                "profile",
                "create",
                name,
                "--project",
                str(project),
                "--placement",
                "direct",
                "--execute",
            ]
        )
        == 2
    )
    assert _tree_bytes(tmp_path) == before
    if boundary in {"symlink", "dangling"}:
        assert destination.is_symlink()
    elif boundary == "directory":
        assert destination.is_dir()


@pytest.mark.parametrize("change", ("parent", "destination", "default", "published"))
def test_profile_creation_detects_publication_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    change: str,
) -> None:
    project = build(tmp_path / "project")
    destination = project.parent / "runtime/profiles/new.yaml"
    defaults = tmp_path / "packaged-default.yaml"
    defaults.write_bytes(execution_profile.DEFAULT_PROFILE_PATH.read_bytes())
    monkeypatch.setattr(execution_profile, "DEFAULT_PROFILE_PATH", defaults)
    original_link = exclusive_publication.os.link
    displaced = destination.parent.with_name("preserved-profiles")
    redirected = tmp_path / "redirected"
    redirected.mkdir()

    def change_before_link(source: str, target: str, **kwargs) -> None:
        if change == "parent":
            destination.parent.rename(displaced)
            destination.parent.symlink_to(redirected, target_is_directory=True)
        elif change == "destination":
            destination.write_bytes(b"concurrent operator content\n")
        elif change == "default":
            document = yaml.safe_load(defaults.read_bytes())
            document["resources"]["workflow_cores"] = 8
            defaults.write_text(yaml.safe_dump(document))
        original_link(source, target, **kwargs)
        if change == "published":
            destination.write_bytes(destination.read_bytes() + b"# concurrent change\n")

    monkeypatch.setattr(exclusive_publication.os, "link", change_before_link)
    assert (
        cli.main(
            [
                "profile",
                "create",
                "new",
                "--project",
                str(project),
                "--placement",
                "direct",
                "--execute",
            ]
        )
        == 2
    )
    assert "Profile created." not in capsys.readouterr().out
    if change == "parent":
        assert not (redirected / "new.yaml").exists()
        assert (displaced / "new.yaml").exists()
    elif change == "destination":
        assert destination.read_bytes() == b"concurrent operator content\n"


def test_runtime_profile_path_derives_from_a_relative_default_project() -> None:
    assert onboarding.runtime_profile_path(Path("project.yaml")) == (
        Path.cwd() / "runtime/runtime.tsv"
    )


def _no_probe_inspection(
    profile_bytes: bytes,
    profile_path: Path,
    **_kwargs,
) -> RuntimeInspection:
    return RuntimeInspection(
        profile_path=profile_path,
        profile_sha256=hashlib.sha256(profile_bytes).hexdigest(),
        profile_bytes=profile_bytes,
        observations=(),
    )


def test_runtime_discovery_builds_project_owned_fixed_policy_without_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project_with_owned_runtime(tmp_path / "project")
    environment, tool_dir = _runtime_environment(tmp_path)
    monkeypatch.setattr(
        onboarding,
        "inspect_runtime_profile_bytes",
        _no_probe_inspection,
    )

    inspection = onboarding.discover_runtime_profile(
        project=project,
        environment=environment,
        root=PACKAGE_ROOT,
        python_executable=Path(sys.executable),
    )
    rows = list(
        csv.DictReader(
            inspection.profile_bytes.decode().splitlines(),
            delimiter="\t",
            strict=True,
        )
    )
    by_id = {row["check_id"]: row for row in rows}
    assert inspection.profile_path == project.parent / "runtime/runtime.tsv"
    assert onboarding.runtime_profile_path(project) == inspection.profile_path
    assert by_id["python"]["target"] == sys.executable
    assert by_id["star"]["target"] == str((tool_dir / "STAR").resolve())
    assert by_id["picard_jar"]["target"] == environment["EMRYS_PICARD_JAR"]
    assert by_id["renv_library"]["target"] == environment["EMRYS_RENV_LIBRARY"]
    assert len(rows) == 12
    assert set(rows[0]) == {"check_id", "target"}
    checks = {
        check.check_id: check
        for check in onboarding.runtime_profile_checks(
            inspection.profile_bytes, PACKAGE_ROOT
        )
    }
    assert len(checks) == 26
    assert checks["renv_project"].target == str(PACKAGE_ROOT)
    assert checks["picard"].probe_args[1] == environment["EMRYS_PICARD_JAR"]
    assert checks["r_variant_annotation"].probe_args == (environment["EMRYS_RSCRIPT"],)
    assert not inspection.profile_path.exists()


def test_runtime_discovery_does_not_require_writable_project_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project_with_owned_runtime(tmp_path / "project")
    environment, _tool_dir = _runtime_environment(tmp_path)
    real_admit = onboarding._admit_existing_path
    runtime_admissions: list[bool] = []

    def admit(value: str | Path, label: str, **options) -> Path:
        if label == "Project runtime directory":
            runtime_admissions.append(options["writable"])
        return real_admit(value, label, **options)

    monkeypatch.setattr(onboarding, "_admit_existing_path", admit)
    monkeypatch.setattr(
        onboarding,
        "inspect_runtime_profile_bytes",
        _no_probe_inspection,
    )

    onboarding.discover_runtime_profile(
        project=project,
        environment=environment,
        root=PACKAGE_ROOT,
    )

    assert runtime_admissions == [False]


def test_runtime_discovery_rejects_missing_and_ambiguous_tools(
    tmp_path: Path,
) -> None:
    project = _project_with_owned_runtime(tmp_path / "project")
    environment, first_dir = _runtime_environment(tmp_path)
    (first_dir / "STAR").unlink()

    with pytest.raises(onboarding.RuntimeDiscoveryError, match="star: STAR is absent"):
        onboarding.discover_runtime_profile(
            project=project,
            environment=environment,
            root=PACKAGE_ROOT,
        )

    _executable(first_dir / "STAR")
    second_dir = tmp_path / "second"
    second_dir.mkdir()
    _executable(second_dir / "STAR", "#!/bin/sh\nexit 99\n")
    environment["PATH"] = f"{first_dir}{os.pathsep}{second_dir}"

    with pytest.raises(
        onboarding.RuntimeDiscoveryError,
        match="multiple STAR installations",
    ):
        onboarding.discover_runtime_profile(
            project=project,
            environment=environment,
            root=PACKAGE_ROOT,
        )


def test_runtime_discovery_cli_is_dry_run_then_create_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = _project_with_owned_runtime(tmp_path / "project")
    environment, _tool_dir = _runtime_environment(tmp_path)
    monkeypatch.setattr(
        onboarding,
        "inspect_runtime_profile_bytes",
        _no_probe_inspection,
    )
    inspection = onboarding.discover_runtime_profile(
        project=project,
        environment=environment,
        root=PACKAGE_ROOT,
    )
    monkeypatch.setattr(
        onboarding,
        "_plan_runtime_discovery",
        lambda **_kwargs: onboarding._RuntimeDiscoveryPlan(
            inspection,
            lambda: onboarding.publish_runtime_profile(inspection) or inspection,
        ),
    )
    arguments = argparse.Namespace(project=project, execute=False, verbose=False)

    assert onboarding.discover_runtime_from_args(arguments) == 0
    preview = capsys.readouterr().out
    assert "Runtime discovery: READY" in preview
    assert "Dry-run complete" in preview
    assert "Runtime checks:" not in preview
    assert all(item.check.check_id not in preview for item in inspection.observations)
    assert not inspection.profile_path.exists()

    arguments.verbose = True
    assert onboarding.discover_runtime_from_args(arguments) == 0
    detailed = capsys.readouterr().out
    assert "Runtime checks:" in detailed
    assert all(item.check.check_id in detailed for item in inspection.observations)

    with monkeypatch.context() as terminal_context:
        terminal = _Terminal()
        terminal_context.delenv("NO_COLOR", raising=False)
        terminal_context.setenv("TERM", "xterm-256color")
        terminal_context.setattr(onboarding.sys, "stdout", terminal)
        arguments.verbose = False
        assert onboarding.discover_runtime_from_args(arguments) == 0
        assert "\x1b[" in terminal.getvalue()

    arguments.verbose = False
    arguments.execute = True
    assert onboarding.discover_runtime_from_args(arguments) == 0
    assert inspection.profile_path.read_bytes() == inspection.profile_bytes
    before = inspection.profile_path.stat()
    assert onboarding.discover_runtime_from_args(arguments) == 2
    assert inspection.profile_path.stat() == before


def test_runtime_publication_rejects_a_swapped_project_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _project_with_owned_runtime(tmp_path / "project")
    environment, _tool_dir = _runtime_environment(tmp_path)
    monkeypatch.setattr(
        onboarding,
        "inspect_runtime_profile_bytes",
        _no_probe_inspection,
    )
    inspection = onboarding.discover_runtime_profile(
        project=project,
        environment=environment,
        root=PACKAGE_ROOT,
    )
    runtime = project.parent / "runtime"
    displaced = project.parent / "runtime-displaced"
    redirected = tmp_path / "redirected"
    redirected.mkdir()
    real_link = exclusive_publication.os.link
    swapped = False

    def swap_parent(source: str, destination: str, **options) -> None:
        nonlocal swapped
        if not swapped:
            runtime.rename(displaced)
            runtime.symlink_to(redirected, target_is_directory=True)
            swapped = True
        real_link(source, destination, **options)

    monkeypatch.setattr(exclusive_publication.os, "link", swap_parent)

    with pytest.raises(onboarding.OnboardingError, match="changed during publication"):
        onboarding.publish_runtime_profile(inspection)

    assert not (redirected / "runtime.tsv").exists()


def _reuse_projects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from tests.evidence.runtime_availability.test_runtime_availability import (
        _managed_seal_fixture,
    )

    donor = _project_with_owned_runtime(tmp_path / "donor")
    borrower = _project_with_owned_runtime(tmp_path / "borrower")
    seal, inspection = _managed_seal_fixture(tmp_path, monkeypatch)
    (donor.parent / "runtime/runtime.tsv").write_bytes(inspection.profile_bytes)
    monkeypatch.setattr(
        doctor.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail(
            "runtime reuse launched a package manager or unmocked probe"
        ),
    )
    return donor, borrower, seal, inspection


def test_runtime_reuse_previews_then_seals_and_selects_without_installation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from emrys.evidence.runtime_availability import inspector

    donor, borrower, seal, original = _reuse_projects(tmp_path, monkeypatch)
    calls = []
    observe = inspector.run_checks

    def fresh(checks, *, environment):
        calls.append(tuple(checks))
        return observe(checks, environment=environment)

    monkeypatch.setattr(inspector, "run_checks", fresh)
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    arguments = argparse.Namespace(project=borrower, from_project=donor, execute=False)
    assert onboarding.discover_runtime_from_args(arguments) == 0
    assert "Dry-run complete" in capsys.readouterr().out
    assert before == {
        path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    }
    assert len(calls) == 1
    arguments.execute = True
    assert onboarding.discover_runtime_from_args(arguments) == 0
    selected = borrower.parent / "runtime/runtime.tsv"
    assert selected.read_bytes().startswith(b"seal_path\tseal_sha256\tpython\n")
    assert len(calls) == 3
    assert (donor.parent / "runtime/runtime.tsv").read_bytes() == original.profile_bytes
    assert not (seal.parent / "maintenance.lock").exists()
    assert inspector.load_runtime_seal(seal).data == seal.read_bytes()
    another = _project_with_owned_runtime(tmp_path / "another-borrower")
    identity = seal.stat()
    onboarding.reuse_runtime_profile(project=another, donor=donor, execute=True)
    assert len(calls) == 4
    assert seal.stat() == identity
    assert (
        another.parent / "runtime/runtime.tsv"
    ).read_bytes() == selected.read_bytes()
    with pytest.raises(onboarding.OnboardingError, match="already exists"):
        onboarding.reuse_runtime_profile(project=borrower, donor=donor, execute=True)
    assert len(calls) == 4


def test_runtime_reuse_interactive_confirmation_reuses_preview_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from emrys.evidence.runtime_availability import inspector

    donor, borrower, _seal, _original = _reuse_projects(tmp_path, monkeypatch)
    calls = []
    observe = inspector.run_checks

    def fresh(checks, *, environment):
        calls.append(tuple(checks))
        return observe(checks, environment=environment)

    monkeypatch.setattr(inspector, "run_checks", fresh)
    output, errors = _Terminal(), _Terminal()
    monkeypatch.setattr(onboarding.sys, "stdin", _Terminal("y\n"))
    monkeypatch.setattr(onboarding.sys, "stdout", output)
    monkeypatch.setattr(onboarding.sys, "stderr", errors)
    arguments = argparse.Namespace(
        project=borrower,
        from_project=donor,
        execute=False,
        replace=False,
        verbose=False,
    )

    assert onboarding.discover_runtime_from_args(arguments) == 0
    assert len(calls) == 2
    assert (borrower.parent / "runtime/runtime.tsv").is_file()
    assert "Runtime discovery" in _decoded_terminal(output.getvalue()).plain
    assert "Runtime inventory admitted" in _decoded_terminal(output.getvalue()).plain
    assert (
        "Admit this runtime inventory? [y/N]"
        in _decoded_terminal(errors.getvalue()).plain
    )


def test_runtime_reuse_confirmation_rejects_content_changed_after_preview(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    donor, borrower, seal, _original = _reuse_projects(tmp_path, monkeypatch)
    plan = onboarding._plan_runtime_reuse(project=borrower, donor=donor)
    (seal.parent / "managed/star").write_bytes(b"changed after preview\n")

    with pytest.raises(onboarding.OnboardingError, match="changed after preview"):
        plan.admit()

    assert not seal.exists()
    assert (seal.parent / "maintenance.lock").is_file()
    assert not (borrower.parent / "runtime/runtime.tsv").exists()


def test_runtime_reuse_explicitly_replaces_only_the_same_shared_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from emrys.evidence.runtime_availability import inspector

    donor, borrower, old_seal, original = _reuse_projects(tmp_path, monkeypatch)
    onboarding.reuse_runtime_profile(project=borrower, donor=donor, execute=True)
    old_selection = (borrower.parent / "runtime/runtime.tsv").read_bytes()
    old_seal_bytes = old_seal.read_bytes()

    generation = donor.parent / "runtime/generations" / ("a" * 32)
    shutil.copytree(old_seal.parent / "managed", generation / "managed")
    old_managed = old_seal.parent / "managed"
    choices = inspector.runtime_profile_choices(original.profile_bytes)
    replacement_choices = {
        key: generation / "managed" / path.relative_to(old_managed)
        if path.is_relative_to(old_managed)
        else path
        for key, path in choices.items()
    }
    replacement_data = inspector.runtime_profile_bytes(replacement_choices)
    replacement = inspector.inspect_runtime_profile_bytes(
        replacement_data,
        donor.parent / "runtime/runtime.tsv",
        checks=inspector.runtime_profile_checks(replacement_data, tmp_path),
        environment={
            "RENV_LIBRARY": str(replacement_choices["renv_library"]),
        },
    )
    replacement_seal = generation / "shared.json"
    replacement_seal.write_bytes(
        inspector.runtime_seal_bytes(replacement, replacement_seal)
    )
    donor_profile = inspector.shared_runtime_profile_bytes(
        replacement_seal, replacement_seal.read_bytes(), Path(sys.executable)
    )
    (donor.parent / "runtime/runtime.tsv").write_bytes(donor_profile)

    preview = onboarding.reuse_runtime_profile(
        project=borrower,
        donor=donor,
        execute=False,
        replace_existing=True,
    )
    assert (borrower.parent / "runtime/runtime.tsv").read_bytes() == old_selection
    assert preview.profile_bytes.startswith(
        f"seal_path\tseal_sha256\tpython\n{replacement_seal}\t".encode()
    )
    onboarding.reuse_runtime_profile(
        project=borrower,
        donor=donor,
        execute=True,
        replace_existing=True,
    )

    assert (
        borrower.parent / "runtime/runtime.tsv"
    ).read_bytes() == preview.profile_bytes
    assert old_seal.read_bytes() == old_seal_bytes
    assert not (borrower.parent / "runtime/maintenance.lock").exists()
    other = _project_with_owned_runtime(tmp_path / "other")
    (other.parent / "runtime/runtime.tsv").write_bytes(
        inspector.shared_runtime_profile_bytes(
            tmp_path / "different/runtime/shared.json",
            b"different source\n",
            Path(sys.executable),
        )
    )
    with pytest.raises(onboarding.OnboardingError, match="same source Project"):
        onboarding.reuse_runtime_profile(
            project=other,
            donor=donor,
            execute=True,
            replace_existing=True,
        )


@pytest.mark.parametrize("failure", ("before_seal", "after_seal", "borrower"))
@pytest.mark.parametrize("error_type", (OSError, KeyboardInterrupt))
def test_runtime_reuse_publication_failure_preserves_seal_and_claim_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
    error_type: type[BaseException],
) -> None:
    donor, borrower, seal, _original = _reuse_projects(tmp_path, monkeypatch)
    publish = onboarding.publish_exclusive

    def fail(path, data, publication_error_type, **kwargs):
        if path == seal and failure == "before_seal":
            raise error_type("injected seal publication failure")
        if path != seal and failure == "borrower":
            raise error_type("injected borrower publication failure")
        publish(path, data, publication_error_type, **kwargs)
        if path == seal and failure == "after_seal":
            raise error_type("injected post-publication failure")

    monkeypatch.setattr(onboarding, "publish_exclusive", fail)
    with pytest.raises(error_type, match="injected"):
        onboarding.reuse_runtime_profile(project=borrower, donor=donor, execute=True)
    assert seal.exists() is (failure != "before_seal")
    assert (seal.parent / "maintenance.lock").exists() is (failure != "borrower")
    assert not (borrower.parent / "runtime/runtime.tsv").exists()


@pytest.mark.parametrize("sealed", (False, True))
def test_runtime_reuse_refuses_outstanding_donor_claim_before_any_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sealed: bool,
) -> None:
    from emrys.evidence.runtime_availability import inspector

    donor, borrower, seal, original = _reuse_projects(tmp_path, monkeypatch)
    if sealed:
        seal.write_bytes(inspector.runtime_seal_bytes(original, seal))
    claim = seal.parent / "maintenance.lock"
    claim.write_bytes(b"unresolved owner\n")
    monkeypatch.setattr(
        inspector,
        "run_checks",
        lambda *_args, **_kwargs: pytest.fail("claimed donor was probed"),
    )
    with pytest.raises(
        (onboarding.OnboardingError, inspector.RuntimeInspectionError), match="claim"
    ):
        onboarding.reuse_runtime_profile(project=borrower, donor=donor, execute=True)
    assert claim.read_bytes() == b"unresolved owner\n"
    assert not (borrower.parent / "runtime/runtime.tsv").exists()


def test_runtime_reuse_rechecks_content_after_seal_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from emrys.evidence.runtime_availability import inspector

    donor, borrower, seal, _original = _reuse_projects(tmp_path, monkeypatch)
    publish = onboarding.publish_exclusive

    def mutate_after_seal(path, data, error_type, **kwargs):
        publish(path, data, error_type, **kwargs)
        if path == seal:
            (seal.parent / "managed/star").write_bytes(b"same version, changed bytes\n")

    monkeypatch.setattr(onboarding, "publish_exclusive", mutate_after_seal)
    with pytest.raises(
        inspector.RuntimeInspectionError, match="content or version changed"
    ):
        onboarding.reuse_runtime_profile(project=borrower, donor=donor, execute=True)
    assert seal.exists()
    assert not (seal.parent / "maintenance.lock").exists()
    assert not (borrower.parent / "runtime/runtime.tsv").exists()
