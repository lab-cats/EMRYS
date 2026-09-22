# RELEASE-01 release readiness investigation

This is the working investigation for [`RELEASE-01`](backlog_matrix.md#maintainability-and-release).
The backlog row alone owns its status, outcome, and acceptance. This document
records the decisions to make, what the source currently establishes, the
remaining checks, and the existing owners of related work. It is not a release
approval or a second task-status register.
Before closing the card, reduce this working investigation to the concise
readiness checklist; move lasting policy to its owner and let Git retain the
investigation history.

**Source reviewed:** open [PR #307](https://github.com/lab-cats/EMRYS/pull/307),
`f32260f0408fe1826af401fc1ddce0f2478ae6ce` (2026-09-22). This head
contains PRs #300, #302, and #304. PRs #303, #305, and #306 form a separate
CI stack and are not in the reviewed tree. PR #307 changes the cluster backlog
and selected synthetic CI evidence; the release-specific package and guide
sources reviewed here are unchanged from PR #304. Recheck the live PR head and
the relevant diff before using
these observations for a release candidate. No candidate artifact, installed
full Run, institutional execution, or release publication was performed for
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
| `R01` | Exact candidate and included work | PR #307 head is the reviewed source; PRs #303/#305/#306 are a separate CI stack. | Select and freeze the eventual candidate, then bind each check and artifact to that exact head. | `RELEASE-01`; live Git and CI |
| `R02` | Promised operations | Quickstart describes a Viking Project-to-Results path; the Runbook also describes direct-host operation. | Classify each public operation as prerelease/v1 promised, limited, or unsupported, including recovery and report regeneration. | `RELEASE-01`; coordinator and reporting owners |
| `R03` | Platforms and site | README describes Linux/POSIX, direct one-host or one-node Slurm; managed repair is narrower. | State tested combinations and resource/storage requirements; qualify any named Viking promise at one revision. | `RELEASE-01`, `SITE-PARITY-01`, `CLUSTER-VERIFY-01` |
| `R04` | Distributed artifact | Quickstart clones the moving default branch and uses `uv sync --locked`; Runbook documents an exact tag/commit checkout; wheel assets and some installed commands have tests. | Choose checkout plus locks, standalone wheel, or a deliberately limited wheel; pin the candidate and prove every promised asset is supplied. | `RELEASE-01`; package and onboarding owners |
| `R05` | Study-selection resource | Viking Init points to `configs/step_07_partitions.primary_contigs.tsv` in the checkout. | Settle its installed-package route before promising checkout-free EV/PUM1 Init. | `INIT-02`; onboarding/package owners |
| `R06` | Dependency support | Wheel smoke constrains installation to `uv.lock`; package metadata permits broader `jsonschema` and `referencing` ranges. | Choose lock-required or independently resolved metadata support; state Pixi/native/R policy separately. | `RELEASE-01`, `RUNTIME-CLOSURE-01`; package/runtime owners |
| `R07` | Version and artifact provenance | Package version is `0.1.0.dev0`; build metadata can record Git origin and Python-lock hash; installed code is content-bound. | Define prerelease/v1 numbering and prove the actual candidate artifact binds the reviewed commit, lock, version, and installed bytes. | `RELEASE-01`; package/source-authority owners |
| `R08` | Public installed journey | Isolated wheel smoke covers help, Init, and validation outside the checkout; report smoke calls internal APIs. | Exercise every selected operation through the public installed command, from an arbitrary directory; a full wheel promise requires a tiny complete Run and public report regeneration. | `RELEASE-01`; package, CLI, synthetic-journey owners |
| `R09` | Record and schema support | Approved policy supports current formats only; schema IDs are exact and span unrelated families. | Verify public older-Run refusal preserves retained bytes; decide any schema reset through `SCHEMA-01`, independently of product v1. | `RELEASE-01`, `SCHEMA-01`; contract owners |
| `R10` | Guides and limitations | README, Quickstart, Runbook, and Troubleshooting already divide reader and operator guidance. | Reconcile install route, supported environment, Results journey, recovery, known limits, and external-provider claims without duplicate status prose. | `RELEASE-01`, `QUICKSTART-01`, `DOCS-01`, conditional `EXTENSION-01` |
| `R11` | Exact-revision evidence | Ordinary CI contains a wheel lane; selected hosted real-tool Slurm and institutional exercise are separate evidence layers. | Record software, installed-artifact, disposable-Slurm, named-site, visual, scientific-review, and biological claims separately. | `RELEASE-01`, `SITE-PARITY-01`, `CLUSTER-VERIFY-01`, `REPORT-01`–`03`, `SCI-AUDIT-01` |
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

### R02 — Promised operations

The [Quickstart](../../quickstart.md) presents guided setup, Project creation,
validation, Doctor, Run, inspection, and completed Results on Viking. The
[Runbook](../operations/RUNBOOK.md) also provides a direct-host synthetic path
and advanced recovery. Public command help and implementation expose further
operations, including resume, watch, stop, runtime discovery, and independent
reporting. Availability of a command is not yet a release promise. Build a
per-operation matrix with environment, required resources, success and refusal
behavior, and evidence for both prerelease and v1.

The current isolated-wheel check establishes only the following part of that
matrix. “Not exercised” describes this check, not a claim that the command
cannot work.

| Public operation | Documented user route | Isolated-wheel check at this head |
|---|---|---|
| `--version`, help | Runbook and public CLI | Help; version has a separate public-CLI check |
| `setup` | Viking Quickstart | Not exercised; requires a Git checkout (R13) |
| named `init`, `validate` | Quickstart | Preview, creation, and validation from arbitrary working directories |
| `doctor`, `run` | Quickstart and direct-host Runbook | Not exercised as a complete installed journey |
| `inspect`, `watch`, `resume`, `stop` | Quickstart/Runbook and public CLI | Help only for some commands; no end-to-end installed journey |
| `report` regeneration | README and Runbook | Internal report APIs with a fixture, not public `emrys report` |

### R03 — Platforms and site

The [README](../../README.md#supported-environment) describes Linux/POSIX,
Python 3.11 or newer, one direct host or one Snakemake executor inside a
single-node Slurm allocation, and storage that passes Doctor. It narrows
managed repair to x86-64 Linux with Pixi. The Quickstart selects Python 3.14
and a specific Viking path; the Runbook's managed direct-host route specifies
kernel 4.18+, glibc 2.28+, and at least 12 visible CPUs and 240 GiB for the
retained stage allowances. These resource figures are admission conditions,
not a full-study capacity estimate.
These are documented boundaries, not proof of every combination. The open
[`SITE-PARITY-01`](backlog_matrix.md#platform-operation-and-portability) and
[`CLUSTER-VERIFY-01`](cluster_verification_campaign.md) work retain exact-site
qualification. Do not promote hosted disposable-Slurm results to Viking proof.

The reviewed [CI workflow](../../.github/workflows/ci.yml) primarily tests
Python 3.14 and has a Python 3.11 wheel smoke; no separate 3.12 or 3.13 lane
was found. Its managed-runtime profiles exercise selected Rocky, Ubuntu, and
Debian userspaces, while explicitly declining to call the hosted runner a
4.18-kernel proof. Check the actual result for a candidate commit before citing
any lane. A passing selected userspace or minimum-Python smoke does not widen
the release promise to every POSIX distribution or Python minor version.

### R04 — Distributed artifact

The [Quickstart installation](../../quickstart.md#1-install-emrys) clones the
default branch and installs a locked Python environment. The
[Runbook](../operations/RUNBOOK.md#install-a-chosen-release-or-commit) has the
exact tag/commit route that a release candidate needs. The package declares
workflow, scientific/R, schema, runtime, and reporting assets in
[`pyproject.toml`](../../pyproject.toml). The
[distribution test](../../tests/test_package_distribution.py) checks packaged
resources and some installed behavior. Choose one supported artifact route
before writing its installation instructions or claiming wheel completeness.
The source checkout remains an artifact choice; a wheel need not promise the
entire user journey unless that scope is deliberately selected. `emrys setup`
adds a separate checkout dependency, recorded under R13 below.

### R05 — Study-selection resource

The guided PUM1 command still reads the maintained selection manifest under
repository `configs/`; `pyproject.toml` package-data does not list that root
directory. The [`INIT-02`](backlog_matrix.md#novice-setup-and-operational-follow-up)
row explicitly leaves its installed-package supply unresolved. Decide whether
the selected release route keeps a checkout or needs an installed resource,
then use that owner's existing manifest admission. Do not duplicate or infer
the biological region selection from the site or reference.

### R06 — Dependency policy

The wheel smoke constructs constraints from the checkout's `uv.lock`, while
`pyproject.toml` allows broader versions of `jsonschema` and `referencing`.
That test proves neither an incompatible range nor compatibility across it.
The [environment owner](../operations/ENGINEERING_CONVENTIONS.md#dependencies-and-environments)
assigns Python to uv and Project-owned native/R environments to Pixi and
`renv`. The packaged Pixi and `renv` locks do not by themselves prove the
complete installed R dependency closure; `RUNTIME-CLOSURE-01` owns that open
assurance finding. Select one Python support policy and test it from the actual
candidate artifact. Keep native/R lock and site-runtime claims explicit and
distinct.

### R07 — Version and provenance

[`emrys.__version__`](../../src/emrys/__init__.py) is `0.1.0.dev0` and package
metadata derives its version from it. [`setup.py`](../../setup.py) records a Git
commit and dirty state when built from a matching Git root, plus the Python
lock hash; [installed-package admission](../../src/emrys/libraries/source_authority.py)
binds exact installed bytes. The wheel smoke builds from a copied tree lacking
that Git root, so it does not itself prove a candidate artifact's origin at
the reviewed commit. Verify that link on the artifact selected for release.

### R08 — Installed public journey

The existing wheel test installs to an isolated environment, uses an arbitrary
working directory, and exercises help, named Init, and validation through the
installed command. Its report portion creates a fixture using repository test
helpers and invokes internal report preparation/publication, not public
`emrys report`. It does not run a complete Project through Doctor, scientific
execution, Results, and independent report regeneration. Extend the existing
package/public-CLI and synthetic-journey owners for the chosen promise rather
than create a second release harness.

The proposed candidate exercise is: build once from a clean frozen revision;
record the artifact digest and embedded build identity; install it in an
isolated environment; run public commands from a directory outside the
checkout with source-path leakage checked; use only resources documented for
that artifact; and retain success, refusal, and no-write evidence. Run the
tiny complete Project and public report regeneration only when that full
installed operation is selected. These are future checks, not checks performed
for this document.

### R09 — Record and schema support

The approved [version policy](../design/decisions/platform-direction.md#version-support)
requires current record formats and refusal of obsolete Runs without changing
their scientific files or evidence. The original environment is needed for
older inspection, resume, or report regeneration. Verify public refusal and
byte preservation; this policy alone is not a test of every older byte pattern.
Current-version Attempt recovery still requires full identity and evidence
checks. The
[schema rules](../../src/emrys/contracts/schemas/README.md#version-and-identity-rules)
say present IDs are exact and their numbered directories span unrelated
families. The [reporting owner](../../src/emrys/reporting/README.md) identifies
artifact entries v4, Run summaries v8, and report receipts v8 as current;
reporting package release-number changes do not themselves change scientific
Run identity. Product version 1.0 does not itself rename schema IDs.

### R10 — Documentation and known limits

Keep scientist purpose and the first Results journey in README/Quickstart,
operator commands and recovery in Runbook/Troubleshooting, exact behavior with
its owner, and dated evidence in its evidence home under the
[documentation authority](../design/decisions/repository-and-delivery.md#documentation-authority-and-compression).
Reconcile the README's description of a synthetic first Run with the current
Quickstart's optional smoke test. Document current limits, including
computational-candidate terminology, no biological interpretation, one-node
execution, storage/runtime admission, and whichever artifact route is selected.
If separately installed collaborator analyses are promised, route their
end-to-end proof through `EXTENSION-01`.

### R11 — Evidence layers and blockers

The ordinary PR wheel lane checks packaging and selected installed commands.
The selected real-tool synthetic lane runs from the checkout in hosted
disposable Slurm; it is not an installed release-artifact or Viking test and
is scheduled or explicitly dispatched rather than an ordinary PR lane. The
cluster campaign records a distinct institutional novice journey and unresolved
actual-data completion. A readiness review should screen open runtime,
recovery, report, and site findings for the chosen promise, then cite exact
software, site, and rendered-output evidence without promoting any layer.
Scientific review and biological interpretation remain external work-process
records, not pipeline completion states.

### R12 — Notes and release decision

Draft release notes should identify version, source revision, artifact and
dependency identities, supported workflow/platform/installation route, current
record formats, changes, limitations, known issues, and the exact level of
verification. No tracked release-note or changelog file was found in the
reviewed tree, so choose one durable home without adding a second status
registry. Distinguish a narrower prerelease criterion from each additional
v1 claim. The backlog row can close its planning outcome only after its required
installed-operation exercise and readiness checklist are evidenced. Publication,
package-index registration, and added platform support require separate
authority. Citation guidance and SBOM/attestation remain separate proposed
work, not automatic `RELEASE-01` completion criteria.

### R13 — Saved defaults and Projects home

The current [`emrys setup` owner](../../src/emrys/orchestration/run_coordinator/onboarding.py)
requires an EMRYS Git checkout, writes `.env` at its root, and defaults the
Projects home to its `Projects/` child. This matches the documented checkout
journey. It is a separate obstacle to a wheel-only novice path even if the
maintained PUM1 selection is packaged. The existing wheel smoke does not call
`setup`. Preserve one setup authority: either select checkout-based operation
or approve a bounded onboarding change with public-command, no-write, and
resource tests before claiming standalone setup.

## Next investigation cycle

1. Turn R02/R03 into a literal operation-by-environment promise table, marking
   prerelease and v1 separately and tracing each claim to current guide text.
2. Decide the R04/R06 artifact and dependency questions before specifying
   artifact-level tests. Record alternatives rejected and the capability gap
   before adding release machinery.
3. Map each promised operation to an existing public test or a concrete missing
   scenario, then route a bounded implementation to its owner. Quantify product,
   tests, documentation, configuration, and evidence changes separately.
4. Assemble a candidate checklist with exact revision, artifact digest,
   evidence link, limitation, and owner for each selected claim. Run applicable
   checks only under their separate implementation, environment, and site
   authorities.
