# Scientific-evidence contract tests

This directory protects the neutral Step 08, Step 09, and review-package
contracts: public identities, literal headers and vocabularies, parsing and
reconciliation behavior, status reduction, and rejection paths. The
[scientific-evidence owner](../../../src/norad/contracts/scientific_evidence/README.md)
defines the corresponding production boundaries.

These tests intentionally exclude pipeline computation, review policy,
artifact publication, and independent statistical oracles. Their synthetic
evidence does not establish runtime completion, scientific review, or
biological interpretation.
