from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

import emrys.analyses as analysis_modules
from emrys.analyses import LoadedAnalysisModuleV1
from emrys.analyses.paired_cmh_candidate_ranking import analysis_module_v1
from emrys.contracts.orchestration import api as contracts
from emrys.libraries.installed_package_identity import (
    InstalledPackageTreeIdentity,
    InstalledProviderV1,
)
from emrys.orchestration.local_pilot import normalization
from emrys.orchestration.local_pilot.normalization import admit_project
from tests.orchestration.local_pilot import fixture

REPO_ROOT = Path(__file__).resolve().parents[3]
LOCAL_PROFILE = REPO_ROOT / "workflow/contracts/local_cmh_v2.json"


def test_analysis_revision_is_path_and_name_neutral(
    tmp_path: Path,
) -> None:
    project_path = fixture.build(tmp_path / "project-root")
    first_project = admit_project(project_path, fixture.profile())
    first = first_project.select_analysis()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    previous = Path.cwd()
    try:
        os.chdir(elsewhere)
        second = admit_project(project_path, fixture.profile()).select_analysis()
    finally:
        os.chdir(previous)

    relocated = admit_project(
        fixture.build(tmp_path / "relocated-project-root"),
        fixture.profile(),
    ).select_analysis()
    assert first.revision.canonical_bytes == second.revision.canonical_bytes
    assert first.revision.canonical_bytes == relocated.revision.canonical_bytes

    original_project_hash = first_project.source_sha256
    project_path.write_text(
        project_path.read_text(encoding="utf-8").replace(
            "  primary:\n", "  renamed:\n"
        ),
        encoding="utf-8",
    )
    renamed_project = admit_project(project_path, fixture.profile())
    renamed = renamed_project.select_analysis()
    assert renamed.name == "renamed"
    assert renamed_project.source_sha256 != original_project_hash
    assert renamed.revision.canonical_bytes == first.revision.canonical_bytes
    assert (
        renamed_project.select_analysis(
            "primary",
            expected_revision=first.revision,
        ).name
        == "renamed"
    )
    contracts.validate_record("application-model", first.revision.record)


def test_explicit_module_normalizes_once_without_provider_facts_in_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_path = fixture.build(tmp_path / "project-root")
    flat_revision = admit_project(project_path, fixture.profile()).select_analysis().revision
    definition = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    authored = definition["analyses"]["primary"]
    partitions = authored.pop("partitions")
    definition["analyses"]["primary"] = {
        "module": "emrys.paired-cmh",
        "partitions": partitions,
        "config": authored,
    }
    project_path.write_text(yaml.safe_dump(definition), encoding="utf-8")

    descriptor = analysis_module_v1()
    original_normalize = descriptor.normalize_config
    calls = 0

    def normalize(config, context):
        nonlocal calls
        calls += 1
        return original_normalize(config, context)

    descriptor = replace(descriptor, normalize_config=normalize)
    package = InstalledPackageTreeIdentity(
        REPO_ROOT / "src/emrys/analyses/paired_cmh_candidate_ranking",
        "0" * 64,
    )

    def loaded(
        distribution: str,
        implementation: str = "0" * 64,
    ) -> LoadedAnalysisModuleV1:
        return LoadedAnalysisModuleV1(
            descriptor,
            InstalledProviderV1(
                analysis_module_v1,
                "emrys.analyses.paired_cmh_candidate_ranking:analysis_module_v1",
                distribution,
                "1",
                replace(package, sha256=implementation),
            ),
        )

    monkeypatch.setattr(normalization, "load_analysis_module", lambda _name: loaded("A"))
    first = admit_project(project_path, fixture.profile()).select_analysis()
    monkeypatch.setattr(normalization, "load_analysis_module", lambda _name: loaded("B"))
    second = admit_project(project_path, fixture.profile()).select_analysis()

    assert calls == 2
    assert flat_revision.record["schema_version"] == "emrys.analysis-revision.v1"
    assert first.revision.record["schema_version"] == "emrys.analysis-revision.v2"
    assert first.revision == second.revision
    assert first.workflow_inputs["analysis"]["policy"] != second.workflow_inputs[
        "analysis"
    ]["policy"]
    policy = first.workflow_inputs["analysis"]["policy"]
    assert policy["implementation_sha256"] == "0" * 64
    monkeypatch.setattr(
        analysis_modules,
        "load_analysis_module",
        lambda _name: loaded("A"),
    )
    assert analysis_modules.readmit_analysis_module(policy).descriptor is descriptor
    monkeypatch.setattr(
        analysis_modules,
        "load_analysis_module",
        lambda _name: loaded("A", "1" * 64),
    )
    with pytest.raises(
        analysis_modules.AnalysisModuleLoadError,
        match="implementation differs",
    ):
        analysis_modules.readmit_analysis_module(policy)
    scientific_module = first.revision.record["identity"]["analysis_module"]
    assert set(scientific_module) == {
        "module_id",
        "interface_version",
        "module_version",
        "configuration",
    }
    assert scientific_module["configuration"]["rna_ref"] == "A"
    assert "target_change" not in scientific_module["configuration"]


