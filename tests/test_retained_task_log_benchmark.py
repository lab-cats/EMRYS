"""Focused end-to-end checks for retained task-log benchmark cases."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import mock

from emrys.orchestration.local_pilot import inspection, task

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests/tools/retained_stage_benchmark.py"


def _load_harness() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "retained_task_log_benchmark_harness", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


HARNESS = _load_harness()
CASES = HARNESS._task_log_case_module()


def _phase(
    operation: str,
    *,
    context: Path,
    case: str,
    trial: Path,
    variant: str | None = None,
) -> int:
    return HARNESS._internal(
        argparse.Namespace(
            operation=operation,
            context=context,
            case=case,
            value=1,
            variant=variant,
            trial_dir=trial,
        )
    )


class RetainedTaskLogBenchmarkTests(unittest.TestCase):
    def test_fresh_subprocess_loads_the_modular_case(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            trial = root / "trial"
            trial.mkdir()
            context = root / "context.json"
            context.write_text(
                json.dumps({"sources": {"master": str(ROOT), "head": str(ROOT)}}),
                encoding="utf-8",
            )
            completed = subprocess.run(
                (
                    sys.executable,
                    str(SCRIPT),
                    "_setup",
                    "--context",
                    str(context),
                    "--case",
                    CASES.CAPTURE,
                    "--value",
                    "1",
                    "--trial-dir",
                    str(trial),
                ),
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((trial / "task-log-fixture/identity.json").is_file())

    def test_old_and_new_private_adapters_preserve_the_same_evidence(self) -> None:
        def run_buffered(
            argv: tuple[str, ...], cwd: Path, _environment: object
        ) -> SimpleNamespace:
            completed = subprocess.run(argv, cwd=cwd, capture_output=True, check=False)
            return SimpleNamespace(
                exit_code=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )

        def reference(path: Path, root: Path) -> dict[str, str]:
            return {
                "path": path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }

        legacy = SimpleNamespace(
            _default_run_command=run_buffered,
            _publish_bytes=lambda path, data: path.write_bytes(data),
            _record_reference=reference,
        )
        command = (
            sys.executable,
            "-c",
            "import os; os.write(1,b'opaque\\x00\\xff'); os.write(2,b'error\\xfe')",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            old_root, new_root = root / "old", root / "new"
            old_root.mkdir()
            new_root.mkdir()
            old = CASES._capture(legacy, old_root, "task", (command,))
            new = CASES._capture(task, new_root, "task", (command,))
            self.assertEqual(old[:2], new[:2])
            for name in ("task.stdout.log", "task.stderr.log"):
                self.assertEqual(
                    (old_root / name).read_bytes(), (new_root / name).read_bytes()
                )

            payload = b"inspection\x00\xff"
            for selected in (old_root, new_root):
                (selected / "inspect.log").write_bytes(payload)
            old_inspection = SimpleNamespace(
                _read_bytes=lambda path, _root, _label: path.read_bytes(),
                _reference_for_bytes=lambda path, selected_root, data: {
                    "path": path.relative_to(selected_root).as_posix(),
                    "sha256": hashlib.sha256(data).hexdigest(),
                },
            )
            self.assertEqual(
                CASES._inspection_reference(
                    old_inspection,
                    old_root / "inspect.log",
                    old_root,
                    "old inspection",
                ),
                CASES._inspection_reference(
                    inspection,
                    new_root / "inspect.log",
                    new_root,
                    "new inspection",
                ),
            )

    def test_archived_imports_and_production_call_sites_are_source_bound(self) -> None:
        for name, path in (
            (
                "emrys.orchestration.local_pilot.task",
                ROOT / "src/emrys/orchestration/local_pilot/task.py",
            ),
            (
                "emrys.orchestration.local_pilot.inspection",
                ROOT / "src/emrys/orchestration/local_pilot/inspection.py",
            ),
        ):
            with self.subTest(module=name):
                selected = CASES._source_module(ROOT, name)
                self.assertEqual(Path(selected.__file__).resolve(), path)
        with tempfile.TemporaryDirectory() as directory:
            foreign = Path(directory).resolve()
            foreign_task = foreign / "src/emrys/orchestration/local_pilot/task.py"
            foreign_task.parent.mkdir(parents=True)
            foreign_task.write_text("# foreign source fixture\n", encoding="utf-8")
            with (
                mock.patch.object(CASES.importlib, "import_module", return_value=task),
                self.assertRaisesRegex(
                    CASES.TaskLogCaseError,
                    "outside the selected archived source",
                ),
            ):
                CASES._source_module(foreign, "emrys.orchestration.local_pilot.task")

        # Full behavior is exercised by the focused task/lifecycle owner tests;
        # these assertions keep the timed private helpers attached to those paths.
        task_source = inspect.getsource(task.run_task)
        self.assertIn("streams = _TaskStreamCapture(", task_source)
        self.assertIn("streams=streams", task_source)
        self.assertIn("_publish_attempt(", task_source)
        inspection_source = inspect.getsource(inspection.inspect_attempt_task_trees)
        self.assertIn("_stable_file_reference(", inspection_source)
        self.assertNotIn("log_data = _read_bytes", inspection_source)
        self.assertIn(
            "private task-log capture/hash hot path", CASES.MEASUREMENT_BOUNDARY
        )

    def test_success_cleans_bulk_state_but_tamper_retains_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            context = root / "context.json"
            context.write_text(
                json.dumps({"sources": {"master": str(ROOT), "head": str(ROOT)}}),
                encoding="utf-8",
            )
            for case in CASES.CASES:
                with self.subTest(case=case):
                    success = root / f"{case}-success"
                    success.mkdir()
                    self.assertEqual(
                        _phase("_setup", context=context, case=case, trial=success),
                        0,
                    )
                    self.assertEqual(
                        _phase(
                            "_produce",
                            context=context,
                            case=case,
                            trial=success,
                            variant="head",
                        ),
                        0,
                    )
                    self.assertEqual(
                        _phase("_validate", context=context, case=case, trial=success),
                        0,
                    )
                    parity = json.loads((success / "parity.bin").read_text())
                    self.assertEqual(parity["case"], case)
                    self.assertEqual(
                        parity["stdout_size_bytes"] + parity["stderr_size_bytes"],
                        1024 * 1024,
                    )
                    if case == CASES.CAPTURE:
                        spawn = parity["diagnostics"]["spawn_127"]
                        self.assertEqual(len(spawn["stdout_sha256"]), 64)
                        self.assertEqual(len(spawn["stderr_sha256"]), 64)
                        self.assertGreater(spawn["stderr_size_bytes"], 0)
                    for name in (
                        "task-log-fixture",
                        "task.stdout.log",
                        "task.stderr.log",
                        "task-log-result.json",
                        "diagnostics",
                        "inspection-diagnostics",
                    ):
                        self.assertFalse((success / name).exists())

                    tampered = root / f"{case}-tampered"
                    tampered.mkdir()
                    _phase("_setup", context=context, case=case, trial=tampered)
                    _phase(
                        "_produce",
                        context=context,
                        case=case,
                        trial=tampered,
                        variant="head",
                    )
                    with (tampered / "task.stdout.log").open("ab") as stream:
                        stream.write(b"tamper")
                    with self.assertRaisesRegex(
                        HARNESS.BenchmarkSetupError,
                        "task-log bytes, stream order, or references differ",
                    ):
                        _phase(
                            "_validate",
                            context=context,
                            case=case,
                            trial=tampered,
                        )
                    self.assertFalse((tampered / "parity.bin").exists())
                    for name in (
                        "task-log-fixture",
                        "task.stdout.log",
                        "task.stderr.log",
                        "task-log-result.json",
                    ):
                        self.assertTrue((tampered / name).exists())


if __name__ == "__main__":
    unittest.main()
