# FUT-SITE-01 — CSU SLURM execution profile

State: [`UNREFINED` proposal](README.md). It is not a selectable task and does
not establish CSU runtime or cluster evidence.

## Proposal

Define a future CSU SLURM execution profile that lets a researcher move from a
local-pilot contract to explicit batch-visible runtime, storage, scheduler,
logging, and recovery contracts.

## Why preserve it

Batch-visible tool and module versions, storage and scratch allocations,
retention policy, scheduler limits, R-package availability, operator authority,
and cluster-proof evidence are not sufficiently settled for implementation.
The site-profile concept is useful to retain without inventing those facts.

## Potential scope

- Batch-visible dependency and module identity.
- Explicit project, scratch, temporary, output, and retention behavior.
- SLURM resources, dependencies, retries, logs, cancellation, and recovery.
- Login-node versus compute-node boundaries.
- Cluster dry-run and cluster-proof evidence requirements.
- Site-specific operator handoff and failure recovery.

## Settled boundaries

- A local pilot remains independently useful and must not infer CSU state.
- A SLURM dry-run is not cluster proof.
- Tool availability, local fixtures, and mocked tests are not batch-execution
  evidence.
- Heavy alignment, sorting, mpileup, and analysis remain compute-node work.
- This proposal authorizes no cluster access, job submission, dependency
  restoration, storage change, or production-data handling.

## Questions before refinement

- Which versions and modules are actually visible inside batch jobs?
- Which storage, scratch, temporary-space, quota, and retention contracts apply?
- Which scheduler limits, retry/cancellation rules, operator roles, and evidence
  records are required?
- Which R environment and validation commands can support a bounded cluster
  acceptance contract?

## Related work

- Completed [`TEST-01E`](../COMPLETED/TEST-01E-characterize-slurm-wrapper-contracts.md)
  is historical wrapper-contract evidence, not CSU runtime proof.
- [`FUT-CLI-03`](../TODO/FUT-CLI-03-installable-norad-control-plane.md)
  owns the future control-plane boundary.
- [`FUT-DATA-02`](../TODO/FUT-DATA-02-public-reference-and-sra-acquisition.md)
  and [`FUT-SUCCESS-04`](../TODO/FUT-SUCCESS-04-optional-analysis-and-archival-semantics.md)
  preserve adjacent future input and success contracts.

These are refinement inputs, not dependency relationships.

## Promotion conditions

Promote only after the CSU runtime, storage, scheduler, batch-visible R
environment, operator roles, evidence contract, and validation commands are
confirmed well enough for a complete reviewed TODO card.
