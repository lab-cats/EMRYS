# Git orchestration helpers

This directory contains bounded, operator-invoked safeguards for integration-
fragment Git operations. The tools turn the mechanical checks formerly
embedded in `RUNBOOK.md` into independently testable programs. They do not
select work, grant authority, choose dispositions, compose canonical prose,
resolve conflicts, clean recovery state, or authorize publication.

The read-only validators are:

- [`validate_documentation.py`](validate_documentation.py), which runs the
  repository documentation structure gate for an explicit worktree root;
- [`validate_fragment_candidate.py`](validate_fragment_candidate.py), which
  binds one frozen candidate to its worktree, branch, base, exact diff,
  reservations, fragment shape, and published source ref; and
- [`validate_fragment_target.py`](validate_fragment_target.py), which checks
  one operator-declared target mode and prints target drift for human review.

The mutating entry points are dry-run by default and require `--execute`:

- [`apply_fragment_candidate.sh`](apply_fragment_candidate.sh) rebinds both
  lanes and applies one candidate, aborting only a normal cherry-pick conflict;
- [`finalize_fragment_integration.sh`](finalize_fragment_integration.sh)
  stages only declared final paths, removes the fragment, and amends from an
  operator-authored commit-message file;
- [`record_fragment_noop.sh`](record_fragment_noop.sh) records a terminal
  exchange whose canonical tree does not change; and
- [`publish_exact_ref.sh`](publish_exact_ref.sh) performs an exact-SHA canonical
  push guarded by a compare-and-swap lease after source, parent, final-tip, and
  expected-remote checks. It verifies the immutable source ref immediately
  before and after publication; a concurrent source-ref violation is a
  surfaced recovery incident, not a successful closure.

Run any entry point with `--help` for its complete interface. The supported
sequence and evidence interpretation remain in
[`RUNBOOK.md`](../../docs/operations/RUNBOOK.md#manual-integration-fragment-exchange),
while authority and lifecycle semantics remain in
[`CONCURRENT_WORK.md`](../../docs/operations/CONCURRENT_WORK.md#integration-fragment-authority-and-lifecycle).

The private `_common.py` and `_common.sh` modules centralize mechanical checks;
they are not operator entry points. Focused tests live in
[`tests/git_orchestration/`](../../tests/git_orchestration/).
