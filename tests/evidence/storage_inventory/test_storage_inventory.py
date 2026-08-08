import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    ROOT / "src" / "norad" / "evidence" / "storage_inventory" / "storage_inventory.py"
)
ROOT_HEADER = "storage_id\tpath\trequired\tpurpose\tquota_bytes_expected\tnotes\n"
POLICY_HEADER = "policy_id\tstorage_id\tartifact_class\taction\tretention_days\tapproval_status\tapproved_by\tapproved_at\tnotes\n"
SPEC = importlib.util.spec_from_file_location(
    "norad_storage_inventory_faults",
    SCRIPT,
)
assert SPEC and SPEC.loader
STORAGE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = STORAGE
SPEC.loader.exec_module(STORAGE)


def contracts(tmp_path: Path, *, approved: bool = True):
    storage = tmp_path / "storage"
    storage.mkdir(parents=True)
    (storage / "file").write_bytes(b"1234")
    link = storage / "link"
    link.symlink_to(storage / "file")
    roots = tmp_path / "roots.tsv"
    roots.write_text(
        ROOT_HEADER + f"project\t{storage}\ttrue\tdurable\t1000\tfixture\n"
    )
    policy = tmp_path / "policy.tsv"
    approval = (
        "approved\ttester\t2020-01-01T00:00:00Z" if approved else "pending\tNA\tNA"
    )
    policy.write_text(
        POLICY_HEADER
        + f"v1\tproject\tnative\tretain\tindefinite\t{approval}\tfixture\n"
    )
    return roots, policy, storage


def run(roots, policy, output, *extra):
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--roots",
            str(roots),
            "--retention-policy",
            str(policy),
            "--output-root",
            str(output),
            *extra,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def rows(path):
    with path.open() as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def publication_data(roots: Path, policy: Path) -> dict[str, bytes]:
    roots_data, parsed_roots = STORAGE.load_roots(roots)
    policy_data, parsed_policy = STORAGE.load_policy(
        policy,
        {root.storage_id for root in parsed_roots},
    )
    return STORAGE.outputs(
        roots_data,
        policy_data,
        parsed_roots,
        parsed_policy,
    )


def publication_paths(output: Path) -> dict[str, Path]:
    return {
        "inventory": output / "storage_inventory.tsv",
        "policy": output / "retention_policy.tsv",
        "summary": output / "storage_retention_summary.tsv",
    }


def test_dry_run_is_side_effect_free(tmp_path):
    roots, policy, _ = contracts(tmp_path)
    output = tmp_path / "missing"
    result = run(roots, policy, output)
    assert result.returncode == 0
    assert "no storage is altered" in result.stdout
    assert not output.exists()


def test_dry_run_execute_and_repeat_are_cwd_independent(tmp_path):
    roots, policy, storage = contracts(tmp_path)
    output = tmp_path / "out"
    invocation = tmp_path / "invocation"
    invocation.mkdir()
    command = [
        sys.executable,
        str(SCRIPT),
        "--roots",
        str(roots),
        "--retention-policy",
        str(policy),
        "--output-root",
        str(output),
    ]

    dry_run = subprocess.run(
        command,
        cwd=invocation,
        text=True,
        capture_output=True,
        check=False,
    )
    assert dry_run.returncode == 0, dry_run.stderr
    assert "Dry-run complete" in dry_run.stdout
    assert not output.exists()

    output.mkdir()
    first = subprocess.run(
        [*command, "--execute"],
        cwd=invocation,
        text=True,
        capture_output=True,
        check=False,
    )
    assert first.returncode == 0, first.stderr
    first_inventory = rows(output / "storage_inventory.tsv")[0]
    first_policy = (output / "retention_policy.tsv").read_bytes()
    first_summary = (output / "storage_retention_summary.tsv").read_bytes()

    repeated = subprocess.run(
        [*command, "--execute"],
        cwd=invocation,
        text=True,
        capture_output=True,
        check=False,
    )
    assert repeated.returncode == 0, repeated.stderr
    second_inventory = rows(output / "storage_inventory.tsv")[0]
    volatile_fields = {
        "filesystem_total_bytes",
        "filesystem_free_bytes",
        "filesystem_available_bytes",
    }
    assert {
        key: value
        for key, value in first_inventory.items()
        if key not in volatile_fields
    } == {
        key: value
        for key, value in second_inventory.items()
        if key not in volatile_fields
    }
    assert first.stdout == repeated.stdout
    assert first.stderr == repeated.stderr == ""
    assert first_policy == (output / "retention_policy.tsv").read_bytes()
    assert first_summary == (output / "storage_retention_summary.tsv").read_bytes()
    assert (storage / "file").read_bytes() == b"1234"
    assert (storage / "link").is_symlink()
    assert not any(invocation.iterdir())
    assert sorted(path.name for path in output.iterdir()) == [
        "retention_policy.tsv",
        "storage_inventory.tsv",
        "storage_retention_summary.tsv",
    ]


