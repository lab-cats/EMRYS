# Semantic workflow identity and DAG

This file owns the built-in paired-CMH workflow's semantic identities,
historical aliases, typed inputs, and direct artifact edges. Owner contracts
define local behavior. An admitted collaborator descriptor owns its Run-specific
Step `09` and optional Step `10` tail; this map is not a provider registry,
universal Stage hierarchy, orchestration contract, or archival policy.

## Identity rules

Each owner has one `stage`, `analysis`, or `evidence` kind, one public slug, and
one frozen `emrys.<kind>.<slug>.v1` key. Display titles may change without
changing identity. Paths, implementations, DAG position, and numeric historical
aliases define neither identity nor order.

## Identity map

| Kind | Display title | Public slug | Frozen machine key | Historical aliases |
| --- | --- | --- | --- | --- |
| stage | Construct STAR Index | `construct_STAR_index` | `emrys.stage.construct_STAR_index.v1` | `00a` |
| stage | Convert GTF to BED12 | `convert_GTF_to_BED12` | `emrys.stage.convert_GTF_to_BED12.v1` | `00b` |
| stage | Construct FASTA Sidecars | `construct_FASTA_sidecars` | `emrys.stage.construct_FASTA_sidecars.v1` | `00c` |
| stage | Align RNA Reads with STAR | `align_RNA_reads_with_STAR` | `emrys.stage.align_RNA_reads_with_STAR.v1` | `01` |
| stage | Construct Canonical BAM | `construct_canonical_BAM` | `emrys.stage.construct_canonical_BAM.v1` | `02` |
| evidence | Collect Canonical BAM QC Evidence | `collect_canonical_BAM_QC_evidence` | `emrys.evidence.collect_canonical_BAM_QC_evidence.v1` | `02b` |
| evidence | Collect RSeQC Paired Orientation Evidence | `collect_RSeQC_paired_orientation_evidence` | `emrys.evidence.collect_RSeQC_paired_orientation_evidence.v1` | `03` |
| stage | Mark BAM Duplicates with Picard | `mark_BAM_duplicates_with_Picard` | `emrys.stage.mark_BAM_duplicates_with_Picard.v1` | `04` |
| stage | Split N-Cigar Reads with GATK | `split_N_cigar_reads_with_GATK` | `emrys.stage.split_N_cigar_reads_with_GATK.v1` | `05` |
| stage | Partition BAM by Mechanical Read Orientation | `partition_BAM_by_mechanical_read_orientation` | `emrys.stage.partition_BAM_by_mechanical_read_orientation.v1` | `06` |
| stage | Generate Partitioned Cohort Mpileup VCFs | `generate_partitioned_cohort_mpileup_VCFs` | `emrys.stage.generate_partitioned_cohort_mpileup_VCFs.v1` | `07` |
| stage | Preprocess and Annotate Cohort Candidates | `preprocess_and_annotate_cohort_candidates` | `emrys.stage.preprocess_and_annotate_cohort_candidates.v1` | `08` |
| analysis | Rank Cohort Candidates with Paired CMH | `rank_cohort_candidates_with_paired_CMH` | `emrys.analysis.rank_cohort_candidates_with_paired_CMH.v1` | `09` |
| analysis | Project Candidate Scientific Context | `project_candidate_scientific_context` | `emrys.analysis.project_candidate_scientific_context.v1` | `10` |

## Edge semantics

A direct edge exists only when one owner produces an artifact required by
another; validators are not nodes. `fan-in` names distinct upstream artifacts,
`barrier` requires the consumer's complete declared set, and `evidence branch`
is non-gating. External inputs create no producer node. Operational coupling,
aliases, filenames, prose order, directories, and imports create no semantic
edge.

## Typed external inputs

