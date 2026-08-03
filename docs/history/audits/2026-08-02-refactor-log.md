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

## 2026-08-02T19:16:41-0400 — REVIEW-ARCH-03B completed

- **High finding — mirrored test ownership:** `MIG-03B` initially moved only
  the dedicated validator file even though the frozen mirrored-test contract
  says an owner home covers its native assets and failure semantics. Move the
  Step `00a`-specific mocked-job behavior case and its narrow fixtures into the
  mirrored owner test home as well; retain only exact cross-owner job roster,
  directive, mode, and generic wrapper assertions in the independent suite.
- **Medium finding — mixed-layout inventories:** the current SLURM, public-CLI,
  validator-roster, and validation-report tests treat basenames as children of
  one flat root. Require explicit repository-relative path maps keyed by the
  existing public basename or semantic ID, with Step `00a` as the only changed
  entry. Preserve exact roster equality; do not use wrappers, path inference,
  recursive runtime discovery, or global path mutation to hide the move.
- **Low finding — maturity claim:** the target topology names a future
  descriptor, but this physical unit does not own descriptor schemas or loading.
  The new README must link the detailed contract and distinguish implemented
  native-asset placement from the unrealized descriptor/schema and package
  identity. Do not claim the complete mature stage shape.
- **Accepted architecture:** use one atomic wrapper-free cutover, one physical
  job and validator owner, exact-file dependency on the neutral report library,
  unchanged typed-external-input reference materialization, and an intentional
  artifact implementation-evidence path transition. Measure `scripts` plus the
  stable `src/norad` source boundary; this is coverage/static selection, not a
  package identity or future-owner preload.
- **Independence and evidence boundary:** this was a separate committed-time
  adversarial pass by the same campaign agent; independent authorship is not
  claimed. Corrections affect planning documentation only. No executable/test
  file changed, no computational test ran, and no runtime, cluster, production,
  scientific-review, or biological-readiness evidence was created.

## 2026-08-02T19:18:58-0400 — REVIEW-REL-03B selected

- **Selection:** move only `REVIEW-REL-03B` to `IN_PROGRESS` and repair its
  lifecycle links after published architecture checkpoint `94199dc` was clean,
  upstream-equal, and live-remote equal. `REVIEW-UX-03B` and `MIG-03B` remain
  unselected in `TODO`.
- **Review boundary:** this begins one read-only independent-in-time adversarial
  pass over job side effects/failures, validator publication states, artifact
  implementation evidence, coverage rename accounting, and rollback. The same
  campaign agent performs the pass, so independent authorship is not claimed;
  executable/test mutation and computational testing remain out of scope.

## 2026-08-02T19:22:35-0400 — REVIEW-REL-03B completed

- **High finding — producer state coverage:** the existing mocked Step `00a`
  case proves one success and module/STAR exits but does not prove the promised
  default-eight-thread path, preservation of nonempty prepared reference bytes,
  directory creation timing, success without complete index validation, or the
  exact side effects retained after failure. Add those assertions against the
  old path before movement and run the identical owner-local cases after it.
- **High finding — validator arbitrary-CWD parity:** public characterization
  covers help and malformed input from an arbitrary CWD, while the complete
  dry-run and execute/repeat fixture runs currently force repository CWD. Add
  full identical-input journeys from a non-repository CWD before and after the
  move, comparing streams, exits, report bytes, and invocation-directory
  residue.
- **Medium finding — fault-fixture topology:** shared copied-validator failure
  tests currently flatten every file beneath a copied `scripts/` directory.
  Recreate each validator at its actual repository-relative location so the
  moved Step `00a` validator exercises its real owner-relative neutral-library
  resolution under missing and corrupt owner states.
- **Medium finding — provenance assertion:** artifact-index construction hashes
  each registered producer but no focused test names the Step `00a` path
  transition. Add one assertion that the final path changes while status,
  evidence ID, Git commit, job bytes/SHA-256, artifact identities, schemas, and
  ordering remain intact.
- **Coverage decision:** the frozen tracked Step `00a` validator entry is
  `165/189` covered/statements and `42/60` covered/total branches. Generate and
  inspect the final-path measurement before running the reviewed baseline-update
  command; only then may the tracked row move. Keep the neutral-library
  threshold and global exact-rate non-regression checks active.
- **Fault-state disposition:** the neutral fault suite already owns first/repeat
  publication, malformed stage/predecessor, symlink, fsync, replace, restoration,
  interruption, residue, file-descriptor, and lock-cleanup states. Preserve its
  same-size/restored-mtime, row-order, late-foreign deletion, incomplete
  rollback/lock loss, cleanup residue, and lock-cleanup findings as defects.
- **Independence and evidence boundary:** this was a separate committed-time
  adversarial pass by the same campaign agent; independent authorship is not
  claimed. Corrections affect planning documentation only. No executable/test
  file changed, no computational test ran, and no runtime, cluster, production,
  scientific-review, or biological-readiness evidence was created.

## 2026-08-02T19:25:27-0400 — REVIEW-UX-03B selected

- **Selection:** move only `REVIEW-UX-03B` to `IN_PROGRESS` and repair its
  lifecycle links after published reliability checkpoint `581879f` was clean,
  upstream-equal, and live-remote equal. `MIG-03B` remains unselected in `TODO`.
- **Review boundary:** this begins the final read-only independent-in-time
  adversarial pass over submitted-job and interpreter-only validator paths,
  arbitrary-CWD journeys, diagnostics, Make/operator commands, artifact
  provenance, owner findability, link repair, and rollback. The same campaign
  agent performs the pass, so independent authorship is not claimed;
  executable/test mutation and computational testing remain out of scope.

## 2026-08-02T19:27:45-0400 — REVIEW-UX-03B completed

- **High finding — command/CWD ambiguity:** the current runbook lists the job
  as a bare path, while the migration changes that path and the job remains a
  mode-`0644`, implicit-execute scheduler input whose relative data paths use
  caller CWD. Publish one explicit final `sbatch` command and distinguish that
  preserved CWD dependence from the validator's explicit-interpreter,
  explicit-input arbitrary-CWD behavior. Do not retain a legacy alias.
- **Medium finding — Make visibility:** both `validation-static` and `smoke`
  currently cover the job only through `jobs/*.slurm`. Add the exact final job
  path alongside the remaining flat-job check and update literal expansions in
  the executable/test commit; do not let the migrated native asset fall outside
  syntax validation or restore its old path for wildcard convenience.
- **Medium finding — owner journey:** the documentation-close README must name
  final job/validator/test paths and invocation forms, warn about implicit job
  execution and caller-relative inputs, link the contract/runbook, describe the
  intentional artifact-provenance path transition, and state the no-wrapper,
  no-package, no-descriptor, and local-only evidence boundaries.
- **Accepted transition:** all repository-owned job, validator, Make, artifact,
  test, and documentation consumers can move atomically. A compatibility alias
  would preserve an accidental flat-layout surface and is not justified.
- **Independence and evidence boundary:** this was a separate committed-time
  adversarial pass by the same campaign agent; independent authorship is not
  claimed. Corrections affect planning documentation only. No executable/test
  file changed, no computational test ran, and no runtime, cluster, production,
  scientific-review, or biological-readiness evidence was created.

## 2026-08-02T19:32:13-0400 — MIG-03B selected

- **Selection:** move only `MIG-03B` from `TODO` to `IN_PROGRESS` and repair its
  lifecycle links after usability-review checkpoint `028eedb` was clean,
  upstream-equal, and live-remote equal. The three dedicated adversarial reviews
  are complete, and no later migration unit is created or selected.
- **Decision:** selection opens task-specific read-only inspection, execution-
  plan freeze, and pre-mutation characterization for the one
  `construct_STAR_index` owner. It does not by itself begin executable or test
  mutation; those wait for a clean, published, local/upstream/live-remote-equal
  selection checkpoint and the package-delivery evidence sequence.
- **Risk boundary:** the accepted transition changes public repository-relative
  job, validator, and focused-test paths without an alias. The atomic cutover,
  caller-CWD versus validator-CWD distinction, exact mixed-layout inventories,
  coverage measurement-before-update rule, rollback point, and inherited defect
  preservation remain mandatory card obligations.
- **Evidence boundary:** this lifecycle change is documentation only. No
  executable/test file changed, no computational test ran, and no runtime,
  cluster, production, scientific-review, or biological-readiness evidence was
  created.

## 2026-08-02T19:41:13-0400 — MIG-03B execution baseline frozen

- **Git and authority:** inspected clean selection tip `be1b658` on the one
  campaign branch and proved local/upstream equality `0 0`; no merge commit,
  recovery head, index lock, untracked file, or shared mutable branch was
  present. Existing sibling worktrees remain separate historical lanes and do
  not authorize or receive mutation from this package.
- **Bounded plan:** move only the mode-`0644` Step `00a` job, validator, direct
  validator test, and owner-specific mocked producer behavior/fixtures into the
  frozen `construct_STAR_index` source/test homes. Cut over the explicit SLURM,
  public-CLI, validator-roster, shared-loader, artifact-provenance, coverage,
  Make, static/smoke, and literal-expansion consumers in one uncommitted batch
  and one atomic executable/test commit. No wrapper, alias, symlink, package
  marker, descriptor, schema, scheduler abstraction, or second owner is allowed.
- **Parity decision:** extend and run the mocked job cases and full validator
  non-repository-CWD dry-run/execute/repeat journey at the legacy paths before
  moving them, then run the identical cases at the final paths. The cross-owner
  SLURM suite retains only independent roster/directive/mode/generic behavior;
  the Step `00a` behavior test and narrow fakes move to the mirrored owner home.
- **Frozen bytes and modes:** job `0644`, 1,954 bytes,
  `f27924e80fee3b8f207a41fd7af472897ad51f06aa2e4c670973eb51f25b5fcc`;
  validator `0644`, 11,883 bytes,
  `0bb5ce8f87f1542fd731bcdd80f606d2f3a3982df1f65f8a17e6bc39bf9c0a6e`;
  direct test `0644`, 4,621 bytes,
  `65a9f07b6f8465290b44c9b4dde76a44ad0c59d51b225421fc749fb955a8c95a`.
- **Focused old-path evidence:** direct validator `5 passed`; Step `00a`
  mocked/inventory selection `4 passed, 109 deselected`; public-path selection
  `3 passed, 116 deselected`; exact validator rosters `105 passed`; shared
  validator/loader selection `113 passed, 24 deselected`; coverage tool
  `7 passed`; artifact-index dry-run `1 passed, 68 deselected`. These results
  are local fixtures/mocks, not runtime, cluster, production, scientific-review,
  or biological-readiness evidence.
- **Documentation gate ceiling:** the exact runbook checker reports only the
  same nine inherited `invalid card location` findings for the authorized
  `UNREFINED` documents. This is expected-only nonpassing evidence with no
  migration-caused finding; it is not recorded as a passing gate.
- **Coverage risk:** the source policy must expand from `scripts` plus
  `src/norad/libraries` to `scripts` plus `src/norad`. Measure before update and
  compare the moved row to `165/189` lines and `42/60` branches and global
  totals to `9343/11506` lines and `3281/4698` branches. Only then use the
  reviewed baseline-update command; a path rename is not deleted coverage.
- **Environment decision:** the existing approved tools are executable and
  version-compatible: repository Python `3.14.5`, coverage `7.15.2`, pytest
  `9.0.3`, pytest-xdist `3.8.0`, execnet `2.1.2`, Rscript `4.6.1`, repository R
  library, and pinned Quarto root. No install, restore, or ambient substitution
  is authorized; the final runner must start before its result is classified.
- **Cleanup classification:** the stale final `ARCHITECTURE.md` paragraph that
  still says shared report publication lives in the Step `00a` validator is
  `FIX_NOW_REQUIRED` because it would contradict both the already implemented
  neutral owner and this move. Correct it during impact-directed documentation
  close. No other collateral observation expands this card.
- **Rollback:** the commit containing this baseline is the stable pre-mutation
  reversion point. Rollback uses Git history and reverses a later documentation
  close before the atomic executable cutover; it never copies an implementation
  back or touches runtime, production, lock, backup, or recovery artifacts.

## 2026-08-02T20:21:16-0400 — MIG-03B executable checkpoint and documentation close

- **Published reversion points:** pre-mutation baseline
  `5e8342146e6a102dbda1cc3e952ebc2c45ca8eed` was clean, published, and
  upstream-equal before source mutation. Atomic executable/test checkpoint
  `4f9c863e9cdc2ba43ce631830ca237878b7ff875` is also clean, published, and
  upstream-equal `0 0`; it is the rollback point before this separate
  documentation close.
- **Remote-location diagnostic:** the executable push succeeded to the
  configured `https://github.com/Glen-Cocoa/norad.git` origin, while GitHub
  reported that the repository has moved to `https://github.com/lab-cats/norad.git`.
  Local/upstream equality is exact after the push. Changing the configured
  remote is outside this owner migration; reverify the live remote route before
  later publication rather than silently rewriting repository configuration.
- **Physical-owner decision:** move the Step `00a` job, validator, and direct
  validator test once to the frozen `construct_STAR_index` source/test homes,
  and move owner-specific mocked producer behavior out of the cross-owner SLURM
  suite. The job is a 100% rename, remains mode `0644`, 1,954 bytes, and retains
  SHA-256 `f27924e80fee3b8f207a41fd7af472897ad51f06aa2e4c670973eb51f25b5fcc`.
  The validator changes only its exact owner-relative route to the neutral
  validation-report file. No wrapper, compatibility copy, symlink, package
  marker, descriptor, schema, public import identity, or second owner was added.
- **Caller and provenance decision:** public Python, SLURM, validator-roster,
  and shared-loader inventories now use explicit path maps so mixed physical
  placement stays exhaustive without numeric inference or recursive runtime
  discovery. Make static/smoke and compile coverage name the final assets.
  Artifact implementation evidence intentionally changes only the producer path
  while preserving its status, evidence ID, Git commit projection, source hash,
  artifact identities, schemas, and ordering.
- **Preserved producer risks:** the job still executes implicitly, is submitted
  as a mode-`0644` scheduler input, resolves hardcoded Novogene inputs and
  `refs/` outputs from caller CWD, defaults to eight threads, reuses nonempty
  prepared references, creates directories before STAR, retains prepared state
  on STAR failure, and performs no final index validation or transaction. These
  are characterized current behaviors, not newly approved design choices.
- **Focused parity evidence:** the extended legacy-path direct validator suite
  reported `6 passed`, the extended legacy-path owner mocked-job suite reported
  `4 passed`, and the retained SLURM selection reported `4 passed, 108
  deselected`. At final paths the two owner suites reported `10 passed`; the
  complete affected selection covering owner tests, SLURM, public CLI, exact
  rosters, shared report loaders, artifact adapters, and coverage tooling
  reported `560 passed` in 63.68 seconds. These are local fixture/mock results.
- **Coverage measurement-before-update:** the first exact final-path
  `make python-coverage-measure` ran all 1,079 collected tests and reported
  `1061 passed, 17 skipped, 1 failed`; the sole failing test was the repository
  documentation validator, which found six temporary migration-caused stale
  links plus the nine inherited authorized `UNREFINED` locations. A separately
  reviewed serial coverage-only run deselected exactly that documentation test,
  then measured the final validator at the frozen `165/189` lines and `42/60`
  branches with unchanged global `9343/11506` lines and `3281/4698` branches
  (`0.812011` and `0.698382`) across 31 files. Only after inspection was the
  tracked snapshot updated through `make python-coverage-baseline-update`; the
  subsequent exact baseline check passed with `1061 passed, 17 skipped,
  1 deselected`. The source boundary is now stable `scripts` plus `src/norad`.
- **Parallel-coverage risk:** a parallel covered lane emitted the known
  no-data-collected/combine warning. It was not accepted as coverage evidence;
  only the clean serial measurement and baseline check above support the
  recorded metrics.
- **Canonical-gate evidence:** the default sandbox attempt passed static
  preflight but guarded R stopped before meaningful R validation when
  Bioconductor DNS resolution was unavailable; it also exposed an inherited
  stray `macos` missing-`DESCRIPTION` warning. No dependency was installed,
  restored, deleted, or repaired. The required network-enabled retry passed
  static in 0.111 seconds, shell contracts in 40.606 seconds, guarded R in
  154.666 seconds, and report runtime in 131.658 seconds. Its Python lane
  reported `1061 passed, 17 skipped, 1 failed` solely for the same pre-close
  documentation finding set. The complete gate therefore ran but is
  expected-only nonpassing; it is not called a passing gate.
- **Documentation and topology decision:** repair every active job, validator,
  direct-test, command, inventory, coverage, ownership, roadmap, handoff, and
  lifecycle route; add one adjacent owner README; and correct the stale current-
  architecture reverse-dependency statement. The semantic DAG and public data
  flow did not change, so no diagram mutation is justified. Historical task and
  audit references retain legacy paths as dated evidence rather than supported
  commands.
- **Evidence ceiling:** this migration establishes implemented-local and
  locally fixture-tested ownership plus successful local guarded-R/report
  runtime lanes. It supplies no SLURM scheduler run, production data execution,
  cluster proof, completed scientific review, or biological-readiness evidence.
- **Documentation-close validation:** the first post-move documentation check
  exposed one lifecycle backlink still targeting the former `IN_PROGRESS` card
  plus the nine inherited `UNREFINED` findings. The backlink was repaired to the
  completed card without changing review meaning. The repeated exact checker
  then reported only the same nine `invalid card location` findings and no
  migration-caused path, anchor, lifecycle, or ownership error. This remains an
  expected-only nonpassing documentation ceiling, not a passing gate.

## 2026-08-02T20:32:00-0400 — MIG-03C JIT unit defined

- **Git and predecessor:** inspected clean campaign tip
  `1b82e4f04b926ac12e6306e40d03fee7840f3fa6` and proved local/upstream equality
  `0 0`. Recent history is linear through separate `MIG-03B` executable and
  documentation commits; no merge/rebase/cherry-pick/revert marker, index lock,
  recovery state, untracked file, or overlapping mutable lane was present.
- **Selection decision:** the live semantic map exposes two currently eligible
  typed-external-input roots, `convert_GTF_to_BED12` and
  `construct_FASTA_sidecars`. Select only `convert_GTF_to_BED12`: its validator
  imports only its same-owner producer plus the already migrated neutral report
  owner. The sidecar validator additionally imports the still-flat cross-cutting
  reference-provenance parser owner. The selected unit is therefore the smaller
  dependency-safe surface; historical aliases and filenames did not determine
  order. The sidecar owner remains uninspected beyond this bounded comparison.
- **Frozen native surface:** producer `scripts/gtf_to_bed12.py` is mode `0755`,
  10,613 bytes, SHA-256
  `5c69dabba9139598a9c67331b3200b8db8a29793334ff80f19850eb37ad57a04`;
  validator `scripts/validate_step_00b_bed12.py` is mode `0644`, 8,953 bytes,
  SHA-256 `e7f2caac22bf461374e23c18dd3a92c9c61456422b0fcf960b52aa7b7076d97d`;
  job `jobs/step_00b_gtf_to_bed12.slurm` is mode `0755`, 3,119 bytes, SHA-256
  `7eb6b3f904daa7ec6cb74f7a55377d0be1aa485b2c80cdd1464d025f9129414f`.
  The two mode-`0644` direct tests and owner-specific mocked-job case are the
  initial mirrored-test surface.
- **Direct graph:** the scheduler names the producer; the validator imports the
  producer's normalization logic; artifact implementation evidence names and
  hashes the producer. Exact public-CLI, SLURM, validator-roster, shared-loader,
  Make, literal-expansion, coverage, runbook, troubleshooting, inventory, and
  contract consumers name one or more legacy paths. No config, public schema,
  report template, or scientific consumer names a source path.
- **Wrapper decision:** all named path callers are repository-owned and can move
  atomically with the three assets. A legacy wrapper, re-export, package marker,
  symlink, compatibility copy, or global path mutation is not justified. The
  scheduler's delegated argument and artifact evidence intentionally transition
  to the final producer path; public BED12 and validation artifact identities do
  not change.
- **Coverage boundary:** stable source roots already include `src/norad`.
  Tracked producer coverage is `151/167` lines and `44/56` branches; tracked
  validator coverage is `127/140` lines and `29/36` branches. Global baseline is
  `9343/11506` lines and `3281/4698` branches. Final-path measurement must be
  inspected before moving both rows and the producer's required-subprocess
  identity through the reviewed update command.
- **Risk boundary:** preserve converter warning/skip, deterministic bytes,
  immediate write, output-parent creation, and silent replacement; validator
  producer-coupled agreement and neutral publication faults; and scheduler
  implicit execution, submit-directory requirement, directory timing, duplicate
  sorting, redirect truncation, nontransactional intermediate/final residue,
  field-count diagnostics, module/child failures, and exact modes/directives.
  Reviews must identify any missing old/new oracle before mutation.
- **Review and evidence boundary:** create only `MIG-03C` and dedicated
  `REVIEW-ARCH-03C`, `REVIEW-REL-03C`, and `REVIEW-UX-03C` cards. All remain
  unselected in `TODO`. This is documentation-only behavior/architecture
  planning; no computational test ran and no executable, runtime, scheduler,
  production, scientific-review, or biological evidence was created.

## 2026-08-02T20:37:08-0400 — REVIEW-ARCH-03C selected

- **Selection:** move only `REVIEW-ARCH-03C` from `TODO` to `IN_PROGRESS` and
  repair its dependency/status links after JIT-definition checkpoint `44e3393`
  was clean, published, and local/upstream-equal. `REVIEW-REL-03C`,
  `REVIEW-UX-03C`, and `MIG-03C` remain unselected in `TODO`.
- **Review boundary:** this begins one read-only independent-in-time
  adversarial pass over final-owner placement, sibling producer import,
  scheduler delegation, path-aware caller/test ownership, artifact evidence,
  wrapper necessity, atomic cutover, and rollback. The same campaign agent
  performs the pass, so independent authorship is not claimed. No executable or
  test mutation and no computational, runtime, scheduler, production,
  scientific-review, or biological evidence is authorized by this selection.

## 2026-08-02T20:39:37-0400 — REVIEW-ARCH-03C completed

- **High finding — sibling import under exact-file tests:** production
  `validate_step_00b_bed12.py` correctly imports its same-owner producer by the
  existing `gtf_to_bed12` identity when invoked as a script. The shared loader
  matrix currently exact-loads moved validators but has no corresponding final-
  path producer binding. After movement it could fail, import the wrong cache,
  or tempt global `sys.path` mutation. Preserve the production import; make the
  test-owned loader exact-load and path-validate the final sibling producer,
  reject a foreign cached module, preserve `sys.path`, and copy both sibling
  files into final-layout missing/corrupt-neutral-owner fixtures.
- **Medium finding — job/producer atomicity:** the scheduler must move with the
  producer and validator because its embedded child argument changes to the
  final path. Freeze the original job hash for rollback and require a diff that
  changes only that delegated path; do not demand an impossible final job hash.
  The producer remains byte-identical, so its frozen hash remains the artifact-
  implementation evidence invariant.
- **Medium finding — mixed-layout ownership:** keep explicit maps keyed by the
  existing public basename or semantic ID in public Python, SLURM, validator,
  loader, coverage, and artifact consumers. Each must prove every actual path
  exists once; recursive discovery, alias-derived placement, and relaxed flat-
  root equality are rejected. Move Step `00b` mocked behavior/fakes to the
  mirrored owner while keeping cross-owner directives/modes/rosters independent.
- **Accepted architecture:** `convert_GTF_to_BED12` is a typed-external-input DAG
  root. Its producer-validator dependency remains inside one final owner, its
  neutral report dependency remains exact-file and cross-cutting, all path
  callers can cut over atomically, and no wrapper/package/descriptor/schema or
  new neutral extraction is required. Reverse rollback is documentation close,
  caller/job/validator cutover, then the move; repository history, never a
  duplicate copy, performs restoration.
- **Topology and evidence boundary:** public artifact flow and the semantic DAG
  are unchanged, so no diagram edit is warranted. This separate committed-time
  pass was performed by the same campaign agent; independent authorship is not
  claimed. Corrections are planning documentation only. No executable/test
  mutation or computational, runtime, scheduler, production, scientific-review,
  or biological evidence was created.

## 2026-08-02T20:41:49-0400 — REVIEW-REL-03C selected

- **Selection:** move only `REVIEW-REL-03C` to `IN_PROGRESS` and repair its
  dependency/status links after architecture checkpoint `aed342d` was clean,
  published, and local/upstream-equal. `REVIEW-UX-03C` and `MIG-03C` remain
  unselected in `TODO`.
- **Review boundary:** this begins one read-only independent-in-time
  adversarial pass over converter writes/replacement, validator coupling and
  publication, scheduler side effects/failures/residue, artifact evidence,
  coverage rename, and rollback. The same campaign agent performs the pass, so
  independent authorship is not claimed. Executable/test mutation and
  computational, runtime, scheduler, production, scientific-review, and
  biological evidence remain out of scope.

## 2026-08-02T20:44:16-0400 — REVIEW-REL-03C completed

- **High finding — reused-state scheduler test masks residue:** the current
  Step `00b` case runs failure variants after a successful invocation in one
  fixture. Preexisting intermediate/final files and directories prevent exact
  claims about each failure's timing and residue. Build fresh owner-local
  scenarios for success, missing submit directory, colliding output paths,
  missing GTF, nonexecutable Python, module failure, converter failure, bedtools
  failure, and malformed sorted output; run the identical matrix old and new.
- **Characterized scheduler defects:** bedtools output redirection can create or
  truncate the final BED before bedtools returns success, leaving the
  intermediate plus an empty/partial final on failure. A bad-field final remains
  published, and awk executes its `END` block so stdout can contain both the
  error and `BED12 field-count check passed` before nonzero exit. Preserve and
  assert these states; do not repair, normalize, or call them target contracts.
- **High finding — validator journey gap:** the direct suite forces repository
  CWD and does not compare repeat publication streams/bytes. Add one full
  non-repository-CWD dry-run and execute/repeat journey with identical absolute
  BED/GTF/output paths before and after movement, proving exact stdout/stderr,
  exit, deterministic five-row bytes, no dry-run output, stable replacement,
  and no invocation-directory residue.
- **Producer and publication disposition:** the eleven direct producer tests and
  public CLI matrix already cover conversion rules, warnings, failures,
  arbitrary CWD, direct-help mode, and silent declared-output replacement.
  Neutral publisher tests retain stable-input, same-size/restored-mtime,
  collision, rollback, interruption, late-foreign, cleanup, descriptor, residue,
  and lock findings. Producer-coupled GTF agreement remains a characterized
  validation limitation and is not redesigned by this move.
- **Coverage and provenance:** final-path measurement must retain producer
  `151/167` lines and `44/56` branches and validator `127/140` lines and `29/36`
  branches or improve only through reviewed parity tests, while global rates do
  not regress. Move the required-subprocess producer identity and both baseline
  rows only after inspection. Assert final producer path and unchanged SHA-256
  in artifact implementation evidence; no artifact schema or identity changes.
- **Independence and evidence boundary:** this was a separate committed-time
  adversarial pass by the same campaign agent; independent authorship is not
  claimed. Corrections affect planning documentation only. No executable/test
  file changed and no computational, runtime, scheduler, production,
  scientific-review, or biological evidence was created.

## 2026-08-02T20:47:31-0400 — REVIEW-UX-03C selected

- **Selection:** move only `REVIEW-UX-03C` to `IN_PROGRESS` and repair its
  dependency/status links after reliability checkpoint `f12bc8b` was clean,
  published, and local/upstream-equal. `MIG-03C` remains unselected in `TODO`.
- **Review boundary:** this begins the final read-only independent-in-time pass
  over executable producer and explicit-interpreter validator journeys,
  scheduler submission/CWD/override guidance, Make/coverage paths, diagnostics,
  provenance, runbook/troubleshooting commands, owner findability, links, and
  rollback. The same campaign agent performs the pass, so independent authorship
  is not claimed; executable/test mutation and computational, runtime,
  scheduler, production, scientific-review, and biological evidence remain out
  of scope.

## 2026-08-02T20:50:49-0400 — REVIEW-UX-03C completed

- **High finding — bare paths are not usable final commands:** replace the
  runbook's bare producer and job listings with complete final-path commands.
  Distinguish repository-root direct and exact-interpreter producer use from
  arbitrary-CWD absolute-path use; keep the validator interpreter-only. The
  owner README must preserve the same distinctions and name silent declared-
  output replacement, diagnostics, artifact expectations, rollback, and the
  local-only evidence ceiling.
- **High finding — scheduler CWD and execution must be explicit:** the supported
  command is `cd <checkout>` followed by `sbatch` of the exact final job path.
  This preserves required `SLURM_SUBMIT_DIR`, implicit execution with no dry-run,
  four environment overrides, and characterized nontransactional intermediate/
  final residue. An alias or bare path would conceal rather than solve those
  conditions.
- **Medium finding — flat wildcard loses the moved job:** add the exact final job
  to `validation-static` and `smoke` shell-syntax commands and their literal Make
  oracle after it leaves `jobs/*.slurm`. Existing `compileall` roots already
  cover `src/norad`; move the `shell-test` path and give one focused command for
  producer, validator, and owner-local mocked-job suites.
- **Findability and recovery disposition:** add one concise owner README linking
  contract, runbook, and troubleshooting; record final paths, invocation forms,
  provenance transition, diagnostics, recovery, next safe validation action,
  no-wrapper/package/descriptor boundary, and evidence ceiling. Update Step
  `00b` troubleshooting to name the exact final producer. No compatibility
  alias is needed because every known caller is repository-owned and movable.
- **Independence and evidence boundary:** this separate committed-time pass was
  performed by the same campaign agent; independent authorship is not claimed.
  Corrections affect planning documentation only. No executable/test mutation
  or computational, runtime, scheduler, production, scientific-review, or
  biological evidence was created.

## 2026-08-02T20:53:11-0400 — MIG-03C selected

- **Selection:** move only `MIG-03C` to `IN_PROGRESS` after usability-review
  checkpoint `784073e` was clean, published, and local/upstream-equal. Its three
  dedicated reviews are complete; no later migration card or review is created
  or selected.
- **Boundary and next action:** this status-only checkpoint authorizes task-
  specific read-only execution planning. Publish and prove it upstream-equal
  before running old-path computational baselines. No executable/test file,
  production data, scheduler state, dependency, runtime artifact, scientific-
  review state, or biological evidence changes here.

## 2026-08-02T21:09:37-0400 — MIG-03C task-specific plan and old-path baseline complete

- **Git and scope decision:** planning ran on clean, published, upstream-equal
  selection tip `28acbbb871fd77815ea03d1631ff7462dbe50c2f`, with no recovery
  state or mutable lane overlap. The exact write set is one producer, its
  same-owner validator, its scheduler asset, two moved direct tests, one new
  owner-local scheduler test, and only their named Make, artifact, public-CLI,
  SLURM, validator, loader, coverage, and literal-fixture callers. No wrapper,
  package marker, descriptor, schema, `.coveragerc`, unrelated owner, or
  documentation belongs in the executable commit.
- **Frozen source evidence:** producer mode `0755`, SHA-256
  `5c69dabba9139598a9c67331b3200b8db8a29793334ff80f19850eb37ad57a04`,
  341 lines; validator mode `0644`, SHA-256
  `e7f2caac22bf461374e23c18dd3a92c9c61456422b0fcf960b52aa7b7076d97d`,
  226 lines; job mode `0755`, SHA-256
  `7eb6b3f904daa7ec6cb74f7a55377d0be1aa485b2c80cdd1464d025f9129414f`,
  121 lines. The producer bytes/hash remain invariant; the job hash is rollback
  evidence because its delegated path intentionally changes.
- **Existing-suite baseline:** the two direct modules plus public CLI, SLURM,
  validation roster/report, artifact-adapter, and coverage suites passed `566`
  tests in `62.90s`. This is local fixture/mock evidence only.
- **Expanded old-path baseline:** an out-of-tree harness initially failed only
  during collection because its fallback path expression was evaluated despite
  an explicit environment path; no repository file or test executed. After the
  harness-only initialization fix, all `11` cases passed in `1.81s`: direct and
  exact-interpreter producer parity, full non-repository-CWD validator dry-run/
  execute/repeat parity, and fresh success, missing-submit, colliding-output,
  missing-GTF, nonexecutable-Python, module-failure, converter-failure,
  bedtools-failure, and bad-field scheduler fixtures.
- **Failure/residue decision:** preserve exact preflight-before-directory/tool
  effects, module-load directory residue, converter-failure directories without
  outputs, bedtools-failure intermediate plus redirect-created empty final, and
  bad-field published bytes plus contradictory awk success stdout before exit
  `1`. These are characterized defects, not approved behavior or repair scope.
- **Coverage-gate result:** unmodified `make python-coverage-check` ran all
  `1,079` tests and ended at exactly `1,061` passed, `17` skipped, and the one
  expected documentation-validator failure caused by the nine authorized
  `UNREFINED` locations, so Make correctly stopped before export. To measure
  without changing the repository or calling that gate passing, the same test
  body was rerun under one out-of-tree strict expected-failure marker: `1,061`
  passed, `17` skipped, `1` xfailed in `264.15s`; coverage comparison passed.
- **Coverage baseline:** producer remains `151/167` lines and `44/56` branches;
  validator remains `127/140` and `29/36`. Global current measurement is
  `9472/11506` lines and `3353/4698` branches (`0.823223`/`0.713708`), above the
  committed baseline `9343/11506` and `3281/4698` (`0.812011`/`0.698382`). Do
  not update tracked rows until final-path measurement is reviewed.
