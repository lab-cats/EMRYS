# Backlog

This is NORAD's compact live inventory. Actionable items may be selected only
after their open blockers are gone and a reviewed JIT card exists under
[`cards/`](cards/). Proposal entries preserve questions but confer no roadmap,
selection, implementation, or publication authority.

## AUDIT-99 — Final refactor and documentation audit

- **Kind:** actionable
- **Blocked by:** `DOC-SKILL-10`, `LOG-05`
- **Intent:** Audit only the implemented refactor program, rank residual code and documentation risk, and publish exact validation and evidence ceilings.
- **Boundaries:** No new feature, runtime, scientific, cluster, or biological claim; local characterization and stale receipts never become broader proof.

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

## FUT-DASH-01 — Portable live workflow dashboard

- **Kind:** proposal
- **Blocked by:** None
- **Intent:** Generalize the CSU-specialized live dashboard around versioned machine-readable workflow events, bounded parsing, verified report discovery, and request-derived samples, partitions, resources, and stage topology.
- **Boundaries:** The dashboard remains read-only and nonauthoritative; scheduler state, logs, inferred progress, and displayed report paths never become completion or evidence authority. Discovery must remain bounded and fail closed, explicit overrides must be validated, and portability may not introduce shared-storage scans, hard-coded cohort structure, output adoption, or workflow mutation.

## FUT-DATA-02 — Public reference and SRA acquisition

- **Kind:** actionable
- **Blocked by:** `AUDIT-99`
- **Intent:** Define explicit, retryable public-reference and public-read acquisition adapters with provenance and content identity.
- **Boundaries:** Reference and read acquisition remain separate; no scraping, credential handling, silent updates, implicit trust, or production-data authority.

## FUT-INDEX-01 — Prebuilt STAR-index admission

- **Kind:** proposal
- **Blocked by:** None
- **Intent:** Define safe admission and reuse of an explicitly declared prebuilt STAR index in a fresh local-pilot run by binding every required index member to the source FASTA/GTF identities, STAR parameters and tool version, and exact content hashes.
- **Boundaries:** Existing-directory presence is never proof of compatibility; do not discover, adopt, repair, merge, or mutate an index implicitly. Preserve the Step `00a` producer's create-absent semantics and require fail-closed validation plus the same content-bound verified-task meaning before downstream use.

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

## REVIEW-UX-03 — Review usability plan

- **Kind:** actionable
- **Blocked by:** None
- **Intent:** Independently review scientist, operator, maintainer, and automation journeys before report, logging, onboarding, and documentation-skill implementation.
- **Boundaries:** Review findability, terminology, cognitive load, accessibility, failure recovery, console/report hierarchy, intake state, and local context without implementing or changing scientific meaning.

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
