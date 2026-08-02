# 2026-08-02 pre-migration refactor log

- Status: pre-migration phase closed; the chronological record continues on the
  separately authorized `MIG-03A` execution descendant.
- Originating canonical integration commit:
  `15aba53c538cabf2b7d2284575be0089b0ca90cf`.
- Integration source evidence:
  `5a35a057cd9ca259f83ee1dde3116fee63928d72`.
- Working branch: `codex/plan-02z-first-migration-readiness`.
- Evidence boundary through the pre-migration close: planning and non-consuming
  Markdown documentation only; no source migration, executable behavior,
  runtime, cluster, scientific-review, or biological-readiness evidence.

This is the user-requested chronological risk and decision record for the
bounded pre-migration planning/review sequence and the now-authorized first
migration. The pre-migration portion is frozen on the published planning branch;
new entries belong only to its `MIG-03A` descendant. Current checkout and
roadmap truth remain in `HANDOFF.md` and `PIPELINE_PLAN.md`.

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

## 2026-08-02T13:38:20-0400 — Architecture review findings incorporated

- **High — revised:** the planned repository-local `src` insertion would
  mutate process-global `sys.path`, contradicting the Python migration contract
  and risking ambient package resolution. `MIG-03A` now requires caller-local
  exact-file loading, one private cached module identity, exact `__file__`
  verification, wrong-path rejection, and a test that `sys.path` is unchanged.
- **Medium — revised:** naming `norad.libraries.validation_report` as an import
  identity implied package semantics despite the explicit packaging deferral.
  The card now fixes only the source-owner path and excludes `__init__.py`,
  build metadata, distribution, and a public import name.
- **Medium — revised:** a temporary Step `00a` re-export had no unmovable
  caller and would add avoidable compatibility state. Final-owner introduction,
  all caller/test cutovers, and removal of the embedded implementation are now
  one atomic executable commit with one-step rollback.
- **Accepted:** neutral ownership, the nine shared API names plus internal
  `HEADER`, mirrored test home, stage-local check ownership, future dependency
  direction, and no-wrapper final tree are coherent.
- **Residual risk:** review authorship is not independent. The result is a
  separate clean-tree adversarial pass, not a claim of external review.
- **Evidence boundary:** documentation only; no import was changed and no
  Python, runtime, cluster, scientific-review, or biological evidence was
  produced.

## 2026-08-02T13:39:54-0400 — Reliability review selected

- **Boundary:** `REVIEW-REL-03A` starts from architecture-corrected checkpoint
  `74d9380` and may revise only planning/card documentation.
- **Risk:** moving the implementation owner can make existing fault tests pass
  against the wrong module, or can convert a characterized unsafe outcome into
  an accepted contract through imprecise wording.
- **Decision:** trace every publication-fault case and independent roster/
  golden owner to the exact final file, require old/new state equivalence, and
  keep every known unsafe state explicitly characterized. The previously
  disclosed same-author limitation continues to apply.

## 2026-08-02T13:42:33-0400 — Reliability review findings incorporated

- **High — revised:** a private exact-file loader can leave a partially
  initialized module in `sys.modules` if execution fails. The card now requires
  exact cache ownership, wrong-path rejection, owned-partial removal, and
  foreign-entry preservation; no loader may reuse partial state.
- **Medium — revised:** the initial parity prose named headline defects but did
  not enumerate every protected injected outcome. The acceptance boundary now
  covers first/repeat publication, malformed stage/predecessor, symlinks,
  fsync, both move boundaries, post-publish validation, interruption, late
  collision, failed restoration, cleanup, descriptor, and lock residue.
- **Accepted:** the current safe outcomes stay preserved; metadata-only rewrite
  blindness, unordered report acceptance, late-foreign deletion, unprotected
  rollback residue, cleanup/descriptor retention, and post-publication lock
  residue remain characterized defects rather than target behavior.
- **Evidence boundary:** documentation-only review of existing fault evidence;
  no test execution, defect correction, cleanup, recovery action, or evidence
  promotion occurred.

## 2026-08-02T13:43:57-0400 — Usability review selected

- **Boundary:** `REVIEW-UX-03A` starts from reliability-corrected checkpoint
  `102510b` and may revise only public-boundary planning/card documentation.
