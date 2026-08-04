# LIB-02K — Extract the reference-contig parser library

## Objective

Extract the exact ordered FASTA, FAI, and DICT contig/length parsers into their
permanent neutral library and cut over all three repository consumers without
changing parser results, failure behavior, consumer aggregation, evidence, or
public command behavior.

## Why this exists

Reference provenance currently owns parsers consumed through private exact-file
bridges by the final Step `00c` and Step `05` validators. Completed `LIB-02F`
proved that the three consumers share only this narrow safety-critical seam and
fixed `src/norad/libraries/reference_contigs.py` as its neutral home. The peer-
owner bridges must be removed before reference provenance can move to its final
evidence owner.

## Fixed decisions

- Create one standard-library-only owner at
  `src/norad/libraries/reference_contigs.py` and independent API tests at
  `tests/libraries/test_reference_contigs.py`.
- Expose one parser-specific `RuntimeError` subclass and the exact ordered
  `parse_fasta`, `parse_fai`, and `parse_dict` APIs. Keep the duplicate/empty
  check and raiser private.
- Preserve exact return order and values, parser messages, explicit/default
  decoding behavior, the parser-error `RuntimeError` category, raw
  `OSError`/`UnicodeError` and characterized raw conversion/index exceptions,
  accepted empty names/zero lengths where the current parsers accept them, and
  every current malformed/duplicate/empty boundary. Only the error's neutral
  owner and truthful parser-specific class name change. This card extracts
  characterized behavior; it does not repair it.
- Give reference provenance and the Step `00c`/`05` validators one validated,
  ready-marked, cached exact-file module identity without package discovery,
  installation, `PYTHONPATH`, or `sys.path` mutation.
- Loader-integrity failures may substitute only the truthful neutral owner name
  and final path in their diagnostics. Preserve exit status, empty stdout, no-
  traceback behavior, normalized reason text, cache/partial cleanup, and all
  other public bytes.
- Reference provenance retains inventory, hashing, STAR/GTF/BED parsing,
  agreement, evidence assembly, CLI, stable-input checks, publication, locking,
  rollback, and recovery. Its per-role parser aggregation continues after a
  failed role.
- Step `00c` retains independent per-role parsing, three structure rows, and two
  ordered-agreement rows. Step `05` retains ordered FASTA-to-FAI-to-DICT
  short-circuit parsing and its single reference-sidecars evidence row.
- Do not move reference provenance, create its later migration card, add a
  compatibility owner, broaden the neutral API, or change another contig parser
  that was not approved by `LIB-02F`.

## Blocked by

- None.

## Completion unblocks

- None.

## Prerequisites

- Use completed
  [LIB-02F](../COMPLETED/LIB-02F-define-shared-library-ownership.md) as the
  semantic boundary and
  [RPT-05A](../COMPLETED/RPT-05A-relocate-reporting-to-final-source-home.md) as
  the clean, published campaign predecessor.
- Start from clean, published, live-remote-equal RPT-05A documentation close
  `8a5cf28df6d5f595ef74bde6f22ad376dc41c374`.
- Freeze the current parser AST/outputs/messages/error categories and raw
  exceptions, consumer module identities, Step `00c` per-role aggregation,
  Step `05` short-circuit aggregation, direct/CLI/arbitrary-CWD bytes, modes,
  hashes, and measured coverage before implementation.

## Required context

- `LIB-02F`, `SOURCE_TOPOLOGY.md`, the three current parser consumers, their
  direct tests, neutral-library loader conventions, public CLI characterization,
  and coverage policy only.

## Questions owned by this card

- None.

## In scope

- One neutral parser owner and independent suite; exact-file loader/cached-
  identity cutover in reference provenance and the final Step `00c`/`05`
  validators; removal of the command-owned parser definitions and both private
  validator bridges; loader-fault, parser-edge, consumer-aggregation, parity,
  arbitrary-CWD, stale-dependency, duplicate-owner, and measured-coverage
  tests; impact-directed documentation close.

## Out of scope

- Contig agreement policy; evidence rows or schemas; reference inventory,
  hashing, snapshots, CLI, publication, locking, rollback, or recovery;
  reference-provenance relocation; Step `00c`/`05` owner behavior; other FAI
  parsing; packaging; scheduler, ingestion, orchestration/profile, runtime,
  cluster, production, scientific-review, or biological work.

## Deliverables

- One final neutral reference-contig parser identity with independent tests,
  all three consumers cut over, and no command-owned duplicate or peer-owner
  bridge.

## Acceptance evidence

- Frozen pre/post parity proves exact ordered parser outputs, messages,
  `RuntimeError` failure behavior and raw exceptions, encoding behavior,
  accepted/rejected edge cases, consumer aggregation, public CLI bytes, and
  arbitrary-CWD behavior, apart from the approved neutral error owner/name and
  exact truthful loader owner/path substitutions.
- Exact searches and import-isolation tests prove one neutral identity, no
  duplicate parser definitions, no reference-provenance load from either
  validator, no compatibility owner, and no package/path mutation.
- The independent library suite, all three direct consumer suites, affected
  public/validation tests, measured Python coverage, applicable local gates,
  documentation validation, and semantic diff review pass at the final
  executable state.

## Canonical documentation updates

- Neutral-library ownership, final Step `00c`/`05` consumer contracts,
  functional-owner inventory, future architecture, source topology only if
  current-state wording changes, runbook/troubleshooting bridge guidance,
  `TEST_BASELINE.md`, `PIPELINE_PLAN.md`, `HANDOFF.md`, lifecycle links, and this
  card.

## Escalation conditions

- Stop for any change to ordered parser results, messages, exception behavior
  beyond the approved neutral error owner/name, raw-read behavior,
  duplicate/empty rules, Step `00c` per-role aggregation, Step
  `05` short-circuit aggregation, agreement/evidence rows, CLI/help/output
  bytes beyond the exact truthful neutral loader owner/path substitutions,
  hashing, snapshots, publication, or recovery; any external consumer,
  wrapper or compatibility owner, package/import-path/install need, split
  neutral identity, missing independent parity oracle, or scope into reference-
  evidence relocation or a deferred domain.

## Completion record

Selected from clean, published, live-remote-equal RPT-05A documentation close
`8a5cf28df6d5f595ef74bde6f22ad376dc41c374`. The bounded read-only audit
confirmed exactly three consumers and fixed the behavior/parity boundary above.
Pre-change characterization and executable/test work have not begun.
