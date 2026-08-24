# Canonical-BAM QC evidence tests

This directory protects the Step 02b producer and validator through shell
cases and Python report checks. The
[production owner](../../../src/norad/evidence/canonical_bam_qc/README.md)
defines supported commands, mixed-attempt hazards, and evidence meaning. The
Python tests invoke the grouped `python -I -m norad validate canonical-bam-qc`
route; `validator.py` is a private implementation module.

Local fixtures and mocked tools do not establish real samtools, scheduler,
cluster, production, scientific-review, or biological evidence.
