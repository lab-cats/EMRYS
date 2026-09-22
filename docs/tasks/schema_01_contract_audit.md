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
| S01 — Resource scope | Observed | There are 20 packaged Draft 2020-12 resources: four artifact and 16 orchestration files. Public record selection covers three artifact and 15 orchestration selectors; two resources provide common definitions. The artifact loader also holds its common definitions as internal registry keys. See the resource ledger below. | Trace every selected record's writer, reader, and references before choosing a reset. |
| S02 — Version identity | Observed | Packaged directory numbers, `$id` versions, and serialized record versions differ in current files. The [schema owner](../../src/emrys/contracts/schemas/README.md#version-and-identity-rules) says directory numbers span separate families and participate in resource paths and references. | Give each kind of version and path a separate disposition; do not rename directories for visual consistency. |
| S03 — Registry and references | Observed | Artifact common definitions reference orchestration common's installed-package definition. All external `$ref` bases in the 20 files resolve within this set. [Orchestration](../../src/emrys/contracts/orchestration/api.py) requires exact registered `$id`s; the [artifact loader](../../src/emrys/contracts/artifacts/_artifact_contracts/schema.py) requires nonempty IDs and closes public selectors separately. | Check whether any registry consolidation preserves the different selector, error, and semantic-admission contracts while reducing total code. |
| S04 — Production consumers | Partial | Artifact entries feed the Run summary and reporting. Project setup, normalization, materialization, Task execution, lifecycle, and reporting boundaries write orchestration records; inspection and reporting read admitted records. | Complete a per-record writer/reader table covering public CLI, installed wheel, direct, Slurm, resume, report, fixtures, and documented integrations. Record negative searches. |
| S05 — Package and Run identity | Observed | [Package-data globs](../../pyproject.toml) cover seven schema directories, and the [wheel resource roster](../../tests/test_package_distribution.py) names all 20 files. Twelve orchestration schema paths are explicitly included in [Run implementation identity](../../src/emrys/orchestration/run_coordinator/run_implementation.py). All 20 packaged resources also affect the installed-package tree digest recorded by new workflow Attempts. The other eight do not enter the explicit Run admission-root list; `execution_profile` is still an active validator and Attempt-placement input. | Determine whether that Run-root omission is intentional before claiming a defect. Inventory retained identities before selecting a migration. |
| S06 — Prerelease distribution | Partial | The package declares Alpha and `0.1.0.dev0`. On 2026-09-22, the exact PyPI project lookup returned 404, and GitHub listed no releases or tags. The [Quickstart](../../quickstart.md) documents source installation. A wheel test and public CLI, artifact-validation, provider and reporter interfaces establish supported external surfaces, not observed third-party use. | Inventory known collaborators, source installs, private distributions, and downstream readers. The checked public channels do not prove absence of external consumers. |
| S07 — Retained Runs | Partial | Tracked `Projects/` contains only placeholders and Project data is ignored by Git. The [campaign record](backlog_matrix.md#viking-walkthrough-findings) reports actual-data Runs, including an unresolved cancelled Run and replacement at the time of that report. Their present locations, versions, and recovery needs were not inspected. | Obtain owner-identified locations or a bounded inventory. Inspect version and identity metadata read-only without changing or copying scientific data. |
| S08 — Version-support boundaries | Observed | The [approved policy](../design/decisions/platform-direction.md#version-support) rejects obsolete Run records, preserves retained evidence, and requires full checks for current-format recovery. The Project v1 schema has two current forms, provider v1 metadata remains admissible while v1 execution is not, and a separate submission-request reader accepts v1–v4 retained diagnostics with narrower stop authority. | Treat each as its own contract; do not group current forms, diagnostic readers, and historical fixture names into one obsolete-alias category. |
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

### Field use, identity, and defense

The packaged processing profile contains 12 owner tasks and 57 artifact
templates; a composed built-in profile test expects 70 templates. The
[functional projection](../../src/emrys/contracts/orchestration/application_model.py)
keeps owner keys, steps, and scope types, template identity fields, edges,
required owners, and evidence owners. It omits `semantic_owner_keys`,
`rule_name`, and both selectors. This does not make those omitted fields inert:
the exact canonical profile is written to `contract/profile.json` and its hash
is recorded in each workflow Attempt. The [implementation identity](../../src/emrys/orchestration/run_coordinator/run_implementation.py)
also binds the packaged base profile, its schema, and backend bytes. A field
or schema migration can therefore change new Run and Attempt identities even
when the projected functional value is unchanged. Existing snapshots must not
be rewritten to make a new contract appear compatible.

The profile validator requires `semantic_owner_keys` and
`required_owner_keys` to equal the full set of profile owners. The immutable
Run's `required_owner_keys` is a different functional field: it may be a subset
under its [application-model rules](../../src/emrys/contracts/orchestration/application_model.py)
and drives stopping, reuse, and Task admission. Deriving the profile roster is
therefore a narrower question than removing the Run field. The packaged
profile's authored order is also independently compared with `STAGE_MAP` by
the [profile tests](../../tests/orchestration/run_coordinator/test_profile.py); a
transition must move that defense to a surviving authority.

The backend builds processing rules from the installed base profile, then
checks the retained Run profile against an independent fixed owner/step/rule
projection in the [Snakefile](../../src/emrys/workflow/Snakefile). An
adversarial [workflow test](../../tests/orchestration/run_coordinator/test_workflow.py) swaps two same-scope
owner keys under unchanged rule names and expects refusal. Deriving rule
names solely from each supplied profile's keys would make that check
self-confirming. Any replacement needs an independently pinned mapping and
the same refusal. Analysis-tail rules have a different, generated naming path
and use the generic backend analysis owner rule.

For both selector fields, the validator defines a total five-scope mapping.
The owner selector participates in the independent backend check. The
template selector drives first-seen grouping and output order in
[inventory expansion](../../src/emrys/contracts/orchestration/artifact_inventory.py),
which also rejects mismatches and reopened groups. Derivation must preserve
those rows, ordering, and refusals. The adjacent `workflow_inputs["profile"]`
triplet is a private generated projection in
[normalization](../../src/emrys/orchestration/run_coordinator/normalization.py);
the repository search found no production lookup. External Python use has
not been established or excluded, so this is a separate reduction candidate.

### Consumer and retained-record premise

The source package declares an `emrys` command and analysis-provider and
reporter entry-point groups in [package metadata](../../pyproject.toml).
An [isolated-wheel test](../../tests/test_package_distribution.py) checks
resource packaging and the installed command away from the checkout. These
demonstrate an intended packaged interface; they do not demonstrate an
uploaded release or an actual collaborator install. The loader accepts entry
points from distinct installed distributions, and `emrys validate
artifact-contracts` is a public route. The [extension card](polish-campaign.md)
still calls for a separately installed collaborator example. Known external
readers, private distributions, and source installations remain uncounted.

Only `Projects/.gitkeep` and `Projects/README.md` are tracked in that tree;
the [Project guidance](../../Projects/README.md) and `.gitignore` keep study
children off Git. A [Viking walkthrough entry](backlog_matrix.md#viking-walkthrough-findings)
records actual-data Run state at its observation time. It does not establish
today's storage path, record version, or recovery disposition. A reset decision
needs a bounded owner-identified metadata inventory, without copying payloads.

The current [version policy](../design/decisions/platform-direction.md#version-support)
rejects obsolete Run formats while retaining evidence and full current-format
recovery. Its neighboring cases are not interchangeable: Project v1 accepts
flat paired-CMH and explicit-module forms; provider v1 metadata can be read
but v1 workers cannot execute; the non-registry Slurm submission-request
reader accepts v1–v4 for diagnostics while stop requires a complete v3/v4
named request. Current Execution Plan v1 also permits an absent optional
reference parameter. Older-named fixture directories contain current
artifact records and explicitly disclaim production evidence. None of these
observations alone justifies deleting a reader or resetting a schema ID.

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

### Packaged record paths

This source-level map names production producers and readers rather than
treating a registered schema as proof that a serialized record is used. All
20 resources are installed and loaded; the two `common` resources are
definition-only. The 15 orchestration selectors include `application-model`,
which admits three current labels: analysis revision v2, Execution Plan v1,
and Run binding v1. The three artifact selectors have separate public
validation. This map does not establish external use or complete route parity.

| Resource | Producer or source | Current reader or boundary |
| --- | --- | --- |
| Artifact `common` | Definitions; no standalone record | All three artifact schemas; run-contract wrapper in the artifact index; installed-package definition from orchestration common |
| Artifact `artifact_record` | Artifact-index record builder | Nested in Run summary; standalone artifact-contract CLI validation |
| Artifact `run_summary` | Reporting summary document builder | Reporting context, transaction revalidation, public artifact-contract CLI |
| Artifact `report_receipt` | Reporting receipt builder | Receipt/transaction revalidation, public artifact-contract CLI |
| Orchestration `common` | Definitions; no standalone record | Referenced by 13 orchestration resources and artifact common |
| `project` | User-authored or onboarding-built Project YAML | Normalization, run control, and onboarding preview admission |
| `resource_config` | Packaged defaults or user override | Resource policy/effective-profile admission; Run policy and backend recheck |
| `execution_profile` | Packaged or Project YAML; effective profile | Placement admission and Attempt hashes; workflow-attempt schema reference |
| `profile` | Packaged base plus analysis composition | Normalization; canonical Run snapshot; backend, inspection, lifecycle, Task, reporting |
| `application_model` | Application-model constructors; three records under `contract/` | Canonical record checks and inspection admission |
| `reference` | Normalization from Project reference | Project/application-model references; backend and reporting projections |
| `policy` | Normalized module policy | Attempt-local and reporting projections; summary and report context |
| `run_lock` | Run lifecycle lock projection | Inspection, admission, and lifecycle recovery |
| `workflow_attempt` | Run materialization | Lifecycle, backend, inspection, Task, reporting |
| `attempt_receipt` | Attempt lifecycle closure | Inspection/admission and reporting boundary |
| `task_start` | Task owner | Task admission and lifecycle-linked receipt |
| `task_attempt` | Task owner | Task admission, verified Task, and Attempt receipt linkage |
| `verified_task` | Task owner | Task recovery and Attempt receipt linkage |
| `reporting_start` | Reporting boundary | Reporting ledger recovery and verification |
| `verified_reporting` | Reporting boundary | Reporting ledger inspection and verification |

The producer/reader anchors are [artifact index and reporting](../../src/emrys/reporting/),
[orchestration registry](../../src/emrys/contracts/orchestration/api.py),
[normalization](../../src/emrys/orchestration/run_coordinator/normalization.py),
[materialization](../../src/emrys/orchestration/run_coordinator/materialization.py),
[Task ownership](../../src/emrys/orchestration/run_coordinator/task.py),
[lifecycle](../../src/emrys/orchestration/run_coordinator/lifecycle.py),
[reporting boundary](../../src/emrys/orchestration/run_coordinator/reporting_boundary.py),
and the [backend](../../src/emrys/workflow/Snakefile).
[Orchestration fixture tests](../../tests/contracts/orchestration/test_orchestration_contracts.py),
[artifact schema fixtures](../../tests/contracts/artifacts/test_artifact_schema_contracts.py),
[independent goldens](../../tests/contract_integration/independent_contract_goldens/),
and [wheel tests](../../tests/test_package_distribution.py) cover different
surfaces; they are not evidence of real retained-record or external-consumer
counts. A source search found no direct packaged-schema path or `$id`
reference in `scripts/` or `.github/`; a CI profile-version literal is a
separate check. The Slurm submission-request
versions are a separate non-registry reader in
[Slurm submission handling](../../src/emrys/orchestration/run_coordinator/slurm_submission.py).

The `$ref` closure is also bounded: artifact common refers to orchestration
common; artifact entry to artifact common; Run summary to artifact entry and
artifact common; receipt to artifact common. Orchestration application model
refers to common, reference, and resource config; Project to common and
reference; workflow Attempt to common and execution profile; execution
profile to resource config. Every external reference base found in the 20
resources resolves within their packaged set. Removing or renaming a shared
resource therefore requires a caller-complete reference and wheel migration,
even if that resource has no standalone serialized record.

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
