# Validation-roster expectations

This directory owns independent ordered expectations for the check IDs emitted
by every live validation producer. `validation_roster_expectations.py` contains
the literal rosters; `test_validation_check_rosters.py` protects inventory,
membership, ordering, and the shared report validator's characterized
reordering behavior.

Do not derive these expectations from producer constants. The canonical risk
route is the [test baseline](../../../docs/design/TEST_BASELINE.md); individual
validators retain ownership of each check's semantics. Roster agreement is
local contract evidence, not proof that a check is scientifically sufficient
or that a real workflow run passed.
