import subprocess
import sys
from pathlib import Path

from emrys.stages.gtf_to_bed12.converter import (
    normalize_gtf,
    render_bed,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def run_converter(
    *args: str,
    cwd: Path = REPO_ROOT,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "emrys.stages.gtf_to_bed12.converter",
            *args,
        ],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def write_gtf(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n")
    return path


def gtf_row(
    chrom: str,
    coordinates: tuple[int | str, int | str],
    strand: str,
    attributes: str,
    *,
    feature: str = "exon",
) -> str:
    start, end = coordinates
    return "\t".join(
        [
            chrom,
            "test",
            feature,
            str(start),
            str(end),
            ".",
            strand,
            ".",
            attributes,
        ]
    )


def read_bed(path: Path) -> list[str]:
    return path.read_text().splitlines()


def test_multi_exon_transcript_conversion_and_exon_sorting(
    tmp_path: Path,
) -> None:
    gtf = write_gtf(
        tmp_path / "input.gtf",
        [
            "# comment rows are ignored",
            gtf_row("chr1", (201, 250), "+", 'gene_id "geneA"; transcript_id "txA";'),
            gtf_row("chr1", (101, 150), "+", 'gene_id "geneA"; transcript_id "txA";'),
        ],
    )
    bed = tmp_path / "out" / "models.bed"

    bed.parent.mkdir()
    result = run_converter(
        "--gtf",
        str(gtf),
        "--bed",
        str(bed),
    )

    assert result.returncode == 0, result.stderr
    assert read_bed(bed) == [
        "chr1\t100\t250\ttxA|geneA\t0\t+\t100\t250\t0\t2\t50,50,\t0,100,"
    ]


def test_single_exon_transcript_conversion(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "single.gtf",
        [
            gtf_row("chr2", (10, 20), "-", 'gene_id "geneB"; transcript_id "txB";'),
        ],
    )
    bed = tmp_path / "single.bed"

    result = run_converter("--gtf", str(gtf), "--bed", str(bed))

    assert result.returncode == 0
    assert read_bed(bed) == ["chr2\t9\t20\ttxB|geneB\t0\t-\t9\t20\t0\t1\t11,\t0,"]


def test_missing_gene_id_uses_transcript_only_name(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "missing_gene.gtf",
        [
            gtf_row("chr1", (1, 5), "+", 'transcript_id "txOnly";'),
        ],
    )
    bed = tmp_path / "missing_gene.bed"

    result = run_converter("--gtf", str(gtf), "--bed", str(bed))

    assert result.returncode == 0
    assert read_bed(bed)[0].split("\t")[3] == "txOnly"


def test_multiple_gene_ids_warns_and_keeps_first(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "gene_conflict.gtf",
        [
            gtf_row("chr1", (1, 5), "+", 'gene_id "gene1"; transcript_id "tx1";'),
            gtf_row("chr1", (10, 15), "+", 'gene_id "gene2"; transcript_id "tx1";'),
        ],
    )
    bed = tmp_path / "gene_conflict.bed"

    result = run_converter("--gtf", str(gtf), "--bed", str(bed))

    assert result.returncode == 0
    assert "multiple non-empty gene IDs" in result.stderr
    assert read_bed(bed)[0].split("\t")[3] == "tx1|gene1"


def test_normalization_preserves_admission_accumulation_and_warning_order(
    tmp_path: Path,
) -> None:
    gtf = write_gtf(
        tmp_path / "accumulation.gtf",
        [
            gtf_row("chr1", (1, 5), "+", 'transcript_id "keep";'),
            gtf_row(
                "chr1", ("bad", 8), "+", 'gene_id "ignored"; transcript_id "keep";'
            ),
            gtf_row("chr1", (11, 15), "+", 'gene_id "geneA"; transcript_id "keep";'),
            gtf_row("chr1", (21, 25), "+", 'gene_id "geneB"; transcript_id "keep";'),
            gtf_row("chr1", (31, 35), "+", 'gene_id "geneC"; transcript_id "keep";'),
            gtf_row("chr2", (1, 5), "+", 'gene_id "geneX"; transcript_id "drop";'),
            gtf_row("chr3", (11, 15), "+", 'gene_id "geneY"; transcript_id "drop";'),
            gtf_row("chr2", (21, 25), "-", 'gene_id "geneZ"; transcript_id "drop";'),
            "malformed",
        ],
    )
    warnings: list[str] = []

    records = normalize_gtf(gtf, warnings.append)

    assert render_bed(records) == (
        b"chr1\t0\t35\tkeep|geneA\t0\t+\t0\t35\t0\t4\t5,5,5,5,\t0,10,20,30,\n"
    )
    assert warnings == [
        "row 2: start and end must be integers; skipping row",
        "transcript 'keep' has multiple non-empty gene IDs; keeping first gene ID "
        "'geneA' and ignoring 'geneB'",
        "transcript 'drop' has multiple non-empty gene IDs; keeping first gene ID "
        "'geneX' and ignoring 'geneY'",
        "row 9: expected 9 tab-separated columns; skipping row",
        "conflicting chromosome or strand for transcript 'drop' at row 8; "
        "skipping entire transcript",
    ]


def test_nonexon_features_are_skipped_and_names_are_normalized(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "custom.gtf",
        [
            gtf_row(
                "chr3",
                (1, 5),
                "+",
                'gene_id "ignored"; transcript_id "ignored";',
                feature="CDS",
            ),
            gtf_row(
                "chr3",
                (11, 20),
                ".",
                'gene_id "gene C"; transcript_id "tx C";',
            ),
        ],
    )
    bed = tmp_path / "custom.bed"

    result = run_converter(
        "--gtf",
        str(gtf),
        "--bed",
        str(bed),
    )

    assert result.returncode == 0
    assert read_bed(bed) == ["chr3\t10\t20\ttx_C|gene_C\t0\t.\t10\t20\t0\t1\t10,\t0,"]


def test_malformed_missing_transcript_and_invalid_strand_rows_warn_and_skip(
    tmp_path: Path,
) -> None:
    gtf = write_gtf(
        tmp_path / "malformed.gtf",
        [
            "not\tenough\tcolumns",
            gtf_row("chr1", (1, 5), "*", 'gene_id "geneBad"; transcript_id "txBad";'),
            gtf_row(
                "chr1",
                (10, 15),
                "+",
                'gene_id "geneMissingTranscript";',
            ),
            gtf_row(
                "chr1",
                (20, 25),
                "+",
                'gene_id "geneGood"; transcript_id "txGood";',
            ),
        ],
    )
    bed = tmp_path / "malformed.bed"

    result = run_converter("--gtf", str(gtf), "--bed", str(bed))

    assert result.returncode == 0
    assert "expected 9 tab-separated columns" in result.stderr
    assert "invalid strand '*'" in result.stderr
    assert "missing required attribute 'transcript_id'" in result.stderr
    assert read_bed(bed)[0].split("\t")[3] == "txGood|geneGood"


def test_invalid_numeric_and_range_coordinates_warn_and_skip(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "coordinates.gtf",
        [
            gtf_row(
                "chr1",
                ("not-an-integer", 5),
                "+",
                'gene_id "bad1"; transcript_id "bad1";',
            ),
            gtf_row(
                "chr1",
                (0, 5),
                "+",
                'gene_id "bad2"; transcript_id "bad2";',
            ),
            gtf_row(
                "chr1",
                (8, 7),
                "+",
                'gene_id "bad3"; transcript_id "bad3";',
            ),
            gtf_row(
                "chr1",
                (10, 12),
                "+",
                'gene_id "good"; transcript_id "good";',
            ),
        ],
    )
    bed = tmp_path / "coordinates.bed"

    result = run_converter("--gtf", str(gtf), "--bed", str(bed))

    assert result.returncode == 0
    assert "row 1: start and end must be integers; skipping row" in result.stderr
    assert "row 2: invalid coordinates start=0 end=5; skipping row" in result.stderr
    assert "row 3: invalid coordinates start=8 end=7; skipping row" in result.stderr
    assert read_bed(bed) == ["chr1\t9\t12\tgood|good\t0\t+\t9\t12\t0\t1\t3,\t0,"]


def test_conflicting_chromosome_or_strand_skips_entire_transcript(
    tmp_path: Path,
) -> None:
    gtf = write_gtf(
        tmp_path / "conflicts.gtf",
        [
            gtf_row("chr1", (1, 5), "+", 'gene_id "geneBad"; transcript_id "txBad";'),
            gtf_row("chr2", (10, 15), "+", 'gene_id "geneBad"; transcript_id "txBad";'),
            gtf_row(
                "chr3",
                (20, 25),
                "-",
                'gene_id "geneBad2"; transcript_id "txBad2";',
            ),
            gtf_row(
                "chr3",
                (30, 35),
                "+",
                'gene_id "geneBad2"; transcript_id "txBad2";',
            ),
            gtf_row(
                "chr4",
                (40, 45),
                "+",
                'gene_id "geneGood"; transcript_id "txGood";',
            ),
        ],
    )
    bed = tmp_path / "conflicts.bed"

    result = run_converter("--gtf", str(gtf), "--bed", str(bed))

    assert result.returncode == 0
    assert "conflicting chromosome or strand for transcript 'txBad'" in result.stderr
    assert "conflicting chromosome or strand for transcript 'txBad2'" in result.stderr
    bed_lines = read_bed(bed)
    assert len(bed_lines) == 1
    assert bed_lines[0].split("\t")[3] == "txGood|geneGood"


def test_no_valid_transcripts_fails_nonzero(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "empty.gtf",
        [
            "# comments only",
            gtf_row(
                "chr1",
                (1, 5),
                "+",
                'gene_id "gene1"; transcript_id "tx1";',
                feature="gene",
            ),
        ],
    )
    bed = tmp_path / "empty.bed"

    result = run_converter("--gtf", str(gtf), "--bed", str(bed))

    assert result.returncode != 0
    assert "No valid transcripts were produced" in result.stderr
    assert not bed.exists()


def test_output_is_sorted_by_chrom_start_end_and_name(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "unsorted.gtf",
        [
            gtf_row("chr2", (1, 5), "+", 'gene_id "gene2"; transcript_id "tx2";'),
            gtf_row("chr1", (50, 60), "+", 'gene_id "geneB"; transcript_id "txB";'),
            gtf_row("chr1", (10, 20), "+", 'gene_id "geneC"; transcript_id "txC";'),
            gtf_row("chr1", (10, 20), "+", 'gene_id "geneA"; transcript_id "txA";'),
        ],
    )
    bed = tmp_path / "sorted.bed"

    result = run_converter("--gtf", str(gtf), "--bed", str(bed))

    assert result.returncode == 0
    assert [line.split("\t")[3] for line in read_bed(bed)] == [
        "txA|geneA",
        "txC|geneC",
        "txB|geneB",
        "tx2|gene2",
    ]


def test_existing_output_is_never_replaced_from_arbitrary_cwd(
    tmp_path: Path,
) -> None:
    gtf = write_gtf(
        tmp_path / "input.gtf",
        [
            gtf_row(
                "chr1",
                (1, 4),
                "+",
                'gene_id "g1"; transcript_id "tx1";',
            )
        ],
    )
    bed = tmp_path / "output" / "models.bed"
    invocation_cwd = tmp_path / "elsewhere"
    invocation_cwd.mkdir()
    bed.parent.mkdir()
    arguments = ("--gtf", str(gtf), "--bed", str(bed))

    first = run_converter(*arguments, cwd=invocation_cwd)
    first_bytes = bed.read_bytes()
    second = run_converter(*arguments, cwd=invocation_cwd)

    assert first.returncode == 0
    assert second.returncode == 1
    assert second.stdout == ""
    assert "File exists" in second.stderr
    assert bed.read_bytes() == first_bytes
    assert first_bytes == b"chr1\t0\t4\ttx1|g1\t0\t+\t0\t4\t0\t1\t4,\t0,\n"
    assert list(invocation_cwd.iterdir()) == []
