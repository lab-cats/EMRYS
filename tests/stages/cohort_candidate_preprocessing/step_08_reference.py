"""Tiny-fixture Step 08 reference: plain VCF fields and finite GTF point sets.

No production imports or interval/VCF libraries. This is deliberately not a
second general-purpose parser: only the documented synthetic fixture dialect
and coordinates 1..10000 are admitted. Expectations come from raw inputs, never
from producer outputs; the public validator is a separate downstream check.
"""

from __future__ import annotations

import csv
import math
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

METADATA = (
    "partition_id candidate_id orientation chromosome position alt_index "
    "genomic_ref genomic_alt rna_ref rna_alt annotation_strand gene_ids "
    "transcript_ids is_cds is_five_prime_utr is_three_prime_utr is_exon "
    "is_intron qual filter info_alt_depth orientation_policy"
).split()
COUNTS = (
    "observed_vcf_record_count observed_alt_allele_count supported_snv_count "
    "skipped_symbolic_count skipped_non_snv_count published_candidate_count"
).split()
FEATURES = ("cds", "five_prime_utr", "three_prime_utr", "exon", "intron")
POLICY = "legacy_provisional_v1"


def read_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        return list(reader.fieldnames or ()), list(reader)


def annotation_model(path: Path) -> list[dict]:
    """Derive features using point-set arithmetic, not interval reduction."""
    grouped = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        chrom, _, feature, start, end, _, strand, _, attributes = line.split("\t")
        feature = feature.lower()
        assert feature in {"exon", "cds", "utr", "five_prime_utr", "three_prime_utr"}
        attributes = dict(
            re.findall(r'(gene_id|transcript_id) "([^";]+)";', attributes)
        )
        assert 1 <= int(start) <= int(end) <= 10000, "oracle fixture coordinate bound"
        grouped[attributes["transcript_id"]].append(
            (
                chrom,
                strand,
                attributes["gene_id"],
                feature,
                set(range(int(start), int(end) + 1)),
            )
        )
    result = []
    for transcript, records in sorted(grouped.items()):
        identities = {row[:3] for row in records}
        if len(identities) != 1:
            continue  # The contract excludes inconsistent transcripts.
        chrom, strand, gene = identities.pop()
        assert strand in {"+", "-"}
        by_feature = defaultdict(set)
        for _, _, _, feature, points in records:
            by_feature[feature].update(points)
        exon, cds = by_feature["exon"], by_feature["cds"]
        assert exon, "oracle fixture transcript requires exons"
        span = set(range(min(exon), max(exon) + 1))
        features = {"exon": exon, "intron": span - exon, "cds": cds}
        for feature in ("five_prime_utr", "three_prime_utr"):
            points = set()
            if cds:
                low_side = (feature == "five_prime_utr") == (strand == "+")
                if by_feature[feature]:
                    points = by_feature[feature]
                elif by_feature["utr"]:
                    # Fixture generic UTR intervals must lie wholly outside CDS span.
                    generic = [row[4] for row in records if row[3] == "utr"]
                    assert all(max(p) < min(cds) or min(p) > max(cds) for p in generic)
                    points = {
                        p
                        for p in by_feature["utr"]
                        if (p < min(cds) if low_side else p > max(cds))
                    }
                else:
                    points = {
                        p for p in exon if (p < min(cds) if low_side else p > max(cds))
                    }
            features[feature] = points
        result.append(
            dict(
                chrom=chrom,
                strand=strand,
                gene=gene,
                transcript=transcript,
                span=span,
                **features,
            )
        )
    return result


def annotate(model: list[dict], chromosome: str, position: int, strand: str) -> dict:
    compatible = [
        tx for tx in model if (tx["chrom"], tx["strand"]) == (chromosome, strand)
    ]
    overlapping = [tx for tx in compatible if position in tx["span"]]
    return {
        "gene_ids": ";".join(sorted({tx["gene"] for tx in overlapping})) or "NA",
        "transcript_ids": ";".join(sorted(tx["transcript"] for tx in overlapping))
        or "NA",
        **{
            f"is_{feature}": any(position in tx[feature] for tx in compatible)
            for feature in FEATURES
        },
    }


