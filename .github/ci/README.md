# Real synthetic E2E runtime

`real-tools.environment.yml` is the human-reviewed source specification for
the real non-R scientific tools used by the scheduled synthetic E2E lanes.
`real-tools.conda-lock.yml` is its generated Linux x86-64 lock and is the only
environment input CI installs. CI must not solve this environment dynamically.

R 4.6.1 and the exact R namespaces remain owned by `renv.lock`; the workflow
restores them through the same guarded project path used by the ordinary R CI
lane. The checkout's `uv.lock` remains authoritative for EMRYS, Snakemake, and
the controlled workflow Python. Ubuntu's Slurm and Munge packages provide only
the disposable single-node scheduler, not any scientific tool.

To intentionally update the real-tool lock after reviewing this source file:

```bash
uvx --from conda-lock==4.0.2 conda-lock lock \
  --micromamba \
  --file .github/ci/real-tools.environment.yml \
  --platform linux-64 \
  --lockfile .github/ci/real-tools.conda-lock.yml
```

Lock generation is maintenance, not a local E2E run. Full synthetic execution
belongs only in the selected GitHub Actions lanes.

## Long-lane schedule and manual selection

The workflow runs the complete Python 3.11 suite and the 130-pair `smoke-v1`
real synthetic E2E every night. Its Sunday UTC schedule also runs the
100,000-pair `production-like-v1` E2E and, after that lane succeeds, paired
retained benchmarks for alignment-signature I/O, reference-contig membership,
and Steps 02, 04, 06, 07, and 08.
A manual dispatch exposes independent `python311`, `synthetic_130`, and
`synthetic_100000` boolean lane inputs; any nonempty combination is valid, and
ordinary pull-request lanes do not run for that dispatch. The optional string
`retained_benchmark_cases` filters the retained benchmark but does not count as
a lane and is valid only when `synthetic_100000` is selected. Leave it blank to
run every registered suite, or provide comma-delimited exact case names such as
`step07-partitions,step08-reread`. Segments are not trimmed or deduplicated, so
empty, whitespace-padded, unknown, and duplicate values fail closed at the
benchmark CLI. Scheduled runs always select every registered suite. Selecting
`synthetic_100000` also selects the retained-stage benchmark; allow roughly
30--60 additional minutes and expect the retained 100,000-pair artifact to be
substantially larger.

Each synthetic profile retains its operator root as a separate artifact, while
the shared artifact records the locked runtime and disposable single-node
Slurm state. A failed selected profile does not prevent later selected profiles
or the shared diagnostics from running and uploading their evidence. The
retained-stage benchmark writes beneath
`100000/retained-stage-benchmark`, so the existing 100,000-pair upload retains
the benchmark evidence, including any diagnostics produced before a failure.
The final gate requires successful benchmark execution and correctness parity
whenever the 100,000-pair lane is selected; recorded speedups have no pass/fail
threshold.

The benchmark is hosted-runner, single-node, synthetic-data performance
evidence under the locked runtime. The same job's disposable Slurm proof does
not promote those timings to CSU or other real-cluster, shared-filesystem,
production, scientific-review, or biological evidence.
