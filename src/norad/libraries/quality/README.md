# Quality-format libraries

This package contains neutral quality-metric parsers. Its current
[`picard.py`](picard.py) module parses Picard duplication metrics without owning
duplicate-marking policy, tool execution, validation rosters, or evidence
claims.

The Step `04`
[`mark_BAM_duplicates_with_Picard`](../../stages/mark_BAM_duplicates_with_Picard/README.md)
owner retains those semantics. Direct parser protection is in
[`test_shared_domain_helpers.py`](../../../../tests/libraries/test_shared_domain_helpers.py).
