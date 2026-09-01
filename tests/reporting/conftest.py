"""Installed-entry-point doubles for source-tree reporting tests."""

from __future__ import annotations

import importlib
import importlib.metadata
from dataclasses import dataclass

import pytest

_ENTRY_POINTS = importlib.metadata.entry_points


@dataclass(frozen=True)
class _Distribution:
    name: str = "emrys-rna-workflow"
    version: str = importlib.metadata.version("emrys-rna-workflow")


@dataclass(frozen=True)
class _ReporterEntryPoint:
    name: str = "emrys.paired-cmh"
    value: str = (
        "emrys.analyses.paired_cmh_candidate_ranking_report:"
        "render_scientific_report"
    )
    dist: _Distribution = _Distribution()

    def load(self):
        package, name = self.value.split(":", 1)
        return getattr(importlib.import_module(package), name)


@pytest.fixture(autouse=True)
def installed_analysis_reporter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expose the pyproject reporter entry point without reinstalling per test."""

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda *, group: (
            (_ReporterEntryPoint(),)
            if group == "emrys.analysis_reporters"
            else _ENTRY_POINTS(group=group)
        ),
    )
