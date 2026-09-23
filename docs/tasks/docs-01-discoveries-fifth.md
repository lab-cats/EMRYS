# DOCS-01 discovery notes, fifth file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F130–F139. F130–F131 use local audit head `3ebfb2bf`, read on 2026-09-23;
F132–F133 use `935adf06`, and F134–F139 use `ebc0012d` on that date.
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

### F134 — CV-25 implementation account beside current log owners

The completed [CV-25 card](cluster_verification_backlog.md#cv-25-log-discovery-and-readable-output)
lines 3689–3746 spends roughly 58 lines on the Task-log, started-stream, and
Run-selected log-discovery implementation and verification sequence. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 532–555 and 663–671 owns current log-root precedence, association,
Task-stream admission, and diagnostic limits; the [Runbook](../operations/RUNBOOK.md)
lines 17–37 gives the operator's selected-Run route. The CV card mixes current
mechanics with dated test and CI genealogy. Its original E01–E06 discovery
need, explicit-identity/no-guessed-latest acceptance, hosted-only Completed
disposition, historical Attempt/start limits, and separate institutional and
retirement boundaries remain evidence. This is a placement review, not a
verified 58-line saving or permission to delete the record.

### F135 — CV-24 repeats the current watch action protocol

The [CV-24 card](cluster_verification_backlog.md#cv-24-run-center-actions)
lines 3639–3661 describes `p`/`b`/`s` handoffs, fresh planning, refusal of
noninteractive actions, and Slurm's concurrent-resume caveat. The
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 644–661 owns that exact present behavior, and the
[Runbook](../operations/RUNBOOK.md) lines 121–137 gives the operator keys and
commands. The card's selected three-action disposition, fixture/CI evidence,
new-analysis choice at lines 3663–3672, hosted-only completion, and separate
CV-16/institutional and dashboard-retirement acceptance remain distinct.
Only the repeated current-protocol prose is a compression review surface;
no safe saving is established.

### F136 — Private planning-helper narration in the coordinator contract

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 852–858 states the public planning composition, then names private
`_tasks` and `_task_commands` helpers and their caller's three local results
at 854–856. [Materialization source](../../src/emrys/orchestration/run_coordinator/materialization.py)
lines 328, 891, and 1042–1059 confirms the implementation; the
[coordinator index](../../src/emrys/orchestration/run_coordinator/README.md)
lines 29–40 already maps `materialization.py` to planning. The helper names
have no evident public or recovery role. Preserve the planning contract and
special path, command, and resource guarantees around this three-line span;
no deletion is approved or measured here.

### F137 — Reporting artifact format in the coordinator contract

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1218–1222 lists manifest fields, JSON-last order, excluded record/index
files, and HTML receipt/output facts. The [reporting owner](../../src/emrys/reporting/README.md)
lines 10–20 and 38–40 already owns these exact artifact details and its
publication section at 66–79 owns create-only and receipt-last behavior.
Keep the coordinator's two-transaction sequence and independent science and
reporting admission at 1203–1218, plus its Run-root location map at 1230–1244.
The five-line overlap is a placement candidate, not a demonstrated full
saving; caller links and recovery boundaries require review before transfer.

### F138 — Reporting fault-test detail in the production guide

The [reporting owner guide](../../src/emrys/reporting/README.md) lines 114–119
has an “Implementation and fault tests” section that repeats monkeypatch,
source-observer, and input-recheck detail in the
[reporting test guide](../../tests/reporting/README.md#fault-injection)
lines 11–24. Current source retains the observers and recheck callbacks in
`_artifact_index/models.py:102`, `_artifact_index/context.py:243–249`, and
`_run_report/publication.py:91–99`; this is a placement observation, not a
claim that the protection is obsolete. Preserve the production guarantee
that source and inputs are rechecked, plus test-specific fault coverage. The
six-line span is a review surface, not a verified net saving.

### F139 — Storage command route in the evidence index

The [evidence index](../../src/emrys/evidence/README.md) lines 16–20 points
readers to `emrys debug storage-qualification` “for storage.” The
[storage owner](../../src/emrys/evidence/storage_inventory/README.md)
lines 32–52 calls this an advanced manual check and gives head-node
`emrys doctor --repair` as the normal path; the
[Runbook](../operations/RUNBOOK.md) lines 538–575 agrees. The index may be a
command catalog, but does not distinguish routine qualification from the
manual two-phase procedure. This is a reader-route ambiguity only. Preserve
the manual command, its phase and residue cautions, and Doctor's ordinary
qualification route; no storage command was run.