def test_named_analysis_selection_is_closed_and_content_bound(tmp_path: Path) -> None:
    project_path = fixture.build(tmp_path / "project-root")
    definition = project_path.read_text(encoding="utf-8")
    second = definition.split("analyses:\n", 1)[1].replace(
        "  primary:\n", "  sensitivity:\n", 1
    ).replace("    min_sample_dp: 1\n", "    min_sample_dp: 2\n", 1)
    project_path.write_text(definition + second, encoding="utf-8")

    project = admit_project(project_path, fixture.profile())
    assert tuple(analysis.name for analysis in project.analyses) == (
        "primary",
        "sensitivity",
    )
    with pytest.raises(contracts.ContractValidationError, match="--analysis"):
        project.select_analysis()
    with pytest.raises(contracts.ContractValidationError, match="Unknown Analysis"):
        project.select_analysis("missing")
    primary = project.select_analysis("primary")
    sensitivity = project.select_analysis("sensitivity")
    assert primary.revision.canonical_bytes != sensitivity.revision.canonical_bytes

    primary.workflow_inputs["analysis"]["cohort_id"] = "mutated"
    primary.profile["profile_id"] = "mutated"
    assert project.select_analysis("primary").revision == primary.revision
    assert primary.workflow_inputs["analysis"]["cohort_id"].startswith("scope-cohort-")


def test_named_analysis_sample_selection_is_explicit_and_order_neutral(
    tmp_path: Path,
) -> None:
    project_path = fixture.build(tmp_path / "project-root", replicate_count=3)
    definition = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    primary = definition["analyses"]["primary"]
    definition["analyses"]["subset"] = {
        **primary,
        "sample_ids": ["PUM1_3", "EV_2", "PUM1_2", "EV_3"],
    }
    definition["analyses"]["explicit-all"] = {
        **primary,
        "sample_ids": ["PUM1_3", "EV_3", "PUM1_2", "EV_2", "PUM1_1", "EV_1"],
    }
    project_path.write_text(
        yaml.safe_dump(definition, sort_keys=False),
        encoding="utf-8",
    )

    project = admit_project(project_path, fixture.profile())
    full = project.select_analysis("primary")
    subset = project.select_analysis("subset")
    explicit_all = project.select_analysis("explicit-all")

    assert project.dataset_sample_count == 6
    assert [
        row["sample_id"] for row in subset.workflow_inputs["samples"]["rows"]
    ] == ["EV_2", "PUM1_2", "EV_3", "PUM1_3"]
    assert [
        row["sample_id"] for row in subset.revision.record["identity"]["samples"]
    ] == ["EV_2", "EV_3", "PUM1_2", "PUM1_3"]
    assert subset.revision != full.revision
    assert subset.selected_sample_manifest_bytes is not None
    assert explicit_all.revision == full.revision
    assert explicit_all.workflow_inputs == full.workflow_inputs
    assert explicit_all.selected_sample_manifest_bytes is None

    definition["analyses"]["subset"]["sample_ids"].reverse()
    project_path.write_text(
        yaml.safe_dump(definition, sort_keys=False),
        encoding="utf-8",
    )
    reordered = admit_project(project_path, fixture.profile()).select_analysis("subset")
    assert reordered.revision == subset.revision
    assert reordered.workflow_inputs == subset.workflow_inputs
    assert (
        reordered.selected_sample_manifest_bytes
        == subset.selected_sample_manifest_bytes
    )


def test_named_analysis_sample_selection_rejects_unknown_or_incomplete_cohorts(
    tmp_path: Path,
) -> None:
    project_path = fixture.build(tmp_path / "project-root", replicate_count=3)
    definition = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    primary = definition["analyses"]["primary"]
    definition["analyses"]["primary"] = {
        **primary,
        "sample_ids": ["EV_1", "PUM1_1", "EV_2", "missing"],
    }
    project_path.write_text(
        yaml.safe_dump(definition, sort_keys=False),
        encoding="utf-8",
    )
    with pytest.raises(contracts.ContractValidationError, match="unknown sample IDs"):
        admit_project(project_path, fixture.profile())

    definition["analyses"]["primary"]["sample_ids"] = [
        "EV_1",
        "PUM1_1",
        "EV_2",
    ]
    project_path.write_text(
        yaml.safe_dump(definition, sort_keys=False),
        encoding="utf-8",
    )
    with pytest.raises(
        contracts.ContractValidationError,
        match="exactly one control and treatment",
    ):
        admit_project(project_path, fixture.profile())


