# Source tree

This directory contains tracked NORAD implementation and contract source under
[`norad/`](norad/). It does not contain generated outputs, runtime environments,
or an installed command layout. Root `pyproject.toml` provides the explicit
internal import distribution without turning every owner directory into a
package automatically.

Use the [`norad` source index](norad/) to choose a functional domain. Public
repository-path interfaces remain documented by their domain and owner
READMEs; supported cross-cutting commands remain in the
[`RUNBOOK`](../docs/operations/RUNBOOK.md).
