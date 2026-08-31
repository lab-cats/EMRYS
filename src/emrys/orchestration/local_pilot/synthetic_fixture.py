"""Generate deterministic four-library synthetic Projects."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
import random
import sys
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from types import MappingProxyType
from typing import cast

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.orchestration.local_pilot.onboarding import (
    OnboardingError,
    PROJECT_DIRECTORIES,
    _project_yaml,
    _require_external_absent_output,
    publish_create_absent_tree,
    source_root,
    validate_project,
)

DESCRIPTION = (
    "Generate one deterministic four-library RNA fixture for a real-tool "
    "EMRYS Project. Dry-run is the default."
)
FIXTURE_SCHEMA = "emrys.synthetic-local-pilot.v2"
COMPLETION_MANIFEST = "fixture.manifest.json"
CONTIG = "chrSynthetic"
READ_LENGTH = 75
FRAGMENT_LENGTH = 225
CANDIDATE_PAIR_COUNT = 64
SPLICE_PAIR_COUNT = 2
CORE_PAIR_COUNT_PER_LIBRARY = 2 * CANDIDATE_PAIR_COUNT + SPLICE_PAIR_COUNT
MIN_ENGINEERED_ALT_OFFSET = 10
MAX_ENGINEERED_ALT_OFFSET = 64
DEFAULT_DATASET_PROFILE = "smoke-v1"
PRODUCTION_LIKE_DATASET_PROFILE = "production-like-v1"
NEUTRAL_BACKGROUND_START_ZERO_BASED = 100_000
GZIP_WRITE_BUFFER_SIZE = 1024 * 1024


@dataclass(frozen=True)
class DatasetProfile:
    """One closed deterministic synthetic-dataset plan."""

    name: str
    fixture_id: str
    seed: int
    contig_length: int
    pair_count_per_library: int
    neutral_unique_template_pair_count_per_library: int
    neutral_duplicate_pair_count_per_library: int
    neutral_start_zero_based: int | None
    genome_sa_index_nbases: int

    @property
    def neutral_pair_count_per_library(self) -> int:
        return (
            self.neutral_unique_template_pair_count_per_library
            + self.neutral_duplicate_pair_count_per_library
        )


DATASET_PROFILES: Mapping[str, DatasetProfile] = MappingProxyType(
    {
        DEFAULT_DATASET_PROFILE: DatasetProfile(
            name=DEFAULT_DATASET_PROFILE,
            fixture_id="deterministic-science-smoke-v1",
            seed=20260814,
            contig_length=100_000,
            pair_count_per_library=CORE_PAIR_COUNT_PER_LIBRARY,
            neutral_unique_template_pair_count_per_library=0,
            neutral_duplicate_pair_count_per_library=0,
            neutral_start_zero_based=None,
            genome_sa_index_nbases=3,
        ),
        PRODUCTION_LIKE_DATASET_PROFILE: DatasetProfile(
            name=PRODUCTION_LIKE_DATASET_PROFILE,
            fixture_id="deterministic-production-like-v1",
            seed=20260814,
            contig_length=5_000_000,
            pair_count_per_library=100_000,
            neutral_unique_template_pair_count_per_library=89_883,
            neutral_duplicate_pair_count_per_library=9_987,
            neutral_start_zero_based=NEUTRAL_BACKGROUND_START_ZERO_BASED,
            genome_sa_index_nbases=10,
        ),
    }
)
DEFAULT_PROFILE = DATASET_PROFILES[DEFAULT_DATASET_PROFILE]

# Preserve the established tiny-fixture Python constants for callers and tests.
SEED = DEFAULT_PROFILE.seed
CONTIG_LENGTH = DEFAULT_PROFILE.contig_length
PAIR_COUNT_PER_LIBRARY = DEFAULT_PROFILE.pair_count_per_library
PLUS_EXONS = ((29_001, 30_300), (30_601, 31_900))
MINUS_EXONS = ((49_001, 50_300), (50_601, 51_900))
NULL_SITE = {
    "key": "null",
    "orientation": "FWD_like",
    "position": 30_000,
    "genomic_ref": "T",
    "genomic_alt": "C",
    "rna_change": "A>G",
}
POSITIVE_SITE = {
    "key": "positive",
    "orientation": "REV_like",
    "position": 50_000,
    "genomic_ref": "A",
    "genomic_alt": "G",
    "rna_change": "A>G",
}
NON_TARGET_SITE = {
    "key": "non_target",
    "orientation": "REV_like",
    "position": 50_010,
    "genomic_ref": "C",
    "genomic_alt": "T",
    "rna_change": "C>T",
}
SAMPLES = (
    {"sample_id": "control_pair_01", "condition": "control", "replicate": "pair_01", "positive_ad": 4},
    {"sample_id": "treatment_pair_01", "condition": "treatment", "replicate": "pair_01", "positive_ad": 32},
    {"sample_id": "control_pair_02", "condition": "control", "replicate": "pair_02", "positive_ad": 4},
    {"sample_id": "treatment_pair_02", "condition": "treatment", "replicate": "pair_02", "positive_ad": 32},
)


def _neutral_start_capacity(profile: DatasetProfile) -> int:
    if profile.neutral_start_zero_based is None:
        return 0
    return (
        profile.contig_length - FRAGMENT_LENGTH + 1 - profile.neutral_start_zero_based
    )


@cache
def _coprime_step(modulus: int, seed: int) -> int:
    if modulus < 1:
        raise ValueError("permutation modulus must be positive")
    if modulus == 1:
        return 1
    candidate = seed % modulus or 1
    while math.gcd(candidate, modulus) != 1:
        candidate += 1
    return candidate


def _neutral_unique_start(
    profile: DatasetProfile,
    sample_index: int,
    unique_index: int,
) -> int:
    unique_count = profile.neutral_unique_template_pair_count_per_library
    if not 0 <= sample_index < len(SAMPLES):
        raise ValueError(f"invalid sample index: {sample_index}")
    if not 0 <= unique_index < unique_count:
        raise ValueError(f"invalid neutral unique-template index: {unique_index}")
    neutral_start = cast(int, profile.neutral_start_zero_based)
    capacity = _neutral_start_capacity(profile)
    step = _coprime_step(capacity, profile.seed ^ 0x454D5259)
    offset = (profile.seed ^ 0x53594E54) % capacity
    global_index = sample_index * unique_count + unique_index
    return neutral_start + ((offset + global_index * step) % capacity)


def _neutral_duplicate_source_index(
    profile: DatasetProfile,
    sample_index: int,
    duplicate_index: int,
) -> int:
    unique_count = profile.neutral_unique_template_pair_count_per_library
    duplicate_count = profile.neutral_duplicate_pair_count_per_library
    if not 0 <= sample_index < len(SAMPLES):
        raise ValueError(f"invalid sample index: {sample_index}")
    if not 0 <= duplicate_index < duplicate_count:
        raise ValueError(f"invalid neutral duplicate index: {duplicate_index}")
    step = _coprime_step(unique_count, profile.seed ^ 0x4455504C)
    offset = (profile.seed + sample_index * 104_729) % unique_count
    return (offset + duplicate_index * step) % unique_count


def _reference(profile: DatasetProfile = DEFAULT_PROFILE) -> str:
    generator = random.Random(profile.seed)
    bases = [generator.choice("ACGT") for _ in range(profile.contig_length)]
    for site in (NULL_SITE, POSITIVE_SITE, NON_TARGET_SITE):
        bases[int(site["position"]) - 1] = str(site["genomic_ref"])
    return "".join(bases)


def _reverse_complement(sequence: str) -> str:
    return sequence.translate(str.maketrans("ACGT", "TGCA"))[::-1]


def _wrapped_fasta(sequence: str) -> bytes:
    lines = [f">{CONTIG}"]
    lines.extend(sequence[index : index + 80] for index in range(0, len(sequence), 80))
    return ("\n".join(lines) + "\n").encode("ascii")


def _gtf_bytes() -> bytes:
    return f'''{CONTIG}\temrys-poc\tgene\t29001\t31900\t.\t+\t.\tgene_id "GENE_PLUS"; gene_name "GENE_PLUS";
{CONTIG}\temrys-poc\ttranscript\t29001\t31900\t.\t+\t.\tgene_id "GENE_PLUS"; transcript_id "TX_PLUS"; gene_name "GENE_PLUS";
{CONTIG}\temrys-poc\texon\t{PLUS_EXONS[0][0]}\t{PLUS_EXONS[0][1]}\t.\t+\t.\tgene_id "GENE_PLUS"; transcript_id "TX_PLUS"; exon_number "1";
{CONTIG}\temrys-poc\texon\t{PLUS_EXONS[1][0]}\t{PLUS_EXONS[1][1]}\t.\t+\t.\tgene_id "GENE_PLUS"; transcript_id "TX_PLUS"; exon_number "2";
{CONTIG}\temrys-poc\tgene\t49001\t51900\t.\t-\t.\tgene_id "GENE_MINUS"; gene_name "GENE_MINUS";
{CONTIG}\temrys-poc\ttranscript\t49001\t51900\t.\t-\t.\tgene_id "GENE_MINUS"; transcript_id "TX_MINUS"; gene_name "GENE_MINUS";
{CONTIG}\temrys-poc\texon\t{MINUS_EXONS[0][0]}\t{MINUS_EXONS[0][1]}\t.\t-\t.\tgene_id "GENE_MINUS"; transcript_id "TX_MINUS"; exon_number "2";
{CONTIG}\temrys-poc\texon\t{MINUS_EXONS[1][0]}\t{MINUS_EXONS[1][1]}\t.\t-\t.\tgene_id "GENE_MINUS"; transcript_id "TX_MINUS"; exon_number "1";
'''.encode("utf-8")


def _covering_starts(
    first_position: int,
    last_position: int,
    sample_index: int,
) -> list[int]:
    starts = list(range(last_position - READ_LENGTH, first_position))
    if len(starts) < CANDIDATE_PAIR_COUNT:
        raise OnboardingError("synthetic candidate interval has too few read starts")
    rotation = sample_index * 13 % len(starts)
    return (starts[rotation:] + starts[:rotation])[:CANDIDATE_PAIR_COUNT]


def _selected_indices(
    count: int,
    rotation: int,
    starts: list[int],
    sites: tuple[dict[str, object], ...],
) -> set[int]:
    eligible = [
        index
        for index, start in enumerate(starts)
        if all(
            MIN_ENGINEERED_ALT_OFFSET
            <= int(site["position"]) - 1 - start
            <= MAX_ENGINEERED_ALT_OFFSET
            for site in sites
        )
    ]
    if len(eligible) < count:
        raise OnboardingError(
            "synthetic candidate interval has too few internal starts"
        )
    start_index = rotation % len(eligible)
    return set((eligible[start_index:] + eligible[:start_index])[:count])


def _mutate(sequence: str, start: int, site: dict[str, object]) -> str:
    offset = int(site["position"]) - 1 - start
    if not 0 <= offset < len(sequence) or sequence[offset] != site["genomic_ref"]:
        raise OnboardingError(f"synthetic reference mismatch at {site['key']}")
    return sequence[:offset] + str(site["genomic_alt"]) + sequence[offset + 1 :]


def _fastq_record(name: str, mate: int, sequence: str) -> str:
    return f"@{name}/{mate}\n{sequence}\n+\n{'I' * len(sequence)}\n"


def _candidate_pairs(
    reference: str,
    sample: dict[str, object],
    sample_index: int,
) -> list[tuple[str, str]]:
    sample_id = str(sample["sample_id"])
    pairs: list[tuple[str, str]] = []
    fwd_starts = _covering_starts(30_000, 30_000, sample_index)
    null_alt = _selected_indices(8, sample_index * 5, fwd_starts, (NULL_SITE,))
    for pair_index, start in enumerate(fwd_starts):
        fragment = reference[start : start + FRAGMENT_LENGTH]
        r1 = fragment[:READ_LENGTH]
        if pair_index in null_alt:
            r1 = _mutate(r1, start, NULL_SITE)
        r2 = _reverse_complement(fragment[-READ_LENGTH:])
        name = f"{sample_id}:FWD:{pair_index + 1:04d}:{start + 1}"
        pairs.append((_fastq_record(name, 1, r1), _fastq_record(name, 2, r2)))

    rev_starts = _covering_starts(50_000, 50_010, sample_index)
    positive_alt = _selected_indices(
        int(sample["positive_ad"]),
        3 + sample_index * 11,
        rev_starts,
        (POSITIVE_SITE,),
    )
    non_target_alt = _selected_indices(
        8,
        9 + sample_index * 7,
        rev_starts,
        (NON_TARGET_SITE,),
    )
    for pair_index, start in enumerate(rev_starts):
        fragment = reference[start : start + FRAGMENT_LENGTH]
        r2 = fragment[:READ_LENGTH]
        if pair_index in positive_alt:
            r2 = _mutate(r2, start, POSITIVE_SITE)
        if pair_index in non_target_alt:
            r2 = _mutate(r2, start, NON_TARGET_SITE)
        r1 = _reverse_complement(fragment[-READ_LENGTH:])
        name = f"{sample_id}:REV:{pair_index + 1:04d}:{start + 1}"
        pairs.append((_fastq_record(name, 1, r1), _fastq_record(name, 2, r2)))
    return pairs


def _transcript_sequence(
    reference: str,
    exons: tuple[tuple[int, int], ...],
    strand: str,
) -> str:
    pieces = [reference[start - 1 : end] for start, end in exons]
    if strand == "+":
        return "".join(pieces)
    return "".join(_reverse_complement(piece) for piece in reversed(pieces))


def _splice_pairs(
    reference: str,
    sample_id: str,
    sample_index: int,
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for sentinel_index, (label, exons, strand) in enumerate(
        (("PLUS_SPLICE", PLUS_EXONS, "+"), ("MINUS_SPLICE", MINUS_EXONS, "-"))
    ):
        transcript = _transcript_sequence(reference, exons, strand)
        first_exon_length = exons[0][1] - exons[0][0] + 1
        start = first_exon_length - 42 - sample_index * 2 - sentinel_index
        fragment = transcript[start : start + FRAGMENT_LENGTH]
        if len(fragment) != FRAGMENT_LENGTH:
            raise OnboardingError(f"short synthetic splice fragment: {label}")
        name = f"{sample_id}:{label}:0001:{start + 1}"
        pairs.append(
            (
                _fastq_record(name, 1, fragment[:READ_LENGTH]),
                _fastq_record(name, 2, _reverse_complement(fragment[-READ_LENGTH:])),
            )
        )
    return pairs


def _core_pairs(
    reference: str,
    sample: dict[str, object],
    sample_index: int,
) -> Iterator[tuple[str, str]]:
    pairs = _candidate_pairs(reference, sample, sample_index)
    pairs.extend(_splice_pairs(reference, str(sample["sample_id"]), sample_index))
    if len(pairs) != CORE_PAIR_COUNT_PER_LIBRARY:
        raise OnboardingError(
            f"synthetic core has {len(pairs)} pairs; "
            f"expected {CORE_PAIR_COUNT_PER_LIBRARY}"
        )
    yield from pairs


def _neutral_pairs(
    reference: str,
    sample: dict[str, object],
    sample_index: int,
    profile: DatasetProfile,
) -> Iterator[tuple[str, str]]:
    sample_id = str(sample["sample_id"])
    unique_count = profile.neutral_unique_template_pair_count_per_library
    duplicate_count = profile.neutral_duplicate_pair_count_per_library
    for unique_index in range(unique_count):
        start = _neutral_unique_start(profile, sample_index, unique_index)
        fragment = reference[start : start + FRAGMENT_LENGTH]
        if len(fragment) != FRAGMENT_LENGTH:
            raise OnboardingError(
                f"short neutral fragment for {sample_id} at zero-based start {start}"
            )
        name = f"{sample_id}:NEUTRAL_UNIQUE:{unique_index + 1:06d}:{start + 1}"
        yield (
            _fastq_record(name, 1, fragment[:READ_LENGTH]),
            _fastq_record(name, 2, _reverse_complement(fragment[-READ_LENGTH:])),
        )

    for duplicate_index in range(duplicate_count):
        source_index = _neutral_duplicate_source_index(
            profile, sample_index, duplicate_index
        )
        start = _neutral_unique_start(profile, sample_index, source_index)
        fragment = reference[start : start + FRAGMENT_LENGTH]
        name = (
            f"{sample_id}:NEUTRAL_DUPLICATE:{duplicate_index + 1:06d}:"
            f"{source_index + 1:06d}:{start + 1}"
        )
        yield (
            _fastq_record(name, 1, fragment[:READ_LENGTH]),
            _fastq_record(name, 2, _reverse_complement(fragment[-READ_LENGTH:])),
        )


def _fastq_records(
    reference: str,
    sample: dict[str, object],
    sample_index: int,
    profile: DatasetProfile,
    mate: int,
) -> Iterator[str]:
    if mate not in (1, 2):
        raise ValueError(f"FASTQ mate must be 1 or 2, not {mate}")
    pair_count = 0
    for pairs in (
        _core_pairs(reference, sample, sample_index),
        _neutral_pairs(reference, sample, sample_index, profile),
    ):
        for r1_record, r2_record in pairs:
            pair_count += 1
            yield r1_record if mate == 1 else r2_record
    if pair_count != profile.pair_count_per_library:
        raise OnboardingError(
            f"dataset profile {profile.name!r} produced {pair_count} pairs; "
            f"expected {profile.pair_count_per_library}"
        )


def _gzip_records(records: Iterable[str]) -> bytes:
    destination = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        compresslevel=9,
        fileobj=destination,
        mtime=0,
    ) as stream:
        buffer = bytearray()
        for record in records:
            buffer.extend(record.encode("ascii"))
            if len(buffer) >= GZIP_WRITE_BUFFER_SIZE:
                stream.write(buffer)
                buffer.clear()
        if buffer:
            stream.write(buffer)
    return destination.getvalue()


def _sample_manifest() -> bytes:
    rows = ["sample_id\tr1_fastq\tr2_fastq\tstrandedness\tcondition\treplicate"]
    for sample in SAMPLES:
        sample_id = sample["sample_id"]
        rows.append(
            f"{sample_id}\tinputs/reads/{sample_id}_R1.fastq.gz\t"
            f"inputs/reads/{sample_id}_R2.fastq.gz\tforward\t"
            f"{sample['condition']}\t{sample['replicate']}"
        )
    return ("\n".join(rows) + "\n").encode("utf-8")


def _project_definition(profile: DatasetProfile = DEFAULT_PROFILE) -> bytes:
    return _project_yaml(
        {
            "analysis_name": "primary",
            "sample_manifest": Path("samples.tsv"),
            "partition_manifest": Path("partitions.tsv"),
            "reference_fasta": Path("inputs/reference/reference.fa"),
            "reference_gtf": Path("inputs/reference/genes.gtf"),
            "sjdb_overhang": READ_LENGTH - 1,
            "genome_sa_index_nbases": profile.genome_sa_index_nbases,
            "control_condition": "control",
            "treatment_condition": "treatment",
            "target_change": "A>G",
            "min_sample_dp": 1,
            "mean_dp_threshold": 50,
            "fdr_threshold": 0.05,
            "common_or_threshold": 1.2,
            "absolute_difference_threshold": 0.005,
            "background_condition": None,
            "background_max_fraction": 0.01,
        }
    )


def _candidate_metadata(site: dict[str, object]) -> dict[str, object]:
    strata: dict[str, dict[str, dict[str, object]]] = {}
    for sample in SAMPLES:
        replicate = str(sample["replicate"])
        condition = str(sample["condition"])
        ad = int(sample["positive_ad"]) if site["key"] == "positive" else 8
        strata.setdefault(replicate, {})[condition] = {
            "sample_id": sample["sample_id"],
            "dp": CANDIDATE_PAIR_COUNT,
            "ad": ad,
        }
    genomic_change = f"{site['genomic_ref']}>{site['genomic_alt']}"
    return {
        "candidate_id": (
            f"{site['orientation']}|{CONTIG}|{site['position']}|{genomic_change}"
        ),
        "orientation": site["orientation"],
        "chromosome": CONTIG,
        "position": site["position"],
        "genomic_ref": site["genomic_ref"],
        "genomic_alt": site["genomic_alt"],
        "input": {"rna_change": site["rna_change"], "strata": strata},
    }


def fixture_metadata(
    profile: DatasetProfile = DEFAULT_PROFILE,
) -> dict[str, object]:
    """Return the explicit deterministic contract for one dataset profile."""

    if profile.neutral_start_zero_based is None:
        neutral_interval: list[int] | None = None
        reserved_core_region: list[int] | None = None
    else:
        neutral_interval = [
            profile.neutral_start_zero_based,
            profile.contig_length - FRAGMENT_LENGTH + 1,
        ]
        reserved_core_region = [1, profile.neutral_start_zero_based]
    return {
        "schema_version": FIXTURE_SCHEMA,
        "fixture_id": profile.fixture_id,
        "dataset_profile": profile.name,
        "seed": profile.seed,
        "contig": CONTIG,
        "contig_length": profile.contig_length,
        "read_length": READ_LENGTH,
        "fragment_length": FRAGMENT_LENGTH,
        "library_count": len(SAMPLES),
        "read_pairs_per_library": profile.pair_count_per_library,
        "core_read_pairs_per_library": CORE_PAIR_COUNT_PER_LIBRARY,
        "candidate_fragment_pair_count": CANDIDATE_PAIR_COUNT,
        "engineered_alt_read_offset_bounds": [
            MIN_ENGINEERED_ALT_OFFSET,
            MAX_ENGINEERED_ALT_OFFSET,
        ],
        "splice_sentinel_pair_count_per_library": SPLICE_PAIR_COUNT,
        "reference_generation": {
            "alphabet": "ACGT",
            "generator": "python.random.Random.choice-v1",
            "seed": profile.seed,
            "contig_length": profile.contig_length,
        },
        "neutral_background": {
            "pair_count_per_library": profile.neutral_pair_count_per_library,
            "unique_template_pair_count_per_library": (
                profile.neutral_unique_template_pair_count_per_library
            ),
            "deliberate_duplicate_pair_count_per_library": (
                profile.neutral_duplicate_pair_count_per_library
            ),
            "placement_seed": profile.seed,
            "fragment_start_interval_0_based_half_open": neutral_interval,
            "reserved_core_region_1_based_closed": reserved_core_region,
        },
        "star": {
            "genome_sa_index_nbases": profile.genome_sa_index_nbases,
            "sjdb_overhang": READ_LENGTH - 1,
        },
        "samples": [
            {
                "sample_id": sample["sample_id"],
                "condition": sample["condition"],
                "replicate": sample["replicate"],
                "strandedness": "forward",
                "read_pair_count": profile.pair_count_per_library,
            }
            for sample in SAMPLES
        ],
        "engineered_candidates": [NULL_SITE, POSITIVE_SITE, NON_TARGET_SITE],
        "engineered_candidate_inputs": {
            "positive": _candidate_metadata(POSITIVE_SITE),
            "null": _candidate_metadata(NULL_SITE),
            "non_target": _candidate_metadata(NON_TARGET_SITE),
        },
        "splice_junction_sentinels": [
            {
                "transcript_id": "TX_PLUS",
                "strand": "+",
                "expected_orientation": "FWD_like",
                "junction_1_based": [PLUS_EXONS[0][1], PLUS_EXONS[1][0]],
            },
            {
                "transcript_id": "TX_MINUS",
                "strand": "-",
                "expected_orientation": "REV_like",
                "junction_1_based": [MINUS_EXONS[0][1], MINUS_EXONS[1][0]],
            },
        ],
        "intended_use": (
            "real-tool EMRYS Step 00a-10 and reporting workflow exercise; "
            "not production data or biological evidence"
        ),
        "expected_terminal_computational_result": {
            "all_sites_rows": 3,
            "significant_sites_rows": 1,
            "significant_candidate_id": "REV_like|chrSynthetic|50000|A>G",
            "control_af": 0.0625,
            "treatment_af": 0.5,
            "absolute_af_difference": 0.4375,
            "common_odds_ratio": 15.0,
            "interpretation": (
                "computational smoke expectation; not scientific adjudication"
                if profile.name == DEFAULT_DATASET_PROFILE
                else "computational production-like expectation; not scientific "
                "adjudication"
            ),
        },
        "expected_terminal_workflow": {
            "last_scientific_step": "10",
            "scientific_results_complete": True,
            "reporting_complete": True,
            "interpretation": (
                "synthetic functional expectation; not production, scientific-review, "
                "or biological evidence"
            ),
        },
    }


def fixture_members(
    profile: DatasetProfile = DEFAULT_PROFILE,
) -> dict[str, tuple[bytes, int]]:
    """Return deterministic fixture members, excluding the completion manifest."""

    reference = _reference(profile)
    members: dict[str, tuple[bytes, int]] = {
        "project.yaml": (_project_definition(profile), 0o644),
        "samples.tsv": (_sample_manifest(), 0o644),
        "partitions.tsv": (
            f"partition_id\tselector_type\tselector_value\nprimary\tregion\t{CONTIG}\n".encode(),
            0o644,
        ),
        "inputs/reference/reference.fa": (_wrapped_fasta(reference), 0o644),
        "inputs/reference/genes.gtf": (_gtf_bytes(), 0o644),
    }
    for sample_index, sample in enumerate(SAMPLES):
        sample_id = str(sample["sample_id"])
        for mate in (1, 2):
            members[f"inputs/reads/{sample_id}_R{mate}.fastq.gz"] = (
                _gzip_records(
                    _fastq_records(reference, sample, sample_index, profile, mate=mate)
                ),
                0o644,
            )
    metadata = fixture_metadata(profile)
    members["fixture.json"] = (
        (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        0o644,
    )
    return members


def _completion_bytes(members: dict[str, tuple[bytes, int]]) -> bytes:
    manifest = {
        name: {
            "mode": f"{mode:04o}",
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
        }
        for name, (data, mode) in sorted(members.items())
    }
    return (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Absolute absent directory to receive the deterministic fixture.",
    )
    parser.add_argument(
        "--dataset-profile",
        choices=tuple(DATASET_PROFILES),
        default=DEFAULT_DATASET_PROFILE,
        help=(
            "Closed deterministic dataset plan. smoke-v1 is the 130-pair "
            "default; production-like-v1 emits 100,000 pairs per library "
            "on a 5 Mb reference."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Create the fixture. Default is a no-write plan.",
    )
    parser.set_defaults(_command_parser=parser)


def init_from_args(arguments: argparse.Namespace) -> int:
    """Plan or publish one deterministic fixture outside the checkout."""

    try:
        root = source_root()
        output = _require_external_absent_output(arguments.output_dir, root)
        profile_name = str(
            getattr(arguments, "dataset_profile", DEFAULT_DATASET_PROFILE)
        )
        try:
            profile = DATASET_PROFILES[profile_name]
        except KeyError as exc:
            raise OnboardingError(
                f"unsupported synthetic dataset profile: {profile_name}"
            ) from exc
        print(f"Dataset profile: {profile.name}")
        print(f"Output directory: {output}")
        print(f"Libraries: {len(SAMPLES)}")
        print(f"Read pairs per library: {profile.pair_count_per_library}")
        print(f"Engineered/core pairs per library: {CORE_PAIR_COUNT_PER_LIBRARY}")
        print(
            "Neutral unique/duplicate pairs per library: "
            f"{profile.neutral_unique_template_pair_count_per_library}/"
            f"{profile.neutral_duplicate_pair_count_per_library}"
        )
        print(f"Reference length: {profile.contig_length}")
        print("Publication policy: create-absent; fixture manifest is written last.")
        if not arguments.execute:
            print("Dry-run complete; no files were written.")
            return 0

        members = fixture_members(profile)

        def validate_before_completion(published: Path) -> None:
            validate_project(published / "project.yaml", root=root)

        publish_create_absent_tree(
            output,
            members,
            completion_name=COMPLETION_MANIFEST,
            completion_bytes=_completion_bytes(members),
            directories=PROJECT_DIRECTORIES,
            before_completion=validate_before_completion,
        )
        print(f"Published deterministic synthetic Project ({profile.name}): {output}")
        print(f"Project: {output / 'project.yaml'}")
        print(
            "Evidence boundary: synthetic workflow smoke input; not biological evidence."
        )
        return 0
    except (
        OSError,
        OnboardingError,
        orchestration_contracts.ContractValidationError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


__all__ = (
    "COMPLETION_MANIFEST",
    "CORE_PAIR_COUNT_PER_LIBRARY",
    "DATASET_PROFILES",
    "DEFAULT_DATASET_PROFILE",
    "DESCRIPTION",
    "PAIR_COUNT_PER_LIBRARY",
    "PRODUCTION_LIKE_DATASET_PROFILE",
    "SAMPLES",
    "configure_parser",
    "fixture_metadata",
    "fixture_members",
    "init_from_args",
)