- **Execution and handoff decision:** no executable/test mutation has begun.
  Publish and prove this documentation checkpoint equal, then the next agent
  begins only the exact atomic cutover frozen in `MIG-03C`; final-path parity,
  coverage, and the complete applicable gate precede the executable commit.
  No dependency, cluster, production, scientific-review, or biological claim
  was created.

## 2026-08-02T22:07:41-0400 — MIG-03C documentation and lifecycle close

- **Checkpoint and authority:** before documentation mutation, live Git
  verification found branch
  `codex/mig-03a-extract-validation-report-library` clean including untracked
  files at `e19f28162a84f674cf910b38665e3c8ee85f0c45`, with no index lock, merge,
  rebase, cherry-pick, revert, bisect, sequencer, or other recovery marker. A
  network-enabled fetch and `ls-remote` proved local `HEAD`, configured
  upstream, and the live GitHub ref equal at that SHA with ahead/behind `0/0`.
- **Delivered owner and provenance decision:** the mode-`0755` producer is
  byte-identical at its final path with SHA-256
  `5c69dabba9139598a9c67331b3200b8db8a29793334ff80f19850eb37ad57a04`.
  The mode-`0644` validator changed only its neutral-library owner-relative
  lookup and retains the sibling producer import. The mode-`0755` job changed
  only its delegated producer path and has final SHA-256
  `2b902dd60d9f027eca912f5c50598963c728114facfa9e37157e25cd3a1ff381`.
  Artifact identity, BED12/validation contracts, scheduler semantics, and
  producer implementation hash remain unchanged; no wrapper, compatibility
  copy, package marker, descriptor, schema, or stage-to-stage import was added.
- **Documentation-impact decision:** add the adjacent owner README; repair the
  owner contract, functional inventory, coverage route, documentation ownership
  map, runbook, troubleshooting path, current architecture, roadmap, handoff,
  card lifecycle, review backlink, and this dated record. Exact pre-close
  validation found ten migration-caused broken links: five in the contract and
  five in the inventory. The source move changes mixed physical placement but
  not the semantic DAG or public artifact flow, so neither canonical diagram is
  changed.
- **Operator and recovery decision:** repository-root documentation now gives
  complete direct and exact-interpreter producer commands, explicit-interpreter
  validator dry-run/execute commands, the three-suite focused-test command, and
  `cd <checkout>` before the exact final `sbatch` path. Arbitrary-CWD use
  requires an absolute checkout path or an explicit `cd`. Submission executes
  implicitly, has no dry run, retains all four overrides, and publishes
  nontransactionally. Silent producer replacement, failure-created directories,
  intermediate/final residue, and contradictory bad-field stdout remain
  characterized defects; preserve ambiguous artifacts and logs rather than
  treating characterization as cleanup authority.
- **Evidence decision:** reviewed final-path coverage retained producer
  `151/167` lines and `44/56` branches and validator `127/140` lines and `29/36`
  branches; global measurement was `9474/11506` and `3354/4698`
  (`0.823396`/`0.713921`), above the committed floor. Focused final-path suites
  passed. The aggregate gate was not fully green because documentation
  validation still contained the ten migration links plus nine inherited
  authorized `UNREFINED` locations; do not promote that result to a passing
  gate. No runtime, scheduler, production, scientific-review, or biological
  evidence was created.
- **Card-boundary gate:** after the documentation edits, `git diff --check`
  passed and the exact repository documentation validator reported only the
  same nine inherited `invalid card location` findings under
  `docs/tasks/UNREFINED/`, with no migration-caused finding. This is an
  expected-only nonpassing documentation result, not a pass. The complete
  predecessor-to-final diff is documentation-only/non-consuming, so Python,
  shell, R, report-runtime, and cluster suites are not applicable and were not
  rerun.
- **Lifecycle and slice policy:** move `MIG-03C` to `COMPLETED`, repair every
  inbound lifecycle link, and publish this documentation close separately from
  executable checkpoint `e19f281`. Keep future slices explicitly small; use
  only the minimum safety check at a slice boundary, batch migration links and
  other impact-directed documentation into the card-boundary close, and run the
  complete applicable gate only at that boundary. No later card or owner is
  preloaded. Select one next dependency-valid unit from live DAG evidence only
  after this close is clean, published, and upstream-equal.

## 2026-08-02T22:19:35-0400 — MIG-03D JIT unit defined

- **Git and predecessor:** inspected clean campaign tip
  `f9d638199c6d60cbe81c992fde6a1090cb364302` and proved configured-upstream and
  live-remote equality with ahead/behind `0 0`. Recent history is linear through
  the separate `MIG-03C` executable and documentation commits; no merge, rebase,
  cherry-pick, revert, bisect, sequencer, index lock, recovery state, untracked
  file, or overlapping mutable lane was present.
- **Selection decision:** the live semantic map exposes two dependency-valid
  candidates. Select only `align_RNA_reads_with_STAR`: its sole hard predecessor
  `construct_STAR_index` is migrated; its three native assets total 17,454
  bytes and 538 lines; and its validator loads only the migrated neutral
  validation-report owner. `construct_FASTA_sidecars` remains eligible but its
  three assets total 24,954 bytes and 827 lines and its validator still imports
  the separate flat `reference_provenance` implementation. The selected unit is
  therefore the smaller, less-coupled live surface; historical aliases did not
  determine order and the unselected owner was not preloaded further.
- **Frozen native surface:** producer `scripts/step_01_star_align.sh` is mode
  `0755`, 5,600 bytes, 195 lines, SHA-256
  `25e2120ca9843ea25f2e1f3b4084aced6261976ab46f7cb25c33d7911f82d0ba`;
  validator `scripts/validate_step_01_star_alignment.py` is mode `0644`, 8,506
  bytes, 229 lines, SHA-256
  `40b878493949b3d095379aae1413999f1cbfca5954c31299c2a1a34ba89d2aed`;
  job `jobs/step_01_star_align.slurm` is intentionally mode `0644`, 3,348
  bytes, 114 lines, SHA-256
  `1b75457580d294a7a4e06017c80aea36b3a9abd68794b8047f47172be3706aa4`.
  Direct shell and Python tests are the initial mirrored-test surface; Step
  `01`-specific setup and default-fixture behavior also live in the independent
  scheduler suite and require an architecture disposition before extraction.
- **Direct graph and path changes:** the scheduler delegates to the producer;
  the validator exact-loads `src/norad/libraries/validation_report.py`; and
  artifact implementation evidence names and hashes the producer. Final
  placement necessarily changes the producer's displayed usage path, the
  validator's owner-relative neutral-library lookup, the job's child path, and
  explicit public-CLI, SLURM, validator-roster, shared-loader, Make, literal-
  expansion, coverage, artifact, test, runbook, inventory, and contract path
  consumers. The contract's statement that Step `01` still imports Step `00a`
  is stale; batch that repair with all other migration links at card close.
- **Wrapper and topology decision:** every named path caller is repository-
  owned and can move atomically with the three assets. No legacy wrapper,
  re-export, package marker, symlink, compatibility copy, global path mutation,
  descriptor, or schema is justified. The public semantic DAG and artifact flow
  do not change, so no diagram edit is warranted unless final inspection finds
  contrary evidence. The old producer and job hashes are rollback evidence
  because their self/delegation path text must change; the final producer path
  and reviewed final hash replace only implementation provenance for Step `01`.
- **Coverage and Make boundary:** the validator baseline is `125/140` covered
  lines and `34/44` branches; the committed global floor is `9343/11506` lines
  and `3281/4698` branches. Stable roots already include `src/norad`; inspect a
  final-path measurement before renaming the row. Because both shell assets
  leave flat wildcards, exact final producer and job paths must enter
  `validation-static`, `smoke`, and their literal Make oracle; direct shell and
  validator test recipe paths must move without discovery or inventory
  weakening.
- **Risk boundary:** preserve producer dry-run directory creation, direct final-
  path STAR writes, suffix-only compression choice, lack of sample-ID/content
  validation, lack of receipt/lock/staging/no-clobber/post-validation, and child
  failure residue. Preserve scheduler caller-CWD dependence, mutable placeholder
  FASTQ/index creation in default dry-run, execution refusal with those defaults,
  strict STAR module load, allocation-derived threads, TMPDIR mutation, mode
  `0644`, and delegate-only output validation. Preserve validator structural-
  only evidence, exact five checks, deterministic report/publication behavior,
  and inherited neutral-publisher defects. Reviews must identify any missing
  old/new oracle; none of these defects is fixed or blessed by relocation.
- **Review, validation, and evidence boundary:** create only `MIG-03D` and
  dedicated `REVIEW-ARCH-03D`, `REVIEW-REL-03D`, and `REVIEW-UX-03D` cards. All
  remain unselected in `TODO`. This definition is documentation-only and uses
  only documentation validation at its boundary; no computational test, real
  STAR run, scheduler submission, dependency action, runtime, production,
  scientific-review, or biological evidence was created. Full applicable
  validation and batched migration documentation remain card-boundary work.

## 2026-08-02T22:25:00-0400 — REVIEW-ARCH-03D selected

- **Selection:** move only `REVIEW-ARCH-03D` to `IN_PROGRESS` and repair its
  dependency/status links after JIT-definition checkpoint `5ef6c6a` was clean,
  published, and local/upstream-equal. `REVIEW-REL-03D`, `REVIEW-UX-03D`, and
  `MIG-03D` remain unselected in `TODO`.
- **Review boundary:** this begins one read-only independent-in-time
  adversarial pass over DAG eligibility, final-owner placement, exact path
  changes, job delegation, neutral-library loading, artifact provenance,
  explicit caller inventories, test ownership, wrapper necessity, atomicity,
  and rollback. The same campaign agent performs the pass, so independent
  authorship is not claimed. Executable/test mutation and computational,
  runtime, scheduler, production, scientific-review, and biological evidence
  remain out of scope.

## 2026-08-02T22:32:00-0400 — REVIEW-ARCH-03D completed

- **High finding — flat shell inventory cannot represent the final owner:**
  `test_public_cli_contracts.py` currently derives every shell path from
  `scripts/`, unlike its explicit Python path map. Add an explicit
  `SHELL_ENTRYPOINT_PATHS` map, derive the basename roster from its keys, route
  every shell CLI/mode journey through a path helper, and compare the live flat
  root only with entries whose declared parent remains `scripts/`. Do not use
  recursive discovery or weaken exact inventory equality.
- **High finding — shared test loader assumes flat module import:** the shared
  validation-report suite exact-loads the two migrated validators but imports
  all others by module name from `scripts/`. Reuse its existing path-validating
  exact-file helper for every declared non-flat validator, including the final
  Step `01` path; retain module-name import for still-flat validators, foreign-
  cache rejection, and `sys.path` preservation. No package identity, global
  path mutation, Step-specific loader, or new framework is required.
- **Medium finding — scheduler-specific evidence remains independently owned:**
  the Step `01` fixture adapter is required by every parametrized delegated-job
  assertion, and its default-placeholder test reuses the same central harness.
  Keep both in the independent cross-wrapper suite and update only its explicit
  job/delegation paths. Move the direct shell and validator suites to the owner;
  do not duplicate the scheduler harness or import one test module from another.
- **Atomicity, provenance, and rollback:** one executable/test commit moves all
  three native assets and two direct tests, changes production text only in the
  producer usage self-path, validator neutral-owner depth, and job child path,
  and cuts over explicit Make, CLI, SLURM, roster, loader, artifact, coverage,
  and test callers. Old producer/job hashes are rollback evidence because path
  text changes; assert the reviewed final producer path/hash for artifact
  provenance. Rollback reverts the atomic caller/move commit after reverting the
  later documentation close; repository history, not a duplicate, restores the
  legacy layout.
- **Accepted architecture and evidence boundary:** the migrated STAR-index
  predecessor, explicit FASTQ inputs, final homes, direct-cutover/no-wrapper
  decision, one-owner invariant, nonexecutable job mode, public artifact
  identities, and no-package/descriptor/schema boundary pass. The DAG and public
  artifact flow are unchanged, so diagrams remain untouched. This separate
  committed-time pass was performed by the same campaign agent; independent
  authorship is not claimed. No executable/test mutation or computational,
  runtime, scheduler, production, scientific-review, or biological evidence was
  created.

## 2026-08-02T22:36:00-0400 — REVIEW-REL-03D selected

- **Selection:** move only `REVIEW-REL-03D` to `IN_PROGRESS` and repair its
  dependency/status links after architecture checkpoint `cd3f3d4` was clean,
  published, and local/upstream-equal. `REVIEW-UX-03D` and `MIG-03D` remain
  unselected in `TODO`.
- **Review boundary:** this begins one read-only independent-in-time
  adversarial pass over producer dry-run/execute/failure residue, validator
  parsing/publication/loader faults, scheduler caller-CWD and mutable-fixture
  states, artifact provenance, coverage rename, modes/hashes, and reverse
  rollback. The same campaign agent performs the pass, so independent
  authorship is not claimed. Executable/test mutation and computational,
  runtime, scheduler, production, scientific-review, and biological evidence
  remain out of scope.

## 2026-08-02T22:44:00-0400 — REVIEW-REL-03D completed

- **High finding — producer child-failure residue lacks a direct oracle:** the
  current shell suite proves successful fake-STAR execution but its fake cannot
  fail. Add one controlled child exit to the moved direct suite and run the same
  case at the frozen old and final paths, asserting the exact exit, recorded
  invocation, and retained output directory. The producer's direct-final writes
  and absence of post-execution validation remain defects; the fixture must not
  synthesize output artifacts or imply real STAR evidence.
- **High finding — validator relocation needs a complete arbitrary-CWD
  journey:** generic CLI coverage proves help/parse failure from another CWD,
  while the direct suite runs successful publication only from repository root.
  Add one absolute-input non-repository-CWD dry-run, execute, and repeat journey
  with exact stdout/stderr and exit parity, no dry-run output, deterministic
  five-row bytes, stable replacement, and no invocation-directory residue.
- **Existing fault ownership:** the cross-wrapper scheduler matrix already
  freezes mode `0644`, directives, invalid `EXECUTE`, strict STAR module
  failure, child exit, caller-CWD failure, delegate-only output checking, and
  default placeholder creation. Keep it central and run it through the final
  explicit paths. The neutral validation-report matrix continues owning exact
  loader identity, snapshots, input recheck, locks, collisions, rollback,
  interruption, cleanup, and characterized same-size/restored-mtime,
  late-foreign-final, and check-reordering gaps. Relocation neither repairs nor
  approves those behaviors.
- **Coverage, provenance, and evidence boundary:** move the validator's
  `125/140` line and `34/44` branch baseline row only after inspected final-path
  measurement and global non-regression. Assert Step `01` artifact evidence at
  the reviewed final producer path/hash without changing artifact IDs or
  schemas. This separate committed-time pass was performed by the same campaign
  agent; independent authorship is not claimed. No executable/test mutation or
  computational, real STAR, runtime, scheduler, production, scientific-review,
  or biological evidence was created.

## 2026-08-02T22:48:00-0400 — REVIEW-UX-03D selected

- **Selection:** move only `REVIEW-UX-03D` to `IN_PROGRESS` and repair its
  dependency/status links after reliability checkpoint `f11dc9f` was clean,
  published, and local/upstream-equal. `MIG-03D` remains unselected in `TODO`.
- **Review boundary:** this begins the final read-only independent-in-time pass
  over producer direct/interpreter and arbitrary-CWD journeys, validator
  invocation/publication, scheduler submission/CWD/default/override guidance,
  Make and focused-test commands, artifact provenance, diagnostics, owner
  findability, recovery, links, and evidence ceilings. The same campaign agent
  performs the pass, so independent authorship is not claimed; executable/test
  mutation and computational, runtime, scheduler, production, scientific-
  review, and biological evidence remain out of scope.

## 2026-08-02T22:56:00-0400 — REVIEW-UX-03D completed

- **High finding — bare paths are not supported final commands:** replace the
  Step `01` runbook's producer and job path labels with complete final-path
  commands. Distinguish repository-root direct and explicit-`bash` producer use
  from arbitrary-CWD absolute paths; keep the validator interpreter-only with
  dry-run and execute examples. The producer command includes every required
  argument and explicitly warns that its dry-run creates the output directory.
- **High finding — scheduler submission hides mutable defaults:** document
  `cd <checkout>` before exact final-path `sbatch` because the job delegates by
  caller CWD. `EXECUTE=0` is default but the default bindings create placeholder
  FASTQs and an index directory; `EXECUTE=1` refuses them. Real work supplies
  `SAMPLE_ID`, `R1_FASTQ`, `R2_FASTQ`, `STAR_INDEX`, and `OUTPUT_DIR`, while
  threads come from the allocation. Submission and mocked tests do not prove
  scheduler or cluster parity.
- **Medium finding — Make and focused commands must follow both shell moves:**
  add the exact final producer and job to `validation-static`, `smoke`, and the
  literal Make oracle after both leave flat wildcards. Move the direct shell and
  validator test recipe paths. Publish one focused block covering those moved
  suites plus the independent central scheduler module; do not replace exact
  paths with discovery.
- **Findability, diagnostics, and recovery:** add one concise owner README and
  update the Step `01` troubleshooting route during the batched documentation
  close. Name the BAM, three logs, splice-junction table, validation report,
  STAR-native and scheduler diagnostics, direct-final partial-output risk,
  preservation-first recovery, rollback, implementation provenance path/hash
  transition, next safe validation action, and local-only migration evidence
  ceiling. No alias, wrapper, package, descriptor, schema, transaction, or
  scientific-policy change is needed.
- **Independence and evidence boundary:** this separate committed-time pass was
  performed by the same campaign agent; independent authorship is not claimed.
  Corrections affect planning documentation only. No executable/test mutation
  or computational, real STAR, runtime, scheduler, production, scientific-
  review, or biological evidence was created.

## 2026-08-02T23:00:00-0400 — MIG-03D selected

- **Selection:** move only `MIG-03D` to `IN_PROGRESS` after usability-review
  checkpoint `7d31459` was clean, published, and local/upstream-equal. Its three
  dedicated reviews are complete; no later migration card or review is created
  or selected.
- **Boundary and next action:** this status-only checkpoint authorizes task-
  specific read-only execution planning and the exact old-path local fixture/
  mock baselines required by the reviewed card. Publish and prove it upstream-
  equal before those baselines. No executable/test file, real STAR process,
  production data, scheduler state, dependency, runtime artifact, scientific-
  review state, or biological evidence changes here.

## 2026-08-02T23:04:00-0400 — MIG-03D task-specific plan frozen

- **Git and scope:** planning began from clean, published, upstream-equal
  selection tip `d6abed12a303dabc9b8166c511969b87f8c41ff2`, with no recovery
  marker, index lock, untracked file, or mutable lane overlap. The executable
  commit is exactly fourteen tracked files: five moves and nine explicit caller/
  harness updates. Documentation remains a separate later card-boundary close.
- **Moves and production diff:** move the shell producer, Python validator, and
  nonexecutable SLURM job to
  `src/norad/stages/align_RNA_reads_with_STAR/`; move the direct shell and
  validator tests to the mirrored test home. Production text changes only the
  producer usage self-path, validator neutral-library owner depth, and job
  delegated producer path. Preserve modes `0755`, `0644`, and `0644`; add no
  legacy wrapper, duplicate, package marker, descriptor, or schema.
- **Caller and test cutover:** update only `Makefile`, artifact producer mapping
  and focused evidence assertion, explicit public-shell path inventory, SLURM
  job/delegation map, validator roster, shared non-flat validator exact-loader,
  coverage baseline row, and literal Make fixture. The two moved tests receive
  only required root/path corrections plus the reviewed controlled child-
  failure and arbitrary-CWD validator repeat cases. The central scheduler
  adapter/default-placeholder test remains independent and in place.
- **Baseline tranche:** after this planning checkpoint is published/equal, run
  syntax for the two shell assets; the current direct shell suite; direct
  validator, public CLI, SLURM, validation roster, shared publisher, artifact,
  and coverage-policy modules; and two temporary untracked-free parity probes
  for producer child-failure residue and validator non-repository-CWD dry-run/
  execute/repeat behavior. Record modes, hashes, counts, streams/exits,
  deterministic report hash, and residue without updating tracked coverage.
- **Validation boundary:** these are targeted old-path fixture/mock baselines,
  not the complete card gate. Run the complete applicable local gate once only
  after the final-path cutover, before the executable checkpoint commit. Do not
  run real STAR, submit a job, install/restore dependencies, touch production
  data, or claim runtime, scheduler, production, scientific-review, or
  biological evidence.

## 2026-08-02T23:10:00-0400 — MIG-03D old-path baseline captured

- **Published parent and clean scope:** the baseline began from clean,
  published, local/upstream-equal task-specific plan checkpoint `03cbc97`, with
  no untracked file, recovery marker, index lock, or mutable-lane collision. It
  changed no tracked executable/test file and did not preload another owner.
- **Targeted suites:** `bash -n` passed for the frozen producer and scheduler
  job; the direct shell suite passed all existing cases. The exact planned
  Python surface passed `555` tests in `62.65s`, covering the direct validator,
  public CLI, scheduler wrapper, validation roster, shared report publisher,
  artifact adapter, and coverage policy. This is not the complete card gate.
- **Reviewed missing oracles:** a temporary fake STAR returned `37`; the
  producer propagated `37`, invoked the child with the reviewed arguments,
  emitted no stderr, and retained an empty pre-created output directory. A
  temporary non-repository-CWD validator journey returned `0` for dry-run and
  two executions, wrote no dry-run report, then produced five all-pass rows
  with byte-identical SHA-256
  `13a6540f578ed55a7c2e5ba66346ec41df45e95df06e746b920cb31dcd5d3a94`;
  invocation-CWD and publisher residue were empty. These results characterize
  existing behavior without approving the residue or inherited publisher gaps.
- **Frozen rollback evidence:** producer mode/hash is `0755` /
  `25e2120ca9843ea25f2e1f3b4084aced6261976ab46f7cb25c33d7911f82d0ba`;
  validator `0644` /
  `40b878493949b3d095379aae1413999f1cbfca5954c31299c2a1a34ba89d2aed`;
  job `0644` /
  `1b75457580d294a7a4e06017c80aea36b3a9abd68794b8047f47172be3706aa4`;
  direct shell test `0755` /
  `f86f797b9d8a77437b92a1315c355f2f811ac4d09628c85e775846a2deb9f535`;
  and direct Python test `0644` /
  `2ec9ab15cc2da5f59582b71c778da2b2358a3aee9eb47f38ea353201c7def3c3`.
- **Evidence ceiling and next action:** no tracked coverage run, real STAR
  process, scheduler submission, dependency action, production data, cluster
  state, scientific review, or biological-readiness evidence was created. The
  committed coverage floor remains validator `125/140` lines and `34/44`
  branches and global `9343/11506` lines and `3281/4698` branches. Publish this
  documentation-only baseline checkpoint, prove live remote equality, then
  apply only the reviewed fourteen-file atomic cutover.

## 2026-08-02T23:24:00-0400 — MIG-03D executable cutover and documentation close

- **Published execution parent and atomic scope:** cutover began only after
  old-path baseline checkpoint `1ceeda0` was clean, published, and live-remote
  equal. Executable checkpoint
  `12f9be514e849ebf3d9b01cd2eabb65677e298c3` contains exactly the reviewed
  fourteen tracked files: three native-asset moves, two direct-test moves, and
  nine explicit caller/harness updates. It is published and upstream-equal.
- **Final owner and production changes:** the mode-`0755` producer now has
  SHA-256
  `718625e101a700b4da56b8e30249b1b42f8dea81546a763fc9db246be9a3edaf`;
  production logic changed only its displayed self-path. The mode-`0644`
  validator has SHA-256
  `6d33a05de2d802ffc7e80a5e744d597ef82d7aa11e784cc65257de2be187e4d7`
  after only the reviewed neutral-owner depth change. The intentionally
  mode-`0644` job has SHA-256
  `6e2af7994b36efe6c55f5799a8350e3530e699c7dc2e1570b76b4d2b02879900`
  after its child path and adjacent stale path comment changed; its original
  no-final-newline byte shape was restored before commit.
- **Caller, evidence, and test decisions:** Make static/smoke and direct-test
  recipes name the final assets; the literal expansion oracle matches. Public
  shell entry points now use an explicit basename/path map parallel to Python.
  The shared publisher suite exact-loads every declared non-flat validator and
  imports only still-flat validators. SLURM and validation rosters use final
  paths; the central Step `01` scheduler adapter/default-placeholder assertion
  remains independent. Artifact implementation evidence preserves identity and
  records the final producer path/hash. No wrapper, compatibility copy, package
  marker, descriptor, schema, or runtime discovery was added.
- **Final-path parity:** shell syntax and the owner shell suite passed,
  including exact fake-STAR exit `37`, invocation, empty retained output
  directory, and empty stderr. The direct/caller Python surface passed `556`
  tests in `62.76s`, including arbitrary-CWD validator dry-run, execute, repeat,
  deterministic five-row bytes, and empty invocation/publisher residue.
- **Coverage decision:** a completed final-path measurement retained validator
  coverage at `125/140` lines and `34/44` branches and measured global coverage
  at `9474/11506` lines and `3354/4698` branches
  (`0.823396`/`0.713921`). This exceeds the committed `9343/11506` and
  `3281/4698` rollback floor. Only the validator row moved to its lexically
  sorted final path; the standalone policy comparison passed and no coverage
  tool, policy, or configuration changed.
- **Aggregate-gate result:** the complete local gate was not fully green.
  Static preflight, shell contracts, guarded R, and pinned report runtime
  passed. Python coverage executed `1,073` passes and `17` skips before the
  repository documentation-validator test reported exactly ten MIG-03D stale
  links plus the nine inherited `UNREFINED` card-location findings. The ten
  migration links are batched into this documentation close; the nine inherited
  findings remain expected-only nonpassing evidence and are never called a
  passing gate.
- **Guarded-R environment decision:** the first sandboxed aggregate attempt
  stopped on unavailable Bioconductor DNS metadata after warning about the
  preserved ignored nested `macos` directory. The recorded
  `RENV_PATHS_LIBRARY` route reproduced that warning. A read-only network-
  metadata rerun then proved R `4.6.1`, Bioconductor `3.23`, synchronized renv
  state, required packages, and PDF output. No package was installed, restored,
  removed, or updated, and the ignored malformed-directory warning remains
  preserved recovery state.
- **Preserved risk boundary:** producer dry-run directory creation,
  direct-final writes, child-failure residue, suffix-only compression choice,
  and lack of sample/content validation, receipt, lock, staging, no-clobber,
  cleanup, and post-validation remain defects. Scheduler caller-CWD dependence,
  default placeholder mutation, default-execute refusal, strict STAR module,
  allocation threads, TMPDIR mutation, nonexecutable mode, and delegate-only
  validation remain defects. Validator evidence remains structural-only and
  inherited neutral-publisher gaps remain owned by their existing fault matrix.
  Relocation neither fixes nor blesses any of them.
- **Unpublished staging recovery:** an explicit `git add` path list included
  legacy paths already absent after `git mv`; Git rejected that add while the
  previously staged pure moves still formed local commit `7f963e3`. Before any
  push, that unpublished commit was immediately amended with all fourteen
  reviewed changes. The remote contains only atomic checkpoint `12f9be5`.
- **Documentation and lifecycle decision:** add the adjacent owner README;
  repair current contract, architecture, inventory, test-baseline,
  documentation-ownership, runbook, troubleshooting, roadmap, and handoff
  routes; move `MIG-03D` to `COMPLETED`; repair every inbound lifecycle link;
  and leave dated old-path evidence immutable. The public DAG and artifact flow
  did not change, so no diagram edit is warranted. Rollback reverts this
  documentation close before `12f9be5`; preserve runtime artifacts and use Git
  history rather than duplicate legacy files.
- **Evidence ceiling and continuation:** no real STAR process, scheduler
  submission, cluster/production input, scientific review, or biological-
  readiness evidence was created. Publish and prove this separate
  documentation/lifecycle checkpoint equal before selecting exactly one next
  dependency-valid owner; no future card is preloaded here.

## 2026-08-02T23:35:12-0400 — MIG-03E JIT unit defined

- **Git and predecessor:** selection began only after `MIG-03D`
  documentation/lifecycle checkpoint
  `5259acbf3b717487e78eecfd938cc793665673f8` was committed, published, clean,
  and proved equal across local `HEAD`, configured upstream, and the live remote
  branch. Recent history is linear; no merge, rebase, cherry-pick, revert,
  sequencer, index lock, recovery marker, untracked file, or overlapping mutable
  lane was present.
- **Selection decision:** the live semantic map exposes two data-DAG-eligible
  candidates. Select only `construct_FASTA_sidecars`. It has no hard stage
  predecessor, and no peer stage imports its implementation. Its three native
  assets total `24,954` bytes and `827` lines. Do not select the slightly smaller
  `construct_canonical_BAM` surface (`23,743` bytes, `746` lines): the Step `04`
  and Step `05` validators still import helpers directly from its stage-named
  validator, so moving it now would retain a prohibited peer-implementation
  dependency. Historical aliases and raw file size did not override dependency
  direction, and the unselected owner was not carded.
- **Frozen native surface:** producer
  `scripts/step_00c_prepare_gatk_reference.sh` is mode `0755`, `14,477` bytes,
  `515` lines, SHA-256
  `f041c55a0e9a3b36c14dcc9b929cfa56190e1c00d23a5a62fa72ac3669f0c478`;
  validator `scripts/validate_step_00c_reference_sidecars.py` is mode `0644`,
  `5,945` bytes, `161` lines, SHA-256
  `5aa6358412a56b5ddb8ce963a6d7431cfb07c1bbd9fbb37c8237fc3cbebe15fd`;
  and job `jobs/step_00c_prepare_gatk_reference.slurm` is mode `0755`, `4,532`
  bytes, `151` lines, SHA-256
  `78b00abb7751e78264bae30d6b3dbfb7792ca5532850f192b1b2098cbf8e85d0`.
  Direct shell and validator tests are the mirrored-test candidates; Step `00c`
  scheduler behavior remains in the independent parametrized wrapper suite.
- **Import boundary:** the validator already exact-loads the migrated neutral
  validation-report owner but ambient-imports the flat public
  `scripts/reference_provenance.py`. This unit neither moves nor edits that
  separate public CLI/implementation, its direct tests, coverage row, or its
  Step `05` consumer. The proposed final validator instead uses a private
  caller-local exact-file bridge back to the existing path, with exact cache
  ownership, wrong/partial-state rejection, owned-partial cleanup, foreign-
  state preservation, explicit failure diagnostics, and unchanged `sys.path`.
  Architecture review must reject the unit if that bridge cannot remain private,
  bounded, and reversible without approving the deferred neutral extraction.
- **Direct graph and path changes:** the scheduler delegates to the producer;
  the validator depends on the validation-report and reference-provenance
  implementations; and artifact implementation evidence names and hashes the
  producer. Final placement necessarily changes the producer's displayed usage
  path, both validator owner-relative paths/import mechanics, the job's child
  path, and explicit public-CLI, SLURM, validator-roster, shared-loader, Make,
  literal-expansion, coverage, artifact, test, runbook, inventory, and contract
  path consumers. Batch current documentation/path repairs at card close.
- **Wrapper and topology decision:** every named public path caller is
  repository-owned and can move atomically with the three native assets. No
  legacy wrapper, re-export, package marker, symlink, compatibility copy,
  descriptor, schema, or global path mutation is justified. The semantic DAG
  and artifact flow do not change. The old producer hash remains rollback
  evidence because its help path must change; only Step `00c` implementation
  path/hash provenance may change.
- **Coverage and Make boundary:** the validator baseline is `90/96` covered
  lines and `23/26` branches; the committed global floor is `9343/11506` lines
  and `3281/4698` branches. Stable roots already include `src/norad`; inspect
  final-path measurement and any review-required loader branches before moving
  the row. Because both shell assets leave flat wildcards, exact final producer
  and job paths must enter `validation-static`, `smoke`, and their literal Make
  oracle; direct shell and validator test recipes move without discovery or
  inventory weakening.
- **Preserved producer risks:** retain tool-resolution precedence, Java/GATK
  probes, dry-run no-write behavior, conditional sidecar reuse/generation,
  contig validation, lock ownership, run-token temps, and cleanup. The two-
  output publication remains nontransactional: a successful final FAI move
  followed by a failed final DICT move can leave only the FAI, without a receipt,
  rollback restoration, or recovery marker. Reviews must name an old/final-path
  oracle and preservation response; relocation cannot fix or bless this state.
- **Preserved scheduler and validator risks:** retain the executable job mode,
  seven directives, fallback submit CWD, tolerated samtools module calls, CSU
  defaults, Java discovery/version policy, explicit execute control, file-only
  output checks, and Bash `3.2` empty-array dry-run defect. Preserve the
  validator's five structural checks, ordered parser comparison, deterministic
  report/publication behavior, stable-input recheck, and inherited neutral-
  publisher faults. A successful local fixture/mock run will not become real
  samtools/GATK/Java, scheduler, cluster, production, scientific-review, or
  biological evidence.
- **Review and validation boundary:** create only `MIG-03E` and dedicated
  `REVIEW-ARCH-03E`, `REVIEW-REL-03E`, and `REVIEW-UX-03E` cards. All remain
  unselected in `TODO`. This definition is documentation-only and uses only Git
  and documentation validation at its boundary; no computational test,
  dependency action, scheduler submission, executable mutation, or future-owner
  preload occurred. Full applicable validation and batched migration
  documentation remain card-boundary work.

