# Architecture rationale

## Protect behavior before structural change

Classify affected behavior as preserved contract, characterized defect,
undefined and requiring a decision, or environment-deferred. Protect preserved
behavior independently before mutation. Structural cleanup does not silently
correct a defect or authorize a public/scientific interface change.

## Organize by functional owner

Keep each stage, analysis, evidence operation, reporting component, or neutral
domain with its implementation, native assets, commands, contract, diagnostics,
recovery behavior, and mirrored tests. Public starter inputs and repository
development controls remain outside runtime domains when they are not
implementation-native.

A source move goes directly to its final current owner. Compatibility paths are
exceptional, bounded, parity-protected, and removable. Placement creates no
installed package, new runtime behavior, or evidence.

## Use semantic identities and artifact edges

Each functional owner has a semantic slug and stable versioned machine key;
numeric identifiers remain historical aliases. Required produced artifacts and
declared barriers create DAG edges. Filenames, narrative order, shared
directories, validators, or one wrapper's materialization behavior do not.

Exact identities and edges live in
[`STAGE_MAP.md`](../../../src/emrys/contracts/STAGE_MAP.md). Current source and
dependency rules live in
[`SOURCE_TOPOLOGY.md`](../../../src/emrys/contracts/SOURCE_TOPOLOGY.md).

## Share only proven equivalence

Keep the first use owner-local. Compare behavior, failure, recovery,
determinism, and scientific meaning before extraction. Promote only sufficiently
complex or safety-relevant equivalent reuse, with independent API and consumer
tests, into the narrowest neutral owner. Never create a generic utility bucket,
force cross-language DRY, or let neutral code depend on a functional owner.

## Preserve inspectable boundaries

Cross-owner data passes through explicit contracts; owners do not import peer
private implementation. Reporting remains downstream of computation and
evidence. Dependency restoration, Git/documentation tooling, quality gates,
and project environments remain repository controls rather than scientific
workflow domains.

## Select a local-first orchestration boundary

The first workflow control plane uses Snakemake's local executor because the
existing semantic owners already expose the scientific operations and artifact
edges that a general-purpose workflow engine should schedule. EMRYS therefore
does not build a second scheduler, stage registry, scientific implementation,
or recovery system. One fixed profile is easier to inspect and prove than a
generic extension surface before a second real workflow exists.

Human YAML remains concise while ordered scientific records stay in TSV. A
normalizer resolves and hashes explicit inputs into canonical JSON so formatting
and caller working directory cannot determine run identity. The complete
execution contract remains distinct from the existing reporting run contract:
reporting is a downstream projection and cannot silently become lifecycle
authority.

Owner validation is evidence production rather than a process-level Boolean;
several validators intentionally publish `status=fail` with exit zero. Each
workflow task must consequently parse the persisted report and publish its own
content-bound verified record only after every row passes. This record is a
local scheduling/reuse boundary, not a scientific or cluster promotion.

Local execution precedes site execution so workflow semantics can be proven
without mixing CSU modules, storage, accounting, or scheduler policy into the
scientific graph. SLURM and the possible Linux VM remain deferred rather than
rejected. The decision-complete lifecycle and resume rules are in
[`ORCHESTRATION_CONTRACT.md`](../ORCHESTRATION_CONTRACT.md); accepted remaining
work is tracked in the [findings matrix](../../tasks/backlog_matrix.md).

The public control plane remains thin: it reruns read-only admission, prints an
exact no-write plan by default, materializes only the fixed profile under the
aggregate run lock, and delegates scientific work to public owners. It exposes
no raw Snakemake flags or automatic owner recovery.

Logging, report profiles, analysis modules, public acquisition, standalone
workflow packaging,
site profiles, and optional-success policy remain designs, not current
architecture. Accepted outcomes are in the
[findings matrix](../../tasks/backlog_matrix.md); unsliced alternatives remain
in the temporary
[architecture campaign](../../tasks/architecture_campaign.md).
