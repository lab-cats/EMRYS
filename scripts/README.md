# Repository scripts

Scientists and operators normally use `emrys`. This directory holds repository
maintenance tools and Makefile fragments; invoke Make targets through the root
`Makefile`.

| File | Purpose |
| --- | --- |
| `benchmark_stage_resources.py` | Measures stage commands at declared resource values; previews unless execution is enabled. |
| `check_r_environment.R` | Checks the selected R library against the lock and verifies report support. |
| `documentation/validate_structure.py` | Checks documentation ownership, required pages, local links, and Mermaid structure. |
| `make_quality.mk` | Supplies test, coverage, formatting, documentation, package, shell, and R targets. |

The packaged [R restore command](../src/emrys/resources/runtime/restore_r_environment.R)
restores the selected library from the packaged lock through Doctor or the root
Make target. The [runbook](../docs/operations/RUNBOOK.md) explains resource benchmarking and
dependency maintenance.

## Measurement and adoption

Use the existing benchmark helper only for its declared producer-command scope;
a separately invoked validator is not included in that timing. Complete Task,
Run, inspect, resume, report or Doctor costs need their complete public operation.
Retain exact baseline/candidate, inputs, reference/annotation, tool, node, storage
and profile identities, every trial outcome and raw failures. Recommendations
based only on successful trials must not hide failed ones.

Choose workload, primary metric, acceptable tradeoffs, threshold and execution
authority before a comparison. Balanced paired trials (three as an initial design,
not a universal rule) distinguish ordinary variation from an adoption claim.
Do not flush shared caches or change site policy for a benchmark without authority.

| Metric | Required distinction |
| --- | --- |
| Wall time | Queue/admission, producer, independent validation, publication and rendering versus complete public-operation elapsed time. |
| Memory | Individual/aggregate concurrent use versus reservation; largest-child RSS is not summed complete-Run peak memory. |
| I/O | Logical reads and filesystem/block accounting versus measured physical device or NFS traffic; name cache conditions. |
| Disk | Peak temporary plus retained allocated bytes; regular-path sizes count hard links repeatedly and are not reclaimable space. |
| Correctness | Exact bytes or an approved semantic comparison, independent checks and fault/recovery parity; faster successful output alone is insufficient. |

No traversal count or allocation formula is measured performance. Prefer existing
owner instrumentation and package/native capabilities over a new benchmark
framework. Retiring campaign prose does not retire this helper: `SETUP-02` requires
its own bounded remaining-use/adoption decision. The [frozen method](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/optimization_campaign.md#measurement-and-adoption)
retains the original proposal; stage-specific gates are not universal thresholds.