## 2026-08-02T23:39:53-0400 — REVIEW-ARCH-03E selected

- **Selection:** move only `REVIEW-ARCH-03E` to `IN_PROGRESS` and repair its
  reciprocal dependency/status links after JIT-definition checkpoint `3c6aaf0`
  was clean, published, and equal across local `HEAD`, configured upstream, and
  the live remote branch. `REVIEW-REL-03E`, `REVIEW-UX-03E`, and `MIG-03E`
  remain unselected in `TODO`.
- **Review boundary:** this begins one read-only independent-in-time
  adversarial pass over DAG eligibility, final-owner placement, exact path and
  import changes, job delegation, neutral-report and temporary reference-
  provenance loading, artifact provenance, explicit caller inventories, test
  ownership, wrapper necessity, atomicity, and rollback. The same campaign
  agent performs the pass, so independent authorship is not claimed.
  Executable/test mutation and computational, runtime, scheduler, production,
  scientific-review, and biological evidence remain out of scope.

## 2026-08-02T23:42:00-0400 — REVIEW-ARCH-03E completed

- **High finding — exact reference-provenance readiness was underspecified:**
  the separate `scripts/reference_provenance.py` has no readiness sentinel, and
  adding one would violate this unit's immutable-owner boundary. Freeze private
  identity `_norad_reference_provenance`, exact path resolution independent of
  caller CWD, cached `__file__` verification, and the complete required API
  `ProvenanceError`, `parse_fasta`, `parse_fai`, and `parse_dict`. Reject wrong
  or incomplete cached state, remove only an owned partial module after failed
  execution, preserve foreign state and `sys.path`, and fail before publication
  with one explicit path-bearing diagnostic.
- **High finding — the atomic cutover lacked an enumerated file ceiling:**
  freeze exactly fourteen tracked files: moves of the producer, validator, job,
  direct shell test, and direct validator test; plus `Makefile`, artifact-index
  producer evidence, artifact-adapter assertion, public CLI map, SLURM map,
  validator roster, shared validation-loader roster, coverage baseline path,
  and literal Make-expansion fixture. A fifteenth executable/test path reopens
  architecture review rather than expanding the slice silently.
- **Medium findings — independent owners stay independent:** route the final
  non-flat validator through the shared suite's existing path-validating exact-
  file loader while still-flat validators retain module-name import. Keep the
  Step `00c` adapter and every scheduler behavior in the central parametrized
  wrapper suite; move only the two direct tests. Do not move or edit the public
  reference-provenance CLI, its direct test/coverage row, or the Step `05`
  consumer. The private bridge is bounded mixed-layout debt, not approval of a
  neutral extraction or package contract.
- **Accepted architecture and rollback:** the no-predecessor DAG eligibility,
  final source/test homes, direct no-wrapper cutover, one-owner invariant,
  artifact identity preservation, documentation-after-executable order, and
  reverse rollback pass. The production edit ceiling is the producer help
  self-path, validator owner/dependency resolution and private loader, and job
  child path. The DAG and artifact flow are unchanged, so no diagram edit is
  warranted.
- **Evidence boundary:** this was a separate committed-time adversarial pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.

## 2026-08-02T23:43:45-0400 — REVIEW-REL-03E selected

- **Selection:** move only `REVIEW-REL-03E` to `IN_PROGRESS` and repair its
  reciprocal dependency/status links after architecture completion checkpoint
  `494889f` was clean, published, and equal across local `HEAD`, configured
  upstream, and the live remote branch. `REVIEW-UX-03E` and `MIG-03E` remain
  unselected in `TODO`.
- **Review boundary:** this begins one read-only independent-in-time pass over
  producer dry-run/execute/reuse/failure states, partial two-output publication,
  validator parsing/publication and both private loaders, scheduler Bash `3.2`/
  tool/module/output states, artifact provenance, coverage rename, residue,
  and rollback. The same campaign agent performs the pass, so independent
  authorship is not claimed. No executable/test mutation, computational test,
  runtime tool, scheduler submission, production input, dependency action,
  scientific review, or biological evidence is in scope.

## 2026-08-02T23:46:12-0400 — REVIEW-REL-03E completed

- **High finding — partial two-output publication lacked an exact oracle:** add
  one controlled fake-`mv` case that fails only the final DICT publication
  after the FAI reaches its final path. Run a temporary equivalent on the old
  path and the tracked case on the final path. Both must return nonzero, retain
  a nonempty final FAI, leave the final DICT absent, remove the owned lock, and
  leave no run-token temporary paths. Preserve the FAI as incomplete-attempt
  evidence; do not call the state successful or authorize deletion.
- **High finding — private loader failures need owner-local independent tests:**
  exact-load the validator in its moved direct suite and exercise healthy exact
  reuse, missing owner, foreign wrong-path cache, correct-path incomplete API,
  and injected loader-owned execution failure. Require `ProvenanceError` to be
  an exception type and all three parsers callable. Preserve all preexisting
  cache objects and `sys.path`, remove only the loader-created partial, publish
  no report, and leave no invocation-CWD residue.
- **Medium findings — parity and independent scheduler coverage:** add one full
  non-repository-CWD validator dry-run/execute/repeat journey with five ordered
  deterministic rows and stable replacement. Retain the central scheduler
  matrix rather than duplicate it: it already owns directives, executable mode,
  fallback submit CWD, tolerated modules, site defaults, Java choice/version,
  mode handling, Bash `3.2`, child exit, output validation, and streams.
- **Coverage and artifact decision:** final measurement must retain at least the
  old validator's `90/96` covered lines and `23/26` covered branches while
  exposing, not hiding, new loader branches. Global `9343/11506` line and
  `3281/4698` branch counts remain the rollback floor. Only the implementation
  producer path/hash changes; artifact identities, schemas, reconciliation,
  public reference provenance, and Step `05` remain unchanged.
- **Evidence boundary:** this was a read-only committed-time pass by the same
  campaign agent; independent authorship is not claimed. No executable, test,
  harness, dependency, runtime, scheduler, production, scientific-review, or
  biological evidence changed or ran.

## 2026-08-02T23:48:11-0400 — REVIEW-UX-03E selected

- **Selection:** move only `REVIEW-UX-03E` to `IN_PROGRESS` and repair its
  reciprocal dependency/status links after reliability completion checkpoint
  `522a4b4` was clean, published, and equal across local `HEAD`, configured
  upstream, and the live remote branch. `MIG-03E` remains unselected in `TODO`.
- **Review boundary:** this begins one read-only independent-in-time pass over
  root/arbitrary-CWD producer and validator commands, exact loader diagnostics,
  scheduler submit/CWD/site-tool/Bash `3.2` guidance, dry-run/reuse/partial-
  publication recovery, artifact provenance, Make/test commands, owner
  findability, rollback, and evidence language. The same campaign agent performs
  the pass, so independent authorship is not claimed. No executable/test
  mutation, computational test, dependency action, scheduler submission,
  runtime, production, scientific-review, or biological evidence is in scope.

## 2026-08-02T23:53:33-0400 — REVIEW-UX-03E completed

- **High finding — supported Step `00c` instructions are stale and
  incomplete:** the current runbook still names flat producer, validator, and
  job paths; omits the Java path from direct commands and portable scheduler
  overrides from submission; does not require `logs/` before `sbatch`; and
  repeats ad hoc/BAM evidence that is not the Step `00c` structured evidence
  contract. The MIG-03E documentation close must replace that block with exact
  final paths, direct and explicit-`bash` forms, explicit samtools/GATK/Java
  paths, root and arbitrary-CWD distinctions, dry-run side-effect guarantees,
  interpreter-only validation, scheduler preflight/default/override behavior,
  and a local-only migration evidence ceiling.
- **High finding — partial publication needs an operator-safe preservation
  route:** both Step `00c` troubleshooting entries and the owner README must
  distinguish malformed or mismatched sidecars from the characterized state
  where final FAI publication succeeds and final DICT publication fails.
  Preserve producer context, scheduler stdout/stderr, lock state, run-token
  temporary paths, and final FAI/DICT state before cleanup or a separately
  authorized rerun. The retained FAI remains evidence of an incomplete attempt,
  not successful transaction output; this review neither fixes nor blesses the
  defect.
- **Medium findings — owner discovery and recovery boundaries:** the adjacent
  README must route final producer, validator, scheduler, focused-test, central
  scheduler-test, diagnostic, documentation-first rollback, and evidence
  journeys. It must keep the public flat `reference_provenance.py` owner
  separate and explain that a private exact-loader failure is a checkout-
  integrity diagnostic, not a `PYTHONPATH` workaround or extraction approval.
  Exact command and migration-link repairs remain batched for the migration
  documentation close rather than expanding this review slice.
- **Evidence boundary:** this was a read-only independent-in-time pass against
  clean, published, local/upstream/live-remote-equal selection checkpoint
  `4750161`, performed by the same campaign agent; independent authorship is
  not claimed. No executable, test, dependency, runtime-tool, scheduler,
  production, scientific-review, or biological evidence changed or ran.

## 2026-08-02T23:57:20-0400 — MIG-03E selected

- **Selection:** move only `MIG-03E` to `IN_PROGRESS` and repair its reciprocal
  lifecycle/status links after usability-review completion checkpoint `9ae3b12`
  was clean, published, and equal across local `HEAD`, configured upstream, and
  the live remote branch. All three dedicated reviews are complete; no later
  migration or review card is created or selected.
- **Execution boundary:** this checkpoint authorizes task-specific planning for
  the reviewed fourteen-file `construct_FASTA_sidecars` cutover. Baseline
  capture, executable/test mutation, card-boundary validation, and batched
  canonical documentation remain separate bounded slices. No executable, test,
  harness, dependency, runtime-tool, scheduler, production, scientific-review,
  or biological evidence changed or ran at selection.

## 2026-08-03T00:01:02-0400 — MIG-03E task-specific plan frozen

- **Git and scope:** planning began from clean, published,
  local/upstream/live-remote-equal selection tip `177a912`, with no untracked
  file, recovery marker, index lock, or mutable-lane collision. The executable
  commit is exactly fourteen tracked files: five moves and nine explicit caller/
  harness updates. Canonical command, migration-link, and lifecycle repairs
  remain one separate later card-boundary close.
- **Moves and production diff:** move the producer, validator, and executable
  job to `src/norad/stages/construct_FASTA_sidecars/`; move only their two
  direct tests to the mirrored test home. Preserve modes `0755`, `0644`, and
  `0755`. Production changes are limited to the producer usage self-path, the
  validator's final report-owner path plus private exact-file bridge to the
  unchanged flat reference-provenance owner, and the job's final child path.
  Add no wrapper, duplicate, package marker, descriptor, schema, alias, global
  path mutation, or reference-provenance readiness sentinel.
- **Caller and test cutover:** update only Make, artifact producer mapping and
  focused evidence, public CLI map, SLURM map, validator roster, shared non-flat
  validator loader, coverage row, and literal Make fixture. Add the reviewed
  final-DICT `mv` failure case to the moved shell suite and the arbitrary-CWD
  repeat plus exact reference-loader fault matrix to the moved validator suite.
  Keep scheduler behavior in its independent central matrix and the public
  reference-provenance owner/test plus Step `05` consumer unchanged.
- **Baseline tranche:** after this planning checkpoint is published and equal,
  run syntax for both shell assets, the current direct shell suite, and the
  exact directly affected Python modules. Add only temporary untracked-free
  probes for FAI-only partial publication and non-repository-CWD validator dry-
  run/execute/repeat parity. Record modes, sizes, lines, hashes, counts, streams,
  exits, deterministic report hash, and residue without updating tracked
  coverage.
- **Validation and evidence boundary:** this is planning documentation only.
  The temporary old-path tranche is not the full card gate; the complete
  applicable local gate runs once after final-path cutover. No real samtools,
  GATK, or Java work, scheduler submission, dependency action, production data,
  scientific-review state, or biological evidence is authorized or created.

## 2026-08-03T00:06:51-0400 — MIG-03E old-path baseline captured

- **Published parent and clean scope:** the baseline began from clean,
  published, local/upstream/live-remote-equal plan checkpoint `d7c29ad`, with no
  tracked or untracked file, recovery marker, index lock, or mutable-lane
  collision. Temporary probes were removed after execution; no tracked
  executable/test file changed and no later owner was preloaded.
- **Targeted suites:** syntax passed for the producer and executable job, and
  the unchanged direct shell suite passed all existing cases. The exact seven-
  module affected Python surface passed `555` tests in `61.43s`, covering the
  direct validator, public CLI, central scheduler, validation roster, shared
  report publisher, artifact adapter, and coverage policy. This is not the
  complete card gate.
- **Reviewed missing oracles:** a fake `mv` failed only final DICT publication
  with exit `73` after final FAI publication. The producer propagated `73`,
  retained a nonempty `26`-byte FAI with SHA-256
  `a5c1d01825f0a3c585991b63efa4d0cccb96007c8ece00d78eb4c72096c82068`,
  left DICT absent, removed the owned lock, and left no run-token temporary
  path. From a non-repository CWD, validator dry-run, execute, and repeat all
  returned `0`; execute/repeat produced the same five ordered pass rows and
  byte-identical `493`-byte report with SHA-256
  `b8fb138d7c0087eb02e8b217d11ff1b9ecb4d326869f10a0db67272f2597a6d4`,
  empty stderr, unchanged inputs, and no invocation or publisher residue.
- **Frozen rollback evidence:** producer mode/hash is `0755` /
  `f041c55a0e9a3b36c14dcc9b929cfa56190e1c00d23a5a62fa72ac3669f0c478`;
  validator `0644` /
  `5aa6358412a56b5ddb8ce963a6d7431cfb07c1bbd9fbb37c8237fc3cbebe15fd`;
  job `0755` /
  `78b00abb7751e78264bae30d6b3dbfb7792ca5532850f192b1b2098cbf8e85d0`;
  direct shell test `0755` /
  `a477786e5f331c7ecc91ef338b89abc8cc209aae14c62dac2877f684e18fc7d5`;
  and direct validator test `0644` /
  `7ec48d7394268e451a2087a2892a6435a02f5216d08b692fce6a3cc2094c6d48`.
- **Evidence ceiling and next action:** no tracked coverage run, real samtools/
  GATK/Java generation, scheduler submission, dependency action, production
  input, cluster state, scientific review, or biological evidence was created.
  The committed floor remains validator `90/96` lines and `23/26` branches and
  global `9343/11506` lines and `3281/4698` branches. Publish this baseline
  checkpoint, prove live remote equality, then apply only the reviewed fourteen-
  file atomic cutover.

## 2026-08-03T00:41:29-0400 — MIG-03E executable cutover accepted and documentation close prepared

- **Published parent and atomic scope:** the cutover began from clean,
  published, local/upstream/live-remote-equal old-path baseline `9850a8d`, with
  no untracked file, recovery marker, index lock, or mutable-lane collision. It
  moved exactly the producer, validator, job, shell test, and validator test and
  changed only the nine reviewed Make, artifact, public-CLI, SLURM, validation-
  roster, shared-loader, coverage, and literal-fixture callers. Git's default
  rename display represented the heavily expanded validator test as an add and
  delete; `--find-renames=20%` confirms the frozen five logical moves and nine
  modifications. Published executable/test checkpoint is `cd3b547`.
- **Final native identity:** producer mode/bytes/lines/hash is `0755` / `14,511`
  / `515` /
  `ed3e9ca039102c881c4f91cb02fd32e4a67d09ad799300c789cbab27ce1ab0a1`;
  validator `0644` / `8,699` / `234` /
  `d2554dea8888d51cbcb7a02a6638e09d05ea16526f9d0d82ba0c36f18b3c2a5a`;
  job `0755` / `4,566` / `151` /
  `c084f8bcbc9173b3f99c2a0baf6f443f2a8121e8bf90b8af345c21b751593d51`;
  shell test `0755` / `14,410` / `458` /
  `35bfce22da1aa08d155bd74ed4a306a10d0002c5df43f63fe1a7914013940882`;
  and validator test `0644` / `10,247` / `295` /
  `e768515779268206728a21a8ef0a1fbddb8b8ba2cb4031648b3cafae7afdb900`.
  Production changes remain limited to producer usage self-path, validator
  owner depths/private loader, and job child path.
- **Mixed-layout decision:** the validator resolves the neutral report owner
  from its final source depth and uses private identity
  `_norad_reference_provenance` to exact-load unchanged public
  `scripts/reference_provenance.py`. It verifies cached `__file__`, exception
  and callable API shape, preserves foreign cache objects and `sys.path`, and
  removes only its owned partial state. This bridge is bounded debt, not a
  package identity, `PYTHONPATH` convention, readiness-sentinel addition, or
  reference-provenance extraction approval. The public CLI/test/coverage row
  and Step `05` consumer remain unchanged.
- **Focused final-path acceptance:** the moved shell suite passed, including
  controlled final-DICT move failure with exit `73`, retained nonempty FAI,
  absent DICT, removed owned lock, and no run-token residue. The direct moved
  validator suite passed `11` tests. The exact affected Python surface passed
  `561` tests in `62.92s`, including arbitrary-CWD dry-run/execute/repeat bytes
  and the missing/wrong-cache/incomplete/owned-failure loader matrix.
- **Coverage decision:** deterministic serial coverage passed `1,079` tests,
  skipped `17`, and explicitly deselected only the documentation-validator test
  whose stale links were reserved for this close. It measured the final
  validator at `128/139` lines and `35/42` branches
  (`0.920863`/`0.833333`) and global coverage at `9381/11549` lines and
  `3293/4714` branches (`0.812278`/`0.698557`), above the frozen covered-count
  floor. Every non-target row matched the prior baseline. The standalone policy
  comparison passed after moving the renamed row to lexical order; coverage
  policy was not weakened.
- **Aggregate-gate truth:** static preflight, shell contracts, guarded R, and
  report runtime passed. The first sandboxed guarded-R run failed only because
  DNS could not reach Bioconductor metadata; the exact network-enabled rerun
  used the existing project library and changed no dependency. The ignored
  malformed `macos` warning remains characterized local recovery state. Python
  executed `1,079` passes and `17` skips before the documentation-validator test
  reported exactly ten migration-caused stale links in the owner contract and
  functional inventory plus the nine inherited `UNREFINED` card-location
  findings. The aggregate gate was not fully green and is not recorded as such.
- **Preserved defects and operational risks:** retain FAI-first nontransactional
  publication without receipt or recovery marker; the retained FAI is
  incomplete-attempt evidence, not successful output or deletion authority.
  Retain scheduler Bash `3.2` empty-array dry-run failure, CSU site bindings,
  tolerated modules, fallback submit CWD, Java selection/version policy, and
  nonempty-file-only post-checks. These remain characterized defects and are
  neither fixed nor blessed. Local fixture/mock success is not real
  samtools/GATK/Java, scheduler, cluster, production, scientific-review, or
  biological evidence.
- **Documentation and lifecycle decision:** batch the adjacent owner README,
  final commands, current topology/coverage/ownership status, both diagnostic
  routes, all ten migration links, every inbound lifecycle link, completed-card
  move, and this risk ledger into one documentation-only close. The public DAG
  and artifact flow did not change, so no diagram edit is warranted. Select no
  later owner until this close is committed, pushed, and proved equal.
- **Rollback and evidence ceiling:** reverse the documentation close before
  reverting executable checkpoint `cd3b547`; published old-path baseline is
  `9850a8d`. Preserve runtime artifacts during rollback and restore no duplicate
  legacy source. The nine inherited `UNREFINED` findings remain a nonpassing
  documentation ceiling, not authority for unrelated lifecycle changes.

## 2026-08-03T00:42:49-0400 — MIG-03E documentation/lifecycle acceptance

- **Canonical close:** added the adjacent implemented-owner README; repaired the
  contract, architecture, functional inventory, coverage owner, documentation
  ownership roster, roadmap, handoff, complete Step `00c` commands, and both
  troubleshooting routes; moved `MIG-03E` to `COMPLETED`; repaired every inbound
  lifecycle link; and recorded the executable evidence and risks above. No
  executable, test, dependency, diagram, schema, or later-owner card changed.
- **Exact migration-link result:** nonhistorical searches found no remaining
  active-card link or legacy Step `00c` producer, validator, job, or direct-test
  path. Historical old-path planning/baseline text remains immutable evidence in
  the completed card and dated history rather than being rewritten as current
  topology.
- **Documentation gate:** `git diff --check` passed. The exact documentation
  validator reported only the nine inherited `invalid card location` findings
  under `docs/tasks/UNREFINED/`; all ten `MIG-03E`-caused missing links are
  repaired. This is an expected-only nonpassing documentation result, not a
  green gate and not authority to change those inherited files.
- **Publication boundary:** stage only this impact-directed documentation and
  lifecycle close, commit it separately from executable checkpoint `cd3b547`,
  push normally, and prove local `HEAD`, configured upstream, and live remote
  equality before selecting the next dependency-valid owner.

## 2026-08-03T00:49:15-0400 — MIG-03F JIT unit defined

- **Git and predecessor:** definition began only after `MIG-03E`
  documentation/lifecycle checkpoint
  `fa79883683b37559dfa90880a3f04a978bbfb530` was committed, published, clean,
  and proved equal across local `HEAD`, configured upstream, and the live remote
  branch. Recent history is linear; no merge, rebase, cherry-pick, revert,
  sequencer, index lock, recovery marker, untracked file, or overlapping mutable
  lane was present.
- **Live-DAG decision:** select only `construct_canonical_BAM` for JIT
  definition. Its sole hard predecessor, `align_RNA_reads_with_STAR`, is
  migrated. Every other remaining stage, analysis, or evidence owner still has
  at least one unmigrated hard predecessor. Historical alias order and raw file
  size did not choose the unit; no downstream owner was carded.
- **Frozen native surface:** producer `scripts/step_02_sort_index_bam.sh` is
  mode `0755`, `13,670` bytes, `442` lines, SHA-256
  `ad73a5476447cba0cd5265864a16710492a2e313150ab2ac7293fef8c26a627c`;
  validator `scripts/validate_step_02_canonical_bam.py` is mode `0644`, `7,686`
  bytes, `207` lines, SHA-256
  `d805f17c4c95aea004f4a440c82241d7d5f5e8d3024fac94fb1de90421bb67ac`;
  and job `jobs/step_02_sort_index_bam.slurm` is intentionally mode `0644`,
  `2,387` bytes, `97` lines, SHA-256
  `b67f50db365aba533d882746df02a1f9ea0c5e6b5c25170e9251978cc8be6f8b`.
  Direct-test hashes are shell
  `239646b44d6b411fe9b590108e6e7e977427ee93c62cee1b16212f90c275e29c`
  and validator
  `f7f9dd25ec9ad7e70a4d5566a09039e67f3b27cee5dd0294bffaa48990260492`.
- **Known target-direction leak:** Step `04` and Step `05` validators ambient-
  import `run_tool` and `parse_header` from the Step `02` validator. A direct
  move would retain a prohibited peer-implementation import or require a legacy
  wrapper. The bounded candidate is one private neutral
  `src/norad/libraries/bam_validation.py` containing only those two proven
  helpers, with exact-file caller-local loaders in all three validators. Reviews
  must settle module identity, readiness/API checks, cache ownership, fault
  diagnostics, direct tests, path ceiling, and rollback. They must reject copied
  helpers, public package identity, `sys.path` mutation, broad library design,
  or migration of either downstream owner.
- **Small-slice decision:** after all reviews and a frozen plan/baseline, perform
  the helper preparation and Step `02` native owner move as two separate
  executable checkpoints. Run only their smallest direct checks at slice
  boundaries and the complete applicable computational gate once on assembled
  final executable state at the card boundary. Batch path links, owner README,
  canonical status, troubleshooting, lifecycle, and audit closure separately at
  the card boundary.
- **Producer risks:** preserve side-effect-free producer dry-run, samtools PATH
  resolution, staged sort/read-group/index validation, complete-pair
  precondition, owned lock, run-token paths, replaceable predecessor, backup/
  publish/final-validation order, and cleanup. Rollback restoration moves are
  best-effort and ignored on failure; cleanup can remove backups without a
  receipt or recovery marker. Reliability review must assign a safe old/final-
  path oracle and evidence-preservation route without fixing or blessing this
  ambiguous recovery state.
- **Validator and scheduler risks:** preserve the validator's five rows,
  deterministic publisher behavior, and intentional divergence from the
  producer on zero records, `LB`, `PL`, quickcheck detail, and BAM/BAI identity.
  Preserve job mode `0644`, caller-CWD behavior, strict module load with
  tolerated listings, dry-run directory creation, explicit execute control,
  nonempty-file checks, and the Bash `3.2` empty-array dry-run defect. Local
  fixture/mock evidence will not become real samtools, SLURM, cluster,
  production, scientific-review, or biological evidence.
- **Coverage, artifact, and caller boundary:** committed Step `02` validator
  coverage is `105/115` lines and `21/28` branches; current global snapshot is
  `9381/11549` lines and `3293/4714` branches. The new neutral helper must meet
  the existing 90% line/85% branch threshold, and final measurement must preserve
  global policy. Only Step `02` implementation path/hash artifact evidence may
  change. Make, public CLI, SLURM, validator, shared-loader, coverage, artifact,
  and literal fixtures remain explicit; no recursive discovery is approved.
- **Review and evidence boundary:** create only `MIG-03F` and dedicated
  `REVIEW-ARCH-03F`, `REVIEW-REL-03F`, and `REVIEW-UX-03F` cards. All remain
  unselected in `TODO`. This definition is documentation-only and uses only Git
  and documentation validation at its boundary; no computational test,
  dependency action, scheduler submission, executable mutation, or future-owner
  preload occurred.

## 2026-08-03T00:52:50-0400 — REVIEW-ARCH-03F selected

- **Selection:** move only `REVIEW-ARCH-03F` to `IN_PROGRESS` and repair its
  reciprocal dependency/status links after definition checkpoint `ee25492` was
  clean, published, and equal across local `HEAD`, configured upstream, and the
  live remote branch. `REVIEW-REL-03F`, `REVIEW-UX-03F`, and `MIG-03F` remain
  unselected in `TODO`.
- **Review boundary:** this begins one read-only independent-in-time adversarial
  pass over live-DAG eligibility, final-owner placement, exact two-function
  neutral ownership, three caller-local loader depths, job delegation, direct
  and cross-owner test placement, explicit caller maps, executable-slice
  ceilings, artifact/coverage ownership, wrapper necessity, and rollback order.
  The same campaign agent performs the pass, so independent authorship is not
  claimed. Executable/test mutation and computational, runtime, scheduler,
  production, scientific-review, and biological evidence remain out of scope.

## 2026-08-03T00:58:19-0400 — REVIEW-ARCH-03F completed

- **High finding — neutral API and loader contract were underspecified:**
  accept exactly one mode-`0644` private
  `src/norad/libraries/bam_validation.py` containing behavior-preserving
  `run_tool` and `parse_header`. Freeze private identity
  `_norad_bam_validation`, readiness `_NORAD_BAM_VALIDATION_READY`, callable API
  checks, exact cached-path validation, owned-partial cleanup, foreign-cache and
  `sys.path` preservation, and the path-bearing fail-closed diagnostic. Add no
  validation-report dependency, CLI, package identity, or stage-specific logic.
- **High finding — executable slices lacked exact ceilings:** helper preparation
  is exactly five files: add the neutral module and neutral test suite, and
  modify only the Step `02`, `04`, and `05` validators. Owner cutover is exactly
  five moves plus ten updates: Make, artifact producer and assertion, public
  CLI, SLURM, validation roster, validation-report map, BAM-helper caller map,
  coverage row, and literal Make fixture. A sixth move, eleventh update, or
  downstream direct-test edit reopens architecture review.
- **Medium finding — test and artifact ownership needed separation:** the new
  neutral suite owns helper semantics and all three caller-local loader states;
  unchanged Step-specific direct suites remain functional-owner evidence and
  run as the helper slice's affected regression set. Helper extraction changes
  no artifact evidence. Owner cutover changes only Step `02` producer path/hash
  and adds its assertion to the existing migrated-evidence test; public artifact
  contracts remain unchanged.
- **Accepted architecture and rollback:** `construct_canonical_BAM` is the only
  live-DAG-supported next owner. Two published executable slices eliminate the
  peer import without a wrapper or copied helper. Roll back documentation, then
  native owner movement, then helper extraction so a restored flat Step `02`
  validator always retains its dependency. No descriptor, schema, package,
  wrapper, compatibility path, downstream migration, or public import is
  warranted.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.

## 2026-08-03T00:59:32-0400 — REVIEW-REL-03F selected

- **Selection:** move only `REVIEW-REL-03F` to `IN_PROGRESS` and repair its
  reciprocal dependency/status links after architecture completion checkpoint
  `c429d8d` was clean, published, and equal across local `HEAD`, configured
  upstream, and the live remote branch. `REVIEW-UX-03F` and `MIG-03F` remain
  unselected in `TODO`.
- **Review boundary:** this begins one read-only independent-in-time pass over
  helper byte/exception parity, three loader fault surfaces, producer staging/
  pair/lock/backup/publish/final-validation/rollback states, validator
  asymmetries and publication, scheduler modes/residue, artifact evidence,
  coverage, minimal slice checks, and commit rollback. The same campaign agent
  performs the pass, so independent authorship is not claimed. No executable/
  test mutation, computational test, runtime tool, scheduler submission,
  production input, dependency action, scientific review, or biological
  evidence is in scope.

## 2026-08-03T01:03:49-0400 — REVIEW-REL-03F completed

- **High finding — failure inside rollback lacked a safe exact oracle:** extend
  only the moved shell suite's fake `mv` so final BAI publication fails and
  prior-BAM restoration then fails. Both old and final paths must fail nonzero,
  retain the prior BAI but no canonical BAM, remove backups and the owned lock,
  and leave no run-token scratch. The resulting lockless partial pair and lost
  prior BAM are a characterized ambiguous/data-loss defect, not a repaired or
  approved transaction.
- **High finding — extraction parity and loader faults needed one owner:**
  capture old Step `02` `run_tool` and `parse_header` results before extraction;
  then make the neutral suite prove exact result/exception parity plus healthy,
  missing, wrong-cache, incomplete-API, and owned-execution-failure states for
  the three callers at flat and final Step `02` depths. Preserve foreign cache
  objects and `sys.path`, remove only an owned partial, emit the exact path/type/
  reason diagnostic, and publish no report or CWD residue on load failure.
- **Medium finding — relocated validator journey was incomplete:** extend only
  the moved validator suite with non-repository-CWD dry-run, execute, and repeat
  parity: exact deterministic five-row bytes, empty successful stderr, stable
  replacement, unchanged inputs/modes, and no invocation-directory residue.
  The existing central scheduler and shared publication/roster suites retain
  their independent contracts; duplicating them is not justified.
- **Coverage and evidence boundary:** freeze Step `02` at `105/115` lines and
  `21/28` branches, Step `04` at `105/114` and `22/28`, Step `05` at `98/108`
  and `19/24`, combined targeted covered-count floors `308`/`62`, global floors
  `9381/11549` and `3293/4714`, exact non-target rows, and new-helper thresholds
  90%/85%. This was a read-only committed-time pass by the same campaign agent;
  no executable/test mutation or computational, dependency, runtime, scheduler,
  production, scientific-review, or biological evidence changed or ran.

## 2026-08-03T01:09:25-0400 — REVIEW-UX-03F selected

- **Selection:** move only `REVIEW-UX-03F` to `IN_PROGRESS` and repair its
  reciprocal dependency/status links after reliability completion checkpoint
  `b3fe326` was clean, published, and equal across local `HEAD`, configured
  upstream, and the live remote branch. `MIG-03F` remains unselected in `TODO`.
- **Review boundary:** this begins one read-only independent-in-time pass over
  producer direct/explicit-Bash/arbitrary-CWD journeys, validator dry-run/
  execute/repeat commands, scheduler submission/CWD/default/override/module
  caveats, helper-integrity diagnostics, recovery preservation, Make/test
  routes, implementation provenance, owner findability, rollback, and evidence
  ceilings. The same campaign agent performs the pass, so independent
  authorship is not claimed. No executable/test mutation, computational test,
  runtime tool, scheduler submission, dependency action, production input,
  scientific review, or biological evidence is in scope.

## 2026-08-03T01:11:45-0400 — REVIEW-UX-03F completed

- **High finding — public journeys need complete final commands:** the owner
  README and Step `02` runbook must replace bare old paths with final direct and
  explicit-`bash` producer dry-run/execute forms, arbitrary-CWD absolute paths,
  and explicit PATH-only samtools resolution. The mode-`0644` validator remains
  an explicit-interpreter dry-run/execute/repeat journey with an explicit
  samtools path. Producer dry-run invokes no samtools command and creates no
  output directory, lock, scratch, backup, BAM, or BAI.
- **High finding — scheduler and recovery guidance overstate safety:** final
  submission must `cd` to the checkout, create `logs/`, name the final job, and
  expose `SAMPLE_ID`, `INPUT_ALIGNMENT`, `OUTPUT_DIR`, `THREADS`, and `EXECUTE`.
  Document caller CWD, forced `/tmp`, strict samtools load, tolerated module
  lists, dry-run directory creation, and the Bash `3.2` defect. Replace the
  complete-rollback promise with the characterized prior-BAI-only lockless
  state and preserve pair, stream, run-token, final, and backup evidence before
  any separately authorized recovery decision.
