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
- The seventh source-comparison pass checked operator recovery, coordinator contract
  navigation, and evidence-authority overlap at the same source after
  audit-only commit `d977e055`. It added F49–F51 and refined F08, F18, and
  F21. A tiny source-bound `--version` fixture could not reach the CLI because
  the available Python lacks `jsonschema`; it supplies no behavioral result
  for F08. No dependency was installed and no product behavior was verified.
- The eighth source-comparison pass checked maintenance-surface candidates
  against current tests, owner documents, and Git provenance at the same source
  after audit-only commit `b4356f48`. It refined F16, F20, F25, and F28. The
  quantified F28 reduction remains a proposal, and no source, test, or
  retained evidence was changed.
- The ninth pass checked high-consequence stop/resume, resources, guided Init,
  Doctor, watch, and reporting-diagram claims against the same source after
  audit-only commit `b3656a05`. It refined F01–F03, F07, F30, and F33,
  including which direct tests exercise only v3 stop requests and which
  statements are merely outdated summaries. No product command or cluster
  operation was run.
- The tenth pass checked root-to-operator reader routes and reporting recovery
  vocabulary at the same source after audit-only commit `1ce339f2`. It
  refined F04–F06 and F48–F49 and added F52. It compared source and current
  owner guidance without running the CLI or changing an operator guide.
- The eleventh pass checked source-owner contract terms, test-scope claims,
  schema metadata, and lossless evidence placement against the same source
  after audit-only commit `4fe9ce84`. It refined F10, F18, F39, F42, F44–F46,
  and F51, separating true filename or public-command errors from valid
  conceptual contracts and preserving unique history. No tests or evidence
  transfers were run.
- The twelfth pass checked mate-discovery language, shared-runtime recovery,
  reporting-provider shape, internal worker classification, and CI routing
  against the same source after audit-only commit `c55d7f47`. It refined
  F33, F35, and F44 and added F53–F55. This was source and document comparison
  only; no runtime replacement, product test, or cluster operation was run.
- The thirteenth pass checked test-tool mutation claims, Make target
  applicability, and lane selection overlap against the same source after
  audit-only commit `bb1961fb`. It added F56–F58 and independently found no
  further coordinator recovery mismatch in the selected paths. The lanes
  were not executed; possible duplicate selection is not a measured CI run.
- The fourteenth pass traced historical source documents, preserved Git
  revisions, current Viking owners, and direct/Slurm reader routes at the
  same source after audit-only commit `6cb40ed3`. It refined F18, F51–F53 and
  added F59–F60. Git document dates were not promoted to observation dates; no
  evidence was moved or changed and no product or cluster command was run.
- The fifteenth audit pass rechecked F05, F08, F21–F23, and F54 against their
  owners, and added F61. At this PR's `0cb5d507` head, generic study choices
  point to configuration guidance, but the linked Quickstart continuation still
  contains EV/PUM1 paths and Slurm steps. Base-revision findings remain pinned
  as stated; the current-head limit is recorded below. No further guide or
  product edits or runtime checks were made in this pass.
- The sixteenth read-only pass at `b67e0eeb` compared diagram, decision, and
  test-tool claims with their current owners. It refined F37 and F56 and added
  F62–F64. Source and tests were read, not executed; no owner guide, product
  source, or retained evidence was changed.
- The seventeenth read-only pass at `e500e7c0` traced F14's current task-entry
  source-attestation path. Four installed-package observations remain before
  producer entry, but the historical 24-Git-call count no longer describes
  that path. This is a source count, not a timing measurement.
- The eighteenth read-only pass at `cf94af08` compared runtime, reporting,
  and Step 08/09 owner descriptions with their current source. It narrowed
  F22 and added F65–F66. These are static documentation observations; no
  execution, guide change, or scientific conclusion followed.
- The nineteenth read-only pass at `c0a6027a` compared source ownership, CI
  diagnostic capture and test selection, and Init site defaults with their
  documentation. It added F67–F70. No CI artifact, CLI, runtime, or Slurm
  execution was inspected; these findings describe source-visible scope.
- The twentieth read-only pass at `9c4fafdc` checked the fourteen-owner stage
  map against profile and module declarations, traced selected history claims
  to retained Git revisions, and followed Quickstart's saved-default route. It
  corrected F37's computation-versus-Run gate wording, extended F66, and added
  F71. Historical scale-probe numbers and a cited merge-tree equality matched
  their named Git records; original VM/Viking runtime artifacts were not in
  the checked trees and were not independently qualified here.
- The twenty-first read-only pass at `b3af5d9e` compared reporting and profile
  scope with source, traced selected reference and Step 07–10 input/output
  claims, and checked historical report golden digests against their parent
  revisions. It added F72–F73 and refined F20. The selected stage claims had
  no further high-confidence mismatch; no producer, report, or runtime ran.
