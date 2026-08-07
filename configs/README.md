# Configuration and input catalog

This directory holds explicit public inputs, structural examples, operator
selections, and reference tables that callers receive as files. It is not one
configuration system: there is no universal loader, implicit discovery rule,
or executable orchestrator for the whole directory.

## Catalog

| Area | Audience | Placement and ownership | State | Tracked inputs |
| --- | --- | --- | --- | --- |
| Deferred workflow profiles | Maintainers and future workflow operators | Neutral, shared future-orchestration inputs; no current functional owner or reader | Deferred; illustrative only, with no supported execution semantics | [`cluster_full.yaml.example`](cluster_full.yaml.example), [`local_test.yaml`](local_test.yaml) |
| Sample-manifest starter | Operators | Public, single-owner input for [sample-manifest admission](../src/norad/ingestion/sample_manifest_admission/README.md) | Current structural starter; schema-checked without FASTQ existence checks, not a runnable fixture | [`samples.example.tsv`](samples.example.tsv) |
| Artifact and report projection | Operators and report developers | Public reporting inputs; the inventory is also accepted by the [neutral artifact-contract validator](../src/norad/contracts/artifacts/validate_artifact_contracts.py) | Current shared structural examples; not production inventory, run contract, approval, or report | [`artifact_inventory.example.tsv`](artifact_inventory.example.tsv), [`artifact_run_contract.example.json`](artifact_run_contract.example.json), [`report_table_approvals.example.tsv`](report_table_approvals.example.tsv) |
| Reference provenance | Operators | Public, single-owner input for [reference-provenance evidence](../src/norad/evidence/reference_provenance/README.md) | Current structural starter; illustrative identity and hashes must be replaced | [`reference_provenance.example.tsv`](reference_provenance.example.tsv) |
| Runtime availability | Operators | Public, single-owner input for [runtime-preflight evidence](../src/norad/evidence/runtime_preflight/README.md) | Current structural starter; illustrative probes establish no availability | [`runtime_preflight.example.tsv`](runtime_preflight.example.tsv) |
| Storage and retention state | Operators and approvers | Public, single-owner inputs for [storage-inventory evidence](../src/norad/evidence/storage_inventory/README.md) | Current structural starters; they record state and approval but execute no retention action | [`storage_roots.example.tsv`](storage_roots.example.tsv), [`retention_policy.example.tsv`](retention_policy.example.tsv) |
| Step `07` partition selection | Operators | Public, single-owner inputs for the [Step `07` stage](../src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/README.md) | Current example, pilot, and 25-selector reference; runtime-reference agreement remains unproved | [`step_07_partitions.example.tsv`](step_07_partitions.example.tsv), [`step_07_partitions.pilot.tsv`](step_07_partitions.pilot.tsv), [`step_07_partitions.primary_contigs.tsv`](step_07_partitions.primary_contigs.tsv) |
| Step `09` pairing | Operators | Public, single-owner reference for the [Step `09` analysis](../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/README.md) | Current reference-only pairing; not a runtime overlay or result | [`step_09_pairs.NORAD_EV_PUM1.tsv`](step_09_pairs.NORAD_EV_PUM1.tsv) |
| Step `09c` scientific-review inputs | Operators and reviewers | Public shared references for the [Step `09c` evidence owner](../src/norad/evidence/assemble_scientific_review_evidence_package/README.md) and [neutral review-package contract](../src/norad/contracts/scientific_evidence/review_package.py) | Current structural references; not selected evidence, completed review, or biological-readiness authority | [`step_09c_review_plan.example.tsv`](step_09c_review_plan.example.tsv), [`step_09c_evidence_manifest.example.tsv`](step_09c_evidence_manifest.example.tsv), and the thirteen schema references listed below |

The thirteen Step `09c` schema-reference tables are header-only structural
references for declared review evidence. The neutral review-package contract
owns the public roster, headers, and vocabularies; the evidence owner retains
input, publication, and review-policy behavior:

- [`annotation_audit.schema.tsv`](step_09c_evidence_schemas/annotation_audit.schema.tsv)
- [`candidate_adjudication.schema.tsv`](step_09c_evidence_schemas/candidate_adjudication.schema.tsv)
- [`candidate_selection.schema.tsv`](step_09c_evidence_schemas/candidate_selection.schema.tsv)
- [`computational_validation.schema.tsv`](step_09c_evidence_schemas/computational_validation.schema.tsv)
- [`decisions.schema.tsv`](step_09c_evidence_schemas/decisions.schema.tsv)
- [`evidence_index.schema.tsv`](step_09c_evidence_schemas/evidence_index.schema.tsv)
- [`leave_one_pair_out.schema.tsv`](step_09c_evidence_schemas/leave_one_pair_out.schema.tsv)
- [`limitations.schema.tsv`](step_09c_evidence_schemas/limitations.schema.tsv)
- [`orientation_locus_audit.schema.tsv`](step_09c_evidence_schemas/orientation_locus_audit.schema.tsv)
- [`qc_funnel.schema.tsv`](step_09c_evidence_schemas/qc_funnel.schema.tsv)
- [`replicate_effects.schema.tsv`](step_09c_evidence_schemas/replicate_effects.schema.tsv)
- [`review_summary.schema.tsv`](step_09c_evidence_schemas/review_summary.schema.tsv)
- [`sensitivity_matrix.schema.tsv`](step_09c_evidence_schemas/sensitivity_matrix.schema.tsv)

## Authority and use

This catalog defines no file schema, default, validation behavior, selection,
or evidence authority. Each group routes to its implemented owner, neutral
contract, or explicit deferred disposition. The deferred profiles have no
supported execution semantics, and the Step `09` pairing file remains
reference-only. Exact commands and preparation rules live in the
[`RUNBOOK`](../docs/operations/RUNBOOK.md); current evidence state lives in
[`HANDOFF.md`](../docs/operations/HANDOFF.md). The durable placement rule for
public caller-supplied inputs is in
[`SOURCE_TOPOLOGY.md`](../src/norad/contracts/SOURCE_TOPOLOGY.md).

Exact committed-file tests cover the artifact inventory, runtime-preflight
example, Step `07` pilot and primary selections, both Step `09c` declaration
examples, and all thirteen Step `09c` schema-reference tables. The other listed
assets have no exact-file automated test. A linked owner may validate a
supplied file; that does not prove every tracked starter or reference here is
current or production-ready.

The repository static gate also schema-checks the tracked sample-manifest
starter. It does not request FASTQ existence checks or turn the declared paths
into fixtures.

An `.example` name means structural or synthetic starter, not a ready-to-run
production selection. Other tracked reference and selection files still
require their documented consumer or preparation checks and do not prove that
a run occurred. Nothing here should be edited to manufacture a passing status,
approval, provenance record, or evidence claim. Files created under `configs/`
are trackable by default; do not assume that a site-specific or sensitive local
copy here is ignored.
