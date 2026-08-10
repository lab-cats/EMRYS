# Source-owner documentation footprint audit

## Scope and rule

At commit `755678ec28a6aa4e58149447704551312e365254`, `src/norad` contained
`47` tracked `README.md` or `CONTRACT.md` files totaling `5,856` lines. The
earlier estimate of `5,809` was stale by `47` lines.

The audit used one ownership rule:

- `CONTRACT.md` owns exact responsibility, inputs, outputs, execution surfaces,
  validation, consumers, protected behavior, defects, and evidence limits.
- A colocated `README.md` owns only orientation, exact operator commands,
  diagnostics/recovery routing, and focused test commands.
- A README without a colocated contract remains the local owner of its unique
  directory-level context and was not mechanically shortened.

No `CONTRACT.md` changed: all 14 contracts remain `2,461` lines. Twelve paired
READMEs remove duplicated contract narrative and historical migration receipts
while retaining public entry points, dry-run/execute distinctions, scheduler
bindings, recovery warnings, focused tests, and evidence ceilings. The STAR-
index and GTF-conversion READMEs were already concise and remain unchanged.

After the audit, the 33 READMEs total `1,889` lines, down from `3,395`; all 47
files total `4,350` lines, a reduction of `1,506` lines (`25.7%`) with exact
contract bytes unchanged.

## Paired owners

| Owner | README disposition | Contract disposition |
| --- | --- | --- |
| `analyses/rank_cohort_candidates_with_paired_CMH` | compact operator sheet | unchanged |
| `evidence/assemble_scientific_review_evidence_package` | compact operator sheet | unchanged |
| `evidence/collect_RSeQC_paired_orientation_evidence` | compact operator sheet | unchanged |
| `evidence/collect_canonical_BAM_QC_evidence` | compact operator sheet | unchanged |
| `stages/align_RNA_reads_with_STAR` | compact operator sheet | unchanged |
| `stages/construct_FASTA_sidecars` | compact operator sheet | unchanged |
| `stages/construct_STAR_index` | already concise; retained | unchanged |
| `stages/construct_canonical_BAM` | compact operator sheet | unchanged |
| `stages/convert_GTF_to_BED12` | already concise; retained | unchanged |
| `stages/generate_partitioned_cohort_mpileup_VCFs` | compact operator sheet | unchanged |
| `stages/mark_BAM_duplicates_with_Picard` | compact operator sheet | unchanged |
| `stages/partition_BAM_by_mechanical_read_orientation` | compact operator sheet | unchanged |
| `stages/preprocess_and_annotate_cohort_candidates` | compact operator sheet | unchanged |
| `stages/split_N_cigar_reads_with_GATK` | compact operator sheet | unchanged |

## Standalone READMEs retained

The other 19 files are concise package, facade, private-module, or cross-cutting
owners with no colocated contract to absorb their unique content:

```text
contracts/artifacts/{README.md,_artifact_contracts/README.md}
contracts/scientific_evidence/README.md
evidence/{README.md,reference_provenance/README.md,runtime_preflight/README.md,storage_inventory/README.md}
evidence/assemble_scientific_review_evidence_package/_scientific_review/README.md
ingestion/{README.md,sample_manifest_admission/README.md}
libraries/{README.md,validation/README.md}
reporting/{README.md,_artifact_index/README.md,_run_report/README.md,_run_summary/README.md,styles/README.md,templates/README.md}
stages/README.md
```

## Verification boundary

The documentation gate protects presence and adjacency but does not prove every
sentence against runtime behavior. Focused owner tests protect commands and
public behavior; unchanged contract bytes protect the exact textual contract.
This audit changes no executable, schema, artifact, recovery mechanism,
scientific policy, or evidence state.
