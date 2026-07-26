# NORAD Pipeline Architecture

This page is a compact visual map for PI demo use. It summarizes the pipeline shape, validated boundaries, output contracts, and reliability pattern without replacing `docs/design/PIPELINE_PLAN.md` or `docs/operations/RUNBOOK.md` as the detailed sources of truth.

For deferred modular architecture ideas, see `docs/architecture/FUTURE_ARCHITECTURE.md`.

## One-Screen Summary

This project rebuilds a legacy hardcoded RNA-editing/RNA-seq workflow into a staged, dry-run-first, testable SLURM pipeline.

Steps `00a`-`00c` are cluster-proven reference prep. Steps `01`-`06` are
cluster-proven across all six samples. Step `07` is implemented locally and
mocked-bcftools tested at commit `e68b00c`, but it has no real-bcftools or
cluster evidence. Step `08` is implemented locally at `90335d8`, and Step
`09` is implemented locally at `e4371de`; both retain passing shell/fake-R
contracts.

The signed and notarized Apple-silicon CRAN R `4.6.1` runtime is now installed
locally. A guarded repository `renv` environment is locked to Bioconductor
`3.23` and activates only with `NORAD_USE_RENV=1`. Namespace, lock consistency,
headless PDF, and empty cache-disabled binary restore checks pass. Both real-R
fixture suites now execute without `SKIP`, but neither is a semantic pass:
Step `08` exposes a partition-overlap rejection defect, and Step `09` exposes a
locale-sensitive PDF EOF test assertion. Those defects trigger the next
descendant `step-09b1-real-r-fixes`.

No Step `07`-`09` remote dry-run, execute, log, or output evidence was added;
all three remain not cluster-proven. Remote promotion is intentionally paused
while the approved local sequence implements scientific-validation tooling,
the artifact/run-summary/report vertical slice, read-only foundations, and
one validator branch per pipeline step.

Current boundary:

