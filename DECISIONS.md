# Decisions

## TSV is the canonical manifest format

Reason: simple, robust with file paths, easy to parse in Python/R/shell, avoids CSV quoting issues.

## STAR wrapper is dry-run by default

Reason: prevents accidental large jobs and makes command construction testable.

## Picard is invoked through `$PICARD`

Reason: CSU exposes Picard as a jar path through the `picard/3.1.1` module rather than a `picard` executable.

## SLURM jobs export `TMPDIR=/tmp`

Reason: CSU default `/local/tmp` was not writable on compute node `node004`.