# Runtime-preflight evidence owner

[`runtime_preflight.py`](runtime_preflight.py) performs read-only availability
probes declared in an explicit profile. It records observations for an asserted
`local` or `cluster_batch` context; it does not infer the context, install
dependencies, load modules, execute a workflow, validate production inputs, or
repair a runtime.

The supported probes cover tool versions, R namespaces, hash utilities, and
absolute-path visibility. Rows report `pass`, `fail`, `blocked`, or
`not_checked`. Dry run performs applicable read-only probes but publishes
nothing; execute mode publishes the requested TSV. Exit zero means probing and
any requested publication completed, not that every required probe passed.

[`tool_check.slurm`](tool_check.slurm) is a separate manual cluster smoke
probe. It attempts to load its declared CSU Python, STAR, samtools, and Picard module names and
records scheduler context, module state, resolved executable paths, and tool
versions in SLURM logs. It does not call `runtime_preflight.py`, publish a
structured report, run analysis, or prove that the workflow works on the
cluster. Its module loads and required probes fail strictly; only the optional
Picard version probe is tolerated. Central wrapper characterization lives in
[`test_slurm_wrapper_contracts.py`](../../../../tests/test_slurm_wrapper_contracts.py).

The committed
[`runtime_preflight.example.tsv`](../../../../configs/runtime_preflight.example.tsv)
is a structural starter requiring site-specific paths and expectations. Direct
protection lives in
[`test_runtime_preflight.py`](../../../../tests/evidence/runtime_preflight/test_runtime_preflight.py).

Dry-run, execute, focused test, and the separate scheduler probe are:

```bash
.venv/bin/python src/norad/evidence/runtime_preflight/runtime_preflight.py \
  --profile configs/runtime_preflight.example.tsv \
  --output results/qc/runtime/local.runtime_preflight.tsv \
  --runtime-context local

mkdir -p results/qc/runtime
.venv/bin/python src/norad/evidence/runtime_preflight/runtime_preflight.py \
  --profile /explicit/path/to/runtime_profile.tsv \
  --output results/qc/runtime/runtime_preflight.tsv \
  --runtime-context cluster_batch \
  --execute

.venv/bin/python -m pytest -q \
  tests/evidence/runtime_preflight/test_runtime_preflight.py

mkdir -p logs
sbatch src/norad/evidence/runtime_preflight/tool_check.slurm
```

Use [`TROUBLESHOOTING`](../../../../docs/operations/TROUBLESHOOTING.md) for
contract, status, and publication-lock failures.

Even an all-pass report or successful manual smoke probe proves only the
declared availability checks in the declared context. Current evidence is
local fixture and mocked-wrapper evidence; CSU batch execution and
workflow/cluster proof remain absent.