- **Risk:** a private loader can preserve computation while degrading direct
  command diagnostics, arbitrary-CWD behavior, or maintainer findability; a
  handoff can also blur "selected for planning" into "implementation begun."
- **Decision:** compare every current public script path and CLI boundary,
  require explicit loader-failure behavior and discoverable owner documentation,
  and preserve an unambiguous stop before source mutation. The same-author
  review limitation remains disclosed.

## 2026-08-02T13:48:53-0400 — Usability review findings incorporated

- **High — revised:** all thirteen validators are tracked at mode `0644` and
  the public contract invokes them through an explicit Python interpreter. The
  card now prohibits implying direct executable support and requires the
  healthy-owner arbitrary-CWD help/malformed matrix to remain unchanged.
- **High — revised:** exact-file owner loading creates new corrupted-checkout
  failure journeys before argument parsing. Each validator must now emit one
  concise stderr-only diagnostic with the expected path and causal exception,
  exit nonzero, and create no report or invocation-directory artifact; ordinary
  load errors must not produce a traceback or swallow control-flow exceptions.
- **Medium — revised:** a path-only owner is hard to discover when it has no
  package/import identity. The migration now includes a local library README,
  module docstring, and concise caller comments that name the nine APIs,
  internal `HEADER`, known defects, and temporary loader lifetime without
  adding package metadata or an installation step.
- **Accepted:** public filenames, shebangs, runbook command, flags, streams,
  normal exit states, dry-run/execute effects, report bytes, check rosters, and
  evidence meanings remain unchanged. Corrupted-owner tests are separate from
  the existing healthy public-CLI contract.
- **Residual risk:** review authorship is not independent. This was a separate
  clean-tree pass against immutable reliability checkpoint `102510b`, not a
  claim of external review.
- **Evidence boundary:** documentation-only review; no source/test mutation,
  command execution, result publication, runtime, cluster, scientific-review,
  or biological evidence occurred.

## 2026-08-02T13:52:46-0400 — MIG-03A selected for read-only planning

- **Verification:** review checkpoint `b714f61` is clean, eight commits ahead
  of integrated parent `15aba53`, and changes Markdown only. All three dedicated
  review cards are complete; the broad review cards remain frozen.
- **Risk:** treating an `IN_PROGRESS` lifecycle move as executable authority
  would bypass the required clean published parent, supported dry run, live
  import/mode/test refresh, and separate source-mutation boundary.
- **Decision:** move only `MIG-03A` into `IN_PROGRESS`, repair its inbound
  status links, and continue task-specific read-only planning on the same
  branch. Do not create the implementation branch, run the validator, edit
  source/tests, or begin the migration.
- **Evidence boundary:** this is a status/documentation checkpoint only. Live
  Git will define the later executable parent after the planning base is clean,
  published, and proved upstream-equal.

## 2026-08-02T13:58:28-0400 — MIG-03A execution plan frozen

- **Verification:** the selected clean tree still has exactly twelve Step
  `00a` importers plus the owner CLI, the nine planned APIs and internal
  `HEADER`, thirteen mode-`0644` validator and direct-test pairs, the complete
  adversarial publication suite, and no executable diff from integrated parent
  `15aba53`. Repository searches found no external runtime importer or public
  path that requires a compatibility wrapper.
- **High — revised:** `.coveragerc` and the deterministic snapshot tool measure
  only `scripts`, while the proposed owner is under `src/norad/libraries`.
  Without a coupled harness cutover, the moved safety-critical implementation
  could disappear from coverage while the gate appeared healthy. The one
  atomic executable/test commit must therefore update the exact source roots,
  new-shared-module Make arguments, compile/static targets, wiring tests,
  literal Make expansions, and reviewed snapshot. This is direct evidence
  wiring for one owner, not authority for general harness refactoring.
- **Medium — revised:** the loader plan named a private cache concept but not
  its stable identity or new failure status. Freeze `_norad_validation_report`,
  exact caller-relative owner resolution, and status `2` with the stable
  `ERROR: unable to load NORAD validation-report owner ...` stderr prefix.
  Cleanup owns only the exact partial cache entry and re-raises control-flow
  exceptions.
- **Medium — revised:** current root and architecture prose says executable
  source has not migrated under `src/norad`. The documentation-close write set
  now includes those implemented-topology owners, `TEST_BASELINE.md`, and the
  documentation ownership map, while the unchanged runbook validator command
  remains untouched unless final impact inspection proves otherwise.
