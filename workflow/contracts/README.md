# Reviewed workflow projection contracts

This directory contains checked-in processing-profile bases. The current
[`local_cmh_v2.json`](local_cmh_v2.json) maps the common canonical semantic
owners through Step `08`. Planning composes it with exactly one admitted
analysis-module descriptor; the checked-in file is not a provider registry or
complete immutable Run profile by itself.

At a high level, the base fixes common owners, scope expansion, direct
dependency projection, and required evidence leaves. Project admission loads
the selected installed module, planning composes its typed inputs/outputs and
one Step `09` plus optional Step `10`, and materialization publishes the exact
canonical result into the Run. Task, inspection, artifact indexing, and
Snakefile admission use that exact bound profile.

This directory does not own JSON schemas, canonical serialization, semantic
owner identity, stage behavior, request values, or scheduler settings. Exact
field validation belongs to the
[`contracts/orchestration`](../../src/emrys/contracts/orchestration/README.md)
owner and its profile schema; the semantic graph belongs to
[`STAGE_MAP.md`](../../src/emrys/contracts/STAGE_MAP.md). The parent
[`workflow README`](../README.md) explains how the instance enters execution.

Adding or changing a checked-in base changes the common workflow surface and
requires explicit approval. Adding an installed module instead follows the
bounded `emrys.analysis_modules` contract and does not edit this directory;
normalization, materialization, Snakefile parity, task/inspection admission,
and descriptor-derived reporting inventory remain enforced.
