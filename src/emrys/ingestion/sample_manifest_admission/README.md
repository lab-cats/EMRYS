# Sample-manifest admission owner

`emrys validate manifest` requires `sample_id`, `r1_fastq`, `r2_fastq`,
`strandedness`, and `condition`; only `notes` and `replicate` are optional.
It rejects duplicate/empty identities, malformed rows, empty manifests, and
strandedness outside `forward`, `reverse`, `unstranded`, and `unknown`.
`--check-files` additionally checks path existence relative to `--base-dir`.
The command publishes no normalized manifest or receipt.

[`check_fastq_pairs.sh`](check_fastq_pairs.sh) checks one plain or gzip FASTQ
pair for record-count agreement and a requested number of leading normalized
read IDs. It writes nothing and does not prove full pairing, sequence/quality
integrity, sample identity, or provenance. The stricter `emrys init manifests`
Project route requires `replicate` and delegates scientific admission to the
current downstream contracts.

Neither interface discovers or acquires inputs, chooses policy, freezes a Run,
executes a stage, or establishes production, scientific, or biological state.
