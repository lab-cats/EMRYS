"""Focused consumer contracts for local-pilot runtime content identity."""

from __future__ import annotations

import hashlib
from pathlib import Path

from emrys.evidence.runtime_availability.inspector import (
    RuntimeCheck,
    RuntimeInspection,
    RuntimeObservation,
)
from emrys.libraries.installed_package_identity import installed_package_tree_identity
from emrys.orchestration.local_pilot import doctor


def _observation(
    check_id: str,
    check_type: str,
    target: str,
    probe_args: tuple[str, ...],
    *,
    resolved_path: Path | None = None,
) -> RuntimeObservation:
    return RuntimeObservation(
        check=RuntimeCheck(
            check_id=check_id,
            check_type=check_type,
            runtime_context="local",
            required=True,
            target=target,
            probe_args=probe_args,
            expected="expected",
            description=check_id,
        ),
        status="pass",
        observed="1.0.0",
        detail="fixture",
        resolved_path=resolved_path,
    )


def test_r_namespace_binding_uses_exact_package_tree_not_rscript(
    tmp_path: Path,
) -> None:
    rscript = tmp_path / "Rscript"
    rscript.write_bytes(b"first-rscript-bytes\n")
    rscript.chmod(0o755)
    library = tmp_path / "library"
    package = library / "VariantAnnotation"
    database = package / "R" / "VariantAnnotation.rdb"
    database.parent.mkdir(parents=True)
    database.write_bytes(b"package-database\n")
    (package / "DESCRIPTION").write_text(
        "Package: VariantAnnotation\nVersion: 1.0.0\n",
        encoding="utf-8",
    )
    observations = (
        _observation("rscript", "tool_version", str(rscript), ("--version",)),
        _observation(
            "renv_library",
            "path_visibility",
            str(library),
            ("directory_readable",),
        ),
        _observation(
            "r_variant_annotation",
            "r_namespace",
            "VariantAnnotation",
            (str(rscript),),
            resolved_path=package,
        ),
    )
    inspection = RuntimeInspection(
        profile_path=tmp_path / "runtime.tsv",
        profile_sha256=hashlib.sha256(b"runtime\n").hexdigest(),
        profile_bytes=b"runtime\n",
        runtime_context="local",
        observations=observations,
        rendered_bytes=b"rendered\n",
    )

    before = {item.check_id: item for item in doctor.runtime_file_bindings(inspection)}
    rscript.write_bytes(b"second-rscript-data\n")
    after = {item.check_id: item for item in doctor.runtime_file_bindings(inspection)}

    expected_package = installed_package_tree_identity(package)
    assert before["r_variant_annotation"].path == package
    assert before["r_variant_annotation"].resolved_path == package
    assert before["r_variant_annotation"].sha256 == expected_package.sha256
    assert after["r_variant_annotation"].sha256 == before["r_variant_annotation"].sha256
    assert after["rscript"].sha256 != before["rscript"].sha256