```text
cluster-proven reference prep through Steps 00a-00c
-> cluster-proven sample workflow through Step 06
-> Step 07 implemented and locally tested with mocked bcftools; cluster validation pending
-> local R 4.6.1 + guarded renv/Bioconductor 3.23 environment checks pass
-> Step 08 and Step 09 real-R suites execute individually without SKIP but expose two defects
-> step-09b1-real-r-fixes is next; remote validation remains paused
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
        s08["08 VCF preprocessing<br/>real-R suite executed; partition-overlap defect open<br/>not cluster-proven"]
        s09["09 CMH/editing-site calling<br/>real-R suite executed; PDF-test defect open<br/>not cluster-proven"]
    end

    localr["09b local R runtime<br/>R 4.6.1 + guarded renv / Bioc 3.23<br/>environment checks pass"]
    fixes["09b1 real-R fixes<br/>next local branch"]
    science["09c scientific-validation tooling<br/>local evidence package; no biological-readiness claim"]
    reports["immediate artifact + report slice<br/>schema -> adapters -> run summary -> HTML -> PDF<br/>activated, not implemented"]

    fastq --> s01 --> s02
    s00a --> s01
    s00b --> s03
    s00c --> s05
    s02 --> s02b
    s02 --> s03
    s02 --> s04 --> s05 --> s06 --> s07 --> s08 --> s09
    s09 --> localr --> fixes --> science --> reports

    class fastq input
    class s00a,s00b,s00c,s01,s02,s02b,s03,s04,s05,s06 proven
    class s07,s08,s09,localr boundary
    class fixes,science,reports pending
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
| `08` | `results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv`, `results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv`, and `results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv` | implemented locally at `90335d8`; shell/fake-R tested; real-R suite executes but currently fails partition-overlap rejection; not cluster-proven | Consumes the exact partition-manifest × `{FWD_like,REV_like}` receipt set. The local R runtime is available, but semantic real-R acceptance awaits `step-09b1-real-r-fixes`; no cluster evidence exists. |
| `09` | four TSVs and two PDFs under `results/editing/<analysis>/` | implemented locally at `e4371de`; shell/fake-R tested; real-R suite executes but currently fails a locale-sensitive PDF EOF test assertion; not cluster-proven | Uses explicit manifest-defined pairs plus the Step `08` sites table and complete input receipt. Semantic real-R acceptance awaits `step-09b1-real-r-fixes`; no cluster evidence exists. |

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
| VCF preprocessing | `results/vcf_preprocessed/<cohort>/<cohort>.step08_sites.tsv`, `results/vcf_preprocessed/<cohort>/<cohort>.step08_inputs.tsv`, and `results/qc/vcf_preprocessing/<cohort>.step08_summary.tsv` |
| Paired CMH calling | `results/editing/<analysis>/<analysis>.cmh_all_sites.tsv`, `results/editing/<analysis>/<analysis>.cmh_significant_sites.tsv`, `results/editing/<analysis>/<analysis>.cmh_summary.tsv`, `results/editing/<analysis>/<analysis>.mutation_spectrum.tsv`, `results/editing/<analysis>/<analysis>.mutation_spectrum.pdf`, and `results/editing/<analysis>/<analysis>.depth_delta.pdf` |

Step `08` enumerates the exact declared partition set in manifest order and both orientations in fixed `FWD_like`, then `REV_like`, order. It validates the Step `07` receipts, manifest hashes, VCF paths, declared record counts, and exact sample order rather than globbing available files. The deterministic wide candidate table starts with:

```text
partition_id
candidate_id
orientation
chromosome
position
alt_index
genomic_ref
genomic_alt
rna_ref
rna_alt
annotation_strand
gene_ids
transcript_ids
is_cds
is_five_prime_utr
is_three_prime_utr
is_exon
is_intron
qual
filter
info_alt_depth
orientation_policy
```

It then appends manifest-ordered `DP__<sample>`, `AD__<sample>`, and `AF__<sample>` groups. The exact inputs-receipt schema is:

```text
cohort_id
partition_id
selector_type
selector_value
orientation
step07_receipt_path
step07_receipt_sha256
vcf_path
vcf_sha256
sample_manifest_sha256
partition_manifest_sha256
annotation_gtf
annotation_gtf_sha256
sample_count
declared_vcf_record_count
observed_vcf_record_count
observed_alt_allele_count
supported_snv_count
skipped_symbolic_count
skipped_non_snv_count
published_candidate_count
orientation_policy
```

The exact one-row QC-summary schema is:

```text
cohort_id
partition_count
step07_receipt_count
input_vcf_count
sample_count
observed_vcf_record_count
observed_alt_allele_count
supported_snv_count
skipped_symbolic_count
skipped_non_snv_count
published_candidate_count
sample_manifest_sha256
partition_manifest_sha256
annotation_gtf
annotation_gtf_sha256
orientation_policy
```

The receipt and summary reconcile every declared VCF's observed records, ALT alleles, supported SNVs, skipped symbolic/non-SNV alleles, and published candidates. `step08_inputs.tsv` is published last as the complete Step `08` output-set commit marker.

Step `09` uses only explicit replicate pairs from the full sample manifest and
validates its hash against the complete Step `08` input receipt. It retains
every candidate with explicit test/call/background status, runs two-sided
continuity-corrected paired CMH tests, and applies one BH family across all
successfully tested target candidates before call-level depth, background, and
effect filters. Defaults are EV versus PUM1, RNA `A>G`, per-sample DP at least
`1`, mean DP strictly above `50`, FDR strictly below `0.05`, common OR above
`1.2` or below `1/1.2`, and absolute treatment-control difference above
`0.005`. Background is disabled by default. The six files are one
rollback-protected transaction whose summary is published last; all-sites,
significant-sites, and summary preserve
`orientation_policy=legacy_provisional_v1`, which is not biologically
validated.

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
    descendant["next descendant<br/>local stage branch"]
    localr["local R gate<br/>guarded renv / real-R suites"]
    sciencebranch["scientific-validation tooling<br/>explicit evidence; dry-run first"]
    artifacts["artifact contracts<br/>schema -> adapters -> run summary"]
    reports["immediate reports<br/>HTML -> PDF exports"]
    foundations["read-only foundations<br/>runtime -> reference -> storage"]
    validators["one validator branch per step<br/>00a through 09"]
    localstop["final local validator<br/>clean / docpatched / pushed"]
    remotehold["remote promotion paused"]
    pull["later cluster pull<br/>CSU checkout"]
    dryrun["SLURM dry-run<br/>default gate"]
    execute["execute<br/>explicit EXECUTE=1"]
    validate["validate outputs<br/>logs + contracts"]
    validationpatch["evidence + report regeneration<br/>validation docpatch"]

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
    descendant --> localr --> sciencebranch --> artifacts --> reports --> foundations --> validators --> localstop --> remotehold
    remotehold -.-> pull --> dryrun --> execute --> validate --> validationpatch
    validationpatch -->|clean push, then next descendant| pull

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
    trouble -.-> sciencebranch

    class stagebranch,local,tests,implcommit,cleanpush,descendant,localr,localstop gate
    class pull,dryrun,execute,validate cluster
    class fake,drydefault,execflag,locks,runtoken,publish,rollback,cleanup,trouble safeguard
    class stagepatch,validationpatch docs
    class sciencebranch,artifacts,reports,foundations,validators safeguard
    class remotehold docs
```

