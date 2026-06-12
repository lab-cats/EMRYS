# Pending test plan for Step 06 BAM orientation splitting.
#
# Documentation scaffold only. Do not add this file to Makefile or shell-test.
#
# Future tests should verify:
# - split-N-cigar BAM input is validated before running samtools
# - FWD/REV output BAM and index names are deterministic
# - SAM flag grouping is documented and covered by tiny fixtures
# - dry-run output prints all samtools commands safely
