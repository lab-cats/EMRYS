# EMRYS source domains

The package separates neutral [`contracts/`](contracts/) and
[`libraries/`](libraries/) from functional [`stages/`](stages/),
[`analyses/`](analyses/), [`evidence/`](evidence/),
[`ingestion/`](ingestion/), [`reporting/`](reporting/), and the
[`orchestration/`](orchestration/) application owner. Static scheduling assets
remain at repository-root `workflow/`.

[`SOURCE_TOPOLOGY.md`](contracts/SOURCE_TOPOLOGY.md) is the dependency
authority. A directory is not automatically a public command or import seam;
each reviewed owner retains its contract, implementation, and direct tests.
