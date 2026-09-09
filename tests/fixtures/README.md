# Shared test fixtures

This directory holds tracked inputs used by more than one test owner. Each
fixture family explains its contents and interpretation, including the
[public CLI fixtures](public_cli_contracts/README.md).

Keep domain-specific fixtures beside the tests that interpret them. Sharing a
fixture does not make it an independent expected result; follow the
[fixture rules](../README.md#fixtures-and-independent-expectations).
