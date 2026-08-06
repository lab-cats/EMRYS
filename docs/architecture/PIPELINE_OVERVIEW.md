# Current pipeline overview

This is the short scientist-facing view of NORAD's implemented RNA-seq and
RNA-editing candidate workflow. It groups the exact semantic owners into nine
explanatory phases; those phase labels are not machine identities, public
slugs, or scheduling commands. The canonical identities and direct artifact
edges remain in [`STAGE_MAP.md`](../../src/norad/contracts/STAGE_MAP.md).
The [`architecture index`](README.md) routes other system views.

- [Conceptual Mermaid source](diagrams/current_user_pipeline.mmd)
- [Detailed current system projection](diagrams/pipeline.mmd)
- [Owner-local commands and contracts](../../src/norad/stages/README.md)

Arrows below mean data or contract dependency, not automatic execution. NORAD
does not yet provide a one-command orchestrator, and its current owners remain
separately invoked.

## Nine explanatory phases

| Phase | Canonical semantic owner(s) | Purpose and ordering reason | Principal outputs and branches |
| --- | --- | --- | --- |
| Prepare the reference | `construct_STAR_index`; `convert_GTF_to_BED12`; `construct_FASTA_sidecars` | Establish the alignment index, transcript intervals, and FASTA sidecars before consumers require their coordinate and annotation contracts. These owners share external reference inputs but do not form a three-step dependency chain. | STAR index, BED12, FAI, and sequence dictionary. |
| Align reads | `align_RNA_reads_with_STAR` | Place each declared paired RNA-read input against the prepared STAR index before BAM normalization. | Coordinate-sorted STAR BAM and owner-local logs. |
| Canonicalize alignments | `construct_canonical_BAM` | Create the stable, coordinate-sorted, read-group-tagged BAM/BAI boundary used by downstream transformations and evidence branches. | Canonical BAM/BAI. |
| Inspect alignment evidence | `collect_canonical_BAM_QC_evidence`; `collect_RSeQC_paired_orientation_evidence` | Record non-gating BAM QC and mechanical library-orientation evidence from the canonical BAM; RSeQC also consumes BED12. | QC metrics and neutral paired-orientation evidence. This branch does not gate the main BAM path. |
| Prepare read evidence | `mark_BAM_duplicates_with_Picard`; `split_N_cigar_reads_with_GATK`; `partition_BAM_by_mechanical_read_orientation` | Mark duplicates, perform RNA-aware split-N-cigar handling, then form neutral mechanical-orientation BAM pairs before cohort observation. | Duplicate-marked and split-N-cigar BAM/BAI pairs, then `FWD_like` and `REV_like` BAM/BAI pairs. These labels are mechanical, not biological strand calls. |
| Observe the cohort | `generate_partitioned_cohort_mpileup_VCFs` | Count bases across every declared sample, partition, and mechanical orientation while preserving manifest order. | Receipt-last partitioned multi-sample VCF transactions. |
| Normalize and annotate candidates | `preprocess_and_annotate_cohort_candidates` | Validate the declared VCF set, expand alternate alleles, apply the provisional orientation conversion, annotate candidates, and publish deterministic TSVs before statistical comparison. | Sites TSV, exact input receipt, and QC summary TSV; unsupported non-SNV alleles are counted and excluded. |
| Rank paired candidates | `rank_cohort_candidates_with_paired_CMH` | Compare declared RNA reference/alternate counts across manifest-defined replicate strata, applying depth, statistical, and effect thresholds plus one global BH adjustment. An independently declared background cohort is optional. | Six-output transaction with all candidates, significant subset, summaries, spectrum, and plots. Outputs are **CMH-ranked candidates**, not validated editing sites. |
| Assemble review evidence | `assemble_scientific_review_evidence_package` | Combine the complete Step `08` and Step `09` transactions with explicit manifests and any separately supplied review evidence without rerunning analysis. | Deterministic review-evidence package with recorded, pending, absent, or limitation states. Explicit scientific review is optional and does not unlock biological readiness. |

## Exact continuing inputs

| Input or artifact contract | Where it continues to be consumed |
| --- | --- |
| Reference FASTA and its FAI | Reference preparation, split-N-cigar handling, and cohort observation. |
| Reference GTF | STAR-index construction, BED12 conversion, and Step `08` annotation. |
| BED12 | RSeQC paired-orientation inference. |
| Sample manifest | Steps `07`, `08`, and `09`, plus review-evidence assembly. |
| Partition manifest | Steps `07`, `08`, and `09`, plus review-evidence assembly. |
| Analysis/review declarations | Step `09` thresholds and optional background inputs; review plans and declared evidence enter only the review-evidence owner. |

## Reporting after the semantic workflow

Read-only artifact adapters and the canonical run-summary builder project
explicit native outputs and validation records into reporting inputs. Static
rendering is conditional on the selected HTML and/or PDF formats and publishes
a deterministic summary TSV plus a validated, identity-bound receipt last.
Reporting does not discover inputs, execute analysis, repair artifacts, or
promote runtime, cluster, scientific-review, or biological evidence.

## Prose fallback

NORAD prepares a shared reference universe, aligns each declared read pair,
and converts the alignment into a canonical BAM. QC and mechanical-orientation
evidence branch from that boundary while the main BAM continues through
duplicate marking, RNA-aware splitting, and neutral mechanical-orientation
partitioning. Manifest-declared samples and partitions then enter cohort
mpileup; the exact VCF set is normalized and annotated before paired-CMH
ranking. The complete candidate transactions can flow directly into the
review-evidence package, while any scientific review joins only when explicitly
supplied. Read-only reporting may then publish selected static formats from a
validated canonical summary.

Computational completion is not a biological conclusion. `FWD_like` and
`REV_like` are mechanical labels, `science_review_complete_exploratory` remains
provisional, and `biological_interpretation_ready` remains reserved pending a
separately authorized policy.
