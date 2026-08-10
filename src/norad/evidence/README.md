# Evidence owners

This directory contains implemented owners that collect, reconcile, or package
evidence. It does not own computational transformations, scientific analysis,
report projections, or neutral contracts.

| Owner | Role |
| --- | --- |
| [`collect_canonical_BAM_QC_evidence`](canonical_bam_qc/README.md) | Numbered evidence operation `02b`; collects and validates canonical-BAM QC evidence. |
| [`collect_RSeQC_paired_orientation_evidence`](rseqc_orientation/README.md) | Numbered evidence operation `03`; collects paired-orientation evidence without selecting a biological strandedness policy. |
| [`assemble_scientific_review_evidence_package`](assemble_scientific_review_evidence_package/README.md) | Numbered evidence operation `09c`; validates and packages declared review evidence without granting scientific approval. |
| [`reference_provenance`](reference_provenance/README.md) | Reconciles one explicitly declared reference bundle without repair. |
| [`runtime_preflight`](runtime_preflight/README.md) | Records declared runtime-availability probes and owns the separate manual cluster module/tool smoke probe; neither installs software or executes the workflow. |
| [`storage_inventory`](storage_inventory/README.md) | Measures declared storage roots and records retention-policy state without acting on it. |

Each child owns its inputs, outputs, publication/recovery behavior, direct
tests, and evidence boundary. The three numbered operations participate in the
canonical graph in [`STAGE_MAP.md`](../contracts/STAGE_MAP.md); the operational
evidence tools are cross-cutting checks, not additional stages.

Steps `02b` and `03` keep their shell producers and schedulers as
repository-path interfaces while exposing their private validators as
`python -I -m norad validate canonical-bam-qc` and
`python -I -m norad validate rseqc-orientation`, respectively.

Use the [`RUNBOOK`](../../../docs/operations/RUNBOOK.md) for supported commands,
[`TROUBLESHOOTING`](../../../docs/operations/TROUBLESHOOTING.md) for failure and
recovery routes, and
[`HANDOFF.md`](../../../docs/operations/HANDOFF.md) for current evidence state.
Ownership and system boundaries live in
[`ARCHITECTURE.md`](../../../docs/architecture/ARCHITECTURE.md) and the
[`functional-owner inventory`](../../../docs/architecture/FUNCTIONAL_OWNER_INVENTORY.md).

Publication or downstream consumption never promotes evidence by itself;
promotion requires an explicit authorized owner contract or policy.
Availability is not workflow execution, local characterization is not cluster
or production validation, package assembly is not scientific approval, and
scientific review is not biological readiness.
