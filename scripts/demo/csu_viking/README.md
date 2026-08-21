# CSU Viking live-demo shortcuts

This directory is an explicit, disposable presentation layer. It is **not** a
supported NORAD CLI, production execution mode, validation receipt, or source of
scientific evidence. It leaves the normal parser and workflow unchanged.

The shortcut exists so a rehearsed CSU presentation can show NORAD's real
dry-run-first control flow without spending the first hour rebuilding an index
that was already produced from the identical reference and parameters. The
demo STAR proxy imports the retained 15-member index by hardlink during Step
`00a`; Steps `01` through `10`, owner validation, reporting, and final
inspection remain normal workflow work. The resulting run must be described as
demo execution, not as proof that NORAD natively admits prebuilt indexes.

## Prerequisites

Before the presentation:

1. Let the retained v2 source run finish and run its final NORAD inspection.
2. Commit this demo patch and keep the cluster checkout completely clean. The
   dry-run signature binds that exact commit, the demo driver/proxy, real STAR,
   retained completion receipt, artifact inventory, and low-I/O index identity.
3. Confirm the retained v2 inputs, runtime profile, source index, artifact
   inventory, and both final HTML reports remain present and read-only.
4. Start a fresh shell and activate this façade once, off camera if desired:

   ```bash
   source scripts/demo/csu_viking/activate.sh
   ```

Activation chooses new create-absent input, workspace, log, and state paths.
Override any `NORAD_DEMO_*` default **before** sourcing if the retained rehearsal
paths differ. A new shell/session is the supported way to rehearse again; do not
delete or adopt a prior demo run to make a name reusable.

## Presentation sequence

Run from the repository root:

```bash
norad init local-pilot
norad init local-pilot --execute
norad inspect storage-qualification
norad inspect storage-qualification --execute
norad execute
norad execute --execute
make dashboard
```

The first command in each pair is a real no-write plan and ends with a loud
`*_DRY_RUN=PASS` marker. The storage execute command runs the compute half in a
small Slurm job and finalizes on the head node. The workflow dry-run is a real
256-CPU exclusive-node Slurm submission and is waited to completion. The final
execute command submits asynchronously, records its exact job/log identity for
the shell function, and returns so `make dashboard` can attach immediately.
The small storage-compute probe uses the CSU `short` partition by default;
override `NORAD_DEMO_QUALIFICATION_PARTITION` before activation only if that
site policy changes.

## Evidence and mutation boundary

- Mutable demo inputs, workspace, logs, qualification receipts, and state live
  outside the checkout. Doctor can therefore still require a clean source tree.
- The source FASTA/GTF and existing sidecars are referenced directly and are
  not copied, rewritten, or hardlinked.
- The proxy hardlinks only the 15 required STAR-index members. This changes
  their link counts/ctime but not their paths, bytes, size, or mtime. Never edit
  or chmod either linked tree.
- The proxy fails closed unless the real STAR digest, exact references,
  parameters (`149`/`14`), 12-thread generation call, source roster, destination
  filesystem, and workspace boundary all match the rehearsed configuration.
- The dashboard remains read-only and nonauthoritative. A completed demo still
  requires `norad inspect local-pilot-run` against the printed run root.

Native prebuilt-index admission remains tracked as `FUT-INDEX-01`; portable
dashboard/site generalization remains `FUT-DASH-01` and `FUT-SITE-01` in
[`docs/tasks/BACKLOG.md`](../../../docs/tasks/BACKLOG.md).
