# DOCS-01 repository-wide working audit

This is a temporary investigation record for [DOCS-01](backlog_matrix.md). It
records observations and questions, not accepted changes, task status, or new
completion criteria. The backlog matrix remains the authority for DOCS-01;
the [cluster verification backlog](cluster_verification_backlog.md) remains the
authority for its delegated CV cards. A proposed destination below is not
permission to change or delete the source.

## Baseline, scope, and evidence

- Initial read-only pass (2026-09-22) audited source
  `3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`, the
  `codex/pr302-original-intent-corrections` revision immediately after PR
  #302's `42d02c5a` head. Branch names are provenance for this working audit,
  not a claim about the current checkout. Recheck live Git and affected text
  before selecting a correction.
- Target scope: documentation across the whole tracked repository, including root guides, operations,
  decisions, architecture, tasks, history, owner READMEs and contracts, tests,
  configuration, scripts, and CI documentation. A static first read of the
  tracked document inventory is now complete; claim-to-owner verification and
  evidence tracing remain selective. The initial inventory found
  170 Markdown files, three Mermaid files, and 15,834 Markdown physical lines.
  Four non-test Markdown files exceed 600 physical lines: Runbook (774),
  coordinator contract (1,248), cluster verification backlog (4,107), and
  polish campaign (1,084). [SIZE-01](backlog_matrix.md) separately owns size
  exceptions; line count alone does not justify splitting a file.
- Method: compare present-tense claims with their named authorities, production
  callers, tests, and adjacent reader paths. Source and tests below were read,
  not executed. A limited pre-draft local-link/heading scan found no missing
  target among 1,006 relative destinations and 369 anchors; that scan does not
  validate this new record and is not the repository's documentation check.
  The official check could not start here because the checkout has
  no `.venv` and the available Python lacks `markdown_it`. No dependencies were
  installed; no CI, Slurm, runtime, or scientific validation was performed.
- Line references below are for the pinned revision. Append the observed
  commit to any later audit pass or newly discovered finding; never silently
  mix revisions in one source claim. “Contradiction” means
  source-grounded disagreement at that revision. “Candidate” means that a
  transfer or reduction still needs a caller, link, and evidence review. No
  finding here establishes institutional qualification or biological meaning.
- The second read-only pass on 2026-09-22 checked the same `3a672fdf` source
  after the audit-only commit `8f8ac2e1`. It refined F03, F07–F08, F10,
  F12–F13, F15, F17–F22, and F25–F29, and added F30–F33. Source and tests
  were inspected, not executed.
- The third read-only pass checked the same source after audit-only commit
  `d8d11f00`. It reviewed the reference guides, scientific decision, diagrams,
  stage and selected other owner guides, and test/tooling claims. It added
  F34–F43 and refined F32–F33. No runtime or cluster work was performed.
- The fourth read-only pass checked the same source after audit-only commit
  `e9b69dd0`: all nine root and operations Markdown files, all 62 source
  READMEs and 15 owner contracts, all 53 Markdown files under tests,
  scripts, and `.github`, all 19 Markdown/Mermaid files in architecture,
  design, and reference, and all eight task/history Markdown files. It added
  F44–F45 and refined F01, F07, and F18. These counts describe static reading
  and comparison, not executed behavior or completion of the full
  repository audit. The 14 grouped-validator `CHECK_IDS` sets matched their
  contract lists in a static comparison.
- The fifth pass completed the seven remaining tracked Markdown files outside
  those groups: the docs, Projects, licenses, and source-tree indexes,
  configuration guide, stage map, and source topology. Together the passes
  touched the initial 170 Markdown and three Mermaid files, but many claims
  still need deeper caller/evidence checks. Task-record comparison and a
  targeted schema/code-comment scan added F46–F47 and refined F44; neither
  executed product behavior.
- The sixth read-only pass rechecked selected claims against the same source
  after audit-only commit `c093c696`. It corrected F26's provider path and
  removed an unsupported clause from F36, refined F07, F13, and F26, and added
  F48. Discovery notes were split at F30 to keep both temporary files below
  the 600-line review threshold. No source or runtime behavior changed.

