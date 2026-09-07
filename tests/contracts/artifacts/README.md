# Artifact-contract tests

This directory directly protects the curated computational artifact-contract API,
its shared import identity, the grouped validation route and private
coordinator, schema registry, semantic validators, inventory compatibility,
and CLI failure behavior. The detailed contract and supported validation command
remain with the [artifact-contract owner](../../../src/emrys/contracts/artifacts/README.md).

[`fixtures/`](fixtures/) contains the tracked valid example documents used by
this suite. Fixture and schema bytes are contract inputs: do not regenerate or
rewrite them merely to make a failing test pass. These synthetic contracts do
not establish that a real artifact was produced or biologically validated.
