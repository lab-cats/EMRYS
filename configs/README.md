# Configuration and input guide

The five tracked `local_pilot_*` examples are the policy templates behind the
generated matched starter set for the supported automatic workflow. They
describe what to analyze; they do not contain reads, a reference, scientific
software, or a ready-to-run production selection.

Initialize the set in an operator-managed directory **outside the Git
checkout**. Both forms are dry-run-first; the output must be an absolute absent
directory beneath an existing writable real parent:

```sh
norad init local-pilot --output-dir /absolute/absent/norad-inputs
norad init local-pilot \
  --output-dir /absolute/absent/norad-inputs \
  --execute
```

The execute form publishes `request.yaml`, `norad.resources.yaml`,
`samples.tsv`, `partitions.tsv`, `runtime.tsv`, executable `run-in-slurm.sh`,
and then `starter-set.manifest.tsv` last. The manifest proves only the initial
generated starter; expected data/config edits make those original hashes
historical.

Keep the authored request, resource configuration, manifests, selected runtime
profile, and source data together for the life of the run. NORAD binds the
scientific inputs into run identity and snapshots the effective resource policy
for each attempt; changing either is not a way to repair an entered attempt.

## Recommended input layout

This layout makes every data path relative to the request and keeps the
checkout clean:

```text
norad-inputs/
|-- request.yaml
|-- norad.resources.yaml
|-- samples.tsv
|-- partitions.tsv
|-- runtime.tsv
|-- runtime.selected.tsv
|-- run-in-slurm.sh
|-- starter-set.manifest.tsv
`-- inputs/
    |-- reads/
    |   |-- control_01_R1.fastq.gz
    |   |-- control_01_R2.fastq.gz
    |   |-- treatment_01_R1.fastq.gz
    |   `-- treatment_01_R2.fastq.gz
    |-- reference/
    |   |-- genome.fa
    |   `-- annotation.gtf
    `-- regions/
        `-- selected_regions.txt
