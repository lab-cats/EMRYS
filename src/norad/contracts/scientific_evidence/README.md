# Scientific-evidence contract owners

This neutral package publishes the shared Step 08 and Step 09 computational
table contracts. It does not implement pipeline computation, candidate review
or adjudication, artifact publication, or independent test oracles.

| Public module | Responsibility |
| --- | --- |
| [`step08.py`](step08.py) | Direct owner of Step 08 headers, parsing, path- and exact-byte manifest validation, and table reconciliation. |
| [`step09.py`](step09.py) | Direct owner of Step 09 headers, intrinsic result-trio admission, full owner validation primitives, mutation-spectrum reconciliation, and scientific plot-PDF validation. |

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
