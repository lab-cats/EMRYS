# Configuration and input guide

`emrys init project` is the supported Project-creation route. It collects the
current profile's scientific answers, validates existing sample and partition
manifests plus their reference, and plans one absent Project root. On a
terminal, omitted answers are prompted; automation supplies them as flags.
Add `--execute` only after reviewing the no-write plan.

The output must be outside the EMRYS checkout beneath an existing canonical,
writable parent. Setup creates the root and empty owned directories; Runs later
extend them as follows:

```text
PROJECT/
|-- project.yaml
|-- logs/
|-- runtime/
`-- runs/
    `-- RUN-ID/
        `-- results/
```

The `project.yaml` parent is the Project root. EMRYS creates and owns
`logs/`, `runtime/`, and `runs/`; ordinary `run` and Doctor commands derive
that root and do not accept a separate workspace. Scientist-facing Results
remain under `runs/<run-id>/results`, including reports beneath
`results/reports/<run-id>`.

Setup records the admitted absolute sample and initial Analysis-partition
manifest paths in `project.yaml`; manifests and FASTQ, FASTA, GTF, and
regions-file data all remain in place. `emrys init manifests` produces the
required portable form without inventing biological assignments. No execution
or runtime profile is generated or selected. Without `--profile` or
`--execution-profile`, execution remains direct with the built-in resource
policy. Runtime discovery separately admits the Project-owned
`runtime/runtime.tsv`.

Keep the Project and every referenced input for the life of its Runs. Changing
scientific inputs or computational policy is not a way to repair an entered
Attempt. Authored paths are literal: no `~`, environment interpolation,
templates, globs, redundant separators, or `.`/`..` components.

## Execution profile

EMRYS has one optional public execution configuration. With no selector, the
built-in profile uses conservative resources and direct placement. A selected
profile is a closed YAML fragment with two concerns:

- `resources` declares the single-host computational policy; and
- `placement` selects direct execution or one outer Slurm allocation.

The built-in profile is the base, the selected file overrides it, and CLI
resource flags override both. `--profile NAME` accepts the safe grammar
`[A-Za-z0-9][A-Za-z0-9._-]*` and resolves exactly
`<project-root>/emrys.execution.NAME.yaml`. It is mutually exclusive with the
retained advanced `--execution-profile PATH` selector. The name is human
selection metadata only: it enters no Project schema, Run/Attempt identity, or
runtime mode. EMRYS does not scan directories, consult a registry, or search
site/global paths. If retired `emrys.resources.yaml` or
`emrys.launcher.yaml` files remain beside the Project definition, omitting both
selectors fails closed and requires deliberate migration.

Use [`execution_profile.example.yaml`](execution_profile.example.yaml) as the
Slurm starter. `account`, `partition`, `qos`, `memory_mb`, and `nodelist` may
be null to use site defaults. `cpus_per_task`, `time`, `exclusive`, and
`scratch_parent` define the one outer allocation. `modules.mode: none` loads
nothing; `modules.mode: exact` requires one absolute initializer and a closed
module roster. Paths and values are literal: environment interpolation,
templates, shell commands, merge keys, and unknown fields are rejected.

Name a Project-local file with `--profile NAME`, or select any admitted file
with `--execution-profile PATH`, on `emrys run` or `emrys resume`; see the
[runbook](../docs/operations/RUNBOOK.md#local-pilot-lifecycle-routes) for the
complete commands. Planning never submits or writes. `--execute`
submits exactly once and prints `JOB_ID`, `OUT`, and `ERR`. Scheduler streams
use `<project-root>/logs`; the application-log root defaults to its
`application/` subdirectory. Execution mode is never inferred from the profile
or environment.

On resume, omitting both selectors preserves direct placement, while omission
or a selected placement-only fragment reuses the predecessor's symbolic
computational resources before applying CLI overrides. A fragment that declares
resources follows built-in → fragment → CLI precedence and must remain
compatible with immutable Run identity. Runtime acquisition and admission remain separate.

## Project definition and analysis

The public definition is the closed `emrys.project.v1` shape. A Project owns
one shared Dataset and Reference plus one or more named Analyses:

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

Each Analysis may add `sample_ids`, a nonempty unique list of IDs from the
shared Dataset. Omission selects every Dataset sample. EMRYS preserves Dataset
manifest order, validates the selected cohort as a complete scientific design,
and gives a proper subset its own content-derived Analysis and Run identities:

```yaml
analyses:
  leave_one_pair_out:
    sample_ids: [EV_2, PUM1_2, EV_3, PUM1_3]
    # partitions, comparison, target change, and thresholds are also required
