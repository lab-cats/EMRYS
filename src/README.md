# Source tree

This directory contains tracked EMRYS implementation and contract source under
[`emrys/`](emrys/). It does not contain generated outputs, runtime environments,
or an installed command layout. Root `pyproject.toml` provides the explicit
internal distribution and grouped command without turning every owner
directory into a package or public command automatically.

Use the [`emrys` source index](emrys/) to choose a functional domain. Migrated
installed commands and remaining repository-path interfaces are documented by
their domain and owner READMEs; supported cross-cutting commands remain in the
[`RUNBOOK`](../docs/operations/RUNBOOK.md).
