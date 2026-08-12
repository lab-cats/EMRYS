# `construct_FASTA_sidecars` owner

Native owner of `norad.stage.construct_FASTA_sidecars.v1` (historical `00c`).
[`CONTRACT.md`](CONTRACT.md) owns exact behavior, recovery boundaries, and
evidence limits.

## Entry points

- repository producer:
  [`step_00c_prepare_gatk_reference.sh`](step_00c_prepare_gatk_reference.sh)
- grouped validator: `python -I -m norad validate fasta-sidecars`, implemented
  by the private [`validator.py`](validator.py) module
- repository scheduler:
  [`step_00c_prepare_gatk_reference.slurm`](step_00c_prepare_gatk_reference.slurm)

## Operate

Producer dry-run resolves every tool and writes nothing:

```bash
src/norad/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh \
  --reference-fasta refs/novogene_ref/genome.fa \
  --samtools-bin /absolute/path/to/samtools \
  --gatk-bin /absolute/path/to/gatk \
  --java-bin /absolute/path/to/java
```

Add `--execute` after inspection. A valid existing sidecar is reused and only a
missing one is generated. When both are absent, a controlled failure while
publishing the second sidecar rolls the first back, leaving neither final.
Execute mode hashes the FASTA before invoking tools and rechecks it after
generation and through publication; a byte change rejects the attempt and
publishes no new sidecar.
Publication is create-exclusive: a FAI or DICT that appears after the locked
state check is preserved and blocks the attempt. Existing or late foreign
sidecars are never rollback targets. Cleanup removes a published final only
while its retained staging anchor still proves invocation ownership; otherwise
the producer preserves the lock and final/staged residue for explicit
inspection rather than claiming a clean retry boundary.
Run tokens must use the owner's safe identifier vocabulary. Any Step `00c`
FAI, DICT, temporary-FASTA, or temporary-FAI staging path left by another token
blocks both planning and execution. A failed staging or lock removal likewise
returns failure and retains the lock plus remaining residue.

Validator dry-run:

```bash
.venv/bin/python -I -m norad validate fasta-sidecars \
  --scope-id novogene_ref \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --reference-dict refs/novogene_ref/genome.dict \
  --output results/qc/validation/00c/novogene_ref.validation.tsv
```

Create the output parent and add `--execute` to publish. From another working
directory, use the absolute path to the installed interpreter and explicit
absolute input and output paths. The validator shares the neutral contig parser
with reference provenance and the Step `05` validator; each consumer retains
its own evidence decision.

SLURM requires explicit final paths. Omit `EXECUTE=1` for dry-run:

```bash
cd <checkout>
mkdir -p logs
REFERENCE_FASTA=/absolute/refs/genome.fa \
SAMTOOLS_BIN_OVERRIDE=/absolute/path/to/samtools \
GATK_BIN_OVERRIDE=/absolute/path/to/gatk \
JAVA_BIN_OVERRIDE=/absolute/path/to/java TMPDIR=/absolute/path/to/tmp \
EXECUTE=1 \
  sbatch src/norad/stages/fasta_sidecars/step_00c_prepare_gatk_reference.slurm
```

Site defaults are not portable. The wrapper checks only nonempty FAI and DICT;
mocked scheduler tests do not prove site runtime.

## Diagnose and verify

Preserve FASTA, FAI, DICT, validator report, scheduler streams, lock, and
run-token paths before recovery. A clean controlled failure removes only
outputs created by its own attempt; ambiguous or failed-rollback residue is
preserved. Failed staging/lock cleanup and older-token residue are blocking,
not stale state to delete automatically. Never delete a partial pair
automatically. After provenance and ownership are established, an authorized
rerun may generate only the missing sidecar.

```bash
bash tests/stages/fasta_sidecars/test_step_00c_prepare_gatk_reference.sh
.venv/bin/python -m pytest -q \
  tests/stages/fasta_sidecars/test_validate_step_00c_reference_sidecars.py \
  tests/test_slurm_wrapper_contracts.py
```

Evidence is local fixture/mock only, not real samtools/GATK/Java, scheduler,
cluster, production, scientific-review, or biological proof.
