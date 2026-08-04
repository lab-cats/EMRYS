from __future__ import annotations

import ast
import importlib.util
import inspect
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT / "src/norad/libraries/reference_contigs.py"
MODULE_NAME = "_norad_test_reference_contigs"
SPEC = importlib.util.spec_from_file_location(MODULE_NAME, OWNER)
assert SPEC is not None and SPEC.loader is not None
REFERENCE_CONTIGS = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = REFERENCE_CONTIGS
SPEC.loader.exec_module(REFERENCE_CONTIGS)

CONSUMERS = (
    ROOT / "scripts/reference_provenance.py",
    ROOT
    / "src/norad/stages/construct_FASTA_sidecars/"
    "validate_step_00c_reference_sidecars.py",
    ROOT
    / "src/norad/stages/split_N_cigar_reads_with_GATK/"
    "validate_step_05_split_ncigar.py",
)
PRODUCTION_MODULE_NAMES = (
    "_norad_reference_contigs",
    "_norad_validation_report",
    "_norad_bam_validation",
)


@contextmanager
def isolated_consumer_modules():
    missing = object()
    previous = {
        name: sys.modules.get(name, missing) for name in PRODUCTION_MODULE_NAMES
    }
    for name in PRODUCTION_MODULE_NAMES:
        sys.modules.pop(name, None)
    try:
        yield
    finally:
        for name in PRODUCTION_MODULE_NAMES:
            sys.modules.pop(name, None)
            if previous[name] is not missing:
                sys.modules[name] = previous[name]


def load_consumer(path: Path) -> tuple[str, object]:
    name = f"_norad_reference_contigs_consumer_{path.stem}_{id(path)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return name, module


def test_exact_neutral_api_and_ready_marker() -> None:
    assert REFERENCE_CONTIGS._NORAD_REFERENCE_CONTIGS_READY is True
    assert issubclass(REFERENCE_CONTIGS.ReferenceContigError, RuntimeError)
    assert not hasattr(REFERENCE_CONTIGS, "ProvenanceError")
    assert str(inspect.signature(REFERENCE_CONTIGS.parse_fasta)) == (
        "(path: 'Path') -> 'list[tuple[str, int]]'"
    )
    assert str(inspect.signature(REFERENCE_CONTIGS.parse_fai)) == (
        "(path: 'Path') -> 'list[tuple[str, int]]'"
    )
    assert str(inspect.signature(REFERENCE_CONTIGS.parse_dict)) == (
        "(path: 'Path') -> 'list[tuple[str, int]]'"
    )


def test_one_definition_owner_and_no_stale_peer_bridge() -> None:
    definitions: list[tuple[Path, str]] = []
    for path in (OWNER, *CONSUMERS):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        definitions.extend(
            (path, node.name)
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in {
                "parse_fasta",
                "parse_fai",
                "parse_dict",
                "unique_contigs",
                "_unique_contigs",
            }
        )
    assert definitions == [
        (OWNER, "parse_fasta"),
        (OWNER, "parse_fai"),
        (OWNER, "parse_dict"),
        (OWNER, "_unique_contigs"),
    ]
    for path in CONSUMERS:
        source = path.read_text(encoding="utf-8")
        assert "_norad_reference_contigs" in source
        assert "_norad_reference_provenance" not in source


@pytest.mark.parametrize("consumer", CONSUMERS, ids=lambda path: path.stem)
def test_all_consumers_resolve_one_final_identity(consumer: Path) -> None:
    with isolated_consumer_modules():
        name, module = load_consumer(consumer)
        try:
            cached = sys.modules["_norad_reference_contigs"]
            assert module.reference_contigs is cached
            assert module._REFERENCE_CONTIGS_MODULE_NAME == (
                "_norad_reference_contigs"
            )
            assert module._REFERENCE_CONTIGS_MODULE_PATH == OWNER
            assert Path(cached.__file__).resolve() == OWNER
        finally:
            sys.modules.pop(name, None)


@pytest.mark.parametrize("consumer", CONSUMERS, ids=lambda path: path.stem)
@pytest.mark.parametrize(
    ("fault", "error_type", "reason"),
    [
        (
            "no_path",
            "AttributeError",
            "module '_norad_reference_contigs' has no attribute '__file__'",
        ),
        (
            "not_ready",
            "ImportError",
            "cached reference-contig owner is partially initialized",
        ),
        (
            "invalid_error",
            "ImportError",
            "cached reference-contig owner has invalid ReferenceContigError",
        ),
    ],
)
def test_all_consumer_loaders_reject_invalid_cached_owner_without_residue(
    consumer: Path,
    fault: str,
    error_type: str,
    reason: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with isolated_consumer_modules():
        consumer_name, module = load_consumer(consumer)
        try:
            bad = ModuleType("_norad_reference_contigs")
            if fault != "no_path":
                bad.__file__ = str(OWNER)
            if fault == "invalid_error":
                bad._NORAD_REFERENCE_CONTIGS_READY = True
                bad.ReferenceContigError = ValueError
                bad.parse_fasta = lambda path: path
                bad.parse_fai = lambda path: path
                bad.parse_dict = lambda path: path
            sys.modules["_norad_reference_contigs"] = bad
            invocation_cwd = tmp_path / "invocation"
            invocation_cwd.mkdir()
            before_sys_path = list(sys.path)
            monkeypatch.chdir(invocation_cwd)

            with pytest.raises(SystemExit) as raised:
                module._load_reference_contigs_or_exit()

            assert raised.value.code == 2
            captured = capsys.readouterr()
            assert captured.out == ""
            assert captured.err == (
                "ERROR: unable to load NORAD reference-contig owner at "
                f"{OWNER}: {error_type}: {reason}\n"
            )
            assert sys.modules["_norad_reference_contigs"] is bad
            assert sys.path == before_sys_path
            assert not any(invocation_cwd.iterdir())
        finally:
            sys.modules.pop(consumer_name, None)


@pytest.mark.parametrize("consumer", CONSUMERS, ids=lambda path: path.stem)
def test_all_consumer_loaders_reject_unavailable_exact_file_spec(
    consumer: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with isolated_consumer_modules():
        consumer_name, module = load_consumer(consumer)
        try:
            sys.modules.pop("_norad_reference_contigs", None)
            real_spec = importlib.util.spec_from_file_location

            def unavailable_spec(name, location, *args, **kwargs):
                if name == "_norad_reference_contigs" and Path(location) == OWNER:
                    return None
                return real_spec(name, location, *args, **kwargs)

            monkeypatch.setattr(
                importlib.util, "spec_from_file_location", unavailable_spec
            )
            invocation_cwd = tmp_path / "invocation"
            invocation_cwd.mkdir()
            before_sys_path = list(sys.path)
            monkeypatch.chdir(invocation_cwd)

            with pytest.raises(SystemExit) as raised:
                module._load_reference_contigs_or_exit()

            assert raised.value.code == 2
            captured = capsys.readouterr()
            assert captured.out == ""
            assert captured.err == (
                "ERROR: unable to load NORAD reference-contig owner at "
                f"{OWNER}: ImportError: unable to create an exact-file module "
                "specification\n"
            )
            assert "_norad_reference_contigs" not in sys.modules
            assert sys.path == before_sys_path
            assert not any(invocation_cwd.iterdir())
        finally:
            sys.modules.pop(consumer_name, None)


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
        ("@SQ\tSN:chr1\tLN:1\n@SQ\tSN:chr1\tLN:2\n", "DICT contigs are empty or duplicated"),
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
def test_raw_missing_file_error_is_preserved(
    tmp_path: Path, parser_name: str
) -> None:
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
