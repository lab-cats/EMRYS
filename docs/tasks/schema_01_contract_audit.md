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
| S02 — Version identity | Observed | Nine current resources already have v1 `$id`s; 11 do not (three artifact and eight orchestration). Packaged directory numbers, `$id` versions, and serialized record versions differ in current files. The [schema owner](../../src/emrys/contracts/schemas/README.md#version-and-identity-rules) says directory numbers span separate families and participate in resource paths and references. | Give each kind of version and path a separate disposition; do not rename directories for visual consistency. |
| S03 — Registry and references | Observed | Artifact common definitions reference orchestration common's installed-package definition. All external `$ref` bases in the 20 files resolve within this set. [Orchestration](../../src/emrys/contracts/orchestration/api.py) requires exact registered `$id`s; the [artifact loader](../../src/emrys/contracts/artifacts/_artifact_contracts/schema.py) requires nonempty IDs and closes public selectors separately. | Check whether any registry consolidation preserves the different selector, error, and semantic-admission contracts while reducing total code. |
| S04 — Production consumers | Partial | The per-resource map below identifies producers and readers. Direct and delegated Slurm scientific execution share Run/Attempt/Task writers; resume re-admits the immutable Run. Automatic and standalone reporting share report producers. Head-node submission requests and reporting ledgers have distinct boundaries. | Recheck each selected change against direct, Slurm, resume, standalone report, public CLI, installed wheel, fixtures, and known integrations. Obtain exact-head route results before claiming parity. |
| S05 — Package and Run identity | Observed | [Package-data globs](../../pyproject.toml) cover seven schema directories, and the [wheel resource roster](../../tests/test_package_distribution.py) names all 20 files. Twelve orchestration schema paths are explicitly included in [Run implementation identity](../../src/emrys/orchestration/run_coordinator/run_implementation.py). All 20 packaged resources also affect the installed-package tree digest recorded by new workflow Attempts. The other eight do not enter the explicit Run admission-root list; `execution_profile` is still an active validator and Attempt-placement input. | Determine whether that Run-root omission is intentional before claiming a defect. Inventory retained identities before selecting a migration. |
| S06 — Prerelease distribution | Partial | The package declares Alpha and `0.1.0.dev0`. On 2026-09-22, the exact PyPI project lookup returned 404, and GitHub listed no releases or tags. The [Quickstart](../../quickstart.md) documents source installation. A wheel test and public CLI, artifact-validation, provider and reporter interfaces establish supported external surfaces, not observed third-party use. | Inventory known collaborators, source installs, private distributions, and downstream readers. The checked public channels do not prove absence of external consumers. |
| S07 — Retained Runs | Partial | Tracked `Projects/` contains only placeholders and Project data is ignored by Git. The [campaign record](backlog_matrix.md#viking-walkthrough-findings) reports actual-data Runs, including an unresolved cancelled Run and replacement at the time of that report. Their present locations, versions, and recovery needs were not inspected. | Obtain owner-identified locations or a bounded inventory. Inspect version and identity metadata read-only without changing or copying scientific data. |
| S08 — Version-support boundaries | Observed | The [approved policy](../design/decisions/platform-direction.md#version-support) rejects obsolete Run records, preserves retained evidence, and requires full checks for current-format recovery. The Project v1 schema has two current forms, provider v1 metadata remains admissible while v1 execution is not, and a separate submission-request reader accepts v1–v4 retained diagnostics with narrower stop authority. | Treat each as its own contract; do not group current forms, diagnostic readers, and historical fixture names into one obsolete-alias category. |
| S09 — Existing protection | Observed | Source tests assert exact closed registration and references, strict JSON refusal, profile graph/order/scope rules, independent backend owner mapping, obsolete Attempt refusal, retained Run recovery, content-bound identity, independent artifact goldens, and installed wheel resources. Test presence and assertions were inspected, but results at this revision were not. | Map each selected change to a surviving defense at the same trust boundary. Run focused checks on an approved implementation and long lanes in CI. |
| S10 — Reduction opportunities | Partial | Both registries repeat strict JSON parsing and Draft 2020-12 setup, but differ in exact-ID enforcement, selectors, diagnostics, and semantic admission. Artifact and orchestration common definitions share only two identical small shapes. A private generated profile triplet has no found production lookup. Raw overlap is not net savings. | Prototype caller-complete savings before sharing machinery or definitions. Inventory tests, scripts, configuration, docs, compatibility, and mutable state separately; retain independent evidence. |
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
| Adjacent `validate_record(..., profile=...)` | The orchestration API includes this optional parameter and serializes it into the successful-validation cache key, but the called record validator does not read it. Inspection forwards it, while a separate successor-Run check actually validates Run/profile consistency. This is an API/cache candidate, not a schema field. | Inspect external Python callers and error precedence before removing the parameter or cache dimension. Preserve the separate successor-Run admission. |

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

The 12 explicit [Run admission roots](../../src/emrys/orchestration/run_coordinator/run_implementation.py)
are `application_model`, orchestration `common`, `policy`, `reference`,
`run_lock`, `task_attempt`, `task_start`, `verified_task`, `workflow_attempt`,
`attempt_receipt`, `profile`, and `resource_config`. The eight omitted
packaged resources are all four artifact schemas plus `project`,
`reporting_start`, `verified_reporting`, and `execution_profile`. They remain
active package resources: [installed-package identity](../../src/emrys/libraries/installed_package_identity.py)
digests the package tree for new Attempts; the execution-profile schema
validates selected YAML and is a workflow-attempt `$ref`, and its effective
profile/source hashes bind placement. Omission from the Run-root list is not
evidence that a resource is unused or safe to rename.

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

### Existing defenses and maintenance surface

These are source-inspected assertions, not test results for this revision.
The [orchestration contract tests](../../tests/contracts/orchestration/test_orchestration_contracts.py)
check the closed Draft 2020-12 registry, exact `$id` and path examples, local
references, unknown selectors, duplicate keys, and nonstandard numeric
constants. The [artifact contract tests](../../tests/contracts/artifacts/test_artifact_schema_contracts.py)
check their distinct closed registry, local references, public validation,
and strict JSON refusals. The profile tests also reject owner-count and
required-set drift, duplicate rule names, selector mismatches, cycles, and
reopened artifact groups. The independent stage map and backend swap test
protect a different boundary from schema validity alone.

The [Task tests](../../tests/orchestration/run_coordinator/test_task.py)
refuse an obsolete Attempt before mutation. The
[materialization tests](../../tests/orchestration/run_coordinator/test_materialization.py)
cover identity changes from schema/admission bytes and a new edge drift
alongside an unchanged retained Run. The
[lifecycle tests](../../tests/orchestration/run_coordinator/test_lifecycle.py)
exercise tree/log tamper refusal in recovery. The
[wheel tests](../../tests/test_package_distribution.py) check the entire
packaged schema roster and byte equality, then install and invoke an isolated
wheel. Independent [artifact goldens](../../tests/contract_integration/independent_contract_goldens/)
give a separate semantic comparison. No single one of these substitutes for
the others or for retained-record and institutional evidence.

At the target revision, the schema surface is 20 files, 3,105 physical lines,
and 90,500 bytes: artifact resources are 4 files/733 lines/21,650 bytes;
orchestration resources are 16 files/2,372 lines/68,850 bytes. This is a
baseline, not a proposed deletion count. The artifact loader's
[schema setup](../../src/emrys/contracts/artifacts/_artifact_contracts/schema.py)
and [orchestration registry](../../src/emrys/contracts/orchestration/api.py)
both use standard-library strict JSON hooks and existing `jsonschema` and
`referencing` machinery. Their error and selector policies are not identical.
The artifact loader requires a nonempty `$id` and lets its direct validator
look up registry keys; its public CLI restricts selection to the three record
schemas. Orchestration checks each exact registered `$id`, rejects names
outside its 15 public selectors, and caches validators and successful
canonical-record validation. Artifact schema errors return sorted validation
objects before CLI formatting; orchestration returns sorted rendered messages.
Their `ContractValidationError` base classes and diagnostics differ, and each
owner applies its own semantic admission after JSON Schema. A shared helper
would have to preserve those policies, failure precedence, and direct callers
while reducing total maintained code.
The only structurally identical cross-family common definitions are `safe_id`
and `sha256`, about eight lines total in artifact common, with 15 local
references; moving them would not retire either common resource. Other
same-named definitions differ. Canonical JSON helpers elsewhere differ in
output bytes or NaN policy and are not yet equivalent-input duplicates.

The source-level candidate `workflow_inputs["profile"]` has roughly seven
authored construction lines plus one dictionary entry, but the whole input
map is propagated. A removal needs an API and equality review even if no
literal production lookup exists. No caller-complete product-code saving is
established yet. The [schema owner](../../src/emrys/contracts/schemas/README.md)
already delegates registration to its two owners, and the
[topology guardrails](../../src/emrys/contracts/SOURCE_TOPOLOGY.md) require
equivalent behavior before policy sharing. A third registry or custom
validator framework has no demonstrated capability gap.

Another bounded candidate is the optional `profile` parameter on
[orchestration record validation](../../src/emrys/contracts/orchestration/api.py).
The current validator passes it through a cache key but does not consult it
for a record decision. [Inspection](../../src/emrys/orchestration/run_coordinator/_inspection_admission.py)
forwards the parameter, then separately performs the actual cross-record
Run/profile admission. Removing the unused cache dimension could reduce code,
but public Python callers and error precedence have not been audited. This
candidate must not be confused with the independent successor-Run protection.

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

### Reset decision worksheet

This is a scope split, not a recommendation to change any resource. A v1
`$id` says nothing by itself about every serialized label inside a schema.

| Resource group | Source-bound impact of a selected reset | Current disposition |
| --- | --- | --- |
| Nine resources with v1 `$id`s | No `$id` reset to v1 is needed. `application_model` still contains three separately versioned current records; `execution_profile` sits in packaged `v3` while its ID is v1. Directory names remain resource paths. | Retain current IDs pending any independently justified format change. |
| Three artifact resources with non-v1 `$id`s | Artifact entry is nested in Run summary; summary and receipt serialize `8.0.0`. A selected change would touch reporting writers/readers, public artifact validation, references, fixtures, independent goldens, wheel resources, and Attempt package provenance. They are not explicit Run admission roots. | Open until actual consumer and reporting impact is bounded. |
| Seven non-v1 orchestration Run roots | `run_lock`, `task_attempt`, `task_start`, `verified_task`, `workflow_attempt`, `attempt_receipt`, and `profile` enter the explicit Run implementation closure. A selected path or byte change affects new Run identity and current-format recovery comparisons. | Open until retained state, all callers, and surviving defenses are bounded. |
| Non-v1 `reporting_start` | Reporting ledger writer/reader and installed-package provenance depend on it, while the explicit Run-root list omits it. | Open as a reporting/recovery decision, not an inferred Run-ID change. |

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

### Direct, Slurm, resume, and reporting routes

The public [control owner](../../src/emrys/orchestration/run_coordinator/control.py)
funnels `run` and `resume` through shared planning. Direct execution and a
Slurm delegate call the same Run admission, Attempt publication, lifecycle,
and Task owners. Slurm submission first admits the Project for duplicate
intent screening, writes a separate `emrys.submission-request.v4`, and
re-enters `emrys run|resume|report --execute` in the allocation. That request
is outside the 20 packaged schemas; shared scientific writers do not settle
its version or head-node diagnostics.

| Route | Shared record authority | Distinct boundary or open evidence |
| --- | --- | --- |
| Initial direct Run | Materialization writes analysis, Execution Plan, Run binding, profile, and workflow Attempt; lifecycle and Task owners write receipts and Task records. | Source and focused tests identify the path; exact-head runtime result was not run here. |
| Delegated Slurm Run | Re-enters the same scientific writers after scheduler placement and allocation checks. | Submission request and placement are route-specific; a scheduled CI driver is not proof it ran for this head. |
| Resume | Re-admits the immutable Run and predecessor compatibility before a successor Attempt/Task chain; a prepared-receipt path may finalize without a new Attempt. | It cannot rewrite Run authority; retained real recovery status remains unknown. |
| Automatic or standalone report | Both call [reporting operation](../../src/emrys/orchestration/run_coordinator/reporting_operation.py), which inspects admitted Run/Attempt state and writes Run summary, artifact records, receipt, and ordered reporting ledgers. | Standalone report creates no scientific Attempt; Slurm report delegates to the same owner. |

[Focused route tests](../../tests/orchestration/run_coordinator/test_materialization.py)
cover direct/Slurm planning, delegated report, and prepared resume.
[Reporting tests](../../tests/orchestration/run_coordinator/test_reporting_operation.py)
cover reuse, partial refusal, preview, and ledger order. The
[real-tool driver](../../tests/tools/real_synthetic_e2e.py) contains
direct/Slurm and interrupted/resumed comparisons, but its CI lane is
conditional and a source search found no standalone `emrys report` command
in that driver. These are inspected test designs, not exact-head pass results
or institutional parity evidence.

The `$ref` closure is also bounded: artifact common refers to orchestration
common; artifact entry to artifact common; Run summary to artifact entry and
artifact common; receipt to artifact common. Orchestration application model
refers to common, reference, and resource config; Project to common and
reference; workflow Attempt to common and execution profile; execution
profile to resource config. Every external reference base found in the 20
resources resolves within their packaged set. Removing or renaming a shared
resource therefore requires a caller-complete reference and wheel migration,
even if that resource has no standalone serialized record.

## Fine-grained audit plan and decision gate

The states below describe audit progress at the pinned source revision, not
SCHEMA-01 acceptance. Repeat the revision comparison if the target PR head
advances before deciding; record the changed files and refresh affected rows.

| Pass | Current state | Bounded work and output | Decision gate |
| --- | --- | --- | --- |
| P0 — Revision | Done | Pin PR #307 head, base comparison, and schema-source delta; keep the audit PR's own head separate. | Recheck live Git before a final decision. |
| P1 — Resources | Done | Inventory all 20 paths, `$id`s, serialized labels, selectors, common resources, external `$ref` edges, package globs, wheel roster, and direct Run roots. | No path or version reset from directory appearance alone. |
| P2 — Production closure | Partial | For each record, close writer, direct/Slurm submission, resume/inspection, reporting, public validation, fixture, and reference paths. Mark definition-only resources and non-registry versioned records separately; confirm negative searches. | Do not call a field or resource dead from its absence in one caller family. |
| P3 — Consumers | Partial | Reconcile source installs, collaborator entry points, private distributions, public artifacts, exported schemas, and known downstream code with the owner. Record an observed reader, a bounded negative, or unknown for each route. | A missing public release does not prove a closed audience. |
| P4 — Retained state | Open | With owner-supplied Project locations, inventory only record labels, schema IDs, implementation/package/profile hashes, and recovery status; preserve payloads and markers. | No reset choice until affected recovery/evidence classes are bounded, or explicitly recorded unknown. |
| P5 — Field semantics | Partial | For each candidate, identify sole semantic authority, current producer and reader, derived value, independent refusal, ordering, and functional/profile byte effects. Compare tiny representative base and composed profiles without editing retained Runs. | A derivation is accepted only if graph, uniqueness, scope, inventory bytes, backend names, and direct/Slurm behavior survive. |
| P6 — Identity and recovery | Partial | Trace `$id`, packaged path, Run implementation/Plan identity, Attempt package/profile identity, installed wheel, current-format recovery, report revalidation, and incompatible-record refusal for each proposed change. | Keep old evidence immutable; do not infer recovery from schema validity or a receipt. |
| P7 — Compression | Partial | Count a proposed migration's product files/lines separately from tests, scripts, config, docs, and evidence. Compare existing owner code, standard library, `jsonschema`/`referencing`, and maintained tools. Audit every duplicate caller and retirement path. | Require meaningful caller-complete net product reduction or a quantified, explicitly approved exception; no evidence deletion as an offset. |
| P8 — Decision | Open | Compare retain-current, selected field transition, and selected v1 reset per resource. Record consumer impact, required new IDs/record labels, parity defenses, migration scope, compatibility policy, cost, and rejected options. Keep product 1.0 a separate release decision. | An owner-reviewed selected outcome and separate bounded implementation authority are required before changing schemas or callers. |
| P9 — Proof for an approved migration | Not started | On the selected implementation revision, run focused source/fixture/wheel checks locally, long checks in CI, then request separately authorized real/site evidence where required. Compare new records and retained current-format recovery at exact identities. | Local, hosted, institutional, scientific-review, and biological claims remain distinct. |

Current decision options are intentionally asymmetric. Retaining existing IDs
may be the correct outcome even if a private projection can be retired under a
different reduction owner. A targeted profile transition must preserve the
independent backend and inventory checks and cannot use a compatibility writer
just for cleanup. A selected v1 reset must name its exact resources, paths,
serialized labels, readers, writers, and rejection behavior; it cannot be a
blanket rename of all `v2`/`v3`/`v5` directories. Any implementation must
move all affected current callers together, reject incompatible records
without modifying evidence, and avoid unnecessary aliases or historical
readers.

Stop a decision when a consumer, field meaning, recovery behavior, required
defense, or maintenance exception cannot be bounded from available evidence.
No identifier reset, field deletion, cluster proof, scientific review, or
evidence promotion is implied by this audit record.
