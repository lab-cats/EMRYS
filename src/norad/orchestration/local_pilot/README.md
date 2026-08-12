# Local-pilot orchestration boundary

This owner exposes two narrow, read-only B2 APIs:

- `normalization.normalize_request(request_path, profile)` safely admits one
  YAML request plus its ordered TSV manifests and returns a canonical,
  content-bound execution identity without writing a run. Its no-follow,
  descriptor-bound admission makes the exact read bytes the only parse and
  identity authority;
- `all_pass.require_all_pass(...)` checks the meaning of one owner-validation
  report rather than trusting its process exit.

The neutral
`norad.contracts.orchestration.projection.project_reporting(...)` API
reproduces the exact legacy reporting contract and deterministic artifact
inventory without depending on the local-pilot application owner.

This local pilot assumes a single-user, cooperative workspace. Its no-follow
and descriptor-bound checks reject admitted symlink components, leaf
substitution, unstable bytes, and unexpected state rosters; they do not defend
against a hostile process concurrently renaming ancestor directories or
changing mount namespaces. That interference invalidates local evidence and
requires external isolation, not automatic recovery.

The semantic checker also has this grouped command:

```bash
.venv/bin/python -I -m norad validate all-pass \
  --report /absolute/path/SCOPE.validation.tsv \
  --step-id 01 \
  --scope-id SAMPLE
```

It verifies report meaning after an owner validator has run, because
validators may publish failed rows while exiting zero. It prints the report
hash, row count, and ordered check IDs on success and creates no files.

The internal `python -X pycache_prefix=/dev/null -I -m
norad.orchestration.local_pilot.task --dispatch ...` module is the B3 one-owner
job boundary. It runs the exact admitted public producer and validator,
performs semantic all-pass and stable-content checks, preserves failure
evidence, and publishes a verified-task record only after complete success.
The fixed profile and local Snakemake graph live under
[`workflow/`](../../../../workflow/README.md).

B4 adds internal direct APIs, still without a public top-level command:

- `lifecycle.run_attempt(...)` owns one create-exclusive aggregate run lock,
  immutable attempt record, exact reviewed Snakefile and absolute workflow
  profile, the same content-admitted Python runtime running
  `-I -m snakemake`, new-process-group invocation, clean signal forwarding,
  semantic task/report transaction revalidation, retained released-lock
  evidence, exact producer-entry/reporting ledgers, recursively closed
  attempt-local task evidence, and the terminal attempt receipt published last;
- `inspection.inspect_run(...)` derives prepared, running,
  resume-available, blocked, or complete state from NORAD contracts and
  receipts, never from `.snakemake/` metadata;
- `reporting_boundary.publish_start(...)` and `publish_verified(...)` own the
  irreversible entry and semantic-completion records for each of the three
  reporting transactions; `validate_start(...)` and `validate_verified(...)`
  are their read-only admission surface. Its grouped module CLI is internal to
  the fixed workflow, not a user lifecycle command.

Each science scope publishes
`state/task-starts/<machine>/<scope>.json` immediately before producer entry.
An entered scope is reusable only with its succeeded task attempt and exact
verified record. A failed pre-entry diagnostic has no start record, remains
bound in terminal receipts, and may be retried by a later attempt. Reporting
uses the equivalent fixed `state/reporting/<kind>/{start,verified}.json`
ledger, with full semantic receipt revalidation.

Resume creates a new immutable attempt, accepts only a failed/interrupted
between-task boundary, rechecks source/tool/config/contracts and every ledger
binding, and adds exactly `--rerun-triggers input --ignore-incomplete`. The
latter is an internal engine-admission flag used only after NORAD independently
proves that every entered scope is verified and every remaining scope never
crossed producer entry. It never unlocks, cleans metadata, forces work, or
invokes owner recovery.
Blocked attempt receipts are deliberately not resumable in B4; an explicit
future reconciliation record is required to turn historical ambiguity into a
safe automatic boundary. A pre-attempt establishment failure retains its owned
lock under `locks/released-<workflow-attempt-id>-run-lock.json`; inspection
blocks on that evidence and never repairs or removes it.

The adjacent neutral [machine contracts](../../contracts/orchestration/README.md)
define request, profile, normalized execution, lock, attempt, receipt,
task-start/task-attempt/verified-task, and reporting-ledger record shapes. No
run materializer, public lifecycle command, real-tool adapter, or automatic
owner-recovery mechanism is implemented here.
See [`CONTRACT.md`](CONTRACT.md) for the exact boundary.
