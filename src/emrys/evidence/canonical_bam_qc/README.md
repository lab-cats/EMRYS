# `collect_canonical_BAM_QC_evidence` owner

Operation `02b` runs samtools quickcheck and flagstat on one BAM, keeping native
text evidence for validation and reporting. It does not change the BAM or gate
later computation. An adjacent BAI is required for admission but neither tool
command uses or validates it.

Supply the sample ID, BAM/BAI, output directory, and samtools. Outputs are
`<sample>.quickcheck.txt` and `<sample>.flagstat.txt`. The validator checks those
texts without receiving the original BAM, BAI, or tool identity.

The normal Run uses this operation automatically. For standalone help from
the checkout root:

```bash
bash src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh --help
emrys validate canonical-bam-qc --help
```

The Run uses `--no-clobber`; direct execute without it can overwrite files and
leave mixed or partial evidence. The [contract](CONTRACT.md) documents both
routes and the quickcheck producer/validator mismatch. Passing rows do not
prove sample identity, alignment correctness, or biological validity.