- **Decision:** use one future branch from the final published planning tip,
  one atomic executable/test cutover commit, and one impact-directed
  documentation-close commit. The published planning tip is the stable pre-
  mutation rollback point; do not add a wrapper, package marker, install step,
  generic loader, or empty baseline commit.
- **Stop boundary:** publication/equality verification is the only remaining
  pre-migration action. Do not create the execution branch or run even the
  supported tiny-fixture dry run in this sequence.
- **Evidence boundary:** planning and existing-test inspection only; no
  computational test, dependency action, runtime/cluster work, source/test
  mutation, defect correction, or evidence promotion occurred.

## 2026-08-02T14:00:58-0400 — Execution authority expanded

- **Authority:** after the narrow execution plan was prepared, the user
  explicitly directed the migration to begin upon completion of the pre-
  migration base and to continue autonomously.
- **Risk:** beginning source work on an unpushed planning tip would erase the
  requested stable publication/reversion boundary and make the executable
  parent ambiguous.
- **Decision:** first commit, validate, publish, and prove the planning branch
  upstream-equal. Only then create the one `MIG-03A` execution branch from that
  exact tip, record baseline evidence, and run the supported dry run before
  source mutation. The authority expansion covers the reviewed card, its exact
  tests/harness wiring, impact-directed documentation, local validation,
  commits, and publication; it does not activate another migration, cluster or
  production work, dependency installation, or defect correction.

## 2026-08-02T17:47:22-0400 — Pre-migration base published and closed

- **Verification:** planning tip `3fdc6e7` was pushed to
  `origin/codex/plan-02z-first-migration-readiness`; local `HEAD`, configured
  upstream, and the live remote ref were identical with ahead/behind `0/0`.
  The committed tree was clean, changed no executable/test-harness path from
  integrated parent `15aba53`, passed `git diff --check`, and reproduced only
  the nine inherited unsupported-`UNREFINED` documentation findings.
- **Risk:** GitHub reported that configured origin
  `https://github.com/Glen-Cocoa/norad.git` redirects to
  `https://github.com/lab-cats/norad.git`. Silently rewriting local remote
  configuration would be an unrequested workstation mutation; ignoring the
  redirect would hide the actual publication destination.
- **Decision:** preserve the configured `origin`, record the redirect, and use
  live-ref equality rather than the URL spelling as publication proof. Repush
  this final closure commit and verify equality again; the resulting exact tip
  is the only valid `MIG-03A` execution parent.
- **Boundary:** close the pre-migration phase before creating the execution
  branch. The planning branch contains Markdown only and remains the stable
  remote rollback point requested before risky source work.

## 2026-08-02T17:52:01-0400 — MIG-03A execution baseline frozen

- **Parent verification:** dedicated branch
  `codex/mig-03a-extract-validation-report-library` was created at exact clean,
  published, upstream-equal planning tip
  `1966d03a9906f1fe8afbe21d8373d877569182ad`. No other mutable lane owns this
  branch, worktree, card, or write set; source, tests, and harness still match
  that parent.
- **Supported dry run:** the existing Step `00a` tiny-fixture dry-run test
  passed (`1 passed`) without execute mode or dependency restoration. This is
  local fixture evidence only and does not establish real-runtime, cluster,
  scientific-review, or biological evidence.
- **Characterization baseline:** the thirteen direct validator suites,
  publication-fault suite, exact check rosters, independent contract goldens,
  public CLI contracts, and coverage-baseline wiring passed together
  (`347 passed`). All thirteen public validators and their direct tests remain
  tracked at mode `0644`; the target library directory is still absent.
- **High risk:** the final owner and every caller must change together because
  no supported hybrid import state or compatibility re-export exists.
  **Decision:** publish this documentation-only execution baseline as the
  stable pre-mutation rollback point, then make the final module, all thirteen
  loaders, direct/fault/import tests, and exact coverage/static wiring one
  atomic executable/test commit.
- **Medium risk:** an exact-file loader can reuse a wrong or partial cache
  entry, overwrite foreign state, or convert `KeyboardInterrupt` into an
  ordinary diagnostic. **Decision:** use the frozen private identity
  `_norad_validation_report`, verify the exact resolved `__file__` and ready
  sentinel, register before execution, remove only the exact owned partial on
  any execution failure, preserve foreign entries, and catch only ordinary
  `Exception` at the public diagnostic boundary.
