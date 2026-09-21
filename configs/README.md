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
`runtime/`, and `runs/`. Guided initialization also creates `samples.tsv` and
`partitions.tsv` in that root. FASTQs, references, and regions files stay where
declared. Existing current-schema Projects may continue to reference manifests
at their established paths; new named initialization copies validated manifest
content into its Project.

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
    genome_chr_bin_nbits: 18
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

Replace the example paths, conditions, reference and thresholds with your study's
choices. Named Project creation derives an omitted `genome_sa_index_nbases` from
the admitted FASTA length before preview as
`max(1, floor(min(14, log2(total reference bases) / 2 - 1)))`. During creation's
existing FASTQ admission pass, it derives an omitted `sjdb_overhang` from the
maximum read length and resolves an omitted `genome_chr_bin_nbits`. References
with at most 5,000 sequences use `18`; references with more sequences use
`max(1, floor(min(18, log2(max(total reference bases / sequence count, maximum admitted read length)))))`.
Creation freezes all three numeric `star_index` values, while advanced callers
may supply explicit overrides. Existing hand-authored Projects that omit
`genome_chr_bin_nbits` retain STAR's prior value of `18`; EMRYS normalizes that
value without rewriting the Project. Hand-authored Projects still supply the
other two numeric values. `star_index` configures index construction; it does
not admit an external prebuilt index.

Guided creation asks once for a study-wide strandedness value when it must author
missing sample rows. `unknown` is the conservative prompt default; `mixed` is a
prompt-only branch that asks separately for each missing row and is never stored.
Persisted values remain exactly the four values in the sample-manifest contract
below. Conditions and pairing groups are always operator-authored. When those
new rows form exactly two conditions with identical, unambiguous pairing strata,
Init shows both control-to-treatment directions and requires a numbered choice
with no default; filenames and row order never choose the direction. Copied
manifests and explicit `--sample` rows retain their supplied content.

When all five built-in paired-CMH settings are omitted interactively, Init shows
their existing values together and offers one explicit acceptance. Declining
returns to the individual questions. If a background condition is present and
its maximum is also omitted, `background_max_fraction=0.01` is disclosed in the
same set; otherwise the closed configuration still persists `0.01` but displays
it as inactive because no background condition exists. These conveniences do
not change the scientific field semantics below or fill missing noninteractive
arguments.

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

