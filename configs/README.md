# Configuration and input guide

This directory contains examples of scientist-authored inputs and optional
execution settings. The [quickstart](../quickstart.md) explains how to create
and run a Project; the [runbook](../docs/operations/RUNBOOK.md) explains the
commands available after setup.

## What belongs here

| Files | Purpose |
| --- | --- |
| `samples.example.tsv` | Example Dataset manifest. |
| `step_07_partitions*.tsv` | Example region partitions for cohort processing. |
| `execution_profile*.yaml` | Example local or Slurm execution settings. |
| Other `.example.*` files | Specialist formats owned by the component that consumes them. |

The scientist-authored `project.yaml` normally lives in the Project root, not
in this directory. Its parent is the Project root. EMRYS manages that Project's
`logs/`, `runtime/`, and `runs/` directories; FASTQs, references, and manifests
stay at their declared locations.

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

Unknown fields, duplicate keys, merge keys, and legacy request-v3 documents
are rejected by current Project commands. The FASTA parent must permit the
Step `00c` `.fai` and `.dict` sidecars. Safe identifiers begin with an ASCII
letter or digit and contain only letters, digits, `.`, `_`, or `-`.

### Built-in Analysis fields

The built-in Analysis uses paired, two-sided, continuity-corrected
Cochran-Mantel-Haenszel tests and one global Benjamini-Hochberg correction.
Threshold comparisons are strict.

| Field | Contract |
| --- | --- |
| Analysis mapping key | Human selector for `--analysis`; it is not part of content-derived Analysis identity. |
| `partitions` | One admitted, nonoverlapping partition manifest. Multiple Analyses may share it. |
| `sample_ids` | Optional nonempty, unique subset of Dataset IDs. Omission selects all samples; manifest order is preserved. |
| `control_condition` / `treatment_condition` | Distinct conditions with exactly the same replicate strata. |
| `target_change` | Two distinct canonical bases, such as `A>G`. Other changes remain non-target rows. |
| `min_sample_dp` | Minimum depth required in every Analysis sample before testing. |
| `mean_dp_threshold` | Tested candidates advance only when mean depth is greater than this value. |
| `fdr_threshold` | Candidates advance only when global BH-adjusted p-value is less than this value. |
| `common_or_threshold` | Must exceed `1`; up calls require a greater OR and down calls an OR below its reciprocal. |
| `absolute_difference_threshold` | Minimum absolute treatment-minus-control mean allele-fraction change. |
| `background_condition` | Optional non-paired condition used only as a background filter. |
| `background_max_fraction` | Every usable background sample must have AF below this value and meet `min_sample_dp`. |

These fields define computational ranking policy, not a universal editing
standard or biological conclusion. A selected subset or changed policy creates
a distinct immutable Analysis and Run.

### Collaborator Analysis

An installed collaborator module replaces the built-in fields with an exact
provider ID and provider-owned closed configuration:

```yaml
analyses:
  differential:
    module: org.example.differential
    partitions: partitions.tsv
    config:
      design: "~ condition"
      fdr: 0.05
```

`module` names an installed `emrys.analysis_modules` entry point. EMRYS does
not infer, install, or substitute providers. The provider owns normalization
and scientific meaning while inheriting EMRYS's immutable Run, task,
publication, recovery, logging, and Results contracts. See
[`src/emrys/analyses/README.md`](../src/emrys/analyses/README.md).

## Sample manifest

`samples.tsv` is literal tab-separated data. Project setup can draft it from
supplied paths and explicit metadata, but EMRYS never guesses biological
conditions or replicate relationships from filenames.

| Column | Contract |
| --- | --- |
| `sample_id` | Required unique safe identifier. |
| `r1_fastq` / `r2_fastq` | Required distinct files with the same plain or gzip compression mode. |
| `strandedness` | Exactly `forward`, `reverse`, `unstranded`, or `unknown`. |
| `condition` | Authored experimental condition. |
| `replicate` | Required pairing-stratum identity; row order and filenames do not establish pairing. |
| `notes` | Optional final column, present on every row when used. |

The built-in Analysis requires at least two strata, each containing exactly one
control and one treatment row. Do not treat technical lanes as biological
replicates unless that is the declared experimental design. EMRYS binds the
files but does not prove sample provenance; retain provider checksums.

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

Execution configuration is separate from scientific configuration. Omission
of `--profile` selects `<project-root>/runtime/profiles/default.yaml`.
`--profile NAME` selects `runtime/profiles/NAME.yaml`; an absolute value selects
that exact file. There is no site/global registry or search path.

An `emrys.execution-profile.v1` document may contain:

- `resources`: `workflow_cores`, `workflow_memory_mb`, per-stage concurrency,
  per-step threads, per-stage memory, and reporting memory; and
- `placement`: direct execution or one outer Slurm allocation, including its
  account, partition, QoS, CPU, memory, time, exclusivity, node, scratch, and
  exact module policy.

Packaged defaults apply first, the selected profile overrides them, and CLI
resource flags have highest precedence. EMRYS rejects unknown fields,
interpolation, templates, shell commands, impossible totals, and resources
larger than the visible allocation. See
[`execution_profile.example.yaml`](execution_profile.example.yaml) for a Slurm
shape and the generated default profile for direct placement.

## Specialist examples

The remaining examples show the shape of inputs used for artifact/report
projection, reference provenance, retention, runtime or storage inspection,
and retained pairing evidence. An `.example` file is a structural starter, not
proof from a real Run. Use one only when the component that consumes it asks
for that format.
