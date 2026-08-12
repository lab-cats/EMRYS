from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from norad.contracts.orchestration import api as contracts
from norad.orchestration.local_pilot import normalization
from norad.orchestration.local_pilot.normalization import normalize_request
from tests.orchestration.local_pilot import fixture


def test_normalization_is_deterministic_and_independent_of_cwd_and_label(
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

    assert first.run_id == second.run_id
    assert first.normalized_bytes == second.normalized_bytes
    original_request_hash = first.request_sha256
    request.write_text(
        request.read_text(encoding="utf-8")
        .replace("label: first label\n", "label: reformatted label\n")
        .replace("schema_version:", "schema_version: "),
        encoding="utf-8",
    )
    relabeled = normalize_request(request, fixture.profile())
    assert relabeled.request_sha256 != original_request_hash
    assert relabeled.run_id == first.run_id
    assert relabeled.normalized_bytes == first.normalized_bytes
    assert "label" not in first.normalized_bytes.decode("utf-8")
    contracts.validate_record(
        "execution", first.execution_contract, profile=fixture.profile()
    )


def test_bound_input_change_creates_a_new_run(tmp_path: Path) -> None:
    request = fixture.build(tmp_path / "request-root")
    before = normalize_request(request, fixture.profile())
    changed = request.parent / "reads" / "PUM1_2_R1.fastq"
    changed.write_text("@changed/1\nGGGG\n+\nIIII\n", encoding="utf-8")
    after = normalize_request(request, fixture.profile())

    assert after.run_id != before.run_id
    assert after.normalized_bytes != before.normalized_bytes


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
    if manifest_name == "samples.tsv":
        assert [
            row["sample_id"] for row in normalized.execution_contract["samples"]["rows"]
        ] == [
            "EV_1",
            "PUM1_1",
            "EV_2",
            "PUM1_2",
        ]
        assert (
            normalized.execution_contract["samples"]["manifest"]["sha256"]
            == admitted_hash
        )
    else:
        assert (
            normalized.execution_contract["partitions"]["rows"][0]["selector_value"]
            == "chrSynthetic"
        )
        assert (
            normalized.execution_contract["partitions"]["manifest"]["sha256"]
            == admitted_hash
        )


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

    assert omitted.run_id == explicit.run_id
    assert (
        omitted.execution_contract["analysis"]["policy"]["background_condition"] is None
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
            "schema_version: norad.request.v1\nschema_version: norad.request.v1\n",
            "Duplicate YAML mapping key",
        ),
        (
            "defaults: &defaults\n  id: synthetic_ref\nreference:\n  <<: *defaults\n",
            "merge keys are not allowed",
        ),
        ("schema_version: !custom norad.request.v1\n", "could not determine"),
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
