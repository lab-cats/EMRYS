# Campaign B assembled local gate

This frozen record preserves the assembled local validation used to close
Campaign B. Current policy remains in
[`TEST_BASELINE.md`](../../design/TEST_BASELINE.md), current evidence ceilings
in [`HANDOFF.md`](../../operations/HANDOFF.md), and operator commands in the
[`RUNBOOK`](../../operations/RUNBOOK.md).

## Source and command

- Date: `2026-08-13` in `America/New_York`.
- Tested source revision: `844920ccaa22c78b7848c102dd3ebfaf452c2eac`.
- Source state: clean detached checkout in the retained validation clone.
- Python: locked clone-local CPython `3.14.5` workflow environment.
- R: `/usr/local/bin/Rscript`, R `4.6.1`, with the restored repository library.

The assembled command was:

```bash
RSCRIPT_BIN=/usr/local/bin/Rscript make -s all-checks
```

Result: `SUMMARY status=0 mode=parallel jobs=3 python_workers=2
elapsed=1407.804s`.

## Passed lanes

- locked-environment congruence and static preflight;
- isolated installed-wheel smoke;
- direct shell producer and SLURM-wrapper contract fixtures;
- guarded real-R package and fixture checks;
- the full Python behavior/coverage lane; and
- exact coverage non-regression against the Campaign B baseline: `13817 /
  15987` lines (`0.864265`), `4530 / 6054` branches (`0.748266`), and ten
  independent critical-owner floors. The Python lane reported
  `PASS python-coverage elapsed=1407.031s`.

## Evidence ceiling

This is assembled local engineering evidence for the tested revision. It is
separate from the clean-clone deterministic no-science E2E recorded at
`cbea15b`. It did not run real STAR, samtools, Picard, GATK, bcftools, or RSeQC
science stages; submit or account for SLURM jobs; exercise CSU modules,
filesystems, or production data; complete scientific review; validate editing
sites biologically; or prove production capacity and performance.
