"""Deterministic neutral Step 08/09 fixture support.

This support contains computational inputs only. It is shared by the Step 09
contract and owner-validator suites and is not an independent science oracle.
"""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from norad.contracts.scientific_evidence import step08, step09

COHORT_ID = "cohort"
PRIMARY_ANALYSIS_ID = "analysis_primary"
SAMPLE_IDS = (
    "ABE_EV_2",
    "ABE_EV_3",
    "ABE_EV4",
    "ABE_PUM1_2",
    "ABE_PUM1_3",
    "ABE_PUM1_4",
)
PAIRINGS = (
    ("2", "ABE_EV_2", "ABE_PUM1_2"),
    ("3", "ABE_EV_3", "ABE_PUM1_3"),
    ("4", "ABE_EV4", "ABE_PUM1_4"),
)


@dataclass(frozen=True)
class FixturePaths:
    root: Path
    sample_manifest: Path
    partition_manifest: Path
    step08_sites: Path
    step08_inputs: Path
    step08_summary: Path
    step09_analysis_dir: Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_tsv(
    path: Path,
    header: Sequence[str],
    rows: Iterable[Mapping[str, str]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(header),
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def table_row(header: Sequence[str], **values: str) -> dict[str, str]:
    unexpected = set(values) - set(header)
    if unexpected:
        raise ValueError(f"Unexpected fixture column(s): {sorted(unexpected)}")
    return {column: values.get(column, "NA") for column in header}


def write_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4\n% synthetic Step 09 fixture\n%%EOF\n")


def sample_rows() -> list[dict[str, str]]:
    cases = (
        ("ABE_EV_2", "EV", "2"),
        ("ABE_EV_3", "EV", "3"),
        ("ABE_EV4", "EV", "4"),
        ("ABE_PUM1_2", "PUM1", "2"),
        ("ABE_PUM1_3", "PUM1", "3"),
        ("ABE_PUM1_4", "PUM1", "4"),
    )
    return [
        {
            "sample_id": sample,
            "r1_fastq": f"reads/{sample}_R1.fastq.gz",
            "r2_fastq": f"reads/{sample}_R2.fastq.gz",
            "strandedness": "reverse",
            "condition": condition,
            "replicate": replicate,
        }
        for sample, condition, replicate in cases
    ]


def candidate_spec(
    partition_id: str,
    candidate_id: str,
    annotation_strand: str,
    gene_ids: str,
    transcript_ids: str,
    regions: tuple[str, ...],
    dp: tuple[int, ...],
    ad: tuple[int, ...],
    test_status: str,
    call_status: str,
    means: tuple[str, str, str],
    statistics: tuple[str, str, str, str] = ("NA",) * 4,
    rna_change: str = "A>G",
) -> dict[str, object]:
    orientation, chromosome, position, genomic_change = candidate_id.split("|")
    genomic_ref, genomic_alt = genomic_change.split(">")
    rna_ref, rna_alt = rna_change.split(">")
    return {
        "partition_id": partition_id,
        "candidate_id": candidate_id,
        "orientation": orientation,
        "chromosome": chromosome,
        "position": position,
        "genomic_ref": genomic_ref,
        "genomic_alt": genomic_alt,
        "rna_ref": rna_ref,
        "rna_alt": rna_alt,
        "annotation_strand": annotation_strand,
        "gene_ids": gene_ids,
        "transcript_ids": transcript_ids,
        **{
            f"is_{region}": str(region in regions).upper()
            for region in ("cds", "five_prime_utr", "three_prime_utr", "exon", "intron")
        },
        "dp": dp,
        "ad": ad,
        "test_status": test_status,
        "call_status": call_status,
        **dict(
            zip(("mean_control_af", "mean_treatment_af", "delta"), means, strict=True)
        ),
        **dict(
            zip(
                ("cmh_statistic", "cmh_p_value", "cmh_fdr_bh", "common_odds_ratio"),
                statistics,
                strict=True,
            )
        ),
    }


def candidate_specs() -> list[dict[str, object]]:
    return [
        candidate_spec(
            "p1",
            "FWD_like|1|10|T>C",
            "+",
            "gene1;gene_overlap",
            "tx1;tx1b",
            ("cds", "exon"),
            (100,) * 6,
            (10, 12, 14, 30, 32, 34),
            "tested",
            "significant_up",
            ("0.12", "0.32", "0.20"),
            ("12.0", "0.0005", "0.0015", "3.5"),
        ),
        candidate_spec(
            "p1",
            "REV_like|1|20|A>G",
            "-",
            "gene2",
            "tx2",
            ("three_prime_utr", "exon"),
            (100,) * 6,
            (30, 28, 26, 10, 12, 14),
            "tested",
            "significant_down",
            ("0.28", "0.12", "-0.16"),
            ("10.0", "0.001", "0.0015", "0.35"),
        ),
        candidate_spec(
            "p1",
            "REV_like|1|30|C>T",
            "-",
            "gene3",
            "tx3",
            ("five_prime_utr", "exon"),
            (100,) * 6,
            (5,) * 6,
            "not_target_change",
            "not_tested",
            ("0.05", "0.05", "0"),
            rna_change="C>T",
        ),
        candidate_spec(
            "p2",
            "FWD_like|2|40|T>C",
            "+",
            "gene4",
            "tx4",
            ("intron",),
            (0, 10, 10, 10, 10, 10),
            (0, 1, 1, 2, 2, 2),
            "low_coverage",
            "not_tested",
            ("NA", "NA", "NA"),
        ),
        candidate_spec(
            "p2",
            "FWD_like|2|50|T>C",
            "+",
            "gene5",
            "tx5",
            ("intron",),
            (100,) * 6,
            (0,) * 6,
            "degenerate_table",
            "not_tested",
            ("0",) * 3,
        ),
        candidate_spec(
            "p2",
            "REV_like|2|60|A>G",
            "-",
            "NA",
            "NA",
            (),
            (100,) * 6,
            (10, 11, 12, 12, 13, 14),
            "tested",
            "effect_not_met",
            ("0.11", "0.13", "0.02"),
            ("0.5", "0.01", "0.01", "1.2"),
        ),
    ]


def step08_site_rows(header: Sequence[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for spec in candidate_specs():
        values = {
            "partition_id": str(spec["partition_id"]),
            "candidate_id": str(spec["candidate_id"]),
            "orientation": str(spec["orientation"]),
            "chromosome": str(spec["chromosome"]),
            "position": str(spec["position"]),
            "alt_index": "1",
            "genomic_ref": str(spec["genomic_ref"]),
            "genomic_alt": str(spec["genomic_alt"]),
            "rna_ref": str(spec["rna_ref"]),
            "rna_alt": str(spec["rna_alt"]),
            "annotation_strand": str(spec["annotation_strand"]),
            "gene_ids": str(spec["gene_ids"]),
            "transcript_ids": str(spec["transcript_ids"]),
            "is_cds": str(spec["is_cds"]),
            "is_five_prime_utr": str(spec["is_five_prime_utr"]),
            "is_three_prime_utr": str(spec["is_three_prime_utr"]),
            "is_exon": str(spec["is_exon"]),
            "is_intron": str(spec["is_intron"]),
            "qual": "60",
            "filter": "PASS",
            "info_alt_depth": str(sum(spec["ad"])),
            "orientation_policy": "legacy_provisional_v1",
        }
        for sample_id, dp in zip(SAMPLE_IDS, spec["dp"], strict=True):
            values[f"DP__{sample_id}"] = str(dp)
        for sample_id, ad in zip(SAMPLE_IDS, spec["ad"], strict=True):
            values[f"AD__{sample_id}"] = str(ad)
        for sample_id, dp, ad in zip(SAMPLE_IDS, spec["dp"], spec["ad"], strict=True):
            values[f"AF__{sample_id}"] = "NA" if dp == 0 else f"{ad / dp:.12g}"
        rows.append(table_row(header, **values))
    return rows


def step09_result_rows(header: Sequence[str]) -> list[dict[str, str]]:
    step08_header = (
        tuple(step08.STEP08_METADATA_HEADER)
        + tuple(f"DP__{sample}" for sample in SAMPLE_IDS)
        + tuple(f"AD__{sample}" for sample in SAMPLE_IDS)
        + tuple(f"AF__{sample}" for sample in SAMPLE_IDS)
    )
    source_rows = step08_site_rows(step08_header)
    rows: list[dict[str, str]] = []
    for spec, source in zip(candidate_specs(), source_rows, strict=True):
        min_dp = min(spec["dp"])
        mean_dp = sum(spec["dp"]) / len(spec["dp"])
        values = {
            "analysis_id": PRIMARY_ANALYSIS_ID,
            **{column: source[column] for column in step08.STEP08_METADATA_HEADER},
            "control_condition": "EV",
            "treatment_condition": "PUM1",
            "target_rna_change": "A>G",
            "replicate_count": "3",
            "test_status": str(spec["test_status"]),
            "call_status": str(spec["call_status"]),
            "background_condition": "NA",
            "background_status": "disabled",
            "min_analysis_dp": str(min_dp),
            "mean_analysis_dp": f"{mean_dp:.12g}",
            "mean_control_af": str(spec["mean_control_af"]),
            "mean_treatment_af": str(spec["mean_treatment_af"]),
            "treatment_control_difference": str(spec["delta"]),
            "max_background_af": "NA",
            "cmh_statistic": str(spec["cmh_statistic"]),
            "cmh_degrees_freedom": ("1" if spec["test_status"] == "tested" else "NA"),
            "cmh_p_value": str(spec["cmh_p_value"]),
            "cmh_fdr_bh": str(spec["cmh_fdr_bh"]),
            "common_odds_ratio": str(spec["common_odds_ratio"]),
        }
        for sample_id in SAMPLE_IDS:
            values[f"DP__{sample_id}"] = source[f"DP__{sample_id}"]
            values[f"AD__{sample_id}"] = source[f"AD__{sample_id}"]
            values[f"AF__{sample_id}"] = source[f"AF__{sample_id}"]
        rows.append(table_row(header, **values))
    return rows


def write_step09_summary(
    path: Path,
    analysis_id: str,
    sample_manifest: Path,
    partition_manifest: Path,
    step08_sites: Path,
    step08_inputs: Path,
    *,
    candidate_count: str = "6",
    tested_count: str = "3",
    significant_up: str = "1",
    significant_down: str = "1",
    min_sample_dp: str = "1",
    absolute_difference_threshold: str = "0.005",
) -> None:
    row = table_row(
        step09.STEP09_SUMMARY_HEADER,
        analysis_id=analysis_id,
        cohort_id=COHORT_ID,
        control_condition="EV",
        treatment_condition="PUM1",
        background_condition="NA",
        target_rna_change="A>G",
        replicate_count="3",
        sample_count="6",
        candidate_count=candidate_count,
        target_candidate_count="5",
        successfully_tested_count=tested_count,
        not_target_change_count="1",
        missing_counts_count="0",
        low_coverage_count="1",
        degenerate_table_count="1",
        below_mean_dp_count="0",
        background_not_passed_count="0",
        fdr_not_met_count="0",
        effect_not_met_count="1",
        significant_up_count=significant_up,
        significant_down_count=significant_down,
        sample_manifest_path=str(sample_manifest.resolve()),
        sample_manifest_sha256=sha256_file(sample_manifest),
        partition_manifest_path=str(partition_manifest.resolve()),
        partition_manifest_sha256=sha256_file(partition_manifest),
        step08_sites_path=str(step08_sites.resolve()),
        step08_sites_sha256=sha256_file(step08_sites),
        step08_inputs_path=str(step08_inputs.resolve()),
        step08_inputs_sha256=sha256_file(step08_inputs),
        min_sample_dp=min_sample_dp,
        mean_dp_threshold="50",
        fdr_threshold="0.05",
        common_or_threshold="1.2",
        absolute_difference_threshold=absolute_difference_threshold,
        background_max_fraction="0.01",
        multiple_testing_method="BH",
        cmh_alternative="two.sided",
        continuity_correction="TRUE",
        orientation_policy="legacy_provisional_v1",
    )
    write_tsv(path, step09.STEP09_SUMMARY_HEADER, [row])


def build_fixture(root: Path) -> FixturePaths:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    sample_manifest = root / "samples.tsv"
    partition_manifest = root / "partitions.tsv"
    write_tsv(
        sample_manifest,
        (
            "sample_id",
            "r1_fastq",
            "r2_fastq",
            "strandedness",
            "condition",
            "replicate",
        ),
        sample_rows(),
    )
    write_tsv(
        partition_manifest,
        ("partition_id", "selector_type", "selector_value"),
        [
            {
                "partition_id": "p1",
                "selector_type": "region",
                "selector_value": "1:1-100",
            },
            {
                "partition_id": "p2",
                "selector_type": "region",
                "selector_value": "2:1-100",
            },
        ],
    )
    annotation = root / "annotation.gtf"
    annotation.write_text(
        '1\tfixture\texon\t1\t100\t.\t+\t.\tgene_id "gene1"; transcript_id "tx1";\n',
        encoding="utf-8",
    )

    step08_dir = root / "step08"
    step08_sites = step08_dir / "cohort.step08_sites.tsv"
    step08_inputs = step08_dir / "cohort.step08_inputs.tsv"
    step08_summary = step08_dir / "cohort.step08_summary.tsv"
    sites_header = (
        tuple(step08.STEP08_METADATA_HEADER)
        + tuple(f"DP__{sample}" for sample in SAMPLE_IDS)
        + tuple(f"AD__{sample}" for sample in SAMPLE_IDS)
        + tuple(f"AF__{sample}" for sample in SAMPLE_IDS)
    )
    write_tsv(step08_sites, sites_header, step08_site_rows(sites_header))

    step07_dir = root / "step07"
    input_counts = {
        ("p1", "FWD_like"): 1,
        ("p1", "REV_like"): 2,
        ("p2", "FWD_like"): 2,
        ("p2", "REV_like"): 1,
    }
    input_rows = []
    for partition_id in ("p1", "p2"):
        receipt = step07_dir / partition_id / f"{partition_id}.receipt.tsv"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text("synthetic receipt\n", encoding="utf-8")
        for orientation in step08.ORIENTATIONS:
            vcf = step07_dir / partition_id / f"{partition_id}.{orientation}.vcf"
            vcf.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")
            count = input_counts[(partition_id, orientation)]
            input_rows.append(
                table_row(
                    step08.STEP08_INPUTS_HEADER,
                    cohort_id=COHORT_ID,
                    partition_id=partition_id,
                    selector_type="region",
                    selector_value=f"{partition_id[1:]}:1-100",
                    orientation=orientation,
                    step07_receipt_path=str(receipt.resolve()),
                    step07_receipt_sha256=sha256_file(receipt),
                    vcf_path=str(vcf.resolve()),
                    vcf_sha256=sha256_file(vcf),
                    sample_manifest_sha256=sha256_file(sample_manifest),
                    partition_manifest_sha256=sha256_file(partition_manifest),
                    annotation_gtf=str(annotation.resolve()),
                    annotation_gtf_sha256=sha256_file(annotation),
                    sample_count="6",
                    declared_vcf_record_count=str(count),
                    observed_vcf_record_count=str(count),
                    observed_alt_allele_count=str(count),
                    supported_snv_count=str(count),
                    skipped_symbolic_count="0",
                    skipped_non_snv_count="0",
                    published_candidate_count=str(count),
                    orientation_policy="legacy_provisional_v1",
                )
            )
    write_tsv(step08_inputs, step08.STEP08_INPUTS_HEADER, input_rows)
    write_tsv(
        step08_summary,
        step08.STEP08_SUMMARY_HEADER,
        [
            table_row(
                step08.STEP08_SUMMARY_HEADER,
                cohort_id=COHORT_ID,
                partition_count="2",
                step07_receipt_count="2",
                input_vcf_count="4",
                sample_count="6",
                observed_vcf_record_count="6",
                observed_alt_allele_count="6",
                supported_snv_count="6",
                skipped_symbolic_count="0",
                skipped_non_snv_count="0",
                published_candidate_count="6",
                sample_manifest_sha256=sha256_file(sample_manifest),
                partition_manifest_sha256=sha256_file(partition_manifest),
                annotation_gtf=str(annotation.resolve()),
                annotation_gtf_sha256=sha256_file(annotation),
                orientation_policy="legacy_provisional_v1",
            )
        ],
    )

    step09_root = root / "step09"
    step09_analysis_dir = step09_root / PRIMARY_ANALYSIS_ID
    result_header = (
        tuple(step09.STEP09_RESULT_HEADER)
        + tuple(f"DP__{sample}" for sample in SAMPLE_IDS)
        + tuple(f"AD__{sample}" for sample in SAMPLE_IDS)
        + tuple(f"AF__{sample}" for sample in SAMPLE_IDS)
    )
    all_sites = step09_analysis_dir / f"{PRIMARY_ANALYSIS_ID}.cmh_all_sites.tsv"
    significant_sites = (
        step09_analysis_dir / f"{PRIMARY_ANALYSIS_ID}.cmh_significant_sites.tsv"
    )
    summary = step09_analysis_dir / f"{PRIMARY_ANALYSIS_ID}.cmh_summary.tsv"
    mutation = step09_analysis_dir / f"{PRIMARY_ANALYSIS_ID}.mutation_spectrum.tsv"
    result_rows = step09_result_rows(result_header)
    write_tsv(all_sites, result_header, result_rows)
    write_tsv(
        significant_sites,
        result_header,
        [
            row
            for row in result_rows
            if row["call_status"] in {"significant_up", "significant_down"}
        ],
    )
    write_step09_summary(
        summary,
        PRIMARY_ANALYSIS_ID,
        sample_manifest,
        partition_manifest,
        step08_sites,
        step08_inputs,
    )
    mutation_rows = []
    for mutation_type in step09.CANONICAL_MUTATIONS:
        count = (
            "5" if mutation_type == "A>G" else ("1" if mutation_type == "C>T" else "0")
        )
        fraction = (
            "0.833333333333"
            if mutation_type == "A>G"
            else ("0.166666666667" if mutation_type == "C>T" else "0")
        )
        mutation_rows.append(
            table_row(
                step09.STEP09_MUTATION_HEADER,
                analysis_id=PRIMARY_ANALYSIS_ID,
                rna_ref=mutation_type[0],
                rna_alt=mutation_type[2],
                mutation_type=mutation_type,
                candidate_count=count,
                candidate_fraction=fraction,
                successfully_tested_count=("3" if mutation_type == "A>G" else "0"),
                significant_up_count=("1" if mutation_type == "A>G" else "0"),
                significant_down_count=("1" if mutation_type == "A>G" else "0"),
            )
        )
    write_tsv(mutation, step09.STEP09_MUTATION_HEADER, mutation_rows)
    write_pdf(step09_analysis_dir / f"{PRIMARY_ANALYSIS_ID}.mutation_spectrum.pdf")
    write_pdf(step09_analysis_dir / f"{PRIMARY_ANALYSIS_ID}.depth_delta.pdf")

    return FixturePaths(
        root=root,
        sample_manifest=sample_manifest,
        partition_manifest=partition_manifest,
        step08_sites=step08_sites,
        step08_inputs=step08_inputs,
        step08_summary=step08_summary,
        step09_analysis_dir=step09_analysis_dir,
    )
