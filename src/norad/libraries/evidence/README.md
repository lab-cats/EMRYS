# Evidence-format libraries

This package contains neutral parsers for evidence-style files. Its current
[`qc.py`](qc.py) module parses samtools flagstat counts and fraction reports; it
does not decide evidence state, sample identity, scientific meaning, or
publication.

The
[`canonical-BAM QC`](../../evidence/canonical_bam_qc/README.md)
and
[`RSeQC orientation`](../../evidence/rseqc_orientation/README.md)
evidence owners consume these helpers and retain their own contracts. Direct
neutral protection is in
[`test_shared_domain_helpers.py`](../../../../tests/libraries/test_shared_domain_helpers.py).
