# Artifact schema versions

Active artifact schemas span several versions, all registered by the
[artifact contract](../../artifacts/README.md):

- [`v1/`](v1/README.md): shared definitions.
- [`v2/`](v2/README.md): artifact records and flat paired-CMH run summaries.
- [`v3/`](v3/README.md): module-neutral run summaries and the frozen historical single-HTML receipt.
- [`v4/`](v4/README.md): flat paired-CMH receipts for scientific HTML, evidence HTML, and summary TSV.
- [`v5/`](v5/README.md): explicit-module receipts, attributing computation provider,
  scientific reporter, and fixed core renderer separately.

Each directory participates in packaging and local reference resolution. Follow
the common [version and identity rules](../README.md#version-and-identity-rules)
before changing a resource or its consumers.
