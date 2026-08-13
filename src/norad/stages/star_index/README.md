# `construct_STAR_index` owner

This directory is the implemented native owner for semantic stage
`construct_STAR_index` (`norad.stage.construct_STAR_index.v1`, historical alias
`00a`). Its current public surfaces and direct protection are:

- [`step_00a_build_novogene_star_index.slurm`](step_00a_build_novogene_star_index.slurm),
  the mode-`0644` scheduler entry point;
- [`step_00a_build_star_index.sh`](step_00a_build_star_index.sh), the explicit
  scheduler-independent producer;
- `python -I -m norad validate star-index`, implemented by the private
  mode-`0644` [`validator.py`](validator.py) module; and
- the mirrored [validator](../../../../tests/stages/star_index/test_validate_step_00a_star_index.py)
  and [mocked-job](../../../../tests/stages/star_index/test_step_00a_build_novogene_star_index.py)
  tests.

Plan one local build from any working directory with explicit paths:

```bash
bash src/norad/stages/star_index/step_00a_build_star_index.sh \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-gtf refs/novogene_ref/genome.gtf \
  --index-dir refs/novogene_star_index \
  --threads 8 \
  --sjdb-overhang 149 \
  --genome-sa-index-nbases 14 \
  --star-bin /absolute/path/to/STAR
```

Dry-run validates the inputs and STAR executable and writes nothing. Add
`--execute` to generate into an owner-token staging directory, require all 15
declared index members, reserve the absent final directory, and link every staged
member into that reservation. Immediately before commit, the final directory
must contain exactly the staged member set and every final must still be the
staged inode. Existing or late-arriving output, an owner lock, or any staging
residue blocks the invocation and is never replaced automatically. A failure
after final reservation preserves the partial final, lock, and residue for
operator inspection.

The legacy Novogene scheduler entry point remains:

```bash
sbatch src/norad/stages/star_index/step_00a_build_novogene_star_index.slurm
```

The job executes implicitly on submission, resolves its hardcoded compressed
Novogene inputs and `refs/` outputs from the caller's working directory,
materializes the legacy reference files, and then delegates index construction
to the public producer with `--execute`. It is a scheduler input, not a directly
executable file.

Invoke the validator with the repository Python and explicit inputs. Omitting
`--execute` is the no-write dry run; adding it publishes the declared output:

```bash
.venv/bin/python -I -m norad validate star-index \
  --scope-id novogene_ref \
  --index-dir refs/novogene_star_index \
  --reference-fasta refs/novogene_ref/genome.fa \
  --reference-gtf refs/novogene_ref/genome.gtf \
  --parameter-path-base . \
  --expected-sjdb-overhang 149 \
  --expected-genome-sa-index-nbases 14 \
  --output results/qc/validation/00a/novogene_ref.validation.tsv
```

The producer and installed validator route are arbitrary-CWD capable when their
paths are explicit. Use absolute script, executable, and interpreter paths from
another working directory. Create the validation output parent before an
`--execute` invocation. Run the owner-focused local tests with:

```bash
.venv/bin/python -m pytest -q \
  tests/stages/star_index/test_validate_step_00a_star_index.py \
  tests/stages/star_index/test_step_00a_build_novogene_star_index.py
```

The artifact index intentionally records the producer's final path while
preserving its implementation evidence ID and frozen source hash. See
[`CONTRACT.md`](CONTRACT.md) for behavior and recovery boundaries. Available
fixture/mock evidence is local only; it is not runtime, scheduler, production,
scientific-review, or biological proof.
