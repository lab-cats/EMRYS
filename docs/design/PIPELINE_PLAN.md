# NORAD pipeline plan

This is the authoritative pipeline/package roadmap, status matrix, acceptance
criteria, and approved branch lineage. Current checkout details belong in
[`../operations/HANDOFF.md`](../operations/HANDOFF.md); commands belong in
[`../operations/RUNBOOK.md`](../operations/RUNBOOK.md).

## Pipeline

| ID | Purpose | Acceptance boundary | Status |
| --- | --- | --- | --- |
| `00a` | Build STAR index | Source identity, contigs, index structure, and configured overhang inspected | cluster-proven |
| `00b` | Convert GTF to BED12 | BED12 structure, sorting, blocks, and GTF agreement inspected | cluster-proven |
| `00c` | Build FASTA sidecars | FASTA/FAI/DICT identity and contig agreement inspected | cluster-proven |
| `01` | STAR alignment | STAR outputs, logs, mapping summary, and BAM inspected | cluster-proven |
| `02` | Canonical BAM | BAM/BAI, coordinate sorting, read groups, and alignment RG tags inspected | cluster-proven |
| `02b` | BAM QC | quickcheck and flagstat evidence inspected | cluster-proven evidence set |
| `03` | Infer library orientation | RSeQC structure and paired-orientation fractions inspected | cluster-proven |
| `04` | Mark duplicates | BAM/BAI/metrics, sorting, RG preservation, and duplication metrics inspected | cluster-proven |
| `05` | Split N cigars | declared output transaction and validation inspected | cluster-proven |
| `06` | Split mechanical orientations | outputs, indexes, and count arithmetic inspected | cluster-proven |
| `07` | Cohort mpileup | receipts, VCF structure, selectors, hashes, sample order, and counts inspected with real runtime | local mocked-runtime only |
| `08` | Preprocess and annotate VCFs | three-output transaction, schemas, hashes, ordering, uniqueness, and counts inspected | local real-R fixtures only |
| `09` | Paired CMH ranking | six-output transaction, statuses, subsets, mutation spectrum, and PDFs inspected | local real-R fixtures only |
| `09c` | Validate scientific evidence | explicit production evidence reconciled and review state lawfully published | local synthetic fixtures only |

Steps `07`–`09` are not cluster-proven. Step `09c` tooling does not constitute
a completed production review.

## Evidence and reporting packages

| Package | Responsibility | Status |
| --- | --- | --- |
| `artifact-schema-v1` | Public artifact, scientific-review, run-summary, and report-receipt contracts | implemented and fixture-tested |
| `artifact-adapters-v1` | Explicit read-only artifact inventory adaptation | implemented and fixture-tested |
| `artifact-run-summary` | Canonical summary and deterministic TSV/QC projections | implemented and fixture-tested |
| `report-html-v1` | Static self-contained HTML rendering | implemented and locally renderer-tested |
| `report-html-v1a-report-table-approvals` | Exact run-bound supplemental-table approvals | implemented and fixture-tested |
| `report-html-v1b-docs-responsibility-consolidation` | One canonical owner per documentation category | completed |
| `report-exports-v1` | Atomic HTML/PDF/TSV/report-receipt bundle | implemented and locally tested |
| `post09-runtime-preflight` | Explicit-profile runtime availability checks | implemented and locally fixture-tested; CSU batch execution pending |
| `post09-reference-provenance` | Explicit reference hashes, provenance, and contig reconciliation | implemented and locally fixture-tested; production execution pending |
| `post09-storage-inventory-retention` | Explicit storage measurement and retention-policy recording | implemented and locally fixture-tested; production inventory and approvals pending |
| `post09-validation-report-00a` | Structured STAR-index validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-00b` | Structured BED12/GTF validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-00c` | Structured FASTA/FAI/DICT validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-01` | Structured STAR-alignment output validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-02` | Structured canonical-BAM validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-02b` | Structured persisted BAM-QC validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-03` | Structured RSeQC orientation-fraction validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-04` | Structured marked-BAM/Picard-metrics validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-05` | Structured split-N-cigar/reference-prerequisite validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-06` | Structured mechanical-orientation output/count validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-07` | Structured VCF/receipt/selector/manifest/count validation and report propagation | implemented and locally fixture-tested; real-runtime and production report pending |
| `post09-validation-report-08` | Structured three-output preprocessing transaction validation and report propagation | implemented and locally fixture-tested; production report pending |
| `post09-validation-report-09` | Structured six-output CMH transaction and semantic validation with report propagation | implemented and locally fixture-tested; production report pending |
| `refactor-00-comprehensive-audit` | Final evidence-ranked audit, one-time locked dependency refresh, do-not-abstract boundaries, and documentation consistency correction | complete; the next descendant requires live clean, pushed, upstream-equal verification |
| `refactor-01-test-baseline` | Measured Python line/branch baseline and public-contract risk-to-test matrix | approved; next |
| `refactor-01a-*` through `refactor-01z-test-sufficiency-gate` | Evidence-determined characterization packages and final refactor-readiness decision | approved sequence; exact gap branches pending baseline evidence |
| `refactor-02-high-level-plan` through `refactor-02d-review-usability` | High-level/detailed plan plus architecture, reliability, and usability reviews | approved sequence; pending |
| `refactor-03a-*` | Small reviewed refactor packages, one architectural concern per branch | exact packages pending the three reviews |
| `refactor-99-final-audit` | Final finding disposition, compatibility comparison, measured validation, and handoff | approved final local gate; pending |

