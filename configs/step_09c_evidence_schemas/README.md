# Step 09c evidence schema references

This directory contains thirteen header-only TSV references for the declared
scientific-review evidence categories accepted by Step `09c`. They are
structural examples, not JSON Schemas, selected evidence, a completed review,
or biological-readiness authority.

The neutral
[`review_package.py`](../../src/norad/contracts/scientific_evidence/review_package.py)
owns the public category roster, headers, and vocabularies. The
[Step `09c` evidence owner](../../src/norad/evidence/assemble_scientific_review_evidence_package/README.md)
owns input, review-policy, validation, and publication behavior.

Every tracked `*.schema.tsv` file is checked against that public contract by
[`test_step_09c_scientific_validation.py`](../../tests/evidence/assemble_scientific_review_evidence_package/test_step_09c_scientific_validation.py).
The parent [`configs/README.md`](../README.md) owns their placement in the public
input catalog.
