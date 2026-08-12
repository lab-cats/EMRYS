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

The internal `python -I -m norad.orchestration.local_pilot.task --dispatch ...`
module is the B3 one-owner job boundary. It runs the exact admitted public
producer and validator, performs semantic all-pass and stable-content checks,
preserves failure evidence, and publishes a verified-task record only after
complete success. The fixed profile and local Snakemake graph live under
[`workflow/`](../../../../workflow/README.md).

The adjacent neutral [machine contracts](../../contracts/orchestration/README.md)
define request, profile, normalized execution, attempt, task, and verified
record shapes. No run materializer, aggregate attempt finalizer, public
lifecycle command, reporting tail, real-tool adapter, or recovery mechanism is
implemented here yet. See [`CONTRACT.md`](CONTRACT.md) for the exact boundary.
