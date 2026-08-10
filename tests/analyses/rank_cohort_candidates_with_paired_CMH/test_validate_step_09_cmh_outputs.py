import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from tests.stage_validator_test_support import load_roster_oracle

ROOT = Path(__file__).resolve().parents[3]
assert_exact_check_roster = load_roster_oracle(ROOT).assert_exact_check_roster

SCRIPT = (
    ROOT
    / "src/norad/analyses/rank_cohort_candidates_with_paired_CMH"
    / "validate_step_09_cmh_outputs.py"
)
STEP09_PATH = ROOT / "src/norad/contracts/scientific_evidence/step09.py"
STEP08_PATH = ROOT / "src/norad/contracts/scientific_evidence" / "step08.py"
FIXTURE_PATH = (
    ROOT
    / "tests/evidence/assemble_scientific_review_evidence_package"
    / "build_fixture.py"
)
FIXTURE_MODULE_NAME = "_norad_test_step09c_fixture_for_step09_validator"
FIXTURE_SPEC = importlib.util.spec_from_file_location(FIXTURE_MODULE_NAME, FIXTURE_PATH)
assert FIXTURE_SPEC is not None and FIXTURE_SPEC.loader is not None
FIXTURE = importlib.util.module_from_spec(FIXTURE_SPEC)
sys.modules[FIXTURE_MODULE_NAME] = FIXTURE
try:
    FIXTURE_SPEC.loader.exec_module(FIXTURE)
except BaseException:
    if sys.modules.get(FIXTURE_MODULE_NAME) is FIXTURE:
        sys.modules.pop(FIXTURE_MODULE_NAME, None)
    raise


def fixture(root: Path):
    built = FIXTURE.build_fixture(root)
    analysis = built.step09_analysis_dir
    analysis_id = FIXTURE.PRIMARY_ANALYSIS_ID
    out = root / "validation"
    out.mkdir()
    return (
        built.sample_manifest,
        built.partition_manifest,
        built.step08_sites,
        built.step08_inputs,
        analysis / f"{analysis_id}.cmh_all_sites.tsv",
        analysis / f"{analysis_id}.cmh_significant_sites.tsv",
        analysis / f"{analysis_id}.cmh_summary.tsv",
        analysis / f"{analysis_id}.mutation_spectrum.tsv",
        analysis / f"{analysis_id}.mutation_spectrum.pdf",
        analysis / f"{analysis_id}.depth_delta.pdf",
        out / f"{analysis_id}.validation.tsv",
    )


def arguments(values, *extra):
    (
        samples,
        partitions,
        sites,
        inputs,
        all_sites,
        significant,
        summary,
        mutation,
        mutation_pdf,
        depth_pdf,
        output,
    ) = values
    return [
        "--analysis-id",
        FIXTURE.PRIMARY_ANALYSIS_ID,
        "--cohort-id",
        FIXTURE.COHORT_ID,
        "--sample-manifest",
        str(samples),
        "--partition-manifest",
        str(partitions),
        "--step08-sites",
        str(sites),
        "--step08-inputs",
        str(inputs),
        "--all-sites",
        str(all_sites),
        "--significant-sites",
        str(significant),
        "--summary",
        str(summary),
        "--mutation-spectrum",
        str(mutation),
        "--mutation-spectrum-pdf",
        str(mutation_pdf),
        "--depth-delta-pdf",
        str(depth_pdf),
        "--output",
        str(output),
        *extra,
    ]


def run(values, *extra, cwd=ROOT):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments(values, *extra)],
        cwd=cwd,
        text=True,
        capture_output=True,
    )


def load_validator():
    module_name = "_test_step09_cmh_outputs_validator"
    validator_spec = importlib.util.spec_from_file_location(module_name, SCRIPT)
    assert validator_spec is not None and validator_spec.loader is not None
    validator = importlib.util.module_from_spec(validator_spec)
    validator_spec.loader.exec_module(validator)
    return validator


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def test_arbitrary_cwd_dry_execute_repeat_byte_parity_has_no_residue(tmp_path):
    values = fixture(tmp_path / "fixture")
    invocation_cwd = tmp_path / "arbitrary-cwd"
    invocation_cwd.mkdir()
    input_paths = values[:-1]
    before = {path: (path.read_bytes(), path.stat().st_mode) for path in input_paths}

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
    assert first.stdout.encode().startswith(first_report)

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


def test_dry_run_is_side_effect_free(tmp_path):
    values = fixture(tmp_path)
    assert run(values).returncode == 0
    assert not values[-1].exists()


def test_execute_publishes_seven_passes(tmp_path):
    values = fixture(tmp_path)
    result = run(values, "--execute")
    assert result.returncode == 0, result.stderr
    assert_exact_check_roster(rows(values[-1]), "09")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_summary_disagreement_is_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    summary = values[6]
    lines = summary.read_text().splitlines()
    header = lines[0].split("\t")
    data = lines[1].split("\t")
    data[header.index("candidate_count")] = "999"
    summary.write_text("\t".join(header) + "\n" + "\t".join(data) + "\n")
    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["summary_count_reconciliation"] == "fail"


def test_candidate_reordering_is_failed_upstream_evidence(tmp_path):
    values = fixture(tmp_path)
    all_sites = values[4]
    lines = all_sites.read_text(encoding="utf-8").splitlines()
    lines[-2], lines[-1] = lines[-1], lines[-2]
    all_sites.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["upstream_identity_and_candidate_order"] == "fail"


