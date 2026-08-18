# Documentation history

This tree is reserved for frozen, dated evidence views whose durable value is
not already carried by current subject owners and Git history. Historical
records never own current checkout state, roadmap order, executable commands,
contracts, or evidence promotion.

## Current index

No historical child record is currently indexed. Testing transcripts, obsolete
matrices, superseded baselines, and completed gate narratives remain available
through Git history rather than the live documentation tree.

Create a topic child only when a dated record has repository-backed provenance,
unique ongoing value, and no adequate current subject owner or Git record.

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
