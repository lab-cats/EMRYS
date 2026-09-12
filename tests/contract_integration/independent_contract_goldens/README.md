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

The direct-template migration compared both complete and unavailable scientific
and evidence views against the previous renderer. HTML elements, attributes,
visible text, and embedded figure bytes matched; only insignificant whitespace
changed. The reviewed HTML digests reflect that formatting change. Scientific,
schema, header, and receipt-serialization oracles are otherwise unchanged.

The installed-runtime migration adds fixed synthetic package identities to the
current manifest and report-receipt schema fixtures. The existing minimal receipt
serialization oracle does not validate provenance and remains unchanged.

CS-11 preserves the scientific HTML bytes. The reviewed evidence-view difference
updates the manifest version, replaces the repeated implementation-status column
with original Run/Attempt references, and explains their scientific provenance.
The remaining scientific values, figures, statuses and limitations are unchanged.

The artifact-field retirement narrows entries to v3 and manifests to v6. Schema
and TSV header oracles remove only the retired attempt/proof-status fields.
Both previous HTML digests were reproduced before comparing the new views.
Scientific HTML changes only the Operations link target; its remaining bytes
match exactly. The evidence view removes synthetic proof labels and empty
history/tool tables, moves the unchanged original Run/Attempt references into
Operations, and retains source, QC, warning, limitation and publisher details.
The literal receipt serialization oracle remains unchanged.

The unread-summary-copy retirement moves manifests and report receipts to v7.
The previous scientific and evidence HTML digests were reproduced from commit
`c7561b3e` before comparison. Scientific HTML remains byte-identical; the evidence
fixture changes only its displayed manifest version from 6.0.0 to 7.0.0. Both
views read metrics from their original artifact entries. No figure, QC row,
scientific value or provenance reference was removed. Receipt serialization
remains an independent byte oracle and is unchanged.
