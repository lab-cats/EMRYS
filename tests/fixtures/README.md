# Shared test fixtures

This directory owns tracked inputs shared across test owners. Fixture families
with a detailed contract keep their own README, including
[`public_cli_contracts/`](public_cli_contracts/README.md).

Domain-specific fixtures remain beside the tests that interpret them rather
than moving here solely for reuse. Synthetic or characterized fixture results
remain local test evidence and do not promote runtime or scientific state.
