from __future__ import annotations

import importlib.util
import inspect
import sys
import types
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "src/norad/libraries/bam_validation.py"
BAM_MODULE_NAME = "_norad_bam_validation"
REPORT_MODULE_NAME = "_norad_validation_report"


@dataclass(frozen=True)
class Caller:
    name: str
    source: Path


CALLERS = (
    Caller(
        "step02",
        ROOT
        / "src/norad/stages/construct_canonical_BAM/validate_step_02_canonical_bam.py",
    ),
    Caller(
        "step04",
        ROOT
        / "src/norad/stages/mark_BAM_duplicates_with_Picard/"
        "validate_step_04_mark_duplicates.py",
    ),
    Caller("step05", ROOT / "scripts/validate_step_05_split_ncigar.py"),
)


@contextmanager
def isolated_module_cache():
    names = (BAM_MODULE_NAME, REPORT_MODULE_NAME, "reference_provenance")
    missing = object()
    previous = {name: sys.modules.get(name, missing) for name in names}
    for name in names:
        sys.modules.pop(name, None)
    try:
        yield
    finally:
        for name in names:
            sys.modules.pop(name, None)
            if previous[name] is not missing:
                sys.modules[name] = previous[name]


def exact_load(path: Path, module_name: str) -> object:
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_caller(caller: Caller) -> object:
    if caller.name == "step05":
        sys.modules["reference_provenance"] = types.ModuleType(
            "reference_provenance"
        )
    return exact_load(caller.source, f"_mig03f_{caller.name}_{id(caller)}")


def assert_loader_failure(
    caller: Caller,
    capsys: pytest.CaptureFixture[str],
    expected_type: str,
    expected_reason: str,
) -> None:
    path_before = list(sys.path)
    cwd_before = sorted(path.name for path in Path.cwd().iterdir())
    with pytest.raises(SystemExit) as raised:
        load_caller(caller)
    assert raised.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "ERROR: unable to load NORAD BAM-validation owner at "
        f"{HELPER}: {expected_type}: {expected_reason}\n"
    )
    assert sys.path == path_before
    assert sorted(path.name for path in Path.cwd().iterdir()) == cwd_before


class FailingLoader:
    def __init__(self, error: Exception):
        self.error = error

    def create_module(self, spec: object) -> None:
        return None

    def exec_module(self, module: object) -> None:
        raise self.error


def inject_bam_loader_failure(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    original = importlib.util.spec_from_file_location

    def controlled_spec(
        module_name: str, path: object, *args: object, **kwargs: object
    ):
        if module_name == BAM_MODULE_NAME:
            return importlib.util.spec_from_loader(module_name, FailingLoader(error))
        return original(module_name, path, *args, **kwargs)

    monkeypatch.setattr(importlib.util, "spec_from_file_location", controlled_spec)


def inject_bam_spec_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    original = importlib.util.spec_from_file_location

    def controlled_spec(
        module_name: str, path: object, *args: object, **kwargs: object
    ):
        if module_name == BAM_MODULE_NAME:
            return None
        return original(module_name, path, *args, **kwargs)

    monkeypatch.setattr(importlib.util, "spec_from_file_location", controlled_spec)


def test_helper_preserves_old_result_and_header_contract():
    module = exact_load(HELPER, "_mig03f_bam_helper_contract")
    functions = {
        name
        for name, value in vars(module).items()
        if inspect.isfunction(value) and value.__module__ == module.__name__
    }
    assert functions == {"run_tool", "parse_header"}
    assert module._NORAD_BAM_VALIDATION_READY is True

    completed = module.run_tool(
        Path("/bin/sh"),
        "-c",
        "printf 'probe-out\\n'; printf 'probe-err\\n' >&2; exit 7",
    )
    assert completed.args == [
        "/bin/sh",
        "-c",
        "printf 'probe-out\\n'; printf 'probe-err\\n' >&2; exit 7",
    ]
    assert completed.returncode == 7
    assert completed.stdout == "probe-out\n"
    assert completed.stderr == "probe-err\n"
    with pytest.raises(FileNotFoundError) as raised:
        module.run_tool(Path("/definitely/missing/mig03f-tool"), "--probe")
    assert raised.value.errno == 2

    assert module.parse_header(
        "@HD\tVN:1.6\tSO:coordinate\n@RG\tID:S\tSM:S\n", "S"
    ) == (True, True, "HD=1 RG=1")
    assert module.parse_header("", "S") == (False, False, "HD=0 RG=0")
    assert module.parse_header(
        "@HD\tSO:coordinate\n@HD\tSO:coordinate\n"
        "@RG\tID:S\tSM:S\n@RG\tID:S\tSM:S\n",
        "S",
    ) == (False, False, "HD=2 RG=2")
    assert module.parse_header(
        "@HD\tSO:coordinate\n@RG\tID:wrong\tSM:S\n", "S"
    ) == (True, False, "HD=1 RG=1")


@pytest.mark.parametrize("caller", CALLERS, ids=lambda caller: caller.name)
@pytest.mark.parametrize("preloaded", (False, True), ids=("owned", "cached"))
def test_each_caller_loads_and_reuses_the_exact_helper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caller: Caller,
    preloaded: bool,
):
    monkeypatch.chdir(tmp_path)
    path_before = list(sys.path)
    with isolated_module_cache():
        expected = None
        if preloaded:
            expected = exact_load(HELPER, BAM_MODULE_NAME)
            sys.modules[BAM_MODULE_NAME] = expected
        module = load_caller(caller)
        helper = module.bam_report
        if expected is not None:
            assert helper is expected
        assert sys.modules[BAM_MODULE_NAME] is helper
        assert Path(helper.__file__).resolve() == HELPER.resolve()
    assert sys.path == path_before
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("caller", CALLERS, ids=lambda caller: caller.name)
def test_each_caller_missing_helper_fails_closed_and_removes_owned_partial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caller: Caller,
):
    monkeypatch.chdir(tmp_path)
    missing = FileNotFoundError(2, "No such file or directory", str(HELPER))
    inject_bam_loader_failure(monkeypatch, missing)
    with isolated_module_cache():
        assert_loader_failure(
            caller,
            capsys,
            "FileNotFoundError",
            f"[Errno 2] No such file or directory: '{HELPER}'",
        )
        assert BAM_MODULE_NAME not in sys.modules


