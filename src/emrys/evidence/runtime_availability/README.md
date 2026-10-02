# Runtime availability

This owner checks the tools and files needed by a Project. Runtime discovery,
Doctor, and execution use the same probes for tool versions, backend startup, R packages,
SHA-256 support, and path visibility. The coordinator owns readiness decisions
and the Project runtime inventory; this owner returns observations.

[`inspector.py`](inspector.py) reads the Project inventory as two TSV columns,
`check_id` and `target`, with one absolute path for each of 12 runtime choices,
or the shared-runtime selector described below.
The installed policy derives all 26 fixed checks, including Python and Java
aliases, Picard arguments, and the selected R launcher. The installed package
supplies the R project path. Doctor adds the selected analysis module's declared
dependencies; execution reconstructs those same checks from the Run-bound
analysis policy. Probe rules are never copied into the inventory.

Inspection binds the exact inventory bytes and returns immutable observations.
Every check is required and runs in the process that requested it. Direct and
Slurm execution use the same probes; scheduler placement is checked by the
coordinator. The inventory cannot select optional checks or alternate contexts.

Fresh content admission at repair, qualification and final readiness protects
different mutation boundaries; an earlier digest is not current evidence. A
fixed-roster fixture found 14 executable/jar hashes for 11 distinct files, but
avoiding three reads did not establish an equivalent identity-preserving cache
or attribute institutional latency. An invocation-local digest cache remains
deferred pending material complete-operation cost and an equally strong
replacement.

