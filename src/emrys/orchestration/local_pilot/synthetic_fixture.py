"""Generate a tiny deterministic four-library local-pilot science fixture."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import random
import sys
from pathlib import Path

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.orchestration.local_pilot.onboarding import (
    OnboardingError,
    _require_external_absent_output,
    publish_create_absent_tree,
    source_root,
    validate_local_pilot_request,
)

DESCRIPTION = (
    "Generate one tiny deterministic four-library RNA fixture for a fast, "
    "real-tool local-pilot smoke run. Dry-run is the default."
)
FIXTURE_SCHEMA = "emrys.synthetic-local-pilot.v1"
COMPLETION_MANIFEST = "fixture.manifest.json"
SEED = 20260814
CONTIG = "chrSynthetic"
CONTIG_LENGTH = 100_000
READ_LENGTH = 75
FRAGMENT_LENGTH = 225
CANDIDATE_PAIR_COUNT = 64
SPLICE_PAIR_COUNT = 2
PAIR_COUNT_PER_LIBRARY = 2 * CANDIDATE_PAIR_COUNT + SPLICE_PAIR_COUNT
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
    {
        "sample_id": "control_pair_01",
        "condition": "control",
        "replicate": "pair_01",
        "positive_ad": 4,
    },
    {
        "sample_id": "treatment_pair_01",
        "condition": "treatment",
        "replicate": "pair_01",
        "positive_ad": 32,
    },
    {
        "sample_id": "control_pair_02",
        "condition": "control",
        "replicate": "pair_02",
        "positive_ad": 4,
    },
    {
        "sample_id": "treatment_pair_02",
        "condition": "treatment",
        "replicate": "pair_02",
        "positive_ad": 32,
    },
)


def _reference() -> str:
    generator = random.Random(SEED)
    bases = [generator.choice("ACGT") for _ in range(CONTIG_LENGTH)]
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
    rows = (
        ("gene", 29_001, 31_900, "+", 'gene_id "GENE_PLUS"; gene_name "GENE_PLUS";'),
        (
            "transcript",
            29_001,
            31_900,
            "+",
            'gene_id "GENE_PLUS"; transcript_id "TX_PLUS"; gene_name "GENE_PLUS";',
        ),
        (
            "exon",
            PLUS_EXONS[0][0],
            PLUS_EXONS[0][1],
            "+",
            'gene_id "GENE_PLUS"; transcript_id "TX_PLUS"; exon_number "1";',
        ),
        (
            "exon",
            PLUS_EXONS[1][0],
            PLUS_EXONS[1][1],
            "+",
            'gene_id "GENE_PLUS"; transcript_id "TX_PLUS"; exon_number "2";',
        ),
        ("gene", 49_001, 51_900, "-", 'gene_id "GENE_MINUS"; gene_name "GENE_MINUS";'),
        (
            "transcript",
            49_001,
            51_900,
            "-",
            'gene_id "GENE_MINUS"; transcript_id "TX_MINUS"; gene_name "GENE_MINUS";',
        ),
        (
            "exon",
            MINUS_EXONS[0][0],
            MINUS_EXONS[0][1],
            "-",
            'gene_id "GENE_MINUS"; transcript_id "TX_MINUS"; exon_number "2";',
        ),
        (
            "exon",
            MINUS_EXONS[1][0],
            MINUS_EXONS[1][1],
            "-",
            'gene_id "GENE_MINUS"; transcript_id "TX_MINUS"; exon_number "1";',
        ),
    )
    return "".join(
        f"{CONTIG}\temrys-poc\t{feature}\t{start}\t{end}\t.\t{strand}\t.\t{attributes}\n"
        for feature, start, end, strand, attributes in rows
    ).encode("utf-8")


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
        if all(10 <= int(site["position"]) - 1 - start <= 64 for site in sites)
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


def _gzip_records(records: list[str]) -> bytes:
    destination = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        compresslevel=9,
        fileobj=destination,
        mtime=0,
    ) as stream:
        stream.write("".join(records).encode("ascii"))
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


def _request() -> bytes:
    return b"""schema_version: emrys.request.v3
label: deterministic-science-smoke-v1
profile: emrys.profile.local_cmh.v2
sample_manifest: samples.tsv
partition_manifest: partitions.tsv
reference:
  id: synthetic-smoke-v1
  fasta: inputs/reference/reference.fa
  gtf: inputs/reference/genes.gtf
  star_index:
    sjdb_overhang: 74
    genome_sa_index_nbases: 3
