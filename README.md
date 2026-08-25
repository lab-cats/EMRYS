# EMRYS: Epic Molecular Read Yield System
## Evidence-bound analysis of DNA and RNA sequencing data.

EMRYS is an evidence-bound workflow for paired-end RNA-seq alignment, QC,
mechanical read-orientation partitioning, cohort mpileup, candidate annotation,
paired CMH ranking, and bounded sequence/motif context projection. You provide
declared reads, a matching FASTA/GTF
reference, paired experimental strata, genomic partitions, analysis thresholds,
and exact scientific-tool identities. EMRYS produces validated native outputs,
an immutable task history, a deterministic artifact index, a machine-readable
run summary, QC tables, and separate self-contained scientific and
evidence/provenance HTML views.

EMRYS is alpha research software, not a clinical or diagnostic system. It is
not a general RNA-seq expression workflow: it does not demultiplex, trim or
quality-filter reads, merge technical lanes, quantify transcripts, test
differential expression, discover samples, or infer experimental pairing.
Provide analysis-ready paired FASTQs and author the intended design explicitly.

The automatic workflow produces **CMH-ranked computational candidates**. It
does not prove that a candidate is an RNA-editing site, infer biological strand
from the mechanical orientation labels, or make a biological conclusion.
Candidate review, adjudication, and biological interpretation are external
work-process records. EMRYS does not model them as pipeline steps, gates,
artifacts, or completion states.

## What happens to the data

| Step | Scope | Operation | Principal result |
| --- | --- | --- | --- |
| `00a` | Reference | Build and validate a STAR genome index. | STAR index directory |
| `00b` | Reference | Convert the declared GTF deterministically to BED12. | BED12 annotation |
| `00c` | Reference | Create or re-admit the FASTA index and sequence dictionary. | `.fai` and `.dict` beside the FASTA |
| `01` | Each sample | Align paired reads with STAR. | Coordinate-sorted STAR BAM |
| `02` | Each sample | Construct and validate a canonical BAM/BAI pair. | Canonical BAM and index |
| `02b` | Each sample | Collect flagstat, quickcheck, and alignment QC evidence. | QC evidence branch |
| `03` | Each sample | Measure paired-read orientation with RSeQC. | Orientation evidence branch |
| `04` | Each sample | Mark duplicates with Picard. | Duplicate-marked BAM, BAI, and metrics |
| `05` | Each sample | Apply GATK `SplitNCigarReads`. | Split BAM and BAI |
| `06` | Each sample | Partition reads into legacy mechanical flag groups. | `FWD_like` and `REV_like` BAM/BAI pairs |
| `07` | Each partition | Run cohort bcftools mpileup for both mechanical groups. | Two VCFs and a bound receipt |
| `08` | Cohort | Normalize SNV candidates, attach per-sample counts and GTF overlaps. | Candidate, input-receipt, and QC tables |
| `09` | Analysis | Perform paired two-sided CMH tests and global BH correction. | All-sites, significant-sites, summary, spectrum, and plots |
| `10` | Analysis | Project fixed Step `09` calls onto an indexed reference and registered PUM motif. | Candidate context, motif hits, logo frequencies, motif statistics, and receipt |
| Reporting | Run | Index artifacts, assemble the run summary, and render both report views. | Scientific HTML, evidence/provenance HTML, summary TSV, and receipt-last publication |

Steps `02b` and `03` are required QC leaves but do not gate downstream
scientific computation. External review or adjudication may use EMRYS's
computational outputs and provenance, but it is not part of `emrys run`.

The fixed graph contains `3 + 7S + P + 3` scientific-owner jobs for `S`
samples and `P` genomic partitions. The four-sample, one-partition starter
therefore expands to 35 jobs, followed by three reporting transactions.

## Supported execution boundary

Read this before installing:

- The public runtime target is a Linux/POSIX host with Python `3.11` or newer,
  Git, GNU Make, `uv`, and the scientific runtime listed below.
- The workflow uses Snakemake's **single-host local executor**. It defaults to
  a packaged resource policy that can be overridden by adjacent
  `emrys.resources.yaml` and then by explicit CLI values. `workflow_cores` and
  `workflow_memory_mb` bound the whole scheduler; per-stage concurrency,
  threads, and memory model each owner class. EMRYS neither submits SLURM jobs
  nor distributes work across nodes.
- Run it on a suitably provisioned Linux workstation, or run the same local
  process inside **one** batch allocation on **one** compute node. Never run the
  scientific workflow on a cluster login/head node; use that node only to
  clone, edit, transfer small files, submit, inspect, and tail logs.
- One cooperative user is required. The exact workspace parent and Step `00c`
  reference-sidecar parent must pass EMRYS's two-phase site qualification for
  hard links, `flock`, rename/visibility, fsync, UID/access, and post-allocation
  durability. No filesystem family—including NFS—is admitted by name alone.
- Local-pilot inputs, workspace, control logs, and results stay outside the Git
  checkout. The locked ignored `.venv/`, the default ignored `renv/library/`,
  and the report-only demo's ignored `results/demo-report-jinja/` are sanctioned
  checkout-local exceptions; an already provisioned R library may instead be
  selected explicitly. The doctor requires tracked checkout content to be clean
  and binds its exact commit and installed package bytes.
- EMRYS does not download data, install tools, load modules, restore R
  packages, estimate runtime, force retries, delete locks, or repair outputs.
  It does observe the CPU affinity and memory capacity available to its local
  executor so an impossible resource policy fails before workflow entry.

