"""Independent API and behavior tests for the neutral Step 08 contract."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import inspect
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

import pytest


ROOT = Path(__file__).resolve().parents[3]
OWNER = ROOT / "src/norad/contracts/scientific_evidence/step08.py"
MODULE_NAME = "_norad_step08_scientific_evidence_contract"
READY_ATTRIBUTE = "_NORAD_STEP08_CONTRACT_READY"


def load_contract():
    cached = sys.modules.get(MODULE_NAME)
    if cached is not None:
        assert Path(cached.__file__).resolve() == OWNER.resolve()
        assert getattr(cached, READY_ATTRIBUTE) is True
        return cached
    spec = importlib.util.spec_from_file_location(MODULE_NAME, OWNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
        setattr(module, READY_ATTRIBUTE, True)
    except BaseException:
        if sys.modules.get(MODULE_NAME) is module:
            del sys.modules[MODULE_NAME]
        raise
    return module


STEP08 = load_contract()


def write_tsv(path: Path, header, rows) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def read_tsv(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.reader(stream, delimiter="\t"))


def replace_cell(path: Path, data_row: int, column: str, value: str) -> None:
    rows = read_tsv(path)
    rows[data_row + 1][rows[0].index(column)] = value
    write_tsv(path, rows[0], rows[1:])


def clone(path: Path, root: Path, name: str) -> Path:
    target = root / name
    shutil.copyfile(path, target)
    return target


def build_valid(root: Path) -> SimpleNamespace:
    root.mkdir(parents=True, exist_ok=True)
    sample_manifest = root / "samples.tsv"
    write_tsv(
        sample_manifest,
        STEP08.SAMPLE_MANIFEST_REQUIRED,
        (("S", "/r1", "/r2", "reverse", "control", "1"),),
    )
    partition_manifest = root / "partitions.tsv"
    write_tsv(
        partition_manifest,
        STEP08.PARTITION_MANIFEST_HEADER,
        (("p1", "region", "1"),),
    )
    sample_hash = hashlib.sha256(sample_manifest.read_bytes()).hexdigest()
    partition_hash = hashlib.sha256(partition_manifest.read_bytes()).hexdigest()
    step08_inputs = root / "cohort.step08_inputs.tsv"
    input_rows = []
    for orientation in STEP08.ORIENTATIONS:
        input_rows.append(
            (
                "cohort",
                "p1",
                "region",
                "1",
                orientation,
                f"/step07/{orientation}.tsv",
                "a" * 64,
                f"/vcf/{orientation}.vcf",
                "b" * 64,
                sample_hash,
                partition_hash,
                "/reference/annotation.gtf",
                "c" * 64,
                "1",
                "1",
                "1",
                "1",
                "1",
                "0",
                "0",
                "1",
                "legacy_provisional_v1",
            )
        )
    write_tsv(step08_inputs, STEP08.STEP08_INPUTS_HEADER, input_rows)
    step08_sites = root / "cohort.step08_sites.tsv"
    sites_header = STEP08.STEP08_METADATA_HEADER + (
        "DP__S",
        "AD__S",
        "AF__S",
    )
    metadata = (
        "p1",
        "candidate",
        "FWD_like",
        "1",
        "2",
        "1",
        "A",
        "G",
        "A",
        "G",
        "+",
        "gene",
        "transcript",
        "TRUE",
        "FALSE",
        "FALSE",
        "TRUE",
        "FALSE",
        "60",
        "PASS",
        "2",
        "legacy_provisional_v1",
    )
    reverse_metadata = list(metadata)
    reverse_metadata[1] = "candidate/with:arbitrary+characters"
    reverse_metadata[2] = "REV_like"
    reverse_metadata[4] = "0"
    write_tsv(
        step08_sites,
        sites_header,
        (
            metadata + ("10", "2", "0.2"),
            tuple(reverse_metadata) + ("8", "1", "0.125"),
        ),
    )
    step08_summary = root / "cohort.step08_summary.tsv"
    write_tsv(
        step08_summary,
        STEP08.STEP08_SUMMARY_HEADER,
        (
            (
                "cohort",
                "1",
                "1",
                "2",
                "1",
                "2",
                "2",
                "2",
                "0",
                "0",
                "2",
                sample_hash,
                partition_hash,
                "/reference/annotation.gtf",
                "c" * 64,
                "legacy_provisional_v1",
            ),
        ),
    )
    return SimpleNamespace(
        sample_manifest=sample_manifest,
        partition_manifest=partition_manifest,
        sample_hash=sample_hash,
        partition_hash=partition_hash,
        inputs=step08_inputs,
        sites=step08_sites,
        summary=step08_summary,
    )


def validated(fixture: SimpleNamespace):
    sample_table, sample_ids, sample_rows = STEP08.validate_sample_manifest(
        fixture.sample_manifest
    )
    partitions = STEP08.validate_partition_manifest(fixture.partition_manifest)
    inputs = STEP08.validate_step08_inputs(
        fixture.inputs,
        sample_ids,
        partitions.rows,
        fixture.sample_hash,
        fixture.partition_hash,
    )
    sites = STEP08.validate_step08_sites(
        fixture.sites, sample_ids, partitions.rows, inputs.rows
    )
    summary = STEP08.validate_step08_summary(
        fixture.summary,
        sample_ids,
        partitions.rows,
        inputs.rows,
        sites.rows,
        fixture.sample_hash,
        fixture.partition_hash,
    )
    return sample_table, sample_ids, sample_rows, partitions, inputs, sites, summary


def public_fingerprint(module) -> bytes:
    constants = [
        "NA_VALUE",
        "ORIENTATIONS",
        "SAMPLE_MANIFEST_REQUIRED",
        "SAMPLE_MANIFEST_ALLOWED",
        "PARTITION_MANIFEST_HEADER",
        "STEP08_METADATA_HEADER",
        "STEP08_INPUTS_HEADER",
        "STEP08_SUMMARY_HEADER",
    ]
    functions = [
        "validate_safe_id",
        "sha256_file",
        "validate_sample_manifest",
        "validate_partition_manifest",
        "validate_step08_inputs",
        "validate_step08_sites",
        "validate_step08_summary",
    ]
    document = {
        "constants": {name: getattr(module, name) for name in constants},
        "functions": {
            name: str(inspect.signature(getattr(module, name)))
            for name in functions
        },
        "table_fields": list(module.Table.__dataclass_fields__),
        "error_base": [value.__name__ for value in module.ContractError.__mro__],
    }
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()


def test_public_api_fingerprint_matches_pre_extraction_oracle() -> None:
    payload = public_fingerprint(STEP08)

    assert len(payload) == 3316
    assert hashlib.sha256(payload).hexdigest() == (
        "8824d7b30f3c45dddcb475d21d4382ac"
        "52de2520031cdd89bab107fb2edc2bf1"
    )
    assert STEP08.ContractError.__mro__[:2] == (
        STEP08.ContractError,
        RuntimeError,
    )
    assert tuple(STEP08.Table.__dataclass_fields__) == ("header", "rows", "path")


def test_valid_contract_preserves_exact_results_and_characterized_permissiveness(
    tmp_path: Path,
) -> None:
    fixture = build_valid(tmp_path)
    sample_table, sample_ids, sample_rows, partitions, inputs, sites, summary = (
        validated(fixture)
    )

    assert type(sample_table) is STEP08.Table
    assert sample_rows is sample_table.rows
    assert sample_ids == ["S"]
    assert sample_table.path == fixture.sample_manifest.resolve()
    assert partitions.header == STEP08.PARTITION_MANIFEST_HEADER
    assert inputs.header == STEP08.STEP08_INPUTS_HEADER
    assert sites.rows[1]["candidate_id"] == "candidate/with:arbitrary+characters"
    assert sites.rows[1]["position"] == "0"
    assert summary.rows[0]["published_candidate_count"] == "2"
    assert STEP08.sha256_file(fixture.sample_manifest) == fixture.sample_hash

    rows = read_tsv(fixture.sites)
    write_tsv(fixture.sites, rows[0], tuple(reversed(rows[1:])))
    reordered = STEP08.validate_step08_sites(
        fixture.sites, sample_ids, partitions.rows, inputs.rows
    )
    assert [row["orientation"] for row in reordered.rows] == [
        "REV_like",
        "FWD_like",
    ]

    replace_cell(fixture.sites, 0, "DP__S", "NA")
    replace_cell(fixture.sites, 0, "AD__S", "NA")
    replace_cell(fixture.sites, 0, "AF__S", "NA")
    assert STEP08.validate_step08_sites(
        fixture.sites, sample_ids, partitions.rows, inputs.rows
    ).rows[0]["DP__S"] == "NA"


def test_optional_manifest_and_allowed_vocabularies(tmp_path: Path) -> None:
    fixture = build_valid(tmp_path)
    write_tsv(
        fixture.sample_manifest,
        STEP08.SAMPLE_MANIFEST_ALLOWED,
        (("S", "/r1", "/r2", "forward", "control", "1", "note"),),
    )
    assert STEP08.validate_sample_manifest(fixture.sample_manifest)[1] == ["S"]
    for strandedness in ("forward", "reverse", "unstranded", "unknown"):
        replace_cell(fixture.sample_manifest, 0, "strandedness", strandedness)
        STEP08.validate_sample_manifest(fixture.sample_manifest)
    replace_cell(fixture.partition_manifest, 0, "selector_type", "regions_file")
    STEP08.validate_partition_manifest(fixture.partition_manifest)


def test_private_parsing_closure_preserves_exact_edges(tmp_path: Path) -> None:
    fixture = build_valid(tmp_path)
    assert STEP08.parse_nonnegative_int("count", "0") == 0
    assert STEP08.parse_number("value", "NA", allow_na=True) is None
    assert STEP08.parse_number("value", "1.5", nonnegative=True) == 1.5
    assert STEP08.values_close(None, None)
    assert not STEP08.values_close(None, 0.0)
    assert STEP08.values_close(1.0, 1.0 + 1e-9)
    STEP08.validate_safe_id("sample_id", "safe.ID-1")
    STEP08.validate_hash("hash", "a" * 64)
    STEP08.require_text("text", "NA", allow_na=True)
    assert STEP08.require_file("sample", fixture.sample_manifest) == (
        fixture.sample_manifest.resolve()
    )

    failures: list[tuple[Callable[[], object], str]] = [
        (
            lambda: STEP08.validate_safe_id("sample_id", "unsafe/id"),
            "sample_id must match [A-Za-z0-9][A-Za-z0-9._-]*; got: unsafe/id",
        ),
        (
            lambda: STEP08.validate_enum("orientation", "SIDE", STEP08.ORIENTATIONS),
            "orientation must be one of FWD_like, REV_like; got: SIDE",
        ),
        (
            lambda: STEP08.parse_nonnegative_int("count", "01"),
            "count must be a non-negative integer; got: 01",
        ),
        (
            lambda: STEP08.parse_number("value", "x"),
            "value must be numeric; got: x",
        ),
        (
            lambda: STEP08.parse_number("value", "inf"),
            "value must be finite; got: inf",
        ),
        (
            lambda: STEP08.parse_number("value", "-1", nonnegative=True),
            "value must be non-negative; got: -1",
        ),
        (
            lambda: STEP08.validate_hash("hash", "A" * 64),
            f"hash must be a lowercase SHA-256 value; got: {'A' * 64}",
        ),
        (
            lambda: STEP08.require_text("text", " surrounded "),
            "text must be non-empty and have no surrounding whitespace.",
        ),
        (
            lambda: STEP08.require_file("missing", tmp_path / "missing"),
            f"missing does not exist or is not a regular file: {tmp_path / 'missing'}",
        ),
    ]
    for call, expected in failures:
        with pytest.raises(STEP08.ContractError) as caught:
            call()
        assert str(caught.value) == expected

    empty = tmp_path / "empty.tsv"
    empty.touch()
    with pytest.raises(STEP08.ContractError, match="empty"):
        STEP08.require_file("empty", empty)
    with pytest.raises(STEP08.ContractError, match="Could not hash"):
        STEP08.sha256_file(tmp_path / "missing-hash")


@pytest.mark.parametrize(
    ("case", "expected"),
    (
        (
            "sample_bad_header",
            "Sample manifest must have the exact Step 09 schema, with optional notes as the final column.",
        ),
        ("sample_empty", "Sample manifest contains no sample rows."),
        ("sample_duplicate", "Sample manifest contains duplicate sample_id: S"),
        ("sample_unsafe_id", "sample_id must match"),
        (
            "sample_bad_strandedness",
            "Sample manifest row 2 has invalid strandedness: diagonal",
        ),
        ("partition_empty", "Partition manifest contains no partition rows."),
        (
            "partition_bad_selector",
            "Partition manifest row 2 selector_type must be one of region, regions_file; got: all",
        ),
        (
            "inputs_incomplete",
            "Step 08 input receipt is not the complete declared partition x orientation set.",
        ),
        (
            "inputs_reordered",
            "Step 08 input receipt is not ordered as the declared partition x {FWD_like, REV_like} universe.",
        ),
        ("inputs_stale_sample", "Step 08 input receipt sample manifest hash is stale."),
        (
            "inputs_stale_partition",
            "Step 08 input receipt partition manifest hash is stale.",
        ),
        ("inputs_bad_count", "must be a non-negative integer; got: 01"),
        (
            "inputs_sample_count",
            "Step 08 input receipt sample_count differs from the manifest.",
        ),
        (
            "inputs_record_counts",
            "Step 08 declared and observed VCF record counts differ.",
        ),
        (
            "inputs_alt_arithmetic",
            "Step 08 alternate-allele counts do not reconcile.",
        ),
        (
            "inputs_publish_arithmetic",
            "Step 08 published and supported SNV counts do not reconcile.",
        ),
        ("inputs_multi_cohort", "Step 08 input receipt contains multiple cohort IDs."),
        (
            "inputs_annotation",
            "Step 08 input receipt contains inconsistent annotation provenance.",
        ),
        ("inputs_policy", "Step 08 input receipt contains multiple orientation policies."),
        ("sites_unknown_partition", "references an unknown partition"),
        ("sites_bad_orientation", "orientation must be one of FWD_like, REV_like"),
        (
            "sites_policy",
            "Step 08 sites table orientation policy differs from its receipt.",
        ),
        ("sites_bad_position", "must be a non-negative integer; got: -1"),
        ("sites_alt_zero", "Step 08 alt_index must be at least 1."),
        ("sites_one_sided", "has one-sided DP/AD missingness"),
        ("sites_af_without_counts", "has AF without DP/AD"),
        ("sites_ad_over_dp", "has inconsistent counts"),
        ("sites_zero_depth", "has invalid zero-depth counts"),
        ("sites_af_ratio", "AF__S does not equal AD/DP."),
        (
            "sites_scope_counts",
            "Step 08 sites counts do not reconcile by partition and orientation.",
        ),
        ("summary_row_count", "Step 08 summary must contain exactly one data row."),
        ("summary_stale_sample", "Step 08 summary sample manifest hash is stale."),
        (
            "summary_stale_partition",
            "Step 08 summary partition manifest hash is stale.",
        ),
        (
            "summary_count",
            "Step 08 summary published_candidate_count does not reconcile.",
        ),
        (
            "summary_provenance",
            "Step 08 summary orientation_policy differs from the input receipt.",
        ),
    ),
)
def test_exact_rejection_contract(case: str, expected: str, tmp_path: Path) -> None:
    fixture = build_valid(tmp_path / "valid")
    sample = STEP08.validate_sample_manifest(fixture.sample_manifest)
    partitions = STEP08.validate_partition_manifest(fixture.partition_manifest)
    inputs = STEP08.validate_step08_inputs(
        fixture.inputs,
        sample[1],
        partitions.rows,
        fixture.sample_hash,
        fixture.partition_hash,
    )
    sites = STEP08.validate_step08_sites(
        fixture.sites, sample[1], partitions.rows, inputs.rows
    )
    target = None
    call: Callable[[], object]

    if case.startswith("sample_"):
        target = clone(fixture.sample_manifest, tmp_path, f"{case}.tsv")
        if case == "sample_bad_header":
            rows = read_tsv(target)
            write_tsv(
                target,
                tuple(rows[0]) + ("extra",),
                (tuple(row) + ("value",) for row in rows[1:]),
            )
        elif case == "sample_empty":
            write_tsv(target, STEP08.SAMPLE_MANIFEST_REQUIRED, ())
        elif case == "sample_duplicate":
            rows = read_tsv(target)
            write_tsv(target, rows[0], (rows[1], rows[1]))
        elif case == "sample_unsafe_id":
            replace_cell(target, 0, "sample_id", "unsafe/id")
        else:
            replace_cell(target, 0, "strandedness", "diagonal")
        call = lambda: STEP08.validate_sample_manifest(target)
    elif case.startswith("partition_"):
        target = clone(fixture.partition_manifest, tmp_path, f"{case}.tsv")
        if case == "partition_empty":
            write_tsv(target, STEP08.PARTITION_MANIFEST_HEADER, ())
        else:
            replace_cell(target, 0, "selector_type", "all")
        call = lambda: STEP08.validate_partition_manifest(target)
    elif case.startswith("inputs_"):
        target = clone(fixture.inputs, tmp_path, f"{case}.tsv")
        if case == "inputs_incomplete":
            rows = read_tsv(target)
            write_tsv(target, rows[0], rows[1:2])
        elif case == "inputs_reordered":
            rows = read_tsv(target)
            write_tsv(target, rows[0], tuple(reversed(rows[1:])))
        elif case == "inputs_stale_sample":
            replace_cell(target, 0, "sample_manifest_sha256", "d" * 64)
        elif case == "inputs_stale_partition":
            replace_cell(target, 0, "partition_manifest_sha256", "d" * 64)
        elif case == "inputs_bad_count":
            replace_cell(target, 0, "sample_count", "01")
        elif case == "inputs_sample_count":
            replace_cell(target, 0, "sample_count", "2")
        elif case == "inputs_record_counts":
            replace_cell(target, 0, "declared_vcf_record_count", "2")
        elif case == "inputs_alt_arithmetic":
            replace_cell(target, 0, "observed_alt_allele_count", "2")
        elif case == "inputs_publish_arithmetic":
            replace_cell(target, 0, "published_candidate_count", "0")
        elif case == "inputs_multi_cohort":
            replace_cell(target, 1, "cohort_id", "other")
        elif case == "inputs_annotation":
            replace_cell(target, 1, "annotation_gtf_sha256", "d" * 64)
        else:
            replace_cell(target, 1, "orientation_policy", "other_policy")
        call = lambda: STEP08.validate_step08_inputs(
            target,
            sample[1],
            partitions.rows,
            fixture.sample_hash,
            fixture.partition_hash,
        )
    elif case.startswith("sites_"):
        target = clone(fixture.sites, tmp_path, f"{case}.tsv")
        if case == "sites_unknown_partition":
            replace_cell(target, 0, "partition_id", "missing")
        elif case == "sites_bad_orientation":
            replace_cell(target, 0, "orientation", "SIDE")
        elif case == "sites_policy":
            replace_cell(target, 0, "orientation_policy", "other")
        elif case == "sites_bad_position":
            replace_cell(target, 0, "position", "-1")
        elif case == "sites_alt_zero":
            replace_cell(target, 0, "alt_index", "0")
        elif case == "sites_one_sided":
            replace_cell(target, 0, "DP__S", "NA")
        elif case == "sites_af_without_counts":
            replace_cell(target, 0, "DP__S", "NA")
            replace_cell(target, 0, "AD__S", "NA")
        elif case == "sites_ad_over_dp":
            replace_cell(target, 0, "AD__S", "11")
        elif case == "sites_zero_depth":
            replace_cell(target, 0, "DP__S", "0")
            replace_cell(target, 0, "AD__S", "0")
            replace_cell(target, 0, "AF__S", "0")
        elif case == "sites_af_ratio":
            replace_cell(target, 0, "AF__S", "0.3")
        else:
            rows = read_tsv(target)
            write_tsv(target, rows[0], rows[1:2])
        call = lambda: STEP08.validate_step08_sites(
            target, sample[1], partitions.rows, inputs.rows
        )
    else:
        target = clone(fixture.summary, tmp_path, f"{case}.tsv")
        if case == "summary_row_count":
            rows = read_tsv(target)
            write_tsv(target, rows[0], (rows[1], rows[1]))
        elif case == "summary_stale_sample":
            replace_cell(target, 0, "sample_manifest_sha256", "d" * 64)
        elif case == "summary_stale_partition":
            replace_cell(target, 0, "partition_manifest_sha256", "d" * 64)
        elif case == "summary_count":
            replace_cell(target, 0, "published_candidate_count", "3")
        else:
            replace_cell(target, 0, "orientation_policy", "other")
        call = lambda: STEP08.validate_step08_summary(
            target,
            sample[1],
            partitions.rows,
            inputs.rows,
            sites.rows,
            fixture.sample_hash,
            fixture.partition_hash,
        )

    with pytest.raises(STEP08.ContractError) as caught:
        call()
    assert expected in str(caught.value)


def test_tsv_shape_and_uniqueness_failures_are_exact(tmp_path: Path) -> None:
    empty_header = tmp_path / "empty-header.tsv"
    write_tsv(empty_header, ("", "value"), (("x", "y"),))
    duplicate_header = tmp_path / "duplicate-header.tsv"
    write_tsv(duplicate_header, ("value", "value"), (("x", "y"),))
    short_row = tmp_path / "short-row.tsv"
    write_tsv(short_row, ("left", "right"), (("x",),))
    bad_header = tmp_path / "bad-header.tsv"
    write_tsv(bad_header, ("observed",), (("x",),))

    for path, expected_header, expected in (
        (empty_header, None, "contains an empty header field"),
        (duplicate_header, None, "contains duplicate header fields"),
        (short_row, None, "row 2 has 1 fields; expected 2"),
        (bad_header, ("expected",), "header is invalid"),
    ):
        with pytest.raises(STEP08.ContractError, match=expected):
            STEP08.read_tsv("Table", path, expected_header)

    with pytest.raises(STEP08.ContractError, match="empty sample_id"):
        STEP08.ensure_unique(({"sample_id": ""},), "sample_id", "Rows")
    with pytest.raises(STEP08.ContractError, match="duplicate sample_id"):
        STEP08.ensure_unique(
            ({"sample_id": "S"}, {"sample_id": "S"}),
            "sample_id",
            "Rows",
        )
