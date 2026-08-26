"""End-to-end contract for the modular strict-TSV benchmark case."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests/tools/retained_stage_benchmark.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("retained_stage_benchmark", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BENCHMARK = _load_script()
CASE = BENCHMARK.STRICT_TSV_CASE


def _run(operation: str, context: Path, trial: Path) -> None:
    command = [
        sys.executable,
        "-X",
        "pycache_prefix=/dev/null",
        str(SCRIPT),
        operation,
        "--context",
        str(context),
        "--case",
        CASE.CASE_NAME,
        "--value",
        "1000001",
    ]
    if operation == "_produce":
        command.extend(("--variant", "head"))
    command.extend(("--trial-dir", str(trial)))
    completed = subprocess.run(
        command,
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_exact_oracle_diagnostics_and_tamper_rejection() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        trial = root / "results/trials" / CASE.CASE_NAME / "1000001/rep-01/head"
        trial.mkdir(parents=True)
        context = root / "context.json"
        context.write_text(
            json.dumps({"sources": {"master": str(ROOT), "head": str(ROOT)}}) + "\n",
            encoding="utf-8",
        )

        for operation in ("_setup", "_produce", "_validate"):
            _run(operation, context, trial)

        fixture = root / "results/fixtures" / CASE.CASE_NAME / "1000001"
        marker = json.loads((fixture / "fixture.json").read_text(encoding="utf-8"))
        observation = json.loads(
            (trial / "observation.json").read_text(encoding="utf-8")
        )
        parity = json.loads((trial / "parity.bin").read_text(encoding="utf-8"))
        assert marker["row_count"] == 10_000
        assert marker["column_count"] == 25
        assert [probe["row_index"] for probe in marker["probes"]] == [0, 5_000, 9_999]
        assert observation == CASE._expected_observation(marker)
        assert [entry["name"] for entry in observation["diagnostics"]] == [
            name for name, _data, _header in CASE.DIAGNOSTICS
        ]
        assert parity == {
            "schema_version": CASE.PARITY_SCHEMA,
            "observation": observation,
        }

        observation["ordered_cell_sha256"] = "0" * 64
        (trial / "observation.json").write_text(
            json.dumps(observation) + "\n", encoding="utf-8"
        )
        with pytest.raises(CASE.StrictTsvBenchmarkError, match="observation differs"):
            CASE.validate(trial, fixture, CASE.CASE_NAME, 1_000_001)
