import subprocess
import sys
from pathlib import Path
from typing import List, Union


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "gtf_to_bed12.py"


def run_converter(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_gtf(path: Path, lines: List[str]) -> Path:
    path.write_text("\n".join(lines) + "\n")
    return path


def gtf_row(
    chrom: str,
    feature: str,
    start: Union[int, str],
    end: Union[int, str],
    strand: str,
    attributes: str,
) -> str:
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


def read_bed(path: Path) -> List[str]:
    return path.read_text().splitlines()


def test_help_interface() -> None:
    result = run_converter("--help")

    assert result.returncode == 0
    assert "--gtf" in result.stdout
    assert "--bed" in result.stdout
    assert "--feature" in result.stdout
    assert "--name-attribute" in result.stdout
    assert "--gene-attribute" in result.stdout


def test_multi_exon_transcript_conversion_and_exon_sorting(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "input.gtf",
        [
            "# comment rows are ignored",
            gtf_row("chr1", "exon", 201, 250, "+", 'gene_id "geneA"; transcript_id "txA";'),
            gtf_row("chr1", "exon", 101, 150, "+", 'gene_id "geneA"; transcript_id "txA";'),
        ],
    )
    bed = tmp_path / "out" / "models.bed"

    result = run_converter("--gtf", str(gtf), "--bed", str(bed))

    assert result.returncode == 0
    assert read_bed(bed) == [
        "chr1\t100\t250\ttxA|geneA\t0\t+\t100\t250\t0\t2\t50,50,\t0,100,"
    ]


def test_single_exon_transcript_conversion(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "single.gtf",
        [
            gtf_row("chr2", "exon", 10, 20, "-", 'gene_id "geneB"; transcript_id "txB";'),
        ],
    )
    bed = tmp_path / "single.bed"

    result = run_converter("--gtf", str(gtf), "--bed", str(bed))

    assert result.returncode == 0
    assert read_bed(bed) == [
        "chr2\t9\t20\ttxB|geneB\t0\t-\t9\t20\t0\t1\t11,\t0,"
    ]


def test_missing_gene_id_uses_transcript_only_name(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "missing_gene.gtf",
        [
            gtf_row("chr1", "exon", 1, 5, "+", 'transcript_id "txOnly";'),
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
            gtf_row("chr1", "exon", 1, 5, "+", 'gene_id "gene1"; transcript_id "tx1";'),
            gtf_row("chr1", "exon", 10, 15, "+", 'gene_id "gene2"; transcript_id "tx1";'),
        ],
    )
    bed = tmp_path / "gene_conflict.bed"

    result = run_converter("--gtf", str(gtf), "--bed", str(bed))

    assert result.returncode == 0
    assert "multiple non-empty gene IDs" in result.stderr
    assert read_bed(bed)[0].split("\t")[3] == "tx1|gene1"


def test_custom_feature_and_attribute_names(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "custom.gtf",
        [
            gtf_row("chr3", "exon", 1, 5, "+", 'gene_name "ignored"; tx_name "ignored";'),
            gtf_row("chr3", "CDS", 11, 20, ".", 'gene_name "gene C"; tx_name "tx C";'),
        ],
    )
    bed = tmp_path / "custom.bed"

    result = run_converter(
        "--gtf",
        str(gtf),
        "--bed",
        str(bed),
        "--feature",
        "CDS",
        "--name-attribute",
        "tx_name",
        "--gene-attribute",
        "gene_name",
    )

    assert result.returncode == 0
    assert read_bed(bed) == [
        "chr3\t10\t20\ttx_C|gene_C\t0\t.\t10\t20\t0\t1\t10,\t0,"
    ]


def test_malformed_missing_transcript_and_invalid_strand_rows_warn_and_skip(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "malformed.gtf",
        [
            "not\tenough\tcolumns",
            gtf_row("chr1", "exon", 1, 5, "*", 'gene_id "geneBad"; transcript_id "txBad";'),
            gtf_row("chr1", "exon", 10, 15, "+", 'gene_id "geneMissingTranscript";'),
            gtf_row("chr1", "exon", 20, 25, "+", 'gene_id "geneGood"; transcript_id "txGood";'),
        ],
    )
    bed = tmp_path / "malformed.bed"

    result = run_converter("--gtf", str(gtf), "--bed", str(bed))

    assert result.returncode == 0
    assert "expected 9 tab-separated columns" in result.stderr
    assert "invalid strand '*'" in result.stderr
    assert "missing required attribute 'transcript_id'" in result.stderr
    assert read_bed(bed)[0].split("\t")[3] == "txGood|geneGood"


def test_conflicting_chromosome_or_strand_skips_entire_transcript(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "conflicts.gtf",
        [
            gtf_row("chr1", "exon", 1, 5, "+", 'gene_id "geneBad"; transcript_id "txBad";'),
            gtf_row("chr2", "exon", 10, 15, "+", 'gene_id "geneBad"; transcript_id "txBad";'),
            gtf_row("chr3", "exon", 20, 25, "-", 'gene_id "geneBad2"; transcript_id "txBad2";'),
            gtf_row("chr3", "exon", 30, 35, "+", 'gene_id "geneBad2"; transcript_id "txBad2";'),
            gtf_row("chr4", "exon", 40, 45, "+", 'gene_id "geneGood"; transcript_id "txGood";'),
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
            gtf_row("chr1", "gene", 1, 5, "+", 'gene_id "gene1"; transcript_id "tx1";'),
        ],
    )
    bed = tmp_path / "empty.bed"

    result = run_converter("--gtf", str(gtf), "--bed", str(bed))

    assert result.returncode != 0
    assert "no transcripts were written" in result.stderr
    assert not bed.exists()


def test_output_is_sorted_by_chrom_start_end_and_name(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "unsorted.gtf",
        [
            gtf_row("chr2", "exon", 1, 5, "+", 'gene_id "gene2"; transcript_id "tx2";'),
            gtf_row("chr1", "exon", 50, 60, "+", 'gene_id "geneB"; transcript_id "txB";'),
            gtf_row("chr1", "exon", 10, 20, "+", 'gene_id "geneC"; transcript_id "txC";'),
            gtf_row("chr1", "exon", 10, 20, "+", 'gene_id "geneA"; transcript_id "txA";'),
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
