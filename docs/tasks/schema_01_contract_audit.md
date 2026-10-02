# SCHEMA-01 contract decision brief

The [backlog matrix](backlog_matrix.md#maintainability-and-release) alone owns
acceptance and status. This brief preserves the bounded audit and decisions
needed before changing a schema; it approves no reset, field removal or migration.
The [schema owner](../../src/emrys/contracts/schemas/README.md) remains authoritative.

The September 22 source pass reviewed `f32260f0408fe1826af401fc1ddce0f2478ae6ce`;
schema source matched `3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d` and was unchanged
by `5ecc409c123fe34f746a61f7e92397c6978f3cab`. It inspected source, tests and public
metadata without executing tests, a Run, cluster work or migration. The
[frozen audit](https://github.com/lab-cats/EMRYS/blob/06f88dbca7161599d7445f8cb2bfedf58f377282/docs/tasks/schema_01_contract_audit.md)
retains detailed searches and measurements. Its historical observations are not
a current consumer census or permission to rewrite retained records.

## Decision and coverage

Decide product version, `$id`, serialized label and packaged path independently.
Compare retaining current contracts, a justified field transition, and a selected
reset against complete caller migration, retained-state impact and measured net
maintenance reduction. Product 1.0 does not require schema v1.

| Alias | Retained finding and decision limit |
| --- | --- |
| S01–S03 | Twenty Draft 2020-12 resources: four artifact and 16 orchestration; three artifact and 15 orchestration selectors plus common definitions. Nine IDs already use v1; eleven do not. External references close within this set. Artifact common references orchestration's installed-package definition. Registries have different selection/admission policies. |
| S04 | Producer/reader routes are identified below; complete direct, Slurm, resume, report, CLI, installed-wheel and external-consumer parity remains unproved. |
| S05 | Seven package-data directories and the wheel roster include all 20 resources. Twelve orchestration schemas are explicit Run roots; all 20 affect installed-package identity for new Attempts. Omission from the Run-root list is neither dead code nor proof that a registry edit is Run-neutral. |
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

## Field candidates

These are qualified hypotheses, not unused-field claims. Profile candidates also
belong to deferred `PROFILE-CONTRACT-01`; a full family-by-family screen remains
necessary before S11. Preserve the Run's functional required-owner field even if
a profile copy is selected for derivation.

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

## Approval and proof gate

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
