# Local-pilot intake contract

## Public onboarding boundary

`emrys init local-pilot --output-dir ABSENT` is dry-run-first and publishes one
external create-absent starter tree only with `--execute`. The parent must
already be a canonical real writable/searchable directory and the target must
not overlap the selected checkout. The owner reserves the output directory,
writes the matched request, launcher/resource policy, sample, partition,
runtime, and single-allocation Slurm-wrapper members create-exclusively,
publishes the manifest last, and then re-admits exact membership, regular-file
types, modes, sizes, and bytes.
It never overwrites, adopts, installs, restores, selects reference data, or
guesses site-specific scheduler/tool values. Failure after reservation leaves
the partial directory for inspection with no claim that its manifest is valid.

`emrys validate local-pilot-request --request FILE` calls the canonical
normalizer with the tracked `emrys.profile.local_cmh.v2` contract, then reuses
the reference-contig and GTF-to-BED12 owners to require nonempty FASTA contigs,
usable exon transcript models, matching contig names, in-bounds transcript
coordinates, and in-bounds `region` or `regions_file` partition selectors. It
rechecks every reference/selector content snapshot after compatibility parsing.
It writes nothing and invokes no external tool. Success is input/configuration
compatibility evidence only, not readiness, execution, or scientific evidence.

`emrys prepare local-pilot-runtime` renders the tracked fixed runtime policy to
standard output without writing a file, probing a version, loading a module,
or installing software. Java, Picard jar, Rscript, and the `renv` library must
be explicit paths resolving to canonical real files/directories. The ordinary
command-line tools may be explicit;
an omitted tool is accepted only when the existing absolute PATH entries yield
one distinct resolved executable. Zero or multiple identities fail closed.
The helper changes editable paths and their dependent Picard/R-namespace probe
arguments only; the tracked check roster, expected versions, contexts,
required flags, and descriptions remain unchanged. Doctor owns the later
content binding and actual version/readiness probes.

`emrys init synthetic-local-pilot` uses the same external, dry-run-first,
create-absent publication policy. Its closed `--dataset-profile` selector
defaults to `smoke-v1` (130 pairs per library on 100 kb) and also admits
`production-like-v1` (100,000 pairs per library on 5 Mb). The larger profile
retains the exact engineered core while adding globally disjoint deterministic
neutral templates and an explicit deliberate-duplicate subset. Dry-run plans
either profile without generating its reference or FASTQs. Execute writes the
reference, annotation, four paired libraries, matched manifests, and explicit
metadata, validates its own request before publishing `fixture.manifest.json`
last, and then re-admits the complete transaction. The metadata's expected
three Step 09 computational candidates, one significant candidate, and Step 10
workflow completion are deterministic synthetic expectations, not production
data, scientific review, or biological interpretation.

The generated `run-in-slurm.sh` is a submit-or-batch template, not a scheduler
inside EMRYS. With no `SLURM_JOB_ID`, it calls the generation-bound controlled
Python to resolve packaged launcher defaults, adjacent or explicit launcher
YAML, and explicit wrapper options in ascending precedence, then invokes
`sbatch` for exactly one node/task/allocation. It does not run the doctor or
workflow on the submit host.

Launcher YAML is a closed `emrys.local-pilot-launcher.v1` fragment. A field is
either a literal or its field-specific `{env: EMRYS_NAME}` object; `$VAR`, shell
commands, merge keys, custom tags, arbitrary environment names, and execution
mode are not configuration. A structured reference uses an existing process
environment value before the source-checkout root `.env`. The private file is
optional, UTF-8 `NAME=VALUE` only, closed to launcher variables, duplicate-free,
owned by the live user, mode `0600` or stricter, and a real nonsymlink file.
Admission errors never include private values; missing-reference and `.env`
diagnostics identify only the affected field or variable name.

