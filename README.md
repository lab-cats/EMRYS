# EMRYS: Epic Molecular Read Yield System

EMRYS is an evidence-bound RNA-seq workflow for reference preparation,
paired-read alignment and QC, cohort candidate generation, modular analysis,
and static reporting. Its public model is:

```text
Project -> named Analysis -> immutable Run -> Results
```

A Project references an explicit Dataset and Reference. Each Analysis selects
its cohort, regions, method, and scientific policy. A Run freezes that admitted
content and its execution policy; retrying creates an Attempt rather than
changing the Run. Results and their provenance remain together beneath the Run.

EMRYS is alpha research software, not a clinical or diagnostic system. Its
built-in paired-CMH Analysis produces **CMH-ranked computational candidates**,
not validated RNA-editing sites or biological conclusions. `FWD_like` and
`REV_like` are mechanical alignment groups, not biological strand labels.
Scientific review and interpretation remain outside the pipeline.

## Built-in workflow

| Boundary | Work |
| --- | --- |
| Reference | Build or admit STAR, BED12, FASTA-index, and dictionary artifacts. |
| Per sample | Align, canonicalize, collect QC, mark duplicates, split spliced reads, and partition mechanical orientations. |
| Cohort | Generate partitioned mpileups and normalize annotated candidates. |
| Analysis | Rank candidates with paired CMH and project sequence/motif context. |
| Reporting | Index admitted artifacts and publish scientific and evidence/provenance HTML views. |

BAM QC and orientation inspection are required leaves; they do not gate
downstream scientific computation. Installed collaborator modules may replace
the downstream Analysis while retaining EMRYS's Run, validation, recovery,
logging, Results, and reporting boundaries. See the
[analysis-module contract](src/emrys/analyses/README.md).

## Supported environment

- Linux/POSIX with Python 3.11 or newer and the admitted scientific runtime.
- One Snakemake local executor, either directly on one host or inside one Slurm
  allocation on one compute node. EMRYS is not a distributed backend and must
  not run scientific work on a cluster login node.
- One cooperative user and storage that passes Doctor's checks for links,
  locking, atomic publication, visibility, durability, and access.
- Inputs and Projects outside the source checkout. EMRYS owns each Project's
  `runs/`, `logs/`, and `runtime/` directories but leaves source data in place.

`emrys doctor` diagnoses without mutation. Explicit managed repair delegates
dependency work to `uv`, Pixi, and `renv` and may modify only EMRYS-owned
environment state. EMRYS does not download scientific inputs, force retries,
delete uncertain locks, or repair result artifacts.

Readiness is bounded admission evidence, not a storage, performance, scheduler,
scientific-review, or biological claim. Capacity depends on the reference,
reads, and selected regions; plan for the STAR index and multiple BAM
generations per sample.

## Start here

The [quickstart](quickstart.md) runs the managed synthetic golden path. For a
real Project, the ordinary journey is:

```sh
emrys init PROJECT_NAME
emrys init PROJECT_NAME --execute
cd PROJECT_NAME
emrys validate
emrys runtime discover
emrys runtime discover --execute
emrys doctor
emrys run
emrys inspect
emrys report
```

Commands that can publish or execute expose a no-write plan; automation uses
explicit `--execute`. Interactive Run execution asks for confirmation.
Reporting follows a full Run by default, can be skipped with `--no-report`, and
can be regenerated with `emrys report [RUN] --execute`.

Each Run also receives a stable two-word name for `inspect`, `resume`, and
`report`. Full Run IDs and unique prefixes remain available for automation.
Outside a Project root, select it with `--project NAME_OR_PATH`.

## Documentation

| Need | Start here |
| --- | --- |
| First successful Run | [Quickstart](quickstart.md) |
| Project, Analysis, manifest, and execution-profile fields | [Configuration guide](configs/README.md) |
| Routine operation, Slurm, resume, and report regeneration | [Runbook](docs/operations/RUNBOOK.md) |
| Diagnosis and recovery | [Troubleshooting](docs/operations/TROUBLESHOOTING.md) |
| Scientific and system boundaries | [Architecture](docs/architecture/README.md) |
| Development workflow | [Documentation index](docs/README.md) |
| Accepted remaining work | [Findings matrix](docs/tasks/backlog_matrix.md) |

## License and data policy

EMRYS is **source-available**, not open-source software. Academic, nonprofit,
research, and internal commercial use and modification are permitted without
charge, as is commercialization of scientific outputs and analysis services.
Selling, relicensing, rebranding, or providing EMRYS or substantially
equivalent functionality as a paid hosted product is prohibited. The complete
[`LICENSE`](LICENSE) controls; third-party terms remain separate in
[`NOTICE`](NOTICE) and [`LICENSES/`](LICENSES/).

Do not commit production reads, BAM/CRAM/VCF data, results, logs, credentials,
restored tools or libraries, or caches. Preserve uncertain run state and its
recovery evidence until its ownership and disposition are known.
