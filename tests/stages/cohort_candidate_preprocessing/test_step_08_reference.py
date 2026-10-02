import builtins
import csv
import importlib
import runpy
from pathlib import Path

import pytest

OWNER = Path(__file__).parent
ORACLE = importlib.import_module(
    "tests.stages.cohort_candidate_preprocessing.step_08_reference"
)
HEADER = (
    "partition_id candidate_id orientation chromosome position alt_index "
    "genomic_ref genomic_alt rna_ref rna_alt annotation_strand gene_ids "
    "transcript_ids is_cds is_five_prime_utr is_three_prime_utr is_exon "
    "is_intron qual filter info_alt_depth orientation_policy DP__z DP__a "
    "AD__z AD__a AF__z AF__a"
).split()
GOLDEN = [
    "z FWD_like|1|15|A>G FWD_like 1 15 1 A G T C + gA;gZ tA;tZ TRUE FALSE FALSE TRUE FALSE 60 q10 7 legacy_provisional_v1 10 20 2 5 0.2 0.25",
    "z FWD_like|1|15|A>T FWD_like 1 15 2 A T T A + gA;gZ tA;tZ TRUE FALSE FALSE TRUE FALSE 60 q10 10 legacy_provisional_v1 10 20 3 7 0.3 0.35",
    "a REV_like|1|25|C>T REV_like 1 25 1 C T C T - gM tM TRUE FALSE FALSE TRUE FALSE NA PASS 0 legacy_provisional_v1 NA 0 NA 0 NA NA",
]


