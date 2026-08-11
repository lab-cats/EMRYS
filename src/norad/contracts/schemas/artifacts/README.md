# Artifact schema versions

This directory groups public artifact-contract schemas by version. Each version
is a distribution and reference-resolution boundary, not a documentation-only
folder split.

- [`v1/`](v1/) — the current version `1.0.0` schema resources.

Schema registration and validation remain owned by the
[`artifacts` contract](../../artifacts/README.md). A future version requires an
explicit contract and consumer change rather than an in-place rewrite.
