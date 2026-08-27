from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from emrys.contracts.orchestration import api as contracts
from emrys.orchestration.local_pilot import normalization
from emrys.orchestration.local_pilot.normalization import normalize_request
from tests.orchestration.local_pilot import fixture

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_ROOT = REPO_ROOT / "configs"
LOCAL_PROFILE = REPO_ROOT / "workflow/contracts/local_cmh_v2.json"
LOCAL_PILOT_STARTERS = (
    "local_pilot_request.example.yaml",
    "local_pilot_resources.example.yaml",
    "local_pilot_samples.example.tsv",
    "local_pilot_partitions.example.tsv",
)


def test_local_pilot_starters_normalize_after_explicit_paths_are_populated(
    tmp_path: Path,
) -> None:
    starter_root = tmp_path / "local-pilot-inputs"
    starter_root.mkdir()
    for name in LOCAL_PILOT_STARTERS:
        shutil.copy2(CONFIG_ROOT / name, starter_root / name)

    placeholder_paths = (
        "inputs/reference/genome.fa",
        "inputs/reference/annotation.gtf",
        "inputs/reads/sample_001_R1.fastq.gz",
        "inputs/reads/sample_001_R2.fastq.gz",
        "inputs/reads/sample_002_R1.fastq.gz",
        "inputs/reads/sample_002_R2.fastq.gz",
        "inputs/reads/sample_003_R1.fastq.gz",
        "inputs/reads/sample_003_R2.fastq.gz",
        "inputs/reads/sample_004_R1.fastq.gz",
        "inputs/reads/sample_004_R2.fastq.gz",
    )
    assert all(not (CONFIG_ROOT / path).exists() for path in placeholder_paths)
    for relative_path in placeholder_paths:
        path = starter_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"placeholder for {relative_path}\n".encode())

    normalized = normalize_request(
        starter_root / "local_pilot_request.example.yaml",
        LOCAL_PROFILE,
    )

    assert (starter_root / "local_pilot_resources.example.yaml").is_file()

    assert normalized.request["sample_manifest"] == ("local_pilot_samples.example.tsv")
    assert normalized.request["partition_manifest"] == (
        "local_pilot_partitions.example.tsv"
    )
    assert normalized.profile["profile_id"] == "emrys.profile.local_cmh"
    assert normalized.profile["profile_version"] == "v2"
    source = normalized.projection_source
    assert [
        (row["sample_id"], row["condition"], row["replicate"])
        for row in source["samples"]["rows"]
    ] == [
        ("sample_001", "control", "pair_01"),
        ("sample_002", "treatment", "pair_01"),
        ("sample_003", "control", "pair_02"),
        ("sample_004", "treatment", "pair_02"),
    ]
    assert source["partitions"]["rows"] == [
        {
            "partition_id": "primary",
            "selector_type": "region",
            "selector_value": "chr1",
            "selector_file": None,
        }
    ]


def test_analysis_revision_is_deterministic_path_neutral_and_label_independent(
    tmp_path: Path,
) -> None:
    request = fixture.build(tmp_path / "request-root")
    first = normalize_request(request, fixture.profile())
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    previous = Path.cwd()
    try:
        os.chdir(elsewhere)
        second = normalize_request(request, fixture.profile())
    finally:
        os.chdir(previous)

    relocated = normalize_request(
        fixture.build(tmp_path / "relocated-request-root"),
        fixture.profile(),
    )
    assert first.analysis_revision.analysis_revision_id == (
        second.analysis_revision.analysis_revision_id
    )
    assert first.analysis_revision.canonical_bytes == (
        second.analysis_revision.canonical_bytes
    )
    assert first.analysis_revision.analysis_revision_id == (
        relocated.analysis_revision.analysis_revision_id
    )
    assert first.analysis_revision.canonical_bytes == (
        relocated.analysis_revision.canonical_bytes
    )
    assert first.projection_source_bytes != relocated.projection_source_bytes
    original_request_hash = first.request_sha256
    request.write_text(
        request.read_text(encoding="utf-8")
        .replace("label: first label\n", "label: reformatted label\n")
        .replace("schema_version:", "schema_version: "),
        encoding="utf-8",
    )
    relabeled = normalize_request(request, fixture.profile())
    assert relabeled.request_sha256 != original_request_hash
    assert relabeled.analysis_revision.analysis_revision_id == (
        first.analysis_revision.analysis_revision_id
    )
    assert relabeled.analysis_revision.canonical_bytes == (
        first.analysis_revision.canonical_bytes
    )
    assert relabeled.projection_source_bytes == first.projection_source_bytes
    assert "label" not in first.analysis_revision.canonical_bytes.decode("utf-8")
    contracts.validate_record("application-model", first.analysis_revision.record)

    historical, historical_bytes = first.historical_execution_v1()
    contracts.validate_record("execution", historical, profile=fixture.profile())
    assert historical_bytes == contracts.canonical_json_bytes(historical)
    assert historical["run_id"] == (f"run-{historical['identity_envelope_sha256']}")


