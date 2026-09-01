from __future__ import annotations

import argparse
import os
import signal
from dataclasses import dataclass, field
from pathlib import Path

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
            "--no-clobber",
            "--execute",
        ]


@pytest.fixture
def fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Fixture:
    tool = tmp_path / "samtools"
    tool.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    tool.chmod(0o755)
    input_bam = tmp_path / "S.split_ncigar.bam"
    input_bam.write_bytes(b"BAM\x01input\n")
    Path(f"{input_bam}.bai").write_bytes(b"BAI\x01input\n")
    monkeypatch.setenv("EMRYS_RUN_TOKEN", "owner-step06-test")
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
    fail_final_quickcheck: bool = False
    mutate_input: str | None = None
    signal_parent: bool = False
    commands: list[tuple[str, ...]] = field(default_factory=list)

    def run(
        self,
        tx: producer.Publication,
        arguments: tuple[str, ...],
        *,
        capture: bool = False,
    ) -> str:
        command = tuple(map(str, arguments))
        self.commands.append(command)
        action = command[1]
        if self.signal_parent:
            self.signal_parent = False
            tx.interrupted(signal.SIGTERM, None)
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
        elif action == "quickcheck":
            path = Path(command[2])
            if self.mutate_input is not None and ".tmp." in path.name:
                target = getattr(self.fixture, self.mutate_input)
                self.mutate_input = None
                target.write_bytes(b"mutated\n")
            if self.fail_final_quickcheck and not path.name.startswith("."):
                raise producer.ProducerError("forced final quickcheck failure")
        assert not capture or action == "view"
        return ""


def install_fake(
    monkeypatch: pytest.MonkeyPatch,
    fake: FakeSamtools,
) -> None:
    def command(
        tx: producer.Publication,
        arguments: tuple[str, ...],
        *,
        capture: bool = False,
    ) -> str:
        return fake.run(tx, arguments, capture=capture)

    monkeypatch.setattr(producer.Publication, "command", command)


def install_process_failure(
    monkeypatch: pytest.MonkeyPatch,
    returncode: int,
) -> None:
    class Process:
        def communicate(self) -> tuple[str, None]:
            return "", None

    Process.returncode = returncode
    monkeypatch.setattr(
        producer.subprocess, "Popen", lambda *_args, **_kwargs: Process()
    )


def assert_clean(fixture: Fixture) -> None:
    assert not any(path.exists() for path in fixture.finals)
    assert (
        not list(fixture.output.glob(".S.step06.*"))
        if fixture.output.exists()
        else True
    )
    assert not list(fixture.qc.glob(".S.step06.*")) if fixture.qc.exists() else True


def test_success_preserves_commands_counts_order_and_create_absent_cleanup(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeSamtools(fixture)
    install_fake(monkeypatch, fake)
    links: list[Path] = []
    real_link = producer.os.link

    def record_link(source: Path, destination: Path, **kwargs: object) -> None:
        links.append(Path(destination))
        real_link(source, destination, **kwargs)

    monkeypatch.setattr(producer.os, "link", record_link)
    assert producer.main(fixture.argv()) == 0

    assert [path.name for path in links] == [path.name for path in fixture.finals]
    counts = fixture.finals[-1].read_bytes()
    assert counts == (
        b"sample_id\tinput_records\tflag_99_records\tflag_147_records\t"
        b"flag_83_records\tflag_163_records\tfwd_like_records\trev_like_records\t"
        b"assigned_records\tunassigned_records\tassigned_fraction\n"
        b"S\t20\t5\t6\t4\t3\t11\t7\t18\t2\t0.900000\n"
    )
    commands = [item[1:] for item in fake.commands]
    prefix = fixture.output / ".S.step06.owner-step06-test"
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
                str(Path(f"{prefix}.{flag}.tmp.bam")),
            )
            for flag in ("99", "147", "83", "163")
        ],
        (
            "merge",
            "-@",
            "2",
            "-o",
            str(Path(f"{prefix}.FWD_like.tmp.bam")),
            str(Path(f"{prefix}.99.tmp.bam")),
            str(Path(f"{prefix}.147.tmp.bam")),
        ),
        (
            "merge",
            "-@",
            "2",
            "-o",
            str(Path(f"{prefix}.REV_like.tmp.bam")),
            str(Path(f"{prefix}.83.tmp.bam")),
            str(Path(f"{prefix}.163.tmp.bam")),
        ),
        ("index", str(Path(f"{prefix}.FWD_like.tmp.bam"))),
        ("index", str(Path(f"{prefix}.REV_like.tmp.bam"))),
        ("view", "-c", str(fixture.input_bam)),
        ("view", "-c", "-f", "99", str(fixture.input_bam)),
        ("view", "-c", "-f", "147", str(fixture.input_bam)),
        ("view", "-c", "-f", "83", str(fixture.input_bam)),
        ("view", "-c", "-f", "163", str(fixture.input_bam)),
        ("view", "-c", str(Path(f"{prefix}.FWD_like.tmp.bam"))),
        ("view", "-c", str(Path(f"{prefix}.REV_like.tmp.bam"))),
        ("quickcheck", str(Path(f"{prefix}.FWD_like.tmp.bam"))),
        ("quickcheck", str(Path(f"{prefix}.REV_like.tmp.bam"))),
        ("quickcheck", str(fixture.finals[0])),
        ("quickcheck", str(fixture.finals[2])),
    ]
    assert not list(fixture.output.glob(".S.step06.*"))
    assert not list(fixture.qc.glob(".S.step06.*"))


