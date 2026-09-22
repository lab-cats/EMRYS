# SCHEMA-01 contract audit and decision

This is the working evidence record for [SCHEMA-01](backlog_matrix.md#maintainability-and-release).
The backlog matrix owns the task's status and acceptance. Findings here do not
change the [current schema rules](../../src/emrys/contracts/schemas/README.md)
or approve a version reset or field removal.

The first source pass reviewed commit
`f32260f0408fe1826af401fc1ddce0f2478ae6ce` on 2026-09-22. Its schema
source is unchanged from `3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`.
This pass used source, documentation, package metadata, and public distribution
metadata. No tests, Run, cluster operation, or migration were performed.
`Observed` means confirmed in that bounded pass; `Partial` means a real path
was identified but its complete consumer or behavior inventory remains open;
`Open` means the evidence does not yet support a decision. These are finding
states, not another task-status registry.

## Decision questions

1. Does the prerelease and consumer evidence justify resetting any current
   JSON Schema identifier to v1? Decide `$id`, serialized record version,
   packaged directory, and product 1.0 separately.
2. Which candidate fields are unused, which can be derived from an existing
   semantic authority, and which repeated fields provide an independent check?
3. What would each choice change for installed resources, new Run identity,
   retained Runs, recovery, reporting, and external consumers?
4. Would the complete caller migration reduce maintained product code without
   weakening a distinct protection or adding an unnecessary compatibility path?

## Findings matrix

| ID | State | Discovery at the reviewed revision | Next evidence or decision |
| --- | --- | --- | --- |
| S01 — Resource scope | Observed | There are 20 packaged Draft 2020-12 resources: four artifact and 16 orchestration files. The registries expose three artifact and 15 orchestration selectors; two resources provide common definitions. See the resource ledger below. | Trace every selected record's writer, reader, and references before choosing a reset. |
| S02 — Version identity | Observed | Packaged directory numbers, `$id` versions, and serialized record versions differ in current files. The [schema owner](../../src/emrys/contracts/schemas/README.md#version-and-identity-rules) says directory numbers span separate families and participate in resource paths and references. | Give each kind of version and path a separate disposition; do not rename directories for visual consistency. |
| S03 — Registry and references | Observed | Artifact common definitions reference orchestration common's installed-package definition. All external `$ref` bases in the 20 files resolve within this set. [Orchestration](../../src/emrys/contracts/orchestration/api.py) requires exact registered `$id`s; the [artifact loader](../../src/emrys/contracts/artifacts/_artifact_contracts/schema.py) requires nonempty IDs and closes public selectors separately. | Check whether any registry consolidation preserves the different selector, error, and semantic-admission contracts while reducing total code. |
| S04 — Production consumers | Partial | Artifact entries feed the Run summary and reporting. Project setup, normalization, materialization, Task execution, lifecycle, and reporting boundaries write orchestration records; inspection and reporting read admitted records. | Complete a per-record writer/reader table covering public CLI, installed wheel, direct, Slurm, resume, report, fixtures, and documented integrations. Record negative searches. |
| S05 — Package and Run identity | Observed | [Package-data globs](../../pyproject.toml) cover seven schema directories, and the [wheel resource roster](../../tests/test_package_distribution.py) names all 20 files. Twelve orchestration schema paths are explicitly included in [Run implementation identity](../../src/emrys/orchestration/run_coordinator/run_implementation.py); changing their paths or bytes changes that identity component for new Runs. | Classify how the other eight resources enter identity and provenance. Determine whether the execution-profile schema's absence from that explicit list is intentional before claiming a defect. |
| S06 — Prerelease distribution | Partial | The package declares Alpha and `0.1.0.dev0`. On 2026-09-22, the exact PyPI project lookup returned 404, and GitHub listed no releases or tags. The [Quickstart](../../quickstart.md) documents source installation, and [provider and reporter entry points](../../src/emrys/analyses/README.md#collaborator-providers) are documented. | Inventory known collaborators, source installs, private distributions, and downstream readers. The checked public channels do not prove absence of external consumers. |
| S07 — Retained Runs | Open | Tracked `Projects/` contains only placeholders and Project data is ignored by Git. The [campaign record](backlog_matrix.md#viking-walkthrough-findings) reports actual-data Runs outside tracked source. Their current locations, versions, and recovery needs were not inspected. | Obtain owner-identified locations or a bounded inventory. Inspect version and identity metadata read-only without changing or copying scientific data. |
| S08 — Version-support boundaries | Observed | The [approved policy](../design/decisions/platform-direction.md#version-support) rejects obsolete Run records, preserves retained evidence, and requires full checks for current-format recovery. Current schemas also admit some v1 provider metadata and a flat Project form. A separate submission-request reader admits v1–v4 retained diagnostics. | Classify those current-format and diagnostic paths by authority before treating them as obsolete aliases or proposing retirement. |
| S09 — Existing protection | Partial | Source tests cover exact registration, schema contracts, independent artifact goldens, obsolete Attempt refusal, and content-bound recovery. Their presence was inspected; their result at this revision was not. | Map each proposed change to its distinct surviving defense. Run focused checks on a final approved implementation and long lanes in CI. |
| S10 — Reduction opportunities | Partial | Both registries repeat some strict JSON parsing and Draft 2020-12 setup, but differ in exact-ID enforcement, selectors, diagnostics, and semantic admission. Artifact and orchestration common definitions share identical `safe_id` and `sha256` shapes; other same-named definitions differ. | Measure caller-complete savings before sharing machinery or definitions. Inventory tests, scripts, configuration, docs, compatibility, and mutable state separately; retain independent evidence. |
| S11 — Contract decision | Open | No reset or removal follows from this pass. | Compare keeping current contracts, justified field transitions, and a selected v1 reset with quantified consumer impact and maintenance cost. Record a reasoned disposition for each candidate. |

### Field candidates

These profile fields also fall under deferred
[PROFILE-CONTRACT-01](backlog_matrix.md#platform-operation-and-portability).
`Derivable` here names a hypothesis, not authority to remove a current field.

| Candidate | Current role and protection | Derivation question and remaining check |
| --- | --- | --- |
| `semantic_owner_keys` | The [profile validator](../../src/emrys/contracts/orchestration/api.py) compares this roster with owner tasks and classifications. The packaged profile has the same 12 keys as its owner tasks; validation compares sets. It is absent from the Execution Plan functional projection, though exact profile bytes are bound elsewhere. | Can unique `owner_tasks[].machine_key` supply the set while preserving owner membership and divergence refusal? Inspect external profiles and retained records. |
| `required_owner_keys` | Its profile set must currently equal all semantic owners. It is also copied into immutable Execution Plan identity and consumed by stopping, reuse, Task admission, and verified-task admission. | Assess removing only the profile copy while retaining the Run functional field. Removing the Run field is a wider identity and recovery decision. |
| `owner_tasks[].rule_name` | [Snakemake](../../src/emrys/workflow/Snakefile) uses it to name processing rules and in an independent fixed mapping check. A test swaps machine keys under unchanged rule names to exercise that check. | Could a pinned backend mapping or stable owner identity derive it while retaining exact names and the independent remapping defense? The field is used, not dead. |
| `owner_tasks[].scope_selector` | Validation requires the current one-to-one mapping from `scope_type`; Snakemake's fixed processing check reads both. | Test whether derivation preserves the independent scope fence and exact profile binding. |
| `artifact_templates[].scope_selector` | [Inventory expansion](../../src/emrys/contracts/orchestration/artifact_inventory.py) groups templates in first-seen selector order and rejects selector/scope mismatches. | Derivation from `scope_type` must preserve inventory rows, order, grouping, and rejection behavior. The field is used, not dead. |
| Adjacent `workflow_inputs["profile"]` | Source review found a generated private backend projection of profile ID, version, and hash with no production reader found so far. It is not a JSON Schema field. | Check external/API exposure and route any justified removal to its proper reduction owner. Do not infer that the schema's profile ID or version fields are unused. |

## Resource ledger at the reviewed revision

This snapshot keeps paths, identifiers, and record labels separate. It is an
audit aid, not another schema registry or a proposed renaming list. Exact
machine contracts remain in the [artifact](../../src/emrys/contracts/schemas/artifacts/README.md)
and [orchestration](../../src/emrys/contracts/schemas/orchestration/README.md)
schema resources.

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

## Next audit passes and decision gate

1. Complete the per-resource writer, reader, fixture, documentation, and
   installed-package map. Classify versioned JSON records outside the packaged
   registry separately.
2. Reconcile the external-consumer premise and retained-Run inventory with
   explicitly bounded evidence. Report unknowns instead of treating a negative
   repository search as proof of absence.
3. For each field candidate, compare current and derived values on tiny
   representative profiles and enumerate every caller, defense, identity
   change, and byte change. Preserve graph, uniqueness, scope, inventory
   ordering, Execution Plan identity, and direct/Slurm behavior.
4. Report product code and file counts separately from tests, configuration,
   documentation, and evidence. Evaluate the existing owners, standard library,
   `jsonschema`/`referencing`, and maintained tools before adding machinery.
5. Decide whether to retain current identifiers or propose an exact migration.
   A selected migration requires separate approval and must move every affected
   current caller together, reject incompatible records without changing
   retained evidence, and avoid unnecessary aliases or historical readers.

Stop when a consumer, field meaning, recovery behavior, required defense, or
maintenance exception cannot be bounded from the available evidence. No
identifier reset, field deletion, cluster proof, scientific review, or evidence
promotion is implied by this audit record.
