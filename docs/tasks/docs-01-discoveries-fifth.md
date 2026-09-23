# DOCS-01 discovery notes, fifth file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F130–F133. F130–F131 use local audit head `3ebfb2bf`, read on 2026-09-23;
F132–F133 use local head `935adf06` on the same date.
F130 was dismissed as a duplicate on recheck at local head `935adf06`.
Source and direct tests were read, not executed. These are documentation
observations, not runtime results, accepted changes, or permission to alter
retained evidence.

## Discovery notes

### F130 — Repeated test-scope paragraph across eight owner guides

**Dismissed duplicate.** [F28](docs-01-discoveries.md#f28-repeated-owner-boilerplate)
already records the identical five-line paragraph in the same six stage and
two evidence test guides (40 physical lines), plus six production README copies.
F130 adds no independent finding or saving estimate. Its number remains to
trace this correction; no documentation deletion follows.

### F131 — Receipt validation scope in the glossary

The [glossary](../reference/GLOSSARY.md) line 69 defines a receipt as published
after all other transaction members “validate” and says its presence marks
transaction completion. The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1117–1126 distinguishes staged checks from independent validation:
Steps 08/09 validate before publication, while other scientific owners publish
native finals, including any receipt last, before the independent validator
and semantic all-pass. The [Step 07 owner contract](../../src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md)
lines 57–64 makes the second order explicit: its worker checks staged VCFs,
the runner publishes VCFs and receipt, and the independent validator checks
the visible set. A [direct task test](../../tests/orchestration/run_coordinator/test_task.py)
lines 759–776 shows a failed validation row prevents the verified-task marker.
The glossary's unqualified “validate” and “completion” blur native transaction
completion with verified task completion. Staged checks and receipt-last order
remain real; a native receipt alone is not verified-task proof. No runtime or
reporting defect follows from this glossary wording.

### F132 — Benchmark timing scope in the Runbook

The [Runbook](../operations/RUNBOOK.md) lines 730–733 says the resource helper
measures explicitly listed setup, production, and validation commands, then
mentions wall time and peak child memory without assigning their scope. The
[helper](../../scripts/benchmark_stage_resources.py) lines 427–466 executes
setup and validation with `_run`, but times only the producer with `_run_timed`.
Its result fields at lines 41–57 and 484–499 retain setup and validator exit
codes, while elapsed, CPU, RSS, and block counts are producer-specific. The
[optimization campaign](optimization_campaign.md#measurement-and-adoption)
lines 364–374 explicitly says validator time is excluded and a producer-only
benchmark does not establish complete public-command latency. The Runbook
wording can give an operator a broader measurement expectation. Setup and
validation still execute and gate trial success; this is a documentation-scope
observation, distinct from F62's value-label issue. No benchmark was run and
no performance result follows.

### F133 — Fourteen workflow owners labeled scientific

The [architecture guide](../architecture/ARCHITECTURE.md) line 54 calls all
fourteen owners in the built-in path “scientific.” Its responsibility table at
lines 41–43 separates scientific stages/analyses from operational evidence,
and its phase table at lines 64–68 calls alignment evidence non-gating. The
[stage map](../../src/emrys/contracts/STAGE_MAP.md) lines 19–34 lists fourteen
identities: ten stages, two analyses, and two evidence collectors (canonical
BAM QC and RSeQC orientation). The total is accurate, but the adjective blurs
the guide's own evidence boundary. This is a reader-label ambiguity only; it
does not show a graph, scheduling, or scientific-result defect.
