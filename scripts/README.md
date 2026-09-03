# Repository scripts

Scientists and operators normally use the `emrys` command. This directory holds
repository maintenance tools and Makefile fragments.

| File | Purpose |
| --- | --- |
| `benchmark_stage_resources.py` | Measures selected stage commands across declared resource values; it previews unless execution is explicitly enabled. |
| `check_r_environment.R` | Checks that the selected R library matches the locked EMRYS environment and can create reports. |
| `restore_r_environment.R` | Restores the repository's R library from `renv.lock`; use the root Make target rather than calling it directly. |
| `documentation/validate_structure.py` | Checks documentation ownership, local links, required pages, and Mermaid structure; its retired-path guard is temporary while stacked changes are integrated. |
| `make_operations.mk` | Supplies the retained legacy dashboard Make target while its final disposition remains pending. |
| `make_quality.mk` | Supplies the repository's test, coverage, formatting, documentation, package, shell, and R Make targets. |

Use the root `Makefile` for Make targets. The [runbook](../docs/operations/RUNBOOK.md)
explains the optional resource benchmark and dependency maintenance.
