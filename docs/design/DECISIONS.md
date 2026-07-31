# Decisions

This file records durable choices, rationale, alternatives, and consequences.
Current status belongs in [`PIPELINE_PLAN.md`](PIPELINE_PLAN.md), current
evidence in [`../operations/HANDOFF.md`](../operations/HANDOFF.md), and
commands in [`../operations/RUNBOOK.md`](../operations/RUNBOOK.md).

## Development and repository

### Use TSV manifests

Decision: sample, partition, inventory, approval, and evidence manifests are
tab-separated when a table is appropriate.

Reason: TSV is easy to inspect and parse across shell, Python, and R without
CSV quoting ambiguity. Consequence: headers and row order are public
contracts and must validate exactly.

### Develop locally and scale through SLURM

Decision: editing, fixtures, mocks, and syntax checks happen locally; heavy
production computation runs through SLURM jobs.

Alternative rejected: executing heavy work on the login node.

### Use descendant branches and separate docpatch gates

Decision: each package descends linearly from the latest clean, docpatched
predecessor. Implementation and documentation are separate commits; a
documentation-only package uses one documentation commit.

Reason: evidence, interfaces, and current state remain reviewable at every
stage. The authoritative current lineage belongs in `PIPELINE_PLAN.md`.

### Run one complete computational gate per executable state

Decision: use focused tests during implementation, then run one de-duplicated
complete computational gate against the final executable state before its
implementation commit. A subsequent documentation-only patch runs the
documentation gate and reuses that recorded computational evidence when Git
inspection proves that executable configuration, dependencies, Make targets,
schemas, fixtures, and test selection/execution semantics are unchanged.

Reason: rerunning identical multi-runtime suites before both the implementation
and documentation commits adds substantial latency without testing a new
executable state. Any executable change after the recorded gate invalidates
reuse and reopens the full implementation/docpatch sequence.

### Prefer failure-first validation output

Decision: local pytest uses quiet progress, short tracebacks, and its default
captured-output behavior. Make command echo and routine successful shell, R,
and report output are suppressed or captured; complete output is shown for a
failure or an explicit verbose run.

Reason: successful progress narration consumes operator attention and agent
context without changing evidence. Failure logs must remain complete and
diagnosable.

Decision: the complete developer gate uses a bounded orchestrator rather than
unconstrained `make -j`. Python coverage, shell contracts, sequential guarded
R, and pinned report-runtime checks are independent lanes. A parallel default
is allowed only after exact repeated serial/parallel result, file, line,
branch, and coverage equality; the measured improvement thresholds and
smallest-stable-concurrency rule in `PIPELINE_PLAN.md`; controlled failure and
interruption cleanup; and a working serial fallback. Developer-only parallel
dependencies are pinned and synchronized explicitly, never installed by tests
or workflow entry points.

Reason: this removes duplicate work and reduces feedback latency while keeping
coverage, evidence boundaries, failure provenance, process cleanup, and a
deterministic low-concurrency fallback reviewable.

### Read canonical documentation by task boundary

Decision: every task starts with complete reads of the conduct and current
handoff documents, the applicable roadmap sections, and task-relevant anchored
sections of the other canonical owners. Complete reads of the nine-document
corpus are reserved for phase boundaries, documentation-ownership changes,
detected inconsistencies, and tasks that cannot otherwise be bounded safely.

Reason: canonical ownership and targeted repository searches preserve the
safety boundary without repeatedly loading thousands of unrelated operational
lines. Commands, rationale, current state, and roadmap remain in their single
owners so targeted reading does not depend on a duplicate summary.

### Keep active and future tests separate

Decision: active runnable shell tests live under `tests/shell/`; future plans
live under `tests/pending/` and are not wired into active targets.

### Treat legacy scripts as protocol references

Decision: translate legacy behavior into parameterized, tested interfaces.
Do not copy hardcoded paths, samples, or undocumented assumptions.

## Execution and publication

### Default to dry-run

Decision: workflow scripts require `--execute`; SLURM wrappers use
`EXECUTE=0` by default and accept only `0` or `1`.

