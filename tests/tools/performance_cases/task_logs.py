"""Retained task-log capture/hash hot paths, not full public-run timing.

Focused production tests separately prove that ``run_task`` and
``inspect_attempt_task_trees`` use the measured helpers.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import shutil
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

MIB = 1024 * 1024
CHUNK = 64 * 1024
VALUES = (1, 32, 128)
CAPTURE = "task-log-capture"
INSPECTION = "task-log-inspection"
CASES = (CAPTURE, INSPECTION)
SCHEMA = "emrys.retained-task-log.v1"
MEASUREMENT_BOUNDARY = (
    "private task-log capture/hash hot path; focused production call-site tests "
    "cover public run and inspection wiring"
)

_EMITTER = """
import os, sys
def copy(path, descriptor, offset, length):
    with open(path, "rb", buffering=0) as stream:
        stream.seek(offset)
        while length:
            block = stream.read(min(length, 65536))
            if not block: raise RuntimeError("fixture ended early")
            view = memoryview(block)
            while view:
                written = os.write(descriptor, view)
                if written <= 0: raise RuntimeError("short write")
                view = view[written:]
            length -= len(block)
copy(sys.argv[1], 1, int(sys.argv[3]), int(sys.argv[4]))
copy(sys.argv[2], 2, int(sys.argv[5]), int(sys.argv[6]))
"""
_PARTIAL = (
    "import os; os.write(1,b'partial-stdout\\x00\\xff'); "
    "os.write(2,b'partial-stderr\\xfe\\x00'); raise SystemExit(7)"
)
_INHERITED = """
import os, time
os.write(1, b"parent-stdout|")
os.write(2, b"parent-stderr|")
child = os.fork()
if child == 0:
    time.sleep(0.02)
    os.write(1, b"child-stdout")
    os.write(2, b"child-stderr")
    os._exit(0)