The [quickstart's guided Project creation](../quickstart.md#3-create-the-project)
asks for these selectors. Its advanced command form accepts repeated
`--region PARTITION_ID SELECTOR` and
`--regions-file PARTITION_ID PATH` options. They can be combined; partition IDs
must be unique across both forms. A selector such as `1` selects that entire
contig without a regions file. Reference compatibility is checked during
Project creation.

Partitions must not overlap. Begin with a small declared region when verifying
an unfamiliar runtime. Zero candidates and a header-only VCF may be valid when
the declared transaction reconciles.

Region selectors and regions files must use the same chromosome or contig names
as the reference FASTA. For a `.bed` file, tab-separated columns use zero-based
coordinates with the end excluded: `chr1`, `0`, `100` selects the first 100
bases of `chr1`. A plain three-column region table instead uses one-based
coordinates with both ends included: `chr1`, `1`, `100` selects the same
interval. Do not change the extension without converting coordinates or use
this illustrative interval automatically. With the manifest helper,
`--region 1 1 --region 2 2 --region X X` selects whole contigs and
`--region target 1:1-100` selects an inclusive interval. Declare each intended
selector explicitly; `--region` and `--regions-file` may be combined when all
partition IDs are unique.

## Reusing an existing study definition

Operate a current Project in place with `emrys validate --project /absolute/path/project.yaml`
and the same `--project` selection on Doctor and Run. Named `emrys init NAME`
provides guided creation: omit `--execute`, review its admitted study summary,
then copy its quoted creation command to retain every answer without repeating
the questions. Referenced inputs are freshly checked on that second invocation.

Legacy bundles are preserved, not translated automatically. Unsupported fields
retain their schema diagnostics and point to guided setup or correction of a
current definition. Confirm biological assignments and scientific settings with
the study owner. Do not copy only a Project YAML into a new directory: relative
FASTQ paths in a sample manifest resolve from the Project root, even when the
manifest path itself is absolute. A move can therefore change their meaning.

## Execution profile

Execution settings are separate from scientific inputs. The
[coordinator contract](../src/emrys/orchestration/run_coordinator/CONTRACT.md#profiles-and-immutable-planning)
owns profile selection and precedence.

### Create a named profile without writing YAML

From an existing Project, preview placement and resource choices with
`emrys profile create NAME`. Choose `--site viking`, `--placement direct`, or
`--placement slurm`; add `--project /absolute/path/project.yaml` when outside
the Project. A name identifies `runtime/profiles/NAME.yaml`. Existing files,
including `default.yaml`, are preserved.

New Viking Projects already select the whole-node placement. For an
existing Project with an older placement, create a named Viking profile:

```bash
emrys profile create cohort --site viking
```

Review the complete placement, workflow, and stage settings. Repeat the same
command with `--execute` to create the absent profile, then select it with
`emrys doctor --profile cohort --repair` and `emrys run --profile cohort`.
Preview and creation do not read FASTQs, probe tools, or request an allocation;
Doctor and execution still perform their independent admission checks.

Custom Slurm placement requires `--cpus-per-task`, `--time`, and an absolute
`--scratch-parent`. Optional fields are `--account`, `--partition`, `--qos`,
`--memory-mb`, `--nodelist`, and `--exclusive`/`--no-exclusive`. Exact module
setup requires both an absolute `--module-init` and one or more ordered
`--module` values. Direct placement rejects Slurm-only options.

Set workflow budgets with `--workflow-cores` and `--workflow-memory-mb`.
The repeatable `--step-threads STAGE=COUNT`, `--stage-memory-mb STAGE=MIB`, and
`--stage-concurrency STAGE=COUNT` options use the existing stage identifiers
and resource validation. Any resource override saves the complete reviewed
computational policy. With placement options alone, the profile leaves
computational policy unspecified: a new Run uses packaged defaults and a
resumed Run retains its immutable policy. To change computation, create a new
Run. A larger reservation does not itself increase workflow or stage limits.

Impossible declared relationships fail during profile admission, before an
allocation. Symbolic capacity remains symbolic until actual allocation
admission; EMRYS does not silently lower an allowance. The
[profile contract](../src/emrys/orchestration/run_coordinator/CONTRACT.md#profiles-and-immutable-planning)
owns precedence, reservation checks, and immutable resume behavior.

The default workflow uses all process-accessible CPUs and RAM granted to the
allocation. Repeated stages share that allowance across the admitted samples or
partitions that fit; native thread controls receive each task's CPU share.
Singleton stages receive the workflow memory allowance. Viking requests one
exclusive node, all node RAM and 12 hours. This removes fixed workflow and stage
caps; it does not guarantee that serial or I/O-bound phases saturate the node.
Doctor and Run show the declared policy, then numeric limits inside the allocation.

For an existing Project with old explicit limits, create and select a fresh
profile. Profile creation starts from packaged defaults, not `default.yaml`.
The explicit allocation flags below save the entire current computational policy:

```bash
emrys profile create full-node --site viking \
  --workflow-cores allocation --workflow-memory-mb allocation
emrys profile create full-node --site viking \
  --workflow-cores allocation --workflow-memory-mb allocation --execute
emrys doctor --profile full-node
emrys run --profile full-node
```

Review the account, partition and other site fields in the preview. This creates
`runtime/profiles/full-node.yaml`; it preserves `default.yaml` and existing Runs.
A resumed Run retains its previous resource declaration. Use a new Run for the
new computational policy. An unchanged explicit numeric override remains a cap.

### Profile document

An `emrys.execution-profile.v1` document separates resource budgets from
placement (where to run):

| Under `resources` | Meaning |
|---|---|
| `workflow_cores` | Total CPU budget; `allocation` uses the process-accessible allocated CPUs. |
| `workflow_memory_mb` | Total memory budget in MiB; `allocation` uses the available allocation. |
| `stage_concurrency` | Positive maximum simultaneous tasks, or `auto` to fit sample/partition work to CPU and memory capacity. |
| `step_threads` | Positive CPU allowance per task, `auto` to divide workflow CPUs across stage concurrency, or `workflow` for the whole CPU allowance (concurrency 1). |
| `stage_memory_mb` | Positive MiB per task; `workflow` for the whole budget; `auto` to divide memory across stage concurrency; `{minimum_mb: N}` to share it while retaining a minimum per task. |

With automatic concurrency, the resolver takes the smallest of the number of
admitted tasks, tasks fitting the CPU allowance, and tasks fitting the memory
minimum. It then divides CPUs and memory using integer shares. For example,
256 CPUs, 524288 MiB and six samples give six STAR tasks with 42 threads and
87381 MiB each. With 96 CPUs, 131072 MiB and twenty samples, the 40960 MiB
minimum allows three STAR tasks with 32 threads and 43690 MiB each.
These recovered memory values are configurable planning minimums, not measured
bounds for every dataset. Explicit numeric limits and `workflow` retain their
meaning; `workflow` never silently becomes a shared per-task allowance.

| Stage | Default CPU use | Default task memory |
|---|---|---|
| `00a` STAR index | Whole workflow | Whole workflow |
| `00b` GTF conversion | Serial | Whole workflow |
| `00c` FASTA sidecars | Whole-workflow Java helper allowance; main operations serial | Whole workflow |
| `01` STAR alignment | Automatic samples and threads, including BAM sorting | Shared, minimum 40960 MiB |
| `02` canonical BAM | Automatic samples and samtools workers | Shared, minimum 4096 MiB |
| `02b` BAM QC | Automatic samples and flagstat read workers | Shared, minimum 2048 MiB |
| `03` RSeQC | Automatic samples; one CPU per task | Shared, minimum 4096 MiB |
| `04` duplicate marking | Automatic samples and Java helper allowance | Shared, minimum 32768 MiB |
| `05` SplitNCigarReads | Automatic samples and Java helper allowance | Shared, minimum 16384 MiB |
| `06` orientation | Automatic samples and samtools workers | Shared, minimum 4096 MiB |
| `07` mpileup | Automatic partitions; one CPU per task | Shared, minimum 8192 MiB |
| `08` preprocessing | Workflow CPUs; R uses at most the available VCF jobs | Whole workflow |
| `09`, `10` analysis | Serial main algorithms | Whole workflow |

Automatic shares are fixed for one Attempt rather than redistributed as tasks
finish. Steps `09`/`10` retain historical thread fields for retained-policy
compatibility. See the
[command-construction contract](../src/emrys/orchestration/run_coordinator/CONTRACT.md#profiles-and-immutable-planning)
for native tool controls, derivation, and minimum usable budgets.

`placement` chooses direct execution or one Slurm allocation. Its fields cover
account, partition, `qos` (the site's Quality of Service class), CPUs, memory,
time, exclusivity, node selection, scratch, and exact module setup. See the
[stage map](../src/emrys/contracts/STAGE_MAP.md) for numeric stage identities.

Values are literal; unknown fields, interpolation, shell commands, impossible
totals, and resources larger than the allocation are rejected. Project creation
with `--site viking` writes the built-in Viking placement to
`runtime/profiles/default.yaml`; users do not supply scheduler settings. Without
a site selection, creation retains direct placement.
[execution_profile.example.yaml](execution_profile.example.yaml) shows the fields
for administrators configuring another placement. Retired reporting-memory
settings are rejected.

For a site administrator configuring Slurm, these fields are under `placement`:

| Field | Value |
| --- | --- |
| `cpus_per_task` | A positive integer, or `node` with `exclusive: true` to request every CPU on one node without fixing its size. |
| `memory_mb` | Positive MiB, `0` for all node memory (`--mem=0`), or `null` to leave the request to site policy. Exclusivity alone does not request all RAM. |
| `time` | The wall-time limit; use a quoted `"HH:MM:SS"` value, such as `"08:00:00"`. |
| `modules` without module setup | `mode: none`, `init: ""`, and `load: []`. |
| `modules` with module setup | `mode: exact`, an absolute path to the real, nonsymlink initialization file in `init`, and a nonempty list of exact module names in `load`. |

The batch wrapper starts with `PATH=/usr/bin:/bin`. For exact module setup it
sources the initialization file, purges modules, then loads the declared names
in order. The interactive module roster is not inherited. Record the setup
used to admit the runtime; the wrapper does not install dependencies.

### Slurm and tool resource semantics

The
[profile contract](../src/emrys/orchestration/run_coordinator/CONTRACT.md#profiles-and-immutable-planning)
owns allocation observation, automatic sharing, native tool controls, and their
limits. Resource declarations are admission controls, not live utilization or
performance measurements. Base overrides on comparable retained measurements;
use the [resource benchmark procedure](../docs/operations/RUNBOOK.md#resource-benchmarking)
for operator-owned trials.

## Specialist examples

Other examples cover artifact/report inputs, reference provenance, and pairing.
Use them only when their owner requests that format; examples are not Run evidence.
