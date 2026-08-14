# Local-pilot adversarial hardening proof

This frozen record preserves the final local evidence used to close the
adversarial hardening follow-up to Campaign B. Current policy remains in
[`TEST_BASELINE.md`](../../design/TEST_BASELINE.md), current evidence ceilings
in [`HANDOFF.md`](../../operations/HANDOFF.md), and operator commands in the
[`RUNBOOK`](../../operations/RUNBOOK.md).

## Assembled local gate

- Date: `2026-08-14` in `America/New_York`.
- Tested source revision:
  `e7ec294c776ef550ebc55d776994c5f896cf3dd3`.
- Source state: clean checkout with the locked CPython `3.14.5` workflow
  environment.
- R: `/usr/local/bin/Rscript`, R `4.6.1`, using the selected existing project
  library root without restoration.

The assembled command was:

```bash
make -s all-checks \
  RSCRIPT_BIN=/usr/local/bin/Rscript \
  RENV_PATHS_LIBRARY=/private/tmp/norad-b6-final.bxJnJJ/norad/renv/library
```

Result: `SUMMARY status=0 mode=parallel jobs=3 python_workers=2
elapsed=1404.214s`.

Passed lanes were static preflight (`0.762s`), isolated installed-wheel smoke
(`12.922s`), guarded real-R checks (`159.735s`), shell and SLURM-wrapper
contracts (`282.447s`), and Python behavior/coverage (`1403.448s`). The clean
coverage measurement reported `1,447` passing tests, `6` explicit skips, and
`34` subprocess tests. Coverage passed the unchanged Campaign B floors with
`14,676 / 16,973` lines (`0.864667`), `4,788 / 6,386` branches (`0.749765`),
and all ten independent critical-owner floors. The two newly admitted shared
modules also passed their `90%` line and `85%` branch introduction floors.

## Clean fresh-clone journey

- Tested source revision:
  `6bded806b4cfb319e27a380da4b6f906c5ce9f66`.
- Source state: a new nonlocal, no-hardlink clone with a clone-local environment
  created from the locked dependency graph in offline mode.
- Result: `2 passed in 280.84s`.

The opt-in journey used explicit deterministic no-science owner collaborators.
It exercised the public help and doctor routes, no-write planning, controlled
between-task failure, failed-run inspection, no-write resume planning,
byte-and-mtime-preserving verified-task reuse, successful resume, semantic
completion inspection, all three reporting transactions, and refusal of a
second initial run and a completed-run resume.

## Evidence ceiling

This is local engineering and deterministic no-science control-plane evidence
for the two named revisions. It did not run real STAR, samtools, Picard, GATK,
bcftools, RSeQC, or scientific R owners; submit or account for SLURM jobs;
exercise CSU modules, filesystems, or production data; establish NFS or other
distributed-filesystem safety; complete scientific review; validate editing
sites biologically; or prove production capacity and performance.
