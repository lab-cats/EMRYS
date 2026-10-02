# CLEANUP-01: ownership decision brief

The [main matrix](backlog_matrix.md#deferred-operational-work) owns the Deferred
outcome and acceptance. No retained class has a proven deletion route. This is
not a cleanup command, approved design, artifact inventory or implementation task.

## Basis and evidence ceiling

The original review checked PR #310 at `aff2c91509b33e7d2b166d37ff9e85eb43f0f6b4`
against implementation `1a58d2da8c2d232078c3e86b1be3d0d4241eb41e` on 2026-09-22.
It read owner contracts, source and existing tests; it performed no Project-data
census, product fault suite, institutional run or deletion. One isolated Rscript
probe checked top-level `on.exit`, not EMRYS R-check or operator storage.
The [frozen investigation](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/cleanup-01-ownership-audit.md)
retains exact source locations, fault cases and inference labels. The findings
below are that revision-bound decision basis, not a new current-source audit.

## Six retained classes

Deletion needs an exact subtype, exclusive ownership, a complete empty inbound
reference set, no possible writer and understood recovery/evidence consequences.
Transaction-owned temporary cleanup is a separate existing boundary. Age, a
missing success receipt, scheduler disappearance or a partial search establishes
neither quiescence nor absence of references: **unknown is not unused**.

| Finding | Class and existing owner | Why no retained subtype was selected |
| --- | --- | --- |
| F1 | Runs, older Attempts, reporting ledger and scientific artifacts; coordinator, Task and artifact owners | Downstream Runs, resume and reporting bind historical records and bytes; Project-local enumeration cannot close external references. |
| F2 | Native/publication staging, locks, backups and outputs; their publishers | Live captured ownership is not a post-crash certificate. Failed rollback can leave needed backups after a lock disappears. |
| F3 | Runtime generations, caches and installed packages; Doctor/runtime owners | Current Projects, borrowers, historical Attempts and selected analysis dependencies reference distinct generations and trees; no complete reverse roster exists. |
| F4 | Qualification probes and receipts; storage qualification | Site receipts name probes; staged/final names may share an inode; successful publication does not certify every retained remainder safe. |
| F5 | Inputs, references, sidecars, profiles and created roots; admission and producer owners | Content admission does not establish exclusive ownership. External/cross-Run readers and partial publication remain possible. |
| F6 | Requests, streams and application/maintenance records; submission and logging owners | Inspection, watch, stop and project-free readers consume them; bounded scans and custom roots cannot close historical or external references. |

## Distinct boundary findings

S1–S31 refine F1–F6; they are not new cleanup classes or accepted defects to fix.
Similar suffixes do not make different publication or trust boundaries equivalent.

| IDs | Boundary that a later exact-subtype proposal must preserve |
| --- | --- |
| S1 | Validation `.previous` can survive without a lock, with or without the replacement final; retain recovery bytes. |
| S2, S30 | Reference reconciliation has three finals and caller-selected roots. Failed restoration retains backups; a later same-ID successor ignoring older backups is a source inference, not a tested coexistence case. |
| S3 | Shared exclusive publication removes only its captured live transaction state; `.emrys-stage`/`.displaced` names do not establish the calling owner's post-crash authority. |
| S4 | Batch scratch EXIT/TERM cleanup does not prove safety after abrupt loss or scheduler termination. |
| S5 | Harness logs, E2E roots and hosted artifacts have separate evidence owners; hosted expiry grants no local deletion authority. |
| S6 | Create-absent Project, manifest and synthetic publishers preserve failed partial trees. Completion-member presence or absence is insufficient. |
| S7, S17 | Named/absolute profile sources are retained Attempt references; module-init files and scratch parents extend beyond the Project. A profile hash does not bind module-init bytes. |
| S8 | Retired producer locks, anchors, backups and partial QC outputs retain their original recovery boundary; no current producer is not a deletion certificate. |
| S9 | Caller-selected benchmark roots retain failed trials, streams and measurements even under a Project; SETUP-02 helper retirement preserves that evidence. |
| S10 | An explicit external `RENV_PROJECT` has operator-owned settings, libraries and caches outside managed-generation authority. |
| S11 | `.snakemake/` is opaque backend/possibly foreign state, not EMRYS completion authority or a proven cleanup candidate. |
| S12, S22 | Doctor/backend probe scratch and Matplotlib import caches normally clean on return; custom temporary roots and abrupt loss remain unproved. |
| S13 | Unclosed reporting `start.json` and broken ledger prefixes block admission even without outputs or after scientific success. |
| S14, S18 | Project-free streams and Doctor/stop maintenance logs have readers and destinations outside Project request/default-log rosters. |
| S15 | Qualification stage/final receipt names can be hardlinks to one inode; a staged blocker is not independent payload space to reclaim. |
| S16, S19 | Installed EMRYS code and selected analysis executable/file/package checks create positive historical Attempt references beyond standard runtime inventories. |
| S20 | Incomplete bounded application-log association reports unknown; no match is not a complete empty reference set. |
| S21 | Direct probe paths depend on canonical Project/FASTA parents across receipt generations. The complete pair's 192 distinct payload bytes are source-derived, not measured reclaimable space; partial pairs have no equivalent fixed bound. |
| S23, S27 | Older Attempt sample/reporting projections and runtime-profile snapshots remain positively referenced during resume; latest-only scans miss them. |
| S24 | Step 00c works beside external FASTA and may share a dictionary basename across same-stem FASTAs; one input's status cannot classify the shared path. |
| S25 | The reporting artifact manifest projects declared rows, not every file; an undeclared native VCF can remain outside it. |
| S26 | Repository `.env` is functional configuration and can select external Project/log roots; it is not Project residue. |
| S28 | A tiny file-mode Rscript probe left its PDF after top-level `on.exit`; registration follows creation/reading. Full EMRYS R-check and retained-path ownership were not tested. |
| S29 | Retired runtime-report finals, locks, temporary files and predecessors remain operator evidence; publisher retirement does not remove them. |
| S31 | Optional renv startup profiling retains and prints a temporary `.Rprof`; it is diagnostic evidence, separate from caches and R-check PDFs. |

## Selection gate for any later implementation

1. Select at most one subtype. Record exact paths/identities, producer, owner,
   mutations, all current/historical/external readers, possible writers, recovery
   role and consequences of absence. Mark references closed, open or unknown.
2. Demonstrate exclusive ownership, complete absence of references and quiescence.
   A Projects-home scan, a free lock or a final receipt cannot substitute. Direct
   qualification leftovers still lack that proof; site receipts positively name
   their probes. Storage-only repair need not have a runtime maintenance claim.
3. Propose a no-write preview and a separate mutation-boundary re-admission rule.
   Exercise referenced candidates, ambiguous locks, partial publication, path
   drift, symlink/hardlink substitution and preservation of unrelated files.
4. Prefer the existing owner/standard library/package manager. Existing reporting
   helpers may support their own preview; Task, validation, reference and storage
   cleanup have different writer/rollback rules. No generic engine, registry,
   status cache, new command, redundant test or product retirement is justified.
5. Quantify the selected change and preserve independent protections. Fixtures
   and hosted checks cannot prove institutional storage or global absence of
   references. Public changes, deletion and exact-evidence retirement retain
   their explicit authority, including a separate evidence-deletion commit.

No retained subtype or space-saving claim is selected by this brief. Status and
future selection remain in the matrix; durable behavior belongs to its owner.
