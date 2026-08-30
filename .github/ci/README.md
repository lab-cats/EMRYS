# Real synthetic E2E runtime

`src/emrys/resources/runtime/pixi.toml` is the reviewed managed-runtime
specification. Its adjacent `pixi.lock` is the only input CI installs for the
native scientific-tool and R-base environments. CI stages those two files in
an external temporary workspace and installs them with Pixi 0.75.0 in locked
mode; it must neither solve them dynamically nor change the source checkout.

Pixi pins the R 4.6.1 base and build toolchain; `renv.lock` remains
authoritative for the exact R namespaces and restores them through the same
guarded project path used by the ordinary R CI lane. The checkout's `uv.lock`
remains authoritative for EMRYS, Snakemake, and the controlled workflow Python.
Only `Rscript` from Pixi's `r` environment is an EMRYS R authority; any R
package pulled transitively into `native` is ignored.
Ubuntu's Slurm and Munge packages provide only the disposable single-node
scheduler, not any scientific tool.

To intentionally update the managed-runtime lock after reviewing its manifest:

```bash
pixi lock --manifest-path src/emrys/resources/runtime/pixi.toml
```

Lock generation is maintenance, not a local E2E run. Full synthetic execution
belongs only in the selected GitHub Actions lanes.

The ordinary CI matrix installs the same unchanged lock in Rocky Linux 8.10,
Ubuntu 22.04, and Debian 12 containers and invokes both managed environments.
That is userspace evidence for glibc 2.28, 2.35, and 2.36 respectively.
Containers share the hosted runner's kernel, so this matrix does not prove
execution on Linux kernel 4.18; a real 4.18 host or VM remains required for
that separate claim.

## Long-lane schedule and manual selection

The workflow runs the complete Python 3.11 suite and the 130-pair `smoke-v1`
real synthetic E2E every night. Its Sunday UTC schedule also runs the
100,000-pair `production-like-v1` E2E. A manual dispatch exposes independent
`python311`, `synthetic_130`, and `synthetic_100000` boolean inputs; any
nonempty combination is valid, and ordinary pull-request lanes do not run for
that dispatch.

Each synthetic profile retains its operator root as a separate artifact, while
the shared artifact records the locked runtime and disposable single-node
Slurm state. A failed selected profile does not prevent later selected profiles
or the shared diagnostics from running and uploading their evidence.
