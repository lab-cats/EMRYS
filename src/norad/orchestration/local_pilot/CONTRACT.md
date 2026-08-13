# Local-pilot intake contract

`normalization.normalize_request` is a read-only public Python boundary. It
uses the closed safe YAML loader, resolves paths against the request directory,
reuses the public Step `08`/`09` manifest contracts, requires at least two
exact control/treatment strata, requires each paired FASTQ row to use one
matching compression mode, snapshots declared regular non-symlink inputs, and
validates the canonical execution contract. Duplicate keys, custom tags, merge
keys, globs, templates, environment/home interpolation, unknown fields, and
ambiguous paths fail admission. Request formatting and the optional human
label do not enter the execution identity.

`doctor.inspect_local_pilot` and the grouped `norad doctor local-pilot` route
are the read-only B5 setup boundary. They reuse normalization plus the runtime-
availability owner's direct API, require the exact fixed local runtime roster,
run R namespace probes with explicit guarded `renv` variables, compare the
selected Python/Snakemake identity, bind admitted tool/jar bytes, and reject a
workspace overlapping the source checkout. An absent workspace is admissible
only as one missing leaf beneath an existing canonical, real,
writable/searchable immediate parent; the doctor plans that leaf but never
creates it. The doctor neither installs nor repairs dependencies, loads
modules, mutates a run, executes Snakemake/scientific owners, or promotes
readiness into local-runtime, scheduler, cluster, scientific-review, or
biological evidence.

`control.plan_run` and `plan_resume` are the B5 dry-run public Python boundary;
the grouped `norad run`, `norad resume`, and `norad inspect local-pilot-run`
routes are the operator surface. `run` and `resume` require the controlled
Python invocation and mutate nothing without `--execute`. Planning reruns the
doctor, normalizes the authored request again, derives the deterministic run
identity, and prints the exact request-expanded owner-job plan plus three
reporting transactions. The tracked four-sample, one-partition starter expands
to 34 owner jobs; other admitted sample/partition counts expand according to
the fixed profile. The control surface exposes no raw Snakemake flags, force,
unlock, cleanup, retry, plugin, or alternate-profile escape hatch.

`materialization.build_attempt_plan` is the sole production projection from
the fixed profile to owner commands, declared inputs/outputs, validation
reports, immutable task dispatches, reporting projections, workflow config,
and workflow-attempt record. Initial run skeleton creation is create-absent.
The aggregate lifecycle lock is acquired before attempt-specific directories,
dispatches, config, request snapshot, or attempt record are published. Resume
retains only independently revalidated predecessor dispatches for verified
scopes and materializes new dispatches for the unentered remainder.

Every authored file path passes one lexical policy before access. Admission
opens the file without following a final symbolic link, verifies that the open
descriptor and pathname name the same inode before and after reading, and binds
the exact descriptor bytes. Request YAML, path-based profile JSON, and sample
and partition TSV parsing consume those admitted bytes without reopening the
pathname.

The neutral `norad.contracts.orchestration.projection.project_reporting` API
deterministically derives the existing six-field artifact run contract and
explicit inventory bytes. Generated paths are run-root-relative; stationary
Step `00c` FASTA and sidecar paths may be absolute normalized external paths.
The projection does not discover files or promote reporting identity into
workflow identity.

The public `python -I -m norad validate all-pass` route reads one explicit
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

The internal lifecycle owns aggregate serialization before Snakemake. A
create-exclusive run lock is acquired before an exact absent attempt directory
is created. Lock release atomically renames the public lock to the exact absent
attempt-local immutable `released-run-lock.json`; it never conditionally
unlinks the moved pathname. The moved inode and bytes are re-admitted and bound
by the terminal receipt published after it. A foreign public replacement is
never unlinked, and a foreign moved inode remains visible as recovery evidence.
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
mutation and again after the child exits. Ordinary success, failure,
interruption, and diagnosed ambiguity first retain released-lock evidence and
then publish the immutable terminal receipt last.

If attempt establishment fails after the public lock is acquired but before a
complete attempt record exists, lifecycle still atomically retains the lock as
`locks/released-<workflow-attempt-id>-run-lock.json`. That aggregate recovery
evidence is never auto-deleted; inspection treats it, the partial attempt
directory, or both as blocked state requiring explicit reconciliation.

Only failed/interrupted between-task boundaries are automatically resumable. Resume
requires the same run, profile, execution, source commit, executor, execution
mode, and ordered tool identities. The closed task-start ledger must prove that
every entered scope has a succeeded task-attempt and verified-task chain; an
unverified scope must have no start, though an exact receipt-bound pre-entry
failure may remain in an earlier attempt. Each reporting start must likewise
have its exact verified completion. Its fixed Snakemake arguments add
`--rerun-triggers input --ignore-incomplete`; this accepts already-admitted
NORAD evidence despite engine metadata, but does not rerun or repair incomplete
owner state. Blocked attempts remain blocked: B4 defines no reconciliation
record that can supersede their historical ambiguity.

Inspection reads the complete linear attempt chain, attempt-bound configs,
terminal receipts, the closed task-start and reporting ledgers, recursively
closed attempt-local task trees, verified task content, reporting transactions,
and the live owned lock. Receipt references make deletion a blocker rather than
turning entered work back into pending state. It ignores `.snakemake/`, performs
no repair, and does not consider timestamps or output presence to be completion
evidence.

The B6 proof extends the B5 adapter evidence to a clean fresh clone with the
locked workflow environment. It exercises the top-level parser using explicit
repository-only no-science collaborators and leaves the shipped command default
unchanged, with no fake mode or raw-engine option. Separate clean-success and
controlled between-task failure/resume paths cover all 34 owner jobs, the three
real reporting transactions, byte-preserving reuse, final inspection, and
completed-run refusal. These are local structural/no-science workflow facts,
not real science-tool or cluster proof, completed scientific review, or
biological validation.
