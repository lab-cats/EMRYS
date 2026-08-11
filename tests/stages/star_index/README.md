# STAR-index stage tests

This directory protects the Step 00a scheduler-owned producer and explicit
validator, including caller-working-directory behavior and mocked job output.
The [stage owner](../../../src/norad/stages/star_index/README.md) owns
the exact submission command, fixed inputs, known defects, and evidence limit.

Mocked-job and fixture validation do not establish real STAR indexing,
scheduler execution, cluster execution, or production reference readiness.