- **Medium findings — maintainer routes and evidence boundaries:** the adjacent
  README must treat neutral-helper loader errors as checkout-integrity
  diagnostics, never `PYTHONPATH`/package/public-CLI workarounds; route the
  moved owner, neutral helper, unchanged Step `04`/`05`, and central scheduler
  suites; record only the producer implementation path/hash artifact change;
  and state documentation-first rollback plus the local fixture/mock ceiling.
  No compatibility alias is required.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, dependency, runtime tool, scheduler, production, scientific-review, or
  biological evidence changed or ran.

## 2026-08-03T01:13:49-0400 — MIG-03F selected

- **Selection:** move only `MIG-03F` to `IN_PROGRESS` and repair its reciprocal
  lifecycle/status links after three-review-complete checkpoint `a8d760b` was
  clean, published, and equal across local `HEAD`, configured upstream, and the
  live remote branch. No downstream or later owner is selected or preloaded.
- **Execution boundary:** task-specific planning and old-path baseline remain
  documentation/evidence slices before executable mutation. Then publish one
  exact five-file neutral-helper checkpoint and one exact five-move/ten-update
  owner checkpoint with minimum slice checks. Run the full applicable gate once
  at the assembled executable card boundary, then batch canonical documentation
  and lifecycle repair into a separate close. No executable/test mutation,
  computational test, dependency action, runtime tool, scheduler submission,
  production input, scientific review, or biological evidence occurred at
  selection.

## 2026-08-03T01:15:58-0400 — MIG-03F task-specific plan frozen

- **Git and slicing:** planning began from clean, published,
  local/upstream/live-remote-equal selection `679aba9`, with no untracked file,
  recovery marker, index lock, or mutable-lane collision. Publish two small old-
  path evidence slices, an exact five-file helper checkpoint, and an exact five-
  move/ten-update owner checkpoint. Run the complete local gate only at the
  assembled executable card boundary; batch canonical documentation and links
  into the separate close.
- **Helper slice:** add only private mode-`0644`
  `src/norad/libraries/bam_validation.py` and its neutral suite; modify only the
  Step `02`, `04`, and `05` validators. Extract exactly `run_tool` and
  `parse_header`; freeze private identity/readiness/API, exact path/cache
  validation, foreign state and `sys.path` preservation, owned-partial cleanup,
  and the reviewed exit-`2` diagnostic. Run only the neutral and three affected
  direct validator suites at this boundary.
- **Owner slice:** move only the producer, validator, mode-`0644` job, and two
  direct tests. Update only Make, artifact producer/assertion, public CLI,
  SLURM, validation roster, validation-report map, BAM-helper suite, coverage
  baseline, and literal Make fixture. Production edits are confined to help,
  two validator depths, and job delegation. The moved tests add the persistent
  rollback-restore fault and non-repository-CWD repeat journey.
- **Baseline, gate, and rollback:** first freeze old helper results, then native
  shell/validator/scheduler behavior, without tracked executable mutation, real
  samtools, submission, production data, or dependency action. Minimal checks
  guard executable slice boundaries. Final coverage measurement and the exact
  `RUNBOOK.md` complete gate run once before the executable commit. Rollback is
  documentation, owner cutover, then helper preparation; runtime artifacts are
  never deleted by Git rollback. No executable/test mutation or computational,
  scheduler, production, scientific-review, or biological evidence changed or
  ran in this planning slice.

## 2026-08-03T01:19:02-0400 — MIG-03F old helper baseline captured

- **Exact probe:** from clean, published, local/upstream/live-remote-equal plan
  `d8638a0`, an isolated non-repository-CWD exact-load of the flat Step `02`
  validator recorded `run_tool` argv, status `7`, `probe-out` stdout,
  `probe-err` stderr, and missing-tool `FileNotFoundError(errno=2)`. Bytecode
  writes were disabled and the temporary directory removed itself.
- **Header results:** valid returned `(true, true, HD=1 RG=1)`; empty returned
  `(false, false, HD=0 RG=0)`; two HD/two RG returned
  `(false, false, HD=2 RG=2)`; and a coordinate header with wrong RG ID returned
  `(true, false, HD=1 RG=1)`. The complete canonical JSON SHA-256 is
  `e5676241625a500ddcef922f98c33fc7ddcd25b3f750fbd495b6a453b0a12d23`.
- **Residue and evidence ceiling:** `sys.path` remained byte-for-byte equal, the
  temporary CWD remained empty, and Git stayed tracked/untracked clean. This is
  local interpreter/subprocess characterization only; no executable/test file,
  coverage, dependency, real samtools runtime, scheduler, production,
  scientific-review, or biological evidence changed.

## 2026-08-03T01:21:45-0400 — MIG-03F old native baseline captured

- **Focused checks:** from clean, published, local/upstream/live-remote-equal
  helper-evidence checkpoint `9a2517b`, producer/job syntax and the complete
  direct producer suite passed. The direct Step `02`/`04`/`05` validator set
  passed `15` tests in `2.53s`; the exact Step `02` scheduler subset passed `9`
  in `0.82s` with `102` unrelated cases deselected.
- **Arbitrary-CWD parity:** dry-run and two execute attempts returned zero with
  empty stderr from a temporary non-repository CWD. Dry-run wrote no report and
  stdout hashed to `e0edf8f70d40ffc6ca9ae6ef732c797ac00abd056ee16496ad22038e277c5c1f`.
  Execute/repeat produced identical ordered five-pass-row bytes: length `542`,
  SHA-256 `0007c190b23071286fea72670f72d9cf98666c5c11fd76f1657715aa2d76a7c8`.
  Inputs and modes were unchanged and the invocation CWD stayed empty.
- **Frozen owner evidence:** producer/validator/job modes remain `0755`/`0644`/
  `0644`, lines `442`/`207`/`97`, bytes `13,670`/`7,686`/`2,387`, with hashes
  `ad73a547...`, `d805f17c...`, and `b67f50db...`. Direct shell/Python tests
  remain modes `0755`/`0644`, lines `528`/`90`, bytes `20,546`/`3,189`, with
  hashes `239646b4...` and `f7f9dd25...`; the active card records full hashes.
  Git stayed tracked/untracked clean. Evidence is local synthetic fixture/mock
  only; no real samtools, scheduler, dependency, production, scientific-review,
  or biological action occurred.

## 2026-08-03T02:23:00-0400 — MIG-03F executable campaign accepted and documentation close prepared

- **Published sequencing and exact scope:** helper preparation began only after
  clean, published, live-remote-equal native baseline `6a716b1`; it changed the
  exact five reviewed files and was published as `4726ad1`. Owner assembly then
  moved exactly the producer, validator, mode-`0644` job, shell test, and
  validator test and modified only the ten reviewed Make, artifact, public-CLI,
  scheduler, roster, shared-loader, coverage, and literal-fixture paths.
  Published executable/test checkpoint is `13a2748`; both checkpoints were
  proved clean and equal across local `HEAD`, configured upstream, and the live
  remote before this close.
- **Neutral-helper decision:** private mode-`0644`
  `src/norad/libraries/bam_validation.py` is `905` bytes and `30` lines with
  SHA-256
  `c98c301c4dbc80f8a7ee7689005be85f513101764e806099654ac0d9d03e02bc`.
  It owns exactly `run_tool`, `parse_header`, and readiness state. Final Step
  `02` and flat Step `04`/`05` exact-load it under private identity, verify
  path/readiness/callables, preserve foreign cache and `sys.path`, and remove
  only loader-owned partial state. This resolves the peer-stage import without
  package identity, public CLI, installation, `PYTHONPATH`, wrapper, duplicate,
  or later-owner migration.
- **Final native identity:** producer mode/bytes/lines/hash is `0755` / `13,703`
  / `442` /
  `602c9b6f71d7fb38533e29e294fcdd3685339614daa6efa264ba413669dd0cd3`;
  validator `0644` / `9,414` / `253` /
  `bcda016ad0a2c3b414a1eb1cc545af1cf49c1e53887efa6e85a0cdb8543b522b`;
  and job `0644` / `2,420` / `97` /
  `d5b68d303c81ecdff6badd3b20c5cdf16fadd0bde49b4c71bd30d9803be48723`.
  Direct shell/Python tests are `0755` / `22,404` / `562` /
  `01806301844e4243a122c480c3cf462ff53c24b4aadc7b77853ba600246ff9de`
  and `0644` / `4,987` / `142` /
  `daefea7259306201f7d08f8f8269eecfe02cdefb04c9153db27ec0046b44ec32`.
  Production changes remain limited to producer help, validator depths/helper
  ownership, and job child path.
- **Focused final-path acceptance:** the helper boundary passed `40` affected
  validator tests in `2.63s`. After the owner move, producer/job syntax and the
  complete moved shell suite passed, including the persistent failure-inside-
  rollback oracle. The moved validator plus neutral helper passed `31` tests;
  the exact Step `02` scheduler subset passed `9` with `102` unrelated cases
  deselected. Arbitrary-CWD dry-run/execute/repeat retained the frozen `542`-
  byte report hash, empty stderr, unchanged inputs/modes, and empty invocation
  directory.
- **Reliability risk preserved:** controlled final-BAI publication failure
  followed by prior-BAM restoration failure returned nonzero with both
  diagnostics, retained only the prior BAI, and left canonical BAM, both
  backups, owned lock, and run-token scratch absent. This is a characterized
  lockless partial-pair and prior-BAM data-loss defect. It is neither fixed nor
  blessed and supplies no deletion, adoption, retry, or recovery authority.
- **Coverage decision:** deterministic serial coverage passed `1,109` tests,
  skipped `17`, and deselected only the already-observed documentation-
  validator assertion reserved for this close. Step `02` measured `137/149`
  lines and `32/42` branches; Step `04` `144/155` and `33/42`; Step `05`
  `138/149` and `31/38`; helper `12/12`; global `9504/11677` and `3327/4756`.
  Every non-target row remained exact. Old per-row rates, combined targeted
  counts, global covered-count floors, and the helper threshold passed the
  standalone policy comparison; coverage policy was not weakened.
- **Aggregate-gate truth:** the first exact sandboxed gate passed static
  preflight and then stopped when guarded R could not resolve Bioconductor
  metadata. The exact network-enabled rerun used the existing project library
  and installed, restored, deleted, and updated nothing. Static preflight,
  shell contracts, guarded R, and report runtime passed. Python executed
  `1,109` passes and `17` skips before the sole documentation-validator failure
  reported exactly ten migration-caused links in the owner contract and
  functional inventory plus the nine inherited `UNREFINED` location findings.
  The aggregate gate was not green and is not represented as green.
- **Preserved behavior and evidence boundaries:** retain producer/validator
  empty-BAM, read-group, quickcheck, and BAI-identity asymmetries; best-effort
  rollback without receipt/recovery marker; scheduler caller CWD, ignored
  `SLURM_SUBMIT_DIR`, forced `/tmp`, Bash `3.2` dry-run failure, strict samtools
  load, tolerated module-list diagnostics, dry-run directory creation, and
  file-only post-checks. Passing local fixtures/mocks, guarded local R, pinned
  report runtime, and coverage do not establish real samtools, scheduler,
  cluster, production, scientific-review, or biological evidence.
- **Documentation and lifecycle decision:** batch the adjacent owner README,
  final commands, current topology/coverage/ownership status, helper route,
  ambiguous-recovery route, all ten migration links, every inbound lifecycle
  link, completed-card move, and this risk ledger into one documentation-only
  close. The public DAG and artifact flow did not change, so no diagram edit is
  warranted. Select or create no later owner until this close is committed,
  pushed, and proved equal.
- **Rollback:** reverse the documentation close before executable/test
  checkpoint `13a2748`, then helper checkpoint `4726ad1`, then published pre-
  card parent `fa79883`. Preserve runtime artifacts and restore no duplicate
  legacy source. The nine inherited `UNREFINED` findings remain a nonpassing
  documentation ceiling, not authority for unrelated lifecycle work.

## 2026-08-03T02:25:13-0400 — MIG-03F documentation/lifecycle acceptance

- **Canonical close:** added the adjacent implemented-owner README; updated the
  contract and neutral-library README; repaired architecture, functional
  inventory, coverage, documentation ownership, roadmap, handoff, complete
  Step `02` commands, and both troubleshooting routes; moved `MIG-03F` to
  `COMPLETED`; repaired every inbound lifecycle link; and recorded the complete
  executable evidence and risk ledger above. No executable, test, dependency,
  diagram, schema, or later-owner card changed in this close.
- **Exact migration-link result:** nonhistorical current-owner searches found
  no remaining active-card link or legacy Step `02` producer, validator, job,
  or direct-test path. Historical old-path planning/baseline text remains
  immutable evidence in the completed card and dated history rather than being
  rewritten as current topology.
- **Documentation gate:** the exact RUNBOOK documentation-only sequence ran.
  `git diff --check` passed. The documentation validator reported only the nine
  inherited `invalid card location` findings under `docs/tasks/UNREFINED/`;
  all ten MIG-03F-caused missing links are repaired. This is an expected-only
  nonpassing documentation result, not a green gate and not authority to change
  those inherited files.
- **Publication boundary:** stage only this impact-directed documentation and
  lifecycle close, commit it separately from executable/test checkpoint
  `13a2748`, push normally, and prove local `HEAD`, configured upstream, and
  live remote equality before selecting the next dependency-valid owner.

## 2026-08-03T02:33:30-0400 — MIG-03G JIT unit defined

- **Verified parent:** definition began only after `MIG-03F` documentation
  checkpoint `543eb8f` was clean, tracked/untracked empty, published, and equal
  across local `HEAD`, configured upstream, and the live remote branch. No
  index/recovery lock, card-ID/path collision, or mutable-lane overlap was
  found.
- **Live-DAG decision:** migrated `construct_canonical_BAM` now makes three
  identities eligible: `collect_canonical_BAM_QC_evidence`,
  `collect_RSeQC_paired_orientation_evidence`, and
  `mark_BAM_duplicates_with_Picard`. Define only the first identity in the
  canonical map, historical Step `02b`, because it is the smallest deterministic
  dependency-valid unit. This is not a claim that it is uniquely eligible.
  Step `03`, Step `04`, and later owner/review cards remain uncreated and
  unselected.
- **Frozen identity and surface:** `collect_canonical_BAM_QC_evidence` is
  evidence key `norad.evidence.collect_canonical_BAM_QC_evidence.v1`, alias
  `02b`, with final source/test homes under `src/norad/evidence/` and
  `tests/evidence/`. Producer/validator/job modes are `0755`/`0644`/`0644`,
  lines `163`/`186`/`87`, bytes `4,017`/`6,934`/`2,094`, and hashes
  `64221013...`, `b1f5ff7b...`, and `44e1573b...`; the migration card records
  full hashes. Direct shell/Python tests are modes `0755`/`0644`, lines
  `231`/`81`, bytes `7,628`/`2,617`, with full hashes frozen in the card.
- **Proposed bounded cutover:** five native/direct-test moves plus nine explicit
  Make, artifact, public-CLI, SLURM, roster, shared-report, coverage, and literal-
  fixture updates. Proposed production edits are producer help self-path,
  validator neutral-report depth, and job child path only. Architecture review
  must confirm this exact ceiling and the producer artifact path/hash
  transition before any execution planning.
- **Risks reserved for sequential review:** retain direct-final silent
  replacement, dry-run output-directory creation, shallow unused BAI admission,
  sample/path nonbinding, nonempty-success marker disagreement, no stable-input
  recheck, and absence of lock/stage/no-clobber/rollback/receipt/set validation.
  Reliability must decide predecessor-bearing quickcheck and flagstat fault
  oracles for partial or mixed-attempt bytes. Scheduler review must retain
  required `SLURM_SUBMIT_DIR`, exported `/tmp`, strict samtools load, tolerated
  module list, Bash `3.2` dry-run failure, and file-existence-only post-checks.
  These are characterized risks, not approved behavior or repair authority.
- **Review and evidence boundary:** create only `MIG-03G` and dedicated
  `REVIEW-ARCH-03G` → `REVIEW-REL-03G` → `REVIEW-UX-03G`, all unselected in
  `TODO`. Reviews remain sequential and read-only; task-specific planning,
  baseline, executable cutover, full gate, and documentation close remain later
  bounded slices. No executable/test file, dependency, runtime tool, scheduler,
  production input, scientific-review state, or biological evidence changed or
  ran in this definition slice.
- **Definition gate:** `git diff --check` passed and the exact documentation
  validator reported only the nine inherited `UNREFINED` card-location
  findings. This is an expected-only nonpassing documentation ceiling, not a
  green gate or authority for unrelated lifecycle changes. Publish this
  definition checkpoint and prove live remote equality before selecting the
  architecture review.

## 2026-08-03T02:38:01-0400 — REVIEW-ARCH-03G selected

- **Selection:** move only `REVIEW-ARCH-03G` to `IN_PROGRESS` and repair its
  reciprocal dependency/status links after definition checkpoint `417a2a5` was
  clean, tracked/untracked empty, published, and equal across local `HEAD`,
  configured upstream, and the live remote branch. `REVIEW-REL-03G`,
  `REVIEW-UX-03G`, and `MIG-03G` remain unselected in `TODO`; Step `03`, Step
  `04`, and later owner cards remain uncreated.
- **Review boundary:** this begins one read-only independent-in-time adversarial
  pass over live-DAG non-uniqueness, evidence-owner placement, exact five-move/
  nine-update ceiling, artifact path/hash continuity, direct and cross-owner
  test placement, explicit caller maps, wrapper necessity, cutover atomicity,
  coverage ownership, and reverse-order rollback. The same campaign agent
  performs the pass, so independent authorship is not claimed. Executable/test
  mutation and computational, runtime, scheduler, production, scientific-
  review, and biological evidence remain out of scope.

## 2026-08-03T02:41:50-0400 — REVIEW-ARCH-03G completed

- **High finding — moved-file edits were underspecified:** freeze exactly the
  producer usage self-path, validator neutral-report depth `parents[4]`, job
  child path, moved shell-test root `SCRIPT_DIR/../../..`, and moved Python-test
  root `parents[3]`. Those are the only edits inside the five moved files; any
  other moved-file edit reopens architecture review.
- **High finding — exact cutover ceiling confirmed:** one atomic direct cutover
  is fourteen logical files: five moves plus Make, artifact producer, artifact
  assertion, public CLI, SLURM, validation roster, validation-report map,
  coverage row, and literal Make fixture. Make adds exact final producer/job
  syntax inputs after both leave flat wildcards. A sixth move or tenth update
  reopens architecture review.
- **Medium finding — test and artifact ownership confirmed:** move the two
  direct suites with the evidence owner. Central scheduler, public-CLI,
  validation-roster, validation-report, artifact, coverage, and Make suites stay
  independent cross-owner consumers. Change only Step `02b` artifact producer
  path and reviewed post-help hash, with an exact existing-test assertion;
  public evidence and artifact identities, schemas, contents, ordering, and
  consumers remain unchanged.
- **Accepted architecture and rollback:** Step `02b` is first deterministic
  among three eligible owners, not uniquely eligible. Every known executable
  caller fits the atomic cutover, so no wrapper, duplicate, package, descriptor,
  schema, alias, symlink, or second owner is warranted. Roll back documentation,
  then owner/caller/coverage cutover, then old-path test baseline; keep Make and
  its oracle plus artifact path/hash/assertion changes together.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.

## 2026-08-03T02:45:49-0400 — REVIEW-REL-03G selected

- **Selection:** move only `REVIEW-REL-03G` to `IN_PROGRESS` and repair its
  reciprocal dependency/status links after architecture checkpoint `06a69c7`
  was clean, tracked/untracked empty, published, and equal across local `HEAD`,
  configured upstream, and the live remote branch. `REVIEW-UX-03G` and
  `MIG-03G` remain unselected in `TODO`; Step `03`, Step `04`, and later owner
  cards remain uncreated.
- **Review boundary:** this begins one read-only independent-in-time adversarial
  pass over predecessor-bearing quickcheck and flagstat faults, exact partial/
  mixed-attempt bytes, directory/sibling/unrelated-file residue, streams/exits,
  producer-validator mismatch, validator stable-input and publication behavior,
  scheduler defects, artifact path/hash continuity, coverage, and rollback.
  The same campaign agent performs the pass, so independent authorship is not
  claimed. Executable/test mutation and computational, runtime, scheduler,
  production, scientific-review, and biological evidence remain out of scope.

## 2026-08-03T02:50:45-0400 — REVIEW-REL-03G completed

- **High finding — producer mixed-attempt faults lacked exact oracles:** create
  one test-only old-path baseline across exactly the direct shell test, direct
  validator test, and central SLURM suite. Quickcheck exit `42` becomes producer
  exit `1`, replaces only quickcheck, and retains prior flagstat. Flagstat exit
  `43` follows a new PASS quickcheck, replaces prior flagstat with partial
  stdout, exposes child stderr, and propagates `43`. Both preserve an unrelated
  file and prove the absence of transaction/recovery artifacts without
  approving the behavior.
- **High finding — validator direct-path coverage was incomplete:** add explicit
  producer-success/validator-failure marker disagreement, arbitrary-CWD dry-run/
  execute/repeat byte parity, and post-build input mutation that exits `2` while
  preserving a valid predecessor report. Neutral publication mechanics remain
  owned by the shared suite rather than being duplicated.
- **High finding — scheduler stale-file false success lacked an oracle:** a
  mocked exit-`0` child that emits nothing still lets the Step `02b` wrapper
  succeed when both named files already exist; their stale bytes remain exact.
  Preserve this alongside required submit CWD, strict load/tolerated list,
  exported `/tmp`, Bash `3.2` dry-run, and child-exit behavior.
- **Accepted boundary:** add the PATH-only missing-samtools failure before
  output-directory creation. No fourth test file, production edit, harness,
  fixture, coverage-baseline, or documentation change enters the old-path
  baseline. The final five-move/nine-update architecture ceiling remains exact;
  target coverage may increase but may not regress below frozen rates or global
  covered-count floors.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.

## 2026-08-03T02:54:09-0400 — REVIEW-UX-03G selected

- **Selection:** move only `REVIEW-UX-03G` to `IN_PROGRESS` and repair its
  reciprocal dependency/status links after reliability checkpoint `56bac42`
  was clean, tracked/untracked empty, published, and equal across local `HEAD`,
  configured upstream, and the live remote branch. `MIG-03G` remains unselected
  in `TODO`; Step `03`, Step `04`, and later owner cards remain uncreated.
- **Review boundary:** this begins the final read-only independent-in-time pass
  over final producer direct/explicit-Bash/arbitrary-CWD journeys, validator
  dry-run/execute/repeat, scheduler submission and defaults, Make/focused-test
  commands, PATH and mixed-attempt diagnostics, recovery navigation, owner
  findability, implementation/evidence provenance, rollback, links, and local-
  only evidence ceilings. The same campaign agent performs the pass, so
  independent authorship is not claimed. Executable/test mutation and
  computational, runtime, scheduler, production, scientific-review, and
  biological evidence remain out of scope.

## 2026-08-03T02:57:02-0400 — REVIEW-UX-03G completed

- **High finding — active commands need complete final journeys:** at
  documentation close, replace every Step `02b` producer, validator, job, and
  focused-test path. The runbook must own root direct/explicit-Bash and absolute-
  CWD producer dry-run/execute forms plus explicit-interpreter validator dry-
  run/execute/repeat and absolute-CWD forms. Every producer command names
  sample, BAM, and output directory; samtools is PATH-only and dry-run creates
  the output directory.
- **High finding — scheduler and recovery guidance can overpromise:** submit
  the final mode-`0644` job from the checkout and expose defaults plus
  `SAMPLE_ID`, `BAM`, `OUTPUT_DIR`, `EXECUTE`, required `SLURM_SUBMIT_DIR`,
  forced `/tmp`, strict samtools load, tolerated module list, Bash `3.2` dry-run,
  and file-existence-only checks. Exit `0` can rediscover stale files. Preserve
  evidence files, unrelated files, and producer/job streams; authorize neither
  cleanup nor same-name retry before ownership and attempt provenance are known.
- **Medium finding — status and provenance need explicit ceilings:** producer
  exit `0` is not validator pass, validator exit `0` can publish failed rows,
  and Step `02b` remains non-gating. The README routes direct/central tests,
  final producer path/hash provenance, rollback, and the local fixture/mock
  ceiling; no real samtools, scheduler, cluster, production, scientific-review,
  or biological evidence is created.
- **Accepted findability:** one adjacent README plus contract, runbook,
  troubleshooting PATH and mixed-attempt routes, inventory, baseline, ownership
  map, architecture, roadmap, handoff, lifecycle, and audit updates provide
  complete navigation. Roll back docs, cutover, then old-path test baseline. No
  alias, wrapper, package, or compatibility path is justified.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.

## 2026-08-03T03:01:01-0400 — MIG-03G selected

- **Selection:** move only `MIG-03G` to `IN_PROGRESS` after usability-review
  checkpoint `7b86a5e` was clean, tracked/untracked empty, published, and equal
  across local `HEAD`, configured upstream, and the live remote branch. All
  three dedicated reviews are complete. Step `03`, Step `04`, and later owner
  cards remain uncreated and unselected; no recovery/index lock or mutable-lane
  overlap was found.
- **Execution boundary:** selection changes documentation/lifecycle state only.
  Task-specific planning must publish before the exact three-test old-path
  baseline begins; final owner cutover and full card-boundary validation remain
  later slices, followed by a separate documentation close. No executable/test
  path, harness, fixture, coverage baseline, dependency, runtime tool,
  scheduler, production input, scientific-review state, or biological evidence
  changed or ran.

## 2026-08-03T03:03:35-0400 — MIG-03G task-specific plan frozen

- **Git and slicing:** planning began from clean, tracked/untracked-empty,
  published, local/upstream/live-remote-equal selection `18703e1`, with no
  recovery/index lock or mutable-lane collision. Publish one exact three-test
  old-path baseline, one atomic fourteen-file cutover/executable card boundary,
  and one separate documentation close. Batch canonical links and small docs in
  that close; no later owner is preloaded.
- **Baseline boundary:** modify only the direct Step `02b` shell and validator
  tests plus the central SLURM suite. Add exact PATH, predecessor-bearing
  quickcheck/flagstat, marker mismatch, arbitrary-CWD repeat, post-build input-
  mutation, and stale-output false-success oracles. Run only syntax, those two
  direct suites, and scheduler cases selected by `step_02b_bam_qc`; no coverage
  or broad suite runs here.
- **Cutover boundary:** move only producer, validator, mode-`0644` job, and two
  direct tests; update only Make, artifact producer/assertion, public CLI,
  SLURM, roster, shared-report map, coverage row, and literal Make fixture.
  Production edits remain the reviewed help, report depth, and job child path.
  No docs, wrapper, alias, package, descriptor, schema, transaction, receipt,
  recovery marker, dependency, or later owner enters the slice.
- **Gate and truthful ceiling:** after minimal final-path checks, measure coverage
  with only the intentionally stale documentation assertion deselected, then run
  the exact RUNBOOK aggregate once with an explicit result JSON. The aggregate
  may report only that assertion with ten deferred Step `02b` links plus nine
  inherited `UNREFINED` locations; this is an expected-only nonpassing ceiling,
  not a green gate. Any other failure must be understood before commit.
- **Close and rollback:** the separate close adds the owner README, repairs the
  contract and all canonical/current/lifecycle links, records exact evidence,
  and runs the documentation-only gate. It may retain only nine inherited
  findings. Roll back docs, then cutover, then baseline; Git rollback never
  deletes runtime/production evidence, locks, logs, or recovery artifacts. No
  executable/test mutation or computational, scheduler, production,
  scientific-review, or biological evidence changed or ran in this plan slice.

## 2026-08-03T03:47:26-0400 — MIG-03G completed

- **Published slice chain:** plan `6a0377b`, test-only baseline `0904faf`, and
  executable/test checkpoint `2f186dd` were each clean, pushed, and equal across
  local HEAD, configured upstream, and the live remote before the next slice.
  The close containing this record is documentation/lifecycle only. No later
  owner or review card was created or selected.
- **Old-path baseline:** exactly three test files changed. Shell syntax and the
  complete direct shell suite passed; the validator reported `8` passes; and
  scheduler selection `step_02b_bam_qc` reported `9` passes with `103`
  deselected. The added PATH, quickcheck-`42`, flagstat-`43`, predecessor,
  marker-mismatch, arbitrary-CWD repeat, post-build mutation, and stale-wrapper
  oracles preserve exact exits, bytes, streams, unrelated files, and absence of
  transaction/recovery artifacts. They approve none of the exposed defects.
- **Atomic cutover:** exactly five files moved and nine callers/harnesses
  changed. Producer is mode/bytes/lines/hash `0755` / `4,062` / `163` /
  `92895b2dbd1117e72703e8261a66ce1a7cc34db6000280e23753cd5f9132101c`;
  validator `0644` / `6,934` / `186` /
  `fa25aeba0e6bd2e9fd0fc90229590cced4e6f44bb7b83310215500b9fb51fe96`;
  and job `0644` / `2,139` / `87` /
  `119e0cc7f8937a03c7e766c60aede204ae743ee735300eceda126333fe51a77c`.
  Shell test is `0755` / `12,106` / `350` /
  `03e1234e9e35f705aae25336e0c1b77336f92daf50ad9d671b59cde953bc2a0f`;
  validator test is `0644` / `6,616` / `196` /
  `77147a9e0c8822c26a63ac82a874c6dea662109fb771bcc82232908a3ee90b48`.
  Production edits remain the producer help path, neutral-report root depth,
  and scheduler child path.
- **Reviewed-plan omission and decision:** the first moved-validator test run
  failed collection because its old direct roster-oracle import no longer
  resolved from the deeper directory. Exact-loading the unchanged
  `tests/validation_roster_expectations.py` by repository path within that same
  moved test was the minimum functional relocation fix. It added no logical
  file, package identity, `PYTHONPATH`, production behavior, or roster change;
  the rerun passed `8`. The deviation is explicit rather than folded into a
  false claim that only two moved-test path edits were sufficient.
- **Minimal final-path acceptance:** producer/job/shell-test syntax, the full
  moved shell suite, `8` validator tests, `9` scheduler cases, and `12` exact
  public-CLI/Make/roster/report/artifact assertions passed. Exact searches found
  one final owner per basename and no live non-documentation legacy source,
  wrapper, alias, duplicate, symlink, package marker, descriptor, schema,
  receipt, recovery marker, dependency change, or later-owner preload.
- **Coverage decision:** the complete serial Python measurement deselected only
  the intentionally stale documentation assertion and passed `1,113` tests
  with `17` skips. Step `02b` improved from `102/110` lines and `23/30` branches
  to `103/110` and `24/30`; global covered counts improved from `9504/11677`
  and `3327/4756` to `9505/11677` and `3328/4756`. Every non-target row was
  exact, the baseline equals the measured snapshot, and standalone policy
  comparison passed without weakening a floor.
- **Aggregate-gate truth:** the first exact sandboxed gate passed static and
  stopped on unavailable Bioconductor DNS metadata after preserving the
  inherited malformed `macos` warning. The network-enabled rerun used the
  existing project library and installed, restored, deleted, and updated
  nothing. Static passed in `0.120s`, shell in `85.781s`, guarded R in
  `364.185s`, and report runtime in `302.007s`. Python reported `1,113` passes
  and `17` skips before its sole failure listed exactly ten deferred migration
  links plus nine inherited `UNREFINED` locations. The aggregate is not green.
- **Preserved risk boundary:** direct-final quickcheck/flagstat writes,
  mixed-attempt residue, quickcheck status normalization, shallow unused BAI
  admission, sample/path nonbinding, producer/validator marker mismatch,
  validator-zero failed rows, and zero-count acceptance remain characterized.
  Scheduler required-submit-CWD, forced `/tmp`, Bash `3.2` empty-array failure,
  strict samtools load, tolerated module-list diagnostics, dry-run directory
  creation, and stale-file false success also remain defects. Step `02b`
  remains non-gating; producer, validator, and scheduler success are distinct.
- **Documentation and provenance decision:** add the adjacent README, correct
  the contract, owner inventory, architecture, coverage owner, documentation
  ownership, roadmap, handoff, runbook, troubleshooting, card, review backlink,
  and all ten migration links. Artifact evidence changes only to the final
  producer path/hash; identities, schemas, contents, ordering, reconciliation,
  consumers, semantic DAG edges, and evidence status remain unchanged. No
  diagram edit is warranted.
- **Close gate, evidence ceiling, and rollback:** the documentation-only gate
  for this final tree reported exactly the nine inherited `UNREFINED` location
  findings and no migration-caused failure; that expected-only result is not a
  passing gate. Reverse the documentation close, `2f186dd`, then `0904faf`;
  Git rollback never deletes runtime artifacts, evidence files, logs, locks, or
  recovery state and never restores a duplicate flat owner.
  No real samtools run, scheduler submission, cluster/production input,
  dependency action, scientific review, or biological evidence was created.

## 2026-08-03T03:53:26-0400 — MIG-03H JIT unit defined

- **Verified parent:** definition began only after `MIG-03G` documentation
  checkpoint `eafec29` was clean, tracked/untracked empty, published, and equal
  across local `HEAD`, configured upstream, and the live remote branch. No
  index/recovery lock, card-ID/path collision, or mutable-lane overlap was
  found.
