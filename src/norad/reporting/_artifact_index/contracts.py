"""Exact-file contract owners used by artifact-index reporting."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ARTIFACT_CONTRACTS_MODULE_NAME = "_norad_artifact_contracts"
_ARTIFACT_CONTRACTS_MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "src"
    / "norad"
    / "contracts"
    / "artifacts"
    / "validate_artifact_contracts.py"
).resolve(strict=False)
_ARTIFACT_CONTRACTS_READY_ATTRIBUTE = "_NORAD_ARTIFACT_CONTRACTS_READY"


def _validated_artifact_contracts(module: object) -> object:
    try:
        module_path = Path(getattr(module, "__file__")).resolve(strict=False)
    except (OSError, TypeError) as exc:
        raise ImportError(
            "cached artifact-contract owner has no valid file path"
        ) from exc
    if module_path != _ARTIFACT_CONTRACTS_MODULE_PATH:
        raise ImportError(
            f"cached artifact-contract owner resolves to {module_path}, "
            f"expected {_ARTIFACT_CONTRACTS_MODULE_PATH}"
        )
    if getattr(module, _ARTIFACT_CONTRACTS_READY_ATTRIBUTE, False) is not True:
        raise ImportError("cached artifact-contract owner is partially initialized")
    return module


def _load_artifact_contracts() -> object:
    cached = sys.modules.get(_ARTIFACT_CONTRACTS_MODULE_NAME)
    if cached is not None:
        return _validated_artifact_contracts(cached)
    spec = importlib.util.spec_from_file_location(
        _ARTIFACT_CONTRACTS_MODULE_NAME,
        _ARTIFACT_CONTRACTS_MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            "unable to create an exact-file artifact-contract module specification"
        )
    module = importlib.util.module_from_spec(spec)
    existing = sys.modules.setdefault(_ARTIFACT_CONTRACTS_MODULE_NAME, module)
    if existing is not module:
        return _validated_artifact_contracts(existing)
    try:
        spec.loader.exec_module(module)
        setattr(module, _ARTIFACT_CONTRACTS_READY_ATTRIBUTE, True)
        _validated_artifact_contracts(module)
    except BaseException:
        if sys.modules.get(_ARTIFACT_CONTRACTS_MODULE_NAME) is module:
            del sys.modules[_ARTIFACT_CONTRACTS_MODULE_NAME]
        raise
    return module


contracts = _load_artifact_contracts()


_STEP08_MODULE_NAME = "_norad_step08_scientific_evidence_contract"
_STEP08_MODULE_PATH = (
    Path(__file__).resolve().parents[4]
    / "src"
    / "norad"
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
    Path(__file__).resolve().parents[4]
    / "src"
    / "norad"
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
            "Step 09 contract and artifact indexing resolved different Step 08 "
            "objects"
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
    Path(__file__).resolve().parents[4]
    / "src"
    / "norad"
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
            "cached review-package scientific-evidence contract has no valid file path"
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
