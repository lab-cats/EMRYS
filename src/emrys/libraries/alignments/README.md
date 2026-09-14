# Alignment parsers

These modules read alignment-related formats and return validated in-memory data:

- [`bam.py`](bam.py): BAM/BAI and SAM headers for Steps `01`, `02`, `04`, `05`, and `06` validators.
- [`bed.py`](bed.py): BED12 for the Step `00b` validator only.
- [`orientation.py`](orientation.py): mechanical-orientation labels and counts
  for scientific contracts, validators, and artifact indexing.
- [`star.py`](star.py): STAR outputs for Steps `00a` and `01` validation and artifact indexing.

Callers choose checks and interpret evidence; these parsers run no scientific
tools and publish no output. [SOURCE_TOPOLOGY](../../contracts/SOURCE_TOPOLOGY.md)
defines permitted consumers. [BAM tests](../../../../tests/libraries/test_bam_validation.py)
and [format tests](../../../../tests/libraries/test_shared_domain_helpers.py) check their behavior.