Reason: operators should inspect resolved inputs, outputs, tools, and commands
before publication.

### Publish validated transactions

Decision: multi-file stages use owned locks, run-token staging, input rechecks,
validation before publication, rollback, cleanup, and a receipt or summary
published last.

Consequence: transaction completion describes the publication set, not the
success or existence of every underlying evidence item.

### Preserve recovery evidence

Decision: do not automatically delete locks, backups, or recovery markers when
ownership, rollback, or cleanup cannot be proved.

Alternative rejected: optimistic cleanup that can destroy the only evidence
needed for safe recovery.

## Reference and BAM pipeline

### Use the Novogene-provided reference

Decision: the delivered reference is the workflow reference unless a separate
migration is approved. Reference FASTA, annotation, sidecars, BED, and STAR
index identities must reconcile explicitly.

### Build STAR with the declared read-length overhang

Decision: the reference index uses `sjdbOverhang=149` for the declared
150-base reads. Validators must inspect the configured value rather than infer
it from filenames.

### Generate BED12 from GTF

Decision: RSeQC consumes a deterministic BED12 derived from the declared GTF.

### Treat FASTA sidecars as Step `00c`

Decision: FAI and sequence dictionary preparation is a formal, validated step,
not an undocumented prerequisite.

### Make Step `02` the canonical BAM boundary

Decision: downstream consumers use coordinate-sorted, indexed BAMs with
sample-specific read-group metadata. Publication is validation-first and
rollback-protected.

### Keep QC and downstream transformation as separate consumers

Decision: BAM QC, orientation inference, and duplicate marking consume the
canonical BAM independently. QC evidence does not mutate the BAM.

### Mark rather than remove duplicates

Decision: Step `04` marks duplicates and preserves reads for downstream policy
decisions.

### Validate the effective Java runtime

Decision: resolve the actual Java executable, log its version, and fail before
Picard when it is below the required major version. Module names and
`JAVA_HOME` alone are insufficient evidence.

Node pinning is a temporary operational mitigation, not architecture.

### Use project storage for large GATK temporary files

Decision: Step `05` routes large temporary files to an owned project-storage
location and cleans only paths it owns.

## Orientation and downstream analysis

### Separate mechanical orientation from biological strand

Decision: retain neutral `FWD_like` and `REV_like` labels. Do not infer
biological sense/antisense from flag groupings.

Reason: the cohort is reverse-stranded/first-strand-style, but read
orientation, transcript strand, and biological interpretation are distinct.

### Run Step `07` cohort-wide and manifest-partitioned

Decision: each declared partition processes all manifest samples together in
manifest order for both mechanical orientations. Selector type determines the
bcftools interface. Outputs and counts are committed by a receipt published
last.

No input discovery by glob and no sample-order inference are allowed.

### Consume only declared Step `07` transactions in Step `08`

Decision: Step `08` verifies the exact partition/orientation cross-product,
receipts, paths, hashes, counts, and sample order before semantic parsing.

Multiallelic records are expanded deterministically; symbolic and non-SNV
alleles are counted and excluded. Raw count lexemes are validated before
semantic coercion.

### Keep the orientation policy provisional

Decision: `legacy_provisional_v1` is a compatibility mapping, not biological
validation. Outputs and reports must retain that limitation.

### Pair Step `09` samples only through manifest replicates

Decision: pairing is explicit manifest metadata, never inferred from sample
names. The declared design requires matching treatment/control replicate sets
and at least two strata.

### Use one paired CMH and global BH family

Decision: Step `09` retains every eligible and ineligible candidate with an
explicit status, uses the declared two-sided continuity-corrected CMH
direction, and applies one BH family across successfully tested target
candidates.

Outputs are “CMH-ranked candidates,” not validated editing sites.

## Runtime environments

### Guard the repository-local R environment

Decision: repository activation occurs only when `NORAD_USE_RENV=1`; `0`
leaves normal startup unchanged and other values fail. Restoration is an
explicit operator action. Compute scripts and tests never bootstrap packages.

