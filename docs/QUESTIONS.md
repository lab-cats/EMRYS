# Open questions

- No visible `gatk` module found with `module avail gatk`.
- Need to ask whether GATK is installed elsewhere, should be installed in a project environment, or should be run via jar/container/conda.

## Cluster

- What is the correct login node?
- Is VPN required?
- What are the exact module names for STAR, samtools, Picard, GATK, R, Python?
- Where should full data live: home, scratch, or project storage?
- What are storage quotas?
- What partition/account should jobs use?

## Reference files

- Genome build?
- Annotation version?
- STAR index path?
- FASTA path?
- GTF/GFF path?

## Sequencing data

- Paired-end or single-end?
- Strandedness?
- Read length?
- Sample manifest source?
- Naming convention?

## Pipeline

- Which steps are already done?
- Which steps need to be reproduced?
- Expected final deliverables?
