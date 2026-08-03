# `construct_FASTA_sidecars` owner

This directory is the implemented native owner for semantic stage
`construct_FASTA_sidecars` (`norad.stage.construct_FASTA_sidecars.v1`,
historical alias `00c`). Its current public assets are:

- [`step_00c_prepare_gatk_reference.sh`](step_00c_prepare_gatk_reference.sh),
  the mode-`0755` shell producer;
- [`validate_step_00c_reference_sidecars.py`](validate_step_00c_reference_sidecars.py),
  the mode-`0644` explicit-interpreter validator;
- [`step_00c_prepare_gatk_reference.slurm`](step_00c_prepare_gatk_reference.slurm),
  the mode-`0755` scheduler entry point; and
- the mirrored [producer](../../../../tests/stages/construct_FASTA_sidecars/test_step_00c_prepare_gatk_reference.sh)
  and [validator](../../../../tests/stages/construct_FASTA_sidecars/test_validate_step_00c_reference_sidecars.py)
  tests. Scheduler behavior remains independently owned by the central
  [wrapper-contract suite](../../../../tests/test_slurm_wrapper_contracts.py).

## Producer

From the repository root, invoke the producer directly or through Bash with
the reference and all three tools explicit. Both forms are dry-run by default:

```bash
src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.sh \
  --reference-fasta refs/novogene_ref/genome.fa \
  --samtools-bin /absolute/path/to/samtools \
  --gatk-bin /absolute/path/to/gatk \
  --java-bin /absolute/path/to/java

bash src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.sh \
  --reference-fasta refs/novogene_ref/genome.fa \
  --samtools-bin /absolute/path/to/samtools \
  --gatk-bin /absolute/path/to/gatk \
  --java-bin /absolute/path/to/java
```

Dry-run resolves the tools and prints the generation plan but invokes no tool
version or generation command and creates no directory, lock, temporary path,
FAI, or DICT. Add `--execute` only after inspecting that resolved command. From
another working directory, use the absolute checkout path for the producer and
explicit absolute paths for the reference and all three tools.

The producer reuses each valid sidecar and generates only a missing one. Its
two-output publication is not transactional: if final FAI publication succeeds
and final DICT publication fails, the FAI can remain while the DICT is absent.
That FAI is evidence of an incomplete attempt, not successful transaction
output. Preserve it and the surrounding attempt evidence for diagnosis.

## Validator

Invoke the mode-`0644` validator through an explicit interpreter. Omitting
`--execute` is the no-write dry run:

```bash
.venv/bin/python src/norad/stages/construct_FASTA_sidecars/validate_step_00c_reference_sidecars.py \
  --scope-id novogene_ref \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-fai refs/novogene_ref/genome.fa.fai \
  --reference-dict refs/novogene_ref/genome.dict \
  --output results/qc/validation/00c/novogene_ref.validation.tsv
```

After inspecting the five structured rows, create the output parent and add
`--execute` to publish the report. Repeating the same execute command replaces
the owned report deterministically after stable-input validation. From another
working directory, use absolute paths for the interpreter, validator, three
inputs, and output.

The validator privately exact-loads the unchanged public
[`scripts/reference_provenance.py`](../../../../scripts/reference_provenance.py)
owner and the neutral validation-report library. An exact reference-loader
failure is a checkout-integrity diagnostic; do not work around it by changing
`PYTHONPATH`. This migration does not extract, package, or reassign the public
reference-provenance owner.

## Scheduler entry point

SLURM opens the declared log paths before the job body runs. Create `logs/`,
change to the intended checkout, and submit the exact final job. Omitting
`EXECUTE` keeps the default dry run:

```bash
cd /path/to/norad
mkdir -p logs
REFERENCE_FASTA=/absolute/refs/genome.fa \
SAMTOOLS_BIN_OVERRIDE=/absolute/path/to/samtools \
GATK_BIN_OVERRIDE=/absolute/path/to/gatk \
JAVA_BIN_OVERRIDE=/absolute/path/to/java \
TMPDIR=/absolute/path/to/tmp \
  sbatch src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.slurm
```

Real work uses the same explicit bindings plus `EXECUTE=1`:

```bash
cd /path/to/norad
mkdir -p logs
REFERENCE_FASTA=/absolute/refs/genome.fa \
SAMTOOLS_BIN_OVERRIDE=/absolute/path/to/samtools \
GATK_BIN_OVERRIDE=/absolute/path/to/gatk \
JAVA_BIN_OVERRIDE=/absolute/path/to/java \
TMPDIR=/absolute/path/to/tmp \
EXECUTE=1 \
  sbatch src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.slurm
```

The current CSU samtools and GATK defaults are site bindings, not portable
defaults. Module setup is tolerated. Bash `3.2` can fail in default dry-run
before producer delegation because of the characterized empty-array expansion.
After execute mode, the wrapper checks only that the declared FAI and DICT are
nonempty files; it does not independently validate their contents.

## Diagnostics, recovery, and evidence

For malformed or mismatched sidecars, preserve the FASTA, FAI, DICT, and
validator report together and establish their provenance before deciding on a
rerun. For a nonzero producer attempt that leaves FAI present and DICT absent,
also preserve the exact producer context, scheduler stdout/stderr, lock state,
run-token temporary paths, and final FAI/DICT state. Do not call that partial
publication success or delete it automatically. After provenance and ownership
are established, a separately authorized rerun may generate only the missing
DICT while reusing a valid FAI.

Run the focused local migration surface with:

```bash
bash tests/stages/construct_FASTA_sidecars/test_step_00c_prepare_gatk_reference.sh
.venv/bin/python -m pytest -q \
  tests/stages/construct_FASTA_sidecars/test_validate_step_00c_reference_sidecars.py \
  tests/test_slurm_wrapper_contracts.py
```

Final-path acceptance passed the moved shell suite and the exact affected
Python surface (`561` tests). Deterministic serial coverage measured the
validator at `128/139` lines and `35/42` branches and the global surface at
`9381/11549` lines and `3293/4714` branches, above the frozen covered-count
floor. The aggregate gate was not fully green: static preflight, shell
contracts, guarded R, and report runtime passed, while Python reported only ten
migration-caused stale documentation links plus nine inherited `UNREFINED`
card-location findings. This documentation close repairs the ten migration
links; the inherited findings remain nonpassing.

The artifact index records the producer's final path and reviewed SHA-256
`ed3e9ca039102c881c4f91cb02fd32e4a67d09ad799300c789cbab27ce1ab0a1`
without changing public artifact identities or schemas. Rollback reverts the
documentation close before executable checkpoint `cd3b547`; published
old-path baseline `9850a8d` is the prior evidence checkpoint.

The migration added no wrapper, symlink, package marker, import identity,
descriptor, schema, transaction, receipt, recovery marker, or scheduler
abstraction. See [`CONTRACT.md`](CONTRACT.md) for the full current behavior and
characterized defects. Migration evidence is local fixture/mock, guarded
local-R, pinned report-runtime, and local coverage evidence only; it is not real
samtools/GATK/Java runtime, scheduler, cluster, production, scientific-review,
or biological proof.