`account: site-default` and `qos: site-default` emit neither optional Slurm
flag; any other admitted account or QOS emits its flag exactly once.
`memory: site-default` emits no `--mem`; a positive explicit Slurm size is
emitted exactly once. `exclusive: true` emits one `--exclusive`; a nonempty
validated node list emits one exact `--nodelist=VALUE`. Both are submission-only
placement controls. Module mode is closed to `exact` or `none`: exact mode
requires the initializer and module roster, while none mode requires both to
be empty and never sources the module system.

The generated source checkout and Python identities cannot be replaced by
launcher YAML, `.env`, or wrapper options. The submitted batch `PATH` is exactly
the absolute parent directory of that lexical Python launcher followed by
`/usr/bin:/bin`; no ambient submit-host path entry is exported. A virtualenv
launcher symlink is preserved after its launcher and executable target are
stably admitted, so invoking the generated wrapper does not discard virtualenv
identity. Before invoking `sbatch`, the launcher removes ambient `SBATCH_*`
policy variables and ambient `EMRYS_EXECUTE`; the closed command and export
arguments remain the submission authority.
Submission derives `EMRYS_SUBMIT_UID` and `EMRYS_SUBMIT_USER` only from
`/usr/bin/id`, requires nonempty export-safe `USER` and `LOGNAME` to equal
that live user, and exports all four values. Batch mode requires and validates
the four values against a fresh `/usr/bin/id` observation before loading
modules, creating scratch, running doctor, or writing workflow state.

In the batch allocation the wrapper creates a private mode-`0700` directory
below the resolved real writable scratch parent, exports it as
`TMPDIR`, records the effective path and `df -PT` filesystem/capacity
output, and removes that private directory on exit. It then runs request
compatibility and doctor checks before delegating the entire single-host local
pilot. Batch mode requires both Slurm allocation identity and the one exact
internal script argument emitted by the submit helper; inherited
`SLURM_JOB_ID` alone cannot enter it. Submission without a wrapper mode flag
always plans. Only
`run-in-slurm.sh --execute` derives the internal `EMRYS_EXECUTE=1` batch
transport and adds the public EMRYS `--execute` gate; ambient or authored
`EMRYS_EXECUTE` cannot activate it. The
wrapper does not claim login-node computation, per-owner Slurm jobs, multi-node
scheduling, scheduler success as workflow completion, or site portability
before site validation. The outer CPU/memory request is allocation capacity,
not a minimum. `emrys.resources.yaml` remains the separate authority for
workflow cores, stage concurrency, per-step threads, and per-job memory, and
its effective totals must fit the observed allocation.

## Normalization and execution

`normalization.normalize_request` is a read-only public Python boundary. It
uses the closed safe YAML loader, resolves paths against the request directory,
reuses the public Step `08`/`09` manifest contracts, requires at least two
exact control/treatment strata, requires each paired FASTQ row to use one
matching compression mode, snapshots declared regular non-symlink inputs, and
validates the canonical execution contract. Duplicate keys, custom tags, merge
keys, globs, templates, environment/home interpolation, unknown fields, and
ambiguous paths fail admission. Request formatting and the optional human
label do not enter the execution identity.

`doctor.inspect_local_pilot` and the grouped `emrys doctor local-pilot` route
are the read-only B5 setup boundary. They reuse normalization plus the runtime-
availability owner's direct API, require the exact fixed local runtime roster
and policy fields before any probe, run R namespace probes with explicit
guarded `renv` variables, compare the selected Python/Snakemake identity, bind
admitted tool/jar bytes and installed R-package trees, and reject a workspace
overlapping the source checkout. The Java path must resolve to canonical
`<JAVA_HOME>/bin/java`; doctor, lifecycle, and GATK owner work share that
selected launcher after ambient JVM/GATK selectors are removed. An absent
workspace is admissible
only as one missing leaf beneath an existing canonical, real,
writable/searchable immediate parent; the doctor plans that leaf but never
creates it. The doctor neither installs nor repairs dependencies, loads
modules, mutates a run, executes Snakemake/scientific owners, or promotes
readiness into local-runtime, scheduler, cluster, scientific-review, or
biological evidence.
Ordinary executable and hash probes are bounded at 30 seconds. Each guarded R
namespace load has a separate 120-second bound and records elapsed/configured
timing in its diagnostic; timeouts remain readiness failures. The selected
`renv_library` is canonical and real, while one installed-package entry may
resolve through a cache symlink only when the loaded namespace and exact
canonical package-tree binding agree on its target.

