# Reporting tests

These tests check artifact indexing, run summaries, report models and exports,
Jinja safety, publication, and rendered HTML. They pin candidate selection,
primary/supporting figures, visible figure guidance, ranked candidate cards,
and print behavior, including the absence of scientific disclosure controls
and wide-table wrappers. [Fixtures](fixtures/README.md) supply shared builders
and literal inputs; the [reporting owner](../../src/emrys/reporting/README.md)
defines the production contract and recovery rules.

## Fault injection

Publication and source-identity tests patch real filesystem or validation
functions with scoped pytest monkeypatches. Each patch targets the relevant
path or receipt and delegates other calls. File, lock, and staging faults target
the shared reporting `_files` operations; signal faults target `_signals`.
The artifact context captures its real installed-package observer for later rechecks,
and validated transactions retain real input-recheck callbacks.

The Step 10 adapter semantic-mismatch fixture rebinds only its changed
candidate-context output digest, then requires the bound-reference-window
diagnostic in published failed evidence. Separate contract tests retain the
stale-output-hash refusal; these establish distinct computational boundaries.

Combined publication tests cover the index and summary output set, including
terminal-receipt failure and owned rollback. Summary tests retain independent
schema, deterministic projection, QC, provenance, and current-source checks.
Faults target the actual publisher and read validator, without test-only
production behavior or a second suite for the retired summary publisher.

## Retained synthetic VM and report evidence

This historical observation comes from the former NORAD handoff retained at
[`b9cf4767`](https://github.com/lab-cats/EMRYS/blob/b9cf4767e6ebdf686070410f06b9cc9298582979/docs/operations/HANDOFF.md).
The source names the execution and renderer revisions below, but supplies no
exact VM execution date. It does not describe current report formats or current
CI. The artifact paths identify retained evidence, not supported regeneration
instructions for these obsolete Run contracts.

NORAD science commit
`2587126e7e471b504657c9a43789e870713f8bb6` completed admitted FASTQ intake
through deterministic HTML reporting in lane
`full-cohort-public-2587126e7e47-02`. Slurm job `91` ran for `00:05:14` in one
single-node, two-CPU, 6 GiB allocation on a native ARM64 Ubuntu VM and reached
`COMPLETED/0:0`. The Run was
`run-bb36785424aba063e336ebaecdde4e78d984a4470187b8e1421fd281d3afa04f`.
All 24 declared runtime checks passed against the complete admitted VM
installation, and the lifecycle re-admitted the bound runtime profile before
Slurm submission.

The deterministic fixture used four paired-end libraries with 100,000 read
pairs each and a 5 Mb reference. It verified 34/34 scientific owner tasks across
13 automatic owners, 3/3 reporting transactions, and all 38 DAG rules. Step 09
published three CMH-ranked candidates, one passing the fixed significance
contract; the lab-owned independent Step 09 oracle matched. The retained legacy
HTML is 214,102 bytes with SHA-256
`50d4cc7bd26cd706544283ce532000ee6a900f8a8195ccb29b021809670afef8`.

The lane was sealed without rerunning science or reporting. Its portable
manifest records 861 entries: 206 directories, 655 files, and 210,401,447
regular bytes. Guest, private-host, and create-absent host-collection admission
passed. The retained tree is
`runs/full-cohort-public-2587126e7e47-02` in the Linux validation lab. The guest
seal SHA-256 is
`8c1816748725087ee7a23b7713f7853258442de4ec9d0de62199eccce5f81e72`;
the adjacent verified host-collection receipt SHA-256 is
`abd12efdf707ac54bfb66ac72479c9da6a289d0d5d9834a33bccad378c63ab8e`.

Renderer commit `441a7b0a36efb6d1c6baa43d2c4090f1f4957b3d` later published a separate
receipt-last computational-results derivative from those preserved sources
without rerunning a scientific owner. That exact commit passed the assembled
local repository gate before publication. The retained report path is:

```text
runs/full-cohort-public-2587126e7e47-02-vm-computational-report-441a7b0a36ef/
products/report/run-bb36785424aba063e336ebaecdde4e78d984a4470187b8e1421fd281d3afa04f/
run-bb36785424aba063e336ebaecdde4e78d984a4470187b8e1421fd281d3afa04f.run_report.html
```

Its HTML SHA-256 is
`ba426da9a4bdc387172f749a28e7140ec0b7dc0201d0dd74b4f59bb492e0dc30`;
the semantic-receipt SHA-256 is
`105e552768acb755f92a032ba68bdf5f05321861ff4f9a2f9335cb30fd301cce`.
It displays all three computational candidates and identifies the one
threshold-passing candidate as not scientifically adjudicated.

These observations are real-tool, synthetic, one-VM, single-node-Slurm evidence
only. They establish neither CSU Viking execution, multi-node or distributed
behavior, production-scale performance, production-data correctness, completed
scientific review, nor biological validation.

## Rendered report review

[Shared report acceptance](../../docs/tasks/backlog_matrix.md#shared-report-acceptance)
keeps scientific and evidence/operations reports distinct. Retain exact-revision
observations for representative long content, collapsed sections, keyboard use,
zoom/narrow reflow, meaningful screen-reader structure, links into disclosures and
complete print output. Review a copied full Results tree with its relative files,
fragments and checksums; copying rendered HTML alone is a different claim.
HTML structure or style-string tests, receipts and successful rendering calls are
not browser/print proof. Visual acceptance establishes no scientific or biological
validity and does not select a third report or a new reporting framework.

### Nine-candidate presentation review

REPORT-04 pins the literal nine-row selection/order, A–I labels, final context
panel and three-by-three paired figure in the existing tests. Independent native
contract tests refuse rank 10 and retained version-1 receipts without changing
those bytes; the real-R fixture requires nine exact IDs while retaining all 40
candidate-context rows and existing motif/logo/statistic counts.

A disposable model fixture on 2026-10-02 used the actual selector, SVG builders,
full template, CSS and HTML validator with nine long IDs, long annotations and
condition names, three sample pairs and three motif states. Exact source hashes,
inputs and the reproduction recipe are retained in
`/private/tmp/emrys-report04-visual/render-w0e53rjh/render-xd7vy82t/`.
An actual browser at 390×844 and 1280×900 showed all A–I details and no document
horizontal overflow; candidate-I navigation clears the persistent banner. An
actual 43-page Letter PDF of the preceding render in `render-z5sn8zqg` exposed
and verified corrections to paired-panel label spacing and context annotation
wrapping. The final `report04-final-print.pdf` in `render-xd7vy82t` was then
rendered with the final CSS; index and nine-panel pages were visually rechecked.
All PDF bytes match the inspected predecessor after substituting only creation/
modification dates and the exact disposable directory in link targets. The final
PDF SHA-256 is
`52217d361b050191bbfe41cbbc0d8064a173fe216a930493413b37dedf5c5a57`;
`print-review.json` retains that bounded comparison.

These are constructed display models, not a native R transaction, published
report receipt, complete copied Results tree, Run, or scientific/biological proof.
Locked non-skipped native-R execution and the broader shared report acceptance
remain pending. Do not substitute structure tests or
this model fixture for those checks.
