# `assemble_scientific_review_evidence_package` owner

This directory is the implemented native owner for semantic evidence operation
`assemble_scientific_review_evidence_package`
(`norad.evidence.assemble_scientific_review_evidence_package.v1`, historical
alias `09c`). Its public assets are:

- [`step_09c_scientific_validation.sh`](step_09c_scientific_validation.sh),
  the mode-`0755` directly executable Bash launcher;
- [`step_09c_scientific_validation.py`](step_09c_scientific_validation.py),
  the mode-`0644` explicit-interpreter validation and thirteen-table
  publication owner; and
- the mirrored [shell](../../../../tests/evidence/assemble_scientific_review_evidence_package/test_step_09c_scientific_validation.sh)
  and [Python](../../../../tests/evidence/assemble_scientific_review_evidence_package/test_step_09c_scientific_validation.py)
  protection plus its adjacent
  [fixture builder](../../../../tests/evidence/assemble_scientific_review_evidence_package/build_fixture.py).

There is no SLURM wrapper, installed command, package import, compatibility
copy, legacy executable path, symlink, ambient `PYTHONPATH`, or global
`sys.path` mutation.

## Inputs, evidence choices, and dry run

The owner accepts one safe review ID and exact paths for the sample and
partition manifests; all three Step `08` outputs; the directory containing all
six Step `09` outputs named by the review plan; the one-row review plan; the
evidence manifest and every payload it declares; and the output root. It does
not discover substitutes, rerun CMH, infer reviewer decisions, repair evidence,
or install dependencies.

The committed
[`step_09c_review_plan.example.tsv`](../../../../configs/step_09c_review_plan.example.tsv),
[`step_09c_evidence_manifest.example.tsv`](../../../../configs/step_09c_evidence_manifest.example.tsv),
and thirteen
[`step_09c_evidence_schemas/`](../../../../configs/step_09c_evidence_schemas/)
TSVs are structural references. They are not selected automatically and are
not production evidence. Build production declarations from inspected source
evidence under approved results storage; never alter a hash, row count, status,
category, or decision merely to force acceptance.

From the repository root, this is a no-write dry run unless `--execute` is
added:

```bash
review=REVIEW_ID
analysis=ANALYSIS_ID
cohort=COHORT_ID
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

Dry-run validates every declaration and source, prints the selected review,
inputs, evidence, output names, and delegated Python command, and creates no
output directory, lock, scratch path, backup, or final table. Inspect all
choices before adding `--execute`. The shell resolves
`PYTHON_BIN_OVERRIDE` as an executable slash path or PATH basename and then
delegates only to its adjacent Python sibling.

Direct Python use has the same arguments and effects:

```bash
.venv/bin/python \
  src/norad/evidence/assemble_scientific_review_evidence_package/step_09c_scientific_validation.py \
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

From another CWD, make the launcher or Python file, interpreter, both
manifests, all three Step `08` files, Step `09` directory, review plan, evidence
manifest and every payload it names, and output root absolute. Use a unique
review ID and a fresh absolute output root for the safest first run.

## Evidence and science state

The package requires explicit orientation/locus and annotation audits; QC
funnel and replicate effects; sensitivity and leave-one-pair-out analyses;
candidate selection and adjudication; decisions and limitations; and separately
declared computational validation. Evidence is `missing`, `incomplete`,
`complete`, or justifiably `not_applicable`.

The only accepted overall science states are:

```text
evidence_incomplete
science_review_complete_exploratory
```

`science_review_complete_exploratory` remains provisional.
`biological_interpretation_ready` is reserved and rejected. Package
publication validates and packages declarations; it does not authenticate
declared Git/software/runtime metadata, prove production execution, complete a
production scientific review, validate editing sites, or establish biological
readiness.

## Thirteen-file transaction

Execute mode owns `<output-root>/<review-id>/` and publishes exactly:

