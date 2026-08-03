#!/usr/bin/env python3
"""Build a deterministic synthetic Step 09c input/evidence package.

The fixture imports the production Step 09c schema constants so tests fail
immediately when a contract changes without a corresponding fixture update.
All paths and SHA-256 values are generated for the requested temporary root.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    REPO_ROOT
    / "src"
    / "norad"
    / "evidence"
    / "assemble_scientific_review_evidence_package"
    / "step_09c_scientific_validation.py"
)
REVIEW_ID = "review_fixture"
COHORT_ID = "cohort"
PRIMARY_ANALYSIS_ID = "analysis_primary"
SCIENCE_STATUSES = (
    "evidence_incomplete",
    "science_review_complete_exploratory",
)
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


def load_contract() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "norad_step09c_contract", CONTRACT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load Step 09c contract: {CONTRACT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CONTRACT = load_contract()


@dataclass(frozen=True)
class FixturePaths:
    root: Path
    review_id: str
    sample_manifest: Path
    partition_manifest: Path
    step08_sites: Path
    step08_inputs: Path
    step08_summary: Path
    step09_analysis_dir: Path
    review_plan: Path
    evidence_manifest: Path
    output_root: Path

    def command_args(self) -> list[str]:
        return [
            "--review-id",
            self.review_id,
            "--sample-manifest",
            str(self.sample_manifest),
            "--partition-manifest",
            str(self.partition_manifest),
            "--step08-sites",
            str(self.step08_sites),
            "--step08-inputs",
            str(self.step08_inputs),
            "--step08-summary",
            str(self.step08_summary),
            "--step09-analysis-dir",
            str(self.step09_analysis_dir),
            "--review-plan",
            str(self.review_plan),
            "--evidence-manifest",
            str(self.evidence_manifest),
            "--output-root",
            str(self.output_root),
        ]


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
    path.write_bytes(b"%PDF-1.4\n% synthetic Step 09c fixture\n%%EOF\n")


def sample_rows() -> list[dict[str, str]]:
    return [
        {
            "sample_id": "ABE_EV_2",
            "r1_fastq": "reads/ABE_EV_2_R1.fastq.gz",
            "r2_fastq": "reads/ABE_EV_2_R2.fastq.gz",
            "strandedness": "reverse",
            "condition": "EV",
            "replicate": "2",
        },
        {
            "sample_id": "ABE_EV_3",
            "r1_fastq": "reads/ABE_EV_3_R1.fastq.gz",
            "r2_fastq": "reads/ABE_EV_3_R2.fastq.gz",
            "strandedness": "reverse",
            "condition": "EV",
            "replicate": "3",
        },
        {
            "sample_id": "ABE_EV4",
            "r1_fastq": "reads/ABE_EV4_R1.fastq.gz",
            "r2_fastq": "reads/ABE_EV4_R2.fastq.gz",
            "strandedness": "reverse",
            "condition": "EV",
            "replicate": "4",
        },
        {
            "sample_id": "ABE_PUM1_2",
            "r1_fastq": "reads/ABE_PUM1_2_R1.fastq.gz",
            "r2_fastq": "reads/ABE_PUM1_2_R2.fastq.gz",
            "strandedness": "reverse",
            "condition": "PUM1",
            "replicate": "2",
        },
        {
            "sample_id": "ABE_PUM1_3",
            "r1_fastq": "reads/ABE_PUM1_3_R1.fastq.gz",
            "r2_fastq": "reads/ABE_PUM1_3_R2.fastq.gz",
            "strandedness": "reverse",
            "condition": "PUM1",
            "replicate": "3",
        },
        {
            "sample_id": "ABE_PUM1_4",
            "r1_fastq": "reads/ABE_PUM1_4_R1.fastq.gz",
            "r2_fastq": "reads/ABE_PUM1_4_R2.fastq.gz",
            "strandedness": "reverse",
            "condition": "PUM1",
            "replicate": "4",
        },
    ]


def candidate_specs() -> list[dict[str, object]]:
    return [
        {
            "partition_id": "p1",
            "candidate_id": "FWD_like|1|10|T>C",
            "orientation": "FWD_like",
            "chromosome": "1",
            "position": "10",
            "genomic_ref": "T",
            "genomic_alt": "C",
            "rna_ref": "A",
            "rna_alt": "G",
            "annotation_strand": "+",
            "gene_ids": "gene1;gene_overlap",
            "transcript_ids": "tx1;tx1b",
            "is_cds": "TRUE",
            "is_five_prime_utr": "FALSE",
            "is_three_prime_utr": "FALSE",
            "is_exon": "TRUE",
            "is_intron": "FALSE",
            "dp": [100, 100, 100, 100, 100, 100],
            "ad": [10, 12, 14, 30, 32, 34],
            "test_status": "tested",
            "call_status": "significant_up",
            "mean_control_af": "0.12",
            "mean_treatment_af": "0.32",
            "delta": "0.20",
            "cmh_statistic": "12.0",
            "cmh_p_value": "0.0005",
            "cmh_fdr_bh": "0.0015",
            "common_odds_ratio": "3.5",
        },
        {
            "partition_id": "p1",
            "candidate_id": "REV_like|1|20|A>G",
            "orientation": "REV_like",
            "chromosome": "1",
            "position": "20",
            "genomic_ref": "A",
            "genomic_alt": "G",
            "rna_ref": "A",
            "rna_alt": "G",
            "annotation_strand": "-",
            "gene_ids": "gene2",
            "transcript_ids": "tx2",
            "is_cds": "FALSE",
            "is_five_prime_utr": "FALSE",
            "is_three_prime_utr": "TRUE",
            "is_exon": "TRUE",
            "is_intron": "FALSE",
            "dp": [100, 100, 100, 100, 100, 100],
            "ad": [30, 28, 26, 10, 12, 14],
            "test_status": "tested",
            "call_status": "significant_down",
            "mean_control_af": "0.28",
            "mean_treatment_af": "0.12",
            "delta": "-0.16",
            "cmh_statistic": "10.0",
            "cmh_p_value": "0.001",
            "cmh_fdr_bh": "0.0015",
            "common_odds_ratio": "0.35",
        },
        {
            "partition_id": "p1",
            "candidate_id": "REV_like|1|30|C>T",
            "orientation": "REV_like",
            "chromosome": "1",
            "position": "30",
            "genomic_ref": "C",
            "genomic_alt": "T",
            "rna_ref": "C",
            "rna_alt": "T",
            "annotation_strand": "-",
            "gene_ids": "gene3",
            "transcript_ids": "tx3",
            "is_cds": "FALSE",
            "is_five_prime_utr": "TRUE",
            "is_three_prime_utr": "FALSE",
            "is_exon": "TRUE",
            "is_intron": "FALSE",
            "dp": [100, 100, 100, 100, 100, 100],
            "ad": [5, 5, 5, 5, 5, 5],
            "test_status": "not_target_change",
            "call_status": "not_tested",
            "mean_control_af": "0.05",
            "mean_treatment_af": "0.05",
            "delta": "0",
            "cmh_statistic": "NA",
            "cmh_p_value": "NA",
            "cmh_fdr_bh": "NA",
            "common_odds_ratio": "NA",
        },
        {
            "partition_id": "p2",
            "candidate_id": "FWD_like|2|40|T>C",
            "orientation": "FWD_like",
            "chromosome": "2",
            "position": "40",
            "genomic_ref": "T",
            "genomic_alt": "C",
            "rna_ref": "A",
            "rna_alt": "G",
            "annotation_strand": "+",
            "gene_ids": "gene4",
            "transcript_ids": "tx4",
            "is_cds": "FALSE",
            "is_five_prime_utr": "FALSE",
            "is_three_prime_utr": "FALSE",
            "is_exon": "FALSE",
            "is_intron": "TRUE",
            "dp": [0, 10, 10, 10, 10, 10],
            "ad": [0, 1, 1, 2, 2, 2],
            "test_status": "low_coverage",
            "call_status": "not_tested",
            "mean_control_af": "NA",
            "mean_treatment_af": "NA",
            "delta": "NA",
            "cmh_statistic": "NA",
            "cmh_p_value": "NA",
            "cmh_fdr_bh": "NA",
            "common_odds_ratio": "NA",
        },
        {
            "partition_id": "p2",
            "candidate_id": "FWD_like|2|50|T>C",
            "orientation": "FWD_like",
            "chromosome": "2",
            "position": "50",
            "genomic_ref": "T",
            "genomic_alt": "C",
            "rna_ref": "A",
            "rna_alt": "G",
            "annotation_strand": "+",
            "gene_ids": "gene5",
            "transcript_ids": "tx5",
            "is_cds": "FALSE",
            "is_five_prime_utr": "FALSE",
            "is_three_prime_utr": "FALSE",
            "is_exon": "FALSE",
            "is_intron": "TRUE",
            "dp": [100, 100, 100, 100, 100, 100],
            "ad": [0, 0, 0, 0, 0, 0],
            "test_status": "degenerate_table",
            "call_status": "not_tested",
            "mean_control_af": "0",
            "mean_treatment_af": "0",
            "delta": "0",
            "cmh_statistic": "NA",
            "cmh_p_value": "NA",
            "cmh_fdr_bh": "NA",
            "common_odds_ratio": "NA",
        },
        {
            "partition_id": "p2",
            "candidate_id": "REV_like|2|60|A>G",
            "orientation": "REV_like",
            "chromosome": "2",
            "position": "60",
            "genomic_ref": "A",
            "genomic_alt": "G",
            "rna_ref": "A",
            "rna_alt": "G",
            "annotation_strand": "-",
            "gene_ids": "NA",
            "transcript_ids": "NA",
            "is_cds": "FALSE",
            "is_five_prime_utr": "FALSE",
            "is_three_prime_utr": "FALSE",
            "is_exon": "FALSE",
            "is_intron": "FALSE",
            "dp": [100, 100, 100, 100, 100, 100],
            "ad": [10, 11, 12, 12, 13, 14],
            "test_status": "tested",
            "call_status": "effect_not_met",
            "mean_control_af": "0.11",
            "mean_treatment_af": "0.13",
            "delta": "0.02",
            "cmh_statistic": "0.5",
            "cmh_p_value": "0.01",
            "cmh_fdr_bh": "0.01",
            "common_odds_ratio": "1.2",
        },
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
        for sample_id, dp, ad in zip(
            SAMPLE_IDS, spec["dp"], spec["ad"], strict=True
        ):
            values[f"AF__{sample_id}"] = "NA" if dp == 0 else f"{ad / dp:.12g}"
        rows.append(table_row(header, **values))
    return rows


def step09_result_rows(header: Sequence[str]) -> list[dict[str, str]]:
    step08_header = tuple(CONTRACT.STEP08_METADATA_HEADER) + tuple(
        f"DP__{sample}" for sample in SAMPLE_IDS
    ) + tuple(f"AD__{sample}" for sample in SAMPLE_IDS) + tuple(
        f"AF__{sample}" for sample in SAMPLE_IDS
    )
    source_rows = step08_site_rows(step08_header)
    rows: list[dict[str, str]] = []
    for spec, source in zip(candidate_specs(), source_rows, strict=True):
        min_dp = min(spec["dp"])
        mean_dp = sum(spec["dp"]) / len(spec["dp"])
        values = {
            "analysis_id": PRIMARY_ANALYSIS_ID,
            **{column: source[column] for column in CONTRACT.STEP08_METADATA_HEADER},
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
            "cmh_degrees_freedom": (
                "1" if spec["test_status"] == "tested" else "NA"
            ),
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
        CONTRACT.STEP09_SUMMARY_HEADER,
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
    write_tsv(path, CONTRACT.STEP09_SUMMARY_HEADER, [row])


def write_evidence_tables(
    root: Path,
    step09_summary: Path,
    loo_artifacts: Mapping[str, tuple[Path, Path]],
    sensitivity_summaries: Mapping[str, Path],
) -> dict[str, Path]:
    evidence_dir = root / "evidence"
    review_date = "2026-01-10"

    orientation_path = evidence_dir / "orientation_locus_audit.tsv"
    orientation_rows = [
        table_row(
            CONTRACT.ORIENTATION_HEADER,
            review_id=REVIEW_ID,
            evidence_id="e_orientation",
            analysis_id=PRIMARY_ANALYSIS_ID,
            locus_id="locus_plus",
            candidate_id="FWD_like|1|10|T>C",
            partition_id="p1",
            orientation="FWD_like",
            chromosome="1",
            position="10",
            transcript_id="tx1",
            transcript_strand="+",
            sample_id="ABE_EV_2",
            condition="EV",
            replicate="2",
            flag_group="99",
            genomic_ref="T",
            genomic_alt="C",
            rna_ref="A",
            rna_alt="G",
            raw_dp="100",
            raw_ad="10",
            raw_ref_count="90",
            current_expected_rna_ref="A",
            current_expected_rna_alt="G",
            inverted_expected_rna_ref="T",
            inverted_expected_rna_alt="C",
            concordance_status="concordant",
            reviewer="reviewer_one",
            review_date=review_date,
            detail="Synthetic plus-strand concordance.",
        ),
        table_row(
            CONTRACT.ORIENTATION_HEADER,
            review_id=REVIEW_ID,
            evidence_id="e_orientation",
            analysis_id=PRIMARY_ANALYSIS_ID,
            locus_id="locus_minus",
            candidate_id="REV_like|1|20|A>G",
            partition_id="p1",
            orientation="REV_like",
            chromosome="1",
            position="20",
            transcript_id="tx2",
            transcript_strand="-",
            sample_id="ABE_EV_2",
            condition="EV",
            replicate="2",
            flag_group="83",
            genomic_ref="A",
            genomic_alt="G",
            rna_ref="A",
            rna_alt="G",
            raw_dp="100",
            raw_ad="30",
            raw_ref_count="70",
            current_expected_rna_ref="A",
            current_expected_rna_alt="G",
            inverted_expected_rna_ref="T",
            inverted_expected_rna_alt="C",
            concordance_status="concordant",
            reviewer="reviewer_one",
            review_date=review_date,
            detail="Synthetic minus-strand concordance.",
        ),
    ]
    write_tsv(orientation_path, CONTRACT.ORIENTATION_HEADER, orientation_rows)

    annotation_path = evidence_dir / "annotation_audit.tsv"
    cases = [
        ("audit_cds", "FWD_like|1|10|T>C", "1", "10", "FWD_like", "+", "cds"),
        (
            "audit_five_utr",
            "REV_like|1|30|C>T",
            "1",
            "30",
            "REV_like",
            "-",
            "five_prime_utr",
        ),
        (
            "audit_three_utr",
            "REV_like|1|20|A>G",
            "1",
            "20",
            "REV_like",
            "-",
            "three_prime_utr",
        ),
        ("audit_exon", "FWD_like|1|10|T>C", "1", "10", "FWD_like", "+", "exon"),
        ("audit_intron", "FWD_like|2|40|T>C", "2", "40", "FWD_like", "+", "intron"),
        (
            "audit_intergenic",
            "REV_like|2|60|A>G",
            "2",
            "60",
            "REV_like",
            "-",
            "intergenic",
        ),
        (
            "audit_overlap",
            "FWD_like|1|10|T>C",
            "1",
            "10",
            "FWD_like",
            "+",
            "overlapping_gene",
        ),
        (
            "audit_multitx",
            "FWD_like|1|10|T>C",
            "1",
            "10",
            "FWD_like",
            "+",
            "multi_transcript",
        ),
    ]
    annotation_rows = []
    for audit_id, candidate_id, chrom, pos, orientation, strand, case_type in cases:
        candidate = next(
            spec for spec in candidate_specs() if spec["candidate_id"] == candidate_id
        )
        annotation_rows.append(
            table_row(
                CONTRACT.ANNOTATION_HEADER,
                review_id=REVIEW_ID,
                evidence_id="e_annotation",
                analysis_id=PRIMARY_ANALYSIS_ID,
                audit_id=audit_id,
                candidate_id=candidate_id,
                chromosome=chrom,
                position=pos,
                orientation=orientation,
                annotation_strand=strand,
                case_type=case_type,
                observed_gene_ids=str(candidate["gene_ids"]),
                observed_transcript_ids=str(candidate["transcript_ids"]),
                observed_is_cds=str(candidate["is_cds"]),
                observed_is_five_prime_utr=str(
                    candidate["is_five_prime_utr"]
                ),
                observed_is_three_prime_utr=str(
                    candidate["is_three_prime_utr"]
                ),
                observed_is_exon=str(candidate["is_exon"]),
                observed_is_intron=str(candidate["is_intron"]),
                expected_gene_ids=str(candidate["gene_ids"]),
                expected_transcript_ids=str(candidate["transcript_ids"]),
                expected_is_cds=str(candidate["is_cds"]),
                expected_is_five_prime_utr=str(
                    candidate["is_five_prime_utr"]
                ),
                expected_is_three_prime_utr=str(
                    candidate["is_three_prime_utr"]
                ),
                expected_is_exon=str(candidate["is_exon"]),
                expected_is_intron=str(candidate["is_intron"]),
                assignment_status="match",
                ambiguity_status=(
                    "ambiguous"
                    if case_type in {"overlapping_gene", "multi_transcript"}
                    else "unambiguous"
                ),
                reviewer="reviewer_one",
                review_date=review_date,
                detail=f"Synthetic {case_type} annotation audit.",
            )
        )
    write_tsv(annotation_path, CONTRACT.ANNOTATION_HEADER, annotation_rows)

    qc_path = evidence_dir / "qc_funnel.tsv"
    qc_specs = [
        ("p1", "FWD_like", 1, 1, 1, 0, 0, 0, 0, 0, 1, 0),
        ("p1", "REV_like", 2, 1, 1, 1, 0, 0, 0, 0, 0, 1),
        ("p2", "FWD_like", 2, 2, 0, 0, 0, 1, 1, 0, 0, 0),
        ("p2", "REV_like", 1, 1, 1, 0, 0, 0, 0, 1, 0, 0),
    ]
    qc_rows = []
    for (
        partition,
        orientation,
        candidates,
        targets,
        tested,
        not_target,
        missing,
        low,
        degenerate,
        effect_not_met,
        significant_up,
        significant_down,
    ) in qc_specs:
        qc_rows.append(
            table_row(
                CONTRACT.QC_FUNNEL_HEADER,
                review_id=REVIEW_ID,
                evidence_id="e_qc",
                analysis_id=PRIMARY_ANALYSIS_ID,
                scope_type="partition_orientation",
                partition_id=partition,
                orientation=orientation,
                step07_declared_vcf_records=str(candidates),
                step08_observed_vcf_records=str(candidates),
                step08_observed_alt_alleles=str(candidates),
                step08_supported_snvs=str(candidates),
                step08_skipped_symbolic="0",
                step08_skipped_non_snv="0",
                step08_published_candidates=str(candidates),
                step09_candidates=str(candidates),
                step09_target_candidates=str(targets),
                step09_tested=str(tested),
                step09_not_target=str(not_target),
                step09_missing_counts=str(missing),
                step09_low_coverage=str(low),
                step09_degenerate=str(degenerate),
                step09_below_mean_dp="0",
                step09_background_not_passed="0",
                step09_fdr_not_met="0",
                step09_effect_not_met=str(effect_not_met),
                step09_significant_up=str(significant_up),
                step09_significant_down=str(significant_down),
                reconciliation_status="reconciled",
                detail="Synthetic partition-orientation reconciliation.",
            )
        )
    write_tsv(qc_path, CONTRACT.QC_FUNNEL_HEADER, qc_rows)

    replicate_path = evidence_dir / "replicate_effects.tsv"
    replicate_rows = []
    for candidate_id in (
        "FWD_like|1|10|T>C",
        "REV_like|1|20|A>G",
    ):
        candidate = next(
            spec for spec in candidate_specs() if spec["candidate_id"] == candidate_id
        )
        for pair_index, (replicate, control, treatment) in enumerate(PAIRINGS):
            control_index = SAMPLE_IDS.index(control)
            treatment_index = SAMPLE_IDS.index(treatment)
            control_dp = candidate["dp"][control_index]
            control_ad = candidate["ad"][control_index]
            treatment_dp = candidate["dp"][treatment_index]
            treatment_ad = candidate["ad"][treatment_index]
            control_af = control_ad / control_dp
            treatment_af = treatment_ad / treatment_dp
            difference = treatment_af - control_af
            replicate_rows.append(
                table_row(
                    CONTRACT.REPLICATE_EFFECTS_HEADER,
                    review_id=REVIEW_ID,
                    evidence_id="e_replicates",
                    analysis_id=PRIMARY_ANALYSIS_ID,
                    candidate_id=candidate_id,
                    partition_id=str(candidate["partition_id"]),
                    orientation=str(candidate["orientation"]),
                    replicate=replicate,
                    control_sample=control,
                    treatment_sample=treatment,
                    control_dp=str(control_dp),
                    control_ad=str(control_ad),
                    control_af=f"{control_af:.12g}",
                    treatment_dp=str(treatment_dp),
                    treatment_ad=str(treatment_ad),
                    treatment_af=f"{treatment_af:.12g}",
                    treatment_control_difference=f"{difference:.12g}",
                    direction_status=(
                        "concordant_up" if difference > 0 else "concordant_down"
                    ),
                    reviewer="reviewer_one",
                    review_date=review_date,
                    detail=f"Synthetic replicate effect {pair_index + 1}.",
                )
            )
    write_tsv(replicate_path, CONTRACT.REPLICATE_EFFECTS_HEADER, replicate_rows)

    sensitivity_path = evidence_dir / "sensitivity_matrix.tsv"
    sensitivity_rows = []
    sensitivity_specs = [
        (PRIMARY_ANALYSIS_ID, "TRUE", step09_summary, "primary", "3", "1", "1"),
        (
            "analysis_sensitivity_dp",
            "FALSE",
            sensitivity_summaries["analysis_sensitivity_dp"],
            "lower_dp",
            "4",
            "1",
            "1",
        ),
        (
            "analysis_sensitivity_effect",
            "FALSE",
            sensitivity_summaries["analysis_sensitivity_effect"],
            "higher_effect",
            "3",
            "1",
            "0",
        ),
    ]
    for replicate, (_, summary_path) in loo_artifacts.items():
        sensitivity_specs.append(
            (
                f"analysis_loo_{replicate}",
                "FALSE",
                summary_path,
                f"loo_{replicate}",
                "3",
                "1",
                "1",
            )
        )
    for analysis_id, is_primary, summary_path, parameter_id, tested, up, down in (
        sensitivity_specs
    ):
        sensitivity_rows.append(
            table_row(
                CONTRACT.SENSITIVITY_HEADER,
                review_id=REVIEW_ID,
                evidence_id="e_sensitivity",
                analysis_id=analysis_id,
                is_primary=is_primary,
                analysis_summary_path=str(summary_path.resolve()),
                analysis_summary_sha256=sha256_file(summary_path),
                parameter_set_id=parameter_id,
                min_sample_dp=("1" if parameter_id != "lower_dp" else "0"),
                mean_dp_threshold="50",
                fdr_threshold="0.05",
                common_or_threshold="1.2",
                absolute_difference_threshold=(
                    "0.005" if parameter_id != "higher_effect" else "0.05"
                ),
                background_condition="NA",
                background_max_fraction="0.01",
                target_rna_change="A>G",
                candidate_count="6",
                successfully_tested_count=tested,
                significant_up_count=up,
                significant_down_count=down,
                comparison_status=(
                    "primary" if is_primary == "TRUE" else "reviewed"
                ),
                reviewer="reviewer_one",
                review_date=review_date,
                detail=f"Synthetic sensitivity set {parameter_id}.",
            )
        )
    write_tsv(sensitivity_path, CONTRACT.SENSITIVITY_HEADER, sensitivity_rows)

    loo_path = evidence_dir / "leave_one_pair_out.tsv"
    loo_rows = []
    for replicate, (all_path, summary_path) in loo_artifacts.items():
        for candidate_id, primary_call, delta, common_or, fdr in (
            (
                "FWD_like|1|10|T>C",
                "significant_up",
                "0.20",
                "3.5",
                "0.0015",
            ),
            (
                "REV_like|1|20|A>G",
                "significant_down",
                "-0.16",
                "0.35",
                "0.0015",
            ),
        ):
            loo_rows.append(
                table_row(
                    CONTRACT.LEAVE_ONE_OUT_HEADER,
                    review_id=REVIEW_ID,
                    evidence_id="e_loo",
                    primary_analysis_id=PRIMARY_ANALYSIS_ID,
                    omitted_replicate=replicate,
                    analysis_id=f"analysis_loo_{replicate}",
                    all_sites_path=str(all_path.resolve()),
                    all_sites_sha256=sha256_file(all_path),
                    summary_path=str(summary_path.resolve()),
                    summary_sha256=sha256_file(summary_path),
                    candidate_id=candidate_id,
                    primary_call_status=primary_call,
                    leave_one_out_test_status="tested",
                    leave_one_out_call_status=primary_call,
                    primary_delta=delta,
                    leave_one_out_delta=delta,
                    primary_common_or=common_or,
                    leave_one_out_common_or=common_or,
                    primary_fdr=fdr,
                    leave_one_out_fdr=fdr,
                    direction_concordance="concordant",
                    reviewer="reviewer_one",
                    review_date=review_date,
                    detail="Synthetic leave-one-pair-out result.",
                )
            )
    write_tsv(loo_path, CONTRACT.LEAVE_ONE_OUT_HEADER, loo_rows)

    selection_path = evidence_dir / "candidate_selection.tsv"
    selection_specs = [
        (
            "top_up",
            "FWD_like|1|10|T>C",
            "significant_up",
            "0.0015",
            "3.5",
            "0.20",
        ),
        (
            "top_down",
            "REV_like|1|20|A>G",
            "significant_down",
            "0.0015",
            "0.35",
            "-0.16",
        ),
        (
            "discordant",
            "FWD_like|2|50|T>C",
            "not_tested",
            "NA",
            "NA",
            "0",
        ),
        (
            "near_threshold",
            "REV_like|2|60|A>G",
            "effect_not_met",
            "0.01",
            "1.2",
            "0.02",
        ),
    ]
    selection_rows = []
    for selection_set, candidate_id, call_status, fdr, common_or, delta in (
        selection_specs
    ):
        selection_rows.append(
            table_row(
                CONTRACT.CANDIDATE_SELECTION_HEADER,
                review_id=REVIEW_ID,
                evidence_id="e_selection",
                analysis_id=PRIMARY_ANALYSIS_ID,
                selection_set=selection_set,
                rank="1",
                candidate_id=candidate_id,
                selection_policy_version="candidate_selection_v1",
                selection_reason=f"Synthetic {selection_set} selection.",
                ranking_metric="cmh_fdr_bh",
                ranking_value=fdr,
                source_call_status=call_status,
                source_fdr=fdr,
                source_common_or=common_or,
                source_delta=delta,
                reviewer="reviewer_one",
                review_date=review_date,
            )
        )
    write_tsv(
        selection_path, CONTRACT.CANDIDATE_SELECTION_HEADER, selection_rows
    )

    adjudication_path = evidence_dir / "candidate_adjudication.tsv"
    adjudication_rows = []
    for selection_set, candidate_id, *_ in selection_specs:
        adjudication_rows.append(
            table_row(
                CONTRACT.CANDIDATE_ADJUDICATION_HEADER,
                review_id=REVIEW_ID,
                evidence_id="e_adjudication",
                analysis_id=PRIMARY_ANALYSIS_ID,
                candidate_id=candidate_id,
                selection_set=selection_set,
                adjudication_status=(
                    "pass"
                    if selection_set in {"top_up", "top_down"}
                    else "flag"
                ),
                coverage_status="pass",
                base_quality_status="pass",
                mapping_quality_status="pass",
                read_position_status="pass",
                splice_status="pass",
                repeat_multimapping_status="pass",
                duplicate_status="flag" if selection_set == "discordant" else "pass",
                nearby_indel_status="pass",
                annotation_status="pass",
                polymorphism_status="not_assessed",
                matched_dna_status="unavailable",
                orthogonal_evidence_status="unavailable",
                reason=f"Synthetic {selection_set} adjudication.",
                supporting_evidence_ids="e_selection",
                reviewer="reviewer_one",
                review_date=review_date,
            )
        )
    write_tsv(
        adjudication_path,
        CONTRACT.CANDIDATE_ADJUDICATION_HEADER,
        adjudication_rows,
    )

    decisions_path = evidence_dir / "decisions.tsv"
    decision_values = {
        "orientation": "provisional",
        "annotation": "collapsed_flags_accepted",
        "thresholds": "primary_defaults_retained",
        "background": "no_eligible_cohort",
        "matched_dna": "unavailable",
        "orthogonal_evidence": "unavailable",
        "adjudication": "review_recorded",
    }
    decisions_rows = []
    for dimension in CONTRACT.DECISION_DIMENSIONS:
        decisions_rows.append(
            table_row(
                CONTRACT.DECISIONS_HEADER,
                review_id=REVIEW_ID,
                evidence_id="e_decisions",
                analysis_id=PRIMARY_ANALYSIS_ID,
                decision_id=f"decision_{dimension}",
                decision_dimension=dimension,
                evidence_status="complete",
                decision_status="recorded",
                decision_value=decision_values[dimension],
                rationale=f"Synthetic recorded {dimension} decision.",
                supporting_evidence_ids="e_adjudication",
                decision_owner="owner_one",
                decision_date=review_date,
                policy_version="decision_policy_v1",
                rerun_required="FALSE",
                rerun_scope="none",
            )
        )
    write_tsv(decisions_path, CONTRACT.DECISIONS_HEADER, decisions_rows)

    limitations_path = evidence_dir / "limitations.tsv"
    limitation_rows = []
    for limitation_id, category, severity in (
        ("lim_orientation", "orientation_provisional", "high"),
        ("lim_annotation", "annotation_release_unresolved", "moderate"),
        ("lim_orthogonal", "orthogonal_evidence_unavailable", "high"),
    ):
        limitation_rows.append(
            table_row(
                CONTRACT.LIMITATIONS_HEADER,
                review_id=REVIEW_ID,
                evidence_id="e_limitations",
                analysis_id=PRIMARY_ANALYSIS_ID,
                limitation_id=limitation_id,
                limitation_category=category,
                limitation_status="active",
                severity=severity,
                description=f"Synthetic limitation: {category}.",
                impact="Results remain exploratory and provisional.",
                mitigation="Retain explicit reporting banner.",
                owner="owner_one",
                review_date=review_date,
                related_evidence_ids="e_decisions",
            )
        )
    write_tsv(limitations_path, CONTRACT.LIMITATIONS_HEADER, limitation_rows)

    computational_path = evidence_dir / "computational_validation.tsv"
    computational_rows = [
        table_row(
            CONTRACT.COMPUTATIONAL_VALIDATION_HEADER,
            review_id=REVIEW_ID,
            evidence_id="e_computational",
            analysis_id=PRIMARY_ANALYSIS_ID,
            validation_scope="local_fixture_tests",
            validation_status="passed",
            evidence_path="NA",
            evidence_sha256="NA",
            scheduler_state="NA",
            exit_code="0",
            reviewer="reviewer_one",
            evidence_date=review_date,
            notes="Synthetic local-only evidence; no cluster claim.",
        )
    ]
    write_tsv(
        computational_path,
        CONTRACT.COMPUTATIONAL_VALIDATION_HEADER,
        computational_rows,
    )

    return {
        "orientation_locus_audit": orientation_path,
        "annotation_audit": annotation_path,
        "qc_funnel": qc_path,
        "replicate_effects": replicate_path,
        "sensitivity_matrix": sensitivity_path,
        "leave_one_pair_out": loo_path,
        "candidate_selection": selection_path,
        "candidate_adjudication": adjudication_path,
        "decisions": decisions_path,
        "limitations": limitations_path,
        "computational_validation": computational_path,
    }


def build_fixture(
    root: Path,
    science_status: str = "evidence_incomplete",
) -> FixturePaths:
    if science_status not in SCIENCE_STATUSES:
        raise ValueError(
            f"science_status must be one of {', '.join(SCIENCE_STATUSES)}"
        )
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
    sites_header = tuple(CONTRACT.STEP08_METADATA_HEADER) + tuple(
        f"DP__{sample}" for sample in SAMPLE_IDS
    ) + tuple(f"AD__{sample}" for sample in SAMPLE_IDS) + tuple(
        f"AF__{sample}" for sample in SAMPLE_IDS
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
        for orientation in CONTRACT.ORIENTATIONS:
            vcf = step07_dir / partition_id / f"{partition_id}.{orientation}.vcf"
            vcf.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")
            count = input_counts[(partition_id, orientation)]
            input_rows.append(
                table_row(
                    CONTRACT.STEP08_INPUTS_HEADER,
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
    write_tsv(step08_inputs, CONTRACT.STEP08_INPUTS_HEADER, input_rows)
    write_tsv(
        step08_summary,
        CONTRACT.STEP08_SUMMARY_HEADER,
        [
            table_row(
                CONTRACT.STEP08_SUMMARY_HEADER,
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
    result_header = tuple(CONTRACT.STEP09_RESULT_HEADER) + tuple(
        f"DP__{sample}" for sample in SAMPLE_IDS
    ) + tuple(f"AD__{sample}" for sample in SAMPLE_IDS) + tuple(
        f"AF__{sample}" for sample in SAMPLE_IDS
    )
    all_sites = (
        step09_analysis_dir / f"{PRIMARY_ANALYSIS_ID}.cmh_all_sites.tsv"
    )
    significant_sites = (
        step09_analysis_dir
        / f"{PRIMARY_ANALYSIS_ID}.cmh_significant_sites.tsv"
    )
    summary = step09_analysis_dir / f"{PRIMARY_ANALYSIS_ID}.cmh_summary.tsv"
    mutation = (
        step09_analysis_dir / f"{PRIMARY_ANALYSIS_ID}.mutation_spectrum.tsv"
    )
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
    for mutation_type in CONTRACT.CANONICAL_MUTATIONS:
        count = "5" if mutation_type == "A>G" else (
            "1" if mutation_type == "C>T" else "0"
        )
        fraction = (
            "0.833333333333"
            if mutation_type == "A>G"
            else ("0.166666666667" if mutation_type == "C>T" else "0")
        )
        mutation_rows.append(
            table_row(
                CONTRACT.STEP09_MUTATION_HEADER,
                analysis_id=PRIMARY_ANALYSIS_ID,
                rna_ref=mutation_type[0],
                rna_alt=mutation_type[2],
                mutation_type=mutation_type,
                candidate_count=count,
                candidate_fraction=fraction,
                successfully_tested_count=(
                    "3" if mutation_type == "A>G" else "0"
                ),
                significant_up_count=(
                    "1" if mutation_type == "A>G" else "0"
                ),
                significant_down_count=(
                    "1" if mutation_type == "A>G" else "0"
                ),
            )
        )
    write_tsv(mutation, CONTRACT.STEP09_MUTATION_HEADER, mutation_rows)
    write_pdf(
        step09_analysis_dir / f"{PRIMARY_ANALYSIS_ID}.mutation_spectrum.pdf"
    )
    write_pdf(step09_analysis_dir / f"{PRIMARY_ANALYSIS_ID}.depth_delta.pdf")

    sensitivity_summaries: dict[str, Path] = {}
    for analysis_id, tested, up, down in (
        ("analysis_sensitivity_dp", "4", "1", "1"),
        ("analysis_sensitivity_effect", "3", "1", "0"),
    ):
        sensitivity_dir = step09_root / analysis_id
        sensitivity_path = sensitivity_dir / f"{analysis_id}.cmh_summary.tsv"
        write_step09_summary(
            sensitivity_path,
            analysis_id,
            sample_manifest,
            partition_manifest,
            step08_sites,
            step08_inputs,
            tested_count=tested,
            significant_up=up,
            significant_down=down,
            min_sample_dp=("0" if analysis_id == "analysis_sensitivity_dp" else "1"),
            absolute_difference_threshold=(
                "0.05"
                if analysis_id == "analysis_sensitivity_effect"
                else "0.005"
            ),
        )
        sensitivity_summaries[analysis_id] = sensitivity_path

    loo_artifacts: dict[str, tuple[Path, Path]] = {}
    for replicate, _, _ in PAIRINGS:
        analysis_id = f"analysis_loo_{replicate}"
        loo_dir = step09_root / analysis_id
        loo_all = loo_dir / f"{analysis_id}.cmh_all_sites.tsv"
        loo_summary = loo_dir / f"{analysis_id}.cmh_summary.tsv"
        loo_rows = []
        for row in result_rows:
            copied = dict(row)
            copied["analysis_id"] = analysis_id
            loo_rows.append(copied)
        write_tsv(loo_all, result_header, loo_rows)
        write_step09_summary(
            loo_summary,
            analysis_id,
            sample_manifest,
            partition_manifest,
            step08_sites,
            step08_inputs,
        )
        loo_artifacts[replicate] = (loo_all, loo_summary)

    evidence_paths = write_evidence_tables(
        root,
        summary,
        loo_artifacts,
        sensitivity_summaries,
    )

    review_plan = root / "review_plan.tsv"
    plan_row = table_row(
        CONTRACT.REVIEW_PLAN_HEADER,
        review_id=REVIEW_ID,
        primary_analysis_id=PRIMARY_ANALYSIS_ID,
        superseded_analysis_ids="NA",
        plan_version="review_plan_v1",
        plan_date="2026-01-01",
        reviewer="reviewer_one",
        decision_owner="owner_one",
        git_commit="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        overall_science_status=science_status,
        implementation_status="implemented",
        local_test_status="passed",
        runtime_validation_status="blocked",
        cluster_dry_run_status="not_run",
        cluster_proof_status="not_run",
        orientation_policy="legacy_provisional_v1",
        orientation_policy_version="legacy_provisional_v1",
        orientation_status="provisional",
        locus_selection_policy_version="locus_selection_v1",
        locus_selection_rule="predeclared_plus_minus_loci",
        locus_target_count="2",
        required_orientations="FWD_like,REV_like",
        required_annotation_strands="+,-",
        required_annotation_cases=(
            "cds,five_prime_utr,three_prime_utr,exon,intron,intergenic,"
            "overlapping_gene,multi_transcript"
        ),
        candidate_selection_policy_version="candidate_selection_v1",
        candidate_selection_rule=(
            "one_each_top_up_top_down_discordant_near_threshold"
        ),
        top_up_count="1",
        top_down_count="1",
        discordant_count="1",
        near_threshold_count="1",
        sensitivity_policy_version="sensitivity_v1",
        sensitivity_rule="primary_plus_predeclared_dp_and_effect_sets",
        sensitivity_analysis_ids=(
            "analysis_sensitivity_dp,analysis_sensitivity_effect,"
            "analysis_loo_2,analysis_loo_3,analysis_loo_4"
        ),
        leave_one_pair_out_rule="omit_each_manifest_replicate_once",
        background_policy_version="background_v1",
        annotation_policy_version="annotation_v1",
        adjudication_policy_version="adjudication_v1",
        software_versions="python=fixture;step09c=local",
        review_completed_date=(
            "2026-01-10"
            if science_status == "science_review_complete_exploratory"
            else "NA"
        ),
        notes="Synthetic fixture; never production scientific evidence.",
    )
    write_tsv(review_plan, CONTRACT.REVIEW_PLAN_HEADER, [plan_row])

    evidence_manifest = root / "evidence_manifest.tsv"
    evidence_ids = {
        "orientation_locus_audit": "e_orientation",
        "annotation_audit": "e_annotation",
        "qc_funnel": "e_qc",
        "replicate_effects": "e_replicates",
        "sensitivity_matrix": "e_sensitivity",
        "leave_one_pair_out": "e_loo",
        "candidate_selection": "e_selection",
        "candidate_adjudication": "e_adjudication",
        "decisions": "e_decisions",
        "limitations": "e_limitations",
        "computational_validation": "e_computational",
    }
    evidence_rows = []
    for category in tuple(CONTRACT.CATEGORY_ORDER) + ("computational_validation",):
        source_path = evidence_paths[category]
        with source_path.open("r", encoding="utf-8", newline="") as stream:
            row_count = sum(1 for _ in csv.reader(stream, delimiter="\t")) - 1
        evidence_rows.append(
            table_row(
                CONTRACT.EVIDENCE_MANIFEST_HEADER,
                evidence_id=evidence_ids[category],
                evidence_category=category,
                analysis_id=PRIMARY_ANALYSIS_ID,
                source_path=str(source_path.relative_to(root)),
                source_sha256=sha256_file(source_path),
                source_row_count=str(row_count),
                evidence_status="complete",
                not_applicable_reason="NA",
                reviewer="reviewer_one",
                owner="owner_one",
                evidence_date="2026-01-10",
                policy_version=f"{category}_v1",
            )
        )
    write_tsv(
        evidence_manifest, CONTRACT.EVIDENCE_MANIFEST_HEADER, evidence_rows
    )

    return FixturePaths(
        root=root,
        review_id=REVIEW_ID,
        sample_manifest=sample_manifest,
        partition_manifest=partition_manifest,
        step08_sites=step08_sites,
        step08_inputs=step08_inputs,
        step08_summary=step08_summary,
        step09_analysis_dir=step09_analysis_dir,
        review_plan=review_plan,
        evidence_manifest=evidence_manifest,
        output_root=root / "output",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a dynamically hashed synthetic Step 09c fixture."
    )
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument(
        "--science-status",
        choices=SCIENCE_STATUSES,
        default="evidence_incomplete",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fixture = build_fixture(args.root, args.science_status)
    print(f"Built Step 09c fixture: {fixture.root}")
    print(f"Review ID: {fixture.review_id}")
    print(f"Science status: {args.science_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
