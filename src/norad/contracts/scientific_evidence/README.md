# Scientific-evidence contract owners

This neutral package publishes shared computational table contracts for Step
08, Step 09, and the post-Step09 scientific-context projection. It does not
implement pipeline computation, candidate review or adjudication, artifact
publication, figure rendering, or independent test oracles.

| Public module | Responsibility |
| --- | --- |
| [`step08.py`](step08.py) | Direct owner of Step 08 headers, parsing, path- and exact-byte manifest validation, carried-location lexical validation, and table reconciliation. |
| [`step09.py`](step09.py) | Direct owner of Step 09 headers, intrinsic result-trio admission, full owner validation primitives, mutation-spectrum reconciliation, and scientific plot-PDF validation. |
| [`scientific_context.py`](scientific_context.py) | Direct owner of the v1 candidate-context, known-motif hit, sequence-logo, motif-statistics, and receipt-last transaction contracts. |

The carried-location validator checks chromosome text, annotation-strand
vocabulary, semicolon-delimited annotation identifiers, and the exact five
`TRUE`/`FALSE` overlap flags. Step 08 admission and the Step 09 projection reuse
that one lexical boundary. It deliberately does not reannotate the GTF or turn
independent transcript overlaps into exclusive biological regions.

The modules define their supported constants and functions directly;
`__all__` names each public surface. `validate_step09_projection` canonically
admits the all-sites/significant-sites/summary read-side projection: headers,
sample blocks, analysis identity, values, summary counts/context, the exact
significant subset, and, when supplied, mutation-spectrum reconciliation.
Artifact paths, hashes, graphs, and display policy remain consumer-local.

The full Step 09 validator adds upstream Step 08 identity, paired-sample CMH,
global BH, PDF, and publication checks. The shell/R producer owns computation;
its independent oracle does not reuse production contract logic. Step 09
imports shared Step 08 definitions without re-exporting that module.

The `validate_sample_manifest_bytes` and `validate_partition_manifest_bytes`
entry points validate already-admitted bytes and use the supplied path only as
a diagnostic source label. They never reopen that pathname.

`validate_scientific_context_outputs` streams and cross-reconciles the four
figure-ready context TSVs before publication. A consumer admits the completed
transaction through `validate_scientific_context_transaction(receipt)`, which
revalidates the hash-bound Step 09 result trio, fixed PUM model, output hashes,
row counts, exact FAI/FASTA windows and center bases, population accounting,
exact overlapping hits, logo matrices, position bins, and Fisher result. The
mechanical RNA-change orientation is not a transcript-direction or
biological-strand claim.