The [documentation authority](../design/decisions/repository-and-delivery.md#documentation-authority-and-compression)
guides placement: scientist journey in root guides, operator action and recovery
in operations, exact behavior beside owners, durable rationale in decisions,
and dated retained observations in history or retained artifacts. Before
closing DOCS-01, account for every finding: correct or transfer it to its
durable owner, dismiss it with a reason, or explicitly defer it to an
authoritative row or owner. Reconcile the backlog and live links, then retire
this temporary record. Exact evidence deletion needs its own proposal,
explicit approval, and separate commit.

### Coverage so far

The inventory spans tracked Markdown and Mermaid files; the limited link scan
covered Markdown. Source comparisons are narrower. The following map keeps the
remaining repository-wide work visible without claiming file-by-file completion.

| Area | Compared to date | Further reading needed |
| --- | --- | --- |
| Scientist and operator paths | All nine root and operations Markdown files; configuration and selected reference guides | End-to-end reader routes and any reference guides not yet compared. |
| Architecture and decisions | All 19 architecture, design, and reference Markdown/Mermaid files, including all three diagrams | Check remaining source implications and reader routes; no visual rendering was performed. |
| Task and evidence records | All eight task/history Markdown files; 61 CV index entries reconciled to card endings | Original evidence origins and retained artifacts still need independent verification. |
| Product owners | All 62 source READMEs and all 15 owner contracts, with focused production comparisons | Remaining code and schema claims beyond selected owner paths. |
| Tests, scripts, and CI | All 53 Markdown files in these trees, plus selected source assertions and documentation-check code | Executable checks were not run; compare remaining code, fixtures, and retained evidence. |

## Findings matrix

The last column names the next investigation or possible durable home. It is
not a list of approved edits. Discovery notes below give the source references
and the boundary for each row.

| ID | Kind | Observation at the pinned revision | Next check or likely owner |
| --- | --- | --- | --- |
| [F01](docs-01-discoveries.md#f01-public-stop-in-the-platform-decision) | Contradiction | Platform decision denies public stop and limits resume to failed/interrupted Runs; exact-request stop and prepared finalization exist. | Reconcile both decision claims with the stop/resume contracts and CV-18 ceiling. |
| [F02](docs-01-discoveries.md#f02-standalone-resource-floor) | Contradiction | Runbook gives a fixed 12-CPU/240-GiB standalone floor; defaults resolve against capacity and reject unmet task minima. | Check resource resolver and planning minima; correct operator capacity advice. |
| [F03](docs-01-discoveries.md#f03-init-02-in-cluster-summaries) | Contradiction | CV summaries call INIT-01–03 source-complete while INIT-02 is Open. | Preserve explicit-manifest proof; reconcile present status with the authoritative backlog. |
| [F04](docs-01-discoveries.md#f04-root-quickstart-description) | Reader route | Root README calls Quickstart a synthetic first Run; Quickstart leads with real EV/PUM1. | Align root journey and retain optional smoke link. |
| [F05](docs-01-discoveries.md#f05-generic-study-versus-named-evpum1-route) | Reader route | “Own study” Runbook route points into fixed EV/PUM1 inputs and choices. | Separate generic study guidance from the named example. |
| [F06](docs-01-discoveries.md#f06-existing-project-and-new-project-recovery) | Reader route | Troubleshooting combines existing-Project navigation with absent-child Init. | Give each failure its own recovery instruction. |
| [F07](docs-01-discoveries.md#f07-doctor-repair-does-not-always-install) | Contradiction | Runbook, decision, and coordinator contract imply Doctor always installs; the decision also assigns it uv work, but Python setup is separate. | Align operator, owner, and decision wording with Doctor plan and package-manager ownership. |
| [F08](docs-01-discoveries.md#f08---version-and-local-env) | Behavior question | Runbook promises `--version` from any directory; `.env` is parsed before the version response. | Exercise malformed marked `.env` in a tiny local fixture before changing the promise. |
| [F09](docs-01-discoveries.md#f09-runbook-entry-order) | Reader route | Advanced request/watch/stop procedures precede Runbook orientation. | Test whether moving the orientation improves entry without hiding recovery commands. |
| [F10](docs-01-discoveries.md#f10-contract-location-claim) | Contradiction | Two indexes claim every source owner has an adjacent `CONTRACT.md`; many use a README or schema instead. | State actual owner-specific contract locations. |
| [F11](docs-01-discoveries.md#f11-python-hook-scope) | Contradiction | Engineering guide omits root `setup.py` from hook scope. | Align the guide with `.pre-commit-config.yaml`. |
| [F12](docs-01-discoveries.md#f12-init-preview-proposal) | Prior-revision proposal | Polish campaign's dated audit says Init preview shows only destination and directories; normal preview now shows scientific values. | Compare remaining requested fields and preview/publication protection. |
| [F13](docs-01-discoveries.md#f13-doctor-profile-proposal) | Prior-revision proposal | Polish campaign's dated audit says Doctor has no `--profile`; the public option now exists. | Reconcile proposal with accepted work and tests. |
| [F14](docs-01-discoveries.md#f14-old-source-attestation-cost-candidate) | Recheck candidate | Old optimization Git-call finding counts a prior revision's source calls, not necessarily current execution. | Re-evaluate the current source before selecting optimization work. |
| [F15](docs-01-discoveries.md#f15-cv-u22-interim-status-prose) | Preserve chronology | CV-U22's dated checkpoints explain why the card returned to Open; compression has no demonstrated benefit yet. | Keep the causal record unless a concrete reader conflict is found. |
| [F16](docs-01-discoveries.md#f16-polish-merged-pr-tables) | Compression candidate | Polish campaign repeats merged-PR chronology in two long tables. | Check unique decisions before leaving routine genealogy to Git. |
| [F17](docs-01-discoveries.md#f17-main-backlog-chronology-and-run-repetition) | Preserve row evidence | One hosted run supports three distinct backlog rows; repeated row-local citations may be warranted. | Check only routine genealogy for safe compression. |
| [F18](docs-01-discoveries.md#f18-history-filing-rule-and-existing-compendium) | Evidence placement | History requires dated topic files, yet its compendium is undated and backlog names it as the CV evidence transfer destination. | Decide legacy exception versus dated records after mapping links and origins. |
| [F19](docs-01-discoveries.md#f19-doctor-experiment-evidence-in-workflow-readme) | Evidence placement | CI workflow README repeats a shorter Doctor experiment summary already detailed in the CV backlog. | Use the CV card as evidence source before considering a history transfer. |
| [F20](docs-01-discoveries.md#f20-independent-golden-migration-comparisons) | Evidence placement | Independent-golden README mixes current oracle use with successive migration history. | Preserve comparison evidence before shortening owner instructions. |
| [F21](docs-01-discoveries.md#f21-coordinator-contracts-no-write-section) | Navigation candidate | Coordinator contract has a 632-line no-write section without subheadings; similar topics guard distinct boundaries. | Map topics before restructuring; no deletion inferred. |
| [F22](docs-01-discoveries.md#f22-coordinator-cross-owner-detail) | Ownership question | Coordinator, logging, runtime, and Runbook descriptions overlap but have different trust boundaries. | Preserve each owner's guarantee and useful cross-links. |
| [F23](docs-01-discoveries.md#f23-init-details-in-the-runbook) | Compression candidate | Runbook Init guidance mixes operator choices with hashing and file-identity internals. | Retain actionable warnings; place exact mechanics beside coordinator/config owners. |
| [F24](docs-01-discoveries.md#f24-named-profile-procedure-placement) | Audience question | Config guide holds a long named-profile operator procedure while Runbook routes there. | Decide whether Runbook needs a concise command path and config guide the format. |
| [F25](docs-01-discoveries.md#f25-reporting-decision-versus-migration-history) | Compression candidate | Reporting decision record includes implementation and PR migration detail beside lasting rationale. | Check unique rationale, then rely on reporting owner/Git for mechanics. |
| [F26](docs-01-discoveries.md#f26-alpha-carrier-note-in-reporting-readme) | Preserve API guidance | Reporting README's five-line carrier note mixes a brief migration phrase with current collaborator API guidance. | Retain current types and positional guidance; isolated trimming has negligible value. |
| [F27](docs-01-discoveries.md#f27-old-fixed-resource-provenance) | Compression candidate | Resource-profile README repeats old 12-core provenance. | Retain current resource contract and historical evidence at their owners. |
| [F28](docs-01-discoveries.md#f28-repeated-owner-boilerplate) | Compression candidate | Owner test and stage READMEs repeat near-identical generic paragraphs. | Compare exceptions, then use one shared explanation and local differences. |
| [F29](docs-01-discoveries.md#f29-library-subowner-navigation) | Navigation mismatch | Tests point to a library index that does not route readers to six documented Python subowners. | Add a concise subowner route without copying contracts. |
| [F30](docs-01-discoveries-continued.md#f30-dashboard-reporting-stage-text) | Product-facing text | Dashboard still describes three reporting transactions and a final workflow target after reporting. | Check current workflow/reporting owners and historical log aliases before selecting a product correction. |
| [F31](docs-01-discoveries-continued.md#f31-historical-slurm-username-recovery-advice) | Recovery wording | Troubleshooting gives an undated upgrade instruction for a Slurm username incident whose submission fix is already present. | Preserve incident evidence and give current-version diagnosis. |
| [F32](docs-01-discoveries-continued.md#f32-mermaid-checks-stated-ceiling) | Evidence ceiling | Documentation guides overstate Mermaid syntax and all-file heading checks; checker covers declarations/fences and canonical H1s. | Narrow both READMEs to the actual structural checks. |
| [F33](docs-01-discoveries-continued.md#f33-report-receipt-version-in-the-scientist-diagram) | Diagram contradiction | Scientist pipeline diagram names a v4 receipt and groups summary TSV with HTML reporting; current report receipt is v8. | Separate summary and HTML publication, using reporting/schema owners. |
| [F34](docs-01-discoveries-continued.md#f34-prepared-finalization-in-the-reliability-diagram) | Diagram omission | Reliability diagram sends every resume to a new Attempt; prepared finalization may complete the old Attempt. | Show finalization and eligible continuation as distinct paths. |
| [F35](docs-01-discoveries-continued.md#f35-fastq-pairing-in-the-glossary) | Wording ambiguity | Glossary says filenames never infer R1/R2 pairing; guided Init detects mate pairs from names. | Distinguish mate discovery from authored biological pairing. |
| [F36](docs-01-discoveries-continued.md#f36-cross-owner-history-in-runtime-test-guidance) | Placement candidate | Runtime test README ends with a sentence about retired report-publisher tests. | Check whether that history belongs with reporting evidence, then keep this README to runtime test scope. |
| [F37](docs-01-discoveries-continued.md#f37-bed12-dependency-in-the-scientist-diagram) | Diagram omission | Combined QC/orientation node lacks the BED12 dependency required by RSeQC. | Show the fan-in or split the evidence branches. |
| [F38](docs-01-discoveries-continued.md#f38-slurm-request-in-the-reliability-diagram) | Diagram omission | Slurm authorization is drawn as direct Attempt creation, omitting the pre-Run submission request. | Show request/submission and compute-side admission separately. |
| [F39](docs-01-discoveries-continued.md#f39-validation-roster-inventory-claim) | Evidence ceiling | Roster guides claim every validator; inventory test checks a fixed grouped-producer map. | Name its actual producer scope and discovery limit. |
| [F40](docs-01-discoveries-continued.md#f40-concurrency-in-the-local-workflow-profile) | Terminology drift | Local workflow profile guide says “sample concurrency”; current policy resolves per-stage concurrency. | Align wording with resource schema and policy. |
| [F41](docs-01-discoveries-continued.md#f41-step-05-checks-read-only-help) | Script help contradiction | Retained Step 05 check calls itself read-only while writing a TSV and directory probe. | State input immutability and output mutation precisely. |
| [F42](docs-01-discoveries-continued.md#f42-report-transfer-in-the-coordinator-test-index) | Evidence placement | Coordinator test index lists report transfer as a check but links an operator procedure, not a test. | Route the prior tiny copy observation to its CV evidence record. |
| [F43](docs-01-discoveries-continued.md#f43-print-behavior-in-the-reporting-test-guide) | Evidence ceiling | Reporting test guide says it pins print behavior; checks cover CSS/HTML structure, while visual acceptance is pending. | Name source-level print checks without implying rendered review. |
| [F44](docs-01-discoveries-continued.md#f44-internal-workers-described-as-standalone-commands) | Contract contradiction | STAR/RSeQC contracts and coordinator comments call producer commands public, although they are internal Run workers. | Correct command ownership across these texts; retain direct help and grouped validators. |
| [F45](docs-01-discoveries-continued.md#f45-watch-and-stop-in-the-command-audience-map) | Reader route | Functional-owner audience map omits public `watch` and `stop` despite their novice and operator routes. | Add the audiences or mark the examples nonexhaustive. |
| [F46](docs-01-discoveries-continued.md#f46-artifact-common-schema-description) | Schema description | Public common-schema metadata still says it serves v1 records; current registry reuses it for v4/v8 documents. | Review schema-byte compatibility before any wording correction. |
| [F47](docs-01-discoveries-continued.md#f47-r-probe-concurrency-candidate-after-cv-26) | Selection context | Optimization candidate still asks for a bounded R-probe concurrency comparison after CV-26 already measured and deferred two workers. | Bind any future proposal to CV-26's disposition and new resource/cancellation authority. |
| [F48](docs-01-discoveries-continued.md#f48-project-name-lookup-from-the-repository-root) | Reader route | Root guide suggests `--project NAME_OR_PATH` outside a Project, but bare names resolve only beside the current directory. | Give a path from the repository root or an absolute Project path. |

## Discovery notes

The [first discovery notes](docs-01-discoveries.md) and
[continued notes](docs-01-discoveries-continued.md) give sources, uncertainty,
and preservation boundaries for every matrix row. The temporary split keeps
each document below the 600-line review threshold.

## Preservation boundaries for the next pass

The CV campaign's E01–E12 evidence register, CV-26 measurements, the
optimization campaign's measured PR #45 experiment, the validation-evidence
compendium, the workflow Doctor experiment, and independent-golden migration
comparisons are retained support for bounded claims. Their placement can be
reviewed, but shortening or moving adjacent guidance must not silently delete
or promote them. The [CV backlog](cluster_verification_backlog.md) also retains
an original-note crosswalk near its end; inspect that before condensing any
card history. The [FASTQ admission owner](../../src/emrys/ingestion/sample_manifest_admission/README.md)
preserves a NUL-byte header counterexample from an unpublished helper rewrite;
the optimization campaign relies on that accepted-input boundary, and this
pass found no direct NUL regression fixture. Retain it before shortening that
owner history or changing the helper. Concise current surfaces, including the
root CI index and schema README hierarchy, need no change merely because they
were audited.

The 14 grouped-validator contracts retain distinct producer and validator
boundaries. For example, canonical BAM QC accepts a nonempty zero-exit
quickcheck as producer evidence while its validator rejects it; FASTA sidecar
production permits unordered contig pairs while validation requires order.
The canonical BAM, partitioned mpileup, and candidate-preprocessing contracts
also record exact recovery or evidence limits. Compression must preserve those
limits and the owner-local check IDs rather than treat all repeated checks as
redundant.
