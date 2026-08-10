# Alignment libraries

This package contains neutral parsers and validator helpers for alignment and
alignment-adjacent formats:

- [`bam.py`](bam.py) — BAM/BAI admission, samtools readiness, and SAM-header
  inspection.
- [`bed.py`](bed.py) — BED12 parsing and structural checks.
- [`orientation.py`](orientation.py) — mechanical orientation labels, policy,
  and count parsing.
- [`star.py`](star.py) — STAR log, junction, parameter, and contig parsing.

Stage, analysis, evidence, and reporting consumers retain their own check
rosters and meaning. Direct neutral protection lives in
[`test_bam_validation.py`](../../../../tests/libraries/test_bam_validation.py)
and
[`test_shared_domain_helpers.py`](../../../../tests/libraries/test_shared_domain_helpers.py).