`control.plan_run` and `plan_resume` are the B5 dry-run public Python boundary;
the grouped `emrys run`, `emrys resume`, and `emrys inspect local-pilot-run`
routes are the operator surface. `run` and `resume` require the controlled
Python invocation and mutate nothing without `--execute`. Planning reruns the
doctor, normalizes the authored request again, derives the deterministic run
identity, and prints the exact request-expanded owner-job plan plus three
reporting transactions. The tracked four-sample, one-partition starter expands
to 35 owner jobs; other admitted sample/partition counts expand according to
the fixed profile. The control surface exposes no raw Snakemake flags, force,
unlock, cleanup, retry, plugin, or alternate-profile escape hatch.
Successful run and resume execution, and only a completed final inspection,
print a short `Results:` block with the scientific report first and evidence
report second. Those absolute locations are carried from the fully revalidated
report receipt; dry-run, failed, blocked, incomplete, or unverified state prints
no result locations. The dashboard does not derive or display them.

`materialization.build_attempt_plan` is the sole production projection from
the fixed profile to owner commands, declared inputs/outputs, validation
reports, immutable task dispatches, reporting projections, workflow config,
and workflow-attempt record. Initial run skeleton creation is create-absent.
Lifecycle first holds the persistent zero-byte `locks/acquire.mutex` advisory
mutex and revalidates the exact prepared attempt under that serialization
boundary. The mutex is infrastructure, not run evidence. Only an admissible
current execute/resume then publishes the evidence-bearing aggregate run lock
before attempt-specific directories, dispatches, config, request snapshot, or
attempt record. A stale waiting contender exits before its materializer runs
and leaves no attempt, dispatch, config, or released-lock residue. Resume
retains only independently revalidated predecessor dispatches for verified
scopes and materializes new dispatches for the unentered remainder.

Every authored file path passes one lexical policy before access. Admission
opens the file without following a final symbolic link, verifies that the open
descriptor and pathname name the same inode before and after reading, and binds
the exact descriptor bytes. Request YAML, path-based profile JSON, and sample
and partition TSV parsing consume those admitted bytes without reopening the
pathname.

The neutral `emrys.contracts.orchestration.projection.project_reporting` API
deterministically derives the existing six-field artifact run contract and
explicit inventory bytes. Generated paths are run-root-relative; stationary
Step `00c` FASTA and sidecar paths may be absolute normalized external paths.
The projection does not discover files or promote reporting identity into
workflow identity.

The public `python -I -m emrys validate all-pass` route reads one explicit
owner-validation report and writes nothing. It requires the exact shared
seven-column validation header, at least one well-formed check row, the
declared step and scope on every row, unique nonempty `check_id` values, and
`status=pass` for every row.

Success exits `0` and reports the absolute lexical input path, SHA-256 of the
exact parsed bytes, row count, and ordered check IDs. A malformed, mismatched,
empty, or nonpassing report exits `1`; argument-usage errors exit `2`. The
checker publishes no receipt and does not infer success from validator exit,
output presence, Snakemake metadata, or timestamps.

The internal task module consumes one closed, run-contained dispatch. It binds
the canonical execution/profile snapshots and selected owner scope; captures
the exact public producer, validator, and semantic commands; rechecks inputs,
outputs, validation report, and native receipt; publishes an immutable task
attempt on admitted success or failure; and publishes a create-exclusive
verified-task record only on complete success. Only the exact Step `00c`
FAI/dictionary pair may be stationary external outputs, and its FASTA and
parent must be canonical before producer invocation. That pair may be reused
only when both files already exist as stable regular files; a partial pair is a
pre-entry failure. Reused bytes and file identities are rechecked across
producer execution, validation, semantic gating, and immediately before
verified-task publication. Every other native destination remains
create-absent.

