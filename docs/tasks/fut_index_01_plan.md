# FUT-INDEX-01: supplied STAR index investigation and draft plan

This is a planning companion to the [FUT-INDEX-01 backlog row](backlog_matrix.md#platform-operation-and-portability). The backlog remains the authority for outcome, status, priority, and acceptance. This document records source findings, design questions, and a proposed implementation sequence; it does not change the accepted contract or authorize implementation.

## Audit basis and intended outcome

- Source target: [PR #307](https://github.com/lab-cats/EMRYS/pull/307) head f32260f0408fe1826af401fc1ddce0f2478ae6ce, the newest open PR head when checked on 2026-09-22. It directly follows [PR #304](https://github.com/lab-cats/EMRYS/pull/304) head 3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d; its only changed files concern Doctor timing evidence, not the FUT-INDEX-01 owners reviewed here. Recheck the live head and affected diff before implementation.
- Accepted outcome: an externally supplied prebuilt STAR index is an explicit Project input. Bind every required member to exact hashes, the matching FASTA/GTF identity, and STAR parameters and version. Reuse it without generating, repairing, merging, or mutating it. Directory presence alone cannot admit it.
- Existing processing-Run reuse and standalone index validation are delivered but do not admit an external index. Reference/read acquisition remains under FUT-DATA-02.
- The current generated-index path, public contracts, recovery evidence, and scientific interpretation boundaries are preservation requirements. No Run may change its immutable plan in place.

## Findings matrix

The matrix records investigation findings, not task status or acceptance. “Observed” is tied to the source snapshot above. “Direction” is a proposal to test, not an accepted design.

| ID | Finding | Observed at the target head | Direction or unresolved question |
| --- | --- | --- | --- |
| F01 | Project input has no supplied-index declaration | Closed Project and Reference schemas accept FASTA, GTF, and three STAR construction values; normalization snapshots FASTA/GTF only. | Decide one optional, explicit source declaration without overloading the numeric construction policy. |
| F02 | Existing validation does not prove build-source bytes | The seven Step 00a checks compare historical source paths, contigs, and three values, but not build-time source or index hashes. Exact path comparison can reject a relocated but content-identical source. | Define a fail-closed historical-provenance rule and decide whether original paths are required or hashes govern relocation. |
| F03 | Native version and generation settings are incomplete proof | Runtime STAR is pinned to 2.7.11b, but its identity does not prove the external producer. versionGenome is a compatibility floor; native metadata omits some effective generation choices. | Specify the admitted producer evidence, a closed recipe, and distinct producer/runtime version checks. |
| F04 | The whole directory matters | Fifteen files are required, but STAR may add files; the producer permits an empty extra while Stage 01 Task admission rejects it. Task rechecks top-level members at boundaries, not continuously during STAR reads. | Bind complete membership and bytes; settle extras, canonical paths, nesting, concurrent writes, and drift. |
| F05 | The graph unconditionally constructs Stage 00a | The built-in profile, profile-vs-installed-graph check, expected-Task roster, planner, and Snakemake owner projection include construction. | Route one source mode consistently through graph admission and execution, with no fabricated Stage 00a Task. |
| F06 | Immutable identities omit supplied-index content | Reference scope uses FASTA/GTF; Run and processing identities have no supplied-index fingerprint. Resume recomputes Run binding, and processing reuse currently collects verified Task outputs only. | Bind mode/content in immutable identities; settle relocation, retained Task inputs, and reuse re-admission. |
| F07 | External storage crosses lifecycle boundaries | Attempt planning indexes admitted external files, not a directory manifest; Task can recheck an input directory only when Stage 01 declares it. | Keep the index an external input, bind its member inventory into planning and Task/recovery admission, and diagnose inaccessible storage. |
| F08 | Artifact and report contracts assume generated 00a products | Inventory rows derive from the Run profile; absent 00a rows need no 00a roster, but the installed adapter registry still recognizes generated 00a products. Reporting hashes the reference contract. | Keep external input provenance distinct from produced artifact rows and avoid accidental path-sensitive report identity. |
| F09 | Guided creation has no supplied-index journey | Init freezes three STAR values and has a no-write preview and one creation admission path. | Decide how the optional index and provenance appear in preview, creation, validation, and ordinary Run output. |
| F10 | New machinery would increase maintenance unless consolidated | Stable hashing, directory enumeration, STAR parsers, Task binding, and owner tests already exist. | Reuse them, audit duplicate mechanics and retire only proved redundancy; quantify any product-growth exception. |
| F11 | Verification needs boundary and evidence separation | Current tests protect generated-index validation, materialization, graph, drift, and reporting at distinct levels. | Add focused supplied-mode fault cases and state local, CI, real STAR, Slurm, and institutional evidence separately. |

## Source-grounded discoveries

### F01 — Authored and normalized input

The [Project schema](../../src/emrys/contracts/schemas/orchestration/v1/project.schema.json) closes reference to FASTA, GTF, and star_index. The [Reference schema](../../src/emrys/contracts/schemas/orchestration/v1/reference.schema.json) closes star_index to sjdb_overhang, genome_sa_index_nbases, and optional genome_chr_bin_nbits. [Normalization](../../src/emrys/orchestration/run_coordinator/normalization.py) snapshots the two reference files and carries a closed numeric STAR policy. Named creation derives and freezes all three settings; existing hand-authored Projects that omit the chromosome-bin value normalize to 18 without rewriting them ([configuration guide](../../configs/README.md)).

**Proposed direction:** keep source selection separate from these construction numbers so existing Projects retain their meaning. A possible authored shape is one optional supplied-index object containing an explicit directory and provenance path. Field names, schema version effect, all writers/readers, and whether a separate provenance file is justified remain open. New public fields require explicit approval.

### F02 — Content and historical provenance

The [Stage 00a validator](../../src/emrys/stages/star_index/validator.py) checks seven identities: required members, FASTA and GTF paths recorded in genomeParameters.txt, ordered contig names and lengths, and the three numeric settings. It does not compare FASTA/GTF content hashes to build-time hashes, fingerprint every index member, or establish the exact producer release. A validation mismatch may appear as a failed report row rather than a nonzero process exit; a caller must inspect every required row. The current Run Task separately invokes semantic all-pass after validation, so the standalone command's exit behavior is an admission concern, not an identified Run bypass.

[STAR 2.7.11b writes](https://raw.githubusercontent.com/alexdobin/STAR/2.7.11b/source/genomeParametersWrite.cpp) source path strings, settings, and output sizes, without source-content digests. Matching present-day paths and contig lengths cannot prove which exact sequence and annotation bytes generated a historical index. [Project normalization](../../src/emrys/orchestration/run_coordinator/normalization.py) hashes the current FASTA/GTF bytes, but those hashes have no retained build-time counterpart for an external index.

The validator requires native `genomeFastaFiles` and `sjdbGTFfile` paths to resolve to the current Project paths. A relocated index and content-identical current references can therefore fail its path rows. Preserve the existing seven check IDs and generated-mode meaning; decide whether supplied admission requires original paths or treats those native paths as historical corroboration while comparing retained build-time hashes with present bytes. In the latter case, supplied admission cannot simply require all seven old rows to pass unchanged.

**Proposed direction:** require retained build provenance captured during generation with FASTA/GTF SHA-256, complete member hashes, producer release, effective generation settings, and provenance origin. Independently rehash present files and compare that record with native metadata. A supplier-authored manifest is an assertion about history, even when EMRYS verifies its present bytes. Decide whether that assertion meets admission policy; a post hoc manifest alone cannot establish historical causation. No arbitrary index should pass solely because it exists or passes the seven current checks.

### F03 — Exact version and closed recipe

The installed [runtime policy](../../src/emrys/resources/runtime/runtime_policy.tsv) requires STAR `2.7.11b`. [Doctor](../../src/emrys/orchestration/run_coordinator/doctor.py) records the observed runtime version, canonical executable path, and binary SHA-256; [processing identity](../../src/emrys/contracts/orchestration/application_model.py) binds tool content. These facts identify the admitted runtime, not the external producer.

STAR's [versionGenome default](https://raw.githubusercontent.com/alexdobin/STAR/2.7.11b/source/parametersDefault) is `2.7.4a` for release `2.7.11b`: it marks the earliest compatible index version, not the exact producer release. Requiring it to equal `STAR --version` would reject a normal index. The native [metadata writer](https://raw.githubusercontent.com/alexdobin/STAR/2.7.11b/source/genomeParametersWrite.cpp) includes an override-command line; the tagged [parameter reader](https://raw.githubusercontent.com/alexdobin/STAR/2.7.11b/source/Parameters.cpp) constructs that line from user overrides rather than a closed effective recipe. A retained producer `Log.out` reports release/build text but remains supplier evidence, not cryptographic proof linking that release to these bytes.

Other index-affecting settings and inputs include suffix-array sparsity, genome transformation, extra splice-junction sources, and GTF feature/tag choices. One concrete gap is `genomeSuffixLengthMax`: the tagged [generator](https://raw.githubusercontent.com/alexdobin/STAR/2.7.11b/source/Genome_genomeGenerate.cpp) uses it during suffix-array construction, yet the metadata writer has no dedicated row for it. The [current worker](../../src/emrys/stages/star_index/step_00a_build_star_index.sh) passes the three explicit Project values to STAR genome generation.

**Open decision:** define the supported externally generated recipe, including acceptable defaults and whether extra inputs or transformations are rejected. For a first fail-closed route, require a declared exact producer release matching the admitted runtime STAR release unless a separately reviewed compatibility rule is supported. Decide what producer-origin record and attestation are sufficient. Keep the producer claim, native compatibility marker, and observed runtime identity separate.

### F04 — Directory closure and change detection

The [stage contract](../../src/emrys/stages/star_index/CONTRACT.md) lists fifteen nonempty regular members as the protected minimum and permits additional native files. The [alignment worker](../../src/emrys/stages/star_alignment/step_01_star_align.sh) passes the entire directory as genomeDir. The Stage 00a producer accepts an empty extra regular file, while [Stage 01 Task directory admission](../../src/emrys/orchestration/run_coordinator/task.py) rejects any empty member. Supplied-mode policy must settle this existing cross-boundary difference without silently changing generated-mode behavior.

The Task boundary enumerates and content-snapshots every top-level input-directory member when that directory is planned as a Task input, then rechecks at producer entry, after the producer and validator, and during later verified-Task admission. It does not bind an external directory into Project or Run identity or continuously freeze shared storage while STAR reads. The [shared input helpers](../../src/emrys/libraries/validation/inputs.py) support stable, no-follow directory listing and streamed hashing. Project normalization accepts lexical absolute paths, whereas Task input directories must be real canonical paths; external admission should diagnose that mismatch before creating a Run.

**Proposed direction:** admit a deterministic ordered inventory of every present top-level regular member, require the fifteen named members, and bind each name, size, and SHA-256. Reject links and unsafe nesting unless source review demonstrates a required supported STAR form. Put the provenance record outside the indexed directory to avoid self-reference in a complete inventory. Recheck membership and bytes at existing trust boundaries, and state the residual concurrent-writer risk and required storage policy. Measure repeated hashing cost on representative shared storage before a performance claim.

### F05 — Graph and worker authority

The [semantic stage map](../../src/emrys/contracts/STAGE_MAP.md) describes external inputs as having no producer node and currently has a direct Stage 00a-to-01 index edge. The [built-in profile](../../src/emrys/workflow/contracts/local_cmh_v2.json) requires construction and its artifacts. [Materialization](../../src/emrys/orchestration/run_coordinator/materialization.py) always builds a Stage 00a producer command into a create-absent Run directory; Stage 01 reads the resulting path.

At planning, [profile validation](../../src/emrys/contracts/orchestration/artifact_inventory.py) compares processing edges with the installed task graph. The [Snakemake graph](../../src/emrys/workflow/Snakefile) then checks a static complete processing-owner projection and builds rules from installed processing tasks. The [expected-Task roster](../../src/emrys/orchestration/run_coordinator/_inspection_admission.py) derives from immutable functional specification, while materialization builds its commands from installed processing tasks. Removing 00a from only the Run profile would fail graph admission or leave a mismatched plan and verified-Task tree. Historical generated Run profiles also need a preserved readmission path.

**Proposed direction:** select one source mode in the immutable plan and carry it through profile admission, owner/edge projection, expected Tasks, materialization, Snakemake rules, and Stage 01 index input. Supplied mode must not schedule construction or invent a successful Stage 00a Task. Reuse existing graph authorities where possible instead of a parallel execution backend. Generated mode must remain equivalent.

### F06 — Analysis, Run, and processing reuse

The [application model](../../src/emrys/contracts/orchestration/application_model.py) derives reference scope from FASTA/GTF hashes. Execution Plan and processing compatibility currently bind the three STAR values and runtime toolchain, but no supplied-index digest. The [Attempt continuity fields](../../src/emrys/orchestration/run_coordinator/_inspection_attempts.py) omit authored paths, yet [resume](../../src/emrys/orchestration/run_coordinator/control.py) recomputes the Run binding and retains verified Tasks with their original dispatch input bindings. A content-identical supplied index at a new path therefore needs an explicit policy for new and retained Tasks; path relocation must not silently change the Run plan.

[Processing reuse](../../src/emrys/orchestration/run_coordinator/inspection.py) requires compatible Reference and processing identities and collects content-bound verified Task outputs. A supplied index has no 00a Task output, so source admission and re-admission need their own representation before `--from-processing-run` can rely on it. [Reporting projection](../../src/emrys/contracts/orchestration/projection.py) also hashes the reference contract; inserting a physical index path there would make that report identity path-sensitive, an effect to review rather than assume.

**Proposed direction:** keep the scientific FASTA/GTF reference meaning unless an independently approved contract decision changes it. Bind supplied-source mode and content fingerprint into the immutable Run/processing compatibility decisions, and bind the chosen path and member snapshots at the Attempt and Task boundaries. Decide whether same-content relocation is allowed, how retained Tasks and processing reuse readmit it, and whether generated and supplied sources may ever be reuse-compatible. Changed index bytes must create a distinct Run or fail continuation; they cannot alter an existing Run.

### F07 — Storage, execution, and recovery

The [Task owner](../../src/emrys/orchestration/run_coordinator/task.py) permits outside-Run native outputs only for the exact Step 00c FAI/dictionary pair. [Attempt materialization](../../src/emrys/orchestration/run_coordinator/materialization.py) indexes admitted external single-file snapshots, not a supplied index-directory manifest. Task input-directory binding detects changed membership and bytes at execution only if Stage 01 declares the directory. [Verified-Task admission](../../src/emrys/orchestration/run_coordinator/task.py) rehashes recorded inputs and checks membership during later inspection. None of these checks alone binds an external directory to the immutable Run.

The [Run contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md) requires fresh admission for resume and preserves ambiguous locks, partial outputs, and terminal evidence. Shared storage may be unavailable from a compute placement even when a head-node Project path exists. This is a placement and admission failure, not a reason to copy, repair, adopt, or mutate an index.

**Proposed direction:** never publish a supplied directory as a Task output. Bind its exact member inventory into planning, declare the directory as Stage 01 Task input, and verify that the selected path is readable from the execution placement. Recheck at existing Task, resume, and inspection boundaries where completion depends on it; state the residual mutation-during-read risk. Define clear diagnostics for inaccessible or changed source storage without cleaning the source or ambiguous recovery state.

### F08 — Inventory and truthful reporting

The [profile artifact templates](../../src/emrys/workflow/contracts/local_cmh_v2.json) register fifteen required Stage 00a index artifacts and a Stage 00a validation report at Run-native paths. [Inventory projection](../../src/emrys/contracts/orchestration/artifact_inventory.py) expands the admitted Run profile. The [artifact-index roster check](../../src/emrys/reporting/_artifact_index/core.py) requires the exact fifteen STAR basenames when a Stage 00a scope has rows; absent 00a rows do not trigger that scope check. The [reporting adapter registry](../../src/emrys/reporting/_artifact_index/registry.py) still reads installed processing templates and recognizes the historical generated 00a products. The projection and reader must agree on supplied mode without erasing generated-mode support.

[Artifact inspection](../../src/emrys/reporting/_artifact_index/inspection.py) and the [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md) separate admitted artifact facts from downstream reports. A supplied directory is an admitted input, not a Run-produced artifact or Stage 00a validation report. Source provenance needs a truthful place in Run inspection and ordinary summary. The [reporting contract projection](../../src/emrys/contracts/orchestration/projection.py) hashes the reference object; adding a physical supplied-index path there could make report identity depend on location rather than content.

**Open decision:** select one existing contract location for supplied-input provenance and decide what, if anything, appears in artifact inventory. Trace each report reader and independent expectation before changing templates or statuses. Preserve generated-mode rows and avoid a second Artifact Store or report authority.

### F09 — Project and operator experience

[Named Init and validation](../../src/emrys/orchestration/run_coordinator/CONTRACT.md) disclose three STAR settings, preserve a no-write preview, and perform full input admission at creation. The [RUNBOOK](../operations/RUNBOOK.md) presents one Project path; the [configuration guide](../../configs/README.md) explicitly says the current star_index field does not admit a prebuilt index.

**Proposed direction:** offer the optional source in both hand-authored and guided Project paths. Preview should display the chosen source, declared version/settings, expected provenance, and work that creation will perform without implying that deferred hashing has succeeded. Creation and validation should report one clear admissibility result; ordinary Run output should identify the selected index source without exposing Task internals. Resolve whether content hashing belongs in creation or a later no-write validation phase before choosing CLI details.

### F10 — Maintenance compression

Candidates already found: derive the hard-coded member count in materialization from the shared [STAR member tuple](../../src/emrys/libraries/alignments/star.py); reuse the stable [hash/list helpers](../../src/emrys/libraries/validation/inputs.py) and Task directory checks; inspect the separately owned [reference-provenance contig parser](../../src/emrys/evidence/reference_provenance/_reference_contigs.py) for semantic parity before sharing. Its inventory permits unknown expected hashes and is not a fail-closed Run admission authority ([inventory](../../src/emrys/evidence/reference_provenance/_reference_inventory.py)). The shell worker's separate producer check protects a different boundary and should remain unless equivalent protection is proved.

The current reduction audit is specific about each surface:

| Surface | Candidate or retained boundary |
| --- | --- |
| Product code | Derive the planner's hard-coded member count from the shared tuple; extend existing input and Task helpers rather than writing another directory hasher or STAR parser. |
| Tests and fixtures | Extend owner-local cases; compare repeated synthetic-index setup in workflow and reporting fixtures before sharing it. Keep independent literal expectations for the seven-check report and generated mode. |
| Scripts | Keep the shell producer's member check as a distinct generation defense. Add no import wrapper; audit its list against the shared owner contract when the affected path is changed. |
| Schemas and configuration | Review all references to the existing star_index object before adding one optional supplied-source declaration. Do not duplicate the three-value policy in a second configuration authority. |
| Documentation | Link this investigation from the backlog once; put eventual exact behavior with the owner and operator steps in the RUNBOOK. Replace the README's stale limitation only when the feature exists. |
| Public concepts and compatibility | Prefer one source-mode distinction within the current Project/Run model. Old generated Projects must retain their meaning; any new record reader or migration has to be justified. |
| Mutable state and evidence | Avoid an index cache, copy, or separate registry. Preserve existing locks, reports, goldens, and recovery records; evidence deletion has its own approval boundary. |

Before implementation, quantify exact file and line deltas for a proposed patch, with product, tests, configuration/docs, and evidence counted separately. Any unavoidable product-growth exception needs explicit approval; unrelated test, documentation, or evidence deletion cannot offset it.

### F11 — Protection and evidence

Existing anchors include [contract tests](../../tests/contracts/orchestration/test_orchestration_contracts.py), [application identity tests](../../tests/contracts/orchestration/test_application_model_contracts.py), [Project normalization tests](../../tests/orchestration/run_coordinator/test_normalization.py), [materialization tests](../../tests/orchestration/run_coordinator/test_materialization.py), [workflow and drift tests](../../tests/orchestration/run_coordinator/test_workflow.py), [Stage 00a validator tests](../../tests/stages/star_index/test_validate_step_00a_star_index.py), and [artifact-adapter tests](../../tests/reporting/test_artifact_adapters.py).

The proposed protection matrix is:

| Boundary | Focused cases | Evidence sought |
| --- | --- | --- |
| Project and provenance admission | Missing, empty, nonregular or linked members; altered member bytes; mismatched FASTA/GTF hashes despite matching names and lengths; each parameter/version error; unsupported extra generation inputs. | Explicit fail-closed diagnosis, no published false Project/Run authority, and preserved partial creation state where publication has begun. |
| Immutable plan and graph | Same references with different index bytes; changed source mode; generated versus supplied graph; direct and Slurm plan renderings. | Distinct correct Run identity, no supplied-mode generator, unchanged generated mode. |
| Task, resume and reuse | Membership or content change before entry, during alignment, after a partial Attempt, and before reuse. | No false completion, preserved recovery evidence, compatible processing source only. |
| Inventory and presentation | Supplied input attribution, absent generated Stage 00a evidence, generated-mode literal roster. | No fabricated construction/validation claim and unchanged old output contract. |
| Operator journey | Preview, decline, create, validate and Run with an explicit index. | Preview writes nothing; normal diagnostics name the source and evidence limit. |

Preserve independent literal expectations rather than computing test expectations from production helpers.

Repository fixtures establish only their stated local behavior. Real STAR, hosted CI, disposable Slurm, institutional storage/site qualification, scientific review, and biological interpretation require separate evidence. This planning pass ran no scientific, workflow, real-STAR, or cluster tests. Its source inspection and documentation checks do not raise the evidence level.

## Proposed vertical implementation sequence

1. **Contract decision:** agree on external provenance authority, supported STAR recipe/version, authored input shape, graph source mode, identity placement, inventory attribution, and guided Init scope. Review every current writer/reader and the full affected path.
2. **Admission and identity:** implement one stable read-only directory/source admission using existing helpers; bind immutable content and source mode. Protect no-write failure and change races with small fixtures.
3. **Graph and lifecycle:** route supplied mode through an honest external input, omit generation, preserve generated mode, and complete Task, resume, processing reuse, inspection, and reporting behavior together. Do not merge a partial feature that can claim false completion.
4. **Operator documentation and protection:** complete Init/validation/Run presentation, owner contracts and guide updates, negative tests, and exact generated-mode parity. Review the complete semantic diff and quantify maintained-surface changes.
5. **Validation and acceptance:** run fast applicable local checks on the final state; send long checks to CI. Record exact commit and result. Keep real-tool, Slurm, institutional, performance, and scientific claims at their actual evidence levels.

Stop for ambiguous source history, an unsupported STAR recipe, unsafe directory or recovery behavior, a graph that can only fabricate Stage 00a completion, missing required protection, or an unapproved public-surface or quantified product-growth decision.
