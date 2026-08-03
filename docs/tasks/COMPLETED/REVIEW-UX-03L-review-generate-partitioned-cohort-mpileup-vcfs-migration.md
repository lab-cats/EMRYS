# REVIEW-UX-03L — Review partitioned cohort mpileup migration usability

## Objective

Review `MIG-03L` for operator, maintainer, automation, recovery, scientific-
language, and evidence continuity across every explicit Step `07` path change.

## Why this exists

The migration changes a directly executable Bash producer path, explicit-
interpreter validator path, submitted-job path and delegated command, Make/
coverage/test/helper paths, and implementation provenance. Correct relocation
can still leave stale commands, hidden selector/depth/filter/tool/output/lock
selection, calling or biological overclaim, incorrect dry-run claims, unsafe
retry guidance, or an undiscoverable final owner.

## Fixed decisions

- Review only; do not redesign arguments, outputs, messages, scheduler or tool
  policy, mechanical labels, selectors, pileup/filter behavior, transaction,
  or evidence state.
- Preserve explicit repository-relative invocation without installation,
  ambient import discovery, global `sys.path`, or a legacy alias.
- Keep fixture/fake-tool migration evidence distinct from real bcftools,
  scheduler, cluster, production, scientific-review, variant/editing-site,
  or biological-readiness proof.

## Blocked by

- [REVIEW-REL-03L](REVIEW-REL-03L-review-generate-partitioned-cohort-mpileup-vcfs-migration.md) — Required: completed reliability review fixes the architecture and reliability obligations used here.

## Completion unblocks

- [MIG-03L](../IN_PROGRESS/MIG-03L-migrate-generate-partitioned-cohort-mpileup-vcfs-owner.md) — Fully: the required fresh-branch boundary is published and migration selection began with all three reviews closed.

## Prerequisites

- Inspect the committed reliability-reviewed cards against public CLI,
  arbitrary-CWD, producer, validator, scheduler submission, Make, runbook/
  troubleshooting, artifact, helper, evidence-status, and rollback journeys.

## Required context

- `MIG-03L`; Step `07` runbook/troubleshooting commands; producer and
  validator help; public CLI and scheduler characterization; Make/literal
  expansions; coverage/artifact/helper paths; owner contract; current/future
  topology; partition manifests; selector/depth/filter/bcftools/output/lock/
  receipt diagnostics; mechanical-orientation and non-calling language; and
  the three-file transaction evidence boundary.

## Questions owned by this card

- None.

## In scope

- Direct producer and explicit-interpreter validator root/arbitrary-CWD dry-
  run/execute/repeat journeys; exact mechanical and non-calling wording;
  partition/selector/FAI/regions-file, depth, filter, bcftools, input, output,
  scratch, lock, and receipt selection; staged publication, rollback failure,
  mutation, relative-path disagreement, residue, and safe preservation;
  scheduler submit CWD, modules, overrides, version, logs, delegation, and
  stale outputs; Make/test commands; implementation/evidence provenance;
  owner findability; links; rollback; and next-safe-action instructions.

## Out of scope

- New aliases, wrappers, package installation, PATH/`PYTHONPATH` redesign,
  transaction repair, receipt/provenance/recovery redesign, selector or
  pileup/filter/depth policy, calling, scheduler hardening, cluster
  submission, dependency action, scientific/biological interpretation, or
  future units.

## Deliverables

- Journey-based findings with exact card/documentation corrections and dated
  audit dispositions.

## Acceptance evidence

- Every supported healthy/failure transition has one final command, owned
  diagnostic, artifact expectation, preservation route, and evidence ceiling.
- The owner README and runbook make producer/validator/scheduler, dry-run
  effects, mechanical/non-calling meaning, selector/depth/filter/tool/output/
  lock/receipt selection, rollback residue, focused tests, evidence status,
  provenance, and rollback discoverable without an alias or proof overclaim.

## Canonical documentation updates

- This card, `MIG-03L`, current roadmap/handoff where status changes, and the
  dated refactor log.

## Escalation conditions

- Stop if continuity requires a legacy path, changed public interface,
  dependency installation, public import identity, calling/scientific/
  biological claim, or an unreviewed alias/package contract.

## Completion record

Completed against clean, published, local/upstream/live-remote-equal selection
checkpoint `3ec83073ceae62eb6a59afe9470941cd1bf1eec3`.

