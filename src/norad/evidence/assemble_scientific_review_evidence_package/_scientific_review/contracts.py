"""Exact neutral contract owners and retained Step 09c constants."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_STEP08_MODULE_NAME = "_norad_step08_scientific_evidence_contract"
_STEP08_MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "contracts"
    / "scientific_evidence"
    / "step08.py"
).resolve(strict=False)
_STEP08_READY_ATTRIBUTE = "_NORAD_STEP08_CONTRACT_READY"


def _validated_step08_contract(module: object) -> object:
    try:
        module_path = Path(getattr(module, "__file__")).resolve(strict=False)
    except (OSError, TypeError) as exc:
        raise ImportError(
            "cached Step 08 scientific-evidence contract has no valid file path"
        ) from exc
    if module_path != _STEP08_MODULE_PATH:
        raise ImportError(
            "cached Step 08 scientific-evidence contract resolves to "
            f"{module_path}, expected {_STEP08_MODULE_PATH}"
        )
    if getattr(module, _STEP08_READY_ATTRIBUTE, False) is not True:
        raise ImportError(
            "cached Step 08 scientific-evidence contract is partially initialized"
        )
    return module


def _load_step08_contract() -> object:
    cached = sys.modules.get(_STEP08_MODULE_NAME)
    if cached is not None:
        return _validated_step08_contract(cached)
    spec = importlib.util.spec_from_file_location(
        _STEP08_MODULE_NAME, _STEP08_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            "unable to create an exact-file Step 08 module specification"
        )
    module = importlib.util.module_from_spec(spec)
    existing = sys.modules.setdefault(_STEP08_MODULE_NAME, module)
    if existing is not module:
        return _validated_step08_contract(existing)
    try:
        spec.loader.exec_module(module)
        setattr(module, _STEP08_READY_ATTRIBUTE, True)
        _validated_step08_contract(module)
    except BaseException:
        if sys.modules.get(_STEP08_MODULE_NAME) is module:
            del sys.modules[_STEP08_MODULE_NAME]
        raise
    return module


try:
    step08 = _load_step08_contract()
except Exception as exc:
    reason = " ".join(str(exc).replace("\x00", "").split()) or "no detail"
    print(
        "ERROR: unable to load Step 08 scientific-evidence contract at "
        f"{_STEP08_MODULE_PATH}: {type(exc).__name__}: {reason}",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


_STEP09_MODULE_NAME = "_norad_step09_scientific_evidence_contract"
_STEP09_MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "contracts"
    / "scientific_evidence"
    / "step09.py"
).resolve(strict=False)
_STEP09_READY_ATTRIBUTE = "_NORAD_STEP09_CONTRACT_READY"


def _validated_step09_contract(module: object) -> object:
    try:
        module_path = Path(getattr(module, "__file__")).resolve(strict=False)
    except (OSError, TypeError) as exc:
        raise ImportError(
            "cached Step 09 scientific-evidence contract has no valid file path"
        ) from exc
    if module_path != _STEP09_MODULE_PATH:
        raise ImportError(
            "cached Step 09 scientific-evidence contract resolves to "
            f"{module_path}, expected {_STEP09_MODULE_PATH}"
        )
    if getattr(module, _STEP09_READY_ATTRIBUTE, False) is not True:
        raise ImportError(
            "cached Step 09 scientific-evidence contract is partially initialized"
        )
    return module


def _load_step09_contract() -> object:
    cached = sys.modules.get(_STEP09_MODULE_NAME)
    if cached is not None:
        return _validated_step09_contract(cached)
    spec = importlib.util.spec_from_file_location(
        _STEP09_MODULE_NAME, _STEP09_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            "unable to create an exact-file Step 09 module specification"
        )
    module = importlib.util.module_from_spec(spec)
    existing = sys.modules.setdefault(_STEP09_MODULE_NAME, module)
    if existing is not module:
        return _validated_step09_contract(existing)
    try:
        spec.loader.exec_module(module)
        setattr(module, _STEP09_READY_ATTRIBUTE, True)
        _validated_step09_contract(module)
    except BaseException:
        if sys.modules.get(_STEP09_MODULE_NAME) is module:
            del sys.modules[_STEP09_MODULE_NAME]
        raise
    return module


try:
    step09 = _load_step09_contract()
    if step09.step08 is not step08:
        raise ImportError(
            "Step 09c and Step 09 resolved different Step 08 contract objects"
        )
    if (
        step09.ContractError is not step08.ContractError
        or step09.Table is not step08.Table
    ):
        raise ImportError("Step 09 contract resolved different shared identities")
except Exception as exc:
    reason = " ".join(str(exc).replace("\x00", "").split()) or "no detail"
    print(
        "ERROR: unable to load Step 09 scientific-evidence contract at "
        f"{_STEP09_MODULE_PATH}: {type(exc).__name__}: {reason}",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


_REVIEW_PACKAGE_MODULE_NAME = "_norad_review_package_scientific_evidence_contract"
_REVIEW_PACKAGE_MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "contracts"
    / "scientific_evidence"
    / "review_package.py"
).resolve(strict=False)
_REVIEW_PACKAGE_READY_ATTRIBUTE = "_NORAD_REVIEW_PACKAGE_CONTRACT_READY"


def _validated_review_package_contract(module: object) -> object:
    try:
        module_path = Path(getattr(module, "__file__")).resolve(strict=False)
    except (OSError, TypeError) as exc:
        raise ImportError(
            "cached review-package scientific-evidence contract has no valid "
            "file path"
        ) from exc
    if module_path != _REVIEW_PACKAGE_MODULE_PATH:
        raise ImportError(
            "cached review-package scientific-evidence contract resolves to "
            f"{module_path}, expected {_REVIEW_PACKAGE_MODULE_PATH}"
        )
    if getattr(module, _REVIEW_PACKAGE_READY_ATTRIBUTE, False) is not True:
        raise ImportError(
            "cached review-package scientific-evidence contract is partially "
            "initialized"
        )
    return module


def _load_review_package_contract() -> object:
    cached = sys.modules.get(_REVIEW_PACKAGE_MODULE_NAME)
    if cached is not None:
        return _validated_review_package_contract(cached)
    spec = importlib.util.spec_from_file_location(
        _REVIEW_PACKAGE_MODULE_NAME, _REVIEW_PACKAGE_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            "unable to create an exact-file review-package module specification"
        )
    module = importlib.util.module_from_spec(spec)
    existing = sys.modules.setdefault(_REVIEW_PACKAGE_MODULE_NAME, module)
    if existing is not module:
        return _validated_review_package_contract(existing)
    try:
        spec.loader.exec_module(module)
        setattr(module, _REVIEW_PACKAGE_READY_ATTRIBUTE, True)
        _validated_review_package_contract(module)
    except BaseException:
        if sys.modules.get(_REVIEW_PACKAGE_MODULE_NAME) is module:
            del sys.modules[_REVIEW_PACKAGE_MODULE_NAME]
        raise
    return module


try:
    review_package = _load_review_package_contract()
except Exception as exc:
    reason = " ".join(str(exc).replace("\x00", "").split()) or "no detail"
    print(
        "ERROR: unable to load review-package scientific-evidence contract at "
        f"{_REVIEW_PACKAGE_MODULE_PATH}: {type(exc).__name__}: {reason}",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


ContractError = step08.ContractError
NA_VALUE = step08.NA_VALUE
COMPUTATIONAL_SCOPE_ROLES = {
    "local_fixture_tests": "local_test",
    "local_test": "local_test",
    "runtime_validation": "runtime_output",
    "runtime_log": "runtime_log",
    "runtime_output": "runtime_output",
    "cluster_dry_run": "cluster_dry_run",
    "cluster_proof": "cluster_output",
    "cluster_scheduler": "cluster_scheduler",
    "cluster_log": "cluster_log",
    "cluster_output": "cluster_output",
}
COMPUTATIONAL_SCOPE_PLAN_FIELDS = {
    "local_fixture_tests": "local_test_status",
    "local_test": "local_test_status",
    "runtime_validation": "runtime_validation_status",
    "runtime_log": "runtime_validation_status",
    "runtime_output": "runtime_validation_status",
    "cluster_dry_run": "cluster_dry_run_status",
    "cluster_proof": "cluster_proof_status",
    "cluster_scheduler": "cluster_proof_status",
    "cluster_log": "cluster_proof_status",
    "cluster_output": "cluster_proof_status",
}

EVIDENCE_MANIFEST_HEADER = (
    "evidence_id",
    "evidence_category",
    "analysis_id",
    "source_path",
    "source_sha256",
    "source_row_count",
    "evidence_status",
    "not_applicable_reason",
    "reviewer",
    "owner",
    "evidence_date",
    "policy_version",
)

COMPUTATIONAL_VALIDATION_HEADER = (
    "review_id",
    "evidence_id",
    "analysis_id",
    "validation_scope",
    "validation_status",
    "evidence_path",
    "evidence_sha256",
    "scheduler_state",
    "exit_code",
    "reviewer",
    "evidence_date",
    "notes",
)

COMPUTATIONAL_VALIDATION_STATUSES = (
    "not_run",
    "blocked",
    "passed",
    "failed",
    "proven",
)


Table = step08.Table
values_close = step08.values_close
sha256_file = step08.sha256_file
read_tsv = step08.read_tsv
resolve_recorded_path = step09.resolve_recorded_path
