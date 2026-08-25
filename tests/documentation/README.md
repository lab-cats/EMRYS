# Documentation structure tests

[`test_validate_structure.py`](test_validate_structure.py) protects the
read-only documentation structure gate in
[`scripts/documentation/`](../../scripts/documentation/README.md).

The suite seeds success without writes, exact-root and Git-inventory failures,
canonical-owner and retired-surface failures, semantic-owner adjacency defects,
and malformed standalone Mermaid sources. It does not validate workflow
computation, scientific artifacts, documentation prose, or general links.