def test_regions_file_resolves_from_nested_partition_manifest(
    tmp_path: Path,
) -> None:
    request = fixture.build(tmp_path / "request-root")
    partition_root = request.parent / "manifests"
    partition_root.mkdir()
    partition_manifest = partition_root / "partitions.tsv"
    (request.parent / "partitions.tsv").rename(partition_manifest)
    partition_manifest.write_text(
        "partition_id\tselector_type\tselector_value\np1\tregions_file\ttarget.bed\n",
        encoding="utf-8",
    )
    selector = partition_root / "target.bed"
    selector.write_text("chrSynthetic\t0\t100\n", encoding="utf-8")
    request.write_text(
        request.read_text(encoding="utf-8").replace(
            "    partitions: partitions.tsv",
            "    partitions: manifests/partitions.tsv",
        ),
        encoding="utf-8",
    )

    row = admit_project(request, fixture.profile()).select_analysis().workflow_inputs[
        "partitions"
    ]["rows"][0]

    assert row["selector_value"] == str(selector)
    assert row["selector_file"] == {
        "path": str(selector),
        "size_bytes": selector.stat().st_size,
        "sha256": hashlib.sha256(selector.read_bytes()).hexdigest(),
    }


def test_bound_input_change_creates_a_new_analysis_revision(tmp_path: Path) -> None:
    request = fixture.build(tmp_path / "request-root")
    before = admit_project(request, fixture.profile())
    changed = request.parent / "reads" / "PUM1_2_R1.fastq"
    changed.write_text("@changed/1\nGGGG\n+\nIIII\n", encoding="utf-8")
    after = admit_project(request, fixture.profile())

    assert after.select_analysis().revision != before.select_analysis().revision


def test_large_input_identities_are_streamed_without_byte_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = fixture.build(tmp_path / "request-root")
    byte_capture = normalization._regular_file
    captured_labels: list[str] = []

    def reject_large_byte_capture(path: Path, label: str) -> tuple[Path, bytes]:
        captured_labels.append(label)
        assert "FASTQ" not in label
        assert label not in {"Reference FASTA", "Reference GTF"}
        assert "regions file" not in label
        return byte_capture(path, label)

    monkeypatch.setattr(normalization, "_regular_file", reject_large_byte_capture)

    normalized = admit_project(request, fixture.profile())

    assert captured_labels == [
        "Project definition",
        "Sample manifest",
        "Analysis primary partition manifest",
    ]
    source = normalized.select_analysis().workflow_inputs
    reference = source["reference"]
    for key in ("fasta", "gtf"):
        path = Path(reference[key]["path"])
        assert reference[key]["size_bytes"] == path.stat().st_size
        assert reference[key]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    for row in source["samples"]["rows"]:
        for key in ("r1_fastq", "r2_fastq"):
            path = Path(row[key]["path"])
            assert row[key]["size_bytes"] == path.stat().st_size
            assert row[key]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_mixed_fastq_compression_is_rejected_before_analysis_identity(
    tmp_path: Path,
) -> None:
    request = fixture.build(tmp_path / "request-root")
    manifest = request.parent / "samples.tsv"
    compressed = request.parent / "reads" / "EV_1_R1.fastq.gz"
    (request.parent / "reads" / "EV_1_R1.fastq").rename(compressed)
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "reads/EV_1_R1.fastq", "reads/EV_1_R1.fastq.gz"
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        contracts.ContractValidationError,
        match="EV_1 R1 and R2 FASTQs must use the same compression mode",
    ):
        admit_project(request, fixture.profile())


@pytest.mark.parametrize("replacement_kind", ("file", "symlink"))
def test_admission_rejects_deterministic_pathname_replacement_after_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    replacement_kind: str,
) -> None:
    request = fixture.build(tmp_path / "request-root")
    target = request.parent / "reads" / "EV_1_R1.fastq"
    held = target.with_name("held.fastq")
    replacement = target.with_name("replacement.fastq")
    replacement.write_text("@replacement/1\nGGGG\n+\nIIII\n", encoding="utf-8")
    real_open = normalization.os.open
    swapped = False

    def open_then_replace(path: str | bytes | os.PathLike[str], flags: int) -> int:
        nonlocal swapped
        descriptor = real_open(path, flags)
        if Path(path) == target and not swapped:
            swapped = True
            target.rename(held)
            if replacement_kind == "file":
                replacement.rename(target)
            else:
                target.symlink_to(held.name)
        return descriptor

    monkeypatch.setattr(normalization.os, "open", open_then_replace)

    with pytest.raises(contracts.ContractValidationError, match="pathname changed"):
        admit_project(request, fixture.profile())