Reason: local reproducibility must not silently alter ordinary R startup or
cluster jobs.

### Restore report tooling explicitly

Decision: Quarto restoration is separate from rendering and testing. Installed
identity, receipt, tree, and version must validate before reuse. Rendering
never installs or repairs software.

### Probe runtime availability from explicit profiles

Decision: runtime preflight consumes one exact TSV profile with closed
tool-version, R-namespace, SHA-256, and absolute-path visibility check types.
Each row declares `local`, `cluster_batch`, or `any`; the operator explicitly
declares the context in which the probes run.

Reason: login-shell availability, local development state, module names, and
path assumptions do not prove batch visibility. Context mismatches remain
`blocked` or `not_checked` rather than being silently promoted.

Consequence: preflight installs and repairs nothing. Command success means the
checks were evaluated and, in execute mode, the report was published; every
required row still must be inspected. Even an all-pass batch report is
availability evidence, not workflow runtime validation or cluster proof.

### Reconcile references without repair

Decision: reference provenance uses an explicit TSV inventory and base
directory, hashes every named physical member, retains declared annotation
source/release, and compares contig identities across FASTA, FAI, DICT, GTF,
BED12, and STAR metadata.

Reason: filenames and colocated directories are not provenance, while an
inspection tool must not silently regenerate or normalize shared references.
Consequently, missing files, hash differences, malformed metadata, and contig
disagreement are reported in a summary-last transaction and require separate
operator resolution.

### Measure storage without acting on retention policy

Decision: storage evidence comes from an exact TSV inventory of absolute roots
and a separate exact retention-policy TSV. The inventory records declared and
resolved paths, tree size, entry counts, filesystem capacity, expected quota,
and policy approval state in a three-file summary-last transaction.

Reason: capacity evidence and retention authorization must be inspectable
before large runs, but an observational foundation tool must not become an
implicit cleanup engine. Consequently, pending or rejected approvals and
missing required storage are reported without deleting, moving, archiving,
compressing, or otherwise changing data.

## Evidence and scientific state

### Separate computational proof and scientific interpretation

Decision: implementation, fixture testing, real-runtime testing, cluster
dry-run, cluster proof, scientific review, and biological readiness are
independent fields.

`cluster-proven` requires inspected scheduler, log, command, and output
evidence. Report generation is not validation.

### Preserve two post-review states

Decision:

- `science_review_complete_exploratory` records a completed but provisional
  evidence review;
- `biological_interpretation_ready` is reserved for stricter, separately
  approved exit criteria.

Current tools must reject an unauthorized ready state.

### Require explicit evidence relationships

Decision: passed, failed, or proven claims require their defined evidence
roles. Runtime and cluster roles additionally require exact underlying paths
and hashes. Blocked or not-run states are never proof.

## Structured artifacts and reporting

### Decouple reporting from computation

Decision: native compute outputs remain unchanged behind explicit, read-only
artifact adapters. Renderers consume a canonical structured summary rather
than native outputs directly.

### Use versioned closed schemas

Decision: public artifact, scientific-review, run-summary, and report-receipt
documents use explicit schema versions. A closed shape is not silently
changed; incompatible changes require a version increment.

### Inventory physical artifacts explicitly

Decision: each expected-artifact row names one concrete physical path.
Artifact IDs and physical paths are unique; logical-scope rows remain
contiguous and stable. Globs, unresolved templates, traversal components, and
implicit machine substitutions are rejected.

### Bind run identity to immutable analysis inputs

Decision: run identity derives from explicit sample, reference, partition, and
primary-analysis policy identities. Changing an identity component requires a
new run ID. Inventory revisions are adapter-attempt metadata, not silent run
identity changes.

### Represent missing and failed evidence

Decision: expected scopes remain in records and summaries when missing,
failed, incomplete, externally unavailable, blocked, or not run. Absence is
not silently dropped.

### Adapt step validation reports without promotion

Decision: each step validator publishes the exact seven-column report contract
defined in the pipeline plan and receives a step-specific read-only artifact
adapter. Failed checks remain failed artifact and expected-scope states through
the canonical summary and consolidated reports.

