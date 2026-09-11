# GTF-to-BED12 tests

These cases check the Run worker's Step 00b conversion and the BED12 validator
using synthetic GTF/BED files. They cover coordinates, exon grouping, names,
ordering, rejected rows and transcripts, and source-GTF agreement. The
[stage contract](../../../src/emrys/stages/gtf_to_bed12/CONTRACT.md)
defines scientific behavior; runner tests cover publication and recovery.