- **Live-DAG decision:** both direct prerequisites for
  `collect_RSeQC_paired_orientation_evidence` are migrated, and
  `mark_BAM_duplicates_with_Picard` is independently eligible. Define only the
  first identity in the canonical map, historical Step `03`, because it is the
  smallest deterministic dependency-valid unit. This is not a claim that it is
  uniquely eligible. Step `04` and later owner/review cards remain uncreated
  and unselected.
- **Frozen identity and surface:** Step `03` is evidence key
  `norad.evidence.collect_RSeQC_paired_orientation_evidence.v1`, with final
  source/test homes under `src/norad/evidence/` and `tests/evidence/`.
  Producer/validator/job are each mode `0644`, lines `209`/`183`/`123`, bytes
  `6,804`/`6,888`/`4,068`, and hashes `9bcb3ddf...`, `b4ade297...`, and
  `d1a21a63...`; the migration card records full hashes. Direct shell/Python
  tests are each mode `0644`, lines `250`/`79`, bytes `9,254`/`2,615`, with
  full hashes frozen in the card.
- **Proposed bounded cutover:** five native/direct-test moves plus nine explicit
  Make, artifact, public-CLI, SLURM, roster, shared-report, coverage, and
  literal-fixture updates. Proposed production edits are producer usage self-
  path, validator neutral-report depth, and job child path only. Architecture
  review must confirm this exact ceiling, both demo targets, test-local roster
  loading, and the producer artifact path/hash transition before planning.
- **Risks reserved for sequential review:** retain CWD-sensitive `.venv`/PATH
  RSeQC selection, shallow unused BAI admission, sample/input nonbinding,
  direct-final silent replacement, partial or empty predecessor truncation,
  nonempty-only producer success, no lock/stage/no-clobber/stable-input recheck/
  receipt/rollback, and the producer/validator semantic boundary. Scheduler
  review must retain submit-CWD fallback, exported `/tmp`, optional virtualenv,
  tolerated module listing, Bash `3.2` dry-run failure, dry-run log mutation,
  and stale-nonempty-file false success. Mechanical orientation fractions must
  not be promoted into biological strandedness or manifest policy.
- **Review and evidence boundary:** create only `MIG-03H` and dedicated
  `REVIEW-ARCH-03H` → `REVIEW-REL-03H` → `REVIEW-UX-03H`, all unselected in
  `TODO`. Reviews remain sequential and read-only; task-specific planning,
  baseline, executable cutover, full gate, and documentation close remain later
  bounded slices. No executable/test file, dependency, runtime tool, scheduler,
  production input, scientific-review state, or biological evidence changed or
  ran in this definition slice.
- **Definition gate:** `git diff --check` passed and the documentation validator
  reported only the nine inherited `UNREFINED` card-location findings. This is
  an expected-only nonpassing documentation ceiling, not a green gate or
  authority for unrelated lifecycle changes. Publish this definition checkpoint
  and prove live remote equality before selecting the architecture review.

## 2026-08-03T03:58:43-0400 — REVIEW-ARCH-03H selected

- **Selection:** move only `REVIEW-ARCH-03H` to `IN_PROGRESS` and repair its
  reciprocal dependency/status links after definition checkpoint `0cd872e` was
  clean, tracked/untracked empty, published, and equal across local `HEAD`,
  configured upstream, and the live remote branch. `REVIEW-REL-03H`,
  `REVIEW-UX-03H`, and `MIG-03H` remain unselected in `TODO`; Step `04` and
  later owner cards remain uncreated.
- **Review boundary:** this begins one read-only independent-in-time adversarial
  pass over live-DAG non-uniqueness, two-predecessor evidence-owner placement,
  exact five-move/nine-update ceiling, demo and artifact path/hash continuity,
  direct and cross-owner test placement, explicit caller maps, wrapper
  necessity, cutover atomicity, coverage ownership, and reverse-order rollback.
  The same campaign agent performs the pass, so independent authorship is not
  claimed. Executable/test mutation and computational, runtime, scheduler,
  production, scientific-review, and biological evidence remain out of scope.

## 2026-08-03T04:01:14-0400 — REVIEW-ARCH-03H completed

- **High finding — moved-test loading needed an explicit boundary:** freeze the
  producer usage path, validator report-owner depth `parents[4]`, scheduler
  child, shell-test root `SCRIPT_DIR/../../..`, and Python-test root
  `parents[3]`. The moved Python test must exact-load the unchanged root roster
  oracle by repository path; package creation or `PYTHONPATH` mutation is not
  warranted. Any other moved-file edit reopens architecture review.
- **High finding — exact cutover ceiling confirmed:** one atomic direct cutover
  is fourteen logical files: five moves plus Make, artifact producer, artifact
  assertion, public CLI, SLURM, validation roster, validation-report map,
  coverage row, and literal Make fixture. Make adds exact final producer/job
  syntax inputs and moves direct-test and both demo paths. A sixth move or tenth
  update reopens architecture review.
- **Medium finding — test and artifact ownership confirmed:** move the two
  direct suites with the evidence owner. Central scheduler, public-CLI,
  validation-roster, validation-report, artifact, coverage, and Make suites stay
  independent cross-owner consumers. Change only Step `03` artifact producer
  path and reviewed post-usage hash, with an exact existing-test assertion;
  public evidence and artifact identities, schemas, contents, ordering,
  scientific meaning, and consumers remain unchanged.
- **Accepted architecture and rollback:** Step `03` is first deterministic
  among two eligible owners, not uniquely eligible, and both direct
  prerequisites are migrated. Every known executable caller fits the atomic
  cutover, so no wrapper, duplicate, package, descriptor, schema, alias,
  symlink, or second owner is warranted. Roll back documentation, then owner/
  caller/coverage cutover, then old-path test baseline; keep Make/oracle and
  artifact path/hash/assertion changes together.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.
- **Card-boundary gate:** `git diff --check` passed and the documentation
  validator reported only the nine inherited `UNREFINED` card-location
  findings. That expected-only result is not a green gate; no architecture-
  review-caused finding remains.

## 2026-08-03T04:03:41-0400 — REVIEW-REL-03H selected

- **Selection:** move only `REVIEW-REL-03H` to `IN_PROGRESS` and repair its
  reciprocal dependency/status links after architecture-completion checkpoint
  `350223f` was clean, tracked/untracked empty, published, and equal across
  local `HEAD`, configured upstream, and the live remote branch.
  `REVIEW-UX-03H` and `MIG-03H` remain unselected in `TODO`; Step `04` and later
  owner cards remain uncreated.
- **Review boundary:** this begins one read-only independent-in-time adversarial
  pass over producer direct-final truncation and partial bytes, validator
  structure/tolerance/publication, scheduler venv/tool/CWD/dry-run/stale-output
  states, exact streams/exits/residue, artifact and coverage continuity, and
  recoverable commit rollback. The same campaign agent performs the pass, so
  independent authorship is not claimed. Executable/test mutation and
  computational, real-RSeQC, scheduler, production, scientific-review, and
  biological evidence remain out of scope.

## 2026-08-03T04:08:19-0400 — REVIEW-REL-03H completed

- **High finding — predecessor-bearing producer faults lacked exact oracles:**
  add one test-only old-path baseline across exactly the direct shell test,
  direct validator test, and central SLURM suite. Partial RSeQC stdout followed
  by exit `42` propagates `42`, replaces a predecessor with partial bytes,
  preserves an unrelated file, and exposes child stderr. Empty exit `0` makes
  the producer exit `1`, truncates the predecessor to empty, preserves the
  unrelated file, and emits the producer diagnostic. Both prove the absence of
  transaction/recovery artifacts without approving the behavior.
- **High finding — producer/validator and stable-input coverage was incomplete:**
  add a nonempty malformed report that producer accepts but validator publishes
  as failed evidence; explicit-binary arbitrary-CWD producer use; arbitrary-CWD
  validator dry-run/execute/repeat byte parity; and post-build input mutation
  that exits `2` while preserving a valid predecessor report. Neutral shared-
  publication fault mechanics remain in the neutral report suite.
- **High finding — scheduler tool and stale-file states lacked direct oracles:**
  freeze repository `.venv` preference and activation, PATH fallback, dry-run
  `logs/` creation without scientific output, and an exit-`0` child that emits
  nothing while a stale nonempty report satisfies the wrapper's `-s` check and
  remains byte-exact. Existing submit-CWD fallback, tolerated module list,
  exported `/tmp`, Bash `3.2`, invalid mode, and child-exit oracles remain.
- **Accepted boundary:** no fourth test file, production edit, fixture, coverage
  baseline, documentation, dependency, or later owner enters the old-path
  baseline. The architecture-reviewed five-move/nine-update ceiling stays
  exact; target coverage may increase but cannot regress below frozen rates or
  global covered-count floors.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.
- **Card-boundary gate:** `git diff --check` passed and the documentation
  validator reported only the nine inherited `UNREFINED` card-location
  findings. That expected-only result is not a green gate; no reliability-
  review-caused finding remains.

## 2026-08-03T04:11:14-0400 — REVIEW-UX-03H selected

- **Selection:** move only `REVIEW-UX-03H` to `IN_PROGRESS` and repair its
  reciprocal dependency/status links after reliability-completion checkpoint
  `1d1de19` was clean, tracked/untracked empty, published, and equal across
  local `HEAD`, configured upstream, and the live remote branch. `MIG-03H`
  remains unselected in `TODO`; Step `04` and later owner cards remain
  uncreated.
- **Review boundary:** this begins one read-only independent-in-time journey
  pass over Bash-only producer and explicit-interpreter validator commands,
  arbitrary CWD, `.venv`/PATH selection, dry-run effects, scheduler submission
  and demo targets, partial/stale evidence preservation, focused checks,
  implementation provenance, mechanical-orientation language, and rollback.
  The same campaign agent performs the pass, so independent authorship is not
  claimed. Executable/test mutation and computational, real-RSeQC, scheduler,
  production, scientific-review, and biological evidence remain out of scope.

## 2026-08-03T04:18:23-0400 — REVIEW-UX-03H completed

- **Verified parent:** selection checkpoint `c0c60da` was clean, tracked/
  untracked empty, published, and equal across local `HEAD`, configured
  upstream, and the live remote branch before the read-only journey pass.
- **High finding — final commands need explicit execution context:** batch all
  active producer, validator, job, demo, and focused-test path repairs into the
  documentation close. Root producer forms invoke the mode-`0644` final file
  through Bash with explicit sample, BAM, BED12, output, and RSeQC binary.
  Arbitrary-CWD use requires absolute producer, input, output, and binary paths
  because default `.venv` lookup is CWD-relative. Dry-run validates those
  inputs but creates neither output directory nor report.
- **High finding — validator and scheduler effects must remain distinct:** use
  an explicit interpreter for validator dry-run, execute, repeat, and absolute-
  CWD forms; create its output parent before execute; and distinguish exit `0`
  with failed rows from exit `2` without new publication. Submit the final job
  from the checkout and document `SLURM_SUBMIT_DIR`, `/tmp`, six overrides,
  venv activation, `.venv`/PATH choice, tolerated module listing, dry-run log
  creation, Bash `3.2` failure, and stale-report false success. Local mock demo
  targets can create logs but prove no scheduler or cluster behavior.
- **High finding — recovery must preserve rather than bless direct-final
  defects:** no producer lock, stage, backup, receipt, input recheck, or rollback
  exists. Partial/empty replacement and wrapper rediscovery of stale nonempty
  output remain characterized defects. Preserve native report bytes, unrelated
  files, both streams, job identity/logs, selected tool/path, BAM/BAI, and BED12
  before retry or cleanup; Git rollback does not recover runtime artifacts.
- **Medium finding — evidence and provenance require a hard ceiling:** producer
  exit `0` proves only nonempty output; validator exit `0` can publish failed
  rows. Fractions remain non-gating mechanical paired-read orientations, not
  transcript strand, biological sense/antisense, approved strandedness policy,
  or manifest mutation. The README must route exact implementation path/hash,
  focused direct and central tests, reverse-order rollback, and fixture/mock
  local-only evidence. Existing operational observations are not migration,
  scheduler, cluster, production, scientific-review, or biological proof.
- **Disposition and boundary:** the reviewed corrections fit the frozen owner,
  public interfaces, five-move/nine-update ceiling, and separate documentation
  close. No alias, compatibility copy, package, dependency action, or escalation
  is required. This was an independent-in-time pass by the same campaign agent;
  independent authorship is not claimed. No executable/test mutation or
  computational, real-RSeQC, scheduler, production, scientific-review, or
  biological run occurred.
- **Card-boundary gate:** run `git diff --check` and the complete documentation
  validator on the assembled review close. Report the inherited nine
  `UNREFINED` card-location findings as a nonpassing expected-only ceiling, not
  a green gate, and leave them unchanged.

## 2026-08-03T04:24:18-0400 — MIG-03H selected

- **Selection:** move only `MIG-03H` to `IN_PROGRESS` and repair its reciprocal
  lifecycle/status links after usability-completion checkpoint `76923e1` was
  clean, tracked/untracked empty, published, and equal across local `HEAD`,
  configured upstream, and the live remote branch. Step `04` and every later
  owner/review card remain uncreated and unselected.
- **Execution boundary:** task-specific planning is next. No source, test,
  fixture, Make, coverage, artifact, dependency, runtime, scheduler,
  production, scientific-review, or biological evidence changed or ran in
  this selection slice. The reviewed five-move/nine-update ceiling and three-
  checkpoint delivery sequence remain binding.

## 2026-08-03T04:26:47-0400 — MIG-03H task-specific plan frozen

- **Git and slicing:** planning began from clean, tracked/untracked-empty,
  published, local/upstream/live-remote-equal selection `13b8a7e`, with no
  recovery/index lock or mutable-lane collision. Publish one exact three-test
  old-path baseline, one atomic fourteen-file cutover/executable card boundary,
  and one separate documentation close. Batch canonical links and small docs in
  that close; no later owner is preloaded.
- **Baseline boundary:** modify only the direct Step `03` shell and validator
  tests plus the central SLURM suite. Add exact partial/empty predecessor,
  malformed nonempty, arbitrary-CWD, post-build mutation, venv/PATH selection,
  dry-run logs, and stale-output false-success oracles. Run only syntax, those
  two direct suites, and scheduler cases selected by the Step `03` basename;
  no coverage or broad suite runs here.
- **Cutover boundary:** move only producer, validator, mode-`0644` job, and two
  direct tests; update only Make, artifact producer/assertion, public CLI,
  SLURM, roster, shared-report map, coverage row, and literal Make fixture.
  Production edits remain the reviewed usage path, report depth, and job child
  path; direct-test edits remain the reviewed roots, final targets, and private
  exact roster load. No docs, wrapper, alias, package, descriptor, schema,
  transaction, receipt, recovery marker, dependency, or later owner enters the
  slice.
- **Gate and truthful ceiling:** after minimal final-path checks, measure
  coverage with only the intentionally stale documentation assertion
  deselected, then run the exact RUNBOOK aggregate once with an explicit result
  JSON. The aggregate may report only that assertion with ten deferred Step
  `03` links plus nine inherited `UNREFINED` locations; this is an expected-
  only nonpassing ceiling, not a green gate. Any other failure must be
  understood before commit.
- **Close and rollback:** the separate close adds the owner README, repairs the
  contract and all canonical/current/lifecycle links, records exact evidence,
  and runs the documentation-only gate. It may retain only nine inherited
  findings. Roll back docs, then cutover, then baseline; Git rollback never
  deletes runtime/production evidence, locks, logs, or recovery artifacts. No
  executable/test mutation or computational, real-RSeQC, scheduler,
  production, scientific-review, or biological evidence changed or ran in
  this plan slice.

## 2026-08-03T05:10:28-0400 — MIG-03H executable evidence and documentation/lifecycle close

- **Verified close parent and boundary:** documentation work began from clean,
  tracked/untracked-empty, published, local/upstream/live-remote-equal
  executable/test checkpoint
  `24ed9b1ec98f63944a963628907a4c310558a420`, with no recovery/index lock or
  overlapping mutable-lane collision. The close remains documentation and
  lifecycle only. It adds no executable/test/configuration/fixture/schema/
  dependency change and no later-owner card or review.
- **Published baseline and cutover:** test-only reliability baseline
  `88f499487ea69fb0b884bec3572af9808912e28a` changed exactly the direct shell
  test, direct validator test, and central scheduler suite. Executable/test
  checkpoint `24ed9b1` moved exactly producer, validator, mode-`0644` job, and
  two direct tests, then updated exactly the nine reviewed callers/harnesses.
  No legacy executable/test path, wrapper, alias, duplicate, package marker,
  descriptor, schema, transaction, receipt, recovery marker, or later-owner
  preload remains.
- **Final provenance:** producer is mode `0644`, `6,857` bytes, `209` lines,
  SHA-256
  `01aa11cc60d9042ac541cfe445aec3e562a198a761c45449e82e96b7b9ab0784`;
  validator is mode `0644`, `6,888` bytes, `183` lines, SHA-256
  `d92eac61eeedec553b2541e446256836406f81c75e5fb8f6b12369f11bf58e67`;
  and the job is mode `0644`, `4,121` bytes, `123` lines, SHA-256
  `d65fde6e7cb3d0ebccf76cb7101dffaf0ea42edfa49e1387d4cac3c3568d8c08`.
  Moved shell test is mode `0644`, `14,931` bytes, `400` lines, SHA-256
  `123d464fa26d623aacacff5a5b7ebb316051bc8f984a26bdff630adeefd2bf80`;
  moved validator test is mode `0644`, `6,493` bytes, `189` lines, SHA-256
  `0b1b3802e65309856b5aa04f33682b6f4ce193453dde0a8440d7578cb98734a5`.
- **Focused and coverage evidence:** producer/job/test syntax, the complete
  moved shell suite, `8` validator cases, and `8` Step `03` scheduler cases
  with `108` unrelated cases deselected passed. Artifact path/hash, public
  CLI/Make, complete validation roster, and shared-report/inventory targeting
  contributed `143` passing wiring assertions. Deterministic serial coverage
  passed `1,120` tests with `17` skips and only the intentionally stale
  documentation assertion deselected. The validator improved to `103/115`
  lines and `28/34` branches; global measurement improved to `9508/11677`
  lines and `3331/4756` branches. Every non-target row remained exact and the
  standalone policy comparison passed.
- **Aggregate gate was not fully green:** the first sandboxed exact gate passed
  static preflight and stopped when guarded R could not resolve Bioconductor
  metadata, while preserving the inherited malformed `macos` warning. The
  network-enabled rerun used only the existing project R library and installed,
  restored, deleted, and updated no dependency. Static preflight passed in
  `0.118s`, shell contracts in `116.947s`, guarded R in `432.217s`, and report
  runtime in `325.043s`. Python ran `1,120` passes and `17` skips before its
  sole documentation assertion failed; aggregate elapsed time was `455.541s`.
  That failure listed exactly five stale inventory links, five stale owner-
  contract links, and nine inherited `UNREFINED` locations. Result JSON remains
  `/private/tmp/norad-mig-03h-validation.json`; the retained Python log is
  `/var/folders/y0/bg0yx6g54bs0403dn0x_k28w0000gn/T/norad-validation-python-coverage-gqps7nta.log`.
  This is an expected-only nonpassing ceiling, never a green-gate claim.
- **Canonical documentation decisions:** add one adjacent README; make the
  owner contract implemented-current; update current architecture, functional
  inventory, test baseline, documentation ownership, roadmap, handoff, Step
  `03` runbook commands, and troubleshooting routes; batch all ten migration
  links here; move `MIG-03H` to `COMPLETED`; and repair every inbound lifecycle
  link. The final paths require Bash for the producer, an explicit interpreter
  for the validator, absolute paths outside the checkout, and explicit
  scheduler overrides. No diagram changes because semantic DAG edges and
  public data flow are unchanged.
- **Preserved risks and evidence meaning:** the producer still writes directly
  to the final report with silent replacement, partial/empty predecessor
  truncation, nonempty-only success, and no lock, stage, no-clobber rule,
  stable-input recheck, receipt, rollback, or recovery artifact. Validator exit
  `0` may publish failed rows; exit `2` publishes nothing new. Scheduler CWD/
  venv/PATH selection, exported `/tmp`, tolerated module listing, dry-run
  `logs/` mutation, Bash `3.2` dry-run failure, and stale-nonempty-report false
  success remain characterized defects, not approved behavior. Operators must
  preserve report bytes, unrelated files, streams, job identity/logs, selected
  tool/path, BAM/BAI, and BED12 before retry or cleanup.
- **Scientific and environment ceiling:** the three fractions remain non-
  gating mechanical paired-read orientations. They do not establish transcript
  strand, biological sense/antisense, a forward/reverse tool option, approved
  manifest policy, or manifest mutation. Historical cohort observations remain
  operational history rather than migration evidence. No real RSeQC,
  scheduler, cluster, production, scientific-review, or biological proof was
  created.
- **Documentation gate and lifecycle result:** `git diff --check` passed. The
  complete documentation validator reported exactly the nine inherited
  `UNREFINED` card-location findings and no migration-caused finding after all
  ten final-path repairs and lifecycle links were assembled. This is still a
  nonpassing expected-only result, not green and not authority to alter the
  inherited cards. No later owner is selected; refresh the live DAG only after
  this close is committed, published, and proved equal.
- **Rollback decision:** revert this documentation/lifecycle close first,
  executable/test checkpoint `24ed9b1` second, and test baseline `88f4994`
  third; task-specific plan is `3388466`. Keep Make/oracle and artifact path/
  hash/assertion changes together. Git rollback never deletes, restores, or
  authenticates runtime evidence, production data, locks, logs, or recovery
  artifacts.

## 2026-08-03T05:23:22-0400 — MIG-03I and sequential reviews defined

- **Verified definition parent:** `MIG-03H` documentation/lifecycle close
  `ef990c892626ba720b79b8998a783cabf2360cab` was clean, tracked/untracked
  empty, published, and equal across local `HEAD`, configured upstream, and the
  server-acknowledged remote-tracking ref, with `0/0` divergence. No recovery,
  rebase, merge, cherry-pick, or index-lock state and no mutable-lane collision
  was present.
- **Live-DAG decision:** only `mark_BAM_duplicates_with_Picard` is eligible.
  Its sole direct artifact predecessor, migrated `construct_canonical_BAM`, is
  complete; `split_N_cigar_reads_with_GATK` still requires Step `04` and is not
  eligible. Define only `MIG-03I` and `REVIEW-ARCH-03I` → `REVIEW-REL-03I` →
  `REVIEW-UX-03I`, all unselected in `TODO`. No Step `05` or later owner/review
  card is created or preloaded.
- **Frozen identity and native provenance:** semantic stage identity is
  `mark_BAM_duplicates_with_Picard`, machine key
  `norad.stage.mark_BAM_duplicates_with_Picard.v1`, alias `04`, final source
  home `src/norad/stages/mark_BAM_duplicates_with_Picard/`, and mirrored test
  home `tests/stages/mark_BAM_duplicates_with_Picard/`. Mode-`0644` producer,
  validator, and job total `22,336` bytes and `679` lines, with SHA-256 values
  `cd1b52c2e2a2ba1a5de93efd1b32c11f753616b28f527567780d42fe5b88aa41`,
  `8b1a4bf54731281c5636d16a27292589864a446d23e1d3b459043ea30b3152a6`,
  and `c0be74fc58b8ef343aaa48d62f9bc118ea08e652d3f28ba07b3c744295baa684`.
  The two mode-`0644` direct-test hashes are
  `c92426b4e7594795e5f6a3b3f00c1174418aa870b17ffc5d576f0f7bc63283a7`
  and `e3ed5075abf29b3715b4f2dfa0ecbf95f76f4f079419083dbcd7c9985c4b77d6`.
- **Candidate architecture boundary:** propose exactly five moves plus ten
  caller/harness updates. The Step `04`-specific tenth update is the independent
  neutral BAM-helper caller matrix; all other path owners mirror the preceding
  owner cutover pattern. Proposed path-only producer, dual-loader validator,
  and job hashes are
  `b845aa910ccabaf8799e000dc62e8939b0203c7848511524fadf51c79292eb2d`,
  `17a541e7b9d9822df5de0721747187621035f0dae7aaa0f1a35995f727bfb178`,
  and `4e41c4cd7ee1ec36169797bfc4897968e38010e78aec35d16c6921dfd55217fc`.
  Architecture review must confirm the full fifteen-logical-file ceiling,
  moved-test roots/imports, artifact assertion, and no-wrapper decision before
  executable planning.
- **Reliability risks reserved for review:** preserve, do not approve, direct-
  final Picard BAM/metrics writes, quickcheck-before-index, silent replacement,
  and absent lock/stage/no-clobber/stable-input recheck/receipt/rollback/all-or-
  none transaction. Controlled Picard, quickcheck, index, empty-output, and
  post-check faults must disposition partial/new/prior BAM/BAI/metrics bytes.
  Scheduler review must cover submit-CWD, strict modules, `PICARD`, Java
  override/`JAVA_HOME`/PATH/version behavior, samtools PATH, exported `/tmp`,
  tolerated module listing, dry-run logs, Bash `3.2`, unset-`JAVA_HOME`, child
  exits, and stale-three-file false success. Validator review must preserve
  both neutral exact loaders, five rows, stable-input behavior, and exit `0`
  failed evidence versus exit `2` nonpublication.
- **Coverage/artifact/evidence boundary:** starting Step `04` validator coverage
  is `144/155` lines and `33/42` branches; global coverage is `9508/11677`
  lines and `3331/4756` branches. Only implementation producer path/hash may
  change; four Step `04` public artifact identities, schemas, contents,
  ordering, consumers, and marked-BAM meaning remain fixed. No executable/test,
  Make, fixture, artifact, coverage, dependency, runtime, scheduler,
  production, scientific-review, or biological evidence changed or ran in this
  definition slice.
- **Sequential review and stop boundary:** architecture reviews DAG/path/helper/
  artifact ownership first; reliability reviews exact fault/residue parity
  second; usability reviews commands, tool/temp selection, diagnostics,
  preservation, provenance, and rollback third. Independent-in-time passes are
  by the same campaign agent, so independent authorship will not be claimed.
  Publish and prove this four-card definition checkpoint equal before selecting
  only `REVIEW-ARCH-03I`.
- **Definition gate:** `git diff --check` passed and the complete documentation
  validator reported exactly the nine inherited `UNREFINED` card-location
  findings. No MIG-03I/review path, anchor, dependency, cycle, orphan, or other
  definition-caused finding remains. This expected-only result is still
  nonpassing, not a green gate and not authority to alter inherited lifecycle
  state.

## 2026-08-03T05:26:23-0400 — REVIEW-ARCH-03I selected

- **Selection:** move only `REVIEW-ARCH-03I` to `IN_PROGRESS` and repair its
  reciprocal dependency/status links after definition checkpoint `86419d3` was
  clean, tracked/untracked empty, published, and equal across local `HEAD`,
  configured upstream, and the live remote branch. `REVIEW-REL-03I`,
  `REVIEW-UX-03I`, and `MIG-03I` remain unselected in `TODO`; Step `05` and
  later owner cards remain uncreated.
- **Review boundary:** this begins one read-only independent-in-time adversarial
  pass over unique live-DAG eligibility, stage-owner placement, exact five-
  move/ten-update ceiling, dual-neutral-loader ownership, direct and cross-
  owner test placement, explicit caller maps, wrapper necessity, cutover
  atomicity, artifact path/hash continuity, coverage ownership, and reverse-
  order rollback. The same campaign agent performs the pass, so independent
  authorship is not claimed. Executable/test mutation and computational,
  runtime, scheduler, production, scientific-review, and biological evidence
  remain out of scope.
- **Selection gate:** after repairing both sides of the moved lifecycle edge,
  `git diff --check` passed and the documentation validator reported only the
  nine inherited `UNREFINED` card-location findings. The first diagnostic pass
  caught and the final tree fixes the architecture-card link to the still-TODO
  reliability card; no selection-caused finding remains. The inherited result
  is nonpassing, not green.

## 2026-08-03T05:30:40-0400 — REVIEW-ARCH-03I completed

- **Verified parent:** selection checkpoint `d277bc3` was clean, tracked/
  untracked empty, published, and equal across local `HEAD`, configured
  upstream, and the live remote branch before the read-only architecture pass.
- **High finding — moved-test and dual-loader depths needed an explicit
  boundary:** freeze only the producer usage self-path, both validator neutral-
  library roots at `parents[4]`, scheduler child, shell-test root
  `SCRIPT_DIR/../../..`, and Python-test root `parents[3]`. The moved Python
  test exact-loads unchanged `tests/validation_roster_expectations.py` by
  repository path; package creation and `PYTHONPATH` mutation are rejected. Any
  other moved-file edit reopens architecture review.
- **High finding — exact cutover ceiling confirmed:** one atomic direct cutover
  contains five moves plus ten updates: Make, artifact producer, artifact
  assertion, public CLI, SLURM, validation roster, validation-report map,
  neutral BAM-helper caller matrix, coverage row, and literal Make fixture. The
  BAM-helper matrix is the Step `04`-specific tenth update. Both final shell
  assets become explicit static/smoke inputs; Step `04` has no Make demo target.
  An eleventh update or sixth move reopens review.
- **Medium finding — helper, test, artifact, and documentation ownership
  confirmed:** the final validator retains private exact loads of both neutral
  libraries, and Step `05` stays an unchanged flat peer caller of the neutral
  BAM helper. Direct shell/validator tests move with the stage; central suites
  stay cross-owner consumers. Artifact evidence changes only the implementation
  path and reviewed producer hash
  `b845aa910ccabaf8799e000dc62e8939b0203c7848511524fadf51c79292eb2d`;
  evidence ID, four artifact identities, schemas, contents, ordering, meaning,
  and consumers remain fixed. The canonical-BAM owner README is an impacted
  documentation close target because it names the Step `04` helper test/path.
- **Accepted architecture and rollback:** Step `04` is uniquely live-DAG-
  eligible; Step `05` remains blocked, uncreated, and unselected. Exhaustive
  nonhistorical path inspection found all executable callers repository-owned
  and compatible with the fifteen-logical-file atomic cutover. No wrapper,
  duplicate, alias, symlink, package, descriptor, schema, helper extraction,
  or second owner is warranted. Roll back documentation first, then owner/
  caller/helper-matrix/coverage cutover, then any reliability baseline; keep
  Make/oracle and artifact path/hash/assertion together.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, Make, fixture, dependency, runtime, scheduler, production,
  scientific-review, or biological evidence changed or ran. Reliability and
  usability reviews plus `MIG-03I` remain unselected.
- **Card-boundary gate:** `git diff --check` passed and the complete
  documentation validator reported only the nine inherited `UNREFINED` card-
  location findings. This remains a nonpassing expected-only ceiling, not a
  green gate; no architecture-review path, lifecycle, dependency, or anchor
  finding remains.

## 2026-08-03T05:34:25-0400 — REVIEW-REL-03I selected

- **Selection:** after published architecture-completion checkpoint `403fdf5`
  was clean, tracked/untracked empty, and equal across local `HEAD`, configured
  upstream, and the live remote branch, move only `REVIEW-REL-03I` to
  `IN_PROGRESS` and repair both reciprocal lifecycle links. `REVIEW-UX-03I`
  and `MIG-03I` remain unselected in `TODO`; Step `05` and all later owner cards
  remain uncreated.
- **Review boundary:** select one documentation-only independent-in-time
  adversarial pass over direct-final three-output fault residue, tool and temp
  selection, stable-input enforcement, validator parity, scheduler behavior,
  evidence limits, and reverse-order rollback. The same campaign agent performs
  the pass, so independent authorship is not claimed. Reliability findings,
  executable/test edits, and computational, scheduler, cluster, production,
  scientific-review, and biological evidence remain out of this selection
  slice.
- **Selection gate:** `git diff --check` passed and the complete documentation
  validator reported only the nine inherited `UNREFINED` card-location
  findings. No reliability-selection path, lifecycle, dependency, cycle,
  orphan, or anchor finding remains. The inherited result is still nonpassing,
  not green and not authority to modify those preserved cards.

## 2026-08-03T05:39:03-0400 — REVIEW-REL-03I completed

- **Verified parent:** reliability-selection checkpoint `25dbef6` was clean,
  tracked/untracked empty, published, and equal across local `HEAD`, configured
  upstream, and the live remote branch before this read-only pass.
- **High decision — producer residue needs four exact cut-point oracles:** the
  old-path direct shell owner must freeze Picard exit `42` after partial BAM/
  metrics replacement with prior BAI retained; quickcheck exit `43` after new
  BAM/metrics with prior BAI and no index; index exit `44` after partial BAI
  replacement; and zero-exit Picard with empty metrics followed by successful
  quickcheck/index and final producer exit `1`. Each test preserves exact
  tokenized new/partial/prior bytes, child diagnostics, one unrelated file, and
  the absence of recovery artifacts. These mixed triplets remain defects.
- **High decision — admission and stable-input behavior needs direct proof:**
  add arbitrary-CWD explicit Java/samtools use, missing explicit samtools before
  directory creation, and controlled input mutation that the lockless producer
  fails to recheck. The direct validator must add arbitrary-CWD dry-run/
  execute/repeat byte parity, quickcheck failure as exit-`0` failed evidence,
  header-tool failure as exit-`2` nonpublication, and post-build input mutation
  preserving a valid prior report. Shared neutral suites retain exact-loader
  and publication-fault ownership.
