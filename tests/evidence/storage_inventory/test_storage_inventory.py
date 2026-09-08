import argparse
import csv
import hashlib
import json
import subprocess
import sys
from collections.abc import Sequence
from functools import partial
from pathlib import Path
from types import SimpleNamespace

import pytest

import emrys.evidence.storage_inventory._storage_contract as contract
import emrys.evidence.storage_inventory._storage_measurement as measurement
import emrys.evidence.storage_inventory._storage_publication as publication
from emrys import __main__ as emrys_main
from emrys.evidence.storage_inventory import qualification

ROOT = Path(__file__).resolve().parents[3]
COMMAND = (sys.executable, "-I", "-m", "emrys", "debug", "storage-inventory")
ROOT_HEADER = "storage_id\tpath\trequired\tpurpose\tquota_bytes_expected\tnotes\n"
POLICY_HEADER = "policy_id\tstorage_id\tartifact_class\taction\tretention_days\tapproval_status\tapproved_by\tapproved_at\tnotes\n"


def contracts(tmp_path: Path, *, approved: bool = True) -> tuple[Path, Path, Path]:
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


def run_cli(
    roots: Path,
    policy: Path,
    output: Path,
    *extra: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            *COMMAND,
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
        check=False,
    )


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def publication_data(roots: Path, policy: Path) -> dict[str, bytes]:
    roots_data, parsed_roots = contract.load_roots(roots)
    policy_data, parsed_policy = contract.load_policy(
        policy,
        {root.storage_id for root in parsed_roots},
    )
    return measurement.outputs(roots_data, policy_data, parsed_roots, parsed_policy)


def publication_paths(output: Path) -> dict[str, Path]:
    return {
        "inventory": output / "storage_inventory.tsv",
        "policy": output / "retention_policy.tsv",
        "summary": output / "storage_retention_summary.tsv",
    }


def synthetic_mount_identity(path: Path) -> dict[str, str]:
    return {
        "mount_point": path.anchor,
        "filesystem_type": "synthetic-test-filesystem",
        "filesystem_source": "synthetic-test-device",
    }


def test_dry_run_is_side_effect_free(tmp_path: Path) -> None:
    roots, policy, _ = contracts(tmp_path)
    output = tmp_path / "missing"
    result = run_cli(roots, policy, output)
    assert result.returncode == 0
    assert "no storage is altered" in result.stdout
    assert not output.exists()


