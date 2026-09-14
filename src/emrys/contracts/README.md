# Shared data contracts

These packages define the data exchanged between workflow owners:

- [STAGE_MAP](STAGE_MAP.md): producer identities and artifact dependencies.
- [SOURCE_TOPOLOGY](SOURCE_TOPOLOGY.md): permitted imports and shared code.
- [Artifacts](artifacts/README.md): artifact records, summaries, receipts, and validation.
- [Orchestration](orchestration/README.md): Project, Run, Attempt, task, and reporting records.
- [Scientific evidence](scientific_evidence/README.md): shared scientific tables.
- [Schemas](schemas/README.md): packaged, versioned JSON Schema files.

Producers own computation and publication; these contracts define and validate
the records they exchange.