Reason: validation evidence must be visible without hand-editing artifact
records or inferring a stronger runtime state. A published local validation
report records only its explicit checks; it does not create cluster proof,
scientific review, or biological readiness.

### Authorize supplemental report tables explicitly

Decision: a report table enters the canonical summary only through an exact,
nonempty approval manifest bound to the run contract and active scientific
review. Path, hash, row count, role, display limit, policy, approver, and time
must reconcile. Omission authorizes no tables.

Canonical summary JSON must not be hand-edited.

### Render deterministic, static reports

Decision: reports are self-contained, script-free, accessible projections of
one canonical run summary. They use exact scientific-state banners and disclose
truncation with the full source path and hash.

The public renderer defaults to one atomic HTML/PDF/summary-TSV bundle with a
deterministic report receipt published last. Operators may explicitly select
`html`, `pdf`, or `all`; every mode still publishes the summary and receipt.
PDF uses pinned Quarto with bundled Typst and a pinned pure-Python reader for
structural, text-order, and every-page banner validation. Format-neutral
content keeps the HTML and PDF projections aligned while allowing
format-specific validation.

The HTML projection groups broad report categories with native,
script-free disclosure elements. Overview opens first so status, CMH-ranked
candidates, adjudication, and limitations remain near the top. The page uses
a bounded reading width, while wide approved tables scroll within their own
keyboard-focusable regions instead of widening the document. The PDF remains
linear and renders wide candidate tables as compact per-candidate records.
Full approved rows and provenance remain available in the HTML and authorized
source tables.

Alternative deferred: a richer tab interaction model with additional
keyboard, responsive, print, and browser behavior. It requires separate
review and focused interaction coverage rather than adding script execution
to the current static report implicitly.

Rendering never discovers inputs, invokes analysis engines, installs
dependencies, or promotes evidence state.

## Measure Python coverage without replacing scenario gates

Decision: pin Python coverage as a developer-only dependency, measure line and
branch execution across the complete Python suite and configured Python
subprocesses, and compare a deterministic tracked snapshot by exact ratios.
Ordinary checks reject a global line/branch regression or a removed baseline
module. New shared Python modules start with a 90% line and 85% branch
threshold.

Baseline regeneration is an explicit reviewed action. Tests and runtime entry
points never install the tool or rewrite the snapshot automatically.

Reason: a measured floor makes later refactors comparable, while percentage
coverage alone cannot establish assertion independence, public-contract
completeness, transaction safety, real-R behavior, cluster execution, or
scientific correctness. The public-contract matrix and independent scenario
tests remain separate gates.

## Documentation ownership

Decision: each information category has one canonical owner:

- `AGENTS.md`: stable conduct and gates;
- `README.md`: concise entry point;
- `TODO.md`: prioritized pending work;
- `HANDOFF.md`: current takeover snapshot;
- `PIPELINE_PLAN.md`: status, acceptance criteria, and lineage;
- `QUESTIONS.md`: open questions and resolved index;
- `RUNBOOK.md`: executable commands;
- `DECISIONS.md`: durable choices and rationale;
- `TROUBLESHOOTING.md`: symptom, cause, diagnosis, and fix;
- `ARCHITECTURE.md`: current topology and contracts;
- `FUTURE_ARCHITECTURE.md`: target-state constraints;
- demo documents: presentation material or dated snapshots;
- standalone `.mmd` files: canonical diagrams.

Reason: mutable facts otherwise drift across independently maintained copies.
Documents link to canonical owners instead of repeating branch names, commit
IDs, test totals, commands, live status, or diagrams.

## Deferred engineering

Decision: helper-library extraction, generic orchestration, job arrays,
analysis configuration, module wrapping, public-data ingestion, publishing
infrastructure, targeted reruns, and automatic cleanup remain deferred until
stable evidence demonstrates a concrete need.

Future refactors must preserve proven CLIs, output paths, dry-run/execute
semantics, and transaction contracts unless separately approved.