R namespace checks remain serial. Diagnosis precedes resource resolution and
this owner receives no admitted concurrency budget; valid profiles include one
CPU and bounded memory. Unconditional parallel loading would exceed that
selection and needs proven concurrent-child cancellation ownership. The
[hosted comparison](../../../../.github/workflows/README.md#doctor-namespace-experiment-disposition)
reduced measured diagnosis wall time while increasing sampled memory, without
establishing setup or site benefit. It does not justify weaker fresh checks.

Observed locations remain `Path` or `None`. Tool and hash processes have a
30-second limit; R namespace loads have a 120-second limit. Timeouts fail without
retry. The coordinator always supplies the guarded R environment, and loaded
packages must resolve to the selected library's exact package roots. SHA-256
probing uses the selected Python interpreter; executable paths are absolute.
Custom analysis dependencies still support executables, R namespaces, files
and package trees through these same checks.

After its version matches, the existing `snakemake` check starts the selected
Python/Snakemake with an empty workflow, the local executor, one core, and a
30-second limit. This exercises backend initialization, including its username
lookup, without running a study task. Ambient profiles are disabled. The probe
uses a private temporary directory for its work, home, and caches and removes
that scratch on exit; it writes no Project or Run state. Scratch failures,
startup errors, and timeouts fail the same required check, with bounded detail.
Successful version and startup checks still do not prove that a study will run
or that its scientific results are valid.

Non-timeout process failures retain reported and expected exit status alongside
bounded output in their observation detail. Launch errors keep the existing
normalized status 127. R namespace load errors retain the loader's
message. Missing launchers remain `unavailable`; a timeout or failed assertion
is not reported as a missing executable. These diagnostics change neither the
required checks nor their pass/fail authority.
Successful tool observations also retain the existing subprocess elapsed time.
Snakemake version and empty-workflow startup durations are labelled separately.
The SHA-256 utility probe times its tiny known payload, not runtime-file hashing.

Use [Doctor and runtime discovery](../../../../docs/operations/RUNBOOK.md) for
Project readiness. The standalone runtime-report command and its TSV publisher
are retired. Existing reports, locks, temporary files, and predecessor files
remain operator evidence; retirement does not authorize their cleanup.

The [owner tests](../../../../tests/evidence/runtime_availability/test_runtime_availability.py)
cover path-choice admission and probe behavior. These observations establish the
checks performed, not successful workflow execution or scientific validity.

## Sealed managed runtime reuse

`emrys runtime discover --project BORROWER --from-project SOURCE` probes a
distinct managed source and previews the selection. Terminal confirmation or
`--execute` publishes its initial `runtime/shared.json` seal before creating
the dependent Project's inventory. Declining or noninteractive omission of
`--execute` leaves both Projects unchanged.
Both Projects must admit. The destination inventory must be absent unless
`--replace` selects a new generation from the same source Project. The
source's selected native/R targets and resolved package roots must stay inside
its canonical, UID-owned managed generation. External cache links cannot supply
sealed package trees. Existing ordinary inventories remain valid.

The seal is closed canonical JSON, limited to 64 KiB, with `schema_version: 1`,
`managed_root`, the eleven non-Python `choices`, and the fixed native/R `bindings`.
Each binding records its check ID, selected/resolved path, SHA-256, observed
version and file/package-tree kind. It is an expected-content baseline, not
a copied qualification receipt or a claim about the entire environment.

The dependent Project's TSV has exactly the header `seal_path`, `seal_sha256`,
`python` and one row. It binds the absolute source seal and its exact digest
while keeping the dependent Project's current Python interpreter. The installed
probe policy derives all checks. Doctor and Run/resume freshly probe and hash
through the same runtime binding owner; retained Run/Attempt inventory bytes
preserve this selector. Missing/changed seals, unresolved maintenance claims,
inaccessible targets, incompatible versions or changed fixed content refuse
admission.

Doctor does not modify a sealed generation. Repair of a Project that owns shared
tools creates `runtime/generations/<generation>/managed` and a new seal, verifies
the complete replacement, then replaces only that Project's current
inventory. Dependent Projects keep their exact old selector and must use
`runtime discover --from-project SOURCE --replace --execute` to move to the new
generation. Replacement requires the same source Project, an exact admitted
prior selector, fresh probes and the dependent Project's maintenance claim.
Retained Run/Attempt selectors continue to name their original generation.

Failed publication may leave a seal, generation and unresolved maintenance
claim. There is no automatic claim cleanup or receipt-copy bypass. Keep the
source location and selected fixed content available to every dependent
Project. External tools can still change filesystem content, so operators must
avoid those changes.
Native shared libraries, shebang interpreters, transitive R dependencies and
the complete managed directory are outside this fixed-target baseline.
Dependent-Project Python/EMRYS, Analysis dependencies, storage and allocation
checks remain independent. Site accessibility and scientific execution need
their own evidence. See the
[operator procedure](../../../../docs/operations/RUNBOOK.md#reuse-prepared-managed-tools).

## What qualification establishes

The inventory selects exact tool paths. A managed inventory points to the
Project-managed installation; a site/user inventory selects its own admitted
paths. A different default executable elsewhere on a node's `PATH` is not a
replacement for the selected target. The batch environment and explicit module
setup still matter to loading those selected executables and namespaces.

| Boundary | Evidence checked | Limit |
| --- | --- | --- |
| Doctor diagnosis | Current Project/Analysis and installed EMRYS, selected inventory, required probes, runtime file/package identities, and relevant storage receipt | A passing diagnosis is a current readiness observation, not a completed workflow. |
| Slurm compute qualification | Bound Project/package/runtime under the actual allocation; required probes and shared-storage compute checks | A version probe alone does not prove every possible native code path or shared-library dependency. Snakemake startup and R namespace loading exercise their actual startup paths. |
| Head finalization | The checked bindings, retained compute storage observations, and final readiness | A prior receipt does not make changed inputs or tools trusted. |
| Run/Attempt execution | Actual allocation capacity, selected runtime/Analysis policy, installed package and content identities, executable permissions, storage binding; rechecks at existing lifecycle boundaries | Success still requires every task and report's own evidence. Qualification does not estimate workload demand. |

Slurm eligibility is not a universal hostname pin. The selected placement may
explicitly request nodes; otherwise the scheduler chooses. Each eligible node
must expose the required paths and pass the actual checks. Device numbers may
differ between nodes when the stronger shared-storage identities match.
Direct single-host storage evidence is different: it binds the current host
and numeric UID/GID and cannot substitute for Slurm's two-phase qualification.

Managed repair currently targets x86-64 Linux. Other site environments require
their own supported runtime selection. Loader errors, unavailable targets,
failed checks, changed bound content, or incompatible storage stop admission;
the operator retains diagnostics rather than copying qualification receipts or
forcing a previously successful hostname. The probe roster is not a complete
binary-compatibility certificate for every tool path. Institutional workload
and cross-node acceptance remain separate evidence.

## Proposed R dependency closure

This is the design proposal for [RUNTIME-CLOSURE-01](../../../../docs/tasks/backlog_matrix.md),
not implemented or ratified behavior. The fixed-target contract above remains
current. This source review provides no runtime, cluster or scientific proof.

Derive the recursive `Depends`, `Imports` and `LinkingTo` closure from the fixed
scientific namespaces and selected Analysis's declared R namespaces. Reuse R's
[`tools::package_dependencies`](https://stat.ethz.ch/R-manual/R-devel/library/tools/html/package_dependencies.html)
with an explicit installed-package database; do not use its repository default.
Use [`utils::installed.packages`](https://stat.ethz.ch/R-manual/R-devel/library/utils/html/installed.packages.html)
with explicit libraries and `noCache=TRUE`. Inspection neither solves nor repairs
packages. Bind each member through the existing installed-package-tree hasher
and `package_tree` records; do not relabel an aggregate closure hash as a package
hash or add a parallel manifest, registry or dependency parser. Unrelated
installed packages must not enter Run identity.

One migration must cover namespace probing and immutable inspection, runtime
binding, Doctor identity projection, discovery/publication, managed-generation
sealing and repair qualification, materialization's Run identity, and lifecycle
Attempt readmission. Preserve fixed check IDs and fresh namespace-load checks;
adding bindings alone is insufficient because Doctor projects observations and
lifecycle checks their exact roster. Re-admit closure membership, versions,
resolved roots and bytes together. Changed dependencies create a distinct Run;
retained Run/Attempt records and generation seals remain unchanged.

Before implementation, decide:

- Deterministic derived binding IDs, collision refusal, ordering, and how closure
  observations coexist with the fixed check roster and declared Analysis roots.
- Exact treatment of base/recommended packages under the selected R installation,
  with no arbitrary site-library fallback; preserve ordinary renv cache links by
  binding their resolved roots and retain managed-generation containment.
- A successor to the fixed-roster v1 seal: historical readability, explicit
  generation replacement, byte bound, and donor baseline versus borrower-specific
  Analysis dependencies. Reuse existing orchestration package-tree fields.
- Bounded enumeration/output/time and refusal of missing or ambiguous metadata,
  changed graph membership, or links retargeted across enumeration and hashing.
  Declared strong dependencies do not cover undeclared dynamic package use or
  complete native shared-library identity.

Prove the design with a tiny diamond/cycle dependency fixture, all three edge
kinds, a missing member and an unrelated package. Transitive byte/edge changes
must refuse readmission and change new Run identity; unrelated changes must not.
Exercise normal cache links and retargeting, managed containment, Analysis roots,
borrowing, generation repair and retained Attempt refusal without mutation.

## Automatic-snapshot guard

The reviewed [`.Rprofile`](../../.Rprofile) forces both
`RENV_CONFIG_AUTO_SNAPSHOT=FALSE` and `options(renv.config.auto.snapshot=FALSE)`
when `EMRYS_USE_RENV=1`, before guarded library selection or explicit restoration
activation. Inherited true values cannot enable automatic snapshots through
these supported paths. An unselected profile (`EMRYS_USE_RENV=0`) leaves those
settings alone. Existing guarded subprocess selectors and the vendored autoloader
remain unchanged; this does not forbid an operator's explicit restore/snapshot.

The [shell-owner fixture](../../../../tests/shell/test_local_r_environment.sh)
uses real R to check inherited environment/option overrides, unchanged sandbox
policy, missing-package refusal and exact fixture lock/library bytes during
inspection. Its restoration activation body is fake: it proves guard ordering
and external settings-file routing, not a real package restore or complete renv
behavior. Managed-runtime CI supplies its separately bounded real-runtime proof.
This startup guard does not implement recursive package identity; the closure
proposal above and RUNTIME-CLOSURE-01 remain open.

## Installed backend identity limit

The Snakemake policy selects the Python interpreter: fixed-target binding hashes
that executable, while version and empty-workflow probes exercise the installed
module. It does not bind the entire Snakemake module tree or Python dependency
closure. The lock specifies intended distributions, not a live content digest.
The September source audit demonstrated no controlled same-version escape. A
stronger guarantee remains an unselected decision, separate from R dependency
closure above; if selected, reuse current identity owners and cover Doctor, new
Run, resume and child entry with positive and drift cases. The [frozen finding](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/polish-campaign.md#35-settle-the-installed-snakemake-content-guarantee)
records this limit without implying the existing probes are content-closure proof.
