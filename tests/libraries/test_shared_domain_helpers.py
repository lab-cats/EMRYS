"""Direct behavioral coverage for shared domain parsing helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from norad.libraries import validation as report
from norad.libraries.alignments import bed, orientation, star
from norad.libraries.evidence import qc
from norad.libraries.quality import picard
from norad.libraries.validation import mpileup


def write_tsv(path: Path, header: tuple[str, ...], rows: list[tuple[str, ...]]) -> None:
    path.write_text(
        "\n".join("\t".join(row) for row in [header, *rows]) + "\n",
        encoding="utf-8",
    )


def test_bed12_failure_branches_and_duplicate_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        bed.report,
        "stable_text",
        lambda *_args, **_kwargs: ("", object()),
    )
    with pytest.raises(report.ValidationError, match="at least one row"):
        bed.parse_bed12(tmp_path / "unused.bed")

    nonnumeric = (
        "chr1",
        "bad",
        "10",
        "tx1",
        "0",
        "+",
        "0",
        "10",
        "0",
        "1",
        "10,",
        "0,",
    )
    structurally_invalid = (
        "chr1",
        "0",
        "10",
        "tx1",
        "1",
        "+",
        "0",
        "10",
        "0",
        "1",
        "10,",
        "0,",
    )
    valid = (
        "chr1",
        "0",
        "10",
        "tx1",
        "0",
        "+",
        "0",
        "10",
        "0",
        "1",
        "10,",
        "0,",
    )
    assert bed.inspect_bed12_rows([nonnumeric]) == (False, False, True, True)
    assert bed.inspect_bed12_rows([structurally_invalid]) == (False, False, True, True)
    assert bed.inspect_bed12_rows([valid, valid]) == (True, True, True, False)


def test_orientation_helper_failure_branches(tmp_path: Path) -> None:
    assert orientation.infer_orientation_from_path("sample.unknown.bam") is None
    assert orientation.mechanical_like_count_detail({}, "unknown") == (
        False,
        "unsupported orientation='unknown'",
    )

    missing = tmp_path / "missing.tsv"
    assert orientation.read_orientation_counts(missing, "S")[0] == {}

    wrong_header = tmp_path / "wrong-header.tsv"
    write_tsv(wrong_header, ("sample",), [("S",)])
    assert orientation.read_orientation_counts(wrong_header, "S") == (
        {},
        "header mismatch",
    )

    wrong_scope = tmp_path / "wrong-scope.tsv"
    write_tsv(
        wrong_scope,
        orientation.COUNTS_HEADER,
        [("other", "10", "1", "2", "3", "4", "3", "7", "10", "0", "1")],
    )
    assert orientation.read_orientation_counts(wrong_scope, "S") == (
        {},
        "expected one row for the declared sample",
    )

    for name, row in (
        (
            "negative.tsv",
            ("S", "-1", "1", "2", "3", "4", "3", "7", "10", "0", "1"),
        ),
        (
            "bad-fraction.tsv",
            ("S", "10", "1", "2", "3", "4", "3", "7", "10", "0", "2"),
        ),
    ):
        path = tmp_path / name
        write_tsv(path, orientation.COUNTS_HEADER, [row])
        assert orientation.read_orientation_counts(path, "S") == (
            {},
            "counts must be nonnegative integers and fraction in 0..1",
        )


def test_star_text_parser_failure_branches() -> None:
    assert star.parse_final_log("ignored\nReads | 10") == {"Reads": "10"}
    with pytest.raises(ValueError, match="Invalid STAR"):
        star.parse_final_log("Reads | 10\nReads | 11")
    with pytest.raises(ValueError, match="contains no key/value"):
        star.parse_final_log("ignored")

    mapping = {key: "10%" for key in star.PERCENT_KEYS}
    invalid_mapping = dict(mapping)
    invalid_mapping[next(iter(star.PERCENT_KEYS))] = "bad"
    assert not star.valid_mapping_summary(invalid_mapping)[0]
    outside_mapping = dict(mapping)
    outside_mapping[next(iter(star.PERCENT_KEYS))] = "101%"
    assert not star.valid_mapping_summary(outside_mapping)[0]

    valid_sj = "\nchr1\t1\t2\t0\t0\t0\t0\t0\t0"
    assert star.valid_splice_junction_table(valid_sj) == (
        True,
        "1 splice-junction rows",
    )
    assert not star.valid_splice_junction_table("chr1\tbad\t2\t0\t0\t0\t0\t0\t0")[0]
    assert not star.valid_splice_junction_table("chr1\t2\t1\t0\t0\t0\t0\t0\t0")[0]


def test_star_file_parser_failure_branches(tmp_path: Path) -> None:
    blank_lines = tmp_path / "blank-parameters.txt"
    blank_lines.write_text("\n", encoding="utf-8")
    assert star.parse_parameters(blank_lines)[0] == {}

    for name, content, message in (
        ("missing-value.txt", "genomeFastaFiles\n", "has no value"),
        ("duplicate.txt", "key one\nkey two\n", "repeats 'key'"),
    ):
        path = tmp_path / name
        path.write_text(content, encoding="utf-8")
        with pytest.raises(ValueError, match=message):
            star.parse_parameters(path)

    invalid_fasta = tmp_path / "invalid.fa"
    invalid_fasta.write_text("ACGT\n", encoding="utf-8")
    with pytest.raises(ValueError, match="before its header"):
        star.parse_fasta(invalid_fasta)

    index_dir = tmp_path / "index"
    index_dir.mkdir()
    for names, lengths, message in (
        ("chr1\nchr1\n", "1\n1\n", "empty, duplicate, or misaligned"),
        ("chr1\n", "bad\n", "non-integer"),
        ("chr1\n", "0\n", "nonempty and positive"),
    ):
        (index_dir / "chrName.txt").write_text(names, encoding="utf-8")
        (index_dir / "chrLength.txt").write_text(lengths, encoding="utf-8")
        with pytest.raises(ValueError, match=message):
            star.parse_star_index_contigs(index_dir)


def test_evidence_and_picard_parser_failure_branches() -> None:
    flagstat_values, flagstat_errors = qc.parse_flagstat(
        "\nmalformed\n"
        "10 + 0 in total (QC-passed reads + QC-failed reads)\n"
        "11 + 0 in total (QC-passed reads + QC-failed reads)\n"
    )
    assert flagstat_values["total"] == (11, 0)
    assert flagstat_errors == ["line 2 malformed", "duplicate total row"]

    fraction_values, fraction_errors = qc.parse_fraction_report(
        "ignored\nUnknown: 1\nA: 0.5\nA: 0.6\nB: invalid\nC: inf\n",
        ("A", "B", "C"),
    )
    assert fraction_values == {"A": 0.5}
    assert fraction_errors == [
        "duplicate label at line 4",
        "invalid fraction at line 5",
        "nonfinite fraction at line 6",
        "missing 2 required labels",
    ]

    assert picard.parse_duplication_metrics("# only a comment") == (
        False,
        "missing metrics header/data row",
    )
    nonnumeric = (
        "LIBRARY\tREAD_PAIRS_EXAMINED\tREAD_PAIR_DUPLICATES\tPERCENT_DUPLICATION\n"
        "lib\tbad\t1\t0.5\n"
    )
    assert picard.parse_duplication_metrics(nonnumeric) == (
        False,
        "non-numeric duplication metric",
    )


def test_picard_parser_ignores_the_following_histogram_table() -> None:
    metrics = (
        "## METRICS CLASS\tpicard.sam.DuplicationMetrics\n"
        "LIBRARY\tUNPAIRED_READS_EXAMINED\tREAD_PAIRS_EXAMINED\t"
        "SECONDARY_OR_SUPPLEMENTARY_RDS\tUNMAPPED_READS\t"
        "UNPAIRED_READ_DUPLICATES\tREAD_PAIR_DUPLICATES\t"
        "READ_PAIR_OPTICAL_DUPLICATES\tPERCENT_DUPLICATION\t"
        "ESTIMATED_LIBRARY_SIZE\n"
        "control_pair_01\t0\t130\t0\t0\t0\t0\t0\t0\t\n"
        "\n"
        "## HISTOGRAM\tjava.lang.Double\n"
        "set_size\tall_sets\tnon_optical_sets\n"
        "1.0\t130\t130\n"
    )

    assert picard.parse_duplication_metrics(metrics) == (
        True,
        "library=control_pair_01 pairs=130 duplicates=0 fraction=0",
    )


def test_picard_parser_preserves_header_order_and_prefix_validation() -> None:
    reordered = (
        "PERCENT_DUPLICATION\tLIBRARY\tREAD_PAIR_DUPLICATES\t"
        "READ_PAIRS_EXAMINED\n"
        "0.2\tS\t2\t10\n"
    )
    assert picard.parse_duplication_metrics(reordered) == (
        True,
        "library=S pairs=10 duplicates=2 fraction=0.2",
    )

    prefixed = "unexpected\n" + reordered
    assert picard.parse_duplication_metrics(prefixed) == (
        False,
        "expected one row with required Picard columns",
    )


def test_mpileup_manifest_and_selector_failure_branches(tmp_path: Path) -> None:
    sample_manifest = tmp_path / "samples.tsv"
    write_tsv(sample_manifest, ("other",), [("S",)])
    with pytest.raises(report.ValidationError, match="lacks sample_id"):
        mpileup.read_sample_ids(sample_manifest)
    write_tsv(sample_manifest, ("sample_id",), [("S",), ("S",)])
    with pytest.raises(report.ValidationError, match="nonempty and unique"):
        mpileup.read_sample_ids(sample_manifest)

    partition_manifest = tmp_path / "partitions.tsv"
    write_tsv(partition_manifest, ("partition_id",), [("p1",)])
    with pytest.raises(report.ValidationError, match="lacks required columns"):
        mpileup.read_partition(partition_manifest, "p1")
    write_tsv(
        partition_manifest,
        ("partition_id", "selector_type", "selector_value"),
        [("p1", "region", "chr1")],
    )
    with pytest.raises(report.ValidationError, match="one declared partition"):
        mpileup.read_partition(partition_manifest, "absent")
    write_tsv(
        partition_manifest,
        ("partition_id", "selector_type", "selector_value"),
        [("p1", "invalid", "chr1")],
    )
    with pytest.raises(report.ValidationError, match="selector is invalid"):
        mpileup.read_partition(partition_manifest, "p1")

    invalid_fai = tmp_path / "reference.fa.fai"
    invalid_fai.write_text("bad\n", encoding="utf-8")
    with pytest.raises(report.ValidationError, match="malformed"):
        mpileup.read_fai(invalid_fai)

    contigs = {"chr1": 10}
    for selector in ("", "chr2", "chr1:bad", "chr1:0-1", "chr1:1-11"):
        assert not mpileup.selector_ok(
            "region",
            selector,
            partition_manifest,
            contigs,
        )
    assert mpileup.selector_ok("region", "chr1", partition_manifest, contigs)

    regions = tmp_path / "regions.tsv"
    regions.write_text("chr1\t1\t2\n", encoding="utf-8")
    assert mpileup.selector_ok(
        "regions_file",
        regions.name,
        partition_manifest,
        contigs,
    )


def test_mpileup_vcf_failure_branches(tmp_path: Path) -> None:
    header = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS1"
    cases = (
        ("invalid-header.vcf", header.replace("#CHROM", "#WRONG"), "lacks #CHROM"),
        (
            "data-before-header.vcf",
            "chr1\t1\t.\tA\tG\t.\tPASS\t.\tGT\t0/1",
            "data precedes header",
        ),
        (
            "invalid-row.vcf",
            header + "\nchr1\tbad\t.\tA\tG\t.\tPASS\t.\tGT\t0/1",
            "Invalid VCF data row",
        ),
        ("missing-header.vcf", "##fileformat=VCFv4.2", "lacks #CHROM"),
    )
    for name, content, message in cases:
        path = tmp_path / name
        path.write_text(content + "\n", encoding="utf-8")
        with pytest.raises(report.ValidationError, match=message):
            mpileup.read_vcf(path)

    valid = tmp_path / "valid.vcf"
    valid.write_text(
        "##fileformat=VCFv4.2\n"
        + header
        + "\n#comment\nchr1\t1\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\n",
        encoding="utf-8",
    )
    assert mpileup.read_vcf(valid) == (["S1"], 1)
