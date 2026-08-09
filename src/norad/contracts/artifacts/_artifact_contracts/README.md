# Artifact-contract validator implementation owners

This private package supports the public
[`validate_artifact_contracts.py`](../validate_artifact_contracts.py) command
and compatibility facade. The package remains private to the artifact-contract
owner.

| Module | Owned responsibility |
| --- | --- |
| [`core.py`](core.py) | Compatibility owner for the established shared private bindings. |
| [`definitions.py`](definitions.py) | Schema locations, vocabularies, and the shared validation-error identity. |
| [`schema.py`](schema.py) | Closed-registry JSON/schema loading, deterministic diagnostics, and hashing. |
| [`identity.py`](identity.py) | Run-contract hashing, explicit paths, unique identities, and attempt graphs. |
| [`evidence.py`](evidence.py) | Computational status and evidence-reference semantics. |
| [`artifact.py`](artifact.py) | Artifact-record semantic validation. |
| [`scientific_review.py`](scientific_review.py) | Scientific-review-record semantic validation. |
| [`report_receipt.py`](report_receipt.py) | Report-receipt semantic validation. |
| [`inventory.py`](inventory.py) | Explicit inventory admission and record/run-summary reconciliation. |
| [`run_summary.py`](run_summary.py) | Compatibility owner for run-summary bindings. |
| [`run_summary_status.py`](run_summary_status.py) | Run-summary status reduction. |
| [`run_summary_validation.py`](run_summary_validation.py) | Run-summary semantic validation. |

The public facade imports these modules through the `norad.contracts` package.
It retains schema/document orchestration, the live semantic dispatcher, and
CLI control while exact report-receipt and inventory function objects come
from their private responsibility owners. All modules share the one
`ContractValidationError` originating in
`definitions.py`; `core.py` continues to re-export that identity for
compatibility.
