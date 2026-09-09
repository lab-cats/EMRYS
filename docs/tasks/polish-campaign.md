# EMRYS polish campaign

This document records repository-polish and professional-tooling findings
from the September 7, 2026 audit, their implemented outcomes, and remaining
proposals. It covers correctness, operator experience,
architecture reduction, developer feedback, dependency maintenance, and release
presentation.

The companion [optimization campaign](optimization_campaign.md) covers pipeline
and operator-command wall time, disk usage, I/O, and memory with its own
measurement boundaries.

The user requested this document and its integration with the optimization
campaign and revised quickstart. Selected implementation is identified below;
other proposals still require separate selection and authority. The
[backlog matrix](backlog_matrix.md) owns accepted outcomes and delegates
finite CS cards to the [temporary compression backlog](compression_backlog_matrix.md).
Those are their respective status, score, and acceptance authorities. Existing row
references below identify coverage, not duplicate tasks. Numbered headings are
navigation references, not new backlog IDs. Proposed acceptance below becomes
authoritative only when selected through the existing workflow.

## Evidence and selection

The source audit used GitHub master
[`fdf76760311e6c8076320a289ef3956d754c190d`](https://github.com/lab-cats/EMRYS/commit/fdf76760311e6c8076320a289ef3956d754c190d).
Overlap was checked against the open implementation stack, including
[`8b8642e50fdb7a3b9c94b64200def0c84c9e8b57`](https://github.com/lab-cats/EMRYS/commit/8b8642e50fdb7a3b9c94b64200def0c84c9e8b57),
and open PRs through #126 when this document was prepared. Source, callers,
contracts, tests, configuration, and documentation were inspected. No product
tests, benchmarks, scientific runs, or institutional-site execution were
performed for the audit. Previously recorded local reproductions are identified
as such; reading their records is not a new reproduction.

The combined documentation change also incorporates the optimization campaign
from [PR #127](https://github.com/lab-cats/EMRYS/pull/127) at `b59661a3` and the
scientist quickstart from [PR #130](https://github.com/lab-cats/EMRYS/pull/130) at
`17e6ed2b`. PR #130 records documentation checks, source/parser review, and five
focused setup/Doctor tests. Those are its original evidence, not new execution
performed during this integration. Its completed documentation narrows the
remaining work in items 9–11 below; institutional qualification remains open.

The second pass reviewed the combined documents at `dbb11a3b`, whose product
source still matches the audited master, and relevant open work through PR
#136. It added release acceptance detail and the assurance/usability findings
below. Live GitHub ruleset, effective-branch-rule, and legacy branch-protection
reads inform item 33; hosted settings are an audit-time observation and must be
rechecked before selection. No installed-command reproduction, rendered report
review, performance measurement, or new product test ran during either pass.

The third pass used the same product revision and the campaign at `63effce4`,
checking open work through PR #137. It refined items 12, 29, and 30 and added
items 40–44. These findings also come from source/documentation review, without
new product tests, input-reuse reproductions, installations, or upgrade trials.

The September 8 reconciliation uses `2fb8f5ef`, whose tree is identical to
the tested `8034c211` state. [PR #139](https://github.com/lab-cats/EMRYS/pull/139)
merged the earlier compression and documentation stack into master at
`446802c0`, including this campaign from PR #131. The subsequent changes from
PRs #141–147 are integrated into [PR #140](https://github.com/lab-cats/EMRYS/pull/140).
Its exact `2fb8f5ef` head passed [full ordinary CI](https://github.com/lab-cats/EMRYS/actions/runs/34301289787);
master integration remains blocked and pending at this reconciliation. Original
PRs closed through either integration are not unimplemented proposals. The
[overlap reconciliation](#existing-capabilities-and-overlapping-work) identifies
what each integration contains. This documentation pass ran no product tests
or new performance measurements; ordinary CI does not establish long-lane,
institutional, production, scientific-review, or biological acceptance.

Pinned source references below retain the original audit evidence; relative
links point to the current owner.
Before selecting a candidate, reconcile its current source, backlog coverage,
and overlapping PRs. The [temporary compression backlog](compression_backlog_matrix.md) contains
related observations; preserve its useful decisions without copying its entire
history or reviving discarded task IDs.

For each selected slice:

- State one observable outcome and audit the complete affected owner and its
  callers. Classify behavior as preserved, defective, undecided, or
  environment-deferred before structural changes.
- Prefer the existing owner, standard library, established package manager, or
  maintained tool. Introduce no parallel registry, validation framework,
  environment authority, or generic transaction layer without a demonstrated
  need and a separately approved design.
- Quantify product code, tests/protections, developer tooling, documentation,
  configuration/dependencies, and retained evidence separately. Product changes
  default to meaningful net reduction and no product-file growth. Tooling-only
  work with unchanged product code and small correctness/UX additions need
  their own bounded footprint exception when implementation is selected; this
  documentation request is not blanket approval for those exceptions.
- Preserve immutable Runs, scientific meaning, public records, provenance,
  recovery, and useful independent tests. Retained-evidence deletion requires
  its own exact proposal, approval, and commit.
- Use focused local feedback and the applicable existing CI checks on the exact
  final state. Keep fixture, hosted, Slurm, institutional, scientific-review,
  and biological claims distinct.

The shell syntax correction, selected Ruff correctness rules, shared sharder
self-tests, and automatic stacked-PR CI in items 15, 17, 21, and 22 are
implemented and validated in the pending PR #140 integration. The user has
approved ShellCheck, Ruff formatting, and optional fast hooks under `DEV-01`
(items 16, 18, and 20), public version reporting under `CLI-VERSION-01`
(item 43), and the bounded Python/R test-runtime work under `CI-01` (item 23).
Those slices passed ordinary hosted CI in [run 34306975901](https://github.com/lab-cats/EMRYS/actions/runs/34306975901)
at `b491aac5`, including the complete Python suite/coverage, guarded R, and
managed golden path. PR #148 awaits master integration. The artifact-version
correction, other publication-recovery owners, Project preview, type checker,
and other unselected proposals retain their separate decision boundaries.

The second pass prioritizes the installed-package journey and runtime identity
audits, followed by rendered report review. The merge-rule gap is concrete;
performance additions require complete-command measurements before selecting
an implementation. Existing backlog coverage stays with its current rows.

The third pass prioritizes the FASTQ admission-parity audit, checks for
documented commands, and scientific-output discoverability. Provider and
upgrade evidence refine the existing extension and release outcomes rather
than create parallel initiatives.

## Correctness and recovery

### 1. Preserve ownership during validation-report recovery

**Finding:** [Validation publication](../../src/emrys/libraries/validation/publication.py)
can unlink another process's late output and release its lock after restoration
fails. Existing [characterization tests](../../tests/libraries/test_validation_report.py)
describe these cases.

**Outcome and acceptance:** Cleanup removes only proven-owned outputs; failed
restoration preserves the state needed for unambiguous recovery. Exercise late
foreign publication, replacement, restoration failure, and successful retry
through this publisher. Scope this owner independently of the following three.
This remains proposed recovery work, separate from the merged `RECOVERY-01`
change to Steps 07–09 and storage qualification. Product reduction is unproven.

### 2. Make storage-inventory replacement recoverable

**Finding:** [Storage-inventory publication](../../src/emrys/evidence/storage_inventory/_storage_publication.py)
moves predecessors before entering its rollback handler and can release the
lock after incomplete restoration.

**Outcome and acceptance:** Preserve a recoverable three-file predecessor or
complete replacement across failures during backup, publication, restoration,
and cleanup. Review the [existing tests](../../tests/evidence/storage_inventory/test_storage_inventory.py)
and contract together. Storage inventory and storage qualification are distinct
transactions; PR #115 does not close this proposed owner-specific correction.
The merged measurement-row consolidation in PR #128 and its filesystem-call
test correction in PR #134 also leave this publication defect unresolved.

### 3. Make reference-provenance replacement recoverable

**Finding:** [Reference reconciliation](../../src/emrys/evidence/reference_provenance/reconciler.py)
has a similar backup-before-handler structure and incomplete-restoration gap.

**Outcome and acceptance:** Define and test recoverable state at every
replacement boundary, preserving predecessor bytes and unresolved ownership.
Use the [reference owner's tests](../../tests/evidence/reference_provenance/test_reference_provenance.py).
Similar code spelling does not establish equivalent transaction semantics or
justify combining this proposed slice with storage publication.

### 4. Correct runtime-report publication failures

**Finding:** [Runtime inspection](../../src/emrys/evidence/runtime_availability/inspector.py)
can leak a lock descriptor when writing/syncing the lock fails, release the lock
after failed restoration, and hide a lock-removal failure. Existing
[tests](../../tests/evidence/runtime_availability/test_runtime_availability.py)
characterize these behaviors.

**Outcome and acceptance:** Give descriptors explicit lifetime ownership,
preserve unresolved recovery state, and report relevant finalization failures.
Select descriptor acquisition and publication recovery as separate bounded
slices if necessary; preserve intentional error precedence. Runtime-model
consolidation in PR #116, merged through PR #139, does not repair these cases.
No compression claim is established for the small descriptor fix.

### 5. Admit current artifacts through the public validator

**Finding:** The [artifact CLI](../../src/emrys/contracts/artifacts/validator.py)
uses [unversioned schema selection](../../src/emrys/contracts/artifacts/_artifact_contracts/schema.py),
whose defaults are summary v2 and receipt v4. Current module reporting produces
summary v3 and receipt v5. The stack's intake records a prior local reproduction
of the rejection; the audit independently traced the source selection.

**Outcome and acceptance:** Public and internal artifact admission use one
coherent version-selection authority. Current outputs pass, malformed versions
fail, and explicitly supported historical records retain their intended
admission and semantic checks. Cover real reporting outputs and deterministic
diagnostics. This is a separate unselected artifact correction; completed
`CONTRACT-API-01` and PR #117 address orchestration Attempt receipts. The later
reporting changes in PRs #145 and #147 do not change this public validator's
version dispatch. Quantify any net reduction before describing this correctness
fix as compression.

### 6. Make timestamp admission deterministic

**Finding:** Orchestration schemas declare `format: date-time`, but the
[validator](../../src/emrys/contracts/orchestration/api.py) uses a format checker
whose optional timestamp dependency is absent from the declared lock closure.
The stack's follow-up intake records a previous local observation that
`finished_at: "not-a-time"` passes in that environment.

**Outcome and acceptance:** Choose the intended timestamp policy and provide
its checker reproducibly through the established dependency. Test valid
historical/current timestamps and malformed values through the real admission
path. Review other format-dependent callers and compatibility before tightening
acceptance. Prefer maintained dependency support over bespoke parsing. This is
a proposed dependency/correctness correction, not an established reduction.

## Operator experience

### 7. Show the effective Project before creation

**Finding:** [Initialization](../../src/emrys/orchestration/run_coordinator/onboarding.py)
collects fifteen fields and generates admitted Project bytes, but its preview
shows only the output root, owned directories, and no-copy policy.
The revised quickstart explains the scientific suggestions and repeated setup
answers; the command's generated preview is unchanged.

**Outcome and acceptance:** Display a faithful, readable preview of the already
generated definition, including reference paths, analysis/cohort choices,
target change, and thresholds. Explain suggestions without presenting them as
universally valid scientific settings. Prove preview/publication agreement and
no writes during preview. Reuse current rendering and admission; add no draft
registry or parallel schema. This new UX proposal may need a small product-size
exception.

### 8. Let Doctor inspect the selected execution profile

**Finding:** Run accepts a named or absolute execution profile, while standalone
[Doctor](../../src/emrys/orchestration/run_coordinator/doctor.py) selects the
default and exposes no profile selector.

**Outcome and acceptance:** Resolve the intended profile through the existing
authority and show what was checked. Default, named, and absolute selection
must agree with Run; errors and no-write diagnosis remain clear. Audit repair
and transport callers before settling the public interface. This new selection
proposal is adjacent to, but distinct from, the storage-repair issue below.

### 9. Make Doctor's proposed storage repair match placement

**Finding:** Doctor diagnoses storage against direct or Slurm placement, but
constructs a direct qualification plan when storage is unready. Source predicts
that this cannot satisfy the Slurm qualification requirement; this audit did
not reproduce a site failure.
The runbook now documents the supported route: retain a direct default during
initial preparation, perform compute/finalize storage qualification, and select
the separate Slurm profile. PR #136 consolidated readiness-result construction;
it did not change the storage repair plan or resolve this finding.

**Outcome and acceptance:** Reassess the remaining command-level problem against
that documented route and verify it through the existing plan and admission
paths before selecting a repair change. Any selected correction must make
repair intent and qualification requirements agree without duplicating setup
machinery. Preserve profile ownership and the preview/execute boundary. Local
plan proof and institutional execution are separate. This is the existing
compression-intake discussion 6, still a proposed bounded defect investigation.

### 10. Complete a novice institutional walkthrough

**Finding:** [Quickstart](../../quickstart.md), [Runbook](../operations/RUNBOOK.md),
and [profile examples](../../configs/execution_profile.example.yaml) now cover
installation, real-data setup, institution-provided runtimes, compute-node
preparation, both storage-qualification phases, Slurm profiles, submission,
recovery, and opening reports. This procedure has not yet been demonstrated by
a novice operator at a named institution.

**Outcome and acceptance:** Under existing **`SITE-PARITY-01`**, an operator
without repository-development context follows the maintained instructions
through site modules, Project creation, profile selection, storage/runtime
admission, Slurm execution, inspection/recovery when needed, and Results.
Record concrete friction and qualify the required site semantics at one exact
revision. Use the maintained procedures and correct friction observed during
the walkthrough; hosted success alone does not close the site outcome. Site
execution needs its own authorization.

### 11. Align the initial operator environment with Doctor

**Finding:** Quickstart now selects `--no-default-groups --group workflow`,
matching Doctor. The hosted golden-path clone still installs default groups.
The remaining work is to align that CI bootstrap and verify the documented
operator environment through the existing golden path.

**Outcome and acceptance:** Start operators with the same admitted runtime
groups Doctor selects, retaining development dependencies for repository
checks. A clean environment reaches help, Project creation, Doctor, execution,
reporting, and inspection. Preserve the updated quickstart and align the
existing golden-path CI setup; measure installation savings before quantifying
them. This configuration/verification slice supports `SITE-PARITY-01` without
independently closing site acceptance.

### 12. Draft manifests from explicit mate paths

**Finding:** Canonical manifests accept explicit paths, but the
[drafting helper](../../src/emrys/orchestration/run_coordinator/onboarding.py)
requires a closed filename convention and cannot accept a name such as
`sample_R1_001.fastq.gz` through that route.

**Outcome and acceptance:** Decide whether explicit sample/R1/R2 assignments
should replace filename inference. Use the existing manifest validator and
authored biological metadata; preserve missing-mate, duplicate-file, symlink,
compression, and publication defenses. Prefer retiring inference over adding
more naming patterns or parallel input modes. This is a new capability
proposal adjacent to `OPS-03`; hand-authored manifests already remain usable.
The revised quickstart explicitly documents that route for arbitrary filenames;
the drafting helper's input restriction remains unchanged.

**Admission parity audit:** The [drafting guard][fastq-draft-identity] rejects
one physical FASTQ reused across sample/mate roles using device and inode;
its [hard-link test][fastq-draft-test] protects this behavior. By contrast,
[hand-authored Project normalization][fastq-project-identity] checks only that
each row's R1 and R2 paths differ. Sample/replicate admission checks labels and
strata, not equivalent physical-file uniqueness. Source predicts that repeated
paths across sample rows or hard-linked mate paths can bypass the drafting
guard; this admission-policy discrepancy was not reproduced through a Run.

Decide the intended physical-file reuse policy, then apply it consistently
through the existing Project admission owner. Diagnostics should identify both
conflicting roles. Cover repeated paths across rows, hard-linked mates,
distinct files, and legitimate reuse of the same Dataset by multiple Analyses.
Reuse existing descriptor-bound metadata; do not equate identical content
hashes with biological identity or create another input registry. Scope this
parity correction separately from the filename-interface decision above and
quantify any product growth before implementation selection.

## Architecture reduction

### 13. Retire the ineffective reporting-memory control

**Completed under [CS-04](compression_backlog_matrix.md#cs-04-reporting-memory-control);
ordinary CI passed in PR #150 at `f3a3966f`, awaiting integration.** Report execution never consumed this setting.
The [Run-coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#profiles-and-immutable-planning)
owns its removal from new inputs and the retained historical-reading boundary.
All active carriers/defaults/overlays and the obsolete resume wrapper retire
together; no ignored public option or resource manager replaces them.

149 focused checks pass. Existing immutable Run/source identity, raw historical
records, report regeneration, and transaction behavior remain separate
obligations; removal is not assumed to be source-identity neutral. The broader
`REPORT-ROSTER-01` outcome remains open.

### 14. Retire the frozen dashboard when its existing row is selected

**Finding:** The [coordinator guide](../../src/emrys/orchestration/run_coordinator/README.md)
describes the dashboard as a stale, unsupported preview frozen under
**`DASHBOARD-RETIRE-01`**.

**Disposition and acceptance:** The user requires a usable replacement before
retirement. Keep the dashboard and its protections until that prerequisite is
implemented and accepted; retirement is excluded from the current tranche.
The eventual caller-complete change must preserve Project-local inspection,
required scheduler accounting, sanitized streams, and exact historical reads,
or obtain an explicit narrower capability decision. Product code, parsers,
dedicated tests, targets, and stale guidance retire together only under that
approved scope. The existing row retains the decision and evidence-deletion
boundaries; potential size reduction does not override the replacement condition.

## Development and CI tooling

### 15. Check every script in the Bash syntax gate

**Disposition:** Implemented and validated in [PR #141](https://github.com/lab-cats/EMRYS/pull/141),
included in PR #140 pending master integration. [Make's shared syntax gate](../../scripts/make_quality.mk)
parses each declared script separately and stops on failure. Both `smoke` and
`validation-static` use that gate; a malformed second or third script is a
regression case. The thirteen-path roster is preserved. ShellCheck, formatting,
and any roster expansion are distinct from this completed correction.

### 16. Integrate ShellCheck

**Disposition:** Implemented under `DEV-01`; ordinary hosted CI passed at `b491aac5` (run 34306975901); master integration remains pending.
The existing lint gate checks every tracked `.sh` file with locked ShellCheck,
and actionlint checks embedded workflow shell with the same version. Shared
source resolution uses `.shellcheckrc`. Seven array-reference mistakes are
corrected; annotations explain specific dynamic inputs and intentional shell
semantics instead of disabling a rule repository-wide. Local ShellCheck,
actionlint, and shell-owner contracts pass. Bash syntax checks remain active.

### 17. Broaden Ruff correctness checks

**Disposition:** Implemented and validated in [PR #142](https://github.com/lab-cats/EMRYS/pull/142),
included in PR #140 pending master integration. The [Ruff configuration](../../pyproject.toml) selects
`E9`, `F63`, `F7`, and `F82` through the existing lint command. This subset passes
unchanged product source using the locked Ruff version. Broader lint groups
still need owner-specific review: unused-import diagnostics include live
re-exports, and some suggested fixes change exception or iteration semantics.
Formatting is the separate approved item 18, not part of this completed change.

### 18. Adopt consistent Python formatting

**Disposition:** Implemented under `DEV-01`; ordinary hosted CI passed at `b491aac5` (run 34306975901); master integration remains pending.
The existing Ruff configuration and locked version own formatting for `scripts`,
`src/emrys`, and `tests`. `make lint` and the staged-file hook use `ruff format
--check`. The separate mechanical baseline reformatted 78 files; every changed
file retained identical parsed Python code. Its 2,101 additional physical lines
are formatting expansion, reported separately from functional changes and never
counted as compression. The formatter check passes across all 292 tracked Python files; explicit
Python-only inclusion keeps its scope aligned with the staged-file hook.

### 19. Adopt one Python type checker

**Finding:** No repository-integrated type checker is configured despite the
annotated models, records, and provider interfaces.

**Outcome and acceptance:** Compare [mypy](https://mypy.readthedocs.io/en/stable/existing_code.html)
and [Pyright](https://github.com/microsoft/pyright) on one coherent typed owner,
choose one, and establish matching local/CI checks. Resolve useful errors
without blanket suppressions, public-model changes solely for the checker,
or a repository-wide strict-mode migration. Static typing complements runtime
admission and scientific validation; it does not replace them.

### 20. Add optional fast local hooks

**Disposition:** Implemented under `DEV-01`; ordinary hosted CI passed at `b491aac5` (run 34306975901); master integration remains pending.
The repository's three pre-commit hooks check staged Python correctness,
Python formatting, and shell code with the locked `.venv` tools. They perform
no implicit installation, rewriting, scientific execution, R checks, or test
suites. Explicit installation and use live in the
[engineering conventions](../operations/ENGINEERING_CONVENTIONS.md#development-validation).
Local hook checks pass, including rejection of an invalid staged shell file
while ignoring an unrelated untracked invalid Python file. CI remains the
complete validation path.

### 21. Share local and CI validation inventory

**Disposition:** Implemented and validated in [PR #143](https://github.com/lab-cats/EMRYS/pull/143),
included in PR #140 pending master integration. The correction moves the CI-only self-test invocation
into [shared static preflight](../design/TEST_BASELINE.md#validation-lanes), so
local `all-checks` and CI run it once through the same Make target. The
[sharder](../../tests/tools/python_test_shards.py) still excludes its own tests
to prevent recursive collection; the other exclusion, package distribution,
remains covered by the installed-wheel lane. Failure propagation and exact
Make/CI wiring are protected without adding a test registry or validation lane.

### 22. Run ordinary CI automatically on supported stacked PRs

**Disposition:** Implemented and validated in PR #140, pending master integration.
The `CI-01` correction removes the `master`-only PR
base filter. The [validation policy](../design/TEST_BASELINE.md#validation-lanes)
now covers all PR bases while retaining master-only push runs and the existing
merge-group, scheduled, and manual behavior. Actual stacked pull-request events
started ordinary hosted CI, and the final integrated head passed the full
ordinary run linked above. This closes the automatic-dispatch implementation
outcome, not the remaining `CI-01` performance work or the master merge gate.
Item 33 separately addresses required merge checks.

### 23. Reduce the measured CI critical path

**Disposition:** Implemented under **`CI-01`**; ordinary hosted CI passed at `b491aac5` (run 34306975901); master integration remains pending. PR #124's duration
estimate refresh is already merged through PR #139; it does not close the
remaining wall-time outcome. Hosted timing review now separates queue time,
setup, R restoration, runtime readiness, and test execution rather than treating
all elapsed time as test cost.

The test change combines output and resume assertions around one initial
35-task Python workflow execution and removes a duplicate R package-probe
wrapper. Statement comparison confirms that only the duplicate execution was
removed from the Python test bodies. All sixteen existing R negative
cases and their guards remain; at most two run concurrently. This changes test
scheduling and repeated setup, not scientific computation, the negative-case
roster, or production runtime admission. Independent assertions, private mutable
fixture state, failure propagation, and diagnostic attribution must survive.

**Outcome and acceptance:** Remove the demonstrated repeated execution and
validate the final state through existing local checks and hosted CI, preserving
complete/disjoint test selection, coverage, receipts, subprocess evidence, and
failure behavior. This tranche does not require another benchmark campaign. Cache changes, removal of
readiness observations, and production R-probe concurrency are not implied by
this approved test slice. Report any observed CI timing without claiming that
removed test work equals the same reduction in total CI elapsed time.

### 24. Configure one dependency-update bot

**Finding:** No Dependabot or Renovate configuration is present.

**Outcome and acceptance:** Choose one bot and configure bounded, grouped
proposals for Python and GitHub Actions. Preserve lock consistency and apply
the existing checks before accepting updates. [Dependabot supports uv and
Actions](https://docs.github.com/en/enterprise-cloud%40latest/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories).
Assess actual R/Pixi/native support separately and retain scientific-runtime
qualification. Bot installation, scheduling, and repository writes need the
selected slice's authority; automatic merging is not part of this proposal.

### 25. Assess known dependency vulnerabilities

**Finding:** No repository-visible dependency-audit command is integrated;
hosted dependency-alert coverage was not established by this audit.

**Outcome and acceptance:** First compare hosted coverage, then use a maintained
tool such as [pip-audit](https://github.com/pypa/pip-audit) where it adds value.
Check the selected locked Python dependency set and report package, version,
and advisory with an explicit failure/disposition policy. Do not imply full
R/Pixi/native coverage or perform automatic dependency repair. Dependency
updates and vulnerability detection remain different outcomes.

### 26. Introduce bounded R static analysis

**Finding:** No shared R lint configuration or invocation exists.

**Outcome and acceptance:** Apply a reviewed [lintr](https://lintr.r-lib.org/reference/lint.html)
rule set to selected maintained R owners. Keep the tool in the development/check
environment and preserve scientific namespace admission, invocation, and
behavior. Address real findings with focused owner tests. Adding an R formatter
such as styler is not implied by linting and was not selected in this campaign.

### 27. Format retained shell consistently

**Finding:** `SHFMT_BIN` is declared but never invoked.

**Outcome and acceptance:** Evaluate [shfmt](https://github.com/mvdan/sh) for
retained hand-maintained scripts, define one format and check, and preserve
behavior and generated output. Reconcile `OPS-03` before formatting owners
scheduled for retirement; keep the formatting diff separate. Bash parsing,
ShellCheck, and shfmt have distinct purposes.

### 28. Add local secret detection only for a demonstrated gap

**Finding:** No tracked local secret-scanning hook exists. This does not show
that GitHub secret scanning or push protection is disabled.

**Outcome and acceptance:** Compare hosted protection and local needs. Add a
tool such as [Gitleaks](https://github.com/gitleaks/gitleaks) through the existing
hook mechanism only if it adds useful coverage; otherwise record a reasoned
non-selection. Verify detection with synthetic examples without printing or
committing real credentials. This is conditional tooling work, not an incident
finding or authorization to scan unrelated private data.

## Documentation and release presentation

### 29. Document a minimal external Analysis and reporter

**Finding:** [Analysis extension interfaces](../../src/emrys/analyses/README.md)
exist, but a practical end-to-end provider/reporter walkthrough is missing.
The [sampled collaborator composition test][provider-composition-test]
constructs an installed-provider identity and substitutes its loaders. That
usefully tests composition, but does not demonstrate a separately packaged
collaborator loading through the real entry points. Existing loader and
package-identity checks remain complementary evidence.

**Outcome and acceptance:** Demonstrate one minimal working external provider
and bespoke reporter using the existing entry points. Explain installation,
configuration, input/output ownership, resource/dependency declarations,
independent validation, execution, and reporting. Exercise the documented
example through public production interfaces without a generic workflow DSL
or test-only production behavior. Consolidate existing extension guidance;
this is the compression intake's existing documentation candidate, still
requiring bounded selection and footprint accounting.

Make the example separately installable and exercise actual discovery,
configuration admission, planning, production, independent validation, and
reporting without replacing the loader. Retain a small set of literal expected
outcomes that collaborators can verify against the supported EMRYS version.
Include rejection of incompatible or changed provider identity. Use the public
[versioned interface][provider-interface] and its bounded `09`/optional `10`
capability; add no conformance service, registry, or second plugin framework.
This sharpens the existing example's acceptance, not a second extension task.

### 30. Establish a reviewed alpha release path

**Finding:** Quickstart asks users to select a release or commit; the GitHub
releases endpoint returned no published releases during the audit. Package
version is `0.1.0.dev0`. No claim was made that Git tags are absent.

The [isolated wheel test][release-wheel] covers
installation, packaged resources, public help, and manifest validation. Its
report exercise calls private publication code and supplies the original
checkout as `REPO_ROOT`. [Onboarding][release-root]
derives a checkout-relative root, and
[source admission][release-source] requires a
matching Git checkout. This is installed-component evidence, not proof that an
independently installed wheel supports the whole public Project-to-Results
journey. No standalone-install failure was reproduced in this audit.

The [wheel installer][release-constraints] also constrains dependencies to
the versions in `uv.lock`.
[Package metadata][release-dependencies] expresses broader ranges for
`jsonschema` and `referencing`; the test does not establish compatibility across
those ranges or their lower bounds. No dependency incompatibility is established.

Historical-schema tests can use [current fixture builders][historical-reader-test],
while [provider readmission][provider-readmission] intentionally rejects changed
metadata or implementation. Schema-read support alone therefore does not
promise that a newer installation can inspect, report on, or resume an older
Run. This distinction does not invalidate the existing per-schema tests.

**Outcome and acceptance:** Define the supported distributed artifact and an
exact reviewed revision, then produce coherent versioning, release notes,
installation instructions, and evidence boundaries. Strengthen the existing
release outcome with three decisions and their corresponding evidence:

- Decide whether the wheel supports standalone operation, selected utilities,
  or operation paired with an exact checkout. From an isolated installation
  and arbitrary working directory, exercise every promised operation through
  the public installed command using only documented resources. Cover Project
  initialization and report regeneration if promised; a tiny complete Run is
  necessary only if full wheel operation is selected. Unsupported use should
  fail early with useful instructions. Preserve source attribution rather than
  silently broadening supported installation paths.
- Decide whether support requires the released lock or includes installations
  resolved from wheel metadata alone. Demonstrate the locked route from the
  actual release artifact, or use a bounded independently resolved/minimum-
  dependency check to inform accurate metadata. Keep one explicit support
  policy; do not multiply platform and dependency matrices without a promise
  they verify. Item 6 retains the separate timestamp-checker issue.
- For the first supported upgrade transition, state compatibility separately
  for Project admission, inspection, report regeneration, and resume. Identify
  which operations require the original environment. Retain a tiny artifact
  actually produced by the named predecessor revision and exercise promised
  operations through the new public command. Verify that unsupported resume
  or provider changes fail closed without modifying the Run. Reconcile
  `QUAL-05` and historical-reader contracts; do not imply universal backward
  compatibility, automatic migration, or weaker source identity.

Reuse existing package checks and environment owners. These are release
acceptance details, separate from update bots and vulnerability scanning;
they do not close `SITE-PARITY-01`. Release automation is justified only for
the selected repeatable process. Publication, package-index registration, and
any new product/platform support require their own explicit authority.

### 31. Provide authoritative citation guidance

**Finding:** The tracked repository has no citation file or explicit citation
instructions for research users.

**Outcome and acceptance:** Record maintainer-approved authorship and how to
cite an exact revision or supported release in one durable home. Link it from
the public entry point; use standard citation metadata if selected. Do not
invent authors, a DOI, a publication, or evidence of scientific validation.
This is a small documentation/metadata proposal with unchanged product code.

### 32. Attach dependency inventory and build provenance to releases

**Finding:** No tracked release SBOM or build-attestation integration exists.

**Outcome and acceptance:** Once the supported artifact and release process are
defined, use maintained tooling to attach a generated dependency inventory and
[verifiable build attestation](https://docs.github.com/en/actions/concepts/security/artifact-attestations)
to that exact tested artifact. Source, version, artifact identity, and stated
inventory scope must agree; verify the attestation as a consumer. A Python
inventory does not imply complete native/R coverage. This is later release
tooling, with separate publication authority and no bespoke framework.

## Additional assurance and usability

### 33. Make the required merge checks explicit

**Finding:** The two active repository rulesets and the effective rules for
`master` include PR review, CodeQL, code-quality, and coverage requirements,
but no `required_status_checks` rule naming the ordinary CI suites. The legacy
branch-protection endpoint reports no separate configuration. These findings
do not mean the branch has no protections or that its CI is failing.
[Required status checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#require-status-checks-to-pass-before-merging)
are distinct from the other hosted rules.

**Outcome and acceptance:** Select the ordinary checks that must succeed for
the intended merge and bind their actual emitted check names to the effective
policy. Reconcile overlapping rulesets and document intentional administrative
bypasses without weakening unrelated protections. Verify failure, cancellation,
missing results, intended skips, and updates to the PR head; preserve opt-in
long lanes and the supported stacked-PR policy from item 22. Any consolidation
must preserve the combined intended protections. This is a proposed hosted
configuration outcome adjacent to `CI-01`, not approval to change settings or
another CI inventory. No merge-blocking experiment was performed in the audit.

### 34. Cover the complete admitted R dependency closure

**Finding:** Existing **`RUNTIME-CLOSURE-01`** owns recursive R dependency
binding and disabling automatic snapshots across supported activation paths,
but this outcome was absent from the first campaign pass.
[Doctor's bindings][r-bindings]
hash the selected namespace trees from runtime observations; that loop does
not itself derive the recursive dependency roots.

**Outcome and acceptance:** Use the existing backlog row and its full acceptance
as the authority. Audit runtime policy, installed package metadata, Doctor,
Run/resume admission, child execution, and supported R activation paths
together. Bind only the scientific dependency closure, preserve normal `renv`
cache symlinks, and prevent automatic snapshots from mutating the environment.
Reuse the current runtime/package owner rather than another dependency registry.
The optimization campaign's R-probe measurements must preserve this guarantee;
fewer probes cannot substitute for complete dependency identification.

### 35. Settle the installed Snakemake content guarantee

**Finding:** [Doctor][snakemake-binding]
records the selected Python executable as the Snakemake probe target and file
binding. [Lifecycle admission][snakemake-admission]
requires that equality, and the
[Doctor test][snakemake-test] asserts
equal Python and Snakemake file hashes. This establishes the representation,
not that a package change escapes every other defense. The existing
[compression discovery disposition](compression_backlog_matrix.md#original-discovery-disposition)
already records this as undecided discovery 9 under `COMPRESS-01`; it is
separate from the R closure in item 34.

**Outcome and acceptance:** Trace installed Snakemake and execution-relevant
Python dependencies through setup, Doctor, Run creation, resume, and child
entry. Determine whether existing identities already cover package contents,
and decide whether content identity or pinned versions with the environment
contract is the intended guarantee. A controlled same-version package-content
change must have an explicit, tested disposition across fresh execution and
resume. Preserve unchanged installations. If stronger binding is selected,
reuse existing installed-package authority and retire redundant representations;
do not assume a new digest, receipt, schema, or cache is needed. This remains
an assurance audit and contract decision, with no demonstrated escape or
preselected implementation.

### 36. Reject explicitly insufficient Slurm memory before submission

**Finding:** [Submission control][slurm-preflight]
checks requested CPUs against workflow cores. Existing **`SCHED-01`** owns the
corresponding missing preflight for explicitly undersized memory requests.

**Outcome and acceptance:** Reference `SCHED-01` and its full acceptance rather
than creating another scheduler-policy task. Trace placement, resource
overrides, and the applicable workflow/stage minimum through the existing
submission path. Reject known insufficient capacity before `sbatch`; unknown
capacity remains unknown. Preserve the CPU authority, dry-run/confirmation
boundary, and absence of scheduler/workspace writes on rejection. Reuse the
current resource owners without a general resource solver. Local submission
proof does not establish institutional execution or memory performance.

### 37. Verify reports in browsers, copied Results, and print

**Finding:** [HTML validation][report-structure]
checks structural accessibility, while the
[report tests][report-print-tests] include stylesheet-string
and relative-link assertions. They do not establish rendered keyboard use,
zoom/reflow, links into closed evidence sections, screen-reader meaning,
printed completeness, or usability of the documented copied Results directory.
The reporting cleanup in PRs #129, #132, and #133 does not supply that review.
No rendering or accessibility defect was reproduced in this audit.

**Outcome and acceptance:** Connect existing **`REPORT-01`**, **`REPORT-02`**,
**`REPORT-03`**, and shared report acceptance to a rendered review of both the
scientific and Evidence/operations reports. Use representative existing
fixtures, including long content and closed sections, and exercise navigation,
keyboard access, narrow layouts/zoom, print output, and copied-bundle links in
the selected supported browsers. Retain review evidence bound to the tested
revision. Fix observed problems in current templates/styles, preserving
independent data and HTML checks; add no third report or parallel renderer.
This covers omitted verification, not a duplicate backlog or proof of
scientific validation.

### 38. Handle expected pre-execution cancellation consistently

**Finding:** Some [initialization prompts][init-cancellation]
and [Run/resume confirmations][execution-cancellation]
let `KeyboardInterrupt` propagate. Doctor and the Run picker handle expected
cancellation. [Existing tests][cancellation-test]
explicitly expect propagation while proving that execution has not written
state. An installed-command traceback is source-predicted, not newly reproduced.

**Outcome and acceptance:** First decide the public cancellation message and
exit behavior, then handle expected interruption at existing pre-execution
boundaries. Verify the installed command and preserve no writes, logs, or
submission, EOF refusal, and confirmation of the exact plan. Leave post-start
interruption and recovery with their current owners; add no universal
exception wrapper. This is a characterized usability-policy change rather
than a demonstrated data-safety defect. Quantify any product growth before
implementation selection.

### 39. Consider machine-readable inspection for a concrete consumer

**Finding:** [Inspect][inspect-output]
provides human-readable detail levels. A successful inspection returns zero
even when the observed Run is blocked or failed; that is command-success
semantics, not a defect. An existing immutable
[Run inspection result][inspect-result]
already supplies the facts.

**Outcome and acceptance:** Identify an actual automation consumer before
selecting a stable machine-readable projection of existing facts: Run/Attempt
identity, integrity, execution/scientific/reporting state, blockers, recovery
availability, and verified paths. Preserve human output and existing exit
semantics. Verify agreement across running, failed, blocked, complete, and
supported historical Runs through the same inspection authority. Add no
status database, persistent digest cache, or weaker verification mode. This is
an optional public output contract requiring explicit selection and footprint
approval, not a dashboard replacement or a latency optimization.

## Documented workflows and contributor experience

### 40. Keep documented commands working

**Finding:** The [documentation gate][documentation-gate] validates ownership,
links, headings, and diagram structure, not fenced command examples. Public
CLI tests exercise their own fixtures. PR #130's command/parser review was
evidence for that revision, not an ongoing check against later documentation
or command changes.

**Outcome and acceptance:** Select a finite set of maintained quickstart and
runbook examples for repeatable parser and safe-fixture checks, using the
existing Markdown parser, public CLI, documentation-check owner, and golden
path where applicable. Verify quoting, continuation, placeholders, command
forms, and associated example manifests/configuration without maintaining a
second copy of the tutorial. A broken selected command must fail the applicable
gate. Distinguish syntax/admission checks from an executed user journey; never
execute arbitrary fenced blocks, installation commands, or scheduler examples
as a documentation check. Evaluate established tools before any bespoke
extraction machinery. This proposed tooling outcome complements items 10 and
11 without claiming institutional execution or a new documentation framework.

### 41. Show scientific output locations when reports are absent

**Finding:** Normal [inspection output][inspect-output] derives its Results
locations from verified reports. Scientific artifact paths appear in the debug
task-record dump. A completed processing-only Run directs the user to debug
detail, while a completed full Run without reports offers report generation.
Users who deliberately skip HTML or complete processing for reuse should be
able to locate their admitted outputs directly.

**Outcome and acceptance:** Project a concise set of scientific output
locations from existing admitted task/module declarations in normal human
inspection. Review the [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
alongside presentation changes. Cover processing-only, reporting-skipped,
reporting-failed-but-science-complete, blocked, and collaborator-module cases;
expose only correctly admitted output locations. Preserve distinct scientific
and reporting status and report-receipt checks. Add no copying, report,
registry, cache, or artifact store. This is a human-usability proposal separate
from item 39's optional machine output; quantify any product growth.

### 42. Give Run selection meaningful Analysis context

**Finding:** The [Run picker][run-picker] lists deterministic two-word names,
adding full IDs only for collisions; an [existing test][run-picker-test]
asserts that menu. This makes several Analyses or parameter revisions hard to
distinguish before selection. [Attempt materialization][attempt-context]
already records creation time and request label.

**Outcome and acceptance:** Enrich the current selector with admitted Analysis
context and recorded creation time where available. Preserve name/full-ID/
prefix selection, collision handling, cancellation, historical reads, and
explicit automation selection. Missing or malformed context must remain
visible rather than hide a Run. Labels and times aid orientation and never
establish completion or fresh integrity. Reuse existing admission helpers;
avoid full scientific-file hashing for every menu entry, coordinating with
optimization item 11. Add no mutable metadata or Run-list registry. This is a
bounded optional presentation change requiring a quantified footprint proposal.

### 43. Report the installed package version through the public CLI

**Original finding:** The package defined its version, but the public parser
required a command and exposed no conventional version display.

**Disposition:** Implemented under `CLI-VERSION-01`; ordinary hosted CI passed at
`b491aac5` (run 34306975901); master integration remains pending. `emrys --version` reports the package version; `-v` adds its loaded
path and Python version/executable. Focused production-path tests pass,
including foreign-directory display and preserved ordinary checkout admission.
The existing parser and package version remain the only owners.

**Outcome and acceptance:** The installed command reports its actual package
version from an arbitrary directory without requiring a Project, probing
scientific tools, or writing state. If source identity is included, reuse
existing source authority, distinguish known from unavailable information, and
never infer the installed package's commit from an unrelated current directory.
The implemented display is allowed from another checkout so it can identify
the installation in use; ordinary commands and positional `--version` text
still undergo the existing checkout check. Existing command dispatch remains. A version response does not
prove runtime readiness, cleanliness, or reproducibility. This small public-CLI
slice supports item 30; it does not close the broader release outcome.

### 44. Provide a concise contributor and problem-reporting route

**Finding:** The audited repository has no repository-owned issue forms or PR
template. Maintainer guidance already lives in the workflow kernel and
engineering conventions; troubleshooting already identifies useful diagnostic
facts and protects study data. The missing outcome is a clear public route
that connects those existing instructions to an actionable report.

**Outcome and acceptance:** Reconcile effective inherited GitHub defaults, then
use [native issue forms][issue-forms] or the smallest suitable template for
bugs/setup problems, plus a concise contribution/PR entry point. Request the
revision, command, expected/observed behavior, and a minimal synthetic
reproduction. Link the existing [workflow](../operations/WORKFLOW.md),
[engineering conventions](../operations/ENGINEERING_CONVENTIONS.md), and
[troubleshooting](../operations/TROUBLESHOOTING.md) rather than duplicate them.
Route protected material only through an explicitly selected appropriate
channel; do not solicit raw study data, credentials, or full logs in public
forms or invent a maintainer contact. Review rendered forms and links with
synthetic examples. Keep this small documentation/GitHub-configuration outcome
separate from new diagnostic collectors, telemetry, or automatic uploads.

## Existing capabilities and overlapping work

The following were already present at audit time: guided Project creation,
explicit biological metadata, automatic owned directories, Doctor's managed
repair, default/profile/CLI precedence, human Run names, default reporting,
and Project-local inspection. Tooling already includes actionlint, Ruff,
Vulture, uv/Pixi/renv locks, coverage, deterministic shards/receipts,
minimum-Python checks, isolated wheel installation, guarded real-R checks,
managed-runtime compatibility checks, and the operator golden path.

Hosted [review rules](https://github.com/lab-cats/EMRYS/rules/21180321) and
[default-branch rules](https://github.com/lab-cats/EMRYS/rules/21339165) reference
CodeQL, PR review, code quality, and coverage. Historical evidence also records
a CodeQL run. A configured requirement is not proof of every current execution;
absence of a checked-in CodeQL workflow does not make CodeQL missing. The audit
does not justify another generic scanner stack or validation framework.

The following changes are implemented and merged into master through PR #139.
Their original PR links identify the source slices, not remaining work. This
reconciliation prevents reselection of completed implementation; the backlog
still owns any broader acceptance or unresolved follow-up.

| Work already covered | Reference |
| --- | --- |
| Duplicate runtime-model removal | [PR #116](https://github.com/lab-cats/EMRYS/pull/116) |
| Attempt-receipt validator consolidation | [PR #117](https://github.com/lab-cats/EMRYS/pull/117) |
| Shared processing command framing | [PR #118](https://github.com/lab-cats/EMRYS/pull/118) |
| Unused private reporting-input helpers | [PR #119](https://github.com/lab-cats/EMRYS/pull/119) |
| Compression selection and findings reconciliation | [PR #120](https://github.com/lab-cats/EMRYS/pull/120), [PR #123](https://github.com/lab-cats/EMRYS/pull/123), [PR #135](https://github.com/lab-cats/EMRYS/pull/135) |
| Historical documentation-path bans | [PR #121](https://github.com/lab-cats/EMRYS/pull/121) |
| Reporting import-permission consolidation | [PR #122](https://github.com/lab-cats/EMRYS/pull/122) |
| Long-test duration estimates | [PR #124](https://github.com/lab-cats/EMRYS/pull/124) |
| Continuing stacked work while CI runs | [PR #125](https://github.com/lab-cats/EMRYS/pull/125) |
| Unused reporting-table presentation metadata | [PR #126](https://github.com/lab-cats/EMRYS/pull/126) |
| Storage measurement-row assembly and portable filesystem-call test observation | [PR #128](https://github.com/lab-cats/EMRYS/pull/128), [PR #134](https://github.com/lab-cats/EMRYS/pull/134) |
| Unconsumed summary context, predecessor validation, and scientific input snapshots | [PR #129](https://github.com/lab-cats/EMRYS/pull/129), [PR #132](https://github.com/lab-cats/EMRYS/pull/132), [PR #133](https://github.com/lab-cats/EMRYS/pull/133) |
| Polish, optimization, quickstart, and continued-compression findings | [PR #131](https://github.com/lab-cats/EMRYS/pull/131), [PR #138](https://github.com/lab-cats/EMRYS/pull/138); original documentation inputs are linked in Evidence and selection |
| Single construction of the Doctor readiness result | [PR #136](https://github.com/lab-cats/EMRYS/pull/136) |
| Direct accumulation of admitted GTF exon rows | [PR #137](https://github.com/lab-cats/EMRYS/pull/137) |

The following changes are also implemented, included in the validated PR #140
head, and awaiting that integration into master:

| Work already covered | Reference |
| --- | --- |
| Automatic ordinary CI on stacked PRs | [PR #140](https://github.com/lab-cats/EMRYS/pull/140), item 22 |
| Per-script Bash syntax checking | [PR #141](https://github.com/lab-cats/EMRYS/pull/141), item 15 |
| Selected Ruff correctness rules | [PR #142](https://github.com/lab-cats/EMRYS/pull/142), item 17 |
| Shared local/CI sharder self-tests | [PR #143](https://github.com/lab-cats/EMRYS/pull/143), item 21 |
| Preserved source-identity policy and one shared declaration of fixed HTML outputs | [PR #144](https://github.com/lab-cats/EMRYS/pull/144), [PR #145](https://github.com/lab-cats/EMRYS/pull/145) |
| Canonical BAM create-exclusive publication, with legacy replacement retired | [PR #146](https://github.com/lab-cats/EMRYS/pull/146) |
| Direct create-only reporting publication; six callback carriers and the private facade retired; redundant tests reconciled | [PR #147](https://github.com/lab-cats/EMRYS/pull/147) |

These implementations do not close unrelated recovery defects in items 1–4,
the Doctor storage-repair issue in item 9, reporting-memory policy in item 13,
or browser/scientific review. Canonical BAM retains its documented conservative
cleanup limits and historical recovery record. Reporting retains historical
readmission and provenance checks; create-only publication is not permission to
remove existing outputs or recovery evidence.

The Step 05 BAM I/O and Step 08 VCF experiments in
[PR #44](https://github.com/lab-cats/EMRYS/pull/44) and
[PR #45](https://github.com/lab-cats/EMRYS/pull/45) were outside both integrations.
Their performance evidence and disposition belong to the optimization work;
neither an old open-PR label nor an unmerged experiment establishes current
adoption or permission to repeat the work.

## Campaign disposition

Select finite outcomes from this document through the backlog or an explicitly
approved bounded objective. Existing rows retain their status and full
acceptance; new proposals are not automatically accepted by being listed here.
Use this document for scope and rationale, without copying mutable PR/check
status or maintaining parallel completion checkboxes.

At campaign close, every proposal must have a disposition in the authoritative
backlog or durable owner documentation: accepted and completed, retained for
later selection, or dismissed with its useful rationale preserved. Retire this
campaign document only after its useful content has a verified durable home.

[release-wheel]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/tests/test_package_distribution.py#L375-L468
[release-root]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/onboarding.py#L96-L99
[release-source]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/libraries/source_authority.py#L495-L527
[release-dependencies]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/pyproject.toml#L28-L29
[r-bindings]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/doctor.py#L374-L385
[snakemake-binding]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/doctor.py#L336-L438
[snakemake-admission]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/lifecycle.py#L1087-L1099
[snakemake-test]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/tests/orchestration/run_coordinator/test_doctor.py#L179-L223
[slurm-preflight]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/control.py#L878-L923
[report-structure]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/reporting/_run_report/validation.py#L155-L202
[report-print-tests]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/tests/reporting/test_report.py#L752-L865
[init-cancellation]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/onboarding.py#L384-L415
[execution-cancellation]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/control.py#L1337-L1346
[cancellation-test]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/tests/orchestration/run_coordinator/test_materialization.py#L3178-L3244
[inspect-output]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/control.py#L1684-L1830
[inspect-result]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/inspection.py#L127-L143
[release-constraints]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/tests/test_package_distribution.py#L235-L288
[fastq-draft-identity]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/onboarding.py#L538-L554
[fastq-draft-test]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/tests/orchestration/run_coordinator/test_onboarding.py#L342-L364
[fastq-project-identity]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/normalization.py#L231-L275
[provider-composition-test]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/tests/orchestration/run_coordinator/test_materialization.py#L861-L939
[provider-interface]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/analyses/__init__.py#L23-L149
[historical-reader-test]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/tests/contracts/orchestration/test_application_model_contracts.py#L503-L517
[provider-readmission]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/analyses/__init__.py#L517-L540
[documentation-gate]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/scripts/documentation/validate_structure.py#L289-L300
[run-picker]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/control.py#L144-L173
[run-picker-test]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/tests/orchestration/run_coordinator/test_run_locator.py#L120-L144
[attempt-context]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/orchestration/run_coordinator/materialization.py#L1682-L1688
[package-version]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/__init__.py#L9
[public-command-parser]: https://github.com/lab-cats/EMRYS/blob/fdf76760311e6c8076320a289ef3956d754c190d/src/emrys/__main__.py#L225-L298
[issue-forms]: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository
