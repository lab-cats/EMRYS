# RELEASE-01 release readiness investigation

This is the working investigation for [`RELEASE-01`](backlog_matrix.md#maintainability-and-release).
The backlog row alone owns its status, outcome, and acceptance. This document
records the decisions to make, what the source currently establishes, the
remaining checks, and the existing owners of related work. It is not a release
approval or a second task-status register.
Before closing the card, reduce this working investigation to the concise
readiness checklist; move lasting policy to its owner and let Git retain the
investigation history.

**Current source target:** open [PR #307](https://github.com/lab-cats/EMRYS/pull/307)
at `ba1fbdd3cc56196fc2ece35b73ddba56b786d223` on 2026-09-22. Most source
inspection below used its parent `f32260f0408fe1826af401fc1ddce0f2478ae6ce`.
The only delta between them reformats the selected Doctor timing assertion in
`tests/tools/real_synthetic_e2e.py`; package and guide sources are byte-identical.
The parent contains PRs #300, #302, and #304. PRs #303, #305, and #306 form a
separate CI stack and are not in the target tree. PR #307 changes the cluster
backlog and selected synthetic CI evidence over #304. Recheck the live PR head
and the relevant diff before using these observations for a release candidate.
No candidate artifact, installed full Run, institutional execution, or release
publication was performed for
this investigation.

## Intended decisions and evidence

The first decision is the **promise**: which operations and environments a
prerelease supports, and which additional claims v1 will make. A release number
does not establish platform, scientific, or biological validity. The selected
artifact, installation route, dependencies, documentation, and checks must all
express the same promise. The [earlier alpha proposal](polish-campaign.md#30-establish-a-reviewed-alpha-release-path)
supplies context; the current `RELEASE-01` row supplies acceptance.

For every selected promise, retain a criterion, exact revision and artifact
identity, evidence, limitation, and owner. A prerelease may state a narrower
tested scope and unresolved limitations. A v1 claim needs its corresponding
software and, where a named site is promised, institutional evidence. Neither
category implies scientific review or biological interpretation.

The current lowest-change **working hypothesis** is a pinned source checkout
with its locked Python environment, because that is the documented complete
user route. This is a proposal to test, not a selected release policy. A
standalone wheel can be promised only after its setup, resources, installed
operation, and provenance questions below are resolved.

| Criterion | Prerelease candidate | Additional v1 criterion |
|---|---|---|
| Workflow and artifact | State a narrow support scope and exercise every operation it promises from the selected artifact. | Exercise the complete v1 promise, including a public installed Project-to-Results journey if full standalone operation is claimed. |
| Dependencies and formats | State one supported install route, lock or resolved-range policy, current formats, and older-Run limits. | Retain a coherent tested policy; product 1.0 does not imply schema renumbering or migration. |
| Platform and site | Name supported combinations only with corresponding evidence; label an unqualified site procedure as exploratory. | If Viking is supported for v1, require exact-revision institutional qualification through its existing owners. |
| Notes and evidence | Identify version, source/artifact, changes, limitations, and bounded check results. | Reconcile all v1 claims, owner blockers, guides, and exact-revision software/site evidence before a separate publication decision. |

## Findings matrix

The “next check” column is an investigation step, not authorization to change
code, run on a cluster, install dependencies, or publish a release. The IDs are
local navigation labels, not new backlog items.

| ID | Release question | Established at the reviewed head | Next check or decision | Existing owner |
|---|---|---|---|---|
| `R01` | Exact candidate and included work | PR #307 is at `ba1fbdd3`; the investigated parent `f32260f0` differs only by formatting in one timing check. PRs #303/#305/#306 are a separate CI stack. | Select and freeze the eventual candidate, then bind each check and artifact to that exact head. | `RELEASE-01`; live Git and CI |
| `R02` | Promised operations | Quickstart describes a Viking Project-to-Results path; the Runbook also describes direct-host operation. | Classify each public operation as prerelease/v1 promised, limited, or unsupported, including recovery and report regeneration. | `RELEASE-01`; coordinator and reporting owners |
| `R03` | Platforms and site | README describes Linux/POSIX, direct one-host or one-node Slurm; managed repair is narrower. | State tested combinations and resource/storage requirements; qualify any named Viking promise at one revision. | `RELEASE-01`, `SITE-PARITY-01`, `CLUSTER-VERIFY-01` |
| `R04` | Distributed artifact | Quickstart clones the moving default branch and uses `uv sync --locked`; Runbook documents an exact tag/commit checkout; the distribution test builds an sdist and wheel. | Choose a pinned checkout, wheel paired with that checkout, standalone or limited wheel, and which built artifact is distributed and tested. | `RELEASE-01`; package and onboarding owners |
| `R05` | Study-selection resource | Viking Init points to `configs/step_07_partitions.primary_contigs.tsv` in the checkout. | Settle its installed-package route before promising checkout-free EV/PUM1 Init. | `INIT-02`; onboarding/package owners |
| `R06` | Dependency support | Wheel smoke creates a separate installer lock under constraints derived from checkout `uv.lock`; wheel metadata permits broader `jsonschema` and `referencing` ranges. | Choose lock-required or independently resolved metadata support; if lock-required, specify how the exact lock reaches users of the selected artifact. State Pixi/native/R policy separately. | `RELEASE-01`, `RUNTIME-CLOSURE-01`; package/runtime owners |
| `R07` | Version and artifact provenance | Package version is `0.1.0.dev0`; build metadata can record Git origin and Python-lock hash; installed admission hashes code and build fields. | Define prerelease/v1 numbering and independently compare the candidate artifact, embedded origin, lock, metadata, and installed bytes with reviewed source. | `RELEASE-01`; package/source-authority owners |
| `R08` | Public installed journey | Isolated wheel smoke covers help, Init, and validation outside the checkout; report smoke calls internal APIs. | Exercise selected public commands outside the checkout where supported, with checkout-bound `setup` identified; a full wheel promise requires a tiny complete Run and public report regeneration. | `RELEASE-01`; package, CLI, synthetic-journey owners |
| `R09` | Record and schema support | Approved policy refuses obsolete Run contracts, while some current-format variants and retained diagnostic contexts remain readable; schema IDs are independent of product versions. | Verify public obsolete-Run refusal preserves retained bytes; decide any schema reset through `SCHEMA-01`, independently of product v1. | `RELEASE-01`, `SCHEMA-01`; contract owners |
| `R10` | Guides and limitations | README, Quickstart, Runbook, and Troubleshooting divide reader/operator guidance; README already describes installed collaborator modules. | Reconcile install route, supported environment, Results journey, recovery, known limits, and collaborator promise without duplicate status prose. | `RELEASE-01`, `QUICKSTART-01`, `DOCS-01`, conditional `EXTENSION-01` |
| `R11` | Exact-revision evidence | Ordinary CI contains a wheel lane; selected hosted direct/Slurm and institutional exercise are separate evidence layers. PR #307 strengthens selected Doctor timing instrumentation, pending that lane's run. | Record software, installed-artifact, disposable-Slurm, named-site, visual, scientific-review, and biological claims separately. | `RELEASE-01`, `SITE-PARITY-01`, `CLUSTER-VERIFY-01`, `REPORT-01`–`03`, `SCI-AUDIT-01` |
| `R12` | Release notes and publication | The earlier alpha proposal requests versioning, notes, install guidance, and explicit evidence limits. | Define one release-note format and prerelease/v1 checklist; require separate authority for tag/release publication, package index, or new platform support. | `RELEASE-01`; publication authority remains separate |
| `R13` | Saved defaults and Projects home | `emrys setup` requires an EMRYS Git checkout and writes `.env` there; its default Projects home is checkout-relative. | Preserve this route for a checkout release, or resolve the existing setup/onboarding owner before promising a wheel-only novice path. | `RELEASE-01`; onboarding owner |
| `R14` | Performance and capacity claims | Allocation-aware profiles, Doctor timing, scheduler observations, and selected hosted runs describe configuration or dated operation; the optimization campaign audited an older revision. | Decide whether release notes make any quantitative promise; refresh affected candidates against the selected source, and measure comparable whole-operation results only if promised. | `RELEASE-01`; optimization campaign, `SITE-PARITY-01`, conditional `SETUP-02` |
| `R15` | Cross-owner release coverage | The architecture index maps ingestion, stages, evidence, Analysis, workflow, reporting, contracts, and tests; all 61 tracked package assets in scope match static patterns, but the wheel test samples 43 and no complete installed Run has been exercised. | Trace the selected public journey through each relevant owner and its packaged assets, callers, validators, contracts, and tests; record what remains unexamined. | `RELEASE-01`; functional-owner inventory and existing owners |

## Discovery record

### R01 — Exact candidate and included work

The current source target is PR #307 at the commit above, while the ordinary
checkout from which this investigation began was on an older, unrelated branch.
PRs #303, #305, and #306 change CI independently and are not included in this
head. PR #307 adds selected synthetic CI timing evidence over PR #304. A future
candidate review must inspect its actual ancestry, tree, artifact, and check
results rather than inherit this snapshot's conclusions.

This investigation's branch still descends from `f32260f0`; a direct diff to
the 2026-09-22 live #307 head `ba1fbdd3` found only the formatting change
above. Separate open
[PR #314](https://github.com/lab-cats/EMRYS/pull/314) audits schemas,
[PR #316](https://github.com/lab-cats/EMRYS/pull/316) proposes packaged EV/PUM1
selection, and [PR #320](https://github.com/lab-cats/EMRYS/pull/320) proposes
a prepared-Project runtime donor picker. PR #320 branches from an earlier
commit of #316, not its current head. None is included in the reviewed tree;
their inclusion and integration order remain candidate decisions.

### R02 — Promised operations

The [Quickstart](../../quickstart.md) presents guided setup, Project creation,
validation, Doctor, Run, inspection, and completed Results on Viking. The
[Runbook](../operations/RUNBOOK.md) also provides a direct-host synthetic path
and advanced recovery. Public command help and implementation expose further
operations, including resume, watch, stop, runtime discovery, and independent
reporting. The public parser also exposes specialist profile creation,
manifest and synthetic initialization, validation subjects, reference
reconciliation, and storage qualification. Availability of a command is not
yet a release promise. Build a
per-operation matrix with environment, required resources, success and refusal
behavior, and evidence for both prerelease and v1.

This inventory follows the [public parser](../../src/emrys/__main__.py) and
states only what the current isolated-wheel check exercises. “Not exercised”
does not mean the command cannot work; help alone does not prove its operation.

| Public operation | Current route or purpose | Isolated-wheel check at this head |
|---|---|---|
| `--version`, help | Runbook and public CLI | Help; version has a separate public-CLI check |
| `setup` | Viking Quickstart | Not exercised; requires a Git checkout (R13) |
| `profile create` | Specialist profile authoring | Not exercised |
| named `init` | Quickstart | Preview and creation from arbitrary working directories using repository fixture inputs |
| `init manifests`, `init synthetic` | Specialist inputs and supplied smoke study | Help only; no created Project through these routes |
| `runtime discover` | Existing-runtime admission | Help only; no admission exercise |
| Project `validate`, `validate manifest` | Quickstart and specialist manifest check | Named Project and manifest validation |
| Other `validate` subjects | Specialist checks | Not exercised beyond available help |
| `doctor`, `run` | Quickstart and direct-host Runbook | Not exercised as a complete installed journey |
| `inspect`, `watch`, `resume` | Run observation and recovery | Help only; no end-to-end installed journey |
| `stop` | Exact submitted-job cancellation | Not exercised |
| `report` | Independent report preview/publication/reuse | Internal report APIs with a fixture, not public `emrys report` |
| `reconcile reference-provenance`, `debug storage-qualification` | Specialist evidence and storage checks | Not exercised |

The source snapshot's specialist `validate` subjects are `all-pass`,
`artifact-contracts`, `manifest`, `bed12`, `canonical-bam`,
`canonical-bam-qc`, `cohort-candidate-preprocessing`, `duplicate-marking`,
`fasta-sidecars`, `mechanical-orientation`, `paired-cmh-candidate-ranking`,
`scientific-context-projection`, `partitioned-cohort-mpileup`,
`rseqc-orientation`, `split-n-cigar`, `star-index`, and `star-alignment`.
Each needs its own release disposition if the public parser remains exposed.
Classify material modes as well as command names: Run preview versus execute
and `--no-report`; eligible resume planning/finalization versus a successor
Attempt; report preview, publication and verified reuse; Slurm exact-request
stop; and read-only watch versus opt-in action handoff. Existing owner tests
protect these boundaries, so an installed-artifact check should sample each
promised behavior rather than duplicate their complete fault suites. The
[processing-reuse contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#processing-reuse-and-provider-boundary)
also makes `run --through processing` a distinct Steps 00–06 Run with no report
and `run --from-processing-run` a distinct downstream Run. Neither is implied
by a normal Project-to-Results promise.

### R03 — Platforms and site

The [README](../../README.md#supported-environment) describes Linux/POSIX,
Python 3.11 or newer, one direct host or one Snakemake executor inside a
single-node Slurm allocation, and cooperative single-user storage that passes
Doctor. It narrows
managed repair to x86-64 Linux with Pixi. The Quickstart selects Python 3.14
and a specific Viking path; the Runbook's managed direct-host route specifies
kernel 4.18+, glibc 2.28+, and at least 12 visible CPUs and 240 GiB for the
retained stage allowances. These are the documented default-workflow minimum,
not a full-study capacity estimate. Slurm operation also requires the checkout,
Python environment, Project, runtime, and inputs at the same physical paths
on head and compute nodes.
These are documented boundaries, not proof of every combination. The open
[`SITE-PARITY-01`](backlog_matrix.md#platform-operation-and-portability) and
[`CLUSTER-VERIFY-01`](cluster_verification_campaign.md) work retain exact-site
qualification. Do not promote hosted disposable-Slurm results to Viking proof.

The reviewed [CI workflow](../../.github/workflows/ci.yml) primarily tests
Python 3.14. Ordinary PR CI includes Python 3.11 wheel/manifest smoke; a
complete sharded Python 3.11 suite is selected by schedule or manual dispatch.
No separate 3.12 or 3.13 lane was found. Its managed-runtime profiles exercise
selected Rocky, Ubuntu, and Debian userspaces, while explicitly declining to
call the hosted runner a
4.18-kernel proof. Check the actual result for a candidate commit before citing
any lane. A passing selected userspace or minimum-Python smoke does not widen
the release promise to every POSIX distribution or Python minor version.
The package metadata's Python `>=3.11` has no upper bound. Decide whether the
promised support envelope matches that range; lock resolver markers do not
substitute for execution on an untested interpreter or platform.

The operation inventory in R02 and these environment boundaries must be
combined before selecting a promise. All prerelease and v1 cells below remain
**OPEN / DEFERRED**; a documented command or candidate artifact is not a
support decision.

| Artifact and environment | Operations to classify | Current route or gap | Prerelease | v1 |
|---|---|---|---|---|
| Checkout, Viking head and one Slurm node | `setup`, named `init`, `validate`, `doctor`, `run`, `watch`, `inspect` | [Quickstart](../../quickstart.md) documents the EV/PUM1 journey; exact-revision novice/site proof remains with `SITE-PARITY-01`. | Open | Open |
| Same Viking route | Eligible `resume`, independent `report`, exact-request `stop` | [Runbook](../operations/RUNBOOK.md) and [Troubleshooting](../operations/TROUBLESHOOTING.md) document admitted recovery; `stop` is Slurm-specific. | Open | Open |
| Checkout, approved direct managed Linux host | Synthetic or own-study Init, validation, Doctor, synchronous Run/inspect, eligible recovery/report | [Direct-host procedure](../operations/RUNBOOK.md#standalone-compute-host-with-a-managed-runtime) defines host and resource requirements; selected hosted checkout exercise is not installed-artifact proof. | Open | Open |
| Checkout, named institution runtime and placement | `runtime discover`, Doctor, Run/inspect, eligible recovery/report | [Site-runtime procedure](../operations/RUNBOOK.md#institution-provided-runtime) requires exact tool/R versions; name the site and direct or one-node Slurm placement. | Open | Open |
| Source archive built into a wheel, named host and placement | Every selected public command | The existing test builds an sdist but installs only its derived wheel; prove the exact distributed archive, derived wheel, resources, setup boundary, and dependency route (R04). | Open | Open |
| Wheel paired with a matching checkout, named placement | Every selected public command | No documented route yet proves wheel code executes while the checkout supplies only declared data/defaults (R04). | Open | Open |
| Standalone wheel, named host and placement | Help/version, Init, validation; possibly setup through Results and recovery | Isolated smoke covers selected commands with fixtures; checkout-free setup, maintained PUM1 resource, full Run, and public reporting remain unresolved. | Open | Open |
| Selected route's specialist commands | `profile create`, manifest/synthetic Init, validation subjects, discovery, reconciliation, storage qualification | The [public parser](../../src/emrys/__main__.py) exposes them; classify each before claiming support. | Open | Open |

Each selected cell needs a promised, limited, or unsupported disposition with
expected success and refusal behavior, artifact/dependency identity,
resource/path bounds, exact evidence, and existing owner. The README's broad
platform line and parser availability cannot fill those cells by themselves.

### R04 — Distributed artifact

The [Quickstart installation](../../quickstart.md#1-install-emrys) clones the
default branch and installs a locked Python environment. The
[Runbook](../operations/RUNBOOK.md#install-a-chosen-release-or-commit) has the
exact tag/commit route that a release candidate needs. The package declares
workflow, scientific/R, schema, runtime, and reporting assets in
[`pyproject.toml`](../../pyproject.toml). The
[distribution test](../../tests/test_package_distribution.py) checks packaged
resources and some installed behavior. Its build produces both an sdist and a
wheel from a copied source tree. Choose whether the distributed unit is a
pinned checkout, an sdist, a wheel paired with the exact checkout, or a
standalone/limited wheel. Name which unit is installed and tested. A wheel
need not promise the entire user journey unless that scope is deliberately
selected. The present smoke installs the built wheel, not the sdist. If the
sdist is selected, build and install from the exact distributed sdist, retain
its digest and the resulting wheel digest, and exercise its promised assets,
provenance, and public commands. `emrys setup` adds a separate checkout
dependency under R13.

The distribution choice remains **OPEN / DEFERRED**. These are the current
route-specific acceptance questions, not four simultaneous release promises:

| Candidate route | Current boundary | Minimum additional proof if selected |
|---|---|---|
| Pinned checkout | Supplies Git root, `uv.lock`, `configs/` selection, and `Projects/`; `setup` writes checkout-root settings and direct-host operation uses a separate route. | Freeze a clean commit and lock; install with the documented locked command; resolve the installed command's source; exercise each promised public operation with explicit settings when outside the checkout. |
| Source archive | The test builds an sdist but installs only its derived wheel; an extracted archive is not the Git checkout required by `setup`. | Hash the distributed sdist, inspect its resources and metadata, build and install from that exact archive, hash the derived wheel, and verify the selected commands and dependency policy. |
| Wheel paired with checkout | The checkout can supply data and defaults missing from the wheel, but ordinary checkout `uv sync` installs editable checkout code rather than proving use of the wheel. | Pin and hash both units; document an installer route that actually selects the wheel; prove installed code and assets come from it while only declared data/defaults come from the matching checkout. |
| Standalone wheel | Installed smoke covers selected Init and validation; the reviewed wheel lacks the study selection and checkout-free `setup`, and distributes a lock hash rather than `uv.lock`. | Choose limited or complete scope. For a complete novice promise, resolve R05/R06/R13 and exercise the full public installed path with documented resources and no checkout leakage. |

### R05 — Study-selection resource

The guided PUM1 command still reads the maintained selection manifest under
repository `configs/`; `pyproject.toml` package-data does not list that root
directory. The [`INIT-02`](backlog_matrix.md#novice-setup-and-operational-follow-up)
row explicitly leaves its installed-package supply unresolved. Decide whether
the selected release route keeps a checkout or needs an installed resource,
then use that owner's existing manifest admission. Do not duplicate or infer
the biological region selection from the site or reference.

A separate open [PR #316](https://github.com/lab-cats/EMRYS/pull/316)
(head `bd3f1399` at the 2026-09-22 refresh) proposes to package the maintained
selection, keep the `configs/` path as a link, and offer it after explicit
EV/PUM1 guided sample assignment. Its wheel
check covers resource presence and byte equality, while source-level guided
Init tests cover selection, explicit-manifest preservation, and
missing-reference refusal. PR #316 is a sibling of the reviewed PR #307 head,
so none of these changes are established at this document's source revision.
If it enters a release candidate, recheck the exact built artifact and run
public installed guided Init from outside the checkout using that packaged
choice. Its present wheel smoke still supplies an explicit fixture partition
manifest and does not establish the new interactive path, a complete Run, public report
regeneration, or novice Viking acceptance.

### R06 — Dependency policy

The wheel smoke reads the checkout's `uv.lock`, constructs an installer
project constrained to its resolved versions, creates that project's lock,
then syncs offline. The wheel embeds the checkout lock's hash through build
metadata, but does not distribute the lock file as a wheel resource. If wheel
support requires that exact lock, specify a usable way for consumers to obtain
and apply it or explicitly pair the wheel with a checkout. `pyproject.toml`
allows broader versions of `jsonschema` and `referencing`; the constrained
test proves neither incompatibility nor compatibility across those ranges.
The [environment owner](../operations/ENGINEERING_CONVENTIONS.md#dependencies-and-environments)
assigns Python to uv and Project-owned native/R environments to Pixi and
`renv`. The packaged Pixi and `renv` locks do not by themselves prove the
complete installed R dependency closure; `RUNTIME-CLOSURE-01` owns that open
assurance finding. Select one Python support policy and test it from the actual
candidate artifact. Keep native/R lock and site-runtime claims explicit and
distinct.
The [institution-provided R maintenance route](../operations/RUNBOOK.md#dependency-maintenance)
uses checkout-root Make targets and scripts that a standalone wheel does not
package. A wheel-only institutional maintenance promise needs a documented
supported procedure or an exact checkout companion; managed Doctor repair is
a separate route. Do not add another installer owner to bridge this gap.

### R07 — Version and provenance

[`emrys.__version__`](../../src/emrys/__init__.py) is `0.1.0.dev0` and package
metadata derives its version from it. The distribution test separately asserts
that literal version, an
[installed-package record fixture](../../tests/contracts/orchestration/test_orchestration_contracts.py)
also embeds it, and `pyproject.toml` advertises Alpha. A version change must
review those literals and public wording, preserving any intentionally
historical record fixture rather than creating a second registry.
[`setup.py`](../../setup.py) records a Git commit and dirty
state when built from a matching Git root, plus the Python lock hash; outside
that root its origin may be null. [Installed-package admission](../../src/emrys/libraries/source_authority.py)
hashes installed code with the declared build metadata but does not prove a
claimed commit matches Git source. The wheel smoke builds from a copied tree
lacking Git and expects unavailable commit provenance. For a candidate, compare
clean HEAD, embedded commit/dirty state, lock hash, selected artifact digest(s),
package metadata/entry points, and installed byte identity independently.
Decide how an eventual Git tag name, package version, artifact filenames and
digests correspond, and whether a version may be reused for a rebuilt
artifact. Recording that policy does not authorize tag publication.

### R08 — Installed public journey

The existing wheel test installs to an isolated environment, uses an arbitrary
working directory, and exercises help, named Init, and validation through the
installed command. Init uses repository fixture inputs, and its report portion
uses repository test helpers and invokes internal report preparation/publication,
not public `emrys report`. It does not run a complete Project through Doctor, scientific
execution, Results, and independent report regeneration. Extend the existing
package/public-CLI and synthetic-journey owners for the chosen promise rather
than create a second release harness.
The [public CLI tests](../../tests/test_public_cli_contracts.py) already own
broad help/entry-point enumeration, and adjacent coordinator/reporting tests
own detailed mutation and recovery cases. Use the existing distribution test
for one candidate-artifact boundary: installed `emrys --version -v` and code
path, one documented-resource success, one preview/no-write tree snapshot, and
one selected refusal. Check resource closure for the promised operation through
the actual artifact, not another static asset roster. A full real-tool Run
also needs an explicitly prepared tiny runtime; computation and test execution
must not install or repair dependencies.

The proposed candidate exercise is: build once from a clean frozen revision;
record the artifact digest and embedded build identity; install it in an
isolated environment; run supported public commands from a directory outside
the checkout with source-path leakage checked; exercise any checkout-bound
`setup` in the checkout; use only resources documented for that artifact; and
retain success, refusal, and no-write evidence. Run the
tiny complete Project only when that full installed operation is selected. A
public report exercise can finish a Run with `--no-report`, then check
`emrys report [RUN]` preview and `--execute` publication into empty owned
state, followed by verified reuse. It must not assume existing reports may be
overwritten. These are future checks, not checks performed for this document.

### R09 — Record and schema support

The approved [version policy](../design/decisions/platform-direction.md#version-support)
requires refusal of obsolete Run contracts without changing their scientific
files or evidence. The original environment is needed for older Run inspection,
resume, or report regeneration. A [current-format plan test](../../tests/contracts/orchestration/test_application_model_contracts.py)
admits an earlier content shape without an optional STAR setting; the
[Slurm submission owner](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
also reads retained submission-request v1–v4 contexts for diagnostics.
Those bounded readers do not promise general predecessor-Run support. Existing
owner [Project refusal tests](../../tests/orchestration/run_coordinator/test_normalization.py)
check a legacy Project definition without writes, and a
[Task test](../../tests/orchestration/run_coordinator/test_task.py) rejects a
historical Attempt before Task mutation. Neither is a public installed-command
exercise of obsolete-Run `inspect`, `resume`, and `report`. Select an
owner-identified historically emitted obsolete format, distinguish it from
malformed current data, verify useful original-environment guidance, and
compare every retained file before and after each command. Current-version
Attempt recovery still requires full identity and evidence checks. The
[schema rules](../../src/emrys/contracts/schemas/README.md#version-and-identity-rules)
say present IDs are exact and their numbered directories span unrelated
families. The [reporting owner](../../src/emrys/reporting/README.md) identifies
artifact entries v4, Run summaries v8, and report receipts v8 as current;
reporting package release-number changes do not themselves change scientific
Run identity. Current record schemas also accept some v1 provider metadata
without authorizing v1 execution. Product version 1.0 does not itself rename
schema IDs or provider interfaces.
The separate open [SCHEMA-01 audit PR #314](https://github.com/lab-cats/EMRYS/pull/314)
records schema readers and unresolved retained/external consumers but changes
no accepted schema policy in this reviewed tree. Decide explicitly whether v1
retains current IDs or depends on a separately approved `SCHEMA-01` migration.

### R10 — Documentation and known limits

Keep scientist purpose and the first Results journey in README/Quickstart,
operator commands and recovery in Runbook/Troubleshooting, exact behavior with
its owner, and dated evidence in its evidence home under the
[documentation authority](../design/decisions/repository-and-delivery.md#documentation-authority-and-compression).
Reconcile the README's description of a synthetic first Run with the current
Quickstart's real EV/PUM1 path and optional smoke test; reconcile its Alpha
label with the selected release. The README already says installed collaborator
modules may replace the downstream Analysis. If that is retained as a release
promise, route a separately installed provider/reporter exercise through
`EXTENSION-01`; otherwise narrow the claim. Document current limits, including
computational-candidate terminology, no biological interpretation, one-node
execution, storage/runtime admission, and whichever artifact route is selected.
If collaborator execution is promised, the
[provider contract](../../src/emrys/analyses/README.md#collaborator-providers)
requires a trusted worker that keeps work within its process descendants and
supplied paths; structural admission is not a filesystem or network sandbox.
If copied reports are promised, verify the documented complete-tree transfer
and relative links separately from publication and rendered visual review.

### R11 — Evidence layers and blockers

The ordinary PR wheel lane checks packaging and selected installed commands.
The selected real-tool synthetic lane runs from the checkout in a hosted
environment. Its 130-pair profile exercises both a direct Project and a
disposable-Slurm Project and checks parity; its 100,000-pair profile exercises
Slurm only. Neither profile is an installed release-artifact or Viking test.
The lane is scheduled or explicitly dispatched rather than an ordinary PR lane.
A scheduled run uses the default branch; an exact candidate needs a selected-ref
dispatch and retained commit identity. PR #307 adds complete Doctor timing,
runtime-probe, and Slurm-accounting checks to that selected lane, but its
completed selected hosted evidence at the eventual candidate is still required,
and even a pass would not prove before/after performance or Viking timing. The
cluster campaign records a distinct institutional novice journey and unresolved
actual-data completion. A readiness review should screen open runtime,
recovery, report, and site findings for the chosen promise, then cite exact
software, site, and rendered-output evidence without promoting any layer.
Scientific review and biological interpretation remain external work-process
records, not pipeline completion states.

For each criterion, retain the claimed operation or environment, source commit,
selected artifact digest and installed-version/build identity, dependency
policy, check URL or retained artifact, observed outcome, evidence limit,
owner, and disposition. This is a release evidence record, not a parallel Run
completion state or a substitute for owner acceptance.

### R12 — Notes and release decision

Draft release notes should identify version, source revision, artifact and
dependency identities, supported workflow/platform/installation route, current
record formats, changes, limitations, known issues, and the exact level of
verification. State that obsolete Runs require their original software and
environment for EMRYS inspection, resume, or report regeneration; retained
files remain untouched and readable with ordinary tools. No tracked
release-note or changelog file was found in the reviewed tree, so choose one
durable home without adding a second status registry. Distinguish a narrower
prerelease criterion from each additional v1 claim. Give each claim an exact
evidence identity and ceiling and a proved, limited, excluded, or blocked
disposition; link the authoritative current-format schema indices rather than
copying a full inventory into notes. The backlog row can close
its planning outcome only after its required installed-operation exercise and
readiness checklist are evidenced. Publication, package-index registration,
and added platform support require separate
authority. Citation guidance and SBOM/attestation remain separate proposed
work, not automatic `RELEASE-01` completion criteria.

### R13 — Saved defaults and Projects home

The current [`emrys setup` owner](../../src/emrys/orchestration/run_coordinator/onboarding.py)
requires an EMRYS Git checkout and an existing writable Projects home. It
writes `.env` at the checkout root only with `--execute`, defaults the home to
its `Projects/` child, and currently accepts only the `viking` site. The CLI
loads those saved settings by walking upward from its working directory; a
separate direct-host route does not use the same setup defaults. This matches
the documented Viking checkout journey but is an obstacle to a wheel-only
novice path even if the PUM1 selection is packaged. Named Init already works
outside a checkout when an explicit Projects home is provided, so the gap is
saved-defaults setup, not all installed Init. The wheel smoke does not call
`setup`. Preserve one setup authority: either select checkout-based operation
or approve a bounded onboarding change with public-command, no-write, and
resource tests before claiming standalone setup.
The public parser loads ancestor saved settings before handling even
`--version` and help. A malformed EMRYS-versioned `.env` can therefore refuse
an identity/help request. Check clean and invalid-settings working directories
through the public command, then decide whether the Runbook's “any directory”
wording needs a qualification; do not bypass fail-closed settings admission in
a release-only wrapper.

### R14 — Performance and capacity claims

The existing [optimization campaign](optimization_campaign.md) audited wall
time, disk, I/O, and memory mechanisms against `fdf767603` on 2026-09-07 and
retains 13 candidate observations and a measurement protocol. That revision
precedes this investigation's `f32260f0` source snapshot. Stage, orchestration,
analysis, evidence, and reporting paths relevant to those candidates have
changed since then. Refresh affected source/caller conclusions at the selected
release revision before relying on them; keep the detailed candidate record in
its existing owner rather than create a release performance backlog.

Current [allocation-aware policy](../../src/emrys/orchestration/run_coordinator/resources/default_execution.yaml)
and Viking's exclusive-node request are resource plans, not utilization or
safe peak-RSS measurements. [Doctor timing](../../src/emrys/orchestration/run_coordinator/doctor.py)
includes readiness and possible queue delay; the selected
[PR #307 assertion](../../tests/tools/real_synthetic_e2e.py) checks records,
not a speed threshold. [Slurm batch usage](../../src/emrys/orchestration/run_coordinator/scheduler_observation.py)
is not aggregate concurrent Run memory. The [Quickstart](../../quickstart.md)'s
5–25-minute first-setup guidance includes an explicit queue caveat and needs
dated site observations if used as a release expectation. Removing a redundant
Doctor diagnosis under [CV-26](cluster_verification_backlog.md#cv-26-repeated-doctor-input-reads)
is a structural reduction with no demonstrated
speedup. None of these observations establishes current whole-Run wall-time,
throughput, full-study capacity, or an optimization.

First classify the proposed release claim. A functional-only prerelease needs
exact software and, if named, site operation evidence without a new quantitative
benchmark gate. A claim about setup duration, throughput, wall time, memory,
disk, or I/O needs a separately authorized comparison using the existing
campaign's policy: exact baseline/candidate source and artifacts, representative
inputs, tool/profile/node/storage identities, queue time separate from execution,
complete public-command or Run elapsed time, aggregate concurrent memory,
relevant disk/I/O observations, raw paired trials including failures, and
scientific/recovery parity. The current [benchmark helper](../../scripts/benchmark_stage_resources.py)
times a producer and
cannot by itself prove full Run or network-storage performance. `SETUP-02`
already owns its eventual retirement after the campaign; do not add a release
benchmark runner, duplicate timing ledger, or new resource authority.

### R15 — Cross-owner release coverage

The [architecture index](../architecture/README.md),
[functional-owner inventory](../architecture/FUNCTIONAL_OWNER_INVENTORY.md),
and [stage map](../../src/emrys/contracts/STAGE_MAP.md) define the source,
scientific identities, and artifact edges to audit. This investigation has
examined package metadata, public CLI, onboarding/Run coordination, selected
contracts, CI, guides, and owner documentation for workflow, Analysis,
reporting, and evidence. It has not read every producer, independent validator,
ingestion script, schema consumer, test, or packaged resource through a complete
installed Run. The owner-document survey is not a scientific review.

A static resource cross-check at `f32260f0` found 61 tracked, non-Python,
non-document package assets after excluding the repository-only `.gitignore`.
All 61 match a declared `pyproject.toml` package-data pattern. The existing
[distribution test](../../tests/test_package_distribution.py) asserts presence
and source-byte equality for a selected 43 of them; the other 18 include
internal stage/evidence shell workers, shared shell/R helpers, Step 08 R helpers,
and one orchestration schema. The [processing owner map](../../src/emrys/contracts/orchestration/artifact_inventory.py)
names 12 built-in producer paths (`00a`–`08`, including `02b`); all exist, and
the nine non-Python producers match declared package-data patterns. This is a
source-pattern check, not a built-wheel inventory or execution result. Run
implementation identity already binds stage/evidence and shared-library
sources; preserve that authority while extending only a missing installed
operation check. Do not create a second exhaustive asset roster merely because
the wheel test samples assets.

| Owner boundary | Next targeted release check if its operation is promised |
|---|---|
| Ingestion and reference admission | Trace manifests, FASTQ/reference identities, no-write refusal, and packaged resources from Init through the first Run plan. Keep the limited `validate manifest` and `init manifests` contracts distinct. |
| Workflow, processing Stages `00`–`08`, and Evidence `02b`/`03` | For each selected DAG node, map packaged producer/validator assets, native/R tools, declared inputs, outputs/receipts, independent checks, and smallest real installed exercise. Preserve evidence branches as distinct from scientific completion. |
| Analysis `09`/optional `10` and external providers | Check selected module ID/version, entry points, dependencies, output/validator boundary and reporter pairing; leave method review with `SCI-AUDIT-01` and collaborator proof with `EXTENSION-01`. |
| Reporting and copied Results | Trace template, stylesheet, figure and data-input resource closure, exact receipt and public `emrys report` behavior; verify complete-tree transfer and relative links independently of rendered visual review. |
| Contracts, source libraries, and recovery | Cross-check current Run/Attempt/schema readers, installed-code identity, reuse, locks, no-write paths and obsolete-Run refusal against the selected public route. |
| Owner tests and CI | Reuse adjacent fault/scientific checks; add only missing public candidate-artifact and exact-environment edges. A source test, wheel smoke, selected hosted run, and institutional walkthrough remain different evidence. |

For each selected public operation, produce one trace from owner source through
distributed asset and dependency to output/receipt, independent validator,
public installed check, and retained evidence. Compare changed paths since the
older optimization audit and their adjacent callers/consumers before deep
rereading unaffected implementations.
Record concrete duplicate or retirement candidates with their owner, but do not
turn source-level cost or file counts into a performance result.

Use this order for the remaining read-only audit: (1) capture the current PR
head and produce a changed-path inventory against the reviewed source; (2)
finish package resource and dependency closure for the selected public route;
(3) trace ingestion and each selected processing/evidence node through its
producer, independent validator, contracts, and tests; (4) trace Analysis and
reporting publication/reuse; (5) cross-check public refusal/recovery and guide
claims; (6) reconcile the existing optimization candidates only where these
paths changed. Record an observed fact, exact source revision, remaining gap,
owner, and proposed proof for each finding. Unselected operations receive an
explicit limited or unsupported disposition rather than a full execution
campaign.

## Conditional owner routing

These are dependencies of a **selected claim**, not a second backlog or a
decision that every route must ship. Status and acceptance remain with the
linked [findings matrix](backlog_matrix.md).

| If the release promises... | Route the remaining proof or change through... | Decision boundary |
|---|---|---|
| A pinned-checkout prerelease | `RELEASE-01` for the exact revision, locked install, public operation check, source/version identity, and consistent guides (R04/R06–R08/R10). | Current checkout `setup` and explicit study manifest may be documented limits; automatic selection makes `INIT-02` relevant. |
| A wheel paired with a checkout | Package/onboarding owners for a real wheel installer path and proof of which unit supplies executable code, resources, defaults, and the Python lock (R04–R08/R13). | A checkout `uv sync` that installs editable source does not prove the selected wheel. |
| A standalone wheel with the novice EV/PUM1 journey | `INIT-02` for packaged study selection, onboarding for checkout-free saved defaults, and package/runtime owners for dependency delivery and public full-Run/report evidence (R05/R06/R08/R13). | The separate PR #316 proposal and present wheel smoke do not close this combined path. |
| Viking or another named site | `SITE-PARITY-01` for exact-revision institutional qualification; add the Viking-specific `CLUSTER-VERIFY-01` campaign when applicable. Screen `RUNTIME-CLOSURE-01` for any claimed installed R dependency closure. | Hosted direct/disposable-Slurm checks cannot substitute for institutional qualification. |
| Independently installed collaborator analyses | `EXTENSION-01` for provider/reporter discovery through a real installed execution and report. | Parser and entry-point presence alone do not prove the README's collaborator claim. |
| A selected prerelease schema reset | `SCHEMA-01` and the contract owners for the separately approved identifier/version and field decision with complete caller/evidence review; R09 still requires current public obsolete-Run refusal. | Product v1 numbering does not itself reset schema IDs. |
| Support for obsolete Runs | A separate explicit change to the ratified version policy would be needed before planning such support. | Current policy requires refusal without changing retained scientific files or evidence; `SCHEMA-01` does not authorize historical readers. |
| Reviewed report appearance or scientific conclusions | `REPORT-01`–`03` for rendered review, `SCI-AUDIT-01` for independent scientific review, and external adjudication for biological meaning. | Each claim needs its own evidence; a software release need not imply any higher layer. |

## Proposed readiness sequence

These steps are a decision and evidence plan. They do not authorize code
changes, dependency installation, cluster work, evidence promotion, or release
publication. Keep status and acceptance in the `RELEASE-01` backlog row; retain
one exact-revision evidence record for each selected claim, as specified in
R11.

1. **Freeze the candidate boundary (R01).** Record the exact source commit,
   ancestry, clean-tree state, included PRs, and excluded sibling work. Decide
   whether proposed changes such as PR #316 enter the candidate. If the head
   changes later, identify which artifact and evidence checks it invalidates.
2. **Write the release promise (R02/R03/R14).** For prerelease and v1 separately,
   classify each public operation and environment as promised, limited, or
   unsupported. For each selected combination, state required inputs, success
   and refusal behavior, platform/resource bounds, and the owner of its proof.
   Resolve whether Viking is a named support claim and whether any performance
   or capacity figure is promised; hosted Slurm alone cannot decide either.
3. **Choose one distribution and dependency contract (R04–R07/R13).** Compare
   the four routes above against the selected promise. Decide whether a
   checkout is required, how the exact Python lock reaches users or which
   metadata-resolved range is supported, how native/R locks apply, and how
   version, source, and artifact identities are checked. Record why rejected
   routes do not meet the chosen scope. Decide product numbering independently
   of schema IDs and obsolete-Run policy.
4. **Route only selected gaps to existing owners (R05/R08–R10/R13/R15).** Map
   each promise across the owner/source/resource/validator chain to an existing
   public check or an exact missing scenario. Before
   any separately approved implementation, search adjacent owners for
   duplicate mechanics and record retirement candidates, package-manager or
   library alternatives, and separate product, test, script, configuration,
   documentation, and evidence deltas. Do not add parallel release machinery.
5. **Verify the selected artifact (R04/R06–R08).** Build once from clean frozen
   source and retain source, lock, archive/wheel, installed-code, metadata, and
   resource identities. Install through the route users will follow in a clean
   environment. Check supported public commands from a working directory
   outside the checkout and any checkout-bound `setup` inside it, including
   controlled refusal and no-write paths. If complete installed operation is
   promised, add a tiny real local Project-to-Results Run and public report
   preview, publication into empty owned state, and verified reuse. Source
   fixtures, installed-command checks, and real local execution remain
   distinct evidence layers.
6. **Collect exact-revision assurance (R09/R11/R14).** Test public obsolete-Run
   refusal for `inspect`, `resume`, and `report` with retained bytes unchanged.
   Record targeted local checks and ordinary CI jobs with their actual
   outcomes and skips. Dispatch selected real-tool hosted profiles at the
   candidate ref if those claims are needed; keep 130-pair direct/Slurm parity
   separate from the 100,000-pair Slurm profile. Route any named-site claim
   through `SITE-PARITY-01`, adding `CLUSTER-VERIFY-01` for Viking, and visual
   or scientific review through their existing owners. Quantitative performance
   claims require a separate comparable experiment under R14. Do not infer one
   evidence layer from another.
7. **Reconcile guides, notes, and disposition (R10/R12).** Make README,
   Quickstart, Runbook, Troubleshooting, package metadata, and one durable
   release note agree on the actual install route, supported scope, current
   formats, older-Run limits, known issues, exact evidence, and prerelease/v1
   differences. Mark each unproved claim as limited, excluded, or blocked by
   its existing owner. Review the resulting concise readiness checklist
   against `RELEASE-01` acceptance. Tagging, package-index publication, and
   added platform support remain separate decisions.
