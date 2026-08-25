# Documentation structure helper

[`validate_documentation.py`](validate_documentation.py) is the read-only
repository-maintenance command behind `make -s documentation-check`. It checks
canonical document ownership, retired-document guards, semantic-owner
adjacency, and standalone Mermaid source shape.

It does not select work, grant authority, mutate Git, validate general links or
anchors, establish documentation currency, or create pipeline evidence.
Focused behavior tests live in
[`tests/git_orchestration/test_documentation_validator.py`](../../tests/git_orchestration/test_documentation_validator.py).
