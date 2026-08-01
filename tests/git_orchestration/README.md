# Git orchestration tests

This directory tests the repository-local fragment-integration commands under
`scripts/git_orchestration/`. The tests use only temporary local worktrees and
bare remotes; they never contact a network remote or mutate a developer
checkout.

Run the focused suite from the repository root:

```console
python -m pytest -q tests/git_orchestration
```

The fixtures intentionally exercise exact Git identities, clean-worktree
requirements, frozen path sets, fragment syntax, target modes, conflict
recovery, commit trailers, no-op recording, and non-force publication.
