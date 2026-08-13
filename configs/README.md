# Configuration and input catalog

This directory holds explicit public inputs, structural examples, operator
selections, and reference tables that callers receive as files. It is not one
configuration system: there is no universal loader, implicit discovery rule,
or executable orchestrator for the whole directory.

## Catalog

| Area | Audience | Placement and ownership | State | Tracked inputs |
| --- | --- | --- | --- | --- |
| Sample-manifest starter | Operators | Public, single-owner input for [sample-manifest admission](../src/norad/ingestion/sample_manifest_admission/README.md) | Current structural starter; schema-checked without FASTQ existence checks, not a runnable fixture | [`samples.example.tsv`](samples.example.tsv) |
| Fixed local-pilot starters | Researchers and operators | Matched public inputs for [local-pilot normalization and control](../src/norad/orchestration/local_pilot/README.md) | Structurally valid fixed-profile starter set with two explicit paired strata; relative read/reference paths are placeholders, so the tracked files are not a runnable fixture | [`local_pilot_request.example.yaml`](local_pilot_request.example.yaml), [`local_pilot_samples.example.tsv`](local_pilot_samples.example.tsv), [`local_pilot_partitions.example.tsv`](local_pilot_partitions.example.tsv) |
| Artifact and report projection | Operators and report developers | Public reporting inputs; artifact indexing and run-summary assembly use `python -X pycache_prefix=/dev/null -I -m norad build artifact-index` and `python -X pycache_prefix=/dev/null -I -m norad build run-summary` with an explicit matching source checkout, and the inventory is also accepted by the [artifact-contract owner](../src/norad/contracts/artifacts/README.md) through `python -I -m norad validate artifact-contracts` | Current shared structural examples; not production inventory, run contract, approval, or report | [`artifact_inventory.example.tsv`](artifact_inventory.example.tsv), [`artifact_run_contract.example.json`](artifact_run_contract.example.json), [`report_table_approvals.example.tsv`](report_table_approvals.example.tsv) |
| Reference provenance | Operators | Public, single-owner input for [reference-provenance evidence](../src/norad/evidence/reference_provenance/README.md) | Current structural starter; illustrative identity and hashes must be replaced | [`reference_provenance.example.tsv`](reference_provenance.example.tsv) |
| Runtime availability | Operators | Public, single-owner input for [runtime-availability inspection](../src/norad/evidence/runtime_availability/README.md) through `python -I -m norad inspect runtime-availability`; the fixed local-pilot roster is consumed by `.venv/bin/python -X pycache_prefix=/dev/null -I -m norad doctor local-pilot` | Current structural starters; paths are placeholders and establish no availability until copied, completed, and checked | [`runtime_preflight.example.tsv`](runtime_preflight.example.tsv), [`local_pilot_runtime.example.tsv`](local_pilot_runtime.example.tsv) |
| Storage and retention state | Operators and approvers | Public, single-owner inputs for [storage-inventory inspection](../src/norad/evidence/storage_inventory/README.md) through `python -I -m norad inspect storage-inventory` | Current structural starters; they record state and approval but execute no retention action | [`storage_roots.example.tsv`](storage_roots.example.tsv), [`retention_policy.example.tsv`](retention_policy.example.tsv) |
| Step `07` partition selection | Operators | Public, single-owner inputs for the [Step `07` stage](../src/norad/stages/partitioned_cohort_mpileup/README.md) | Current example, pilot, and 25-selector reference; runtime-reference agreement remains unproved | [`step_07_partitions.example.tsv`](step_07_partitions.example.tsv), [`step_07_partitions.pilot.tsv`](step_07_partitions.pilot.tsv), [`step_07_partitions.primary_contigs.tsv`](step_07_partitions.primary_contigs.tsv) |
| Step `09` pairing | Operators | Public, single-owner reference for the [Step `09` analysis](../src/norad/analyses/paired_cmh_candidate_ranking/README.md) | Current reference-only pairing; not a runtime overlay or result | [`step_09_pairs.NORAD_EV_PUM1.tsv`](step_09_pairs.NORAD_EV_PUM1.tsv) |
| Step `09c` scientific-review inputs | Operators and reviewers | Public shared references for the [Step `09c` evidence owner](../src/norad/evidence/scientific_review_package/README.md) and [neutral review-package contract](../src/norad/contracts/scientific_evidence/review_package.py) | Current structural references; not selected evidence, completed review, or biological-readiness authority | [`step_09c_review_plan.example.tsv`](step_09c_review_plan.example.tsv), [`step_09c_evidence_manifest.example.tsv`](step_09c_evidence_manifest.example.tsv), and the thirteen schema references listed below |

The thirteen Step `09c` schema-reference tables are grouped under
[`step_09c_evidence_schemas/`](step_09c_evidence_schemas/). Its README routes
their structural boundary, neutral public contract, and direct parity test.

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

The three local-pilot starters are one matched set. Copy them to an explicitly
managed input directory, replace every placeholder identity and file target,
and retain explicit condition and replicate metadata. Their relative paths are
resolved from the request file's directory, never from the caller's working
directory. Pairing comes from matching `replicate` values with exactly one
declared `control` and one declared `treatment` row in each of at least two
strata; sample names do not establish pairing.

The local-pilot runtime starter is part of that explicit selection. It binds
the controlled Python/Snakemake launcher, the Python SHA-256 implementation,
Bash, gunzip, every scientific executable or jar, Rscript, the canonical
`renv` project and existing library, and required R namespaces. File-backed
identities are admitted by authored path, canonical target, version, and
SHA-256; the guarded R environment clears ambient R/renv path selectors and
sets the selected project library explicitly. Never fabricate a missing
`renv` library directory merely to make readiness pass.

Exact committed-file tests cover the artifact inventory, runtime-preflight
example, the matched local-pilot starters, Step `07` pilot and primary
selections, both Step `09c` declaration examples, and all thirteen Step `09c`
schema-reference tables. The other listed assets have no exact-file automated
test. A linked owner may validate a supplied file; that does not prove every
tracked starter or reference here is current or production-ready.

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
