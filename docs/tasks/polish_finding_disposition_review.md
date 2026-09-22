# Polish finding disposition review — working draft

Source snapshot: `codex/pr302-original-intent-corrections` at
`3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d` (2026-09-22).
This companion to the [backlog and campaign audit](backlog_campaign_audit.md)
holds the per-item polish review. It is not a task-status authority or
permission to implement or remove any proposal. The original
[polish campaign](polish-campaign.md) and accepted
[main matrix](backlog_matrix.md) retain their distinct roles.

**Observed:** Several original premises in the [polish campaign](polish-campaign.md)
have changed at the audit baseline. Item 7 (lines 313–327) says Init preview
shows only output locations, but the current public preview in
[`onboarding.py`](../../src/emrys/orchestration/run_coordinator/onboarding.py)
lines 1163–1258 includes libraries, Analysis/site, reference, scientific
choices, and defaults, with detailed manifests behind verbose output. That
invalidates the old "only output locations" premise but does not yet prove
full preview/publication agreement; GTF and individual paths remain in
verbose detail. Item 8
(lines 329–339) says Doctor lacks a profile selector, but
[`doctor.py`](../../src/emrys/orchestration/run_coordinator/doctor.py) lines
1976–1982 offers `--profile` and lines 484–510 select it. Item 9's old
direct-storage-plan premise (lines 341–358) is narrowed by Doctor's current
Slurm branch at lines 835–857; site behavior still needs review. Item 36
(lines 798–811) describes explicit-memory preflight as missing, while the
[current `SCHED-01` row](backlog_matrix.md#platform-operation-and-portability)
says its source is implemented and verification remains.

Item 6 is locally reproduced at this audit head: the public
[`validate_record`](../../src/emrys/contracts/orchestration/api.py) path accepts
both a valid timestamp and `finished_at: "not-a-time"` in a minimal blocked v3
Attempt receipt when run with the locked `jsonschema` 4.26.0 package. Its
optional RFC 3339 checker is absent from the lock closure, so `date-time` is
not registered. The [producer](../../src/emrys/orchestration/run_coordinator/lifecycle.py)
emits valid UTC timestamps, and [inspection](../../src/emrys/orchestration/run_coordinator/_inspection_attempts.py)
can later flag the malformed time; neither makes public admission reject it.
The current [contract test](../../tests/contracts/orchestration/test_orchestration_contracts.py)
rejects a non-string time but not a malformed string. This is a local contract
probe, with no hosted or site evidence. Other `FormatChecker` callers remain
to be reviewed before selecting a correction.

**Confirmed group mismatch:** Item 11 is not yet aligned:
[Quickstart](../../quickstart.md) line 44 uses
`--no-default-groups --group workflow`, while the managed golden CI lane in
[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) lines 632–638
lacks `--no-default-groups`. [`pyproject.toml`](../../pyproject.toml) makes both
`dev` and `workflow` default groups. The locked Linux/Python 3.14 dependency graph
projects 73 shared names (EMRYS plus 72 dependencies) and 17 CI-only
development packages,
including `pytest`, `coverage`, `ruff` and `pre-commit`, with no different
versions among the shared names. This offline graph comparison is not an
installed-environment manifest. The [baseline managed golden job](https://github.com/lab-cats/EMRYS/actions/runs/35770811692/job/106891764037)
passed with that broader environment, not the documented minimal one; its
later containment step runs `.venv/bin/python -m pytest`, so merely changing
the sync flags would remove a dependency of that step.

Item 12's draft versus admitted FASTQ identity question remains: the draft
rejects reused physical files by device and inode (`onboarding.py` lines
1441–1457), while Project normalization checks
path equality and caches by path
([`normalization.py`](../../src/emrys/orchestration/run_coordinator/normalization.py)
lines 359–385). This is a policy comparison, not an established defect.

**First complete item inventory:** Each line below maps one numbered
[polish discussion](polish-campaign.md) at `3a672fdf`. "Delivered" means its
described source capability exists at this revision; it is not independent
acceptance of a larger backlog outcome or institutional proof. "Unselected"
means the campaign itself does not authorize implementation. The original
finding and any unique rationale remain available in the campaign while a
durable disposition is decided.

| Item | Audit reading at baseline | Remaining disposition or evidence |
| ---: | --- | --- |
| 1 | Validation-report recovery defect remains documented by its owner. | Keep with validation recovery and direct fault checks. |
| 2 | Storage-inventory replacement proposal is explicitly retired. | Historical rationale can be condensed after checking unique decisions. |
| 3 | Reference-provenance replacement recovery defect remains owner-documented. | Keep recovery evidence with that owner. |
| 4 | Runtime-report publication proposal is explicitly retired. | Historical rationale only after retention check. |
| 5 | Current-artifact admission through the public validator is delivered. | Avoid re-presenting it as a missing feature. |
| 6 | Public v3 Attempt receipt admission accepted `finished_at: "not-a-time"` in a source-bound local probe under the locked checker closure. | Keep a live correctness proposal: select timestamp policy and maintained checker, then cover valid historical/current and malformed strings plus other format callers. |
| 7 | Init preview now shows major scientific choices, but detailed paths are verbose and final bytes follow admission. | Replace the old missing-preview premise; verify exact preview/publication agreement before closing acceptance. |
| 8 | Doctor `--profile` supports default, named, and absolute selections in source and focused tests. | Mark source delivery; keep site acceptance with CV-07. |
| 9 | Current Slurm repair planning skips the formerly alleged direct-storage plan. | Re-evaluate full placement behavior and site evidence; do not claim the old source-predicted failure persists. |
| 10 | Novice institutional walkthrough remains accepted under `SITE-PARITY-01`. | Keep its exact site evidence requirement. |
| 11 | Quickstart excludes default `dev`; managed golden CI includes it. The offline locked graph has 17 CI-only package names, while shared versions agree. | Verify an operator-minimal golden journey separately from the later `pytest` containment check; assert group selection. No install-speed or site claim. |
| 12 | Draft FASTQ physical-identity check differs from Project normalization's path-based check. | Preserve explicit mate-path proposal and settle admission policy before calling this a defect. |
| 13 | Ineffective reporting-memory control is retired. | Historical disposition only. |
| 14 | Standalone dashboard retirement is implemented; ordinary baseline software/docs CI passed, while institutional visual review remains. | Keep `DASHBOARD-RETIRE-01`, legacy readers and the separate evidence-deletion gate. |
| 15 | Per-script Bash syntax checking is delivered. | Keep owner check, not an open proposal. |
| 16 | ShellCheck is delivered under `DEV-01`. | Keep its locked-tool owner. |
| 17 | Selected Ruff correctness rules are delivered. | Do not infer all possible rules were adopted. |
| 18 | Consistent Python formatting is delivered under `DEV-01`. | Keep the accepted formatting baseline. |
| 19 | A Python type checker remains an unselected proposal. | Decide value and exact supported scope before adding a gate. |
| 20 | Optional fast local hooks are delivered under `DEV-01`. | Keep existing hook owner. |
| 21 | Local/CI validation inventory work is delivered. | Retain distinct check coverage. |
| 22 | Ordinary CI on supported stacked PRs is delivered. | Recheck effective hosted rules only if making a new policy claim. |
| 23 | The bounded CI critical-path work is delivered under `CI-01`. | Retain measured evidence rather than an assumed current duration. |
| 24 | Dependency-update bot remains an unselected tooling proposal. | Check current hosted configuration before selection. |
| 25 | Vulnerability assessment remains an unselected tooling proposal. | Identify an actual tool and maintenance owner before adding a gate. |
| 26 | Bounded R static analysis remains unselected. | Preserve distinct real-R and scientific tests. |
| 27 | Shell formatting remains unselected; a declared `SHFMT_BIN` is not a selected gate. | Prove need and scope before tooling growth. |
| 28 | Local secret detection remains an unselected gap-dependent proposal. | Require a demonstrated need and data-safe workflow. |
| 29 | External Analysis/reporter usability is accepted as Open `EXTENSION-01`. | Keep complete real discovery/installation acceptance with that row. |
| 30 | Release path is accepted as Open `RELEASE-01`. | Date-bound old distribution observations; do not claim release readiness. |
| 31 | Citation guidance remains an unselected proposal. | Decide authoritative format and owner. |
| 32 | Release dependency inventory/provenance remains an unselected proposal. | Coordinate with `RELEASE-01` before making a release artifact. |
| 33 | September 22 API recheck found the default-branch rulesets still lack required status checks; PR #312's correction-branch base returned no effective rules. | Keep hosted policy unselected; test proposed merge behavior separately before any settings change. |
| 34 | Complete R dependency closure is accepted as Open `RUNTIME-CLOSURE-01`. | Keep recursive closure and snapshot-off acceptance with the row. |
| 35 | Installed Snakemake content guarantee remains unresolved. | Trace current package binding before calling an escape or solution proven. |
| 36 | Explicit Slurm memory preflight is implemented and its ordinary baseline software checks passed; `SCHED-01` remains Verification pending. | Date-bound the old missing-implementation premise; keep CV-11's institutional capacity limit. |
| 37 | Browser/copy/print report review remains pending under report rows 01–03. | Retain rendered visual and link acceptance separate from receipts. |
| 38 | Pre-execution cancellation policy remains unselected. | Decide expected signal/EOF behavior before changing public exits. |
| 39 | Machine-readable inspection needs a concrete consumer and remains unselected. | Preserve human inspection authority and exit meaning. |
| 40 | The documentation checker validates structure, not fenced-command behavior. | Select safe examples before adding a command check. |
| 41 | Normal inspection still favors verified report locations; scientific paths are in verbose detail. | Retain the processing-only/no-report output-location UX question. |
| 42 | Run selection still lacks sufficient admitted Analysis context. | Retain presentation proposal without treating labels as integrity proof. |
| 43 | `emrys --version` is delivered under `CLI-VERSION-01`. | Keep current source identity and foreign-directory limits. |
| 44 | Contributor/problem-reporting route remains unselected. | Choose a data-safe public route without inventing contact details. |

The five integration-scale architecture options are also unselected; the
campaign withdrew its 6,400–9,200-line estimate. Their prerequisites differ:

| Option | Required evidence before selection |
| --- | --- |
| Unified Inspect/Watch observation | One admitted observation and caller-complete selection/presentation retirement with scheduler state remaining observational. |
| Shared operation kernel | Equivalent trust and mutation boundaries across every migrated owner, with unchanged exits, claims, logs, receipts, and recovery. |
| Declarative records/scenarios | Smaller fixture surface with distinct failure modes and independent scientific/evidence oracles intact. |
| Common reporting transaction | A smaller caller-complete replacement for both publishers despite their different commit/recovery order. |
| Narrow supported surfaces | Exact consumer inventory, migration/rollback, and separate public-contract approval. |

**Next:** Select item 6's timestamp policy and contract checks; verify an
installed operator-minimal journey for item 11 while retaining its later test
step. Decide and test any merge policy for item 33 separately. Resolve items 7,
9, 12 and 35 with direct checks or policy decisions. The campaign's old PR
chronology can be shortened only after unique decisions and dated evidence
have a verified owner.
