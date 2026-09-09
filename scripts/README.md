# Repository scripts

Scientists and operators normally use `emrys`. This directory holds repository
maintenance tools and Makefile fragments; invoke Make targets through the root
`Makefile`.

| File | Purpose |
| --- | --- |
| `benchmark_stage_resources.py` | Measures stage commands at declared resource values; previews unless execution is enabled. |
| `check_r_environment.R` | Checks the selected R library against the lock and verifies report support. |
| `restore_r_environment.R` | Restores the R library from `renv.lock`, through the root Make target. |
| `documentation/validate_structure.py` | Checks documentation ownership, required pages, local links, and Mermaid structure. |
| `make_operations.mk` | Supplies the legacy dashboard target, retained until its replacement is ready. |
| `make_quality.mk` | Supplies test, coverage, formatting, documentation, package, shell, and R targets. |

The [runbook](../docs/operations/RUNBOOK.md) explains resource benchmarking and
dependency maintenance.
