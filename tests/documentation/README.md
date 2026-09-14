# Documentation structure tests

[`test_validate_structure.py`](test_validate_structure.py) checks the read-only
[documentation checker](../../scripts/documentation/README.md) using temporary
repositories. Cases cover successful checks without writes, invalid roots,
Git-inventory failures, required documents and headings, stage identities and
adjacent owners, local links and anchors, and standalone Mermaid syntax.
These tests check document structure, not prose accuracy or workflow science.