```

`emrys init project` creates one initial Analysis, named `primary` by default
or selected with `--analysis-name`. Additional Analyses may reuse the Dataset,
Reference, and even the same partition manifest while changing their own
partition selection or scientific policy. `emrys validate project`, runtime
discovery, and Doctor admit and validate every named Analysis. `emrys run` and
Doctor select the Analysis whose execution readiness is being evaluated with
`--analysis NAME`; omission is accepted only when the Project contains exactly
one. The mapping key is a human selector and retained Attempt
metadata, not part of immutable Analysis identity. Analysis identity is
derived from its admitted scientific content.

The FASTA parent must be writable for Step `00c` sidecars. Analysis names and
other safe identifiers begin with an ASCII letter or digit and then contain
only letters, digits, `.`, `_`, or `-`. Unknown fields and request-v3 input are
rejected by active Project commands. Request-v3 is retained privately only so
an exact historical Run can be re-admitted during resume.

Execution resources remain separate. Packaged defaults apply first, one named
or explicit selected fragment may replace them, and owner-defined CLI overrides
have highest precedence. EMRYS records effective values and sources and rejects
policies that exceed the visible allocation.

### Analysis answers

The current profile performs a paired, two-sided, continuity-corrected
Cochran-Mantel-Haenszel (CMH) test across declared replicate strata and applies
one global Benjamini-Hochberg correction. Threshold comparisons are strict.

| Field | Meaning | Call behavior |
| --- | --- | --- |
| Analysis mapping key | Human name used by `emrys run --analysis NAME`. | Selects an Analysis but does not enter its content-derived immutable identity. |
| `partitions` | Partition manifest for this Analysis. | May be shared by multiple Analyses. Raw bytes and row order remain source provenance; identity binds canonical partition semantics and referenced content. |
| `control_condition` | Condition used as control in every paired stratum. | Must differ from treatment and match manifest rows exactly. |
| `treatment_condition` | Condition compared with control. | Must have the same replicate set as control. |
| `target_change` | Target canonical RNA-base change, such as `A>G`. | Both bases are one of `A`, `C`, `G`, or `T` and must differ. Other changes remain in the all-sites table as `not_target_change`. |
| `min_sample_dp` | Minimum depth in every analysis sample. | A target candidate with any analysis-sample DP below this value is not tested. |
| `mean_dp_threshold` | Minimum mean depth across paired analysis samples. | A tested candidate must have mean DP **greater than** this value to advance. |
| `fdr_threshold` | Maximum global BH-adjusted p-value. | A tested candidate must have FDR **less than** this value to advance. |
| `common_or_threshold` | Minimum common odds-ratio magnitude. | Up calls require OR greater than this value; down calls require OR less than its reciprocal. It must be greater than `1`. |
| `absolute_difference_threshold` | Minimum absolute treatment-minus-control mean allele-fraction change. | Up calls require delta greater than this value; down calls require delta less than its negative. |
| `background_condition` | Optional additional condition used only as a background filter. | Use `null` to disable it. If set, at least one matching manifest row is required. Background rows do not form CMH pairs. |
| `background_max_fraction` | Maximum allowed alternate-allele fraction in each usable background sample. | With background enabled, every background AF must be strictly less than this value and meet `min_sample_dp`. |

These values define a computational ranking policy, not a universal RNA-editing
standard. Choose them with the assay designer and preserve the selection as
part of the run. Passing the policy creates a `significant_up` or
`significant_down` computational call; it does not establish a validated
editing site or biological conclusion.

## Sample manifest

`samples.tsv` is a literal tab-separated file. `emrys init manifests` can
generate a portable draft from supplied FASTQ paths and explicit biological
metadata. Keep the exact column order shown below; `notes` may be appended as
the final optional column.

| Column | Meaning | Rules |
| --- | --- | --- |
| `sample_id` | Stable identity for one paired-end library. | Required, unique, safe ID. |
| `r1_fastq` | Read-1 FASTQ path. | Required nonempty regular file; plain FASTQ or `.gz`. |
| `r2_fastq` | Read-2 FASTQ path. | Required, distinct from R1, and uses the same compression mode as R1. |
| `strandedness` | Authored library metadata. | Exactly `forward`, `reverse`, `unstranded`, or `unknown`. RSeQC evidence does not silently rewrite it. |
| `condition` | Experimental condition. | Must exactly match a Project condition when the row participates in control/treatment or background analysis. |
| `replicate` | Pairing-stratum identity. | Required safe ID. It—not row order or sample naming—defines control/treatment pairing. |
| `notes` | Optional free text. | If used, add it as the last column on every row. |

The fixed profile requires at least two paired strata. Every replicate appearing
in either analysis condition must contain exactly one control row and exactly
one treatment row:

```text
replicate   control row       treatment row
pair_01     control_01        treatment_01
pair_02     control_02        treatment_02
```

Do not use technical lanes as independent biological strata unless that is the
declared experimental design. Merge or model lanes according to an approved
upstream policy before authoring this manifest.

EMRYS checks the declared FASTQ files and binds their bytes, but Project
admission does not prove sample provenance or complete record-level pairing.
Confirm checksums from the sequencing provider and use the paired-FASTQ
diagnostic described in the [ingestion owner](../src/emrys/ingestion/sample_manifest_admission/README.md)
when appropriate.

## Partition manifest

`partitions.tsv` limits the genomic regions entering cohort mpileup. It has
exactly three columns:

| Column | Meaning | Rules |
| --- | --- | --- |
| `partition_id` | Stable partition identity. | Required, unique, safe ID. |
| `selector_type` | How bcftools selects the region. | `region` passes the value to `bcftools mpileup -r`; `regions_file` passes an admitted file to `-R`. |
| `selector_value` | Contig/region expression or regions-file path. | For `region`, use the FASTA/FAI contig vocabulary, for example `chr1` or `chr1:1-1000000`. For `regions_file`, use an explicit file path relative to the Project directory or an absolute path. |

Partitions must be nonoverlapping for Step `08`. Start with one small declared
region for installation/runtime verification before scheduling a whole-genome
analysis. A header-only VCF and zero candidates can be a valid outcome when
all declared counts and receipts reconcile.

## Runtime discovery

Run discovery in the environment that will execute EMRYS. It checks the fixed
runtime policy and displays the one profile it would admit without writing:

```sh
emrys runtime discover --project /absolute/project/project.yaml
emrys runtime discover --project /absolute/project/project.yaml --execute
```

`--execute` publishes the only ordinary runtime authority at
`<project-root>/runtime/runtime.tsv`. `run`, `resume`, and Doctor derive that
path; users do not author the TSV or pass it to those commands. Any existing
profile is preserved and rejected, including byte-identical content.
Discovery does not install software or load modules. A missing or ambiguous
site installation fails without silent selection, so load the approved site environment first
and rerun discovery there. For the supported EMRYS-managed alternative, run
`emrys doctor --project /absolute/project/project.yaml --repair` to preview the
exact repair, then confirm it on a terminal or add `--execute` for deliberate
noninteractive mutation. Doctor preserves any site- or user-owned admitted
profile rather than migrating it. Commands come from the active `PATH`. Select the
Picard jar and R library with `EMRYS_PICARD_JAR` and
`EMRYS_RENV_LIBRARY`. `EMRYS_RSCRIPT` can select Rscript directly, and
`JAVA_HOME` must agree with the Java on `PATH`. The advanced
`emrys inspect runtime-availability` route remains available for explicit
evidence collection against a supplied profile.

The accepted tool versions are:

| Runtime | Accepted identity |
| --- | --- |
| Bash | GNU Bash `3.2` or newer |
| Python | `3.11` or newer from this checkout's locked `.venv` |
| Snakemake | `9.25.1` through that Python |
| STAR | `2.7.11b` |
| samtools | `1.19.2` |
| Java | canonical `<JAVA_HOME>/bin/java`, major `17` or newer |
| GATK | `4.6.1.0` |
| Picard | `3.1.1` jar, including the bound `3.1.1-16-g5b0b4c014-SNAPSHOT` build, invoked through the selected Java |
| bcftools | `1.21` |
| RSeQC | `infer_experiment.py 5.0.4` |
| gzip | a compatible `gunzip` command |
| R | `Rscript 4.6.1` |

The exact Step `08` R namespace versions remain in the internal runtime policy.
The discovered R project is the exact clean EMRYS checkout and its library must
pass the guarded `r-check`. Discovery and execution never install, download,
restore, load modules, or repair a missing runtime. Doctor diagnosis is also
read-only; only its explicit managed repair delegates a locked Python sync to
`uv`, the packaged Linux x86-64 native/R lock to Pixi, and R-library restore to
`renv`. It writes only the checkout-owned `.venv`, Project-owned
`runtime/managed`, the create-absent Project runtime profile, and one
maintenance log under Project `logs/application`, then re-runs readiness.

On a module-based cluster, declare the exact initializer and module roster in
the execution profile. EMRYS loads that roster inside the allocation before
runtime admission. Discover the resulting canonical tools in that environment;
a successful head-node probe does not establish compute-node visibility.

## Before requesting `READY`

Check these facts first:

- the Project root and referenced source data are durable and readable on the
  execution host;
- FASTQ R1/R2 files are distinct, use matching compression, and have retained
  provider checksums;
- every control/treatment replicate has exactly one row from each condition,
  with at least two paired strata;
- FASTA, GTF, and partitions describe the same reference/contig vocabulary;
- the reference directory is the intended writable authority for `.fai` and
  `.dict` sidecars;
- the runtime paths resolve in the actual execution environment;
- the checkout is clean, and the Project root is canonical, writable, and
  outside the checkout; and
- storage and memory have been planned for the reference index, several BAM
  generations per sample, orientation BAMs, VCFs, logs, and immutable recovery
  evidence.

The root [researcher quickstart](../README.md) gives the supported validation,
doctor, dry-run, execute, monitor, inspect, and resume sequence. `READY` means
the bounded admission probes passed; it is not a capacity estimate or a
scientific result.

Before doctor, run the tool-free compatibility validator on the execution host:

```sh
emrys validate project --project /absolute/project/project.yaml
```

It streams and binds declared inputs, checks paired strata for every named
Analysis, reconciles FASTA/GTF contigs and bounds, and checks every
region/regions-file selector.
It writes nothing and establishes no runtime or scientific evidence.

## Other configuration assets

The remaining files in this directory serve narrower owners. They are not
alternate local-pilot overlays and should not be mixed into a Project unless
their owner explicitly calls for them.

| Area | Consumer | Tracked inputs |
| --- | --- | --- |
| Narrow sample-manifest admission | [Sample-manifest admission](../src/emrys/ingestion/sample_manifest_admission/README.md) | [`samples.example.tsv`](samples.example.tsv) |
| Artifact and report projection | [Reporting](../src/emrys/reporting/README.md) and [artifact contracts](../src/emrys/contracts/artifacts/README.md) | [`artifact_inventory.example.tsv`](artifact_inventory.example.tsv), [`artifact_run_contract.example.json`](artifact_run_contract.example.json) |
| Reference provenance | [Reference-provenance evidence](../src/emrys/evidence/reference_provenance/README.md) | [`reference_provenance.example.tsv`](reference_provenance.example.tsv) |
| Standalone runtime inspection | [Runtime-availability evidence](../src/emrys/evidence/runtime_availability/README.md) | [`runtime_preflight.example.tsv`](runtime_preflight.example.tsv) |
| Storage and retention | [Storage-inventory evidence](../src/emrys/evidence/storage_inventory/README.md) | [`storage_roots.example.tsv`](storage_roots.example.tsv), [`retention_policy.example.tsv`](retention_policy.example.tsv) |
| Step `07` selections | [Partitioned cohort mpileup](../src/emrys/stages/partitioned_cohort_mpileup/README.md) | [`step_07_partitions.example.tsv`](step_07_partitions.example.tsv), [`step_07_partitions.pilot.tsv`](step_07_partitions.pilot.tsv), [`step_07_partitions.primary_contigs.tsv`](step_07_partitions.primary_contigs.tsv) |
| Historical Step `09` pairing reference | [Paired CMH ranking](../src/emrys/analyses/paired_cmh_candidate_ranking/README.md) | [`step_09_pairs.NORAD_EV_PUM1.tsv`](step_09_pairs.NORAD_EV_PUM1.tsv) |

`NORAD_EV_PUM1` and `NORAD_EV_vs_PUM1` are frozen scientific cohort and
analysis identifiers. They intentionally retain their original spelling and
must not be treated as current project branding or rewritten in retained
artifact paths.

An `.example` filename means structural starter, not production evidence.
Never edit a tracked example to manufacture a passing status, approval,
provenance record, or result. Site-specific copies placed under `configs/` are
trackable by default and may expose paths or sensitive metadata.
