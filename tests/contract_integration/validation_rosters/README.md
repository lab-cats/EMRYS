# Expected validation checks

`validation_roster_expectations.py` stores the independently reviewed, ordered
check IDs for every current validation producer. `test_validation_check_rosters.py`
checks the producer inventory, membership, ordering, and the shared report
validator's known behavior when checks are reordered.

Never derive expected rosters from producer constants. Each validator defines
what its checks mean; matching the list does not show that the checks are
scientifically sufficient or that a real workflow passed. See the
[test baseline](../../../docs/design/TEST_BASELINE.md) for the covered risk.
