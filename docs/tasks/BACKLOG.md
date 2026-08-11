# Backlog

This is NORAD's compact live inventory. Actionable items may be selected only
after their open blockers are gone and a reviewed JIT card exists under
[`cards/`](cards/). Proposal entries preserve questions but confer no roadmap,
selection, implementation, or publication authority.

## AUDIT-99 — Final refactor and documentation audit

- **Kind:** actionable
- **Blocked by:** `DOC-SKILL-10`, `LOG-05`, `RPT-06`
- **Intent:** Audit only the implemented refactor program, rank residual code and documentation risk, and publish exact validation and evidence ceilings.
- **Boundaries:** No new feature, runtime, scientific, cluster, or biological claim; local characterization and stale receipts never become broader proof.

## CLI-03A — Implement local-pilot control plane

- **Kind:** actionable
- **Blocked by:** `INTAKE-03A`, `PROFILE-03A`, `SETUP-03A`
- **Intent:** Provide a thin local command surface that orchestrates the approved pilot profile, request lifecycle, resume, and state inspection.
- **Boundaries:** Dry-run by default; no hidden installation, private imports, SLURM execution, scientific reimplementation, or implicit state authority.

## CODEDOC-05 — Inventory code documentation

- **Kind:** actionable
- **Blocked by:** None
- **Intent:** Classify every source file's module header, public docstrings, and non-obvious invariant comments as sufficient, update, defer, or exclude.
- **Boundaries:** Preserve CLI help and byte-sensitive fixtures; do not turn inline comments into data, duplicate owner documentation, or execute a rollout.

## DOC-SKILL-10 — Build documentation-health skill

- **Kind:** actionable
- **Blocked by:** `CODEDOC-05`, `REVIEW-UX-03`
- **Intent:** Build and forward-test a read-only-first skill for deterministic and semantic NORAD documentation-health review after the practices are stable.
- **Boundaries:** Use the supported skill workflow; require approval for mutation; detect broken links, owner drift, task integrity, README/glossary/header gaps, and seeded failures without replacing the documentation gate.

## DOC-TASK-SCAN-01 — Scan documentation for future commitments

- **Kind:** actionable
- **Blocked by:** None
- **Intent:** Review repository documentation for unowned future commitments and assign each match an explicit disposition.
- **Boundaries:** Search results are not authority; do not create, prioritize, approve, or select work automatically.

## E2E-03A — Prove fresh-clone local pilot

- **Kind:** actionable
- **Blocked by:** `CLI-03A`
- **Intent:** Prove the approved local pilot from a fresh clone through failure, resume, and final inspectable outputs.
- **Boundaries:** Bind exact fixture/data identity and hashes; distinguish fixture from real runtime; make no cluster, production, scientific-review, or biological claim.

## FUT-ANALYSIS-01 — Preprocessing profiles and analysis modules

- **Kind:** actionable
- **Blocked by:** `AUDIT-99`
- **Intent:** Design typed, language-neutral preprocessing profiles and optional analysis modules from concrete post-audit use cases.
- **Boundaries:** No universal registry or scientific generalization before multiple proven cases; preserve artifact, evidence, and public-runner contracts.

## FUT-CLI-03 — Installable NORAD control plane

- **Kind:** actionable
- **Blocked by:** `AUDIT-99`
- **Intent:** Evaluate a later installable CLI that materializes explicit repository assets and orchestrates stable public boundaries.
- **Boundaries:** Keep it thin and inspectable; no hidden dependency installation, database, private source import, scientific computation, or silent migration.

## FUT-DATA-02 — Public reference and SRA acquisition

- **Kind:** actionable
- **Blocked by:** `AUDIT-99`
- **Intent:** Define explicit, retryable public-reference and public-read acquisition adapters with provenance and content identity.
- **Boundaries:** Reference and read acquisition remain separate; no scraping, credential handling, silent updates, implicit trust, or production-data authority.

## FUT-SUCCESS-04 — Optional analysis and archival semantics

- **Kind:** actionable
- **Blocked by:** `AUDIT-99`
- **Intent:** Define required versus optional analysis completion and metadata archival without changing raw-data retention.
- **Boundaries:** Raw data remains; optional failure cannot be mislabeled success; archival metadata never promotes computational, scientific, or biological evidence.

## GATE-REC-01 — Machine-readable gates and validation receipts

