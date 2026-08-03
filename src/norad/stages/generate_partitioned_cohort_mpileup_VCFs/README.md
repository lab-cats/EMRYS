# `generate_partitioned_cohort_mpileup_VCFs` owner

This directory is the implemented native owner for semantic stage
`generate_partitioned_cohort_mpileup_VCFs`
(`norad.stage.generate_partitioned_cohort_mpileup_VCFs.v1`, historical alias
`07`). Its public assets are:

- [`step_07_bcftools_mpileup_by_chrom_and_strand.sh`](step_07_bcftools_mpileup_by_chrom_and_strand.sh),
  the mode-`0755` directly executable Bash producer;
- [`validate_step_07_mpileup_outputs.py`](validate_step_07_mpileup_outputs.py),
  the mode-`0644` explicit-interpreter validator;
- [`step_07_bcftools_mpileup_by_chrom_and_strand.slurm`](step_07_bcftools_mpileup_by_chrom_and_strand.slurm),
  the mode-`0644` scheduler entry point; and
- the mirrored [producer](../../../../tests/stages/generate_partitioned_cohort_mpileup_VCFs/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh)
  and [validator](../../../../tests/stages/generate_partitioned_cohort_mpileup_VCFs/test_validate_step_07_mpileup_outputs.py)
  tests. Scheduler behavior remains independently owned by the central
  [wrapper-contract suite](../../../../tests/test_slurm_wrapper_contracts.py).

No installed command, package import, compatibility wrapper, legacy path,
symlink, ambient `PYTHONPATH`, or global `sys.path` mutation is supported.

## Producer and scientific meaning

The producer reads the canonical sample order, selects exactly one declared
partition, and requires both Step `06` mechanical-orientation BAM/BAI pairs for
every sample plus a reference FASTA/FAI. It runs separate `FWD_like` and
`REV_like` `bcftools mpileup` pipelines followed by `bcftools filter`. It does
not run `bcftools call`. The mechanical labels do not establish transcript
strand, library strandedness, sense, or antisense, and the outputs do not by
themselves establish variants, RNA-editing sites, scientific readiness, or
biological readiness.

From the repository root, choose an absolute output root so receipt VCF paths
agree with validator-resolved paths. This complete pilot command is a no-write
dry run unless `--execute` is added:

```bash
output_root="$(pwd)/results/mpileup"
src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/step_07_bcftools_mpileup_by_chrom_and_strand.sh \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.pilot.tsv \
  --partition-id pilot_1 \
  --orientation-root results/orientation \
  --reference-fasta refs/novogene_ref/genome.fa \
  --output-root "$output_root" \
  --bcftools-bin /absolute/path/to/bcftools
```

Producer dry-run validates both manifests and their hashes, the unique
partition selector against the FAI, a relative regions file from the partition
manifest directory, every BAM/BAI, positive maximum depth, nonempty filter,
and bcftools resolution. It prints both exact pipelines plus output, lock,
temporary, validation, publication, and rollback paths; it invokes no
bcftools child and creates no directory or file. Inspect those choices before
repeating the command with `--execute`.

The tracked partition choices remain shared operator inputs rather than owner
implementation:

- [`step_07_partitions.pilot.tsv`](../../../../configs/step_07_partitions.pilot.tsv)
  selects only `pilot_1`;
- [`step_07_partitions.primary_contigs.tsv`](../../../../configs/step_07_partitions.primary_contigs.tsv)
  declares the primary 25-partition universe; and
- [`step_07_partitions.example.tsv`](../../../../configs/step_07_partitions.example.tsv)
  demonstrates both `region` and `regions_file` selectors.

`region` is passed with `-r`; `regions_file` is passed with `-R` and resolves
relative to the partition manifest. Defaults are maximum depth `10000000` and
filter `INFO/AD[1-]>2 & MAX(FORMAT/DP)>20`. Bcftools resolves from the explicit
argument, then `BCFTOOLS_BIN_OVERRIDE`, then `PATH`; a value containing `/`
must exist and be executable.

From another working directory, make the producer, both manifests, orientation
root, FASTA/FAI, output root, regions file when applicable, and bcftools paths
absolute:

