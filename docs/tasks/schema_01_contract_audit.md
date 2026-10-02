# SCHEMA-01 contract decision brief

The [backlog matrix](backlog_matrix.md#maintainability-and-release) alone owns
acceptance and status. This brief records the completed field screen and decision
to retain current formats; it approves no reset, field removal or migration.
The [schema owner](../../src/emrys/contracts/schemas/README.md) remains authoritative.

The September 22 source pass reviewed `f32260f0408fe1826af401fc1ddce0f2478ae6ce`;
schema source matched `3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d` and was unchanged
by `5ecc409c123fe34f746a61f7e92397c6978f3cab`. It inspected source, tests and public
metadata without executing tests, a Run, cluster work or migration. The
[frozen audit](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/schema_01_contract_audit.md)
retains detailed searches and measurements. Its historical observations are not
a current consumer census or permission to rewrite retained records.

## Historical decision coverage

The September checkpoint below left S10's full field screen and S11's selection
unfinished. The [October retention decision](#retention-decision-at-a3309dbf) and
[complete declared-field screen](#complete-declared-field-screen) close those
audit gaps without selecting a migration. Product version, `$id`, serialized
label and packaged path remain independent; product 1.0 does not require schema v1.

| Alias | Retained finding and decision limit |
| --- | --- |
| S01–S03 | Twenty Draft 2020-12 resources: four artifact and 16 orchestration; three artifact and 15 orchestration selectors plus common definitions. Nine IDs already use v1; eleven do not. External references close within this set. Artifact common references orchestration's installed-package definition. Registries have different selection/admission policies. |
| S04 | Producer/reader routes are identified below; complete direct, Slurm, resume, report, CLI, installed-wheel and external-consumer parity remains unproved. |
| S05 | Seven package-data directories include all 20 resources; the explicit wheel-roster overclaim is corrected in the October decision below. Twelve orchestration schemas are explicit Run roots; all 20 affect installed-package identity for new Attempts. Omission from the Run-root list is neither dead code nor proof that a registry edit is Run-neutral. |
| S06 | Alpha `0.1.0.dev0`, September 22 PyPI lookup 404 and no GitHub releases/tags. Exact public code searches for `emrys-rna-workflow`, `urn:emrys:schema:` and `emrys.analysis_modules` excluded this repository and returned zero; default-branch/index/size limits exclude a consumer census. Known collaborators, private wheels and source installs remain to inventory. |
| S07 | Tracked Projects are placeholders and data is ignored. Campaign evidence names actual retained cancelled/replacement Runs, but their present locations, versions and recovery needs were not inspected. Use an owner-authorized metadata inventory, without copying scientific data. |
| S08 | Obsolete Runs are refused with evidence preserved. Current Project forms, provider-v1 metadata versus execution support, and retained submission-request v1–v4 diagnostics are distinct contracts, not equivalent legacy aliases. |
| S09 | Source assertions cover closed registration/references, strict JSON, graph/order/scope, independent backend mapping, obsolete Attempt refusal, recovery, content identity, independent goldens and wheel resources. Reading assertions is not executing them. |
| S10 | All 79 definitions are referenced (388 references, 35 `oneOf`, eight `allOf`, eleven `if`). Repeated values and state unions can be independent defenses. No dead-definition deletion or registry merger was established. |
| S11 | No reset/removal was selected. Each candidate needs consumer impact, identity/recovery disposition, surviving defenses and measured complete implementation cost. |

## Resource ledger at the reviewed revision

Paths below omit `.schema.json` and begin at `contracts/schemas/`; ID suffixes
follow `urn:emrys:schema:`. This dated ledger is not a second registry.

| Packaged resource under `contracts/schemas/` | `$id` suffix after `urn:emrys:schema:` | Serialized label or role |
| --- | --- | --- |
| `artifacts/v1/common` | `artifacts:common:v1` | Definitions; references orchestration common |
| `artifacts/v2/artifact_record` | `artifacts:artifact-entry:v4` | Artifact entry; no top-level version field |
| `artifacts/v3/run_summary` | `artifacts:run-summary:v8` | `8.0.0` |
| `artifacts/v5/report_receipt` | `artifacts:report-receipt:v8` | `8.0.0` |
| `orchestration/v1/application_model` | `orchestration:application-model:v1` | Analysis revision v2; Execution Plan v1; Run binding v1 |
| `orchestration/v1/common` | `orchestration:common:v1` | Definitions |
| `orchestration/v1/policy` | `orchestration:policy:v1` | Analysis-module policy v1 definition |
| `orchestration/v1/project` | `orchestration:project:v1` | Project v1 |
| `orchestration/v1/reference` | `orchestration:reference:v1` | Reference v1 |
| `orchestration/v1/reporting_start` | `orchestration:reporting-start:v2` | Reporting start v2 |
| `orchestration/v1/run_lock` | `orchestration:run-lock:v2` | Run lock v2 |
| `orchestration/v1/task_attempt` | `orchestration:task-attempt:v4` | Task attempt v4 |
| `orchestration/v1/task_start` | `orchestration:task-start:v3` | Task start v3 |
| `orchestration/v1/verified_reporting` | `orchestration:verified-reporting:v1` | Verified reporting v1 |
| `orchestration/v1/verified_task` | `orchestration:verified-task:v2` | Verified task v2 |
| `orchestration/v1/workflow_attempt` | `orchestration:workflow-attempt:v4` | Workflow attempt v4 |
| `orchestration/v2/attempt_receipt` | `orchestration:attempt-receipt:v3` | Attempt receipt v3 |
| `orchestration/v2/profile` | `orchestration:profile:v2` | Workflow profile v2 |
| `orchestration/v3/execution_profile` | `orchestration:execution-profile:v1` | Execution profile v1 |
| `orchestration/v3/resource_config` | `orchestration:resource-config:v1` | Local-pilot resources v1 |

The explicit Run roots are `application_model`, orchestration `common`, `policy`,
`reference`, `run_lock`, `task_attempt`, `task_start`, `verified_task`,
`workflow_attempt`, `attempt_receipt`, `profile` and `resource_config`.
The eight others remain active. Changing exact IDs in Run-bound registry code
can affect Run identity even for a schema outside that list.

| Producer/source | Readers and exact couplings to preserve |
| --- | --- |
| Artifact-index builder; summary and receipt writers | Public artifact validation; nested entry v4 in summary v8; receipt v8 binds entry/summary labels and hashes, both HTML hashes, and retained reporting transactions. These non-`$ref` edges are part of migration. |
| User/onboarding Project; packaged or selected resource/execution profiles | Normalization, placement and resource admission, Run policy/backend recheck, selected-profile hashes, workflow-Attempt execution-profile reference. |
| Composed workflow profile; application-model constructors; normalized reference/module policy | Canonical Run snapshots and functional projection; backend, lifecycle, Task and reporting consumers. Exact profile bytes bind Attempts even where fields are absent from the functional projection. |
| Materialization, lifecycle and Task writers | Workflow Attempt, Run lock, prepared/terminal Attempt receipt, Task start/attempt/verified chain; exact references, literal versions, roster/order, retained recovery and successor admission. |
| Reporting boundary | Reporting start and verified-reporting ledger, immutable generation recovery and revalidation. Reporting does not create another scientific Attempt. |
| Common definitions | Thirteen orchestration resources reference orchestration common; artifact common also uses its installed-package definition. |

Direct and delegated Slurm execution share scientific writers; head-node request
admission is separate. Resume freshly admits the immutable Run and prepared or
terminal closure. Automatic and standalone report paths share reporting owners.
Schema references alone do not inventory these consumers. The separate Slurm
request reader is not a registered-schema alias. Source searches found no direct
schema-path/ID references in scripts or workflows; a CI profile-version literal
and external callers still require their own consideration.

## Retention decision at a3309dbf

The October 1 follow-up reviewed source at
`a3309dbf3d8ad5b873501015cf099fd7785ae7a4`. Retain every current `$id`, serialized
version, packaged path and declared field. Do not reset them to v1 for a product
release. Do not introduce aliases, historical readers, record rewriting or a
second registry. This completes the field-screen and keep/transition/reset
**decision** missing from the September pass; it implements no schema migration.
The matrix remains the status authority.

| Option | Decision and reason |
| --- | --- |
| Keep current formats | Selected. Current producers, consumers, exact-byte references and admission checks use these formats. Keeping them preserves all existing defenses without new compatibility machinery. Product code, schema bytes and resource count change by zero. |
| Remove or derive selected fields | Not selected. The candidate table identifies possible future transitions, not dead fields established safe to delete. Some repeated values enforce independent checks; some carry provenance even without a direct lookup. None has a demonstrated caller-complete product reduction with preserved meaning, identities and recovery. `PROFILE-CONTRACT-01` remains deferred. |
| Reset IDs, labels or paths to v1 | Not selected. Renumbering offers no demonstrated runtime or maintenance benefit and can change exact registration, cross-record labels, packaged resource access, Run implementation identity and Attempt/package identity. Nine IDs already use v1. A product release is not a schema migration rationale. |

All 20 resource files, both registries, contract tests, package declarations,
Run schema roots and installed-package identity code are unchanged from the
September source revision. The current writers/readers were checked against that
snapshot: Task changes repair child reaping; Setup changes saved CLI settings;
Control/Report changes admit verified reuse before placement; execution-profile
admission now rejects normalized filesystem roots. None changes a declared schema
field or serialized format. Separate Slurm submission-request admission changes
remain outside this registered family and must not become schema aliases.

The seven package-data globs cover all 20 resources. **Correction to the earlier
roster claim:** the explicit `RESOURCE_PATHS` wheel-test list names 19 schemas,
omitting `application_model`; registration and Run-root inclusion are separate
facts, not an explicit twentieth wheel-roster assertion. The separate packaging
repair in `89c01f26` replaces that stale test list with the existing consumer
registries, enrolling all 20 while preserving the non-schema resource checks.
Its installed-wheel execution remains a separate CI obligation. No new wheel test
was run for this decision. The [retained software checkpoint](../../.github/workflows/README.md#integrated-software-checkpoint)
binds ordinary and real synthetic journeys to exact `4348976f`, with later
ordinary evidence at `06f88dbc`. It supports active use of these unchanged formats,
not exhaustive field mutation coverage, external-consumer absence, present site
recovery, scientific review or migration parity.

The alpha/public-metadata premise is insufficient to prove no consumers. Private
wheels, source installs, collaborators and actual retained site Runs remain
unquantified. Retaining current contracts does not depend on their absence;
inventory them before a future incompatible change, not as a precondition for
leaving their contracts intact. Historical measurements below remain hypotheses,
not implementation savings. No immediate dead-field or dead-definition deletion
was established.

## Complete declared-field screen

This source ledger covers all 20 resources and every declared `properties` group,
including array items, `$defs`, conditional branches and dynamic maps. Names below
use the resource ledger's paths; repeated shared definitions are expanded once.
Scalar constraints, required/optional distinctions, closed-object boundaries,
ordering and state unions are retained. Open objects are explicitly identified;
their owner-specific contents are not additional declared JSON Schema fields.
This is a dated audit ledger, not another executable schema registry.

### Artifact common

- `path_hash`: `path`, `sha256`, `size_bytes`, `row_count`, `media_type`.
  `issue`: `code`, `message`, `related_artifact_ids`.
  `metric`: `metric_id`, `name`, `value`, `unit`, `status`, `source_artifact_id`.
- `provenance`: `producer`, `producer_version`, `git_commit`, `installed_package`,
  `created_at`. `run_contract`: `run_contract_sha256`, `sample_manifest_sha256`,
  `reference_contract_sha256`, `partition_manifest_sha256`, `primary_analysis_id`,
  `primary_analysis_policy_sha256`. `scope`: `step_id`, `scope_type`, `scope_id`.
- Retain: artifact builders, summary/report readers and semantic validators use
  these bindings, typed values, issue references and provenance. Shared scalar
  IDs/hashes/paths and imported installed-package facts constrain those records;
  they are not standalone record candidates. See [artifact admission](../../src/emrys/contracts/artifacts/_artifact_contracts/).

### Artifact entry

- `artifact_id`, `scope`, `adapter`, `expectation(required, source_path)`,
  `availability_status`, `completion_status`, `state_reason`, `source`,
  `parameters`, `metrics`, `warnings`, `errors`; shared scope/path/metric/issue
  definitions apply. `parameters` is an adapter-owned open object.
- Retain: [record construction](../../src/emrys/reporting/_artifact_index/records.py)
  binds the expected inventory even when source content is absent. Semantic
  admission preserves complete/present/null-reason and failure/issue distinctions;
  summary rollups and report rendering consume them. No field is proved dead.

### Run summary

- `schema_name`, `schema_version`, `record_type`, `run_id`, `run_contract`,
  `summary_state`, `generated_at`, `inventory`, `expected_scopes`, `artifacts`,
  `computational_rollup`, `limitations`, `analysis_policy`, `warnings`, `errors`,
  `provenance`, `tables`, `scientific_origin`, `run_contract_file`, `publication`.
- Scope items: `scope`, `artifact_ids`, `aggregate_state`, `warnings`, `errors`.
  Rollup: `expected_artifact_count`, `complete_artifact_count`,
  `missing_artifact_count`, `incomplete_artifact_count`, `failed_artifact_count`,
  `externally_unavailable_artifact_count`. Limitations: `limitation_id`, `status`,
  `description`, `impact`, `evidence_ids`.
- `analysis_policy` and each table bind `path`, `sha256`, `size_bytes`;
  `scientific_origin` binds `run`, `attempt` record references;
  `run_contract_file` binds `path`, `sha256`; `publication` binds `attempt_id`,
  `started_at`, `finished_at`, `transaction_state`.
- Retain: [document/projection owners](../../src/emrys/reporting/_run_summary/)
  construct these records; contract/report/transaction readers check content,
  identity, order, tables and independent rollups. Nested issue arrays are only
  producer-derivable, not universally derivable under the admitted contract.

### Report receipt

- `schema_name`, `schema_version`, `record_type`, `run_id`, `generated_at`,
  `publication_state`, `transaction_state`, `interpretation_boundary`,
  `input_run_summary`, `inputs`, `analysis_policy`, `scientific_renderer`,
  `evidence_renderer`, `template`, `stylesheet`, `outputs`, `state_banner`,
  `schema_versions`, `analysis_execution_performed`, `external_network_assets_used`,
  `validation_claimed`, `warnings`, `errors`, `provenance`.
- Summary input: `path`, `sha256`, `schema_name`, `schema_version`; other inputs:
  `path`, `sha256`, `size_bytes`, `rehash_content`; policy: those first three plus
  `schema_version`; template/stylesheet resources: `path`, `sha256`.
- Scientific renderer: `module_id`, `module_version`, `distribution_name`,
  `distribution_version`, `package`, `entry_point`, `content_sha256`, `core_support`.
  Core/evidence renderer: `producer`, `producer_version`, `package`,
  `content_sha256`, `template_engine`, `template_engine_version`.
  Outputs: `output_id`, `kind`, `path`, `sha256`, `size_bytes`, `media_type`,
  `self_contained`; schema versions: `artifact_entry`, `run_summary`, `report_receipt`.
- Retain: [receipt construction and TSV projection](../../src/emrys/reporting/_run_report/receipt.py),
  semantic admission and transaction revalidation bind both rendered outputs and
  explicit computational-only claims. The equal renderer copies and empty
  `errors` are transition candidates below; constant values do not erase their
  public assertion/provenance role or exact receipt identity.

### Orchestration common

- `file_snapshot(path, size_bytes, sha256)`, `record_reference(path, sha256)`,
  `scope(scope_type, scope_id)`, `command(argv, exit_code)` and its successful/null
  variants; `bound_file(role, path, size_bytes, sha256)`.
- `tool_identity`: `name`, `version`, `path`, `resolved_path`, `sha256`, optional
  `identity_kind`. `installed_package`: `path`, `distribution`, `version`,
  `content_sha256`, `git_commit`, `git_dirty`, `python_lock_sha256`.
- Retain: strict scalar IDs, timestamps, authored/absolute/relative paths and
  hashes feed every referenced record. [Lifecycle](../../src/emrys/orchestration/run_coordinator/lifecycle.py)
  and Task admission distinguish command success, logical versus resolved paths,
  file versus package-tree identity, and package provenance. A distribution
  version ignored by one content-based readmission is still recorded provenance.

### Application model

- Analysis sample: `sample_id`, `condition`, `replicate`, `strandedness`,
  `r1_fastq_sha256`, `r2_fastq_sha256`; partitions: `partition_id`, `selector_type`,
  region `selector_value` or `selector_file_sha256` with paired optional
  `selector_format`, `selector_compression`.
- Analysis module: `module_id`, `interface_version`, `module_version`,
  `configuration`; identity: `identity_domain`, `samples`, `partitions`,
  `reference(fasta_sha256, gtf_sha256)`, `analysis_module`;
  revision: `schema_version`, `identity`, `analysis_revision_id`.
- Functional specification: `owner_tasks(machine_key, step_id, scope_type)`,
  `direct_edges(producer, consumer, artifact, semantics)`, `required_owner_keys`,
  `evidence_owner_keys`, `artifact_templates(artifact_id_template, step_id,
  scope_type, adapter, source_path_template, required)`.
- Plan identity: `identity_domain`, `functional_specification`,
  `scientific_stopping_owner_keys`, `implementation_content_sha256`,
  `processing_compatibility_sha256`, `toolchain(kind, logical_name, content_sha256)`,
  `backend(backend, engine, semantics_sha256)`, `star_index`,
  `computational_resources(workflow_cores, workflow_memory_mb, stage_concurrency,
  step_threads, stage_memory_mb)`, optional `processing_source(source_run_id,
  workflow_attempt_id, attempt_receipt_sha256)`; plan: `schema_version`, `identity`,
  `execution_plan_id`.
- Run: `schema_version`, `binding(identity_domain, analysis_revision_sha256,
  execution_plan_sha256)`, `run_id`. STAR policy uses the reference definition;
  resource owner-key maps and module configuration are intentionally open here.
- Retain: [constructors and successor validation](../../src/emrys/contracts/orchestration/application_model.py)
  canonicalize scientific inputs, functional graph, stopping boundary, content,
  resources and processing reuse into distinct immutable identities. IDs are
  derivable **integrity checks**, not removable duplicates. Provider configuration
  is separately normalized/validated; no scientific field is selected for removal.

### Analysis policy

- Module policy: `schema_version`, `analysis_id`, `module`, `implementation_sha256`,
  `configuration`. Module: `module_id`, `interface_version`, `module_version`,
  `distribution_name`, `distribution_version`, `entry_point`, `config_schema_sha256`,
  `dependencies`.
- Dependency variants: `dependency_id`, `kind`; executable/R-namespace probes
  additionally use `expected` and respectively `probe_args` or `target`.
- Retain: [module admission](../../src/emrys/analyses/__init__.py) and normalization
  produce provider provenance and admitted configuration; readiness, materialized
  Tasks and reporting read them. Open `configuration` belongs to the installed
  provider's schema/normalizer. Scientific identity and distribution provenance
  are deliberately different projections, not redundant schema owners.

### Project

- `schema_version`, `dataset(samples)`, `reference(fasta, gtf, star_index)`,
  `analyses` keyed by Analysis ID. Paired-CMH analysis: optional `sample_ids`,
  `partitions`, `control_condition`, `treatment_condition`, `target_change`,
  `min_sample_dp`, `mean_dp_threshold`, `fdr_threshold`, `common_or_threshold`,
  `absolute_difference_threshold`, optional `background_condition`,
  `background_max_fraction`. Module analysis: `module`, optional `sample_ids`,
  `partitions`, `config`.
- Retain: user/onboarding input flows through [normalization](../../src/emrys/orchestration/run_coordinator/normalization.py)
  into selected samples/partitions, reference bytes and admitted module policy.
  The shorthand and module forms remain accepted interfaces; thresholds are
  scientific configuration, not defaults safe to erase. Module `config` is
  provider-admitted; the STAR policy is the reference schema's shared definition.

### Reference

- `schema_version`, `reference_id`, `fasta`, `gtf` file snapshots;
  `star_index(sjdb_overhang, genome_sa_index_nbases, optional genome_chr_bin_nbits)`.
- Retain: normalization binds bytes and index policy; application identity,
  backend and reporting consume their projections. `reference_id` is a derivable
  provenance candidate below; the whole record remains hashed and referenced.

### Workflow profile

- `schema_version`, `profile_id`, `profile_version`, `semantic_owner_keys`,
  `owner_tasks(machine_key, rule_name, step_id, scope_type, scope_selector)`,
  `direct_edges(producer, consumer, artifact, semantics)`, `required_owner_keys`,
  `evidence_owner_keys`, `artifact_templates(artifact_id_template, step_id,
  scope_type, scope_selector, adapter, source_path_template, required)`.
- Retain: [profile semantic validation](../../src/emrys/contracts/orchestration/api.py),
  application functional projection, [inventory expansion](../../src/emrys/contracts/orchestration/artifact_inventory.py)
  and [Snakemake](../../src/emrys/workflow/Snakefile) use graph/classification,
  independent rule mapping, scope grouping and authored order. The five profile
  candidates below require one coherent future `PROFILE-CONTRACT-01` decision;
  exact profile bytes remain bound even outside the functional projection.

### Resource configuration

- `schema_version`, `workflow_cores`, `workflow_memory_mb`, `stage_concurrency`,
  `step_threads`, `stage_memory_mb`; memory alternatives include `minimum_mb`.
- Closed concurrency keys: `01, 02, 02b, 03, 04, 05, 06, 07`; thread keys:
  `00a, 00c, 02b, 04, 05, 01, 02, 06, 08, 09, 10`; memory keys:
  `00a, 00b, 00c, 01, 02, 02b, 03, 04, 05, 06, 07, 08, 09, 10`.
- Retain: [resource policy](../../src/emrys/orchestration/run_coordinator/resource_policy.py)
  resolves positive/symbolic allocation/auto/workflow values, workload and memory
  floors; backend and successor admission compare the effective policy. These
  33 explicit keys preserve a closed set and diagnostics; a generic map would
  weaken admission. Authored declarations and resolved values serve different
  identity/allocation boundaries.

### Execution profile

- `schema_version`, optional `resources`, optional `placement`; resources use the
  preceding schema. Direct placement: `kind`; Slurm: `kind`, `account`,
  `partition`, `qos`, `cpus_per_task`, `memory_mb`, `time`, `exclusive`, `nodelist`,
  `scratch_parent`, `modules(mode, init, load)`.
- Retain: [execution-profile admission](../../src/emrys/orchestration/run_coordinator/execution_profile.py)
  resolves authored/default values and placement; submission/delegate/Attempt
  paths bind selected-source and effective bytes. `none` versus `exact` module
  forms and normalized nonroot paths remain enforced. Deriving `mode` would be a
  user-format/diagnostic/recovery change, not a dead-member deletion.

### Workflow Attempt

- `schema_version`, `run_id`, `execution_contract_sha256`, `profile_sha256`,
  `workflow_attempt_id`, `supersedes_workflow_attempt_id`, `operation`, `created_at`,
  `request`, `request_label`, `authored_paths`, `normalizer`, `workspace`, `scratch`,
  `installed_package`, `executor`, `execution_mode`, `snakemake_argv`, `host`,
  `process_id`, `owner_token`, `cores`, `required_tools`, optional `placement`,
  `workflow`, `tasks`.
- Authored paths: `request`, `sample_manifest`, `partition_manifest`,
  `reference_fasta`, `reference_gtf`, `analysis_policy`. Placement: `kind`,
  `source(path, sha256)`, `effective_sha256`, `request`, `scheduler_job_id`;
  direct/Slurm variants cross-check request shape and job presence.
- Workflow: `reference_contract_path`, `primary_analysis_policy_path`,
  `reporting_run_contract_path`, `artifact_inventory_path`, `resource_policy`.
  Each owner/scope task is either a `workflow_attempt_record` reference or
  `scope_type`, `task_attempt_id`, `owner_run_token`, `producer_argv`,
  `validator_argv`, `inputs`, `outputs`, `validation_report_path`, `publication`,
  `retry_task_attempt_record`; `task_argv` is a nonempty string array.
- Retain: [materialization](../../src/emrys/orchestration/run_coordinator/materialization.py)
  writes these; lifecycle, backend, inspection, Task and reporting admit them.
  Open resource/file/publication declarations have their own typed owner checks.
  Execute/resume predecessor distinction, inherited-task references, exact
  dispatch, runtime bindings and authored provenance survive. Only the always-null
  `scratch` is a qualified future field-removal candidate; `execution_mode`'s
  historical/test distinction is not changed by this audit.

### Run lock

- `schema_version`, `run_id`, `workflow_attempt_id`, `attempt_record_path`,
  `attempt_record_sha256`, `owner_token`, `process_id`, `host`, `created_at`.
- Retain: `run_lock_record` projects the whole Attempt ownership context;
  [active/released lock admission](../../src/emrys/orchestration/run_coordinator/_inspection_admission.py)
  compares every projected field and exact bytes. A derivable projection is an
  independent ownership/recovery fence, not a second mutable authority to delete.

### Task start

- `schema_version`, `run_id`, `execution_contract_sha256`, `profile_sha256`,
  `workflow_attempt_id`, `task_attempt_id`, `machine_key`, `scope`, `owner_run_token`,
  `workflow_attempt_record`, `run_lock`, `created_at`, `inputs`.
- Retain: [Task publication/admission](../../src/emrys/orchestration/run_coordinator/task.py)
  binds irreversible producer entry to dispatch, active lock and input bytes.
  Cumulative receipt inspection uses it to detect unclosed starts. Repeated
  identity is compared across independently published boundaries.

### Task attempt

- `schema_version`, `run_id`, `execution_contract_sha256`, `profile_sha256`,
  `workflow_attempt_id`, `task_attempt_id`, `machine_key`, `scope`, `owner_run_token`,
  `task_start_record`, `status`, `started_at`, `finished_at`, `producer`, `validator`,
  `semantic_all_pass`, `stable_inputs_rechecked`, `validation_report`, `stdout_log`,
  `stderr_log`, `failure_message`, `inputs`, `outputs`, `abort_closure`.
- Retain: Task terminal publication and readmission distinguish preentry failure,
  success and proven abort before publication. Command exit/argv, semantic report,
  input stability, output hashes, logs and start binding support different claims;
  `abort_closure` admits only the bounded retry case. Status alone cannot replace
  them. Not every schema-admitted status must be emitted by today's success/fail
  writer to remain a retained contract.

### Verified Task

- `schema_version`, `task_attempt_record`.
- Retain: Task writes this marker last; `validate_verified_task` re-admits the
  referenced terminal/start/dispatch/log/semantic-report and current file bytes.
  The marker is a publication boundary, not a cached success boolean.

### Attempt receipt

- `schema_version`, `run_id`, `execution_contract_sha256`, `profile_sha256`,
  `workflow_attempt_id`, `attempt_record`, `released_run_lock`, `status`,
  `finished_at`, `snakemake_exit_code`, `termination_signal`, `task_attempt_records`,
  `task_start_records`, `verified_tasks`, `blockers`, `message`.
- Terminal/start roster items: `workflow_attempt_id`, `machine_key`, `scope`,
  `record`; verified items: `machine_key`, `scope`, `record`.
- Retain: lifecycle writes terminal closure; [receipt evidence inspection](../../src/emrys/orchestration/run_coordinator/_inspection_evidence.py)
  compares exact cumulative ordered rosters and unclosed starts, while lock
  admission binds released ownership. Exit/signal, blockers and message distinguish
  outcome/recovery from mere scheduler success. Factoring the two equal roster
  shapes is only a schema-syntax candidate, not removal of either evidence list.

### Reporting start

- `schema_version`, `run_id`, `execution_contract_sha256`, `profile_sha256`,
  `origin_workflow_attempt_id`, `kind`, `workflow_attempt`, `run_lock`, `created_at`.
- Retain: [reporting boundary](../../src/emrys/orchestration/run_coordinator/reporting_boundary.py)
  publishes entry before summary/HTML generation, verifies origin/lock binding,
  kind and timestamp order, and refuses historical or ambiguous partial state.
  It does not create a new scientific Attempt.

### Verified reporting

- `schema_version`, `run_id`, `execution_contract_sha256`, `profile_sha256`,
  `origin_workflow_attempt_id`, `kind`, `reporting_start`, `semantic_receipt`,
  `created_at`.
- Retain: the same owner publishes proof last after semantic and identity
  rechecks; inspection/reuse revalidates start, receipt and output bindings.
  Repeated identity and separate start/completion timestamps preserve recovery
  and transaction order. They are not interchangeable with a receipt's own fields.

The current screen establishes source-level declared-field coverage and a
reasoned retention decision. It does not establish every unknown consumer,
current external artifact population or exhaustive runtime parity. Those are
future transition gates. No runtime tests, installs, Runs or data mutations were performed for this
field screen, and it makes no new parity claim. Documentation checks validate
this record's structure only.

## Field candidates

The completed screen retains all of these fields now. They remain qualified
future-transition hypotheses, not unused-field claims or newly accepted work.
Profile candidates also belong to deferred `PROFILE-CONTRACT-01`. Preserve the
Run's functional required-owner field if a future decision derives a profile copy.

| Candidate | Current role and protection | Derivation question and remaining check |
| --- | --- | --- |
| `semantic_owner_keys` | The [profile validator](../../src/emrys/contracts/orchestration/api.py) compares this roster with owner tasks and classifications. The packaged profile has the same 12 keys as its owner tasks; validation compares sets. It is absent from the Execution Plan functional projection, though exact profile bytes are bound elsewhere. | Can unique `owner_tasks[].machine_key` supply the set while preserving owner membership and divergence refusal? Inspect external profiles and retained records. |
| `required_owner_keys` | Its profile set must currently equal all semantic owners. It is also copied into immutable Execution Plan identity and consumed by stopping, reuse, Task admission, and verified-task admission. | Assess removing only the profile copy while retaining the Run functional field. Removing the Run field is a wider identity and recovery decision. |
| `owner_tasks[].rule_name` | [Snakemake](../../src/emrys/workflow/Snakefile) uses it to name processing rules and in an independent fixed mapping check. A test swaps machine keys under unchanged rule names to exercise that check. | Could a pinned backend mapping or stable owner identity derive it while retaining exact names and the independent remapping defense? The field is used, not dead. |
| `owner_tasks[].scope_selector` | Validation requires the current one-to-one mapping from `scope_type`; Snakemake's fixed processing check reads both. | Test whether derivation preserves the independent scope fence and exact profile binding. |
| `artifact_templates[].scope_selector` | [Inventory expansion](../../src/emrys/contracts/orchestration/artifact_inventory.py) groups templates in first-seen selector order and rejects selector/scope mismatches. | Derivation from `scope_type` must preserve inventory rows, order, grouping, and rejection behavior. The field is used, not dead. |
| `workflow_attempt.scratch` | The schema requires an absolute path or null; the current [Attempt producer](../../src/emrys/orchestration/run_coordinator/materialization.py) always writes null for execute and resume. A repository search found no direct production read. Slurm `scratch_parent` and Task worker scratch are separate values with different lifetimes. | Decide whether per-Attempt scratch provenance remains needed, then inventory retained Attempts and external readers. Removing its null member saves 15 canonical bytes per currently produced Attempt but changes exact references and a Run-bound schema, not yet measured product code. |
| `run_summary.expected_scopes[].warnings` and `errors` | The [summary producer](../../src/emrys/reporting/_run_summary/projection.py) copies and stably deduplicates artifact issues into each scope, and the schema requires both arrays. No direct in-repository reader of these nested arrays was found, but a [valid fixture](../../tests/contracts/artifacts/fixtures/artifact_schema_v2/valid/run_summary.json) has a scope warning message different from its sole artifact warning. Semantic admission does not require issue-array equality. | These arrays are not universally derivable from artifacts under the admitted contract. Determine external meaning and retained evidence needs before proposing a semantic change; report-template non-use alone is insufficient. |
| `report_receipt.scientific_renderer.core_support` and `evidence_renderer` | The [receipt writer](../../src/emrys/reporting/_run_report/receipt.py) copies one core-renderer record to both locations; [semantic admission](../../src/emrys/contracts/artifacts/_artifact_contracts/report_receipt.py) requires equality. Evidence HTML identity reads `evidence_renderer`. | A single-copy shape would change receipt bytes and evidence identity lookup, and retire an equality defense. Establish whether the two positions represent distinct provenance claims and how retained receipts and external readers would be handled. |
| `report_receipt.errors` | The [schema](../../src/emrys/contracts/schemas/artifacts/v5/report_receipt.schema.json) requires an empty array, and the writer always emits `[]`; no direct production field read was found. | Decide whether the explicit no-error assertion is needed for public receipts. A deletion changes the admitted shape and retained receipt hash even if the current producer value is constant. |
| `reference.reference_id` | [Normalization](../../src/emrys/orchestration/run_coordinator/normalization.py) generates it from the Analysis reference scope ID. No direct lookup of this JSON reference-contract field was found; Task and artifact-inventory code recompute that scope ID. A [separate TSV reference inventory](../../src/emrys/evidence/reference_provenance/_reference_inventory.py) has its own `reference_id`. The complete JSON contract is still bound in reporting. | Check standalone reference provenance, retained readers, and whether a narrower derivation saves product code before changing this Run-bound record. |
| `execution_profile.placement.modules.mode` | The [schema](../../src/emrys/contracts/schemas/orchestration/v3/execution_profile.schema.json) closes `none` to empty `init`/`load` and `exact` to a path and nonempty load list. The mode is read into placement, serialized in Attempt requests, and shown in diagnostics. | Derivation from `init`/`load` is only a hypothesis. A syntax change affects user profiles, selected-source hashes, placement bytes, and recovery; prove a net reduction and equivalent refusals first. |
| Adjacent `workflow_inputs["profile"]` | Source review found a generated private backend projection of profile ID, version, and hash with no production reader found so far. It is not a JSON Schema field. | Check external/API exposure and route any justified removal to its proper reduction owner. Do not infer that the schema's profile ID or version fields are unused. |
| Adjacent `validate_record(..., profile=...)` | The orchestration API includes this optional parameter and serializes it into the successful-validation cache key, but the called record validator does not read it. Inspection forwards it, while a separate successor-Run check actually validates Run/profile consistency. This is an API/cache candidate, not a schema field. | Inspect external Python callers and error precedence before removing the parameter or cache dimension. Preserve the separate successor-Run admission. |

The independent backend mapping must not become self-confirming by deriving its
expected rule names only from supplied profile keys. First-seen template grouping,
ordering, reopened-group refusal and authored profile order also need surviving
checks. Derivation of scope issues is specifically contradicted by an admitted
fixture whose scope warning differs from its artifact warning.

## Reduction measurements and counterexamples

The historical base profile has 12 owners/57 templates and 21,124 canonical bytes.
Independent deletion projections saved 617 bytes each for the two owner rosters,
551 for rule names, 332 for owner selectors and 1,591 for template selectors;
together 3,708 bytes (17.55%). A composed 14-owner/70-template profile has 26,103
bytes; the combined projection saved 4,424 (16.95%). That composed projection was
mechanical and not runtime-validated because `jsonschema` was unavailable then.
Analysis rule names differ from processing names, defeating a universal slug rule.
These are serialized-byte estimates, not measured product savings or parity.

Do not infer redundancy for six rollup counts/aggregate state (independently
recomputed and rendered), receipt schema versions (otherwise missing entry
version), interpretation banner copies (TSV/HTML checks), absent expected-source
paths, admitted issue/metric identities, summary limitations, Attempt cores versus
resolved policy, whole lock projections, or scientific thresholds bound into
identity. Distribution-version changes are deliberately ignored by some
readmission when owned bytes are unchanged; this is not a global version rule.

Small syntax candidates remain unselected: two 27-line Attempt-receipt roster
shapes; repeated 6–8-line path/hash/size shapes; an approximately 15-line artifact
complete-state condition; and workflow-Attempt direct/Slurm condition factoring.
Resource-config's 33 explicit stage keys preserve a closed key set and diagnostics.
Cross-resource sharing adds coupling; large state unions are not dead syntax.

Keep both registries unless a complete migration proves a reduction: their 58
physical lines include only 18 identical nonblank lines, mostly framework setup,
while error types, exact-ID policy, selectors, cache and diagnostics differ.
Only eight shared `safe_id`/SHA lines would not retire a common owner; canonical
JSON helpers also differ in byte and NaN behavior. Adjacent API/cache candidates
must preserve error precedence and independent successor-Run admission.

## Gate for any future transition

1. Select exact fields/IDs/labels/paths and freeze the revision. Obtain bounded
   retained-record and collaborator metadata; unknown is not unused.
2. Trace every producer, consumer, reference and package/Run/Attempt identity.
   Nine v1 IDs need no reset; three artifact IDs, seven non-v1 orchestration Run
   roots and non-root `reporting_start` have different migration effects.
3. Compare keep/transition/reset with accepted and rejected records, exact
   diagnostics/order, recovery/failure injection, immutable retained bytes,
   independent goldens and installed wheel resources. Do not add compatibility
   machinery merely to disguise a contract decision.
4. Measure schema bytes separately from maintained product code. Approve only a
   caller-complete change with equal-or-stronger defenses and the required net
   reduction or explicit quantified exception, then run the selected route checks.

Use the [orchestration owner](../../src/emrys/contracts/orchestration/README.md),
[artifact owner](../../src/emrys/contracts/artifacts/README.md),
[Run identity](../../src/emrys/orchestration/run_coordinator/run_implementation.py)
and [package tests](../../tests/test_package_distribution.py) as current sources.
