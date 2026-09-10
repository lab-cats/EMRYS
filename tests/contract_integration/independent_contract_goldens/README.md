# Independent contract goldens

These literal fixtures define selected schemas, headers, canonical bytes, TSV
serialization, report-receipt projection, and rendered-report digests without
importing production constants or serializers to construct expected values.
`report_html.sha256` keeps separate scientific and evidence-view digests.

Changes require review of the public contract being changed. These synthetic
fixtures characterize serialization and computation only; they are not runtime
or biological evidence.

The current-result-contracts review preserves the scientific HTML golden byte
for byte. The evidence HTML change shows manifest schema 4, replaces the retired
artifact-receipt link with the Run-contract file, and adds the current Analysis
policy path/hash. Existing scientific values, status, limitations, and artifact
rows are unchanged. Header/schema oracles now describe the current manifest and
report receipt; literal TSV serialization checks remain independent.