```bash
/absolute/path/to/norad/src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/step_07_bcftools_mpileup_by_chrom_and_strand.sh \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest /absolute/path/to/samples.tsv \
  --partition-manifest /absolute/path/to/norad/configs/step_07_partitions.pilot.tsv \
  --partition-id pilot_1 \
  --orientation-root /absolute/results/orientation \
  --reference-fasta /absolute/refs/novogene_ref/genome.fa \
  --output-root /absolute/results/mpileup \
  --bcftools-bin /absolute/path/to/bcftools
```

Execute mode owns one cohort/partition lock and run-token scratch/backups. It
requires all three predecessor finals or none, validates temporary VCF sample
order and record counts, publishes FWD VCF, REV VCF, then the two-row receipt,
and revalidates final paths. Receipt visibility precedes post-publication
validation and the in-memory committed flag. Only the manifests are hash-bound
and snapshot-rechecked. BAM/BAI, FASTA/FAI, regions file, tool, depth, filter,
and VCF bytes are not; receipt presence is not immutable-input or current-
attempt proof.

## Validator

The validator reads exactly six explicit input files, invokes no bcftools, and
prints five TSV rows plus its completion line without writing in dry-run mode:

```bash
cohort=NORAD_EV_PUM1
partition=pilot_1
partition_dir="$(pwd)/results/mpileup/$cohort/$partition"
.venv/bin/python \
  src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/validate_step_07_mpileup_outputs.py \
  --cohort-id "$cohort" \
  --partition-id "$partition" \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.pilot.tsv \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --fwd-vcf "$partition_dir/$cohort.$partition.FWD_like.mpileup.vcf" \
  --rev-vcf "$partition_dir/$cohort.$partition.REV_like.mpileup.vcf" \
  --receipt "$partition_dir/$cohort.$partition.step07_outputs.tsv" \
  --output "results/qc/validation/07/${cohort}__${partition}.validation.tsv"
```

Create the report parent and add `--execute` only after inspecting the five
rows. Repeating unchanged inputs deterministically replaces a valid owned
report after stable-input revalidation. From another CWD, make the interpreter,
validator, six inputs, and output path absolute; dry-run, execute, and repeat
leave no invocation-CWD residue.

The checks are `receipt_structure`, `vcf_structure`,
`selector_reconciliation`, `manifest_identity_and_sample_order`, and
`vcf_record_counts`. Exit `0` means all rows were rendered or published; one
or more may still have `status=fail`. The validator does not prove selector-
bounded VCF coordinates, REF/ALT or FORMAT semantics, filter compliance,
bcftools or input identity, VCF hashes, biological meaning, or attempt
identity. Producer-valid compressed regions currently publish failed selector
evidence, while some out-of-bounds BED/VCF and unchecked VCF semantics can
pass. Relative receipt VCF paths can disagree with resolved validator paths.

The validator privately exact-loads neutral
[`validation_report.py`](../../libraries/validation_report.py) under a private
identity. It adds no package identity, public helper API, wrapper, or ambient
path behavior.

## Scheduler

SLURM opens declared log paths before the job body. Start in the checkout,
create `logs/`, and submit the final nonexecutable-mode job through `sbatch`:

```bash
cd /absolute/path/to/norad
mkdir -p logs
sbatch --export=ALL,TMPDIR=/tmp,EXECUTE=0,PARTITION_MANIFEST=configs/step_07_partitions.pilot.tsv,PARTITION_ID=pilot_1 \
  src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm
```

Change only `EXECUTE=1` after accepting dry-run evidence. Scheduler dry-run is
not side-effect-free: it changes to `SLURM_SUBMIT_DIR` with current-CWD
fallback, creates `logs/`, tolerates module diagnostics, probes an executable
bcftools version when applicable, and delegates producer dry-run. The wrapper
requests one CPU, exports `/tmp`, forwards manifest/selector/depth/filter/tool
choices, and checks three nonempty outputs only in execute mode.

Missing or nonexecutable bcftools is warning-only at the wrapper and remains a
producer rejection. A PATH basename is forwarded without a wrapper version
probe. Version-command and child failures propagate. A zero-exit child can be
falsely accepted when three stale nonempty finals already exist. Scheduler
success is not current-attempt, producer-validation, independent-validation,
cluster, or scientific proof.

## Recovery, evidence, and rollback