- **High decision — scheduler selection and stale outputs need named oracles:**
  add Java-home and PATH fallback, Java version failure/unparseable/under-17,
  missing `PICARD`, list-only module failure tolerance, dry-run log mutation,
  and stale-three-file false success. Explicitly freeze the current unguarded
  unset-`JAVA_HOME` abort even with a valid Java override; do not harden or
  approve it. Existing generic cases retain submit-CWD, strict loads, exported
  `/tmp`, override priority, PATH samtools, Bash `3.2`, child exit, and missing-
  output behavior.
- **Bounded implementation decision:** use exactly the existing direct shell,
  direct validator, and central scheduler test files, optionally as three
  sequential small test-only slices. Add no fourth owner, production change,
  fixture, baseline, dependency, or future-owner work. The later atomic cutover
  remains five moves plus ten updates.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent, so independent authorship is not claimed. No source,
  test, harness, runtime, scheduler, production, scientific-review, or
  biological evidence changed or ran. All planned evidence is local fake-tool/
  fixture characterization; real Picard, Java, samtools, scheduler, cluster,
  and production behavior remain outside the migration proof.
- **Card-boundary gate:** `git diff --check` passed and the complete
  documentation validator reported only the nine inherited `UNREFINED` card-
  location findings. No reliability-review path, lifecycle, dependency, cycle,
  orphan, or anchor finding remains. This expected-only ceiling is nonpassing,
  not a green gate and not authority to alter inherited lifecycle state.

## 2026-08-03T05:42:11-0400 — REVIEW-UX-03I selected

- **Selection:** after reliability-completion checkpoint `fae9bae` was clean,
  tracked/untracked empty, published, and equal across local `HEAD`, configured
  upstream, and the live remote branch, move only `REVIEW-UX-03I` to
  `IN_PROGRESS` and repair its reciprocal lifecycle links. `MIG-03I` remains
  unselected in `TODO`; Step `05` and all later owner cards remain uncreated.
- **Review boundary:** select one documentation-only independent-in-time pass
  over final producer/validator/scheduler commands, arbitrary-CWD journeys,
  Picard/Java/samtools/`TMPDIR` diagnostics, truthful dry-run effects, partial/
  mixed/stale output preservation, focused tests, implementation provenance,
  owner discovery, evidence ceiling, and reverse-order rollback. The same
  campaign agent performs the pass, so independent authorship is not claimed.
  Usability findings, executable/test edits, and computational, scheduler,
  cluster, production, scientific-review, and biological evidence remain out
  of this selection slice.
- **Selection gate:** `git diff --check` passed and the complete documentation
  validator reported only the nine inherited `UNREFINED` card-location
  findings. No usability-selection path, lifecycle, dependency, cycle, orphan,
  or anchor finding remains. This expected-only ceiling remains nonpassing, not
  green and not authority to alter inherited lifecycle state.

## 2026-08-03T05:45:20-0400 — REVIEW-UX-03I completed

- **Verified parent:** usability-selection checkpoint `8a85fb3` was clean,
  tracked/untracked empty, published, and equal across local `HEAD`, configured
  upstream, and the live remote branch before this read-only pass.
- **High decision — final journeys are explicit path surfaces:** documentation
  close must replace every active producer, validator, job, focused-test,
  helper, artifact, and coverage path. Root use invokes the mode-`0644` final
  producer through Bash and validator through an explicit interpreter;
  arbitrary-CWD use makes producer/interpreter, inputs, outputs, metrics,
  Picard, Java, samtools, and `TMPDIR` paths absolute. The job is submitted from
  the checkout by its final mode-`0644` path after `logs/` exists. No alias,
  wrapper, symlink, package, installed command, or ambient `PYTHONPATH` is
  supported.
- **High decision — dry-run effects and scheduler diagnostics stay distinct:**
  producer dry-run creates no output/metrics directories; validator dry-run
  emits five TSV rows but no report. The wrapper retains submit-CWD fallback,
  exported `/tmp`, defaults, strict Picard/samtools loads, `PICARD`, Java
  override/home/PATH resolution and version floor, PATH samtools, tolerated
  lists, body-level logs, three-file postcheck, and Bash `3.2` defect. A truly
  unset `JAVA_HOME` still aborts at the later unguarded diagnostic even with a
  valid override; docs must name, not fix or bless, that defect.
- **High decision — recovery never combines or silently retries a triplet:**
  preserve BAM, BAI, metrics, canonical input pair, unrelated files, directories,
  streams, scheduler logs/job identity, and tool paths/versions. Do not infer
  one attempt from timestamps, delete residue, or reuse same names while a
  downstream reader may exist. Only after preservation and reader exclusion is
  an isolated output/metrics destination the safe diagnostic retry route. Git
  rollback never restores runtime artifacts.
- **Medium decision — status, helper ownership, and provenance need correction:**
  producer success does not prove duplicate flags, cross-file correspondence,
  or metadata binding; validator exit `0` may publish failed rows and exit `2`
  publishes nothing new. The contract must stop calling the final home
  unimplemented and route neutral validation-report and BAM-helper ownership,
  not Step `00a`/`02`. Artifact evidence changes only implementation path/hash;
  historical cluster observations stay historical and are not migration proof.
- **Accepted findability and rollback:** one adjacent README and the exact
  canonical documentation roster own commands, focused direct/central tests,
  diagnostics, preservation, provenance, evidence ceiling, and rollback. Revert
  docs first, atomic five-move/ten-update cutover second, then scheduler,
  validator, and producer test slices in reverse. No compatibility surface is
  warranted.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent, so independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.
- **Card-boundary gate:** `git diff --check` passed and the complete
  documentation validator reported only the nine inherited `UNREFINED` card-
  location findings. No usability-review path, lifecycle, dependency, cycle,
  orphan, or anchor finding remains. This expected-only ceiling remains
  nonpassing, not green and not authority to alter inherited lifecycle state.

## 2026-08-03T05:48:00-0400 — MIG-03I selected

- **Selection:** after usability-completion checkpoint `beee633` was clean,
  tracked/untracked empty, published, and equal across local `HEAD`, configured
  upstream, and the live remote branch, move only `MIG-03I` to `IN_PROGRESS`
  and repair its reciprocal usability link. All three dedicated reviews are
  complete. Step `05` and all later owner/review cards remain uncreated and
  unselected.
- **Execution boundary:** this selection starts no executable work. The next
  slice is a task-specific plan freezing the reviewed producer, validator, and
  scheduler test slices, exact atomic five-move/ten-update cutover, focused and
  card-boundary gates, documentation close, publication checks, and reverse-
  order rollback. No source, test, harness, fixture, Make, coverage, artifact,
  runtime, scheduler, cluster, production, scientific-review, or biological
  evidence changed or ran here.
- **Selection gate:** `git diff --check` passed and the complete documentation
  validator reported only the nine inherited `UNREFINED` card-location
  findings. No migration-selection path, lifecycle, dependency, cycle, orphan,
  or anchor finding remains. This expected-only ceiling is nonpassing, not
  green and not authority to alter inherited lifecycle state.

## 2026-08-03T05:50:56-0400 — MIG-03I task-specific plan frozen

- **Git and slice boundary:** planning began from clean, tracked/untracked-
  empty, published, local/upstream/live-remote-equal selection `0c88390`, with
  no recovery/index lock or mutable-lane collision. Publish three single-test-
  file reliability slices, one atomic fifteen-logical-file cutover/executable
  card boundary, and one separate documentation close. Batch migration links
  and small canonical docs only in that close; no later owner is preloaded.
- **Producer baseline:** change only the direct Step `04` shell test for exact
  Picard `42`, quickcheck `43`, index `44`, empty-metrics final-check,
  arbitrary-CWD/tool admission, input-mutation, unrelated-file, and absent-
  recovery oracles. Run only shell syntax and that complete direct test.
- **Validator baseline:** change only the direct validator test for arbitrary-
  CWD dry-run/execute/repeat bytes, exit-`0` failed evidence, exit-`2`
  nonpublication, and stable-input/predecessor preservation. Run only that
  direct pytest file.
- **Scheduler baseline:** change only the central SLURM suite for Java-home/
  PATH/version, `PICARD`, list-only failure, logs, stale triplet, and unset-
  `JAVA_HOME` states. Run only the Step `04` scheduler selection. The assembled
  tip adds no fourth test, production, fixture, baseline, documentation,
  dependency, or future-owner file.
- **Cutover and card-boundary gate:** move exactly five files and update exactly
  ten callers/harness owners. After minimal final-path checks, measure coverage
  with only the intentionally stale documentation assertion deselected, then
  run the exact RUNBOOK aggregate once with an explicit result JSON. Only the
  exact migration-caused documentation paths plus nine inherited `UNREFINED`
  locations may remain, as a nonpassing expected-only ceiling. Any other fault
  must be understood before commit.
- **Close and rollback:** the separate close adds the owner README, repairs the
  contract and full canonical/current/lifecycle roster, records exact evidence,
  and runs the documentation-only gate. It may retain only nine inherited
  findings. Roll back docs, cutover, scheduler test, validator test, then
  producer test. Git rollback never alters runtime/production evidence, locks,
  logs, or recovery artifacts. No executable/test mutation or computational,
  scheduler, cluster, production, scientific-review, or biological evidence
  changed or ran in this plan slice.
- **Minimal slice check:** `git diff --check` passed for exactly the active card
  and dated audit. Per the card-boundary-only validation rule, no computational
  suite or complete documentation validator ran in this planning slice; the
  complete documentation gate remains owned by the separate card close.

## 2026-08-03T05:57:11-0400 — MIG-03I producer reliability baseline

- **Bounded mutation:** starting from clean, published, upstream/live-remote-
  equal plan `44e1db4`, change only
  `tests/shell/test_step_04_mark_duplicates.sh`. No production, validator,
  scheduler, harness, fixture, coverage, documentation, dependency, or later-
  owner file enters this slice.
- **Accepted characterization:** add tokenized Picard exit `42`, quickcheck
  exit `43`, index exit `44`, empty-metrics final-check, arbitrary-CWD explicit-
  tool, missing explicit samtools before directory creation, and controlled
  admitted-input-mutation states. Preserve exact new/partial/prior BAM/BAI/
  metrics bytes, unrelated-file immunity, and absence of recovery artifacts.
  These states prove direct-final multi-output defects; they do not bless,
  repair, or authorize cleanup/retry.
- **Evidence:** shell syntax and the complete direct shell suite passed. Final
  baseline mode/bytes/lines/SHA-256 is `0644` / `20,753` / `573` /
  `eac7b5ef42c6d050a64223975d443698b54d7542317244c8f65a58f8abf39796`.
  Published checkpoint is `de52e93243aa8c95644924f41dc1a25da4b4f600`.
  No broad or complete gate ran at this slice boundary.

## 2026-08-03T05:58:50-0400 — MIG-03I validator reliability baseline

- **Bounded mutation:** from clean, published, equal producer checkpoint
  `de52e93`, change only `tests/test_validate_step_04_mark_duplicates.py`.
  No other test owner, production, harness, fixture, coverage, documentation,
  dependency, or later-owner path changes.
- **Accepted characterization:** freeze arbitrary-CWD dry-run/execute/repeat
  exact bytes; quickcheck nonzero as exit-`0` failed evidence; header-tool
  failure as exit `2` with no new publication; and post-build input mutation
  with valid-predecessor report preservation. Exit `0` is publication/render
  success, not proof all rows pass; exit `2` is not a failed-row synonym.
- **Evidence:** all `9` direct validator tests passed. Final baseline mode/
  bytes/lines/SHA-256 is `0644` / `6,345` / `179` /
  `b8220905f12afef057d4fa357390c9268924b5923e05acb093f2b31ee12f9aa1`.
  Published checkpoint is `3d73d5285b023899967338c30bad29a7629c5187`.
  No shell, scheduler, coverage, or complete gate ran.

## 2026-08-03T06:01:35-0400 — MIG-03I scheduler reliability baseline

- **Bounded mutation:** from clean, published, equal validator checkpoint
  `3d73d52`, change only `tests/test_slurm_wrapper_contracts.py`. No fourth
  test, production, harness, fixture, coverage, documentation, dependency, or
  future-owner file enters the assembled old-path baseline.
- **Accepted characterization:** freeze `JAVA_HOME` executable selection and
  unusable-home PATH fallback, Java `-version` failure, unparseable and below-
  17 output, missing `PICARD`, tolerated list-only module failures, dry-run
  logs, stale-three-file false success, and the unguarded unset-`JAVA_HOME`
  abort. The first focused attempt exposed only a new test-stub quoting error;
  correcting that stub within the same file made the final reviewed oracle
  faithful without changing production behavior.
- **Evidence:** the Step `04` scheduler selection passed `18` tests with `108`
  unrelated cases deselected. Final baseline mode/bytes/lines/SHA-256 is `0644`
  / `59,691` / `1,758` /
  `bff47b60b8563924bb2a30ce13e3d81efb5e80853e90f7f6ac2ae2c28b527d65`.
  Published checkpoint is `3e805ac3c02692c0f2d22682f9ec038776dc4a62`.
  Passing characterization does not approve scheduler defects; no broad gate
  ran at this test-slice boundary.

## 2026-08-03T06:24:58-0400 — MIG-03I executable cutover and card boundary

- **Exact cutover decision:** from clean, published, equal scheduler baseline
  `3e805ac`, move only producer, validator, mode-`0644` job, direct shell test,
  and direct validator test to the reviewed stage-owner homes. Update exactly
  `Makefile`, artifact producer mapping/assertion, public CLI, scheduler,
  validation-roster/report/BAM-helper maps, coverage baseline, and literal Make
  oracle. No wrapper, alias, symlink, package, descriptor, schema, transaction,
  receipt, recovery marker, dependency action, documentation path, or later
  owner enters the cutover.
- **Production and test byte boundary:** change only producer usage self-path,
  two validator neutral-library root depths, job child path, moved-test roots/
  targets/private roster load, and reviewed integration paths. Final producer,
  validator, and job SHA-256 values are respectively
  `b845aa910ccabaf8799e000dc62e8939b0203c7848511524fadf51c79292eb2d`,
  `17a541e7b9d9822df5de0721747187621035f0dae7aaa0f1a35995f727bfb178`,
  and `4e41c4cd7ee1ec36169797bfc4897968e38010e78aec35d16c6921dfd55217fc`;
  all remain mode `0644`. Artifact evidence changes only final producer path
  and reviewed hash; identities, schemas, contents, ordering, consumers, and
  scientific meaning remain unchanged.
- **Focused acceptance:** producer/job/moved-test syntax and the complete shell
  suite passed; the moved validator passed `9`; Step `04` scheduler selection
  passed `18` with `108` deselected; and targeted artifact, public-CLI/Make,
  roster, validation-report, BAM-helper, and coverage-wiring checks passed `68`
  assertions. Exact non-documentation search found no legacy executable/test
  path or undeclared compatibility owner.
- **Coverage:** measurement with only the intentionally stale documentation
  assertion deselected passed `1,134` tests with `17` skips. Step `04` improved
  from `144/155` lines and `33/42` branches to `146/155` and `35/42`; global
  counts improved from `9508/11677` lines and `3331/4756` branches to
  `9510/11677` and `3333/4756`. Every non-target row stayed exact; the tracked
  snapshot exactly matched measured current data and standalone policy passed
  at line `0.814422`, branch `0.700799`, `32` files.
- **Complete-gate evidence:** the aggregate was not fully green. The sandboxed
  attempt passed static preflight in `0.176s`, then guarded R stopped on
  Bioconductor DNS in `8.849s` and retained the inherited malformed `macos`
  warning. The network-enabled exact rerun used the existing locked library and
  changed no dependency. Static passed in `0.116s`, shell in `131.070s`,
  guarded R in `459.450s`, and report runtime in `339.823s`. Python ran `1,134`
  passes and `17` skips before its sole documentation assertion listed exactly
  five stale inventory links, five stale owner-contract links, and nine
  inherited `UNREFINED` locations; aggregate elapsed was `482.874s`. Result is
  `/private/tmp/norad-mig03i-validation.json`, retained Python log
  `/var/folders/y0/bg0yx6g54bs0403dn0x_k28w0000gn/T/norad-validation-python-coverage-g4l9kajd.log`.
  This expected-only documentation ceiling is nonpassing, never green.
- **Preserved risks and publication:** partial/mixed direct finals, silent
  replacement, admitted-input-mutation blindness, missing recovery controls,
  validator status/exit distinctions, Bash `3.2`, dry-run logs, unset
  `JAVA_HOME`, tolerated module listing, and stale-triplet false success remain
  defects. No real Picard/Java/samtools, scheduler, cluster, production,
  scientific-review, or biological evidence was created. Exact cutover
  checkpoint `803fcc479390273ba2dd5eba9907d739dbfdbb2f` is published and equal
  across local `HEAD`, upstream, and live remote before documentation close.

## 2026-08-03T06:28:25-0400 — MIG-03I documentation and lifecycle close

- **Documentation boundary:** from clean, published, equal executable parent
  `803fcc4`, add one adjacent owner README; repair the owner contract, current
  architecture/inventory/test/documentation ownership, Step `04` runbook and
  troubleshooting routes, impacted neutral-library and canonical-BAM helper/
  test routes, roadmap and handoff; append complete evidence here; move only
  `MIG-03I` to `COMPLETED`; and repair every inbound lifecycle link. No
  executable, configuration,
  dependency, schema, fixture, report template, test behavior, or later card
  changes.
- **Truthful operator decisions:** route mode-`0644` producer through Bash,
  validator through the explicit interpreter, and job through `sbatch` after
  creating `logs/`; distinguish producer no-write, validator stdout-only, and
  scheduler log/Bash effects; expose Picard/Java/samtools/`TMPDIR` selection;
  require preservation and reader exclusion before isolated retry; and state
  that Git rollback cannot recover runtime artifacts.
- **Risk and evidence disposition:** preserve rather than approve every
  producer, validator, and scheduler defect above. Keep historical cluster and
  Picard observations historical. The evidence ceiling is local fixture/mock,
  guarded local R, pinned report runtime, and local coverage only. No diagram
  changes because physical placement changes neither semantic DAG edges nor
  public data flow. No next owner/review card is created or selected; refresh
  the live DAG only after this close is published and proved equal.
- **Documentation gate:** `git diff --check` passes. The complete RUNBOOK
  documentation validator reports exactly the nine inherited `UNREFINED`
  card-location findings and no migration-caused path, lifecycle, dependency,
  cycle, orphan, anchor, or diagram finding. This remains a nonpassing
  expected-only ceiling, not green and not authority to alter inherited
  lifecycle state.
- **Rollback and stop:** revert this documentation close, executable checkpoint
  `803fcc4`, scheduler baseline `3e805ac`, validator baseline `3d73d52`, then
  producer baseline `de52e93`. Git rollback never deletes or authenticates
  runtime/production evidence, locks, logs, or recovery artifacts. Publish the
  close, prove clean local/upstream/live-remote equality, then refresh the DAG.

## 2026-08-03T06:45:30-0400 — MIG-03J and sequential reviews defined

- **Checkpoint and live-DAG decision:** begin from clean, published,
  local/upstream/live-remote-equal `MIG-03I` documentation close
  `c6814e01352998ee4ebc01014737fac731f2e029`, with no recovery/index-lock or
  overlapping mutable-lane state. Refresh the canonical semantic edges rather
  than relying on historical numbering. Both direct predecessors of
  `split_N_cigar_reads_with_GATK`—`mark_BAM_duplicates_with_Picard` and
  `construct_FASTA_sidecars`—are migrated, leaving Step `05` as the sole
  eligible unmigrated owner. Step `06` still depends on Step `05`; define no
  Step `06` or later card.
- **Bounded lifecycle decision:** define only unselected `MIG-03J` and
  `REVIEW-ARCH-03J` → `REVIEW-REL-03J` → `REVIEW-UX-03J`, all in `TODO`.
  Architecture alone is dependency-free; reliability depends on architecture,
  usability on reliability, and migration on usability. Publish and prove this
  definition checkpoint equal before selecting only the architecture review.
- **Frozen identity and surface:** semantic owner
  `split_N_cigar_reads_with_GATK`, key
  `norad.stage.split_N_cigar_reads_with_GATK.v1`, historical alias `05`, final
  source home `src/norad/stages/split_N_cigar_reads_with_GATK/`, and mirrored
  test home `tests/stages/split_N_cigar_reads_with_GATK/`. The three mode-`0644`
  native assets total `34,030` bytes and `1,023` lines. Producer SHA-256 is
  `19b3ac73934c28760127a7f447863251e127362bb1cdaeef9346d6a310d3d01e`,
  validator `ceb3a9720b01c1de60d5f23026dea3f9daf3c9b4d1c93a8a140514ffc29c502a`,
  and job `00944fc0997117197b155f6f2e5222f27a371ab4d623c091544d9656fc2dddc6`.
  Direct shell/validator rollback hashes are respectively
  `a2d748f064139b0ed6c2f3c6f0664f445acf83689d379b0787d4f1b2b247a8b6`
  and `9f24713234b0b2ec35d9fd424d8a590334c8071d15078f4095faaf4417e232c4`.
- **Proposed cutover and architecture risk:** propose exactly five moves plus
  ten adjacent integration-owner updates: Make, artifact mapping/assertion,
  public CLI, scheduler contracts, validation roster/report/BAM-helper maps,
  coverage baseline, and literal Make fixture. Architecture review must prove
  that ceiling, final producer/job/test roots, neutral report/BAM-helper
  depths, exact artifact path/hash, coverage/static ownership, and reverse
  rollback. The moved validator cannot retain ambient
  `import reference_provenance`; it needs a private exact-file bridge to
  unchanged public `scripts/reference_provenance.py`. The review must settle
  the bridge and any genuinely required extra caller/test owner without a
  package, `PYTHONPATH`, helper move, alias, wrapper, or duplicate.
- **High transaction risk retained for review:** the producer has a run-token
  scratch area, project-storage GATK temp, output-directory lock, staged
  validation, backups, sequential BAM/BAI publication, final validation, and
  rollback. Inputs are not snapshot-rechecked, the lock is broad, no receipt
  binds an attempt, restoration moves are best-effort, and cleanup can delete
  backups and the lock after rollback itself fails. Reliability must assign
  safe restoration-failure, predecessor/recovery-residue, signal, lock,
  scratch, and admitted-input-mutation oracles; none of these defects may be
  fixed or approved by relocation.
- **Scheduler, validation, and evidence risks retained:** the mode-`0644` job
  preserves submit-directory fallback, exported `/tmp`, tolerated samtools
  module loading, fixed GATK/samtools defaults and overrides, Java override/
  `JAVA_HOME`/PATH selection with actual version floor, dry-run `logs/`
  mutation, Bash `3.2` empty-array failure, and stale nonempty BAM/BAI false
  success. Reliability must disposition Step-`05`-specific module/tool/version/
  log/stale-output states. Producer and five-row validator do not prove the
  split-N-cigar transformation or bind output to an attempt; validator exit
  `0` may publish failed rows. Artifact identities and scientific meaning stay
  fixed. Starting coverage is validator `138/149` lines and `31/38` branches,
  global `9510/11677` lines and `3333/4756` branches.
- **Definition and validation boundary:** this slice changes only four new
  cards, current roadmap/handoff, and this audit. No executable, test, harness,
  configuration, dependency, runtime, scheduler, cluster, production,
  scientific-review, or biological state changes or runs. Full documentation-
  only card-boundary validation follows after the assembled definition; small
  canonical path/link updates remain batched for the eventual migration close.
- **Documentation gate:** `git diff --check` passes. The exact RUNBOOK
  documentation validator reports only the nine inherited `UNREFINED` card-
  location findings and no new card, path, dependency, cycle, orphan, anchor,
  or diagram finding. This expected-only result remains nonpassing, not green,
  and is not authority to alter the inherited lifecycle state.

## 2026-08-03T06:50:21-0400 — REVIEW-ARCH-03J selected

- **Selection:** from clean, published, local/upstream/live-remote-equal JIT
  definition checkpoint `f88f56e2b51a8af9dde558af6ffb6c6ca148f05e`,
  move only `REVIEW-ARCH-03J` to `IN_PROGRESS` and repair its reciprocal
  lifecycle link from `REVIEW-REL-03J`. Reliability, usability, and migration
  remain unselected in `TODO`; Step `06` and every later card remain uncreated.
- **Boundary:** this checkpoint selects review work but does not perform it.
  No architecture finding or migration-card correction is recorded; no
  executable, test, harness, configuration, dependency, runtime, scheduler,
  cluster, production, scientific-review, or biological state changes or runs.
- **Documentation gate:** `git diff --check` passes. The exact RUNBOOK
  documentation validator reports only the nine inherited `UNREFINED` card-
  location findings and no selection-caused path, lifecycle, dependency,
  cycle, orphan, anchor, or diagram finding. The expected-only result remains
  nonpassing and is not called green.

## 2026-08-03T06:57:10-0400 — REVIEW-ARCH-03J completed

- **Live-DAG and placement decision:** against clean, published, equal
  selection checkpoint `032e4fb72998d479001a21561207fba2d327b386`, confirm
  Step `05` is the sole eligible unmigrated identity. Both direct predecessors
  are final-owner migrated; Step `06` remains blocked, uncreated, and
  unselected. The frozen source/test homes and three mode-`0644` native asset
  classes exactly match `SOURCE_TOPOLOGY.md`; no descriptor or package is part
  of this migration.
- **High finding — ambient reference import cannot survive movement:** retain
  unchanged public `scripts/reference_provenance.py` and copy the proven Step-
  `00c` private exact-file bridge shape into the moved Step `05` validator.
  Reuse `_norad_reference_provenance`; resolve from repository-root
  `parents[4]`; validate exact file, `ProvenanceError`, and all three parser
  callables; preserve foreign/incomplete cache entries; remove only an owned
  failed partial; emit the owned exit-`2` diagnostic; and mutate no `sys.path`.
  Keep report and BAM exact-file roots on `parents[4]` with their unchanged
  neutral owners. No public import, `PYTHONPATH`, helper move, or API redesign
  is required.
- **High finding — moved direct-test discovery must be explicit:** shell root
  becomes `SCRIPT_DIR/../../..` and its producer/job paths become final. Python
  root becomes `parents[3]`; replace ambient root-roster import with a private
  exact-file load of unchanged `tests/validation_roster_expectations.py`.
  Consumer-specific reference-bridge cache/path/failure tests stay in that
  moved owner. Update the central BAM-helper caller/cache matrix to final Step
  `05`, isolate `_norad_reference_provenance`, and remove its now-obsolete dummy
  ambient reference module. Public `tests/test_reference_provenance.py` remains
  unchanged.
- **Exact cutover ceiling:** tracked basename/path and semantic-consumer
  searches prove one direct atomic cutover of five moves plus ten updates:
  `Makefile`, artifact producer mapping, artifact path/hash assertion, public
  CLI, SLURM, validation roster, validation-report map, BAM-helper matrix,
  coverage row, and literal Make fixture. Final producer and job become exact
  static/smoke inputs. No unmovable caller, wrapper, alias, symlink, duplicate,
  package, descriptor, schema, or eleventh integration owner exists; any sixth
  move or eleventh update reopens architecture review.
- **Projected native evidence:** reviewed path/loader-only transforms project
  producer `18,920` bytes / `596` lines /
  `e25c8d94d940aa02187e5550c51a71b8fdd8ca75660a07f5851dc215679248ac`,
  validator `12,584` / `334` /
  `f1a1128510de0c4e2b40800185c6cc039c7bb4ed5bf158396d87ee5d0730cdf3`,
  and job `5,383` / `167` /
  `3931b0976a9c97438b5980706a86203eb49ed472390a5a2f201830ae7ccfa147`.
  All remain mode `0644`; a different production hash requires re-review.
- **Artifact, coverage, documentation, and rollback decisions:** change Step
  `05` implementation evidence only to final producer path and projected first
  hash; retain its evidence ID, three public artifact identities, schemas,
  contents, ordering, reconciliation, consumers, and scientific meaning. Move
  the validator coverage row while retaining target rates, every non-target
  row, and global covered-count floors. Batch contract/current topology,
  operational commands, impacted neutral/reference/upstream owner routes,
  lifecycle links, and owner README at migration close; no diagram changes are
  proposed because neither DAG nor public flow changes. Roll back docs, then
  atomic cutover with Make/oracle and artifact path/hash/assertion together,
  then reliability baselines in reverse order.
- **Review evidence boundary:** this was a read-only committed-time pass by the
  same campaign agent; independent authorship is not claimed. No executable,
  test, harness, dependency, runtime, scheduler, cluster, production,
  scientific-review, or biological evidence changed or ran. Reliability,
  usability, and migration remain unselected.
- **Documentation gate:** `git diff --check` passes. The exact RUNBOOK
  documentation validator reports only the nine inherited `UNREFINED` card-
  location findings and no architecture-review-caused path, lifecycle,
  dependency, cycle, orphan, anchor, or diagram finding. The expected-only
  result remains nonpassing and is not called green.

## 2026-08-03T10:08:01-0400 — REVIEW-UX-03L selected

- **Selection:** from clean, published, local/upstream/live-remote-equal
  reliability-completion checkpoint
  `db33d9cdf562134f8377639c23db74cc860830b3`, move only `REVIEW-UX-03L` to
  `IN_PROGRESS` and repair its direct reliability/migration lifecycle links.
  `MIG-03L` remains unselected in `TODO`; Step `08` and every later owner/
  review card remain uncreated.
- **Boundary:** this checkpoint selects read-only usability review but records
  no finding. No executable, test, harness, configuration, dependency, schema,
  fixture, report-template, runtime, scheduler, cluster, production,
  scientific-review, variant/editing-site, or biological state changes or
  runs.
- **Minimal slice check:** `git diff --check` passes. Per the card-boundary-only
  validation rule, no computational suite or complete documentation validator
  runs at selection; the complete documentation gate belongs to usability-
  review completion.

## 2026-08-03T10:13:57-0400 — REVIEW-UX-03L completed

- **Review basis:** complete a separate read-only usability pass from clean,
  published, local/upstream/live-remote-equal selection checkpoint
  `3ec83073ceae62eb6a59afe9470941cd1bf1eec3`. Inspect public CLI/Make/SLURM
  characterization, producer/validator help and behavior, final owner/test
  topology, artifact/coverage/helper routes, contract, runbook,
  troubleshooting, documentation ownership, predecessor/consumer semantics,
  and every reliability-reviewed defect. Independent authorship is not
  claimed.
- **Final invocation decision:** documentation close must replace every active
  Step `07` producer, validator, job, focused-test, helper, artifact-provenance,
  and coverage path. Root use directly invokes the final mode-`0755` producer,
  uses an explicit interpreter for the final mode-`0644` validator, and
  submits the final mode-`0644` job with `sbatch` after creating checkout-root
  `logs/`. Explicit Bash is only a local wrapper diagnostic. Arbitrary-CWD use
  makes code, manifests, selector file, orientation root, BAM/BAIs, FASTA/FAI,
  output/report roots, bcftools, checkout, and owner paths absolute. Supported
  producer commands use an absolute output root so receipt VCF strings agree
  with validator-resolved paths. Add no installed command, package import,
  legacy alias, wrapper, symlink, `PYTHONPATH`, or global `sys.path` route.
- **Dry-run and scheduler decision:** producer dry-run validates manifests,
  FAI-bound selector, relative selector-file resolution, every BAM/BAI,
  bcftools, depth/filter, and manifest hashes; prints both exact pipelines and
  output/lock/temp/validation/publication paths; invokes no bcftools child; and
  writes nothing. Validator dry-run reads/snapshots all six explicit inputs,
  prints five report rows plus completion, invokes no bcftools, and writes no
  report. Scheduler `EXECUTE=0` still changes to submit/fallback CWD, creates
  `logs/`, performs module/tool/version diagnostics when applicable, and
  delegates producer dry-run. Preserve one CPU, exported `/tmp`, exact
  defaults/overrides, warning-only unusable preflight, version failure,
  basename forwarding, child delegation, and stale-three-file false success;
  do not call scheduler dry-run side-effect-free.
- **Recovery and provenance decision:** before cleanup/recovery/retry, preserve
  all three finals, run-token temps/backups, lock/owner, both manifests, every
  BAM/BAI, FASTA/FAI, regions file, unrelated bytes, streams, scheduler job/
  accounting/logs, CWD, exact bcftools path/version, depth/filter, and
  environment. The reviewed receipt-publication exit `67` followed by prior-
  FWD restoration exit `68` leaves prior FWD absent with its backup preserved,
  restores prior REV/receipt, removes owned temps/lock, and creates no recovery
  marker. Receipt visibility, counts, timestamps, and residue absence do not
  identify a clean/current attempt. Never combine files, reconstruct a member,
  remove a foreign lock, trust stale wrapper success, or rerun the same output
  path. Rule out every producer and Step `08` reader; any separately authorized
  diagnostic retry uses a distinct output root and is not production authority.
- **Ownership and evidence-language decision:** add the owner README; repair
  the contract's flat/unimplemented paths; update inventory/topology/test/
  documentation ownership, runbook, troubleshooting, neutral-library, Step
  `06`, Step `08`, artifact, and partition-manifest routes. Keep `FWD_like` and
  `REV_like` mechanical. Producer exit `0` does not bind unhashed BAM/BAI/
  reference/FAI/regions/tool/depth/filter/VCF state. Validator exit `0` may
  publish failed evidence and does not prove bcftools execution, selector-bound
  coordinates, REF/ALT/FORMAT/filter semantics, immutable inputs, output
  hashes, or attempt identity. Scheduler exit `0` may accept stale outputs.
  None proves variants, RNA-editing sites, transcript strand, scientific
  readiness, or biological readiness. Migration evidence remains local fake-
  tool/fixture evidence, not real bcftools, scheduler, cluster, production,
  scientific-review, variant/editing-site, or biological proof.