- **Rollback:** before executable mutation, the migration branch must be
  pushed and proved upstream-equal at this baseline. Later rollback reverts the
  documentation close first and the atomic executable/test cutover second;
  the published planning branch remains the earlier independent recovery base.
- **Documentation validation:** `git diff --check` passed. The repository
  documentation validator reproduced exactly the nine inherited unsupported-
  `UNREFINED` location findings and no other finding; this remains expected-
  only nonpassing evidence, not a passing documentation gate.

## 2026-08-02T18:49:45-0400 — MIG-03A physical cutover and campaign authority

- **Expanded authority:** the user's attached campaign directive supersedes the
  earlier `PLAN-02Z` limitation that activated only `MIG-03A`. Continue on one
  physical-migration campaign branch, creating exactly one dependency-valid
  migration card and architecture/reliability/usability review chain just in
  time. Each unit must close, commit, publish, and prove equality before the
  next is selected; later cards and unrelated roadmap work remain unactivated.
- **Atomic cutover:** published commit
  `9d93694e87858e0d2db71703cfabeecd2980ef69` adds the one final owner at
  `src/norad/libraries/validation_report.py`, moves the direct publication-
  fault owner to `tests/libraries/test_validation_report.py`, and cuts all
  thirteen legacy validators through the same exact caller-local loader. All
  callers remain mode `0644`; there is no wrapper, package marker, public
  import identity, installation step, or `sys.path` mutation. Local `HEAD`,
  configured upstream, and live remote ref were equal at that checkpoint.
- **Preserved behavior decision:** remove only the Step `00a` embedded shared
  implementation and retain stage parsing, rosters, public paths, streams,
  exits, report bytes, and every characterized publication defect. Loader tests
  prove exact-file/module identity, arbitrary-CWD use, wrong-cache rejection,
  owned partial-cache cleanup, foreign-cache preservation, and control-flow
  propagation. This is relocation evidence, not defect correction.
- **Coverage decision:** once the final module entered the reviewed baseline,
  the shared-module threshold tool could no longer require it to be absent from
  that baseline. Keep the explicit 90% line/85% branch threshold enforced both
  before and after baseline promotion, and measure exactly the `scripts` and
  `src/norad/libraries` roots. This prevents the migrated safety-critical code
  from disappearing behind a baseline update. The final deterministic serial
  lane passed (`1056 passed, 17 skipped, 1 deselected`); global exact line and
  branch rates rose from `0.808701`/`0.696956` to
  `0.812011`/`0.698382`, and the final module measured
  `1.000000`/`0.972222`. The one-line `_common.py` helper remained `1/1`.
- **Focused evidence:** final library tests passed (`137 passed`), all thirteen
  direct validator/golden suites passed (`98 passed`), and
  `make validation-static` passed. These follow the pre-cutover supported dry
  run (`1 passed`) and focused characterization (`347 passed`). An earlier
  broad Python attempt before the final expanded loader matrix reported `946
  passed, 17 skipped, 1 failed`; its only failure was the documentation-
  validator repository test described below.
- **Canonical gate risk:** the first guarded-R run could not retrieve
  Bioconductor metadata through the restricted network. The authorized network
  retry passed; no dependency was installed, restored, or changed. Guarded-R,
  shell, report-runtime, and validation-static lanes passed. The aggregate
  Python lane cannot receive the coverage-only deselection because
  `run_validation.py` owns its pytest arguments, and it reported `1056 passed,
  17 skipped, 1 failed`: the one failing documentation test saw eight stale
  links caused by the test-owner move plus the nine inherited unsupported
  `UNREFINED` locations. The documentation close repairs all eight migration-
  caused links; the nine inherited findings remain expected-only nonpassing
  evidence rather than a successful `make all-checks` claim.
- **Parallel-run decision:** a direct xdist coverage attempt completed its
  tests but emitted a coverage-combine no-data warning and produced a lower
  `0.796715` line rate that is not comparable to the tracked deterministic
  baseline. Record the clean serial coverage lane above and do not promote the
  parallel measurement.
- **Documentation impact:** update the implemented topology, functional-owner
  inventory, coverage roots, ownership map, task/roadmap/handoff state, and the
  supported runbook fault-test path. Repair destination-relative contract links
  to the moved test in the same close. No pipeline diagram changes because DAG
  edges and public entry points are unchanged.
