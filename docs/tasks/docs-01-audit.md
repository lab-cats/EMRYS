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
| [F01](docs-01-discoveries.md#f01-public-stop-in-the-platform-decision) | Contradiction | Platform decision denies public stop and limits resume to failed/interrupted Runs; exact-request stop and prepared finalization exist. | Reconcile both decision claims and stale v3-only stop wording; preserve CV-18 evidence limits. |
| [F02](docs-01-discoveries.md#f02-standalone-resource-floor) | Contradiction | Runbook gives a fixed 12-CPU/240-GiB standalone floor; defaults resolve against capacity and reject unmet task minima. | Correct the fixed policy claim while retaining real-study capacity cautions. |
| [F03](docs-01-discoveries.md#f03-init-02-in-cluster-summaries) | Summary overclaim | Grouped CV summaries call INIT-01–03 source-complete while INIT-02 remains Open; detailed cards describe explicit manifest selection. | Narrow the summary without erasing explicit-manifest proof or dated cards. |
| [F04](docs-01-discoveries.md#f04-root-quickstart-description) | Reader route | Root README calls Quickstart a synthetic first Run; Quickstart leads with real EV/PUM1 and makes smoke optional. | Name the selected real-study journey and retain the optional smoke route. |
| [F05](docs-01-discoveries.md#f05-generic-study-versus-named-evpum1-route) | Reader route | At baseline, two “own study” Runbook routes point into fixed EV/PUM1 choices. At PR head `0cb5d507`, the choice route is clearer, but the Quickstart continuation still uses the named Project and Slurm. | Keep the current-head generic reader route open; no usage outcome is established. |
| [F06](docs-01-discoveries.md#f06-existing-project-and-new-project-recovery) | Reader route | Troubleshooting mixes existing-Project lookup with absent-child Init recovery. | Give lookup and new creation distinct preconditions and recovery. |
| [F07](docs-01-discoveries.md#f07-doctor-repair-does-not-always-install) | Contradiction | Guides imply Doctor always installs and the decision assigns it uv; verified Slurm plans can skip package work while still submitting checks. | Separate managed package work, preview, and confirmed verification effects. |
| [F08](docs-01-discoveries.md#f08---version-and-local-env) | Source-ordering limit | Runbook promises `--version` from any directory; malformed marked `.env` is rejected before version dispatch. | Keep the source inference distinct from an unrun installed-command case. |
| [F09](docs-01-discoveries.md#f09-runbook-entry-order) | Reader route | Advanced request/watch/stop procedures precede Runbook orientation. | Test whether moving the orientation improves entry without hiding recovery commands. |
| [F10](docs-01-discoveries.md#f10-contract-location-claim) | Filename overclaim | Two global indexes imply an adjacent `CONTRACT.md` for every component; many README locations use another contract form. | Fix the two global routes; retain the accurate stage-owner claim. |
| [F11](docs-01-discoveries.md#f11-python-hook-scope) | Contradiction | Engineering guide omits root `setup.py` from hook scope. | Align the guide with `.pre-commit-config.yaml`. |
| [F12](docs-01-discoveries.md#f12-init-preview-proposal) | Prior-revision proposal | Polish campaign's dated audit says Init preview shows only destination and directories; normal preview now shows scientific values. | Compare remaining requested fields and preview/publication protection. |
| [F13](docs-01-discoveries.md#f13-doctor-profile-proposal) | Prior-revision proposal | Polish campaign's dated audit says Doctor has no `--profile`; the public option now exists. | Reconcile proposal with accepted work and tests. |
| [F14](docs-01-discoveries.md#f14-old-source-attestation-cost-candidate) | Recheck candidate | Old optimization Git-call finding counts a prior revision's source calls, not necessarily current execution. | Re-evaluate the current source before selecting optimization work. |
| [F15](docs-01-discoveries.md#f15-cv-u22-interim-status-prose) | Preserve chronology | CV-U22's dated checkpoints explain why the card returned to Open; compression has no demonstrated benefit yet. | Keep the causal record unless a concrete reader conflict is found. |
| [F16](docs-01-discoveries.md#f16-polish-merged-pr-tables) | Compression candidate | Polish campaign repeats merged-PR chronology in two tables; the first retains unique slice mappings. | Crosswalk unique mappings before compressing routine genealogy. |
| [F17](docs-01-discoveries.md#f17-main-backlog-chronology-and-run-repetition) | Preserve row evidence | One hosted run supports three distinct backlog rows; repeated row-local citations may be warranted. | Check only routine genealogy for safe compression. |
| [F18](docs-01-discoveries.md#f18-history-filing-rule-and-existing-compendium) | Evidence placement | Undated seven-topic compendium was appended after creation; a prior dated PORT record and unique ARCH-CLOSE limits remain in Git, while several run dates remain unknown. | Preserve each source and six live consumers before deciding legacy exception or dated records. |
| [F19](docs-01-discoveries.md#f19-doctor-experiment-evidence-in-workflow-readme) | Evidence placement | CI workflow README repeats a shorter Doctor experiment summary already detailed in the CV backlog. | Use the CV card as evidence source before considering a history transfer. |
| [F20](docs-01-discoveries.md#f20-independent-golden-migration-comparisons) | Evidence placement | Independent-golden README mixes current oracle use with successive migration history. | Preserve comparison evidence before shortening owner instructions. |
| [F21](docs-01-discoveries.md#f21-coordinator-contracts-no-write-section) | Navigation candidate | Coordinator contract has a 632-line no-write section without subheadings; one owner-index link names watch selection but lands on the later Run/Results section. | Account for both contract sections when tracing selection, admission, and recovery; no deletion inferred. |
| [F22](docs-01-discoveries.md#f22-coordinator-cross-owner-detail) | Ownership question | Coordinator, logging, runtime, and Runbook descriptions overlap but have different trust boundaries, including narrow styling and watch-key repeats. | Distinguish repeated summaries from unique prompt, diagnostic, and action rules. |
| [F23](docs-01-discoveries.md#f23-init-details-in-the-runbook) | Compression candidate | Baseline Runbook Init guidance mixes operator choices with hashing and file-identity internals; the PR head removes 40 net lines from that section. | Check the current-head reader route with F05; the audit does not close DOCS-01. |
| [F24](docs-01-discoveries.md#f24-named-profile-procedure-placement) | Audience question | Config guide holds a long named-profile operator procedure while Runbook routes there. | Decide whether Runbook needs a concise command path and config guide the format. |
| [F25](docs-01-discoveries.md#f25-reporting-decision-versus-migration-history) | Compression candidate | Reporting decision retains predecessor failure provenance and some retired-symbol inventory. | Preserve predecessor and recovery limits; compare narrow symbol inventory with current owners. |
| [F26](docs-01-discoveries.md#f26-alpha-carrier-note-in-reporting-readme) | Preserve API guidance | Reporting README's five-line carrier note mixes a brief migration phrase with current collaborator API guidance. | Retain current types and positional guidance; isolated trimming has negligible value. |
| [F27](docs-01-discoveries.md#f27-old-fixed-resource-provenance) | Compression candidate | Resource-profile README repeats old 12-core provenance. | Retain current resource contract and historical evidence at their owners. |
| [F28](docs-01-discoveries.md#f28-repeated-owner-boilerplate) | Compression candidate | Six stage owners and their tests repeat 48 generic lines. | Evaluate a roughly 31–32-line net reduction while retaining commands and owner-specific limits. |
| [F29](docs-01-discoveries.md#f29-library-subowner-navigation) | Navigation mismatch | Tests point to a library index that does not route readers to six documented Python subowners. | Add a concise subowner route without copying contracts. |
| [F30](docs-01-discoveries-continued.md#f30-dashboard-reporting-stage-text) | Product-facing text | Dashboard places final target after reporting and, with a test fixture, retains three reporting operations; current target precedes two reporting operations. | Correct explanations and fixture while preserving FINAL and historical rule mapping. |
| [F31](docs-01-discoveries-continued.md#f31-historical-slurm-username-recovery-advice) | Recovery wording | Troubleshooting gives an undated upgrade instruction for a Slurm username incident whose submission fix is already present. | Preserve incident evidence and give current-version diagnosis. |
| [F32](docs-01-discoveries-continued.md#f32-mermaid-checks-stated-ceiling) | Evidence ceiling | Documentation guides overstate Mermaid syntax and all-file heading checks; checker covers declarations/fences and canonical H1s. | Narrow both READMEs to the actual structural checks. |
| [F33](docs-01-discoveries-continued.md#f33-report-receipt-version-in-the-scientist-diagram) | Diagram contradiction | Scientist diagram groups summary with HTML, names a v4 report receipt, and calls create-only reporting “read-only”; test baseline echoes that ambiguity. | Separate summary and HTML publication and distinguish input immutability from new outputs. |
| [F34](docs-01-discoveries-continued.md#f34-prepared-finalization-in-the-reliability-diagram) | Diagram omission | Reliability diagram sends every resume to a new Attempt; prepared finalization may complete the old Attempt. | Show finalization and eligible continuation as distinct paths. |
| [F35](docs-01-discoveries-continued.md#f35-fastq-pairing-language) | Wording ambiguity | Glossary and engineering guide say names never infer pairing; guided Init detects R1/R2 mates from names. | Distinguish mate discovery from authored biological pairing. |
| [F36](docs-01-discoveries-continued.md#f36-cross-owner-history-in-runtime-test-guidance) | Placement candidate | Runtime test README ends with a sentence about retired report-publisher tests. | Check whether that history belongs with reporting evidence, then keep this README to runtime test scope. |
| [F37](docs-01-discoveries-continued.md#f37-bed12-dependency-in-the-scientist-diagram) | Diagram ambiguity | Combined QC/orientation node lacks RSeQC's BED12 dependency; the upstream reference node also groups produced FAI/BED12 with external FASTA/GTF. | Stage map defines the artifact edges; no execution defect was observed. |
| [F38](docs-01-discoveries-continued.md#f38-slurm-request-in-the-reliability-diagram) | Diagram omission | Slurm authorization is drawn as direct Attempt creation, omitting the pre-Run submission request. | Show request/submission and compute-side admission separately. |
| [F39](docs-01-discoveries-continued.md#f39-validation-roster-inventory-claim) | Evidence ceiling | Fixed map covers 14 current validation-report producers, not every validator, and cannot discover a new source producer. | Name scope and future-discovery limit; preserve literal rosters and owner checks. |
| [F40](docs-01-discoveries-continued.md#f40-concurrency-in-the-local-workflow-profile) | Terminology drift | Local workflow profile guide says “sample concurrency”; current policy resolves per-stage concurrency. | Align wording with resource schema and policy. |
| [F41](docs-01-discoveries-continued.md#f41-step-05-checks-read-only-help) | Script help contradiction | Retained Step 05 check calls itself read-only while writing a TSV and directory probe. | State input immutability and output mutation precisely. |
| [F42](docs-01-discoveries-continued.md#f42-report-transfer-in-the-coordinator-test-index) | Evidence placement | Coordinator test table lists report transfer but links a procedure; CV-27's tiny local exercise identifies no exact retained artifact. | Keep the test section anchor and route transfer evidence to CV-27 outside test claims. |
| [F43](docs-01-discoveries-continued.md#f43-print-behavior-in-the-reporting-test-guide) | Evidence ceiling | Reporting test guide says it pins print behavior; checks cover CSS/HTML structure, while visual acceptance is pending. | Name source-level print checks without implying rendered review. |
| [F44](docs-01-discoveries-continued.md#f44-internal-worker-command-ownership) | Ownership terminology | Coordinator docstrings and public-CLI tests call internal workers “public”; RSeQC opening ambiguously says independently runnable. | Clarify command and test classification; retain worker help, modes, and grouped validators. |
| [F45](docs-01-discoveries-continued.md#f45-watch-and-stop-in-the-command-audience-map) | Reader route | Selective audience map omits public `watch` and exact-request `stop` despite their novice and operator routes. | Add those audience examples with stop's evidence limit. |
| [F46](docs-01-discoveries-continued.md#f46-artifact-common-schema-description) | Schema description | Common-schema description says v1 records although current records reuse its correct v1 resource identity. | Review schema-byte compatibility; change only description, not `$id` or references. |
| [F47](docs-01-discoveries-continued.md#f47-r-probe-concurrency-candidate-after-cv-26) | Selection context | Optimization candidate still asks for a bounded R-probe concurrency comparison after CV-26 already measured and deferred two workers. | Bind any future proposal to CV-26's disposition and new resource/cancellation authority. |
| [F48](docs-01-discoveries-continued.md#f48-project-name-lookup-from-the-repository-root) | Reader route | Root guide suggests `--project NAME_OR_PATH` outside a Project, but bare names resolve beside the current directory, not the saved Projects home. | Give a path from the repository root or an absolute Project path. |
| [F49](docs-01-discoveries-continued.md#f49-incomplete-allocation-recovery-command) | Recovery instruction | Troubleshooting gives only `--verbose </dev/null`; redirection also cannot neutralize `--execute`. | Name the failed operation and a complete preview without `--execute`. |
| [F50](docs-01-discoveries-continued.md#f50-submission-request-version-in-the-coordinator-contract) | Contract wording | Coordinator inspection prose describes selected requests as v2/v3 and new requests as v3 while current requests are v4. | Name current v4 and preserve exact v2/v3 compatibility rules. |
| [F51](docs-01-discoveries-continued.md#f51-viking-walkthrough-history-in-the-active-backlog) | Evidence placement | Backlog mixes unique historical Viking observations and a former allowance with current policy; the campaign lacks exact installed/runtime bindings for a lossless transfer. | Keep current owner routes, historical attribution, acceptance authority, and inbound anchor distinct. |
| [F52](docs-01-discoveries-continued.md#f52-report-regeneration-wording) | Recovery wording | Root guide and platform decision say reports can be “regenerated”; current reporting creates from empty owned state or reuses a complete bundle. | Clarify generation versus reuse without implying partial-bundle repair or overwrite. |
| [F53](docs-01-discoveries-continued.md#f53-dependent-project-in-shared-runtime-replacement) | Recovery instruction | Troubleshooting replacement commands omit the borrower selector; the adjacent Runbook names an unqualified source-Project Doctor command. | Show exact borrower and source Project selection while preserving preview and admission checks. |
| [F54](docs-01-discoveries-continued.md#f54-analysis-reporter-return-shape) | API description | Two report guides say the analysis provider returns HTML bytes; the admitted return is a structured carrier containing bytes and provenance inputs. | Compare both descriptions with `AnalysisScientificReportV1`; provider behavior is unchanged. |
| [F55](docs-01-discoveries-continued.md#f55-ci-lane-selection-route) | Navigation overclaim | Workflow README says the test baseline defines each CI lane; that section gives broad categories, while exact jobs and selection live in the workflow. | Route precise lane selection to `ci.yml` and retain the baseline's evidence ceiling. |
| [F56](docs-01-discoveries-continued.md#f56-synthetic-driver-dependency-mutation-claim) | Mutation-scope wording | Test-tool and engineering guides imply tests do not install dependencies; the opt-in synthetic driver invokes confirmed Doctor repair in each disposable Project. | Ordinary tests and opt-in Doctor repair have different mutation scopes; no installation was observed. |
| [F57](docs-01-discoveries-continued.md#f57-make-fixture-public-target-label) | Audience classification | Make fixture guide calls every covered target public, while the test map includes internal lanes and operator mutations. | Name the complete target-expansion inventory and preserve applicability classes. |
| [F58](docs-01-discoveries-continued.md#f58-nonoverlapping-validation-lane-claim) | Protection overlap candidate | Test-tool guide and driver call four lanes non-overlapping, but Python sharding and guarded-R selection can both include the same real-R pytest file. | Narrow the claim; route any gate deduplication to ASSURANCE-01 with surviving protection proof. |
| [F59](docs-01-discoveries-continued.md#f59-pre-run-submission-recovery-route) | Recovery omission | Troubleshooting's no-Run path checks an exact scheduler ID but does not route readers through the retained request roster, which can exist with no confirmed job ID. | Inspect the request before resubmission and preserve unknown/partial observations. |
| [F60](docs-01-discoveries-continued.md#f60-submission-request-promise-for-direct-execution) | Placement overclaim | Runbook says Run/resume/report print a submission request after approval; direct placement executes without one. | Scope that promise to Slurm submissions while preserving pre-Run request retention. |
| [F61](docs-01-discoveries-continued.md#f61-run-summary-commit-marker-pronoun) | Publication wording | Run-summary README places “Installing it last” after the QC TSV sentence, although the summary JSON is the last installed member. | Owner code and coordinator contract both define JSON-last publication; no behavior defect observed. |
| [F62](docs-01-discoveries-third.md#f62-benchmark-value-can-be-label-only) | Benchmark evidence ceiling | Scripts guide says the helper measures commands at declared resource values; producer argv need not contain the value placeholder. | Actual resource substitution depends on manifest argv; no benchmark was run. |
| [F63](docs-01-discoveries-third.md#f63-background-cohort-in-the-scientist-diagram) | Diagram ambiguity | Scientist diagram depicts an optional background cohort entering only ranking; selected background samples traverse upstream processing. | The optional filter acts during ranking; no source behavior defect was observed. |
| [F64](docs-01-discoveries-third.md#f64-star-mechanics-in-a-scientific-decision) | Responsibility overlap | Scientific pipeline decision repeats STAR derivation and compatibility mechanics in config and coordinator owners. | Original-study values, rationale, and cited manual remain distinct decision context. |

## Discovery notes

The [first discovery notes](docs-01-discoveries.md) and
[continued notes](docs-01-discoveries-continued.md), plus the
[third file](docs-01-discoveries-third.md), give sources, uncertainty, and
preservation boundaries for every matrix row. The temporary split keeps each
document below the 600-line review threshold.

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