After identity and owner-native preflight, the task boundary durably publishes
the fixed `state/task-starts/<machine>/<scope>.json` record immediately before
producer invocation. A post-start task attempt must bind that exact record and
must end in a succeeded task-attempt plus verified-task chain to be reusable.
If admission fails before start publication, the exact failed task attempt and
its two logs are retained as a bound pre-entry diagnostic; because the owner
never entered, a later attempt may retry that scope without erasing the earlier
record. Every task attempt binds the exact path and SHA-256 of both captured
logs; inspection and verified-task reuse re-read those bytes, so later mutation
or truncation blocks completion and resume.

Snakemake schedules only verified-task records. Native artifacts, validation
reports, receipts, logs, and recovery evidence are never disposable workflow
outputs. Existing verified records are reusable only after read-only schema,
identity, content, attempt, receipt, and semantic-report revalidation.

The internal lifecycle owns aggregate serialization before Snakemake. It holds
the admitted advisory mutex from stale-attempt revalidation through receipt or
recovery publication. A create-exclusive run lock is acquired only after that
revalidation and before an exact absent attempt directory is created. Lock
release creates the exact absent attempt-local immutable
`released-run-lock.json` as a no-replace hard link to the owned public lock,
re-admits the shared inode and bytes, durably synchronizes the evidence, and
then rechecks and unlinks the public name while the advisory mutex remains
held. A colliding evidence name preserves both it and the public lock and fails
closed; no rename or replacement publication may overwrite foreign evidence.
Correctness assumes every sanctioned lifecycle writer holds the mutex.
Descriptor/path checks reject observed changes, but a hostile concurrent leaf
replacement in the narrow post-link, pre-unlink interval is outside the threat
model and invalidates the evidence. The retained inode and bytes are bound by
the terminal receipt published after release.
The attempt binds canonical
execution, profile, and attempt-local workflow-config bytes; the config
transitively binds each dispatch. The executor argument binds the exact reviewed
`workflow/Snakefile` and absolute checked-in local workflow profile beneath the
declared clean checkout, preventing run-directory profile shadowing. It invokes
Snakemake only as `<bound-python> -X pycache_prefix=/dev/null -I -m snakemake`;
the exact lexical venv
launcher, its stable executable target, Python version, Snakemake module
version, normalizer path, and config are admitted as one runtime identity.
Runtime source checkout and required-tool identities are observed before
mutation and again after the child exits. The subprocess environment removes
inherited noninteractive-shell startup hooks before Snakemake starts.
For a local-science attempt, those observations include a fresh semantic
admission of the final storage-qualification receipt for the attempt workspace
and the canonical normalized reference FASTA. The observed receipt path,
digest, qualification identifier, and qualified root identities must reproduce
the one immutable `storage_qualification` tool identity before and after the
child; copying the declared identity into the observed roster is not
admission.
SIGINT/SIGTERM is controlled from before mutex acquisition through durable
receipt or recovery disposition and is forwarded at most once to the delegated
process group. Terminal success, failure, interruption, or a diagnosed state
blocker may release the lock and publish a receipt only after that group is
proved absent. A missing terminal observation or inability to prove process-
group quiescence retains the public run lock and publishes no resumable
receipt. Bounded TERM then KILL escalation covers members that remain in the
original process group after the leader exits; SIGKILL, power loss, and a
descendant deliberately escaping the delegated session/group are excluded.

This implementation requires POSIX signal masking and a doctor-admitted final
storage-qualification receipt for the workflow parent and Step `00c` sidecar
parent. The two-phase compute/head probe must reconcile same-filesystem hard
links, advisory `flock` contention, atomic rename visibility, write/fsync,
numeric UID/GID access, mount identity, and post-allocation durability.
Network/distributed storage remains unsupported until that exact receipt
finalizes. A node-local root invisible after the allocation cannot qualify;
there is no implicit stage-in/stage-out or copy exception.

