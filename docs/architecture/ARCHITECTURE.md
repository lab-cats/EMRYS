# NORAD Pipeline Architecture

This page is a compact visual map for PI demo use. It summarizes the pipeline shape, validated boundaries, output contracts, and reliability pattern without replacing `docs/design/PIPELINE_PLAN.md` or `docs/operations/RUNBOOK.md` as the detailed sources of truth.

For deferred modular architecture ideas, see `docs/architecture/FUTURE_ARCHITECTURE.md`.

## One-Screen Summary

This project rebuilds a legacy hardcoded RNA-editing/RNA-seq workflow into a staged, dry-run-first, testable SLURM pipeline.

Steps `00a`-`00c` are cluster-proven reference prep. Steps `01`-`06` are cluster-proven across all six samples. Step `07` is implemented locally and locally tested with mocked bcftools at commit `e68b00c`; it has not run with real bcftools, passed a cluster dry-run, executed on the cluster, or produced inspected cluster outputs, and it is not cluster-proven. Steps `08`-`09` remain pending / not implemented / not cluster-proven, and Step `08` is the next local implementation boundary.

Current boundary:

```text
cluster-proven reference prep through Steps 00a-00c
-> cluster-proven sample workflow through Step 06
-> Step 07 implemented and locally tested with mocked bcftools; cluster validation pending
-> Step 08 next local implementation boundary
-> Step 09 pending editing-site calling
```

## Pipeline Dataflow

```mermaid
flowchart LR
    classDef proven fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef boundary fill:#fff8e1,stroke:#f9a825,color:#5f4300,stroke-width:2px
    classDef pending fill:#f5f5f5,stroke:#757575,color:#424242,stroke-dasharray:4 3
    classDef input fill:#e3f2fd,stroke:#1565c0,color:#0d47a1

    subgraph ref["Reference prep"]
        direction TB
        s00a["00a STAR index<br/>cluster-proven"]
        s00b["00b GTF -> BED12<br/>cluster-proven"]
        s00c["00c GATK sidecars<br/>cluster-proven"]
    end

    subgraph sample["Sample preprocessing"]
        direction TB
        fastq["FASTQ<br/>raw paired-end reads"]
        s01["01 STAR alignment<br/>cluster-proven"]
        s02["02 canonical BAM<br/>cluster-proven"]
        s02b["02b BAM QC<br/>cluster-proven"]
        s03["03 strandedness<br/>cluster-proven"]
        s04["04 MarkDuplicates<br/>cluster-proven"]
        s05["05 SplitNCigarReads<br/>cluster-proven"]
        s06["06 read-orientation split<br/>cluster-proven"]
    end

    subgraph downstream["Downstream editing workflow"]
        direction TB
        s07["07 bcftools mpileup<br/>implemented + mocked-bcftools tested locally<br/>not cluster-proven"]
        s08["08 VCF preprocessing<br/>next local implementation<br/>pending"]
        s09["09 CMH/editing-site calling<br/>pending"]
    end

    fastq --> s01 --> s02
    s00a --> s01
    s00b --> s03
    s00c --> s05
    s02 --> s02b
    s02 --> s03
    s02 --> s04 --> s05 --> s06 --> s07 --> s08 --> s09

    class fastq input
    class s00a,s00b,s00c,s01,s02,s02b,s03,s04,s05,s06 proven
    class s07 boundary
    class s08,s09 pending
```

Standalone Mermaid source: `docs/architecture/diagrams/pipeline.mmd`.

## Step Status Matrix

| Step | Main output | Status | Notes |
| ---- | ----------- | ------ | ----- |
| `00a` | `refs/novogene_star_index/` | cluster-proven reference prep | STAR index built with `sjdbOverhang=149`. |
| `00b` | `refs/novogene_ref/genome.bed` | cluster-proven reference prep | BED12 generated for RSeQC. |
| `00c` | `refs/novogene_ref/genome.fa.fai`, `refs/novogene_ref/genome.dict` | cluster-proven reference prep | GATK sidecars validated once, not inside per-sample jobs. |
| `01` | `results/star/<sample>/` | cluster-proven across all six samples | STAR alignment. |
| `02` | `results/bam/<sample>/<sample>.sorted.bam(.bai)` | cluster-proven across all six samples | Canonical coordinate-sorted, read-group-tagged BAM. |
| `02b` | `results/qc/bam/<sample>.*.txt` | cluster-proven across all six samples | BAM quickcheck/flagstat QC. |
| `03` | `results/qc/strandedness/<sample>.infer_experiment.txt` | cluster-proven across all six samples | All six libraries are reverse-stranded / first-strand-style. |
| `04` | `results/markdup/<sample>/<sample>.markdup.bam(.bai)` | cluster-proven across all six samples | Duplicate reads are marked, not removed. |
| `05` | `results/split_ncigar/<sample>/<sample>.split_ncigar.bam(.bai)` | cluster-proven across all six samples | GATK temp handling hardened to project storage. |
| `06` | `results/orientation/<sample>/`, `results/qc/orientation/` | cluster-proven across all six samples | Mechanical `FWD_like` / `REV_like` split. |
| `07` | `results/mpileup/<cohort>/<partition>/<cohort>.<partition>.FWD_like.mpileup.vcf`, `results/mpileup/<cohort>/<partition>/<cohort>.<partition>.REV_like.mpileup.vcf`, and `results/mpileup/<cohort>/<partition>/<cohort>.<partition>.step07_outputs.tsv` | implemented locally and locally tested with mocked bcftools; not cluster-proven | Cohort-wide per declared partition. No real-bcftools runtime, cluster dry-run, execute run, or inspected cluster output yet. |
| `08` | `results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv`, `results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv`, and `results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv` | pending / not implemented / not cluster-proven | Approved contract exists; R/Rscript availability and real-R fixture validation remain unresolved. |
| `09` | six approved tables/plots under `results/editing/<analysis>/` | pending / not implemented / not cluster-proven | Approved paired-CMH output contract exists; implementation and real-R validation remain pending. |

