# Independent contract goldens

These tiny synthetic fixtures spell expected public contracts independently of
the production modules. The tests load production constants and serializers
only as the values under test; no fixture builder imports those constants or
generates these expected files.

- `schema_contracts.json` names a bounded set of critical public-schema paths
  and their literal expected values.
- `headers.json` records representative public artifact, summary, report, and
  scientific-review headers in exact order.
- `canonical_object.json` is both a small literal input object and its expected
  canonical JSON byte representation.
- `small_table.tsv` is a literal UTF-8 TSV oracle for the shared Step 09c table
  writer.
- `report_receipt_input.json` and `report_receipt.tsv` pair one minimal literal
  report-receipt input with its exact projected TSV bytes.
- `scientific_state_contracts.json` records literal status vocabularies and
  evidence aggregation cases.

The identifiers, paths, hashes, and content are synthetic. These fixtures
characterize serialization and evidence-state behavior; they do not establish
cluster execution, scientific validation, or biological interpretation.
