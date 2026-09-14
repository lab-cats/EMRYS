from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import pytest

from emrys.stages.mechanical_orientation import producer


@dataclass(slots=True)
class Fixture:
    root: Path
    tool: Path
    input_bam: Path
    output: Path
    qc: Path

    @property
    def input_bai(self) -> Path:
        return Path(f"{self.input_bam}.bai")

    @property
    def finals(self) -> tuple[Path, ...]:
        return (
            self.output / "S.FWD_like.bam",
            self.output / "S.FWD_like.bam.bai",
            self.output / "S.REV_like.bam",
            self.output / "S.REV_like.bam.bai",
            self.qc / "S.orientation_counts.tsv",
        )

    def argv(self) -> list[str]:
        return [
            "--sample-id",
            "S",
            "--input-bam",
            str(self.input_bam),
            "--output-dir",
            str(self.output),
            "--qc-dir",
            str(self.qc),
            "--threads",
            "2",
            "--samtools-bin",
            str(self.tool),
        ]


@pytest.fixture
def fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Fixture:
    tool = tmp_path / "samtools"
    tool.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    tool.chmod(0o755)
    input_bam = tmp_path / "S.split_ncigar.bam"
    input_bam.write_bytes(b"BAM\x01input\n")
    Path(f"{input_bam}.bai").write_bytes(b"BAI\x01input\n")
    monkeypatch.setenv("EMRYS_TASK_WORK_DIR", str(tmp_path))
    (tmp_path / "orientation").mkdir()
    (tmp_path / "qc").mkdir()
    return Fixture(tmp_path, tool, input_bam, tmp_path / "orientation", tmp_path / "qc")


@dataclass(slots=True)
class FakeSamtools:
    fixture: Fixture
    input_records: int = 20
    flag_counts: dict[str, int] = field(
        default_factory=lambda: {"99": 5, "147": 6, "83": 4, "163": 3}
    )
    fwd_records: int = 11
    rev_records: int = 7
    fail_action: str | None = None
    commands: list[tuple[str, ...]] = field(default_factory=list)

    def run(
        self,
        arguments: tuple[str, ...],
        *,
        capture: bool = False,
    ) -> str:
        command = tuple(map(str, arguments))
        self.commands.append(command)
        action = command[1]
        if (
            self.fail_action == action
            or (self.fail_action == "filter" and action == "view" and "-o" in command)
            or (self.fail_action == "count" and action == "view" and "-c" in command)
        ):
            raise producer.ProducerError(f"forced {self.fail_action} failure")
        if action == "view" and "-o" in command:
            Path(command[command.index("-o") + 1]).write_bytes(b"BAM\x01filtered\n")
        elif action == "merge":
            Path(command[command.index("-o") + 1]).write_bytes(b"BAM\x01merged\n")
        elif action == "index":
            Path(f"{command[2]}.bai").write_bytes(b"BAI\x01index\n")
        elif action == "view" and "-c" in command:
            if "-f" in command:
                return f"{self.flag_counts[command[command.index('-f') + 1]]}\n"
            path = Path(command[-1])
            if path == self.fixture.input_bam:
                return f"{self.input_records}\n"
            return (
                f"{self.fwd_records if 'FWD_like' in path.name else self.rev_records}\n"
            )
        assert not capture or action == "view"
        return ""


def install_fake(monkeypatch: pytest.MonkeyPatch, fake: FakeSamtools) -> None:
    monkeypatch.setattr(producer, "_command", fake.run)


def install_process_failure(monkeypatch: pytest.MonkeyPatch, returncode: int) -> None:
    monkeypatch.setattr(
        producer.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=returncode, stdout=""),
    )


