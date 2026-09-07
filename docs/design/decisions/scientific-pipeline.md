# Scientific pipeline decisions

These decisions preserve the scientific and artifact semantics that future
maintainers must not infer from historical step numbers or filenames. Exact
interfaces and checks remain in each functional owner's contract.

## Reference and BAM pipeline

### Use the Novogene-provided reference

Use the delivered reference unless a separate migration is approved. The FASTA,
annotation, sidecars, BED, and STAR index must reconcile to explicit declared
identities.

### Build STAR with the declared read-length overhang

Build the reference index with `sjdbOverhang=149` for the declared 150-base
reads. Validators inspect the configured value rather than infer it from a
filename.

### Generate BED12 from GTF

RSeQC consumes a deterministic BED12 derived from the declared GTF.

### Treat FASTA sidecars as Step `00c`

FAI and sequence-dictionary preparation is a formal validated owner, not an
undocumented prerequisite.

### Make Step `02` the canonical BAM boundary

Downstream owners consume coordinate-sorted, indexed BAMs with sample-specific
read-group metadata. Publication remains validation-first and
rollback-protected.

### Keep QC and downstream transformation as separate consumers

BAM QC, orientation inference, and duplicate marking consume the canonical BAM
independently. Evidence collection does not mutate that BAM.

### Mark rather than remove duplicates

Duplicate handling marks reads and preserves them for downstream policy rather
than removing them.

### Validate the effective Java runtime

Resolve and test the actual Java executable before Picard. Module names and
`JAVA_HOME` alone are insufficient evidence; fail before computation when the
effective major version is unsupported.

### Use project storage for large GATK temporary files

Route large GATK temporary files to an owned project-storage location and clean
only paths owned by the operation.

## Orientation and downstream analysis

### Separate mechanical orientation from biological strand

Retain neutral `FWD_like` and `REV_like` labels. Mechanical read grouping,
transcript strand, and biological sense or antisense interpretation are
different claims.

### Run Step `07` cohort-wide and manifest-partitioned

For each declared partition, process every manifest sample in manifest order
for both mechanical orientations. The selector type determines the bcftools
interface, and a receipt published last commits outputs and counts. Do not
discover inputs by glob or infer sample order.

### Consume only declared Step `07` transactions in Step `08`

Verify the complete partition/orientation cross-product, receipts, paths,
hashes, counts, and sample order before semantic parsing. Expand multiallelic
records deterministically; validate raw count lexemes before coercion, and count
then exclude symbolic or non-SNV alleles.

### Keep the orientation policy provisional

`legacy_provisional_v1` is a compatibility mapping, not biological validation.
Outputs and reports retain that limitation.

### Pair Step `09` samples only through manifest replicates

Pairing comes from explicit manifest replicate metadata, never sample names.
The declared design requires matching treatment/control replicate sets and at
least two strata.

### Use one paired CMH and global BH family

Retain every eligible and ineligible candidate with an explicit status. Use the
declared two-sided continuity-corrected CMH direction and one BH family across
successfully tested target candidates. Outputs are CMH-ranked candidates, not
validated editing sites.

### Keep context projection downstream of ranking

The built-in Step 10 projects report-ready sequence and registered PUM-motif
context from fixed Step 09 candidates. Version 1 uses mechanically
RNA-change-oriented continuous genomic windows, the registered
`PUM_UGUANA`/`TGTANA` model, significant-up foreground, tested
non-significant background, and two-sided Fisher enrichment. It performs no
motif discovery, editing call, binding claim, strand inference, or biological
validation. Display limits are presentation policy and must never silently
truncate the admitted machine-readable result.
