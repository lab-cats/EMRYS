# FUT-DATA-02 — Public reference and SRA acquisition

## Objective

Design separate future adapters for public reference registration and public
read acquisition while preserving the current FASTQ/reference intake contract.

## Why this exists

Scientists should eventually be able to start from authoritative public data,
but GenBank/reference downloads and sequencing-read archives are different
artifact categories. Reference FASTA/FNA plus GTF/GFF3/GBFF must not be
misrepresented as reads or converted to FASTQ.

## Fixed decisions

- This capability is future-only; V1 intake remains local paired FASTQ/FASTQ.GZ
  plus registered FASTA/GTF.
- Priority: local paired reads/reference first, then NCBI reference
  acquisition/registration, then SRA reads, then later ENA/GEO/BAM as justified.
- Reference and read acquisition are separate adapters.
- SRA read archives may materialize FASTQ; reference annotations/sequences do
  not.

## Blocked by

- [AUDIT-99](../TODO/AUDIT-99-final-refactor-and-documentation-audit.md) — Required: public acquisition must not divert the current refactor.

## Completion unblocks

- None.

## Prerequisites

- The implemented YAML+TSV intake and reference registry must have stable
  contracts, identity, provenance, and retry behavior.

## Required context

- Intake lifecycle, reference-provenance contracts, public NCBI/SRA primary
  documentation at execution time, storage policy, hashes, licenses, and
  cluster transfer constraints.

## Questions owned by this card

- [`CHOICE-DATA-01`](../../design/QUESTIONS.md#choice-data-01--first-public-reference-and-read-endpoints).

## In scope

- Reference adapter, SRA/read adapter, accession/version identity, checksum,
  format validation, resumable download, registration, and failure/retry design.

## Out of scope

- Converting reference records to FASTQ, scraping arbitrary websites, silent
  reference upgrades, automatic production execution, or broad ENA/GEO support.

## Deliverables

- Separate adapter designs, priority rationale, security/storage model, and
  small implementation/prototype cards.

## Acceptance evidence

- Reference and read artifacts retain authoritative accession/version/hash
  provenance and enter existing intake through typed contracts.
- Retry/caching cannot silently substitute mutable upstream content.

## Canonical documentation updates

- `FUTURE_ARCHITECTURE.md`, intake/reference docs, `DECISIONS.md`,
  `QUESTIONS.md`, task registry, and this card.

## Escalation conditions

- Stop for mutable/unversioned upstream data, unclear licensing/access,
  uncontrolled storage growth, or any proposal to treat references as reads.

## Completion record

Not started. This future-only card requires a separate planning discussion and
approval after the current refactor.
