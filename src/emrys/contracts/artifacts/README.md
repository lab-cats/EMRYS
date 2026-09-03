# Artifact-contract owner

`emrys validate artifact-contracts` validates the closed artifact-record,
run-summary, and report-receipt schemas through private [`validator.py`](validator.py).
Reporting imports the curated [`api.py`](api.py) surface. Neither interface
discovers artifacts, builds indexes, renders reports, repairs inputs, or
promotes evidence.

The packaged registry spans shared definitions in v1, artifact-record and flat
paired-CMH run-summary v2, module-neutral run-summary plus frozen historical
receipt v3, flat paired-CMH report-receipt v4, and explicit-module
report-receipt v5. Historical versions are validated exactly; they are not
aliases or migration routes. Each registered `$id` remains one packaged file,
with local `$defs` where useful; splitting one is a versioned contract change,
not documentation cleanup.
