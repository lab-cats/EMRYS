"""Prevent unapproved production adoption of application logging."""

from __future__ import annotations

from pathlib import Path

from tests.tools import source_dependencies as dependencies

REPO_ROOT = Path(__file__).resolve().parents[3]
LOGGING_NAMESPACE = "emrys.libraries.application_logging"

# Add exact packaged-Python importer modules only in an approved LOG-05 slice.
APPROVED_PRODUCTION_IMPORTERS: frozenset[str] = frozenset()


def _in_logging_namespace(module: str) -> bool:
    return module == LOGGING_NAMESPACE or module.startswith(f"{LOGGING_NAMESPACE}.")


def test_application_logging_production_import_roster_is_exact() -> None:
    edges = dependencies.collect_edges(
        REPO_ROOT,
        dependencies.python_sources(REPO_ROOT),
    )
    import_edges = tuple(
        edge
        for edge in edges
        if _in_logging_namespace(edge.target_module)
        and not _in_logging_namespace(edge.source_module)
    )
    observed = frozenset(edge.source_module for edge in import_edges)
    unexpected = tuple(
        f"{edge.source_path}:{edge.line} -> {edge.target_module}"
        for edge in import_edges
        if edge.source_module not in APPROVED_PRODUCTION_IMPORTERS
    )
    stale = tuple(sorted(APPROVED_PRODUCTION_IMPORTERS - observed))

    assert not unexpected and not stale, (
        "application-logging production-import roster changed; "
        f"unapproved={unexpected or 'none'}; stale={stale or 'none'}. "
        "Production imports require an approved LOG-05 slice."
    )
