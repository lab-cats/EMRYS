# `project_candidate_scientific_context` analysis contract

This directory owns the bounded post-Step09 scientific-context projection. Its
public identity is `emrys.analysis.project_candidate_scientific_context.v1`;
workflow integration may use historical execution alias `10`, but numeric
order does not define the owner.

## Responsibility and non-goals

The owner consumes the exact Step `09` all-sites, significant-sites, and
summary tables plus one indexed reference and the repository-tracked PUM motif
catalog. It publishes candidate sequence context, every exact motif hit,
position-frequency values, and descriptive/inferential motif statistics for
deterministic report rendering.

It never opens a BAM/CRAM/VCF, recounts alleles, changes a Step `09` test or
call, performs de novo motif discovery, chooses a transcript isoform, infers
biological strand, or renders a plot. Its results remain context attached to
CMH-ranked candidates, not evidence of editing, binding, or biological truth.

## Fixed scientific policy

Context-eligible rows are the Step `09` statuses `significant_up`,
`significant_down`, `fdr_not_met`, and `effect_not_met`. They map respectively
to `significant_up`, `significant_down`, and the combined `background`
population. Other statuses are not silently used as comparison opportunities.

For each eligible candidate, the producer:

1. requires the chromosome name exactly as written in the supplied FAI;
2. verifies that the FASTA center equals `genomic_ref`;
3. extracts the clipped continuous genomic `-100..+100` window;
4. keeps it as written when genomic and RNA alleles agree, otherwise reverse-
   complements it when both genomic alleles complement to the RNA alleles; and
5. verifies that the presented center equals `rna_ref`.

This is `legacy_rna_change_oriented_genomic_v1`. It is mechanical continuous
genomic context, not validated transcript sequence or 5-prime-to-3-prime RNA
orientation. A full 201-base window is `available`; an honestly clipped edge
window is `boundary_truncated` and is excluded from logo, motif, and enrichment
calculations while remaining accounted in candidate context.

The fixed catalog contains only `PUM_UGUANA`, RNA consensus `UGUANA`, and DNA
consensus `TGTANA`. Matching uses the exact overlapping presented-strand regex
`TGTA[ACGT]A`; it does not scan the opposite genomic strand or estimate a PWM
score. Every match is emitted. Position summaries use one nearest hit per
candidate, selected by absolute midpoint distance then the smaller/upstream
start, in left-closed 10-nucleotide bins from `[-100,-90)` through `[90,100)`.

The logo matrix covers positions `-10..+10`, bases `A,C,G,T`, and all three
populations. Counts are retained below minimum population sizes, with an
explicit `population_below_minimum` status. Minimum complete-context counts are
10 for either significant direction and 20 for background.

The sole inferential row tests `significant_up` against background candidate-
level motif presence using a two-sided Fisher exact test. When available, its
effect is Fisher's conditional maximum-likelihood odds-ratio estimate with an
exact two-sided 95% confidence interval. The row becomes
`population_below_minimum`, `background_below_minimum`, or
`uninformative_table` instead of inventing a fallback. Because v1 registers
one motif, `fisher_p_value_bh` is `NA` and the receipt records
`none_single_registered_motif`. Adding a multi-model family requires a new
versioned contract and approval. Significant-down context remains separate and
descriptive.

At most eight significant candidates receive a display rank. Selection is
FDR ascending, absolute treatment-control AF difference descending, then
candidate ID. This is a bounded presentation roster, not a new scientific
rank or modification of Step `09`.

## Inputs and five-output transaction

Inputs are a safe analysis ID; nonempty Step `09` all/significant/summary TSVs;
nonempty FASTA and exact FAI; the exact one-row owner motif catalog; output
root; explicit Rscript/R-program resolution; and the repository commit. The
shell hashes all six scientific inputs before R, passes those bound digests to
the receipt producer, and rechecks them after R and after publication.
Execute mode uses the bound `EMRYS_SHA256_PYTHON` launcher, or an absolute
`python3` resolved from `PATH`, for owner-local fsync barriers.

Stable outputs under `<output-root>/<analysis-id>/` are:

```text
<analysis>.candidate_context.tsv
<analysis>.motif_hits.tsv
<analysis>.sequence_logo.tsv
<analysis>.motif_statistics.tsv
<analysis>.context_receipt.tsv
```

The four payload headers and canonical receipt header are owned by
`emrys.contracts.scientific_evidence.scientific_context`. The receipt binds
absolute canonical input/output paths, lowercase hashes, data-row counts,
the transaction and receipt schema versions, every fixed policy,
R/Biostrings/Rsamtools versions, producer, commit, and complete state. The R
producer serializes and hashes all four
payloads before serializing the receipt. The shell fsyncs all five closed
staging files, publishes all payloads and then the receipt last, and fsyncs the
analysis directory before treating the transaction as committed.

Dry-run creates no output path and invokes no R process. Execute mode acquires
an analysis-owned lock, refuses incomplete prior stable sets, uses run-token
staging and backups, checks inputs at the two post-baseline boundaries,
validates receipt/payload hashes before and after publication, and durably
rolls back or restores a failed replacement. Under
`--no-clobber`, a complete predecessor is rejected and first publication is
create-exclusive with retained staging inode anchors through final checks.
Ambiguous or incomplete rollback retains the lock and residue for operator
recovery.

The receipt can become visible before the shell's final post-publication hash
and input checks. Its presence alone is therefore not proof that the producer
returned success.

## Validation and evidence boundary

The grouped `emrys validate scientific-context-projection` route
accepts only `--receipt`, common `--output`, and optional `--execute`. It
snapshots the receipt and every bound file, performs one canonical transaction
admission, and publishes exactly one check:

```text
scientific_context_transaction
```

That admission revalidates the Step `09` projection, literal motif catalog,
all exact context/hit/logo/statistics semantics, stable hashes and counts,
display roster, and receipt constants. It independently re-derives every
candidate window from the bound FASTA/FAI, including orientation, clipping,
and center-base agreement. It does not rerun R. Focused producer tests and the
independent contract oracle protect the computation boundary separately.

Repository tests protect this deterministic reporting context under the shared
[evidence ceiling](../../../../../tests/README.md); local execution or
validation is not candidate adjudication or biological proof.
