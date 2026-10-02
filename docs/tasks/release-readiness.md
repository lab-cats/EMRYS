# RELEASE-01 release decision brief

The [backlog matrix](backlog_matrix.md#maintainability-and-release) owns acceptance
and status. Release preparation is open; this document selects neither a version
nor a publication target and is not release approval. Five maintenance audits are
closed by the owner's decision; this brief does not reopen them or imply all their
findings were resolved. Feature and support promises require their own evidence.

The lowest-change working hypothesis is a pinned source checkout and locked Python
environment, matching the complete documented route. A standalone wheel, paired
wheel/checkout, or limited wheel needs an explicit promise and the corresponding
proof. Product 1.0 requires no schema renumbering and establishes no science.

## Revision-bound software checkpoint

Software source `4348976f26c6d19dcc7786469f5873bdd8101750` passed
[ordinary CI 36952350554](https://github.com/lab-cats/EMRYS/actions/runs/36952350554)
(all 14 selected jobs) and
[extended CI 36952344816](https://github.com/lab-cats/EMRYS/actions/runs/36952344816),
including full Python 3.11 (3,374 passed, eight skipped) and all four real synthetic
journeys. The [workflow owner](../../.github/workflows/README.md#integrated-software-checkpoint)
retains the scenario artifact IDs and proof-index identity. These are hosted
software/disposable-Slurm checks, not institutional or scientific proof.

The condensation baseline `06f88dbca7161599d7445f8cb2bfedf58f377282` changes history
documentation and the documentation checker's required-path list, not execution.
[Ordinary CI 36956303545](https://github.com/lab-cats/EMRYS/actions/runs/36956303545)
passed all 14 active jobs at exact 06. Do not relabel the extended 434 results as
execution of that documentation commit.
The September 22 audit targeted `f32260f0408fe1826af401fc1ddce0f2478ae6ce` and
production-identical `5ecc409c123fe34f746a61f7e92397c6978f3cab`; its
[frozen details](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/release-readiness.md)
remain provenance for observations below, not a current PR inventory.

Integrated source repaired R17: Report rejects failed/obsolete Runs and admits
complete verified reuse before selecting a placement/profile or scheduling. Complete reuse
creates no job or application log, even with an invalid execution profile;
incomplete generations are freshly inspected before generation. R21's old v3-only
contract wording is corrected to v3/v4. Installed candidate-artifact coverage is
still distinct from these source repairs and hosted checkout journeys.

The renv repair changed only manager 1.2.3→1.2.4; the 72 scientific package records,
repositories and settings were retained. CI R-library paths now travel through a
file so startup diagnostic output cannot contaminate them. These software repairs
do not broaden R dependency-closure or scientific-support claims.

## Promise and retained findings

R aliases are investigation references, not new accepted tasks. For every selected
promise retain environment/mode, artifact identity, criterion, evidence, limitation
and owner. Classify unpromised operations as limited or unsupported explicitly.

| Alias | Decision or remaining criterion |
| --- | --- |
| R01 | Freeze the exact candidate and included changes; live Git/CI replace the historical PR-stack chronology. Evidence for an ancestor is not an exact candidate check. |
| R02 | List public operations including configuration, Doctor/repair, run/resume, report, inspect/Watch, stop and recovery. Processing-only Steps 00–06 produce no report; downstream `--from-processing-run` is a separate route. Raw/request scheduler observation is not Run recovery. Help output is not operation proof. |
| R03 | README's Linux/POSIX and Python ≥3.11 metadata are broader than tested combinations. Managed repair targets x86-64 Linux with kernel/glibc constraints; hosted Ubuntu does not prove every site or kernel floor. Head/compute paths and storage must be shared as required; a named Viking promise needs `SITE-PARITY-01`/cluster evidence. |
| R04 | Choose pinned checkout, sdist, wheel paired with checkout, standalone or limited wheel. Smoke builds copy a subset of root assets; an sdist count is not a member inventory, and installing the wheel does not test installation from the sdist. Editable checkout installation is not standalone-wheel proof. |
| R05 | Accepted `INIT-02` uses the explicit maintained partition manifest. Packaging an optional chooser was not selected. Checkout-free study Init cannot be promised while required configuration resources lack that route. Do not convert a proposal or PR body into feature acceptance. |
| R06 | Choose lock-required or independently resolved metadata support. Wheels retain the Python-lock hash, not its bytes; constrained smoke's separate installer graph does not prove all allowed dependency ranges or installed graph parity. Python, Pixi/native and R policies are distinct; `RUNTIME-CLOSURE-01` remains a separate design. |
| R07 | Define numbering/version reuse and compare exact source/archive, artifact, embedded Git fields, lock, entry points, metadata and installed bytes. `0.1.0.dev0` alone is not unique; nullable or claimed Git fields do not independently establish source correspondence. |
| R08 | Existing outside-checkout wheel smoke covers help, Init and validation; report smoke uses internal APIs. A complete standalone promise needs selected public operations, a tiny full Run, public new report and verified reuse from that artifact. Preview does not render; no-report followed by reporting is a distinct case. Extend existing checks, not a second release harness. |
| R09 | Obsolete Run contracts are refused with retained bytes preserved, while current forms and narrow retained diagnostics are separate. Test genuinely emitted obsolete records as well as malformed fixtures through promised commands; no-new-request refusal is different from optional failure logging. The completed `SCHEMA-01` decision retains current formats; a future reset needs a separately selected transition. |
| R10 | Align README, Quickstart, Runbook and recovery guides with the chosen artifact/route. Report generation means absent-generation creation, complete verified reuse, or partial-generation refusal, not in-place regeneration. Copied Results portability differs from reuse of the admitted original Run. A promised external collaborator journey depends on `EXTENSION-01`; do not reopen `DOCS-01`. |
| R11 | Keep source tests, installed artifacts, hosted real tools/disposable Slurm, institution, rendered review, science and biology separate. Both selected sizes have four libraries and one primary partition; 100,000 pairs increase read/reference workload, not partition fanout. Scenario terminal checks cover three all-sites rows/one significant row and candidate identity/status, not a numeric AF/odds oracle. |
| R12 | Notes need version, exact source/artifact, supported installation/environment, changes, compatibility/refusal policy, limitations and linked checks. Choose prerelease/v1 scope first. Tag/index/release publication needs separate authority; citation/SBOM proposals are not automatically release gates. |
| R13 | Setup requires an EMRYS Git checkout and writes `.env`; default Projects home is checkout-relative and writable. Foreign-directory Init with explicit roots is different. A malformed ancestor `.env` can fail bootstrap before help/version, so do not promise unconditional operation from any directory. |
| R14 | Decide whether any quantitative performance/capacity claim is promised. Allocation/reservation is not RSS or workload demand; queue/wall observations and one batch's memory are not complete-Run performance. A dated setup-duration estimate needs the named environment. Use the [measurement owner](../../scripts/README.md#measurement-and-adoption); no new benchmark framework or implicit helper retirement. |
| R15 | Static packaging found 61 relevant assets matching globs, with 43 sampled and 18 unsampled by the wheel test; twelve producer command paths include nine non-Python paths. This is not built-wheel execution coverage. Trace the selected public journey across every relevant owner and both built-in Steps 09/10, validators, receipts, packaging and recovery; avoid a second roster or duplicate existence tests. |
| R16 | Named Init checks individual FASTQ records, not mate ID/count concordance; Project/specialist validation is narrower and the optional pair helper samples a prefix. Preview performs no FASTQ reads. Publication failure may leave an incomplete Project without `project.yaml`, so no-write and failed-publication claims differ. PASS/provenance does not establish biology. |
| R17 | The scheduling-before-admission defect is repaired in `1a8e5660` and included in the checkpoint above. Preserve complete reuse without profile/job/log and pre-submission failed/obsolete refusal; verify promised candidate-artifact preview/direct/Slurm paths rather than keep a stale open-defect statement. |
| R18 | Interactive named Init, discovery, run/resume and Doctor repair can write after confirmation without `--execute`. Runtime-discovery command/option help and its owner guide now state that either terminal confirmation or `--execute` can publish; their former read-only claim is corrected. Classify explicit preview, decline, accepted prompt and execute per command; Setup/profile/manifest/synthetic commands have distinct rules. No universal mutation-policy wrapper is selected. |
| R19 | Runbook states a concurrency-qualified 12-CPU/240-GiB capacity, while the resolver enforces per-stage fit (largest minimum 40,960 MiB). A lower per-stage or fixture floor alone neither refutes that concurrency statement nor establishes real-study demand. Define the workload and capacity claim, then obtain comparable evidence; native bounds do not measure total RSS. |
| R20 | Specialist validators can return zero while writing failed check rows; reference reconciliation can return zero with `overall_status=fail`. Assert semantic all-pass/summary status as applicable, not process success or output presence. Keep transaction/recovery faults with their owners. |
| R21 | Current stop supports named v3/v4 requests; the old wording is fixed. Hosted production-request stop/resume is now evidenced, but a promised current-v4 installed-distribution preview/execute/refusal journey remains distinct. Request/raw scheduler Watch before a Run exists supplies no resume authority. |
| R22 | Partly valid GTF can pass after malformed rows/transcripts are skipped; Init drops warnings and ordinary validation shows PASS while verbose validation exposes them. Decide how the promised journey presents partial acceptance and test a tiny partly valid GTF. No actual bad-reference/scientific result was established by source review. |

## Proof and support boundaries

Existing full synthetic journeys use lower CI resource floors, including 2,048 MiB;
they do not establish stock-policy capacity for real data. A preparation failure
followed by a skipped scenario supplies no scenario proof. Retain run/head/artifact
IDs, outcomes and relevant hashes before finite hosted artifact retention expires.
Independent stage/scientific oracles remain different from terminal journey checks.
Non-gating evidence owners can still be required DAG edges in the complete profile.

For portable reports inspect copied full Results trees, checksums, relative files
and fragments, browser navigation and print completeness through
[shared report acceptance](backlog_matrix.md#shared-report-acceptance) and the
[report-test owner](../../tests/reporting/README.md#rendered-report-review).
Structural HTML, a receipt or a passing schema does not prove rendering or science.
The [installed extension proof](extension-01-discovery.md#october-1-installed-interface-verification)
is bounded to its exact 9d source and synthetic interface exercise; EX-13 still
blocks a complete external public Run/report. It is not a generic plugin guarantee.

## Readiness sequence

1. Select the artifact, install/dependency policy, environments and promised
   operations for a prerelease; state additional v1 promises separately.
2. Map criteria and remaining blockers to existing owners. Preserve completed
   audits and distinguish delivered repairs, observed faults, unselected proposals
   and missing evidence; do not silently accept all catalog opportunities.
3. Exercise the exact candidate's selected public routes, refusal/recovery and
   installed resources with tiny safe fixtures and existing CI lanes. Use separate
   authority and retained evidence for any institutional or heavy workload.
4. Reconcile notes, guides and support claims with the results and limitations.
   Scientific review, candidate adjudication and biological interpretation remain
   external; EMRYS produces CMH-ranked computational candidates and provenance.
5. Obtain the separate version/target/publication decision. Narrow the promise
   where evidence is absent; neither this checklist nor CI success approves release.
