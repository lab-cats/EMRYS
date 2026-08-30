# Sample-manifest admission owner

This directory owns the existing, deliberately narrow sample-manifest admission
family. Its public assets are:

- `python -I -m emrys validate manifest`, the installed module command
  implemented by [`validator.py`](validator.py), which validates a TSV manifest
  and optionally checks that its declared FASTQ paths exist;
- [`check_fastq_pairs.sh`](check_fastq_pairs.sh), the mode-`0755` operator-run
  paired-FASTQ diagnostic; and
- [`validate_manifest.slurm`](validate_manifest.slurm), the mode-`0644`
  scheduler smoke-check wrapper submitted through `sbatch`.

The committed
[`samples.example.tsv`](../../../../configs/samples.example.tsv) is the public
starter used by `make validate` and the scheduler smoke check. It is an example,
not an admitted production manifest or evidence. Direct validator protection
lives in
[`test_validate_manifest.py`](../../../../tests/ingestion/sample_manifest_admission/test_validate_manifest.py),
the paired-FASTQ diagnostic is characterized with tiny generated inputs in
[`test_check_fastq_pairs.py`](../../../../tests/ingestion/sample_manifest_admission/test_check_fastq_pairs.py),
and scheduler syntax and delegation remain protected by the central
[`test_slurm_wrapper_contracts.py`](../../../../tests/test_slurm_wrapper_contracts.py).
Those local tests do not replace operator review of real data.

## Manifest validator

The validator requires the tab-separated columns `sample_id`, `r1_fastq`,
`r2_fastq`, `strandedness`, and `condition`; it permits only `notes` and
`replicate` as optional columns. It rejects duplicate sample IDs, empty required
identities or paths, unsupported strandedness values, malformed rows, and
manifests with no sample rows. Accepted strandedness values are `forward`,
`reverse`, `unstranded`, and `unknown`.

By default the validator checks manifest structure and values but does not
access the FASTQ files. `--check-files` adds existence checks only. Relative
FASTQ paths are resolved against `--base-dir`, whose default is the process
working directory; absolute FASTQ paths are checked directly. The validator
does not inspect FASTQ contents or invoke the paired-FASTQ checker.

From the repository root:

```bash
.venv/bin/python -I -m emrys validate manifest \
  --manifest configs/samples.example.tsv \
  --base-dir .
```

Add `--check-files` only when the manifest's declared FASTQ paths are available
under the selected base directory. From another working directory, select the
installed interpreter and make the manifest and base directory absolute:

```bash
repo=/absolute/path/to/emrys
"$repo/.venv/bin/python" -I -m emrys validate manifest \
  --manifest "$repo/configs/samples.example.tsv" \
  --base-dir "$repo"
```

Exit `0` means the selected checks passed. Exit nonzero reports admission
errors; no receipt, normalized manifest, hash, frozen copy, or other output is
published. This admission schema intentionally continues to permit a missing
`replicate` column. Stricter sample-manifest requirements owned by downstream
neutral scientific-evidence contracts are separate and are not weakened or
replaced by this validator. The strict Project draft route is `emrys init
manifests`; it requires `replicate` and delegates final admission back to those
current contracts.

## Paired-FASTQ diagnostic

From the repository root, provide one explicit pair:

```bash
src/emrys/ingestion/sample_manifest_admission/check_fastq_pairs.sh \
  --r1-fastq /absolute/path/sample_R1.fastq.gz \
  --r2-fastq /absolute/path/sample_R2.fastq.gz \
  --sample-id sample_001 \
  --num-reads 20
```

The diagnostic accepts plain or gzip-suffixed FASTQ files. It requires each
line count to be divisible by four, requires equal total read counts, and
compares the requested number of leading normalized read IDs. `--num-reads`
defaults to `20`; gzip-suffixed input requires `gunzip` on `PATH`. Input paths
are interpreted from the process working directory unless absolute. The check
reads the declared files and writes no result artifact or receipt.

Passing this diagnostic establishes only those pair-count and leading-ID
checks for the two selected files. It does not establish complete record-level
pairing, sequence or quality integrity, sample identity, provenance, or
production readiness.

## Scheduler smoke check

The scheduler wrapper changes to the submitted repository root and validates
the committed starter without `--check-files`. It uses
`$EMRYS_PYTHON_BIN` when set, otherwise `.venv/bin/python` in that checkout;
the selected environment must already contain the editable EMRYS distribution.
Create `logs/` before submission because SLURM opens the declared output and
error paths before the job body runs:

```bash
mkdir -p logs
sbatch src/emrys/ingestion/sample_manifest_admission/validate_manifest.slurm
```

The wrapper is a lightweight environment and delegation check. Scheduler exit
`0` does not prove FASTQ availability, cluster-scale pipeline execution, or a
production admission event.

## Boundary and evidence ceiling

These interfaces validate only the explicitly selected manifest or FASTQ pair.
They do not discover or acquire inputs, normalize content, calculate or bind
hashes, freeze a request, claim an inbox item, manage run or attempt lifecycle,
select profiles or policies, launch computational stages, or create, publish,
approve, or promote evidence. A passing local or scheduler check is not
workflow execution, scientific review, validated RNA editing, or biological
readiness. No autonomous ingestion runner is implemented here.
