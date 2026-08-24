# Artifact-contract validator implementation owners

This private package supports the grouped
`python -I -m emrys validate artifact-contracts` route through private
[`validator.py`](../validator.py) and the curated reporting
[`api.py`](../api.py). The responsibility modules remain private to the
artifact-contract owner.

| Module | Owned responsibility |
| --- | --- |
| [`definitions.py`](definitions.py) | Schema locations, vocabularies, and the shared validation-error identity. |
| [`schema.py`](schema.py) | Closed-registry JSON/schema loading, deterministic diagnostics, and hashing. |
| [`identity.py`](identity.py) | Run-contract hashing, explicit paths, unique identities, and attempt graphs. |
| [`evidence.py`](evidence.py) | Computational status and evidence-reference semantics. |
| [`artifact.py`](artifact.py) | Artifact-record semantic validation. |
| [`report_receipt.py`](report_receipt.py) | Report-receipt semantic validation. |
| [`inventory.py`](inventory.py) | Explicit inventory admission and record/run-summary reconciliation. |
| [`run_summary_status.py`](run_summary_status.py) | Run-summary status reduction. |
| [`run_summary_validation.py`](run_summary_validation.py) | Run-summary semantic validation. |

The curated API imports exact function objects from these responsibility
owners and owns the live semantic dispatcher used by the grouped validator.
The private validator retains argument selection and document orchestration.
Private modules import the one `ContractValidationError` identity directly
from `definitions.py`; there is no compatibility re-export layer.
