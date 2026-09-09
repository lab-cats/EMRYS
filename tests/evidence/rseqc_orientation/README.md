# RSeQC orientation tests

Shell cases check the Step 03 producer; Python cases check its reports through
`python -I -m emrys validate rseqc-orientation`. The private `validator.py` is
not a separate command. The [owner contract](../../../src/emrys/evidence/rseqc_orientation/CONTRACT.md)
defines publication and the meaning of its mechanical-orientation evidence.

Fixture fractions do not establish transcript strand, sense/antisense assignment,
or an approved manifest policy. Mocked tools also have the
[shared evidence limits](../../README.md#evidence-limits).
