# `generate_partitioned_cohort_mpileup_VCFs` owner

Native owner of `emrys.stage.generate_partitioned_cohort_mpileup_VCFs.v1`
(historical `07`). [`CONTRACT.md`](CONTRACT.md) owns exact selector, output,
transaction, retained-defect, and evidence semantics. The lowercase directory
is the physical owner; the semantic identity, artifact names, and historical
alias do not change with that layout.

## Entry points

- producer: private [`producer.py`](producer.py), invoked as
  `python -I -m emrys.stages.partitioned_cohort_mpileup.producer`
- validator: grouped route
  `python -I -m emrys validate partitioned-cohort-mpileup`, implemented by
  private [`validator.py`](validator.py)

For Slurm execution, use the complete immutable Run through `emrys run` or
`emrys resume` as documented in the
[runbook](../../../../docs/operations/RUNBOOK.md#local-pilot-lifecycle-routes).

## Operate

Dataset, root, partition, and tool bindings are explicit. Dry-run is no-write:

```bash
: "${EMRYS_BCFTOOLS_BIN:?export the admitted bcftools executable path}"
output_root="$(pwd)/results/mpileup"
.venv/bin/python -X pycache_prefix=/dev/null -I \
  -m emrys.stages.partitioned_cohort_mpileup.producer \
  --cohort-id NORAD_EV_PUM1 \
  --sample-manifest data/raw/samples.paired.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --partition-id 1 \
  --orientation-root results/orientation \
  --reference-fasta refs/novogene_ref/genome.fa \
  --output-root "$output_root" \
  --bcftools-bin "$EMRYS_BCFTOOLS_BIN"
```

Add `--execute` after inspecting sample order, partition selector, BAM/BAI and
FASTA/FAI inputs, tool, depth, filter, lock, scratch, and rollback paths. The
producer runs mpileup and filter, not `bcftools call`; `FWD_like`/`REV_like` are
mechanical labels and outputs are not validated variants or editing sites.
The orchestration-safe invocation also supplies `--no-clobber`, which rejects a complete
prior set without running bcftools; direct use retains complete-set
replacement unless that option is supplied. On a new output set, this mode
hashes the exact manifests, reference FASTA/FAI pair, optional regions file,
and every admitted orientation BAM/BAI before bcftools, then rechecks their
membership and bytes before receipt construction and publication.

Do not tune `--max-depth` from the bcftools warning alone. First retain a
representative-partition benchmark with elapsed/CPU time, peak RSS, block I/O,
validator success, and byte hashes. The existing
`scripts/benchmark_stage_resources.py` records those measures; Slurm
`sacct` may supplement them. Keep benchmark manifests/results outside the
repository and leave the default unchanged until site evidence supports a cut.

Execute requires all three predecessors or none, publishes and revalidates the
FWD and REV VCFs, then publishes the two-row receipt. Only manifests are
durably hash-bound in that receipt; the additional `--no-clobber` hashes are
in-attempt guards and are not receipt provenance. Receipt visibility is not
current-attempt proof. An incomplete rollback retains the owned lock and backups
for operator recovery.

The producer prints the exact post-execution validator command using its bound
paths, followed by the exact `emrys validate all-pass` command. Run both after
the owner succeeds. The validator may exit `0` while publishing `fail` rows;
`all-pass` is the semantic gate. The five checks do not prove coordinate
bounds, VCF semantics, filter compliance, tool or input identity, biological
meaning, or publication attempt.

Do not execute private `validator.py` directly, add `PYTHONPATH`, or restore the
retired validator path to bypass package selection.

## Promote, diagnose, and verify

Primary promotion additionally requires the admitted sample manifest to match
the approved pair reference and exactly 25 declared receipts plus 50 VCFs.
Counts supplement per-partition validation; they never prove semantics alone.

Preserve all finals, temp/backups, lock, manifests, BAM/BAI, FASTA/FAI,
regions, streams, job identity, environment, and tool/depth/filter identity.
Never combine attempts, trust receipt presence or counts, or delete a foreign
lock. Use a fresh root for an authorized diagnostic retry.

```bash
.venv/bin/python -m pytest -q \
  tests/stages/partitioned_cohort_mpileup/test_partitioned_cohort_mpileup_producer.py
.venv/bin/python -m pytest -q \
  tests/stages/partitioned_cohort_mpileup/test_validate_step_07_mpileup_outputs.py
```

This is local fixture/fake-tool evidence only.
