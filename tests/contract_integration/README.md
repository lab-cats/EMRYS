# Contract-integration tests

These tests compare multiple owners against expectations stored independently
of production constants and serializers:

- [Contract goldens](independent_contract_goldens/README.md): literal schemas,
  headers, bytes, and computational examples.
- [Validation rosters](validation_rosters/README.md): ordered check IDs for
  every current validator.

The [test baseline](../../docs/design/TEST_BASELINE.md) defines which contract
risks these checks must cover.
