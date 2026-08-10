# `assemble_scientific_review_evidence_package` owner

Native owner of
`norad.evidence.assemble_scientific_review_evidence_package.v1` (historical
`09c`). [`CONTRACT.md`](CONTRACT.md) owns the exact thirteen-output,
evidence-state, recovery, and consumer contract.

## Entry points

- launcher: [`step_09c_scientific_validation.sh`](step_09c_scientific_validation.sh)
- validation/publication owner: [`step_09c_scientific_validation.py`](step_09c_scientific_validation.py)
- private implementation seams: [`_scientific_review/`](_scientific_review/README.md)

There is no scheduler wrapper, installed command, external package API, legacy
path, or ambient `PYTHONPATH` contract.

## Operate

The owner accepts exact manifests, all Step `08` outputs, the Step `09` output
directory, one-row review plan, evidence manifest and every declared payload,
and output root. It never discovers substitutes, reruns CMH, infers reviewer
decisions, repairs evidence, or installs dependencies.

The tracked example plans/manifests/schemas are structural references, not
selected inputs or production evidence. Dry-run writes nothing:

```bash
review=REVIEW_ID analysis=ANALYSIS_ID cohort=COHORT_ID
PYTHON_BIN_OVERRIDE=.venv/bin/python \
  src/norad/evidence/assemble_scientific_review_evidence_package/step_09c_scientific_validation.sh \
  --review-id "$review" \
  --sample-manifest samples.tsv \
  --partition-manifest configs/step_07_partitions.primary_contigs.tsv \
  --step08-sites "results/vcf_preprocessed/$cohort/$cohort.step08_sites.tsv" \
  --step08-inputs "results/vcf_preprocessed/$cohort/$cohort.step08_inputs.tsv" \
  --step08-summary "results/vcf_preprocessed/$cohort/$cohort.step08_summary.tsv" \
  --step09-analysis-dir "results/editing/$analysis" \
  --review-plan /explicit/path/to/review_plan.tsv \
  --evidence-manifest /explicit/path/to/evidence_manifest.tsv \
  --output-root results/scientific_validation
```

Add `--execute` only after every declaration, hash, state, output name, and
recovery path is inspected. From another CWD, make every path absolute and use
a unique review ID plus fresh output root.

Evidence status is `missing`, `incomplete`, `complete`, or justified
`not_applicable`. Overall state is only `evidence_incomplete` or
`science_review_complete_exploratory`; the latter remains provisional.
`biological_interpretation_ready` is reserved and rejected. Publication does
not authenticate declared runtime metadata, prove production execution,
complete scientific review, validate editing sites, or establish biology.

Execute locks one review, stages thirteen tables, requires all predecessors or
none, publishes twelve payloads, then the summary, and rechecks all bound
inputs. Summary visibility precedes final validation and does not prove commit.
Failed restoration preserves the lock/backups/transaction/recovery notice.
`TERM` and `KeyboardInterrupt` have characterized severe recovery defects; see
the exact states in the contract before any recovery action.

## Diagnose and verify

Before cleanup or retry, preserve all thirteen finals, matching temporary and
previous paths, recovery notices, lock metadata, all bound inputs, independent
code/interpreter identity, streams, environment, PID/signal evidence, and
unrelated bytes. Rule out every writer and reader. Never combine attempts,
manufacture a member, delete a foreign/recovery lock, discard a backup, or
reuse an ambiguous root.

```bash
bash tests/evidence/assemble_scientific_review_evidence_package/test_step_09c_scientific_validation.sh
.venv/bin/python -m pytest -q \
  tests/evidence/assemble_scientific_review_evidence_package/test_step_09c_scientific_validation.py \
  tests/contracts/scientific_evidence/test_step08.py \
  tests/contracts/scientific_evidence/test_step09.py \
  tests/contracts/scientific_evidence/test_review_package.py \
  tests/stages/cohort_candidate_preprocessing/test_validate_step_08_preprocessing_outputs.py \
  tests/analyses/paired_cmh_candidate_ranking/test_validate_step_09_cmh_outputs.py
.venv/bin/python -m pytest -q \
  tests/reporting/test_artifact_adapters.py \
  tests/reporting/test_artifact_run_summary.py \
  tests/contract_integration/independent_contract_goldens/test_independent_contract_goldens.py \
  tests/test_public_cli_contracts.py
```

This is local shell/Python/fixture evidence only, not scheduler, cluster,
production, completed-review, editing-site, or biological proof.