cohort_id: synthetic-smoke-v1
analysis:
  id: synthetic-smoke-cmh-v1
  control_condition: control
  treatment_condition: treatment
  rna_ref: A
  rna_alt: G
  min_sample_dp: 1
  mean_dp_threshold: 50
  fdr_threshold: 0.05
  common_or_threshold: 1.2
  absolute_difference_threshold: 0.005
  background_condition: null
  background_max_fraction: 0.01
"""


def _resources() -> bytes:
    return b"""schema_version: emrys.local-pilot-resources.v1
workflow_cores: 1
workflow_memory_mb: allocation
stage_concurrency:
  "01": 1
  "02": 1
  "02b": 1
  "03": 1
  "04": 1
  "05": 1
  "06": 1
  "07": 1
step_threads:
  "00a": 1
  "01": 1
  "02": 1
  "06": 1
  "08": 1
stage_memory_mb:
  "00a": workflow
  "00b": workflow
  "00c": workflow
  "01": workflow
  "02": workflow
  "02b": workflow
  "03": workflow
  "04": workflow
  "05": workflow
  "06": workflow
  "07": workflow
  "08": workflow
  "09": workflow
  "10": workflow
reporting_memory_mb:
  artifact_index: workflow
  run_summary: workflow
  html_report: workflow
"""


def fixture_members() -> dict[str, tuple[bytes, int]]:
    """Return deterministic fixture members, excluding the completion manifest."""

    reference = _reference()
    members: dict[str, tuple[bytes, int]] = {
        "request.yaml": (_request(), 0o644),
        "emrys.resources.yaml": (_resources(), 0o644),
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
        pairs = _candidate_pairs(reference, sample, sample_index)
        pairs.extend(_splice_pairs(reference, sample_id, sample_index))
        if len(pairs) != PAIR_COUNT_PER_LIBRARY:
            raise OnboardingError(
                f"synthetic library has {len(pairs)} pairs; expected {PAIR_COUNT_PER_LIBRARY}"
            )
        members[f"inputs/reads/{sample_id}_R1.fastq.gz"] = (
            _gzip_records([pair[0] for pair in pairs]),
            0o644,
        )
        members[f"inputs/reads/{sample_id}_R2.fastq.gz"] = (
            _gzip_records([pair[1] for pair in pairs]),
            0o644,
        )
    metadata = {
        "schema_version": FIXTURE_SCHEMA,
        "seed": SEED,
        "contig": CONTIG,
        "contig_length": CONTIG_LENGTH,
        "read_length": READ_LENGTH,
        "fragment_length": FRAGMENT_LENGTH,
        "library_count": len(SAMPLES),
        "read_pairs_per_library": PAIR_COUNT_PER_LIBRARY,
        "intended_use": "fast real-tool workflow smoke; not biological evidence",
        "engineered_candidates": [NULL_SITE, POSITIVE_SITE, NON_TARGET_SITE],
        "expected_terminal_computational_result": {
            "all_sites_rows": 3,
            "significant_sites_rows": 1,
            "significant_candidate_id": "REV_like|chrSynthetic|50000|A>G",
            "control_af": 0.0625,
            "treatment_af": 0.5,
            "absolute_af_difference": 0.4375,
            "common_odds_ratio": 15.0,
            "interpretation": "computational smoke expectation; not scientific adjudication",
        },
    }
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
        members = fixture_members()
        print(f"Output directory: {output}")
        print(f"Libraries: {len(SAMPLES)}")
        print(f"Read pairs per library: {PAIR_COUNT_PER_LIBRARY}")
        print(f"Reference length: {CONTIG_LENGTH}")
        print("Publication policy: create-absent; fixture manifest is written last.")
        if not arguments.execute:
            print("Dry-run complete; no files were written.")
            return 0

        def validate_before_completion(published: Path) -> None:
            validate_local_pilot_request(published / "request.yaml", root=root)

        publish_create_absent_tree(
            output,
            members,
            completion_name=COMPLETION_MANIFEST,
            completion_bytes=_completion_bytes(members),
            before_completion=validate_before_completion,
        )
        print(f"Published deterministic local-pilot fixture: {output}")
        print(f"Request: {output / 'request.yaml'}")
        print(
            "Evidence boundary: synthetic workflow smoke input; not biological evidence."
        )
        return 0
    except (
        OSError,
        OnboardingError,
        orchestration_contracts.ContractValidationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


__all__ = (
    "COMPLETION_MANIFEST",
    "DESCRIPTION",
    "PAIR_COUNT_PER_LIBRARY",
    "SAMPLES",
    "configure_parser",
    "fixture_members",
    "init_from_args",
)