Schema validation, adapter completion, summary completion, table approval, and
report rendering never promote computational, scientific, or biological
state.

## Approved local lineage

```text
report-html-v1a-report-table-approvals
└── report-html-v1b-docs-responsibility-consolidation
    └── report-exports-v1
        └── post09-runtime-preflight
            └── post09-reference-provenance
                └── post09-storage-inventory-retention
                    └── post09-validation-report-00a
                        └── post09-validation-report-00b
                            └── post09-validation-report-00c
                                └── post09-validation-report-01
                                    └── post09-validation-report-02
                                        └── post09-validation-report-02b
                                            └── post09-validation-report-03
                                                └── post09-validation-report-04
                                                    └── post09-validation-report-05
                                                        └── post09-validation-report-06
                                                            └── post09-validation-report-07
                                                                └── post09-validation-report-08
                                                                    └── post09-validation-report-09
                                                                        └── refactor-00-comprehensive-audit
                                                                            └── refactor-01-test-baseline
                                                                                └── refactor-01a-<test-gap>
                                                                                    └── ...evidence-determined test branches...
                                                                                        └── refactor-01z-test-sufficiency-gate
                                                                                            └── refactor-02-high-level-plan
                                                                                                └── refactor-02a-detailed-plan
                                                                                                    └── refactor-02b-review-architecture
                                                                                                        └── refactor-02c-review-reliability
                                                                                                            └── refactor-02d-review-usability
                                                                                                                └── refactor-03a-<reviewed-phase>
                                                                                                                    └── ...reviewed refactor branches...
                                                                                                                        └── refactor-99-final-audit
```

Do not perform remote or cluster
validation during this sequence.

## Package acceptance criteria

### Documentation consolidation

- one canonical owner for each mutable fact;
- no current status, detailed product contract, tool snapshot, commit ID, test
  total, or current-next-stage narrative in `AGENTS.md`;
- one authoritative status matrix and branch lineage in this file;
- takeover evidence only in `HANDOFF.md`;
- executable commands only in `RUNBOOK.md`;
- durable rationale only in `DECISIONS.md`;
- open questions plus a resolved index only in `QUESTIONS.md`;
- troubleshooting contains symptom, cause, diagnosis, and fix—not roadmap;
- current topology in `ARCHITECTURE.md`, future constraints in
  `FUTURE_ARCHITECTURE.md`;
- standalone `.mmd` files are canonical and contain no transient status;
- demos are explicitly presentation material or dated snapshots;
- unique scientific and validation evidence is preserved;
- no NORAD workflow, validator, schema, config, scientific-method, or
  public-contract behavior changes; the separately committed one-time
  dependency lock refresh is limited to resolving the guarded local gate;
- complete applicable local and documentation gates pass.

### Comprehensive refactor program

- [`REFACTOR_AUDIT.md`](REFACTOR_AUDIT.md) owns the evidence-ranked findings,
  test-first dispositions, and explicit retained/deferred boundaries;
- Phase `01` records a measured global Python line/branch baseline and a
  public-contract risk-to-test matrix before production refactoring;
- critical/high-risk gaps receive cohesive characterization branches; exact
  branch names come from evidence rather than placeholders;
- `refactor-01z-test-sufficiency-gate` records the measured readiness decision;
- Phase `02` produces high-level and detailed plans followed by separate
  architecture, reliability, and usability reviews;
