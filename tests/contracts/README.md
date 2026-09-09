# Contract tests

These suites test shared data contracts directly:

- [Artifacts](artifacts/README.md): versioned schemas, semantic validation,
  fixtures, and inventory compatibility.
- [Orchestration](orchestration/README.md): request, profile, execution, Attempt,
  task, and reporting records, including canonical JSON and derived summaries.
- [Scientific evidence](scientific_evidence/README.md): Step 08, Step 09, and
  scientific-context data formats and validation.

The [contract owners](../../src/emrys/contracts/README.md) define production
behavior. [Cross-owner tests](../contract_integration/README.md) keep independent
literal expectations for agreement between producers and consumers.
