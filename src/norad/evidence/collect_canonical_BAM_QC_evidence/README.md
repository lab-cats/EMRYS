# `collect_canonical_BAM_QC_evidence` owner

This directory is the implemented native owner for semantic evidence operation
`collect_canonical_BAM_QC_evidence`
(`norad.evidence.collect_canonical_BAM_QC_evidence.v1`, historical alias
`02b`). Its public assets are:

- [`step_02b_bam_qc.sh`](step_02b_bam_qc.sh), the mode-`0755` producer;
- [`validate_step_02b_bam_qc.py`](validate_step_02b_bam_qc.py), the
  mode-`0644` explicit-interpreter validator;
- [`step_02b_bam_qc.slurm`](step_02b_bam_qc.slurm), the intentionally
  mode-`0644` scheduler entry point; and
- the mirrored [producer](../../../../tests/evidence/collect_canonical_BAM_QC_evidence/test_step_02b_bam_qc.sh)
  and [validator](../../../../tests/evidence/collect_canonical_BAM_QC_evidence/test_validate_step_02b_bam_qc.py)
  tests. Scheduler behavior remains independently owned by the central
  [wrapper-contract suite](../../../../tests/test_slurm_wrapper_contracts.py).

## Producer

The producer requires a BAM plus either adjacent `<bam>.bai` or stem `.bai`
and resolves `samtools` only from `PATH`. From the repository root, direct and
explicit-Bash dry runs are supported:

```bash
src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh \
  --sample-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --output-dir results/qc/bam

bash src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh \
  --sample-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --output-dir results/qc/bam
```

Dry-run invokes no samtools command but does create the requested output
directory. After inspecting the printed commands, add `--execute`:

```bash
src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh \
  --sample-id ABE_EV_2 \
  --bam results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --output-dir results/qc/bam \
  --execute
```

From another working directory, make the producer, BAM, and output directory
paths absolute. The selected process still supplies samtools through `PATH`:

```bash
/absolute/path/to/norad/src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh \
  --sample-id ABE_EV_2 \
  --bam /absolute/results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
  --output-dir /absolute/results/qc/bam
```

The producer writes quickcheck and flagstat streams directly to final paths.
It has no lock, stage, backup, receipt, stable-input recheck, rollback, or
complete-set validation. A quickcheck child exit `42` becomes producer exit
`1`, replaces an existing quickcheck file with the combined child diagnostic,
and leaves an older flagstat sibling untouched. A flagstat exit `43` follows a
new exact quickcheck PASS marker, replaces an older flagstat with partial child
stdout, and exposes the child diagnostic on stderr. These mixed-attempt states
are characterized defects, not approved recovery or publication behavior.

## Validator

Invoke the mode-`0644` validator through an explicit interpreter. Omitting
`--execute` is the no-write dry run:

```bash
.venv/bin/python src/norad/evidence/collect_canonical_BAM_QC_evidence/validate_step_02b_bam_qc.py \
  --scope-id ABE_EV_2 \
  --quickcheck results/qc/bam/ABE_EV_2.quickcheck.txt \
  --flagstat results/qc/bam/ABE_EV_2.flagstat.txt \
  --output results/qc/validation/02b/ABE_EV_2.validation.tsv
```

After inspecting the five printed rows, create the output parent and add
`--execute`. Repeating the same command deterministically replaces the owned
report after both inputs are rechecked:

```bash
mkdir -p results/qc/validation/02b
.venv/bin/python src/norad/evidence/collect_canonical_BAM_QC_evidence/validate_step_02b_bam_qc.py \
  --scope-id ABE_EV_2 \
  --quickcheck results/qc/bam/ABE_EV_2.quickcheck.txt \
  --flagstat results/qc/bam/ABE_EV_2.flagstat.txt \
  --output results/qc/validation/02b/ABE_EV_2.validation.tsv \
  --execute
```

From another CWD, use absolute interpreter, validator, input, and output
paths. Dry-run, execute, and repeat leave no invocation-directory residue.
The validator privately exact-loads neutral
[`validation_report.py`](../../libraries/validation_report.py); no package
identity, `PYTHONPATH` change, wrapper, or compatibility import is supported.

Producer exit `0` does not imply a passing validation row. In particular, a
nonempty stream from a zero-exit quickcheck is successful producer output but
fails the validator's exact-marker check. Validator exit `0` means the report
was validly rendered and published; it can contain `status=fail` evidence
rows. Step `02b` remains a non-gating evidence branch.

## Scheduler entry point

