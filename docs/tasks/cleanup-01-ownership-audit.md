# CLEANUP-01 ownership and reference audit

This is a working design audit for the deferred
[CLEANUP-01 outcome](backlog_matrix.md#deferred-operational-work), based on
[PR #310](https://github.com/lab-cats/EMRYS/pull/310) at
1a58d2da8c2d232078c3e86b1be3d0d4241eb41e. Its implementation source
is inherited from PR #307. This audit records two source
discovery passes, not an accepted deletion design. The main backlog matrix
remains the authority for task status and acceptance; the
[CV-23 disposition](cluster_verification_backlog.md#cv-23-safe-project-or-artifact-cleanup)
records the original six classes and the absence of a proven retained
candidate. Recheck source and references if the target head changes.

The evidence level here is review of owner contracts, implementation, and
existing test cases. No tests, Project-data inventory, institutional run, or
deletion was performed for this audit. A source-described protection is not
proof that every runtime failure mode has been exercised.

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
| F1 | Runs, older Attempts, scientific artifacts; Run coordinator, Task and declared artifact owners | Downstream Runs using processing-source reuse bind the source Run, Attempt, receipt and artifact content; resume reads older Attempt history. | No-go on current evidence. | Is there an exact subtype whose complete inbound Run, report and external references can be enumerated? |
| F2 | Native outputs, staging, locks and reporting partials; Task and reporting publishers | Their cleanup owns only state captured during the live transaction; ambiguous writers and failed rollback preserve residue. | No-go on current evidence. | Can ownership and writer quiescence be proved after process loss, without discarding recovery evidence? |
| F3 | Managed runtime generations and caches; Doctor and runtime owner | Borrower Projects and retained Attempts can name older donor seals and generations; cache links complicate ownership. | No-go on current evidence. | What authority enumerates all current and historical borrowers and package links? |
| F4 | Qualification probes and receipts; storage qualification owner | The owner cleans known probes after durable publication; staged or failed cleanup remains evidence, and receipts are reused. | No-go on current evidence. | Can an exact root cohort, active phase, receipt readers and recovery consequences be closed? |
| F5 | Inputs, references and sidecars; Project admission and Step 00c | Admission binds content without exclusive ownership; FAI/dictionary files sit beside potentially shared FASTA files. | No-go on current evidence. | Can any generated subtype be separated from external and cross-Run consumers? |
| F6 | Submission and application records; Control, submission and logging owners | Retained requests feed duplicate protection, inspection, watch, stop and association; application logs supply diagnostic evidence and log discovery. | No-go on current evidence. | Can every record subtype and its historical readers be bounded without losing evidence? |

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
  have different process and commit boundaries, so a shared cleanup policy is
  not justified by similar path names.
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
  marker blocks admission and re-execution; cleanup failure can leave partial
  probes while final authority remains. The
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
  [Attempt inspection](../../src/emrys/orchestration/run_coordinator/_inspection_attempts.py);
  it is not a reverse-reference catalog.
- **Task starts, terminal records, streams and verified references — local
  roster known, external use unknown.** They feed Attempt receipts, inspection,
  resume and reporting attribution. Their absence can change the admission
  result even if final native files remain.
- **Native products, Results and reporting publications — open.** Downstream
  Tasks, reused Runs, report validation and scientist-facing transfer read
  these paths. The [Run-root contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md#run-root-contract)
  lists their distinct authorities.
- **Uncommitted Run quarantine — unknown.**
  [Materialization](../../src/emrys/orchestration/run_coordinator/materialization.py)
  can quarantine a root lacking final Run publication under an
  uncommitted-Attempt name (around lines 1664–1727). The name alone proves
  neither its complete contents nor recovery irrelevance.

### F2 path subtypes

- **Native work, scratch, owner locks and partially linked finals — unknown
  after process loss.** The [Task publisher](../../src/emrys/orchestration/run_coordinator/task.py)
  can clean captured identities while it runs; pre-existing or changed state
  blocks that authority.
- **Artifact-summary stage, lock, recovery marker and partial finals —
  unknown.** The [manifest publisher](../../src/emrys/reporting/_artifact_index/publication.py)
  retains its anchors on incomplete rollback, while
  [transaction validation](../../src/emrys/reporting/transaction_validation.py)
  refuses residue.
- **HTML-report stage, lock, recovery marker and partial finals — unknown.**
  The [HTML publisher](../../src/emrys/reporting/_run_report/publication.py)
  has its own publication sequence. Validation recognizes some older backup
  names; this pass did not establish their current producer.
- **Live Run lock and prepared finalization — local roster known, deletion
  blocked.** [Lifecycle](../../src/emrys/orchestration/run_coordinator/lifecycle.py)
  and inspection use these for exact ownership and recovery. Their path names
  do not authorize a separate cleanup caller.

### F3 path subtypes

- **Current Project runtime inventory — locally selected, still needed.**
  Runtime discovery and Doctor create or replace this selection; Doctor and
  future Runs read it. Historical Attempt selectors remain independent.
- **Retained Attempt runtime selector — open.** Each Attempt freezes an exact
  runtime profile under its Run contract; lifecycle re-reads it, and resume
  can use a predecessor selector when the current Project inventory is absent.
- **Donor seals and managed generations — open across Projects.** Current
  borrower inventories and retained Attempt selectors can point to older
  seals and fixed tool paths after donor repair. No reverse borrower list
  exists in the [runtime owner](../../src/emrys/evidence/runtime_availability/README.md#sealed-managed-runtime-reuse).
- **Managed caches — unknown.** Doctor scopes Pixi and renv caches within its
  managed tree, while package-tree links and an interrupted repair may retain
  dependencies. This pass found no complete cache-object consumer roster.
- **Maintenance claim — owner known, quiescence unknown.** A retained claim
  blocks admission and records unresolved repair or selector publication.
  Its age does not prove package-manager descendants stopped.

### F4 path subtypes

- **Direct receipt generations — historical references open.** Doctor and
  Attempts bind their exact path/hash; a newer current receipt does not erase
  older Attempt identities.
- **Site compute and final receipts — cross-Project references open.** A final
  receipt binds the compute receipt. Their identity derives from storage-root
  parents that multiple Projects can share.
- **Staged markers — recovery state unknown.** A marker blocks admission and
  re-execution after an uncertain publication boundary.
- **Probe directories — transaction cleanup known, retained state unknown.**
  The [qualification owner](../../src/emrys/evidence/storage_inventory/qualification.py)
  checks an exact four-member roster during its cleanup (around lines 582–637).
  A partial cleanup can leave an incomplete directory with a valid final
  receipt, as characterized by
  [fault tests](../../tests/evidence/storage_inventory/test_storage_inventory.py)
  (around lines 513–555). Re-running the current cleanup cannot be presumed
  to admit every retained partial.

### F5 path subtypes

- **Project-created samples and partitions manifests — Project-local readers
  known, wider references open.** [Onboarding](../../src/emrys/orchestration/run_coordinator/onboarding.py)
  authors or copies these members and publishes Project YAML last
  (around lines 1099–1160 and 1376–1390). New admission reads them, while
  Run and Attempt snapshots can retain their content. Other Projects may
  declare their absolute paths; Project ownership does not close that search.
- **Run-local selected samples projection — bound to Attempt history.**
  [Materialization](../../src/emrys/orchestration/run_coordinator/materialization.py)
  publishes the selected manifest beneath the Run contract (around lines
  1338–1376). Its directory is owner-local, but resume and Attempt evidence
  still require it.
- **Declared FASTQs, FASTA/GTF and regions — ownership and references open.**
  Project setup names their existing locations. Normalization admits bytes,
  not exclusive file ownership or a complete list of external consumers.
- **FAI and dictionary beside the FASTA — open.** EMRYS can produce an exact
  pair, but the parent may be shared, complete pairs can be reused across Runs,
  and a cross-Run lock protects publication. A partial pair blocks work.

### F6 path subtypes

- **Request context — Project roster known, historical readers open.**
  Control writes the exact request before sbatch. Its identity and contents
  support duplicate checks, inspection, watch, exact-request stop and
  correlation with an application log and Run. A locally enumerable roster is
  not proof that human selectors or historical uses have ended.
- **Raw sbatch.stdout and sbatch.stderr — request-local, still consumed.**
  The [submission owner](../../src/emrys/orchestration/run_coordinator/slurm_submission.py)
  retains both invocation transcripts. Stdout is the sole recorded scheduler
  response; deleting either can make a request partial or unconfirmed.
- **Slurm job output and error streams — writer and references open.** Slurm
  writes separate job files at paths frozen into the request. Exact scheduler
  observation and watch tails read them; terminal status alone does not
  close the external reader or writer question.
- **Application JSONL — custom-root references open.** The
  [logging owner](../../src/emrys/libraries/application_logging/storage.py)
  can publish under an absolute log root outside the Project. Selected
  requests, explicit Run inspection and watch consume historical entries;
  the [logging contract](../design/LOGGING_CONTRACT.md) preserves partials
  and forbids automatic deletion.

Two narrow **questions**, not selected candidates, emerge from this pass:
whether an exact owner-named reporting stage after completed publication, or
an exact leftover qualification probe after an admitted final receipt, could
ever pass post-crash ownership, no-writer, reference and recovery proofs. The
existing probe cleanup requires a complete roster and cannot simply be rerun
on every partial directory. Both cases may contain retained evidence; neither
currently authorizes deletion or a space-saving claim.

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
| Product code | The Task, reporting and storage owners already clean temporary state inside their own transactions. Their inputs, writer lifetimes and commit rules differ; no caller-complete shared deletion policy or safe product-code retirement is established. A future preview should first consume existing Run inspection and class-specific ownership admission. |
| Tests and protections | The cited reuse, interruption, partial-publication and retained-record cases protect distinct failures. This pass identifies no redundant test or high-risk protection safe to retire. A selected subtype must map each added check against those surviving defenses. |
| Scripts, schemas and configuration | No separate CLEANUP-01 command, schema, retention registry or configuration is present to retire. Do not add one merely to inventory age or free space. |
| Documentation | This working audit adds detail to, but does not replace, the CV-23 disposition. After an accepted design, transfer lasting behavior to its owner contract and reduce or retire this working audit while retaining necessary decisions and evidence. |
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