- **Evidence and rollback boundary:** all evidence is local fixture/static
  evidence. No real-runtime, cluster, scientific-review, or biological-
  readiness state is created. Roll back the documentation/lifecycle close
  first, then atomic commit `9d93694`; published planning tip `1966d03` remains
  the earlier independent recovery point. Do not delete runtime, production,
  lock, backup, or recovery artifacts during rollback.

## 2026-08-02T19:02:53-0400 — MIG-03B JIT unit defined

- **Verified predecessor:** local `HEAD`, configured upstream, and status were
  clean and equal at published `MIG-03A` close
  `f3f2c2ab335d5a803550defd7676e9e9f9eb9fa4`; ahead/behind was `0/0`.
  No untracked, recovery, or lock state was observed in the campaign worktree.
- **Selection evidence:** the semantic DAG has three currently eligible roots:
  `construct_STAR_index`, `convert_GTF_to_BED12`, and
  `construct_FASTA_sidecars`. Live native-asset inspection found the STAR-index
  unit is the smallest bounded root: one 64-line SLURM producer, one 285-line
  Python validator, and one 127-line dedicated validator test, versus larger
  producer/validator/test surfaces for the other roots. Selection therefore
  follows required-artifact eligibility and bounded cutover risk, not numeric
  alias order.
- **Architecture risk and decision:** Step `00a` currently materializes FASTA
  and GTF files used operationally by Steps `00b` and `00c`, but neither consumes
  its STAR index or implementation. Preserve that behavior as typed-external-
  input coupling and move only the assets already assigned by the frozen target
  topology; do not create a reference-preparation owner or semantic edge.
- **Caller risk and decision:** moving the job and validator changes explicit
  public repository paths, the Step `00a` implementation-evidence path, the
  validator's relative neutral-library route, Make/static/coverage selection,
  and independent cross-owner test inventories. All named consumers are
  repository-owned and can cut over atomically, so `MIG-03B` forbids a wrapper,
  compatibility copy, package marker, symlink, or committed hybrid state.
- **Coverage risk and decision:** the validator's measured statements would
  otherwise disappear when it leaves `scripts/`. Replace the narrow
  `src/norad/libraries` measurement entry with the stable `src/norad` source
  boundary, preserve explicit old/new line and branch counts, and regenerate
  the tracked snapshot only through the reviewed repository command. This
  continues measuring the neutral library while admitting the one active owner;
  relocation may not appear as an unrelated deletion and addition.
- **Collision and reconciliation:** two untracked `MIG-03B` drafts appeared
  within five seconds during card creation. Mutation stopped immediately; the
  branch, upstream, and live remote remained equal at `f3f2c2a`, no Git recovery
  or lock state existed, and both drafts then remained byte-stable. Preserve the
  earlier `MIG-03B-migrate-construct-star-index-owner.md` draft because it names
  the complete path-aware caller, provenance, README, and stable coverage-root
  obligations; merge the shared review chain around it and remove only the
  redundant untracked duplicate before validation. No executable state was
  touched and no published history was rewritten.
- **Review decision:** create only `MIG-03B` and its dedicated
  `REVIEW-ARCH-03B` → `REVIEW-REL-03B` → `REVIEW-UX-03B` chain. Each review is
  an independent-in-time adversarial pass by the same campaign agent unless a
  separate author becomes available; independent authorship is not claimed.
  No executable/test file changed and no computational test ran in this slice.
- **Evidence boundary:** this checkpoint is planning documentation only. It
  creates no local runtime, cluster, production, scientific-review, or
  biological-readiness evidence and does not preselect any later migration.

## 2026-08-02T19:12:16-0400 — REVIEW-ARCH-03B selected

- **Selection:** move only `REVIEW-ARCH-03B` to `IN_PROGRESS` and repair its
  exact inbound and outbound lifecycle links. `REVIEW-REL-03B`,
  `REVIEW-UX-03B`, and `MIG-03B` remain unselected in `TODO`.
- **Review boundary:** this begins one read-only independent-in-time adversarial
  architecture pass against published planning checkpoint `5ac7723`. The same
  campaign agent authored or reconciled the plan, so independent authorship is
  not claimed. No executable/test file changes and no computational test is
  authorized by this review.
