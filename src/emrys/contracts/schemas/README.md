# Contract schemas

This directory stores the versioned JSON Schema resources registered by the
[`artifacts`](../artifacts/README.md) and
[`orchestration`](../orchestration/README.md) contract owners. It is packaged
storage, not an independent registry or validator.

Artifact resources span v1–v5; orchestration uses its registered mixed-version
Project, profile, execution, Attempt, task, receipt, and reporting records.
EMRYS schema IDs are hard identities, not aliases for pre-cutover NORAD IDs.
Historical records require the exact registry that owns them; schemas are not
rewritten in place merely to satisfy a consumer or test.
