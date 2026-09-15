# Runtime availability

This owner checks the tools and files needed by a Project. Runtime discovery,
Doctor, and execution use the same probes for tool versions, backend startup, R packages,
SHA-256 support, and path visibility. The coordinator owns readiness decisions
and the Project runtime inventory; this owner returns observations.

[`inspector.py`](inspector.py) reads the Project inventory as two TSV columns,
`check_id` and `target`, with one absolute path for each of 12 runtime choices,
or the sealed donor selector described below.
The installed policy derives all 26 fixed checks, including Python and Java
aliases, Picard arguments, and the selected R launcher. The installed package
supplies the R project path. Doctor adds the selected analysis module's declared
dependencies; execution reconstructs those same checks from the Run-bound
analysis policy. Probe rules are never copied into the inventory.

Inspection binds the exact inventory bytes and returns immutable observations.
Every check is required and runs in the process that requested it. Direct and
Slurm execution use the same probes; scheduler placement is checked by the
coordinator. The inventory cannot select optional checks or alternate contexts.

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

`emrys runtime discover --project BORROWER --from-project DONOR` probes a
distinct managed donor without writing. `--execute` publishes the donor's
permanent `runtime/shared.json` seal before creating the borrower's inventory.
Both Projects must admit, the destination inventory must be absent, and the
donor's selected native/R targets and resolved package roots must stay inside
its canonical, UID-owned `runtime/managed` directory. External cache links
cannot supply sealed package trees. Existing ordinary inventories remain valid.

The seal is closed canonical JSON, limited to 64 KiB, with `schema_version: 1`,
`managed_root`, the eleven non-Python `choices`, and the fixed native/R `bindings`.
Each binding records its check ID, selected/resolved path, SHA-256, observed
version and file/package-tree kind. It is an expected-content baseline, not
a copied qualification receipt or a claim about the entire environment.

The borrower's TSV has exactly the header `seal_path`, `seal_sha256`, `python`
and one row. It binds the absolute donor seal and its exact digest while keeping
the borrower's current Python interpreter. The installed probe policy derives
all checks. Doctor and Run/resume freshly probe and hash through the same
runtime binding owner; retained Run/Attempt inventory bytes preserve this
selector. Missing/changed seals, unresolved maintenance claims, inaccessible
targets, incompatible versions or changed fixed content refuse admission.

EMRYS-managed repair refuses any donor seal object, including malformed seals;
failed publication may leave a permanent seal and unresolved maintenance claim.
There is no unseal, automatic claim cleanup or receipt-copy bypass. Keep the
donor location and fixed content available to every borrower. External tools
can still change filesystem content, so operators must avoid those changes.
Native shared libraries, shebang interpreters, transitive R dependencies and
the complete managed directory are outside this fixed-target baseline.
Borrower Python/EMRYS, Analysis dependencies, storage and allocation checks
remain independent. Site accessibility and scientific execution need their own
evidence. See the [operator procedure](../../../../docs/operations/RUNBOOK.md#reuse-a-sealed-managed-runtime).

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