@pytest.mark.parametrize("caller", CALLERS, ids=lambda caller: caller.name)
def test_each_caller_preserves_foreign_wrong_path_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caller: Caller,
):
    monkeypatch.chdir(tmp_path)
    foreign_path = tmp_path / "foreign/bam_validation.py"
    foreign = types.ModuleType(BAM_MODULE_NAME)
    foreign.__file__ = str(foreign_path)
    foreign._NORAD_BAM_VALIDATION_READY = True
    foreign.run_tool = lambda *args: None
    foreign.parse_header = lambda *args: None
    with isolated_module_cache():
        sys.modules[BAM_MODULE_NAME] = foreign
        assert_loader_failure(
            caller,
            capsys,
            "ImportError",
            "cached BAM-validation owner resolves to "
            f"{foreign_path}, expected {HELPER}",
        )
        assert sys.modules[BAM_MODULE_NAME] is foreign


@pytest.mark.parametrize("caller", CALLERS, ids=lambda caller: caller.name)
def test_each_caller_preserves_cache_without_file_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caller: Caller,
):
    monkeypatch.chdir(tmp_path)
    foreign = types.ModuleType(BAM_MODULE_NAME)
    with isolated_module_cache():
        sys.modules[BAM_MODULE_NAME] = foreign
        assert_loader_failure(
            caller,
            capsys,
            "ImportError",
            "cached BAM-validation owner has no valid file path",
        )
        assert sys.modules[BAM_MODULE_NAME] is foreign


def test_step05_fails_closed_when_exact_file_spec_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.chdir(tmp_path)
    inject_bam_spec_failure(monkeypatch)
    with isolated_module_cache():
        assert_loader_failure(
            CALLERS[2],
            capsys,
            "ImportError",
            "unable to create an exact-file module specification",
        )
        assert BAM_MODULE_NAME not in sys.modules


@pytest.mark.parametrize("caller", CALLERS, ids=lambda caller: caller.name)
@pytest.mark.parametrize("state", ("not_ready", "missing_api", "noncallable"))
def test_each_caller_preserves_correct_path_incomplete_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caller: Caller,
    state: str,
):
    monkeypatch.chdir(tmp_path)
    partial = types.ModuleType(BAM_MODULE_NAME)
    partial.__file__ = str(HELPER)
    partial._NORAD_BAM_VALIDATION_READY = state != "not_ready"
    partial.run_tool = None if state == "noncallable" else lambda *args: None
    if state != "missing_api":
        partial.parse_header = lambda *args: None
    expected_reason = {
        "not_ready": "cached BAM-validation owner is partially initialized",
        "missing_api": "cached BAM-validation owner has incomplete API: parse_header",
        "noncallable": "cached BAM-validation owner has incomplete API: run_tool",
    }[state]
    with isolated_module_cache():
        sys.modules[BAM_MODULE_NAME] = partial
        assert_loader_failure(caller, capsys, "ImportError", expected_reason)
        assert sys.modules[BAM_MODULE_NAME] is partial


@pytest.mark.parametrize("caller", CALLERS, ids=lambda caller: caller.name)
def test_each_caller_owned_execution_failure_removes_only_owned_partial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caller: Caller,
):
    monkeypatch.chdir(tmp_path)
    inject_bam_loader_failure(monkeypatch, RuntimeError("owned boom"))
    with isolated_module_cache():
        assert_loader_failure(
            caller,
            capsys,
            "RuntimeError",
            "owned boom",
        )
        assert BAM_MODULE_NAME not in sys.modules
    assert list(tmp_path.iterdir()) == []