- **Findability, rollback, and next boundary:** the owner README and runbook
  must own root/arbitrary-CWD producer/validator commands, scheduler submission,
  selector/depth/filter/tool/output/lock/receipt selection, focused direct and
  central tests, evidence preservation, provenance, and next safe action. Add
  a dedicated partial-transaction/rollback-failure producer/wrapper route and
  link structured validation to it. No diagram changes are needed because the
  semantic DAG and public flow are unchanged. Roll back documentation, then
  atomic five-move/nine-update cutover, scheduler, validator, producer
  stability/provenance, transaction/recovery, and pipeline/selector baselines
  in reverse order. Git rollback never changes runtime evidence. Publish and
  prove this review completion equal, then cut a fresh branch as a separate
  reversible boundary before selecting `MIG-03L`; do not preload Step `08`.
- **Evidence boundary:** this pass changed or ran no source, test, harness,
  dependency, real bcftools, scheduler, cluster, production, scientific-review,
  variant/editing-site, or biological evidence.
- **Card-boundary gate:** `git diff --check` passed. The exact RUNBOOK
  documentation validator reported only the nine inherited `UNREFINED` card-
  location findings and no usability-review-caused path, lifecycle, dependency,
  cycle, orphan, anchor, or diagram finding. The expected-only result remains
  nonpassing and is not called green.

## 2026-08-03T10:00:03-0400 — REVIEW-REL-03L selected

- **Selection:** from clean, published, local/upstream/live-remote-equal
  architecture-completion checkpoint
  `ec7e8d911c575418ac5fc89fbfb5fef2793b6dc0`, move only `REVIEW-REL-03L` to
  `IN_PROGRESS` and repair its direct architecture/usability lifecycle links.
  `MIG-03L` and `REVIEW-UX-03L` remain unselected in `TODO`; Step `08` and
  every later owner/review card remain uncreated.
- **Boundary:** this checkpoint selects read-only reliability review but
  records no finding. No executable, test, harness, configuration, dependency,
  schema, fixture, report-template, runtime, scheduler, cluster, production,
  scientific-review, variant/editing-site, or biological state changes or
  runs.
- **Minimal slice check:** `git diff --check` passes. Per the card-boundary-only
  validation rule, no computational suite or complete documentation validator
  runs at selection; the complete documentation gate belongs to reliability-
  review completion.

## 2026-08-03T10:05:41-0400 — REVIEW-REL-03L completed

- **Review basis:** complete a separate read-only reliability pass from clean,
  published, local/upstream/live-remote-equal selection
  `3d2b9c0ada9b970bac533a72d910be010e74da3f`. Inspect exact producer, validator,
  direct-test, shared neutral-report, central scheduler, artifact, coverage,
  receipt, selector, mutation, signal, collision, publication, restoration,
  cleanup, and residue behavior without modifying or running executable/test
  files. Independent authorship is not claimed.
- **Pipeline/selector decision:** one old-path direct-shell checkpoint must
  freeze FWD/REV mpileup and filter failures as producer exit `1`; exact
  diagnostics, no finals, owned cleanup, and unrelated preservation; explicit
  unusable-tool rejection; PATH basename from arbitrary CWD; manifest-mutation
  detection; compressed relative regions-file acceptance; and unchanged
  command/sample/depth/filter/annotation/non-calling behavior. Existing tests
  retain dry-run, success, header-only, selector/admission, sample mismatch,
  stale path, lock, partial set, and basic child-failure ownership.
- **Transaction/recovery decision:** one old-path direct-shell checkpoint must
  prove FWD/REV/receipt final move order and barrier-observe the receipt-visible
  pre-commit window. Inject receipt-publication exit `67` then prior-FWD
  restoration exit `68`: propagate `67`, leave prior FWD final absent with its
  backup preserved, restore prior REV and receipt, remove owned temps/lock,
  preserve unrelated bytes, and create no recovery marker. This is ambiguous
  manual recovery, not successful rollback or safe retry authority.
- **Stability/provenance decision:** one old-path direct-shell checkpoint must
  freeze undetected post-admission mutation of BAM/BAI, FASTA/FAI, and regions
  bytes as exit-`0` publication; manifest mutation as rejection; TERM as exit
  `143` with complete-predecessor restoration and cleanup; and same-scope lock
  serialization as one admitted/one rejected run. The exact receipt remains
  without attempt token, input/tool/policy identity, or VCF hashes and cannot
  prove current-attempt or immutable computation.
- **Validator decision:** one old-path direct-validator checkpoint must add
  arbitrary-CWD dry-run/execute/repeat byte parity; an exit-`0` five-check
  semantic-failure matrix; a six-input post-build mutation matrix preserving a
  valid predecessor on exit `2`; compressed-regions selector failure; current
  false passes for out-of-bounds BED detail and VCF coordinate/REF/ALT/FORMAT
  semantics; and relative-receipt-path count failure. Shared neutral report and
  roster suites retain loader/publication and exact-ID ownership.
- **Scheduler decision:** one old-path central checkpoint must freeze bcftools
  version-command failure before child; missing/nonexecutable warnings;
  basename forwarding; launch-CWD fallback; dry-run `logs/`-only mutation; and
  stale-three-file false success. Generic coverage retains exact mode,
  directives, one CPU, module tolerance, arguments/depth/filter, invalid mode,
  child exit, and missing outputs. Step `07` has no characterized Bash `3.2`
  empty-array defect.
- **Slice, coverage, and evidence decision:** publish exactly five sequential
  test-only checkpoints—pipeline/selector, transaction/recovery, stability/
  provenance, validator, scheduler—then the atomic cutover. Only existing
  direct shell, direct validator, and central scheduler tests may change.
  Add no fixture file, fourth owner, production edit, coverage baseline,
  documentation batch, dependency, or future card. Coverage may rise but not
  regress below `167/198` lines, `48/72` branches, or global covered-count
  floors. All evidence remains local fake-tool/fixture evidence, not real
  bcftools, scheduler, cluster, production, scientific-review, variant/editing-
  site, or biological proof.
- **Card-boundary gate:** `git diff --check` passed. The exact RUNBOOK
  documentation validator reports only the nine inherited `UNREFINED` card-
  location findings and no reliability-review-caused path, lifecycle,
  dependency, cycle, orphan, anchor, or diagram finding. The expected-only
  result remains nonpassing and is not called green.

## 2026-08-03T06:59:46-0400 — REVIEW-REL-03J selected

- **Selection:** from clean, published, local/upstream/live-remote-equal
  architecture checkpoint `e40fb3b90462b0f0bf77410b8e035995ce03a13d`, move
  only `REVIEW-REL-03J` to `IN_PROGRESS` and repair reciprocal links from the
  completed architecture and unselected usability cards. Usability and
  migration remain unselected in `TODO`; Step `06` and every later card remain
  uncreated.
- **Boundary:** this checkpoint selects review work but does not perform it.
  No reliability finding or migration-card correction is recorded; no
  executable, test, harness, configuration, dependency, runtime, scheduler,
  cluster, production, scientific-review, or biological state changes or runs.
- **Documentation gate:** after repairing the selection's current lifecycle
  links, `git diff --check` passes and the exact RUNBOOK documentation validator
  reports only the nine inherited `UNREFINED` card-location findings. No
  selection-caused finding remains; the expected-only result is nonpassing and
  is not called green.

## 2026-08-03T07:06:36-0400 — REVIEW-REL-03J completed

- **Verified parent:** reliability-selection checkpoint
  `5785b87660d4274b07e39fba07590fb50f75f6d2` was clean, tracked/untracked
  empty, published, and equal across local `HEAD`, configured upstream, and the
  live remote branch before this read-only pass.
- **High decision — restoration failure needs an exact recoverability oracle:**
  in the old-path direct shell owner, freeze lone-final rejection with byte-
  exact preservation, final-path revalidation failure with byte-exact
  predecessor restoration, and BAI-publication exit `67` followed by BAM-
  restoration exit `68`. The last state propagates `67`, leaves the prior BAM
  missing and prior BAI restored, preserves an unrelated file, and exposes the
  current deletion of backups, lock, scratch, and recovery evidence. This
  ambiguous/data-loss behavior remains a defect, not an approved transaction.
- **High decision — admission, input mutation, and signal behavior need a
  separate producer slice:** freeze missing explicit samtools before output-
  directory creation; controlled GATK-time mutation of admitted BAM, BAI,
  FASTA, FAI, and DICT while the producer still exits `0`; and controlled TERM
  exit `143` with predecessor/unrelated bytes preserved and owned lock/scratch
  removed. Assert that no receipt/recovery marker exists without adding one.
- **High decision — validator parity and bridge states need named ownership:**
  the old-path direct validator adds arbitrary-CWD dry-run/execute/repeat byte
  parity with unchanged inputs, quickcheck nonzero as exit-`0` failed evidence,
  header-tool failure as exit-`2` nonpublication, and post-build input mutation
  as exit `2` preserving a valid predecessor. Cutover adds owner-local exact-
  reference bridge cases for cache reuse without `sys.path` mutation, missing
  owner/spec cleanup, foreign-cache preservation, correct-path incomplete-API
  preservation, and execution-failure owned-partial cleanup. Neutral report
  and BAM-helper suites retain their existing matrices.
- **High decision — Step 05 scheduler states need direct selection:** in the
  central scheduler owner, add `JAVA_HOME/bin/java`, PATH fallback after
  unusable `JAVA_HOME`, missing/unusable override, Java command failure,
  unparseable/under-17 output, GATK/samtools version failure, missing/unusable
  tool warning with unchanged delegation, dynamic absent-`SLURM_SUBMIT_DIR`
  fallback, dry-run `logs/`-only mutation, and stale-pair false success.
  Existing generic cases continue to own directives/mode, overrides, module
  tolerance, invalid mode, child exit, missing output, and Bash `3.2`.
- **Bounded implementation decision:** publish exactly four small sequential
  old-path test-only checkpoints—producer transaction, producer admission/
  signal, validator, then scheduler—before the atomic five-move/ten-update
  cutover. Use only the existing direct shell, direct validator, and central
  scheduler owners; add no fixture, fourth test owner, production edit,
  coverage-baseline edit, documentation batch, dependency, or future owner.
  Coverage may rise but must preserve target rates and global covered-count
  floors.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent, so independent authorship is not claimed. No source,
  test, harness, runtime, scheduler, production, scientific-review, or
  biological evidence changed or ran. Planned evidence is local fake-tool/
  fixture characterization; real GATK, Java, samtools, scheduler, cluster, and
  production behavior remain outside migration proof.
- **Card-boundary gate:** `git diff --check` passed and the exact RUNBOOK
  documentation validator reported only the nine inherited `UNREFINED` card-
  location findings. No reliability-review path, lifecycle, dependency, cycle,
  orphan, anchor, or diagram finding remains. This expected-only ceiling is
  nonpassing, not green, and not authority to alter inherited lifecycle state.

## 2026-08-03T07:09:17-0400 — REVIEW-UX-03J selected

- **Selection:** after reliability-completion checkpoint
  `daa7ec4c0091dd87e86043b83096111efb44e1cb` was clean, tracked/untracked
  empty, published, and equal across local `HEAD`, configured upstream, and the
  live remote branch, move only `REVIEW-UX-03J` to `IN_PROGRESS` and repair its
  reciprocal lifecycle links. `MIG-03J` remains unselected in `TODO`; Step `06`
  and every later card remain uncreated.
- **Boundary:** this checkpoint selects review work but does not perform it. No
  usability finding or migration-card correction is recorded; no executable,
  test, harness, configuration, dependency, runtime, scheduler, cluster,
  production, scientific-review, or biological state changes or runs.
- **Documentation gate:** after repairing the selection's current lifecycle
  links, `git diff --check` passes and the exact RUNBOOK documentation validator
  reports only the nine inherited `UNREFINED` card-location findings. No
  selection-caused path, lifecycle, dependency, cycle, orphan, anchor, or
  diagram finding remains. The expected-only result is nonpassing and is not
  called green.

## 2026-08-03T07:12:43-0400 — REVIEW-UX-03J completed

- **Verified parent:** usability-selection checkpoint
  `f41f988d36c56ac3212d47d284e3eeef4e88e5ad` was clean, tracked/untracked
  empty, published, and equal across local `HEAD`, configured upstream, and the
  live remote branch before this read-only pass.
- **High decision — final journeys are explicit path surfaces:** documentation
  close replaces every active producer, validator, job, focused-test, helper,
  artifact, and coverage path. Root use invokes the mode-`0644` final producer
  through Bash and validator through an explicit interpreter; arbitrary-CWD
  use makes all code, input, output/report, reference, GATK, Java, and samtools
  paths absolute. No installed command, package, alias, wrapper, symlink,
  ambient `PYTHONPATH`, or global `sys.path` route is supported.
- **High decision — dry-run effects and scheduler diagnostics stay distinct:**
  producer dry-run validates files/executable paths, prints scratch/backup/
  lock/GATK-temp plans, invokes no version or data tool, and writes nothing.
  Validator dry-run invokes explicit checks, emits five rows plus completion,
  and writes no report. Scheduler submission starts in the checkout after
  `logs/` exists and retains submit-CWD fallback, exported `/tmp`, body logs,
  defaults/overrides, Java resolution/version floor, tolerated module lists,
  warning-only missing tools, version-command failures, Bash `3.2`, and stale-
  pair false success without hardening or approval.
- **High decision — recovery never combines or silently retries a pair:**
  preserve all surviving final, temp, backup, GATK-temp, lock/owner, input/
  reference, unrelated-file, stream, job/log, checkout, and tool/version
  evidence. Failed BAM restoration can leave only the prior BAI while cleanup
  erases backups, lock, scratch, and recovery evidence; signal cleanup also
  leaves no attempt marker. Absence is not proof of cleanliness. Rule out the
  lock owner, running producer, and Step `06` readers; never combine members,
  infer one attempt from timestamps, remove a foreign lock, or adopt stale
  wrapper success. Only an isolated output directory is a safe separately
  authorized diagnostic retry. Git rollback never restores runtime artifacts.
- **Medium decision — status, helper ownership, and provenance need correction:**
  the contract must stop calling the final home unimplemented or the owner
  flat and must route neutral validation-report/BAM helpers plus unchanged
  public reference provenance accurately. Producer success does not prove the
  GATK transformation or attempt binding; validator exit `0` may publish failed
  rows; scheduler exit `0` may accept stale outputs. Artifact evidence changes
  only path/hash, and historical cluster observations remain historical rather
  than migration proof.
- **Accepted findability and rollback:** one adjacent README and the exact
  canonical documentation roster own commands, focused direct/central tests,
  diagnostics, preservation, provenance, evidence ceiling, and rollback.
  Revert docs, atomic five-move/ten-update cutover, scheduler, validator,
  producer admission/signal, then producer transaction checkpoints in that
  order. No compatibility surface is warranted.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent, so independent authorship is not claimed. No source,
  test, harness, dependency, runtime, scheduler, production, scientific-review,
  or biological evidence changed or ran.
- **Card-boundary gate:** `git diff --check` passed and the exact RUNBOOK
  documentation validator reported only the nine inherited `UNREFINED` card-
  location findings. No usability-review path, lifecycle, dependency, cycle,
  orphan, anchor, or diagram finding remains. This expected-only ceiling is
  nonpassing, not green, and not authority to alter inherited lifecycle state.

## 2026-08-03T07:15:06-0400 — MIG-03J selected

- **Selection:** after usability-completion checkpoint
  `0328fbed07aadd2d316d4b96ae8d7bba17aee63c` was clean, tracked/untracked
  empty, published, and equal across local `HEAD`, configured upstream, and the
  live remote branch, move only `MIG-03J` to `IN_PROGRESS` and repair its
  reciprocal usability link. All three dedicated reviews are complete. Step
  `06` and every later owner/review card remain uncreated and unselected.
- **Boundary:** this checkpoint selects migration work but does not plan or
  perform it. No executable, test, harness, configuration, dependency, schema,
  runtime, scheduler, cluster, production, scientific-review, or biological
  state changes or runs.
- **Documentation gate:** after repairing the selection's current lifecycle
  links, `git diff --check` passes and the exact RUNBOOK documentation validator
  reports only the nine inherited `UNREFINED` card-location findings. No
  selection-caused path, lifecycle, dependency, cycle, orphan, anchor, or
  diagram finding remains. The expected-only result is nonpassing and is not
  called green.

## 2026-08-03T07:17:13-0400 — MIG-03J task-specific plan frozen

- **Git and slice boundary:** planning began from clean, tracked/untracked-
  empty, published, local/upstream/live-remote-equal selection
  `5415538fcaad581e76b13d061251da060dd8e8a9`, with no recovery/index lock or
  mutable-lane collision. Publish four single-test-file reliability slices,
  one atomic fifteen-logical-file cutover/executable card boundary, and one
  separate documentation close. Batch migration links and small canonical
  docs only in that close; no later owner is preloaded.
- **Producer transaction baseline:** change only the direct Step `05` shell
  test for lone-final preservation, final-revalidation restoration, and BAI-
  publication `67` plus BAM-restoration `68` with exact predecessor/unrelated/
  erased-recovery state. Run only shell syntax and that complete direct test.
- **Producer admission/signal baseline:** change only the same shell test for
  missing explicit samtools before directory creation, five admitted-input/
  reference mutations that still succeed, and TERM `143` predecessor/
  unrelated preservation with owned residue removed and no attempt marker.
  Run only shell syntax and that complete direct test.
- **Validator baseline:** change only the direct validator test for arbitrary-
  CWD dry-run/execute/repeat bytes, exit-`0` failed evidence, exit-`2`
  nonpublication, and post-build mutation/predecessor preservation. Run only
  that direct pytest file; exact reference-bridge cases wait for cutover.
- **Scheduler baseline:** change only the central SLURM suite for Java, GATK,
  samtools, submit-directory, log, warning/delegation, and stale-pair states.
  Run only the Step `05` scheduler selection. The assembled tip adds no other
  test, production, fixture, baseline, documentation, dependency, or future-
  owner file.
- **Cutover and card-boundary gate:** move exactly five files and update exactly
  ten callers/harness owners, including the five moved-consumer reference-
  bridge tests. After minimal final-path checks, measure coverage with only the
  intentionally stale documentation assertion deselected, then run the exact
  RUNBOOK aggregate once with explicit result JSON. Only the exact migration-
  caused documentation paths plus nine inherited `UNREFINED` locations may
  remain as a nonpassing expected-only ceiling. Any other fault must be
  understood before commit.
- **Close and rollback:** the separate close adds the owner README, repairs the
  contract and full canonical/current/lifecycle roster, records exact evidence,
  and runs the documentation-only gate. It may retain only nine inherited
  findings. Roll back docs, cutover, scheduler, validator, producer admission/
  signal, then producer transaction. Git rollback never alters runtime/
  production evidence, locks, logs, or recovery artifacts.
- **Minimal slice check:** `git diff --check` passed for exactly the active card,
  current roadmap/handoff, and dated audit. Per the card-boundary-only
  validation rule, no computational suite or complete documentation validator
  ran in this planning slice; the complete documentation gate remains owned by
  the separate card close.

## 2026-08-03T08:02:16-0400 — MIG-03J executable and documentation lifecycle completed

- **Verified bounded sequence:** from published planning checkpoint `d9bdf21`,
  publish four sequential old-path test-only checkpoints: transaction
  `42bf851`, admission/signal `3913215`, validator `8eb3a0b`, and scheduler
  `ec240ae`. Each checkpoint was clean, upstream-equal, and live-remote-equal
  before the next slice. No production, fixture, coverage-baseline,
  documentation batch, dependency, or later-owner file entered those slices.
- **Transaction decisions and retained risk:** the direct producer suite now
  proves lone-final rejection preserves exact bytes, a final-path
  revalidation failure restores a complete predecessor, and injected BAI-
  publication exit `67` followed by injected prior-BAM-restoration exit `68`
  propagates `67`. That state leaves the prior BAM missing and prior BAI
  restored, preserves unrelated bytes, and erases backups, lock, scratch, and
  recovery evidence. This is an ambiguous/data-loss defect, not successful
  rollback, cleanup proof, or retry authority. Transaction checkpoint shell-
  test SHA-256 was
  `85f66da868632995979a16cbba4febcb5cd0e24fd7a9e5577baa46679afdc119`.
- **Admission, mutation, and signal decisions:** missing explicit samtools is
  rejected before output-directory creation. Controlled GATK-time mutation of
  the admitted BAM, BAI, FASTA, FAI, and DICT remains undetected and the
  producer exits `0`; inputs are not stable-snapshot bound. Controlled TERM
  exits `143`, preserves predecessor/unrelated bytes, removes the owned lock/
  scratch, and leaves no receipt or recovery marker. Their absence proves no
  attempt identity or clean recovery. Admission/signal checkpoint shell-test
  SHA-256 was
  `2074e0c1201f44e376e903418f86e1c92d9c2dc50eb8d755e7dc33c2c557e104`.
- **Validator decisions:** the old-path direct suite passed `9` tests and
  froze arbitrary-CWD dry-run/execute/repeat byte identity with unchanged
  inputs, quickcheck nonzero as exit-`0` failed evidence, header failure as
  exit-`2` nonpublication, and post-build mutation as exit `2` preserving a
  valid report predecessor. Checkpoint test SHA-256 was
  `1abaf9e93151d68d10fa36f7631b38dfe5bdd8ffd9fce3816621fa0754ae13db`.
  Cutover added exactly five owner-local reference-bridge cache/path/failure
  cases. Validator exit `0` still may contain failed rows and does not prove
  the GATK transform.
- **Scheduler decisions:** the Step `05` selection passed `24` tests with
  `118` unrelated cases deselected and froze Java override/`JAVA_HOME`/PATH
  selection, unusable home fallback, missing/unusable override, Java command/
  parse/version failures, GATK/samtools version failures, warning-only missing
  tools with unchanged delegation, absent-submit-directory fallback, body-
  level `logs/` mutation, and stale-pair false success. Central suite SHA-256
  was `61d51dc607d6bfae35385677cc241e14e54cf2fb4b3b06a417555437a215a1f0`.
  Submit-CWD fallback, exported `/tmp`, tolerated module diagnostics, Bash
  `3.2`, warning-only probe, version-command, and file-only post-check states
  remain defects, not scheduler proof.
- **Atomic owner cutover:** published executable/test checkpoint
  `ef4cad7b5eeb54e1e7fd963faea427afdbfce0a2` applied exactly five reviewed
  moves and ten integration-owner updates. Final owner is
  `src/norad/stages/split_N_cigar_reads_with_GATK/`; direct tests are under
  `tests/stages/split_N_cigar_reads_with_GATK/`. No legacy owner, wrapper,
  alias, symlink, compatibility copy, package marker, descriptor, schema,
  second owner, helper move, reference redesign, transaction/receipt/recovery
  mechanism, dependency action, or later-card preload was added.
- **Native and private-owner evidence:** final producer is mode `0644`,
  `18,920` bytes, `596` lines, SHA-256
  `e25c8d94d940aa02187e5550c51a71b8fdd8ca75660a07f5851dc215679248ac`;
  validator is mode `0644`, `12,584` bytes, `334` lines,
  `f1a1128510de0c4e2b40800185c6cc039c7bb4ed5bf158396d87ee5d0730cdf3`;
  job is mode `0644`, `5,383` bytes, `167` lines,
  `3931b0976a9c97438b5980706a86203eb49ed472390a5a2f201830ae7ccfa147`.
  All exactly match architecture projections. The validator exact-loads
  neutral report/BAM owners and unchanged public reference provenance under
  private identities, validates exact paths/APIs, preserves foreign or
  incomplete caches, removes only its owned failed partial, and mutates no
  `sys.path`.
- **Focused final-path evidence:** producer/job/direct-test shell syntax and
  the complete producer shell suite passed. The moved validator passed `14`
  tests, the Step `05` scheduler selection passed `24` with `118` deselected,
  and the explicit public-CLI/Make, roster/report/BAM-helper, artifact, and
  path-map surface passed `392` tests. All are local fixture/fake-tool evidence.
- **Coverage decision and result:** one serial pre-aggregate measurement with
  only the intentionally stale documentation assertion deselected passed
  `1,159` tests with `17` skips in `411.68s`. Step `05` moved to its final path
  at `178/192` covered lines and `45/54` branches; global coverage is
  `9550/11720` lines and `3347/4772` branches. All `31` non-target rows stayed
  exact, target/global rates increased, and the standalone policy comparison
  passed. The baseline edit is only the moved target row, canonical sorting,
  and mechanically reconciled totals.
- **Aggregate result, not green:** the exact card-boundary command wrote
  `/private/tmp/norad-validation-mig-03j.json` and ended status `2` in
  `406.739s`. Static preflight passed in `0.176s`, shell contracts in `87.205s`,
  guarded R in `351.324s`, and report runtime in `287.051s`. Python ran
  `1,159` passes and `17` skips before its sole documentation assertion listed
  exactly ten intentionally stale Step `05` links—five in the functional-
  owner inventory and five in the colocated contract—plus the nine inherited
  `UNREFINED` card-location findings. No other lane, test, coverage, tool, or
  dependency fault occurred. Existing pinned environments were used; nothing
  was installed, restored, deleted, or updated.
- **Documentation and lifecycle decisions:** add one adjacent owner README;
  correct the contract from unimplemented/flat and stale peer-stage helper
  attribution; update current architecture, inventory, coverage, ownership,
  roadmap, handoff, runbook, troubleshooting, neutral library, public
  reference, FASTA-sidecar, canonical-BAM, and Step `04` predecessor routes;
  repair every final path/command and inbound lifecycle link; move only
  `MIG-03J` from `IN_PROGRESS` to `COMPLETED`; and retain all historical
  cluster observations explicitly as historical. No diagram changes because
  semantic identities, direct DAG edges, and public data flow did not change.
- **Recovery and evidence ceiling:** before cleanup/retry, preserve all final,
  temp, alternate-index, backup, GATK-temp, lock/owner, input/reference,
  unrelated, stream, scheduler job/log, checkout, and tool/version evidence;
  rule out lock owner, producer, and Step `06` readers; never combine attempts,
  infer identity from timestamps, remove a foreign lock, or adopt stale
  wrapper success. Only an isolated destination is eligible for a separately
  authorized diagnostic retry. Historical GATK/Java/samtools and six-sample
  cluster observations are not migration proof. MIG-03J creates no real tool,
  scheduler, cluster, production, scientific-review, or biological evidence.
- **Documentation gate and rollback:** `git diff --check` passes. The exact
  RUNBOOK documentation validator has no MIG-03J path, anchor, lifecycle,
  dependency, cycle, orphan, or diagram finding and retains only the nine
  inherited `UNREFINED` locations. That expected-only result remains
  nonpassing, not green. Roll back this documentation close, executable
  `ef4cad7`, scheduler `ec240ae`, validator `8eb3a0b`, admission/signal
  `3913215`, then transaction `42bf851`; Git rollback never changes runtime or
  recovery evidence.

## 2026-08-03T08:15:45-0400 — MIG-03K and sequential reviews defined

- **Verified parent and live-DAG choice:** published MIG-03J documentation
  close `db60dfa965f4c878aacfe3221dfc50d30644cb74` was clean, tracked/untracked-
  empty, free of recovery/index locks, and equal across local `HEAD`, configured
  upstream, and the live remote branch before definition work. The canonical
  direct-edge map leaves exactly one eligible unmigrated owner:
  `partition_BAM_by_mechanical_read_orientation`. Its sole direct predecessor,
  `split_N_cigar_reads_with_GATK`, is migrated. Step `07` remains blocked and
  no Step `07` or later card is created.
- **Frozen native boundary:** define only semantic stage
  `norad.stage.partition_BAM_by_mechanical_read_orientation.v1`, historical
  alias `06`, final source home
  `src/norad/stages/partition_BAM_by_mechanical_read_orientation/`, and mirrored
  test home
  `tests/stages/partition_BAM_by_mechanical_read_orientation/`. Candidate moves
  are the mode-`0755` producer, mode-`0644` validator, mode-`0755` job, mode-
  `0755` direct shell test, and mode-`0644` direct validator test. Three native
  assets total `37,398` bytes and `1,136` lines with frozen hashes
  `bb0ebbaea9158c0dfceb3a0cd2e083c99e8f63913859c10df93ec85314de2275`,
  `7b39b8fc27b9992c8ca4b2b4111e5ae872b15806e520c4ca9d595b81e6cc7c69`,
  and `3c0bf399187cb7624350d9896fd2e0228daaf61a7fa71e89c5ba4ce22b7a1419`.
- **Proposed cutover and review question:** the evidence-backed hypothesis is
  five moves plus nine integration owners: Make, artifact producer mapping and
  exact migrated-producer evidence, public CLI maps, SLURM map/delegation,
  validation roster, neutral report-loader matrix, coverage baseline, and the
  literal Make expansion. Architecture review must prove that ceiling, exact
  final hashes/root depths/test-helper bridge, executable-mode continuity, and
  the disposition of obsolete documentation-only
  `tests/pending/test_step_06_split_bam_by_read_orientation.sh`. The scaffold
  may not become a second active test owner.
- **Mechanical and evidence decisions:** preserve `FWD_like` as `-f 99` plus
  `-f 147` and `REV_like` as `-f 83` plus `-f 163`, including additional-bit
  acceptance and non-exhaustive assignment. These labels remain mechanical;
  they are not biological strand, strandedness, sense, or antisense. Preserve
  six Step `06` artifact identities and the eleven-column counts TSV without a
  schema or orientation-policy change.
- **Transaction and validation risks:** preserve but do not approve absent
  input snapshot recheck, absent attempt receipt, best-effort five-file
  restoration, cleanup erasure after rollback failure, and an output-directory
  lock that does not independently serialize a separately chosen QC path. The
  producer quickchecks merged BAMs and enforces nonempty groups plus assigned/
  input bounds but does not explicitly reconcile each pair of flag subcounts
  to its merged count. The independent validator checks container magic and
  counts arithmetic without samtools, BAM recount, flag inspection, BAM/BAI
  correspondence, sort/read-group metadata, or biological/current-attempt
  proof; exit `0` may publish failed rows. Reliability review must assign safe
  old/final-path oracles rather than fix or bless these states.
- **Scheduler risks:** preserve submit-CWD fallback, exported `/tmp`, tolerated
  samtools module diagnostics, fixed default tool plus override, version
  command, one requested CPU with operator-controlled `THREADS`, body-level
  `logs/` mutation, Bash `3.2` empty-array dry-run failure, five-file wrapper
  post-check, and stale-complete-set false success. These are review inputs, not
  scheduler, current-attempt, production, scientific, or biological proof.
- **Coverage and evidence ceiling:** frozen validator coverage is `107/119`
  lines and `23/30` branches; global coverage is `9550/11720` lines and
  `3347/4772` branches. Any later final measurement must keep non-target rows
  exact and preserve target/global rates and covered-count floors. Definition
  adds no real samtools, scheduler, cluster, production, scientific-review,
  biological-orientation, or biological-readiness evidence.
- **Bounded lifecycle decision:** create only unselected `MIG-03K` and
  unselected sequential `REVIEW-ARCH-03K` → `REVIEW-REL-03K` →
  `REVIEW-UX-03K`. No card is selected; no executable, test, harness,
  configuration, dependency, schema, fixture, report-template, runtime,
  scheduler, cluster, production, or future-owner file changes or runs.
- **Minimal slice check:** `git diff --check` passed. Per the card-boundary-only
  validation rule, no computational suite or complete documentation validator
  ran in this definition slice; the complete documentation gate belongs to the
  architecture-review card boundary.

## 2026-08-03T08:20:43-0400 — REVIEW-ARCH-03K selected

- **Selection:** from clean, published, local/upstream/live-remote-equal
  definition checkpoint `0bc12acbb7441dabcbd098e22f9a7e5811eb2d72`, move only
  `REVIEW-ARCH-03K` to `IN_PROGRESS` and repair its direct reliability-review
  lifecycle link. `MIG-03K`, `REVIEW-REL-03K`, and `REVIEW-UX-03K` remain
  unselected in `TODO`; Step `07` and every later owner/review card remain
  uncreated.
- **Boundary:** this checkpoint selects read-only architecture review but
  records no finding. No executable, test, harness, configuration, dependency,
  schema, fixture, report-template, runtime, scheduler, cluster, production,
  scientific-review, biological-orientation, or biological state changes or
  runs.
- **Minimal slice check:** `git diff --check` passes. Per the card-boundary-only
  validation rule, no computational suite or complete documentation validator
  runs at selection; the complete documentation gate belongs to architecture-
  review completion.

## 2026-08-03T09:56:11-0400 — REVIEW-ARCH-03L completed

- **Review basis:** complete a separate read-only architecture pass from clean,
  published, local/upstream/live-remote-equal selection
  `e34edb55e93b9874830fcc66688e5ac3b0d3f9dd`. Recheck the canonical identity,
  direct DAG, target topology, migration mechanics, modes, every tracked old
  path/basename reference, public CLI/Make/SLURM maps, neutral report loader,
  artifact projection/reconciliation, coverage row, direct/pending test owners,
  shared partition manifests, and reverse rollback. Independent authorship is
  not claimed.
