# NORAD: CSU HPC RNA-seq and RNA-editing workflow

NORAD modernizes a legacy Novogene Remora workflow as maintainable research
software for local characterization and CSU SLURM execution. Its implemented
repository-path owners span sample-manifest admission, reference preparation,
RNA-seq alignment and BAM processing, mechanical-orientation-aware cohort
candidate generation, paired CMH ranking, evidence assembly, and report
projection. See the [architecture index](docs/architecture/README.md) for the
organized current-system authority, including the scientist-facing flow,
system map, functional-owner inventory, source topology, stage map, and
diagrams. NORAD does not yet provide a single workflow orchestrator or
installed command-line application. It does provide an explicitly installed,
unreleased Python import distribution for migrated internal packages and their
named schema/report resources.

## Start here

This entry path assumes pinned Python packages, the guarded R environment,
pinned Quarto, and owner-required system tools are already configured. Activate
the configured Python environment before using the Make target below.
Implemented owners collectively consume a sample manifest and paired RNA-seq
reads, reference FASTA/GTF material, and any owner-specific selections or
declarations described by their local contract. The full runtime manifest and
production references may remain operator- or cluster-local.

1. Review the [configuration catalog](configs/README.md) and the structural
   [`samples.example.tsv`](configs/samples.example.tsv) starter.
2. From the repository root, validate the starter's public schema:

   ```sh
   make validate
   ```

   This checks manifest structure only. It does not require the example FASTQ
   paths to exist, run ingestion, or establish a runnable data fixture.
3. Choose the applicable owner through the
   [sample-manifest admission index](src/norad/ingestion/README.md),
   [transformation-stage index](src/norad/stages/README.md),
   [analysis owner](src/norad/analyses/rank_cohort_candidates_with_paired_CMH/README.md),
   [evidence index](src/norad/evidence/README.md), or
   [reporting index](src/norad/reporting/README.md). Read the routed `README.md`
   and any adjacent `CONTRACT.md`, then follow that owner's validation and
   safety instructions. Use a dry-run or preflight where the owner provides
   one; some legacy-preserving owners do not, and there is no repository-wide
   dry-run.
4. Use the [runbook](docs/operations/RUNBOOK.md) for cross-cutting operations,
   the selected owner's README for exact commands, and
   [troubleshooting](docs/operations/TROUBLESHOOTING.md) for symptom-based
   diagnosis.

For current evidence state and blockers, read
[`HANDOFF.md`](docs/operations/HANDOFF.md). For planned work and acceptance
boundaries, read [`PIPELINE_PLAN.md`](docs/design/PIPELINE_PLAN.md); the
[architecture index](docs/architecture/README.md) owns implemented system views.

To generate a synthetic presentation bundle, follow the
[demo-report procedure](docs/demo/README.md),
which creates or replaces ignored artifacts beneath `results/demo-report/`.
Use the reviewed [demo-guide index](docs/demo/README.md) to present them. The
fixture is synthetic and provisional; it does not establish production
execution, local or cluster runtime validation, completed production scientific
review, or biological readiness.

## Evidence boundary

Implementation, local fixtures, real local runtime, cluster execution,
scientific review, and biological interpretation are distinct evidence states.
Evidence in one layer does not automatically establish a higher one: a local
validation proves only its declared local check, while a scheduler exit,
generated artifact, or rendered report alone does not establish scientific
review or biological interpretation.

Candidate rows are **CMH-ranked candidates**, not validated editing sites.
Mechanical `FWD_like` and `REV_like` labels are not biological strand claims.
`biological_interpretation_ready` remains reserved unless an approved
scientific policy explicitly unlocks it.

## Repository map

| Path | Purpose |
| --- | --- |
| [`src/`](src/README.md) | NORAD source domains, functional owners, neutral contracts, and shared libraries. |
| [`configs/`](configs/README.md) | Public inputs, structural starters, selections, and reference tables; there is no universal config loader. |
| [`scripts/`](scripts/README.md) | Explicit dependency lifecycle plus documentation and Git tooling. |
| [`tests/`](tests/) | Active Python, shell, R, contract, and fixture protection, plus explicitly non-runnable future scaffolds under `tests/pending/`. |
| [`docs/`](docs/README.md) | Architecture, operations, design, task, history, reference, and demonstration documentation. |
| [`data/`](data/README.md) and [`refs/`](refs/README.md) | Operator-managed input and reference workspaces; large or runtime children are ignored while safety guidance is tracked. |
| [`results/`](results/README.md) and [`logs/`](logs/README.md) | Ignored generated outputs and scheduler streams; generated does not automatically mean disposable. |
| [`renv/`](renv/README.md) and [root tool configuration](docs/operations/ENGINEERING_CONVENTIONS.md#repository-dependency-and-test-configuration) | Explicit dependency activation plus conventional Python, R, pytest, and coverage configuration. |

Use the [documentation sitemap](docs/sitemap/README.md) for category-level
navigation and canonical responsibility boundaries.

## Data and repository safety

Commit source, tests, configuration starters, schemas, documentation, and tiny
safe fixtures. Do not commit FASTQ, BAM, CRAM, VCF, large result tables, runtime
logs, credentials, tokens, private keys, restored runtimes, or environment
caches.

Record the identity, source, persistence, and hashes of production inputs and
references before downstream runtime promotion; a path or filename is not
provenance. Before deleting ignored data, references, results, or logs, confirm
their owner, active consumers, recovery state, and retention requirements.
