# Execution, evidence, and reporting decisions

These decisions govern execution safety, runtime observations, evidence state,
artifact contracts, and reporting. Exact interfaces remain with their
functional owners; this file retains the reasons and non-negotiable boundaries.

## Execution and publication

### Default to dry-run

Public workflow execution requires an explicit execute action. Operators must
be able to inspect resolved inputs, outputs, tools, and commands before
publication; owner-specific controls remain part of each public contract.

### Publish validated transactions

Multi-file publishers use owned locks, run-token staging, input rechecks,
validation before replacement, rollback, cleanup, and a receipt or summary
published last. Transaction completion describes the publication set and does
not imply that every underlying evidence item passed or exists.

### Preserve recovery evidence

Do not automatically delete a lock, backup, partial output, or recovery marker
when ownership, rollback, and cleanup cannot be proved. Optimistic cleanup can
destroy the only evidence needed for safe recovery.

### Characterize unsafe publication states before correcting them

Protect intended behavior and explicitly label known unsafe states with
adversarial tests before changing publication, rollback, signal, descriptor, or
cleanup code. Characterization records an observed boundary; it does not
approve the defect or make unlike transaction implementations interchangeable.

## Runtime environments

### Guard the repository-local R environment

Repository R activation is opt-in through `EMRYS_USE_RENV=1`; normal startup is
unchanged when it is disabled, and invalid values fail. Restoration is an
explicit operator action. Compute and tests never bootstrap packages.

### Keep report rendering inside the locked Python package

The report owner uses the locked Jinja2, Matplotlib, and Logomaker runtimes plus
packaged template/CSS. Matplotlib initializes through one private temporary
cache that is removed before rendering continues and never writes durable
report state; Logomaker operates inside that already controlled renderer
boundary. The owner never installs or repairs tooling, invokes an external
renderer, accesses the network, or creates report sidecars.

### Inspect runtime availability from explicit profiles

The grouped route `python -I -m emrys inspect runtime-availability` evaluates
one exact profile in one explicitly declared context and installs or repairs
nothing. It retains `runtime_preflight` artifact vocabulary. Local or
login-shell availability does not establish batch visibility. Even an all-pass
batch report is availability evidence, not workflow runtime validation or
cluster proof.

### Reconcile references without repair

Reference provenance hashes and reconciles one explicit inventory, including
annotation identity and contig agreement, without repairing or regenerating
shared artifacts. Names and colocation do not establish provenance.

### Measure storage without acting on retention policy

Storage evidence measures declared roots and records retention-policy approval
separately. Observation never authorizes deletion, movement, archival,
compression, or any other data mutation.

## Evidence and external interpretation

### Separate computational proof and scientific interpretation

Implementation, fixture testing, real-runtime testing, cluster dry-run, and
cluster proof are separate computational claims. Cluster proof requires
inspected scheduler, log, command, and output evidence; report generation is
not validation. Candidate review, adjudication, and biological interpretation
are external work-process records and are not EMRYS evidence states.

### Keep external interpretation outside the pipeline

EMRYS produces CMH-ranked computational candidates and provenance. It does not
encode an approver, adjudication gate, biological-readiness gate, or scientific
completion status. External research records may reference immutable EMRYS
outputs without becoming inputs to pipeline completion.

### Require explicit evidence relationships

Passed, failed, or proven claims require their defined evidence roles. Runtime
and cluster roles additionally bind exact underlying paths and hashes. Blocked,
not-run, and unavailable states are never proof.

## Structured artifacts and reporting

### Decouple reporting from computation

Keep native compute outputs unchanged behind explicit read-only adapters.
Renderers consume one canonical structured summary and never discover inputs or
rerun analysis.

Reporting is downstream operational work, not a semantic scientific stage. A
full run invokes it automatically by default after required upstream artifacts
are admitted, while an explicit supported opt-out may skip that projection.
The exact configuration field and CLI spelling remain public-UX decisions.

