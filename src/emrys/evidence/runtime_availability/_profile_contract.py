"""Read runtime path choices and derive the installed probe policy."""

from __future__ import annotations

import csv
import hashlib
import re
import json
import os
import stat
from dataclasses import dataclass, replace
from pathlib import Path

from emrys.contracts.orchestration import api as contracts
from emrys.libraries import validation as report
from emrys.libraries.validation.inputs import read_bytes_with_identity
from emrys.libraries.source_authority import controlled_python_argv

from ._runtime_model import RuntimeBinding, RuntimeCheck, VERSION_TEXT_LIMIT, _fail

CHOICE_IDS = (
    "bash",
    "python",
    "star",
    "samtools",
    "java",
    "gatk",
    "picard_jar",
    "bcftools",
    "infer_experiment",
    "gunzip",
    "rscript",
    "renv_library",
)


def load_runtime_policy() -> tuple[RuntimeCheck, ...]:
    """Read the fixed, installed policy; Projects cannot author probe rules."""

    path = Path(__file__).resolve().parents[2] / "resources/runtime/runtime_policy.tsv"
    return tuple(
        RuntimeCheck(
            row["check_id"],
            row["check_type"],
            row["target"],
            tuple(json.loads(row["probe_args"])),
            row["expected"],
        )
        for row in csv.DictReader(
            report.read_bytes(path, "Runtime policy").decode().splitlines(),
            delimiter="\t",
        )
    )


SHARED_PROFILE_HEADER = ("seal_path", "seal_sha256", "python")
SEAL_BYTE_LIMIT = 64 * 1024
PYTHON_CHECK_IDS = frozenset({"python", "snakemake", "sha256_python"})
UNSEALED_CHECK_IDS = PYTHON_CHECK_IDS | {"renv_project", "renv_library"}


@dataclass(frozen=True, slots=True)
class RuntimeSeal:
    path: Path
    data: bytes
    choices: tuple[tuple[str, str], ...]
    bindings: tuple[RuntimeBinding, ...]

    @property
    def managed_root(self) -> Path:
        return self.path.parent / "managed"


@dataclass(frozen=True, slots=True)
class SharedRuntimeSelection:
    seal_path: Path
    seal_sha256: str
    python: Path


def runtime_root_for_seal(path: Path) -> Path:
    """Return the owning Project runtime root for one supported seal path."""

    if not path.is_absolute() or path.name != "shared.json":
        _fail("Runtime seal must name an absolute shared.json")
    if path.parent.name == "runtime":
        return path.parent
    if (
        re.fullmatch(r"[0-9a-f]{32}", path.parent.name) is not None
        and path.parent.parent.name == "generations"
        and path.parent.parent.parent.name == "runtime"
    ):
        return path.parent.parent.parent
    _fail("Runtime seal must belong to a Project runtime or generation")


