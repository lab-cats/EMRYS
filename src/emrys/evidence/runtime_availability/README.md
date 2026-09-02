# Runtime-availability inspection owner

[`inspector.py`](inspector.py) directly owns the immutable
`inspect_runtime_availability(...)` API and implements
`emrys debug runtime-availability`. It performs read-only
availability probes declared in an explicit profile and retains the
`runtime_preflight` profile, report, and publication vocabulary. It records
observations for an asserted `local` or `cluster_batch` context; it does not
infer the context, install dependencies, load modules, execute a workflow,
validate production inputs, or repair a runtime.

The direct API returns the admitted profile bytes and SHA-256, normalized
checks, observations, deterministic result bytes, and required-readiness
summary without publication. The run-coordinator doctor consumes that result with
an explicit guarded R environment; it does not parse CLI output or import the
private probe/model modules. Private modules separate
literal data/error contracts (`_runtime_model.py`), profile parsing
(`_profile_contract.py`), read-only probes (`_probes.py`), and deterministic
result rendering/validation (`_result_contract.py`). They add no public command
or evidence state.

The supported probes cover tool versions, R namespaces, hash utilities, and
absolute-path visibility. Rows report `pass`, `fail`, `blocked`, or
`not_checked`. Dry run performs applicable read-only probes but publishes
nothing; execute mode publishes the requested TSV. Exit zero means probing and
any requested publication completed, not that every required probe passed.
Ordinary `tool_version` probes require command status zero. The explicit
`tool_version_exit_1` probe type requires status exactly 1 before applying its
output regex; the fixed run-coordinator profile uses it for Picard 3.1.1's exact
`java -jar ... MarkDuplicates --version` behavior. Other nonzero tool probes
remain failures.

Executable/version and hash commands retain a 30-second per-process bound.
R namespace loading has a separate 120-second per-package bound for cold
read-only library access. Every executed namespace probe records elapsed
seconds and the selected bound; a timeout is a failing readiness observation
and is never retried, suppressed, or treated as availability.

The committed
[`runtime_preflight.example.tsv`](../../../../configs/runtime_preflight.example.tsv)
is a structural starter requiring site-specific paths and expectations. Direct
protection lives in
[`test_runtime_availability.py`](../../../../tests/evidence/runtime_availability/test_runtime_availability.py).
The stricter fixed-pilot roster is the packaged internal
[`runtime_policy.tsv`](../../resources/runtime/runtime_policy.tsv) used by
Project runtime discovery; it does not change this generic profile contract.
For Slurm execution, admit the Project runtime and use the complete immutable
Run through `emrys run` or `emrys resume` as documented in the
[runbook](../../../../docs/operations/RUNBOOK.md#run-coordinator-lifecycle-routes).
For the guarded run coordinator, the declared `renv_library` itself remains one
canonical real directory. An installed package entry may be a normal `renv`
cache symlink, but the probe resolves it and requires `find.package`, the loaded
namespace, and the recorded package-tree identity to agree on the exact
canonical target. Symlinks or special entries inside that resolved package tree
remain inadmissible.

Dry-run, execute, and the focused test are:

```bash
emrys debug runtime-availability \
  --profile configs/runtime_preflight.example.tsv \
  --output results/qc/runtime/local.runtime_preflight.tsv \
  --runtime-context local

mkdir -p results/qc/runtime
emrys debug runtime-availability \
  --profile /explicit/path/to/runtime_profile.tsv \
  --output results/qc/runtime/runtime_preflight.tsv \
  --runtime-context cluster_batch \
  --execute

.venv/bin/python -m pytest -q \
  tests/evidence/runtime_availability/test_runtime_availability.py
```

Use [`TROUBLESHOOTING`](../../../../docs/operations/TROUBLESHOOTING.md) for
contract, status, and publication-lock failures.

Even an all-pass report proves only the declared availability checks in the
declared context. Current focused evidence is local fixture evidence; a
runtime-availability report alone is not CSU batch or workflow/cluster proof.

Publication has three characterized recovery defects. A lock write or fsync
failure can leave the owned lock behind. Failed predecessor restoration leaves
the only predecessor bytes in a run-token `.previous` path while removing the
lock and creating no recovery marker. A lock-cleanup failure is suppressed, so
the command can report success while the surviving lock blocks later attempts.
Preserve the report and every lock, temporary, and previous path; an absent lock
is not proof that publication committed.
