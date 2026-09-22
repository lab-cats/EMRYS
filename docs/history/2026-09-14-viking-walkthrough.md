# Viking walkthrough evidence — 2026-09-14

This additive record preserves the September 14 operator walkthrough and its
limits from the [main-matrix account](../tasks/backlog_matrix.md#viking-walkthrough-findings)
and the [cluster campaign E01–E12 register](../tasks/cluster_verification_campaign.md#evidence-register).
It records what those sources say; it is not a new cluster run, an independent
reproduction, or acceptance of the current checkout. The original records
remain in place while their eventual transfer and retirement are reviewed.

The sources combine operator-supplied terminal output with source review. Raw
cluster logs and artifacts remain with the operator. Git establishes when the
repository recorded a claim, not the raw cluster result or the package identity
of every observed job. The selected revision
`7c427f0ca50de17bbcc9983571fa49acf167f187` and campaign source-review
revision `f2c0149e73a685b6f3d5b162f3804edee7c78c10` have different roles;
neither alone binds every Run, Attempt, profile, input, and managed runtime.

## Source provenance

This record was compiled against source snapshot
`4a337a7e139daa1382001679f620d0699968ed6f`. The following immutable
commits wrote the observations and later interpretations in the source docs.
All dates are repository recording dates in Eastern time, not inferred job
completion dates.

| Source contribution | Commit | Recorded |
| --- | --- | --- |
| Initial matrix walkthrough, manual setup, bounded approval, and first memory observation | `cf9c18ad98ed64ea78534ccd6bdc93e57d03ec2b` | 2026-09-14 14:45 |
| Hosted disposable-Slurm result and limit; Quickstart own-data and reconnect/recovery guidance | `bc277e270f1caa7cf47a0b8fdd1e464d62ba2a53` | 2026-09-14 15:46 |
| Further memory diagnostics and operator-approved fallback | `4d8c7a05976898b9bb40a860b69c1e6ae2c2f416` | 2026-09-14 17:27 |
| Username startup failure and source correction | `9b439d433ebb9a5aa4db21e8484dce2ba4361a2c` | 2026-09-14 18:08 |
| Campaign E01–E12 register, synthetic resume, and actual-data continuation | `1ea21855a4e6db8bc54268e9c6869fa362d424eb` | 2026-09-14 20:03 |
| Later E06 acceptance interpretation, distinct from the original observation | `593f6e728321f535817bcde732d263c2f86079a8` | 2026-09-21 04:19 |

## E01–E12 observations and limits

### E01 — First repair

Native tools and R installation completed, including 71 restored R packages.
Repair then reported that the repaired runtime failed qualification, without
individual failed checks in the supplied output. The cause remains unknown;
later successful probes do not explain that first failure. The adjacent manual
setup identity below must not be presented as the cause or as proof of the
subsequent automated Doctor path.

### E02 — Memory and scheduler

Viking omitted both Slurm memory variables, and the observed cgroup hierarchy
did not yield a finite usable bound. An explicit Slurm memory request was
rejected. A later approved capacity-policy correction let Doctor complete.
Slurm's reported node-memory value of `1` was not a physical-RAM measurement.
These observations do not prove a process memory limit or current Viking memory
safety; the exact jobs and dated policy decision are below.

### E03 — Username startup

Snakemake failed while building its startup header because login-name variables
were absent and compute-node UID lookup failed. Inspection reported a valid
Run, failed Attempt, recovery available, and no completed scientific milestones.
The shared export correction was followed by an operator-reported successful
synthetic resume. Its fixture/source coverage is narrower than the complete
managed or institutional golden-path requirement.

### E04 — Synthetic completion

Operator inspection reported valid Run integrity, a succeeded Attempt, all
scientific milestones, Scientific Results and Reporting complete, 151 inventoried
artifacts, and 3:52 elapsed for the latest Attempt. Visual review of both HTML
reports was deferred. This is reported synthetic execution, not actual-data
completion, report visual acceptance, scientific review, or biological proof.

### E05 — Observing active work

An active Slurm submission initially had no discoverable Run. Later head-node
inspection showed foreign-host lock and incomplete-task blockers during
reference preparation and other active work. Those displays did not establish
execution failure.

### E06 — Reporting visibility

Synthetic inspection temporarily reported missing reporting transaction
directories or receipts. A later inspection completed without operator repair,
while the job log printed report locations. Publication overlap and shared
storage visibility delay remained competing explanations; neither cause was
established. A separate September 21 disposition in the charter states that
CV-21 no longer requires causal reconstruction or reproduction for current
acceptance. That later decision is not part of the September 14 observation.

### E07 — Actual-data onboarding

Reusing the recorded six-library, three-pair, 25-partition study required
inspection of legacy bundles, a long initialization command, and manual
resource-profile editing. Project creation was quiet for several minutes while
admission read substantial inputs. Source review found full input hashing and
reference compatibility checks; their individual elapsed costs were not
measured.

### E08 — Runtime reuse and verification

A new Project ordinarily selected its own managed installation. A manually
verified fresh-Project workaround reused existing runtime inventory and tool
paths, and Doctor passed without package installation. This was a manual route,
not a complete public compatible-donor discovery lifecycle. An already-ready
Project still presented a repair plan and repeated compute/head checks.

### E09 — Cancellation

The operator cancelled an active actual-data job through Slurm during reference
preparation. Accounting confirmed batch SIGTERM; EMRYS retained no terminal
Attempt receipt and offered no recovery. The blocked Run was preserved and a
fresh Project used. Scheduler exit or queue removal alone does not close an
EMRYS transaction.

### E10 — Heterogeneous resources

One node exposed 128,544 MiB total and 111,749 MiB available RAM at one point;
another exposed a 386,627 MiB workflow ceiling. The retained index-building
allowance was 262,144 MiB. A 256-CPU exclusive request waited with 16 CPUs
occupied and 240 idle, while the retained workflow used 12 cores. These are
reported capacity/configuration observations, not measured stage demand or an
optimal placement/resource policy.

### E11 — Doctor latency

A verification-only repair performed initial inspection, approved-input
verification, readiness, compute qualification, runtime/Project verification,
head storage, and final readiness without package installation. Supplied phase
times exceeded ten minutes. The shares attributable to hashing, probes,
storage, and queue waits were not measured; no complete-operation speedup is
established by this record.

### E12 — Actual-data continuation

The replacement Project's Run was active at the latest supplied observation,
after compute qualification and new reference-task starts. No successful
terminal scientific or reporting receipt for that Run had been supplied. This
does not assert that it never completed; task starts or scheduler activity do
not close actual-data acceptance.

### Related node-change interpretation

The charter separately records that the first actual-data allocation passed
its required runtime checks and started work with selected managed tools.
Different system Java versions alone did not make that allocation unsuitable.
Qualification must explain runtime provenance and hardware eligibility rather
than assume that one previously successful hostname is the only valid host.
This interpretation supplies no terminal scientific or reporting result.

## Additional identities and dated decisions

- The initial selected revision was
  `7c427f0ca50de17bbcc9983571fa49acf167f187`. The operator separately
  reported successful fresh installation and synthetic Project validation
  before the later execution observations. Manual setup job `614786`
  reported 71 R packages restored in 600 seconds. The operator later supplied
  successful head-node finalization for qualification identity
  `cfcf7f788fd9d949f1a23f17793ecf22ba1e05f1023bc3b49065eebc0280186f`;
  its receipt was under `.emrys-storage-qualification/` beneath the parent of
  the `emrys-smoke` Project. This was the earlier manually submitted setup,
  not automated Doctor evidence and not an explanation of E01's unknown cause.
- The earlier walkthrough approved up to 750 net additional product lines,
  no new product files or receipt formats, and Rich as the shared terminal
  library, with product/tests/docs/configuration/evidence counted separately.
  This was bounded historical implementation authority, not a current grant.
- Job `605171` supplied the earlier four-CPU/eight-hour scheduler example on
  the `long` partition with `normal` QoS: `ReqMem=1M`, no allocated-memory
  entry, `select/cons_tres`, `CR_CORE`, unlimited default/maximum per-node
  memory, and `task/cgroup`. These facts did not establish a process memory
  limit. The [existing manual Step 08
  entry](validation-evidence.md#csu-viking-manual-steps-0709) also names job
  `605171`, but records a NORAD-stage result, not this E02 Doctor/cgroup claim;
  the shared number alone does not make one record proof of the other.
  The source matrix retains the allocation account identifier, which this
  additive record does not repeat; any later source reduction must decide
  whether that identifier needs preservation for the evidence claim.
- At observer revision `c52178d2ba48c0a39f061e20f016b4f54a471ab3`,
  missing Slurm memory metadata blocked partial-node admission. Automated
  repair job `618134` passed runtime inspection and stopped at that check.
  The source forbade forging scheduler memory variables or enlarging the
  allocation to bypass admission. Its initial direction requested the first
  actual Run diagnostic before selecting a correction; the later approved
  fallback below followed Doctor diagnostics and does not establish that an
  actual Run diagnostic occurred.
  Diagnostic job `618190` on `node009` exposed four CPUs, neither Slurm memory
  variable, and effectively unlimited visible cgroup-v1 memory. The operator
  then approved using process-visible RAM without a separate workflow budget
  or complete-node CPU requirement while preserving observed cgroup/scheduler
  limits and source attribution. Doctor was later reported `READY`; science
  remained pending at that point, and earlier generic failures stayed unknown.
- The selected interface decisions included `--site viking` on both
  Project-creation commands, writing the default Viking profile for Run,
  resume, and standalone reporting; Doctor-managed qualification; and
  `--compute` as an advanced route. The Quickstart covered synthetic and
  own-data journeys, reconnecting, and routine recovery. Normal Doctor
  output named phases and gave a rough 5–15-minute first-setup allowance;
  color supplemented text while redirected output stayed plain. Complete
  package output was retained beside the maintenance log. Repair avoided the
  observed unwritable `/local/tmp`. These are dated decisions/observations;
  current behavior and acceptance belong to their present owners.
- The matrix records the shared correction that forwarded four login-name
  variables after E03, the reported successful synthetic resume, and the
  later blocked/active actual-data distinction. It supplies no exact actual-
  data Run or Attempt identity for terminal acceptance.
- Hosted disposable-Slurm CI [run 34885186045](https://github.com/lab-cats/EMRYS/actions/runs/34885186045)
  was recorded as passing at `e25b10c648df404f884ce03e9ab9757ac31d2781`
  for a Doctor head-preparation journey in place of manual storage commands.
  It does not establish Viking qualification. The six-library Viking profile
  is not a capacity requirement for that tiny fixture.

The [main backlog](../tasks/backlog_matrix.md#cluster-verification-closure-checklist)
and [delegated CV cards](../tasks/cluster_verification_backlog.md) still own
current acceptance and missing evidence. This dated record changes no card
status, proves no later site outcome, and authorizes no source-record deletion.