If attempt establishment fails after the public lock is acquired but before a
complete attempt record exists, lifecycle still atomically retains the lock as
`locks/released-<workflow-attempt-id>-run-lock.json`. That aggregate recovery
evidence is never auto-deleted; inspection treats it, the partial attempt
directory, or both as blocked state requiring explicit reconciliation.
The retained filename alone never proves reconciliation.

Only failed/interrupted between-task boundaries are automatically resumable. Resume
requires the same run, profile, execution, source commit, executor, execution
mode, and ordered tool identities. The closed task-start ledger must prove that
every entered scope has a succeeded task-attempt and verified-task chain; an
unverified scope must have no start, though an exact receipt-bound pre-entry
failure may remain in an earlier attempt. Each reporting start must likewise
have its exact verified completion. Its fixed Snakemake arguments add
`--rerun-triggers input --ignore-incomplete`; this accepts already-admitted
EMRYS evidence despite engine metadata, but does not rerun or repair incomplete
owner state. Blocked attempts remain blocked: B4 defines no reconciliation
record that can supersede their historical ambiguity.

The contract package owns JSON parsing, validation, and canonical bytes;
inspection owns reusable direct-path admission for schema-named immutable
orchestration records. It reads the attempt chain, bound configs and receipts,
closed ledgers, verified content, and the live lock. Hash-bound, schema-free,
in-memory, mutation, and owner-specific semantics remain owner-local. Inspection
ignores `.snakemake/`, performs no repair, and treats deletion as a blocker
rather than inferring state from timestamps or output presence.

## Run-root output contract

The run root is one durable, content-bound execution history. Preserve it as a
unit; a copied result or report without its bound records is not adopted as a
completed EMRYS run.

| Location | Durable contents |
| --- | --- |
| `contract/` | Normalized request, fixed profile, admitted runtime snapshot, reporting inputs, workflow configs, and task dispatches. |
| `attempts/<workflow-attempt-id>/` | Attempt record, owner-task attempts and terminal logs, and the attempt receipt published last. |
| `state/task-starts/` | Immutable producer-entry records. |
| `state/verified/` | Hash-bound successful owner-task records. |
| `state/reporting/` | Start and verified records for artifact index, run summary, and report publication. |
| `results/` | Native scientific outputs, QC evidence, intermediates, and ranked-candidate products. |
| `products/artifact-summary/<run-id>/records/` | Canonical records for every declared artifact, including explicit incomplete or unavailable state. |
| `products/artifact-summary/<run-id>/<run-id>.artifacts.tsv` | Deterministic artifact index. |
| `products/artifact-summary/<run-id>/<run-id>.artifact_receipt.tsv` | Artifact-index receipt, published last for that transaction. |
| `products/artifact-summary/<run-id>/<run-id>.run_summary.json` | Canonical machine-readable run summary. |
| `products/artifact-summary/<run-id>/<run-id>.run_summary.tsv` | Tabular run-status summary. |
| `products/artifact-summary/<run-id>/<run-id>.qc_summary.tsv` | Consolidated QC projection. |
| `products/artifact-summary/<run-id>/<run-id>.run_summary_receipt.tsv` | Run-summary receipt, published last. |
| `products/report/<run-id>/` | Self-contained human report output, renderer summary TSV, and the report receipt published last. |
| Beside the declared FASTA | Step `00c` `.fai` and `.dict`, the only owner outputs outside the run root. |

Locks, released-lock evidence, partials, backups, task logs, and failed attempts
are not disposable merely because a later output exists. Exact report-bundle
members and their receipt semantics belong to the
[`reporting` owner](../../reporting/README.md).

The B6 proof extends the B5 adapter evidence to a clean fresh clone with the
locked workflow environment. It exercises the top-level parser using explicit
repository-only no-science collaborators and leaves the shipped command default
unchanged, with no fake mode or raw-engine option. Separate clean-success and
controlled between-task failure/resume paths cover all 35 owner jobs, the three
real reporting transactions, byte-preserving reuse, final inspection, and
completed-run refusal. These are local structural/no-science workflow facts,
not real science-tool or cluster proof, completed scientific review, or
biological validation.
