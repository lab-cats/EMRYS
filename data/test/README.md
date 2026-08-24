# Local test-data workspace

This directory is a tracked placeholder for tiny, non-sensitive local input
material. No committed file here currently forms a runnable fixture.

The structural [`samples.example.tsv`](../../configs/samples.example.tsv)
names paths under this directory without requiring them to exist. The
[Step `01` owner](../../src/emrys/stages/star_alignment/README.md)
uses only the `sample_001` mate paths as default dry-run placeholders.

FASTQ patterns remain ignored repository-wide. File presence here establishes
neither provenance, admission, runtime execution, nor production evidence. Do
not delete nonempty local contents without applying the parent
[`data/` retention rules](../README.md#retention-and-cleanup).