```text
<review>.step09c_review_plan.tsv
<review>.step09c_evidence_index.tsv
<review>.step09c_orientation_locus_audit.tsv
<review>.step09c_annotation_audit.tsv
<review>.step09c_qc_funnel.tsv
<review>.step09c_replicate_effects.tsv
<review>.step09c_sensitivity_matrix.tsv
<review>.step09c_leave_one_pair_out.tsv
<review>.step09c_candidate_selection.tsv
<review>.step09c_candidate_adjudication.tsv
<review>.step09c_decisions.tsv
<review>.step09c_limitations.tsv
<review>.step09c_review_summary.tsv
```

The owner acquires a mode-`0600` regular lock named
`.<review>.step09c.lock`, stages under one run token, requires either all
thirteen predecessor finals or none, backs up a complete predecessor, removes
its predecessor summary, publishes twelve payloads in fixed order, then
publishes the new summary. It validates final contents and hashes and performs
a second check of all 32 bound inputs. The summary does not hash its twelve
siblings and becomes visible before those final checks; visibility is not
durable committed-attempt proof.

Ordinary first-publication failure removes new finals and owned residue.
Ordinary replacement failure restores all thirteen predecessor files with the
summary last. If restoration is incomplete, preserve the retained lock,
backup, transaction directory, recovery notice, and every final exactly as
found. Do not clean or retry by inference.

Two severe signal defects are characterized, not approved. `TERM` after
summary visibility has no handler and can leave thirteen unvalidated new
finals, thirteen predecessor backups, the lock, and an empty transaction
directory without a recovery notice. `KeyboardInterrupt` can bypass rollback
but run `finally`, leaving the new finals while deleting predecessor backups,
the transaction directory, and the lock.

