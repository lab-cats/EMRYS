# Repository scripts

Scientists and operators normally use `emrys`. This directory holds repository
maintenance tools and Makefile fragments; invoke Make targets through the root
`Makefile`.

| File | Purpose |
| --- | --- |
| `benchmark_stage_resources.py` | Measures stage commands at declared resource values; previews unless execution is enabled. |
| `check_r_environment.R` | Checks the selected R library against the lock and verifies report support. |
| `documentation/validate_structure.py` | Checks documentation ownership, required pages, local links, and Mermaid structure. |
| `make_operations.mk` | Supplies the legacy dashboard target, retained until its replacement is ready. |
| `make_quality.mk` | Supplies test, coverage, formatting, documentation, package, shell, and R targets. |

The packaged [R restore command](../src/emrys/resources/runtime/restore_r_environment.R)
restores the selected library from the packaged lock through Doctor or the root
Make target. The [runbook](../docs/operations/RUNBOOK.md) explains resource benchmarking and
dependency maintenance.
