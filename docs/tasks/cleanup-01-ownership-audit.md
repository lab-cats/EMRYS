# CLEANUP-01 ownership and reference audit

This is a working design audit for the deferred
[CLEANUP-01 outcome](backlog_matrix.md#deferred-operational-work), based on
[PR #310](https://github.com/lab-cats/EMRYS/pull/310) at its checked
2026-09-22 head 2a7081b539006713ea146042e5c0d09aa4c083bd. Relative to
the audited implementation commit 1a58d2da8c2d232078c3e86b1be3d0d4241eb41e,
that head changes only `docs/tasks/release-readiness.md`; implementation source
is inherited from PR #307. This working audit records source discovery and
follow-up findings, not an accepted deletion design. The main backlog matrix
remains the authority for task status and acceptance; the
[CV-23 disposition](cluster_verification_backlog.md#cv-23-safe-project-or-artifact-cleanup)
records the original six classes and the absence of a proven retained
candidate. Recheck source and references if the target head changes.

The evidence level here is review of owner contracts, implementation, and
existing test cases. No product or owner fault tests, Project-data inventory,
institutional run, or deletion was performed for this audit. A source-described
protection is not proof that every runtime failure mode has been exercised.

## Decision question

Can one **retained** candidate class be shown to have an exclusive owner and a
complete, empty set of inbound references, with its recovery and evidence
consequences understood? Temporary files still controlled by their executing
transaction are a separate existing cleanup boundary. Age, missing success
receipts, scheduler disappearance, and apparent process absence do not answer
the question. A partial search yields **unknown**, never **unused**.

No class below currently passes this test. “No-go on current evidence” means
there is no authority to delete a retained member of that class; it does not
claim that every possible future subtype is inherently undeletable.

## Findings matrix

| ID | Retained class and owner | Established reference or recovery fact | Current finding | Next proof question |
| --- | --- | --- | --- | --- |
| F1 | Runs, older Attempts, reporting ledger and scientific artifacts; Run coordinator, Task and declared artifact owners | Downstream Runs bind source Run/Attempt/receipt/artifact content; resume reads older history, while reporting start/verified markers bind publication state. | No-go on current evidence. | Is there an exact subtype whose complete inbound Run, report and external references can be enumerated? |
| F2 | Native outputs, publication staging, locks and backups; Task, reporting, validation and reference-provenance publishers | Live transaction cleanup differs by owner; failed rollback can leave backups after a lock disappears. | No-go on current evidence. | Can ownership, writer quiescence and recovery safety be proved after process loss for one exact owner and path subtype? |
| F3 | Managed runtime generations and caches; Doctor and runtime owner | Project inventories and retained Attempt tool identities name generations or external dependencies; installed package identity is a separate positive Attempt reference. | No-go on current evidence. | What enumerates every current and historical Project, Attempt and package reference? |
| F4 | Qualification probes and receipts; storage qualification owner | The owner cleans known probes after durable publication; a site compute receipt names probes, while staged/final receipt names can share one inode. | No-go on current evidence. | Can any exact direct-probe remainder prove ownership, no writer and recovery safety after process loss? |
| F5 | Inputs, references, sidecars, source profiles and created roots; Project admission, onboarding, Step 00c and reconciliation owner | Admission binds content without exclusive ownership; generated roots can remain partial, while reference outputs and selected profiles may lie outside a Project. | No-go on current evidence. | Can any generated subtype be separated from external and cross-Run consumers? |
| F6 | Submission, streams and application records; Control, submission and logging owners | Retained requests feed inspection, watch, stop and association; project-free stream readers and bounded log scans prevent a Project roster from closing all references. | No-go on current evidence. | Can every request, stream and maintenance-record subtype close its historical and external readers without losing evidence? |

### Repo-wide supplemental owner matrix

This source pass inventoried physical publication/removal calls across
`src/emrys`, inspected stage and wrapper scripts, and traced their owner
contracts, callers and distinguishing fault tests. It separately inspected
`tests/tools` and `.github/workflows` for evidence retention boundaries.
This is a bounded source inventory, not a dynamic filesystem census or a
complete reverse-reference graph. S1–S20 refine or bound F1–F6; they do not
create new accepted cleanup classes. A source search can establish a known
reader or producer, but cannot close operator, external, cross-Project or
post-crash writer references.

| ID | Boundary and relation | Source finding | Disposition or proof gap |
| --- | --- | --- | --- |
| S1 | Step-validation report publication; F2 | Each validator can publish `<scope>.validation.tsv` with adjacent `.lock`, token `.tmp` and `.previous`; fault cases retain a predecessor without a lock or recovery marker. | No-go for retained residue; identify the exact caller output root and recovery state before any proposal. |
| S2 | Reference-provenance reconciliation; F2 and F5 | An explicit `--output-root` can hold three TSV finals, adjacent stage, backup and lock paths; failed restoration can strand all three backups without a lock. | No-go for retained residue or finals; operator and external readers of the caller-supplied root remain open. |
| S3 | Shared exclusive-file publication; F1–F5 | `publish_exclusive` creates `.emrys-stage` and, on replacement, `.displaced` paths for several distinct callers, removing only its live transaction state. | Unknown after process loss; suffix and helper identity do not substitute for the calling owner's proof. |
| S4 | Slurm batch scratch; F2/F6 execution boundary | The wrapper creates a private `TMPDIR` under configured `scratch_parent` and removes it in an EXIT trap; ordinary exit and TERM have focused tests. | Unknown after abrupt loss; path and scheduler status do not establish owner or writer quiescence. |
| S5 | Validation harness and hosted CI artifacts; scope boundary | The test runner retains failed or interrupted lane logs; synthetic E2E retains its operator root; CI uploads have configured expiry. | Separate from Project cleanup. Hosted expiry grants no local deletion authority. |
| S6 | Create-absent Project, manifest-draft and synthetic roots; F5 | One publisher reserves a caller-selected root, writes members and a completion member last, then preserves the whole partial tree on failure. | No-go for a partial root; completion-name presence or absence does not classify the tree or close external references. |
| S7 | Execution-profile source; F5 | Default, named or absolute external profile paths are re-read; Attempts retain the selected source path and hash. | Open historical and cross-Project references; distinguish these files from managed runtime inventories. |
| S8 | Retired producer residue; F2 | Owner contracts preserve characterized older anchor, backup and lock failure states even though current workers delegate publication to Task. | Unknown without exact artifact provenance; old path names are neither current producers nor deletion certificates. |
| S9 | Operator resource-benchmark output; scope boundary | An opt-in script retains per-trial streams, timings, hashes and summaries in a caller-selected absent directory, including failed trials. | Preserve under its operator evidence authority even if physically nested beneath a Project. |
| S10 | External R restoration environment; F3 scope boundary | Explicit `RENV_PROJECT` can own settings, locks, caches and libraries outside a managed Project generation. | External operator ownership and consumers remain open; managed cache inventory is not a universal R cache roster. |
| S11 | Run-local Snakemake metadata; F1 | The execution backend can mutate `.snakemake/` during retry, while EMRYS inspection does not use it as completion authority. | Opaque backend and possible foreign state; no source-backed retained deletion rule. |
| S12 | Doctor and Snakemake readiness scratch; F3 scope boundary | Read-only runtime probes use nested temporary directories under selected temporary storage and normally remove them on return. | Unknown after abrupt loss or custom `TMPDIR`; separate from managed repair cache and batch scratch. |
| S13 | Immutable reporting ledger; F1 and F2 | `start.json` precedes each report producer; `verified.json` binds that start and an admitted semantic receipt. Ordinary inspection treats unclosed starts and broken prefixes as blockers. | No-go for retained markers even when report outputs are absent or the scientific Attempt succeeded. |
| S14 | Project-free scheduler stream diagnostics; F6 | Explicit job/log paths and an offline OUT/ERR pair can be read without a Project request; automatic discovery has a narrower time and count budget. | Open first-party and operator readers; a discovery horizon or closed Project roster is no retention rule. |
| S15 | Hard-linked qualification aliases; F4 | Staged and final receipts can be the same inode; a probe source and its hard link also share bytes. | A retained staged marker is an admission blocker, not independent payload space to reclaim. |
| S16 | Installed EMRYS package tree; F3 scope boundary | An Attempt records exact package path/content/build identity, re-admitted for execution and new publication. | Positive historical reference outside managed runtime; completed report reuse has a narrower requirement. |
| S17 | Slurm profile external paths; F5 and F6 | Placement records `scratch_parent` and optional module-init path; the wrapper uses the parent and sources the init file. | External input and writer scope open; a profile YAML hash does not freeze module-init bytes. |
| S18 | Doctor and stop maintenance streams; F6 | Doctor's batch and sbatch streams and each exact-stop log/raw transcript live beside their maintenance log, possibly at a custom root. | Project request or default log rosters do not enumerate all diagnostic destinations. |
| S19 | Selected analysis-module dependencies; F3 and F5 | Extra executable, file and package-tree checks become retained Attempt tool identities when selected. | Search all retained check identities, not only standard tools, Project TSVs or donor seals; external ownership remains open. |
| S20 | Bounded application-log association; F6 | Inspection caps application directories and log bytes and reports `unknown` when a scan is incomplete. | A missing or unknown match cannot close the reverse-reference universe for cleanup. |

## First source discovery pass

### F1 — Runs, older Attempts and scientific artifacts

- **Observed ownership and references.** Run materialization publishes immutable
  bindings through [materialization.py](../../src/emrys/orchestration/run_coordinator/materialization.py).
  [Processing-source admission](../../src/emrys/orchestration/run_coordinator/inspection.py)
  binds the source Run ID, Attempt ID, receipt hash and artifact snapshots
  (lines 580–687). The [Run contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
  says downstream work reads source artifact paths without copying them
  (lines 882–899); resume refers to original Attempt manifests and history
  (lines 940–998).
- **Consequence.** Removing a source artifact or older record can block a later
  Run's admission, inspection or resume. The same contract defines the Run root
  as one durable history, including locks, partials, streams, failed Attempts
  and recovery evidence (lines 1224–1248). Existing
  [downstream-reuse tests](../../tests/orchestration/run_coordinator/test_materialization.py)
  and [historical-record tests](../../tests/orchestration/run_coordinator/test_lifecycle.py)
  characterize those dependencies (around lines 7247–7582 and 3995–4098).
- **Unresolved.** Map every inbound Run, report and external reader for a
  proposed *exact subtype*. A Project-local Run list does not establish a
  global absence of references.

### F2 — Native outputs, staging, locks and reporting partials

- **Observed ownership.** The Task
  [native publisher](../../src/emrys/orchestration/run_coordinator/task.py)
  captures identities for its own staging, finals and locks during one
  transaction, refuses pre-existing residue, and cleans under captured
  transaction ownership checks
  (lines 1491–1697). Reporting has distinct
  [manifest](../../src/emrys/reporting/_artifact_index/publication.py) and
  [HTML](../../src/emrys/reporting/_run_report/publication.py) publishers.
  [Step-validation reports](../../src/emrys/libraries/validation/publication.py)
  and [reference-provenance outputs](../../src/emrys/evidence/reference_provenance/reconciler.py)
  have two more publication and rollback boundaries (lines 13–70 and 52–127).
- **Recovery boundary.** The [Task contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
  preserves uncertain native writer state and old staging or backups
  (lines 1080–1091 and 1128–1133). The
  [reporting contract](../../src/emrys/reporting/README.md) preserves locks,
  partials, recovery markers and outputs when ownership or rollback is
  uncertain (lines 66–83). Existing
  [Task](../../tests/orchestration/run_coordinator/test_task.py) and
  [reporting](../../tests/reporting/test_report.py) fault cases retain foreign
  or partial state (around lines 810–859 and 1493–1551).
- **Unresolved.** The publisher's in-memory ownership captures are not a
  post-crash deletion certificate. A proposed retained subtype needs independent
  ownership, no-writer and recovery proofs. Native and reporting publication
  have different process and commit boundaries; the validation and reference
  publishers have further distinct failure behavior. Similar path names do not
  justify a shared cleanup policy.

### F3 — Managed runtime generations and caches

- **Observed references.** Doctor publishes managed generations and seals;
  borrower inventories bind an absolute donor seal path and digest. The
  [runtime contract](../../src/emrys/evidence/runtime_availability/README.md)
  requires old generations to remain available after donor repair and borrower
  replacement (lines 59–100). New Attempts retain their own runtime selectors
  through [materialization.py](../../src/emrys/orchestration/run_coordinator/materialization.py)
  (lines 1412–1420); [lifecycle.py](../../src/emrys/orchestration/run_coordinator/lifecycle.py)
  later re-admits them (lines 1244–1292). Checking only current Project
  inventories would miss historical references.
- **Recovery boundary.** Failed publication can retain a seal, generation and
  maintenance claim. Pixi and renv caches live under the managed root; linked
  R packages cannot be presumed disposable. Existing
  [runtime reuse tests](../../tests/orchestration/run_coordinator/test_onboarding.py)
  retain old selectors (around lines 3206–3309).
- **Unresolved.** There is no reverse borrower catalog. Establish the complete
  universe of borrower Projects and retained Attempt selectors, cache-to-library
  links, and active maintenance claims before proposing one exact generation.

### F4 — Qualification probes and receipts

- **Observed ownership.** The
  [storage qualification owner](../../src/emrys/evidence/storage_inventory/qualification.py)
  creates private probes, rechecks them, durably publishes a final receipt,
  then removes only its known probe roster (around lines 414–722). A staged
  marker blocks its own receipt route and re-execution; direct-mode admission
  can still accept separate valid site evidence. Cleanup failure can leave
  partial probes while final authority remains. The
  [storage contract](../../src/emrys/evidence/storage_inventory/README.md)
  requires that residue to remain inspectable.
- **References.** Site receipt identity uses the workspace and FASTA *parents*,
  which may serve more than one Project. Doctor and Attempts retain receipt
  path/hash checks through [doctor.py](../../src/emrys/orchestration/run_coordinator/doctor.py)
  and [lifecycle.py](../../src/emrys/orchestration/run_coordinator/lifecycle.py).
  Existing [fault cases](../../tests/evidence/storage_inventory/test_storage_inventory.py)
  exercise first, later and partial cleanup failures (around lines 432–555).
- **Unresolved.** Distinguish direct and site receipt roots; establish every
  root cohort and receipt reader, active phase, staged or foreign member, and
  recovery effect. A leftover probe is not automatically abandoned.

### F5 — Inputs, references and sidecars

- **Observed ownership.** [Project normalization](../../src/emrys/orchestration/run_coordinator/normalization.py)
  admits declared FASTQs, FASTA/GTF, manifests and regions by path and content
  but permits Project-relative or absolute source paths. The
  [Run contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
  keeps FASTQs, references and region files at declared locations
  (lines 35–48 and 98–103). Project-created manifests must be distinguished
  from the external files they name.
- **References.** [Step 00c](../../src/emrys/stages/fasta_sidecars/CONTRACT.md)
  produces FAI and dictionary files beside the declared FASTA, reuses a
  complete unchanged pair and supplies later stages, provenance, inventory and
  reporting (lines 34–45, 65–74 and 109–122). The Run owner retains a
  cross-Run sidecar lock. Existing
  [sidecar tests](../../tests/orchestration/run_coordinator/test_task.py)
  cover complete-pair reuse and partial-pair refusal (around lines 2970–3038).
- **Unresolved.** Split Project-generated manifests, external declared inputs
  and generated sidecars into exact path subtypes. Determine whether any
  subtype has a finite consumer universe; creator or location alone proves
  neither exclusive ownership nor absence of external use.

### F6 — Submission and application records

- **Observed ownership and readers.** [Control](../../src/emrys/orchestration/run_coordinator/control.py)
  creates and synchronizes a private request directory before submission
  (around lines 1057–1081 and 1165–1209). The
  [submission owner](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
  retains raw sbatch invocation transcripts and enumerates partial as well as complete
  requests (around lines 477–632 and 905–1005). Retained requests feed
  duplicate-submission checks, inspection, watch, exact-request stop and
  application-to-Run association through
  [submission inspection](../../src/emrys/orchestration/run_coordinator/_submission_inspection.py).
  Retained requests also feed inspection with a selected request and ordinary
  watch target discovery
  ([control.py](../../src/emrys/orchestration/run_coordinator/control.py),
  around lines 2731–2756 and 3033–3063).
- **Evidence boundary.** The
  [logging contract](../design/LOGGING_CONTRACT.md) preserves application
  logs and partials; a custom absolute log root can place them outside the
  Project. Legacy request versions and ambiguous scheduler replies remain
  historical diagnostic inputs. Existing
  [submission tests](../../tests/orchestration/run_coordinator/test_slurm_submission.py)
  preserve partial responses; [inspection tests](../../tests/orchestration/run_coordinator/test_submission_inspection.py)
  check drift and historical associations.
- **Unresolved.** Inventory request context, raw streams, application logs and
  legacy variants separately. Terminal scheduler state may remove one duplicate
  warning, but does not remove inspection, stop, association or evidence use.

## Path subtype and reference pass

The next source pass split each broad class into paths with different producers
and readers. **Local roster known** means the owner's expected filenames can
be identified; it does not mean external references are absent. **Open** means
a cross-boundary reader is known. **Unknown** means the available authority
cannot close the reference, ownership or writer question. None of these labels
is deletion eligibility.

### F1 path subtypes

- **Run contract and Attempt records — local roster known, overall open.**
  The Run contract and each Attempt's manifest, request, receipts and released
  lock record feed inspection, resume and reporting. A later Run can bind the
  original Attempt. The roster is checked by
  [Attempt inspection](../../src/emrys/orchestration/run_coordinator/_inspection_attempts.py),
  which requires one linear execute-to-resume chain, a terminal receipt on
  every superseded Attempt, and retained predecessor request and lock records
  (lines 63–106 and 121–336). A downstream processing Run re-admits its bound
  source from the same Project during
  [inspection](../../src/emrys/orchestration/run_coordinator/inspection.py)
  (lines 376–393 and 580–687). These are forward readers, not a
  reverse-reference catalog.
- **Reporting start and verified ledger — local roster known, recovery open.**
  The [reporting operation](../../src/emrys/orchestration/run_coordinator/reporting_operation.py)
  publishes `state/reporting/<kind>/start.json` before each producer and
  `verified.json` only after semantic receipt admission (lines 312–358).
  [Ledger inspection](../../src/emrys/orchestration/run_coordinator/reporting_boundary.py)
  binds verified to the exact start and receipt. Ordinary inspection treats a
  start-only entry, verified-without-start entry or broken transaction prefix
  as a blocker; its exact current-origin exception recognizes in-progress
  state without discarding it (lines 265–333 and 822–878). The
  [owner tests](../../tests/orchestration/run_coordinator/test_reporting_boundary.py)
  distinguish these states (around lines 280–345 and 735–754). A successful
  scientific Attempt or missing report output does not make a retained start
  disposable; the ledger is a separate recovery and diagnostic record.
- **Task starts, terminal records, streams and verified references — local
  roster known, external use unknown.** They feed Attempt receipts, inspection,
  resume and reporting attribution. Their absence can change the admission
  result even if final native files remain.
- **Native products, Results and reporting publications — open.** Downstream
  Tasks, reused Runs, report validation and scientist-facing transfer read
  these paths. The [Run-root contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#run-root-contract)
  lists their distinct authorities.
- **Report input paths and publication roots — open.** The private
  [reporting owner](../../src/emrys/reporting/README.md#code-and-artifact-roots)
  admits an explicit artifact source root independently of its output roots;
  [HTML receipts](../../src/emrys/reporting/_run_report/receipt.py) retain
  exact data-input paths and hashes, including provider and figure inputs
  (lines 74–99). The production
  [Run coordinator](../../src/emrys/orchestration/run_coordinator/reporting_operation.py)
  pins the artifact source and both output roots to its selected Run (lines
  78–107). A root-local file list does not close a report receipt's input
  references, and the private library's broader root boundary must not be
  misreported as the current public `emrys report` destination.
- **Snakemake metadata — backend state unknown.**
  [Lifecycle](../../src/emrys/orchestration/run_coordinator/lifecycle.py)
  executes Snakemake with the Run root as its working directory and forbids
  engine cleanup or unlock flags (lines 605–630). The fixed
  [profile](../../src/emrys/workflow/profiles/local/profile.v9+.yaml) keeps
  incomplete outputs, and the [resume binding](../../src/emrys/orchestration/run_coordinator/run_implementation.py)
  selects the backend's incomplete-output behavior (lines 24–32). EMRYS
  [inspection](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
  does not treat `.snakemake/` as completion authority (lines 1151–1155),
  while a [retry test](../../tests/orchestration/run_coordinator/test_materialization.py)
  observes engine metadata mutation (around lines 6678–6688). A
  [foreign-member test](../../tests/orchestration/run_coordinator/test_lifecycle.py)
  leaves `.snakemake/foreign` in a successful Run (around lines 1767–1773).
  Neither status independence nor an engine directory name proves its contents
  disposable or its writer universe closed.
- **Uncommitted Run quarantine — unknown.**
  [Materialization](../../src/emrys/orchestration/run_coordinator/materialization.py)
  admits only a real root with no `run.json` and at most regular, nonsymlink
  `contract/analysis.json` and `execution-plan.json` members (lines 1620–1661).
  It renames this narrow prebinding residue under an attempt-specific
  `.uncommitted-*` name, refusing a name collision (lines 1664–1727).
  [Fault tests](../../tests/orchestration/run_coordinator/test_materialization.py)
  distinguish prebinding quarantine from exact postbinding reuse and blocked
  postbinding obstruction (lines 2339–2439). A bounded search of current
  `src/emrys` finds the `.uncommitted-*` name only at this producer, with no
  automatic reader by that name. Quarantine still preserves the bytes, and
  that source search cannot close operator or external references.

### F2 path subtypes

- **Native work, scratch, owner locks and partially linked finals — unknown
  after process loss.** The [Task publisher](../../src/emrys/orchestration/run_coordinator/task.py)
  captures parent, stage and lock identities with an owner token. It rolls
  back only finals linked to captured staging snapshots and removes the lock
  only while its contents still match that owner (lines 1491–1576 and
  1625–1697). Pre-existing or changed state blocks that live authority.
- **Artifact-summary stage, lock, recovery marker and partial finals —
  unknown.** The [manifest publisher](../../src/emrys/reporting/_artifact_index/publication.py)
  stages two TSVs and JSON together, then links JSON last (lines 94–122 and
  162–199). It retains control anchors on incomplete rollback (lines 200–282),
  while
  [transaction validation](../../src/emrys/reporting/transaction_validation.py)
  refuses recognized owner-control residue (lines 440–476 and 643–650).
- **HTML-report stage, lock, recovery marker and partial finals — unknown.**
  The [HTML publisher](../../src/emrys/reporting/_run_report/publication.py)
  stages two views and a receipt, then links the receipt last (lines 112–180).
  It preserves control state after uncertain rollback (lines 181–261).
  Validation recognizes older `.previous` names for these *report-output*
  basenames. A bounded search found no current HTML-report producer for those
  names; the distinct step-validation and reference-provenance owners below
  do create `.previous` backups, so suffix alone does not identify the owner.
  The shared [stage remover](../../src/emrys/reporting/_files.py) checks a captured
  directory device/inode and token only during live publication (lines 85–100);
  neither it nor recognized-name validation certifies post-crash deletion.
- **Step-validation report final, lock, stage and predecessor — unknown.** The
  [shared validator runtime](../../src/emrys/libraries/validation/runtime.py)
  sends a caller-supplied output path to the
  [validation publisher](../../src/emrys/libraries/validation/publication.py)
  (lines 27–49 and 13–70). Task later binds a report under its verified output
  contract ([task.py](../../src/emrys/orchestration/run_coordinator/task.py),
  lines 2771–2807 and 2893–2920), but the validator's own publication is a
  separate transaction. Its [owner contract](../../src/emrys/libraries/validation/README.md)
  and [characterization tests](../../tests/libraries/test_validation_report.py)
  document a late foreign final removed on rollback, a predecessor stranded
  as `.previous` after failed restoration without a lock or recovery marker,
  and retained stage or lock after cleanup failure (tests around lines
  507–665). These are observed defects, not a recovery procedure. An absent
  lock, visible final or nominally complete Task is no deletion certificate.
- **Reference-provenance final trio, stage, predecessor and lock — unknown.**
  [Reconciliation](../../src/emrys/evidence/reference_provenance/reconciler.py)
  publishes three TSVs under caller-supplied `<output-root>/<reference-id>/`
  and moves predecessors to token `.previous` paths before replacing finals
  (lines 26–36 and 52–127). The
  [owner contract](../../src/emrys/evidence/reference_provenance/README.md)
  records incomplete backup and restoration behavior. Its
  [fault test](../../tests/evidence/reference_provenance/test_reference_provenance.py)
  leaves three backups after failed restoration with no lock or recovery
  marker (around lines 462–517). Treat finals, stage, backups and lock as one
  recovery context, including when the root lies outside the Project.
- **Historical worker backups, anchors and locks — provenance unknown.**
  Current scientific workers receive staging destinations from Task; the
  retained [canonical-BAM](../../src/emrys/stages/canonical_bam/CONTRACT.md),
  [split-N-cigar](../../src/emrys/stages/split_n_cigar/CONTRACT.md) and
  [scientific-context](../../src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/CONTRACT.md)
  contracts separately record old producer failure states (around lines
  82–118, 62–69 and 98–112). These include anchor cleanup failures,
  predecessor restoration loss, and a linked final without its old staging
  anchor or lock. Those producers are retired, so the old cases are historical
  recovery evidence, not a claim that current Task produces the same residue.
  No Project-data census establishes whether any such paths survive; if they
  do, neither current publisher behavior nor absent old locks authorizes
  deleting them.
- **Shared exclusive-publication stage and displaced names — unknown.** The
  [library primitive](../../src/emrys/libraries/exclusive_publication.py)
  creates `.<final>.<token>.emrys-stage` for exclusive publication and a
  `.displaced` sibling when replacing an exactly admitted predecessor (lines
  23–141). Lifecycle, Task, reporting boundary, Doctor, qualification and
  onboarding call it. The primitive checks identity and removes its own stage
  or displaced name during the live call; any retained member after process
  loss must be traced through its caller's contract and evidence. A generic
  suffix scan would mix different authorities.
- **Live Run lock and prepared finalization — local roster known, deletion
  blocked.** [Lifecycle](../../src/emrys/orchestration/run_coordinator/lifecycle.py)
  promotes captured Run lock and prepared receipt sources to same-inode
  released or terminal aliases, then unlinks the exact source aliases during
  live finalization (lines 796–899 and 2224–2280). The
  [Run contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
  keeps interrupted aliases as recovery state (lines 1008–1043). This narrow
  transition is not a post-run cleanup rule for other records.

### F3 path subtypes

- **Current Project runtime inventory — locally selected, still needed.**
  Runtime discovery and Doctor create or replace this selection; Doctor and
  future Runs read it. Historical Attempt selectors remain independent.
- **Initial and replacement managed generations — open.**
  [Doctor](../../src/emrys/orchestration/run_coordinator/doctor.py) can first
  publish `runtime/managed` with a root `runtime/shared.json` and later publish
  `runtime/generations/<id>/managed` with a generation seal (around lines
  912–970, 1109–1191 and 1824–1876). Either shape may remain named by current
  or historical selectors; a generations-only scan misses the initial shape.
- **Retained Attempt runtime selector — open.** Each Attempt freezes an exact
  runtime profile under its Run contract; lifecycle re-reads it, and resume
  can use a predecessor selector when the current Project inventory is absent.
  Its immutable `required_tools` also record selected `path` and
  `resolved_path` identities
  ([doctor.py](../../src/emrys/orchestration/run_coordinator/doctor.py),
  lines 304–365); searching only profile TSVs misses these retained paths.
- **Selected analysis-module dependencies — positive external references.**
  [Doctor](../../src/emrys/orchestration/run_coordinator/doctor.py) adds a
  selected module's executable, R namespace, file and package-tree checks to
  runtime inspection (lines 416–481), then projects *all passing observations*
  into retained Attempt `required_tools` identities (lines 304–369).
  [Lifecycle](../../src/emrys/orchestration/run_coordinator/lifecycle.py)
  re-derives and compares the full list (lines 1270–1339). A complete scan of
  retained Attempts can find these positive path references; a scan limited
  to fixed tool names, Project TSVs or donor seals cannot. The selected paths
  may be external, and binding them does not make them EMRYS-owned.
- **Installed EMRYS package tree — positive Attempt reference, separate owner.**
  [Materialization](../../src/emrys/orchestration/run_coordinator/materialization.py)
  freezes `installed_package`; the
  [package authority](../../src/emrys/libraries/source_authority.py) records
  its executing path, content hash and build/lock provenance (lines 55–115).
  [Lifecycle](../../src/emrys/orchestration/run_coordinator/lifecycle.py)
  re-admits the exact installed identity for execution and resume (lines
  1194–1216 and 1495–1503). New reporting publication also attests its
  package, while an already complete report can be inspected or reused under
  a narrower rule
  ([reporting boundary](../../src/emrys/orchestration/run_coordinator/reporting_boundary.py),
  lines 898–925). This installed tree is neither a managed generation nor a
  Git checkout cleanup candidate. Retained Attempt provenance supplies a
  positive reference but no reverse package-user catalog.
- **Donor seals and managed generations — open across Projects.** Current
  borrower inventories and retained Attempt selectors can point to older
  seals and fixed tool paths after donor repair. The current
  [profile parser](../../src/emrys/evidence/runtime_availability/_profile_contract.py)
  admits `runtime/shared.json` or `runtime/generations/<32-hex>/shared.json`
  seal paths and records the absolute seal path, hash and borrower Python
  (lines 81–119). Parsing allows a missing seal for later admission; it does
  not prove that an absent file had no borrower. Ordinary runtime inventories
  also accept absolute tool and library paths without a shared seal (lines
  304–324). They could name a managed generation directly; this is an
  inference from permitted paths, not a tested cross-Project fixture. No
  reverse borrower list exists in the
  [runtime owner](../../src/emrys/evidence/runtime_availability/README.md#sealed-managed-runtime-reuse).
- **Managed caches — unknown.** Doctor scopes Pixi and renv caches within its
  selected generation and uses repair scratch there
  ([doctor.py](../../src/emrys/orchestration/run_coordinator/doctor.py),
  lines 1164–1175, 1208–1232 and 1756–1762). Sealed R package trees may link
  into that managed tree
  ([_profile_contract.py](../../src/emrys/evidence/runtime_availability/_profile_contract.py),
  lines 228–244). A seal can prove a positive reference through such an
  internal link, as [tested](../../tests/evidence/runtime_availability/test_runtime_availability.py)
  (lines 1427–1460); it does not cover the whole managed directory. Neither a
  generation name nor a cache path is a complete cache-object consumer roster.
  Package-manager cache paths and `cache/repair-*` scratch have different
  owners and lifetimes; neither basename establishes post-crash quiescence.
- **Doctor readiness and nested backend probe scratch — live cleanup only.**
  A [Doctor read-only check](../../src/emrys/orchestration/run_coordinator/doctor.py)
  uses `emrys-doctor-*` temporary storage (lines 603–613); its
  [Snakemake probe](../../src/emrys/evidence/runtime_availability/_probes.py)
  creates nested `emrys-snakemake-*` scratch under selected `TMPDIR`, using it
  for HOME and cache paths (lines 156–184). The
  [runtime tests](../../tests/evidence/runtime_availability/test_runtime_availability.py)
  cover ordinary return and failure cleanup (around lines 132–195). These
  directories are separate from managed `cache/repair-*` and Slurm batch
  scratch. Abrupt loss or an external `TMPDIR` leaves later ownership and
  writer quiescence unknown.
- **External operator R environment — outside the managed-generation roster.**
  The opt-in [renv owner](../../src/emrys/renv/README.md) describes a separate
  explicit `RENV_PROJECT` for bootstrap settings, locks, staging and caches,
  plus operator-owned libraries (lines 3–28). Its
  [restoration script](../../src/emrys/resources/runtime/restore_r_environment.R)
  requires that external project and lock, then calls `renv::restore` with
  `clean = FALSE` (lines 43–80). Managed Project generation inspection cannot
  enumerate or authorize cleanup of these external paths; their operator and
  package-manager references remain open.
- **Maintenance claim — owner known, quiescence unknown.** A retained claim
  blocks admission and records unresolved repair or selector publication.
  Runtime reuse checks the donor claim before probing; borrower replacement
  holds a separate claim while changing only its runtime inventory
  ([onboarding.py](../../src/emrys/orchestration/run_coordinator/onboarding.py),
  lines 2148–2251). Claim age does not prove package-manager descendants
  stopped.

### F4 path subtypes

- **Direct receipt generations — historical references open.** Doctor and
  Attempts bind their exact path/hash; a newer current receipt does not erase
  older Attempt identities. Direct receipts live beneath the Project's
  `runtime/.emrys-storage-qualification/`, with an optional `.N` generation
  suffix. A failed latest receipt is preserved while planning a successor
  ([qualification.py](../../src/emrys/evidence/storage_inventory/qualification.py),
  lines 174–268). Admission selects the latest generation (lines 725–799), so
  preserving an older receipt alone does not ensure a bound Attempt can resume.
- **Site compute and final receipts — cross-Project references open.** A final
  receipt binds the compute receipt's path and hash and re-reads it on final
  admission (lines 817–847 of
  [qualification.py](../../src/emrys/evidence/storage_inventory/qualification.py)).
  These receipts live under the workspace parent's
  `.emrys-storage-qualification/`; their identity derives from that parent and
  the FASTA parent, which multiple Projects may share (lines 147–171 and
  270–284). The compute receipt also records the exact probe paths and hashes
  (lines 480–548).
- **Staged markers — recovery state unknown.** A marker blocks admission and
  re-execution for its own receipt route after an uncertain publication
  boundary. A pending direct marker blocks direct receipt admission; a valid
  independent site receipt can still satisfy direct-mode requirements
  ([qualification.py](../../src/emrys/evidence/storage_inventory/qualification.py),
  lines 223–232 and 802–827). Publication hard-links staged to final before
  unlinking the staged name (lines 304–313). A
  [fault test](../../tests/evidence/storage_inventory/test_storage_inventory.py)
  confirms a retained staged+final pair can be the same inode (around lines
  465–493). Such a marker is an admission blocker, not another receipt's
  payload bytes to reclaim. The probe's `fsync-source.bin` and `hardlink.bin`
  likewise share an inode (qualification lines 425–444); path counts are not
  content-byte savings estimates.
- **Probe directories — transaction cleanup known, retained state unknown.**
  The [qualification owner](../../src/emrys/evidence/storage_inventory/qualification.py)
  checks an exact four-member roster during its cleanup (around lines 582–637).
  Its site compute receipt records each probe directory, and the final receipt
  binds that compute receipt (lines 470–510 and 665–669); a retained site probe
  therefore has a historical receipt reference. The direct receipt does not
  name its probes (lines 688–717), though the two role-specific paths are
  deterministic and reused across direct receipt generations (lines 174–209).
  Direct admission does not reread probe bytes or require their absence (lines
  725–799). When a new direct plan is otherwise possible, occupied probe paths
  block it (lines 235–268). The probe's `flock` tests storage capability, not
  lifetime publisher ownership (lines 445–458). Both routes publish the final
  receipt before probe cleanup (lines 681–685 and 718–722). A partial cleanup
  can leave an incomplete directory with a valid final receipt, as
  characterized by
  [fault tests](../../tests/evidence/storage_inventory/test_storage_inventory.py)
  (around lines 513–557). Re-running the current cleanup cannot be presumed
  to admit every retained partial; the absence of a probe path in the direct
  receipt proves neither post-crash ownership nor writer quiescence.

### F5 path subtypes

- **Partial create-absent roots — owner and external references open.** The
  shared [tree publisher](../../src/emrys/orchestration/run_coordinator/onboarding.py)
  reserves an absent output directory, writes members, publishes a completion
  member last and preserves the entire partial root on any failure, even when
  that member exists but fails readmission (lines 580–651). The callers are
  [Project creation](../../src/emrys/orchestration/run_coordinator/onboarding.py)
  with `project.yaml` last (around lines 1376–1390), manifest-draft creation
  with `samples.tsv` last (around lines 1563–1595), and
  [synthetic fixture creation](../../src/emrys/orchestration/run_coordinator/synthetic_fixture.py)
  with `fixture.manifest.json` last (around lines 732–785). The
  [Project contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
  refuses adoption or overwrite of partial Project roots (lines 135–145);
  [tests](../../tests/orchestration/run_coordinator/test_onboarding.py)
  retain a root lacking Project YAML after input drift and characterize a
  present-but-invalid completion member (around lines 1044–1075 and
  1873–1901). Completion-name presence, absence or physical location cannot
  classify these three caller-owned roots as deletable.
- **Project-created samples and partitions manifests — Project-local readers
  known, wider references open.** [Onboarding](../../src/emrys/orchestration/run_coordinator/onboarding.py)
  authors or copies these members and publishes Project YAML last
  (around lines 1099–1160 and 1376–1390). Imported sample and partition
  manifests are normalized into Project-local copies; FASTQ and region paths
  resolve from their respective supplied manifest parents (lines 1099–1160).
  [Tests](../../tests/orchestration/run_coordinator/test_onboarding.py)
  preserve supplied partition bytes and an external BED reference (lines
  1521–1592). New admission reads the copies, while Run and Attempt snapshots
  can retain their content. Other Projects may declare absolute paths to
  either original or copy; Project ownership does not close that search.
- **Run-local selected samples projection — bound to Attempt history.**
  [Materialization](../../src/emrys/orchestration/run_coordinator/materialization.py)
  publishes a projection only for a selected subset at
  `contract/workflow-inputs/<attempt>/samples.tsv` (around lines 1338–1376).
  [Resume tests](../../tests/orchestration/run_coordinator/test_materialization.py)
  retain the predecessor projection after an authored-manifest edit (lines
  7391–7444). Its directory is owner-local, but resume and Attempt evidence
  still require it.
- **Declared FASTQs, FASTA/GTF and regions — ownership and references open.**
  Project setup names their existing locations. Normalization admits bytes,
  not exclusive file ownership or a complete list of external consumers.
- **Execution-profile source — positive Attempt references, external use open.**
  [Profile selection](../../src/emrys/orchestration/run_coordinator/execution_profile.py)
  reads the Project default, a named Project profile or an absolute external
  path (lines 92–120). An Attempt's placement records the exact selected
  source path and SHA-256 (lines 293–313), and
  [resume admission](../../src/emrys/orchestration/run_coordinator/control.py)
  re-reads the selected file and rejects source-byte drift (around lines
  823–867 and 1705–1721). The [Run contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
  also names Doctor, Run and report readers (lines 729–746). Retired adjacent
  configuration names block omitted-default migration rather than becoming
  cleanup residue (execution-profile lines 92–109). These source YAML files
  are distinct from F3's managed runtime inventory; an absolute selection
  could be shared across Projects, and a historical Attempt is already a
  positive inbound reference.
- **Slurm module-init file and scratch parent — external path references.**
  A selected [placement](../../src/emrys/orchestration/run_coordinator/execution_profile.py)
  records `scratch_parent` and optional `modules.init` paths in its Attempt
  document (lines 145–172 and 293–313). The
  [batch wrapper](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
  checks and sources the exact module-init file, then creates its private
  scratch under that parent (lines 687–713 and 749–773). The profile binding
  hashes the selected YAML source, not the later module-init file bytes
  (execution-profile lines 48–54 and 281–291). These paths can be
  operator-owned or shared; a recorded string establishes a reference, not
  EMRYS ownership or an immutable copy of external initialization code.
- **FAI and dictionary beside the FASTA — open.** EMRYS can produce an exact
  pair, but the parent may be shared, complete pairs can be reused across Runs,
  and a cross-Run lock protects publication. A partial pair blocks work. The
  [Task boundary](../../src/emrys/orchestration/run_coordinator/task.py)
  permits exactly this pair outside the Run root, snapshots a complete existing
  pair, and rejects replacement during reuse (lines 1300–1445).
  [Step 00c](../../src/emrys/stages/fasta_sidecars/CONTRACT.md) publishes no
  creator receipt or transaction summary (lines 34–49); a complete pre-existing
  pair can be adopted. The source therefore cannot identify an existing pair
  as EMRYS-created cleanup residue. The lock and forbidden staging patterns
  carry writer and recovery meaning
  ([materialization.py](../../src/emrys/orchestration/run_coordinator/materialization.py),
  lines 845–859).
- **Reference-provenance TSVs — external use open.**
  [Reconciliation](../../src/emrys/evidence/reference_provenance/reconciler.py)
  checks one explicit FASTA/FAI/dictionary/GTF/BED12/STAR inventory and
  publishes artifact, contig and summary TSVs under a caller-supplied root;
  it neither repairs nor regenerates the declared sources (lines 26–36 and
  130–175). The [inventory loader](../../src/emrys/evidence/reference_provenance/_reference_inventory.py)
  resolves its own absolute or base-relative source paths independently of a
  Project manifest (lines 21–122). Its input files and output evidence have
  separate reference universes. A bounded `src/emrys` search found only the
  publisher's filename constants, not an automatic reader for its named TSV
  finals. That negative source result does
  not close operator or external readers, nor does it establish that the
  source reference files are owned by reconciliation. Publication residue has
  the separate F2 recovery boundary above.

### F6 path subtypes

- **Request context — Project roster known, historical readers open.**
  Control writes the exact request before sbatch. Its identity and contents
  support duplicate checks, inspection, watch, exact-request stop and
  correlation with an application log and Run. Version 4 records the UID,
  command, Project, requested Run, analysis, application-log root, profile,
  delegate arguments, scheduler stream patterns/name and time; Control syncs
  it before sbatch
  ([control.py](../../src/emrys/orchestration/run_coordinator/control.py),
  lines 1170–1209). Terminal status only removes the duplicate-submission
  warning; inspection, watch discovery and exact stop still select retained
  records ([control.py](../../src/emrys/orchestration/run_coordinator/control.py),
  lines 226–243, 1114–1133 and 2222–2300). A locally enumerable roster is
  not proof that human selectors or historical uses have ended.
- **Raw sbatch.stdout and sbatch.stderr — request-local, still consumed.**
  The [submission owner](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
  retains both invocation transcripts. Stdout is the sole recorded scheduler
  response; deleting either can make a request partial or unconfirmed.
  Enumeration keeps v1–v4 and partial records (lines 477–632). A missing
  stderr can leave a parsed job ID but prevent exact scheduler observation
  ([tests](../../tests/orchestration/run_coordinator/test_slurm_submission.py),
  lines 664–689 and 979–1002). Selected-request association needs a complete
  token-bound v2–v4 record and rechecks all three members
  ([_submission_inspection.py](../../src/emrys/orchestration/run_coordinator/_submission_inspection.py),
  lines 417–505). Complete v1 lacks request-specific stream identity, whereas
  exact stop requires a complete named v3/v4 request
  ([slurm_submission.py](../../src/emrys/orchestration/run_coordinator/slurm_submission.py),
  lines 225–245 and 303–327). Legacy or partial records remain diagnostic
  evidence rather than deletion candidates.
- **Slurm job output and error streams — writer and references open.** Slurm
  writes separate job files at paths frozen into the request. Exact scheduler
  observation compares those recorded *paths* with scheduler metadata
  ([scheduler_observation.py](../../src/emrys/orchestration/run_coordinator/scheduler_observation.py),
  lines 94–150 and 158–241); watch tails read the stream bytes
  ([_inspection_presentation.py](../../src/emrys/orchestration/run_coordinator/_inspection_presentation.py),
  lines 496–528). Terminal status alone does not close the external reader or
  writer question.
- **Project-free stream selection — first-party historical readers open.**
  [Control](../../src/emrys/orchestration/run_coordinator/control.py) can route
  exact `--job-id`/`--log-dir` or offline `--out`/`--err` to the dashboard
  without Project, Run or request admission (lines 2632–2724). The
  [dashboard](../../src/emrys/orchestration/run_coordinator/dashboard.py)
  admits an exact UID-owned stream pair and reads it (lines 502–563 and
  751–779); a [test](../../tests/orchestration/run_coordinator/test_inspection_presentation.py)
  reads legacy streams without a Project or scheduler query (around lines
  1262–1306). Automatic discovery's seven-day/50-candidate bound is a UI
  selection limit (dashboard lines 240 and 566–660), while explicit historical
  paths remain readable. Neither a missing request nor discovery timeout is a
  stream-retention rule.
- **Run and reporting application JSONL — custom-root references open.** The
  [logging owner](../../src/emrys/libraries/application_logging/storage.py)
  can publish under an absolute log root outside the Project. Selected
  requests, explicit Run inspection and watch consume historical entries.
  Historical Run-log discovery can rebind retained Run/Attempt authority even
  when current Project YAML is gone
  ([_submission_inspection.py](../../src/emrys/orchestration/run_coordinator/_submission_inspection.py),
  lines 543–609). An unfinished but newline-complete log can still bind a
  request ([tests](../../tests/orchestration/run_coordinator/test_submission_inspection.py),
  lines 225–249); a truncated line is rejected by the parser, yet retained as
  evidence (lines 168–173 of the inspector). Run contracts do not retain custom
  historical log roots
  ([Run contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md),
  lines 532–550). The [logging contract](../design/LOGGING_CONTRACT.md)
  forbids automatic rotation
  or deletion (lines 144–169).
- **Bounded application association — unknown is not an empty reference set.**
  The [inspector](../../src/emrys/orchestration/run_coordinator/_submission_inspection.py)
  caps application-directory and log-byte scans (lines 34–38); historical
  Run discovery shares its directory budget across `pending` and exact Run
  scopes and reports `unknown` on incomplete admission (lines 543–609).
  [Tests](../../tests/orchestration/run_coordinator/test_submission_inspection.py)
  retain an earlier match while a later directory or byte limit makes the
  result unknown (around lines 480–513 and 846–871). These bounds protect
  inspection; a cleanup preview cannot turn an absent or unknown association
  into proof that no application record refers to the Run or request.
- **Incomplete application-log attempt directory — source inference, unknown.**
  [Storage](../../src/emrys/libraries/application_logging/storage.py)
  exclusively creates an Attempt directory before creating its JSONL file and
  closes descriptors without removing created directories when initialization
  fails (lines 124–160 and 179–209). A later open of the same Attempt name
  refuses an existing directory. This suggests that an interrupted open can
  leave an empty or partial directory that blocks retry; no focused fault case
  here proves an exact survivor. Its path, location and missing JSONL are
  insufficient ownership or deletion evidence.
- **Maintenance JSONL and raw siblings — separate roster, open.** Doctor's
  waited qualification stores `slurm-submit.stdout` and `.stderr` beside its
  maintenance log
  ([doctor.py](../../src/emrys/orchestration/run_coordinator/doctor.py),
  lines 1620–1627). Exact stop records `scancel.stdout` and `.stderr` paths in
  synchronized intent beside `emrys-stop.jsonl`
  ([control.py](../../src/emrys/orchestration/run_coordinator/control.py),
  lines 2456–2499). Doctor also retains `package-output.log` as a separate
  package-manager byte stream, with its path in repair diagnostics
  ([doctor.py](../../src/emrys/orchestration/run_coordinator/doctor.py),
  lines 1705–1720 and 1754–1795) and an
  [operator recovery route](../operations/TROUBLESHOOTING.md) (lines 181–200).
  These records are outside the private
  `submission-*` roster and have distinct operator or source readers. The lack
  of an application-JSONL parser for a raw stream does not make its bytes
  disposable.
- **Doctor and exact-stop diagnostic roots — cross-root roster open.**
  Doctor's compute qualification places `emrys-doctor-%j.out/.err` next to
  its maintenance log and separate sbatch invocation transcripts
  ([doctor.py](../../src/emrys/orchestration/run_coordinator/doctor.py),
  lines 1571–1627). Exact stop derives its default log root from the selected
  request's recorded `application_log_root`, with supported overrides; each
  execution opens a new maintenance Attempt with `emrys-stop.jsonl` and raw
  `scancel` siblings
  ([control.py](../../src/emrys/orchestration/run_coordinator/control.py),
  lines 2405–2417 and 2456–2499). A
  [custom-root test](../../tests/orchestration/run_coordinator/test_materialization.py)
  retains stop diagnostics outside the default Project log path (around lines
  3945–3991). The private `submission-*` roster and default Project logs do
  not enumerate these diagnostic destinations.
- **Slurm batch scratch — live wrapper cleanup, retained state unknown.** The
  [submission wrapper](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
  creates `emrys-${SLURM_JOB_ID}.XXXXXX` beneath the configured scratch parent,
  exports it as `TMPDIR`, and removes that exact path in an EXIT trap (lines
  749–774). [Focused tests](../../tests/orchestration/run_coordinator/test_slurm_submission.py)
  exercise ordinary exit and TERM cleanup (around lines 2029–2152). The
  [RUNBOOK](../operations/RUNBOOK.md#temporary-files) records site lifetime
  limits. An abrupt loss can bypass an EXIT trap; a later path match or
  terminal scheduler state does not establish exclusive ownership, complete
  contents or absence of descendants still writing there.

### Validation and hosted evidence boundary

These paths are part of repository validation, not a seventh Project cleanup
class. The [lane runner](../../tests/tools/run_validation.py) copies failed or
interrupted logs to retained paths before unlinking its transient lane log
(lines 224–240 and 390–473). The
[synthetic E2E driver](../../tests/tools/real_synthetic_e2e.py) records a
complete retained operator root and preserves failure partials (lines
2338–2368). The [CI workflow](../../.github/workflows/ci.yml) configures
7- or 14-day hosted upload retention for coverage and synthetic or golden-path
evidence (around lines 860–899, 936–946 and 1294–1383). That hosting policy
does not transfer ownership or authorize removal of local Project, operator
or scientific evidence. Validation-specific transient log cleanup is not a
model for retained Run or Project cleanup.

The [Python shard tool](../../tests/tools/python_test_shards.py) writes
selection receipts before the complete-suite coverage job reads and checks
them (around lines 169–196, 245–266 and 360–375); the
[CI workflow](../../.github/workflows/ci.yml) downloads them before
finalization (around lines 967–991 and 1083–1097). Their seven-day upload
expiry does not mean they lacked an in-run reader. The disposable
[CI Slurm setup](../../tests/tools/configure_ci_slurm.sh) removes only its
pending temporary configuration files during setup or EXIT cleanup (around
lines 62–71 and 119–141), while the workflow retains selected diagnostics
and excludes private configuration (around lines 1344–1358). This runner
infrastructure and its evidence selection have a different owner from any
Project or institutional Slurm installation.

### Operator benchmark evidence boundary

The opt-in [resource benchmark](../../scripts/benchmark_stage_resources.py)
requires a caller-selected absent output directory, previews without writes,
and on execution retains per-trial stdout/stderr, timing, artifact hashes,
`trials.tsv` and `summary.tsv`, including failed trial rows (around lines
370–510). [Focused tests](../../tests/test_benchmark_stage_resources.py)
cover preview, retained failures and refusal to reuse an existing output
(around lines 145–153, 194–264 and 343–354). A caller can place this evidence
under a Project, but location alone does not give the Project cleanup owner
authority over it. The separate [SETUP-02 retirement card](backlog_matrix.md#deferred-operational-work)
requires raw measurements and scientific-equivalence evidence to survive
helper retirement. No benchmark output is selected for cleanup here.

### Narrow candidate triage

- **Reporting stage beside linked outputs — no-go.** A normal publisher return
  removes its stage and releases its lock after linking the final manifest or
  receipt. A retained stage beside those outputs instead signals incomplete
  cleanup, uncertain rollback or foreign state. The retained state is rejected
  by [transaction validation](../../src/emrys/reporting/transaction_validation.py)
  (lines 440–476, 507–514 and 642–650), and the live publisher's captured
  identity cannot certify post-crash ownership.
- **Staged qualification receipt beside its final — no-go.** Publication
  hard-links the final name to the staged inode, then removes the stage. A
  retained stage can be the same inode as the final, with no second receipt
  payload to reclaim
  ([qualification.py](../../src/emrys/evidence/storage_inventory/qualification.py),
  lines 304–313; [fault test](../../tests/evidence/storage_inventory/test_storage_inventory.py),
  lines 465–493). The staged name still blocks its own admission route and
  marks an uncertain publication boundary. Removing the alias is not a safe
  space-saving cleanup class.
- **Site qualification probe after an admitted final receipt — no-go.** The
  compute receipt retains the probe directory names, and the final receipt
  binds the compute receipt
  ([qualification.py](../../src/emrys/evidence/storage_inventory/qualification.py),
  lines 470–510, 665–669 and 837–847). Final admission need not reread probe
  bytes, but the historical receipt reference is nonempty under this audit's
  gate. Failed or active cleanup also remains possible.
- **Direct qualification probe after an admitted receipt — unknown.** The direct
  receipt does not name its probe directories (lines 688–717 of the same owner),
  and admission may succeed with a leftover. Yet final publication precedes
  cleanup; a later eligible plan refuses occupied deterministic paths, and a
  partial directory fails the existing cleanup roster (lines 235–268 and
  582–637). The transient capability `flock` supplies no post-crash owner or
  no-writer proof for one exact remainder. Storage-only Doctor repair has no
  runtime maintenance claim
  ([doctor.py](../../src/emrys/orchestration/run_coordinator/doctor.py),
  lines 1722–1735), so that claim cannot supply the missing proof.

No retained subtype is selected; none has a justified space-saving claim.

## Next discovery pass and decision gate

1. For each possible subtype, record its producer, exact path and identity,
   owner, allowed mutation, known readers, same-Run and cross-Run links,
   cross-Project and external links, live-writer or lock state, retention role,
   and consequence of absence. Cite source and a distinguishing fault case.
2. Mark the reference universe **closed**, **open**, or **unknown**. The
   [platform direction](../design/decisions/platform-direction.md#ratified-application-model-and-run-boundary)
   has no global Project search or registry; a scan of one Projects home is not
   a reverse-reference proof.
3. Select at most one retained, owner-backed class only after exclusive
   ownership and complete absence of references are demonstrated. Otherwise
   retain the no-go finding and CLEANUP-01's Deferred status.
4. For a selected class, describe a read-only preview of exact canonical paths,
   owner identities, inbound references, unknowns and deletion consequences.
   Re-admission at any later mutation boundary needs a separate design.
5. Before proposing new machinery, compare the existing owner, standard
   library, maintained tools and package manager. Record concrete reductions
   or justified retention across product code, tests, scripts, schemas,
   configuration, documentation and mutable state. Reuse existing inspection
   and transaction ownership; do not add a generic registry, cleanup engine or
   second status cache.

### Maintenance-surface findings

| Surface | Finding from this pass |
| --- | --- |
| Product code | The reporting publishers already share [stage removal](../../src/emrys/reporting/_files.py) and [lock helpers](../../src/emrys/libraries/exclusive_publication.py), while [transaction validation](../../src/emrys/reporting/transaction_validation.py) centralizes recognized residue names. A future reporting preview should use those seams rather than add a second name scan. Validation and reference-provenance publication have documented distinct rollback gaps; similar `.previous` names do not justify collapsing them into reporting. Task rollback and storage probe cleanup have different writer and roster rules, so no cross-owner deletion helper or current product-code retirement is justified. Existing Run inspection and submission enumeration can supply positive references, but bounded association and absent results cannot serve as a complete reverse registry. |
| Tests and protections | The cited reuse, interruption, partial-publication and retained-record cases protect distinct failures. This pass identifies no redundant test or high-risk protection safe to retire. A selected subtype must map each added check against those surviving defenses. |
| Scripts, schemas and configuration | No separate CLEANUP-01 command, schema, retention registry or configuration is present to retire. Slurm scratch and validation harness cleanup already have narrow script owners and do not imply a new cleanup command. `SETUP-02` may eventually retire the benchmark helper, but explicitly preserves its raw measurements and evidence; that retirement is not a cleanup route. Do not add a command merely to inventory age or free space. |
| Documentation | CV-23, the main backlog row and this working matrix currently overlap by design during discovery. After an accepted design, keep status in the backlog, move lasting behavior beside the selected owner, and compress or retire repeated working-audit explanations while preserving decisions and evidence. |
| Mutable state | No cleanup status cache or reverse-reference registry exists. This pass found no mutable state safe to remove; a new persistent registry would require an independently justified authority and maintenance analysis. |

### Verification if a class is later selected

First demonstrate an exact no-write preview on tiny fixtures, including a
referenced candidate, active or ambiguous lock, partial publication, changed
path between preview and recheck, symlink or hardlink substitution, and
unrelated-file preservation. Check public help, exit and refusal behavior only
if a public route is separately approved. Use focused tests beside the chosen
owner and applicable source-boundary checks, then the final exact-commit CI
lanes under the [test baseline](../design/TEST_BASELINE.md#validation-lanes).
Do not promote fixture or hosted results into institutional storage,
cross-Project absence, scientific or biological proof.

This audit does not approve a public preview command, deletion implementation,
cluster execution or evidence removal. A selected interface and high-risk
protection change need separate approval under the
[workflow](../operations/WORKFLOW.md) and
[architecture guardrails](../design/decisions/platform-direction.md#ratified-abstraction-migration-and-test-guardrails).
Deletion of exact retained evidence needs its own proposal, explicit approval
and separate commit. Source review and tiny fixture checks can support software
behavior, not institutional storage or global-reference claims.
