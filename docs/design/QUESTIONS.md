# Questions

This file contains open questions and a concise index of resolved questions.
Durable answers and rationale belong in [`DECISIONS.md`](DECISIONS.md);
current blockers belong in
[`../operations/HANDOFF.md`](../operations/HANDOFF.md).

## Open

### Production sample manifest

- Where is the immutable six-row runtime manifest stored?
- Should a safe canonical copy be tracked or remain cluster-local?
- What is its SHA-256 and retention policy?
- Have explicit replicate values been added before Steps `07`–`09` promotion?

### CSU batch runtime

- Which compute-visible R/Rscript and required namespaces are supported?
- Which hash utilities and exact tool paths are available in batch jobs?
- Is Java 17 consistently available across eligible compute nodes?

### Storage and retention

- What are the home, project-storage, and scratch quotas?
- Which location should large temporary and intermediate files use?
- What retention policy is approved for native and derived artifacts?

### Reference provenance

- What exact Novogene annotation release produced the delivered GTF?
- Do FASTA, FAI, DICT, GTF, BED, and STAR index contigs reconcile?
- Is the mitochondrial contig consistently named and included in the approved
  primary correction universe?

### Runtime promotion

- Are Step `07` resources sufficient for pilot, chromosome, and full primary
  partitions?
- Does real bcftools reproduce the locally tested VCF and receipt contracts?
- What evidence is required before downstream runtime promotion proceeds?

### Scientific policy

- What orthogonal orientation evidence is required?
- What annotation, statistical, replicate, sensitivity, and candidate
  adjudication exits are mandatory?
- What separately approved policy, if any, may unlock
  `biological_interpretation_ready`?

## Resolved index

Durable decisions are recorded in [`DECISIONS.md`](DECISIONS.md), including:

- TSV manifests and explicit manifest-defined sample pairing;
- local-first development with SLURM scaling;
- descendant branches and separate docpatch gates;
- dry-run-first scripts and wrappers;
- Novogene reference use and STAR overhang;
- canonical BAM/read-group and rollback-protected publication rules;
- reverse-stranded/first-strand-style cohort evidence;
- separation of mechanical orientation from biological interpretation;
- Java/Picard, TMPDIR, and module-output handling;
- Step `07` cohort/partition and receipt contracts;
- Step `08` declared-input transaction and provisional orientation policy;
- Step `09` paired CMH, global BH family, and six-output transaction;
- guarded local R and explicit dependency restoration;
- separation of computational proof, scientific review, and biological state;
- structured artifact/reporting decoupling;
- documentation ownership and task-bounded canonical reading;
- one complete computational gate per executable state and failure-first local
  validation output.

Implementation status and remaining package order are intentionally not copied
here; see [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md).
