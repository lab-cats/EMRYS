# `convert_GTF_to_BED12` owner

Stage `00b` converts one admitted GTF into the canonical BED12 artifact.
`emrys convert gtf-to-bed12` and `emrys validate bed12` are implemented by the
private [`converter.py`](converter.py) and [`validator.py`](validator.py).

[`CONTRACT.md`](CONTRACT.md) owns the exact conversion, input/output,
transaction, recovery, validation, and evidence semantics. Normal execution
belongs to the immutable `emrys run`/`resume` journey. This stage does not
select, repair, or biologically validate a reference.