def test_dry_run_execute_and_repeat_are_cwd_independent(tmp_path: Path) -> None:
    roots, policy, storage = contracts(tmp_path)
    output = tmp_path / "out"
    invocation = tmp_path / "invocation"
    invocation.mkdir()
    command = [
        *COMMAND,
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
    first_inventory = read_rows(output / "storage_inventory.tsv")[0]
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
    second_inventory = read_rows(output / "storage_inventory.tsv")[0]
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


def test_execute_measures_without_following_symlinks(tmp_path: Path) -> None:
    roots, policy, storage = contracts(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
    result = run_cli(roots, policy, output, "--execute")
    assert result.returncode == 0, result.stderr
    inventory = read_rows(output / "storage_inventory.tsv")[0]
    summary = read_rows(output / "storage_retention_summary.tsv")[0]
    assert inventory["tree_bytes"] == "4"
    assert inventory["file_count"] == "1"
    assert inventory["symlink_count"] == "1"
    assert summary["overall_status"] == "pass"
    assert (storage / "file").read_bytes() == b"1234"
    first_policy = (output / "retention_policy.tsv").read_bytes()
    first_summary = (output / "storage_retention_summary.tsv").read_bytes()
    assert run_cli(roots, policy, output, "--execute").returncode == 0
    assert first_policy == (output / "retention_policy.tsv").read_bytes()
    assert first_summary == (output / "storage_retention_summary.tsv").read_bytes()


@pytest.mark.parametrize(
    ("outcome", "required", "status", "detail"),
    (
        ("available", "true", "available", "fixture"),
        ("missing_required", "true", "missing_required", "root missing"),
        ("missing_optional", "false", "missing_optional", "root missing"),
        ("invalid_file", "true", "invalid", "root is not a real directory"),
        ("invalid_symlink", "true", "invalid", "root is not a real directory"),
        ("walk_error", "true", "measurement_error", "walk failed"),
        ("file_error", "true", "measurement_error", "file inspection failed"),
        ("capacity_error", "true", "measurement_error", "capacity failed"),
    ),
)
def test_storage_measurement_preserves_complete_rows_and_io_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    outcome: str,
    required: str,
    status: str,
    detail: str,
) -> None:
    roots_path, policy_path, storage = contracts(tmp_path)
    storage = storage.resolve()
    declared = f"{storage}/."
    roots_path.write_text(
        ROOT_HEADER + f"project\t{declared}\t{required}\tdurable\t1000\tfixture\n"
    )
    roots_data, roots = contract.load_roots(roots_path)
    policy_data, policies = contract.load_policy(policy_path, {"project"})
    before_walk = outcome.startswith(("missing_", "invalid_"))
    nested = storage / "nested"
    linked_directory = storage / "linked_directory"
    child = nested / "child"
    if before_walk:
        (storage / "link").unlink()
        (storage / "file").unlink()
        storage.rmdir()
        if outcome == "invalid_file":
            storage.write_bytes(b"not a directory")
        elif outcome == "invalid_symlink":
            target = tmp_path / "elsewhere"
            target.mkdir()
            storage.symlink_to(target, target_is_directory=True)
    else:
        nested.mkdir()
        child.write_bytes(b"abcdef")
        linked_directory.symlink_to(nested, target_is_directory=True)

    calls: list[tuple[str, Path]] = []
    real_lstat = Path.lstat
    real_is_symlink = Path.is_symlink
    inside_is_symlink = False

    def observed_lstat(path: Path):
        if not inside_is_symlink:
            calls.append(("lstat", path))
        if path == storage and outcome.startswith("missing_"):
            raise FileNotFoundError("root\tmissing\n\x00")
        if path == child and outcome == "file_error":
            raise OSError("file inspection failed")
        return real_lstat(path)

    def observed_is_symlink(path: Path):
        nonlocal inside_is_symlink
        calls.append(("is_symlink", path))
        inside_is_symlink = True
        try:
            return real_is_symlink(path)
        finally:
            inside_is_symlink = False

    def observed_walk(path: Path, *, followlinks: bool):
        assert followlinks is False
        calls.append(("walk", path))
        directories = ["nested", "linked_directory"]
        yield str(storage), directories, ["file", "link"]
        assert directories == ["nested"]
        if outcome == "walk_error":
            raise OSError("walk failed")
        yield str(nested), [], ["child"]

    def observed_capacity(path: Path):
        calls.append(("statvfs", path))
        if outcome == "capacity_error":
            raise OSError("capacity failed")
        return SimpleNamespace(f_blocks=1000, f_bfree=300, f_bavail=200, f_frsize=4)

    monkeypatch.setattr(Path, "lstat", observed_lstat)
    monkeypatch.setattr(Path, "is_symlink", observed_is_symlink)
    monkeypatch.setattr(measurement.os, "walk", observed_walk)
    monkeypatch.setattr(measurement.os, "statvfs", observed_capacity)
    generated = measurement.outputs(roots_data, policy_data, roots, policies)

    metrics = (
        ["10", "2", "2", "2", "4000", "1200", "800"]
        if outcome == "available"
        else ["NA", "NA", "NA", "NA", "NA", "NA", "NA"]
    )
    assert list(csv.reader(generated["inventory"].decode().splitlines(), delimiter="\t")) == [
        [
            "storage_id", "declared_path", "resolved_path", "required", "purpose",
            "status", "tree_bytes", "file_count", "directory_count", "symlink_count",
            "filesystem_total_bytes", "filesystem_free_bytes",
            "filesystem_available_bytes", "quota_bytes_expected", "detail",
        ],
        [
            "project", declared, str(storage), required, "durable", status,
            *metrics, "1000", detail,
        ],
    ]
    expected_calls = [("lstat", storage)]
    if not before_walk:
        expected_calls.extend(
            [
                ("walk", storage),
                ("is_symlink", nested),
                ("is_symlink", linked_directory),
                ("lstat", storage / "file"),
                ("lstat", storage / "link"),
            ]
        )
        if outcome != "walk_error":
            expected_calls.append(("lstat", child))
            if outcome != "file_error":
                expected_calls.append(("statvfs", storage))
    assert calls == expected_calls


def test_storage_capacity_attribute_errors_escape_measurement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    roots, policy, _storage = contracts(tmp_path)

    class UnreadableCapacity:
        @property
        def f_blocks(self):
            raise OSError("capacity attribute failed")

    monkeypatch.setattr(measurement.os, "statvfs", lambda _path: UnreadableCapacity())
    with pytest.raises(OSError, match="capacity attribute failed"):
        publication_data(roots, policy)


def test_pending_policy_and_missing_required_are_reported(tmp_path: Path) -> None:
    roots, policy, _ = contracts(tmp_path, approved=False)
    text = roots.read_text()
    roots.write_text(text.replace(str(tmp_path / "storage"), str(tmp_path / "missing")))
    output = tmp_path / "out"
    output.mkdir()
    assert run_cli(roots, policy, output, "--execute").returncode == 0
    summary = read_rows(output / "storage_retention_summary.tsv")[0]
    assert summary["missing_required_count"] == "1"
    assert summary["pending_policy_count"] == "1"
    assert summary["overall_status"] == "fail"


def test_invalid_policy_and_relative_root_fail(tmp_path: Path) -> None:
    roots, policy, _ = contracts(tmp_path)
    roots.write_text(roots.read_text().replace(str(tmp_path / "storage"), "relative"))
    output = tmp_path / "out"
    output.mkdir()
    assert run_cli(roots, policy, output, "--execute").returncode == 2
    roots, policy, _ = contracts(tmp_path / "second")
    policy.write_text(
        policy.read_text().replace("\tapproved\ttester\t", "\tapproved\tNA\t")
    )
    assert run_cli(roots, policy, output, "--execute").returncode == 2


def test_foreign_lock_and_partial_prior_are_preserved(tmp_path: Path) -> None:
    roots, policy, _ = contracts(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
    lock = output / ".storage-inventory-retention.lock"
    lock.write_text("foreign\n")
    result = run_cli(roots, policy, output, "--execute")
    assert result.returncode == 2
    assert lock.read_text() == "foreign\n"
    lock.unlink()
    partial = output / "storage_inventory.tsv"
    partial.write_text("foreign\n")
    result = run_cli(roots, policy, output, "--execute")
    assert result.returncode == 2
    assert partial.read_text() == "foreign\n"


def test_contract_mutation_after_measurement_fails_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    roots, policy, _ = contracts(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
    real_outputs = measurement.outputs

    def render_then_mutate(
        roots_data: bytes,
        policy_data: bytes,
        parsed_roots: Sequence[contract.Root],
        parsed_policies: Sequence[contract.Policy],
    ) -> dict[str, bytes]:
        generated = real_outputs(roots_data, policy_data, parsed_roots, parsed_policies)
        roots.write_text(roots.read_text() + "\n")
        return generated

    monkeypatch.setattr(measurement, "outputs", render_then_mutate)
    status = emrys_main.main(
        [
            "debug",
            "storage-inventory",
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
    publication.publish(output, generated)
    finals = publication_paths(output)
    before = {key: path.read_bytes() for key, path in finals.items()}
    real_replace = publication.os.replace
    failed = False

    def fail_second_publication(source: Path, destination: Path) -> None:
        nonlocal failed
        if (
            not failed
            and Path(destination) == finals["policy"]
            and Path(source).name.endswith(".tmp")
        ):
            failed = True
            raise OSError("injected storage publication failure")
        real_replace(source, destination)

    monkeypatch.setattr(publication.os, "replace", fail_second_publication)
    with pytest.raises(OSError, match="storage publication"):
        publication.publish(output, generated)

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
    publication.publish(output, generated)
    finals = publication_paths(output)
    real_replace = publication.os.replace
    publication_failed = False
    restoration_failed = False

    def fail_publication_and_restoration(source: Path, destination: Path) -> None:
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

    monkeypatch.setattr(publication.os, "replace", fail_publication_and_restoration)
    with pytest.raises(OSError, match="storage restoration"):
        publication.publish(output, generated)

    assert publication_failed and restoration_failed
    assert len(list(output.glob(".*.previous"))) == 3
    # Known TG-02 gap: the incomplete three-file predecessor remains, but its
    # lock and any explicit recovery marker are removed.
    assert not (output / ".storage-inventory-retention.lock").exists()
    assert not list(output.glob("*.RECOVERY.txt"))


def test_linux_mount_identity_selects_deepest_mount_and_decodes_escapes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mountinfo = (
        "24 1 8:1 / / rw,relatime - ext4 /dev/root rw\n"
        "25 24 0:42 / /mnt/research\\040project rw - nfs4 server:/research rw\n"
        "26 25 0:43 / /mnt/research\\040project/run rw - lustre "
        "server:/run\\040source\\134volume rw\n"
    )

    def read_mountinfo(path: Path, *, encoding: str | None = None) -> str:
        assert path == Path("/proc/self/mountinfo")
        assert encoding == "utf-8"
        return mountinfo

    monkeypatch.setattr(Path, "read_text", read_mountinfo)

    assert qualification._mount_identity(Path("/mnt/research project/run/output")) == {
        "mount_point": "/mnt/research project/run",
        "filesystem_type": "lustre",
        "filesystem_source": "server:/run source\\volume",
    }


def _qualification_snapshot() -> dict[str, object]:
    return {
        "path": "/shared/workspace",
        "device_id": 101,
        "inode": 202,
        "uid": 303,
        "gid": 404,
        "filesystem_total_bytes": 1000,
        "filesystem_free_bytes": 500,
        "filesystem_available_bytes": 400,
        "mount_point": "/shared",
        "filesystem_type": "nfs4",
        "filesystem_source": "server:/shared",
    }


def test_storage_snapshot_allows_cross_node_device_id_difference() -> None:
    expected = _qualification_snapshot()
    observed = {**expected, "device_id": 102}

    assert qualification._stable_snapshot(expected, observed)


@pytest.mark.parametrize(
    ("field", "different"),
    [
        ("path", "/other"),
        ("inode", 2002),
        ("uid", 3003),
        ("gid", 4004),
        ("mount_point", "/other-mount"),
        ("filesystem_type", "lustre"),
        ("filesystem_source", "other:/export"),
    ],
)
def test_storage_snapshot_rejects_other_identity_drift(
    field: str,
    different: object,
) -> None:
    expected = _qualification_snapshot()
    observed = {**expected, field: different}

    assert not qualification._stable_snapshot(expected, observed)


def test_two_phase_storage_qualification_is_durable_and_read_only_to_doctor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        qualification,
        "_mount_identity",
        synthetic_mount_identity,
    )
    workspace = tmp_path / "workspace"
    reference_root = tmp_path / "reference"
    reference_root.mkdir()
    reference_fasta = reference_root / "genome.fa"
    reference_fasta.write_text(">1\nA\n", encoding="utf-8")
    arguments = argparse.Namespace(
        workspace=workspace,
        reference_fasta=reference_fasta,
        phase="compute",
        execute=False,
    )
    monkeypatch.delenv("SLURM_JOB_ID", raising=False)

    assert qualification.qualify_from_args(arguments) == 0
    assert not (tmp_path / qualification.EVIDENCE_DIRECTORY).exists()

    arguments.execute = True
    monkeypatch.setenv("SLURM_JOB_ID", "700123")
    assert qualification.qualify_from_args(arguments) == 0
    monkeypatch.delenv("SLURM_JOB_ID")
    arguments.phase = "finalize"
    assert qualification.qualify_from_args(arguments) == 0

    admitted = qualification.admit_final_qualification(
        workspace,
        reference_fasta,
    )
    assert admitted.receipt_path.is_file()
    assert len(admitted.receipt_sha256) == 64
    assert not list(tmp_path.glob(".emrys-storage-probe-*"))
    assert not list(reference_root.glob(".emrys-storage-probe-*"))


def _direct_qualification_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> qualification.DirectQualificationPlan:
    monkeypatch.setattr(qualification, "_mount_identity", synthetic_mount_identity)
    workspace = tmp_path / "project"
    (workspace / "runtime").mkdir(parents=True)
    reference_root = workspace / "reference"
    reference_root.mkdir()
    reference_fasta = reference_root / "genome.fa"
    reference_fasta.write_text(">1\nA\n", encoding="utf-8")
    monkeypatch.delenv("SLURM_JOB_ID", raising=False)
    return qualification.plan_direct_qualification(workspace, reference_fasta)


def _direct_qualification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, qualification.QualifiedStorage]:
    plan = _direct_qualification_plan(tmp_path, monkeypatch)

    admitted = qualification.execute_direct_qualification(plan)

    return plan.workspace, plan.reference_fasta, admitted


def test_direct_qualification_is_single_host_create_absent_and_not_site_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, reference_fasta, admitted = _direct_qualification(
        tmp_path,
        monkeypatch,
    )
    value = json.loads(admitted.receipt_path.read_text(encoding="utf-8"))

    assert admitted.receipt_path.parent == (
        workspace / "runtime" / qualification.EVIDENCE_DIRECTORY
    )
    assert value["schema"] == qualification.DIRECT_SCHEMA
    assert value["checks"] == list(qualification.CHECKS[:4])
    assert "compute" not in value and "head" not in value
    assert not list(workspace.glob(".emrys-storage-probe-*"))
    assert not list(reference_fasta.parent.glob(".emrys-storage-probe-*"))
    with pytest.raises(
        qualification.StorageQualificationError,
        match="Storage qualification evidence directory",
    ):
        qualification.admit_final_qualification(workspace, reference_fasta)
    with pytest.raises(
        qualification.StorageQualificationError,
        match="evidence already exists",
    ):
        qualification.plan_direct_qualification(workspace, reference_fasta)


def test_direct_qualification_supersedes_invalid_evidence_without_deleting_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, reference_fasta, original = _direct_qualification(
        tmp_path,
        monkeypatch,
    )
    stale = json.loads(original.receipt_path.read_bytes())
    stale["context"]["host"] = "stale-host"
    original.receipt_path.write_bytes(qualification._json_bytes(stale))
    preserved = original.receipt_path.read_bytes()

    plan = qualification.plan_direct_qualification(workspace, reference_fasta)
    assert plan.receipt_path.name.endswith(".direct-qualified.1.json")
    replacement = qualification.execute_direct_qualification(plan)

    assert replacement.receipt_path == plan.receipt_path
    assert qualification.admit_direct_qualification(
        workspace,
        reference_fasta,
    ) == replacement
    assert original.receipt_path.read_bytes() == preserved


def test_direct_admission_rejects_a_pending_successor_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, reference_fasta, _original = _direct_qualification(
        tmp_path,
        monkeypatch,
    )
    staged = qualification._direct_layout(
        workspace,
        reference_fasta,
        generation=1,
    ).staged_path
    staged.write_bytes(b"pending successor\n")

    with pytest.raises(
        qualification.StorageQualificationError,
        match="Incomplete direct qualification publication",
    ):
        qualification.admit_direct_qualification(workspace, reference_fasta)


def test_direct_requirement_accepts_stronger_site_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = tmp_path / "site-qualified.json"
    receipt.write_bytes(b"site qualified\n")
    expected = qualification.QualifiedStorage(
        receipt_path=receipt,
        receipt_sha256="a" * 64,
        qualification_id="b" * 64,
    )

    def reject_direct(*_args: object) -> qualification.QualifiedStorage:
        raise qualification.StorageQualificationError("no direct receipt")

    monkeypatch.setattr(
        qualification,
        "admit_direct_qualification",
        reject_direct,
    )
    monkeypatch.setattr(
        qualification,
        "admit_final_qualification",
        lambda *_args: expected,
    )

    assert (
        qualification.admit_direct_requirement(
            tmp_path / "project",
            tmp_path / "reference.fa",
        )
        is expected
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("fields", "invalid fields"),
        ("identity", "invalid identity or status"),
        ("host", "Current host"),
        ("root", "no longer matches workflow_workspace"),
    ),
)
def test_direct_qualification_admission_rejects_mutated_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    message: str,
) -> None:
    workspace, reference_fasta, admitted = _direct_qualification(
        tmp_path,
        monkeypatch,
    )
    value = json.loads(admitted.receipt_path.read_text(encoding="utf-8"))
    if mutation == "fields":
        value["unexpected"] = True
    elif mutation == "identity":
        value["schema"] = qualification.SCHEMA
    elif mutation == "host":
        value["context"]["host"] = "other-host"
    else:
        value["roots"][0]["root"]["device_id"] += 1
    admitted.receipt_path.write_text(
        json.dumps(value, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(qualification.StorageQualificationError, match=message):
        qualification.admit_direct_qualification(workspace, reference_fasta)


def test_storage_finalize_refuses_missing_post_allocation_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        qualification,
        "_mount_identity",
        synthetic_mount_identity,
    )
    workspace = tmp_path / "workspace"
    reference_root = tmp_path / "reference"
    reference_root.mkdir()
    reference_fasta = reference_root / "genome.fa"
    reference_fasta.write_text(">1\nA\n", encoding="utf-8")
    arguments = argparse.Namespace(
        workspace=workspace,
        reference_fasta=reference_fasta,
        phase="compute",
        execute=True,
    )
    monkeypatch.setenv("SLURM_JOB_ID", "700124")
    assert qualification.qualify_from_args(arguments) == 0
    retained = next(tmp_path.glob(".emrys-storage-probe-*/visible.bin"))
    retained.unlink()

    monkeypatch.delenv("SLURM_JOB_ID")
    arguments.phase = "finalize"
    assert qualification.qualify_from_args(arguments) == 2
    evidence_root = tmp_path / qualification.EVIDENCE_DIRECTORY
    assert not list(evidence_root.glob("*.qualified.json"))


def _qualification_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[argparse.Namespace, Path, Path]:
    monkeypatch.setattr(qualification, "_mount_identity", synthetic_mount_identity)
    workspace = tmp_path / "workspace"
    reference_root = tmp_path / "reference"
    reference_root.mkdir(parents=True)
    reference_fasta = reference_root / "genome.fa"
    reference_fasta.write_text(">1\nA\n", encoding="utf-8")
    arguments = argparse.Namespace(
        workspace=workspace,
        reference_fasta=reference_fasta,
        phase="compute",
        execute=True,
    )
    return arguments, workspace, reference_fasta


def _compute_qualification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[argparse.Namespace, Path, Path, Path, Path]:
    arguments, workspace, reference_fasta = _qualification_inputs(tmp_path, monkeypatch)
    monkeypatch.setenv("SLURM_JOB_ID", "700200")
    assert qualification.qualify_from_args(arguments) == 0
    roots = qualification._storage_roots(workspace, reference_fasta)
    _identity, _evidence, compute, final, _staged = qualification._evidence_paths(roots)
    return arguments, workspace, reference_fasta, compute, final


def _final_qualification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, Path, Path]:
    arguments, workspace, reference_fasta, compute, final = _compute_qualification(
        tmp_path, monkeypatch
    )
    monkeypatch.delenv("SLURM_JOB_ID")
    arguments.phase = "finalize"
    assert qualification.qualify_from_args(arguments) == 0
    return workspace, reference_fasta, compute, final


@pytest.fixture(params=("direct", "two-phase"))
def qualification_attempt(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> argparse.Namespace:
    if request.param == "direct":
        plan = _direct_qualification_plan(tmp_path, monkeypatch)
        execute = partial(qualification.execute_direct_qualification, plan)
        admit = partial(qualification.admit_direct_qualification, plan.workspace, plan.reference_fasta)
        final, staged, probes, compute = plan.receipt_path, plan.staged_path, plan.probe_paths, None
    else:
        _arguments, workspace, reference, compute, final = _compute_qualification(tmp_path, monkeypatch)
        staged = qualification._evidence_paths(qualification._storage_roots(workspace, reference))[-1]
        probes = tuple(Path(row["probe_directory"]) for row in json.loads(compute.read_bytes())["roots"])
        execute = partial(qualification._run_finalize, workspace, reference)
        admit = partial(qualification.admit_final_qualification, workspace, reference)
    monkeypatch.delenv("SLURM_JOB_ID", raising=False)
    return argparse.Namespace(execute=execute, admit=admit, final=final, staged=staged, probes=probes, compute=compute)


@pytest.mark.parametrize("fault", ("link", "foreign-final", "first-fsync", "stage-unlink", "second-fsync"))
def test_qualification_publication_failure_preserves_evidence(
    qualification_attempt: argparse.Namespace,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    attempt = qualification_attempt
    compute_bytes = None if attempt.compute is None else attempt.compute.read_bytes()
    real_link = qualification.os.link
    real_fsync = qualification._fsync_directory
    real_unlink = Path.unlink
    fsync_calls = 0

    def link(source: Path, destination: Path, **kwargs: object) -> None:
        if Path(destination) == attempt.final:
            if fault == "link":
                raise OSError("injected final link failure")
            if fault == "foreign-final":
                attempt.final.write_bytes(b"foreign receipt\n")
        real_link(source, destination, **kwargs)

    def fsync(path: Path) -> None:
        nonlocal fsync_calls
        if path == attempt.final.parent:
            fsync_calls += 1
            if (fault, fsync_calls) in (("first-fsync", 1), ("second-fsync", 2)):
                raise OSError("injected final directory fsync failure")
        real_fsync(path)

    def unlink(path: Path, **kwargs: object) -> None:
        if path == attempt.staged and fault == "stage-unlink":
            raise OSError("injected staged receipt cleanup failure")
        real_unlink(path, **kwargs)

    with monkeypatch.context() as injection:
        injection.setattr(qualification.os, "link", link)
        injection.setattr(qualification, "_fsync_directory", fsync)
        injection.setattr(Path, "unlink", unlink)
        with pytest.raises((qualification.StorageQualificationError, OSError)):
            attempt.execute()

    assert attempt.staged.exists() == (fault != "second-fsync")
    receipt = attempt.staged if attempt.staged.exists() else attempt.final
    receipt_bytes = receipt.read_bytes()
    assert json.loads(receipt_bytes)["status"] == "qualified"
    if fault == "link":
        assert not attempt.final.exists()
    elif fault == "foreign-final":
        assert attempt.final.read_bytes() == b"foreign receipt\n"
    else:
        assert attempt.final.read_bytes() == receipt_bytes
        if attempt.staged.exists():
            assert attempt.final.samefile(attempt.staged)
    rows = json.loads((attempt.compute or receipt).read_bytes())["roots"]
    for probe, row in zip(attempt.probes, rows, strict=True):
        assert {path.name for path in probe.iterdir()} == {"flock.lock", "fsync-source.bin", "hardlink.bin", "visible.bin"}
        source = probe / "fsync-source.bin"
        assert source.samefile(probe / "hardlink.bin")
        assert hashlib.sha256(source.read_bytes()).hexdigest() == row["source_sha256"]
        assert hashlib.sha256((probe / "visible.bin").read_bytes()).hexdigest() == row["visible_sha256"]
    if fault == "second-fsync":
        assert attempt.admit().receipt_path == attempt.final
    else:
        with pytest.raises(qualification.StorageQualificationError, match="Incomplete"):
            attempt.admit()
    with pytest.raises(qualification.StorageQualificationError, match="already exists|Incomplete"):
        attempt.execute()
    assert receipt.read_bytes() == receipt_bytes
    if attempt.compute is not None:
        assert attempt.compute.read_bytes() == compute_bytes


@pytest.mark.parametrize("fault", ("first-probe", "partial-probe", "second-probe"))
def test_qualification_cleanup_failure_preserves_receipt(
    qualification_attempt: argparse.Namespace,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    attempt = qualification_attempt
    compute_bytes = None if attempt.compute is None else attempt.compute.read_bytes()
    real_unlink = Path.unlink
    real_cleanup = qualification._cleanup_probe
    receipt_bytes = b""

    def cleanup(probe: Path) -> None:
        nonlocal receipt_bytes
        receipt_bytes = attempt.final.read_bytes()
        assert not attempt.staged.exists()
        assert attempt.admit().receipt_path == attempt.final
        if (fault, probe) in (("first-probe", attempt.probes[0]), ("second-probe", attempt.probes[1])):
            raise OSError("injected probe cleanup failure")
        real_cleanup(probe)

    def unlink(path: Path, **kwargs: object) -> None:
        if path == attempt.probes[0] / "fsync-source.bin" and fault == "partial-probe":
            raise OSError("injected partial probe cleanup failure")
        real_unlink(path, **kwargs)

    with monkeypatch.context() as injection:
        injection.setattr(qualification, "_cleanup_probe", cleanup)
        injection.setattr(Path, "unlink", unlink)
        with pytest.raises(OSError, match="injected .*probe cleanup failure"):
            attempt.execute()

    assert not attempt.staged.exists()
    assert attempt.final.read_bytes() == receipt_bytes
    assert attempt.admit().receipt_sha256 == hashlib.sha256(receipt_bytes).hexdigest()
    assert attempt.probes[1].is_dir()
    assert attempt.probes[0].exists() == (fault != "second-probe")
    if fault == "partial-probe":
        assert not (attempt.probes[0] / "flock.lock").exists()
        assert (attempt.probes[0] / "fsync-source.bin").is_file()
    if attempt.compute is not None:
        assert attempt.compute.read_bytes() == compute_bytes


def test_storage_roots_reject_relative_links_and_noncanonical_inputs(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        qualification.StorageQualificationError, match="must be absolute"
    ):
        qualification._canonical_directory(Path("relative"), "Fixture")

    real = tmp_path / "real"
    real.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    with pytest.raises(qualification.StorageQualificationError, match="canonical real"):
        qualification._canonical_directory(linked, "Fixture")

    reference = tmp_path / "reference.fa"
    reference.write_text(">1\nA\n", encoding="utf-8")
    reference_link = tmp_path / "reference-link.fa"
    reference_link.symlink_to(reference)
    with pytest.raises(
        qualification.StorageQualificationError, match="canonical regular"
    ):
        qualification._storage_roots(tmp_path / "workspace", reference_link)

    workspace_target = tmp_path / "workspace-target"
    workspace_target.mkdir()
    workspace_link = tmp_path / "workspace-link"
    workspace_link.symlink_to(workspace_target, target_is_directory=True)
    with pytest.raises(
        qualification.StorageQualificationError,
        match="absent or a canonical real directory",
    ):
        qualification._storage_roots(workspace_link, reference)


@pytest.mark.parametrize(
    ("payload", "message"),
    (
        (b"not-json", "not valid UTF-8 JSON"),
        (b"[]\n", "must be a JSON object"),
    ),
)
def test_qualification_json_requires_a_strict_object(
    payload: bytes,
    message: str,
) -> None:
    with pytest.raises(qualification.StorageQualificationError, match=message):
        qualification._json_object(payload, "Fixture receipt")


@pytest.mark.parametrize(
    ("mountinfo", "message"),
    (
        ("invalid-row\n", "invalid row"),
        ("24 1 8:1 / /other rw - ext4 /dev/root rw\n", "No Linux mount identity"),
    ),
)
def test_mount_identity_rejects_invalid_or_uncovered_mountinfo(
    monkeypatch: pytest.MonkeyPatch,
    mountinfo: str,
    message: str,
) -> None:
    monkeypatch.setattr(Path, "read_text", lambda *_args, **_kwargs: mountinfo)

    with pytest.raises(qualification.StorageQualificationError, match=message):
        qualification._mount_identity(Path("/shared/workspace"))


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("fields", "invalid fields"),
        ("identity", "invalid identity or status"),
        ("execution", "invalid execution identity"),
        ("roster", "invalid root roster"),
        ("role", "invalid ordered roles"),
        ("probe", "unexpected probe directory"),
        ("hash", "invalid source_sha256"),
    ),
)
def test_compute_receipt_rejects_each_identity_layer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    message: str,
) -> None:
    _arguments, workspace, reference_fasta, compute, _final = _compute_qualification(
        tmp_path, monkeypatch
    )
    value = json.loads(compute.read_text(encoding="utf-8"))
    if mutation == "fields":
        value["unexpected"] = True
    elif mutation == "identity":
        value["status"] = "failed"
    elif mutation == "execution":
        value["compute"] = []
    elif mutation == "roster":
        value["roots"] = []
    elif mutation == "role":
        value["roots"][0]["role"] = "wrong"
    elif mutation == "probe":
        value["roots"][0]["probe_directory"] = "/wrong"
    else:
        value["roots"][0]["source_sha256"] = "short"
    roots = qualification._storage_roots(workspace, reference_fasta)
    qualification_id = qualification._qualification_id(roots)

    with pytest.raises(qualification.StorageQualificationError, match=message):
        qualification._validate_compute(value, qualification_id, roots)


def test_finalize_rejects_tampered_retained_probe_and_head_node_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arguments, _workspace, _reference, compute, _final = _compute_qualification(
        tmp_path / "tampered", monkeypatch
    )
    value = json.loads(compute.read_text(encoding="utf-8"))
    visible = Path(value["roots"][0]["probe_directory"]) / "visible.bin"
    visible.write_bytes(b"tampered")
    monkeypatch.delenv("SLURM_JOB_ID")
    arguments.phase = "finalize"
    assert qualification.qualify_from_args(arguments) == 2

    arguments, _workspace, _reference, _compute, _final = _compute_qualification(
        tmp_path / "inside-allocation", monkeypatch
    )
    arguments.phase = "finalize"
    with pytest.raises(
        qualification.StorageQualificationError,
        match="after the allocation",
    ):
        qualification._run_finalize(arguments.workspace, arguments.reference_fasta)


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("fields", "invalid fields"),
        ("identity", "invalid identity or status"),
        ("binding", "does not bind"),
        ("numeric_identity", "numeric UID/GID differs"),
        ("roster", "invalid root roster"),
        ("root", "no longer matches workflow_workspace"),
    ),
)
def test_final_qualification_admission_rejects_mutated_receipts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    message: str,
) -> None:
    workspace, reference_fasta, _compute, final = _final_qualification(
        tmp_path, monkeypatch
    )
    value = json.loads(final.read_text(encoding="utf-8"))
    if mutation == "fields":
        value["unexpected"] = True
    elif mutation == "identity":
        value["status"] = "failed"
    elif mutation == "binding":
        value["compute_receipt"]["sha256"] = "0" * 64
    elif mutation == "numeric_identity":
        value["head"]["uid"] = value["head"]["uid"] + 1
    elif mutation == "roster":
        value["roots"] = []
    else:
        value["roots"][0]["root"]["path"] = "/wrong"
    final.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(qualification.StorageQualificationError, match=message):
        qualification.admit_final_qualification(workspace, reference_fasta)


def test_final_qualification_rejects_incomplete_staged_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, reference_fasta, _compute, _final = _final_qualification(
        tmp_path, monkeypatch
    )
    roots = qualification._storage_roots(workspace, reference_fasta)
    _identity, _evidence, _compute_path, _final_path, staged = (
        qualification._evidence_paths(roots)
    )
    staged.write_text("incomplete\n", encoding="utf-8")

    with pytest.raises(qualification.StorageQualificationError, match="Incomplete"):
        qualification.admit_final_qualification(workspace, reference_fasta)
