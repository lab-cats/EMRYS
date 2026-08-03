# `construct_STAR_index` owner

This directory is the implemented native owner for semantic stage
`construct_STAR_index` (`norad.stage.construct_STAR_index.v1`, historical alias
`00a`). Its current public assets are:

- [`step_00a_build_novogene_star_index.slurm`](step_00a_build_novogene_star_index.slurm),
  the mode-`0644` scheduler entry point;
- [`validate_step_00a_star_index.py`](validate_step_00a_star_index.py), the
  mode-`0644` explicit-interpreter validator; and
- the mirrored [validator](../../../../tests/stages/construct_STAR_index/test_validate_step_00a_star_index.py)
  and [mocked-job](../../../../tests/stages/construct_STAR_index/test_step_00a_build_novogene_star_index.py)
  tests.

Submit the producer from the repository root with:

```bash
sbatch src/norad/stages/construct_STAR_index/step_00a_build_novogene_star_index.slurm
```

The job executes implicitly on submission, has no dry-run mode, and resolves
its hardcoded Novogene inputs and `refs/` outputs from the caller's working
directory. It is a scheduler input, not a directly executable file. The exact
operator assumptions and output route remain in the
[Step `00a` runbook](../../../../docs/operations/RUNBOOK.md#step-00a-star-index).

Invoke the validator with the repository Python and explicit inputs. Omitting
`--execute` is the no-write dry run; adding it publishes the declared output:

```bash
.venv/bin/python src/norad/stages/construct_STAR_index/validate_step_00a_star_index.py \
  --scope-id novogene_ref \
  --index-dir refs/novogene_star_index \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-gtf refs/novogene_ref/genome.gtf \
  --parameter-path-base . \
  --expected-sjdb-overhang 149 \
  --output results/qc/validation/00a/novogene_ref.validation.tsv
```

Unlike the job, the validator is arbitrary-CWD capable when its inputs are
explicit. Create the output parent before an `--execute` invocation. Run the
owner-focused local tests with:

```bash
.venv/bin/python -m pytest -q \
  tests/stages/construct_STAR_index/test_validate_step_00a_star_index.py \
  tests/stages/construct_STAR_index/test_step_00a_build_novogene_star_index.py
```

The artifact index intentionally records the job's final path while preserving
its implementation evidence ID and frozen source hash. The migration added no
wrapper, compatibility copy, symlink, package marker, import identity,
descriptor, or schema. See [`CONTRACT.md`](CONTRACT.md) for behavior and known
defects. Migration evidence is local fixture/mock evidence only; it is not
runtime, scheduler, production, scientific-review, or biological proof.
