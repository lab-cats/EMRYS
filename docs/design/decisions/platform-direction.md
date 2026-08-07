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
[`STAGE_MAP.md`](../../../src/norad/contracts/STAGE_MAP.md). Current source and
dependency rules live in
[`SOURCE_TOPOLOGY.md`](../../../src/norad/contracts/SOURCE_TOPOLOGY.md).

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

Future YAML intake, orchestration, logging, report profiles, analysis modules,
public acquisition, packaging, and optional-success policy remain designs, not
current architecture. Their concise boundary is
[`FUTURE_ARCHITECTURE.md`](../../architecture/FUTURE_ARCHITECTURE.md); unresolved
choices remain in [`QUESTIONS.md`](../QUESTIONS.md).
