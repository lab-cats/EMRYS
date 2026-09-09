# EMRYS source domains

Shared data rules live in [`contracts/`](contracts/README.md), and shared
implementation in [`libraries/`](libraries/README.md). Work is divided into
[`stages/`](stages/README.md), [`analyses/`](analyses/README.md),
[`evidence/`](evidence/README.md), [`ingestion/`](ingestion/README.md), and
[`reporting/`](reporting/README.md). [`orchestration/`](orchestration/README.md)
coordinates the application using scheduling files in the root `workflow/`.

Each owner's documentation defines its commands and behavior.
[SOURCE_TOPOLOGY](contracts/SOURCE_TOPOLOGY.md) defines permitted imports.
