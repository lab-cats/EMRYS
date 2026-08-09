# NORAD pipeline plan

This document owns current pipeline evidence ceilings, open package families,
and package acceptance. Task scope belongs to [task cards](../tasks/README.md),
current blockers to [`HANDOFF.md`](../operations/HANDOFF.md), commands to the
[`RUNBOOK.md`](../operations/RUNBOOK.md), and rationale to
[`DECISIONS.md`](DECISIONS.md).

## Pipeline evidence

| ID | Purpose | Current evidence ceiling |
| --- | --- | --- |
| `00a` | Build STAR index | cluster-proven before source relocation |
| `00b` | Convert GTF to BED12 | cluster-proven before source relocation |
| `00c` | Build FASTA sidecars | cluster-proven before source relocation |
| `01` | STAR alignment | cluster-proven before source relocation |
| `02` | Canonical BAM | cluster-proven before source relocation |
| `02b` | BAM QC | cluster-proven evidence set before source relocation |
| `03` | Infer library orientation | cluster-proven before source relocation |
| `04` | Mark duplicates | cluster-proven before source relocation |
| `05` | Split N cigars | cluster-proven before source relocation |
| `06` | Split mechanical orientations | cluster-proven before source relocation |
| `07` | Cohort mpileup | local mocked-runtime only |
| `08` | Preprocess and annotate VCFs | local real-R fixtures only |
| `09` | Paired CMH ranking | local real-R fixtures only |
| `09c` | Scientific evidence review package | local synthetic fixtures only |

Physical relocation created no new runtime or cluster proof. Step `09`
produces CMH-ranked candidates, not validated editing sites. Step `09c`
tooling does not constitute completed scientific review.

## Implemented platform surfaces

- Fourteen semantic DAG owners, neutral contracts and libraries, reporting, and
  evidence tools occupy their allowed homes. Exact paths and dependency
  direction belong to
  [`SOURCE_TOPOLOGY.md`](../../src/norad/contracts/SOURCE_TOPOLOGY.md).
- Artifact, review, run-summary, report, runtime-preflight, reference-
  provenance, and storage contracts are implemented and locally fixture-tested.
- Canonical run-summary assembly keeps its public command and compatibility
  bindings over bounded private document, publication, transaction, validation,
  projection, and scientific-review owners; no production summary exists.
- Static HTML/PDF/TSV reporting and the populated demo are locally renderer-
  tested with synthetic inputs. Public renderer paths are thin compatibility
  facades over bounded private model, validation, projection, runtime,
  transaction, and publication owners; no production report exists.
- Current audit and non-regression routes are
  [`REFACTOR_AUDIT.md`](REFACTOR_AUDIT.md) and
  [`TEST_BASELINE.md`](TEST_BASELINE.md).
- Dated implementation evidence remains in [`docs/history`](../history/) and
  Git; it is not a second current roadmap.

### Populated demo report

`make demo-report` creates the complete synthetic HTML/PDF/TSV bundle from
explicit fixture inputs. It remains provisional demonstration output, not
production, cluster, scientific-review, or biological evidence.

## Open package families

The unselected local-pilot dependency order is:

```text
SETUP-03A + INTAKE-03A + PROFILE-03A
                -> CLI-03A -> E2E-03A -> ONBOARD-03A
```

`INTAKE-03A` also requires an accepted `INTAKE-02E` design. These
relationships do not select work.

Reporting remains split across characterization, contract, projection,
usability, and default-profile cards; renderer decomposition is implemented.
Logging, validation
receipts, documentation maintenance, future acquisition/analysis, and
installable-control-plane cards remain unselected. `UNREFINED` proposals are
not actionable.

## Package acceptance

Every package must:

- remain inside one approved objective and preserve public behavior unless a
  separately authorized decision changes it;
- update directly affected implementation, tests, contracts, and live
  operational documentation;
- preserve deterministic bytes, schemas, exit behavior, validation-before-
  publication, locking, no-clobber rules, rollback, recovery, and evidence
  vocabulary where contracted;
- retain stage-specific semantics unless multiple real consumers and
  independent tests justify a neutral seam;
- label local fixtures, real runtime, cluster execution, scientific review, and
  biological readiness separately; and
- validate in proportion to changed behavior and shared risk.

Documentation-only work must preserve live operational and scientific meaning
and pass the documentation gate. Task cards and historical records are not
live canonical owners: completed cards are deleted, surviving cards are not
path-repaired, and `docs/history` is maintained separately.

## Scientific exit boundary

`science_review_complete_exploratory` remains provisional.
`biological_interpretation_ready` is reserved until a separately approved
scientific policy defines and satisfies its exit criteria. No local structural
or reporting gate may promote either state.
