# Tests

Tests mirror product owners and protect public behavior, contracts, failures,
and recovery. Exact owner semantics remain in the adjacent source
`CONTRACT.md`; cross-cutting policy and supported commands remain in the
[test baseline](../docs/design/TEST_BASELINE.md) and
[runbook](../docs/operations/RUNBOOK.md).

Keep independent expectations independent: statistical oracles, literal
validation rosters, and
[contract goldens](contract_integration/independent_contract_goldens/README.md)
must not derive expected values from the production implementation under test.
Tracked fixtures are reviewed literal inputs; do not regenerate them merely to
make a failure pass. The public-Make fixture has its own
[normalization contract](fixtures/public_cli_contracts/README.md). A skipped
guarded real-runtime test supplies no real-runtime evidence, and a coverage
baseline must never be updated to conceal lost protection.

`tools/` contains test-only validation, sharding, dependency, coverage, and
synthetic-E2E support. The files directly under this directory protect
cross-cutting CLI, packaging, scheduler, and policy behavior. Passing tests are
local engineering evidence unless a named higher evidence lane says otherwise;
they do not establish production, cluster, scientific-review, or biological
validity.
