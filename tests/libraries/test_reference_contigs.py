from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from emrys.libraries.references import contigs as REFERENCE_CONTIGS


def test_neutral_public_api() -> None:
    assert issubclass(REFERENCE_CONTIGS.ReferenceContigError, RuntimeError)
    assert str(inspect.signature(REFERENCE_CONTIGS.parse_fasta)) == (
        "(path: 'Path') -> 'list[tuple[str, int]]'"
    )
    assert str(inspect.signature(REFERENCE_CONTIGS.parse_fai)) == (
        "(path: 'Path') -> 'list[tuple[str, int]]'"
    )
    assert str(inspect.signature(REFERENCE_CONTIGS.parse_dict)) == (
        "(path: 'Path') -> 'list[tuple[str, int]]'"
    )


def test_ordered_parsers_preserve_characterized_projection(tmp_path: Path) -> None:
    fasta = tmp_path / "genome.fa"
    fasta.write_text(">chr1 description\nAC\nGT\n\n>MT\nA*.-\n", encoding="utf-8")
    fai = tmp_path / "genome.fa.fai"
    fai.write_text("chr1\t4\textra\nMT\t4\tignored\n", encoding="utf-8")
    dictionary = tmp_path / "genome.dict"
    dictionary.write_text(
        "@HD\tVN:1.6\n"
        "ignored\n"
        "@SQ\tSN:old\tSN:chr1\tLN:4\tUR:value:with:colons\n"
        "@SQ\tSN:MT\tLN:4\textra-without-colon\n",
        encoding="utf-8",
    )

    expected = [("chr1", 4), ("MT", 4)]
    assert REFERENCE_CONTIGS.parse_fasta(fasta) == expected
    assert REFERENCE_CONTIGS.parse_fai(fai) == expected
    assert REFERENCE_CONTIGS.parse_dict(dictionary) == expected


def test_fasta_uses_explicit_utf8_while_sidecars_use_default_decoding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def read_text(path: Path, *args: object, **kwargs: object) -> str:
        calls.append((path.name, args, kwargs))
        if path.name == "genome.fa":
            return ">chr1\nA\n"
        if path.name == "genome.fa.fai":
            return "chr1\t1\n"
        return "@SQ\tSN:chr1\tLN:1\n"

    monkeypatch.setattr(Path, "read_text", read_text)
    assert REFERENCE_CONTIGS.parse_fasta(Path("genome.fa")) == [("chr1", 1)]
    assert REFERENCE_CONTIGS.parse_fai(Path("genome.fa.fai")) == [("chr1", 1)]
    assert REFERENCE_CONTIGS.parse_dict(Path("genome.dict")) == [("chr1", 1)]
    assert calls == [
        ("genome.fa", (), {"encoding": "utf-8"}),
        ("genome.fa.fai", (), {}),
        ("genome.dict", (), {}),
    ]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("AC\n", "FASTA sequence appears before its header"),
        (">chr1\nAC1\n", "FASTA has invalid sequence characters for chr1"),
        (">chr1\nA\n>chr1\nC\n", "FASTA has empty or duplicate contig: 'chr1'"),
        (
            ">chr1 first\nA\n>chr2\nC\n>chr1 later\nG\n",
            "FASTA has empty or duplicate contig: 'chr1'",
        ),
        (">chr1\n\n", "FASTA must contain nonempty contigs"),
        ("", "FASTA must contain nonempty contigs"),
    ],
)
def test_fasta_failures_preserve_exact_messages(
    tmp_path: Path, text: str, message: str
) -> None:
    path = tmp_path / "genome.fa"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(REFERENCE_CONTIGS.ReferenceContigError) as raised:
        REFERENCE_CONTIGS.parse_fasta(path)
    assert str(raised.value) == message


def test_fasta_empty_header_preserves_raw_index_error(tmp_path: Path) -> None:
    path = tmp_path / "genome.fa"
    path.write_text(">   \nA\n", encoding="utf-8")
    with pytest.raises(IndexError):
        REFERENCE_CONTIGS.parse_fasta(path)


