# `collect_canonical_BAM_QC_evidence` owner

Operation `02b` runs samtools quickcheck and flagstat on one BAM, keeping native
text evidence for validation and reporting. It does not change the BAM or gate
later computation. An adjacent BAI is required for admission but neither tool
command uses or validates it.

Supply the sample ID, BAM/BAI, output directory, and samtools. Outputs are
`<sample>.quickcheck.txt` and `<sample>.flagstat.txt`. The validator checks those
texts without receiving the original BAM, BAI, or tool identity.

The Run includes this operation. The shell script is an internal worker;
its help describes that interface. The validator remains directly available:

```bash
bash src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh --help
emrys validate canonical-bam-qc --help
```

The [contract](CONTRACT.md) documents the quickcheck producer/validator
mismatch. Passing rows do not
prove sample identity, alignment correctness, or biological validity.