A report can be regenerated independently from admitted artifacts and evidence
without rerunning scientific work. Skipping or regenerating reporting does not
change the identity or validity of completed science; each generated report may
retain its own content-bound artifact/version identity. A reporting failure is
visible and may make the requested full command unsuccessful or partial, but it
does not invalidate completed science or admitted upstream artifacts.
Independent regeneration is a supported recovery path. Exact persisted status,
retry/resume, and exit-code presentation remain unsettled.

### Use versioned closed schemas

Public artifact, run-summary, and report-receipt documents
use explicit versions and closed shapes. Incompatible changes require a version
increment rather than a silent field change.

### Inventory physical artifacts explicitly

Each expected-artifact row names one concrete path. Artifact IDs and paths are
unique; logical-scope rows remain stable and contiguous. Reject globs,
unresolved templates, traversal components, and implicit machine substitution.

### Bind run identity to immutable analysis inputs

Run identity binds explicit sample, reference, partition, and primary-analysis
policy identities. Changing an identity component creates a new run; inventory
revisions remain adapter-attempt metadata rather than silent identity changes.

### Represent missing and failed evidence

Keep every expected scope visible when it is missing, failed, incomplete,
externally unavailable, blocked, or not run. Absence is a state, not a row to
drop.

### Adapt step validation reports without promotion

Step-specific read-only adapters preserve failed checks as failed artifact and
expected-scope states through summaries and reports. A published validation
report records only its explicit checks and creates no cluster, scientific, or
biological promotion.

### Render deterministic, static reports

Reports are self-contained, script-free, accessible projections of one
canonical summary. They label computational candidates as not scientifically
adjudicated, disclose truncation with source identity, and use one autoescaped
strict Jinja template for HTML. Publication is transactional and never installs
dependencies, accesses the network, creates sidecars, or promotes evidence.
The fixed scientific SVG roster is rendered only from canonically admitted
values and embedded as validated data URIs; reporting owns mappings and
presentation, not scientific calculation. Exact figure inputs, policies,
renderer versions, hashes, and availability are disclosed in the evidence
HTML. Scientific plot PDFs remain analysis artifacts rather than report
formats.

## Operator output and durable logs

### Separate concise console output from durable detailed logs

Keep console output concise while retaining complete durable diagnostic logs
under the target contract in
[`LOGGING_CONTRACT.md`](../LOGGING_CONTRACT.md). Accepted adoption work remains
in the [findings matrix](../../tasks/backlog_matrix.md).
Declared machine responses remain on stdout and human events on stderr. Log
level changes projection only; it never changes computation, validation,
publication, recovery, evidence, or exit behavior.

One operation owns one no-clobber log, delegated components do not append
concurrently, and receipts remain authoritative transaction markers. Logs are
protected operator data: no automatic upload, truncation, rotation, deletion,
or evidence promotion without a separate authorized relationship.

### Derive status from retained records

Persisted Run contracts, Attempt and task records, reporting records, receipts,
and owned-lock state remain status authority. Inspection may derive a read-only
projection from them but never persists a competing status. Snakemake text,
scheduler accounting, application logs, and terminal-renderer caches are
observations only; none establishes scientific or reporting completion.

The ordinary projection uses preparation, alignment, QC, candidate evidence,
statistical/context processing, and downstream reporting milestones. Reporting
may appear in progress without becoming a semantic scientific stage. Elapsed
time is labelled for the current or latest Attempt: running time is measured
from its admitted creation time to observation, and terminal time ends at its
receipt timestamp. Resumed Attempts remain separately visible; EMRYS does not
silently sum them or infer an ETA.

Task, transaction, engine, scheduler, receipt, and raw-stream detail remains
available through explicit expert or debug inspection. The current dashboard's
parsed human-output model is not retained as a second status authority. It is a
stale, frozen transitional surface: the architecture campaign does not update
or extend it, and status work proceeds independently from persisted records.
Retirement is reconsidered only after the architecture campaign is complete
and still requires separate approval for that exact public-surface removal.
