# EMRYS glossary

This glossary covers EMRYS-specific terms that are easy to confuse. Standard
genomics formats, scientific tools, and statistical methods are documented by
their owners and upstream projects rather than repeated here.

| Term | Meaning in EMRYS |
| --- | --- |
| **Project** | The user-facing root containing `project.yaml` and EMRYS-owned `runs/`, `logs/`, and `runtime/`, while referencing source inputs in place. |
| **Analysis** | One named, content-derived scientific definition within a Project. Its human name selects it but does not enter its immutable identity. |
| **analysis module** | An explicitly selected installed provider of closed scientific configuration and downstream tasks. It inherits EMRYS's Run, task, publication, recovery, logging, and Results contracts. |
| **Run** | An immutable admitted scientific and computational plan. Changing its bound content creates another Run. |
| **processing Run** | A complete Run ending after evidence-complete per-sample processing through Step `06`; a later Run may reuse it for compatible downstream analysis. |
| **Attempt** | One execution or resume try beneath a Run. An Attempt may change placement but cannot rewrite the Run. |
| **Results** | Scientist-facing outputs retained with the Run. Presence alone does not establish admitted completion. |
| **artifact** | A declared output with identity, scope, provenance, and evidence metadata. A valid record or schema does not prove the computation. |
| **transaction** | Outputs validated and published as one recoverable unit. Individual member presence is not completion. |
| **receipt-last** | Publication of the transaction receipt only after every declared payload validates. The receipt itself must still be re-admitted. |
| **no-clobber** | Refusal to overwrite or silently adopt an incompatible existing final artifact or transaction. |
| **execution profile** | Optional Project-local or absolute configuration for resources and direct/Slurm placement. It does not contain scientific inputs or runtime acquisition policy. |
| **runtime inventory** | The single Project-owned admission record for already selected tools and libraries. Users do not weaken or hand-author it to make readiness pass. |
| **manifest** | An explicit table declaring repeated inputs such as samples or partitions. EMRYS does not infer these identities from filenames or globs. |
| **CMH-ranked candidate** | A computational candidate ranked by the built-in paired-CMH Analysis. It is not a validated RNA-editing site or biological conclusion. |
| **`FWD_like` / `REV_like`** | Mechanical alignment-flag groups, not transcript strand or biological sense/antisense labels. |
| **evidence ceiling** | The strongest claim supported by a check or artifact. Local fixtures, real-runtime work, scheduler execution, scientific review, and biological interpretation are distinct levels. |

For exact behavior, use the [current architecture](../architecture/ARCHITECTURE.md),
[Run-coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md),
[stage map](../../src/emrys/contracts/STAGE_MAP.md), and affected scientific
owner contract.