```

The workspace is a separate, initially absent directory beside this input
directory. Do not put the workspace, large inputs, restored R library, or
results in the checkout.

Authored paths may be absolute or relative to the directory containing the
request. They must be explicit: no `~`, environment variables, templates,
globs, redundant separators, or `.`/`..` components. NORAD does not search for
files or infer which sample, reference, or runtime you intended.

## Request YAML

[`local_pilot_request.example.yaml`](local_pilot_request.example.yaml) is the
complete request shape. YAML keys are closed; unknown or duplicate keys and
merge keys are rejected.

### Run and reference fields

| Field | Meaning | How to choose it |
| --- | --- | --- |
| `schema_version` | Request contract version. | Keep `norad.request.v3`. |
| `label` | Optional human label. It does not affect the run ID. | Use a short description for operators. |
| `profile` | Fixed automatic workflow. | Keep `norad.profile.local_cmh.v2`. There is no public alternate profile. |
| `sample_manifest` | Sample TSV path. | Point to the matched sample manifest, normally beside the request. |
| `partition_manifest` | Genomic partition TSV path. | Point to the matched partition manifest. |
| `reference.id` | Stable reference-build identity. | Use a safe ID such as `grch38_gencode_v47`; do not use a filename as a substitute for provenance. |
| `reference.fasta` | Materialized, nonempty reference FASTA. | Use the same assembly/build as the annotation and partition selectors. The reference directory must be writable because Step `00c` creates or reuses `.fai` and `.dict` sidecars beside it. |
| `reference.gtf` | Materialized, nonempty annotation GTF. | Use an annotation whose contig vocabulary agrees with the FASTA. |
| `reference.star_index.sjdb_overhang` | STAR splice-junction overhang. | Select deliberately for the read design; a common choice is maximum read length minus one. The value is recorded and later validated. |
| `reference.star_index.genome_sa_index_nbases` | STAR suffix-array index parameter. | Select for the reference size according to the admitted STAR release; `14` is appropriate for many mammalian references but is not universal. |
| `cohort_id` | Identity shared by the samples entering cohort processing. | Use a stable safe ID, not an analysis conclusion. |

### Resource configuration

Execution resources are separate from scientific run intent. The optional
[`local_pilot_resources.example.yaml`](local_pilot_resources.example.yaml) is
published by `norad init local-pilot` as `norad.resources.yaml` beside
`request.yaml`. If that adjacent file is absent, NORAD uses its packaged
conservative defaults. An explicitly selected `--resource-config` replaces
adjacent discovery, and individual resource CLI options override the selected
YAML and packaged defaults.

| Field | Meaning |
| --- | --- |
| `workflow_cores` | Total CPU capacity made available to Snakemake. |
| `workflow_memory_mb` | Total global scheduler memory in MiB, or `allocation` to use observed capacity. |
| `stage_concurrency` | Closed per-stage caps for repeatable Steps `01`, `02`, `02b`, `03`, `04`, `05`, `06`, and `07`. |
| `step_threads` | Closed thread mapping for Steps `00a`, `01`, `02`, `06`, and `08`. |
| `stage_memory_mb` | Total memory reserved by one computational owner job, in MiB or `workflow`. |
| `reporting_memory_mb` | Total memory reserved by each reporting transaction, in MiB or `workflow`. |

NORAD rejects a policy when concurrency multiplied by per-job threads exceeds
workflow cores, when concurrency multiplied by per-job memory exceeds workflow
memory, or when workflow totals exceed the process-visible outer allocation.
The effective policy, source digests, explicit override paths, and observed
allocation are stored in the immutable attempt workflow config.

Safe IDs begin with an ASCII letter or digit and then contain only letters,
digits, `.`, `_`, or `-`.

### Analysis fields

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

[`local_pilot_samples.example.tsv`](local_pilot_samples.example.tsv) is a
literal tab-separated file. Keep the exact column order shown below; `notes`
may be appended as the final optional column.

| Column | Meaning | Rules |
| --- | --- | --- |
| `sample_id` | Stable identity for one paired-end library. | Required, unique, safe ID. |
| `r1_fastq` | Read-1 FASTQ path. | Required nonempty regular file; plain FASTQ or `.gz`. |
| `r2_fastq` | Read-2 FASTQ path. | Required, distinct from R1, and uses the same compression mode as R1. |
| `strandedness` | Authored library metadata. | Exactly `forward`, `reverse`, `unstranded`, or `unknown`. RSeQC evidence does not silently rewrite it. |
| `condition` | Experimental condition. | Must exactly match a request condition when the row participates in control/treatment or background analysis. |
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

NORAD checks the declared FASTQ files and binds their bytes, but the request
contract does not prove sample provenance or complete record-level pairing.
Confirm checksums from the sequencing provider and use the paired-FASTQ
diagnostic described in the [ingestion owner](../src/norad/ingestion/sample_manifest_admission/README.md)
when appropriate.

## Partition manifest

[`local_pilot_partitions.example.tsv`](local_pilot_partitions.example.tsv)
limits the genomic regions entering cohort mpileup. It has exactly three
columns:

| Column | Meaning | Rules |
| --- | --- | --- |
| `partition_id` | Stable partition identity. | Required, unique, safe ID. |
| `selector_type` | How bcftools selects the region. | `region` passes the value to `bcftools mpileup -r`; `regions_file` passes an admitted file to `-R`. |
| `selector_value` | Contig/region expression or regions-file path. | For `region`, use the FASTA/FAI contig vocabulary, for example `chr1` or `chr1:1-1000000`. For `regions_file`, use an explicit file path relative to the request directory or an absolute path. |

Partitions must be nonoverlapping for Step `08`. Start with one small declared
region for installation/runtime verification before scheduling a whole-genome
analysis. A header-only VCF and zero candidates can be a valid outcome when
all declared counts and receipts reconcile.

## Runtime profile

[`local_pilot_runtime.example.tsv`](local_pilot_runtime.example.tsv) is a
fixed admission roster, not a shell setup script. It tells NORAD exactly which
already-installed executables, jar, Python environment, R project/library, and
R namespaces to use.

| Column | Meaning |
| --- | --- |
| `check_id` | Fixed identity consumed by the profile. |
| `check_type` | Fixed probe kind: tool version, path visibility, hash utility, or R namespace. |
| `runtime_context` | Fixed execution context; currently `local`. |
| `required` | Fixed policy; every row is required. |
| `target` | The only generally editable field: replace a path placeholder with the selected executable, jar, directory, or R package name already specified by policy. |
| `probe_args` | JSON array of probe arguments. Change only path values explicitly coupled to a replaced target, such as the Picard jar or Rscript path. |
| `expected` | Fixed accepted version/readability expression. |
| `description` | Fixed human description. |

Do not delete, reorder, or weaken rows to make doctor pass. The roster,
versions, check types, contexts, required flags, ordinary probes, descriptions,
and R package names are policy. File-backed tools are bound by authored path,
canonical target, observed version, and SHA-256. Module names and the login
node's `PATH` are not identities.

Prefer the read-only preparation helper over manually editing 24 coupled rows.
It renders the complete fixed TSV to stdout; redirect it only to a new absent
file:

```sh
test ! -e /absolute/norad-inputs/runtime.selected.tsv && (
  set -C
  norad prepare local-pilot-runtime \
    --bash /canonical/path/to/bash \
    --star /canonical/path/to/STAR \
    --samtools /canonical/path/to/samtools \
    --gatk /canonical/path/to/gatk \
    --bcftools /canonical/path/to/bcftools \
    --infer-experiment /canonical/path/to/infer_experiment.py \
    --gunzip /canonical/path/to/gunzip \
    --java /canonical/java-home/bin/java \
    --picard-jar /canonical/path/to/picard.jar \
    --rscript /canonical/path/to/Rscript \
    --renv-library /canonical/path/to/renv-library \
    > /absolute/norad-inputs/runtime.selected.tsv
)
```

Java, Picard jar, Rscript, and the `renv` library are always explicit.
`--bash`, `--star`, `--samtools`, `--gatk`, `--bcftools`,
`--infer-experiment`, and `--gunzip` may be omitted only if `PATH` exposes one
distinct executable for the corresponding command. The helper checks safe
canonical path structure but performs no version/namespace probe and writes no
file itself. Doctor remains the runtime admission authority.

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

The exact Step `08` R namespace versions remain in the starter. The
`renv_project` target must be the exact clean NORAD checkout; `renv_library`
must be an existing canonical library that passed the guarded `r-check` for
that checkout. Doctor and execution never install, download, restore, load
modules, or repair a missing runtime.

On a module-based cluster, module loading belongs in the batch environment
that will run NORAD. Load the selected modules there, resolve their canonical
commands (for example with `readlink -f "$(command -v STAR)"` where supported),
and author those absolute targets in the profile. Repeat admission inside the
same batch allocation; a successful head-node probe does not establish
compute-node visibility.

## Before requesting `READY`

Check these facts first:

- the request directory and source data are durable and readable on the
  execution host;
- FASTQ R1/R2 files are distinct, use matching compression, and have retained
  provider checksums;
- every control/treatment replicate has exactly one row from each condition,
  with at least two paired strata;
- FASTA, GTF, and partitions describe the same reference/contig vocabulary;
- the reference directory is the intended writable authority for `.fai` and
  `.dict` sidecars;
- the runtime paths resolve in the actual execution environment;
- the checkout is clean, and the external workspace leaf is absent beneath an
  existing writable real directory; and
- storage and memory have been planned for the reference index, several BAM
  generations per sample, orientation BAMs, VCFs, logs, and immutable recovery
  evidence.

The root [researcher quickstart](../README.md) gives the supported validation,
doctor, dry-run, execute, monitor, inspect, and resume sequence. `READY` means
the bounded admission probes passed; it is not a capacity estimate or a
scientific result.

Before doctor, run the tool-free compatibility validator on the execution host:

```sh
norad validate local-pilot-request --request /absolute/norad-inputs/request.yaml
```

It streams and binds declared inputs, checks paired strata, reconciles
FASTA/GTF contigs and bounds, and checks every region/regions-file selector.
It writes nothing and establishes no runtime or scientific evidence.

## Other configuration assets

The remaining files in this directory serve narrower owners. They are not
alternate local-pilot overlays and should not be mixed into a request unless
their owner explicitly calls for them.

| Area | Consumer | Tracked inputs |
| --- | --- | --- |
| Narrow sample-manifest admission | [Sample-manifest admission](../src/norad/ingestion/sample_manifest_admission/README.md) | [`samples.example.tsv`](samples.example.tsv) |
| Artifact and report projection | [Reporting](../src/norad/reporting/README.md) and [artifact contracts](../src/norad/contracts/artifacts/README.md) | [`artifact_inventory.example.tsv`](artifact_inventory.example.tsv), [`artifact_run_contract.example.json`](artifact_run_contract.example.json) |
| Reference provenance | [Reference-provenance evidence](../src/norad/evidence/reference_provenance/README.md) | [`reference_provenance.example.tsv`](reference_provenance.example.tsv) |
| Standalone runtime inspection | [Runtime-availability evidence](../src/norad/evidence/runtime_availability/README.md) | [`runtime_preflight.example.tsv`](runtime_preflight.example.tsv) |
| Storage and retention | [Storage-inventory evidence](../src/norad/evidence/storage_inventory/README.md) | [`storage_roots.example.tsv`](storage_roots.example.tsv), [`retention_policy.example.tsv`](retention_policy.example.tsv) |
| Step `07` selections | [Partitioned cohort mpileup](../src/norad/stages/partitioned_cohort_mpileup/README.md) | [`step_07_partitions.example.tsv`](step_07_partitions.example.tsv), [`step_07_partitions.pilot.tsv`](step_07_partitions.pilot.tsv), [`step_07_partitions.primary_contigs.tsv`](step_07_partitions.primary_contigs.tsv) |
| Historical Step `09` pairing reference | [Paired CMH ranking](../src/norad/analyses/paired_cmh_candidate_ranking/README.md) | [`step_09_pairs.NORAD_EV_PUM1.tsv`](step_09_pairs.NORAD_EV_PUM1.tsv) |

An `.example` filename means structural starter, not production evidence.
Never edit a tracked example to manufacture a passing status, approval,
provenance record, or result. Site-specific copies placed under `configs/` are
trackable by default and may expose paths or sensitive metadata.