def test_fasta_duplicate_membership_work_grows_linearly() -> None:
    class TrackedName(str):
        equality_calls: dict[str, int]
        stable_hash: int

        def __new__(
            cls, value: str, equality_calls: dict[str, int], stable_hash: int
        ) -> TrackedName:
            instance = super().__new__(cls, value)
            instance.equality_calls = equality_calls
            instance.stable_hash = stable_hash
            return instance

        def __eq__(self, other: object) -> bool:
            self.equality_calls["equality"] += 1
            return super().__eq__(other)

        def __hash__(self) -> int:
            self.equality_calls["hash"] += 1
            return self.stable_hash

    class HeaderTail(str):
        name: TrackedName

        def __new__(cls, name: TrackedName) -> HeaderTail:
            instance = super().__new__(cls, name)
            instance.name = name
            return instance

        def split(self, *args: object, **kwargs: object) -> list[str]:
            assert not args and not kwargs
            return [self.name]

    class HeaderLine(str):
        name: TrackedName

        def __new__(cls, name: TrackedName) -> HeaderLine:
            instance = super().__new__(cls, f">{name}")
            instance.name = name
            return instance

        def __getitem__(self, key: object) -> str:
            if key == slice(1, None, None):
                return HeaderTail(self.name)
            return super().__getitem__(key)  # type: ignore[arg-type]

    def membership_operations(contig_count: int) -> int:
        calls = {"equality": 0, "hash": 0}
        lines: list[str] = []
        for index in range(contig_count):
            name = TrackedName(f"contig-{index:08d}", calls, index + 1)
            lines.extend((HeaderLine(name), "A"))

        observed = REFERENCE_CONTIGS.parse_fasta_lines(lines)

        assert [(str(name), length) for name, length in observed] == [
            (f"contig-{index:08d}", 1) for index in range(contig_count)
        ]
        return calls["equality"] + calls["hash"]

    small = membership_operations(64)
    large = membership_operations(128)

    assert small > 0
    assert small <= large <= small * 3


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("chr1\n", "FAI row 1 is malformed"),
        ("chr1\t1\nMT\tnot-a-number\n", "FAI row 2 is malformed"),
        ("", "FAI contigs are empty or duplicated"),
        ("chr1\t1\nchr1\t2\n", "FAI contigs are empty or duplicated"),
    ],
)
def test_fai_failures_preserve_exact_messages(
    tmp_path: Path, text: str, message: str
) -> None:
    path = tmp_path / "genome.fa.fai"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(REFERENCE_CONTIGS.ReferenceContigError) as raised:
        REFERENCE_CONTIGS.parse_fai(path)
    assert str(raised.value) == message


def test_fai_preserves_empty_name_zero_length_and_raw_conversion_error(
    tmp_path: Path,
) -> None:
    path = tmp_path / "genome.fa.fai"
    path.write_text("\t0\textra\n", encoding="utf-8")
    assert REFERENCE_CONTIGS.parse_fai(path) == [("", 0)]
    path.write_text("chr1\t²\n", encoding="utf-8")
    with pytest.raises(ValueError):
        REFERENCE_CONTIGS.parse_fai(path)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("@SQ\tLN:1\n", "DICT has malformed @SQ row"),
        ("@SQ\tSN:chr1\tLN:nope\n", "DICT has malformed @SQ row"),
        ("@HD\tVN:1.6\n@SQ SN:chr1 LN:1\n", "DICT contigs are empty or duplicated"),
        (
            "@SQ\tSN:chr1\tLN:1\n@SQ\tSN:chr1\tLN:2\n",
            "DICT contigs are empty or duplicated",
        ),
    ],
)
def test_dict_failures_preserve_exact_messages(
    tmp_path: Path, text: str, message: str
) -> None:
    path = tmp_path / "genome.dict"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(REFERENCE_CONTIGS.ReferenceContigError) as raised:
        REFERENCE_CONTIGS.parse_dict(path)
    assert str(raised.value) == message


def test_dict_preserves_empty_name_zero_length_and_raw_conversion_error(
    tmp_path: Path,
) -> None:
    path = tmp_path / "genome.dict"
    path.write_text("@SQ\tSN:\tLN:0\n", encoding="utf-8")
    assert REFERENCE_CONTIGS.parse_dict(path) == [("", 0)]
    path.write_text("@SQ\tSN:chr1\tLN:²\n", encoding="utf-8")
    with pytest.raises(ValueError):
        REFERENCE_CONTIGS.parse_dict(path)


@pytest.mark.parametrize("parser_name", ["parse_fasta", "parse_fai", "parse_dict"])
def test_raw_missing_file_error_is_preserved(tmp_path: Path, parser_name: str) -> None:
    parser = getattr(REFERENCE_CONTIGS, parser_name)
    with pytest.raises(FileNotFoundError):
        parser(tmp_path / "missing")


@pytest.mark.parametrize("parser_name", ["parse_fasta", "parse_fai", "parse_dict"])
def test_raw_unicode_decode_error_is_preserved(
    tmp_path: Path, parser_name: str
) -> None:
    path = tmp_path / parser_name
    path.write_bytes(b"\xff")
    parser = getattr(REFERENCE_CONTIGS, parser_name)
    with pytest.raises(UnicodeDecodeError):
        parser(path)
