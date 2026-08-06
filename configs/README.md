# Configuration and input catalog

This directory holds explicit public inputs, structural examples, operator
selections, and reference tables that callers receive as files. It is not one
configuration system: there is no universal loader, implicit discovery rule,
or executable orchestrator for the whole directory.

## Catalog

| Area | Tracked inputs | Consumer and status |
| --- | --- | --- |
| Deferred workflow profiles | [`cluster_full.yaml.example`](cluster_full.yaml.example), [`local_test.yaml`](local_test.yaml) | Illustrative cluster and local layouts retained under the [deferred-profile disposition](../docs/architecture/FUNCTIONAL_OWNER_INVENTORY.md#residual-tracked-path-coverage). No current executable orchestrator consumes either profile. |
| Sample-manifest starter | [`samples.example.tsv`](samples.example.tsv) | Structural two-row public input for the final [sample-manifest admission owner](../src/norad/ingestion/sample_manifest_admission/README.md). Make and the scheduler smoke job schema-check it without FASTQ existence checks; it is not an ingestion runner, runtime manifest, or runnable data fixture. |
| Artifact and report projection | [`artifact_inventory.example.tsv`](artifact_inventory.example.tsv), [`artifact_run_contract.example.json`](artifact_run_contract.example.json), [`report_table_approvals.example.tsv`](report_table_approvals.example.tsv) | Synthetic structural inputs for the [reporting owner](../src/norad/reporting/README.md). The [neutral artifact-contract validator](../src/norad/contracts/artifacts/validate_artifact_contracts.py) also accepts an explicit inventory for bounded contract checks. They are fixtures/examples, not a production inventory, run contract, approval, or report. |
| Reference provenance | [`reference_provenance.example.tsv`](reference_provenance.example.tsv) | Structural starter for the [reference-provenance evidence owner](../src/norad/evidence/reference_provenance/README.md). Replace illustrative paths, hashes, releases, and provenance in an operator-controlled input. |
| Runtime availability | [`runtime_preflight.example.tsv`](runtime_preflight.example.tsv) | Structural starter for the [runtime-preflight evidence owner](../src/norad/evidence/runtime_preflight/README.md). Its illustrative probes do not establish local, batch, or cluster availability. |
| Storage and retention state | [`storage_roots.example.tsv`](storage_roots.example.tsv), [`retention_policy.example.tsv`](retention_policy.example.tsv) | Structural starters for the [storage-inventory evidence owner](../src/norad/evidence/storage_inventory/README.md). They record roots, quota expectations, decisions, and approvals; they never execute a retention action. |
| Step `07` partition selection | [`step_07_partitions.example.tsv`](step_07_partitions.example.tsv), [`step_07_partitions.pilot.tsv`](step_07_partitions.pilot.tsv), [`step_07_partitions.primary_contigs.tsv`](step_07_partitions.primary_contigs.tsv) | The [Step `07` owner](../src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/README.md) defines the schema. The example is a small structural reference, the pilot selects one bounded region, and the primary file declares the shared 25-selector set `1`–`22`, `X`, `Y`, `MT`. Runtime-reference agreement and execution remain unproved. |
| Step `09` pairing | [`step_09_pairs.NORAD_EV_PUM1.tsv`](step_09_pairs.NORAD_EV_PUM1.tsv) | Pairing reference for preparing and verifying the full runtime sample manifest used by the [Step `09` analysis owner](../src/norad/analyses/rank_cohort_candidates_with_paired_CMH/README.md). It is not a runtime overlay or a result. |
| Step `09c` scientific-review inputs | [`step_09c_review_plan.example.tsv`](step_09c_review_plan.example.tsv), [`step_09c_evidence_manifest.example.tsv`](step_09c_evidence_manifest.example.tsv), and the thirteen schema references listed below | Structural references for the [Step `09c` evidence owner](../src/norad/evidence/assemble_scientific_review_evidence_package/README.md) and neutral [review-package contract](../src/norad/contracts/scientific_evidence/review_package.py). They are not selected automatically, attached evidence, a completed review, or biological-readiness authority. |

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