- **Kind:** actionable
- **Blocked by:** None
- **Intent:** Version a gate catalog and content-bound validation receipts that permit reuse only after subject, gate, input, and environment equivalence is proved.
- **Boundaries:** Do not redesign gates, promote evidence, or create a new authority; receipts record schema, gate digest, command, Git/input/environment identity, timestamps, per-check exits, and logs.

## INTAKE-02E — Define YAML plus TSV run lifecycle

- **Kind:** actionable
- **Blocked by:** None
- **Intent:** Specify the request YAML, sample-manifest TSV, normalized identity, attempt, claim, completion, and recovery lifecycle.
- **Boundaries:** Claim atomically; mark success only after required tasks, validators, evidence, and report complete; preserve raw inputs and explicit authority.

## INTAKE-03A — Implement YAML plus TSV run lifecycle

- **Kind:** actionable
- **Blocked by:** `INTAKE-02E`
- **Intent:** Implement the approved request and manifest lifecycle across ingestion, contracts, and orchestration owners.
- **Boundaries:** No filename inference, raw-data movement, cluster execution, hidden installation, or ownership collapse.

## LOG-03 — Build two-sink logging foundation

- **Kind:** actionable
- **Blocked by:** `REVIEW-UX-03`
- **Intent:** Implement a neutral logging foundation that separates concise operator output from complete operation-attempt logs.
- **Boundaries:** The binding interface, identity, record, publication, failure, redaction, retention, and scheduler rules are exact in [`LOGGING_CONTRACT.md`](../design/LOGGING_CONTRACT.md); no stage awareness or behavior change is allowed.

## LOG-05 — Activate concise default logging

- **Kind:** actionable
- **Blocked by:** `LOG-03`
- **Intent:** Activate the approved concise console default only after every applicable domain adopts the foundation with parity evidence.
- **Boundaries:** Durable detail remains complete; artifacts, streams, exits, transactions, recovery, and evidence meaning do not change.

## ONBOARD-03A — Publish researcher onboarding path

- **Kind:** actionable
- **Blocked by:** `E2E-03A`
- **Intent:** Publish a concise researcher journey from setup and request creation through pilot execution, inspection, failure, and resume.
- **Boundaries:** Link canonical commands and proof-matched outputs; state local, runtime, cluster, scientific, and biological evidence limits explicitly.

## PROFILE-03A — Materialize local-pilot workflow profile

- **Kind:** actionable
- **Blocked by:** None
- **Intent:** Materialize the current CMH pilot as one declarative profile over existing semantic stages and public runners.
- **Boundaries:** No generic registry, new orchestrator, scientific change, hidden discovery, or state authority.

## REVIEW-UX-03 — Review usability plan

- **Kind:** actionable
- **Blocked by:** None
- **Intent:** Independently review scientist, operator, maintainer, and automation journeys before report, logging, onboarding, and documentation-skill implementation.
- **Boundaries:** Review findability, terminology, cognitive load, accessibility, failure recovery, console/report hierarchy, intake state, and local context without implementing or changing scientific meaning.

## RPT-01 — Characterize comprehensive report

- **Kind:** actionable
- **Blocked by:** None
- **Intent:** Freeze the current comprehensive report's fields, provenance, interaction, format, transaction, and known-defect behavior with test-supported evidence.
- **Boundaries:** Retain the comprehensive view; characterize rather than fix; reporting projects validated canonical inputs and never generates or promotes evidence.

## RPT-02 — Define science-report contract

- **Kind:** actionable
- **Blocked by:** `RPT-01`
- **Intent:** Define the versioned minimal scientist-facing field model, plain-language descriptions, profiles, missing states, and HTML/PDF semantic parity.
- **Boundaries:** Every value has one authorized source; comprehensive remains available; no inner-panel horizontal scroll; outputs coexist immutably; independent science, usability, accessibility, architecture, transaction, and security review precedes implementation.

## RPT-03 — Build format-neutral report projection

- **Kind:** actionable
- **Blocked by:** `REVIEW-UX-03`, `RPT-02`
- **Intent:** Implement a deterministic renderer-independent science projection derived only from the approved canonical summary and authorized tables.
- **Boundaries:** No file discovery, computation, evidence promotion, format-specific scientific field, default change, or comprehensive-field deletion.

## RPT-04 — Implement science-report usability

