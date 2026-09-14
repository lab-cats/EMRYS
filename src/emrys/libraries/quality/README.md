# Quality-metric parsers

[`picard.py`](picard.py) parses Picard duplication metrics. The
[duplicate-marking owner](../../stages/duplicate_marking/README.md) runs Picard,
chooses validation checks, and interprets the result. This parser does none of
those operations; [format tests](../../../../tests/libraries/test_shared_domain_helpers.py)
check the data it returns.
