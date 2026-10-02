# Quality-metric parsers

[`picard.py`](picard.py) parses Picard duplication metrics. The
[duplicate-marking owner](../../stages/duplicate_marking/README.md) runs Picard,
chooses validation checks, and interprets the result. This parser does none of
those operations; [format tests](../../../../tests/libraries/test_shared_domain_helpers.py)
check the data it returns.

Both the duplicate-marking validator and artifact reporting use the same
first-table reader: literal tab-separated, unique column names, the four required
Picard columns in any order, and exactly one data row before a blank/comment
separator. Leading comments are allowed; an arbitrary noncomment prefix is not.
Later tables such as histograms are not interpreted. The reader consumes the full
input, so reporting still applies its UTF-8/NUL/CR checks to trailing text.

The validator retains its nonempty-library, pair-count and finite-fraction bounds,
and publishes malformed metrics as failed evidence. Reporting retains its own
text admission and projects numeric fields as `not_assessed`; it does not rerun
Picard or turn projected values into scientific validation. After successful
numeric conversion, reporting refuses distinct columns that share a lowercase
key; blank or nonnumeric fields remain omitted. The existing reserved
`source_row_count` omission and later punctuation normalization are unchanged.
The generic strict TSV reader uses CSV quoting and one-table framing, so it is
not a substitute for Picard's existing literal-tab, multi-table format.
