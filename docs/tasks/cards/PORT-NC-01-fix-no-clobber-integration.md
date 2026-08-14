# PORT-NC-01 — Replay cluster-confirmed no-clobber fixes

## Outcome

The hardened Campaign B branch incorporates the useful behavior from
`fix/no-clobber` without replacing stronger current transactions, runtime
authority, or evidence contracts.

## Touches

Writes are limited to the STAR index metadata parser and fixture; the Step 00b
converter wrapper, tests, and adjacent owner documentation; the repository-owning
SLURM wrappers and their direct contract tests; the Step 01 owner/wrapper,
tests, and adjacent documentation; literal producer-provenance or public-command
fixtures changed by those exact bytes; and current task/handoff/evidence text.
Remote branches, `.venv*`, `make setup`, generic site configuration, generic
SLURM validation scripts, cluster systems, production data, scientific methods,
and unrelated owners are outside scope.

## Stop

Stop before mutation if the source or target revision is not exact and clean,
if the semantic replay would weaken create-absent publication, omit current
`--execute` or run-token authority, change scientific output semantics, require
dependency installation, overwrite unrelated work, or delete foreign evidence.
Stop before release if the wrapper-spool contract is not closed across every
repository-owning wrapper, focused owner tests fail, or the assembled local gate
would require policy weakening.

## Context

The source branch head `ee3611274d2f1466eb3bd43daa95bd4753d6c282`
diverges from the hardened branch and contains eight non-merge commits. Its
added tests were run on the cluster and confirmed the intended source-branch
behavior. That evidence guides the replay but does not automatically validate
the different integrated commit. Wholesale merge or cherry-pick would regress
current explicit execution, selected-Java/controlled-Python GATK startup,
run-token binding, and stronger transaction semantics.

## Deliverables

- Ignore `###` STAR metadata rows while retaining current exact index-parameter
  validation.
- Have the Step 00b wrapper publish the deterministic final BED through the
  current converter transaction, with explicit execution and run-token
  authority and no bedtools intermediate.
- Require and enter the literal `SLURM_SUBMIT_DIR` before any checkout-relative
  path resolution in every repository-owning SLURM wrapper.
- Route Step 01 through the current staged create-exclusive no-clobber owner by
  default and keep wrapper dry-run/execute behavior explicit.
- Explicitly reject the source branch's broad environment, setup, site-config,
  generic validation-script, weak-lock, and ambient-runtime changes.

## Acceptance evidence

Each semantic commit passes its direct owner and wrapper tests, syntax/lint,
public-command or literal-provenance checks, and `git diff --check`. The
assembled candidate then passes the unchanged local validation policy. Cluster
verification is a later operator-run sequence against the exact integrated
commit; the source branch's observed cluster behavior is retained as prior
evidence, not promoted to the new tree.

## Documentation updates

Update only directly affected owner contracts, wrapper usage, live handoff,
pipeline plan, task registry, and a dated integration evidence record after the
observed gates. Do not rewrite frozen Campaign B or adversarial-hardening
records, and do not touch the user-owned `docs/quickstart.md`.
