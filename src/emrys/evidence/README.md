# Evidence owners

This directory contains implemented owners that collect or reconcile
operational and mechanical evidence. It does not own computational
transformations, scientific analysis, report projections, candidate review,
adjudication, biological interpretation, or neutral contracts.

| Owner | Role |
| --- | --- |
| [`collect_canonical_BAM_QC_evidence`](canonical_bam_qc/README.md) | Numbered evidence operation `02b`; collects and validates canonical-BAM QC evidence. |
| [`collect_RSeQC_paired_orientation_evidence`](rseqc_orientation/README.md) | Numbered evidence operation `03`; collects paired-orientation evidence without selecting a biological strandedness policy. |
| [`reference_provenance`](reference_provenance/README.md) | Reconciles one explicitly declared reference bundle without repair. |
| [`runtime_preflight`](runtime_availability/README.md) | Semantic runtime-preflight evidence, physically owned by `runtime_availability`; records declared availability probes and owns a separate manual cluster module/tool smoke probe. Neither installs software or executes the workflow. |
| [`storage_inventory`](storage_inventory/README.md) | Measures declared roots, records retention policy, and owns two-phase site qualification without staging data. |

Each child owns its inputs, outputs, publication/recovery behavior, direct
tests, and evidence boundary. The two numbered operations participate in the
canonical graph in [`STAGE_MAP.md`](../contracts/STAGE_MAP.md); the operational
evidence tools are cross-cutting checks, not additional stages.

## Operational role classification

- **Pipeline evidence owners:** Steps `02b` and `03` are required graph
  operations and remain owner-local producers, validators, and scheduler entry
  points.
- **Required readiness:** the local-pilot doctor consumes the direct admitted
  runtime inspection result and the final two-phase storage-qualification
  receipt. These protect execution authority without becoming workflow jobs.
- **Optional operator diagnostics:** reference-provenance reconciliation,
  standalone runtime-availability publication, storage inventory, and the
  manual module/tool probe remain available for inspection. Their results do
  not by themselves grant doctor readiness or workflow completion.

One physical owner may expose both a required direct API and an optional
operator route; those roles do not make their evidence states interchangeable.

Steps `02b` and `03` keep their shell producers and schedulers as
repository-path interfaces while exposing their private validators as
`python -I -m emrys validate canonical-bam-qc` and
`python -I -m emrys validate rseqc-orientation`, respectively.

Reference provenance exposes installed, read-only reconciliation as
`python -I -m emrys reconcile reference-provenance` through a private
reconciler. Dry-run is the default; `--execute` publishes evidence without
repairing references, and exit `0` does not mean the resulting summary passed.

Runtime availability exposes installed inspection as
`python -I -m emrys inspect runtime-availability` through a private inspector.
It retains the `runtime_preflight` profile, report, and lock vocabulary.
Dry-run performs applicable probes without publication; `--execute` publishes
the requested report, and exit `0` does not mean every probe passed.

Storage inventory exposes `emrys inspect storage-inventory` for read-only
measurement and `emrys inspect storage-qualification` for an explicit
compute/head durability probe. The latter publishes a final receipt only after
both declared roots pass and never supplies an ad hoc stage-copy path.

Use the [`RUNBOOK`](../../../docs/operations/RUNBOOK.md) for supported commands,
[`TROUBLESHOOTING`](../../../docs/operations/TROUBLESHOOTING.md) for failure and
recovery routes, and
[`HANDOFF.md`](../../../docs/operations/HANDOFF.md) for current evidence state.
Ownership and system boundaries live in
[`ARCHITECTURE.md`](../../../docs/architecture/ARCHITECTURE.md) and the
[`functional-owner inventory`](../../../docs/architecture/FUNCTIONAL_OWNER_INVENTORY.md).

Publication or downstream consumption never promotes evidence by itself.
Availability is not workflow execution, and local characterization is not
cluster or production validation. Candidate review, adjudication, and
biological interpretation are external work-process records, not evidence
owners or completion states in this package.
