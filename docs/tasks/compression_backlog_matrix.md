# EMRYS temporary compression backlog

Reviewed **2026-09-09** from `abf47b77`. The [campaign](compression_campaign.md)
owns the goals; this file owns CS scope, status, decisions, and proof. The
[main matrix](backlog_matrix.md) owns broader outcomes and campaign completion.

## Working queue

**Current work: [PR #155](https://github.com/lab-cats/EMRYS/pull/155), CS-18 runner-owned scientific execution; implemented, awaiting hosted CI.**
The user approved moving working paths, locks, process supervision, logging,
publication, and recovery into the existing runner. Producers retain scientific
computation, outputs, and provenance; there is no separate manager hierarchy.

[PR #154](https://github.com/lab-cats/EMRYS/pull/154) combines artifact indexing and
summary generation (CS-03). Focused checks and [ordinary hosted CI](https://github.com/lab-cats/EMRYS/actions/runs/34372748153)
pass at `88522d0a`; integration remains pending.

[PR #153](https://github.com/lab-cats/EMRYS/pull/153) delivers shared processing definitions and standalone publication.
The implemented tranche covers CS-01/02 and CS-18, including CS-10's CMH
replacement retirement. It uses the existing processing profile as the shared
source of task, dependency, and artifact facts. New Run admission rejects a
processing graph that disagrees with the supported graph; existing Run records
and resume retain their original interpretation and identity checks.

At PR #153, mpileup, preprocessing, paired CMH, and scientific-context producers refused
existing destinations even without `--no-clobber`; the flag remained accepted.
Replacement/backup creation and restoration were removed while preserving exclusive
publication, input checks, owned-output rollback, and old recovery files. This
approved policy replaces the rejected behavior-preserving helper prototype.
PR #155 supersedes those standalone interfaces with runner-required execution.
CS-05 remains excluded; the dashboard remains until its replacement is validated.
PR #153's first final-state CI exposed one historical-reader test still patching
the retired producer registry. `cab77a26` migrates that test to the shared owner;
its focused check and [replacement hosted CI](https://github.com/lab-cats/EMRYS/actions/runs/34370002882)
pass. CS-01/02/10 are Done; the larger runner migration remains under CS-18.

[PR #152](https://github.com/lab-cats/EMRYS/pull/152) delivered report-table and
R-table compression plus supporting planning/admission cleanup. Its first CI
run passed the R fixtures and managed golden path but failed one assertion
expecting the old dispatch diagnostic. The invalid log path remained rejected.
Commit `72fdf806` corrects that assertion; both focused dispatch checks pass.
[Final-commit CI](https://github.com/lab-cats/EMRYS/actions/runs/34361428680)
passed all ordinary checks at `72fdf806`; master integration remains pending.

CS-16/17 are Done in PR #151 at `76acb9c5`, with all ordinary checks passing in
[run 34314490868](https://github.com/lab-cats/EMRYS/actions/runs/34314490868).
Master integration remains pending.

CS-04/06/07 passed ordinary hosted CI in [PR #150](https://github.com/lab-cats/EMRYS/pull/150)
at `f3a3966f`: [run 34310143034](https://github.com/lab-cats/EMRYS/actions/runs/34310143034).
CS-03 subsequently passed CI in PR #154. PR #150 awaits integration; hosted software checks do not
establish institutional operation, scientific review, or biological validity.

### Status and scoring

- **Needs qualification:** identify equivalent production behavior and a
  caller-complete negative draft; close as Retained if none exists.
- **Needs decision:** the exact unresolved policy is stated in the card;
  dependent implementation stops until it is resolved.
- **Blocked:** a named predecessor or replacement must satisfy its gate.
- **Opportunistic:** bounded but too small to lead a substantial tranche.
- **Deferred:** a stated trigger must occur before reopening the work.
- After approval use **Ready**, **In progress**, **Verification pending**, then
  **Done**, or close as **Retained**, **Rejected**, or **Transferred** with a
  reason and destination. Code written is not verification complete. Record
  the PR, tested commit, and evidence level when changing implementation status.

Importance and Complexity run from 1 (low) to 5 (high), independently. They
estimate remaining value and effort/risk, including compatibility and proof;
they are rough selection aids, not measured benefit or implementation approval.

| ID | Finite outcome / production owner | Status | Importance | Complexity | Next action / dependency | Parent |
|---|---|---|---:|---:|---|---|
| [CS-01](#cs-01-processing-materialization) | Derive one processing owner's command and dispatch from existing admitted facts. | Done | 4 | 4 | PR #153: shared profile facts drive planning, named rules, and reporting; focused/differential checks and ordinary hosted CI pass at cab77a26. | `COMPRESS-01` |
| [CS-02](#cs-02-processing-report-adapters) | Remove equivalent processing-adapter declarations from artifact-index reporting. | Done | 4 | 4 | PR #153: all 42 processing adapters and 12 producer paths migrated; reader parity and ordinary hosted CI pass at cab77a26. | `REPORT-ROSTER-01` |
| [CS-03](#cs-03-reporting-transaction-layout) | Publish artifact indexing and summary generation as one operation. | Done | 4 | 4 | PR #154 implemented generation, readers, and inspection; focused/static and ordinary hosted CI pass at 88522d0a. HTML stays separate; integration is pending. | `REPORT-ROSTER-01` |
| [CS-04](#cs-04-reporting-memory-control) | Remove the ineffective active reporting-memory control and its transport. | Done | 3 | 4 | PR #150: new inputs rejected, historical records/hashes preserved; focused and ordinary hosted checks passed. | `REPORT-ROSTER-01` |
| [CS-05](#cs-05-validation-check-rosters) | Give one scientific validation roster one neutral authority used by its producer and reporting. | Needs decision | 4 | 4 | Select membership/order, historical records, and external-provider obligations. | `REPORT-ROSTER-01` |
| [CS-06](#cs-06-publication-handoff) | Characterize the helper-to-caller publication gap in RSeQC, BAM QC, and duplicate marking. | Done | 4 | 3 | PR #150: three equivalent owners migrated; six corrected probes, shell suites, and ordinary CI passed. | `OPS-03` |
| [CS-07](#cs-07-through-cs-10-standalone-publication) | RSeQC: retire direct-to-final report capture. | Done | 2 | 2 | PR #150: one publication path; legacy flag, errors, and recovery preserved; ordinary CI passed. | `OPS-03` |
| [CS-08](#cs-07-through-cs-10-standalone-publication) | BAM QC: retire mode-dependent publication for two outputs. | Verification pending | 2 | 2 | Absorbed into PR #155's approved runner migration; shell checks pass, full CI requires fixture corrections. | `OPS-03` |
| [CS-09](#cs-07-through-cs-10-standalone-publication) | Duplicate marking: retire direct destinations and mode branches. | Verification pending | 3 | 3 | Absorbed into PR #155's approved runner migration; shell checks pass, full CI requires fixture corrections. | `OPS-03` |
| [CS-10](#cs-07-through-cs-10-standalone-publication) | Paired CMH: retire six-file predecessor replacement/restoration. | Done | 3 | 4 | Implemented within CS-18: direct calls refuse existing destinations; focused publication checks and ordinary hosted CI pass at cab77a26. | `OPS-03` |
| [CS-11](#cs-11-reporting-source-identity) | Define a reporting-source boundary that permits reporting-only changes without changing scientific Run identity. | Needs decision | 4 | 4 | Specify new Run binding, producer identity, historical admission, and resume before a structural migration. | `REPORT-ROSTER-01` |
| [CS-12](#cs-12-canonical-bam-command-printing) | Remove canonical BAM's four print-only command arrays. | Verification pending | 2 | 1 | Retired with standalone preview in PR #155; scientific commands survive, full CI requires fixture corrections. | `COMPRESS-01` |
| [CS-13](#cs-13-runtime-profile-construction) | Remove the redundant RuntimeCheck field-copy construction in onboarding. | Opportunistic | 1 | 2 | Use standard dataclass replacement only after field/order/admission comparison; approximately 11–20 lines. | `COMPRESS-01` |
| [CS-14](#cs-14-paired-cmh-configuration) | Let the existing module normalizer own equivalent newly admitted paired-CMH configuration. | Needs qualification | 2 | 4 | First prove canonical values/errors equivalent; a changed public form or policy needs a separate decision. Retain historical semantics. | `COMPRESS-01` |
| [CS-15](#cs-15-reporting-tsv-grammar) | Retire both reporting CSV engines through the existing strict TSV owner. | Needs decision | 2 | 3 | Agree accepted grammar and diagnostic precedence; stop if a configurable compatibility adapter is required. | `COMPRESS-01` |
| [CS-16](#cs-16-operator-and-developer-documentation) | Complete operator/developer guidance with clear ownership and plain language. | Done | 5 | 3 | PR #151 passed ordinary CI at `76acb9c5`; integration pending. | `COMPRESS-01` |
| [CS-17](#cs-17-scientific-and-owner-documentation) | Consolidate and explain remaining scientific/owner documentation. | Done | 5 | 4 | All 169 Markdown files reviewed; PR #151 passed ordinary CI at `76acb9c5`. | `COMPRESS-01` |
| [CS-18](#cs-18-idiomatic-scientific-producer-implementation) | Simplify complete scientific-producer lifecycles across equivalent callers. | Verification pending | 4 | 4 | All fourteen first-party tasks use runner-owned execution; hosted golden/shell/static checks pass, stale fixture failures corrected for replacement CI. | `OPS-03` |
| [CS-19](#cs-19-scientific-report-table-handling) | Use one admitted table representation across scientific report consumers. | Done | 4 | 3 | PR #152 at `72fdf806`: focused checks and all ordinary hosted CI passed; integration pending. | `COMPRESS-01` |

## Acceptance shared by every card

Use the [workflow](../operations/WORKFLOW.md) and [campaign rules](compression_campaign.md#scope-and-next-tranche).
Before editing, inspect the complete responsibility and its callers, classify
behavior as preserved, defective, undecided, or environment-deferred, and
identify what will disappear and where its useful meaning survives.

A code change must substantially reduce maintained product code, add no
product file without approval, and migrate every equivalent caller. Prefer
clear language constructs and existing libraries over bespoke machinery.
Documentation must become shorter and easier for its intended reader to use,
with one explanation per subject and complete actions, examples, and recovery
instructions. Preserve cross-language contracts and scientific meaning.

Report product, tests, documentation, configuration, tooling, and evidence
separately. Keep independent checks and evidence; neither may be deleted to
improve a product-size result. Use focused local checks, start CI on the PR,
continue authorized independent work, then fix failures. Close only against
verified final evidence or a documented retain/reject/transfer decision.

## Card details

The original detailed audit used `d64baed27a7315aa585dd336dac43c177b837e7e`
(through PR #137) on 2026-09-07. The original discovery survey used
`372844269131568af815e117bd4508e4e200561a`, inventoried 593 tracked files,
and sampled owners and callers. Neither was an exhaustive verification or a
performance/scientific run. The subsequent integration reconciliation used
`2fb8f5ef5a297f3778fd2dd7a5046eec0ab21fa5`; the maintenance changes through
`e6493bfb` do not implement the remaining cards. In particular, mechanical
formatting makes the older line references and counts historical. Refresh
only the selected touched vertical before implementation.

### CS-01 Processing materialization

**Done in PR #153 at `cab77a26`; all ordinary hosted checks pass.** The authored
processing profile supplies twelve base owners, dependencies, and artifact
associations through `contracts/orchestration/artifact_inventory.py`. Shared
facts use immutable mappings, tuple dependencies, and internal path objects.
Planning and producer provenance use the same twelve producer locations.
One ordinary Snakemake rule declaration replaces twelve repeated bodies while
retaining their public names. Scientific arguments and native readers remain
with their owners. The public analysis-provider interface is unchanged.

The independent fixed owner/scope support check survives: accepting a profile
as its own proof of supported ownership would remove a useful defense. It is
an admission check, not a second executable dependency graph. The shared code
and authored source profile are bound into Processing implementation identity
because they now determine execution; stored Run records are never rewritten.

**Preserved:** ordered arguments, resources, rule names, profile schema/bytes,
historical interpretation, and resume/reuse with normal identity checks.
**Defective and corrected:** newly submitted processing dependencies could
contradict the graph actually executed. Only new-Run admission now rejects that
disagreement; stored-record admission and resume retain their previous policy.
**Environment-deferred:** institutional-site and cluster operation, scientific
review, and biological validation. Ordinary hosted software checks passed.

Twenty focused planning cases passed with 33 temporary differential comparisons
of complete dispatch bytes, paths, and directories against `72fdf806`. These
include historical/current resume, processing reuse with relocated sidecars,
subset manifests, resources, and guarded R arguments. Seven existing real
Snakemake cases verify exact DAG counts/edges, named rules, owner-reassignment
refusal, and historical/current resource records. One new production-path test
covers both fresh-Run refusal and resume of the same formerly accepted profile;
the existing identity check also covers the newly executable source dependency.
The profile JSON itself is byte-identical to the base.

**Earlier supporting implementation in PR #152:**
Planning now constructs its path inventory directly, passes its existing
validation path to command construction, and shares the existing ordered flag
serializer with paired-CMH planning. The workflow uses the task owner's dispatch
parser and resource owner's persisted-policy reader instead of parallel checks.
This removes 187 product lines, including 86 from the Snakefile, with no test
changes. Sixteen focused tests passed; temporary differential checks on 17
existing tests compared 25 complete dispatch/path/directory sets with `76acb9c5`,
including current and historical plans. All ordinary hosted checks passed at
`72fdf806` after correcting the obsolete diagnostic assertion.

### CS-02 Processing report adapters

[`build_adapter_registry`](../../src/emrys/reporting/_artifact_index/registry.py)
has 42 distinct processing adapters over 57 artifact templates. Several STAR
files share one adapter, as do the two Step 07 VCFs. The approved migration
derives step/scope associations from the canonical processing profile and keeps
inspection kinds, accepted filenames, scientific headers, and row limits in
reporting. Preserve independent rejection of adapters assigned to the wrong
owner. Module adapters continue to derive from `_add_analysis_adapters`.

All 42 processing adapter specifications match every pre-change field in a
temporary differential comparison. Twenty-four focused reporting tests pass;
wrong-step and wrong-scope probes still reject reassigned artifacts. Producer
path/hash expectations remain independent of the shared implementation. The
three direct registry callers now supply the admitted source checkout, separate
from the artifact root. Rechecked producer/registry cases pass with internal
path objects. Native readers, historical filenames, scientific reconciliation,
and analysis-specific adapter collisions remain protected.

Processing implementation and reporting together remove 193 product lines
(+233/−426), with no product-file growth. Configuration, schemas, dependencies,
and retained evidence are unchanged.

### CS-03 Reporting transaction layout

**Done in [PR #154](https://github.com/lab-cats/EMRYS/pull/154); ordinary hosted CI passes at `88522d0a`, integration pending.**
The earlier shared-path sketch at `0c909f12` was retained because roughly 16
helper lines merely replaced 16 caller lines. The new scope changes the
responsibility itself: one existing index publisher owns the index and summary.

The combined operation derives summary JSON/TSVs directly from admitted artifact
records, stages the complete output set, and installs the summary receipt last.
The artifact receipt remains provenance data. The separate summary publisher,
builder, input-transaction loader, and duplicate context/snapshot plumbing retire.
Current and historical readers reuse admitted records and pure projections;
no historical summary writer remains. HTML retains its separate publication.

Behavior classification: scientific meaning, formats, provenance, input/source
identity, exclusive publication, owned rollback, and historical reading are
preserved. Separate current index/summary completion is replaced by the approved
combined operation. Reporting-start v2 identifies the new two-stage sequence;
v1 retains three-stage admission, including rejection of missing historical
stages. Mixed versions and incomplete/ambiguous state remain blocked. Slurm,
institutional-site, scientific-review, and biological evidence are deferred.

Acceptance requires one current publisher for this complete output set, no
summary-generation disk reload of freshly prepared records, and no reader call
to a summary publication builder. Retarget existing real publication, corruption,
source-mutation, and historical-reader tests; retain independent scientific
checks. Record exact product/test/docs/config/tooling/evidence accounting and
final-commit local/hosted results before marking Done. No retained evidence is
deleted, no product file is added, and no new manager or registry is introduced.

Local verification covers 211 distinct reporting cases, 42 reporting/coordinator
and record-schema cases, 13 independent goldens, 40 source-topology checks, and
the isolated wheel/install command smoke. The full static gate passes, including
Ruff, ShellCheck, dead-code checks, documentation, imports, compilation, manifest,
and sharder checks. The discarded summary publication suite repeats the retained
combined publisher's protections; scientific projections, historical identity,
corruption, and golden evidence remain. [Ordinary hosted CI](https://github.com/lab-cats/EMRYS/actions/runs/34372748153)
passes at `88522d0a`; this does not establish institutional-site or scientific validation.

Implementation is stacked on PR #153 at `cab77a26`.
Product code is +565/−1310 (net −745), tests/constructors +380/−1245 (−865),
and developer tooling −12. Two product files retire and none are added.
The existing reporting-start schema grows four lines; retained evidence and
dependencies are unchanged. Documentation is accounted separately in the PR.
Independent review caught an unbound producer-commit field in the artifact
receipt. Current admission now binds it to the independently observed source
identity before the summary reuses it. One added mutation case failed before
the correction; the complete reader suite validates the correction and
preserved historical identities. No other review issue remained.

### CS-04 Reporting memory control

**Done in PR #150; CI linked above.** Removed new CLI/YAML inputs, defaults,
resource carriers, profile selection, resolution, resume overlays, and every
caller of the obsolete private `resume_resource_plan` wrapper.

The [Run-coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#profiles-and-immutable-planning)
owns retained historical reading: strict admission checks original hashes,
values, numeric/order rules, resolution, and caps without rewriting records;
legacy effective/source-only resume keeps its existing boundary. Historical
schemas, application-model checks, dashboard reads, and implementation identity
remain. An edited checkout is not automatically compatible with an old Run.

Product −46 Python lines, −45 including schema; configuration −8; tests +21.
No product file or replacement abstraction was added. The 149 focused
resource/profile/schema/model/materialization/resume checks passed before CI.
The original 35 matching lines measured spread, not potential savings.

### CS-05 Validation check rosters

[`Artifact-index inspection`](../../src/emrys/reporting/_artifact_index/inspection.py)
checks safe/unique IDs, statuses, shape, and count, but different or reordered
IDs can still pass completeness; [adapter tests](../../tests/reporting/test_artifact_adapters.py)
record this. `AnalysisArtifactV1` has headers/counts but no declared check roster.

**Decision required; excluded from the approved work.** Select membership/order,
historical treatment, and external-provider obligations. Then give one
scientific contract the agreed roster and migrate its validator, artifact
declaration, and reporting together. Preserve valid bytes, pass/fail evidence,
and independent expectations. Check missing/extra/wrong/reordered/duplicate
IDs separately from status/count. Do not import private validator code into
reporting or silently tighten generic artifacts. This changes correctness and
interfaces; any product growth needs its own approval.

### CS-06 Publication handoff

**Done with CS-07 in PR #150; CI linked above.** At `0c909f12`, local probes
sent TERM just after a real first link (exit 143), or replaced that final
before the helper's inode check (exit 1). In RSeQC, BAM QC, and duplicate
marking, the final survived while its staging anchors and lock disappeared.

[Shared shell cleanup](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution)
replaces the six per-output flags across all three equivalent owners. Each
caller arms publication before linking; cleanup examines every output pair.
The shared owner documents surviving guarantees and distinct transactions;
the lower-level helpers remain unchanged. Scientific context has a separate
[unresolved finding](#separate-scientific-context-publication-finding).

All six final probes and four shell suites passed: owned finals roll back;
uncertain missing/replaced outputs retain anchors and lock. One maintained
BAM-QC regression removes the second link before helper return. Existing
ownership, original-exit, cleanup-failure, and success tests survive.
CS-06/07 together remove 123 product lines and add 24 test lines.
TERM probes do not cover every HUP/INT timing or institutional filesystem;
SIGKILL and power loss cannot run EXIT cleanup.

### CS-07 through CS-10 Standalone publication

CS-07 passed CI in PR #150; CS-10 passed in PR #153. PR #155 absorbs
CS-08/09 by retiring standalone operational interfaces across all scientific
workers. The existing runner now owns exclusive publication, logs and recovery;
the workers retain scientific output checks. The former standalone flags and
preview modes no longer apply. See the
[shared execution contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution).
CS-08/09 await PR #155's corrected final-state CI.

| Card / owner | Preserve while retiring overwrite mode | Earlier branch estimate |
|---|---|---:|
| CS-08 [BAM QC](../../src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh) | Two outputs; empty quickcheck success markers, nonempty success behavior, native flagstat text, and producer/validator interpretation differences. | 12–22 lines |
| CS-09 [Duplicate marking](../../src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh) | BAM/index/metrics; `REMOVE_DUPLICATES=false`, Java/Picard admission, indexing, input/JAR identity, validation and partial-publication recovery. | 15–25 lines |
| CS-10 [Paired CMH](../../src/emrys/analyses/paired_cmh_candidate_ranking/producer.py) | R computation, paired strata, statistical/threshold admission, six outputs/headers, summary-last publication, process groups, native/historical readers, and existing `.previous` residue. | 35–60 lines |

These earlier branch estimates are superseded by CS-18's full migration and
must not be added to its measured reduction. Independent scientific oracles,
native output requirements and retained recovery evidence survive. Shared runner
checks replace repeated standalone lifecycle matrices.

### CS-11 Reporting source identity

The [report-output decision](../design/decisions/execution-evidence-and-reporting.md#fixed-report-output-consolidation)
owns the current source binding and historical read/resume rules. This card
requires a decision separating scientific identity from reporting implementation.

Map the affected adapters, materializers, contracts, and producers. Specify
new Run binding, producer identity, and exact historical admission before
migration. A report-only edit should allow compatible scientific resume and
independent regeneration; changed science must still be refused. Preserve
source rechecks, historical outputs/receipts, and extension ownership. Never
rewrite an existing Run, bypass its binding with a translation layer, create
an inspection/reporting cycle, or grow product code without approval.

### CS-12 Canonical BAM command printing

PR #155 retires these four print-only arrays with the approved standalone
preview interface. Canonical BAM retains its scientific sort/read-group/index
commands and `validate_bam_pair`; the runner owns execution logs. This work is
included in CS-18's accounting and awaits its final-state CI.

### CS-13 Runtime profile construction

Onboarding's `_runtime_profile_bytes` has one caller, `discover_runtime_profile`.
It copies six of eight frozen `RuntimeCheck` fields. `dataclasses.replace` could
change only `target` and `probe_args`, saving about 11 lines. An unexecuted
sketch also merged tool aliases and removed a private bytes/library-path handoff
for about 20 net lines. Neither is a substantial standalone tranche.

Before adoption, prove selected-tool/derived-alias noncollision. Compare all
fields and ordered rows, retaining Project/runtime-directory admission, Python
default/spelling, policy load, PATH tools, Rscript, Picard, renv, Python checks,
namespace arguments, and unknown-check diagnostics. Construct the environment
before probing. Use onboarding, Doctor, and runtime-identity tests; retain the
helper if clarity or meaningful reduction suffers. No installation or weakened
checkout admission is authorized.

### CS-14 Paired-CMH configuration

Project v1 accepts flat paired-CMH fields and a module form; onboarding still
writes flat fields. Its [normalizer](../../src/emrys/orchestration/run_coordinator/normalization.py)
repeats target/background transformation from the [module normalizer](../../src/emrys/analyses/paired_cmh_candidate_ranking/__init__.py).
Policy envelopes and provider binding differ. The 17-line transformation is
only a small opportunity unless equivalent validation can also retire.

Use the existing module normalizer only after proving equal canonical values,
defaults, errors/order, target aliases, absent/null backgrounds, conditions,
pairs, and provider binding, or approving their changed behavior. Preserve
request-v3/execution-v1 reads, module readmission's flat fallback, and exact
historical bytes. Changing onboarding's emitted form requires its own decision.
Reuse normalization/onboarding/module/profile/materialization tests; retain the
current forms if compatibility would need a new adapter or parallel path.

### CS-15 Reporting TSV grammar

[Run summary](../../src/emrys/reporting/_run_summary/inputs.py) uses strict CSV
quoting; [artifact index](../../src/emrys/reporting/_artifact_index/records.py)
uses lax quoting. Both use `DictReader`, skip blank records, retain ragged row
shapes, and can reject headers before lexing the remaining body. Their combined
49-line parsing surface is not an estimate of net savings.

The [shared strict TSV parser](../../src/emrys/libraries/validation/tsv.py)
rejects blank/ragged rows and empty/duplicate headers, and lexes before reporting
shape/header errors. Reuse needs a decision on quote/tab/newline grammar, CRLF,
UTF-8, header rules, and diagnostic precedence, including bad headers followed
by bad quoting. Then parse already captured bytes through that owner, retaining
domain checks, hashes, rechecks, and diagnostics. Verify complete transactions,
historical valid TSVs, and raw-byte provenance. Exclude sample manifests,
storage roots/policy, and all-pass reading: their semantics differ. Do not add
a configurable compatibility parser or reopen paths to avoid this decision.

### CS-16 Operator and developer documentation

**Done in PR #151; integration pending.** The quickstart, Runbook,
troubleshooting, configuration guide, engineering guide, and Run-coordinator
contract now separate procedures, fields/examples, and exact selection rules.
General recovery lives in troubleshooting. Resource groups and QoS are explained;
managed/institutional/Slurm routes, commands, checkpoints, and examples survive.

The same change restores campaign scope and records PR #150's verified
outcomes. Documentation structure and its 12 existing regression checks pass;
every original fenced example survives, including procedures moved between
owners. Independent review checked meaning, exceptions, and retained decisions.
No product, test, configuration, tooling, or retained-evidence files change.
The final head `76acb9c5` passed ordinary CI in
[run 34314490868](https://github.com/lab-cats/EMRYS/actions/runs/34314490868).
No fresh-install, scientific, or institutional-site walkthrough was performed.

### CS-17 Scientific and owner documentation

**Done with CS-16 in PR #151.** All 169 tracked
Markdown files were reviewed, covering architecture/design/reference,
Analysis/stage contracts, source/schema guides, tests/fixtures, tooling,
workflow, and planning. Clear files were retained without cosmetic rewrites;
frozen evidence, legal text, schema identities, and scientific numerical rules
remain intact. Module docstrings belong to the idiomatic-code work in CS-18.

Owner READMEs explain purpose, inputs, outputs, and use; contracts keep exact
behavior and exceptions. Shared reporting-root and output rules moved to the
[reporting owner](../../src/emrys/reporting/README.md); fixture evidence limits
to the [test guide](../../tests/README.md#evidence-limits); coverage-update
commands to [Engineering](../operations/ENGINEERING_CONVENTIONS.md#development-validation).
Publication and artifact-version defects formerly stranded in planning now
live beside their implementation, while proposals and acceptance stay here or
in the polish campaign. Review verified transfers and restored the explicit
Step 08 serial-processing constraint. Local and hosted evidence is recorded
under CS-16 above; this does not complete the larger code campaign.

### CS-18 Idiomatic scientific-producer implementation

**Implemented in [PR #155](https://github.com/lab-cats/EMRYS/pull/155) at `d33bbe62`; hosted verification pending:** scientific producers own scientific outputs and
provenance; production execution goes through the existing runner. Consolidate
working paths, locks, process supervision, logs, publication, and recovery there,
across every applicable producer, without a manager beside each one. Preserve
independent validation and its all-checks-pass gate. The implementation covers reusable external reference sidecars, complete STAR
indexes, final-path provenance, original native publication order, and historical
plan reading. New execution uses explicit runner-owned working paths. The
reporting tranche did not implement this migration.


The audited vertical includes nine shell workers (STAR index/alignment,
FAI/dictionary, canonical BAM, BAM QC, RSeQC, duplicate marking, split-N-cigar,
and scientific context), four Python workers (orientation, mpileup,
preprocessing, paired CMH), the GTF Run task, their R computation, command
materialization, module planning, process supervision, scientific validators,
source identity, tests, helper scripts, and documentation.

| Behavior | Classification and disposition |
|---|---|
| Algorithms, scientific flags/thresholds, formats, output checks and provenance | Preserved with the scientific owners. |
| Standalone operational lifecycle for scientific stage scripts | Replaced by the approved runner-required execution interface. Independent validation commands and the separately useful GTF conversion utility remain. |
| Native publication before independent validation | Preserved. Later validator failure retains committed outputs and failed evidence. |
| Workspaces, locks, input stability, process supervision, streams, exclusive publication and recovery | Consolidated in the existing runner; no per-producer manager. |
| FAI/dictionary reuse, all STAR members, final-path receipts and terminal native publication order | Preserved explicitly in new dispatches. |
| Historical dispatches and provider metadata | Readable under their original schemas. New worker execution and module planning use v2; old argv is not rewritten. |
| Institutional-site/Slurm operation, scientific review and biological validation | Environment-deferred; local and hosted software checks cannot establish these claims. |

Shared task tests replace repeated producer lifecycle fault matrices. Scientific
worker tests, independent validators, native-data checks, and numerical/golden
oracles remain with their owners. Retained evidence is unchanged.

Against `88522d0a`, product changes are +1359/−4916 (**−3557**), with one
obsolete product file retired and none added. Tests are net **−5333** after the CI fixture corrections.
The two existing schemas change by +2/−2; no dependency, tooling or retained
evidence changes. Documentation has separate accounting in the PR; its reduction
does not offset product growth.

Focused evidence covers 156 Python worker/independent-validator/oracle cases,
24 STAR-worker/public-shell checks, eight native shell suites and the shared
file-check suite. The coordinator/planner/task/module selection passed 167 cases,
including failure followed by resume. Its remaining long downstream-reuse case
was deliberately interrupted locally and is deferred to CI, not counted as a
pass. After review corrections, 30 affected runner cases and 21 mpileup cases
passed. The latter are included in the 156-case worker total. Two GTF utility/worker
conversion cases and one real Snakemake reference-graph dry run passed. The full
static gate passes, including 169 Markdown documents and three Mermaid sources.
The isolated offline wheel/install and public-command smoke also passes.
Two real-R projection cases skip locally because the required environment is
unavailable; changed R files parse. Ordinary hosted CI still owns the full Run,
managed-R and golden checks.

The first final-head [hosted run](https://github.com/lab-cats/EMRYS/actions/runs/34378285555)
at `abf47b77` passed the managed golden path, shell workers, static/wheel checks
and runtime compatibility lanes. It failed stale test callers: lifecycle fixtures
bound invented outputs instead of the dispatch's native outputs; Step 10 fixtures
used identical working/final paths; two assertions retained the old CMH output
order and FASTA resolver type. The corrections keep the production checks and
existing scientific assertions. All eight failed lifecycle cases and 28 profile/
resolver cases pass locally; static checks pass. Both real-R cases still skip
locally, so replacement hosted CI is required before closeout.

Independent review checked the complete worker flags, native filenames and order,
reference reuse, STAR membership, final-path provenance, removed input-hash
callers and scientific checks. It caught and corrected delayed mpileup failure
propagation, retained descendant streams after a failed worker, and input
rechecks that needed to occur before native commit. No manager hierarchy or
historical execution adapter was added.

#### Earlier completed work

The following records describe PRs #152/153 at their own revisions. The current
runner migration replaces their standalone execution interfaces.


**R work and replacement retirement passed ordinary CI in PRs #152/153.** R annotation
and scientific-context table builders now use transcript/population-sized
frames and base-R operations instead of row counters and repeated metadata.
This removes 114 product lines across two existing files, with no test changes.
Scientific calculations, thresholds, UTR precedence, warnings, row/column order,
empty types, missing values, and independent oracles are preserved.

Temporary local differential fixtures compared 24 context cases and seven
annotation-table cases with `76acb9c5`, matching values, types, order, TSV text,
and warning/error text. Annotation import and GRanges were substituted in that
temporary harness; this is table-fixture evidence. Two real-R tests skipped
because local Bioconductor packages are absent. The guarded R and managed
golden lanes passed in hosted run `34357224032` at `23bcb41e`; the diagnostic-only
follow-up at `72fdf806` also passed all ordinary CI. This is hosted software evidence,
not institutional-site operation, scientific review, or biological validation.

The Step 07/08/09 publication prototype removed only 44 net product lines after
all equivalent callers, including Step 06 file-ownership checks, were migrated.
It passed 187 existing producer tests but was discarded as insufficiently
substantial. The earlier 180–300 estimate did not survive implementation.
All five prototype files are restored; these publishers are unchanged in PR #152.

**Approved replacement:** make create-exclusive publication the only policy in
Step 07, Step 08, Step 09, and scientific-context projection. Their Run callers
already request it. A direct call with existing destinations now stops before
scientific computation; use fresh destinations for a new result. Keep accepting
`--no-clobber`, apply Step 07's full input-stability checks to every invocation,
and retain old backup/residue recognition without creating new backups.

Remove predecessor state, backup-path inventories, replacement branches, and
restoration/backup-cleanup code. Preserve distinct lock formats, metadata-write
state, signals and child handling, scientific validation, publication order,
fsync barriers, and owned-output rollback. No shared lifecycle framework is
needed. First-publication, interruption, collision, residue, and independent
scientific tests survive; tests solely for replacement can retire with that
approved behavior. Retained evidence is unchanged.

The four-owner implementation removes 163 product lines (+142/−305), 233 test
lines (+63/−296), and 27 owner-documentation lines (+33/−60). Shared policy and
backlog documentation are counted separately. No product file, configuration,
dependency, or retained evidence changes. The 135 remaining Python producer
cases and scientific-context shell transaction suite pass. Nine obsolete test
functions were removed; adapting the former two-case replacement failure check
to first publication leaves 11 fewer Python cases overall. Existing collision,
interruption, ambiguous rollback, hash-corruption, publication-order, and fsync
checks survive. An existing Step 08 residue case now injects an old backup during
lock acquisition to verify the preserved second refusal boundary. Ordinary
hosted verification passed at `cab77a26`; these checks do not establish
scientific or site validation.

Independent review found no publication regression. Scientific-context retains
its existing interruption gap between the publication helper returning and the
shell recording the published-file count; its owner contract now states the
cleanup limitation. It also retains its existing narrower post-lock temporary-
file check. These are not repaired or promoted to stronger guarantees by
replacement retirement; remaining owner maintenance stays under `OPS-03`.

### CS-19 Scientific report table handling

**Done in PR #152 at `72fdf806`; all ordinary hosted CI passed.** The existing
[computational table owner](../../src/emrys/reporting/paired_cmh_candidate_ranking_report/computational.py)
now holds one snapshot for path/hash/size, immutable named display rows, and the
streaming reader used by every equivalent candidate/figure consumer. Step 09
reuses canonical candidate metadata and summary rows instead of reparsing them.
Canonical scientific validation and all surrounding content rechecks remain.
Large tables stay streamed; selection limits, ordering, and figure passes survive.

Product −164 lines across six existing modules; test fixtures −12 lines with
no test cases added or removed; owner documentation +9. All 86 existing focused
report tests passed on their final applicable state. Temporary instrumentation
of the real admission path observed one parse each of the Step 09 all-sites,
significant-sites, and summary files; this is not a wall-time or physical-I/O
measurement. Independent review found no scientific or recovery regression.
Malformed tables remain rejected; private parser diagnostic wording can differ.

## Deferred and routed work

These entries have explicit destinations or reopening triggers. They are not
an unbounded requirement to compress every file. Existing main-matrix IDs keep
their status and acceptance there; polish and optimization retain their
subject-specific proposals. The original numbered observations are mapped in
full below so an unresolved finding cannot disappear during conversion.

### Original discovery disposition

| Original discussion | Disposition and surviving home / next action |
|---|---|
| 1–4: validation, storage inventory, reference provenance, runtime publication | Correctness/recovery work in [polish items 1–4](polish-campaign.md#correctness-and-recovery). Validation rollback may delete another process's output; inventory/reference backup moves precede their rollback handler; several owners release locks after failed restoration; runtime also has descriptor/sync/unlink failure handling. PR #115 did not repair these owners. Their distinct guarantees do not justify a shared transaction abstraction. |
| 5: input snapshots | Needs an explicit stability guarantee before consolidation: four-field metadata omits mode/change time retained by descriptor-bound reads. An existing test changes bytes while preserving size/mtime. Metadata does not establish content identity. Retain both mechanisms pending a bounded caller/threat-model decision. |
| 6: Doctor storage repair | Routed to [polish item 9](polish-campaign.md#9-make-doctors-proposed-storage-repair-match-placement): a direct repair is proposed for unready Slurm qualification. Validate the local plan separately from site execution. |
| 7: empty FASTA header | Deferred correctness correction retained here: [the contig parser](../../src/emrys/libraries/references/contigs.py) indexes an empty token list and raises `IndexError`. Reopen as a bounded normal-input-error correction with all callers and the existing contig test; no substantial compression is established. |
| 8: artifact CLI document version | Characterized correctness proposal retained [below](#artifact-cli-document-version-admission), overlapping [polish item 5](polish-campaign.md#5-admit-current-artifacts-through-the-public-validator). It is unselected and unrelated to the delivered package `--version` option. |
| 9: Snakemake package identity | [Polish item 35](polish-campaign.md#35-settle-the-installed-snakemake-content-guarantee) owns the undecided package-content guarantee. Current binding identifies the Python executable; package-change reproduction and the full identity audit remain absent. R dependency closure is a separate `RUNTIME-CLOSURE-01` outcome. |
| 10: runtime private/public models | Delivered in PR #139: one immutable check/observation model and internal path objects; do not reselect it. |
| 11: whole reference reads | Routed to [optimization](optimization_campaign.md): streaming hashes/FASTA parsing may reduce memory. Preserve second observations, decoding/newline/error order. No measured speed or peak-memory claim. |
| 12: repeated FASTQ scans | Retain the independently useful diagnostic under `OPS-03`; optimize only after its byte/diagnostic contract is settled. The draft changed zero-byte header handling, as recorded [below](#retained-audit-counterexamples). |
| 13: processing declarations | Six sample-scoped command frames delivered in PR #139; CS-01 owns remaining materialization and CS-02 the separate reporting adapter. The roughly 18-line path handoff is not a substantial tranche. |
| 14: source-topology rosters | Exact reporting exceptions consolidated in PR #139. A maintained-tool replacement is deferred until dynamic imports, private access, repository admission, CLI seams, and logging policy all have parity; observed imports cannot authorize themselves. Tool-only work needs its own exception. |
| 15: output replacement | Canonical BAM delivered in PR #146; CS-06–10 cover bounded remaining publication work under `OPS-03`. Step 05 remains outside this proposed sequence pending its separate I/O work. |
| 16: configuration normalization | CS-14; immutable provider projection and mutable record decoding remain distinct. |
| 17: reporting declarations | Fixed outputs, scientific snapshots, unused context retirement, and direct lifecycle delivered. CS-02–04 and CS-11 retain the separate remaining adapter/layout/resource/identity outcomes. |
| 18: check identities | CS-05; count and uniqueness are not an admitted roster. |
| 19: eight-selection limit | `REPORT-04` owns nine-or-more panel support through generation, receipts, validation, labels, and rendered review. Not a compression task; preserve complete underlying data. |
| 20: historical documentation bans | Delivered in PR #139. Current structure, link, anchor, and Mermaid checks survive. |

### Broader finding families

| Family retained from the review | Disposition / finite reopening trigger |
|---|---|
| Reader-oriented wording, examples, QoS/resources | CS-16/17 explicitly own the complete reader paths. Explain standard `qos`; do not rename the field. Document review is not a novice/site walkthrough. |
| Documentation ownership and orientation | CS-16/17 reconcile each subject across guides, contracts, READMEs, and docstrings, retaining useful meaning before retiring duplication. |
| Code comprehension and module concentration | CS-01/02/18 cover complete task/report construction and scientific-producer lifecycles. Improve names, fixed-position values, opaque mappings, and purpose explanations during those migrations; example repairs do not close the family. |
| Repeated protection; branch surface; excessive tests | Review with each selected owner. Delete impossible or redundant branches/cases only after checking producers and surviving independent protection. Low control-plane/runtime branch coverage is not an instruction to add tests. |
| Schema generations/layout | Deferred until one exact contract family's current/historical reader inventory supports a negative migration; do not bulk-retire v3 or rename directories for appearance. Audit-time 27 schemas / 5,353 lines span unrelated families and shared references. |
| Scripts, inline/generated programs, R bootstrap wrappers, numeric stage names | `OPS-03` owns substantive retain/migrate/retire decisions. Rename surviving programs during real migration; do not add a common bootstrap merely to inline small, semantically different wrappers. Reconcile the site-specific Step 05 script and PR #44/#45 before new work. |
| Workflow-profile rule/selector fields | `PROFILE-CONTRACT-01`; detailed deferred contract boundary [below](#workflow-profile-fields). `rule_name` is consumed, not unused. |
| Dashboard and old submission names | `DASHBOARD-RETIRE-01`; replacement dashboard first, then caller-complete retirement. Detailed obligations [below](#dashboard-retirement-prerequisites). A frozen renderer's 35–40 repeated lines do not authorize incidental cleanup. |
| Extension tutorial | Deferred documentation deliverable: one minimal working external computation provider and bespoke reporter, with no generic workflow/report DSL. |
| Project workspace creation | Existing Project/setup obligation: EMRYS creates owned directories, references scientific inputs in place, and requires explicit biological metadata. Checkout-level `data/raw`/`data/full` auto-discovery remains rejected. |
| CI control, qualification tests, tooling | `CI-01`, `QUAL-01`, and `DEV-01` own these outcomes. PR #148's fixture/tool/version changes passed ordinary hosted CI 34306975901 at `b491aac5`; master integration remains pending. Neither test scheduling nor mechanical formatting is product compression. |
| Scientific and site evidence | `SCI-AUDIT-01`, `SCI-ORACLE-01`, and `SITE-PARITY-01`; do not substitute compression checks for independent science, rendered user review, or institutional execution. |

### Historical sizing context

These are retained observations from the original audit, not a refreshed
inventory after the integration and formatting changes. They inform owner
selection and carry no promise of deletability or performance improvement.

| Audited surface | Recorded observation and limit |
|---|---|
| Large files | 101 tracked files exceeded 500 lines: 42 product, 52 test, 7 other. Of 37 over 1,000 lines, 15 were hand-maintained product, 17 tests, and 5 generated lock/CI/bootstrap files. Responsibility and duplication, not size alone, determine a slice. |
| Run coordination | About 20,225 product and 20,824 test lines; task, lifecycle, materialization, dashboard, control, Doctor, onboarding, and reporting boundary each exceeded 1,000 product lines. About 1,086 materializer lines covered task commands/dispatch declarations; its main tests had about 4,959 lines. CS-01 qualifies one complete vertical, not a mechanical split. |
| Managed dependency lock | `pixi.lock` had about 3,881 lines / 140 KB. Retain it as generated reproducibility input used by Doctor and CI; it is not maintained product bloat. |
| Persisted filenames and report kinds | `run.json`, `normalized.json`, and `attempt.json` repeat contract vocabulary; three reporting kinds recurred across five owners. The original shared-path sketch failed its reduction gate; CS-03 now combines the underlying operation. String constants alone do not establish semantic compression. |
| Stage/resource vocabulary | Fourteen historical stage IDs recur across policy, profiles, and the Snakefile; Analysis admission permits Step 09 and optional Step 10, and some historical profiles omit newer IDs. Reopen a semantic-key migration only when module extension needs it; preserve historical reads. `QUAL-04` delivered owner-count derivation and `PROFILE-CONTRACT-01` owns its narrower future transition. |

### Retained audit counterexamples

These earlier bounded audits and local reproductions do not establish hosted,
site, production, or scientific evidence. They retain reasons a tempting
consolidation was not selected.

- **Timestamp checking depends on an optional checker.** With the current
  declared dependencies and the available local Python environment, both
  historical v1 and current v2 Attempt receipts accept
  `finished_at: "not-a-time"` when the JSON Schema date-time checker is absent.
  This reproduced before and after orchestration-validator consolidation.
  The schema declares `format: date-time`, but the project declares base
  `jsonschema` and its lock has no RFC 3339 checker package. Audit timestamp
  admission across callers and select the dependency/validation correction
  separately; no dependency change is authorized by this finding.
  [Polish item 6](polish-campaign.md#6-make-timestamp-admission-deterministic)
  owns the correction proposal.
- **A single-pass FASTQ draft changed accepted input.** For paired headers
  `@re<NUL>ad/1` and `@read/2`, where `<NUL>` denotes a zero byte, the existing
  helper succeeds locally. The proposed system-`awk` scan truncated the first
  ID to `re` and failed the pair. The draft was not published. Preserving byte
  handling and shell diagnostics needs further design before this optimization.
  At the audited default of 20 prefix IDs, counting plus per-ID scans makes
  21 logical passes per mate. A replacement must preserve complete record
  counts, decompression failures, and the explicitly limited prefix comparison;
  this source-derived pass count is not a physical I/O measurement.
- **Runtime lock acquisition is a small defect fix, not substantial compression.**
  Standard-library descriptor ownership can close the write/fsync leak, but
  shortening the current descriptor lifetime changes close-failure timing.
  Preserving that timing requires additional handling. Keep the bounded leak
  repair separate from the other unresolved runtime publication failures.
- **Immutable configuration and record projection have different purposes.**
  Module planning has one recursive freeze helper. It supplies read-only
  mappings and tuples after strict JSON admission; the existing record decoder
  instead returns fresh mutable dictionaries and lists. Neither replaces the
  other without changing the provider boundary. Canonical record storage is
  already shared by the existing application-model owner.
- **TSV readers have different admission contracts.** [Run-summary parsing](../../src/emrys/reporting/_run_summary/inputs.py)
  uses strict quoting while [artifact-index parsing](../../src/emrys/reporting/_artifact_index/records.py)
  uses lax quoting; both retain `DictReader` row shapes. The [shared strict parser](../../src/emrys/libraries/validation/tsv.py)
  rejects ragged rows and defers header and row-shape errors until lexing ends.
  Blank rows, malformed quotes, duplicate or empty headers, and diagnostics
  therefore differ. The [all-pass reader](../../src/emrys/orchestration/run_coordinator/all_pass.py)
  also accepts its own unique check roster and requires every status to pass;
  report validation checks an external roster and accepts pass/fail. Reuse
  would change behavior or need a new configurable adapter; defer consolidation.
- **Resource normalization preserves historical identity.** [Resource policy](../../src/emrys/orchestration/run_coordinator/resource_policy.py)
  distinguishes partial fragments, complete symbolic policies, persisted
  effective records, and allocation resolution. Historical records retain
  fixed numeric memory; symbolic records re-resolve allocation/workflow values.
  Historical omissions of thread settings for Steps 09 and 10 default to one
  without adding fields, and integer conversion canonicalizes accepted integral
  numbers. Existing owners already share admission and record mechanics;
  no substantial preserving retirement was qualified.
- **Limitation-ID collision handling has no current collision input.** The
  [summary projection](../../src/emrys/reporting/_run_summary/projection.py)
  emits zero or one limitation with a fixed base ID, and its ID allocator starts
  with an empty set. Full retirement would remove about 14 lines; defer it as
  too small for a standalone substantial slice.
- **R command setup already shares argument parsing.** The remaining owner
  wrappers differ in script-path handling, package admission, diagnostics, and
  error precedence. A common bootstrap would add a new abstraction; inlining
  the argument wrappers alone saves too little for a substantial slice.


### Artifact CLI document-version admission

**Characterized defect.** The artifact owner's [known CLI version limit](../../src/emrys/contracts/artifacts/README.md#known-cli-version-limit)
records the current/default schema mismatch, source selection, and prior local
production-path reproduction. This card owns the proposed correction.

**Proposed correction, not selected.** For an object document, pass its declared version
through the existing schema selection owner. Reuse the resulting ordered
error collection at the two manual call sites in
[`_run_summary/validation.py`](../../src/emrys/reporting/_run_summary/validation.py)
and the one in
[`_run_report/inputs.py`](../../src/emrys/reporting/_run_report/inputs.py).
This could remove about 9–13 net product lines across three existing files.
This would change public correctness behavior; it requires a separate
selection and the checks below before acceptance.

**Preserve.** Keep default `schema_validator` behavior, raw registry keys
and schema IDs, local references, deterministic diagnostic ordering,
the active artifact-record v2 and supported flat summary v2 and receipt v4.
Frozen receipt v3 remains outside this public admission proposal. Retain
explicit supported-version guards with their distinct first errors,
duplicate-key/non-finite JSON rejection, and semantic validation after
schema success. Unknown versions must not become silently accepted.

**Proof.** Use the real public CLI and API for valid current/historical
records and malformed versions; cover non-object documents, missing,
unknown, non-string versions, schema-first failures, and semantic failures.
In particular, object/array version values must produce a schema failure,
not an unhashable registry-key exception.
The starting suites are
[artifact-schema contracts](../../tests/contracts/artifacts/test_artifact_schema_contracts.py),
artifact/run-summary tests, and report transaction tests. Verify that local
invocation imports the selected checkout rather than an older installed
package. This review did not rerun the prior reproduction.

### Workflow-profile fields

`PROFILE-CONTRACT-01` concerns the persisted workflow-profile v2 contract,
not the resource `ExecutionProfile` class. Clarify that terminology when
the backlog subject is next edited.

**Observed.** The
[profile schema](../../src/emrys/contracts/schemas/orchestration/v2/profile.schema.json)
requires `owner_tasks[].rule_name`, owner-task `scope_selector`, and
artifact-template `scope_selector`.
[`api.py`](../../src/emrys/contracts/orchestration/api.py) forces selectors
from `scope_type`; this makes those values redundant in admitted records.
However, `rule_name` is consumed:
[`workflow/Snakefile`](../../workflow/Snakefile) reconstructs and checks the
authored processing-rule projection against its static base graph.
The profile schema also enforces its presence and admission checks uniqueness.
It is incorrect to describe the field as unused merely because the
Execution-Plan projection omits it.

The existing functional projection in `application_model.py` excludes
both fields and provides a semantic starting point for a later migration.
The tracked
[current profile](../../workflow/contracts/local_cmh_v2.json) contains 81
rule-name/selector occurrence lines; retaining the historical profile means
these are not 81 automatically deletable lines.

**Conditional outcome.** During an independently justified profile-contract
transition, determine whether semantic owner keys and scope types can
replace the repeated adapter metadata and backend projection checks
caller-completely. Migrate profile generation, workflow consumers, schema
admission, artifact inventory, and historical inspection together. Preserve
static graph equivalence, rule/owner uniqueness, scope expansion, artifact
group order, Execution-Plan identity, and direct/Slurm behavior.

**Disposition.** Retain deferred. Do not bump the contract solely for
cleanup, silently discard authored metadata, or add a compatibility writer.
Require a net-negative migration after counting the exact v2 reader,
validator, retained profile, and tests. The source review has not established
that those economics work. Profile, workflow, materialization, and
orchestration-contract suites are the validation boundary.

### Separate scientific-context publication finding

The CS-06 audit found that scientific-context rollback counted a link only after
its helper returned, leaving an interruption gap. PR #155 retires that entire
publisher in favor of runner-owned publication with retained ownership anchors.
CS-18 owns this correction and its final verification; it is no longer an
unselected investigation. The original CS-06 probes alone did not prove this owner.

### Dashboard retirement prerequisites

[`dashboard.py`](../../src/emrys/orchestration/run_coordinator/dashboard.py)
had 1,985 product lines at the original audited revision and its
[dedicated test module](../../tests/orchestration/run_coordinator/test_dashboard.py)
had 986 lines. These are owner sizes, not net deletion estimates.
The Make dashboard target and direct script invocation are current callers;
the interface is documented as frozen.

Project-local `inspect` provides admitted status and task-log paths.
It does not fully replace dashboard scheduler discovery/accounting,
historical accounting fallback, exact job identity, stream ownership,
regular-file/no-symlink admission, or sanitized display of raw streams.
The dashboard's incremental stream cache tracks size and resets on truncation; it
does not provide inode-based rotation protection.
A raw `tail -F` invocation does not provide the dashboard's terminal-control
sanitization. Retiring the display therefore needs an explicit supported
home for the capabilities that remain necessary.

**User-required sequence.** First implement and validate a replacement
dashboard, including the agreed scheduler-history and safe-log capabilities.
Only then scope removal of the old dashboard owner, dedicated tests, Make
target, public CLI fixture assertions, and stale documentation caller-completely.
Expert commands alone do not meet this replacement requirement. Account for
all replacement code before claiming the retirement's net size. Neither step
is part of the reporting lifecycle compression tranche.

[`slurm_submission.py`](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
still generates `emrys-local-pilot` job/stream names. The existing
`DASHBOARD-RETIRE-01` acceptance includes retiring that spelling from
new submissions. Treat this as a distinct caller-complete slice within
that accepted outcome: approve the replacement naming before changing
submission, materialization, synthetic-harness, and logging consumers.
It is not a technical prerequisite for removing the display itself.
Preserve exact historical names and paths; never rename old streams or
delete retained accounting evidence as a side effect.

**Acceptance.** Preserve `inspect` as status authority and prove exact job
selection, historical accounting fallback, missing/replaced streams,
ownership and symlink rejection, terminal-control sanitization, and new
submission names. Use dashboard tests to identify obligations before their
retirement and retain direct protection for surviving capabilities.
Institutional scheduler behavior remains environment-deferred until the
separately authorized site qualification.

### Retained mechanisms and rejected shortcuts

The [counterexamples above](#retained-audit-counterexamples) retain the resource,
immutable/mutable projection, TSV, small-helper, and bootstrap findings.
Additional limits remain:

- `computational_resources_explicit` preserves authored omission; merged values
  cannot reconstruct it. CS-04 retired the entire reporting-memory control.
- Parent Slurm resource selection and child planning read the predecessor at
  different times/processes; one cached result cannot replace both checks.
- Four-field snapshots omit descriptor-bound mode/change time; metadata is not
  proof of unchanged bytes. Any consolidation needs a stability decision.
- Schema directories contain unrelated families and shared references: current
  summary v3, frozen receipt v3, resource/profile v1, and historical request v3
  cannot be retired together based on their suffix.
- Validation reports, inventory, references, runtime, and stage publication
  have distinct recovery contracts. Similar names do not justify sharing.
- R dependency closure and Snakemake content identity remain separate questions.
  Independent numerical oracles and generated locks are retained obligations.

## Delivered scope and integration evidence

[PR #139](https://github.com/lab-cats/EMRYS/pull/139), merged at
`446802c06ebceee8328a5cb4b542eea9fb2ed398`, integrated the work from
PRs #116–138. Those original PRs were closed without individual merges;
their changes are present through the integration PR. The delivered outcomes
include:

- one immutable runtime check/observation model and shared Attempt schema
  admission, with the existing public contracts and diagnostic ordering;
- one command frame for the six sample-scoped shell stages, preserving their
  explicit argument/input order and the distinct Step 06 Python path;
- removal of unused reporting input helpers, table metadata, summary-context
  copies, and the scientific-context source carrier, plus shared artifact
  predecessor validation through its existing owner;
- single assembly of storage-measurement rows and Doctor results, and direct
  admission/accumulation of GTF exon rows without the intermediate carrier;
- retirement of completed documentation bans and the separate reporting-import
  permission bypass, preserving active structure checks and rejecting stale
  authored permissions; and
- corrected storage I/O test observations across Python versions, reviewed
  long-test scheduling estimates, the autonomous-stack workflow, and the
  incorporated quickstart, polish, and optimization guidance.

[PR #140](https://github.com/lab-cats/EMRYS/pull/140) is the subsequent
integration boundary. At this reconciliation it is open at
`2fb8f5ef5a297f3778fd2dd7a5046eec0ab21fa5`, containing PRs #141–147; its
source tree is identical to `8034c2112d5f5572f7e21c32818ebc6da7b40b53`.
[Ordinary CI run 34301289787](https://github.com/lab-cats/EMRYS/actions/runs/34301289787)
succeeded on that head. This establishes hosted CI for the integrated source,
not a merge into master or institutional, scientific, or biological validation.
The implemented scope includes:

- ordinary CI on stacked PRs, parsing every declared Bash file, broader Ruff
  correctness checks, and shared local/CI sharder self-tests;
- [fixed report-output declarations](../design/decisions/execution-evidence-and-reporting.md#fixed-report-output-consolidation)
  in PR #145, preserving the existing identity and historical-resume rules;
- [canonical BAM create-exclusive publication](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#scientific-worker-execution)
  in PR #146, retiring replacement while preserving historical defect evidence
  and documenting surviving recovery limits; and
- [direct create-only reporting publication](../design/decisions/execution-evidence-and-reporting.md#reporting-lifecycle-compression)
  in PR #147, retiring the three publishers' predecessor lifecycle, six callback
  carriers, and HTML facade (386 net product lines removed, as recorded for that slice).
  The logical producer identifier, historical
  read/preparation paths, source admission, and ownership-proved recovery remain.
  Its subsequent test consolidation retired approved redundant or obsolete
  cases while retaining distinct scientific, historical, and recovery oracles.

These outcomes must not be selected or counted again. Broader reporting
identity, roster authority, resource-policy, and other publication-owner
findings in this backlog remain separate.

### Addressed before the campaign

The following cited instances no longer require work unless the remaining
review finds a broader live pattern:

- the obsolete Run-coordinator diagram and stale links were removed, while the
  current-user, grouped-pipeline, and reliability diagrams remain as concise
  reader aids rather than contract authorities;
- the functional-owner repository exception and `docs/demo` were removed;
- the global orchestration contract and orchestration-readiness document were
  retired;
- decision records, the test baseline, engineering conventions, the
  documentation index, and paired-CMH/scientific-context READMEs were
  substantially compressed;
- the stale sitemap, rolling handoff, resource README, and path-heavy standalone
  scientific-context command were removed;
- directory orientation removed too broadly during compression was restored for
  the current tracked tree without reviving retired checkout-level storage
  directories or the stale sitemap;
- the glossary remains the comprehensive terminology authority and describes
  the current public model without replacing owner contracts;
- `data/test` and `refs/test_star_index` have no tracked contents; and
- `project.yaml` already supports multiple named Analyses, with one Analysis
  selected per Run.

## Rejected proposals and retained underlying concerns

| Proposal not accepted | Technical reason | Concern that remains |
|---|---|---|
| Flatten `src/emrys` into `src` | `src/` is the standard packaging root and `emrys/` is the stable import package. Flattening would destroy or fragment package identity. | Audit unnecessary package and module fragmentation within `emrys`. |
| Add repository `data/raw` and `data/full` placeholders with automatic discovery | Git cannot retain empty directories without placeholders; Projects intentionally live independently of the source checkout; filenames do not establish biological design. | `emrys init` must create all EMRYS-owned Project directories and ingestion helpers must request explicit scientific metadata. |
| Rename `qos` to a longer field | QoS is Slurm's established term, and a public-schema migration adds more surface than it removes. | Explain it in examples and user-facing help. |
| Maintain a handoff document on every commit | It would duplicate live Git, PR, check, and task state and immediately become another stale registry. | Generate a compact handoff at an actual transfer boundary when needed. |
| Rename every numeric script immediately | Names participate in callers, package data, tests, and sometimes persisted identities; cosmetic churn would not simplify execution. | Rename retained survivors semantically during `OPS-03` migration. |
| Move whole contracts into docstrings | That would hide or duplicate cross-language behavior and recovery guarantees. | Make module docstrings explain local purpose, inputs, outputs, and architectural role. |
| Replace every `row[column]` access | Declared schema iteration can be clear and appropriate. | Replace fixed-position or context-free structures where named values materially improve comprehension. |
| Retire all v3 schemas | Several v3 records remain active and “v3” spans unrelated contract families. | Audit each exact schema and historical reader before consolidation. |

## Closeout record required before retirement

Follow the [campaign retirement procedure](compression_campaign.md#completion-and-retirement).
Record each card's result and exact evidence; update broader rows only when
those outcomes change. An original PR closed through an integration is not
abandoned work. A repaired example or rejected shortcut does not close its
family, and no unfinished concern disappears without a recorded disposition.
