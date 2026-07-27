import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_step_09_cmh_outputs.py"
FIXTURE_PATH = ROOT / "tests/fixtures/step09c/build_fixture.py"
spec = importlib.util.spec_from_file_location("step09_validator_fixture", FIXTURE_PATH)
assert spec is not None and spec.loader is not None
FIXTURE = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = FIXTURE
spec.loader.exec_module(FIXTURE)


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


def run(values, *extra):
    (
        samples, partitions, sites, inputs, all_sites, significant, summary,
        mutation, mutation_pdf, depth_pdf, output,
    ) = values
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--analysis-id", FIXTURE.PRIMARY_ANALYSIS_ID,
         "--cohort-id", FIXTURE.COHORT_ID,
         "--sample-manifest", str(samples), "--partition-manifest", str(partitions),
         "--step08-sites", str(sites), "--step08-inputs", str(inputs),
         "--all-sites", str(all_sites), "--significant-sites", str(significant),
         "--summary", str(summary), "--mutation-spectrum", str(mutation),
         "--mutation-spectrum-pdf", str(mutation_pdf),
         "--depth-delta-pdf", str(depth_pdf), "--output", str(output), *extra],
        cwd=ROOT, text=True, capture_output=True,
    )


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def test_dry_run_is_side_effect_free(tmp_path):
    values = fixture(tmp_path)
    assert run(values).returncode == 0
    assert not values[-1].exists()


def test_execute_publishes_seven_passes(tmp_path):
    values = fixture(tmp_path)
    result = run(values, "--execute")
    assert result.returncode == 0, result.stderr
    assert len(rows(values[-1])) == 7
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

    assert (
        run(values, "--cohort-id", "wrong_cohort", "--execute").returncode
        == 0
    )
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