Before cleanup, same-name retry, or recovery, preserve all three finals;
run-token temporary/backups; lock and owner; both manifests; every BAM/BAI;
FASTA/FAI and regions file; unrelated bytes; producer stdout/stderr; scheduler
stdout/stderr, job ID/accounting and logs; checkout and submit CWD; environment
overrides; and exact bcftools path/version, depth, and filter. Record missing
expected paths too. Absence does not establish clean or single-attempt state.

A controlled receipt-publication exit `67` followed by prior-FWD restoration
exit `68` propagates `67`, leaves the prior FWD final absent while its backup
survives, restores prior REV and receipt bytes, removes owned temps/lock, and
creates no recovery marker. This is ambiguous manual recovery, not successful
rollback. Never combine attempts, reconstruct a member, delete a foreign lock,
trust receipt presence/counts/timestamps, or adopt stale wrapper success. Rule
out every active producer and Step `08` reader. Any separately authorized
diagnostic retry uses an isolated output root and remains nonproduction.

Follow the dedicated
[`Step 07` recovery route](../../../../docs/operations/TROUBLESHOOTING.md#step-07-producer-or-wrapper-leaves-a-partial-rollback-failure-or-stale-transaction)
before action. Git rollback changes tracked files only; it cannot authenticate,
recover, delete, or alter runtime outputs, locks, backups, or scheduler logs.

Focused local protection is:

```bash
bash tests/stages/generate_partitioned_cohort_mpileup_VCFs/test_step_07_bcftools_mpileup_by_chrom_and_strand.sh
.venv/bin/python -m pytest -q \
  tests/stages/generate_partitioned_cohort_mpileup_VCFs/test_validate_step_07_mpileup_outputs.py
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_07_bcftools_mpileup
```

Published pipeline/selector, transaction/recovery, stability/provenance,
validator, and scheduler baselines are `c813ea3`, `ed58fd3`, `82d7049`,
`65277f7`, and `523144e`. Executable checkpoint `60eb356` moved exactly five
files and updated nine reviewed integration owners. Final producer mode/bytes/
lines/SHA-256 is `0755` / `31,526` / `893` /
`e3af9900b6f7831f2feafbc6d13f3755a475f02e5013c8b756107ddd90d22297`;
validator is `0644` / `13,524` / `334` /
`3191a379a4c2e1d589eeb3f327314d91dcb70f5e79da6e2b4f344ffb2b68763b`;
and the mode-`0644` job is `4,421` bytes / `133` lines /
`fbd8144a362cdd688ac14efcd8c003a3527b878d90ab525277a92018ac9a1ed6`.

The direct shell suite passed, as did `35` moved-validator/scheduler tests with
`142` unrelated scheduler cases deselected and `28` focused integration tests.
The complete shell-contract lane and pinned report-runtime lane passed; the
isolated guarded Step `08` and Step `09` real-R semantic suites passed. Python
ran `1,199` passes and `17` skips before its sole documentation assertion
listed ten intentionally deferred MIG-03L links plus nine inherited
`UNREFINED` locations. Step `07` measured `177/198` lines and `51/72` branches;
the tracked global floors are `9561/11720` lines and `3351/4772` branches with
every non-target baseline row exact, and the standalone policy comparison
passed.

The aggregate gate was not green. Static preflight passed; guarded `r-check`
stopped on an inherited malformed ignored `macos` library entry and unavailable
Bioconductor DNS before the orchestrator could complete the other lanes. No
dependency changed. The separately run shell, report, and guarded real-R
semantic lanes passed. This is local fixture/fake-tool and local-runtime
evidence only: no real bcftools workflow, scheduler, cluster, production,
scientific-review, variant/editing-site, or biological evidence was created.

Artifact provenance changes only Step `07`'s implementation path and reviewed
hash in [`build_artifact_index.py`](../../../../scripts/build_artifact_index.py).
Public artifact identities, schemas, ordering, reconciliation, consumers, and
scientific meaning are unchanged.

Rollback reverts this documentation close, executable `60eb356`, scheduler
`523144e`, validator `65277f7`, stability/provenance `82d7049`, transaction/
recovery `ed58fd3`, then pipeline/selector `c813ea3`. See
[`CONTRACT.md`](CONTRACT.md) and completed
[`MIG-03L`](../../../../docs/tasks/COMPLETED/MIG-03L-migrate-generate-partitioned-cohort-mpileup-vcfs-owner.md)
for the complete boundary.
