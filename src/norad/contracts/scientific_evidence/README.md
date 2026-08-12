# Scientific-evidence contract owners

This neutral package publishes shared table and evidence contracts. It does
not implement pipeline computation, scientific review policy, artifact
publication, or independent test oracles.

| Public module | Responsibility |
| --- | --- |
| [`step08.py`](step08.py) | Direct owner of Step 08 headers, parsing, path- and exact-byte manifest validation, and table reconciliation. |
| [`step09.py`](step09.py) | Direct owner of Step 09 headers, table reconciliation, scientific plot-PDF validation, and candidate/CMH-result semantics. |
| [`review_package.py`](review_package.py) | Public Step 09c package roster, headers, vocabularies, and state reduction. |
| [`computational_validation.py`](computational_validation.py) | Computational-validation evidence table contract. |

The public `step08.py` and `step09.py` modules define their supported constants
and functions directly, with each module's `__all__` naming its complete public
surface. This includes the parsing and reconciliation helpers consumed by
validators, Step 09, Step 09c, and artifact indexing. Step 09 explicitly imports
shared definitions from Step 08 without exposing the Step 08 module as part of
its API. Neither module imports or implements the Step 08 R algorithm or Step 09
shell/R CMH algorithm, and independent oracle tests remain independent of
production contract logic. Step 09 `validate_pdf` remains the
scientific-analysis plot validator used by Step 09 validation and Step 09c.

The `validate_sample_manifest_bytes` and `validate_partition_manifest_bytes`
entry points validate already-admitted bytes and use the supplied path only as
a diagnostic source label. They never reopen that pathname.
