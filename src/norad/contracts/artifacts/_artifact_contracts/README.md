# Artifact-contract validator implementation owners

This private package supports the public
[`validate_artifact_contracts.py`](../validate_artifact_contracts.py) command
and compatibility facade. The package remains private to the artifact-contract
owner.

| Module | Owned responsibility |
| --- | --- |
| [`core.py`](core.py) | Schema locations, the shared validation error, JSON/schema loading, path rules, run contracts, attempt graphs, and computational evidence primitives. |
| [`artifact.py`](artifact.py) | Artifact-record semantic validation. |
| [`scientific_review.py`](scientific_review.py) | Scientific-review-record semantic validation. |
| [`run_summary.py`](run_summary.py) | Run-summary status reduction and semantic validation. |

The public facade imports these modules through the `norad.contracts` package.
It retains schema validation, report-receipt semantics,
the semantic dispatcher, inventory reconciliation, and CLI orchestration. All
modules share the one `ContractValidationError` defined in `core.py`.
