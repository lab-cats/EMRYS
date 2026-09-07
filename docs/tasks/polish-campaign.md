# EMRYS polish campaign

This document collects the repository-polish and professional-tooling candidates
from the September 7, 2026 audit. Its purpose is to make the proposed work
concrete enough to select and scope. It covers correctness, operator experience,
architecture reduction, developer feedback, dependency maintenance, and release
presentation.

The user requested this document; implementation of its candidates has not been
authorized. The [backlog matrix](backlog_matrix.md) remains the only authority
for accepted work, execution status, scores, and final acceptance. Existing row
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

References to local source below identify the inspected owner at that revision.
Before selecting a candidate, reconcile its current source, backlog coverage,
and overlapping PRs. The [compression intake](compression_campaign.md) contains
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

Suggested early selections are the shell syntax correction, artifact-version
admission, one publication-recovery owner, and the Project preview. For added
tooling, start with ShellCheck, one type checker, and stronger Ruff integration;
add local hooks after their participating checks have clear owners. These are
selection recommendations, not a required dependency graph.

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
consolidation in PR #116 does not repair these cases. No compression claim is
established for the small descriptor fix.

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
diagnostics. This is a separate unselected artifact correction; `CONTRACT-API-01`
and PR #117 address orchestration Attempt receipts. Quantify any net reduction
before describing this correctness fix as compression.

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

**Outcome and acceptance:** First verify the mismatch through the existing plan
and admission paths. Then provide a placement-appropriate authorized repair or
an actionable route to the required qualification. Preserve profile ownership
and the preview/execute boundary. Local plan proof and institutional execution
are separate. This is the existing compression-intake discussion 6, still a
proposed bounded defect investigation.

### 10. Complete a novice institutional walkthrough

**Finding:** [Quickstart](../../quickstart.md), [Runbook](../operations/RUNBOOK.md),
and [profile examples](../../configs/execution_profile.example.yaml) do not yet
provide a demonstrated fresh-clone-to-Results journey at a named institution.

**Outcome and acceptance:** Under existing **`SITE-PARITY-01`**, an operator
without repository-development context follows the maintained instructions
through site modules, Project creation, profile selection, storage/runtime
admission, Slurm execution, inspection/recovery when needed, and Results.
Record concrete friction and qualify the required site semantics at one exact
revision. Consolidate procedures in their existing homes; hosted success alone
does not close the site outcome. Site execution needs its own authorization.

### 11. Align the initial operator environment with Doctor

**Finding:** Quickstart and its hosted golden path install default developer
groups, while Doctor already uses `--no-default-groups --group workflow`.

**Outcome and acceptance:** Start operators with the same admitted runtime
groups Doctor selects, retaining development dependencies for repository
checks. A clean environment reaches help, Project creation, Doctor, execution,
reporting, and inspection. Update the existing quickstart and CI setup; measure
installation savings before quantifying them. This documentation/configuration
slice supports `SITE-PARITY-01` without independently closing site acceptance.

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

## Architecture reduction

### 13. Retire the ineffective reporting-memory control

**Finding:** [Resource policy](../../src/emrys/orchestration/run_coordinator/resource_policy.py)
parses, resolves, validates, persists, and overlays `reporting_memory_mb`, but
[report execution](../../src/emrys/orchestration/run_coordinator/reporting_operation.py)
does not consume it to allocate or limit memory.

**Outcome and acceptance:** Under **`REPORT-ROSTER-01`**, remove the active control
and redundant defaults, storage, overlays, and validation once accepted
YAML/CLI inputs and historical admission have an explicit disposition. Preserve
immutable records, required historical reads, regeneration, and report
transactions. Demonstrate net reduction across callers, schema/configuration,
tests, and documentation. Do not add an ignored compatibility option or a new
resource manager. Do not claim generic reporting-only identity coupling as a
verified defect: reporting declarations already have a separate owner.

### 14. Retire the frozen dashboard when its existing row is selected

**Finding:** The [coordinator guide](../../src/emrys/orchestration/run_coordinator/README.md)
describes the dashboard as a stale, unsupported preview frozen under
**`DASHBOARD-RETIRE-01`**.

**Outcome and acceptance:** Perform the row's complete caller/evidence audit,
then retire product code, parsers, dedicated tests, targets, and stale guidance
together. Preserve Project-local inspection, required scheduler accounting and
sanitized streams, and exact historical reads. The candidate offers potential
substantial reduction; deletability was not established by this audit. Its
deferred status and evidence-deletion authority remain with the existing row.

## Development and CI tooling

### 15. Check every script in the Bash syntax gate

