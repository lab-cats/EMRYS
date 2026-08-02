# `preprocess_and_annotate_cohort_candidates` stage contract

This is the observed contract of historical Step `08` for `ARCH-02A`. The
exact public identity and historical alias are owned by the
[semantic stage map](../../contracts/STAGE_MAP.md#identity-map). This directory
uses that public slug; it is not yet an implemented source location.
Executables remain in `scripts/` and `jobs/`.

## Responsibility and execution dependencies

Validate the complete declared Step `07` partition-by-orientation VCF set,
expand alternate alleles, retain supported SNVs, attach per-sample depth and
allele measurements plus GTF overlaps, apply the fixed provisional legacy
orientation mapping, and publish one deterministic cohort transaction for
analysis.

Step `08` is a cohort barrier: it requires one receipt and both VCFs for every
partition in manifest order. It rejects overlaps across declared partitions,
revalidates Step `07` receipts and VCF structure, and hashes the current
receipts and VCFs into its own input receipt. Step `09` consumes the Step `08`
sites table and input receipt, not the QC summary.

## Inputs and provisional policy

Inputs are a safe cohort ID, ordered sample manifest, complete nonoverlapping
partition manifest, Step `07` root, nonempty annotation GTF, output and QC
roots, and explicit Rscript/R-program resolution. Required VCF definitions
include FORMAT DP/AD/ADF/ADR/SP and INFO AD/ADF/ADR; sample columns must match
the sample manifest exactly.

The fixed `legacy_provisional_v1` compatibility policy maps:

```text
FWD_like -> annotation_strand + and complemented genomic REF/ALT for RNA alleles
REV_like -> annotation_strand - and unchanged genomic REF/ALT for RNA alleles
```

This mapping is not validated biological strand, library-strandedness, sense,
or antisense interpretation. Symbolic and non-SNV alternate alleles are counted
but omitted from the published candidate table. Supported SNVs receive
partition-independent candidate IDs, GTF gene/transcript and CDS/UTR/exon/intron
overlaps, source QUAL/FILTER/INFO alternate depth, and per-sample DP, AD, and
derived AF fields. An exact-header sites table with no candidate rows is valid
when all input and summary counts reconcile.

## Outputs and transaction marker

The three outputs are:

```text
<cohort>/<cohort>.step08_sites.tsv
<cohort>/<cohort>.step08_inputs.tsv
<qc-root>/<cohort>.step08_summary.tsv
```

The sites header contains 22 fixed metadata fields followed by manifest-ordered
`DP__`, `AD__`, and `AF__` columns for every sample. The input receipt has one
row per partition/orientation, ordered by the partition manifest then
`FWD_like`, `REV_like`; it binds Step `07` receipt and VCF hashes, manifest
hashes, annotation path/hash, observed and skipped counts, and policy. The
one-row summary reconciles aggregate counts and identities.

[`step_08_vcf_preprocessing.sh`](../../../../scripts/step_08_vcf_preprocessing.sh)
is side-effect-free in dry-run. Execute mode uses a cohort lock, run-token
temporary/backup paths, all-three-or-none prior-state enforcement, repeated
input hash checks, prepublication validation, and rollback. It publishes sites,
then summary, then the input receipt as the native commit marker, revalidates
the visible set, verifies hashes and stable inputs, and only then marks the
attempt committed.

The receipt is therefore visible briefly before final post-publication checks;
presence alone is not independent proof that the producer returned success.
Failed restore moves preserve remaining backups, but no recovery marker or
automated recovery interface exists, and cleanup releases the cohort lock even
when restoration is incomplete.

[`step_08_vcf_preprocessing.R`](../../../../scripts/step_08_vcf_preprocessing.R)
owns semantic parsing, candidate construction, provisional orientation policy,
annotation, and deterministic TSV generation. The shell owns orchestration,
validation, locking, and publication.

[`step_08_vcf_preprocessing.slurm`](../../../../jobs/step_08_vcf_preprocessing.slurm)
owns cluster defaults, modules and optional repository-local R environment,
execution gating, delegation, and final path checks.

## Validation interface

[`validate_step_08_preprocessing_outputs.py`](../../../../scripts/validate_step_08_preprocessing_outputs.py)
accepts explicit cohort, manifests, annotation GTF, the three outputs, and a
report path. It does not invoke R. Dry-run prints the common report;
`--execute` snapshot-rechecks inputs and uses Step `00a`'s shared publisher.

Exact checks are:

- `output_transaction`;
- `manifest_annotation_identity`;
- `input_receipt_reconciliation`;
- `sites_order_uniqueness`; and
- `summary_count_reconciliation`.

The validator enforces exact dynamic headers, complete ordered
partition/orientation rows, manifest and annotation identities, typed
per-input arithmetic, unique candidate IDs, sample DP/AD/AF consistency,
per-scope candidate counts, and aggregate summary reconciliation. It validates
the published tables' internal contract; it does not rerun VariantAnnotation,
GTF overlap, allele expansion, provisional complementation, or upstream VCF
filtering. Despite its check name, `sites_order_uniqueness` does not recompute
candidate IDs or prove deterministic row order.

Content mismatches publish `status=fail`; unsafe structure or report-
publication failures exit `2`.

## Consumers and protected evidence

- Step `09` requires exact Step `08` sites and input receipt paths, hashes and
  schemas, preserves the entire candidate order/universe in its all-sites
  output, and carries the provisional policy forward.
- Step `09c` scientific review later requires all three Step `08` outputs; this
  additional review dependency is not part of Step `09` computation.
- Artifact adapters register all three outputs and
  `step08_validation_report_v1`; reporting consumes registered evidence
  without rerunning R.
- Direct shell, R, and Python validator suites protect the cohort barrier,
  schema, allele/count rules, annotation, policy, dry-run, locks, replacement,
  rollback, and independent validation boundary.
- Wrapper, roster, publication-fault, public-CLI, artifact, report, coverage,
  and Step `09` consumer tests protect cross-boundary behavior.

This is local fixture characterization, including guarded real-R fixtures, not
production, cluster, scientific-review, or biological evidence.

## Ownership gaps and deferred decisions

- Shared Step `08` schemas and reconciliation currently live in the Step `09c`
  scientific-validation module and are reused by the independent validator.
- The producer declares the input receipt as its commit marker, while the
  artifact adapter treats the summary as the native-transaction failure
  marker; ownership must resolve this disagreement.
- Receipt and candidate checks are duplicated across shell, R, Python,
  Step `09`, and artifact adapters; shared report publication remains owned by
  the Step `00a` validator.
- Producer and validator disagree on the required breadth of sample-manifest
  columns, and the validator does not reopen the upstream Step `07` files to
  recompute their declared hashes.
- The producer preserves the supplied annotation path spelling, while the
  validator compares it with a resolved absolute path; equivalent relative
  paths can therefore yield failed annotation-identity evidence.
- The commit marker does not hash its sibling sites or summary outputs, and
  provenance omits R/package versions and Step `07` tool/reference/filter
  parameters.
- The orientation policy mixes compatibility behavior with preprocessing and
  remains explicitly provisional.
- Target files, policy/schema ownership, recovery design, and
  migration mechanics remain deferred.