def test_resource_config_does_not_change_analysis_revision(
    tmp_path: Path,
) -> None:
    request = fixture.build(tmp_path / "request-root")
    baseline = normalize_request(request, fixture.profile())
    resource_config = request.parent / "emrys.resources.yaml"
    resource_config.write_text(
        resource_config.read_text(encoding="utf-8")
        .replace("workflow_cores: 1\n", "workflow_cores: 4\n")
        .replace('  "00a": 1\n', '  "00a": 4\n')
        .replace('  "01": 1\n', '  "01": 4\n'),
        encoding="utf-8",
    )

    tuned = normalize_request(request, fixture.profile())

    assert tuned.request_sha256 == baseline.request_sha256
    assert tuned.analysis_revision.analysis_revision_id == (
        baseline.analysis_revision.analysis_revision_id
    )
    assert tuned.analysis_revision.canonical_bytes == (
        baseline.analysis_revision.canonical_bytes
    )
    assert tuned.projection_source_bytes == baseline.projection_source_bytes


def test_bound_input_change_creates_a_new_analysis_revision(tmp_path: Path) -> None:
    request = fixture.build(tmp_path / "request-root")
    before = normalize_request(request, fixture.profile())
    changed = request.parent / "reads" / "PUM1_2_R1.fastq"
    changed.write_text("@changed/1\nGGGG\n+\nIIII\n", encoding="utf-8")
    after = normalize_request(request, fixture.profile())

    assert after.analysis_revision.analysis_revision_id != (
        before.analysis_revision.analysis_revision_id
    )
    assert after.analysis_revision.canonical_bytes != (
        before.analysis_revision.canonical_bytes
    )


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

    normalized = normalize_request(request, fixture.profile())

    assert captured_labels == ["Request", "Sample manifest", "Partition manifest"]
    source = normalized.projection_source
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
        normalize_request(request, fixture.profile())


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

    expected = (
        "must not be a symlink" if replacement_kind == "symlink" else "pathname changed"
    )
    with pytest.raises(contracts.ContractValidationError, match=expected):
        normalize_request(request, fixture.profile())


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

    normalized = normalize_request(request, fixture.profile())

    assert state == {"opens": 1, "path_checks": 2, "swapped": True}
    source = normalized.projection_source
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
    explicit = normalize_request(request, fixture.profile())
    request.write_text(
        request.read_text(encoding="utf-8").replace(
            "  background_condition: null\n", ""
        ),
        encoding="utf-8",
    )
    omitted = normalize_request(request, fixture.profile())

    assert omitted.analysis_revision.analysis_revision_id == (
        explicit.analysis_revision.analysis_revision_id
    )
    assert (
        omitted.projection_source["analysis"]["policy"]["background_condition"] is None
    )


def test_declared_background_requires_at_least_one_sample(tmp_path: Path) -> None:
    request = fixture.build(tmp_path / "request-root")
    request.write_text(
        request.read_text(encoding="utf-8").replace(
            "  background_condition: null",
            "  background_condition: no_dox",
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        contracts.ContractValidationError,
        match="background_condition has no sample rows",
    ):
        normalize_request(request, fixture.profile())


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
            f"  {field}: {accepted}\n",
            f"  {field}: {rejected}\n",
        ),
        encoding="utf-8",
    )

    with pytest.raises(contracts.ContractValidationError, match=field):
        normalize_request(request, fixture.profile())


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        (
            "schema_version: emrys.request.v3\nschema_version: emrys.request.v3\n",
            "Duplicate YAML mapping key",
        ),
        (
            "defaults: &defaults\n  id: synthetic_ref\nreference:\n  <<: *defaults\n",
            "merge keys are not allowed",
        ),
        ("schema_version: !custom emrys.request.v3\n", "could not determine"),
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
        normalize_request(request, fixture.profile())


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
        normalize_request(request, fixture.profile())


def test_request_path_uses_the_same_lexical_policy_before_access(
    tmp_path: Path,
) -> None:
    request = fixture.build(tmp_path / "request-root")
    unsafe_request = f"{request.parent}//{request.name}"

    with pytest.raises(
        contracts.ContractValidationError,
        match="redundant path separators",
    ):
        normalize_request(unsafe_request, fixture.profile())


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

    normalized = normalize_request(request, profile_path)

    assert normalized.profile == fixture.profile()


def test_path_profile_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    request = fixture.build(tmp_path / "request-root")
    profile_path = tmp_path / "profile.json"
    profile_path.write_text('{"schema_version":"first","schema_version":"second"}')

    with pytest.raises(
        contracts.ContractValidationError,
        match="Duplicate JSON object key: schema_version",
    ):
        normalize_request(request, profile_path)


def test_symlinked_fastq_is_rejected(tmp_path: Path) -> None:
    request = fixture.build(tmp_path / "request-root")
    source = request.parent / "reads" / "EV_1_R1.fastq"
    target = request.parent / "reads" / "foreign.fastq"
    source.rename(target)
    source.symlink_to(target.name)

    with pytest.raises(
        contracts.ContractValidationError, match="must not be a symlink"
    ):
        normalize_request(request, fixture.profile())


def test_incomplete_paired_strata_are_rejected(tmp_path: Path) -> None:
    request = fixture.build(tmp_path / "request-root")
    manifest = request.parent / "samples.tsv"
    lines = manifest.read_text(encoding="utf-8").splitlines()
    manifest.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    with pytest.raises(
        contracts.ContractValidationError,
        match="exactly one control and one treatment",
    ):
        normalize_request(request, fixture.profile())
