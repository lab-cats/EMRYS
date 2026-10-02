# Cohort-candidate preprocessing tests

These cases check direct R computation, exact upstream receipt/VCF bindings,
serialized output checks, and validation through the grouped command. Shared runner tests
cover publication and recovery. The
[stage contract](../../../src/emrys/stages/cohort_candidate_preprocessing/CONTRACT.md)
defines the provisional orientation policy. The guarded R fixture also checks
interval reduction and derived UTR ranges against explicit expected coordinates.

The guarded-R runner may skip without a suitable runtime; a skip proves no R
execution. Local candidates are not validated variants or editing sites.

## Independent computational reference

`step_08_reference.py` derives the full scientific sites rows and per-input /
aggregate counts from the tiny raw VCF, sample/partition manifests and GTF.
It uses standard-library parsing and finite point sets (coordinates 1–10000),
not EMRYS helpers, VariantAnnotation or IRanges. It accepts canonical fixture
feature names and simple INFO/AD fields, not the full VCF/GTF dialect. It is a
fixture reference, not another supported parser. Its Python tests bind expectations to literal
rows, refuse production imports, and reject coordinated count/AF corruption,
wrong alleles/annotations, reordered rows/sample headers and false totals.

The existing real-R runner compares the positive, disjoint-chromosome and
reversed-manifest/overlapping-annotation cases against this reference. Together
these cover multiallelic AD/INFO selection, symbolic/non-SNV omission, missing
counts, both provisional orientation mappings, unannotated loci, transcript
span membership, separate overlapping feature flags, explicit and derived UTRs,
and sample/partition/orientation/candidate ordering. The reordered case also
checks zero depth and generic UTRs against real R. The original literal R assertions and
worker-count byte comparisons remain independent additional defenses.

Every sites column, discrete count, ID, flag and order is compared exactly;
AF uses relative tolerance `1e-12` and absolute tolerance `1e-15` for decimal TSV
serialization. The reference then invokes the existing public Python validator
with `--step07-root` against those same native R outputs and real fixture
receipts/VCFs, requiring the exact five check IDs and all-pass rows. This consumer
check does not provide any reference expectations. The shell runner uses the
existing `REPORT_PYTHON_BIN`, defaulting to `.venv/bin/python`; it installs nothing.

SCI-ORACLE-01 is computational contract verification. Changes to expectations
require independent computational review; disagreement with production is a
characterized finding, not permission to change the algorithm or its oracle.
No-CDS UTR behavior follows the existing computation, not a new biological
policy. A non-skipped exact-source guarded-R result is required before claiming the
R/reference comparison passed. These fixtures do not supply independent
scientific review, institutional proof or biological interpretation; provisional
orientation remains provisional. SCI-AUDIT-01 is separate.

Computational reviewers on 2026-10-02: Codex `docs_branch_comparison`
(author), `integration_policy_review` (independent contract/fixture review),
and the primary integration reviewer. Their authority covers source and test
consistency; it does not substitute for an identified scientific reviewer.
