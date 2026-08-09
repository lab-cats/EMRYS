"""Adversarial characterization for the shared step-validation publisher.

These tests intentionally distinguish protected behavior from known audited
gaps.  Assertions labeled as a known gap record the current implementation so
Phase 03 can change it deliberately; they do not endorse that behavior.
"""

from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from norad.libraries import validation as REPORT
from norad.libraries.validation import inputs as INPUTS
from norad.libraries.validation import publication as PUBLICATION

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
        PUBLICATION.uuid,
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


def test_regular_snapshot_rejects_an_empty_required_file(tmp_path: Path) -> None:
    empty = tmp_path / "empty.tsv"
    empty.touch()

    with pytest.raises(REPORT.ValidationError, match="must be nonempty"):
        REPORT.regular_snapshot(empty, "Empty fixture")


def test_regular_snapshot_rejects_a_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.tsv"

    with pytest.raises(REPORT.ValidationError, match="is unavailable"):
        REPORT.regular_snapshot(missing, "Missing fixture")


def test_stable_text_rejects_non_utf8_input(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.tsv"
    invalid.write_bytes(b"\xff")

    with pytest.raises(REPORT.ValidationError, match="cannot be read as UTF-8"):
        REPORT.stable_text(invalid, "Invalid fixture")


def test_stable_text_rejects_a_snapshot_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "changing.tsv"
    source.write_text("stable\n", encoding="utf-8")
    snapshots = iter(
        (
            REPORT.Snapshot(1, 2, 7, 3),
            REPORT.Snapshot(1, 2, 7, 4),
        )
    )
    monkeypatch.setattr(
        INPUTS,
        "regular_snapshot",
        lambda *_args, **_kwargs: next(snapshots),
    )

    with pytest.raises(REPORT.ValidationError, match="changed while read"):
        REPORT.stable_text(source, "Changing fixture")


def test_report_validator_rejects_non_utf8_bytes() -> None:
    with pytest.raises(REPORT.ValidationError, match="not UTF-8"):
        REPORT.validate_report(b"\xff", SCOPE_ID)


def test_report_validator_rejects_an_extra_column() -> None:
    malformed = report_bytes("extra").rstrip(b"\n") + b"\textra\n"

    with pytest.raises(REPORT.ValidationError, match="invalid row"):
        REPORT.validate_report(
            malformed,
            SCOPE_ID,
            step_id=STEP_ID,
            check_ids=CHECK_IDS,
        )


def test_report_validator_rejects_wrong_check_identity() -> None:
    with pytest.raises(REPORT.ValidationError, match="check IDs"):
        REPORT.validate_report(
            report_bytes("wrong check"),
            SCOPE_ID,
            step_id=STEP_ID,
            check_ids={"different_check"},
        )


def test_report_validator_rejects_wrong_scope_identity() -> None:
    with pytest.raises(REPORT.ValidationError, match="scope identity"):
        REPORT.validate_report(
            report_bytes("wrong scope"),
            "different_scope",
            step_id=STEP_ID,
            check_ids=CHECK_IDS,
        )


def test_report_validator_rejects_invalid_status() -> None:
    invalid = report_bytes("wrong status").replace(b"\tpass\t", b"\tunknown\t")

    with pytest.raises(REPORT.ValidationError, match="status is invalid"):
        REPORT.validate_report(
            invalid,
            SCOPE_ID,
            step_id=STEP_ID,
            check_ids=CHECK_IDS,
        )


def test_build_report_preserves_snapshots_and_declared_check_identity() -> None:
    snapshots = object()

    data, returned_snapshots = REPORT.build_report(
        STEP_ID,
        SCOPE_ID,
        snapshots,
        CHECK_IDS,
        {"publication_contract": (True, "observed", "expected", "detail")},
    )

    assert returned_snapshots is snapshots
    REPORT.validate_report(
        data,
        SCOPE_ID,
        step_id=STEP_ID,
        check_ids=CHECK_IDS,
    )


def test_build_report_rejects_a_check_missing_from_owner_declaration() -> None:
    with pytest.raises(REPORT.ValidationError, match="check IDs"):
        REPORT.build_report(
            STEP_ID,
            SCOPE_ID,
            {},
            CHECK_IDS,
            {"unexpected": (True, "observed", "expected", "detail")},
        )


def test_runtime_finish_runs_optional_pre_report_hook(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[str] = []
    runtime = REPORT.Runtime(
        step_id=STEP_ID,
        scope_id=SCOPE_ID,
        check_ids=CHECK_IDS,
        output=tmp_path / f"{SCOPE_ID}.validation.tsv",
        execute=False,
        published_label="fixture",
    )

    status = REPORT.finish(
        runtime,
        report_bytes("hook"),
        {},
        before_report=lambda: calls.append("before"),
    )

    assert status == 0
    assert calls == ["before"]
    assert "Dry-run complete" in capsys.readouterr().out


def test_publish_rejects_a_missing_output_parent(tmp_path: Path) -> None:
    output = tmp_path / "missing" / f"{SCOPE_ID}.validation.tsv"

    with pytest.raises(REPORT.ValidationError, match="Output parent"):
        publish(output, report_bytes("missing parent"))


def test_publish_rejects_a_wrong_output_basename(tmp_path: Path) -> None:
    output = tmp_path / "wrong-name.tsv"

    with pytest.raises(REPORT.ValidationError, match="Output basename"):
        publish(output, report_bytes("wrong basename"))


def test_publish_rejects_an_existing_lock(tmp_path: Path) -> None:
    output = tmp_path / f"{SCOPE_ID}.validation.tsv"
    lock = tmp_path / f".{output.name}.lock"
    lock.write_text("foreign lock\n", encoding="utf-8")

    with pytest.raises(REPORT.ValidationError, match="lock already exists"):
        publish(output, report_bytes("locked"))

    assert lock.read_text(encoding="utf-8") == "foreign lock\n"


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

    monkeypatch.setattr(PUBLICATION.os, "fsync", fail_fsync)
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
    real_replace = PUBLICATION.os.replace

    def fail_predecessor_move(source: object, destination: object) -> None:
        if (
            Path(source) == publication_paths.output
            and Path(destination) == publication_paths.previous
        ):
            raise OSError("injected predecessor move failure")
        real_replace(source, destination)

    monkeypatch.setattr(PUBLICATION.os, "replace", fail_predecessor_move)
    with pytest.raises(OSError, match="predecessor move"):
        publish(publication_paths.output, report_bytes("replacement"))

    assert publication_paths.output.read_bytes() == prior
    assert hidden_attempt_paths(publication_paths) == []


def test_first_publication_move_failure_removes_owned_stage(
    publication_paths: PublicationPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_replace = PUBLICATION.os.replace

    def fail_new_publication(source: object, destination: object) -> None:
        if (
            Path(source) == publication_paths.staged
            and Path(destination) == publication_paths.output
        ):
            raise OSError("injected publication move failure")
        real_replace(source, destination)

    monkeypatch.setattr(PUBLICATION.os, "replace", fail_new_publication)
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
    real_replace = PUBLICATION.os.replace

    def fail_new_publication(source: object, destination: object) -> None:
        if (
            Path(source) == publication_paths.staged
            and Path(destination) == publication_paths.output
        ):
            raise OSError("injected replacement publication failure")
        real_replace(source, destination)

    monkeypatch.setattr(PUBLICATION.os, "replace", fail_new_publication)
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
    real_validate = PUBLICATION.validate_report
    calls = 0

    def fail_published_validation(*args: object, **kwargs: object) -> None:
        nonlocal calls
        calls += 1
        # Replacement validates staged, predecessor, then published bytes.
        if calls == 3:
            raise REPORT.ValidationError("injected published validation failure")
        real_validate(*args, **kwargs)

    monkeypatch.setattr(PUBLICATION, "validate_report", fail_published_validation)
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
    real_replace = PUBLICATION.os.replace

    def interrupt_publication(source: object, destination: object) -> None:
        if (
            Path(source) == publication_paths.staged
            and Path(destination) == publication_paths.output
        ):
            raise KeyboardInterrupt
        real_replace(source, destination)

    # publish catches BaseException around replacement, so interruption must
    # restore the valid predecessor before propagating to the caller.
    monkeypatch.setattr(PUBLICATION.os, "replace", interrupt_publication)
    with pytest.raises(KeyboardInterrupt):
        publish(publication_paths.output, report_bytes("replacement"))

    assert publication_paths.output.read_bytes() == prior
    assert hidden_attempt_paths(publication_paths) == []


def test_characterizes_late_foreign_final_deletion_gap(
    publication_paths: PublicationPaths,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_replace = PUBLICATION.os.replace
    foreign = b"late foreign final\n"

    def inject_foreign_then_fail(source: object, destination: object) -> None:
        if (
            Path(source) == publication_paths.staged
            and Path(destination) == publication_paths.output
        ):
            publication_paths.output.write_bytes(foreign)
            raise OSError("injected late foreign publication collision")
        real_replace(source, destination)

    monkeypatch.setattr(PUBLICATION.os, "replace", inject_foreign_then_fail)
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
    real_replace = PUBLICATION.os.replace

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
        PUBLICATION.os,
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
    real_open = PUBLICATION.os.open
    real_close = PUBLICATION.os.close
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

    monkeypatch.setattr(PUBLICATION.os, "open", track_lock_open)
    monkeypatch.setattr(PUBLICATION, "validate_report", fail_validation)
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