def write_table(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


@pytest.fixture
def case(tmp_path):
    write_table(tmp_path / "samples.tsv", ["sample_id"], [["z"], ["a"]])
    write_table(tmp_path / "partitions.tsv", ["partition_id"], [["z"], ["a"]])
    features = [
        ("+", "gZ", "tZ", "exon", 10, 20),
        ("+", "gZ", "tZ", "exon", 30, 40),
        ("+", "gZ", "tZ", "CDS", 14, 18),
        ("+", "gZ", "tZ", "CDS", 30, 35),
        ("+", "gZ", "tZ", "five_prime_UTR", 10, 12),
        ("+", "gZ", "tZ", "UTR", 36, 40),
        ("+", "gA", "tA", "exon", 15, 16),
        ("-", "gM", "tM", "exon", 20, 30),
        ("-", "gM", "tM", "CDS", 24, 26),
        ("-", "gM", "tM", "five_prime_UTR", 28, 30),
        ("-", "gM", "tM", "three_prime_UTR", 20, 23),
    ]
    (tmp_path / "annotation.gtf").write_text(
        "".join(
            f'1\tfixture\t{feature}\t{start}\t{end}\t.\t{strand}\t.\tgene_id "{gene}"; transcript_id "{tx}";\n'
            for strand, gene, tx, feature, start, end in features
        )
    )
    for partition in ("z", "a"):
        root = tmp_path / "step07" / "fixture_cohort" / partition
        root.mkdir(parents=True)
        for orientation in ("FWD_like", "REV_like"):
            rows = ""
            if (partition, orientation) == ("z", "FWD_like"):
                rows = "1\t15\t.\tA\tG,T,<DEL>,AT\t60\tq10\tAD=20,7,10,2,1\tDP:AD\t10:3,2,3,1,1\t20:8,5,7,0,0\n"
            elif (partition, orientation) == ("a", "REV_like"):
                rows = "1\t25\t.\tC\tT\t.\tPASS\tAD=0,0\tDP:AD\t.:.,.\t0:0,0\n"
            (root / f"fixture_cohort.{partition}.{orientation}.mpileup.vcf").write_text(
                "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tz\ta\n"
                + rows
            )
    return tmp_path


def test_raw_inputs_match_literal_complete_rows_and_counts(case):
    header, sites, inputs, summary = ORACLE.reference(case)
    assert header == HEADER
    ORACLE.require_rows(
        [dict(zip(HEADER, row.split(), strict=True)) for row in GOLDEN],
        sites,
        "literal golden",
    )
    assert [(row["partition_id"], row["orientation"]) for row in inputs] == [
        ("z", "FWD_like"),
        ("z", "REV_like"),
        ("a", "FWD_like"),
        ("a", "REV_like"),
    ]
    assert [[row[key] for key in ORACLE.COUNTS] for row in inputs] == [
        [1, 4, 2, 1, 1, 2],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [1, 1, 1, 0, 0, 1],
    ]
    assert summary == dict(
        observed_vcf_record_count=2,
        observed_alt_allele_count=5,
        supported_snv_count=3,
        skipped_symbolic_count=1,
        skipped_non_snv_count=1,
        published_candidate_count=3,
        partition_count=2,
        step07_receipt_count=2,
        input_vcf_count=4,
        sample_count=2,
    )


def test_annotation_point_sets_preserve_distinct_feature_boundaries(case):
    model = ORACLE.annotation_model(case / "annotation.gtf")
    assert ORACLE.annotate(model, "1", 25, "+")["is_intron"]
    assert ORACLE.annotate(model, "1", 12, "+")["is_five_prime_utr"]
    assert not ORACLE.annotate(model, "1", 13, "+")[
        "is_five_prime_utr"
    ]  # explicit outranks fallback
    assert ORACLE.annotate(model, "1", 37, "+")["is_three_prime_utr"]
    assert ORACLE.annotate(model, "1", 21, "-")["is_three_prime_utr"]
    assert ORACLE.annotate(model, "1", 29, "-")["is_five_prime_utr"]
    assert ORACLE.annotate(model, "other", 15, "+") == dict(
        gene_ids="NA",
        transcript_ids="NA",
        is_cds=False,
        is_five_prime_utr=False,
        is_three_prime_utr=False,
        is_exon=False,
        is_intron=False,
    )
    gtf = case / "annotation.gtf"
    gtf.write_text(
        "\n".join(line for line in gtf.read_text().splitlines() if "UTR" not in line)
        + "\n"
    )
    fallback = ORACLE.annotation_model(gtf)
    assert ORACLE.annotate(fallback, "1", 13, "+")["is_five_prime_utr"]
    assert ORACLE.annotate(fallback, "1", 27, "-")["is_five_prime_utr"]
    assert ORACLE.annotate(fallback, "1", 23, "-")["is_three_prime_utr"]


def test_oracle_rejects_production_imports(case, monkeypatch):
    real_import = builtins.__import__

    def independent_import(name, *args, **kwargs):
        if name.startswith(("emrys", "scripts")):
            raise AssertionError(f"production import in independent reference: {name}")
        return real_import(name, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "__import__", independent_import)
        namespace = runpy.run_path(
            str(OWNER / "step_08_reference.py"), run_name="reference_probe"
        )
        namespace["reference"](case)


@pytest.mark.parametrize(
    "mutation",
    ["allele", "counts", "annotation", "row_order", "sample_order", "totals"],
)
def test_reference_rejects_coherent_or_structural_output_corruption(case, mutation):
    output = case / "output"
    output.mkdir()
    header, _, inputs, summary = ORACLE.reference(case)
    rows = [row.split() for row in GOLDEN]
    for row in inputs:
        row["declared_vcf_record_count"] = row["observed_vcf_record_count"]
    write_table(output / "sites.tsv", header, rows)
    write_table(
        output / "inputs.tsv", list(inputs[0]), [list(row.values()) for row in inputs]
    )
    write_table(output / "summary.tsv", list(summary), [list(summary.values())])
    ORACLE.verify(case, output)
    if mutation == "allele":
        rows[0][header.index("rna_alt")] = "G"
    elif (
        mutation == "counts"
    ):  # Internally consistent AD/AF still disagrees with source counts.
        rows[0][header.index("AD__z")] = "4"
        rows[0][header.index("AF__z")] = "0.4"
    elif mutation == "annotation":
        rows[0][header.index("gene_ids")] = "gZ"
    elif mutation == "row_order":
        rows.reverse()
    elif mutation == "sample_order":
        header[-2:] = reversed(header[-2:])
    else:
        summary["published_candidate_count"] += 1
        write_table(output / "summary.tsv", list(summary), [list(summary.values())])
    write_table(output / "sites.tsv", header, rows)
    with pytest.raises(AssertionError):
        ORACLE.verify(case, output)
