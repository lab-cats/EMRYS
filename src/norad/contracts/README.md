# Contract owners

This directory contains neutral identities and contracts consumed across
functional owners. It does not own stage execution, scientific algorithms,
publication policy, or operator state.

- [`STAGE_MAP.md`](STAGE_MAP.md) owns semantic workflow identities and artifact
  edges.
- [`SOURCE_TOPOLOGY.md`](SOURCE_TOPOLOGY.md) owns source domains, approved shared
  seams, and dependency direction.
- [`artifacts/`](artifacts/) owns public artifact schemas and validation.
- [`scientific_evidence/`](scientific_evidence/) owns neutral Step `08`, Step
  `09`, and review-package contracts.
- [`schemas/`](schemas/) contains the versioned schema files registered by
  their contract owners.

Contract tests live under [`tests/contracts/`](../../../tests/contracts/) and
cross-owner agreement tests under
[`tests/contract_integration/`](../../../tests/contract_integration/).
