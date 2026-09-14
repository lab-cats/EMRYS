# Sample-manifest checks

`emrys validate manifest` checks a declared manifest without writing a normalized
copy or receipt. Required columns are `sample_id`, `r1_fastq`, `r2_fastq`,
`strandedness`, and `condition`; `notes` and `replicate` are optional. It rejects
empty manifests or identities, duplicate identities, malformed rows, and
strandedness values outside `forward`, `reverse`, `unstranded`, and `unknown`.
`--check-files` also checks that paths exist relative to `--base-dir`.

[`check_fastq_pairs.sh`](check_fastq_pairs.sh) reads one plain or gzip FASTQ pair.
It compares record counts and a requested number of leading, normalized read
IDs, writes nothing, and does not prove complete pairing, sequence/quality
integrity, sample identity, or provenance.

The separate `emrys init manifests` Project command requires `replicate` and
uses the downstream scientific contracts for input checks. Neither interface
chooses analysis policy, freezes a Run, executes a stage, or establishes
production readiness, scientific review, or biological validity.

## FASTQ byte and diagnostic boundary

An earlier local single-pass draft changed accepted input: for paired headers
`@re<NUL>ad/1` and `@read/2`, where `<NUL>` is a zero byte, the existing helper
succeeded. The system-`awk` draft truncated the first ID to `re` and failed the
pair; it was not published. Any replacement must preserve byte handling, shell
diagnostics, complete record counts, decompression failures, and the deliberately
limited prefix comparison.

At the audited default of 20 prefix IDs, counting plus per-ID scans makes
21 logical passes per mate. This is a source-derived count, not a physical I/O
measurement. The helper is outside the normal DAG; optimizing it cannot count
as pipeline savings unless the measured operator journey includes it.
