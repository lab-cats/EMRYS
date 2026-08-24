# Alignment libraries

This package contains narrow parsers and admission helpers for alignment and
alignment-adjacent formats:

- [`bam.py`](bam.py) — shared BAM/BAI and SAM-header admission used by Steps
  `01`, `02`, `04`, `05`, and `06` validators.
- [`bed.py`](bed.py) — BED12 parsing currently used only by the Step `00b`
  validator; it is not authority for a broader shared seam.
- [`orientation.py`](orientation.py) — shared mechanical-orientation labels and
  count parsing used by scientific contracts, owner validators, and artifact
  indexing.
- [`star.py`](star.py) — shared STAR output parsing used by Steps `00a` and
  `01` validation plus artifact indexing.

These helpers return in-memory admitted data. They do not run scientific tools,
write native outputs, publish validation, or decide stage or biological
meaning. Consumers retain their own check rosters and evidence semantics. The
approved dependency boundaries live in
[`SOURCE_TOPOLOGY.md`](../../contracts/SOURCE_TOPOLOGY.md). Direct protection lives in
[`test_bam_validation.py`](../../../../tests/libraries/test_bam_validation.py)
and
[`test_shared_domain_helpers.py`](../../../../tests/libraries/test_shared_domain_helpers.py).
