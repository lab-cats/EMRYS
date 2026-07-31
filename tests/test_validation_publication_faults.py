"""Adversarial characterization for the shared step-validation publisher.

These tests intentionally distinguish protected behavior from known audited
gaps.  Assertions labeled as a known gap record the current implementation so
Phase 03 can change it deliberately; they do not endorse that behavior.
"""

from __future__ import annotations

import hashlib
import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

REPORT = importlib.import_module("validate_step_00a_star_index")

VALIDATOR_MODULES = (
    "validate_step_00a_star_index",
    "validate_step_00b_bed12",
    "validate_step_00c_reference_sidecars",
    "validate_step_01_star_alignment",
    "validate_step_02_canonical_bam",
    "validate_step_02b_bam_qc",
    "validate_step_03_rseqc_orientation",
    "validate_step_04_mark_duplicates",
    "validate_step_05_split_ncigar",
    "validate_step_06_orientation_outputs",
    "validate_step_07_mpileup_outputs",
    "validate_step_08_preprocessing_outputs",
    "validate_step_09_cmh_outputs",
)
SCOPE_ID = "fixture_scope"
STEP_ID = "fixture"
CHECK_IDS = {"publication_contract"}
TOKEN = "faulttoken"


@dataclass(frozen=True)
class PublicationPaths:
    parent: Path
    output: Path
    lock: Path
    staged: Path
    previous: Path


@pytest.fixture
def publication_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> PublicationPaths:
    parent = tmp_path / "reports"
    parent.mkdir()
    output = parent / f"{SCOPE_ID}.validation.tsv"
    monkeypatch.setattr(
        REPORT.uuid,
        "uuid4",
        lambda: SimpleNamespace(hex=TOKEN),
    )
    return PublicationPaths(
        parent=parent,
        output=output,
        lock=parent / f".{output.name}.lock",
        staged=parent / f".{output.name}.{TOKEN}.tmp",
        previous=parent / f".{output.name}.{TOKEN}.previous",
    )


def report_bytes(detail: str) -> bytes:
    return REPORT.render(
        (
            (
                STEP_ID,
                SCOPE_ID,
                "publication_contract",
                "pass",
                detail,
                "stable",
                "shared publication fixture",
            ),
        )
    )


def publish(path: Path, data: bytes) -> None:
    REPORT.publish(
        path,
        data,
        SCOPE_ID,
        step_id=STEP_ID,
        check_ids=CHECK_IDS,
    )


def hidden_attempt_paths(paths: PublicationPaths) -> list[Path]:
    return sorted(
        child
        for child in paths.parent.iterdir()
        if child.name.startswith(f".{paths.output.name}")
    )


def test_exact_step_validator_inventory_uses_one_shared_publisher() -> None:
    discovered = {
        path.stem for path in SCRIPT_ROOT.glob("validate_step_*.py")
    }
    assert discovered == set(VALIDATOR_MODULES)

    # One adversarial helper matrix therefore exercises all thirteen public
    # step-report formats; the other twelve modules import this exact owner.
    for module_name in VALIDATOR_MODULES[1:]:
        module = importlib.import_module(module_name)
        assert module.report is REPORT

    for module_name in VALIDATOR_MODULES:
        source = (SCRIPT_ROOT / f"{module_name}.py").read_text(
            encoding="utf-8"
        )
        assert "changed after validation" in source
        if module_name == "validate_step_00a_star_index":
            assert "publish(args.output" in source
        else:
            assert "report.publish(" in source


def test_snapshot_characterizes_same_size_restored_mtime_gap(
    tmp_path: Path,
) -> None:
    source = tmp_path / "input.tsv"
    source.write_bytes(b"alpha")
    metadata = source.stat()
    before = REPORT.regular_snapshot(source, "Input")
    before_digest = hashlib.sha256(source.read_bytes()).hexdigest()

    source.write_bytes(b"omega")
    os.utime(
        source,
        ns=(metadata.st_atime_ns, before.mtime_ns),
    )
    after = REPORT.regular_snapshot(source, "Input")
    after_digest = hashlib.sha256(source.read_bytes()).hexdigest()

    assert before_digest != after_digest
    # Known RA-002 gap: content changed, but the four-field snapshot is equal.
    assert before == after


