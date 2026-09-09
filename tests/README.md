# Tests

Tests mirror product owners and check public behavior, data contracts, failures,
and recovery. Each source owner's contract defines the behavior under test.
The [test baseline](../docs/design/TEST_BASELINE.md) defines repository test
policy; [development validation](../docs/operations/ENGINEERING_CONVENTIONS.md#development-validation)
explains how to run checks.
Files directly in this directory cover CLI, packaging, scheduler, and policy
behavior. [`tools/`](tools/README.md) contains test runners and checking tools.

## Fixtures and independent expectations

Statistical oracles, literal validation rosters, and
[contract goldens](contract_integration/independent_contract_goldens/README.md)
must calculate or store their expectations independently of the production code
under test. Tracked fixtures are reviewed inputs: do not regenerate them to
make a failure pass, or update coverage baselines to conceal lost protection.
The public-Make fixture has its own
[normalization rules](fixtures/public_cli_contracts/README.md).

## Evidence limits

These limits apply throughout the test tree. Fixtures, mocked tools, and injected
failures establish behavior for their stated inputs. They do not prove real-tool
execution, scheduler or institutional-cluster operation, production readiness,
scientific review, or biological validity. Schema validity, file presence, and
rendered reports do not establish those claims either.

Real-runtime evidence requires a test that actually ran the named tool. A skipped
guarded R test supplies no real-R evidence. Local execution, hosted CI, Slurm,
and institutional-site checks are separate claims and must name their actual
scope. Individual suites document narrower scientific or recovery limits beside
their fixtures; none of these tests turns candidate review or adjudication into
a pipeline completion state.
