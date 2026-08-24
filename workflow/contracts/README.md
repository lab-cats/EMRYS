# Reviewed workflow projection contracts

This directory contains checked-in contract instances that select a supported,
fixed EMRYS workflow projection. The current
[`local_cmh_v2.json`](local_cmh_v2.json) maps canonical semantic owners into the
automatic local-pilot graph and declares the native artifacts expected by
reporting.

At a high level, the instance fixes the owner roster, scope expansion, direct
dependency projection, required evidence leaves, and deterministic artifact
inventory. Request normalization admits it, materialization publishes its
canonical bytes into the run, and task, inspection, and Snakefile admission use
that exact bound profile.

This directory does not own JSON schemas, canonical serialization, semantic
owner identity, stage behavior, request values, or scheduler settings. Exact
field validation belongs to the
[`contracts/orchestration`](../../src/emrys/contracts/orchestration/README.md)
owner and its profile schema; the semantic graph belongs to
[`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md). The parent
[`workflow README`](../README.md) explains how the instance enters execution.

Adding or changing a projection instance changes supported workflow surface.
It requires explicit approval and review of normalization, materialization,
Snakefile parity, task/inspection admission, and reporting inventory consumers.

