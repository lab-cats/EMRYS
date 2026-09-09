# Artifact-contract implementation

These private modules support [`validator.py`](../validator.py), the
`emrys validate artifact-contracts` command, and the reporting [`api.py`](../api.py).

| Module | Responsibility |
| --- | --- |
| [`definitions.py`](definitions.py) | Schema paths, vocabularies, and the shared error type. |
| [`schema.py`](schema.py) | Load registered JSON/schemas, hash bytes, and order diagnostics. |
| [`identity.py`](identity.py) | Hash Run contracts and validate paths, identities, and Attempt graphs. |
| [`evidence.py`](evidence.py) | Validate computational status and evidence references. |
| [`artifact.py`](artifact.py) | Validate artifact-record meaning. |
| [`report_receipt.py`](report_receipt.py) | Validate report-receipt meaning. |
| [`inventory.py`](inventory.py) | Check declared inventories and their agreement with records/summaries. |
| [`run_summary_status.py`](run_summary_status.py) | Combine artifact states into summary status. |
| [`run_summary_validation.py`](run_summary_validation.py) | Validate run-summary meaning. |

The API imports the same function objects and dispatches semantic validation;
the command selects arguments and coordinates documents. Private modules import
`ContractValidationError` directly from `definitions.py`, without compatibility
re-exports.
