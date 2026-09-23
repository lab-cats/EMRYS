# DOCS-01 discovery notes, fourth file

This temporary companion to the [findings matrix](docs-01-audit.md#findings-matrix)
holds F100–F104. Sources were read at local audit head `e1771d21` on
2026-09-22. These are documentation observations, not runtime results,
accepted changes, or permission to alter retained evidence.

## Discovery notes

### F100 — GTF worker detail in the coordinator contract

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1099–1104 defines runner ownership of paths, locks, streams,
publication, and recovery, then adds that the GTF-to-BED12 worker shares
normalization with Project and BED12 validation. The
[GTF owner contract](../../src/emrys/stages/gtf_to_bed12/CONTRACT.md)
lines 45–52 already states that exact worker fact and links back to runner
ownership. Current callers use `normalize_gtf` in the
[worker](../../src/emrys/stages/gtf_to_bed12/converter.py) lines 259–263 and
285–289, [validator](../../src/emrys/stages/gtf_to_bed12/validator.py) line 52,
and [Project admission](../../src/emrys/orchestration/run_coordinator/onboarding.py)
line 1719. This is a one-sentence owner-detail overlap inside a cross-owner
execution section. Runner publication and recovery rules remain distinct; no
safe saving is established by this comparison alone.

### F101 — Retired reporting-memory recovery advice in the contract

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 845–847 records rejection of the retired `resources.reporting_memory_mb`
field and `--reporting-memory-mb` flag, then gives the operator action of
removing the field from a selected profile. The
[profile guide](../../configs/README.md) lines 233–264 owns profile authoring
and current options but does not mention that retired field; a tracked guide
search found no other operator route to the advice. The source tests at
`tests/orchestration/run_coordinator/test_execution_profile.py:698–703` and
`test_resource_policy.py:529–532` cover the rejections. Exact rejection
behavior belongs to the coordinator owner. The removal advice has a different
operator audience and currently resides only in that contract. The historical
claim that the old control never constrained reporting was not independently
replayed in this pass.

### F102 — Historical E09 example in current lifecycle rules

The [coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1029–1036 states current prepared-finalization eligibility, then names
the historical E09 Run and says its cause cannot be established or its state
recovered under this path. The [CV evidence register](cluster_verification_campaign.md)
line 114 retains the operator's cancellation observation; the
[CV-10 card](cluster_verification_backlog.md) lines 2732–2744 and 2810–2814
retains its accepted recovery boundary. The named example adds historical
context to the current contract, while its generic missing-evidence rule is
already stated there. Neither the E09 cause nor recovery of that old Run was
verified by this document comparison.

### F103 — Unpublished FASTQ experiment in the owner guide

The [sample-manifest owner guide](../../src/emrys/ingestion/sample_manifest_admission/README.md)
lines 20–32 mixes current helper limits with what it calls an unpublished
single-pass `awk` draft, its NUL-header counterexample, and a source-derived 21-pass
count. The [optimization campaign](optimization_campaign.md) lines 340–345
already records the deferred helper optimization and points to the owner for
the byte and diagnostic boundary. The
[current helper](../../src/emrys/ingestion/sample_manifest_admission/check_fastq_pairs.sh)
lines 73 and 114–151 defaults to 20 IDs, counts records, and rescans each
requested leading ID; this
supports the logical-pass count, not measured physical I/O or pipeline speed.
The current direct test module has prefix, count, mismatch, and compression
cases but no NUL-header case. The owner passage is the only current-tree
description found for the exact NUL-header pair and `awk` truncation; its
documentation commit `550b54025` does not establish the draft's execution
date or retained output. The exact counterexample and truncation detail are
unique to this current guide; the broader accepted-input boundary also appears
in the optimization campaign. This review establishes no deletable span or saving.

### F104 — Automatic reports after successful computation

The [Runbook](../operations/RUNBOOK.md) lines 274–278 says successful
computation generates both reports automatically. For a full Run, the
[coordinator contract](../../src/emrys/orchestration/run_coordinator/CONTRACT.md)
lines 1200–1208 promises a default reporting invocation unless `--no-report`
was selected; a reporting failure does not invalidate completed science.
The [control path](../../src/emrys/orchestration/run_coordinator/control.py)
lines 1514–1536 handles reporting failure after scientific Results complete.
The Runbook's own [recovery route](../operations/RUNBOOK.md#inspect-and-open-reports)
at lines 437–447 handles skipped, partial, and blocked reporting, while
[Quickstart](../../quickstart.md) lines 188–205 requires separate Reporting
admission after scientific completion. “Generates both reports” can read as a
completion guarantee stronger than these independent checks. This is an
operator-wording question, not evidence of a reporting behavior defect.

## Reviewed overlaps without a saving claim

[Troubleshooting](../operations/TROUBLESHOOTING.md) lines 52–56 repeats the
coordinator's exact byte/device/inode and same-UID limitation at contract
1021–1027. Its trusted-workspace warning is relevant to the recovery reader;
the comparison established no safe reduction. Troubleshooting lines 222–230
also names the old unwritable `/local/tmp` incident. [SCRATCH-01](backlog_matrix.md)
line 87 retains that observation and distinguishes it from Viking `/tmp`,
whose suitability remains unverified. The distinction is an active operator
safety boundary, not routine chronology to discard.
