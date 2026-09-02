from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import stat
import sys
from pathlib import Path

import pytest
import yaml

from emrys import __main__ as cli
from emrys.contracts.scientific_evidence import step08
from emrys.evidence.runtime_availability.inspector import RuntimeInspection
from emrys.libraries.validation.tsv import tsv_bytes
from emrys.libraries import exclusive_publication
from emrys.orchestration.local_pilot import doctor, onboarding, synthetic_fixture
from tests.orchestration.local_pilot.fixture import build

REPO_ROOT = Path(__file__).resolve().parents[3]


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


def _fastqs(root: Path, *sample_ids: str) -> list[Path]:
    paths = [root / f"{sample}_R{mate}.fastq.gz" for sample in sample_ids for mate in (1, 2)]
    for path in paths:
        path.write_bytes(b"not inspected by structural drafting\n")
    return paths


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


def test_init_project_is_dry_run_first_and_creates_only_the_project_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "project"
    monkeypatch.chdir(tmp_path)
    arguments = _project_arguments(tmp_path, output, execute=False)
    assert onboarding.init_project_from_args(arguments) == 0
    assert not output.exists()
    assert "Dry-run complete" in capsys.readouterr().out

    arguments.execute = True
    assert onboarding.init_project_from_args(arguments) == 0
    assert set(_tree_bytes(output)) == {
        "project.yaml",
        "runtime/profiles/default.yaml",
    }
    directories = {path.name for path in output.iterdir() if path.is_dir()}
    assert directories == {"logs", "runs", "runtime"}
    assert all(
        stat.S_IMODE((output / name).stat().st_mode) == 0o700
        for name in directories
    )
    definition = yaml.safe_load((output / "project.yaml").read_text(encoding="utf-8"))
    assert definition["schema_version"] == "emrys.project.v1"
    assert definition["dataset"]["samples"] == str(arguments.sample_manifest.resolve())
    assert definition["analyses"][arguments.analysis_name]["partitions"] == str(
        arguments.partition_manifest.resolve()
    )
    assert Path(definition["reference"]["fasta"]).is_absolute()
    assert definition["analyses"][arguments.analysis_name]["target_change"] == "A>G"
    assert not list(output.rglob("*.fastq"))
    assert onboarding.validate_project(output / "project.yaml").sample_count == 4


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
    assert "missing Project setup answers" in error
    assert "--sample-manifest" in error
    assert "--background-max-fraction" in error


def test_init_project_prompts_and_requires_explicit_suggestion_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Terminal(io.StringIO):
        def isatty(self) -> bool:
            return True

    arguments = _project_arguments(tmp_path, tmp_path / "project", execute=False)
    arguments.target_change = None
    arguments.min_sample_dp = None
    terminal_input = Terminal("C>T\n\n")
    terminal_output = Terminal()
    monkeypatch.setattr(onboarding.sys, "stdin", terminal_input)
    monkeypatch.setattr(onboarding.sys, "stderr", terminal_output)

    answers = onboarding._collect_project_answers(arguments)

    assert answers["target_change"] == "C>T"
    assert answers["min_sample_dp"] == 1
    assert "target change:" in terminal_output.getvalue()
    assert "min sample dp [1]:" in terminal_output.getvalue()


def test_init_project_rejects_eof_instead_of_accepting_a_suggestion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Terminal(io.StringIO):
        def isatty(self) -> bool:
            return True

    arguments = _project_arguments(tmp_path, tmp_path / "project", execute=False)
    arguments.min_sample_dp = None
    monkeypatch.setattr(onboarding.sys, "stdin", Terminal())
    monkeypatch.setattr(onboarding.sys, "stderr", Terminal())

    with pytest.raises(onboarding.OnboardingError, match="ended before min sample dp"):
        onboarding._collect_project_answers(arguments)


def test_manifest_init_is_deterministic_validated_and_dry_run_first(
    tmp_path: Path,
) -> None:
    fastqs = _fastqs(tmp_path, "sample_b", "sample_a")
    regions = tmp_path / "targets.bed"
    regions.write_text("chr1\t0\t1\n", encoding="utf-8")
    output = tmp_path / "drafts"
    arguments = [
        "init", "manifests", "--output-dir", str(output), "--fastq",
        *(str(path) for path in reversed(fastqs)),
        "--sample", "sample_b", "treated", "pair_2", "reverse",
        "--sample", "sample_a", "control", "pair_1", "forward",
        "--regions-file", "targets", str(regions),
    ]

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
    assert [row["partition_id"] for row in partitions.rows] == ["targets"]

    sample_only = tmp_path / "sample-only"
    assert cli.main([
        "init", "manifests", "--output-dir", str(sample_only), "--fastq",
        str(fastqs[0]), str(fastqs[1]),
        "--sample", "sample_b", "treated", "pair_2", "reverse", "--execute",
    ]) == 0
    assert set(_tree_bytes(sample_only)) == {"samples.tsv"}


def test_manifest_init_lists_missing_biology_and_writes_nothing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fastqs = _fastqs(tmp_path, "sample_b", "sample_a")
    output = tmp_path / "drafts"

    assert cli.main([
        "init", "manifests", "--output-dir", str(output), "--fastq",
        *(str(path) for path in fastqs), "--execute",
    ]) == 2
    assert not output.exists()
    error = capsys.readouterr().err
    assert "--sample sample_a CONDITION REPLICATE STRANDEDNESS" in error
    assert "--sample sample_b CONDITION REPLICATE STRANDEDNESS" in error