def shared_runtime_selection(data: bytes) -> SharedRuntimeSelection | None:
    """Admit a shared selector without requiring its referenced seal to exist."""

    header, rows = _profile_rows(data)
    if header != list(SHARED_PROFILE_HEADER):
        return None
    if len(rows) != 1 or set(rows[0]) != set(SHARED_PROFILE_HEADER):
        _fail("Shared runtime selection must contain exactly one closed row")
    selected = rows[0]
    if (
        not _absolute_choice(selected["seal_path"])
        or not _absolute_choice(selected["python"])
        or not isinstance(selected["seal_sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", selected["seal_sha256"]) is None
    ):
        _fail("Shared runtime selection has invalid paths or SHA-256")
    seal_path = Path(selected["seal_path"])
    runtime_root_for_seal(seal_path)
    return SharedRuntimeSelection(
        seal_path,
        selected["seal_sha256"],
        Path(selected["python"]),
    )


def _profile_rows(data: bytes) -> tuple[list[str] | None, list[dict[str, str]]]:
    try:
        reader = csv.DictReader(
            data.decode("utf-8").splitlines(), delimiter="\t", strict=True
        )
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        _fail(f"Runtime choices are not valid UTF-8 TSV: {exc}")
    return reader.fieldnames, rows


def _absolute_choice(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and Path(value).is_absolute()
        and not any(char in value for char in "\x00\n\r")
    )


def admit_runtime_seal(
    path: Path, data: bytes, *, require_content: bool = True
) -> RuntimeSeal:
    """Admit the same closed expected-content record before and after publication."""
    if len(data) > SEAL_BYTE_LIMIT:
        _fail("Runtime seal exceeds its byte limit")
    runtime_root_for_seal(path)
    if (
        path.parent.resolve(strict=True) != path.parent
        or path.parent.stat().st_uid != os.getuid()
    ):
        _fail("Runtime seal parent must be canonical and owned by this UID")
    managed = path.parent / "managed"
    if require_content and (
        not managed.is_dir()
        or managed.resolve(strict=True) != managed
        or managed.stat().st_uid != os.getuid()
    ):
        _fail("Sealed runtime root must be a canonical directory owned by this UID")
    try:
        value = contracts.load_json_object_bytes(data, "Runtime seal")
        if contracts.canonical_json_bytes(value) != data:
            _fail("Runtime seal must use canonical JSON")
    except contracts.ContractValidationError as exc:
        _fail(str(exc))
    if (
        set(value) != {"schema_version", "managed_root", "choices", "bindings"}
        or type(value["schema_version"]) is not int
        or value["schema_version"] != 1
        or value["managed_root"] != str(managed)
    ):
        _fail("Runtime seal has invalid fields or identity")
    choices = value["choices"]
    if (
        not isinstance(choices, dict)
        or set(choices) != set(CHOICE_IDS) - {"python"}
        or not all(_absolute_choice(item) for item in choices.values())
    ):
        _fail("Runtime seal must contain the exact native/R choice roster")
    for name, target in choices.items():
        selected = Path(target)
        if not selected.is_relative_to(managed) or (
            require_content
            and not selected.resolve(strict=True).is_relative_to(managed)
        ):
            _fail(f"Sealed runtime choice escaped the managed root: {name}")
    library = Path(choices["renv_library"])
    if require_content and (
        not library.is_dir() or library.resolve(strict=True) != library
    ):
        _fail("Sealed R library must be a canonical real directory")
    expected = tuple(
        check
        for check in load_runtime_policy()
        if check.check_id not in UNSEALED_CHECK_IDS
    )
    records = value["bindings"]
    fields = {
        "check_id",
        "path",
        "resolved_path",
        "sha256",
        "observed",
        "identity_kind",
    }
    if not isinstance(records, list) or len(records) != len(expected):
        _fail("Runtime seal has an incomplete binding roster")
    bindings = []
    for record, check in zip(records, expected, strict=True):
        kind = "package_tree" if check.check_type == "r_namespace" else "file"
        if (
            not isinstance(record, dict)
            or set(record) != fields
            or record["check_id"] != check.check_id
            or record["identity_kind"] != kind
            or not isinstance(record["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", record["sha256"]) is None
            or not isinstance(record["observed"], str)
            or not record["observed"]
            or any(char in record["observed"] for char in "\x00\n\r")
            or len(record["observed"]) > VERSION_TEXT_LIMIT
            or not all(
                _absolute_choice(record[key]) for key in ("path", "resolved_path")
            )
        ):
            _fail("Runtime seal has an invalid content binding")
        target, resolved = Path(record["path"]), Path(record["resolved_path"])
        if not target.is_relative_to(managed) or not resolved.is_relative_to(managed):
            _fail(f"Sealed runtime binding escaped the managed root: {check.check_id}")
        selected = (
            Path(choices["renv_library"]) / check.target
            if kind == "package_tree"
            else Path(choices["java" if check.check_id == "picard" else check.check_id])
        )
        expected_target = (
            selected.resolve(strict=True)
            if require_content and kind == "package_tree"
            else selected
        )
        if ((require_content or kind == "file") and target != expected_target) or (
            require_content and resolved != selected.resolve(strict=True)
        ):
            _fail(f"Sealed runtime binding path changed: {check.check_id}")
        bindings.append(
            RuntimeBinding(
                check.check_id,
                target,
                resolved,
                record["sha256"],
                record["observed"],
                kind,
            )
        )
    return RuntimeSeal(
        path,
        data,
        tuple((name, choices[name]) for name in CHOICE_IDS if name != "python"),
        tuple(bindings),
    )


def load_runtime_seal(
    path: Path,
    expected_sha256: str | None = None,
    *,
    require_content: bool = True,
) -> RuntimeSeal:
    if os.path.lexists(path.parent / "maintenance.lock"):
        _fail(
            f"Runtime maintenance claim is unresolved: {path.parent / 'maintenance.lock'}"
        )
    data, state = read_bytes_with_identity(
        path, "Runtime seal", limit=SEAL_BYTE_LIMIT + 1
    )
    if (
        state.st_size > SEAL_BYTE_LIMIT
        or state.st_uid != os.getuid()
        or path.resolve(strict=True) != path
    ):
        _fail("Runtime seal must be a bounded canonical file owned by this UID")
    if (
        expected_sha256 is not None
        and hashlib.sha256(data).hexdigest() != expected_sha256
    ):
        _fail("Runtime seal differs from the selected SHA-256")
    result = admit_runtime_seal(path, data, require_content=require_content)
    if os.path.lexists(path.parent / "maintenance.lock"):
        _fail("Runtime maintenance claim appeared during seal admission")
    return result


def runtime_profile_seal(data: bytes) -> RuntimeSeal | None:
    selected = shared_runtime_selection(data)
    if selected is None:
        return None
    return load_runtime_seal(
        selected.seal_path,
        selected.seal_sha256,
        require_content=False,
    )


def runtime_profile_choices(data: bytes) -> dict[str, str]:
    header, rows = _profile_rows(data)
    seal = runtime_profile_seal(data)
    if seal is not None:
        return {**dict(seal.choices), "python": rows[0]["python"]}
    if (
        header != ["check_id", "target"]
        or tuple(row.get("check_id") for row in rows) != CHOICE_IDS
    ):
        _fail(
            "Runtime inventory must contain the exact ordered runtime choices: "
            + ", ".join(CHOICE_IDS)
        )
    if any(
        set(row) != {"check_id", "target"} or not _absolute_choice(row["target"])
        for row in rows
    ):
        _fail(
            "Runtime choices must be absolute paths without extra columns or unsafe characters"
        )
    return {row["check_id"]: row["target"] for row in rows}


def runtime_profile_checks(data: bytes, source_root: Path) -> tuple[RuntimeCheck, ...]:
    """Expand one ordinary or sealed selection into the installed probe policy."""
    selected = runtime_profile_choices(data)
    renv_library = Path(selected["renv_library"])
    if os.path.lexists(renv_library):
        state = renv_library.lstat()
        if (
            stat.S_ISLNK(state.st_mode)
            or not stat.S_ISDIR(state.st_mode)
            or renv_library.resolve(strict=True) != renv_library
        ):
            _fail(f"renv library must be a canonical real directory: {renv_library}")
    targets = {
        **selected,
        "snakemake": selected["python"],
        "sha256_python": selected["python"],
        "picard": selected["java"],
        "renv_project": str(source_root),
    }
    arguments = {
        "snakemake": controlled_python_argv(
            selected["python"], "-m", "snakemake", "--version"
        )[1:],
        "picard": ("-jar", selected["picard_jar"], "MarkDuplicates", "--version"),
    }
    return tuple(
        replace(
            check,
            target=check.target
            if check.check_type == "r_namespace"
            else targets[check.check_id],
            probe_args=(selected["rscript"],)
            if check.check_type == "r_namespace"
            else arguments.get(check.check_id, check.probe_args),
        )
        for check in load_runtime_policy()
    )
