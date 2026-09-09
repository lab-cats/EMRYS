# Reference parsers

[`contigs.py`](contigs.py) reads ordered contig names and lengths from FASTA,
FAI, and sequence dictionaries. It selects or repairs no reference and publishes
no evidence. Reference provenance and stage validators decide whether the
parsed references agree.

[Tests](../../../../tests/libraries/test_reference_contigs.py) check parsing;
[SOURCE_TOPOLOGY](../../contracts/SOURCE_TOPOLOGY.md#approved-shared-seams) lists
permitted consumers.