- **Kind:** actionable
- **Blocked by:** `RPT-03`
- **Intent:** Build accessible HTML and PDF presentations of the approved science projection with clear hierarchy and responsive/print behavior.
- **Boundaries:** Do not change the field model in view code; preserve evidence banners and semantic parity; hide no contracted information to avoid scrolling.

## RPT-06 — Make science report the default

- **Kind:** actionable
- **Blocked by:** `RPT-04`
- **Intent:** Change the public default to the approved science profile while keeping the protected comprehensive profile explicitly selectable.
- **Boundaries:** Profile names follow the approved contract; bundles coexist without overwrite or reinterpretation; analysis, artifacts, and evidence meaning remain unchanged.

## SETUP-03A — Implement local-pilot dependency profile and doctor

- **Kind:** actionable
- **Blocked by:** None
- **Intent:** Define the local-pilot dependency profile and a read-only doctor that reports readiness and exact remediation routes.
- **Boundaries:** No installation or repair; distinguish local configuration from CSU, batch, cluster, production, scientific-review, and biological readiness.

## SKILL-11 — Evaluate repository skill opportunities

- **Kind:** actionable
- **Blocked by:** `AUDIT-99`
- **Intent:** Evaluate repeated stable workflows for skill, documentation/script, or defer disposition using measured value and maintenance risk.
- **Boundaries:** Evaluation is not creation; persistent identity/state remains the separate `FUT-AGENT-01` proposal; no destructive, runtime, cluster, or scientific automation authority.

## FUT-AGENT-01 — Persistent agent identity, context, and state

- **Kind:** proposal
- **Blocked by:** None
- **Intent:** Evaluate whether durable agent identity or state adds measurable value beyond explicit files, bounded roles, context packets, skills, and stateless adapters.
- **Boundaries:** No hidden authority or canonical state; define privacy, secrets, provenance, expiry, reset, model drift, isolation, and fail-closed behavior before any time-boxed experiment.

## FUT-AIDEV-01 — Portable AI-development operating system

- **Kind:** proposal
- **Blocked by:** None
- **Intent:** Explore a project-agnostic file-first kernel only from practices proven in NORAD and a materially different repository.
- **Boundaries:** Human-readable files and Git remain canonical; separate generic mechanics, project policy, and live state; adapters stay optional and nonauthoritative; correctness and semantic sufficiency outrank token savings.

## FUT-SITE-01 — CSU SLURM execution profile

- **Kind:** proposal
- **Blocked by:** None
- **Intent:** Explore explicit CSU batch-visible runtime, storage, scheduler, logging, recovery, and operator contracts after those site facts are verified.
- **Boundaries:** Local pilot and dry-run are not cluster proof; authorize no cluster access, submission, restoration, storage change, or production-data handling.

## FUT-SITE-02 — Portable site and container profiles

- **Kind:** proposal
- **Blocked by:** None
- **Intent:** Explore a concrete second-site profile and acceptable container, module, or other deployment mechanism.
- **Boundaries:** Containers do not prove data, scheduler, scientific, or interpretation portability; authorize no image build, registry, credentials, dependency restoration, or nonlocal execution.

## TASK-INTAKE-01 — Persistent task inbox

- **Kind:** proposal
- **Blocked by:** None
- **Intent:** Explore low-ceremony immutable idea capture with stable intake identity and explicit reviewed batch disposition.
- **Boundaries:** Capture grants no status, priority, approval, selection, mutation, or integration authority; canonical changes are separately re-authored from current state.

## TASK-VIEW-01 — Generated tranche dashboard

- **Kind:** proposal
- **Blocked by:** None
- **Intent:** Generate a deterministic Markdown and Mermaid view of approved tranche membership from structured canonical inputs.
- **Boundaries:** The view owns no lifecycle, dependency, branch, gate, evidence, or authorization fact; missing data stays unavailable; committed output must check-regenerate byte-for-byte.

## TEST-E2E-01 — Local synthetic cohort-candidate integration

- **Kind:** proposal
- **Blocked by:** None
- **Intent:** Explore one tiny independent-fixture path across the mpileup, preprocessing, and paired-CMH public stage boundaries.
- **Boundaries:** Preserve transactions, manifests, sample order, provenance, and evidence vocabulary; a pass is local synthetic integration only, never production, cluster, scientific-review, or biological proof.
