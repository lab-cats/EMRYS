# REVIEW-UX-03J — Review SplitNCigarReads migration usability

## Objective

Review `MIG-03J` for operator, maintainer, automation, recovery, and evidence
continuity across every explicit Step `05` path change.

## Why this exists

The migration changes a Bash producer path, explicit-interpreter validator
path, submitted-job path and delegated command, Make/coverage/test/helper
paths, and implementation provenance. Correct relocation can still leave stale
commands, hidden GATK/Java/samtools/reference/temp/lock selection, incorrect
dry-run claims, unsafe retry guidance, or an undiscoverable final owner.

## Fixed decisions

- Review only; do not redesign arguments, outputs, messages, scheduler or tool
  policy, reference behavior, transaction behavior, or evidence state.
- Preserve explicit repository-relative invocation without installation,
  ambient import discovery, global `sys.path`, or a legacy alias.
- Keep fixture/fake-tool migration evidence distinct from real GATK, Java,
  samtools, scheduler, cluster, production, scientific-review, or biological
  proof.

## Blocked by

- [REVIEW-REL-03J](../COMPLETED/REVIEW-REL-03J-review-split-n-cigar-reads-with-gatk-migration.md) — Required: completed reliability review fixes the fault, preservation, and parity obligations used by usability review.

## Completion unblocks

- [MIG-03J](MIG-03J-migrate-split-n-cigar-reads-with-gatk-owner.md) — Fully: migration completed after all three reviews closed.

## Prerequisites

- Inspect the committed reliability-reviewed cards against public CLI,
  arbitrary-CWD, producer, validator, scheduler submission, Make, runbook/
  troubleshooting, artifact, helper, evidence-status, and rollback journeys.

## Required context

- `MIG-03J`; Step `05` runbook/troubleshooting commands; producer and validator
  help; public CLI and scheduler characterization; Make/literal expansions;
  coverage/artifact/helper/reference paths; owner contract; current/future
  topology; GATK/Java/samtools/reference/temp/lock diagnostics; and BAM/BAI
  transaction evidence boundary.

## Questions owned by this card

- None.

## In scope

- Explicit-Bash producer and explicit-interpreter validator root/arbitrary-CWD
  dry-run/execute/repeat journeys; GATK/Java/samtools/reference selection;
  project-storage temp and lock paths; staged publication, rollback failure,
  residue and safe preservation; scheduler submit CWD, modules, overrides,
  versions, logs, Bash `3.2`, delegation and stale outputs; Make/test commands;
  implementation/evidence provenance; owner findability; links; rollback; and
  next-safe-action instructions.

## Out of scope

- New aliases, wrappers, package installation, PATH/`PYTHONPATH` redesign,
  transaction repair, receipts/markers, reference or GATK policy, scheduler
  hardening, cluster submission, dependency action, or future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported healthy/failure transition has one final command, owned
  diagnostic, artifact expectation, preservation route, and evidence ceiling.
- The owner README and runbook make producer/validator/scheduler, dry-run
  effects, tool/reference/temp/lock selection, rollback residue, focused tests,
  evidence status, provenance, and rollback discoverable without an alias or
  proof overclaim.

## Canonical documentation updates

- This card, `MIG-03J`, current roadmap/handoff where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, public import identity, or an unreviewed alias/
  package contract.

## Completion record

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `f41f988d36c56ac3212d47d284e3eeef4e88e5ad`.

- **High — every supported journey needs one explicit final path:** at
  documentation close, replace every live Step `05` producer, validator, job,
  focused-test, helper-matrix, artifact-provenance, and coverage path. Root use
  invokes the mode-`0644` producer through Bash and the validator through an
  explicit interpreter. Arbitrary-CWD use makes the producer/interpreter,
  input BAM, reference FASTA, output directory, GATK, Java, samtools, validator
  BAM/BAI/FASTA/FAI/DICT/report, and final owner paths absolute. No installed
  command, package import, legacy alias, wrapper, symlink, ambient `PYTHONPATH`,
  or global `sys.path` route is supported.
- **High — producer, validator, and scheduler dry runs have distinct effects:**
  producer dry-run validates exact input/reference files and executable paths,
  prints run-token scratch/backup/lock/GATK-temp plans, invokes no version or
  data tool, and creates no output directory. Validator dry-run invokes its
  explicit samtools/reference checks, prints five TSV rows plus its completion
  line, and writes no report. Scheduler submission starts from the checkout,
  creates `logs/` before `sbatch`, and names the final mode-`0644` job. The
  wrapper retains submit-CWD fallback, exported `/tmp`, body-level `logs/`,
  sample/input/reference/output defaults and overrides, Java override/home/
  PATH selection with actual version floor, tolerated module diagnostics,
  warning-only missing/unusable GATK or samtools preflight, version-command
  failures, Bash `3.2` dry-run failure, and stale-pair false success.
- **High — rollback-failure recovery must stop same-name reuse:** preserve any
  surviving final BAM/BAI, run-token temp/backup/GATK-temp paths, lock and owner,
  input BAM/BAI and reference triplet, unrelated files, producer/wrapper
  streams, job/accounting/logs, checkout, and selected GATK/Java/samtools paths
  and versions before cleanup or retry. A failed restore can leave the prior
  BAI without the BAM while cleanup erases backups, lock, scratch, and every
  recovery marker; signal cleanup can also leave no attempt marker. Absence of
  those paths is not proof of a clean state. Rule out the recorded lock owner,
  running producer, and downstream Step `06` readers; do not combine pair
  members, infer one attempt from timestamps, remove a foreign lock, or adopt
  stale scheduler success. A separately authorized diagnostic retry uses an
  isolated output directory and explicit validation; Git rollback never
  restores or authenticates runtime artifacts.
- **Medium — ownership and evidence wording must match the final implementation:**
  update the contract's unimplemented/flat-owner text and its stale Step-`00a`
  report and Step-`02` BAM-helper attribution to the final owner, neutral
  `validation_report.py` and `bam_validation.py`, and unchanged public
  `reference_provenance.py` exact-file bridge. Artifact evidence changes only
  implementation path/hash. Producer exit `0` proves structural publication,
  not split-N-cigar transformation or input/tool-attempt binding; validator
  exit `0` may publish failed rows; scheduler exit `0` may accept a stale pair.
  Historical six-sample cluster observations remain historical and are not
  migration proof.
- **Accepted findability, tests, and rollback:** one adjacent owner README and
  the reviewed canonical roster own final commands, focused direct and central
  tests, diagnostics, preservation, provenance, evidence ceiling, and rollback.
  Revert documentation first, the atomic five-move/ten-update cutover second,
  then scheduler, validator, producer admission/signal, and producer
  transaction baselines in reverse order. No compatibility surface is
  justified.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, real GATK, Java, samtools, scheduler, production,
  scientific-review, or biological evidence changed or ran.
- **Card-boundary gate:** `git diff --check` passed and the exact RUNBOOK
  documentation validator reported only the nine inherited `UNREFINED` card-
  location findings. No usability-review path, lifecycle, dependency, cycle,
  orphan, anchor, or diagram finding remains. This expected-only ceiling is
  nonpassing, not green and not authority to alter inherited lifecycle state.
