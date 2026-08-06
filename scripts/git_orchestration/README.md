# Documentation and task helpers

This directory contains two read-only repository-maintenance commands:

- [`validate_documentation.py`](validate_documentation.py) validates canonical
  owners, semantic-owner adjacency, Mermaid source shape, actionable-card
  structure, and `UNREFINED` proposal shape. It deliberately does not police
  links, anchors, cross-card references, reciprocity, or dependency cycles.
  `make -s documentation-check` is its supported wrapper.
- [`task_status.py`](task_status.py) renders a deterministic view of surviving
  actionable cards and their dependency edges.

Neither command selects work, grants authority, mutates Git, or creates
pipeline evidence. Focused behavior tests live in
[`tests/git_orchestration/test_documentation_validator.py`](../../tests/git_orchestration/test_documentation_validator.py).
