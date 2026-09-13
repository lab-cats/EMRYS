# Contract schemas

These packaged JSON Schema files belong to the
[artifact](../artifacts/README.md) and [orchestration](../orchestration/README.md)
contracts. Each owner registers and validates its resources; this directory
provides no separate validator.

## Version and identity rules

EMRYS schema IDs are exact identities, not aliases for earlier NORAD IDs.
Only current formats are registered under the [version policy](../../../../docs/design/decisions/platform-direction.md#version-support).
Keep the packaged directories: their numbers span unrelated contract families
and participate in resource paths and references. They are not instructions to
support obsolete records or rename files for visual consistency. Each `$id`
occupies one file, with local `$defs` where useful. Change a format only after
reviewing its writers, readers and references together.

The [artifact index](artifacts/README.md) and
[orchestration index](orchestration/README.md) list their current registered formats.
