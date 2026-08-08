from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from norad.libraries.alignments import bam as BAM


def test_public_api_and_characterized_behavior() -> None:
    functions = {
        name
        for name, value in vars(BAM).items()
        if inspect.isfunction(value) and value.__module__ == BAM.__name__
    }
    assert functions == {"run_tool", "parse_header"}

    completed = BAM.run_tool(
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
        BAM.run_tool(Path("/definitely/missing/norad-tool"), "--probe")
    assert raised.value.errno == 2

    assert BAM.parse_header("@HD\tVN:1.6\tSO:coordinate\n@RG\tID:S\tSM:S\n", "S") == (
        True,
        True,
        "HD=1 RG=1",
    )
    assert BAM.parse_header("", "S") == (False, False, "HD=0 RG=0")
    assert BAM.parse_header(
        "@HD\tSO:coordinate\n@HD\tSO:coordinate\n@RG\tID:S\tSM:S\n@RG\tID:S\tSM:S\n",
        "S",
    ) == (False, False, "HD=2 RG=2")
    assert BAM.parse_header("@HD\tSO:coordinate\n@RG\tID:wrong\tSM:S\n", "S") == (
        True,
        False,
        "HD=1 RG=1",
    )