def test_snapshot_detects_inode_replacement_and_rejects_symlink(
    tmp_path: Path,
) -> None:
    source = tmp_path / "input.tsv"
    source.write_bytes(b"alpha")
    before = REPORT.regular_snapshot(source, "Input")
    replacement = tmp_path / "replacement.tsv"
    replacement.write_bytes(b"alpha")

    os.replace(replacement, source)
    assert REPORT.regular_snapshot(source, "Input") != before

    target = tmp_path / "target.tsv"
    target.write_bytes(b"alpha")
    source.unlink()
    source.symlink_to(target)
    with pytest.raises(REPORT.ValidationError, match="non-symlink"):
        REPORT.regular_snapshot(source, "Input")


def test_first_publish_and_valid_predecessor_retry_leave_no_residue(
    publication_paths: PublicationPaths,
) -> None:
    first = report_bytes("first")
    replacement = report_bytes("replacement")

    publish(publication_paths.output, first)
    assert publication_paths.output.read_bytes() == first
    assert hidden_attempt_paths(publication_paths) == []

    publish(publication_paths.output, replacement)
    assert publication_paths.output.read_bytes() == replacement
    assert hidden_attempt_paths(publication_paths) == []


def test_invalid_staged_report_fails_before_publication(
    publication_paths: PublicationPaths,
) -> None:
    with pytest.raises(REPORT.ValidationError, match="header is invalid"):
        publish(publication_paths.output, b"not-a-validation-report\n")

    assert not publication_paths.output.exists()
    assert hidden_attempt_paths(publication_paths) == []


def test_invalid_predecessor_is_preserved(
    publication_paths: PublicationPaths,
) -> None:
    foreign = b"foreign predecessor\n"
    publication_paths.output.write_bytes(foreign)

    with pytest.raises(REPORT.ValidationError, match="header is invalid"):
        publish(publication_paths.output, report_bytes("replacement"))

    assert publication_paths.output.read_bytes() == foreign
    assert hidden_attempt_paths(publication_paths) == []


def test_symlinked_output_is_preserved_and_rejected(
    publication_paths: PublicationPaths,
) -> None:
    target = publication_paths.parent / "foreign.tsv"
    foreign = b"foreign target\n"
    target.write_bytes(foreign)
    publication_paths.output.symlink_to(target)

    with pytest.raises(REPORT.ValidationError, match="unsafe"):
        publish(publication_paths.output, report_bytes("new"))

    assert publication_paths.output.is_symlink()
    assert target.read_bytes() == foreign
    assert hidden_attempt_paths(publication_paths) == []


