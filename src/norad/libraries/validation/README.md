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

Current fault characterization shows that stable-input detection can miss a
same-size rewrite with restored modification time, and publication recovery can
delete a late foreign final or lose protection after incomplete rollback or
lock loss. These remain defects, not approved transaction semantics; recheck
them through `tests/libraries/test_validation_report.py` and every affected
consumer transaction suite. Any correction must preserve first and repeat
publication bytes, names, stage and predecessor validation, symlink and
identity rejection, signal behavior, descriptor cleanup, and recovery evidence
across those consumers; do not generalize this transaction to unrelated
publishers.
