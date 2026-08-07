# Validation infrastructure

The `norad.libraries.validation` facade is the stable import used by owner-local
validators. Implementation is separated by responsibility:

- `errors.py`: `ValidationError` and `fail`
- `inputs.py`: file snapshots, stable reads, and unchanged-input enforcement
- `report.py`: row construction, rendering, and report-schema validation
- `publication.py`: lock-protected transactional publication
- `runtime.py`: shared dry-run/execute completion lifecycle

Check IDs, input selection, external-tool commands, evidence interpretation,
and scientific claims remain in the consuming validator.
