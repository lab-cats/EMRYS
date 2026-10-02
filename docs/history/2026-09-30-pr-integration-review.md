# September 30 PR integration review

This records the source selection and local review for one proposed squash
against `f2c0149e73a685b6f3d5b162f3804edee7c78c10`. The owner approved preparation
and bounded repairs after the initial read-only audit, then approved the single
local commit and quantified growth exception after reviewing this candidate.
That approval does not authorize a merge, PR closure, campaign reopening or
evidence promotion. The
[findings matrix](../tasks/backlog_matrix.md) retains acceptance authority.

## Reviewed sources and duplicate treatment

The source inventory covered 21 open PRs, 147 pre-existing local branches,
eight present clean worktrees, 22 missing worktree registrations, and the one
stash. Branch-base deltas span 203 unique paths. Comparison used Git ancestry,
patch/content identity, end-to-end differences and caller/test inspection;
stacked ancestor changes were counted once. The review concentrated on
publication/recovery, runtime admission, scheduler identity, containment,
inspection/Watch, E2E selection, resource provenance and documentation authority.
It is not an exhaustive new audit of every unchanged repository owner.

All 21 PRs were re-read from GitHub at 2026-09-30 17:19 UTC: still open, with the
same heads and bases used for this review. These are frozen source selections;
later source movement requires renewed comparison.