Before diagnosis, restoration, cleanup, or retry, preserve all thirteen
finals; every matching `.tmp`, `.previous`, and `.RECOVERY.txt` path; the lock
and metadata; all 32 inputs; independently available interpreter/code identity;
streams, environment, PID and signal evidence; and unrelated bytes. Rule out
every writer and downstream reader. Never delete a foreign or recovery lock,
discard a backup, combine attempts, manufacture a member or summary, or reuse
an ambiguous root. A separately authorized nonproduction diagnostic retry uses
a new isolated absolute output root. See the dedicated
[Step `09c` recovery routes](../../../../docs/operations/TROUBLESHOOTING.md#step-09c-finds-a-lock-partial-output-set-changed-input-or-incomplete-rollback).

## Private consumers and downstream provenance

The final Step `09` validator, this implementation, and
[`build_artifact_index.py`](../../../../scripts/build_artifact_index.py)
privately exact-load both neutral
[`step08.py`](../../contracts/scientific_evidence/step08.py) under
`_norad_step08_scientific_evidence_contract` and neutral
[`step09.py`](../../contracts/scientific_evidence/step09.py) under
`_norad_step09_scientific_evidence_contract`. The Step `09` contract reuses the
Step `08` `ContractError` and `Table`; all three consumers fail closed if any
shared owner identity splits.

This implementation, the artifact index, and
[`_run_summary_science.py`](../../../../scripts/_run_summary_science.py)
exact-load neutral
[`review_package.py`](../../contracts/scientific_evidence/review_package.py)
under `_norad_review_package_scientific_evidence_contract` for the public
thirteen-file roster, headers, vocabularies, bindings, and evidence-status
reducer. These loader families validate cached-owner identity and readiness,
insert before execution, clean only their own partial cache entry, leave
`sys.path` unchanged, and expose no public package identity.

The artifact index no longer loads this final Step `09c` Python file. Run-
summary science still exact-loads it under
`_norad_step_09c_scientific_validation_contracts` only for private review
context and policy, and rejects a split neutral review-package identity. The
Step `09` validator consumes the neutral Step `09` owner directly and does not
load this review implementation.

Artifact indexing uses the neutral review-package contract while treating the
published Step `09c` package and `step09c_review_summary_v1` as source evidence
for all thirteen adapters. Run-summary assembly accepts one explicit committed
summary and reconstructs the complete package. Reporting consumes only that
authorized normalized record. None of these consumers proves which
publication attempt returned success or promotes computational, scientific,
or biological state.

## Focused protection and rollback

Focused local protection is:

```bash
bash tests/evidence/assemble_scientific_review_evidence_package/test_step_09c_scientific_validation.sh
.venv/bin/python -m pytest -q \
  tests/evidence/assemble_scientific_review_evidence_package/test_step_09c_scientific_validation.py
.venv/bin/python -m pytest -q \
  tests/contracts/scientific_evidence/test_step08.py \
  tests/contracts/scientific_evidence/test_step09.py \
  tests/contracts/scientific_evidence/test_review_package.py \
  tests/stages/preprocess_and_annotate_cohort_candidates/test_validate_step_08_preprocessing_outputs.py \
  tests/analyses/rank_cohort_candidates_with_paired_CMH/test_validate_step_09_cmh_outputs.py
.venv/bin/python -m pytest -q \
  tests/test_artifact_adapters.py tests/test_artifact_run_summary.py \
  tests/test_independent_contract_goldens.py tests/test_public_cli_contracts.py
```

Published wrapper, input-identity, publication-order, recovery, and signal/
concurrency checkpoints are `0dea4da`, `bd680b6`, `d9b0ce8`, `3fa0699`, and
`d459440`. Executable checkpoint `d1cce50` moved exactly five files and updated
fourteen reviewed integration owners. At that migration checkpoint, the final
Python implementation was byte-identical at SHA-256
`7b6b48b71c07249cb791ceb818bd4aef5c30015724cb2406127159815c1e09f8`;
the shell's only implementation change is its displayed usage path.

At that migration checkpoint, the final shell suite passed; `65` direct Python
tests passed; Step `08`/`09` loader suites passed `53`; selected artifact and
run-summary loader/provenance checks passed `16`; and independent-golden plus
public-CLI suites passed. The first complete network-enabled gate was not
green: static, shell, guarded-R, and report-runtime passed, then Python reached
`1,323` passes and `17` skips before its sole failure listed the eight
intentionally deferred documentation links; coverage did not run. A coverage
run with only that known documentation assertion deselected passed `1,323`
tests with `17` skips and one deselection, and its standalone policy comparison
passed. None of this is cluster,
production, completed-review, editing-site, or biological evidence.

After the separate documentation close repaired those links, `git diff
--check` and `make -s documentation-check` passed for `214` Markdown documents,
`133` task cards, and `6` Mermaid sources. The exact network-enabled aggregate
rerun then passed static, shell, guarded-R, report-runtime, and Python-coverage
lanes with summary status `0` in `200.121s`. This later green result does not
turn either earlier attempt into a pass or establish scheduler, cluster,
production, completed-review, editing-site, or biological proof.

Later executable checkpoint `95f795e` extracted the public review-package
contract without changing Step `09c` review policy or publication. Its final
focused roster passed `558` tests; complete Python coverage passed `1,538`
tests with `17` skips and measured the neutral owner at `53/53` lines and `8/8`
branches. Static, shell, report-runtime, and project-local Step `08`/`09` real-
R semantic routes passed. The aggregate remained non-green at guarded R
because the environment checker reported one out-of-date package; no package
was installed, restored, removed, or updated.

Rollback of only LIB-02I reverts its documentation close, executable
`95f795e`, then selection `d416e47`. Any deeper rollback must follow the full
reverse branch lineage in
[`PIPELINE_PLAN.md`](../../../../docs/design/PIPELINE_PLAN.md#approved-current-delivery-lineage)
and operations history; do not skip the intervening LIB-02G, LIB-02H, or
MIG-04A packages. Git cannot authenticate, recover, delete, or alter runtime
evidence, outputs, locks, backups, notices, or review state. See
[`CONTRACT.md`](CONTRACT.md) for the full boundary.