def test_worker_preserves_scientific_commands_and_counts(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeSamtools(fixture)
    install_fake(monkeypatch, fake)
    assert producer.main(fixture.argv()) == 0
    assert all(path.is_file() for path in fixture.finals)
    counts = fixture.finals[-1].read_bytes()
    assert counts == (
        b"sample_id\tinput_records\tflag_99_records\tflag_147_records\t"
        b"flag_83_records\tflag_163_records\tfwd_like_records\trev_like_records\t"
        b"assigned_records\tunassigned_records\tassigned_fraction\n"
        b"S\t20\t5\t6\t4\t3\t11\t7\t18\t2\t0.900000\n"
    )
    commands = [item[1:] for item in fake.commands]
    prefix = fixture.root / "S"
    assert commands == [
        ("--version",),
        *[
            (
                "view",
                "-@",
                "2",
                "-b",
                "-f",
                flag,
                str(fixture.input_bam),
                "-o",
                str(Path(f"{prefix}.{flag}.bam")),
            )
            for flag in ("99", "147", "83", "163")
        ],
        (
            "merge",
            "-@",
            "2",
            "-o",
            str(fixture.finals[0]),
            str(Path(f"{prefix}.99.bam")),
            str(Path(f"{prefix}.147.bam")),
        ),
        (
            "merge",
            "-@",
            "2",
            "-o",
            str(fixture.finals[2]),
            str(Path(f"{prefix}.83.bam")),
            str(Path(f"{prefix}.163.bam")),
        ),
        ("index", str(fixture.finals[0])),
        ("index", str(fixture.finals[2])),
        ("view", "-c", str(fixture.input_bam)),
        ("view", "-c", "-f", "99", str(fixture.input_bam)),
        ("view", "-c", "-f", "147", str(fixture.input_bam)),
        ("view", "-c", "-f", "83", str(fixture.input_bam)),
        ("view", "-c", "-f", "163", str(fixture.input_bam)),
        ("view", "-c", str(fixture.finals[0])),
        ("view", "-c", str(fixture.finals[2])),
        ("quickcheck", str(fixture.finals[0])),
        ("quickcheck", str(fixture.finals[2])),
    ]


@pytest.mark.parametrize("action", ("filter", "merge", "index", "count", "quickcheck"))
def test_worker_rejects_tool_failures(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    install_fake(monkeypatch, FakeSamtools(fixture, fail_action=action))
    assert producer.main(fixture.argv()) == 1


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"input_records": 0}, "input_records is zero"),
        ({"fwd_records": 0}, "both mechanical-orientation groups"),
        ({"rev_records": 0}, "both mechanical-orientation groups"),
        ({"input_records": 10}, "assigned_records exceeds input_records"),
    ],
)
def test_invalid_count_relationships_are_rejected(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    values: dict[str, int],
    message: str,
) -> None:
    fake = FakeSamtools(fixture)
    for name, value in values.items():
        setattr(fake, name, value)
    install_fake(monkeypatch, fake)
    assert producer.main(fixture.argv()) == 1
    assert message in capsys.readouterr().err


@pytest.mark.parametrize(
    "case",
    ("sample", "threads", "bam", "bai", "relative-tool", "tool-mode"),
)
def test_invalid_scientific_inputs_are_rejected(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    argv = fixture.argv()
    if case == "sample":
        argv[1] = "unsafe/sample"
    elif case == "threads":
        argv[9] = "0"
    elif case == "bam":
        fixture.input_bam.unlink()
    elif case == "bai":
        fixture.input_bai.unlink()
    elif case == "relative-tool":
        argv[11] = "samtools"
    else:
        fixture.tool.chmod(0o644)
    assert producer.main(argv) == 1
    assert not any(path.exists() for path in fixture.finals)


def test_flag_subcount_mismatch_is_left_to_independent_validator(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeSamtools(fixture, fwd_records=12, rev_records=6)
    install_fake(monkeypatch, fake)
    assert producer.main(fixture.argv()) == 0
    assert b"\t12\t6\t18\t2\t0.900000\n" in fixture.finals[-1].read_bytes()


@pytest.mark.parametrize(("returncode", "expected"), ((73, 73), (-15, 143)))
def test_main_propagates_nonzero_child_status(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    returncode: int,
    expected: int,
) -> None:
    install_process_failure(monkeypatch, returncode)
    assert producer.main(fixture.argv()) == expected
