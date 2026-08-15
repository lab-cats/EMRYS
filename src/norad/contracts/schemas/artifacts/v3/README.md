# Artifact schemas v3

This directory contains the registered version 3
[`report_receipt`](report_receipt.schema.json) schema for one self-contained
Jinja HTML report transaction. It records the fixed computational evidence
boundary and contains no scientific-review or approval state.

The schema resolves shared path, hash, issue, and provenance definitions from
the packaged [`common` v1 resource](../v1/common.schema.json). The
[`artifact-contract owner`](../../../artifacts/README.md) defines its supported
validation behavior and direct tests.

Do not rewrite this schema in place merely to satisfy tests; any accepted
change requires explicit version and consumer review.
