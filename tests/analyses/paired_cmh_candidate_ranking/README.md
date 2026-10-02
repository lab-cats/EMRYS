# Paired-CMH analysis tests

These tests cover direct R outputs and planned arguments, requested-policy
validation, an oracle calculated from counts, and a committed guarded real-R
corpus. Shared runner tests cover publication and recovery. The
[analysis contract](../../../src/emrys/analyses/paired_cmh_candidate_ranking/CONTRACT.md)
defines the method, inputs, and outputs; its
[README](../../../src/emrys/analyses/paired_cmh_candidate_ranking/README.md)
explains the supported commands.

Validator cases use `python -I -m emrys validate paired-cmh-candidate-ranking`;
`validator.py` is private implementation. `step_09_cmh_oracle.py` must remain
independent of production statistical code. A skipped guarded-R case supplies
no real-R evidence, as explained in the [test evidence limits](../../README.md#evidence-limits).

## SCI-ORACLE-01 coverage review

The existing count-derived Python oracle and literal TSV corpus already cover
paired multi-stratum CMH, continuity correction, zero/missing/low counts,
degeneracy, infinite odds, rounding and one global BH family. Python tests reject
production imports and coordinated false statistics/BH values; the guarded R
fixture compares the committed corpus to actual R calculations. Existing full
producer fixtures separately protect status precedence, both effect directions,
background statuses, strict equality thresholds, empty input, explicit pairing
refusal, sample columns and deterministic output. No second statistical oracle
is needed.

The added valid-permutation fixture changes sample order independently within
conditions and reverses candidate order. Every carried value, statistic and
status must agree after identity alignment, while native sample columns and the
significant subset retain the new input order. In particular, a weaker candidate
must precede a stronger one when that is the input order: the native significant
TSV is an ordered subset, not a p-value sort. This closes a positive pairing/order
coverage gap without replacing the existing deterministic-repeat test.

Corpus comparisons retain their existing tolerances: Python `rel_tol=1e-12`,
`abs_tol=1e-15`; R absolute `1e-12` for statistic/odds and `1e-15` for p/BH values.
Full-producer literal cases retain their individual declared tolerances. The
permutation comparison is exact after matching candidate/sample identities.
These are computational checks of the declared contract, not a scientific
endorsement of CMH or the provisional orientation policy. Reviewers must record
that authority and characterize disagreements before any semantic change.