| PR | Reviewed head | Candidate treatment |
| --- | --- | --- |
| [#300](https://github.com/lab-cats/EMRYS/pull/300) | `93b5c45aee26ce45857ca8793ba2575db5737e3c` | Retain once through #321; includes current-checkout corrections. |
| [#302](https://github.com/lab-cats/EMRYS/pull/302) | `42d02c5a38ecffaba59e58d5d56ba0ab858eda1f` | Retain once through #321: allocation-aware CI. |
| [#303](https://github.com/lab-cats/EMRYS/pull/303) | `a2680f10f5bd22d7fce2bb3f534be3fd2ecaa065` | Select latest shared prep, isolated scenario jobs, serial stop lane and controller diagnostics; retain #321 exact binding. |
| [#304](https://github.com/lab-cats/EMRYS/pull/304) | `3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d` | Keep applicable corrections; do not restore superseded campaign statuses. |
| [#305](https://github.com/lab-cats/EMRYS/pull/305) | `0027c40ef7471b144972d708e1199ee2087292ae` | Retain Task/SIGCHLD protection through #321; latest #303 owns CI scenario setup. |
| [#306](https://github.com/lab-cats/EMRYS/pull/306) | `607f3ecc7e160743f4911a7ed64b6436bdff3c4a` | Retain duration-aware shard membership and JUnit evidence through #321. |
| [#307](https://github.com/lab-cats/EMRYS/pull/307) | `5ecc409c123fe34f746a61f7e92397c6978f3cab` | Defer optional Doctor timing helper; retain current owner disposition from #321. |
| [#308](https://github.com/lab-cats/EMRYS/pull/308) | `0418f7f841e2459406ca94d9d511257b35579844` | Retain DOCS-01 audit corpus and compatible Runbook compression. |
| [#309](https://github.com/lab-cats/EMRYS/pull/309) | `18fe9fbd64954ea157f5fa868f6bd36bc5bbb4cf` | Retain EXTENSION-01 discovery; no feature implementation selected. |
| [#310](https://github.com/lab-cats/EMRYS/pull/310) | `78132bd206a99f5d4aaa34b4afea93f57a7c9514` | Retain latest RELEASE-01 record, including post-fork updates. |
| [#311](https://github.com/lab-cats/EMRYS/pull/311) | `df2724048bf33cd335880b27a8cc96e1f98fc3f0` | Retain supplied-index investigation; no input-contract extension selected. |
| [#312](https://github.com/lab-cats/EMRYS/pull/312) | `b4a89a0d1b5874152860bc93e2b81df0eaac77c1` | Retain unique audits and dated evidence with superseded-checkpoint notices; preserve #321 current statuses. |
| [#313](https://github.com/lab-cats/EMRYS/pull/313) | `7fd6a9dbf8dd5370658a0562988a5a2ae71304f1` | Retain guided-operation discovery and bare-terminal design choice; implementation stays deferred. |
| [#314](https://github.com/lab-cats/EMRYS/pull/314) | `5779f6defef39782789b1fddba9c4f819aa0fee1` | Retain schema audit and owner link. |
| [#315](https://github.com/lab-cats/EMRYS/pull/315) | `347b6464d9e8b290e3f6ebe6f53d76473510a097` | Retain assurance audit and owner link. |
| [#316](https://github.com/lab-cats/EMRYS/pull/316) | `e1e802177b5333454e93e5e7c4f38d229f33f62a` | Defer optional packaged EV/PUM1 chooser. |
| [#317](https://github.com/lab-cats/EMRYS/pull/317) | `f54c84e6aacf5ec2675d81e8b5e88282b7497b16` | Use unpublished local 9dbd5c8d record, which contains and extends the published audit. |
| [#318](https://github.com/lab-cats/EMRYS/pull/318) | `0746f39009ca4bb38986f1b0755e1f838deac1df` | Retain cleanup investigation only; no artifact deletion selected. |
| [#319](https://github.com/lab-cats/EMRYS/pull/319) | `e16869510abd4c579b1f9409c848c0d486844786` | Retain size audit; convert source-line anchors to its declared immutable snapshot. |
| [#320](https://github.com/lab-cats/EMRYS/pull/320) | `1bb133e5fb47d82e84e8bc797c7591dcbbf4d8ae` | Defer optional general donor browser. |
| [#321](https://github.com/lab-cats/EMRYS/pull/321) | `7b8b428ddd528728b053993592a172166cec4784` | Use as combined product/status foundation and exact E2E request/job/stream binding authority. |

The only unique unpublished branch work found was nine REDUCE-01 commits at
`9dbd5c8d444fcd30df6b9d52d6d4e2eecc4eba1d`: the local record has 122 findings
versus 69 in the published head. Its 913-line audit is retained byte-for-byte;
this selects no reduction implementation. The latest RELEASE-01 record is also
retained byte-for-byte from its reviewed head.

The original checkout at `12164356d555c7103139d8d8fd2e15160e9c0111` contains
corrections already incorporated in the selected foundation. The separate
`a8d226ab415041d61eec8aabf4a4c95930333e1b` Slurm parsing patch is duplicated
there. Stash `3c6969bda8ce846dfc0da0c986c729116966d95e` is superseded by
`30b5c7b8634a698889bf34c37030e856aa823c27`, an ancestor of the foundation.
These refs and the stash are preserved. Missing registrations were not pruned.
No source worktree was edited.

## Findings and retained corrections

| Finding | Disposition and reason |
| --- | --- |
| P1: exclusive replacement can lose the predecessor after displacement or leave the public selector absent | Keep the existing publication owner. Restore an absent selector without clobbering a competitor; retain displaced bytes on failure and identify recovery. Preserve interruption identity and cleanup diagnostics. Replacement is recoverable, not continuously atomic. |
| P2: original sealed donor with missing native/R content cannot reach repair planning | Permit failed-probe diagnosis to admit seal structure for explicit replacement planning. Successful readiness still requires strict root ownership, canonical paths and content admission. A cross-review caught and corrected an initially over-broad relaxation. |
| P2: Setup can publish settings the loader rejects | Share the closed parser between writer and reader, require exact serialized round trip, and reuse the existing log-root policy before publication. |
| P2: retained v4 request metadata can contradict delegated command/Project/Run/analysis | Bind current request selectors to the delegate and reuse that admission in Control's intent parser. Resume/Report retain their real command grammar, which has no analysis flag. Legacy diagnostic readers remain available. |
| P2: immediate and retained submission-response parsers differ | Use one bounded, strict UTF-8, newline-terminated single-job response parser at transport and later observation. Raw response evidence survives refusal. |
| P2: Watch can project unverified log completion or select a name from incomplete discovery | Keep admitted completion distinct from raw logs. Require successful live/accounting discovery and determine uniqueness before display truncation; duplicate accounting IDs remain ambiguity. |
| P2: competing E2E branches combine incompatible waiting/admission paths | Retain #321 exact request/job/stream and compute-side Location binding; select #303 final failure admission, shared immutable setup and serial stop/resume policy. Omit sole-directory Run discovery. |
| P3: allocation CPU provenance can name the wrong Slurm variable | Select the value and its provenance together, including node-only fallback and per-task precedence. |
| Python 3.11 error-text expectations differ | Accept the actual alternative login-resolution diagnostic while preserving refusal/exit semantics. This is not a successful native-runtime claim. |
| Stale documentation statuses and invalid source-line anchors | Retain all 52 pre-existing matrix statuses and 61 CV/CV-U/CV-UX index statuses from #321. Older records keep their evidence and receive checkpoint notices. SIZE-01 links point at its declared immutable source snapshot. |

Independent cross-review covered the new publication/runtime/Setup repairs,
submission/Watch repairs, and the reconciled CI/E2E path. Additional ambiguity and
strict-readiness findings were repaired before finalizing the candidate.

## Consolidation and maintenance cost

The repairs use existing authorities: the publication helper, settings loader,
log-root policy, retained-request admission, scheduler reader and standard-library
argument parsing. They replace duplicate response grammars, share equivalent
delegate-prefix admission, and retire the competing unbound E2E wait path.
They add no dependency, execution backend, artifact store, schema, command or
persistent product state.

The foundation is substantial accumulated feature work. It does not meet the
default net-reduction rule merely because duplicates were omitted. Product,
tests, documentation and other surfaces are measured separately below. Evidence
is not deleted or counted as a saving. The owner approved the quantified growth
exception below for this single integration commit on September 30, 2026.

Measured against the frozen master using staged Git numstat, excluding this
review record to avoid counting its own changing measurement text. Markdown and
Mermaid are classified before tests. Product code includes tracked
`src/emrys` Python, R, shell, CSS, Jinja templates and Snakefile, excluding
generated `renv/activate.R` and runtime restoration tooling.

| Surface | Changed files | Added | Deleted | Net |
| --- | ---: | ---: | ---: | ---: |
| Product code | 54 | 12,014 | 3,221 | +8,793 |
| Tests and fixtures | 58 | 23,747 | 2,976 | +20,771 |
| Markdown and diagrams | 70 | 23,761 | 713 | +23,048 |
| Schemas | 8 | 159 | 88 | +71 |
| Repository scripts | 3 | 69 | 60 | +9 |
| Configuration, CI and other | 7 | 736 | 400 | +336 |

There are three added product files relative to master:
`_inspection_presentation.py`, `_submission_inspection.py` and
`scheduler_observation.py`, all under the coordinator. All three already belong
to the #321 foundation. The approved repair pass adds no product file. Relative
to #321, product changes are +206/-138, **net +68 lines** across eleven files.
The complete candidate is **net +8,793 product lines**, including inherited
feature work. No 25% reduction or meaningful net compression is claimed.

The staged executable/configuration surfaces checked in this review have these
Git tree identities; the final review-record text does not alter them:

| Surface | Tree |
| --- | --- |
| `src/emrys` | `af8e8f67886c2c48beb5704ffb0a1ed1d6d20530` |
| `tests` | `1a89feca4d70f0fa290acb3ccb8ce35991cf8599` |
| `.github` | `0ebd54615cee34eed5b4493587e9590d9d4f092b` |
| `configs` | `6abdacf1fe58433b29a1ffe37f26663844c4d1c9` |
| `scripts` | `571e1bb988569aa8ab8cd9f1966756235e2ac9ad` |

## Local checks and evidence limits

Checks used Python 3.14 and existing cached packages matching `uv.lock`, with
candidate source first on the import path. The existing `setup.py egg_info`
command generated candidate metadata in a temporary directory using cached
setuptools 83.0.0. Its provenance records the frozen base and dirty candidate,
and its lock hash comes from this checkout. No dependencies were installed.
This is source-fixture validation, not an installed-wheel test.

| Check scope | Observed result |
| --- | --- |
| Publication helper, including I/O, interruption, cleanup and parent-move faults | 33 passed |
| Onboarding, including shared saved-settings parser and log-root rejection | 177 passed initially; the remaining sandbox-writability case passed with worktree permission, covering 178 cases |
| Runtime seals and Doctor repair boundaries, final selection | 44 passed |
| Independent crossed readiness/recovery regressions | 5 passed; overlaps the two preceding scopes |
| Capacity provenance | 35 passed |
| Submission, dashboard and inspection presentation/association | Initial four-file run: 581 passed and 59 environment failures; corrected metadata allowed all 49 association failures to pass in a 55-test selection. Ten isolated-child checks remained unavailable. Later coherence/discovery fixes: 38 passed. These selections overlap and are not a full-suite total. |
| Materialization/submission integration | 20 passed after correcting a run-style test fixture to match the actual Resume/Report parser; final stricter non-run selection rerun: 3 passed |
| E2E driver, CI wiring and Python sharding | 81 passed, 1 skipped before the final three plan-wait cases; driver/workflow subset then 68 passed, 1 skipped; final three plan-wait regressions passed |
| Retained Task ownership, reaping and signal checks | 29 selected cases and 3 additional native tiny-fixture cases passed; 3 nested finalization cases could not import EMRYS in isolated children |
| Static checks | Full-repository Ruff correctness and format check passed (282 Python files); Python syntax passed on 95 changed files; Bash syntax and ShellCheck passed on all 14 changed shell files; staged whitespace check passed |
| Documentation structure and local links | 199 Markdown documents and 3 Mermaid sources passed; this is structural validation, not semantic or scientific proof |

The ten isolated submission/terminal cases are
`test_simulated_batch_environment_starts_real_snakemake_without_passwd_or_memory_vars`
(two variants; child lacks pytest),
`test_interactive_quit_restores_terminal_without_waiting_for_stalled_worker`
(six variants), and
`test_interactive_log_navigation_follows_pauses_counts_and_searches`
(two variants). The eight terminal children lack jsonschema. Three
`test_task_signals_preserve_exact_finalization_boundary` variants
(`attempt`, `between`, `verified`) report `No module named emrys` from
controlled `python -I -m emrys validate all-pass`. One E2E public-parser
check skips because its isolated interpreter lacks the installed package.
These are unmet environment requirements, not passing checks. Assertions were
not weakened to bypass the missing installation. Linux kernel subreaper behavior
was not verified on this macOS host.

The final runtime/Doctor selection was
`-k 'seal or ready_donor or shared_donor_missing or shared_owner_repair or valid_shared_owner or dependent_project'`
over the runtime-availability and Doctor test files. The materialization
selection covered no-write Slurm preview, repeated command streams, duplicate
submission intent, prepared resume and delegated request logging. Publication,
Onboarding and capacity exercised the complete corresponding test files with
the environment limits above. All local fixtures used temporary directories.

The source fixtures do not establish full-suite, Python 3.11, installed-wheel,
native synthetic E2E, Slurm, Viking, scientific-review or biological acceptance.
No CI was started, rerun or dispatched. The earlier #303 standard workflow
[35810111627](https://github.com/lab-cats/EMRYS/actions/runs/35810111627) and selected
130-pair workflow
[35810127968](https://github.com/lab-cats/EMRYS/actions/runs/35810127968) passed on
`a2680f10`; the latter ran three 130-pair scenarios, not the separate
100,000-pair scenario. Those results do not validate this combined candidate.
The #321 workflows were cancelled by the owner and remain cancelled evidence.

## Unselected work and remaining review limits

The optional #307 timing machinery, #316 packaged chooser and #320 general donor
browser remain in their source branches. Their omission is a scope decision,
not a claim that their implementations failed review. Guided bare `emrys`,
external STAR index admission, cleanup policy, architecture reductions and other
audit proposals remain with their existing owners and statuses.

The initial audit also found inherited concerns outside the bounded repair:
report execution schedules before its reuse check; lexical scratch-root forms
can pass profile admission and later be refused by the batch script; and retained
Task evidence/cleanup boundaries warrant further owner review. They were not
silently repaired or represented as closed. The first two were confirmed in the
frozen master as well as the selected foundation. Whole interactive dashboard,
installed execution and high-risk native/cluster paths still need their own
environment-bound verification.

No PR was closed, no branch/stash/evidence was deleted, and no merge, push or
commit occurred during preparation. The owner subsequently approved the single
local commit with the measured growth and evidence limits recorded here.


## October 1 CI follow-up

The owner approved the follow-up plan on 2026-10-01: repair CI, then the named
FASTA, normalized scratch-root and Report-admission defects, followed by
runtime-closure design, collaborator entry-point verification and release
readiness. The approved correctness exception is at most 100 additional net
product lines across these named repairs, with no new product files. The five
maintenance audits are separately [complete by owner direction](../tasks/backlog_matrix.md#october-1-2026-owner-completion).
Merging, production/site execution, evidence deletion and scientific acceptance
remain outside this approval.

The ordinary [PR run](https://github.com/lab-cats/EMRYS/actions/runs/36812449696)
and selected [extended run](https://github.com/lab-cats/EMRYS/actions/runs/36812476356)
failed on `213d67be8ebb3953cb0aa3c09818f95263aa1685`. Python 3.14 and 3.11 exposed
a duplicate-submission regression and two stale test assumptions. Managed
restoration also failed its strict lock synchronization check; all selected
real-synthetic scenarios were skipped behind that preparation failure. Those
skips establish no E2E result.

The Python repair keeps unadmitted retained contexts in the existing unknown-risk
path. Only an admitted context can establish an unrelated command, profile or
intent. The existing scheduler observer supplies UNKNOWN without querying Slurm;
the existing explicit duplicate override remains available. No second intent
parser, scheduler query or recovery mechanism was added. Strict v4 request
validation remains unchanged. The public-stop fixture now uses the existing
controlled interpreter argument builder; the E2E admission assertion applies
to noninteractive output, while the interactive case retains its exact output,
submission count and retained-record assertions. The collision fault fixture
uses the explicit duplicate override to reach its distinct no-clobber boundary.

An independent review found no correctness defect in this repair. Local checks
used an isolated, locked Python 3.13.15 environment restored through `uv`, with
an editable installation of this worktree. The focused submission selection
passed 44 tests; the additional malformed-intent selection passed six. Two
Linux native cancellation cases were skipped on macOS and require hosted CI.
Ruff correctness, formatting, Python syntax and whitespace checks passed.
The Python repair adds one net product line and 19 net protection/test lines;
the owner contract adds three lines. No product file, public interface, schema,
mutable-state owner or evidence artifact was added or removed. These local
results do not establish Python 3.11/3.14 full-suite or scheduler acceptance.


### Named admission repairs

The ordinary [follow-up run](https://github.com/lab-cats/EMRYS/actions/runs/36818385910)
completed on `9d34825211412332d42d9348ceca00a20fa370d5`. All four Python 3.14
shards and the complete-suite coverage policy passed, as did Python 3.11 smoke,
static/docs/wheel, workflow lint, shell, guarded R and the three managed-userspace
checks. Managed golden restoration remained failed: renv 1.2.3 selected
S4Arrays 1.12.1 instead of locked 1.12.0, and the strict synchronization check
rejected it. No complete Python 3.11 or selected synthetic-E2E pass is claimed.
The exact archived scientific package remains available. A separately reviewed
renv 1.2.4 proposal preserves all scientific package pins; its approval was still
pending when these independent admission repairs were prepared.

- Empty FASTA headers now enter the existing `ReferenceContigError` path. The
  shared parser serves Init, reference sidecars, split-N validation, provenance
  and the STAR wrapper; no caller-specific parser was added. Existing valid-name,
  ordering, length and other refusal behavior remains in place. Thirty focused
  tests and five tiny caller probes passed.
- The existing profile path normalizer now refuses lexical filesystem roots for
  both scratch parents and module initialization. Nonexistent compute-side paths
  still admit without submitting-host existence checks; compute-side canonical
  root protection remains separate. Sixty-one profile tests passed.
- Report eligibility and complete reuse share one existing reporting-owner policy
  before profile selection or scheduling. Already-complete execution is read-only
  and needs no profile, job or application log. Incomplete generation retains
  delegate admission and fresh execution-context inspection. Forty-nine focused
  reporting tests passed, including actual failed/obsolete Run refusal and
  preserved transport/logging fault assertions.

Independent review found no blocking defect. These local Python 3.13.15 fixture
checks do not establish final-commit hosted CI, real report rendering, scheduler,
site or scientific acceptance. Ruff correctness/format and whitespace checks
passed. The three repairs add 23 net product lines (FASTA 1, profile 3, Report 19);
with the earlier CI repair the approved exception uses 24 of 100 lines. There are
no new product files, schema changes, package installations in product execution,
new registries or evidence deletions. Tests and documentation are separate from
this product accounting.


### Approved design and interface follow-up

The [R closure proposal](../../src/emrys/evidence/runtime_availability/README.md#proposed-r-dependency-closure)
uses standard installed-package dependency enumeration and the existing package
hasher. It identifies every binding/readmission owner and leaves derived IDs,
seal migration, Analysis roots and bounds for a separate implementation decision.
No closure or automatic-snapshot behavior was changed.

The [installed extension check](../tasks/extension-01-discovery.md#october-1-installed-interface-verification)
used a non-editable core wheel from exact `9d348252` source and separate real
Analysis/reporter entry points. Bounded admission, execution, validator and
identity-change cases passed. Actual shared reconciliation reproduced EX-13;
public complete Run/report acceptance remains blocked. An independent review
rehashed all 57 retained manifest entries without a mismatch. The sources,
six wheels, fixtures and logs remain in a local temporary evidence bundle,
not tracked product artifacts or institutional/scientific proof.

The [release checklist](../tasks/release-readiness.md#october-1-integrated-source-readiness-review)
separates the current integrated-source review from historical September findings.
It selects no new distribution/platform promise, release version or publication.
These documentation and verification outcomes do not close RUNTIME-CLOSURE-01,
EXTENSION-01 or RELEASE-01. Independent documentation review found no blocking
overclaim; structure and local links passed for 199 Markdown documents and three
Mermaid sources.


### Approved renv archive-metadata repair

The owner separately approved the reviewed renv 1.2.3 to 1.2.4 update on
2026-10-01. The previous ordinary [run](https://github.com/lab-cats/EMRYS/actions/runs/36820951934)
on `f4eaaa41764cf8f89b8d6e79e57214cadd30151c` passed every selected job except
managed golden restoration, including all Python 3.14 shards and coverage.
The complete [Python 3.11 run](https://github.com/lab-cats/EMRYS/actions/runs/36820988652)
also passed: 3,374 tests passed and eight skipped. The managed-R artifact
retains the exact S4Arrays 1.12.0/1.12.1 mismatch. The named FASTA diagnostic
now has local caller and hosted regression evidence; REFERENCE-INPUT-01 is
complete at that bounded evidence level.

The repair uses the upstream renv archive-metadata behavior instead of changing
scientific packages or adding an installer workaround. Only renv's version in
`renv.lock` changed; independent deep comparison confirmed that all 72 other
package records, repositories and settings are unchanged. The activation body
matches the reviewed upstream template with its version and cache-MD5 header;
existing Python, Make and fixture consumers now agree on 1.2.4. Existing CI
cache keys already include the lock, so no cache policy or workflow change is
needed. The strict post-restore version check remains in force if archive
metadata is unavailable and renv falls back to newer metadata.

Independent review found no blocker. Fifty existing targeted environment,
Doctor-manager, materialization and Make-contract tests passed in the locked
Python 3.13.15 environment. The non-installing shell R-environment contract,
ShellCheck, shell/R/Python syntax, Ruff correctness/format and whitespace
checks passed. No native dependency rebuild or scientific computation was run
locally; fresh managed restore, Doctor/golden path and the selected real-tool
E2E scenarios remain hosted-CI requirements for the updated candidate.

Existing operator libraries with renv 1.2.3 require explicit restoration through
the documented operator path; compute and inspection still never repair
packages. This update changes no product line count and adds no product file.
The approved named-correctness exception therefore remains 24 of 100 net product
lines, with tests, metadata and documentation counted separately.
