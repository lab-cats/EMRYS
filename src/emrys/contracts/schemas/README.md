# Contract schemas

These packaged JSON Schema files belong to the
[artifact](../artifacts/README.md) and [orchestration](../orchestration/README.md)
contracts. Each owner registers and validates its resources; this directory
provides no separate validator.

## Version and identity rules

EMRYS schema IDs are exact identities, not aliases for earlier NORAD IDs.
Historical records require their own registered schema. Each registered `$id`
occupies one packaged file, with local `$defs` where useful. Splitting, replacing,
or regenerating a schema to satisfy a consumer or test changes a contract and
requires explicit version and consumer review. Version directories are part of
packaging and reference resolution, not an arbitrary documentation split.

The [artifact index](artifacts/README.md) lists resources across v1–v5; the
[orchestration index](orchestration/README.md) lists its mixed-version records.
