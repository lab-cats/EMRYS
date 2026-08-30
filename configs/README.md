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

Setup records the admitted absolute sample and partition manifest paths in
`project.yaml`; manifests and FASTQ, FASTA, GTF, and regions-file data all
remain in place. `emrys init manifests` produces the required portable form
without inventing biological assignments. No execution or runtime profile is
generated or selected. Without `--execution-profile`, execution remains direct
with the built-in resource policy. Runtime discovery separately admits the
Project-owned `runtime/runtime.tsv`.

Keep the Project and every referenced input for the life of its Runs. Changing
scientific inputs or computational policy is not a way to repair an entered
Attempt. Authored paths are literal: no `~`, environment interpolation,
templates, globs, redundant separators, or `.`/`..` components.

## Execution profile

EMRYS has one optional public execution configuration. With no
`--execution-profile`, the built-in profile uses conservative resources and
direct placement. An explicit profile is a closed YAML fragment with two
concerns:

- `resources` declares the single-host computational policy; and
- `placement` selects direct execution or one outer Slurm allocation.

The built-in profile is the base, the explicitly selected file overrides it,
and CLI resource flags override both. EMRYS does not discover adjacent
configuration. If retired `emrys.resources.yaml` or `emrys.launcher.yaml`
files remain beside the Project definition, omitting `--execution-profile` fails closed
and requires deliberate migration.

Use [`execution_profile.example.yaml`](execution_profile.example.yaml) as the
Slurm starter. `account`, `partition`, `qos`, `memory_mb`, and `nodelist` may
be null to use site defaults. `cpus_per_task`, `time`, `exclusive`, and
`scratch_parent` define the one outer allocation. `modules.mode: none` loads
nothing; `modules.mode: exact` requires one absolute initializer and a closed
module roster. Paths and values are literal: environment interpolation,
templates, shell commands, merge keys, and unknown fields are rejected.

Select the file only with `--execution-profile FILE` on the `emrys run` or
`emrys resume` command; see the [runbook](../docs/operations/RUNBOOK.md#local-pilot-lifecycle-routes)
for the complete command. Planning never submits or writes. `--execute`
submits exactly once and prints `JOB_ID`, `OUT`, and `ERR`. Scheduler streams
use `<project-root>/logs`; the application-log root defaults to its
`application/` subdirectory. Execution mode is never inferred from the profile
or environment.

## Project definition and analysis

Setup generates closed request-v3 `project.yaml` adapter bytes; scientists do
not assemble that internal shape. Its prompts collect stable Project,
reference, cohort, and analysis IDs, the existing manifests and reference,
STAR index parameters, paired conditions, target RNA change, and analysis
thresholds. The FASTA parent must be writable for Step `00c` sidecars. Safe IDs
begin with an ASCII letter or digit and then contain only letters, digits,
`.`, `_`, or `-`.

Execution resources remain separate. Packaged defaults apply first, an
explicit `--execution-profile` may replace them, and owner-defined CLI
overrides have highest precedence. EMRYS records effective values and sources
and rejects policies that exceed the visible allocation.

### Analysis answers

The current profile performs a paired, two-sided, continuity-corrected
Cochran-Mantel-Haenszel (CMH) test across declared replicate strata and applies
one global Benjamini-Hochberg correction. Threshold comparisons are strict.

| Field | Meaning | Call behavior |
| --- | --- | --- |
| `analysis.id` | Stable identity for this policy and result set. | Becomes the Step `09` output directory and filename prefix. |
| `control_condition` | Condition used as control in every paired stratum. | Must differ from treatment and match manifest rows exactly. |
| `treatment_condition` | Condition compared with control. | Must have the same replicate set as control. |
| `rna_ref`, `rna_alt` | Target canonical RNA-base change. | Each is one of `A`, `C`, `G`, or `T`, and they must differ. Other changes remain in the all-sites table as `not_target_change`. |
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

EMRYS checks the declared FASTQ files and binds their bytes, but the temporary
Project adapter contract does not prove sample provenance or complete record-level pairing.
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
installation fails without silent selection, so load the approved site environment first
and rerun discovery there. Commands come from the active `PATH`. Select the
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
pass the guarded `r-check`. Discovery, Doctor, and execution never install,
download, restore, load modules, or repair a missing runtime.

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

It streams and binds declared inputs, checks paired strata, reconciles
FASTA/GTF contigs and bounds, and checks every region/regions-file selector.
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
