# RELEASE-01 release readiness investigation

This is the working investigation for [`RELEASE-01`](backlog_matrix.md#maintainability-and-release).
The backlog row alone owns its status, outcome, and acceptance. This document
records the decisions to make, what the source currently establishes, the
remaining checks, and the existing owners of related work. It is not a release
approval or a second task-status register.
Before closing the card, reduce this working investigation to the concise
readiness checklist; move lasting policy to its owner and let Git retain the
investigation history.

**Source snapshot reviewed:** open [PR #307](https://github.com/lab-cats/EMRYS/pull/307)
at `f32260f0408fe1826af401fc1ddce0f2478ae6ce` (2026-09-22). This revision
contains PRs #300, #302, and #304. PRs #303, #305, and #306 form a separate
CI stack and are not in the reviewed tree. PR #307 changes the cluster backlog
and selected synthetic CI evidence; the release-specific package and guide
sources reviewed here are unchanged from PR #304. Recheck the live PR head and
the relevant diff before using these observations for a release candidate.
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
| `R01` | Exact candidate and included work | PR #307 at `f32260f0` is the reviewed snapshot; PRs #303/#305/#306 are a separate CI stack. | Select and freeze the eventual candidate, then bind each check and artifact to that exact head. | `RELEASE-01`; live Git and CI |
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

## First discovery pass

### R01 — Exact candidate and included work

The reviewed source is PR #307 at the commit above, while the ordinary
checkout from which this investigation began was on an older, unrelated branch.
PRs #303, #305, and #306 change CI independently and are not included in this
head. PR #307 adds selected synthetic CI timing evidence over PR #304. A future
candidate review must inspect its actual ancestry, tree, artifact, and check
results rather than inherit this snapshot's conclusions.

At a 2026-09-22 live PR refresh, #307 had advanced to `ba1fbdd3` by a
formatting-only change to its selected E2E timing check. This investigation's
branch still descends from the reviewed `f32260f0` snapshot. Separate open
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
No separate 3.12 or 3.13 lane was found. Its managed-runtime profiles exercise selected Rocky, Ubuntu, and
Debian userspaces, while explicitly declining to call the hosted runner a
4.18-kernel proof. Check the actual result for a candidate commit before citing
any lane. A passing selected userspace or minimum-Python smoke does not widen
the release promise to every POSIX distribution or Python minor version.

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
2. **Write the release promise (R02/R03).** For prerelease and v1 separately,
   classify each public operation and environment as promised, limited, or
   unsupported. For each selected combination, state required inputs, success
   and refusal behavior, platform/resource bounds, and the owner of its proof.
   Resolve whether Viking is a named support claim; hosted Slurm alone cannot
   make that decision.
3. **Choose one distribution and dependency contract (R04–R07/R13).** Compare
   the four routes above against the selected promise. Decide whether a
   checkout is required, how the exact Python lock reaches users or which
   metadata-resolved range is supported, how native/R locks apply, and how
   version, source, and artifact identities are checked. Record why rejected
   routes do not meet the chosen scope. Decide product numbering independently
   of schema IDs and obsolete-Run policy.
4. **Route only selected gaps to existing owners (R05/R08–R10/R13).** Map each
   promise to an existing public check or an exact missing scenario. Before
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
   fixtures, installed-command checks,
   and real local execution remain distinct evidence layers.
6. **Collect exact-revision assurance (R09/R11).** Test public obsolete-Run
   refusal for `inspect`, `resume`, and `report` with retained bytes unchanged.
   Record targeted local checks and ordinary CI jobs with their actual
   outcomes and skips. Dispatch selected real-tool hosted profiles at the
   candidate ref if those claims are needed; keep 130-pair direct/Slurm parity
   separate from the 100,000-pair Slurm profile. Route any named-site claim
   through `SITE-PARITY-01` and `CLUSTER-VERIFY-01`, and visual or scientific
   review through their existing owners. Do not infer one layer from another.
7. **Reconcile guides, notes, and disposition (R10/R12).** Make README,
   Quickstart, Runbook, Troubleshooting, package metadata, and one durable
   release note agree on the actual install route, supported scope, current
   formats, older-Run limits, known issues, exact evidence, and prerelease/v1
   differences. Mark each unproved claim as limited, excluded, or blocked by
   its existing owner. Review the resulting concise readiness checklist
   against `RELEASE-01` acceptance. Tagging, package-index publication, and
   added platform support remain separate decisions.