Capacity depends on reference size, read count, and selected partitions. Plan
for the STAR index and several BAM generations per sample, plus orientation
BAMs, VCFs, logs, and immutable recovery evidence. Before a real run, inspect
the input size and destination capacity on the execution host:

```sh
du -sh /absolute/path/to/emrys-inputs/inputs
df -h /absolute/path/to/operator-managed-storage
free -h
```

`free` is Linux-specific. `READY` confirms bounded admission checks only; it is
not a memory, storage, wall-time, throughput, scheduler, or science estimate.
For an unfamiliar reference or cohort, begin with a small declared region and
representative samples before authorizing the full analysis.

## Choose a first run

- **Synthetic installation check:** use [`quickstart.md`](quickstart.md),
  Path A, with `emrys init synthetic-local-pilot`. The default `smoke-v1`
  creates small explicit inputs; the closed `production-like-v1` selector
  creates the 100,000-pair-per-library, 5 Mb functional fixture. Both write
  outside the repository and still require the real admitted scientific
  runtime. A synthetic result
  demonstrates that exact runtime and request, not production or biological
  validity.
- **Your data:** follow [`quickstart.md`](quickstart.md), Path B, and replace
  every starter identity and path with your own declared inputs.
- **Report-only preview:** run `make demo-report` after installation and follow
  [`docs/demo/README.md`](docs/demo/README.md). This renders bundled reporting
  fixtures and does not execute ingestion, STAR, samtools, GATK, Picard,
  RSeQC, bcftools, R analysis, or the workflow.

The exact validation evidence at the current commit is recorded in
[`HANDOFF.md`](docs/operations/HANDOFF.md). A demo, dry run, synthetic fixture,
successful job, or report must not be promoted beyond the evidence it actually
establishes.

## Glossary

| Term | Meaning in EMRYS |
| --- | --- |
| `AD` | Alternate-allele read depth reported for one sample/candidate. |
| `AF` | Alternate fraction, normally `AD / DP`, for one sample/candidate. |
| `DP` | Total read depth used for the candidate calculation. |
| Candidate | A computationally represented SNV row. It is not automatically an editing site. |
| CMH | Cochran-Mantel-Haenszel test combining paired replicate strata while retaining their pairing. |
| FDR / BH | Benjamini-Hochberg-adjusted p-value across the tested target-change candidates. |
| Stratum / replicate | One manifest identifier pairing exactly one control and one treatment sample. |
| Common odds ratio | CMH effect estimate shared across the paired strata; values above `1` favor treatment enrichment and below `1` favor control, subject to the declared thresholds. |
| `FWD_like`, `REV_like` | Legacy mechanical SAM-flag groups; not biological strand labels. |
| Computational call | A Step `09` threshold classification such as `significant_up`; still pending scientific adjudication. |
| External review or adjudication | A research work process that may reference EMRYS outputs but is not an EMRYS step, gate, artifact, or completion state. |
| Create-absent / no-clobber | Publication that requires the destination not to exist and refuses replacement or adoption. |
| Receipt-last | The transaction receipt is published only after its declared payload has been checked; the receipt still must be semantically re-admitted. |
| Run root | The immutable/evidence-bearing directory for one deterministic normalized run ID. |

## Further guidance

| Need | Canonical guide |
| --- | --- |
| Every input and runtime-profile field | [`configs/README.md`](configs/README.md) |
| Public local-pilot boundary | [`src/emrys/orchestration/local_pilot/README.md`](src/emrys/orchestration/local_pilot/README.md) |
| Recurring operations, scheduler inspection, and recovery | [`docs/operations/RUNBOOK.md`](docs/operations/RUNBOOK.md) |
| Evidence-preserving recovery | [`docs/operations/TROUBLESHOOTING.md`](docs/operations/TROUBLESHOOTING.md) |
| Optional external scientific-evaluation checklist | [`docs/reference/EXTERNAL_SCIENTIFIC_EVALUATION.md`](docs/reference/EXTERNAL_SCIENTIFIC_EVALUATION.md) |
| Operator report build and workflow-owned reporting transactions | [`src/emrys/reporting/README.md`](src/emrys/reporting/README.md) |
| Architecture and complete owner DAG | [`docs/architecture/README.md`](docs/architecture/README.md) |
| Current validation evidence and remaining gaps | [`docs/operations/HANDOFF.md`](docs/operations/HANDOFF.md) |
| Local test routes | [`tests/README.md`](tests/README.md) |

## License

EMRYS is **source-available**, not open-source software. You may use and modify
EMRYS without charge for academic, nonprofit, research, and internal commercial
work. You may also commercialize the scientific data, results, reports,
visualizations, interpretations, discoveries, and other outputs produced using
EMRYS, and you may charge for research, compute, or analysis services that
deliver those outputs.

You may not sell EMRYS itself, including through paid rebranding, licensing, or
sublicensing, or by offering EMRYS or substantially equivalent EMRYS
functionality as a paid hosted or managed product or service. The complete
terms in [`LICENSE`](LICENSE) control. Third-party software, tools, data, and
references retain their own terms; see [`NOTICE`](NOTICE) and
[`LICENSES/`](LICENSES/).

Do not commit FASTQ, BAM, CRAM, VCF, production result tables, logs,
credentials, restored tools/libraries, or caches. Before deleting ignored data,
results, locks, or logs, establish their owner, active consumers, recovery
state, and retention requirements.
