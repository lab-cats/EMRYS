"""Neutral mechanics shared by independent stage-validator suites."""

from __future__ import annotations

import csv
from pathlib import Path
from types import ModuleType

from tests.contract_integration.validation_rosters import validation_roster_expectations


def load_roster_oracle(_root: Path) -> ModuleType:
    return validation_roster_expectations


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))