Standalone Mermaid source: `docs/architecture/diagrams/reliability.mmd`.

Safeguards:

- dry-run default
- explicit `EXECUTE=1`
- scope-owned locks, including sample, cohort/partition, and analysis locks
- run-token temp files
- validate-before-publish
- rollback protection
- cleanup on failure
- fake-tool shell tests, including fake-R Step `08`/`09` wrapper tests
- signed local R `4.6.1` with repository activation guarded by
  `NORAD_USE_RENV=1`
- a locked Bioconductor `3.23` environment, explicit restore/check targets,
  and cache-disabled empty-library restore coverage
- troubleshooting docs

## Local Vs Cluster Responsibilities

| Local macOS | CSU/ADAM SLURM |
| ----------- | -------------- |
| Edit scripts/docs/tests. | Run real STAR/samtools/Picard/GATK/bcftools jobs. |
| Run fake-tool shell tests, syntax checks, guarded real-R fixtures, scientific-validation fixtures, artifact aggregation, and synthetic report rendering. | Execute sample/cohort-scale workflows through `jobs/*.slurm`; compute wrappers never install R packages. |
| Validate command construction and dry-run behavior. | Inspect SLURM logs, scheduler status, and output files. |
| Commit/push reviewed changes. | Pull committed changes before dry-run and execute gates. |

## Biological Interpretation Caution

`FWD_like` and `REV_like` are mechanical read-orientation groups based on legacy samtools flag filters. They are not automatically biological strand, transcript strand, sense, or antisense labels.

```text
FWD_like = samtools view -f 99 plus samtools view -f 147
REV_like = samtools view -f 83 plus samtools view -f 163
```

`samtools view -f FLAG` means a record has all bits in `FLAG`; it is not exact flag equality.

Step `08` implements the explicitly provisional `orientation_policy=legacy_provisional_v1` mapping:

```text
FWD_like -> legacy neg -> compatible + transcripts -> complement DNA REF/ALT
REV_like -> legacy pos -> compatible - transcripts -> retain DNA REF/ALT
```

The output retains genomic alleles, RNA-normalized alleles, mechanical orientation, and compatible annotation strand. This policy preserves the legacy analysis mapping for reproduction; it is not biologically validated and must not be presented as such.

Likewise, `cluster-proven` establishes inspected runtime behavior, not
biological truth. `significant_up` and `significant_down` are configured
pipeline call statuses for CMH-ranked candidates. Orientation, GTF semantics,
threshold robustness, replicate sensitivity, candidate quality, and
background eligibility remain subject to the post-Step-09 scientific gate.
`science_review_complete_exploratory` records a finished review while keeping
results provisional. Step `09c` must reject the reserved
`biological_interpretation_ready` value until a separately approved scientific
policy unlocks its exit criteria. Artifact indexes, run summaries, and
HTML/PDF reports describe available evidence; producing them is never evidence
of computational or biological validation.

## What Remains

1. On `step-09b1-real-r-fixes`, correct the Step `08` partition-overlap
   rejection and the Step `09` locale-sensitive PDF EOF test assertion, then
   require both real-R suites to pass without `SKIP`.
2. Implement `step-09c-scientific-validation` as local, explicit-input,
   dry-run-first evidence tooling. Fixture completion can produce
   `evidence_incomplete` or `science_review_complete_exploratory`; it cannot
   produce `biological_interpretation_ready`.
3. Implement the immediate report vertical slice in order:
   `artifact-schema-v1`, `artifact-adapters-v1`,
   `artifact-run-summary`, `report-html-v1`, and `report-exports-v1`.
   Synthetic/incomplete reports must carry their state banners and must not be
   presented as validation evidence.
4. Implement the read-only foundations
   `post09-runtime-preflight`, `post09-reference-provenance`, and
   `post09-storage-inventory-retention`.
5. Add one descendant validation-report branch for each of `00a`, `00b`,
   `00c`, `01`, `02`, `02b`, `03`, `04`, `05`, `06`, `07`, `08`, and `09`,
   ending local work at `post09-validation-report-09`.
6. When remote work resumes, promote Steps `07`, `08`, and `09` in order,
   then validate Step `09c` scientific evidence and perform only targeted
   reruns, regenerating the structured run summary and reports after inspected
   evidence. Remote work is not part of the current sequence.
