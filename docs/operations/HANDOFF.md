# Project handoff

This file owns current evidence ceilings, blockers, and live takeover facts
that are not safely reconstructed from Git. Resolve branch, commit, upstream
relation, and worktree contents directly from Git. Use
[`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md) for open package families and
acceptance, [`RUNBOOK.md`](RUNBOOK.md) for commands, and
[`docs/history`](../history/) for frozen delivery records.

Campaign B owner hardening (`B1a` through `B1c`) and B2 intake/contracts are
implemented. Owners expose explicit local, fail-closed workflow boundaries;
the repository now has a locked workflow dependency group, closed machine
schemas, read-only normalization/reporting projection, and a semantic all-pass
command. No fixed profile, Snakemake rule, record publication, or lifecycle
adapter is implemented yet.

## Evidence boundary

| Surface | Current evidence ceiling |
| --- | --- |
| Local-pilot orchestration | B0 defines the source-checkout-bound lifecycle; B1 adds focused fake-tool owner boundaries; B2 adds schema-tested request/profile/execution/attempt/task records, deterministic read-only normalization/reporting projection, and semantic all-pass checking. No fixed profile, workflow rule, materialized state, public lifecycle CLI, synthetic science dataset, or real science-tool run exists. |
| Physical ownership | Pipeline stages, neutral contracts/libraries, reporting, and evidence helpers occupy their allowed homes. This is local/static topology evidence, not new runtime or cluster proof. |
| Steps `00a`–`06` | B1 owner boundaries are locally fake-tool/fixture tested; earlier production executions remain cluster-proven but predate physical relocation. No current real-tool local proof. |
| Step `07` | B1 no-clobber and rollback boundaries are locally mock-bcftools tested; no real-bcftools or current cluster proof. |
| Steps `08`–`09` | B1 no-clobber/recovery boundaries are locally shell/fake-R tested; prior guarded-real-R tests remain separate. No production or current cluster proof. |
| Step `09c` and reporting | Synthetic-fixture and local-render tested; no production evidence package, completed scientific review, or production report. |
| Operational helpers | Runtime, reference, storage, and structured validators have local fixture evidence; no CSU batch runtime report, production reference/storage report, or approved retention policy. |

A transaction proves only reconciliation of its declared inputs and outputs.
It does not prove every source passed or promote runtime, cluster, scientific,
or biological state. Current test policy belongs to
[`TEST_BASELINE.md`](../design/TEST_BASELINE.md).

Completed maintainability decompositions span reporting, artifact and summary
contracts, the neutral Step `08`/`09` contracts, Step `08`/`09` R owners,
operational evidence tools, and Step `09c` review helpers. Current system shape
and exact public routes belong to the [architecture index](../architecture/README.md)
and [functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md);
Git and dated history preserve delivery detail and extraction measurements.

Those changes preserved public paths, commands, direct-import bindings,
schemas, serialized bytes, explicit inputs, transaction/recovery behavior,
fault-injection boundaries, scientific methods, independent-oracle boundaries,
and evidence semantics. The external REMORA reference is not a parity oracle.
Known publication defects remain current blockers below. Focused storage and
public-CLI tests passed, but that storage slice did not rerun the full coverage
gate. These decompositions establish local maintainability evidence only; they
add no runtime, cluster, scientific-review, or biological proof.

## Cohort and preserved scientific evidence

The operational cohort has three explicit paired strata:

| Replicate | EV | PUM1 |
| --- | --- | --- |
| `2` | `ABE_EV_2` | `ABE_PUM1_2` |
| `3` | `ABE_EV_3` | `ABE_PUM1_3` |
| `4` | `ABE_EV4` | `ABE_PUM1_4` |

`ABE_EV4` intentionally lacks an underscore. Pairing comes from manifest
metadata, never sample-name inference.

Step `03` classified every library as reverse-stranded / first-strand-style:

| Sample | Failed | `1++,1--,2+-,2-+` | `1+-,1-+,2++,2--` |
| --- | ---: | ---: | ---: |
| `ABE_EV_2` | 0.0828 | 0.0432 | 0.8740 |
| `ABE_EV_3` | 0.0964 | 0.0420 | 0.8617 |
| `ABE_EV4` | 0.0908 | 0.0433 | 0.8658 |
| `ABE_PUM1_2` | 0.1063 | 0.0374 | 0.8562 |
| `ABE_PUM1_3` | 0.0955 | 0.0407 | 0.8639 |
| `ABE_PUM1_4` | 0.0926 | 0.0402 | 0.8672 |

The hardened `ABE_EV_2` rerun matched its earlier report. `ABE_EV_2`
remains a mapping outlier, not an established pipeline failure.
`FWD_like` and `REV_like` are mechanical groupings;
`legacy_provisional_v1` is not a validated biological strand model.

`science_review_complete_exploratory` remains provisional, and
`biological_interpretation_ready` remains reserved. No validated editing
site or causal biological conclusion exists.

## Local recovery constraint

A sibling-worktree `renv` activation once created a malformed empty
platform-qualified library path. It remains absent and must not be fabricated
or automatically restored. Guarded checks bind `RENV_PATHS_LIBRARY` to the
project-library root.

The installed project library remains at `renv` `1.2.3` while current
metadata advertises `1.2.4`. Dependency maintenance is a separate package;
do not mutate the environment incidentally.

## Current blockers

- The production `samples.tsv` is not in this checkout; its cluster identity,
  replicate values, persistence, and hash require inspection.
- Step `07` lacks real-bcftools and cluster evidence. Steps `08`, `09`,
  and `09c` lack production/cluster evidence and completed scientific review.
- CSU batch-visible R/package availability, storage capacity and retention
  policy, and the exact Novogene annotation release remain unresolved.
- The Step `09` production validator does not independently recompute CMH
  statistics from DP/AD counts. The independent test oracle characterizes a
  possible correction but did not change production validation.
- Publication characterization retains known same-size rewrite,
  late-foreign-final, incomplete-rollback, descriptor, and stale-lock failure
  states on legacy replacement routes. The local profile will use the B1
  fail-closed no-replace/reuse paths and must still block on any ambiguous
  residue.

Cross-cutting contract risks and recheck routes are indexed in
[`TEST_BASELINE.md`](../design/TEST_BASELINE.md); exact defects remain with the
applicable owner `README.md` or `CONTRACT.md`.

## Immediate resume point

Implement B3 from the accepted orchestration contract: materialize the exact
fixed local-CMH profile, prove its projection against `STAGE_MAP.md`, and use
the pinned Snakemake CLI for dry-run plus reference, one-sample, and cohort
test-double slices. Do not add the public lifecycle adapter or claim real
science-tool execution. Destructive cleanup, real-runtime or cluster execution,
scientific review, evidence promotion, and biological interpretation remain
separate scopes.
