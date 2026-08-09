# Scientific-evidence contract owners

This neutral package publishes shared table and evidence contracts. It does
not implement pipeline computation, scientific review policy, artifact
publication, or independent test oracles.

| Public module | Responsibility |
| --- | --- |
| [`step08.py`](step08.py) | Step 08 table contracts and shared parsing identities. |
| [`step09.py`](step09.py) | Step 09 compatibility contract consumed by validation, Step 09c, and artifact indexing. |
| [`review_package.py`](review_package.py) | Public Step 09c package roster, headers, vocabularies, and state reduction. |
| [`computational_validation.py`](computational_validation.py) | Computational-validation evidence table contract. |

Step 09 implementation is private and bounded:

| Private module | Responsibility |
| --- | --- |
| [`_step09_definitions.py`](_step09_definitions.py) | Exact headers and controlled vocabularies. |
| [`_step09_support.py`](_step09_support.py) | Scalar, path, PDF, status-count, and paired-sample helpers. |
| [`_step09_tables.py`](_step09_tables.py) | Result, summary, and mutation-spectrum table reconciliation. |
| [`_step09_semantics.py`](_step09_semantics.py) | Candidate, significance, background, and global BH semantics. |

The public `step09.py` module preserves the `step08`, `ContractError`, `Table`,
constant, and function identities used by existing consumers. These modules do
not import or implement the Step 09 shell/R CMH algorithm, and independent
oracle tests remain independent of production contract logic.