**Finding:** [Make's static gate](../../scripts/make_quality.mk) passes thirteen
filenames to one `bash -n` invocation, which parses only the first script.

**Outcome and acceptance:** Parse each declared script and propagate failures
through both `smoke` and `validation-static`. A syntax error in a non-first
entry must fail both callers. Reconcile the existing Make expansion fixture.
This is a small new tooling/test correction, separate from ShellCheck and
formatting; no product changes are needed.

### 16. Integrate ShellCheck

**Finding:** ShellCheck has an unused Make variable and source annotations, but
no active invocation; actionlint disables its shell integration.

**Outcome and acceptance:** Run [ShellCheck](https://github.com/koalaman/shellcheck)
on retained shell owners and applicable embedded CI scripts, using existing
source annotations and reviewed rules. Actionable findings fail the established
gate. Reconcile programs scheduled for retirement under `OPS-03`; retain Bash
syntax checks. Add a maintained tool integration, not another shell framework.

### 17. Broaden Ruff correctness checks

**Finding:** [Ruff configuration](../../pyproject.toml) currently selects only
`E9`.

**Outcome and acceptance:** Enable a reviewed correctness subset, including
useful undefined-name detection, through the existing lint command. Triage
actual findings and verify affected behavior in its owner. Use the installed
[Ruff linter](https://docs.astral.sh/ruff/linter/); quantify fixes before approving
a broader scope. This outcome is separate from formatting.

### 18. Adopt consistent Python formatting

**Finding:** Ruff is installed, but no formatter check is integrated.

**Outcome and acceptance:** Use [Ruff's formatter](https://docs.astral.sh/ruff/formatter/)
with one configuration and a reproducible `--check` command. Define the
maintained scope and exclude generated/vendored material deliberately. Keep
one-time formatting churn separate from semantic changes and review its full
size before selection. No additional Python formatter is needed.

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

**Finding:** No repository-managed pre-commit configuration exists.

**Outcome and acceptance:** Explicitly installed [pre-commit](https://pre-commit.com/)
hooks run agreed quick checks on changed files using the same tools and policy
as CI. Include relevant lint/format and basic whitespace/conflict checks once
their owners are established. Ordinary commits do not run long suites, install
scientific dependencies, or acquire a second validation inventory.

### 21. Share local and CI validation inventory

**Finding:** The [sharder](../../tests/tools/python_test_shards.py) excludes its
self-tests from ordinary collection. CI invokes them separately, while local
`all-checks` does not restore that suite.

**Outcome and acceptance:** Move the CI-only invocation into the existing shared
validation owner and remove the duplicate declaration. Both assembled gates run
the sharder self-tests exactly once, and their failure blocks both routes.
Review other explicit exclusions for lost coverage. This is a proposed
tooling-only correction adjacent to `CI-01`, not a new test registry.

### 22. Run ordinary CI automatically on supported stacked PRs

**Finding:** [PR triggers](../../.github/workflows/ci.yml) restrict automatic
checks to a `master` base. PR #117 records manual dispatch compensating for that
restriction.

**Outcome and acceptance:** Settle the supported PR-base policy, then make a PR
against a development branch receive the agreed ordinary checks automatically.
Preserve intended master, merge-group, push, scheduled, and manual behavior,
including opt-in long checks and hosted rules. This is a proposed extension of
`CI-01`; manual lane selection and nonblocking stacked-work procedures already
exist and are not this outcome.

### 23. Reduce the measured CI critical path

**Finding:** Coverage coordination repeats environment setup, full collection,
and separately justified subprocess checks. Source identifies cost centers,
not their actual share of elapsed time or permission to remove them.

**Outcome and acceptance:** Continue existing **`CI-01`** after reconciling PR
#124's duration estimates. Measure one final-state path, remove a demonstrated
avoidable cost through its existing owner, and show lower elapsed time with
the same complete/disjoint test selection, coverage, receipts, subprocess
evidence, and failure behavior. Set a duration target only from measurements.

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

**Outcome and acceptance:** Demonstrate one minimal working external provider
and bespoke reporter using the existing entry points. Explain installation,
configuration, input/output ownership, resource/dependency declarations,
independent validation, execution, and reporting. Exercise the documented
example through public production interfaces without a generic workflow DSL
or test-only production behavior. Consolidate existing extension guidance;
this is the compression intake's existing documentation candidate, still
requiring bounded selection and footprint accounting.

### 30. Establish a reviewed alpha release path

**Finding:** Quickstart asks users to select a release or commit; the GitHub
releases endpoint returned no published releases during the audit. Package
version is `0.1.0.dev0`. No claim was made that Git tags are absent.

**Outcome and acceptance:** Define the supported distributed artifact and an
exact reviewed revision, then produce coherent versioning, release notes,
installation instructions, and evidence boundaries. Reuse existing isolated
wheel checks and validate the actual artifact before publication. Release
automation is justified only for the selected repeatable process; publication
and any package-index registration require explicit authority.

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

The following work was already in open PRs when the document was prepared.
Recheck these PRs and their exact changes before implementation; this table is
an overlap reference, not a completion ledger.

| Work already covered | Reference |
| --- | --- |
| Duplicate runtime-model removal | [PR #116](https://github.com/lab-cats/EMRYS/pull/116) |
| Attempt-receipt validator consolidation | [PR #117](https://github.com/lab-cats/EMRYS/pull/117) |
| Shared processing command framing | [PR #118](https://github.com/lab-cats/EMRYS/pull/118) |
| Unused private reporting-input helpers | [PR #119](https://github.com/lab-cats/EMRYS/pull/119) |
| Compression selection and findings reconciliation | [PR #120](https://github.com/lab-cats/EMRYS/pull/120), [PR #123](https://github.com/lab-cats/EMRYS/pull/123) |
| Historical documentation-path bans | [PR #121](https://github.com/lab-cats/EMRYS/pull/121) |
| Reporting import-permission consolidation | [PR #122](https://github.com/lab-cats/EMRYS/pull/122) |
| Long-test duration estimates | [PR #124](https://github.com/lab-cats/EMRYS/pull/124) |
| Continuing stacked work while CI runs | [PR #125](https://github.com/lab-cats/EMRYS/pull/125) |
| Unused reporting-table presentation metadata | [PR #126](https://github.com/lab-cats/EMRYS/pull/126) |
| Step 05 BAM I/O and Step 08 VCF performance | [PR #44](https://github.com/lab-cats/EMRYS/pull/44), [PR #45](https://github.com/lab-cats/EMRYS/pull/45) |

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
