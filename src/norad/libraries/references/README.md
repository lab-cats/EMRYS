# Reference-format libraries

This package contains neutral reference-format parsers. Its current
[`contigs.py`](contigs.py) module reads ordered FASTA, FAI, and sequence-dictionary
contig/length identities without selecting a reference, repairing files, or
publishing evidence.

Reference provenance and the applicable stage validators retain agreement and
evidence policy. Direct protection lives in
[`test_reference_contigs.py`](../../../../tests/libraries/test_reference_contigs.py);
approved consumers are bounded by
[`SOURCE_TOPOLOGY.md`](../../contracts/SOURCE_TOPOLOGY.md#approved-shared-seams).
