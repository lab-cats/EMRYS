# Artifact schemas v3

This directory contains two independently versioned resources. The active
[`run_summary`](run_summary.schema.json) v3 is the module-neutral summary used
by explicitly selected analysis modules; its analysis-policy binding is path,
SHA-256, and size rather than paired-CMH candidate fields. The frozen
historical [`report_receipt`](report_receipt.schema.json) v3 records the former
single self-contained Jinja HTML transaction. It contains no scientific-review
or approval state and is not an alias or migration route to v4 or v5.

The schema resolves shared path, hash, issue, and provenance definitions from
the packaged [`common` v1 resource](../v1/common.schema.json). The
[`artifact-contract owner`](../../../artifacts/README.md) defines its supported
validation behavior and direct tests.

Do not rewrite this schema in place merely to satisfy tests; any accepted
change requires explicit version and consumer review.
