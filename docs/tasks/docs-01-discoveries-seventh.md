# DOCS-01 discovery notes, seventh file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F188–F189 and an F182 recheck at local audit head `9aaec3ac`, plus an
F76 recheck and coverage screens at `16a98be5`, read on 2026-09-23. Review
spans and proposed line savings are conditional;
no guide, product source, test, or retained evidence was changed, and no
product, CI, or cluster command ran.

### F188 — Retired storage publisher history in polish item 2

The [polish campaign](polish-campaign.md#2-make-storage-inventory-replacement-recoverable)
lines 251–263 spends 13 physical lines on the retired capacity-and-retention
publisher, its unresolved backup/restoration/cleanup hazards, and PR
chronology. The current [storage owner](../../src/emrys/evidence/storage_inventory/README.md)
places capacity planning and retention policy outside EMRYS; its source tree
retains qualification, not that publisher. The campaign's overlap table at
line 1008 already records PR #128/#134, while Git retains routine PR order.
A shorter retirement disposition might save four to six lines, conditional on
retaining the partial-predecessor, lock-release and obscured-original-error
risks; the fact that PR #115/#128/#134 did not repair them; the PR #158/CS-27
retirement merged through PR #169; and surviving storage qualification,
reports and recovery files. Retirement closes the repair proposal without
proving repair. No lossless draft or net saving was verified. F88 concerns
another polish item; F90 concerns other completed tooling sections.

### F189 — CV campaign Related work repeats current owner map

The [CV campaign](cluster_verification_campaign.md#related-work) lines
192–210 spends 19 physical lines on five related-owner routes. The
[main matrix](backlog_matrix.md#platform-operation-and-portability) lines
170–172 and 180 retains SITE-PARITY, SCHED/CV-11 and installed-watch
dispositions, including September 17 acceptance and the evidence-deletion
limit. The [delegated CV backlog](cluster_verification_backlog.md#verified-scope-and-remaining-evidence)
lines 72–79 retains CV-26's Open status, original complete-operation
attribution, E11 timing and no-speedup limit. The optimization and polish
campaigns own their separate work. A concise linked owner map might save six
to nine lines if it keeps all five boundaries, the site-verification limit,
and the campaign's scope relative to those owners. This is separate from
F158's Delivery opening/closure criteria, F187's later Delivery span, F165
priority history and F167 remaining scope.
No non-audit Markdown link targets this heading, but outside bookmarks were not
checked. No lossless draft or net saving was verified.

## Focused rescreens at `9aaec3ac`

The full 734-line Runbook and 271-line Troubleshooting guide were reread with
root/Quickstart routes and selected operator owners. Their apparent command,
recovery and prose overlaps are already recorded in F02/F05–F09/F23/F31/
F52/F53/F70/F72/F83/F89/F92/F104/F119/F123/F126/F132/F144/F154/F155/
F170/F182; report transfer and trusted-workspace warnings serve distinct
operator needs. Reporting, reference, runtime, logging, Step 09/10, BAM QC
and RSeQC owners were compared with selected source and direct-test text;
apparent mismatches were existing findings or owner-specific boundaries.
These were static reads, not executed commands, hosted or site evidence.

All 1,248 lines of the coordinator contract, including its 632-line no-write
and publication section, were reread against selected owners, source and
tests. Existing findings cover the apparent overlap and private detail;
F182 now also names its scratch-cleanup claim at lines 383–387. No separate
safe reduction was established by this recheck.

## Cross-repository duplicate and claim screen at `16a98be5`

Across 170 non-audit Markdown files, a paragraph screen found 2,739 text
blocks; 1,341 non-table blocks of 30–250 words entered a word-weighted,
cross-file similarity comparison. I inspected pairs scoring about 0.28 or
higher, plus repeated non-table lines of at least 70 characters. The strongest
overlaps involved config and Runbook batch setup, coordinator and
Troubleshooting recovery, coordinator and decision reporting, resource policy
and its dated history, and submission and logging identity. Existing findings
or distinct reader roles account for them. This screen cannot rule out every
paraphrase or establish a safe line saving.

A simple scan of inline and reference-style Markdown path links, excluding
temporary audit notes as sources, found 41 non-audit files without an inbound
link. All are directory `README.md` files, not demonstrated orphans. The
[task index](README.md) is explicitly required by the documentation checker.
The license and scientific-context resource indexes retain distinct local
obligations. The scan does not account for directory browsing or external
bookmarks and establishes no deletion or line saving.

All 53 test, script and CI Markdown guides (692 physical lines) were reread
against selected assertions, driver behavior and workflow wiring. Selected
strong guarantees about Init FASTQ reads, STAR members, Step 06/07 validation,
reporting, and Slurm scratch were traced to source. Apparent gaps were already
F182/F185 or expressly limited by source; no new high-confidence finding
emerged. These were static comparisons, not executed checks or hosted evidence.

## F76 historical-sentence recheck at `16a98be5`

The [Step 07 test guide](../../tests/stages/partitioned_cohort_mpileup/README.md)
lines 10–11 also narrates retired shell-suite fixed primary/pilot counts,
introduced at `76acb9c5f`. The current [producer test](../../tests/stages/partitioned_cohort_mpileup/test_partitioned_cohort_mpileup_producer.py)
lines 239–293 checks fixture arguments and the final-path receipt; the
[stage contract](../../src/emrys/stages/partitioned_cohort_mpileup/CONTRACT.md)
does not make those old counts a production requirement. The guide's line 12
fixture-VCF scientific ceiling remains useful. Whether the retired-count
sentence has any distinct current reader value or physical-line saving is
unverified; Git retains its provenance. This remains part of F76's guide
review, not a separate behavior or scientific finding.
