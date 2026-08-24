# Internal libraries

This package owns neutral implementation shared by multiple functional owners.
Stage-specific arguments, check rosters, evidence meaning, and scientific policy
remain beside their stage or evidence owner.

## Owners

- [`validation/`](validation/README.md) owns validation errors, snapshots,
  report rows/schema, transactional publication, and shared runtime lifecycle.
- [`alignments/`](alignments/) owns neutral BAM, BED12, mechanical-orientation,
  and STAR-format helpers.
- [`evidence/`](evidence/) owns neutral evidence-file parsers.
- [`quality/`](quality/) owns neutral quality-metric parsers.
- [`references/`](references/) owns ordered reference-contig parsers.
- [`source_authority.py`](source_authority.py) owns the distinct admitted
  `SourceCheckout` and `ArtifactSourceRoot` values. Checkout inspection binds
  executing Python, packaged schemas/report resources, exact Git HEAD, and
  full tracked/untracked cleanliness through explicit immutable Git-operation
  dependencies. The artifact root independently resolves contract-relative
  native and reporting paths.
- [`process_environment.py`](process_environment.py) owns sanitized child
  startup, the guarded existing-library R selector, and canonical selected-Java
  GATK environment. It does not choose tool versions or scientific commands.
- [`gatk_invocation.sh`](gatk_invocation.sh) is the narrow Step `00c`/`05`
  bridge from one bound absolute Python 3.11+ launcher to that selected-Java
  authority.
- [`installed_package_identity.py`](installed_package_identity.py) owns the
  deterministic no-follow digest of one canonical installed R-package tree;
  namespace/version policy stays with runtime admission.
- [`input_contract.R`](input_contract.R) owns neutral named-argument, file,
  hash, and TSV mechanics
  shared by the Step `08`, Step `09`, and scientific-context R programs; owner
  rosters and policies remain local.
- Root shell assets own bounded argument, file, executable, orientation,
  signal, and trap mechanics used by named consumers; they are not a general
  utility framework.

Known snapshot and publication-recovery gaps remain characterized. Container,
header, or report-shape checks do not become scientific or biological
validation.

Direct behavior tests live in:

- [`test_validation_report.py`](../../../tests/libraries/test_validation_report.py)
- [`test_bam_validation.py`](../../../tests/libraries/test_bam_validation.py)
- [`test_reference_contigs.py`](../../../tests/libraries/test_reference_contigs.py)
- [`test_executable_resolution.py`](../../../tests/libraries/test_executable_resolution.py)
- [`test_shared_domain_helpers.py`](../../../tests/libraries/test_shared_domain_helpers.py)
- [`test_source_authority.py`](../../../tests/libraries/test_source_authority.py)
- [`test_installed_package_identity.py`](../../../tests/libraries/test_installed_package_identity.py)