- The twenty-second read-only pass at `ab25ea9b` checked development/CI guide
  claims and test-index routes against current source. It added F74–F77.
  GitHub metadata for [ordinary run 34857271894](https://github.com/lab-cats/EMRYS/actions/runs/34857271894)
  and [selected run 34857300341](https://github.com/lab-cats/EMRYS/actions/runs/34857300341)
  confirms success at `fdc7cc79`; the selected job's 130-pair step reports
  success. Artifacts and underlying runtime/scientific results were not read.
- A read-only adversarial review at `f96ac3bb` checked F01–F77 against their
  matrix summaries and cited owners. It found no material false positive;
  F52, F53, and F60 now give both baseline and post-compression Runbook line
  locations. No product check or owner-document change followed.
- The next read-only pass at `7a07d502` compared selected test indexes,
  owner boundaries, and placement guidance with current source and tests. It
  added F78–F83. The fixture consumer count is limited to tracked references;
  no shard, reconciler, task, or scientific Run was executed.
- A further read-only pass at `ce9a3289` compared stage contracts, schema and
  configuration guides, optimization candidates, and the active backlog with
  their owners. It added F84–F88. All 62 pinned GitHub source-blob citations in six selected task
  and history files resolved to retained local commits, paths, and in-range
  line numbers; that verifies coordinates, not claims or external artifacts.
  No product, test, runtime, or cluster operation ran in this pass.
- A subsequent read-only pass at local audit head `39a21034` reread the full
  1,248-line coordinator contract and selected CI/test guides against source;
  their apparent discrepancies were already F01–F88 or were owner-specific
  protections. Operator-route comparison added F89. No command, test, CI run,
  or cluster operation was initiated for this pass.
- The next read-only compression pass at local head `9c0264d3` compared
  operator, source-owner, and task/history prose with their distinct audience
  and evidence authorities. It added F90–F93 and extended F85 to the delegated
  CV index. The measured 77- and 48-line surfaces are review scopes, not
  approved savings. No guide, source, test, CI, or cluster action was run.
- The following read-only pass at local head `e90c85f4` checked task closeout
  chronology, application-log ownership, schema reader routes, and selected
  cross-owner overlap against current source. It added F94–F96 and deepened
  F22 and F53. Repeated CV-10 acceptance rows and reporting transaction
  summaries retained distinct limits, so no saving was inferred. No product
  command, test, CI, or cluster operation was run.
- A further standard-library link scan of the 174 Markdown files at local
  head `7adde22a` found 1,441 local destinations and 472 Markdown anchors with
  no unresolved target. Its simple link extraction is narrower than the
  repository's CommonMark-based checker; this is static link evidence, not a
  passing official documentation gate.
- This read-only source pass at local head `7adde22a` traced selected
  coordinator, test-lane, task-history, and stage-contract claims. It added
  F97–F99 and refined F50, F56, F69, and F86. Historical VM/Viking figures
  sampled against retained Git text yielded no additional evidence claim;
  stage check-ID rosters sampled against validator source had no mismatch.
  No test, CI, product, or cluster operation was run.
- A partitioned adversarial recheck at local head `2bd7017c` challenged
  F01–F99 against their cited authorities. F87's claimed owner drift did not
  survive source review and is marked dismissed; F67, F79, F86, and F94 were
  narrowed. F01 and F32 gained adjacent help/checker evidence, while F35,
  F49, and F51 had citation precision corrected. The matrix's final column
  now records audit boundaries rather than implementation directions. No
  product guide, source, test, CI, or cluster operation changed.
- A further read-only pass at local head `e1771d21` compared the coordinator
  contract, operator routes, and sample-manifest owner guidance with current
  sources and prior findings. It added F100–F104. Trusted-workspace and
  `/local/tmp` warnings were checked as operator-relevant overlaps, with no
  saving inferred. No product, test, CI, or cluster command was run.
- A read-only audience and history pass at local head `b65e8fb8` compared the
  stage map, scientific decision, polish campaign, test and reporting guides,
  and logging/coordinator boundaries with current owners. It added F105–F108
  and extended F22/F33. Matrix and CV evidence repetitions with distinct
  acceptance or measurements were retained as such. No product, test, CI, or
  cluster command was run.
- A further read-only pass at local heads `26898b5e` and `c0cdceb1` checked
  owner routing, runtime discovery, and the EV/PUM1 configuration inventory.
  It extended F28 with two evidence test guides and added F109–F110. A
  proposed Setup/Init conflict was withdrawn as ambiguous, and the 130-pair
  resource overlap kept distinct owner and acceptance roles. Full rechecks of
  the coordinator contract and Troubleshooting found no further
  high-confidence finding. No product, test, CI, or cluster command was run.
- A matrix and citation pass at local head `cd45bd51` narrowed F53, F58, and
  F83 against their exact command and policy boundaries and refined F64/F101's
  preservation notes. It added F111 for a current resource description linked
  to old fixed-policy files. All 68 pinned GitHub blob/tree citations in the
  tracked Markdown resolved to local commits, paths, and line ranges; that
  check does not validate their semantic claims or external artifacts. No
  product, test, CI, or cluster command was run.
- A read-only Step 00a–10 owner comparison at local head `b62e207b`
  extended F99 to Step 01→02's data-input versus Run-gate wording. The other
  early and late stage contracts yielded no new high-confidence finding.
  No validator, Run, test, CI, or cluster command was run.
- A read-only reporting, evidence, ingestion, and CI/tooling comparison at
  the same head added F112 for the R check's unqualified report-support claim.
  Other apparent overlaps were existing findings or distinct owner routes.
  No report, R check, test, CI, or cluster command was run.
- A read-only entry-route, architecture, and task-evidence comparison at local
  head `ac14392e` added F113 for CV-26's mixed current and dated record.
  Existing findings covered the other apparent guide and diagram discrepancies.
  No product, test, CI, or cluster command was run.
- An adversarial recheck at local head `d3b1f94a` challenged F100–F113 against
  their cited owners and found no material false positive or unsupported saving.
  The full 1,248-line coordinator contract and selected test-owner guides were
  reread without a distinct new finding. A constrained exact three-line prose
  scan of the 170 non-audit Markdown files found eight cross-file signatures,
  mostly shifted windows of F28/F91 repetition or owner-specific worker detail;
  it does not detect paraphrases. No test, CI, product, or cluster command ran.

The [documentation authority](../design/decisions/repository-and-delivery.md#documentation-authority-and-compression)
guides placement: scientist journey in root guides, operator action and recovery
in operations, exact behavior beside owners, durable rationale in decisions,
and dated retained observations in history or retained artifacts. DOCS-01
remains open while findings lack a documented correction, transfer, dismissal,
or explicit deferral at an authoritative owner. Backlog and live-link
reconciliation and disposition of this temporary record are likewise open.
Exact evidence deletion requires its own proposal, explicit approval, and
separate commit.

### Coverage so far

The inventory spans tracked Markdown and Mermaid files; the limited link scan
covered Markdown. Source comparisons are narrower. The following map keeps the
remaining repository-wide work visible without claiming file-by-file completion.

| Area | Compared to date | Further reading needed |
| --- | --- | --- |
| Scientist and operator paths | All nine root and operations Markdown files, configuration guide, and all three reference guides; selected routes compared with CLI source and direct tests | Remaining claim-to-source paths and an executed operator journey are unverified. |
| Architecture and decisions | All 19 architecture, design, and reference Markdown/Mermaid files, including all three diagrams; selected provider and schema claims compared with source | Remaining source implications and visual rendering are unverified. |
| Task and evidence records | All eight task/history Markdown files; 61 CV index entries reconciled to card endings | Original evidence origins and retained artifacts still need independent verification. |
| Product owners | All 62 source READMEs and all 15 owner contracts, including a full recheck of the 1,248-line coordinator contract and focused production comparisons | Remaining code and schema claims beyond selected owner paths. |
| Tests, scripts, and CI | All 53 Markdown files in these trees, plus selected source assertions, direct test cases, and documentation-check code | Executable checks were not run; compare remaining code, fixtures, and retained evidence. |

## Findings matrix

The 113 numbered records include F87, dismissed after recheck so its original
claim and correction remain traceable. The last column records an evidence
limit, uncertainty, or preservation boundary. It is not a work order.
Discovery notes give source references and the boundary for each row.

| ID | Kind | Observation at the pinned revision | Audit boundary |
| --- | --- | --- | --- |
| [F01](docs-01-discoveries.md#f01-public-stop-in-the-platform-decision) | Contradiction | Platform decision denies public stop and limits resume to failed/interrupted Runs; exact-request stop and prepared finalization exist, while top-level resume help retains the narrow label. | Decision and help scope differ from current source; CV-18's evidence limit remains. |
| [F02](docs-01-discoveries.md#f02-standalone-resource-floor) | Contradiction | Runbook gives a fixed 12-CPU/240-GiB standalone floor; defaults resolve against capacity and reject unmet task minima. | The fixed floor is a guide claim; real-data capacity remains unqualified. |
| [F03](docs-01-discoveries.md#f03-init-02-in-cluster-summaries) | Summary overclaim | Grouped CV summaries call INIT-01–03 source-complete while INIT-02 remains Open; detailed cards describe explicit manifest selection. | Explicit-manifest proof and dated cards remain distinct from INIT-02 acceptance. |
| [F04](docs-01-discoveries.md#f04-root-quickstart-description) | Reader route | Root README calls Quickstart a synthetic first Run; Quickstart leads with real EV/PUM1 and makes smoke optional. | Quickstart leads with EV/PUM1; smoke is optional. |
| [F05](docs-01-discoveries.md#f05-generic-study-versus-named-evpum1-route) | Reader route | At baseline, two “own study” Runbook routes point into fixed EV/PUM1 choices. At pinned revision `0cb5d507`, the choice route is clearer, but the Quickstart continuation still uses the named Project and Slurm. | The generic route remains unverified as a reader journey. |
| [F06](docs-01-discoveries.md#f06-existing-project-and-new-project-recovery) | Reader route | Troubleshooting mixes existing-Project lookup with absent-child Init recovery. | Existing-Project lookup and absent-child creation have distinct preconditions. |
| [F07](docs-01-discoveries.md#f07-doctor-repair-does-not-always-install) | Contradiction | Guides imply Doctor always installs and the decision assigns it uv; verified Slurm plans can skip package work while still submitting checks. | Package work, preview, and confirmed verification have different effects. |
| [F08](docs-01-discoveries.md#f08---version-and-local-env) | Source-ordering limit | Runbook promises `--version` from any directory; malformed marked `.env` is rejected before version dispatch. | Source inference and unrun installed-command behavior remain separate. |
| [F09](docs-01-discoveries.md#f09-runbook-entry-order) | Reader route | Advanced request/watch/stop procedures precede Runbook orientation. | The entry-order usability effect is untested; recovery commands remain necessary. |
| [F10](docs-01-discoveries.md#f10-contract-location-claim) | Filename overclaim | Two global indexes imply an adjacent `CONTRACT.md` for every component; many README locations use another contract form. | Two global routes overstate `CONTRACT.md` coverage; stage-owner wording remains accurate. |
| [F11](docs-01-discoveries.md#f11-python-hook-scope) | Contradiction | Engineering guide omits root `setup.py` from hook scope. | The guide and hook file disagree on `setup.py` scope. |
| [F12](docs-01-discoveries.md#f12-init-preview-proposal) | Prior-revision proposal | Polish campaign's dated audit says Init preview shows only destination and directories; normal preview now shows scientific values. | Requested fields and preview/publication protections remain distinct review points. |
| [F13](docs-01-discoveries.md#f13-doctor-profile-proposal) | Prior-revision proposal | Polish campaign's dated audit says Doctor has no `--profile`; the public option now exists. | The proposal and accepted work/tests have different authority. |
| [F14](docs-01-discoveries.md#f14-old-source-attestation-cost-candidate) | Historical cost claim | Old optimization finding counts 24 Git calls per task entry; current source has four installed-package observations before producer entry but no Git subprocess in that attestation path. | Repeated package-byte work remains unmeasured; old Git-call count is revision-bound. |
| [F15](docs-01-discoveries.md#f15-cv-u22-interim-status-prose) | Retained chronology | CV-U22's dated checkpoints explain why the card returned to Open; compression has no demonstrated benefit yet. | The causal record has no demonstrated reader conflict. |
| [F16](docs-01-discoveries.md#f16-polish-merged-pr-tables) | Compression candidate | Polish campaign repeats merged-PR chronology in two tables; the first retains unique slice mappings. | The first table retains unique mappings; routine chronology overlaps. |
| [F17](docs-01-discoveries.md#f17-main-backlog-chronology-and-run-repetition) | Retained row evidence | One hosted run supports three distinct backlog rows; repeated row-local citations may be warranted. | Only routine genealogy is a compression candidate. |
| [F18](docs-01-discoveries.md#f18-history-filing-rule-and-existing-compendium) | Evidence placement | Undated seven-topic compendium was appended after creation; a prior dated PORT record and unique ARCH-CLOSE limits remain in Git, while several run dates remain unknown. | One source and six live consumers retain distinct evidence and authority boundaries. |
| [F19](docs-01-discoveries.md#f19-doctor-experiment-evidence-in-workflow-readme) | Evidence placement | CI workflow README repeats a shorter Doctor experiment summary already detailed in the CV backlog. | The CV card retains detailed evidence; the workflow README repeats a summary. |
| [F20](docs-01-discoveries.md#f20-independent-golden-migration-comparisons) | Evidence placement | Independent-golden README mixes current oracle use with successive migration history. | Comparison evidence is unique beside current oracle guidance. |
| [F21](docs-01-discoveries.md#f21-coordinator-contracts-no-write-section) | Navigation candidate | Coordinator contract has a 632-line no-write section without subheadings; one owner-index link names watch selection but lands on the later Run/Results section. | Both contract sections contain distinct selection, admission, and recovery rules; no deletion inferred. |
| [F22](docs-01-discoveries.md#f22-coordinator-cross-owner-detail) | Ownership question | Coordinator, logging, runtime, and Runbook descriptions overlap across distinct trust boundaries, including request/stream names; coordinator publication and runtime seal formats are unique. | Summary overlaps coexist with unique prompt, diagnostic, and action rules. |
| [F23](docs-01-discoveries.md#f23-init-details-in-the-runbook) | Compression candidate | Baseline Runbook Init guidance mixes operator choices with hashing and file-identity internals; the approved PR slice removed 40 net lines from that section. | The generic route remains open with F05; DOCS-01 is not closed. |
| [F24](docs-01-discoveries.md#f24-named-profile-procedure-placement) | Audience question | Config guide holds a long named-profile operator procedure while Runbook routes there. | Operator command path and format ownership remain an audience question. |
| [F25](docs-01-discoveries.md#f25-reporting-decision-versus-migration-history) | Compression candidate | Reporting decision retains predecessor failure provenance and some retired-symbol inventory. | Predecessor and recovery limits are distinct; retired symbols may overlap current owners. |
| [F26](docs-01-discoveries.md#f26-alpha-carrier-note-in-reporting-readme) | Retained API guidance | Reporting README's five-line carrier note mixes a brief migration phrase with current collaborator API guidance. | Current types and positional guidance remain; isolated trimming has negligible value. |
| [F27](docs-01-discoveries.md#f27-old-fixed-resource-provenance) | Compression candidate | Resource-profile README repeats old 12-core provenance. | Current resource contract and old fixed-floor provenance have distinct roles. |
| [F28](docs-01-discoveries.md#f28-repeated-owner-boilerplate) | Compression candidate | Six stage owners and eight stage/evidence test guides repeat 58 generic physical lines. | The illustrative 31–32-line saving covers only the original 12-file stage subset; owner-specific limits remain. |
| [F29](docs-01-discoveries.md#f29-library-subowner-navigation) | Navigation mismatch | Tests point to a library index that does not route readers to six documented Python subowners. | Six documented subowners are not routed by the test index. |
| [F30](docs-01-discoveries-continued.md#f30-dashboard-reporting-stage-text) | Product-facing text | Dashboard places final target after reporting and, with a test fixture, retains three reporting operations; current target precedes two reporting operations. | Current reporting-stage and fixture wording conflicts with target order; FINAL and historical rules differ. |
| [F31](docs-01-discoveries-continued.md#f31-historical-slurm-username-recovery-advice) | Recovery wording | Troubleshooting gives an undated upgrade instruction for a Slurm username incident whose submission fix is already present. | Incident evidence remains dated; current recovery wording is unqualified. |
| [F32](docs-01-discoveries-continued.md#f32-mermaid-checks-stated-ceiling) | Evidence ceiling | Documentation guides overstate Mermaid syntax and all-file heading checks; checker covers declarations/fences and canonical H1s. | Both README claims exceed structural-check coverage. |
| [F33](docs-01-discoveries-continued.md#f33-report-receipt-version-in-the-scientist-diagram) | Diagram contradiction | Scientist diagram groups summary with HTML, names a v4 report receipt, and calls create-only reporting “read-only”; test baseline and glossary echo that ambiguity. | Summary and HTML publication are distinct; report output creation and input immutability differ. |
| [F34](docs-01-discoveries-continued.md#f34-prepared-finalization-in-the-reliability-diagram) | Diagram omission | Reliability diagram sends every resume to a new Attempt; prepared finalization may complete the old Attempt. | Prepared finalization and eligible continuation have different Attempt paths. |
| [F35](docs-01-discoveries-continued.md#f35-fastq-pairing-language) | Wording ambiguity | Glossary and engineering guide say names never infer pairing; guided Init detects R1/R2 mates from names. | Mechanical mate discovery and authored biological pairing differ. |
| [F36](docs-01-discoveries-continued.md#f36-cross-owner-history-in-runtime-test-guidance) | Placement candidate | Runtime test README ends with a sentence about retired report-publisher tests. | The runtime test guide includes retired-report history; its unique-evidence status is unverified. |
| [F37](docs-01-discoveries-continued.md#f37-bed12-dependency-in-the-scientist-diagram) | Diagram ambiguity | Combined QC/orientation node lacks RSeQC's BED12 dependency; the reference node groups produced FAI/BED12 with external FASTA/GTF. | Evidence branches do not gate downstream computation but remain required for whole-Run completion. |
| [F38](docs-01-discoveries-continued.md#f38-slurm-request-in-the-reliability-diagram) | Diagram omission | Slurm authorization is drawn as direct Attempt creation, omitting the pre-Run submission request. | Request/submission precede compute-side Run admission. |
| [F39](docs-01-discoveries-continued.md#f39-validation-roster-inventory-claim) | Evidence ceiling | Fixed map covers 14 current validation-report producers, not every validator, and cannot discover a new source producer. | Fixed-roster scope and future producer discovery have different limits. |
| [F40](docs-01-discoveries-continued.md#f40-concurrency-in-the-local-workflow-profile) | Terminology drift | Local workflow profile guide says “sample concurrency”; current policy resolves per-stage concurrency. | The guide term differs from per-stage policy. |
| [F41](docs-01-discoveries-continued.md#f41-step-05-checks-read-only-help) | Script help contradiction | Retained Step 05 check calls itself read-only while writing a TSV and directory probe. | Input immutability and output writes coexist. |
| [F42](docs-01-discoveries-continued.md#f42-report-transfer-in-the-coordinator-test-index) | Evidence placement | Coordinator test table lists report transfer but links a procedure; CV-27's tiny local exercise identifies no exact retained artifact. | The coordinator test index links a transfer procedure; CV-27 holds bounded evidence. |
| [F43](docs-01-discoveries-continued.md#f43-print-behavior-in-the-reporting-test-guide) | Evidence ceiling | Reporting test guide says it pins print behavior; checks cover CSS/HTML structure, while visual acceptance is pending. | Source-level print checks do not establish rendered review. |
| [F44](docs-01-discoveries-continued.md#f44-internal-worker-command-ownership) | Ownership terminology | Coordinator docstrings and public-CLI tests call internal workers “public”; RSeQC opening ambiguously says independently runnable. | Internal-worker and grouped-validator classifications differ from the public wording. |
| [F45](docs-01-discoveries-continued.md#f45-watch-and-stop-in-the-command-audience-map) | Reader route | Selective audience map omits public `watch` and exact-request `stop` despite their novice and operator routes. | The audience map omits watch and stop; stop retains its evidence limit. |
| [F46](docs-01-discoveries-continued.md#f46-artifact-common-schema-description) | Schema description | Common-schema description says v1 records although current records reuse its correct v1 resource identity. | Only the description appears stale; schema bytes and references remain a public contract. |
| [F47](docs-01-discoveries-continued.md#f47-r-probe-concurrency-candidate-after-cv-26) | Selection context | Optimization candidate still asks for a bounded R-probe concurrency comparison after CV-26 already measured and deferred two workers. | CV-26 already deferred two workers; new resource/cancellation authority is unselected. |
| [F48](docs-01-discoveries-continued.md#f48-project-name-lookup-from-the-repository-root) | Reader route | Root guide suggests `--project NAME_OR_PATH` outside a Project, but bare names resolve beside the current directory, not the saved Projects home. | Bare-name lookup is cwd-relative; a repository-root path is not supplied. |
| [F49](docs-01-discoveries-continued.md#f49-incomplete-allocation-recovery-command) | Recovery instruction | Troubleshooting gives only `--verbose </dev/null`; redirection also cannot neutralize `--execute`. | The fragment lacks an operation and selector; a no-write preview excludes `--execute`. |
| [F50](docs-01-discoveries-continued.md#f50-submission-request-version-in-the-coordinator-contract) | Contract wording | Coordinator inspection and stop prose describes current requests as v3, while new requests are v4 and the stop planner admits v3/v4. | Legacy observation rules and the v3-only stop-fixture limit remain distinct. |
| [F51](docs-01-discoveries-continued.md#f51-viking-walkthrough-history-in-the-active-backlog) | Evidence placement | Backlog mixes unique historical Viking observations and a former allowance with current policy; the campaign lacks exact installed/runtime bindings for a lossless transfer. | Current owner routes and dated observations have distinct authority; the inbound anchor remains. |
| [F52](docs-01-discoveries-continued.md#f52-report-regeneration-wording) | Recovery wording | Root guide and platform decision say reports can be “regenerated”; current reporting creates from empty owned state or reuses a complete bundle. | Empty-state generation and complete-bundle reuse are distinct; neither repairs a partial bundle. |
| [F53](docs-01-discoveries-continued.md#f53-dependent-project-in-shared-runtime-replacement) | Recovery instruction | Doctor diagnostics print replacement commands without a borrower selector or working-directory instruction; Troubleshooting supplies a dependent-Project cwd precondition. | Runbook's source-Project Doctor example also depends on context; current-directory selection and source admission remain separate. |
| [F54](docs-01-discoveries-continued.md#f54-analysis-reporter-return-shape) | API description | Two report guides say the analysis provider returns HTML bytes; the admitted return is a structured carrier containing bytes and provenance inputs. | The descriptions and carrier shape differ; provider behavior is unchanged. |
| [F55](docs-01-discoveries-continued.md#f55-ci-lane-selection-route) | Navigation overclaim | Workflow README says the test baseline defines each CI lane; that section gives broad categories, while exact jobs and selection live in the workflow. | Lane policy is in the baseline; exact selections are in `ci.yml`. |
| [F56](docs-01-discoveries-continued.md#f56-synthetic-driver-dependency-mutation-claim) | Mutation-scope wording | Test-tool and engineering guides imply tests do not install dependencies; the opt-in synthetic driver invokes Doctor repair, and ordinary wheel smoke installs into a temporary environment. | The two test paths have different controlled mutation scopes; neither ran in this audit. |
| [F57](docs-01-discoveries-continued.md#f57-make-fixture-public-target-label) | Audience classification | Make fixture guide calls every covered target public, while the test map includes internal lanes and operator mutations. | The fixture includes public and internal targets. |
| [F58](docs-01-discoveries-continued.md#f58-nonoverlapping-validation-lane-claim) | Protection overlap candidate | Test-tool guide and driver call four lanes non-overlapping, but Python sharding and guarded-R selection can both include the same real-R pytest file. | Selected pytest IDs may overlap despite distinct lane purposes; protection equivalence is unproven. |
| [F59](docs-01-discoveries-continued.md#f59-pre-run-submission-recovery-route) | Recovery omission | Troubleshooting's no-Run path checks an exact scheduler ID but does not route readers through the retained request roster, which can exist with no confirmed job ID. | A retained request can precede a Run or confirmed job ID; resubmission eligibility remains uncertain. |
| [F60](docs-01-discoveries-continued.md#f60-submission-request-promise-for-direct-execution) | Placement overclaim | Runbook says Run/resume/report print a submission request after approval; direct placement executes without one. | Direct placement has no submission request; Slurm retains one before Run admission. |
| [F61](docs-01-discoveries-continued.md#f61-run-summary-commit-marker-pronoun) | Publication wording | Run-summary README places “Installing it last” after the QC TSV sentence, although the summary JSON is the last installed member. | Owner code and coordinator contract both define JSON-last publication; no behavior defect observed. |
| [F62](docs-01-discoveries-third.md#f62-benchmark-value-can-be-label-only) | Benchmark evidence ceiling | Scripts guide says the helper measures commands at declared resource values; producer argv need not contain the value placeholder. | Actual resource substitution depends on manifest argv; no benchmark was run. |
| [F63](docs-01-discoveries-third.md#f63-background-cohort-in-the-scientist-diagram) | Diagram ambiguity | Scientist diagram depicts an optional background cohort entering only ranking; selected background samples traverse upstream processing. | The optional filter acts during ranking; no source behavior defect was observed. |
| [F64](docs-01-discoveries-third.md#f64-star-mechanics-in-a-scientific-decision) | Responsibility overlap | Scientific pipeline decision repeats STAR derivation/compatibility and validator mechanics in config, coordinator, and STAR-stage owners. | Original-study values, rationale, and cited manual remain distinct decision context. |
| [F65](docs-01-discoveries-third.md#f65-report-template-owner-description) | Ownership wording | Template README credits Python view builders with title, introduction, sections, and end note; the packaged template defines these elements and Python supplies values. | The discrepancy is in owner description, not observed output. |
| [F66](docs-01-discoveries-third.md#f66-step-09-qc-summary-input-scope) | Input-scope wording | Step 08/09 guides and stage map name sites and receipt only; producer and validator omit QC summary, but the Run task declares and binds it as an input. | Computational reads and Run task-input stability are different roles. |
| [F67](docs-01-discoveries-third.md#f67-step-09-producer-language-in-source-topology) | Role-label ambiguity | Source topology calls a Step 09 contract consumer “Python producer”; Python plans an R result-producing command. | The phrase may mean the planner; no ownership or behavior error is established. |
| [F68](docs-01-discoveries-third.md#f68-slurm-diagnostic-artifact-bounds) | Evidence-scope overclaim | CI guide calls uploaded Slurm diagnostics bounded and redacted; setup and terminal capture write full status and journals without those transformations. | Private accounting files are excluded; no artifact contents or disclosure were assessed. |
| [F69](docs-01-discoveries-third.md#f69-python-shard-inventory-scope) | Test-scope overclaim | Baseline and test-tool guide call shard receipts complete, but two test files are excluded from their inventory. | Ordinary CI runs them separately; scheduled or selected-only shards do not establish all-test coverage. |
| [F70](docs-01-discoveries-third.md#f70-omitted-site-does-not-always-mean-direct) | Conditional reader-route error | Runbook says omitting `--site` creates a direct profile; `EMRYS_SITE=viking` from process or saved settings makes both Init parsers select Slurm. | This does not affect the no-default case; no command was run. |
| [F71](docs-01-discoveries-third.md#f71-quickstart-projects-home-default-and-later-path) | Conditional reader-route error | Quickstart says later commands use the Projects home accepted during setup, but validation and reconnect hard-code the repository Projects path. | An inherited alternate home changes the saved destination; no command was run. |
| [F72](docs-01-discoveries-third.md#f72-automatic-reporting-scope-for-processing-only-runs) | Run-scope wording | Reporting owner README says Run/resume report automatically unless disabled; successful processing-only Runs have reporting not applicable. | The owner contract and direct fixture distinguish full from partial Runs. |
| [F73](docs-01-discoveries-third.md#f73-profile-create-explicit-placement-requirement) | Conditional CLI wording | Coordinator contract says profile creation requires explicit site or placement; the parser accepts inherited `EMRYS_SITE` as the selection. | Explicit selection remains required with no site default. |
| [F74](docs-01-discoveries-third.md#f74-final-check-command-omits-r-library-prerequisite) | Command prerequisite | Engineering guide's displayed `all-checks` command supplies Rscript but not the existing `RENV_LIBRARY` required by its guarded-R lane. | The command can pass that gate only when the library variable is already supplied. |
| [F75](docs-01-discoveries-third.md#f75-validation-lane-diagnostic-bounds) | Evidence-scope overclaim | Test baseline calls failed and cancelled lane diagnostics bounded; the validation driver retains complete logs and prints complete failed logs. | No lane or log content was observed; distinct from Slurm artifact F68. |
| [F76](docs-01-discoveries-third.md#f76-step-07-dataset-promotion-route) | Authority-route overclaim | Step 07 test guide says the linked stage contract owns dataset-promotion criteria, but that contract states no such criteria. | The finding concerns a reader route, not Step 07 behavior. |
| [F77](docs-01-discoveries-third.md#f77-omitted-application-model-test-suite) | Test-index omission | Orchestration contract test README names two suites but omits the present Analysis/Plan/Run application-model suite. | The tests exist; no result or coverage level is inferred. |
| [F78](docs-01-discoveries-third.md#f78-omitted-python-shard-duration-baseline) | Baseline-index omission | Test-baselines README describes only the coverage snapshot; the adjacent duration baseline actively weights Python shards. | The duration values are scheduling estimates, not test outcomes or coverage. |
| [F79](docs-01-discoveries-third.md#f79-shared-fixture-consumer-count) | Current-use question | Shared-fixtures README says tracked inputs serve multiple test owners; its sole tracked data fixture is referenced by one cross-entrypoint test module. | One module can cover multiple owners, so a consumer-count contradiction is unproven. |
| [F80](docs-01-discoveries-third.md#f80-alignment-helper-tool-boundary) | Owner-boundary wording | Alignment-library README says its parsers run no scientific tools; the BAM helper executes supplied `samtools` checks for stage validators. | The observed calls are read-only validation checks; no output publication is inferred. |
| [F81](docs-01-discoveries-third.md#f81-terminal-task-result-versus-verified-marker) | Evidence overclaim | Orchestration index assigns every task a terminal result and verified marker; failed tasks can retain a terminal result without a marker, and interruption can leave neither. | Marker publication remains success-gated; no behavior defect is inferred. |
| [F82](docs-01-discoveries-third.md#f82-reference-provenance-private-test-calls) | Test-scope wording | Reference-provenance test guide says private reconciler calls only inject failures; the suite also calls parsing, rendering, and publication directly. | Direct private coverage and public-command coverage remain distinct; tests were not run. |
| [F83](docs-01-discoveries-third.md#f83-direct-host-study-versus-allocation-only-rule) | Policy-route conflict | Runbook offers an own-data full Run on a non-Slurm host without limiting heavy work, while the safety guard and delivery decision reserve it for whole-Run Slurm allocations. | Direct placement and tiny fixtures remain supported; no direct or institutional Run was exercised. |
| [F84](docs-01-discoveries-third.md#f84-copied-init-manifest-path-fields) | Conditional copy wording | Config guide says named Init copies and retains supplied manifest content; Init resolves relative FASTQ and regions-file paths to absolute paths when publishing the Project manifests. | The path referents are retained, but the persisted path fields can differ; no Run was executed. |
| [F85](docs-01-discoveries-third.md#f85-status-vocabulary-exceptions) | Status vocabulary | Main matrix defines six states, but `REPORT-ROSTER-01` uses `Needs decision`; the delegated CV index labels CV-12 `Discard` under Status. | CV-12 has an explicit terminal disposition; neither decision nor acceptance is reopened. |
| [F86](docs-01-discoveries-third.md#f86-step-02b-parallel-validation-claim) | Execution-order wording | Step 02b contract says it may overlap Step 02 validation; the Run graph waits for the corresponding sample's Step 02 verified marker. | Different samples may overlap; no Run was executed. |
| [F87](docs-01-discoveries-third.md#f87-step-05-scratch-owner-in-optimization-candidate) | Dismissed after recheck | The optimization candidate's historical worker link and current runner both support output-adjacent GATK scratch; its prose does not assign ownership to the worker. | No current documentation error or saving is established; performance remains unmeasured. |
| [F88](docs-01-discoveries-third.md#f88-old-slurm-memory-preflight-proposal) | Prior-revision proposal | Polish item 36 calls explicit Slurm memory preflight missing; current `SCHED-01` records the implemented check with verification still pending. | The institutional heterogeneous-node limit remains open; no new software proof is inferred. |
| [F89](docs-01-discoveries-third.md#f89-one-run-wording-before-run-creation) | Operator precondition ambiguity | Runbook says a ready Project has one Run immediately before `emrys run`; the command plans a new Run and refuses an existing Run with Attempts. | A pristine committed Run without an Attempt is a narrow exception; no command was exercised. |
| [F90](docs-01-discoveries-third.md#f90-completed-tooling-history-in-polish-campaign) | Compression candidate | Five completed polish sections repeat `CI-01`, `DEV-01`, and `CLI-VERSION-01` status and hosted-CI genealogy already recorded in the main matrix. | Their 77 physical lines include unique fixes, measurements, and evidence limits; 77 is not an estimated saving. |
| [F91](docs-01-discoveries-third.md#f91-repeated-stage-and-evidence-contract-openings) | Compression candidate | Twelve stage/evidence contract openings use 48 lines to restate aliases and stage-map ownership alongside distinct local command roles. | Only an illustrative 12–24-line net opportunity remains after local roles; no edit or saving was verified. |
| [F92](docs-01-discoveries-third.md#f92-python-lock-checks-before-institutional-r-restoration) | Audience and prerequisite question | Runbook places Python lock checks before institutional R restoration; developer guidance owns similar checks, while the shown R Make targets do not invoke uv. | Whether this is an independent operator gate remains unverified; the R procedure is unique. |
| [F93](docs-01-discoveries-third.md#f93-repeated-partition-selector-rule) | Small duplication | Config guide twice states that `--region` and `--regions-file` can combine only with unique partition IDs. | The intervening coordinate examples and separate manifest exclusions remain distinct. |
| [F94](docs-01-discoveries-third.md#f94-dashboard-retirement-closeout-tense) | Temporal framing | A PR #169 closeout paragraph says the dashboard remains; a later row records retirement of the standalone wrapper after installed watch acceptance. | The older checkpoint and remaining CI/visual verification have distinct dates and meanings. |
| [F95](docs-01-discoveries-third.md#f95-executed-stop-missing-from-logging-adopter-roster) | Owner-index omission | Source topology calls its logging-adopter roster complete but omits executed `stop`, which opens a maintenance attempt after admission. | Terminal targets and previews open no log; admitted execution opens one. |
| [F96](docs-01-discoveries-third.md#f96-unrouted-artifact-schema-version-notes) | Navigation and compression question | Artifact schema index links current JSON schemas, while four adjacent version READMEs have no inbound Markdown route. | Their 32 lines overlap the index but retain unique compatibility, identity, and evidence limits; no saving is established. |
| [F97](docs-01-discoveries-third.md#f97-past-audit-priority-order-in-polish-campaign) | Historical selection order | Polish campaign keeps nine lines of second/third-pass priorities whose proposals and accepted status are recorded elsewhere. | Nine lines are a review surface; measurement prerequisites and dated decisions remain distinct. |
| [F98](docs-01-discoveries-third.md#f98-worker-prerequisites-inside-validation-sections) | Contract placement | Step 00c and Step 05 validation sections repeat Java/GATK/hash-launcher prerequisites used by internal workers, not their grouped validators. | Worker policy and validator input/evidence limits remain distinct. |
| [F99](docs-01-discoveries-third.md#f99-stage-data-inputs-versus-run-gates) | Execution-order wording | Step 01 calls STAR logs and the SJ table non-prerequisites for Step 02; Step 07 calls Step 06 validation and its marker non-prerequisites. The admitted Run waits for each predecessor's verified marker before starting the next stage. | Worker data inputs and Run scheduling differ; no runtime defect is inferred. |
| [F100](docs-01-discoveries-fourth.md#f100-gtf-worker-detail-in-the-coordinator-contract) | Owner-detail overlap | Coordinator runner section repeats the GTF worker's shared-normalization fact already in its stage contract. | Runner publication and recovery rules remain distinct; no saving established. |
| [F101](docs-01-discoveries-fourth.md#f101-retired-reporting-memory-recovery-advice-in-the-contract) | Audience placement | Coordinator contract alone names exact retired-field removal advice; profile guide gives only a generic retired-setting warning. | Rejection behavior is current owner detail; the old control's effectiveness was not replayed. |
| [F102](docs-01-discoveries-fourth.md#f102-historical-e09-example-in-current-lifecycle-rules) | Evidence placement | Lifecycle contract names the historical E09 Run after stating its generic missing-evidence rule; the CV register and card retain E09. | E09 cause and old-Run recovery remain unverified; current eligibility is distinct. |
| [F103](docs-01-discoveries-fourth.md#f103-unpublished-fastq-experiment-in-the-owner-guide) | Historical owner detail | Sample-manifest guide mixes current helper limits with a described unpublished `awk` draft, exact NUL-header counterexample, and logical-pass count. | The direct test module has no NUL case; no measured I/O, deletable span, or saving established. |
| [F104](docs-01-discoveries-fourth.md#f104-automatic-reports-after-successful-computation) | Operator wording | Runbook says successful computation generates both reports; full Runs invoke reporting by default, but science can complete while reporting is incomplete. | Quickstart and Runbook require separate reporting admission; no behavior defect inferred. |
| [F105](docs-01-discoveries-fourth.md#f105-retired-scheduler-wrapper-in-the-stage-map) | Historical graph explanation | Stage map combines a retired Step 00a wrapper explanation with durable current no-edge semantics for 00b/00c. | No scheduling behavior or safe saving was established. |
| [F106](docs-01-discoveries-fourth.md#f106-doctor-storage-plan-proposal-after-slurm-routing-changed) | Stale proposal framing | Polish item 9 describes direct storage planning and a direct-profile workaround for Slurm; current Doctor source and Viking Runbook route differ. | Dated concern survives, but no Doctor run or institutional proof was established. |
| [F107](docs-01-discoveries-fourth.md#f107-retired-shell-publication-tests-in-a-current-test-guide) | Historical test detail | Shared-library test guide narrates retired shell-publisher faults and links a retained Git revision beside current runner coverage. | Original characterization is unique evidence; current test equivalence and saving unverified. |
| [F108](docs-01-discoveries-fourth.md#f108-scientific-completion-in-the-run-summary-guide) | Terminology ambiguity | Run-summary guide calls scientific completion external, while inspection and architecture define computational Scientific Results completion. | External review and biological interpretation remain distinct; no behavior defect inferred. |
| [F109](docs-01-discoveries-fourth.md#f109-runtime-discoverys-interactive-publication) | No-write wording | Runtime owner guide says discovery without `--execute` does not write; affirmative terminal confirmation publishes, as source and direct fixture show. | Declined or noninteractive previews remain no-write; no runtime command ran in the audit. |
| [F110](docs-01-discoveries-fourth.md#f110-unrouted-study-pairs-configuration-file) | Configuration inventory | Tracked three-column EV/PUM1 pairing roster is unindexed, with no pre-audit reader or caller reference found; current Step 09 uses the six-column sample manifest. | Historical use is unverified; neither deletion nor current Step 09 admission is inferred. |
| [F111](docs-01-discoveries-fourth.md#f111-current-resource-claim-with-old-profile-citations) | Citation provenance | Optimization campaign describes current allocation-aware defaults but links to the fixed-policy profiles from its older audit revision. | Old links remain valid historical citations; no resource performance or runtime result was inferred. |
| [F112](docs-01-discoveries-fourth.md#f112-r-environment-checks-report-support-claim) | Check-scope overclaim | Scripts index says the R environment checker verifies report support; it checks R dependencies and a headless PDF device, not current HTML report rendering. | PDF readiness is relevant to Step 09 scientific outputs; no report failure or runtime result is inferred. |
| [F113](docs-01-discoveries-fourth.md#f113-cv-26-mixed-current-rules-and-measurement-history) | Evidence placement | CV-26's 309-line card mixes open acceptance, current Doctor rules, repeated checkpoint status, and four distinct hosted measurement blocks. | Current rules have an owner and status has a delegated card; unique measurements, failed-suite limits, and operator report remain evidence. No saving is established. |

## Discovery notes

The [first discovery notes](docs-01-discoveries.md),
[continued notes](docs-01-discoveries-continued.md),
[third file](docs-01-discoveries-third.md), and
[fourth file](docs-01-discoveries-fourth.md) give sources, uncertainty, and
preservation boundaries for every matrix row. The temporary split keeps each
document below the 600-line review threshold.

## Preservation boundaries for the next pass

The CV campaign's E01–E12 evidence register, CV-26 measurements, the
optimization campaign's measured PR #45 experiment, the validation-evidence
compendium, the workflow Doctor experiment, and independent-golden migration
comparisons are retained support for bounded claims. Their placement can be
reviewed, but shortening or moving adjacent guidance has an evidence-retention
boundary. The [CV backlog](cluster_verification_backlog.md) also retains
an original-note crosswalk near its end. The [FASTQ admission owner](../../src/emrys/ingestion/sample_manifest_admission/README.md)
preserves a NUL-byte header counterexample from an unpublished helper rewrite;
the optimization campaign relies on that accepted-input boundary, and this
pass found no direct NUL regression fixture. Its provenance and accepted-input
boundary remain relevant to this audit. Concise current surfaces, including the
root CI index and schema README hierarchy, need no change merely because they
were audited.

The 14 grouped-validator contracts retain distinct producer and validator
boundaries. For example, canonical BAM QC accepts a nonempty zero-exit
quickcheck as producer evidence while its validator rejects it; FASTA sidecar
production permits unordered contig pairs while validation requires order.
The canonical BAM, partitioned mpileup, and candidate-preprocessing contracts
also record exact recovery or evidence limits. Those limits and owner-local
check IDs distinguish them from redundant prose.

The Runbook's report-opening summary and terminal-transfer procedure repeat
eligibility and complete-tree language, but the latter adds exact selection
and a warning against copying during publication. Troubleshooting repeats
the coordinator's trusted-workspace limit where a recovery reader needs it.
The Quickstart output table repeats owner rosters but supplies first-time
navigation through copied Results. These overlaps alone establish no safe
reduction. Polish items 29–30 retain external-provider and release evidence
boundaries that the accepted `EXTENSION-01` and `RELEASE-01` rows summarize.
The test-tool guide overlaps CV-01's selected journey but uniquely states
request-token stream matching and its guarded emergency-cancellation limit;
those current driver rules have no demonstrated net reduction.
CV-10's nearby remaining-acceptance rows repeat prepared-finalization status
but retain different exact-hosted, site, and blocked-state limits. Reporting
publication summaries recur at the reporting index and private package owners,
yet their transaction members, reuse rules, and original-Run attribution differ;
neither overlap supplies a defensible deletion on this pass.