def test_wrong_cohort_is_failed_identity_evidence(tmp_path):
    values = fixture(tmp_path)

    assert run(values, "--cohort-id", "wrong_cohort", "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["upstream_identity_and_candidate_order"] == "fail"


def test_nonprovisional_orientation_policy_is_failed_identity_evidence(
    tmp_path,
):
    values = fixture(tmp_path)
    inputs = values[3]
    inputs.write_text(
        inputs.read_text(encoding="utf-8").replace(
            "legacy_provisional_v1", "unsupported_policy"
        ),
        encoding="utf-8",
    )

    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["upstream_identity_and_candidate_order"] == "fail"


def test_incorrect_bh_adjustment_is_failed_semantic_evidence(tmp_path):
    values = fixture(tmp_path)
    all_sites = values[4]
    lines = all_sites.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    data = lines[1].split("\t")
    data[header.index("cmh_fdr_bh")] = "0.002"
    lines[1] = "\t".join(data)
    all_sites.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["status_semantics"] == "fail"


def test_fabricated_cmh_statistics_pvalues_bh_and_odds_ratios_all_pass(
    tmp_path,
):
    values = fixture(tmp_path)
    fabricated = {
        "FWD_like|1|10|T>C": {
            "cmh_statistic": "999999",
            "cmh_p_value": "0.013",
            "cmh_fdr_bh": "0.013",
            "common_odds_ratio": "999",
        },
        "REV_like|1|20|A>G": {
            "cmh_statistic": "0.000001",
            "cmh_p_value": "0.013",
            "cmh_fdr_bh": "0.013",
            "common_odds_ratio": "0.001",
        },
        "REV_like|2|60|A>G": {
            "cmh_statistic": "123456",
            "cmh_p_value": "0.013",
            "cmh_fdr_bh": "0.013",
            "common_odds_ratio": "1.1",
        },
    }
    for path in values[4:6]:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            fieldnames = reader.fieldnames
            table = list(reader)
        assert fieldnames is not None
        for row in table:
            row.update(fabricated.get(row["candidate_id"], {}))
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=fieldnames,
                delimiter="\t",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(table)

    result = run(values, "--execute")
    assert result.returncode == 0, result.stderr
    report_rows = rows(values[-1])
    assert_exact_check_roster(report_rows, "09")
    by_check = {row["check_id"]: row for row in report_rows}
    status_row = by_check["status_semantics"]
    assert status_row["status"] == "pass", status_row
    assert {row["status"] for row in report_rows} == {"pass"}, by_check
    assert status_row["expected"] == (
        "recomputed target/test/call, depth, AF, background, CMH, and BH"
    )


@pytest.mark.parametrize(
    "input_index",
    range(10),
    ids=(
        "sample_manifest",
        "partition_manifest",
        "step08_sites",
        "step08_inputs",
        "all_sites",
        "significant_sites",
        "summary",
        "mutation_spectrum",
        "mutation_spectrum_pdf",
        "depth_delta_pdf",
    ),
)
def test_post_build_mutation_of_each_input_preserves_predecessor_report(
    tmp_path,
    monkeypatch,
    capsys,
    input_index,
):
    values = fixture(tmp_path)
    baseline = run(values, "--execute")
    assert baseline.returncode == 0, baseline.stderr
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
    status = validator.main(arguments(values, "--execute"))

    captured = capsys.readouterr()
    assert status == 2
    assert f"Input changed after validation: {target}" in captured.err
    assert values[-1].read_bytes() == predecessor
    assert target.read_bytes() == before[target] + b"post-build mutation\n"
    assert {path: path.read_bytes() for path in input_paths if path != target} == {
        path: data for path, data in before.items() if path != target
    }
    assert set(values[-1].parent.iterdir()) == {values[-1]}


def test_significant_subset_disagreement_is_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    significant = values[5]
    lines = significant.read_text(encoding="utf-8").splitlines()
    significant.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["significant_subset"] == "fail"


def test_mutation_spectrum_disagreement_is_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    mutation = values[7]
    lines = mutation.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    data = lines[1].split("\t")
    data[header.index("candidate_count")] = "999"
    lines[1] = "\t".join(data)
    mutation.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["mutation_spectrum_reconciliation"] == "fail"


def test_truncated_pdf_is_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    values[8].write_bytes(b"%PDF-1.4\ntruncated\n")

    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["pdf_structure"] == "fail"


def test_analysis_bound_filename_mismatch_is_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    wrong_name = values[4].with_name("wrong.cmh_all_sites.tsv")
    values[4].rename(wrong_name)
    mismatched = (*values[:4], wrong_name, *values[5:])

    assert run(mismatched, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["output_transaction"] == "fail"


def test_cross_directory_member_is_failed_transaction_evidence(tmp_path):
    values = fixture(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    moved = other / values[9].name
    values[9].rename(moved)
    cross_directory = (*values[:9], moved, values[10])

    assert run(cross_directory, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["output_transaction"] == "fail"


def test_hardlinked_pdf_members_are_failed_transaction_evidence(tmp_path):
    values = fixture(tmp_path)
    values[9].unlink()
    values[9].hardlink_to(values[8])

    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["output_transaction"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path):
    values = fixture(tmp_path)
    values[4].unlink()
    assert run(values, "--execute").returncode == 2
    values = fixture(tmp_path / "second")
    bad = (*values[:-1], values[-1].parent / "wrong.tsv")
    assert run(bad, "--execute").returncode == 2


def test_symlinked_input_fails_closed(tmp_path):
    values = fixture(tmp_path)
    target = values[8].with_name("real.pdf")
    values[8].rename(target)
    values[8].symlink_to(target)

    assert run(values, "--execute").returncode == 2
    assert not values[-1].exists()


def test_foreign_lock_is_preserved(tmp_path):
    values = fixture(tmp_path)
    lock = values[-1].parent / f".{values[-1].name}.lock"
    lock.write_text("foreign\n")
    assert run(values, "--execute").returncode == 2
    assert lock.read_text() == "foreign\n"