@pytest.mark.parametrize("action", ("filter", "merge", "index", "count", "quickcheck"))
def test_tool_failures_remove_owned_state(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    install_fake(monkeypatch, FakeSamtools(fixture, fail_action=action))
    assert producer.main(fixture.argv()) == 1
    assert_clean(fixture)


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"input_records": 0}, "input_records is zero"),
        ({"fwd_records": 0}, "both mechanical-orientation groups"),
        ({"rev_records": 0}, "both mechanical-orientation groups"),
        ({"input_records": 10}, "assigned_records exceeds input_records"),
    ],
)
def test_invalid_count_relationships_fail_before_publication(
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
    assert_clean(fixture)


@pytest.mark.parametrize("mutate_input", ("input_bam", "input_bai"))
def test_input_mutation_fails_without_publishing(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    mutate_input: str,
) -> None:
    install_fake(monkeypatch, FakeSamtools(fixture, mutate_input=mutate_input))
    assert producer.main(fixture.argv()) == 1
    assert getattr(fixture, mutate_input).read_bytes() == b"mutated\n"
    assert_clean(fixture)


@pytest.mark.parametrize(
    "case",
    ("sample", "token", "threads", "bam", "bai", "relative-tool", "tool-mode"),
)
def test_invalid_admission_fails_before_owned_state(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    argv = fixture.argv()
    if case == "sample":
        argv[1] = "unsafe/sample"
    elif case == "token":
        monkeypatch.setenv("EMRYS_RUN_TOKEN", "")
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
    assert not fixture.output.exists()
    assert not fixture.qc.exists()


def test_partial_publication_collision_rolls_back_only_owned_finals(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake(monkeypatch, FakeSamtools(fixture))
    real_link = producer.os.link
    calls = 0

    def collide(source: Path, destination: Path, **kwargs: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            Path(destination).write_bytes(b"foreign final\n")
            raise FileExistsError(destination)
        real_link(source, destination, **kwargs)

    monkeypatch.setattr(producer.os, "link", collide)
    assert producer.main(fixture.argv()) == 1
    assert fixture.finals[2].read_bytes() == b"foreign final\n"
    assert not any(path.exists() for path in (*fixture.finals[:2], *fixture.finals[3:]))
    assert not list(fixture.output.glob(".S.step06.*"))


def test_signal_between_link_and_ownership_check_removes_owned_final(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake(monkeypatch, FakeSamtools(fixture))
    real_link = producer.os.link
    interrupted = False

    def interrupt(source: Path, destination: Path, **kwargs: object) -> None:
        nonlocal interrupted
        real_link(source, destination, **kwargs)
        if not interrupted:
            interrupted = True
            os.kill(os.getpid(), signal.SIGTERM)

    monkeypatch.setattr(producer.os, "link", interrupt)
    assert producer.main(fixture.argv()) == 143
    assert_clean(fixture)


def test_signal_before_link_cleans_unpublished_state(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake(monkeypatch, FakeSamtools(fixture))

    def interrupt(*_args: object, **_kwargs: object) -> None:
        os.kill(os.getpid(), signal.SIGTERM)

    monkeypatch.setattr(producer.os, "link", interrupt)
    assert producer.main(fixture.argv()) == 143
    assert_clean(fixture)


def test_ambiguous_final_mutation_preserves_lock_and_staging_anchor(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake(monkeypatch, FakeSamtools(fixture))
    real_link = producer.os.link
    changed = False

    def mutate(source: Path, destination: Path, **kwargs: object) -> None:
        nonlocal changed
        real_link(source, destination, **kwargs)
        if not changed:
            changed = True
            Path(destination).unlink()
            Path(destination).write_bytes(b"foreign replacement\n")

    monkeypatch.setattr(producer.os, "link", mutate)
    assert producer.main(fixture.argv()) == 1
    assert fixture.finals[0].read_bytes() == b"foreign replacement\n"
    assert (fixture.output / ".S.step06.lock").is_dir()
    assert (fixture.output / ".S.step06.owner-step06-test.FWD_like.tmp.bam").exists()


def test_final_revalidation_failure_removes_complete_owned_set(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake(monkeypatch, FakeSamtools(fixture, fail_final_quickcheck=True))
    assert producer.main(fixture.argv()) == 1
    assert_clean(fixture)


def test_scratch_cleanup_failure_preserves_lock_and_ambiguous_state(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake(monkeypatch, FakeSamtools(fixture))
    real_unlink = Path.unlink
    failed = False

    def fail_once(path: Path, *args: object, **kwargs: object) -> None:
        nonlocal failed
        if not failed and path.name.endswith(".99.tmp.bam"):
            failed = True
            raise OSError("forced scratch cleanup failure")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_once)
    assert producer.main(fixture.argv()) == 1
    assert (fixture.output / ".S.step06.lock" / "owner").is_file()
    assert all(path.is_file() for path in fixture.finals)
    assert (fixture.output / ".S.step06.owner-step06-test.99.tmp.bam").is_file()


def test_lost_lock_does_not_remove_winner_scratch(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scratch = fixture.output / ".S.step06.owner-step06-test.99.tmp.bam"

    def lose_lock(_tx: producer.Publication) -> None:
        fixture.output.mkdir(parents=True, exist_ok=True)
        (fixture.output / ".S.step06.lock").mkdir()
        scratch.write_bytes(b"winner scratch\n")
        raise producer.ProducerError("forced lock loss")

    monkeypatch.setattr(producer.Publication, "acquire", lose_lock)
    assert producer.main(fixture.argv()) == 1
    assert scratch.read_bytes() == b"winner scratch\n"


def test_post_lock_residue_is_not_adopted_as_owned_scratch(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_acquire = producer.Publication.acquire

    def race_residue(tx: producer.Publication) -> None:
        real_acquire(tx)
        tx.p["tmp_99"].write_bytes(b"foreign scratch\n")

    monkeypatch.setattr(producer.Publication, "acquire", race_residue)
    assert producer.main(fixture.argv()) == 1
    assert (
        fixture.output / ".S.step06.owner-step06-test.99.tmp.bam"
    ).read_bytes() == b"foreign scratch\n"
    assert not (fixture.output / ".S.step06.lock").exists()


def test_lock_release_failure_restores_exact_owner_record(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake(monkeypatch, FakeSamtools(fixture))
    real_rmdir = Path.rmdir

    def refuse_lock_removal(path: Path) -> None:
        if path.name == ".S.step06.lock":
            raise OSError("forced lock release failure")
        real_rmdir(path)

    monkeypatch.setattr(Path, "rmdir", refuse_lock_removal)
    assert producer.main(fixture.argv()) == 1
    owner = fixture.output / ".S.step06.lock" / "owner"
    assert owner.read_bytes() == b"run_token=owner-step06-test\n"
    assert all(path.is_file() for path in fixture.finals)


@pytest.mark.parametrize(("failure", "expected"), (("child", 73), ("signal", 143)))
def test_lock_owner_unlink_failure_preserves_primary_status(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
    expected: int,
) -> None:
    if failure == "signal":
        install_fake(monkeypatch, FakeSamtools(fixture, signal_parent=True))
    else:
        install_process_failure(monkeypatch, 73)

    real_unlink = Path.unlink

    def refuse_owner_removal(path: Path, *args: object, **kwargs: object) -> None:
        if path.name == "owner":
            raise OSError("forced owner unlink failure")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", refuse_owner_removal)
    assert producer.main(fixture.argv()) == expected
    assert (fixture.output / ".S.step06.lock" / "owner").is_file()


@pytest.mark.parametrize(("failure", "expected"), (("child", 73), ("signal", 143)))
def test_cleanup_runs_with_signals_ignored_and_preserves_primary_status(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
    expected: int,
) -> None:
    if failure == "signal":
        install_fake(monkeypatch, FakeSamtools(fixture, signal_parent=True))
    else:
        install_process_failure(monkeypatch, 73)

    handlers = {number: signal.getsignal(number) for number in producer.SIGNALS}
    real_discard = producer.Publication.discard_scratch
    observed: list[object] = []

    def inspect_cleanup(tx: producer.Publication) -> bool:
        observed.extend(signal.getsignal(number) for number in producer.SIGNALS)
        return real_discard(tx)

    monkeypatch.setattr(producer.Publication, "discard_scratch", inspect_cleanup)
    assert producer.main(fixture.argv()) == expected
    assert observed == [signal.SIG_IGN] * len(producer.SIGNALS)
    assert all(
        signal.getsignal(number) == handler for number, handler in handlers.items()
    )
    assert_clean(fixture)


def test_flag_subcount_mismatch_is_left_to_independent_validator(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeSamtools(fixture, fwd_records=12, rev_records=6)
    install_fake(monkeypatch, fake)
    assert producer.main(fixture.argv()) == 0
    assert b"\t12\t6\t18\t2\t0.900000\n" in fixture.finals[-1].read_bytes()


@pytest.mark.parametrize("occupied", ("output-residue", "qc-residue", "final"))
def test_preexisting_state_is_preserved(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    occupied: str,
) -> None:
    path = {
        "output-residue": fixture.output / ".S.step06.foreign.tmp.bam",
        "qc-residue": fixture.qc / ".S.step06.foreign.orientation_counts.tmp.tsv",
        "final": fixture.finals[0],
    }[occupied]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"preexisting\n")
    fake = FakeSamtools(fixture)
    install_fake(monkeypatch, fake)
    assert producer.main(fixture.argv()) == 1
    assert path.read_bytes() == b"preexisting\n"
    assert fake.commands == []


def test_term_returns_signal_status_and_cleans_owned_state(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake(monkeypatch, FakeSamtools(fixture, signal_parent=True))
    assert producer.main(fixture.argv()) == 143
    assert_clean(fixture)


def test_signal_is_forwarded_to_the_owned_child_process_group(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arguments = argparse.Namespace(
        sample_id="S",
        input_bam=fixture.input_bam,
        output_dir=fixture.output,
        qc_dir=fixture.qc,
        threads="2",
        samtools_bin=str(fixture.tool),
    )
    transaction = producer.Publication(producer.build_context(arguments))

    class Child:
        pid = 4321

        @staticmethod
        def poll() -> None:
            return None

        @staticmethod
        def wait() -> None:
            return None

    def spawn(*_args: object, **kwargs: object) -> Child:
        assert kwargs["process_group"] == 0
        transaction.interrupted(signal.SIGTERM, None)
        return Child()

    delivered: list[tuple[int, int]] = []
    handlers = {number: signal.getsignal(number) for number in producer.SIGNALS}
    monkeypatch.setattr(producer.subprocess, "Popen", spawn)
    monkeypatch.setattr(
        producer.os, "killpg", lambda pid, sig: delivered.append((pid, sig))
    )
    try:
        with pytest.raises(producer.Interrupted):
            transaction.command((str(fixture.tool), "--version"))
    finally:
        for number, handler in handlers.items():
            signal.signal(number, handler)
    assert delivered == [(4321, signal.SIGTERM)]


@pytest.mark.parametrize(("returncode", "expected"), ((73, 73), (-15, 143)))
def test_main_propagates_nonzero_child_status_and_cleans_owned_state(
    fixture: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    returncode: int,
    expected: int,
) -> None:
    install_process_failure(monkeypatch, returncode)
    assert producer.main(fixture.argv()) == expected
    assert_clean(fixture)
