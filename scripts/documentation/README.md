# Documentation structure checker

`make -s documentation-check` runs [`validate_structure.py`](validate_structure.py)
without changing the repository. It reads tracked and untracked, non-ignored
Markdown and Mermaid files and checks required pages and first headings, the
14 identities in `STAGE_MAP`, adjacent owner READMEs/contracts/tests, local links
and anchors, and standalone Mermaid declarations and fences.

The direct command requires the exact Git worktree root:

```bash
./scripts/documentation/validate_structure.py --repo /exact/git/worktree/root
```

Invalid roots or failed Git inventory stop the check. Otherwise it reports all
structure problems and exits nonzero if any were found. It does not assess
prose accuracy, whether diagrams are linked to, backlog meaning, or Python
import rules. [Direct tests](../../tests/documentation/test_validate_structure.py)
cover the checker and its failures.