"""


class TaskLogCaseError(RuntimeError):
    """The task-log comparison boundary is invalid."""


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(MIB), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def _load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise TaskLogCaseError(f"expected one JSON object: {path}")
    return value


def _sizes(value: int) -> tuple[int, int]:
    if value not in VALUES:
        raise TaskLogCaseError(f"unregistered task-log size: {value}")
    total = value * MIB
    return (total + 1) // 2, total // 2


def _write_pattern(path: Path, size: int, seed: int) -> None:
    pattern = bytes(
        (((index * 131 + seed * 17) ^ (index >> 3)) & 0xFF) for index in range(CHUNK)
    )
    with path.open("xb") as stream:
        while size:
            block = pattern[: min(size, CHUNK)]
            stream.write(block)
            size -= len(block)


def _fixture(trial: Path) -> tuple[Path, Path, Path]:
    root = trial / "task-log-fixture"
    return root, root / "stdout.bin", root / "stderr.bin"


def _declared_identity(trial: Path, case: str, value: int) -> Mapping[str, Any]:
    root, stdout, stderr = _fixture(trial)
    expected = _load_json(root / "identity.json")
    stdout_size, stderr_size = _sizes(value)
    if (
        set(expected)
        != {
            "schema_version",
            "case",
            "value_mib",
            "stdout_size_bytes",
            "stderr_size_bytes",
            "stdout_sha256",
            "stderr_sha256",
        }
        or expected["schema_version"] != SCHEMA
        or expected["case"] != case
        or expected["value_mib"] != value
        or expected["stdout_size_bytes"] != stdout_size
        or expected["stderr_size_bytes"] != stderr_size
        or stdout.stat().st_size != stdout_size
        or stderr.stat().st_size != stderr_size
        or any(
            not isinstance(expected[field], str) or len(expected[field]) != 64
            for field in ("stdout_sha256", "stderr_sha256")
        )
    ):
        raise TaskLogCaseError("task-log fixture identity differs")
    return expected


def _identity(trial: Path, case: str, value: int) -> Mapping[str, Any]:
    expected = _declared_identity(trial, case, value)
    _root, stdout, stderr = _fixture(trial)
    if (
        _sha(stdout) != expected["stdout_sha256"]
        or _sha(stderr) != expected["stderr_sha256"]
    ):
        raise TaskLogCaseError("task-log fixture identity differs")
    return expected


def setup(trial: Path, case: str, value: int) -> None:
    if case not in CASES or not trial.is_dir() or trial.is_symlink():
        raise TaskLogCaseError("invalid task-log setup boundary")
    stdout_size, stderr_size = _sizes(value)
    root, stdout, stderr = _fixture(trial)
    root.mkdir(mode=0o700)
    _write_pattern(stdout, stdout_size, 11)
    _write_pattern(stderr, stderr_size, 29)
    _write_json(
        root / "identity.json",
        {
            "schema_version": SCHEMA,
            "case": case,
            "value_mib": value,
            "stdout_size_bytes": stdout_size,
            "stderr_size_bytes": stderr_size,
            "stdout_sha256": _sha(stdout),
            "stderr_sha256": _sha(stderr),
        },
    )
    if case == INSPECTION:
        shutil.copyfile(stdout, trial / "task.stdout.log")
        shutil.copyfile(stderr, trial / "task.stderr.log")


def _source_module(source: Path, name: str) -> ModuleType:
    source_python = source / "src"
    if not source_python.is_dir() or source_python.is_symlink():
        raise TaskLogCaseError(f"archived source tree is unavailable: {source}")
    prior = {
        key: module
        for key, module in tuple(sys.modules.items())
        if key == "emrys" or key.startswith("emrys.")
    }
    for key in prior:
        sys.modules.pop(key, None)
    sys.path.insert(0, str(source_python))
    importlib.invalidate_caches()
    try:
        try:
            module = importlib.import_module(name)
        except (ImportError, OSError) as exc:
            raise TaskLogCaseError(
                f"could not import {name} from archived source: {exc}"
            ) from exc
        expected = source_python.joinpath(*name.split(".")).with_suffix(".py")
        observed_file = getattr(module, "__file__", None)
        try:
            observed = (
                Path(observed_file).resolve(strict=True)
                if isinstance(observed_file, str)
                else None
            )
            selected = expected.resolve(strict=True)
        except OSError as exc:
            raise TaskLogCaseError(
                f"could not resolve {name} in the selected archived source: {exc}"
            ) from exc
        if observed != selected:
            raise TaskLogCaseError(
                f"{name} imported outside the selected archived source: {observed}"
            )
        return module
    finally:
        sys.path.remove(str(source_python))
        for key in tuple(sys.modules):
            if key == "emrys" or key.startswith("emrys."):
                sys.modules.pop(key, None)
        sys.modules.update(prior)


def _segments(size: int) -> tuple[tuple[int, int], ...]:
    base, remainder = divmod(size, 3)
    lengths = tuple(base + (index < remainder) for index in range(3))
    offsets = (0, lengths[0], lengths[0] + lengths[1])
    return tuple(zip(offsets, lengths, strict=True))


def _emitter_commands(trial: Path, value: int) -> tuple[tuple[str, ...], ...]:
    _root, stdout, stderr = _fixture(trial)
    stdout_segments = _segments(_sizes(value)[0])
    stderr_segments = _segments(_sizes(value)[1])
    return tuple(
        (
            sys.executable,
            "-c",
            _EMITTER,
            str(stdout),
            str(stderr),
            str(stdout_segment[0]),
            str(stdout_segment[1]),
            str(stderr_segment[0]),
            str(stderr_segment[1]),
        )
        for stdout_segment, stderr_segment in zip(
            stdout_segments, stderr_segments, strict=True
        )
    )


def _capture(
    module: ModuleType,
    root: Path,
    name: str,
    commands: Sequence[tuple[str, ...]],
    *,
    mutate: bool = False,
) -> tuple[tuple[int, ...], tuple[dict[str, str], dict[str, str]], bool]:
    stdout_path = root / f"{name}.stdout.log"
    stderr_path = root / f"{name}.stderr.log"
    if hasattr(module, "_TaskStreamCapture"):
        streams = module._TaskStreamCapture(stdout_path, stderr_path, root)  # noqa: SLF001
        descriptors = streams.open()
        results = tuple(
            module._default_run_command(command, root, None, *descriptors)  # noqa: SLF001
            for command in commands
        )
        references = streams.finalize()
        if mutate:
            stdout_path.write_bytes(stdout_path.read_bytes() + b"mutation")
            try:
                streams.revalidate_after_attempt_publication()
            except module.TaskBoundaryError:
                detected = True
            else:
                detected = False
        else:
            streams.revalidate_after_attempt_publication()
            detected = False
    else:
        results = tuple(
            module._default_run_command(command, root, None)  # noqa: SLF001
            for command in commands
        )
        stdout_data = b"".join(result.stdout for result in results)
        stderr_data = b"".join(result.stderr for result in results)
        module._publish_bytes(stdout_path, stdout_data)  # noqa: SLF001
        module._publish_bytes(stderr_path, stderr_data)  # noqa: SLF001
        references = (
            module._record_reference(stdout_path, root),  # noqa: SLF001
            module._record_reference(stderr_path, root),  # noqa: SLF001
        )
        if mutate:
            stdout_path.write_bytes(stdout_data + b"mutation")
            detected = (
                module._record_reference(stdout_path, root)  # noqa: SLF001
                != references[0]
            )
        else:
            if references != (
                module._record_reference(stdout_path, root),  # noqa: SLF001
                module._record_reference(stderr_path, root),  # noqa: SLF001
            ):
                raise TaskLogCaseError("buffered task logs changed during publication")
            detected = False
    return tuple(result.exit_code for result in results), references, detected


def _capture_diagnostics(module: ModuleType, trial: Path) -> Mapping[str, Any]:
    root = trial / "diagnostics"
    root.mkdir(mode=0o700)
    missing = ("/emrys-retained-missing-command",)
    spawn = _capture(module, root, "spawn", (missing,))[0]
    spawn_stdout = (root / "spawn.stdout.log").read_bytes()
    spawn_stderr = (root / "spawn.stderr.log").read_bytes()
    partial = _capture(module, root, "partial", ((sys.executable, "-c", _PARTIAL),))[0]
    inherited = _capture(
        module, root, "inherited", ((sys.executable, "-c", _INHERITED),)
    )[0]
    mutation = _capture(
        module,
        root,
        "mutation",
        ((sys.executable, "-c", _PARTIAL),),
        mutate=True,
    )[2]
    if (
        spawn != (127,)
        or spawn_stdout
        or not spawn_stderr.startswith(
            f"Could not execute {missing[0]}: ".encode("utf-8")
        )
        or not spawn_stderr.endswith(b"\n")
        or partial != (7,)
        or inherited != (0,)
        or (root / "partial.stdout.log").read_bytes() != b"partial-stdout\x00\xff"
        or (root / "partial.stderr.log").read_bytes() != b"partial-stderr\xfe\x00"
        or (root / "inherited.stdout.log").read_bytes() != b"parent-stdout|child-stdout"
        or (root / "inherited.stderr.log").read_bytes() != b"parent-stderr|child-stderr"
        or not mutation
    ):
        raise TaskLogCaseError("task-log capture diagnostics differ")
    return {
        "spawn_127": {
            "stdout_sha256": hashlib.sha256(spawn_stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(spawn_stderr).hexdigest(),
            "stderr_size_bytes": len(spawn_stderr),
        },
        "partial_streams": True,
        "inherited_writer": True,
        "mutation_detected": True,
    }


def _inspection_reference(
    module: ModuleType, path: Path, root: Path, label: str
) -> dict[str, str]:
    if hasattr(module, "_stable_file_reference"):
        return module._stable_file_reference(path, root, label)  # noqa: SLF001
    data = module._read_bytes(path, root, label)  # noqa: SLF001
    return module._reference_for_bytes(path, root, data)  # noqa: SLF001


def _inspection_diagnostics(module: ModuleType, trial: Path) -> Mapping[str, Any]:
    root = trial / "inspection-diagnostics"
    root.mkdir(mode=0o700)
    target = trial / "task.stdout.log"
    symlink = root / "symlink.log"
    symlink.symlink_to(target)
    rejected = []
    for path, admitted_root in ((target, root), (symlink, trial)):
        try:
            _inspection_reference(module, path, admitted_root, "diagnostic log")
        except module.InspectionError:
            rejected.append(True)
    if rejected != [True, True]:
        raise TaskLogCaseError("task-log inspection diagnostics differ")
    return {"outside_root_rejected": True, "symlink_rejected": True}


def produce(trial: Path, source: Path, case: str, value: int) -> None:
    identity = _declared_identity(trial, case, value)
    if case == CAPTURE:
        module = _source_module(source, "emrys.orchestration.local_pilot.task")
        exits, references, _detected = _capture(
            module, trial, "task", _emitter_commands(trial, value)
        )
        if exits != (0, 0, 0):
            raise TaskLogCaseError(f"task-log emitter exits differ: {exits}")
        diagnostics = (
            _capture_diagnostics(module, trial)
            if value == VALUES[0]
            else {"covered_at_value_mib": VALUES[0]}
        )
    elif case == INSPECTION:
        module = _source_module(source, "emrys.orchestration.local_pilot.inspection")
        references = (
            _inspection_reference(
                module, trial / "task.stdout.log", trial, "task stdout log"
            ),
            _inspection_reference(
                module, trial / "task.stderr.log", trial, "task stderr log"
            ),
        )
        diagnostics = (
            _inspection_diagnostics(module, trial)
            if value == VALUES[0]
            else {"covered_at_value_mib": VALUES[0]}
        )
    else:
        raise TaskLogCaseError(f"unknown task-log benchmark case: {case}")
    _write_json(
        trial / "task-log-result.json",
        {
            "schema_version": SCHEMA,
            "case": case,
            "value_mib": value,
            "references": list(references),
            "diagnostics": diagnostics,
            "measurement_boundary": MEASUREMENT_BOUNDARY,
            "expected": {
                "stdout_sha256": identity["stdout_sha256"],
                "stderr_sha256": identity["stderr_sha256"],
            },
        },
    )


def _equal(left: Path, right: Path) -> bool:
    with left.open("rb") as observed, right.open("rb") as expected:
        while True:
            left_block, right_block = observed.read(MIB), expected.read(MIB)
            if left_block != right_block:
                return False
            if not left_block:
                return True


def _cleanup_successful_trial(trial: Path) -> None:
    for path in (
        trial / "task.stdout.log",
        trial / "task.stderr.log",
        trial / "task-log-result.json",
    ):
        path.unlink()
    for path in (
        trial / "task-log-fixture",
        trial / "diagnostics",
        trial / "inspection-diagnostics",
    ):
        if path.is_symlink():
            path.unlink()
        elif path.exists():
            shutil.rmtree(path)


def validate(trial: Path, case: str, value: int) -> None:
    identity = _identity(trial, case, value)
    _root, stdout_fixture, stderr_fixture = _fixture(trial)
    stdout_log, stderr_log = trial / "task.stdout.log", trial / "task.stderr.log"
    result = _load_json(trial / "task-log-result.json")
    expected_references = [
        {"path": "task.stdout.log", "sha256": identity["stdout_sha256"]},
        {"path": "task.stderr.log", "sha256": identity["stderr_sha256"]},
    ]
    if (
        not _equal(stdout_log, stdout_fixture)
        or not _equal(stderr_log, stderr_fixture)
        or set(result)
        != {
            "schema_version",
            "case",
            "value_mib",
            "references",
            "diagnostics",
            "expected",
            "measurement_boundary",
        }
        or result.get("schema_version") != SCHEMA
        or result.get("case") != case
        or result.get("value_mib") != value
        or result.get("references") != expected_references
        or not isinstance(result.get("diagnostics"), Mapping)
        or result.get("expected")
        != {
            "stdout_sha256": identity["stdout_sha256"],
            "stderr_sha256": identity["stderr_sha256"],
        }
        or result.get("measurement_boundary") != MEASUREMENT_BOUNDARY
    ):
        raise TaskLogCaseError("task-log bytes, stream order, or references differ")
    _write_json(
        trial / "parity.bin",
        {
            "schema_version": SCHEMA,
            "case": case,
            "value_mib": value,
            "stdout_size_bytes": identity["stdout_size_bytes"],
            "stderr_size_bytes": identity["stderr_size_bytes"],
            "stdout_sha256": identity["stdout_sha256"],
            "stderr_sha256": identity["stderr_sha256"],
            "diagnostics": result["diagnostics"],
            "measurement_boundary": MEASUREMENT_BOUNDARY,
        },
    )
    _cleanup_successful_trial(trial)
