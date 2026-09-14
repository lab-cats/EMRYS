# Artifact-contract tests

These cases check the public API and shared function identities, grouped command,
private validator, schema registry, record semantics, inventory compatibility,
and CLI failures. The [artifact owner](../../../src/emrys/contracts/artifacts/README.md)
defines the supported contract and command.

[Fixtures](fixtures/README.md) are reviewed contract inputs. Do not regenerate
them or change schema bytes merely to make a failing test pass.