def test_manifest_init_rejects_unpaired_fastq_without_writing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    r1 = _fastqs(tmp_path, "sample_a")[0]
    output = tmp_path / "drafts"
    result = cli.main([
        "init", "manifests", "--output-dir", str(output), "--fastq", str(r1),
        "--sample", "sample_a", "control", "pair_1", "unknown", "--execute",
    ])

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

    assert cli.main([
        "init", "manifests", "--output-dir", str(output), "--fastq",
        *(str(path) for path in fastqs),
        "--sample", "sample_a", "control", "pair_1", "forward", "--execute",
    ]) == 2
    assert not output.exists()
    assert message in capsys.readouterr().err


def test_manifest_init_rejects_a_condition_that_requires_tsv_quoting(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fastqs = _fastqs(tmp_path, "sample_a")
    output = tmp_path / "drafts"

    assert cli.main([
        "init", "manifests", "--output-dir", str(output), "--fastq",
        *(str(path) for path in fastqs),
        "--sample", "sample_a", "bad\tcondition", "pair_1", "forward",
        "--execute",
    ]) == 2
    assert not output.exists()
    assert "condition must match" in capsys.readouterr().err


def test_manifest_init_pairs_by_the_admitted_file_not_a_symlink_alias(
    tmp_path: Path,
) -> None:
    canonical = _fastqs(tmp_path, "actual")
    aliases = [tmp_path / f"alias_R{mate}.fastq.gz" for mate in (1, 2)]
    aliases[0].symlink_to(canonical[1])
    aliases[1].symlink_to(canonical[0])
    output = tmp_path / "drafts"

    assert cli.main([
        "init", "manifests", "--output-dir", str(output), "--fastq",
        *(str(path) for path in aliases),
        "--sample", "actual", "control", "pair_1", "forward",
        "--execute",
    ]) == 0
    rows = step08.validate_sample_manifest(output / "samples.tsv")[0].rows
    assert rows[0]["r1_fastq"] == str(canonical[0])
    assert rows[0]["r2_fastq"] == str(canonical[1])


def test_manifest_init_rejects_hard_linked_fastq_reuse(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    r1 = tmp_path / "sample_a_R1.fastq.gz"
    r2 = tmp_path / "sample_a_R2.fastq.gz"
    r1.write_bytes(b"same file\n")
    r2.hardlink_to(r1)
    output = tmp_path / "drafts"

    assert cli.main([
        "init", "manifests", "--output-dir", str(output), "--fastq", str(r1), str(r2),
        "--sample", "sample_a", "control", "pair_1", "forward", "--execute",
    ]) == 2
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
        path.relative_to(first).as_posix()
        for path in first.rglob("*")
        if path.is_dir()
    } >= {"logs", "runs", "runtime"}
    assert all(
        stat.S_IMODE((first / name).stat().st_mode) == 0o700
        for name in onboarding.PROJECT_DIRECTORIES
    )
    assert not (first / "emrys.execution.yaml").exists()
    validation = onboarding.validate_project(first / "project.yaml")
    analysis = validation.project.select_analysis()
    source = analysis.workflow_inputs
    control = source["analysis"]["policy"]["control_condition"]
    assert validation.sample_count == 4
    assert analysis.name == "primary"
    assert len(
        {
            row["replicate"]
            for row in source["samples"]["rows"]
            if row["condition"] == control
        }
    ) == 2
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

    result = onboarding.validate_project(project_path, root=REPO_ROOT)

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


def test_project_validation_reports_invalid_project(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing_request = tmp_path / "missing-project.yaml"

    assert (
        onboarding.validate_from_args(argparse.Namespace(project=missing_request)) == 1
    )
    assert "ERROR:" in capsys.readouterr().err


def test_public_cli_routes_synthetic_init_and_project_validation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "public-fixture"
    assert (
        cli.main(
            [
                "init",
                "synthetic",
                "--output-dir",
                str(output),
                "--execute",
            ]
        )
        == 0
    )
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
    assert len(
        result.project.select_analysis().workflow_inputs["partitions"]["rows"]
    ) == 1

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

    assert len(
        result.project.select_analysis().workflow_inputs["partitions"]["rows"]
    ) == 1


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


def test_runtime_profile_path_derives_from_a_relative_default_project() -> None:
    assert onboarding.runtime_profile_path(Path("project.yaml")) == (
        Path.cwd() / "runtime/runtime.tsv"
    )


def _no_probe_inspection(
    profile_bytes: bytes,
    profile_path: Path,
    runtime_context: str,
    **_kwargs,
) -> RuntimeInspection:
    return RuntimeInspection(
        profile_path=profile_path,
        profile_sha256=hashlib.sha256(profile_bytes).hexdigest(),
        profile_bytes=profile_bytes,
        runtime_context=runtime_context,
        observations=(),
        rendered_bytes=b"",
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
        root=REPO_ROOT,
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
    assert json.loads(by_id["picard"]["probe_args"])[1] == environment[
        "EMRYS_PICARD_JAR"
    ]
    assert json.loads(by_id["r_variant_annotation"]["probe_args"]) == [
        environment["EMRYS_RSCRIPT"]
    ]
    assert not inspection.profile_path.exists()


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
            root=REPO_ROOT,
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
            root=REPO_ROOT,
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
        root=REPO_ROOT,
    )
    monkeypatch.setattr(
        onboarding,
        "discover_runtime_profile",
        lambda **_kwargs: inspection,
    )
    arguments = argparse.Namespace(project=project, execute=False)

    assert onboarding.discover_runtime_from_args(arguments) == 0
    assert "Dry-run complete" in capsys.readouterr().out
    assert not inspection.profile_path.exists()

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
        root=REPO_ROOT,
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