def vcf_reference(
    path: Path, samples: list[str], partition: str, orientation: str, model: list[dict]
) -> tuple[list[dict], dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header = next(line.split("\t") for line in lines if line.startswith("#CHROM\t"))
    assert header[9:] == samples, "oracle VCF/manifest sample order"
    rows = []
    counts = dict.fromkeys(COUNTS, 0)
    strand = "+" if orientation == "FWD_like" else "-"
    complement = str.maketrans("ACGT", "TGCA")
    for line in lines:
        if line.startswith("#"):
            continue
        chrom, position, _, ref, alternatives, qual, filt, info, fmt, *sample_fields = (
            line.split("\t")
        )
        ref = ref.upper()
        counts["observed_vcf_record_count"] += 1
        counts_by_sample = [
            dict(zip(fmt.split(":"), fields.split(":"), strict=True))
            for fields in sample_fields
        ]
        info_ad = dict(field.split("=", 1) for field in info.split(";"))["AD"].split(
            ","
        )
        for index, alt in enumerate(alternatives.upper().split(","), 1):
            counts["observed_alt_allele_count"] += 1
            if alt in {"", ".", "*"} or alt.startswith("<") or "[" in alt or "]" in alt:
                counts["skipped_symbolic_count"] += 1
                continue
            if (
                ref not in {"A", "C", "G", "T"}
                or alt not in {"A", "C", "G", "T"}
                or ref == alt
            ):
                counts["skipped_non_snv_count"] += 1
                continue
            counts["supported_snv_count"] += 1
            row = dict(
                partition_id=partition,
                candidate_id=f"{orientation}|{chrom}|{position}|{ref}>{alt}",
                orientation=orientation,
                chromosome=chrom,
                position=int(position),
                alt_index=index,
                genomic_ref=ref,
                genomic_alt=alt,
                rna_ref=ref.translate(complement) if strand == "+" else ref,
                rna_alt=alt.translate(complement) if strand == "+" else alt,
                annotation_strand=strand,
                **annotate(model, chrom, int(position), strand),
                qual="NA" if qual == "." else qual,
                filter=filt,
                info_alt_depth="NA" if info_ad == ["."] else int(info_ad[index]),
                orientation_policy=POLICY,
            )
            for sample, values in zip(samples, counts_by_sample, strict=True):
                depth = None if values["DP"] == "." else int(values["DP"])
                alt_depth = (
                    None if depth is None else int(values["AD"].split(",")[index])
                )
                row[f"DP__{sample}"] = depth
                row[f"AD__{sample}"] = alt_depth
                row[f"AF__{sample}"] = alt_depth / depth if depth else None
            rows.append(row)
    counts["published_candidate_count"] = len(rows)
    return rows, counts


def reference(case: Path) -> tuple[list[str], list[dict], list[dict], dict]:
    _, manifest = read_table(case / "samples.tsv")
    _, partitions = read_table(case / "partitions.tsv")
    samples = [row["sample_id"] for row in manifest]
    model = annotation_model(case / "annotation.gtf")
    sites, inputs = [], []
    for partition in partitions:
        partition_id = partition["partition_id"]
        for orientation in ("FWD_like", "REV_like"):
            vcf = (
                case
                / "step07"
                / "fixture_cohort"
                / partition_id
                / f"fixture_cohort.{partition_id}.{orientation}.mpileup.vcf"
            )
            rows, counts = vcf_reference(vcf, samples, partition_id, orientation, model)
            sites.extend(rows)
            inputs.append(
                dict(partition_id=partition_id, orientation=orientation, **counts)
            )
    summary = {key: sum(row[key] for row in inputs) for key in COUNTS}
    summary.update(
        partition_count=len(partitions),
        step07_receipt_count=len(partitions),
        input_vcf_count=len(inputs),
        sample_count=len(samples),
    )
    header = METADATA + [
        f"{prefix}__{sample}" for prefix in ("DP", "AD", "AF") for sample in samples
    ]
    return header, sites, inputs, summary


def require_rows(
    actual: list[dict[str, str]], expected: list[dict], label: str
) -> None:
    assert len(actual) == len(expected), (
        f"{label}: row count {len(actual)} != {len(expected)}"
    )
    for index, (observed, wanted) in enumerate(zip(actual, expected, strict=True), 1):
        for field, value in wanted.items():
            got = observed[field]
            if field.startswith("AF__") and value is not None:
                assert math.isclose(float(got), value, rel_tol=1e-12, abs_tol=1e-15), (
                    f"{label} row {index} {field}: {got} != {value}"
                )
            else:
                serialized = (
                    "NA"
                    if value is None
                    else str(value).upper()
                    if isinstance(value, bool)
                    else str(value)
                )
                assert got == serialized, (
                    f"{label} row {index} {field}: {got} != {serialized}"
                )


def verify(case: Path, output: Path) -> None:
    header, sites, inputs, summary = reference(case)
    actual_header, actual = read_table(output / "sites.tsv")
    assert actual_header == header, "sites: complete manifest-ordered header"
    require_rows(actual, sites, "sites")
    _, actual = read_table(output / "inputs.tsv")
    require_rows(actual, inputs, "inputs")
    for row in actual:
        assert row["declared_vcf_record_count"] == row["observed_vcf_record_count"]
    _, actual = read_table(output / "summary.tsv")
    require_rows(actual, [summary], "summary")


def validate_native(case: Path, output: Path) -> None:
    """Exercise the existing consumer separately; it supplies no oracle values."""
    report = output / "independent-reference.validation.tsv"
    subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "emrys",
            "validate",
            "cohort-candidate-preprocessing",
            "--cohort-id",
            "fixture_cohort",
            "--sample-manifest",
            str(case / "samples.tsv"),
            "--partition-manifest",
            str(case / "partitions.tsv"),
            "--annotation-gtf",
            str(case / "annotation.gtf"),
            "--step07-root",
            str(case / "step07"),
            "--sites",
            str(output / "sites.tsv"),
            "--inputs",
            str(output / "inputs.tsv"),
            "--summary",
            str(output / "summary.tsv"),
            "--output",
            str(report),
            "--execute",
        ],
        check=True,
    )
    _, rows = read_table(report)
    assert [row["check_id"] for row in rows] == [
        "output_transaction",
        "manifest_annotation_identity",
        "input_receipt_reconciliation",
        "sites_order_uniqueness",
        "summary_count_reconciliation",
    ]
    assert {row["status"] for row in rows} == {"pass"}, rows


if __name__ == "__main__":
    case, output = (Path(value).resolve(strict=True) for value in sys.argv[1:])
    verify(case, output)
    validate_native(case, output)
    print(
        "Step 08 independent raw-input reference and upstream-bound validator passed."
    )
