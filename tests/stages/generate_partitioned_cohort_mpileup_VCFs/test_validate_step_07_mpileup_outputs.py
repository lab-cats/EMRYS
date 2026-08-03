import csv
import gzip
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[3]
ROSTER_ORACLE = ROOT / "tests" / "validation_roster_expectations.py"
ROSTER_SPEC = importlib.util.spec_from_file_location(
    "generate_partitioned_cohort_mpileup_vcfs_validation_roster_oracle",
    ROSTER_ORACLE,
)
assert ROSTER_SPEC is not None and ROSTER_SPEC.loader is not None
ROSTER_MODULE = importlib.util.module_from_spec(ROSTER_SPEC)
ROSTER_SPEC.loader.exec_module(ROSTER_MODULE)
assert_exact_check_roster = ROSTER_MODULE.assert_exact_check_roster
SCRIPT = (
    ROOT
    / "src"
    / "norad"
    / "stages"
    / "generate_partitioned_cohort_mpileup_VCFs"
    / "validate_step_07_mpileup_outputs.py"
)
TEST_MODULE_NAME = "_norad_test_validate_step_07_mpileup_outputs"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_receipt(
    samples: Path,
    partitions: Path,
    fwd: Path,
    rev: Path,
    receipt: Path,
    *,
    selector_type: str = "region",
    selector_value: str = "1:1-10",
    fwd_path: str | None = None,
    rev_path: str | None = None,
    fwd_count: int = 1,
    rev_count: int = 0,
) -> None:
    receipt.write_text(
        "cohort_id\tpartition_id\tselector_type\tselector_value\torientation\t"
        "vcf_path\tsample_manifest_sha256\tpartition_manifest_sha256\t"
        "sample_count\tvcf_record_count\n"
        f"cohort\tp1\t{selector_type}\t{selector_value}\tFWD_like\t"
        f"{fwd_path or fwd.resolve()}\t{sha256(samples)}\t{sha256(partitions)}\t"
        f"2\t{fwd_count}\n"
        f"cohort\tp1\t{selector_type}\t{selector_value}\tREV_like\t"
        f"{rev_path or rev.resolve()}\t{sha256(samples)}\t{sha256(partitions)}\t"
        f"2\t{rev_count}\n"
    )


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    samples = root / "samples.tsv"
    samples.write_text("sample_id\tcondition\nA\tx\nB\ty\n")
    partitions = root / "partitions.tsv"
    partitions.write_text("partition_id\tselector_type\tselector_value\np1\tregion\t1:1-10\n")
    fai = root / "ref.fa.fai"; fai.write_text("1\t100\t0\t80\t81\n")
    header = (
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\tB\n"
    )
    fwd = root / "cohort.p1.FWD_like.mpileup.vcf"
    rev = root / "cohort.p1.REV_like.mpileup.vcf"
    fwd.write_text(header + "1\t2\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\t0/0\n")
    rev.write_text(header)
    receipt = root / "cohort.p1.step07_outputs.tsv"
    write_receipt(samples, partitions, fwd, rev, receipt)
    out = root / "out"; out.mkdir()
    return samples, partitions, fai, fwd, rev, receipt, out / "cohort__p1.validation.tsv"


def arguments(values, *extra):
    samples, partitions, fai, fwd, rev, receipt, output = values
    return [
        "--cohort-id", "cohort", "--partition-id", "p1",
        "--sample-manifest", str(samples), "--partition-manifest", str(partitions),
        "--reference-fai", str(fai), "--fwd-vcf", str(fwd),
        "--rev-vcf", str(rev), "--receipt", str(receipt),
        "--output", str(output), *extra,
    ]


