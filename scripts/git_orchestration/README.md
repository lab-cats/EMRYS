# Documentation and task helpers

This directory contains two read-only repository-maintenance commands:

- [`validate_documentation.py`](validate_documentation.py) validates canonical
  owners, semantic-owner adjacency, Mermaid source shape, compact-backlog
  structure, genuine dependency integrity, and selected JIT-card structure.
  It rejects unknown, proposal, self, and cyclic blockers. `make -s
  documentation-check` is its supported wrapper.
- [`task_status.py`](task_status.py) renders a deterministic view of actionable
  items, proposals, readiness, reverse dependencies, and JIT detail.

Neither command selects work, grants authority, mutates Git, or creates
pipeline evidence. Focused behavior tests live in
[`tests/git_orchestration/test_documentation_validator.py`](../../tests/git_orchestration/test_documentation_validator.py).
