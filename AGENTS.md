# NORAD / CSU HPC agent instructions

This file defines how coding agents should work in this repository.

It should stay mostly stable over time. Do not use this file to track current pipeline status, job IDs, sample-specific results, or transient TODOs.

For current project state, consult:

```text
docs/operations/HANDOFF.md
docs/design/PIPELINE_PLAN.md
docs/design/QUESTIONS.md
docs/operations/RUNBOOK.md
docs/operations/TROUBLESHOOTING.md
docs/design/DECISIONS.md
TODO.md
```

## Purpose

This repository supports a local-first, SLURM-scaled bioinformatics workflow for RNA-seq / lncRNA / NORAD-related analysis.

The project should be developed as maintainable research software, not as a pile of one-off scripts.

Prioritize:

* reproducible workflows
* parameterized scripts
* explicit inputs and outputs
* clear local vs cluster execution paths
* small local tests before full-scale cluster execution
* debuggable logs
* documented assumptions
* boring, understandable code

## Development model

Use a gated workflow:

```text
implement locally
-> run local checks/tests
-> commit/push
-> pull on cluster
-> run SLURM dry-run
-> inspect logs
-> run SLURM execute mode
-> inspect outputs
-> update docs
-> proceed
```

Do not skip gates.

Do not implement multiple major pipeline steps at once unless explicitly requested.

Do not run heavy computation on the cluster login node.

## State belongs elsewhere

Do not put transient project state in `AGENTS.md`.

Avoid adding:

* current validation sample
* current next step
* job IDs
* current output sizes
* current cluster validation status
* temporary blockers
* sample-specific biological results
* recently discovered module versions unless they define a durable coding convention

Use these files instead:

```text
docs/operations/HANDOFF.md        current project handoff and big-picture state
docs/design/PIPELINE_PLAN.md      current pipeline map and step validation status
docs/design/QUESTIONS.md          answered and unresolved questions
docs/operations/RUNBOOK.md        operational commands and cluster procedure
docs/operations/TROUBLESHOOTING.md symptom -> cause -> fix
docs/design/DECISIONS.md          durable decisions and rationale
TODO.md                tactical next work
README.md              project overview and entrypoint
```

`AGENTS.md` is for behavior and standards.

## Local development expectations

Local development happens on macOS, usually in VS Code.

Local work should focus on:

* editing source code
* writing tests
* validating command construction
* using tiny fixtures or mocks
* checking shell/Python syntax
* committing and pushing changes

Do not assume local paths match cluster paths.

Do not require full FASTQ/BAM data for local tests.

## Cluster expectations

The cluster uses SLURM and environment modules.

Heavy computation must run through `jobs/*.slurm`.

The login node is only for:

* Git operations
* small file transfers
* light file inspection
* editing
* checking logs
* submitting jobs
* small smoke tests

Do not run full alignment, sorting, mpileup, or large analysis directly on the login node.

## Repository conventions

Expected structure:

```text
scripts/        # Python, shell, and later R scripts
jobs/           # SLURM job wrappers
tests/          # active tests and pending test plans
configs/        # optional local/cluster config files
data/test/      # tiny committed fixtures only
data/raw/       # symlinks or raw data paths; not committed
data/full/      # optional full-scale data paths; not committed
results/        # generated outputs; not committed
logs/           # SLURM logs; not committed
docs/           # project documentation
```

Prefer adding each executable workflow step as:

```text
scripts/step_XX_<name>.sh
jobs/step_XX_<name>.slurm
tests/shell/test_step_XX_<name>.sh
```

Use `tests/pending/` only for future test plans that are not active yet.

## Git and data rules

Use Git for:

* source code
* SLURM job wrappers
* configs
* documentation
* small safe test fixtures

Never commit:

* FASTQ / FASTQ.GZ
* SAM / BAM / CRAM / BAI
* large TSV/CSV outputs
* logs
* results directories
* credentials
* tokens
* API keys
* private SSH keys
* `.env` files

Tiny synthetic or representative fixtures may be committed only if they are small, safe, and non-sensitive.

## Path and configuration rules

Do not hardcode machine-specific paths inside analysis scripts.

Prefer:

* command-line arguments
* config files
* explicit input paths
* explicit output paths
* manifest-driven sample selection
* documented local and cluster examples

Scripts should run locally or on the cluster by changing arguments/configs, not by editing source code.

Avoid hidden assumptions about the current working directory unless clearly documented.

## Manifest conventions

The manifest should remain the source of truth for sample metadata.

Prefer tab-separated manifest files for workflow metadata.

Reasons:

* robust with file paths
* easy to parse in Python, R, and shell
* avoids CSV quoting problems
* easy to inspect manually

Future multi-sample execution should use manifest-driven selection rather than hardcoded sample lists.

Do not overbuild orchestration before the underlying step is proven on one sample.

## Script conventions

Scripts should:

* live in `scripts/`
* accept explicit command-line arguments
* provide useful `--help`
* validate required inputs before expensive work
* create output directories intentionally
* write outputs to explicit paths
* fail loudly with useful error messages
* print resolved context
* print exact commands before execution
* avoid hidden global state
* avoid hardcoded sample names
* avoid hardcoded machine-specific paths
* support tiny local tests or mocked tools
* validate expected outputs after execution

For bash scripts:

* use `#!/usr/bin/env bash` or `#!/bin/bash` consistently
* use `set -euo pipefail`
* quote variables
* use arrays for command construction where helpful
* avoid zsh-only syntax
* make dry-run behavior explicit
* keep tool invocation logic in scripts, not SLURM wrappers