@pytest.mark.parametrize("manifest_name", ("samples.tsv", "partitions.tsv"))
def test_manifest_parsing_uses_admitted_bytes_across_an_aba_path_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    manifest_name: str,
) -> None:
    request = fixture.build(tmp_path / "request-root")
    manifest = request.parent / manifest_name
    admitted_bytes = manifest.read_bytes()
    admitted_hash = hashlib.sha256(admitted_bytes).hexdigest()
    if manifest_name == "samples.tsv":
        lines = admitted_bytes.decode("utf-8").splitlines()
        replacement_bytes = (
            "\n".join((lines[0], lines[2], lines[1], *lines[3:])) + "\n"
        ).encode()
    else:
        replacement_bytes = admitted_bytes.replace(b"chrSynthetic", b"chrAltered")
    replacement = manifest.with_name(f"replacement-{manifest.name}")
    held_admitted = manifest.with_name(f"admitted-{manifest.name}")
    held_replacement = manifest.with_name(f"held-{manifest.name}")
    replacement.write_bytes(replacement_bytes)

    real_open = normalization.os.open
    real_stat = normalization.os.stat
    state = {"opens": 0, "path_checks": 0, "swapped": False}

    def aba_open(path: str | bytes | os.PathLike[str], flags: int) -> int:
        if Path(path) == manifest:
            state["opens"] += 1
            if state["opens"] == 2 and state["swapped"]:
                manifest.rename(held_replacement)
                held_admitted.rename(manifest)
        return real_open(path, flags)

    def stat_then_swap(
        path: str | bytes | os.PathLike[str],
        *,
        follow_symlinks: bool = True,
    ) -> os.stat_result:
        result = real_stat(path, follow_symlinks=follow_symlinks)
        if Path(path) == manifest:
            state["path_checks"] += 1
            if state["path_checks"] == 2 and not state["swapped"]:
                manifest.rename(held_admitted)
                replacement.rename(manifest)
                state["swapped"] = True
        return result

    monkeypatch.setattr(normalization.os, "open", aba_open)
    monkeypatch.setattr(normalization.os, "stat", stat_then_swap)

    normalized = admit_project(request, fixture.profile())

    assert state == {"opens": 1, "path_checks": 2, "swapped": True}
    source = normalized.select_analysis().workflow_inputs
    if manifest_name == "samples.tsv":
        assert [row["sample_id"] for row in source["samples"]["rows"]] == [
            "EV_1",
            "PUM1_1",
            "EV_2",
            "PUM1_2",
        ]
        assert source["samples"]["manifest"]["sha256"] == admitted_hash
    else:
        assert source["partitions"]["rows"][0]["selector_value"] == "chrSynthetic"
        assert source["partitions"]["manifest"]["sha256"] == admitted_hash


def test_absent_optional_background_normalizes_to_explicit_null(
    tmp_path: Path,
) -> None:
    request = fixture.build(tmp_path / "request-root")
    explicit = admit_project(request, fixture.profile())
    request.write_text(
        request.read_text(encoding="utf-8").replace(
            "    background_condition: null\n", ""
        ),
        encoding="utf-8",
    )
    omitted = admit_project(request, fixture.profile())

    assert omitted.select_analysis().revision == explicit.select_analysis().revision
    assert (
        omitted.select_analysis().workflow_inputs["analysis"]["policy"][
            "background_condition"
        ]
        is None
    )


