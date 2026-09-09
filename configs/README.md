# Configuration and input guide

This guide defines Project inputs and execution settings. Use the
[quickstart](../quickstart.md) to create and run a Project, and the
[runbook](../docs/operations/RUNBOOK.md) for later operations.

## What belongs here

| Files | Purpose |
| --- | --- |
| `samples.example.tsv` | Five-column fixture for the generic manifest validator; not a complete paired-CMH Project manifest. Use the [Project sample format](#sample-manifest) below. |
| `step_07_partitions*.tsv` | Example region partitions for cohort processing. |
| `execution_profile*.yaml` | Example local or Slurm execution settings. |
| Other `.example.*` files | Specialist formats owned by the component that consumes them. |

The parent of `project.yaml` is the Project root. EMRYS manages its `logs/`,
`runtime/`, and `runs/`; FASTQs, references, and manifests stay where declared.

Paths declared by `project.yaml` and its sample manifest, including FASTQ
entries, resolve from the Project root. A partition `regions_file` entry resolves
from that manifest's directory. Paths are literal and may be absolute or
relative but cannot contain `~`, environment variables, templates, globs,
redundant separators, or `.`/`..` components. Keep the Project and every
referenced input for the life of its Runs.

## `project.yaml`

The closed `emrys.project.v1` document shares one Dataset and Reference across
one or more named Analyses:

```yaml
schema_version: emrys.project.v1
dataset:
  samples: samples.tsv
reference:
  fasta: reference/genome.fa
  gtf: reference/genes.gtf
  star_index:
    sjdb_overhang: 149
    genome_sa_index_nbases: 14
analyses:
  primary:
    partitions: partitions.tsv
    control_condition: EV
    treatment_condition: PUM1
    target_change: A>G
    min_sample_dp: 1
    mean_dp_threshold: 50
    fdr_threshold: 0.05
    common_or_threshold: 1.2
    absolute_difference_threshold: 0.005
    background_condition: null
    background_max_fraction: 0.01
```

Replace the example paths, conditions, reference, STAR parameters, and thresholds
with your study's choices. EMRYS does not infer them from reads. `star_index`
configures index construction; it does not admit an external prebuilt index.

Unknown fields, duplicate keys, merge keys, and legacy request-v3 documents
are rejected by current Project commands. The FASTA parent must permit the
Step `00c` `.fai` and `.dict` sidecars. Safe identifiers begin with an ASCII
letter or digit and contain only letters, digits, `.`, `_`, or `-`.

### Built-in Analysis fields

The built-in Analysis uses paired, two-sided, continuity-corrected
Cochran-Mantel-Haenszel tests and one global Benjamini-Hochberg correction over
all successfully tested target candidates. Minimum sample depth is inclusive;
the other threshold comparisons are strict.

| Field | Contract |
| --- | --- |
| Analysis mapping key | Human selector for `--analysis`; it is not part of content-derived Analysis identity. |
| `partitions` | One admitted, nonoverlapping partition manifest. Multiple Analyses may share it. |
| `sample_ids` | Optional nonempty, unique subset of Dataset IDs. Omission selects all samples; manifest order is preserved. |
| `control_condition` / `treatment_condition` | Distinct conditions with exactly the same replicate strata. |
| `target_change` | Two distinct canonical bases, such as `A>G`. Other changes remain non-target rows. |
| `min_sample_dp` | Every paired control/treatment sample needs usable counts and depth at least this value for testing. Background samples are checked separately. |
| `mean_dp_threshold` | Tested candidates advance only when mean depth across paired control/treatment samples is greater than this value. |
| `fdr_threshold` | Candidates advance only when global BH-adjusted p-value is less than this value. |
| `common_or_threshold` | Must exceed `1`; up calls require a greater OR and down calls an OR below its reciprocal. |
| `absolute_difference_threshold` | Up calls require treatment-minus-control mean AF greater than this value; down calls require it below the negative of this value, alongside the corresponding OR criterion. |
| `background_condition` | Optional distinct non-paired condition. It filters calls without changing paired CMH testing or the BH family. |
| `background_max_fraction` | Every background sample must have usable counts, depth at least `min_sample_dp`, and AF below this value. Missing or insufficient counts fail the background filter. |

These are computational ranking choices, not biological conclusions. Changing
the selected samples or policy creates a distinct immutable Analysis and Run.

### Collaborator Analysis

A collaborator Analysis uses an installed provider and its closed configuration:

```yaml
analyses:
  differential:
    module: org.example.differential
    partitions: partitions.tsv
    config:
      design: "~ condition"
      fdr: 0.05
```

`module` names an installed `emrys.analysis_modules` entry point; EMRYS never
infers, installs, or substitutes it. The [provider contract](../src/emrys/analyses/README.md)
defines scientific ownership and the shared Run, task, and Results guarantees.

## Sample manifest

`samples.tsv` is literal tab-separated data. Setup can draft it from supplied
paths and metadata; filenames never establish conditions or pairing.

This six-column example declares two `EV`/`PUM1` pairs. Replace the paths and
metadata; `unknown` is an allowed strandedness value, not a measured result.

```tsv
sample_id	r1_fastq	r2_fastq	strandedness	condition	replicate
EV_1	/data/EV_1_R1.fastq.gz	/data/EV_1_R2.fastq.gz	unknown	EV	pair1
PUM1_1	/data/PUM1_1_R1.fastq.gz	/data/PUM1_1_R2.fastq.gz	unknown	PUM1	pair1
EV_2	/data/EV_2_R1.fastq.gz	/data/EV_2_R2.fastq.gz	unknown	EV	pair2
PUM1_2	/data/PUM1_2_R1.fastq.gz	/data/PUM1_2_R2.fastq.gz	unknown	PUM1	pair2
```

| Column | Contract |
| --- | --- |
| `sample_id` | Required unique safe identifier. |
| `r1_fastq` / `r2_fastq` | Required distinct files with the same plain or gzip compression mode. |
| `strandedness` | Exactly `forward`, `reverse`, `unstranded`, or `unknown`. |
| `condition` | Authored experimental condition. |
| `replicate` | Required pairing-stratum identity: the control and treatment belonging to the same pair share this value. Row order and filenames do not establish pairing. |
| `notes` | Optional final column, present on every row when used. |

The built-in Analysis requires at least two strata, each with one control and
one treatment. Technical lanes are not biological replicates unless the study
declares them so. Retain provider checksums: file binding does not prove provenance.

## Partition manifest

`partitions.tsv` has exactly three columns:

| Column | Contract |
| --- | --- |
| `partition_id` | Required unique safe identifier. |
| `selector_type` | `region` for a bcftools `-r` expression or `regions_file` for an admitted `-R` file. |
| `selector_value` | A FASTA/FAI contig or interval, or a literal regions-file path. |

Partitions must not overlap. Begin with a small declared region when verifying
an unfamiliar runtime. Zero candidates and a header-only VCF may be valid when
the declared transaction reconciles.

## Execution profile

Execution settings are separate from scientific inputs. The
[coordinator contract](../src/emrys/orchestration/run_coordinator/CONTRACT.md#profiles-and-immutable-planning)
owns profile selection, precedence, and historical compatibility.

An `emrys.execution-profile.v1` document separates resource budgets from
placement (where to run):

| Under `resources` | Meaning |
|---|---|
| `workflow_cores` | Total CPU budget for the workflow. |
| `workflow_memory_mb` | Total memory budget in MiB; `allocation` uses the available allocation. |
| `stage_concurrency` | Maximum simultaneous tasks for each repeatable stage. |
| `step_threads` | Threads per task for stages that support threaded tools. |
| `stage_memory_mb` | Memory budget per stage task in MiB; `workflow` uses the workflow budget. |

`placement` chooses direct execution or one Slurm allocation. Its fields cover
account, partition, `qos` (the site's Quality of Service class), CPUs, memory,
time, exclusivity, node selection, scratch, and exact module setup. See the
[stage map](../src/emrys/contracts/STAGE_MAP.md) for numeric stage identities.

Values are literal; unknown fields, interpolation, shell commands, impossible
totals, and resources larger than the allocation are rejected. The generated
default uses direct placement; [execution_profile.example.yaml](execution_profile.example.yaml)
shows Slurm fields. Retired reporting-memory settings are rejected.

## Specialist examples

Other examples cover artifact/report inputs, reference provenance, retention,
runtime/storage inspection, and pairing evidence. Use them only when the named
component requests that format; example content is not evidence from a real Run.