For Python scripts:

* use `argparse`
* prefer `pathlib.Path`
* use `if __name__ == "__main__":`
* keep parsing, computation, and file writing separable where reasonable
* use type hints when helpful
* avoid over-engineering

For R scripts:

* use `commandArgs(trailingOnly = TRUE)`
* validate the expected number of arguments
* document argument order clearly
* avoid hardcoded working directories
* print resolved input/output paths
* fail clearly when inputs are missing

## Dry-run / execute convention

Dry-run should be the default for workflow scripts and SLURM wrappers.

Script-level pattern:

```bash
scripts/some_step.sh ...          # dry-run
scripts/some_step.sh ... --execute
```

SLURM-level pattern:

```bash
sbatch jobs/some_step.slurm
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=1 jobs/some_step.slurm
```

Convention:

```text
EXECUTE=0 -> dry-run
EXECUTE=1 -> execute
any other value -> fail clearly
```

Dry-run should print:

* resolved inputs
* resolved outputs
* selected sample information
* selected tool paths
* exact command that would run

Dry-run should not create final output files.

For steps where accidental directory creation could confuse validation, dry-run should avoid creating output directories too.

## SLURM job conventions

SLURM wrappers should:

* live in `jobs/`
* call scripts from `scripts/`
* avoid embedding analysis logic directly in the SLURM file
* use `set -euo pipefail`
* write stdout/stderr to `logs/`
* print job ID, job name, node, start time, working directory, and TMPDIR
* print selected inputs and outputs
* load required modules inside the job script
* avoid relying on the interactive shell environment
* default to dry-run mode
* use `EXECUTE=1` for real execution
* fail on invalid `EXECUTE` values
* avoid explicit memory requests unless known to work for the cluster/partition

Preferred log pattern:

```bash
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err
```

Use:

```bash
module list 2>&1 || true
```

instead of plain:

```bash
module list
```

because module output often goes to stderr.

## Testing expectations

Before committing changes, run the local validation gate used by this project.

At minimum, check:

```bash
git diff --check
bash -n scripts/*.sh
bash -n jobs/*.slurm
python -m compileall scripts tests
python -m pytest
make shell-test
git status --short
git diff --name-status
```

When adding or modifying a workflow step:

* add or update local tests
* prefer fake/mocked external tools where real cluster tools are unavailable locally
* test dry-run behavior
* test execute-mode command construction if possible
* test failure behavior for missing inputs
* test that expected output paths are validated

Active implemented-step tests should live under:

```text
tests/shell/
```

Future-step test plans may live under:

```text
tests/pending/
```

Pending tests must not be wired into active test runners.

## Documentation expectations

When changing workflow behavior, update the relevant docs.

Use the docs according to purpose:

```text
README.md              entrypoint / overview
docs/operations/HANDOFF.md        big project-state handoff
docs/design/PIPELINE_PLAN.md      tactical step map and validation status
docs/design/QUESTIONS.md          answered/open project questions
docs/operations/RUNBOOK.md        operational commands and cluster procedure
docs/operations/TROUBLESHOOTING.md symptom -> cause -> fix
docs/design/DECISIONS.md          decisions and reasons
TODO.md                tactical next work
AGENTS.md              coding-agent instructions
```

Do not turn one document into an everything-bucket.

When a step becomes implemented, update the pipeline plan.

When a step becomes cluster-proven, update the pipeline plan and handoff notes.

When a new cluster quirk is discovered, update troubleshooting or the runbook.

When a durable choice is made, update decisions.

## Handoff readiness

Develop this repository as if another researcher will take over and run or modify the workflow later.

A future user should be able to understand:

* what each script does
* what inputs it expects
* what outputs it creates
* whether it is meant to run locally or through SLURM
* what modules/software it requires
* how to run a tiny test
* how to run the full cluster workflow
* where logs and results are written

When adding or modifying a script, include:

* a short module/script docstring or header comment when the purpose is not obvious from the filename and CLI
* command-line arguments with `--help`
* an example command in the README or relevant docs
* validation for required input files/directories
* clear output naming
* failure messages that explain what went wrong and how to fix it

Avoid:

* hardcoded user-specific paths
* unexplained magic numbers
* silent overwrites
* assumptions about current working directory
* analysis logic hidden inside SLURM files
* one-off scripts with unclear purpose
* undocumented manual steps

## Legacy workflow handling

Legacy uploaded scripts should be treated as protocol references.

Do not directly copy:

* hardcoded paths
* hardcoded sample names
* undocumented assumptions
* brittle one-off command sequences

Instead, translate legacy behavior into:

* parameterized scripts
* explicit inputs
* explicit outputs
* local tests
* SLURM wrappers
* documented assumptions

## Biological interpretation caution

Be careful with terminology around:

* library strandedness
* read orientation
* biological transcript strand
* sense/antisense interpretation
* editing-site interpretation

Do not assume read-orientation labels directly equal biological strand labels unless the workflow explicitly documents why.

When uncertain, preserve neutral orientation labels and document the uncertainty.

## Engineering standard

Treat this repository as long-lived research software.

Prefer designs that are:

* easy to run
* easy to test
* easy to debug
* easy to hand off
* explicit about assumptions
* resistant to user error
* stable across local and cluster environments

Avoid cleverness that makes the workflow harder to understand later.

Default preference:

```text
Make it simple.
Make it runnable locally.
Make it scalable through SLURM.
Make failures easy to debug.
```