def test_declared_background_requires_at_least_one_sample(tmp_path: Path) -> None:
    request = fixture.build(tmp_path / "request-root")
    request.write_text(
        request.read_text(encoding="utf-8").replace(
            "    background_condition: null",
            "    background_condition: no_dox",
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        contracts.ContractValidationError,
        match="policy conditions must exist",
    ):
        admit_project(request, fixture.profile())


@pytest.mark.parametrize(
    ("field", "accepted", "rejected"),
    [
        ("min_sample_dp", "1", "0"),
        ("common_or_threshold", "1.2", "1"),
        ("background_max_fraction", "0.01", "0"),
        ("background_max_fraction", "0.01", "1"),
    ],
)
def test_normalization_rejects_step09_threshold_boundaries(
    tmp_path: Path,
    field: str,
    accepted: str,
    rejected: str,
) -> None:
    request = fixture.build(tmp_path / "request-root")
    request.write_text(
        request.read_text(encoding="utf-8").replace(
            f"    {field}: {accepted}\n",
            f"    {field}: {rejected}\n",
        ),
        encoding="utf-8",
    )

    with pytest.raises(contracts.ContractValidationError, match=field):
        admit_project(request, fixture.profile())


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        (
            "schema_version: emrys.project.v1\nschema_version: emrys.project.v1\n",
            "Duplicate YAML mapping key",
        ),
        (
            "defaults: &defaults\n  id: synthetic_ref\nreference:\n  <<: *defaults\n",
            "merge keys are not allowed",
        ),
        ("schema_version: !custom emrys.project.v1\n", "could not determine"),
    ],
)
def test_yaml_extensions_are_rejected(
    tmp_path: Path,
    replacement: str,
    message: str,
) -> None:
    request = fixture.build(tmp_path / "request-root")
    request.write_text(replacement, encoding="utf-8")

    with pytest.raises(contracts.ContractValidationError, match=message):
        admit_project(request, fixture.profile())


@pytest.mark.parametrize(
    "unsafe",
    (
        "reads/*.fastq",
        "reads/[literal].fastq",
        "${READS}/R1.fastq",
        "{reads}/R1.fastq",
        "~/R1",
        "reads//EV_1_R1.fastq",
    ),
)
def test_literal_existing_unsafe_or_interpolated_paths_are_rejected_before_access(
    tmp_path: Path,
    unsafe: str,
) -> None:
    request = fixture.build(tmp_path / "request-root")
    literal = request.parent / unsafe
    literal.parent.mkdir(parents=True, exist_ok=True)
    if not literal.exists():
        literal.write_text("@literal/1\nACGT\n+\nIIII\n", encoding="utf-8")
    manifest = request.parent / "samples.tsv"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("reads/EV_1_R1.fastq", unsafe),
        encoding="utf-8",
    )

    expected = (
        "redundant path separators" if "//" in unsafe else "explicit normalized path"
    )
    with pytest.raises(contracts.ContractValidationError, match=expected):
        admit_project(request, fixture.profile())


def test_request_path_uses_the_same_lexical_policy_before_access(
    tmp_path: Path,
) -> None:
    request = fixture.build(tmp_path / "request-root")
    unsafe_request = f"{request.parent}//{request.name}"

    with pytest.raises(
        contracts.ContractValidationError,
        match="redundant path separators",
    ):
        admit_project(unsafe_request, fixture.profile())


def test_path_profile_is_parsed_from_strict_admitted_json_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = fixture.build(tmp_path / "request-root")
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(
        json.dumps(fixture.profile(), sort_keys=True),
        encoding="utf-8",
    )

    real_load = contracts.load_json_object

    def unexpected_profile_reopen(path: str | Path) -> dict[str, object]:
        if Path(path) == profile_path:
            raise AssertionError("profile pathname was reopened")
        return real_load(path)

    monkeypatch.setattr(
        contracts,
        "load_json_object",
        unexpected_profile_reopen,
    )

    normalized = admit_project(request, profile_path)

    assert len(normalized.select_analysis().profile["owner_tasks"]) == 6


def test_path_profile_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    request = fixture.build(tmp_path / "request-root")
    profile_path = tmp_path / "profile.json"
    profile_path.write_text('{"schema_version":"first","schema_version":"second"}')

    with pytest.raises(
        contracts.ContractValidationError,
        match="Duplicate JSON object key: schema_version",
    ):
        admit_project(request, profile_path)


def test_symlinked_fastq_is_rejected(tmp_path: Path) -> None:
    request = fixture.build(tmp_path / "request-root")
    source = request.parent / "reads" / "EV_1_R1.fastq"
    target = request.parent / "reads" / "foreign.fastq"
    source.rename(target)
    source.symlink_to(target.name)

    with pytest.raises(contracts.ContractValidationError, match="non-symlink"):
        admit_project(request, fixture.profile())


def test_incomplete_paired_strata_are_rejected(tmp_path: Path) -> None:
    request = fixture.build(tmp_path / "request-root")
    manifest = request.parent / "samples.tsv"
    lines = manifest.read_text(encoding="utf-8").splitlines()
    manifest.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    with pytest.raises(
        contracts.ContractValidationError,
        match="exactly one control and treatment",
    ):
        admit_project(request, fixture.profile())