- Phase `03` implements only reviewed, bounded architectural concerns while
  preserving public contracts;
- Step `07`–`09` scientific/statistical algorithms remain unchanged until
  inspected remote baseline evidence and separate authorization exist;
- `refactor-99-final-audit` classifies every finding and closes the local
  program without beginning cluster work.

### Report exports

Extend the report renderer with explicit `html`, `pdf`, and `all` formats,
defaulting to `all`. Publish an all-or-none bundle containing HTML, PDF,
deterministic summary TSV, and a report receipt published last.

Use canonical run-summary `1.1.0`, the existing report-receipt `1.1.0`
contract, pinned Quarto with bundled Typst, and an explicitly pinned
pure-Python PDF reader. Preserve the existing HTML path and safely handle a
valid HTML-only predecessor.

Validate PDF signatures, EOF, extractable text, page order, and the applicable
banner on every page. Preserve explicit-input-only behavior, owned locks,
staging, stable input rechecks, no-clobber rules, rollback, cleanup, and
recovery evidence. Rendering must not install software, invoke analysis
engines, discover inputs, or promote state.

Test incomplete, failed, missing, exploratory, empty-candidate, orientation,
strand, truncation, limitation, reserved-state, mutation, determinism,
accessibility, isolation, lock, signal, cleanup, and rollback cases without
regressing HTML behavior.

### Foundation packages

`post09-runtime-preflight` publishes read-only explicit-profile tool,
namespace, hash-utility, and visibility checks. It never installs software or
claims runtime proof merely because preflight passed.

`post09-reference-provenance` explicitly inventories FASTA, FAI, DICT, GTF,
BED, STAR index, hashes, annotation provenance, and contig agreement. It
reports inconsistencies but never repairs references.

`post09-storage-inventory-retention` records storage roots, sizes, capacity or
quota evidence, and an approved retention-policy TSV. It never deletes,
moves, compresses, or cleans data.

### Per-step validation reports

Each validator is dry-run-first, explicit-input-only, and publishes:

```text
results/qc/validation/<step>/<scope>.validation.tsv
```

with:

```text
step_id
scope_id
check_id
status
observed
expected
detail
```

Each package adds its read-only artifact adapter and an end-to-end fixture
showing the status in the run summary and consolidated HTML/PDF report. Do not
introduce a generic dispatcher or job array.

Checks cover:

- `00a`: index/source identity, contigs, and `sjdbOverhang`;
- `00b`: BED12 structure, sorting, blocks, and GTF agreement;
- `00c`: FASTA/FAI/DICT identity and contig agreement;
- `01`: STAR outputs, logs, BAM, and mapping summary;
- `02`: BAM/BAI, sorting, read groups, and alignment RG tags;
- `02b`: quickcheck and flagstat;
- `03`: RSeQC structure and paired-orientation fractions;
- `04`: BAM/BAI/metrics, sorting, RG preservation, and duplication metrics;
- `05`: parameterized existing output validation;
- `06`: orientation outputs and count arithmetic;
- `07`: receipts, VCF structure, selectors, hashes, order, and counts;
- `08`: three-output transaction, schemas, hashes, ordering, uniqueness, counts;
- `09`: four exact TSV headers; analysis-bound basenames; one shared native
  output parent; six distinct physical outputs; explicit analysis/cohort and
  provisional-policy identity; complete ordered Step `08` candidate universe;
  count-derived target/test/call, depth, AF, and enabled-background semantics;
  type/range validation of reported CMH fields; global BH recomputation from
  the reported p-values; exact significant subset; summary/provenance
  reconciliation; canonical mutation spectrum; and PDF structure. Independent
  CMH statistic, p-value, odds-ratio, and estimability recomputation from DP/AD
  counts is a critical audited gap.

## Deferred remote lineage

Only after new user direction and completion of the local sequence:

```text
refactor-99-final-audit
└── validate-step-07
    └── validate-step-08
        └── validate-step-09
            └── validate-step-09c-scientific-evidence
                └── post09-targeted-reruns
```

Remote promotion is upstream-sequential. Each validation branch inspects
evidence, regenerates the structured summary and reports, performs a separate
docpatch, and reaches a clean pushed gate before the next branch.

## Scientific exit boundary

Mechanical orientation, annotation provenance, statistical policy,
replicate/sensitivity evidence, candidate adjudication, and limitations require
explicit review. `science_review_complete_exploratory` remains provisional.
`biological_interpretation_ready` is reserved until a separately approved
policy defines and unlocks its stricter exits.
