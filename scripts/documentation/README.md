# Documentation structure validation

This owner contains the read-only repository structure gate behind
`make -s documentation-check`.

[`validate_structure.py`](validate_structure.py) admits one exact Git worktree
root and inventories tracked plus untracked, non-ignored Markdown and Mermaid
sources. It checks:

- canonical document presence and first H1;
- presence and opening warnings for legacy transition documents until the
  owning retirement package deliberately removes them from the roster;
- absence of explicitly retired document and task-detail surfaces;
- required cross-cutting owner documentation;
- the 14-identity `STAGE_MAP` roster and adjacent owner `README.md`,
  `CONTRACT.md`, and mirrored test directory;
- standalone Mermaid declaration and fence shape.

The supported direct interface is:

```bash
./scripts/documentation/validate_structure.py --repo /exact/git/worktree/root
```

The command performs no writes. It fails closed when Git inventory or exact-root
admission fails and exits nonzero with all detected structure problems.

This is intentionally not a general documentation linter. It does not validate
links, anchors, prose currency, diagram inbound references, matrix semantics,
or dependency edges inside `SOURCE_TOPOLOGY.md`. Exact behavior and seeded
failure coverage live in
[`tests/documentation/test_validate_structure.py`](../../tests/documentation/test_validate_structure.py).
