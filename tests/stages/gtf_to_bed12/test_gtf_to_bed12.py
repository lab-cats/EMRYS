import argparse
import subprocess
import sys
from pathlib import Path

import pytest

from norad.stages.gtf_to_bed12.converter import (
    PublicationOperations,
    convert_from_args,
    publish_bed,
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
            "norad",
            "convert",
            "gtf-to-bed12",
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


def test_help_interface() -> None:
    result = run_converter("--help")

    assert result.returncode == 0
    assert "--gtf" in result.stdout
    assert "--bed" in result.stdout
    assert "--feature" in result.stdout
    assert "--name-attribute" in result.stdout
    assert "--gene-attribute" in result.stdout
    assert "--run-token" in result.stdout
    assert "--execute" in result.stdout


def test_unsafe_explicit_run_token_is_rejected_before_publication(
    tmp_path: Path,
) -> None:
    gtf = write_gtf(
        tmp_path / "input.gtf",
        [gtf_row("chr1", (1, 4), "+", 'gene_id "g1"; transcript_id "tx1";')],
    )
    bed = tmp_path / "output" / "models.bed"

    result = run_converter(
        "--gtf",
        str(gtf),
        "--bed",
        str(bed),
        "--run-token",
        "../unsafe-token",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Unsafe Step 00b publication token" in result.stderr
    assert not bed.parent.exists()


def test_empty_direct_api_run_token_does_not_fall_back(tmp_path: Path) -> None:
    bed = tmp_path / "output" / "models.bed"

    with pytest.raises(ValueError, match="Unsafe Step 00b publication token"):
        publish_bed(
            b"complete payload\n",
            bed,
            run_token="",
            operations=PublicationOperations(token_factory=lambda: "fallback-token"),
        )

    assert not bed.parent.exists()


def test_multi_exon_transcript_conversion_and_exon_sorting(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "input.gtf",
        [
            "# comment rows are ignored",
            gtf_row("chr1", (201, 250), "+", 'gene_id "geneA"; transcript_id "txA";'),
            gtf_row("chr1", (101, 150), "+", 'gene_id "geneA"; transcript_id "txA";'),
        ],
    )
    bed = tmp_path / "out" / "models.bed"

    result = run_converter(
        "--gtf",
        str(gtf),
        "--bed",
        str(bed),
        "--run-token",
        "explicit-owner-00b",
        "--execute",
    )

    assert result.returncode == 0
    assert "Run token: explicit-owner-00b" in result.stdout
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

    result = run_converter("--gtf", str(gtf), "--bed", str(bed), "--execute")

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

    result = run_converter("--gtf", str(gtf), "--bed", str(bed), "--execute")

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

    result = run_converter("--gtf", str(gtf), "--bed", str(bed), "--execute")

    assert result.returncode == 0
    assert "multiple non-empty gene IDs" in result.stderr
    assert read_bed(bed)[0].split("\t")[3] == "tx1|gene1"


def test_custom_feature_and_attribute_names(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "custom.gtf",
        [
            gtf_row("chr3", (1, 5), "+", 'gene_name "ignored"; tx_name "ignored";'),
            gtf_row(
                "chr3",
                (11, 20),
                ".",
                'gene_name "gene C"; tx_name "tx C";',
                feature="CDS",
            ),
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
        "--execute",
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

    result = run_converter("--gtf", str(gtf), "--bed", str(bed), "--execute")

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

    result = run_converter("--gtf", str(gtf), "--bed", str(bed), "--execute")

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

    result = run_converter("--gtf", str(gtf), "--bed", str(bed), "--execute")

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

    result = run_converter("--gtf", str(gtf), "--bed", str(bed), "--execute")

    assert result.returncode != 0
    assert "no transcripts were written" in result.stderr
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

    result = run_converter("--gtf", str(gtf), "--bed", str(bed), "--execute")

    assert result.returncode == 0
    assert [line.split("\t")[3] for line in read_bed(bed)] == [
        "txA|geneA",
        "txC|geneC",
        "txB|geneB",
        "tx2|gene2",
    ]


def test_dry_run_is_side_effect_free_from_arbitrary_cwd(
    tmp_path: Path,
) -> None:
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    gtf = write_gtf(
        inputs / "input.gtf",
        [
            gtf_row(
                "chr1",
                (1, 5),
                "+",
                'gene_id "gene1"; transcript_id "tx1";',
            )
        ],
    )
    output = tmp_path / "outputs" / "models.bed"
    unrelated = tmp_path / "unrelated.tsv"
    unrelated.write_text("must\tremain\nunchanged\ttrue\n")
    unrelated_before = unrelated.read_bytes()
    invocation_cwd = tmp_path / "elsewhere"
    invocation_cwd.mkdir()

    result = run_converter(
        "--gtf",
        str(gtf),
        "--bed",
        str(output),
        cwd=invocation_cwd,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "Mode: dry-run" in result.stdout
    assert "Dry-run only" in result.stdout
    assert not output.parent.exists()
    assert unrelated.read_bytes() == unrelated_before


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
    arguments = ("--gtf", str(gtf), "--bed", str(bed), "--execute")

    first = run_converter(*arguments, cwd=invocation_cwd)
    first_bytes = bed.read_bytes()
    second = run_converter(*arguments, cwd=invocation_cwd)

    assert first.returncode == 0
    assert second.returncode == 1
    assert second.stdout == ""
    assert "refusing to replace" in second.stderr
    assert bed.read_bytes() == first_bytes
    assert first_bytes == b"chr1\t0\t4\ttx1|g1\t0\t+\t0\t4\t0\t1\t4,\t0,\n"
    assert list(invocation_cwd.iterdir()) == []


def test_publication_failure_cleans_owned_lock_and_stage(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "input.gtf",
        [gtf_row("chr1", (1, 4), "+", 'gene_id "g1"; transcript_id "tx1";')],
    )
    bed = tmp_path / "output" / "models.bed"
    arguments = argparse.Namespace(
        gtf=gtf,
        bed=bed,
        feature="exon",
        name_attribute="transcript_id",
        gene_attribute="gene_id",
        execute=True,
    )

    def fail_link(_staged: Path, _output: Path) -> None:
        raise OSError("controlled link failure")

    result = convert_from_args(
        arguments,
        publication_operations=PublicationOperations(
            token_factory=lambda: "controlled-failure",
            link=fail_link,
        ),
    )

    assert result == 1
    assert not bed.exists()
    assert list(bed.parent.iterdir()) == []


def test_lock_cleanup_failure_retains_lock_and_staging_residue(
    tmp_path: Path,
) -> None:
    gtf = write_gtf(
        tmp_path / "input.gtf",
        [gtf_row("chr1", (1, 4), "+", 'gene_id "g1"; transcript_id "tx1";')],
    )
    bed = tmp_path / "output" / "models.bed"
    token = "lock-cleanup-failure"
    lock = bed.parent / ".models.bed.step00b.lock"
    staged = bed.parent / f".models.bed.step00b.{token}.tmp"
    arguments = argparse.Namespace(
        gtf=gtf,
        bed=bed,
        feature="exon",
        name_attribute="transcript_id",
        gene_attribute="gene_id",
        execute=True,
    )

    def fail_lock_unlink(path: Path) -> None:
        if path == lock:
            raise OSError("controlled lock unlink failure")
        path.unlink()

    result = convert_from_args(
        arguments,
        publication_operations=PublicationOperations(
            token_factory=lambda: token,
            unlink=fail_lock_unlink,
        ),
    )

    assert result == 1
    assert not bed.exists()
    assert lock.read_text(encoding="utf-8") == f"run_token={token}\n"
    assert staged.read_bytes() == b"chr1\t0\t4\ttx1|g1\t0\t+\t0\t4\t0\t1\t4,\t0,\n"


def test_stage_cleanup_failure_retains_staging_residue(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "input.gtf",
        [gtf_row("chr1", (1, 4), "+", 'gene_id "g1"; transcript_id "tx1";')],
    )
    bed = tmp_path / "output" / "models.bed"
    token = "stage-cleanup-failure"
    lock = bed.parent / ".models.bed.step00b.lock"
    staged = bed.parent / f".models.bed.step00b.{token}.tmp"
    arguments = argparse.Namespace(
        gtf=gtf,
        bed=bed,
        feature="exon",
        name_attribute="transcript_id",
        gene_attribute="gene_id",
        execute=True,
    )

    def fail_stage_unlink(path: Path) -> None:
        if path == staged:
            raise OSError("controlled staging unlink failure")
        path.unlink()

    result = convert_from_args(
        arguments,
        publication_operations=PublicationOperations(
            token_factory=lambda: token,
            unlink=fail_stage_unlink,
        ),
    )

    assert result == 1
    assert not bed.exists()
    assert not lock.exists()
    assert staged.read_bytes() == b"chr1\t0\t4\ttx1|g1\t0\t+\t0\t4\t0\t1\t4,\t0,\n"


def test_foreign_replacement_during_lock_cleanup_is_never_deleted(
    tmp_path: Path,
) -> None:
    gtf = write_gtf(
        tmp_path / "input.gtf",
        [gtf_row("chr1", (1, 4), "+", 'gene_id "g1"; transcript_id "tx1";')],
    )
    bed = tmp_path / "output" / "models.bed"
    token = "foreign-replacement"
    lock = bed.parent / ".models.bed.step00b.lock"
    staged = bed.parent / f".models.bed.step00b.{token}.tmp"
    foreign_bytes = b"foreign final must remain\n"
    arguments = argparse.Namespace(
        gtf=gtf,
        bed=bed,
        feature="exon",
        name_attribute="transcript_id",
        gene_attribute="gene_id",
        execute=True,
    )

    def replace_final_then_fail_lock(path: Path) -> None:
        if path == lock:
            bed.unlink()
            bed.write_bytes(foreign_bytes)
            raise OSError("controlled lock unlink failure after foreign replacement")
        path.unlink()

    result = convert_from_args(
        arguments,
        publication_operations=PublicationOperations(
            token_factory=lambda: token,
            unlink=replace_final_then_fail_lock,
        ),
    )

    assert result == 1
    assert bed.read_bytes() == foreign_bytes
    assert lock.read_text(encoding="utf-8") == f"run_token={token}\n"
    assert staged.is_file()
    assert not staged.samefile(bed)


def test_interruption_residue_is_preserved_and_blocks_retry(tmp_path: Path) -> None:
    gtf = write_gtf(
        tmp_path / "input.gtf",
        [gtf_row("chr1", (1, 4), "+", 'gene_id "g1"; transcript_id "tx1";')],
    )
    bed = tmp_path / "output" / "models.bed"
    arguments = argparse.Namespace(
        gtf=gtf,
        bed=bed,
        feature="exon",
        name_attribute="transcript_id",
        gene_attribute="gene_id",
        run_token="explicit-interrupted",
        execute=True,
    )

    def interrupt_after_stage(_staged: Path, _output: Path) -> None:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        convert_from_args(
            arguments,
            publication_operations=PublicationOperations(
                token_factory=lambda: "factory-token-must-not-win",
                after_stage_write=interrupt_after_stage,
            ),
        )

    lock = bed.parent / ".models.bed.step00b.lock"
    staged = bed.parent / ".models.bed.step00b.explicit-interrupted.tmp"
    assert not bed.exists()
    assert lock.read_text(encoding="utf-8") == "run_token=explicit-interrupted\n"
    assert staged.is_file()

    retry = run_converter(
        "--gtf",
        str(gtf),
        "--bed",
        str(bed),
        "--execute",
    )

    assert retry.returncode == 1
    assert "publication lock already exists" in retry.stderr
    assert lock.is_file()
    assert staged.is_file()


def test_staging_residue_without_lock_is_preserved_and_blocks_plan(
    tmp_path: Path,
) -> None:
    gtf = write_gtf(
        tmp_path / "input.gtf",
        [gtf_row("chr1", (1, 4), "+", 'gene_id "g1"; transcript_id "tx1";')],
    )
    bed = tmp_path / "output" / "models.bed"
    bed.parent.mkdir()
    staged = bed.parent / ".models.bed.step00b.older-attempt.tmp"
    staged.write_bytes(b"preserve\n")

    result = run_converter("--gtf", str(gtf), "--bed", str(bed))

    assert result.returncode == 1
    assert result.stdout == ""
    assert "staging residue requires inspection" in result.stderr
    assert staged.read_bytes() == b"preserve\n"
    assert not bed.exists()
