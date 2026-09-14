# Evidence-file parsers

[`qc.py`](qc.py) reads samtools flagstat counts and fraction reports for
[BAM QC](../../evidence/canonical_bam_qc/README.md) and
[RSeQC orientation](../../evidence/rseqc_orientation/README.md). Those owners
choose checks, interpret evidence, and publish results. Parsing alone establishes
no sample identity.
[Format tests](../../../../tests/libraries/test_shared_domain_helpers.py) check parsing.
