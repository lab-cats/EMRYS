# Documentation history

This tree indexes frozen, dated evidence views. Historical records preserve
what was observed, attempted, rejected, or concluded at a known point; they do
not own current checkout state, roadmap order, executable commands, contracts,
or evidence promotion.

## Topics

- [Audits](audits/) — dated repository audits, findings, rejected approaches,
  limitations, and recheck evidence.
- [Operations](operations/) — dated delivery, branch-lineage, concurrency, and
  takeover records that no longer belong in live state.
- [Testing](testing/) — dated validation runs, baselines, risks, and gate
  provenance.

The topic name `demos/` is reserved for separately owned history work. It is
not an evidence route until an indexed child exists.

## Record rules

- Name a record `YYYY-MM-DD-<topic>.md`, using the date established by its
  source evidence rather than filesystem modification time.
- State the originating document and immutable source commit near the top of
  every record. Retain any more specific run date, command, commit, or artifact
  provenance carried by the source.
- Freeze a record after migration. A later result gets a new dated record; it
  does not rewrite the earlier observation into current truth.
- Keep each record under one topic and link it from that topic's index. Other
  documents link the record instead of copying its historical narrative.
- Route current state and evidence to
  [`HANDOFF.md`](../operations/HANDOFF.md), roadmap and lineage to
  [`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md), exact commands to
  [`RUNBOOK.md`](../operations/RUNBOOK.md), and functional meaning to the
  applicable colocated contract.
