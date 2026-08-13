# ORCH-04A — Close local-pilot adversarial safety gaps

## Outcome

The fixed local-pilot control plane rejects unsafe entry and runtime drift,
binds its durable evidence completely, serializes attempts without contaminating
valid runs, and terminalizes only after interruption handling and child-process
quiescence are proved.

## Touches

Writes are limited to the local-pilot orchestration owners and schemas under
`src/norad/orchestration/local_pilot/` and
`src/norad/contracts/schemas/orchestration/v1/`; the neutral source/runtime
admission owners they directly use; the selected Step 00b, Step 00c, Step 01,
and shared shell-library owners needed for explicit run-token, decompression,
and hashing authority; the fixed profile/runtime starters; direct tests and
fixtures for those owners; package metadata; and adjacent current design,
operations, owner, task-registry, and evidence documentation. The user-owned
untracked `docs/quickstart.md`, frozen prior evidence records, remote branches,
cluster systems, and unrelated owners are outside scope.

## Stop

Stop before mutation if a durable external consumer of the pre-release v1
orchestration records is found, if the selected filesystem cannot provide the
required advisory serialization or create-absent lock transfer, if a fix would
change scientific selection or output semantics, if a dependency install or
network operation becomes necessary, if unrelated dirty work appears, or if
foreign evidence would need to be deleted or overwritten. Stop before release
if process-group quiescence cannot be proved, any receipt precedes durable lock
disposition, coverage policy would need to be weakened, or the fresh-clone
control-plane proof no longer matches the documented public journey.

## Context

The Campaign B adversarial review found a mismatch between valid Step 00c
sidecar reuse and generic task entry, incomplete runtime/tool/R identity,
unpropagated owner tokens, unbound task logs, overly permissive absent-workspace
readiness, stale-contender lock residue, a replacing released-lock move, and
signal/process-group gaps around the lifecycle transaction. The branch is
unmerged and package metadata remains pre-release, so the v1 records may be
tightened together unless an external durable consumer is discovered.

## Deliverables

- Make owner entry match the declared Step 00c reuse and Step 01 compression
  contracts while retaining fail-closed create-absent behavior elsewhere.
- Bind executable, JAR, decompression, hashing, R-library, and owner-token
  authority through doctor, materialization, execution, and resume.
- Replace task log path-only evidence with content-bound record references.
- Admit one absent workspace leaf only when its immediate real parent is safe.
- Serialize attempt admission before irreversible evidence, transfer released
  locks without replacement, and leave stale contenders residue-free.
- Cover the complete owned-lock transaction with phase-aware interruption and
  prove the child process group is quiescent before terminal publication.
- Reconcile public commands, external Step 00c mutation guidance, dynamic job
  counts, pre-release metadata, current status, and the exact evidence ceiling.

## Acceptance evidence

Each behavior commit passes its direct owner, schema, shell, and fault tests,
format/lint checks, documentation checks where applicable, and `git diff
--check`. The assembled package then passes the stable orchestration/lifecycle
and public-CLI suites, one unchanged-policy coverage measurement, one
`make -s all-checks`, and the opt-in clean fresh-clone deterministic no-science
journey. Evidence is reported exactly and is not promoted to real science-tool,
SLURM, cluster, production, scientific-review, or biological proof.

## Documentation updates

Update current owner contracts and READMEs with their behavior commits. After
the assembled proof, reconcile the root onboarding, runbook,
troubleshooting, workflow/local-pilot documentation, HANDOFF, PIPELINE_PLAN,
readiness, package metadata assertions, and this task registry. Remove this JIT
card and its backlog entry when the package completes. Do not edit the frozen B6
fresh-clone record; add a separate dated remediation record only from observed
final evidence if durable gate provenance is needed.
