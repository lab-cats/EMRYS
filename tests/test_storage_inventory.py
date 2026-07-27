import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/storage_inventory.py"
ROOT_HEADER = "storage_id\tpath\trequired\tpurpose\tquota_bytes_expected\tnotes\n"
POLICY_HEADER = "policy_id\tstorage_id\tartifact_class\taction\tretention_days\tapproval_status\tapproved_by\tapproved_at\tnotes\n"


def contracts(tmp_path: Path, *, approved: bool = True):
    storage = tmp_path / "storage"; storage.mkdir(parents=True)
    (storage / "file").write_bytes(b"1234")
    link = storage / "link"; link.symlink_to(storage / "file")
    roots = tmp_path / "roots.tsv"
    roots.write_text(ROOT_HEADER + f"project\t{storage}\ttrue\tdurable\t1000\tfixture\n")
    policy = tmp_path / "policy.tsv"
    approval = "approved\ttester\t2020-01-01T00:00:00Z" if approved else "pending\tNA\tNA"
    policy.write_text(POLICY_HEADER + f"v1\tproject\tnative\tretain\tindefinite\t{approval}\tfixture\n")
    return roots, policy, storage


def run(roots, policy, output, *extra):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--roots", str(roots), "--retention-policy",
         str(policy), "--output-root", str(output), *extra],
        cwd=ROOT, text=True, capture_output=True,
    )


def rows(path):
    with path.open() as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def test_dry_run_is_side_effect_free(tmp_path):
    roots, policy, _ = contracts(tmp_path)
    output = tmp_path / "missing"
    result = run(roots, policy, output)
    assert result.returncode == 0
    assert "no storage is altered" in result.stdout
    assert not output.exists()


def test_execute_measures_without_following_symlinks(tmp_path):
    roots, policy, storage = contracts(tmp_path)
    output = tmp_path / "out"; output.mkdir()
    result = run(roots, policy, output, "--execute")
    assert result.returncode == 0, result.stderr
    inventory = rows(output / "storage_inventory.tsv")[0]
    summary = rows(output / "storage_retention_summary.tsv")[0]
    assert inventory["tree_bytes"] == "4"
    assert inventory["file_count"] == "1"
    assert inventory["symlink_count"] == "1"
    assert summary["overall_status"] == "pass"
    assert (storage / "file").read_bytes() == b"1234"
    first_policy = (output / "retention_policy.tsv").read_bytes()
    first_summary = (output / "storage_retention_summary.tsv").read_bytes()
    assert run(roots, policy, output, "--execute").returncode == 0
    assert first_policy == (output / "retention_policy.tsv").read_bytes()
    assert first_summary == (output / "storage_retention_summary.tsv").read_bytes()


def test_pending_policy_and_missing_required_are_reported(tmp_path):
    roots, policy, _ = contracts(tmp_path, approved=False)
    text = roots.read_text()
    roots.write_text(text.replace(str(tmp_path / "storage"), str(tmp_path / "missing")))
    output = tmp_path / "out"; output.mkdir()
    assert run(roots, policy, output, "--execute").returncode == 0
    summary = rows(output / "storage_retention_summary.tsv")[0]
    assert summary["missing_required_count"] == "1"
    assert summary["pending_policy_count"] == "1"
    assert summary["overall_status"] == "fail"


def test_invalid_policy_and_relative_root_fail(tmp_path):
    roots, policy, _ = contracts(tmp_path)
    roots.write_text(roots.read_text().replace(str(tmp_path / "storage"), "relative"))
    output = tmp_path / "out"; output.mkdir()
    assert run(roots, policy, output, "--execute").returncode == 2
    roots, policy, _ = contracts(tmp_path / "second")
    policy.write_text(policy.read_text().replace("\tapproved\ttester\t", "\tapproved\tNA\t"))
    assert run(roots, policy, output, "--execute").returncode == 2


def test_foreign_lock_and_partial_prior_are_preserved(tmp_path):
    roots, policy, _ = contracts(tmp_path)
    output = tmp_path / "out"; output.mkdir()
    lock = output / ".storage-inventory-retention.lock"; lock.write_text("foreign\n")
    result = run(roots, policy, output, "--execute")
    assert result.returncode == 2
    assert lock.read_text() == "foreign\n"
    lock.unlink()
    partial = output / "storage_inventory.tsv"; partial.write_text("foreign\n")
    result = run(roots, policy, output, "--execute")
    assert result.returncode == 2
    assert partial.read_text() == "foreign\n"
