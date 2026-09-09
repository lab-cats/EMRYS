# EMRYS temporary compression backlog

Reconciled: **2026-09-09**, against maintenance revision
`e6493bfb2e401d25e6652bdc06efde184a15947a` and its PR #140 base.

This is the working backlog for the finite `COMPRESS-01` campaign.
The [campaign](compression_campaign.md) owns its objective, boundaries, and
retirement conditions. This file alone owns the `CS-*` cards: their status,
remaining scope, dependencies, acceptance, and disposition. The
[main matrix](backlog_matrix.md) owns the campaign umbrella and broader
outcomes such as `REPORT-ROSTER-01` and `OPS-03`; their linked child cards
are not duplicate tasks to complete in both places.

The approved tranche is CS-03, CS-04, CS-06, and CS-07; CS-05 is excluded.
It preserves existing reporting identity policy, rejects reporting-memory
settings in new inputs while retaining historical reading and hashes, and
makes RSeQC refuse existing outputs. Every implemented logical change must
substantially reduce product code; shared mechanics must replace all equivalent
production callers. No new evidence deletion or unrelated policy is approved.

## Working queue

The current tranche is **CS-04** plus the shared publication change
**CS-06/07**. **CS-03** closed as Retained after its complete equivalent-caller
review found no substantial reduction. **CS-01/02** remain the next unselected
processing-declaration candidates. **CS-05** and **CS-08/09** remain outside this
approval; the latter still require their own standalone publication decision.

