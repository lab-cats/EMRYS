# 2026-08-02 pre-migration refactor log

- Status: active until the reviewed pre-migration base is published and verified.
- Originating canonical integration commit:
  `15aba53c538cabf2b7d2284575be0089b0ca90cf`.
- Integration source evidence:
  `5a35a057cd9ca259f83ee1dde3116fee63928d72`.
- Working branch: `codex/plan-02z-first-migration-readiness`.
- Evidence boundary: planning and non-consuming Markdown documentation only;
  no source migration, executable behavior, runtime, cluster, scientific-review,
  or biological-readiness evidence.

This is the user-requested chronological risk and decision record for the
bounded pre-migration planning/review sequence. It remains mutable only until
that sequence closes; current checkout and roadmap truth remain in
`HANDOFF.md` and `PIPELINE_PLAN.md`.

## 2026-08-02T13:08:21-0400 — Canonical integration parent frozen

- **Observation:** two clean polls ten minutes apart reported integration
  `HEAD` `15aba53c538cabf2b7d2284575be0089b0ca90cf`, configured upstream
  `origin/codex/reconciliation-consolidated-01-integration`, and ahead/behind
  `0/0`. A live remote-ref check returned the same SHA.
- **Verification:** the result is one direct canonical child of
  `0fd6348e6cfe54457fef5f65f3468bea106e61f9`; the frozen sidecar SHA remains
  provenance rather than canonical ancestry. No integration fragment or Git
  recovery marker remains.
- **Risk:** treating either input tip or the sidecar's 98-checkpoint history as
  the new parent would bypass the reviewed semantic integration.
- **Decision:** freeze only `15aba53c538cabf2b7d2284575be0089b0ca90cf` as
  the parent of all planning/review work and preserve the published integration
  branch unchanged.
- **Validation boundary:** `git diff --check` passes. The documentation
  validator reproduces exactly nine `invalid card location` findings for the
  authorized but not-yet-supported `UNREFINED` README and eight proposals, with
  no additional finding. This is expected-only nonpassing, not a passing gate.

## 2026-08-02T13:11:59-0400 — PLAN-02Z selection exposed stale blockers

- **Observation:** moving `PLAN-02Z` to `IN_PROGRESS` and repairing inbound
  links caused seven additional `active/completed card has incomplete blocker`
  findings for `RPT-02`, `CONTEXT-09`, `DOC-PIPE-04`, `SIZE-07`, `INTAKE-02E`,
  `CODEDOC-05`, and `LIB-02F`.
- **Risk:** committing the status move alone would turn the known nine-finding
  integration exception into a broader invalid state and would preserve the
  superseded whole-program waterfall as active blocker semantics.
- **Decision:** do not commit the intermediate selection. Inspect the minimum
  first-migration boundary, recast the stale edges as genuine blockers or
  nonblocking context based on that evidence, and require the first checkpoint
  to return to exactly the inherited nine findings.

## 2026-08-02T13:26:17-0400 — First migration seam selected

- **Observation:** twelve validators import the same nine report/snapshot/
  publication primitives from `validate_step_00a_star_index.py`; with Step
  `00a`, thirteen public validators use that one implementation. The functional
  inventory already names it as a cross-cutting validation-evidence publication
  owner, and the fault suite asserts the exact consumer roster and exercises
  its transaction failures.
- **Risk:** moving Step `00a`, Step `00b`, or another functional owner first
  would preserve or create a prohibited stage-to-stage implementation import.
  Generalizing all publishers would instead conflate heterogeneous safety
  state machines documented by `RA-009`.
- **Decision:** make `MIG-03A` the first physical unit and limit it to the nine
  proven shared primitives. Target `src/norad/libraries/validation_report.py`
  and `tests/libraries/test_validation_report.py`; keep all stage checks and
  other transaction/helper candidates local. Use three dedicated review cards
  so their completion cannot unblock unrelated broad-program work.
- **Import decision:** retain all thirteen public script paths and use explicit
  file-relative repository-local `src` resolution in each affected validator.
  Do not install NORAD, depend on caller CWD or global `PYTHONPATH`, or introduce
  a generic bootstrap helper. A temporary Step `00a` re-export is permitted
  only between reversible cutover checkpoints and must be removed at close.
- **Evidence boundary:** no executable or test file changed and no
  computational test ran. `git diff --check` passes; documentation validation
  is back to exactly the inherited nine unsupported-`UNREFINED` findings, with
  all seven stale PLAN blocker findings eliminated.

## 2026-08-02T13:31:03-0400 — PLAN-02Z accepted and closed

- **Verification:** committed checkpoint `c45e748` is a clean direct descendant
  of the frozen integrated parent. Reinspection found twelve direct importers,
  the exact nine shared symbols named by `MIG-03A`, and mode `0644` for every
  affected validator and the current fault-test owner.
- **Risk:** treating the planning proposal as implementation evidence, or
  completing a broad `REVIEW-*` card, would either bypass executable task start
  or falsely unblock unrelated logging, report, size, and documentation work.
- **Decision:** close only `PLAN-02Z`. Keep the broad review cards frozen and
  route this tranche through `REVIEW-ARCH-03A`, `REVIEW-REL-03A`, and
  `REVIEW-UX-03A` before selecting `MIG-03A`.
- **Validation boundary:** the committed planning tree adds no validator
  finding beyond the inherited nine unsupported-`UNREFINED` locations. No
  source, test, configuration, dependency, runtime, or cluster action occurred.

## 2026-08-02T13:33:26-0400 — Architecture review selected

- **Boundary:** `REVIEW-ARCH-03A` reviews committed plan tip `ed4f42d` and may
  revise planning/card documentation only; it cannot touch executable source.
- **Risk:** the current autonomous sequence has no separately commissioned
  reviewer, so this pass is independent in time, evidence read, and commit
  boundary but not in authorship.
- **Decision:** perform a clean-tree adversarial pass, disclose the authorship
  limitation in its completion record, and place any correction after the
  immutable plan checkpoints. A later requirement for a different reviewer
  reopens this review before execution rather than being silently claimed now.
