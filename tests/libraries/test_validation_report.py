"""Adversarial characterization for the shared step-validation publisher.

These tests intentionally distinguish protected behavior from known audited
gaps.  Assertions labeled as a known gap record the current implementation so
Phase 03 can change it deliberately; they do not endorse that behavior.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import os
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "scripts"
REPORT_PATH = REPO_ROOT / "src" / "norad" / "libraries" / "validation_report.py"
VALIDATOR_PATHS = {
    "validate_step_00a_star_index": Path(
        "src/norad/stages/construct_STAR_index/validate_step_00a_star_index.py"
    ),
    "validate_step_00b_bed12": Path(
        "src/norad/stages/convert_GTF_to_BED12/validate_step_00b_bed12.py"
    ),
    "validate_step_00c_reference_sidecars": Path(
        "src/norad/stages/construct_FASTA_sidecars/"
        "validate_step_00c_reference_sidecars.py"
    ),
    "validate_step_01_star_alignment": Path(
        "src/norad/stages/align_RNA_reads_with_STAR/"
        "validate_step_01_star_alignment.py"
    ),
    "validate_step_02_canonical_bam": Path(
        "src/norad/stages/construct_canonical_BAM/"
        "validate_step_02_canonical_bam.py"
    ),
    "validate_step_02b_bam_qc": Path("scripts/validate_step_02b_bam_qc.py"),
    "validate_step_03_rseqc_orientation": Path(
        "scripts/validate_step_03_rseqc_orientation.py"
    ),
    "validate_step_04_mark_duplicates": Path(
        "scripts/validate_step_04_mark_duplicates.py"
    ),
    "validate_step_05_split_ncigar": Path(
        "scripts/validate_step_05_split_ncigar.py"
    ),
    "validate_step_06_orientation_outputs": Path(
        "scripts/validate_step_06_orientation_outputs.py"
    ),
    "validate_step_07_mpileup_outputs": Path(
        "scripts/validate_step_07_mpileup_outputs.py"
    ),
    "validate_step_08_preprocessing_outputs": Path(
        "scripts/validate_step_08_preprocessing_outputs.py"
    ),
    "validate_step_09_cmh_outputs": Path(
        "scripts/validate_step_09_cmh_outputs.py"
    ),
}
VALIDATOR_MODULES = tuple(VALIDATOR_PATHS)
NON_FLAT_VALIDATOR_MODULES = frozenset(
    module_name
    for module_name, path in VALIDATOR_PATHS.items()
    if path.parent != Path("scripts")
)
STEP_00B_VALIDATOR_NAME = "validate_step_00b_bed12"
STEP_00B_PRODUCER_NAME = "gtf_to_bed12"
STEP_00B_PRODUCER_PATH = (
    REPO_ROOT
    / "src"
    / "norad"
    / "stages"
    / "convert_GTF_to_BED12"
    / "gtf_to_bed12.py"
)
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))


def validator_path(module_name: str) -> Path:
    return REPO_ROOT / VALIDATOR_PATHS[module_name]


def load_exact_test_module(module_name: str, path: Path) -> ModuleType:
    cached = sys.modules.get(module_name)
    if cached is not None:
        try:
            cached_path = Path(getattr(cached, "__file__")).resolve(strict=False)
        except (OSError, TypeError) as exc:
            raise RuntimeError(
                f"cached test module {module_name} has no valid file path"
            ) from exc
        if cached_path != path.resolve(strict=False):
            raise RuntimeError(
                f"cached test module {module_name} resolves to {cached_path}, "
                f"expected {path.resolve(strict=False)}"
            )
        assert isinstance(cached, ModuleType)
        return cached
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not exact-load test module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(module_name) is module:
            sys.modules.pop(module_name, None)
        raise
    return module


def load_validator_module(module_name: str) -> ModuleType:
    if module_name == STEP_00B_VALIDATOR_NAME:
        producer_was_cached = STEP_00B_PRODUCER_NAME in sys.modules
        load_exact_test_module(STEP_00B_PRODUCER_NAME, STEP_00B_PRODUCER_PATH)
        try:
            return load_exact_test_module(module_name, validator_path(module_name))
        except BaseException:
            if not producer_was_cached:
                sys.modules.pop(STEP_00B_PRODUCER_NAME, None)
            raise
    if module_name in NON_FLAT_VALIDATOR_MODULES:
        return load_exact_test_module(module_name, validator_path(module_name))
    return importlib.import_module(module_name)


STEP_00A = load_validator_module("validate_step_00a_star_index")
REPORT = STEP_00A.report
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
    discovered_flat = {
        Path("scripts") / path.name
        for path in SCRIPT_ROOT.glob("validate_step_*.py")
    }
    expected_flat = {
        path for path in VALIDATOR_PATHS.values() if path.parent == Path("scripts")
    }
    assert discovered_flat == expected_flat
    assert all(validator_path(name).is_file() for name in VALIDATOR_MODULES)
    assert len(set(VALIDATOR_PATHS.values())) == len(VALIDATOR_MODULES)
    assert STEP_00B_PRODUCER_PATH.is_file()

    # One adversarial helper matrix therefore exercises all thirteen public
    # step-report formats through the exact final owner and private identity.
    assert Path(REPORT.__file__).resolve() == REPORT_PATH.resolve()
    assert sys.modules["_norad_validation_report"] is REPORT
    for module_name in VALIDATOR_MODULES:
        module = load_validator_module(module_name)
        assert module.report is REPORT
    assert (
        Path(sys.modules[STEP_00B_PRODUCER_NAME].__file__).resolve()
        == STEP_00B_PRODUCER_PATH.resolve()
    )

    for module_name in VALIDATOR_MODULES:
        source = validator_path(module_name).read_text(encoding="utf-8")
        assert "changed after validation" in source
        assert "report.publish(" in source
        assert "import validate_step_00a_star_index as report" not in source


def test_all_validator_loaders_preserve_sys_path() -> None:
    before = list(sys.path)
    for module_name in VALIDATOR_MODULES:
        sys.modules.pop(module_name, None)
        module = load_validator_module(module_name)
        assert module.report is REPORT
        assert Path(module.report.__file__).resolve() == REPORT_PATH.resolve()
    assert sys.path == before


def test_step00b_exact_loader_rejects_a_foreign_sibling_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = list(sys.path)
    foreign = ModuleType(STEP_00B_PRODUCER_NAME)
    foreign.__file__ = str(tmp_path / "foreign_gtf_to_bed12.py")
    monkeypatch.setitem(sys.modules, STEP_00B_PRODUCER_NAME, foreign)

    with pytest.raises(RuntimeError, match="expected"):
        load_validator_module(STEP_00B_VALIDATOR_NAME)

    assert sys.modules[STEP_00B_PRODUCER_NAME] is foreign
    assert sys.path == before


@pytest.mark.parametrize(
    ("cached_file", "ready", "message"),
    (
        ("wrong-owner.py", True, "expected"),
        (str(REPORT_PATH), False, "partially initialized"),
    ),
)
@pytest.mark.parametrize("module_name", VALIDATOR_MODULES)
def test_loader_rejects_and_preserves_foreign_cache_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cached_file: str,
    ready: bool,
    message: str,
    module_name: str,
) -> None:
    validator = load_validator_module(module_name)
    foreign = ModuleType("_norad_validation_report")
    foreign.__file__ = (
        str(tmp_path / cached_file) if cached_file == "wrong-owner.py" else cached_file
    )
    if ready:
        foreign._NORAD_VALIDATION_REPORT_READY = True
    monkeypatch.setitem(sys.modules, "_norad_validation_report", foreign)

    with pytest.raises(ImportError, match=message):
        validator._load_validation_report()

    assert sys.modules["_norad_validation_report"] is foreign


@pytest.mark.parametrize(
    ("cached_file", "ready"),
    (
        ("wrong-owner.py", True),
        (str(REPORT_PATH), False),
    ),
)
@pytest.mark.parametrize("module_name", VALIDATOR_MODULES)
def test_public_loader_cache_collision_is_one_stderr_line(
    tmp_path: Path,
    cached_file: str,
    ready: bool,
    module_name: str,
) -> None:
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    effective_file = (
        str(tmp_path / cached_file) if cached_file == "wrong-owner.py" else cached_file
    )
    setup = textwrap.dedent(
        f"""
        import runpy
        import sys
        from types import ModuleType

        cached = ModuleType("_norad_validation_report")
        cached.__file__ = {effective_file!r}
        cached._NORAD_VALIDATION_REPORT_READY = {ready!r}
        sys.modules["_norad_validation_report"] = cached
        runpy.run_path(
            {str(validator_path(module_name))!r},
            run_name="__main__",
        )
        """
    )
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", setup],
        cwd=invocation_cwd,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert_owner_failure(result, REPORT_PATH, "ImportError")
    assert list(invocation_cwd.iterdir()) == []


@pytest.mark.parametrize(
    ("source", "error_type"),
    (
        ("raise RuntimeError('injected ordinary owner failure')\n", RuntimeError),
        ("raise KeyboardInterrupt\n", KeyboardInterrupt),
    ),
)
@pytest.mark.parametrize("module_name", VALIDATOR_MODULES)
def test_loader_removes_only_its_owned_partial_after_execution_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    error_type: type[BaseException],
    module_name: str,
) -> None:
    validator = load_validator_module(module_name)
    failing_owner = tmp_path / "validation_report.py"
    failing_owner.write_text(source, encoding="utf-8")
    monkeypatch.setattr(validator, "_REPORT_MODULE_PATH", failing_owner)
    monkeypatch.delitem(sys.modules, "_norad_validation_report", raising=False)

    with pytest.raises(error_type):
        validator._load_validation_report()

    assert "_norad_validation_report" not in sys.modules


@pytest.mark.parametrize("module_name", VALIDATOR_MODULES)
def test_each_loader_can_initialize_the_exact_owner_from_an_empty_cache(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
) -> None:
    validator = load_validator_module(module_name)
    monkeypatch.delitem(sys.modules, "_norad_validation_report", raising=False)

    loaded = validator._load_validation_report()

    assert Path(loaded.__file__).resolve() == REPORT_PATH.resolve()
    assert getattr(loaded, "_NORAD_VALIDATION_REPORT_READY") is True
    assert sys.modules["_norad_validation_report"] is loaded


@pytest.mark.parametrize("module_name", VALIDATOR_MODULES)
def test_each_loader_fails_closed_when_no_specification_can_be_created(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
) -> None:
    validator = load_validator_module(module_name)
    monkeypatch.delitem(sys.modules, "_norad_validation_report", raising=False)
    monkeypatch.setattr(
        validator.importlib.util,
        "spec_from_file_location",
        lambda *_args, **_kwargs: None,
    )

    with pytest.raises(ImportError, match="module specification"):
        validator._load_validation_report()

    assert "_norad_validation_report" not in sys.modules


def owner_failure_result(
    script: Path,
    invocation_cwd: Path,
) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=invocation_cwd,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


def assert_owner_failure(
    result: subprocess.CompletedProcess[str],
    expected_path: Path,
    exception_name: str,
) -> None:
    assert result.returncode == 2
    assert result.stdout == ""
    lines = result.stderr.splitlines()
    assert len(lines) == 1
    assert lines[0].startswith(
        f"ERROR: unable to load NORAD validation-report owner at {expected_path}: "
        f"{exception_name}: "
    )
    assert "Traceback" not in result.stderr


def copy_validator_fixture(module_name: str, copied_root: Path) -> Path:
    source = validator_path(module_name)
    copied = copied_root / VALIDATOR_PATHS[module_name]
    copied.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, copied)
    if module_name == STEP_00B_VALIDATOR_NAME:
        shutil.copy2(STEP_00B_PRODUCER_PATH, copied.parent / "gtf_to_bed12.py")
    return copied


def test_every_copied_validator_reports_a_missing_exact_owner_without_artifacts(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "copied"
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    expected_path = copied_root / "src" / "norad" / "libraries" / "validation_report.py"

    for module_name in VALIDATOR_MODULES:
        copied = copy_validator_fixture(module_name, copied_root)
        result = owner_failure_result(copied, invocation_cwd)
        assert_owner_failure(result, expected_path, "FileNotFoundError")
        assert list(invocation_cwd.iterdir()) == []


def test_every_copied_validator_reports_owner_execution_failure_without_artifacts(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "copied"
    owner = copied_root / "src" / "norad" / "libraries" / "validation_report.py"
    owner.parent.mkdir(parents=True)
    owner.write_text("raise RuntimeError('injected corrupt owner')\n", encoding="utf-8")
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()

    for module_name in VALIDATOR_MODULES:
        copied = copy_validator_fixture(module_name, copied_root)
        result = owner_failure_result(copied, invocation_cwd)
        assert_owner_failure(result, owner, "RuntimeError")
        assert list(invocation_cwd.iterdir()) == []


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
        REPORT,
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
