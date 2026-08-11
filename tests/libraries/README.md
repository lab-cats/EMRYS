# Shared-library tests

This directory owns direct tests for neutral helpers shared by multiple
workflow owners, including validation reports and inputs, BAM and reference
checks, executable resolution, and shell file checks. The corresponding
implementation domains are routed by the
[library README](../../src/norad/libraries/README.md).

Consumer transaction and recovery suites remain responsible for their own
end-to-end semantics. Passing a neutral-helper test does not extend the helper
beyond its documented contract or promote scientific evidence.