def test_stage_fsync_failure_removes_owned_attempt(
    publication_paths: PublicationPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_fsync(descriptor: int) -> None:
        raise OSError("injected staged fsync failure")

    monkeypatch.setattr(REPORT.os, "fsync", fail_fsync)
    with pytest.raises(OSError, match="staged fsync"):
        publish(publication_paths.output, report_bytes("new"))

    assert not publication_paths.output.exists()
    assert hidden_attempt_paths(publication_paths) == []


def test_predecessor_move_failure_preserves_predecessor(
    publication_paths: PublicationPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prior = report_bytes("prior")
    publication_paths.output.write_bytes(prior)
    real_replace = REPORT.os.replace

    def fail_predecessor_move(source: object, destination: object) -> None:
        if (
            Path(source) == publication_paths.output
            and Path(destination) == publication_paths.previous
        ):
            raise OSError("injected predecessor move failure")
        real_replace(source, destination)

    monkeypatch.setattr(REPORT.os, "replace", fail_predecessor_move)
    with pytest.raises(OSError, match="predecessor move"):
        publish(publication_paths.output, report_bytes("replacement"))

    assert publication_paths.output.read_bytes() == prior
    assert hidden_attempt_paths(publication_paths) == []


def test_first_publication_move_failure_removes_owned_stage(
    publication_paths: PublicationPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_replace = REPORT.os.replace

    def fail_new_publication(source: object, destination: object) -> None:
        if (
            Path(source) == publication_paths.staged
            and Path(destination) == publication_paths.output
        ):
            raise OSError("injected publication move failure")
        real_replace(source, destination)

    monkeypatch.setattr(REPORT.os, "replace", fail_new_publication)
    with pytest.raises(OSError, match="publication move"):
        publish(publication_paths.output, report_bytes("new"))

    assert not publication_paths.output.exists()
    assert hidden_attempt_paths(publication_paths) == []


def test_replacement_move_failure_restores_valid_predecessor(
    publication_paths: PublicationPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prior = report_bytes("prior")
    publication_paths.output.write_bytes(prior)
    real_replace = REPORT.os.replace

    def fail_new_publication(source: object, destination: object) -> None:
        if (
            Path(source) == publication_paths.staged
            and Path(destination) == publication_paths.output
        ):
            raise OSError("injected replacement publication failure")
        real_replace(source, destination)

    monkeypatch.setattr(REPORT.os, "replace", fail_new_publication)
    with pytest.raises(OSError, match="replacement publication"):
        publish(publication_paths.output, report_bytes("replacement"))

    assert publication_paths.output.read_bytes() == prior
    assert hidden_attempt_paths(publication_paths) == []


def test_post_publication_validation_failure_restores_predecessor(
    publication_paths: PublicationPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prior = report_bytes("prior")
    publication_paths.output.write_bytes(prior)
    real_validate = REPORT.validate_report
    calls = 0

    def fail_published_validation(*args: object, **kwargs: object) -> None:
        nonlocal calls
        calls += 1
        # Replacement validates staged, predecessor, then published bytes.
        if calls == 3:
            raise REPORT.ValidationError("injected published validation failure")
        real_validate(*args, **kwargs)

    monkeypatch.setattr(REPORT, "validate_report", fail_published_validation)
    with pytest.raises(REPORT.ValidationError, match="published validation"):
        publish(publication_paths.output, report_bytes("replacement"))

    assert calls == 3
    assert publication_paths.output.read_bytes() == prior
    assert hidden_attempt_paths(publication_paths) == []


def test_keyboard_interrupt_restores_predecessor_and_cleans_attempt(
    publication_paths: PublicationPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prior = report_bytes("prior")
    publication_paths.output.write_bytes(prior)
    real_replace = REPORT.os.replace

    def interrupt_publication(source: object, destination: object) -> None:
        if (
            Path(source) == publication_paths.staged
            and Path(destination) == publication_paths.output
        ):
            raise KeyboardInterrupt
        real_replace(source, destination)

    # publish catches BaseException around replacement, so interruption must
    # restore the valid predecessor before propagating to the caller.
    monkeypatch.setattr(REPORT.os, "replace", interrupt_publication)
    with pytest.raises(KeyboardInterrupt):
        publish(publication_paths.output, report_bytes("replacement"))

    assert publication_paths.output.read_bytes() == prior
    assert hidden_attempt_paths(publication_paths) == []


def test_characterizes_late_foreign_final_deletion_gap(
    publication_paths: PublicationPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_replace = REPORT.os.replace
    foreign = b"late foreign final\n"

    def inject_foreign_then_fail(source: object, destination: object) -> None:
        if (
            Path(source) == publication_paths.staged
            and Path(destination) == publication_paths.output
        ):
            publication_paths.output.write_bytes(foreign)
            raise OSError("injected late foreign publication collision")
        real_replace(source, destination)

    monkeypatch.setattr(REPORT.os, "replace", inject_foreign_then_fail)
    with pytest.raises(OSError, match="late foreign"):
        publish(publication_paths.output, report_bytes("new"))

    # Known RA-002 gap: rollback unlinks an unowned late final and releases the
    # lock instead of retaining collision evidence for operator recovery.
    assert not publication_paths.output.exists()
    assert hidden_attempt_paths(publication_paths) == []


def test_characterizes_incomplete_rollback_recovery_gap(
    publication_paths: PublicationPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prior = report_bytes("prior")
    publication_paths.output.write_bytes(prior)
    real_replace = REPORT.os.replace

    def fail_publication_and_restoration(
        source: object,
        destination: object,
    ) -> None:
        source_path = Path(source)
        destination_path = Path(destination)
        if (
            source_path == publication_paths.staged
            and destination_path == publication_paths.output
        ):
            raise OSError("injected publication failure")
        if (
            source_path == publication_paths.previous
            and destination_path == publication_paths.output
        ):
            raise OSError("injected restoration failure")
        real_replace(source, destination)

    monkeypatch.setattr(
        REPORT.os,
        "replace",
        fail_publication_and_restoration,
    )
    with pytest.raises(OSError, match="restoration failure"):
        publish(publication_paths.output, report_bytes("replacement"))

    assert not publication_paths.output.exists()
    assert publication_paths.previous.read_bytes() == prior
    # Known RA-002 gap: backup bytes survive, but ownership protection and a
    # recovery marker do not, leaving the attempt ambiguous.
    assert not publication_paths.lock.exists()
    assert not list(publication_paths.parent.glob("*.RECOVERY.txt"))


def test_characterizes_previous_cleanup_failure(
    publication_paths: PublicationPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prior = report_bytes("prior")
    replacement = report_bytes("replacement")
    publication_paths.output.write_bytes(prior)
    real_unlink = Path.unlink

    def fail_previous_cleanup(
        path_value: Path,
        *args: object,
        **kwargs: object,
    ) -> None:
        if path_value == publication_paths.previous:
            raise OSError("injected previous cleanup failure")
        real_unlink(path_value, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_previous_cleanup)
    with pytest.raises(OSError, match="previous cleanup"):
        publish(publication_paths.output, replacement)

    assert publication_paths.output.read_bytes() == replacement
    assert publication_paths.previous.read_bytes() == prior
    assert not publication_paths.lock.exists()


def test_stage_cleanup_failure_retains_stage_and_lock(
    publication_paths: PublicationPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_unlink = Path.unlink
    real_open = REPORT.os.open
    real_close = REPORT.os.close
    opened: list[int] = []

    def track_lock_open(*args: object, **kwargs: object) -> int:
        descriptor = real_open(*args, **kwargs)
        opened.append(descriptor)
        return descriptor

    def fail_validation(*args: object, **kwargs: object) -> None:
        raise REPORT.ValidationError("injected staged validation failure")

    def fail_stage_cleanup(
        path_value: Path,
        *args: object,
        **kwargs: object,
    ) -> None:
        if path_value == publication_paths.staged:
            raise OSError("injected stage cleanup failure")
        real_unlink(path_value, *args, **kwargs)

    monkeypatch.setattr(REPORT.os, "open", track_lock_open)
    monkeypatch.setattr(REPORT, "validate_report", fail_validation)
    monkeypatch.setattr(Path, "unlink", fail_stage_cleanup)
    with pytest.raises(OSError, match="stage cleanup"):
        publish(publication_paths.output, report_bytes("new"))

    # The cleanup exception stops the finally block before descriptor close or
    # lock removal. Close the injected descriptor explicitly after observing.
    assert publication_paths.staged.is_file()
    assert publication_paths.lock.is_file()
    for descriptor in opened:
        real_close(descriptor)
    real_unlink(publication_paths.staged)
    real_unlink(publication_paths.lock)


def test_lock_cleanup_failure_retains_lock_after_publication(
    publication_paths: PublicationPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = report_bytes("new")
    real_unlink = Path.unlink

    def fail_lock_cleanup(
        path_value: Path,
        *args: object,
        **kwargs: object,
    ) -> None:
        if path_value == publication_paths.lock:
            raise OSError("injected lock cleanup failure")
        real_unlink(path_value, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_lock_cleanup)
    with pytest.raises(OSError, match="lock cleanup"):
        publish(publication_paths.output, data)

    assert publication_paths.output.read_bytes() == data
    assert publication_paths.lock.is_file()
    real_unlink(publication_paths.lock)