def test_execute_measures_without_following_symlinks(tmp_path):
    roots, policy, storage = contracts(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
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
    output = tmp_path / "out"
    output.mkdir()
    assert run(roots, policy, output, "--execute").returncode == 0
    summary = rows(output / "storage_retention_summary.tsv")[0]
    assert summary["missing_required_count"] == "1"
    assert summary["pending_policy_count"] == "1"
    assert summary["overall_status"] == "fail"


def test_invalid_policy_and_relative_root_fail(tmp_path):
    roots, policy, _ = contracts(tmp_path)
    roots.write_text(roots.read_text().replace(str(tmp_path / "storage"), "relative"))
    output = tmp_path / "out"
    output.mkdir()
    assert run(roots, policy, output, "--execute").returncode == 2
    roots, policy, _ = contracts(tmp_path / "second")
    policy.write_text(
        policy.read_text().replace("\tapproved\ttester\t", "\tapproved\tNA\t")
    )
    assert run(roots, policy, output, "--execute").returncode == 2


def test_foreign_lock_and_partial_prior_are_preserved(tmp_path):
    roots, policy, _ = contracts(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
    lock = output / ".storage-inventory-retention.lock"
    lock.write_text("foreign\n")
    result = run(roots, policy, output, "--execute")
    assert result.returncode == 2
    assert lock.read_text() == "foreign\n"
    lock.unlink()
    partial = output / "storage_inventory.tsv"
    partial.write_text("foreign\n")
    result = run(roots, policy, output, "--execute")
    assert result.returncode == 2
    assert partial.read_text() == "foreign\n"


def test_contract_mutation_after_measurement_fails_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    roots, policy, _ = contracts(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
    real_outputs = STORAGE.outputs

    def render_then_mutate(*args, **kwargs):
        generated = real_outputs(*args, **kwargs)
        # Change the exact input bytes after measurement so the publication
        # boundary must reject the stale generated transaction.
        roots.write_text(roots.read_text() + "\n")
        return generated

    monkeypatch.setattr(STORAGE, "outputs", render_then_mutate)
    status = STORAGE.main(
        [
            "--roots",
            str(roots),
            "--retention-policy",
            str(policy),
            "--output-root",
            str(output),
            "--execute",
        ]
    )

    assert status == 2
    assert not any(path.exists() for path in publication_paths(output).values())


def test_publication_failure_restores_complete_storage_predecessor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    roots, policy, _ = contracts(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
    generated = publication_data(roots, policy)
    STORAGE.publish(output, generated)
    finals = publication_paths(output)
    before = {key: path.read_bytes() for key, path in finals.items()}
    real_replace = STORAGE.os.replace
    failed = False

    def fail_second_publication(source, destination):
        nonlocal failed
        if (
            not failed
            and Path(destination) == finals["policy"]
            and Path(source).name.endswith(".tmp")
        ):
            failed = True
            raise OSError("injected storage publication failure")
        real_replace(source, destination)

    monkeypatch.setattr(STORAGE.os, "replace", fail_second_publication)
    with pytest.raises(OSError, match="storage publication"):
        STORAGE.publish(output, generated)

    assert failed
    assert {key: path.read_bytes() for key, path in finals.items()} == before
    assert not [child for child in output.iterdir() if child.name.startswith(".")]


def test_characterizes_storage_incomplete_rollback_gap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    roots, policy, _ = contracts(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
    generated = publication_data(roots, policy)
    STORAGE.publish(output, generated)
    finals = publication_paths(output)
    real_replace = STORAGE.os.replace
    publication_failed = False
    restoration_failed = False

    def fail_publication_and_restoration(source, destination):
        nonlocal publication_failed, restoration_failed
        source_path = Path(source)
        destination_path = Path(destination)
        if (
            not publication_failed
            and destination_path == finals["policy"]
            and source_path.name.endswith(".tmp")
        ):
            publication_failed = True
            raise OSError("injected storage publication failure")
        if (
            publication_failed
            and not restoration_failed
            and destination_path == finals["inventory"]
            and source_path.name.endswith(".previous")
        ):
            restoration_failed = True
            raise OSError("injected storage restoration failure")
        real_replace(source, destination)

    monkeypatch.setattr(
        STORAGE.os,
        "replace",
        fail_publication_and_restoration,
    )
    with pytest.raises(OSError, match="storage restoration"):
        STORAGE.publish(output, generated)

    assert publication_failed and restoration_failed
    assert len(list(output.glob(".*.previous"))) == 3
    # Known TG-02 gap: the incomplete three-file predecessor remains, but its
    # lock and any explicit recovery marker are removed.
    assert not (output / ".storage-inventory-retention.lock").exists()
    assert not list(output.glob("*.RECOVERY.txt"))
