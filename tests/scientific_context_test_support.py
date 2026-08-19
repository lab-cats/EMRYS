"""Deterministic synthetic scientific-context records for independent tests."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

from norad.contracts.scientific_evidence import scientific_context as CONTEXT
from norad.contracts.scientific_evidence.step08 import sha256_file


@dataclass(frozen=True, slots=True)
class ContextFixture:
    receipt: Path
    candidate_context: Path
    motif_hits: Path
    sequence_logo: Path
    motif_statistics: Path
    reference_fasta: Path
    reference_fai: Path
    motif_catalog: Path


def write_tsv(
    path: Path,
    header: tuple[str, ...],
    rows: list[dict[str, str]],
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
        writer.writerows(rows)


def replace_cell(path: Path, row_index: int, column: str, value: str) -> None:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    rows[row_index][column] = value
    write_tsv(path, header, rows)


def candidate_row(
    candidate_id: str,
    population: str,
    sequence: str,
    *,
    analysis_id: str = "analysis",
    chromosome: str = "1",
    display_rank: str = "NA",
    position: int = 101,
    contig_length: int = 201,
    genomic_change: tuple[str, str] = ("A", "G"),
    action: str = "identity",
) -> dict[str, str]:
    start = max(1, position - CONTEXT.CONTEXT_RADIUS)
    end = min(contig_length, position + CONTEXT.CONTEXT_RADIUS)
    edit_offset = position - start if action == "identity" else end - position
    genomic_ref, genomic_alt = genomic_change
    complements = {"A": "T", "C": "G", "G": "C", "T": "A"}
    rna_ref, rna_alt = (
        (genomic_ref, genomic_alt)
        if action == "identity"
        else (complements[genomic_ref], complements[genomic_alt])
    )
    return {
        "analysis_id": analysis_id,
        "candidate_id": candidate_id,
        "population": population,
        "display_rank": display_rank,
        "chromosome": chromosome,
        "position": str(position),
        "contig_length": str(contig_length),
        "genomic_ref": genomic_ref,
        "genomic_alt": genomic_alt,
        "rna_ref": rna_ref,
        "rna_alt": rna_alt,
        "orientation_action": action,
        "window_start_1based": str(start),
        "window_end_1based": str(end),
        "edit_offset_0based": str(edit_offset),
        "context_status": (
            "available" if len(sequence) == 201 else "boundary_truncated"
        ),
        "oriented_sequence": sequence,
    }


def sequence_with_hit(has_hit: bool) -> str:
    sequence = list("A" * 201)
    if has_hit:
        sequence[105:111] = "TGTACA"  # start +5, midpoint +7.5
    return "".join(sequence)


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    row_one = a + b
    row_two = c + d
    column_one = a + c
    denominator = math.comb(row_one + row_two, column_one)

    def probability(value: int) -> float:
        return (
            math.comb(row_one, value)
            * math.comb(row_two, column_one - value)
            / denominator
        )

    observed = probability(a)
    return sum(
        probability(value)
        for value in range(max(0, column_one - row_two), min(row_one, column_one) + 1)
        if probability(value) <= observed * (1 + 1e-7) + 1e-15
    )


def build_derived_rows(
    candidates: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    analysis_id = candidates[0]["analysis_id"] if candidates else "analysis"
    bases = ("A", "C", "G", "T")
    populations = CONTEXT.CONTEXT_POPULATIONS
    minimum = CONTEXT.POPULATION_MINIMUM_COUNTS
    analyzable = {
        population: sum(
            row["population"] == population and row["context_status"] == "available"
            for row in candidates
        )
        for population in populations
    }
    eligible = {
        population: sum(row["population"] == population for row in candidates)
        for population in populations
    }
    hits: list[dict[str, str]] = []
    hits_by_population = {population: 0 for population in populations}
    candidates_with = {population: 0 for population in populations}
    for row in candidates:
        if row["context_status"] != "available":
            continue
        population = row["population"]
        sequence = row["oriented_sequence"]
        found = False
        for index in range(len(sequence) - 5):
            matched = sequence[index : index + 6]
            if not (
                matched[:4] == "TGTA" and matched[4] in bases and matched[5] == "A"
            ):
                continue
            start = index - int(row["edit_offset_0based"])
            midpoint = start + 2.5
            bin_start = math.floor((midpoint + 100) / 10) * 10 - 100
            hits.append(
                {
                    "analysis_id": analysis_id,
                    "candidate_id": row["candidate_id"],
                    "population": population,
                    "motif_id": "PUM_UGUANA",
                    "matched_sequence": matched,
                    "start_offset": str(start),
                    "end_offset": str(start + 5),
                    "midpoint_offset": f"{midpoint:.1f}",
                    "bin_start": str(bin_start),
                    "bin_end": str(bin_start + 10),
                }
            )
            hits_by_population[population] += 1
            found = True
        candidates_with[population] += found

    logo: list[dict[str, str]] = []
    for population in populations:
        population_rows = [
            row
            for row in candidates
            if row["population"] == population and row["context_status"] == "available"
        ]
        status = (
            "available"
            if len(population_rows) >= minimum[population]
            else "population_below_minimum"
        )
        for relative in range(-10, 11):
            observed = [
                row["oriented_sequence"][int(row["edit_offset_0based"]) + relative]
                for row in population_rows
            ]
            observed_count = sum(base in bases for base in observed)
            for base in bases:
                count = observed.count(base)
                logo.append(
                    {
                        "analysis_id": analysis_id,
                        "population": population,
                        "availability_status": status,
                        "relative_position": str(relative),
                        "base": base,
                        "candidate_count": str(len(population_rows)),
                        "observed_base_count": str(observed_count),
                        "base_count": str(count),
                        "base_fraction": (
                            "NA"
                            if observed_count == 0
                            else f"{count / observed_count:.12g}"
                        ),
                    }
                )

    foreground = analyzable["significant_up"]
    background = analyzable["background"]
    foreground_with = candidates_with["significant_up"]
    background_with = candidates_with["background"]
    if foreground < 10:
        enrichment_status = "population_below_minimum"
    elif background < 20:
        enrichment_status = "background_below_minimum"
    elif foreground_with + background_with in (0, foreground + background):
        enrichment_status = "uninformative_table"
    else:
        enrichment_status = "available"
    standard_available = (
        foreground == 10
        and background == 20
        and foreground_with == 5
        and background_with == 2
    )
    statistics = [
        {
            "analysis_id": analysis_id,
            "motif_id": "PUM_UGUANA",
            "population": "significant_up",
            "statistic_type": "enrichment",
            "availability_status": enrichment_status,
            "bin_start": "NA",
            "bin_end": "NA",
            "eligible_candidate_count": str(eligible["significant_up"]),
            "analyzable_candidate_count": str(foreground),
            "candidate_with_motif_count": str(foreground_with),
            "hit_count": str(hits_by_population["significant_up"]),
            "background_candidate_count": str(background),
            "background_with_motif_count": str(background_with),
            "odds_ratio": "8.2032507913135131" if standard_available else "NA",
            "odds_ratio_ci95_lower": (
                "0.99085835216927842" if standard_available else "NA"
            ),
            "odds_ratio_ci95_upper": (
                "111.30151186108532" if standard_available else "NA"
            ),
            "fisher_p_value_two_sided": (
                f"{fisher_two_sided(5, 5, 2, 18):.17g}" if standard_available else "NA"
            ),
            "fisher_p_value_bh": "NA",
        }
    ]
    for population in populations:
        status = (
            "available"
            if analyzable[population] >= minimum[population]
            else "population_below_minimum"
        )
        for bin_start in range(-100, 100, 10):
            hits_in_bin = sum(
                row["population"] == population and int(row["bin_start"]) == bin_start
                for row in hits
            )
            statistics.append(
                {
                    "analysis_id": analysis_id,
                    "motif_id": "PUM_UGUANA",
                    "population": population,
                    "statistic_type": "position_bin",
                    "availability_status": status,
                    "bin_start": str(bin_start),
                    "bin_end": str(bin_start + 10),
                    "eligible_candidate_count": str(eligible[population]),
                    "analyzable_candidate_count": str(analyzable[population]),
                    "candidate_with_motif_count": str(hits_in_bin),
                    "hit_count": str(hits_in_bin),
                    "background_candidate_count": "NA",
                    "background_with_motif_count": "NA",
                    "odds_ratio": "NA",
                    "odds_ratio_ci95_lower": "NA",
                    "odds_ratio_ci95_upper": "NA",
                    "fisher_p_value_two_sided": "NA",
                    "fisher_p_value_bh": "NA",
                }
            )
    return hits, logo, statistics


def write_outputs(
    root: Path,
    candidates: list[dict[str, str]],
) -> tuple[dict[str, Path], dict[str, list[dict[str, str]]]]:
    hits, logo, statistics = build_derived_rows(candidates)
    output_rows = {
        "candidate_context": candidates,
        "motif_hits": hits,
        "sequence_logo": logo,
        "motif_statistics": statistics,
    }
    output_headers = {
        "candidate_context": CONTEXT.CANDIDATE_CONTEXT_HEADER,
        "motif_hits": CONTEXT.MOTIF_HITS_HEADER,
        "sequence_logo": CONTEXT.SEQUENCE_LOGO_HEADER,
        "motif_statistics": CONTEXT.MOTIF_STATISTICS_HEADER,
    }
    paths: dict[str, Path] = {}
    for name, rows in output_rows.items():
        path = (root / f"{name}.tsv").resolve()
        write_tsv(path, output_headers[name], rows)
        paths[name] = path
    return paths, output_rows


def build_outputs(root: Path) -> dict[str, Path]:
    candidates: list[dict[str, str]] = []
    populations = (("significant_up", 10), ("background", 20), ("significant_down", 10))
    motif_counts = {"significant_up": 5, "background": 2, "significant_down": 1}
    for population, count in populations:
        for index in range(count):
            candidates.append(
                candidate_row(
                    f"{population}_{index:02d}",
                    population,
                    sequence_with_hit(index < motif_counts[population]),
                    display_rank=(
                        str(index + 1)
                        if population == "significant_up" and index < 8
                        else "NA"
                    ),
                )
            )
    return write_outputs(root, candidates)[0]


def _fai_lengths(path: Path) -> dict[str, int]:
    lengths: dict[str, int] = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            fields = line.rstrip("\n").split("\t")
            if len(fields) >= 2:
                lengths[fields[0]] = int(fields[1])
    return lengths


def _fasta_sequences(path: Path) -> dict[str, str]:
    sequences: dict[str, list[str]] = {}
    current: str | None = None
    with path.open(encoding="ascii") as stream:
        for line in stream:
            text = line.strip()
            if text.startswith(">"):
                current = text[1:].split()[0]
                sequences[current] = []
            elif current is not None:
                sequences[current].append(text.upper())
    return {name: "".join(parts) for name, parts in sequences.items()}


def build_transaction(
    root: Path,
    *,
    analysis_id: str,
    step09_all_sites: Path,
    step09_significant_sites: Path,
    step09_summary: Path,
    reference_fasta: Path | None = None,
    reference_fai: Path | None = None,
    motif_catalog: Path | None = None,
    git_commit: str = "0" * 40,
) -> ContextFixture:
    """Build one no-R receipt-backed transaction from a valid Step 09 trio."""

    root.mkdir(parents=True, exist_ok=True)
    with step09_all_sites.open(encoding="utf-8", newline="") as stream:
        all_rows = list(csv.DictReader(stream, delimiter="\t"))
    significant = sorted(
        (
            float(row["cmh_fdr_bh"]),
            -abs(float(row["treatment_control_difference"])),
            row["candidate_id"],
        )
        for row in all_rows
        if row["call_status"] in ("significant_up", "significant_down")
    )
    ranks = {
        candidate_id: str(index)
        for index, (_fdr, _effect, candidate_id) in enumerate(
            significant[: CONTEXT.DISPLAY_LIMIT], start=1
        )
    }
    eligible_rows = [
        row
        for row in all_rows
        if row["call_status"] in CONTEXT.CONTEXT_STATUS_BY_CALL_STATUS
    ]
    chromosome_lengths: dict[str, int]
    if reference_fai is None:
        chromosome_lengths = {
            chromosome: max(
                int(row["position"])
                for row in eligible_rows
                if row["chromosome"] == chromosome
            )
            for chromosome in {row["chromosome"] for row in eligible_rows}
        }
        reference_fasta = (root / "reference.fa").resolve()
        reference_fai = (root / "reference.fa.fai").resolve()
        reference_sequences = {
            chromosome: ["A"] * length
            for chromosome, length in chromosome_lengths.items()
        }
        for row in eligible_rows:
            chromosome = row["chromosome"]
            index = int(row["position"]) - 1
            observed = reference_sequences[chromosome][index]
            if observed != "A" and observed != row["genomic_ref"]:
                raise ValueError(
                    "fixture candidates disagree at one reference position"
                )
            reference_sequences[chromosome][index] = row["genomic_ref"]
        fasta_lines: list[str] = []
        fai_lines: list[str] = []
        offset = 0
        for chromosome in sorted(chromosome_lengths):
            length = chromosome_lengths[chromosome]
            header = f">{chromosome}\n"
            sequence = "".join(reference_sequences[chromosome]) + "\n"
            fasta_lines.extend((header, sequence))
            fai_lines.append(
                f"{chromosome}\t{length}\t{offset + len(header)}\t{length}\t{length + 1}\n"
            )
            offset += len(header) + len(sequence)
        reference_fasta.write_text("".join(fasta_lines))
        reference_fai.write_text("".join(fai_lines))
    else:
        if reference_fasta is None:
            raise ValueError("reference_fasta is required with reference_fai")
        chromosome_lengths = _fai_lengths(reference_fai)
        reference_sequences = {
            chromosome: list(sequence)
            for chromosome, sequence in _fasta_sequences(reference_fasta).items()
        }
    if motif_catalog is None:
        motif_catalog = (root / "pum_motifs_v1.tsv").resolve()
        write_tsv(
            motif_catalog,
            CONTEXT.MOTIF_CATALOG_HEADER,
            [
                {
                    "motif_id": "PUM_UGUANA",
                    "rna_consensus": "UGUANA",
                    "dna_consensus": "TGTANA",
                }
            ],
        )
    candidates: list[dict[str, str]] = []
    for row in eligible_rows:
        position = int(row["position"])
        contig_length = chromosome_lengths[row["chromosome"]]
        start = max(1, position - CONTEXT.CONTEXT_RADIUS)
        end = min(contig_length, position + CONTEXT.CONTEXT_RADIUS)
        action = (
            "identity" if row["genomic_ref"] == row["rna_ref"] else "reverse_complement"
        )
        genomic_sequence = "".join(
            reference_sequences[row["chromosome"]][start - 1 : end]
        )
        oriented_sequence = (
            genomic_sequence
            if action == "identity"
            else genomic_sequence.translate(str.maketrans("ACGTN", "TGCAN"))[::-1]
        )
        candidates.append(
            candidate_row(
                row["candidate_id"],
                CONTEXT.CONTEXT_STATUS_BY_CALL_STATUS[row["call_status"]],
                oriented_sequence,
                analysis_id=analysis_id,
                chromosome=row["chromosome"],
                display_rank=ranks.get(row["candidate_id"], "NA"),
                position=position,
                contig_length=contig_length,
                genomic_change=(row["genomic_ref"], row["genomic_alt"]),
                action=action,
            )
        )
    output_paths, output_rows = write_outputs(root, candidates)
    receipt_row = {column: "NA" for column in CONTEXT.SCIENTIFIC_CONTEXT_RECEIPT_HEADER}
    receipt_row.update(
        schema_name="norad.scientific_context_receipt",
        schema_version="1.0.0",
        analysis_id=analysis_id,
        scientific_context_schema_version="1.0.0",
        context_orientation_policy="legacy_rna_change_oriented_genomic_v1",
        context_radius="100",
        logo_radius="10",
        display_limit="8",
        motif_match_policy="exact_iupac_presented_strand_v1",
        motif_distance_policy="nearest_midpoint_from_edit_v1",
        motif_distance_bin_width="10",
        foreground_population="significant_up",
        background_population="fdr_not_met,effect_not_met",
        separate_population="significant_down",
        foreground_minimum_count="10",
        background_minimum_count="20",
        separate_minimum_count="10",
        enrichment_test="Fisher_exact",
        enrichment_alternative="two.sided",
        multiple_testing_method="none_single_registered_motif",
        published_output_count="5",
        producer="build_scientific_context",
        producer_version="1.0.0",
        r_version="fixture",
        biostrings_version="fixture",
        rsamtools_version="fixture",
        git_commit=git_commit,
        transaction_state="complete",
    )
    inputs = {
        "step09_all_sites": step09_all_sites.resolve(),
        "step09_significant_sites": step09_significant_sites.resolve(),
        "step09_summary": step09_summary.resolve(),
        "reference_fasta": reference_fasta.resolve(),
        "reference_fai": reference_fai.resolve(),
        "motif_catalog": motif_catalog.resolve(),
    }
    for name, path in inputs.items():
        receipt_row[f"{name}_path"] = str(path)
        receipt_row[f"{name}_sha256"] = sha256_file(path)
    for name, path in output_paths.items():
        receipt_row[f"{name}_path"] = str(path)
        receipt_row[f"{name}_sha256"] = sha256_file(path)
        receipt_row[f"{name}_row_count"] = str(len(output_rows[name]))
    receipt = (root / f"{analysis_id}.scientific_context_receipt.tsv").resolve()
    write_tsv(receipt, CONTEXT.SCIENTIFIC_CONTEXT_RECEIPT_HEADER, [receipt_row])
    return ContextFixture(
        receipt=receipt,
        candidate_context=output_paths["candidate_context"],
        motif_hits=output_paths["motif_hits"],
        sequence_logo=output_paths["sequence_logo"],
        motif_statistics=output_paths["motif_statistics"],
        reference_fasta=reference_fasta.resolve(),
        reference_fai=reference_fai.resolve(),
        motif_catalog=motif_catalog.resolve(),
    )