The older size counts below are audit surfaces, not promised deletions.
CS-12 and CS-13 are opportunistic small work and must not be presented as
another substantial tranche. Correctness, performance, documentation, and
replacement work routed below are not counted as product compression.

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
| [CS-01](#cs-01-processing-materialization) | Derive one processing owner's command and dispatch from existing admitted facts. | Needs qualification | 4 | 4 | Trace one complete profile → task → producer path; deliver a net-negative draft or retain rationale. | `COMPRESS-01` |
| [CS-02](#cs-02-processing-report-adapters) | Remove equivalent processing-adapter declarations from artifact-index reporting. | Needs qualification | 4 | 4 | Identify missing metadata and its existing owner; stop if a parallel registry is needed. | `REPORT-ROSTER-01` |
| [CS-03](#cs-03-reporting-transaction-layout) | Consolidate only equivalent reporting-layout declarations. | Retained | 4 | 3 | The complete minimal shared-owner sketch is approximately neutral after plumbing; no code change qualified. Reopen only with a concrete larger equivalent duplication. | `REPORT-ROSTER-01` |
| [CS-04](#cs-04-reporting-memory-control) | Remove the ineffective active reporting-memory control and its transport. | Verification pending | 3 | 4 | Approved: reject new inputs; preserve historical records and hashes. Caller-complete migration and 149 focused checks pass; hosted CI remains required. | `REPORT-ROSTER-01` |
| [CS-05](#cs-05-validation-check-rosters) | Give one scientific validation roster one neutral authority used by its producer and reporting. | Needs decision | 4 | 4 | Select membership/order, historical records, and external-provider obligations. | `REPORT-ROSTER-01` |
| [CS-06](#cs-06-publication-handoff) | Characterize the helper-to-caller publication gap in RSeQC, BAM QC, and duplicate marking. | Verification pending | 4 | 3 | Gap reproduced in all three owners; all migrated callers and six corrected probes pass; hosted CI remains required. | `OPS-03` |
| [CS-07](#cs-07-through-cs-10-standalone-publication) | RSeQC: retire direct-to-final report capture. | Verification pending | 2 | 2 | Approved with CS-06: one create-exclusive path, accepted legacy flag, preserved tool errors and recovery; local checks pass, hosted CI remains required. | `OPS-03` |
| [CS-08](#cs-07-through-cs-10-standalone-publication) | BAM QC: retire mode-dependent publication for two outputs. | Blocked | 2 | 2 | CS-06 plus the same policy decision, preserving QC-specific capture semantics. | `OPS-03` |
| [CS-09](#cs-07-through-cs-10-standalone-publication) | Duplicate marking: retire direct destinations and mode branches. | Blocked | 3 | 3 | CS-06 plus the policy decision; preserve three-output recovery and tool identity. | `OPS-03` |
| [CS-10](#cs-07-through-cs-10-standalone-publication) | Paired CMH: retire six-file predecessor replacement/restoration. | Needs decision | 3 | 4 | Approve standalone publication policy and characterize its own recovery; CS-06 is not evidence for this different owner. | `OPS-03` |
| [CS-11](#cs-11-reporting-source-identity) | Define a reporting-source boundary that permits reporting-only changes without changing scientific Run identity. | Needs decision | 4 | 4 | Specify new Run binding, producer identity, historical admission, and resume before a structural migration. | `REPORT-ROSTER-01` |
| [CS-12](#cs-12-canonical-bam-command-printing) | Remove canonical BAM's four print-only command arrays. | Opportunistic | 2 | 1 | Compare exact rendered command bytes and execution calls; approximately 30 lines before final recount. | `COMPRESS-01` |
| [CS-13](#cs-13-runtime-profile-construction) | Remove the redundant RuntimeCheck field-copy construction in onboarding. | Opportunistic | 1 | 2 | Use standard dataclass replacement only after field/order/admission comparison; approximately 11–20 lines. | `COMPRESS-01` |
| [CS-14](#cs-14-paired-cmh-configuration) | Let the existing module normalizer own equivalent newly admitted paired-CMH configuration. | Needs qualification | 2 | 4 | First prove canonical values/errors equivalent; a changed public form or policy needs a separate decision. Retain historical semantics. | `COMPRESS-01` |
| [CS-15](#cs-15-reporting-tsv-grammar) | Retire both reporting CSV engines through the existing strict TSV owner. | Needs decision | 2 | 3 | Agree accepted grammar and diagnostic precedence; stop if a configurable compatibility adapter is required. | `COMPRESS-01` |

## Acceptance shared by every card

Before changing structure, classify affected behavior as preserved, defective,
undecided, or environment-deferred. Audit the complete owner and its callers,
contracts, tests, scripts, configuration, compatibility, and mutable state.
A qualification ends with the proposed deletion, surviving owner, caller list,
resolved decisions, separate product/test/docs/config/tooling/evidence footprint,
and proportionate local/hosted proof, or a documented reason to retain it.

Implementation must deliver that one observable outcome, retire its old path
caller-completely, meaningfully reduce maintained product code, and add no
product file unless a quantified exception is explicitly approved. Do not
pad the slice or its tests to manufacture scale. Preserve scientific meaning,
immutable Runs, provenance, supported historical reads, and recovery evidence.
High-risk protection changes need explicit approval and equal-or-stronger
surviving defenses; retained evidence deletion needs its exact separate approval
and commit. The [delivery workflow](../operations/WORKFLOW.md#deliver) owns
these rules and the single common rollback requirement.

Use focused real-path checks locally and applicable long checks in hosted CI.
Publish an approved slice and start CI, then continue independent authorized
work; review outstanding checks after that work and cut bounded fixes.
Verification remains pending until required checks pass on the final state.
Local fixtures, hosted CI, Slurm, institutional operation, scientific review,
and biological validation remain distinct claims.

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

**Materialization finding.**
[`materialization.py`](../../src/emrys/orchestration/run_coordinator/materialization.py)
had 1,960 lines at the original audited revision; `_task_commands` and `_dispatches`
are the relevant construction owners. Artifact rows are resolved into paths,
grouped by owner and scope, and projected into commands, inputs, outputs,
resource declarations, and dispatches. These transformations are candidates
for a focused producer-to-consumer audit, not proof of redundant logic.

Audit one processing owner through profile, artifact inventory, resource
resolution, materialization, task admission, and its native producer. The
deliverable is either one complete deletion proposal or a retain decision
with its semantic reason. Compare exact ordered arguments, planned-file
bytes, graph/scopes, input snapshots, output roles, retained predecessor
paths, source identity, and resource choices. Use existing materialization,
workflow, task, and public-path tests. No new step registry or shell-to-Python
conversion is selected.

**Important retained distinctions.** Module descriptors are re-admitted at
execution planning; this is not necessarily duplicate construction.
Current AnalysisRevision scopes and historical execution scopes differ.
Processing-source snapshots must match the immutable Run binding.
Positional FASTA-sidecar outputs and reused predecessor scopes have distinct
roles. The previously noted roughly 18-line validation-path handoff and
8–10-line inventory-copy opportunities do not justify bundling unrelated
owners into one slice.

### CS-02 Processing report adapters

**Reporting adapter finding.**
[`_artifact_index/registry.py`](../../src/emrys/reporting/_artifact_index/registry.py)
has a roughly 175-line `build_adapter_registry`, including processing
declarations, local assembly, and the existing module-adapter call.
The `_add_analysis_adapters` path already
derives module adapters. Current processing profile templates lack some
adapter semantics, so their existing facts are not a complete replacement.

An implementation proposal must identify the rightful existing home for
output metadata across
[`analyses/__init__.py`](../../src/emrys/analyses/__init__.py),
artifact inventory, the
[authored profile](../../workflow/contracts/local_cmh_v2.json), its
[closed schema](../../src/emrys/contracts/schemas/orchestration/v2/profile.schema.json),
profile admission, and reporting. Derive kinds, scope,
paths, and completeness only where semantics are equivalent. Retain native
format readers, independent scientific reconciliation, historical profiles,
and bespoke module output interpretation. The 175-line block is a target
surface, not promised savings. Stop if a new table must coexist indefinitely
with the old one or the migration grows maintained product code.



### CS-03 Reporting transaction layout

**Observed owners.** Transaction kinds, predecessor order, receipt locations,
and shared paths recur in
[`reporting_operation.py`](../../src/emrys/orchestration/run_coordinator/reporting_operation.py),
`reporting_boundary.py`, `transaction_validation.py`, and inspection.
The inspection consumers include
[`inspection.py`](../../src/emrys/orchestration/run_coordinator/inspection.py)
and
[`_inspection_evidence.py`](../../src/emrys/orchestration/run_coordinator/_inspection_evidence.py).
The ordered producer execution loop is already consolidated; do not count
that completed work again. The historical/current report-root distinction
already has an owner in
[`artifact_inventory.py`](../../src/emrys/contracts/orchestration/artifact_inventory.py).

**Proposed outcome.** Derive the fixed artifact-index → run-summary → HTML
layout from one existing contract owner and remove the equivalent local
declarations. Keep producer-specific preparation with its production owner.
This does not select a new transaction kind, extension protocol, generic
pipeline description, or parallel reporting registry.

**Preserved behavior and proof.** Compare prepared arguments and bytes,
receipt/input/output paths, ledger order and timing, predecessor selection,
processing-source rechecks, independent regeneration, and exact failure
stopping points. Preserve historical root interpretation. Use
[reporting-operation tests](../../tests/orchestration/run_coordinator/test_reporting_operation.py),
reporting-boundary tests, transaction-validation tests, and
[ledger contract tests](../../tests/contracts/orchestration/test_reporting_ledger_contracts.py).

**Retain decision.** Review at `0c909f12` found 11 lines of receipt-root/suffix
selection in `_inspection_evidence.py`, five receipt-path lines and four
predecessor-map lines in `transaction_validation.py`. A straightforward shared
path function costs about 16 lines and replaces approximately 16 net lines
before imports, public type exports, and caller plumbing: roughly neutral,
not substantial compression. Moving the roster/type mostly relocates seven
lines. No implementation or product test was added for this decision.

Producer arguments, standalone paths, residue inventories, root admission,
historical dispatch, and boundary rechecks serve distinct contracts; they
cannot be folded into the total as equivalent declarations. Reopen only for
a concrete larger equivalent duplication. Existing identity rules still allow
ordinary edits to hashed code; CS-11 is required only for a policy change.
The broader reporting identity/roster outcome remains open.

### CS-04 Reporting memory control

**Implemented; hosted verification pending.** The entire inactive control is
removed from new CLI/YAML inputs, defaults, the three resource carriers,
profile selection, resolution, and resume overlays. The existing strict record
reader validates historical raw hashes, reporting values, numeric/order rules,
resolution, and caps without rewriting bytes. Legacy effective/source-only
resume retains its original admission boundary. The now-unused private
`resume_resource_plan` wrapper and every caller are retired.

The [Run-coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#profiles-and-immutable-planning)
owns the current input and historical behavior. The historical resource schema,
application-model checks, and frozen dashboard reads remain required; none is
an active memory allocation control. Existing implementation-identity rules
still apply, so editing these owners does not promise old Runs can resume
under a different checkout.

The complete change removes 46 Python product lines (45 including its schema
change), eight configuration lines, and adds 21 test lines. No new product
file, resource manager, model, or compatibility wrapper is introduced.
149 focused resource/profile/schema/application-model and materialization
identity/resume checks pass. Hosted ordinary CI remains required. The
original audit's 35 matching source lines measured spread, not savings.

### CS-05 Validation check rosters

**Observed.**
[`_artifact_index/inspection.py`](../../src/emrys/reporting/_artifact_index/inspection.py)
checks row shape, safe and unique check IDs, statuses, and count.
[Artifact-adapter tests](../../tests/reporting/test_artifact_adapters.py)
characterize different or reordered unique IDs still being considered
complete. Count and uniqueness do not establish the intended check roster.
The public `AnalysisArtifactV1` declaration has headers/counts but no
declared check-ID roster. Some scientific validators require membership;
reporting may also depend on order.

**Proposed outcome.** Start with one owner whose neutral scientific contract
can own the agreed roster. Migrate that validator, artifact declaration,
and report admission together, removing repeated declarations and superseded
checks. Keep independent expected-result tests.

**Decisions and proof.** Approve ordered versus unordered completeness,
historical treatment, and external-provider obligations. Characterize
missing, extra, wrong, reordered, and duplicate IDs independently of status
and count. Preserve valid output bytes and allowed pass/fail evidence.
Do not import a private validator into reporting or silently tighten every
generic artifact. This is a correctness/interface proposal, not a preserving
helper extraction; size is unknown and any growth requires its own exception.

### CS-06 Publication handoff

**Implemented with CS-07; hosted verification pending.** Baseline local
production-script probes at `0c909f12` reproduced the gap in RSeQC, BAM QC,
and duplicate marking. TERM immediately after a real first hard link exited
143; replacing that final before the helper's inode check exited 1. In both
cases the final survived while staging and the owned lock disappeared.

The [shared shell cleanup owner](../../src/emrys/libraries/README.md#shell-publication-cleanup)
now owns the full equivalent rollback/staging/lock sequence across all three
producers. Their six per-output flags are gone; publication is armed before
linking, and cleanup inspects every staging/final pair. That owner documents
precise recovery guarantees, retained limitations, and why other transaction
lifecycles are not equivalent consumers. The lower-level link/ownership helpers
are unchanged. The separate scientific-context counter gap is retained
[below](#separate-scientific-context-publication-finding).

All six before/after probes pass: provably owned finals roll back, and an
unresolved missing/replaced output retains its staging anchors and lock.
One maintained real BAM-QC regression removes the second link before helper
return; existing ownership, original-exit, failure-cleanup and success tests
survive. All three producer shell suites and the shared file-check suite pass.
The CS-06/07 publication change removes 123 net product lines across four
existing files; its tests add 24 net lines. No additional fault matrix was added.

TERM was exercised locally; this does not prove every HUP/INT timing, Slurm,
or institutional filesystem case. SIGKILL/power loss do not execute EXIT
cleanup. Local software probes and hosted CI cannot establish scientific or
biological validation.

### CS-07 through CS-10 Standalone publication

Canonical BAM uses one create-exclusive publication path under its approved
[owner contract](../../src/emrys/stages/canonical_bam/CONTRACT.md#producer-publication-boundary).
Its replacement, backup, and restoration mode is retired. Existing backups and
ambiguous residue remain operator-owned recovery state; the contract preserves
the historical restoration defect and the surviving cleanup limitations.

**Policy scope.** CS-07 RSeQC is approved for create-exclusive standalone
publication: existing outputs are preserved and replacement is refused.
The same policy remains a proposal for CS-08–10, not implementation approval.
All independently useful standalone commands remain.
Normal Run materialization already selects `--no-clobber` for the shell owners below, and the paired-CMH
provider selects it for its producer. This does not establish that the
standalone interfaces are unused or that every surviving failure path is
already sufficient.

The policy decision must also cover the continued acceptance of the
`--no-clobber` spelling, newly unconditional safe-ID and input-hash
admission, and where failed tool captures and diagnostics survive. These
are public behavior, not incidental cleanup. For example, QC's direct
quickcheck failure retains its capture and prints its location, while
staged cleanup can remove that capture. A universal staged path must
preserve an approved useful diagnostic outcome and truthful messages.

The common preservation and evidence rules live in the
[workflow](../operations/WORKFLOW.md#deliver) and
[architecture guardrails](../design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails).
Across these proposed retirements, preserve scientific computation, native
artifacts, provenance, original inputs, historical readers, and recovery
evidence. Validate present outputs, partial publication, input changes,
replacement by another process, tool failure, cleanup failure, and retained
ambiguous state. Owner-specific requirements follow; they do not create
four separate versions of the common rollback rule.

| Proposed slice | Audited owner and removable mode | Owner-specific requirements and size |
|---|---|---|
| CS-07 RSeQC | Implemented: one existing staged publication path for both standalone and Run calls; the legacy flag is accepted without a second mode. | Native report text, input binding, safe sample IDs, exit codes, diagnostics, and recovery follow the [producer contract](../../src/emrys/evidence/rseqc_orientation/CONTRACT.md#producer-publication-boundary). Its owner loses 51 net product lines within the complete CS-06/07 change. |
| CS-08 BAM QC | [QC producer](../../src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh): retire final-versus-staged capture for its two outputs. | Preserve empty quickcheck success-marker semantics, nonempty success behavior, native flagstat text, and producer/validator interpretation differences. Approximate branch opportunity: 12–22 product lines. |
| CS-09 Duplicate marking | [Picard producer](../../src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh): retire direct destinations and mode branches for BAM, index, and metrics. | Preserve `REMOVE_DUPLICATES=false`, Java/Picard admission, indexing, three-output validation, input/JAR identities, and partial-publication recovery. Approximate branch opportunity: 15–25 product lines. |
| CS-10 Paired CMH | [CMH producer](../../src/emrys/analyses/paired_cmh_candidate_ranking/producer.py): retire six-file predecessor backup/replacement and restoration. | Retain R computation, paired strata, statistical/threshold admission, six outputs and headers, summary-last publication, process-group handling, and native/historical readers. Recognize existing `.previous` recovery residue even if new attempts cease creating it. Approximate branch opportunity: 35–60 product lines. |

The remaining CS-08–10 audit estimate is 62–107 product lines before recovery and
compatibility costs. QC and duplicate marking primarily shed mode
conditionals, sentinel digest values, and target aliases; their substantive staging and
protection code remains. Their main additional value is a consistent safer
publication policy. Qualify each slice against Rule 5 rather than treating
that policy value as an automatic compression exception.

Recount each actual draft; this range is neither a net commitment nor a
reason to delete tests. Existing owner suites are the
[RSeQC shell tests](../../tests/evidence/rseqc_orientation/test_step_03_infer_strandedness_and_orientation.sh),
[QC shell tests](../../tests/evidence/canonical_bam_qc/test_step_02b_bam_qc.sh),
[duplicate-marking shell tests](../../tests/stages/duplicate_marking/test_step_04_mark_duplicates.sh),
[canonical BAM shell tests](../../tests/stages/canonical_bam/test_step_02_sort_index_bam.sh),
and
[CMH producer tests](../../tests/analyses/paired_cmh_candidate_ranking/test_paired_cmh_producer.py).
Their corresponding native-output validators and independent scientific
oracles survive. Retiring tests for deliberately retired behavior requires
preserving useful decisions and failure evidence first; retained evidence
deletion still needs its separate exact proposal and commit.

Step 05 remains part of the broader `OPS-03` family but is excluded from
this proposed tranche pending reconciliation with its separate I/O work.
Step 08 optimization is likewise not absorbed.

### CS-11 Reporting source identity

The [fixed report-output decision](../design/decisions/execution-evidence-and-reporting.md#fixed-report-output-consolidation)
owns the identity map, current/historical read and resume rules, report-source
restrictions, alternatives, and surviving defenses. The approved consolidation
preserves those rules; it does not close the broader identity goal or approve
a different reporting producer. Changing those policies remains a separate
decision.

**Required outcome and decision.** Map which current reporting adapters,
materializers, contract declarations, and producers affect the Run-bound source
closure. Define which must remain scientific identity and where report-only
implementation belongs. Select the new producer identity and exact historical
read/resume behavior; do not rewrite an existing Run or add an identity
translation layer merely to bypass its binding. The existing decision above
is the preserving baseline, not evidence that the broader goal is done.

**Acceptance.** A concrete boundary and caller-complete migration proposal
must show that a report-only change permits scientifically compatible resume
and independent regeneration while changed science is still refused. Preserve
historical output/receipt interpretation, source rechecks, and extension
ownership. Stop if the proposed boundary introduces an inspection/reporting
cycle, weakens binding, or grows product code without an approved exception.


### CS-12 Canonical BAM command printing

 Four arrays in the canonical BAM producer
are used only to print quickcheck, header, record-count, and sample-tag-count
commands. The audited 30-line declaration block remains after replacement retirement;
its sole reads remain four `print_command` calls. Replace those calls with the same
directly quoted arguments and retire the declarations. Keep executable sort,
read-group, index, and input-header command arrays.

The proposal removes 30 product lines in one existing file and leaves real
validation with `validate_bam_pair`. These commands are printed in both
dry-run and execute modes. Before acceptance, compare complete rendered
command bytes with fixed tokens and quoted paths, preserving
`printf '%q '` escaping, trailing spaces, headings, and order; verify
execute-mode invocation logs are unchanged. Run the owner shell and
executable-resolution checks through the selected production path.
This estimate is independent of canonical BAM replacement retirement.

### CS-13 Runtime profile construction

 The onboarding helper
`_runtime_profile_bytes` has one caller, `discover_runtime_profile`.
It rebuilds each frozen eight-field `RuntimeCheck`, copying six fields
unchanged. Standard-library `dataclasses.replace` can retain those fields
while replacing `target` and `probe_args`; no new carrier is needed.
That constructor-only change is approximately 11 net physical lines and
does not by itself establish a substantial slice.

An earlier in-memory construction sketch estimated about 20 net product
lines by also expanding the existing selected-tool mapping with derived
aliases and retiring the private bytes/library-path handoff within the same
owner. That combined estimate is provisional, not an executed or validated
patch. Preserve Project/runtime-directory admission, Python default
resolution, policy load, PATH tools, Rscript, Picard, renv, and Python
admission order; preserve policy-row order, authored Python spelling,
Picard/R namespace arguments, and the unknown-check diagnostic.

Validate the static selected-tool/derived-alias noncollision assumption
before changing dispatch, then compare every generated check field and
ordered row. Preserve environment construction before probing.
Use onboarding discovery, Doctor, and runtime-identity tests. Retain the
helper if removing it harms clarity or the complete draft lacks meaningful
reduction. Neither candidate authorizes installation or weakening a
checkout-origin check to make local testing convenient.

### CS-14 Paired-CMH configuration

**Observed.** Current Project v1 accepts both flat paired-CMH fields and an
explicit module form.
[`onboarding.py`](../../src/emrys/orchestration/run_coordinator/onboarding.py)
still writes the flat form. In
[`normalization.py`](../../src/emrys/orchestration/run_coordinator/normalization.py),
the flat branch translates target/background values separately from the
existing module's `_normalize_config` in
[`paired_cmh_candidate_ranking/__init__.py`](../../src/emrys/analyses/paired_cmh_candidate_ranking/__init__.py).
The forms differ in policy envelope and provider binding; one is not merely
a different spelling of identical persisted intent.

**Conditional outcome.** Have the existing module normalizer own newly
admitted scientific configuration, retiring the duplicated flat transformation
only when equivalent canonical values and errors are demonstrated or their
correction is approved. Changing onboarding's emitted form is a separate
public/provenance decision. No new normalization abstraction is proposed.

**Preserve and prove.** Retain historical request-v3/execution-v1 reading,
the module readmission flat fallback, and exact flat policy semantics until
every consumer is accounted for. Compare canonical numeric types/defaults,
target aliases, absent versus null background, condition and pair errors,
error order, provider binding, and exact historical Run bytes. Use
normalization, onboarding, module, profile, and materialization tests.

The gross duplicated flat transformation is about 17 lines. Net saving is
unproven and likely small unless equivalent semantic validation can also
retire. Defer if preservation requires a new adapter or parallel pathway.
Do not describe active flat configuration or all request-v3 support as obsolete.

### CS-15 Reporting TSV grammar

**Observed.** The CSV engines in
[`_run_summary/inputs.py`](../../src/emrys/reporting/_run_summary/inputs.py)
and
[`_artifact_index/records.py`](../../src/emrys/reporting/_artifact_index/records.py)
occupy about 49 lines combined. Summary parsing uses strict quoting; index
parsing uses lax quoting. Both use `DictReader`, skip blank records, and
can retain ragged row shapes. They can reject headers before lexing the
remaining body.

The existing
[`parse_strict_tsv_bytes`](../../src/emrys/libraries/validation/tsv.py)
rejects blank/ragged rows and empty/duplicate headers, and defers shape/header
errors until lexical scanning finishes. A later quote error can therefore
take precedence. It is not a preserving drop-in replacement.

**Conditional outcome.** After an explicit input-compatibility decision,
parse already captured report bytes through that existing owner and retire
both local CSV engines. Keep domain row-count checks, hashes, snapshots,
rechecks, and diagnostics in their owners. Do not reopen a pathname or create
a configurable parser adapter to emulate every previous behavior.

**Decision and proof.** Specify malformed quotes, quoted tabs/newlines, blank
and ragged rows, duplicate/empty/wrong headers, CRLF, invalid UTF-8, and
header-plus-later-lexical-error precedence. Test complete artifact-index and
run-summary transactions, including historical valid TSVs and raw-byte
provenance. The 49-line surface is not a net estimate because domain checks
and error translation remain. Exclude sample manifests, storage roots/policy,
and the all-pass reader: their accepted forms and status semantics differ.

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
| Reader-oriented wording; examples; unclear QoS and resource groups | Deferred to a bounded reader review of one role's complete path. Explain standard `qos` rather than migrating its spelling. Existing quickstart expansion does not prove a novice/site walkthrough. |
| Documentation ownership; contracts/READMEs/docstrings; weak directory/schema orientation | Deferred to one subject's complete authority reconciliation. Examples include setup procedure in configs, validation status in Architecture, developer CI in Runbook, scientific interpretation in Troubleshooting, and mixed purpose/exact behavior in owner contracts. Preserve useful meaning before moving or deleting its former home. |
| Code comprehension and module concentration | CS-01/02 are the selected planning focus. Other names, positional tuples, opaque mappings, module openings, and fragmentation require a bounded owner rationale before edits; file length is not a defect. The Step 09 threshold tuple and application/artifact-inventory docstrings remain examples. |
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
| Persisted filenames and report kinds | `run.json`, `normalized.json`, and `attempt.json` repeat contract vocabulary; three reporting kinds recurred across five owners. CS-03 retained these declarations after its complete shared-owner sketch failed the reduction gate; string constants alone do not establish semantic compression. |
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

**Characterized defect.** The earlier local production-path reproduction
established that current module run-summary v3 and report-receipt v5 pass
their explicit schemas but fail the unversioned artifact CLI. The default
`schema_errors` call in
[`schema.py`](../../src/emrys/contracts/artifacts/_artifact_contracts/schema.py)
does not select the document's version, although `schema_validator`
already supports the closed versioned schema map.

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

The CS-06 caller audit also found a helper-return counter gap in
[`scientific_context_projection.sh`](../../src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/scientific_context_projection.sh):
its rollback loop visits only `published_count`, incremented after each link
helper returns. Unlike the three migrated producers, this owner also controls
backups, directory syncing, commit state, and a different lock record.
The new cleanup is not an equivalent replacement for that transaction.

Retain as an unselected owner-specific recovery investigation under `OPS-03`.
Reproduce its actual native publication path before selecting a correction;
CS-06's three-owner probes do not establish that result. Do not mark every
caller of the low-level link helper repaired by this tranche.

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

The following distinctions limit the current proposals; they do not claim
that every surrounding owner has been exhaustively audited.

| Mechanism | Evidence for retaining it or narrowing the proposal |
|---|---|
| Resource override intent | `computational_resources_explicit` still records authored omission; effective merged resources cannot reconstruct it. CS-04 removes `selected_reporting_memory` because its entire active control is retired, not because authored overlay intent was derivable. |
| Repeated predecessor admission | Resource selection before Slurm submission and later child planning independently admit the predecessor. They cross a time/process boundary; do not cache one result across that boundary merely to delete validation. |
| Resource normalization | Partial fragments, complete symbolic policies, historical effective records, numeric canonicalization, and allocation resolution carry different semantics. Historical missing thread fields and accepted integral numbers affect exact record identity. |
| Immutable and mutable projections | A frozen mapping/tuple boundary for providers does not duplicate decoding into a fresh mutable JSON object. Shared canonical record storage is already implemented. |
| Input stability checks | Four-field metadata snapshots and descriptor-bound mode/change-time checks make different guarantees. Metadata is not proof of unchanged content; any consolidation needs an explicit threat-model decision. |
| Schema generations | Physical directories contain different contract families and cross-directory references. Current summary v3, frozen receipt v3, current resource/execution-profile v1 IDs, and historical request v3 cannot share one version-retirement decision. |
| Publication mechanisms | Validation reports, inventory replacement, reference provenance, runtime inspection, and stage outputs have different ownership/recovery contracts. Similar backup/lock spelling does not justify one shared transaction implementation. |
| Runtime and source identity | R dependency closure and Snakemake package-content binding remain separate assurance questions. A smaller file roster is not evidence of equally strong identity. |
| Small independent fragments | The fixed limitation-ID allocator, tiny unused helpers, small row-copy handoffs, and R wrappers did not qualify a substantial standalone change in the reviewed scopes. This is a value judgment per candidate, not an arbitrary repository-wide line-count threshold. |
| Scientific oracles and generated locks | Independent numerical expectations and reproducibility locks have different maintenance and evidence roles from duplicated production logic. Their removal cannot manufacture a product-code reduction. |

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
- [canonical BAM create-exclusive publication](../../src/emrys/stages/canonical_bam/CONTRACT.md#producer-publication-boundary)
  in PR #146, retiring replacement while preserving historical defect evidence
  and documenting surviving recovery limits; and
- [direct create-only reporting publication](../design/decisions/execution-evidence-and-reporting.md#reporting-lifecycle-compression)
  in PR #147, retiring the three publishers' predecessor lifecycle, six callback
  carriers, and HTML facade. The logical producer identifier, historical
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

A card closes with its accepted result and exact evidence, or its explicit
retain/reject/transfer reason. Update the parent matrix row only when that
broader outcome actually changes. Do not leave an implemented card described
as discovery, and do not mark a broader family complete because one example
was removed. A PR's closure without individual merge is not proof its work
was abandoned; use the integration ancestry above.

Before retiring these temporary documents, reconcile every CS card and routed
finding, move unresolved accepted work into the main matrix, and transfer
useful constraints, counterexamples, recovery defects, and evidence ceilings
to the named durable owner. Verify every link and transfer, record the final
user disposition, and explicitly scope retirement. No unselected candidate
must be implemented merely to close the campaign; no unresolved concern can
be dropped merely because its easiest simplification was rejected.
