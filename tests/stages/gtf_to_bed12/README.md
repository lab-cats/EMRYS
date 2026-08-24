# GTF-to-BED12 stage tests

This directory protects the Step 00b Python conversion rules, validator, and
mocked scheduler behavior. Producer coverage includes side-effect-free dry-run,
arbitrary-CWD execution, create-exclusive publication, controlled rollback,
no-clobber behavior, and interruption-residue blocking. Scheduler coverage
retains its later bedtools partial-publication characterization. The
[stage owner](../../../src/norad/stages/gtf_to_bed12/README.md) owns
commands, recovery guidance, and exact evidence limits.

Synthetic GTF/BED inputs and mocked jobs do not establish scheduler, cluster,
production, scientific-review, or biological evidence.
