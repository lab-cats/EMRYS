# Contract-integration tests

This directory owns cross-owner checks whose expectations must remain
independent of the production constants and serializers under test.

- [`independent_contract_goldens/`](independent_contract_goldens/README.md)
  owns literal schema, header, byte, and computational-contract fixtures.
- [`validation_rosters/`](validation_rosters/README.md) owns literal ordered
  check rosters for every live validator.

The [test baseline](../../docs/design/TEST_BASELINE.md) owns the broader
contract-risk policy and evidence limits. These synthetic checks do not prove
runtime, cluster, scientific-review, or biological state.
