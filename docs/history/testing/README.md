# Testing history

This mutable index links immutable dated testing records. A historical testing
record may preserve a measured run, baseline, risk assessment, limitation, and
gate provenance. Current validation boundaries and active baseline routes
remain in [`TEST_BASELINE.md`](../../design/TEST_BASELINE.md).

## Records

| Frozen date | Record | Provenance and boundary |
| --- | --- | --- |
| 2026-08-13 | [Campaign B assembled local gate](2026-08-13-campaign-b-assembled-local-gate.md) | Exact revision `844920c`; static, wheel, shell/SLURM-contract, guarded-R, and Python-coverage lanes passed against the ten-owner Campaign B baseline. Local engineering evidence only. |
| 2026-08-13 | [B6 fresh-clone local-pilot proof](2026-08-13-b6-fresh-clone-local-pilot.md) | Exact revision `cbea15b`, locked setup, fixture hashes, clean completion, controlled failure, byte-preserving resume, reporting outputs, and no-science evidence ceiling. |
| 2026-08-01 | [Test baseline and public-contract traceability](2026-08-01-test-baseline-and-public-contract-traceability.md) | Initial baseline `4fc32e0` and affirmative TEST-01Z snapshot `dc6f444` on 2026-07-31; exact final source `eb65c95` on 2026-08-01. Dated counts, matrices, LOG-01 inventory, gates, and decisions only; current policy and risk routes remain in `TEST_BASELINE.md`. |