- **Eligibility and placement decision:**
  `generate_partitioned_cohort_mpileup_VCFs` remains the only eligible
  unmigrated owner; Step `08` remains blocked, uncreated, and unselected. Move
  only the mode-`0755` producer, mode-`0644` validator, mode-`0644` job, mode-
  `0755` direct shell test, and mode-`0644` direct validator test to their
  frozen stage/test homes. Preserve direct-executable, explicit-interpreter,
  and `sbatch`/explicit-Bash surfaces and exact modes.
- **Exact cutover decision:** all supported callers are repository-owned and
  fit one atomic direct cutover of five moves plus exactly nine integration
  owners: Make, artifact producer mapping, artifact final-path/hash assertion,
  public CLI, SLURM path/delegation, validation roster, neutral report-loader
  map, coverage row, and literal Make fixture. Exact tracked-path/basename/
  recipe searches found no tenth integration owner. Root Step `07` partition
  manifests remain shared inputs, the contract remains documentation, and no
  pending Step `07` scaffold exists. An extra integration owner, sixth move,
  or different production edit reopens architecture review; no wrapper, alias,
  duplicate, package, or compatibility copy is justified.
- **Production and moved-test roots:** production edits only the producer usage
  path, validator report root `parents[1]` → `parents[4]`, and job child path.
  The private report identity/behavior stays unchanged. The shell test uses
  `SCRIPT_DIR/../../..` and final producer/job targets. The Python test uses
  `parents[3]`, the final validator, and a private exact-file load of unchanged
  `tests/validation_roster_expectations.py` under
  `generate_partitioned_cohort_mpileup_vcfs_validation_roster_oracle` without
  `sys.path`, package, production-helper, or global module-cache change.
- **Projected native evidence:** applying only those reviewed substitutions in
  read-only streams projects producer `31,526` bytes / `893` lines /
  `e3af9900b6f7831f2feafbc6d13f3755a475f02e5013c8b756107ddd90d22297`,
  validator `13,524` / `334` /
  `3191a379a4c2e1d589eeb3f327314d91dcb70f5e79da6e2b4f344ffb2b68763b`,
  and job `4,421` / `133` /
  `fbd8144a362cdd688ac14efcd8c003a3527b878d90ab525277a92018ac9a1ed6`.
  Any final production hash or mode difference reopens review.
- **Artifact and coverage ownership:** Step `07` artifact evidence changes only
  to the final producer path and first projected hash. VCF, receipt, validation-
  report identities, schemas, ordering, downstream dependency, receipt-marker
  interpretation, consumers, and scientific meaning remain fixed. Coverage
  renames one validator row and must preserve its `167/198` line and `48/72`
  branch rates, every non-target row, and global covered-count floors.
- **Rollback and evidence ceiling:** reverse documentation first, then the
  atomic five-move/nine-update cutover with Make/oracle and artifact path/hash
  assertion together, then later reliability baselines in reverse order. Git
  rollback never changes runtime VCF/receipt, lock, backup, scratch, log, or
  recovery evidence. This review changed or ran no executable, test, harness,
  dependency, real bcftools, scheduler, production, scientific-review,
  variant/editing-site, or biological state.
- **Card-boundary gate:** `git diff --check` passed. The exact RUNBOOK
  documentation validator reports only the nine inherited `UNREFINED` card-
  location findings and no architecture-review-caused path, lifecycle,
  dependency, cycle, orphan, anchor, or diagram finding. The expected-only
  result remains nonpassing and is not called green.

## 2026-08-03T08:25:54-0400 — REVIEW-ARCH-03K completed

- **Review basis:** complete a separate read-only architecture pass from clean,
  published, local/upstream/live-remote-equal selection
  `efdec11229edcddaa1a14d6165330898a0261a13`. Recheck the canonical identity,
  direct DAG, target topology, migration mechanics, modes, every tracked old
  path/basename reference, public CLI/Make/SLURM maps, neutral report loader,
  artifact projection/reconciliation, coverage row, active/pending test owners,
  and reverse rollback. Independent authorship is not claimed.
- **Eligibility and placement decision:** `partition_BAM_by_mechanical_read_orientation`
  remains the only eligible unmigrated owner; Step `07` remains blocked,
  uncreated, and unselected. Move only the mode-`0755` producer, mode-`0644`
  validator, mode-`0755` job, mode-`0755` direct shell test, and mode-`0644`
  direct validator test to their frozen stage/test homes. Preserve direct-
  executable, explicit-interpreter, and scheduler surfaces and exact modes.
- **Exact cutover decision:** all supported callers are repository-owned and
  fit one atomic direct cutover of five moves plus exactly nine integration
  owners: Make, artifact producer mapping, artifact final-path/hash assertion,
  public CLI, SLURM path/delegation, validation roster, neutral report-loader
  map, coverage row, and literal Make fixture. Exact tracked-path/basename
  searches found no tenth integration owner. An extra integration owner,
  sixth executable move, or different moved-file edit reopens architecture
  review; no wrapper, alias, duplicate, package, or compatibility copy is
  justified.
- **Production and moved-test roots:** production edits only the producer usage
  path, validator report root `parents[1]` → `parents[4]`, and job child path.
  The private report identity/behavior stays unchanged and the neutral loader
  matrix covers its path/cache/failure states. The shell test uses
  `SCRIPT_DIR/../../..` and final producer/job targets. The Python test uses
  `parents[3]`, the final validator, and a private exact-file load of unchanged
  `tests/validation_roster_expectations.py` without `sys.path`, package, or
  production-helper change.
- **Projected native evidence:** applying only those reviewed substitutions in
  read-only streams projects producer `24,542` bytes / `784` lines /
  `74399ceb42cb081b213256977b03137d7ae8513c07f98fb4cd06b2f7ee6a2730`,
  validator `8,892` / `227` /
  `96385f8988219a486094c05d490acc8d2b228001d241ee29af784ec269460b33`,
  and job `4,072` / `125` /
  `fc1ddbce861293fac9dcbd9e87571d8b4f955ae602f4f2daa6afa7908d5251af`.
  Any final production hash/mode difference reopens review.
- **Artifact, coverage, and pending-test ownership:** Step `06` artifact
  evidence changes only to the final producer path and first projected hash.
  All six identities, schemas, contents, ordering, counts reconciliation/
  completion-marker interpretation, consumers, and meaning remain fixed.
  Coverage renames one validator row and must preserve its rates, all non-
  target rows, and global covered-count floors. Delete obsolete documentation-
  only `tests/pending/test_step_06_split_bam_by_read_orientation.sh` at the
  separate documentation close because the active direct suite already
  implements all four bullets; do not move or promote it.
- **Rollback and evidence ceiling:** reverse documentation and pending-scaffold
  deletion first, then the atomic five-move/nine-update cutover with Make/
  oracle and artifact path/hash assertion together, then later reliability
  baselines in reverse order. Git rollback never changes runtime BAM/BAI/
  counts, lock, backup, scratch, log, or recovery evidence. This review changed
  or ran no executable, test, harness, dependency, runtime, scheduler,
  production, scientific-review, biological-orientation, or biological state.
- **Card-boundary gate:** `git diff --check` passed. The exact RUNBOOK
  documentation validator reports only the nine inherited `UNREFINED` card-
  location findings and no architecture-review-caused path, lifecycle,
  dependency, cycle, orphan, anchor, or diagram finding. The expected-only
  result remains nonpassing and is not called green.

## 2026-08-03T08:30:04-0400 — REVIEW-REL-03K selected

- **Selection:** from clean, published, local/upstream/live-remote-equal
  architecture checkpoint `2452332d463f9517eeaf0b2a5af13b9f0bf65fbc`, move
  only `REVIEW-REL-03K` to `IN_PROGRESS` and repair its architecture/usability
  lifecycle links. `MIG-03K` and `REVIEW-UX-03K` remain unselected in `TODO`;
  Step `07` and every later owner/review card remain uncreated.
- **Boundary:** this checkpoint selects read-only reliability review but
  records no finding. No executable, test, harness, configuration, dependency,
  schema, fixture, report-template, runtime, scheduler, cluster, production,
  scientific-review, biological-orientation, or biological state changes or
  runs.
- **Minimal slice check:** `git diff --check` passes. Per the card-boundary-only
  validation rule, no computational suite or complete documentation validator
  runs at selection; the complete documentation gate belongs to reliability-
  review completion.

## 2026-08-03T08:38:44-0400 — REVIEW-REL-03K completed

- **Review basis:** complete a separate read-only reliability pass from clean,
  published, local/upstream/live-remote-equal selection checkpoint
  `7ca503d7224f068fe51df0e9ad54c35b1d346583`. Inspect the producer, validator,
  scheduler, three active test owners, neutral report/roster/public-CLI suites,
  artifact reconciliation, coverage baseline, runbook/troubleshooting, and
  historical risk matrix. Independent authorship is not claimed.
- **Producer child/count decision:** the first old-path direct-shell checkpoint
  will freeze exact filter, merge, index, and count-command exits `71`-`74`,
  stderr, nonpublication, unrelated-file preservation, and owned dual-directory
  cleanup. It also owns missing explicit samtools before directory creation,
  arbitrary-CWD basename/PATH execution, assigned-greater-than-input rejection,
  and current exit-`0` publication when flag `99 + 147` disagrees with the
  merged FWD count. Existing cases retain help/admission/thread/dry-run,
  command/count/fraction success, empty group, temporary quickcheck, lock,
  stale-path, and ordinary rollback behavior.
- **Producer transaction/recovery decision:** the second old-path direct-shell
  checkpoint will fix final move order with counts last, preserve an incomplete
  predecessor, restore a complete five-file predecessor after final-path
  quickcheck failure, and inject publication exit `67` followed by FWD-BAM
  restoration exit `68`. The last fault propagates `67`, leaves the prior FWD
  BAM missing, restores the other four prior files, preserves unrelated bytes,
  and exposes cleanup erasure of backups, lock, scratch, and recovery evidence.
  This ambiguous data-loss state is not approved.
- **Producer stability/collision decision:** the third old-path direct-shell
  checkpoint will preserve the admitted BAM/BAI mutation blind spot, controlled
  `TERM` exit `143`, and the output-directory-only lock defect. A deterministic
  barrier lets two same-sample runs with distinct output directories and shared
  QC both exit `0`; both BAM/BAI quartets remain while the last writer replaces
  the shared counts TSV, producing mixed-attempt evidence. Assert predecessor/
  unrelated preservation where applicable and the absence of a receipt or
  durable recovery marker; add no transaction mechanism.
- **Validator decision:** one old-path direct-validator checkpoint will add
  arbitrary-CWD dry-run/execute/repeat byte parity, invalid container magic as
  exit-`0` failed evidence, and post-build mutation of each of the five inputs
  as exit `2` with a valid predecessor report preserved. Existing direct count
  disagreement owns flag/merged and assigned arithmetic failure; the neutral
  report suite owns exact-loader/publication faults, and the roster suite owns
  the five IDs. No duplicate helper or private/public API is warranted.
- **Scheduler decision:** one old-path central-suite checkpoint will add
  samtools version-command failure before delegation, missing/nonexecutable
  warning with unchanged delegation, PATH basename forwarding, absent-submit-
  directory fallback, dry-run `logs/`-only mutation, `THREADS` independent of
  the one-CPU request, and byte-exact false success over five stale nonempty
  outputs. Generic cases continue to own directives/mode, module calls and
  tolerance, override arguments, invalid mode, child exit, missing-output
  rejection, and the Bash `3.2` empty-array defect.
- **Bounded sequence, artifact, coverage, and evidence:** execute exactly five
  small sequential old-path test-only checkpoints—producer child/count,
  producer transaction, producer stability/collision, validator, scheduler—
  using only the existing three test files. Add no fixture, fourth test owner,
  production edit, coverage edit, documentation batch, dependency, or future
  owner. Existing artifact tests own six Step `06` identities, reconciliation,
  and six-decimal fraction. Later coverage may rise but must preserve target
  rates, every non-target row, and global covered-count floors. This review
  changed or ran no executable, test, harness, runtime, scheduler, production,
  scientific-review, biological-orientation, or biological evidence.
- **Card-boundary gate:** `git diff --check` passed. The exact RUNBOOK
  documentation validator reports only the nine inherited `UNREFINED` card-
  location findings and no reliability-review-caused path, lifecycle,
  dependency, cycle, orphan, anchor, or diagram finding. The expected-only
  result remains nonpassing and is not called green.

## 2026-08-03T08:41:01-0400 — REVIEW-UX-03K selected

- **Selection:** from clean, published, local/upstream/live-remote-equal
  reliability-review completion
  `1d5406ac4a085ea1ad82a2c8bedf37f5b69a4bd5`, move only `REVIEW-UX-03K` to
  `IN_PROGRESS` and repair its reliability/migration lifecycle links.
  `MIG-03K` remains unselected in `TODO`; Step `07` and every later owner/review
  card remain uncreated.
- **Boundary:** this checkpoint selects read-only usability review but records
  no finding. No executable, test, harness, configuration, dependency, schema,
  fixture, report-template, runtime, scheduler, cluster, production,
  scientific-review, biological-orientation, or biological state changes or
  runs.
- **Minimal slice check:** `git diff --check` passes. Per the card-boundary-only
  validation rule, no computational suite or complete documentation validator
  runs at selection; the complete documentation gate belongs to usability-
  review completion.

## 2026-08-03T08:46:24-0400 — REVIEW-UX-03K completed

- **Review basis:** complete a separate read-only usability pass from clean,
  published, local/upstream/live-remote-equal selection checkpoint
  `3f71f877627d039b158ded9b5f470c04ee1424b0`. Inspect public CLI/Make/SLURM
  characterization, producer/validator help and behavior, final owner/test
  topology, artifact/coverage/helper routes, the contract, runbook,
  troubleshooting, documentation ownership, predecessor/consumer semantics,
  and reviewed recovery defects. Independent authorship is not claimed.
- **Final invocation decision:** documentation close replaces every live Step
  `06` producer, validator, job, focused-test, helper, artifact-provenance, and
  coverage path. Root use directly invokes the final mode-`0755` producer and
  submits the final mode-`0755` job; the mode-`0644` validator uses an explicit
  interpreter. Arbitrary-CWD use makes every executable/interpreter, BAM,
  output/QC, samtools, counts/report, checkout, and owner path absolute. No
  installed command, package import, alias, wrapper, symlink, `PYTHONPATH`, or
  global `sys.path` compatibility route is supported.
- **Dry-run and scheduler decision:** direct producer dry-run validates the
  exact BAI, threads, and samtools resolution, prints the full two-directory
  plan, invokes no samtools, and creates neither directory. Validator dry-run
  reads five explicit inputs, prints five rows plus its completion line, invokes
  no samtools, and writes no report. Scheduler use starts at the checkout,
  creates `logs/` before submission, and preserves submit-CWD fallback, `/tmp`,
  module/version diagnostics, fixed/override samtools, warning-only unusable
  preflight, one CPU independent of `THREADS`, body `logs/`, Bash `3.2`, exact
  delegation, and stale-five-file false success.
- **Recovery and next-safe-action decision:** preserve all five finals, every
  two-directory temp/backup, every relevant output-directory lock/owner, input
  pair, unrelated file, stream, scheduler job/accounting/log, checkout/submit
  CWD, override, and samtools path/version before action. Failed restoration can
  leave the prior FWD BAM missing while the other four files return and all
  recovery paths disappear. Distinct output locks do not serialize a shared QC
  path, so last-writer counts can mix attempts. Rule out every producer and Step
  `07` reader; do not combine/reconstruct members, infer identity from counts or
  timestamps, remove foreign locks, or adopt stale wrapper success. A
  separately authorized diagnostic retry uses isolated output and QC
  directories. Git rollback cannot restore or authenticate runtime artifacts.
- **Ownership, evidence, and documentation decision:** update the contract's
  unimplemented/flat-path, stale-test, Step-`00a` publisher, and deferred-
  migration text to the implemented owner, mirrored tests, and neutral report
  library. Producer exit `0` may retain flag-subcount/merged-count disagreement
  and proves no biological orientation or attempt identity; validator exit `0`
  may contain failed rows and performs no BAM quickcheck/recount; scheduler exit
  `0` may accept stale files. Artifact identity/meaning is unchanged apart from
  final path/hash. Add one adjacent README; repair inventory, architecture
  migrated-validator count, test baseline, documentation ownership, runbook,
  troubleshooting, current roadmap/handoff, lifecycle, and audit. Stable Step
  `05` predecessor/Step `07` consumer semantics and diagrams need no edit.
- **Rollback and evidence ceiling:** revert documentation first, atomic five-
  move/nine-update cutover second, then scheduler, validator, producer
  stability/collision, transaction, and child/count baselines. Historical six-
  sample cluster observations remain historical. This review changed or ran no
  source, test, harness, dependency, real samtools, scheduler, production,
  scientific-review, biological-orientation, or biological evidence.
- **Card-boundary gate:** `git diff --check` passed. The exact RUNBOOK
  documentation validator reports only the nine inherited `UNREFINED` card-
  location findings and no usability-review-caused path, lifecycle, dependency,
  cycle, orphan, anchor, or diagram finding. The expected-only result remains
  nonpassing and is not called green.

## 2026-08-03T08:50:01-0400 — MIG-03K selected

- **Selection:** from clean, published, local/upstream/live-remote-equal
  usability-review completion
  `5653ce25a6f5f442b8136691a58030c831180f88`, move only `MIG-03K` to
  `IN_PROGRESS`, repair its direct usability-review lifecycle link, and make it
  the sole active migration. Step `07` and every later owner/review card remain
  uncreated.
- **Seven-slice boundary:** execute five old-path test-only baselines in strict
  order—producer child/count, producer transaction, producer stability/
  collision, validator, then scheduler—followed by one atomic five-move/nine-
  update executable/test cutover with the single complete computational card-
  boundary gate, then one separate canonical documentation/lifecycle close.
  Each slice is independently revertible and must be published and proven
  upstream/live-remote-equal before the next.
- **Validation and documentation decision:** run only the smallest named
  focused check at each test-only or cutover sub-boundary. Defer all migration-
  link repairs, small canonical-documentation updates, the owner README/
  contract close, and deletion of the obsolete pending scaffold to the final
  documentation slice. Run the complete computational gate only at the
  assembled executable card boundary and the exact documentation-only gate
  only at lifecycle close.
- **Boundary:** selection changes only lifecycle, planning, current roadmap/
  handoff, and this audit. It changes or runs no executable, test, harness,
  configuration, dependency, schema, fixture, report-template, runtime,
  scheduler, cluster, production, scientific-review, biological-orientation,
  or biological state.
- **Minimal slice check:** `git diff --check` passes. Per the card-boundary-only
  validation rule, no computational suite or complete documentation validator
  runs at selection; those checks remain assigned to their recorded boundaries.

## 2026-08-03T09:35:04-0400 — MIG-03K executable and documentation lifecycle completed

- **Verified bounded sequence:** from published selection checkpoint `cd5d8e9`,
  publish five sequential old-path test-only checkpoints: child/count
  `3ae6e3e`, transaction `dafcd18`, stability/collision `66e41fe`, validator
  `1332529`, and scheduler `e871d5c`. Each checkpoint was clean, upstream-
  equal, and live-remote-equal before the next slice. No production, fixture,
  coverage-baseline, documentation batch, dependency, or later-owner file
  entered those baseline slices.
- **Child/count decisions and retained risk:** exact filter, merge, index, and
  count-command failures propagate exits `71`–`74`, publish no final, clean
  owned scratch/lock, preserve unrelated bytes, and emit the expected stderr.
  Missing explicit samtools is rejected before directory creation; a basename
  resolves through `PATH` from arbitrary CWD; and assigned greater than input
  is rejected. The producer still exits `0` and publishes when flag `99 + 147`
  counts disagree with the merged FWD count. This is a characterized defect,
  not arithmetic approval. Baseline shell-test SHA-256 was
  `824ee5adec0509088e410b5a34fae2538278dced7f18081aef65c736b3813754`.
- **Transaction decisions and retained risk:** counts is published last; an
  incomplete predecessor set is rejected with exact preservation; and final-
  path quickcheck failure restores all five predecessor files byte-exactly.
  Injected counts-publication exit `67` followed by prior-FWD-BAM restoration
  exit `68` propagates `67`, leaves that prior BAM missing, restores the other
  four prior files, preserves unrelated bytes, and erases backup/lock/scratch/
  recovery evidence. This is ambiguous data loss, not successful rollback or
  retry authority. Transaction shell-test SHA-256 was
  `ee9128d572713aee2ba9b4d7f1706ffa59a4c1a8a8d93e7586cc85146da83fd3`.
- **Stability, signal, and collision decisions:** controlled BAM/BAI mutation
  during filtering remains undetected and the producer exits `0`; admitted
  inputs are not stable-snapshot bound. Controlled TERM exits `143`, preserves
  predecessor/unrelated bytes, and removes owned lock/scratch. Barrier-
  controlled same-sample runs with distinct output directories and shared QC
  both exit `0`, retain both BAM/BAI quartets, and leave last-writer counts from
  one attempt beside the other attempt's outputs. No receipt or durable
  recovery marker identifies the attempt. Stability/collision shell-test SHA-
  256 was
  `ca97c0bc7b781a56457eaed88980f28f1fb875871ab8173863e738219294944f`.
- **Validator decisions:** the old-path direct suite passed `15` tests and
  froze arbitrary-CWD dry-run/execute/repeat byte parity with unchanged inputs
  and no invocation-CWD residue; four invalid BAM/BAI container cases as exit-
  `0` failed evidence; and post-build mutation of each of five inputs as exit
  `2` preserving a valid predecessor report. The validator still invokes no
  samtools, quickcheck, record recount, flag inspection, BAM/BAI correspondence,
  or sort/read-group validation. Baseline test SHA-256 was
  `5f39f8157c27a01d516725c22c26b90a6ea421d0bfebaa29dd9c981369aef140`.
- **Scheduler decisions:** the old-path Step `06` selection passed `16` tests
  with `134` unrelated cases deselected. It freezes samtools version-command
  failure before delegation; warning-only missing/nonexecutable paths with
  unchanged delegation; PATH-basename forwarding; dynamic absent-submit-CWD
  fallback; body-level `logs/`-only dry-run mutation; `THREADS` independent of
  the one-CPU request; and a zero-output child falsely succeeding against five
  stale nonempty files. Generic cases retain directives/mode, tolerated module
  calls, override arguments, invalid mode, child exit, missing outputs, and
  Bash `3.2`. Central-suite SHA-256 was
  `11f27ddfb51d0497e2ef53e254d00d18c56eb9757a8d9d093bf25bb69a3cf924`.
- **Atomic owner cutover:** published executable/test checkpoint
  `1d5b76a9345d585a079b22b4ffd8c13566f9e177` applied exactly five reviewed
  moves and nine integration-owner updates. Final owner is
  `src/norad/stages/partition_BAM_by_mechanical_read_orientation/`; direct
  tests are under the mirrored stage test directory. No legacy owner, wrapper,
  alias, symlink, compatibility copy, package marker, descriptor, schema,
  second owner, transaction/receipt/recovery mechanism, dependency action, or
  later-card preload was added.
- **Native and private-owner evidence:** final producer is mode `0755`,
  `24,542` bytes, `784` lines, SHA-256
  `74399ceb42cb081b213256977b03137d7ae8513c07f98fb4cd06b2f7ee6a2730`;
  validator is mode `0644`, `8,892` bytes, `227` lines,
  `96385f8988219a486094c05d490acc8d2b228001d241ee29af784ec269460b33`;
  job is mode `0755`, `4,072` bytes, `125` lines,
  `fc1ddbce861293fac9dcbd9e87571d8b4f955ae602f4f2daa6afa7908d5251af`.
  All exactly match architecture projections. The validator exact-loads the
  neutral report owner under private identity, validates its path/readiness,
  preserves foreign cache and `sys.path`, and adds no package or wrapper.
- **Focused final-path evidence:** producer/job/direct-test shell syntax and
  the complete producer shell suite passed. The moved validator passed `15`
  tests, the Step `06` scheduler selection passed `16` with `134` deselected,
  and the explicit public-CLI/Make, roster/report, artifact, and path-map
  surface passed `432` tests. All are local fixture/fake-tool evidence.
- **Coverage decision and result:** one pre-aggregate measurement with only the
  intentionally stale documentation assertion deselected passed `1,177` tests
  with `17` skips in `290.88s`. Step `06` moved to its final path at `108/119`
  covered lines and `24/30` branches; global coverage is `9551/11720` lines and
  `3348/4772` branches. Every non-target row stayed exact, target/global rates
  increased, and the standalone policy comparison passed. The baseline edit
  is only the moved target row, canonical sorting, and mechanically reconciled
  totals.
- **Aggregate result, not green:** the first exact sandboxed command passed
  static preflight and stopped only when guarded R could not resolve
  Bioconductor metadata; it retained the inherited ignored malformed `macos`
  warning, ended status `2` in `5.343s`, and changed no dependency. The exact
  network-enabled rerun used the existing project library, wrote
  `/private/tmp/norad-validation-mig-03k.json`, and ended status `2` in
  `183.791s`. Static preflight passed in `0.166s`, shell contracts in `42.813s`,
  report runtime in `129.807s`, and guarded R in `177.640s`. Python ran `1,177`
  passes and `17` skips before its sole documentation assertion listed exactly
  ten intentionally stale Step `06` links—five in the functional-owner
  inventory and five in the colocated contract—plus the nine inherited
  `UNREFINED` card-location findings. No other lane, test, coverage, tool, or
  dependency fault occurred.
- **Documentation and lifecycle decisions:** add one adjacent owner README;
  correct the contract from unimplemented/flat, stale-test, Step-`00a`
  publisher, and deferred-migration wording; update current architecture,
  inventory, coverage, ownership, roadmap, handoff, runbook, troubleshooting,
  neutral-library, Step `05` predecessor, Step `07` consumer, artifact-
  provenance, and pending-test routes; repair every final path/command and
  inbound lifecycle link; delete only the obsolete documentation scaffold;
  and move only `MIG-03K` from `IN_PROGRESS` to `COMPLETED`. No diagram changes
  because semantic identities, direct DAG edges, and public data flow did not
  change. No Step `07` or later owner/review card is selected or created.
- **Recovery and evidence ceiling:** before cleanup/retry, preserve all five
  finals, two-directory temp/backups, every relevant lock/owner, input pair,
  unrelated bytes, streams, scheduler job/accounting/log, checkout/submit CWD,
  overrides, threads, and samtools path/version. Rule out every producer and
  Step `07` reader; never combine attempts, infer identity from counts or
  timestamps, remove a foreign lock, reconstruct a missing file, or adopt
  stale wrapper success. Only isolated output and QC directories are eligible
  for a separately authorized diagnostic retry. Historical six-sample
  samtools/cluster observations are not migration proof. MIG-03K creates no
  real tool, scheduler, cluster, production, scientific-review, or biological
  evidence.
- **Documentation gate, rollback, and pause:** `git diff --check` passes. The
  exact RUNBOOK documentation validator has no MIG-03K path, anchor, lifecycle,
  dependency, cycle, orphan, or diagram finding and retains only the nine
  inherited `UNREFINED` locations. That expected-only result remains
  nonpassing, not green. Roll back this documentation close and pending-
  scaffold deletion, executable `1d5b76a`, scheduler `e871d5c`, validator
  `1332529`, stability/collision `66e41fe`, transaction `dafcd18`, then child/
  count `3ae6e3e`; Git rollback never changes runtime or recovery evidence.
  Publish and prove this close clean/upstream/live-remote-equal, then pause at
  MIG-03K completion without selecting another owner.

## 2026-08-03T09:44:00-0400 — MIG-03L and sequential reviews defined

- **Verified parent and live-DAG choice:** published MIG-03K documentation
  close `b73b12bfb7d5af02f9e2c5bb7749a91cfb030f6d` was clean, tracked/
  untracked-empty, free of recovery/index locks, and equal across local
  `HEAD`, configured upstream, and the live remote branch before definition
  work. The canonical direct-edge map leaves exactly one eligible unmigrated
  owner: `generate_partitioned_cohort_mpileup_VCFs`. Every declared-sample
  Step `06` BAM/BAI pair and the reference FAI predecessors are migrated.
  Step `08` remains blocked and no Step `08` or later card is created.
- **Frozen native boundary:** define only semantic stage
  `norad.stage.generate_partitioned_cohort_mpileup_VCFs.v1`, historical alias
  `07`, final source home
  `src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/`, and mirrored
  test home `tests/stages/generate_partitioned_cohort_mpileup_VCFs/`.
  Candidate moves are the mode-`0755` producer, mode-`0644` validator, mode-
  `0644` job, mode-`0755` direct shell test, and mode-`0644` direct validator
  test. Three native assets total `49,371` bytes and `1,360` lines with
  frozen hashes
  `e790946db19ad26f8f8e75a325ced9035fcc69d58819ca3b43a1032131fac858`,
  `4171442377c9c115d54baf9dc303cf22e37f2094b89daec9a982ad3c2704a85a`,
  and `a2c64ceaebbf367f1c3f4c01cce663d16e958252a5a9dbd49ad26990b42d7659`.
- **Proposed cutover and review question:** the evidence-backed hypothesis is
  five moves plus nine integration owners: Make, artifact producer mapping
  and exact migrated-producer evidence, public CLI maps, SLURM map/delegation,
  validation roster, neutral report-loader matrix, coverage baseline, and the
  literal Make expansion. Architecture review must prove that ceiling, exact
  final hashes/root depths/test-helper bridge, mode continuity, and absence of
  any hidden config, scaffold, wrapper, or duplicate owner.
- **Pipeline and evidence decisions:** preserve exact manifest order, FAI-
  bounded `region` and `regions_file` selectors, relative selector-file
  resolution, reference and orientation-BAM paths, depth and filter defaults,
  mechanical `FWD_like`/`REV_like` labels, and the two `mpileup`-to-`filter`
  pipelines. This is pileup/filtering, not `bcftools call`, variant calling,
  RNA-editing-site identification, transcript-strand assignment, or
  biological/scientific readiness.
- **Transaction and provenance risks:** preserve but do not approve receipt
  visibility before final validation/commit, manifest-only hash and stability
  binding, unhashed BAM/BAI/reference/FAI/regions/tool/policy/VCF inputs and
  outputs, best-effort restoration, absent durable recovery/attempt identity,
  and relative-output-root versus resolved-validator-path disagreement. The
  cohort/partition lock, run-token scratch/backups, all-three-or-none
  predecessor admission, receipt-last rename, final validation, cleanup, and
  signal behavior remain review inputs rather than successful-recovery or
  immutable-computation proof.
- **Validation risks:** preserve exact five-row reporting and exit-`0` failed
  evidence. The validator checks receipt/VCF shape, numeric positions,
  selector declarations against the FAI, manifest hashes/sample order, VCF
  paths, and counts without bcftools. It does not prove selector-bound data
  coordinates, REF/ALT or FORMAT annotations, filter compliance, input/output
  hashes, tool/policy identity, calling, biological meaning, or current-
  attempt identity. Producer/validator `regions_file` detail remains
  asymmetric. Reliability review must assign safe old/final-path oracles
  rather than fix or bless these states.
- **Scheduler risks:** preserve submit-CWD fallback, exported `/tmp`, tolerated
  bcftools module diagnostics, fixed default tool plus override, version
  command, one requested CPU, explicit execute gate, body-level `logs/`
  mutation, three-file wrapper post-check, and possible stale-complete-set
  false success. These are review inputs, not scheduler, current-attempt,
  production, scientific, or biological proof.
- **Coverage and evidence ceiling:** frozen validator coverage is `167/198`
  lines and `48/72` branches; global coverage is `9551/11720` lines and
  `3348/4772` branches. Any later final measurement must keep non-target rows
  exact and preserve target/global rates and covered-count floors. Definition
  adds no real bcftools, scheduler, cluster, production, scientific-review,
  variant/editing-site, or biological evidence.
- **Bounded lifecycle decision:** create only unselected `MIG-03L` and
  unselected sequential `REVIEW-ARCH-03L` → `REVIEW-REL-03L` →
  `REVIEW-UX-03L`. No card is selected; no executable, test, harness,
  configuration, dependency, schema, fixture, report-template, runtime,
  scheduler, cluster, production, or future-owner file changes or runs.
- **Card-boundary documentation gate:** `git diff --check` passes and the
  exact RUNBOOK documentation validator reports only the nine inherited
  `UNREFINED` card-location findings. No MIG-03L path, lifecycle, dependency,
  cycle, orphan, anchor, or diagram finding remains. This expected-only result
  is nonpassing, not green and not authority to alter inherited lifecycle
  state.

## 2026-08-03T09:52:46-0400 — REVIEW-ARCH-03L selected

- **Selection:** from clean, published, local/upstream/live-remote-equal
  definition checkpoint `8dc61287819d7ea10ca4bcc38934a0819161d24a`, move only
  `REVIEW-ARCH-03L` to `IN_PROGRESS` and repair its direct reliability-review
  lifecycle link. `MIG-03L`, `REVIEW-REL-03L`, and `REVIEW-UX-03L` remain
  unselected in `TODO`; Step `08` and every later owner/review card remain
  uncreated.
- **Boundary:** this checkpoint selects read-only architecture review but
  records no finding. No executable, test, harness, configuration, dependency,
  schema, fixture, report-template, runtime, scheduler, cluster, production,
  scientific-review, variant/editing-site, or biological state changes or
  runs.
- **Minimal slice check:** `git diff --check` passes. Per the card-boundary-only
  validation rule, no computational suite or complete documentation validator
  runs at selection; the complete documentation gate belongs to architecture-
  review completion.
