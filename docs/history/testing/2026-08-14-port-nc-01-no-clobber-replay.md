# PORT-NC-01 no-clobber semantic replay

This frozen record preserves the local integration evidence used to close
PORT-NC-01. Current policy remains in
[`TEST_BASELINE.md`](../../design/TEST_BASELINE.md), current evidence ceilings
in [`HANDOFF.md`](../../operations/HANDOFF.md), and operator commands in the
[`RUNBOOK`](../../operations/RUNBOOK.md).

## Integration boundary

- Date: `2026-08-14` in `America/New_York`.
- Exact integrated candidate:
  `ebc43b4a8342b676eafb6b56492989498886ab55`.
- Source branch head considered during replay:
  `ee3611274d2f1466eb3bd43daa95bd4753d6c282` from `fix/no-clobber`.

The tests added on the source branch were reported as run on the cluster and
as validating real source-branch behavior. That observation established the
intended behavior to preserve; it did not validate the differently implemented
integrated candidate. The replay retained the hardened branch's stronger
create-exclusive transactions, explicit execution, run-token, output-
validation, and controlled-runtime boundaries instead of merging or
cherry-picking the source branch wholesale.

The integrated behavior admits STAR `###` metadata rows without weakening the
required index-parameter checks, sends the deterministic Step `00b` final
through the converter's no-clobber transaction, requires every
repository-owning Slurm wrapper to resolve from the submitted checkout rather
than its spool copy, and routes Step `01` through staged create-exclusive
publication with one bound hash-runtime launcher.

## Assembled local gate

The assembled command used the selected existing R library without dependency
restoration:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript \
RENV_PATHS_LIBRARY=/private/tmp/norad-b6-final.bxJnJJ/norad/renv/library \
  make -s all-checks
```

Result: `SUMMARY status=0 mode=parallel jobs=3 python_workers=2
elapsed=1489.128s`.

Passed lanes were static preflight (`0.745s`), isolated installed-wheel smoke
(`6.768s`), guarded local R (`150.636s`), shell and Slurm-wrapper contracts
(`265.943s`), and Python behavior/coverage (`1488.378s`). The result applies
only to the exact integrated candidate above.

## Evidence ceiling

This is assembled local engineering evidence. The guarded-R lane exercised its
local package and fixture policy, and the shell/Slurm lane exercised local
wrapper contracts; it did not submit or account for Slurm jobs, execute a
distributed filesystem, or prove a site profile. The integrated candidate was
not run on the cluster. This closeout also did not run a fresh-clone or public
local-pilot E2E, real STAR, samtools, Picard, GATK, bcftools, RSeQC, or
production scientific owners and data. It establishes no production readiness,
scientific review, editing-site validity, biological conclusion, or capacity
and performance claim.
