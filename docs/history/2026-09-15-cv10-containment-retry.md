# CV-10 containment and retry evidence — 2026-09-15

This additive record transfers the September 15 source-bound cancellation and
closed-abort retry evidence from [CV-10](../tasks/cluster_verification_backlog.md#cv-10-external-cancellation-and-recovery).
It was compiled against audit baseline
`3a672fdf8e55b30efc63dea9aecc4a29d28a5f4d`. The source account was
recorded in immutable commits
`7143df5c7662ee33e3b7b5db02c58691b4db92a3`,
`a947b8fca04eb052c3829e897f255b046b002087`, and
`8e16def88e7d0e2be6b418b88bf4e54c591977f3` on September 15. The source
card remains in place. These are retained software observations, not a new
test, Viking result, or reconstruction of the [original E09
failure](2026-09-14-viking-walkthrough.md#e09-cancellation).

## Boundary and exact results

The positive `linux-task-prepublication.v1` closure applies only to a fresh
Linux Task worker that proves all native descendants reaped, unchanged input
identities and bytes, unchanged Task-directory membership, untouched
publication destinations, owned cleanup and directory synchronization. Worker
loss, uncertain child state, reused sidecars
or postpublication failure do not earn closure. `task-start.v3`, failed
`task-attempt.v4`, cumulative `attempt-receipt.v3`, and the new Attempt's frozen
latest-abort reference keep the retry tied to the original Task and Run.
Historical abort admission can remain valid after a successful retry publishes
outputs; current retry readiness separately rechecks unchanged inputs, empty
destinations and absent owned residue.

| Source-bound result | Exact identity and retained limit |
| --- | --- |
| Native descendant containment | [CI 34993805649](https://github.com/lab-cats/EMRYS/actions/runs/34993805649) passed 32 selected cases, including 17 Linux/native cases, with 14 standard jobs passing and four configured skips. The native job tested merge `f28a829ca894674f4e17d9e6f4bf618b7296ea1e`, containing product head `21992c732b44392cfe63528633a0e147b7979f85` and base `94a13fbea639d769fb22b1e443ccdb78b536fdd7`. [Artifact 10407865575](https://github.com/lab-cats/EMRYS/actions/runs/34993805649/artifacts/10407865575) has SHA-256 `8e53347a597b2f6b081e9c965ab5259d6621674d2e1af3009a44ae0d1151bb3a`. |
| Public cancellation and retry checkpoint | Product `79d45fb8a974d34572aca5da1ec22a4e4cdbac74` passed its real-Snakemake cancellation, read-only preview and distinct successful resume journey in 238.76 seconds at [CI job 104486782385](https://github.com/lab-cats/EMRYS/actions/runs/35000308100/job/104486782385). The managed golden job passed 47 selected containment cases with zero skips, including ten abort-proof modes and four real samtools cases. Tested merge `3aa865b1c42d710f40b2a698045db2eed9438bcf` contained that head and base `13cd68750e4223431a594478804795905bfe9154`. [Artifact 10410455801](https://github.com/lab-cats/EMRYS/actions/runs/35000308100/artifacts/10410455801) has SHA-256 `a8b0e166cd0d1b5f1a898cd8abb32eb91b2b418582ea2342ed7926ba1fd0f258`. |
| Corrected complete-suite result | The first complete suite failed four older fixture assumptions about Task labels, retained origins and immutable resource policy. After corrections that kept the refusal predicates, final product head `a947b8fca04eb052c3829e897f255b046b002087` passed all 14 standard jobs, with four configured skips, in [CI 35002451860](https://github.com/lab-cats/EMRYS/actions/runs/35002451860). Its stronger public cancellation/resume journey passed in 282.22 seconds; all 47 native cases passed without skips. [Artifact 10411245477](https://github.com/lab-cats/EMRYS/actions/runs/35002451860/artifacts/10411245477) has SHA-256 `7f691245b22bf4b24cd479745b041adfdcc9d11b662f0455ff1ceebde6d16985`. |

The real `sort` cancellation fixture deliberately stopped an observed native
process before escalation. Both real cancellation output rosters were empty;
synthetic descendant cases retained partial bytes. This proves bounded
stopped-native containment in those fixtures, not ordinary unpaused Viking
cancellation. Only the fully closed abort mode gained positive closure; nine
refused modes retained null closure. Preexisting services, remote delegation,
lost workers, and ambiguous historical Tasks are outside that positive claim.

The later September 16 timeout warning and September 21 prepared-finalization
`resume` extension have separate evidence and acceptance. These September 15
results did not recover the original E09 Run, establish its cause, or prove an
institutional cancellation/recovery journey. The original E09 and any later
unclosed Run remain untouched.