- **High — every supported journey needs one explicit final path:** at
  documentation close, replace every live Step `07` producer, validator, job,
  focused-test, helper-matrix, artifact-provenance, and coverage path. Root use
  directly invokes the mode-`0755` producer at
  `src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/step_07_bcftools_mpileup_by_chrom_and_strand.sh`
  and uses an explicit interpreter for the mode-`0644` validator at the same
  owner. Submit the mode-`0644` job through `sbatch` from the checkout after
  creating `logs/`; explicit Bash is a local wrapper diagnostic, not cluster
  execution. Arbitrary-CWD use makes the producer/interpreter, every manifest,
  selector file, BAM/BAI root, FASTA/FAI, output/report root, bcftools, checkout,
  and final owner path absolute. Use an absolute producer output root so its
  receipt VCF paths agree with the validator's resolved arguments. No installed
  command, package import, legacy alias, wrapper, symlink, ambient `PYTHONPATH`,
  or global `sys.path` route is supported.
- **High — producer, validator, and scheduler dry runs have different effects:**
  producer dry-run validates manifests, FAI-bound selector, relative selector-
  file resolution, every BAM/BAI, tool resolution, depth/filter values, and
  manifest hashes; prints both exact pipelines plus output, lock, temporary,
  validation, and publication paths; invokes no bcftools child; and creates no
  directory or file. Validator dry-run reads and snapshots all six explicit
  inputs, prints five report rows plus the completion line, invokes no
  bcftools, and writes no report. Scheduler `EXECUTE=0` still changes to the
  submit/fallback directory, creates `logs/`, runs module and executable/version
  diagnostics when applicable, and delegates producer dry-run. Preserve its
  one CPU, `/tmp`, defaults/overrides, warning-only unusable-tool preflight,
  version-command failure, basename forwarding, exact child path, and stale-
  three-file false success; scheduler dry-run is not side-effect-free.
- **High — recovery requires evidence preservation, not a same-name retry:**
  before cleanup, recovery, or retry, preserve all three finals, run-token
  temporary/backups, lock and owner, both manifests, every BAM/BAI, FASTA/FAI,
  regions file, unrelated bytes, producer/wrapper streams, scheduler job/
  accounting/logs, checkout/submit CWD, exact bcftools path/version, depth,
  filter, and environment. A receipt-publication failure followed by prior-FWD
  restoration failure can propagate exit `67`, leave the prior FWD final
  absent while its backup survives, restore prior REV and receipt, remove owned
  temps/lock, and create no recovery marker. Receipt visibility, timestamps,
  counts, or residue absence cannot identify a clean/current attempt. Do not
  combine files, reconstruct a missing member, delete a foreign lock, trust
  stale wrapper success, or rerun the same output path. Rule out every producer
  and Step `08` reader first; a separately authorized diagnostic retry needs a
  distinct output root and remains nonproduction.
- **Medium — ownership, validation, and scientific language must remain exact:**
  update the contract's unimplemented/flat-owner paths, runbook, troubleshooting,
  inventory/topology/test/documentation routes, neutral-library references,
  Step `06` predecessor, Step `08` consumer, artifact provenance, and partition-
  manifest navigation. `FWD_like`/`REV_like` are mechanical groups. Producer
  exit `0` proves its current structural checks and three-file publication, but
  unhashed BAM/BAI/reference/FAI/regions/tool/depth/filter/VCF state remains
  unbound. Validator exit `0` may publish failed rows and does not check
  bcftools, selector-bound coordinates, REF/ALT/FORMAT/filter semantics,
  immutable inputs, output hashes, or attempt identity. Scheduler exit `0` may
  accept stale outputs. None establishes variants, RNA-editing sites,
  transcript strand, scientific readiness, or biological readiness.
- **Accepted findability, tests, documentation, and rollback:** add one adjacent
  owner README that owns root/arbitrary-CWD producer and validator commands,
  checkout-root scheduler submission, selector/depth/filter/tool/output/lock/
  receipt choices, focused direct/central tests, preservation, provenance,
  evidence ceiling, and next safe action. Add a dedicated Step `07` producer/
  wrapper partial-transaction and rollback-failure troubleshooting route and
  link structured validation to it. Diagrams need no update because semantic
  identity, direct DAG edges, and public data flow do not change. Revert
  documentation first, the atomic five-move/nine-update cutover second, then
  scheduler, validator, producer stability/provenance, transaction/recovery,
  and pipeline/selector baselines in reverse order. Git rollback never changes
  runtime artifacts or recovery evidence. No compatibility surface is
  justified.
- **Evidence boundary:** this was a separate committed-time read-only pass by
  the same campaign agent; independent authorship is not claimed. No source,
  test, harness, dependency, real bcftools, scheduler, cluster, production,
  scientific-review, variant/editing-site, or biological evidence changed or
  ran.
- **Card-boundary gate:** `git diff --check` passed and the exact RUNBOOK
  documentation validator reported only the nine inherited `UNREFINED` card-
  location findings. No usability-review path, lifecycle, dependency, cycle,
  orphan, anchor, or diagram finding remains. This expected-only ceiling is
  nonpassing, not green, and not authority to alter inherited lifecycle state.
