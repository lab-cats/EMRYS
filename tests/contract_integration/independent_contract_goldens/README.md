# Independent contract goldens

These literal fixtures define selected schemas, headers, canonical bytes, TSV
serialization, report-receipt projection, and rendered-report digests without
importing production constants or serializers to construct expected values.
`report_html.sha256` keeps separate scientific and evidence-view digests.

Changes require review of the public contract being changed. These synthetic
fixtures characterize serialization and computation only; they are not runtime
or biological evidence.