## Data Contracts

| Stage | Contract |
| ----- | -------- |
| STAR alignment | `results/star/<sample>/` |
| Canonical BAM | `results/bam/<sample>/<sample>.sorted.bam(.bai)` |
| MarkDuplicates | `results/markdup/<sample>/<sample>.markdup.bam(.bai)` |
| SplitNCigarReads | `results/split_ncigar/<sample>/<sample>.split_ncigar.bam(.bai)` |
| Read-orientation BAMs | `results/orientation/<sample>/<sample>.FWD_like.bam(.bai)` and `results/orientation/<sample>/<sample>.REV_like.bam(.bai)` |
| Orientation QC | `results/qc/orientation/<sample>.orientation_counts.tsv` |
| Cohort mpileup partition | `results/mpileup/<cohort>/<partition>/<cohort>.<partition>.FWD_like.mpileup.vcf`, `results/mpileup/<cohort>/<partition>/<cohort>.<partition>.REV_like.mpileup.vcf`, and `results/mpileup/<cohort>/<partition>/<cohort>.<partition>.step07_outputs.tsv` |

## Reliability Workflow

```mermaid
flowchart LR
    classDef gate fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef cluster fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef safeguard fill:#fff8e1,stroke:#f9a825,color:#5f4300
    classDef docs fill:#f5f5f5,stroke:#616161,color:#424242

    stagebranch["stage branch<br/>from prior docpatch"]
    local["local implementation<br/>macOS / VS Code"]
    tests["local tests<br/>syntax + fake tools"]
    implcommit["implementation commit"]
    stagepatch["repository-wide docpatch<br/>separate commit"]
    cleanpush["clean check / push"]
    descendant["next descendant<br/>stage branch"]
    pull["cluster pull<br/>CSU checkout"]
    dryrun["SLURM dry-run<br/>default gate"]
    execute["execute<br/>explicit EXECUTE=1"]
    validate["validate outputs<br/>logs + contracts"]
    validationpatch["validation docpatch<br/>evidence + status"]

    fake["fake-tool tests"]
    drydefault["dry-run default"]
    execflag["explicit EXECUTE=1"]
    locks["locks"]
    runtoken["run-token temp files"]
    publish["validate before publish"]
    rollback["rollback"]
    cleanup["cleanup"]
    trouble["troubleshooting docs"]

    stagebranch --> local --> tests --> implcommit --> stagepatch --> cleanpush --> descendant
    cleanpush --> pull --> dryrun --> execute --> validate --> validationpatch

    fake -.-> tests
    drydefault -.-> dryrun
    execflag -.-> execute
    locks -.-> execute
    runtoken -.-> execute
    publish -.-> validate
    rollback -.-> validate
    cleanup -.-> validate
    trouble -.-> stagepatch
    trouble -.-> validationpatch

    class stagebranch,local,tests,implcommit,cleanpush,descendant gate
    class pull,dryrun,execute,validate cluster
    class fake,drydefault,execflag,locks,runtoken,publish,rollback,cleanup,trouble safeguard
    class stagepatch,validationpatch docs
```

Standalone Mermaid source: `docs/architecture/diagrams/reliability.mmd`.

Safeguards:

- dry-run default
- explicit `EXECUTE=1`
- scope-owned locks, including sample and cohort/partition locks
- run-token temp files
- validate-before-publish
- rollback protection
- cleanup on failure
- fake-tool shell tests
- troubleshooting docs

## Local Vs Cluster Responsibilities

| Local macOS | CSU/ADAM SLURM |
| ----------- | -------------- |
| Edit scripts/docs/tests. | Run real STAR/samtools/Picard/GATK/bcftools jobs. |
| Run fake-tool shell tests and syntax checks. | Execute sample-scale workflows through `jobs/*.slurm`. |
| Validate command construction and dry-run behavior. | Inspect SLURM logs, scheduler status, and output files. |
| Commit/push reviewed changes. | Pull committed changes before dry-run and execute gates. |

## Biological Interpretation Caution

`FWD_like` and `REV_like` are mechanical read-orientation groups based on legacy samtools flag filters. They are not automatically biological strand, transcript strand, sense, or antisense labels.

```text
FWD_like = samtools view -f 99 plus samtools view -f 147
REV_like = samtools view -f 83 plus samtools view -f 163
```

`samtools view -f FLAG` means a record has all bits in `FLAG`; it is not exact flag equality.

## What Remains

1. Create the descendant Step `08` branch from the clean, pushed Step `07` implementation and docpatch history.
2. Implement, locally test, and docpatch Step `08`, then repeat the gate for Step `09`.
3. Begin later cluster promotion with a Step `07` dry-run and narrow pilot before primary-contig execution.
4. Do not execute downstream stages on the cluster until each preceding stage is cluster-proven.
5. Review QC and biological interpretation with PI guidance.