| Input type | Meaning | Current semantic consumers |
| --- | --- | --- |
| `reference_fasta` | Materialized reference FASTA supplied outside the computational-stage DAG. | `construct_STAR_index`, `construct_FASTA_sidecars`, `split_N_cigar_reads_with_GATK`, `generate_partitioned_cohort_mpileup_VCFs`, `project_candidate_scientific_context` |
| `reference_gtf` | Materialized reference GTF supplied outside the computational-stage DAG. | `construct_STAR_index`, `convert_GTF_to_BED12`, `preprocess_and_annotate_cohort_candidates` |
| `paired_rna_fastq` | One externally supplied read-1/read-2 RNA-seq FASTQ pair for a declared sample. | `align_RNA_reads_with_STAR` |
| `sample_manifest` | Explicit sample identities and canonical sample order. | `generate_partitioned_cohort_mpileup_VCFs`, `preprocess_and_annotate_cohort_candidates`, `rank_cohort_candidates_with_paired_CMH` |
| `partition_manifest` | Explicit partition identities and selectors. | `generate_partitioned_cohort_mpileup_VCFs`, `preprocess_and_annotate_cohort_candidates`, `rank_cohort_candidates_with_paired_CMH` |

Runtime tools and scalar parameters are stage-local contract inputs, not DAG
nodes.

## Direct DAG edges

This table is the complete set of direct artifact edges for the currently
supported default workflow.

| Producer | Consumer | Artifact | Semantics |
| --- | --- | --- | --- |
| `construct_STAR_index` | `align_RNA_reads_with_STAR` | STAR genome-index directory | required artifact |
| `align_RNA_reads_with_STAR` | `construct_canonical_BAM` | coordinate-sorted STAR BAM | required artifact |
| `construct_canonical_BAM` | `collect_canonical_BAM_QC_evidence` | canonical BAM/BAI pair | required artifact; non-gating evidence branch |
| `construct_canonical_BAM` | `collect_RSeQC_paired_orientation_evidence` | canonical BAM/BAI pair | required artifact; fan-in; non-gating evidence branch |
| `convert_GTF_to_BED12` | `collect_RSeQC_paired_orientation_evidence` | BED12 annotation | required artifact; fan-in; non-gating evidence branch |
| `construct_canonical_BAM` | `mark_BAM_duplicates_with_Picard` | canonical BAM/BAI pair | required artifact |
| `mark_BAM_duplicates_with_Picard` | `split_N_cigar_reads_with_GATK` | duplicate-marked BAM/BAI pair | required artifact; fan-in |
| `construct_FASTA_sidecars` | `split_N_cigar_reads_with_GATK` | reference FAI and sequence dictionary | required artifact; fan-in |
| `split_N_cigar_reads_with_GATK` | `partition_BAM_by_mechanical_read_orientation` | split-N-cigar BAM/BAI pair | required artifact |
| `partition_BAM_by_mechanical_read_orientation` | `generate_partitioned_cohort_mpileup_VCFs` | both orientation BAM/BAI pairs for every declared sample | required artifact; declared-sample barrier; fan-in |
| `construct_FASTA_sidecars` | `generate_partitioned_cohort_mpileup_VCFs` | reference FAI paired with the external reference FASTA | required artifact; fan-in |
| `generate_partitioned_cohort_mpileup_VCFs` | `preprocess_and_annotate_cohort_candidates` | receipt and both orientation VCFs for every declared partition | required artifact; declared-partition-and-orientation barrier |
| `preprocess_and_annotate_cohort_candidates` | `rank_cohort_candidates_with_paired_CMH` | sites table and Step 08 input receipt | required artifact |
| `rank_cohort_candidates_with_paired_CMH` | `project_candidate_scientific_context` | all-sites, significant-sites, and summary tables | required artifact; complete Step 09 transaction barrier |
| `construct_FASTA_sidecars` | `project_candidate_scientific_context` | reference FAI paired with the external reference FASTA | required artifact; fan-in |

## Current operational coupling that is not a semantic edge

The retired Step `00a` scheduler wrapper materialized shared FASTA/GTF inputs for
historical Steps `00b` and `00c`; it created no `00a -> 00b` or `00a -> 00c`
edge because neither consumer used the STAR index. The current workflow admits
those references as typed external inputs, not outputs of another stage.
