# RSeQC orientation-evidence tests

This directory protects the Step 03 producer and validator through shell cases
and Python report checks. The
[production owner](../../../src/norad/evidence/rseqc_orientation/README.md)
defines supported commands, publication hazards, and the mechanical-evidence
boundary.

Python tests invoke the grouped `python -I -m norad validate rseqc-orientation`
route; the owner's `validator.py` is private.

Mocked or fixture fractions do not establish real RSeQC execution, transcript
strand, sense/antisense assignment, approved manifest policy, scheduler
behavior, or cluster evidence.
