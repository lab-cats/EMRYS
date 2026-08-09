# Project handoff

This file contains live takeover facts that are not safely reconstructed from
Git. Resolve branch, commit, upstream relation, and worktree contents directly
from Git. Use [`PIPELINE_PLAN.md`](../design/PIPELINE_PLAN.md) for pipeline
status, [`RUNBOOK.md`](RUNBOOK.md) for commands, and
[`docs/history`](../history/) for frozen delivery records.

No successor package is selected.

## Evidence boundary

| Surface | Current evidence ceiling |
| --- | --- |
| Physical ownership | Pipeline stages, neutral contracts/libraries, reporting, and evidence helpers occupy their allowed homes. This is local/static topology evidence, not new runtime or cluster proof. |
| Steps `00a`–`06` | Earlier production executions remain cluster-proven; that evidence predates physical relocation. |
| Step `07` | Locally fixture/mock-bcftools tested; no real-bcftools or cluster proof. |
| Steps `08`–`09` | Locally shell/fake-R and guarded-real-R tested; no production or cluster proof. |
| Step `09c` and reporting | Synthetic-fixture and local-render tested; no production evidence package, completed scientific review, or production report. |
| Operational helpers | Runtime, reference, storage, and structured validators have local fixture evidence; no CSU batch runtime report, production reference/storage report, or approved retention policy. |

A transaction proves only reconciliation of its declared inputs and outputs.
It does not prove every source passed or promote runtime, cluster, scientific,
or biological state. Current test policy belongs to
[`TEST_BASELINE.md`](../design/TEST_BASELINE.md).

The reporting renderer now keeps its public shell and Python paths stable over
a private, acyclic `_run_report` package. Models, input/context validation,
HTML/PDF/receipt projection, pinned runtime execution, transaction primitives,
and HTML versus receipt-last bundle publication have separate owners; no
private module exceeds 445 lines. This is maintainability and local test
evidence only and does not change the reporting evidence ceiling above.

Canonical run-summary assembly likewise keeps its public command and direct
import bindings stable over bounded private owners for document assembly,
receipt-last publication, transaction input, validation, projection, and
scientific-review models, I/O, package reconstruction, and evidence
normalization. The public coordinator is 381 lines, the science compatibility
owner is 405 lines, and no new private module exceeds 442 lines. This is also
maintainability and local test evidence only.

Artifact indexing keeps its public command and fault-injection bindings over a
private 302-line publication coordinator. Registry, inspection,
reconciliation, record/context assembly, validation, and publication remain
separate reporting-local owners; the public facade is 279 lines. This does not
change schemas, discovery policy, evidence states, serialized bytes, or the
receipt-last transaction boundary.

Artifact-contract Python mechanics are separated behind the unchanged neutral
facade: definitions/error identity, closed-registry schema I/O,
path/run/attempt identity, computational evidence, run-summary reduction, and
record semantics have distinct private owners. The five schema resources are
unchanged and remain one file per registered `$id`, using local `$defs`; this
is maintainability evidence, not a schema version or evidence promotion.

The neutral Step `09` scientific-evidence contract keeps its public module,
headers, signatures, and shared Step `08` identities over private definition,
support, table-reconciliation, and cross-table-semantic owners. The public
module is 47 lines and no private owner exceeds 373 lines. The Step `09`
shell/R CMH method and independent oracle were not changed; this adds no
runtime, scientific-review, or biological evidence.

Step `07` shell keeps its exact bcftools pipelines, input snapshots, locks,
signals, rollback, and receipt-last publication in a 468-line public producer.
Owner-local modules contain the byte-identical partition/FAI/selector and
generated VCF/receipt validation functions and do not exceed 211 lines. The
scheduler preserves copied-producer execution by exporting the packaged helper
location before changing directories. This is maintainability and mock-
bcftools evidence only, not real-bcftools or cluster proof.

Step `06` shell keeps its exact samtools commands and ordered execution plus
counts-last publication in a 477-line public producer. Owner-local 120- and
84-line modules contain byte-identical final-set/rollback/cleanup/stale-path
and generated-output/counts-contract functions. The scheduler exports their
packaged location before changing directories. This adds no new runtime,
cluster, mechanical-orientation, or biological evidence.

Step `08` shell keeps R resolution/command construction, admitted-input
snapshots, locks, signals, rollback, and receipt-last publication in a 461-line
public transaction owner. Owner-local 144- and 198-line modules contain the
byte-identical Step `07` admission/stability and generated-table reconciliation
functions; all three shell files total 803 lines. The scheduler preserves
copied-producer execution by exporting the packaged helper location. This does
not add production Step `07` inputs, an approved R runtime, or cluster proof.

Step `08` R now retains a 401-line public coordinator over input-contract,
annotation, Step `07` receipt, and VCF/candidate modules no larger than 570
lines. All 23 pre-existing top-level function bodies are parse-identical to the
committed monolith. The complete owner remains about 1,900 lines; decomposition
improves responsibility boundaries without disguising total complexity or
promoting the 176-line external REMORA reference into a parity oracle.

Step `09` R is already divided into a 179-line coordinator plus common,
validation, evaluation, and output modules no larger than 279 lines. The five
files total 1,101 lines. Its audit found no dead top-level function or safe
owner-local collapse; independent validation and CMH-oracle boundaries remain
separate.

Runtime preflight keeps its executable, CLI, TSV bytes, probe behavior, and
publication/fault-injection bindings stable over private model, profile,
probe, and result-contract owners. The public compatibility/publication owner
is 251 lines and no private module exceeds 167 lines. Known characterized
publication gaps remain unchanged; this is maintainability and local test
evidence, not CSU batch runtime or cluster proof.

Reference provenance keeps its executable, public names, CLI behavior, TSV
bytes/order, contig reconciliation, stability recheck, and publication/fault-
injection bindings over private contract, inventory, contig, and rendering
owners. The public CLI/publication facade is 230 lines, no private module
exceeds 135 lines, and all nine extracted function bodies are AST-identical to
the committed monolith. The five implementation files total 693 lines; this is
maintainability and local fixture evidence, not production reference proof.

Step `09c` intake keeps its sibling-import surface over distinct data-model,
support, review-plan, and evidence-manifest owners. The compatibility facade is
42 lines and the largest extracted owner is 228 lines. Review policy, manifest
normalization/order, hashes, evidence states, and public Step `09c` publication
remain unchanged; this adds no completed review or production evidence.

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
  states. Passing characterization does not approve them.

Other live defects and recheck routes are indexed in
[`REFACTOR_AUDIT.md`](../design/REFACTOR_AUDIT.md).

## Immediate resume point

Any new package requires fresh user direction. Dependency mutation,
destructive cleanup, runtime or cluster execution, scientific review, evidence
promotion, and biological interpretation remain separate scopes.
