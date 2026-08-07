# Internal libraries

This package owns neutral implementation shared by multiple functional owners.
Stage-specific arguments, check rosters, evidence meaning, and scientific policy
remain beside their stage or evidence owner.

## Modules

- `validation/` owns validation errors, input snapshots, report rows and schema
  validation, transactional publication, and the shared dry-run/execute
  lifecycle. Validators import the stable facade from
  `norad.libraries.validation`.
- `alignments/bam.py` owns only `run_tool` and `parse_header`, shared by the
  Step `02`, `04`, and `05` validators.
- `references/contigs.py` owns `ReferenceContigError` and the ordered
  `parse_fasta`, `parse_fai`, and `parse_dict` APIs used by reference provenance
  and the Step `00c` and `05` validators.
- `executable_resolution.sh` owns the three-argument
  `resolve_executable_value(label, value, default_name)` Bash function used by
  selected producers. It remains shell infrastructure rather than Python
  package code.

The extraction preserves characterized behavior, including known snapshot and
publication-recovery gaps. It does not turn container, header, or report-shape
checks into scientific or biological validation.

Direct behavior tests live in:

- [`test_validation_report.py`](../../../tests/libraries/test_validation_report.py)
- [`test_bam_validation.py`](../../../tests/libraries/test_bam_validation.py)
- [`test_reference_contigs.py`](../../../tests/libraries/test_reference_contigs.py)
- [`test_executable_resolution.py`](../../../tests/libraries/test_executable_resolution.py)
