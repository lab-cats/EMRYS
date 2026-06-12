# Pending test plan for Step 04 duplicate marking.
#
# Documentation scaffold only. Do not add this file to Makefile or shell-test.
#
# Future tests should verify:
# - required sorted BAM input is validated before running Picard
# - duplicate-marked BAM and metrics output names are deterministic
# - dry-run output prints the Picard MarkDuplicates command safely
# - missing tools or inputs fail with clear messages