def run(values, *extra, cwd=ROOT):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments(values, *extra)],
        cwd=cwd, text=True, capture_output=True,
    )


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def load_validator() -> ModuleType:
    sys.modules.pop(TEST_MODULE_NAME, None)
    spec = importlib.util.spec_from_file_location(TEST_MODULE_NAME, SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not exact-load validator: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[TEST_MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(TEST_MODULE_NAME) is module:
            sys.modules.pop(TEST_MODULE_NAME, None)
        raise
    return module


def test_dry_run_is_side_effect_free(tmp_path):
    values = fixture(tmp_path)
    assert run(values).returncode == 0
    assert not values[-1].exists()


def test_execute_publishes_five_passes(tmp_path):
    values = fixture(tmp_path)
    result = run(values, "--execute")
    assert result.returncode == 0, result.stderr
    assert_exact_check_roster(rows(values[-1]), "07")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_arbitrary_cwd_dry_run_execute_and_repeat_are_byte_identical(tmp_path):
    values = fixture(tmp_path / "fixture")
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    input_paths = values[:-1]
    before = {
        path: (path.read_bytes(), path.stat().st_mode) for path in input_paths
    }

    dry = run(values, cwd=invocation_cwd)
    assert dry.returncode == 0, dry.stderr
    assert dry.stderr == ""
    assert dry.stdout.endswith("Dry-run complete; no output was written.\n")
    assert not values[-1].exists()

    first = run(values, "--execute", cwd=invocation_cwd)
    assert first.returncode == 0, first.stderr
    assert first.stderr == ""
    first_report = values[-1].read_bytes()
    assert dry.stdout.encode().startswith(first_report)
    assert_exact_check_roster(rows(values[-1]), "07")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}

    second = run(values, "--execute", cwd=invocation_cwd)
    assert second.returncode == 0, second.stderr
    assert second.stderr == ""
    assert second.stdout == first.stdout
    assert values[-1].read_bytes() == first_report
    assert {
        path: (path.read_bytes(), path.stat().st_mode) for path in input_paths
    } == before
    assert list(invocation_cwd.iterdir()) == []
    assert set(values[-1].parent.iterdir()) == {values[-1]}


@pytest.mark.parametrize(
    ("case", "failed_check"),
    [
        ("receipt_scope", "receipt_structure"),
        ("vcf_sample_order", "vcf_structure"),
        ("selector_disagreement", "selector_reconciliation"),
        ("manifest_hash", "manifest_identity_and_sample_order"),
        ("record_count", "vcf_record_counts"),
    ],
)
def test_each_semantic_check_can_publish_failed_evidence(
    tmp_path, case, failed_check
):
    values = fixture(tmp_path)
    if case == "receipt_scope":
        values[5].write_text(values[5].read_text().replace("cohort\tp1", "other\tp1"))
    elif case == "vcf_sample_order":
        values[3].write_text(
            values[3].read_text().replace("\tFORMAT\tA\tB\n", "\tFORMAT\tB\tA\n")
        )
    elif case == "selector_disagreement":
        values[5].write_text(values[5].read_text().replace("1:1-10", "1:1-11"))
    elif case == "manifest_hash":
        values[5].write_text(
            values[5].read_text().replace(sha256(values[0]), "0" * 64)
        )
    elif case == "record_count":
        values[5].write_text(
            values[5].read_text().replace("\t2\t1\n", "\t2\t9\n")
        )
    else:
        raise AssertionError(f"Unhandled semantic-failure case: {case}")

    result = run(values, "--execute")

    assert result.returncode == 0, result.stderr
    assert_exact_check_roster(rows(values[-1]), "07")
    by_check = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert by_check[failed_check] == "fail"


@pytest.mark.parametrize(
    "input_index",
    [0, 1, 2, 3, 4, 5],
    ids=[
        "sample_manifest",
        "partition_manifest",
        "reference_fai",
        "fwd_vcf",
        "rev_vcf",
        "receipt",
    ],
)
def test_post_build_input_mutation_preserves_valid_predecessor(
    tmp_path, monkeypatch, capsys, input_index
):
    values = fixture(tmp_path)
    initial = run(values, "--execute")
    assert initial.returncode == 0, initial.stderr
    predecessor = values[-1].read_bytes()
    input_paths = values[:-1]
    before = {path: path.read_bytes() for path in input_paths}
    target = input_paths[input_index]
    validator = load_validator()
    real_build = validator.build

    def mutate_after_build(args):
        built = real_build(args)
        target.write_bytes(before[target] + b"post-build mutation\n")
        return built

    monkeypatch.setattr(validator, "build", mutate_after_build)
    try:
        status = validator.main(arguments(values, "--execute"))
    finally:
        if sys.modules.get(TEST_MODULE_NAME) is validator:
            sys.modules.pop(TEST_MODULE_NAME, None)

    captured = capsys.readouterr()
    assert status == 2
    assert f"Input changed after validation: {target}" in captured.err
    assert values[-1].read_bytes() == predecessor
    assert target.read_bytes() == before[target] + b"post-build mutation\n"
    assert {
        path: path.read_bytes() for path in input_paths if path != target
    } == {
        path: data for path, data in before.items() if path != target
    }
    assert set(values[-1].parent.iterdir()) == {values[-1]}


def test_compressed_regions_file_is_exit_zero_failed_selector_evidence(tmp_path):
    values = fixture(tmp_path)
    compressed_regions = tmp_path / "regions.bed.gz"
    with gzip.open(compressed_regions, "wt") as stream:
        stream.write("1\t0\t10\n")
    values[1].write_text(
        "partition_id\tselector_type\tselector_value\n"
        "p1\tregions_file\tregions.bed.gz\n"
    )
    write_receipt(
        values[0], values[1], values[3], values[4], values[5],
        selector_type="regions_file", selector_value="regions.bed.gz",
    )

    result = run(values, "--execute")

    assert result.returncode == 0, result.stderr
    by_check = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert by_check["selector_reconciliation"] == "fail"


def test_out_of_bounds_bed_coordinates_are_a_current_false_pass(tmp_path):
    values = fixture(tmp_path)
    regions = tmp_path / "regions.bed"
    regions.write_text("1\t0\t1000\n")
    values[1].write_text(
        "partition_id\tselector_type\tselector_value\n"
        "p1\tregions_file\tregions.bed\n"
    )
    write_receipt(
        values[0], values[1], values[3], values[4], values[5],
        selector_type="regions_file", selector_value="regions.bed",
    )

    result = run(values, "--execute")

    assert result.returncode == 0, result.stderr
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_vcf_selector_ref_alt_and_format_semantics_are_current_false_passes(
    tmp_path,
):
    values = fixture(tmp_path)
    values[3].write_text(
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\tB\n"
        "1\t99\t.\tNOT_REF\t<UNCHECKED>\t.\tFAIL\tBROKEN=1\tUNCHECKED\tbad\tbad\n"
    )

    result = run(values, "--execute")

    assert result.returncode == 0, result.stderr
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_relative_receipt_vcf_paths_are_exit_zero_count_failure(tmp_path):
    values = fixture(tmp_path)
    write_receipt(
        values[0], values[1], values[3], values[4], values[5],
        fwd_path=values[3].name, rev_path=values[4].name,
    )

    result = run(values, "--execute")

    assert result.returncode == 0, result.stderr
    by_check = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert by_check["vcf_record_counts"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path):
    values = fixture(tmp_path)
    values[3].unlink()
    assert run(values, "--execute").returncode == 2
    values = fixture(tmp_path / "second")
    bad = (*values[:-1], values[-1].parent / "wrong.tsv")
    assert run(bad, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path):
    values = fixture(tmp_path)
    lock = values[-1].parent / f".{values[-1].name}.lock"
    lock.write_text("foreign\n")
    assert run(values, "--execute").returncode == 2
    assert lock.read_text() == "foreign\n"