Submit the exact final job from the checkout. Slurm must provide
`SLURM_SUBMIT_DIR`; the wrapper changes to it before resolving its relative
inputs and child path. Bind the sample, BAM, output directory, and execution
mode explicitly:

```bash
cd /absolute/path/to/norad
SAMPLE_ID=ABE_EV_2 \
BAM=/absolute/results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
OUTPUT_DIR=/absolute/results/qc/bam \
EXECUTE=0 \
  sbatch src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.slurm

SAMPLE_ID=ABE_EV_2 \
BAM=/absolute/results/bam/ABE_EV_2/ABE_EV_2.sorted.bam \
OUTPUT_DIR=/absolute/results/qc/bam \
EXECUTE=1 \
  sbatch src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.slurm
```

The wrapper forces `TMPDIR=/tmp`, creates `logs/` and the output directory,
strictly loads samtools `1.19.2`, and tolerates diagnostics only from
`module list`. Bash `3.2` can fail while expanding the empty dry-run argument
array before producer delegation. After execute, the wrapper checks only that
both named files exist. An exit-`0` child that emitted nothing can therefore
rediscover stale predecessors and let the job succeed. Local mocked coverage
does not prove real submission, module, scheduler, or cluster behavior.

## Diagnostics, recovery, and evidence

For any producer or wrapper fault, preserve both evidence files, unrelated
files in the directory, producer stdout/stderr, scheduler stdout/stderr, and
job/accounting identity before deciding whether a file belongs to the current
attempt. There may be no lock, stage, backup, receipt, or recovery marker to
inspect. Do not delete, adopt, or retry the same names merely because one file
looks current or the scheduler returned zero. Follow the
[Step `02b` troubleshooting route](../../../../docs/operations/TROUBLESHOOTING.md#step-02b-producer-or-wrapper-leaves-a-partial-mixed-or-stale-evidence-pair).

Focused local protection is:

```bash
bash tests/evidence/collect_canonical_BAM_QC_evidence/test_step_02b_bam_qc.sh
.venv/bin/python -m pytest -q \
  tests/evidence/collect_canonical_BAM_QC_evidence/test_validate_step_02b_bam_qc.py
.venv/bin/python -m pytest -q \
  tests/test_slurm_wrapper_contracts.py -k step_02b_bam_qc
```

Published baseline checkpoint `0904faf` froze PATH absence, mixed-attempt
faults, validator mismatch/mutation behavior, arbitrary-CWD repeatability, and
stale scheduler false success. Executable checkpoint `2f186dd` moved exactly
five files and updated nine callers/harnesses. Final producer mode/bytes/lines/
SHA-256 is `0755` / `4,062` / `163` /
`92895b2dbd1117e72703e8261a66ce1a7cc34db6000280e23753cd5f9132101c`;
validator is `0644` / `6,934` / `186` /
`fa25aeba0e6bd2e9fd0fc90229590cced4e6f44bb7b83310215500b9fb51fe96`;
and the intentionally mode-`0644` job is `2,139` bytes / `87` lines /
`119e0cc7f8937a03c7e766c60aede204ae743ee735300eceda126333fe51a77c`.

Serial coverage passed `1,113` tests with `17` skips and one explicit
documentation-validator deselection. The moved validator measured `103/110`
lines and `24/30` branches; global coverage was `9505/11677` lines and
`3328/4756` branches, with every non-target row exact and the standalone
policy comparison passing.

The aggregate gate was not fully green. Its network-enabled run passed static,
shell, guarded-R, and report-runtime lanes. Python reported `1,113` passes and
`17` skips before its sole documentation assertion listed ten intentionally
deferred migration links plus nine inherited `UNREFINED` card-location
findings. This close repairs the ten links; the inherited nine remain
nonpassing. No result is represented as a green aggregate gate.

Artifact evidence records the final producer path and SHA-256 above without
changing artifact identities, schemas, contents, ordering, or consumers.
Rollback reverts the documentation close, executable checkpoint `2f186dd`,
then test baseline `0904faf`; it never deletes runtime artifacts or restores a
legacy duplicate. See [`CONTRACT.md`](CONTRACT.md) and the completed
[`MIG-03G`](../../../../docs/tasks/COMPLETED/MIG-03G-migrate-collect-canonical-bam-qc-evidence-owner.md)
record for complete boundaries.

The migration added no wrapper, alias, symlink, package marker, public import
identity, descriptor, schema, transaction, receipt, recovery marker, or
scheduler abstraction. Its evidence is local fixture/mock, guarded local-R,
pinned report-runtime, and local coverage evidence only—not new real samtools,
scheduler, cluster, production, scientific-review, or biological proof.
