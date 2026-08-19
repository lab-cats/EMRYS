# Local STAR-index fixture path

This directory preserves the ignored local STAR-index path used by the Step
`01` owner-local scheduler-entry-point dry-run contract. The tracked README is
not a valid STAR index and supplies no runtime, cluster, scientific, or
biological evidence.

[`step_01_star_align.slurm`](../../src/norad/stages/star_alignment/step_01_star_align.slurm)
may create placeholder FASTQs and one deliberately invalid `Genome` member for
its default dry run; it does not produce a usable index or native stage output.
Execute mode rejects that placeholder set. Operators must supply and inspect a
real index and real inputs before execution. Keep this fixture distinct from
production references, and do not commit generated STAR data here. The
[owner README](../../src/norad/stages/star_alignment/README.md) orients use;
its [contract](../../src/norad/stages/star_alignment/CONTRACT.md) owns exact
inputs, outputs, and failure behavior.
