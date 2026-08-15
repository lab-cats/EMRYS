# Contract tests

This directory owns direct protection for neutral public contracts shared
across workflow owners.

- [`artifacts/`](artifacts/README.md) protects versioned artifact schemas,
  semantic validation, fixtures, and inventory compatibility.
- [`scientific_evidence/`](scientific_evidence/README.md) protects neutral Step
  08 and Step 09 computational APIs and behavior.

Production identities and dependency direction remain with the
[contract owners](../../src/norad/contracts/README.md). Independent literal
expectations that compare multiple owners remain under
[`../contract_integration/`](../contract_integration/README.md).
