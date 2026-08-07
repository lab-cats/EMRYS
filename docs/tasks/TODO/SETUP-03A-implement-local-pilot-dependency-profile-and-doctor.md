# SETUP-03A — Implement local-pilot dependency profile and doctor

## Objective

Implement an explicit local-pilot dependency profile and read-only diagnostic
that lets a researcher verify the supported environment before running NORAD.

## Why this exists

The intended researcher path starts with a clone, explicit setup, authorized
data, and a workflow run. Setup burden is currently distributed across command
instructions, optional tools, local R state, report tooling, and machine
assumptions. One bounded profile and doctor can expose that burden without
hiding dependency restoration inside computation.

## Fixed decisions

- Dependency restoration remains an explicit operator action. Compute scripts,
  validators, report renderers, SLURM jobs, and tests never install tools or
  system packages implicitly.
- The profile declares supported platforms, interpreters, runtimes, tools,
  packages, versions, paths, and required, optional, or cluster-only roles; it
  does not infer them from scientific inputs.
- The doctor reports resolved context, missing requirements, version mismatch,
  and exact next actions without changing or repairing the environment.
- This card exclusively owns local-environment readiness semantics and the
  deterministic readiness result. It does not own request/run identity,
  workflow graph or plan generation, lifecycle state, or command routing;
  later consumers invoke the accepted readiness interface.
- Existing runtime preflight remains the owner of its narrower availability
  contract. This card must explicitly decide whether the doctor wraps,
  consumes, or extends that result without silently redefining it.
- Any overall readiness-failing exit behavior is a new public contract and
  requires explicit design and tests; successful report publication alone
  cannot be assumed to mean every required row passed.
- Local-pilot readiness, CSU batch availability, cluster proof, scientific
  review, and biological interpretation remain separate states.

## Blocked by

- None.

## Completion unblocks

- [CLI-03A](CLI-03A-implement-local-pilot-control-plane.md) — Partially: the control plane needs an explicit setup contract and deterministic readiness result before coordinating a researcher run.

## Prerequisites

- Bound the supported local pilot to the current workflow and existing explicit
  setup procedures at the selected revision.
- Inventory required local tools, optional report runtimes, current dependency
  manifests, environment profiles, and fixture setup without changing the
  dependency-restoration policy.
- Decide and document the supported-local-platform boundary and readiness exit
  semantics during task-specific planning.

## Required context

- [`ARCH-02C`](../COMPLETED/ARCH-02C-define-vertical-source-contract-and-test-topology.md)
  for ownership and contract context, not a sequence-only blocker.
- [`FUT-CLI-03`](FUT-CLI-03-installable-norad-control-plane.md) for the later
  installable control-plane boundary and
  [`CONTEXT-09`](CONTEXT-09-define-local-maintainer-context.md) for local
  maintainer context.
- [`RUNBOOK.md`](../../operations/RUNBOOK.md) setup, runtime-preflight,
  guarded-R, report-runtime, and recovery sections.
- The existing runtime-preflight implementation, profile, consumers, tests,
  dependency manifests, report tooling, and local fixture setup surfaces.

## Questions owned by this card

- None. The supported-platform, runtime-preflight composition, and exit
  semantics remain explicit task-plan decision points and must be routed to a
  canonical question owner if they cannot be settled within this card.

## In scope

- A versioned or byte-stable local-pilot dependency profile.
- A doctor or equivalent read-only interface with explicit exit behavior and
  useful resolved output.
- Checks for required interpreters, tools, packages, report runtimes, and paths.
- Clear required, optional, and cluster-only classifications.
- A clean-checkout setup smoke path using small safe fixtures.
- Actionable failures for missing tools, incompatible versions, invalid paths,
  malformed profiles, and incomplete explicit restoration.

## Out of scope

- Implicit installation, package managers hidden behind workflow commands, or
  system-level repair.
- A universal multi-assay environment registry.
- CSU module discovery, batch-visible runtime proof, job submission, production
  data, cluster execution, or scientific interpretation.

## Deliverables

- The local-pilot dependency profile and validation interface.
- A doctor command or equivalent read-only diagnostic entry point.
- Focused fixtures and tests for passing, missing, mismatched, malformed, and
  ambiguous environment requirements.
- The directly required setup, interface, and recovery documentation patch.

## Acceptance evidence

- A clean checkout can follow the explicit setup procedure and receive one
  deterministic, inspectable readiness result.
- Missing or incompatible requirements fail according to the reviewed contract
  before expensive analysis and name the exact operator action.
- Doctor execution neither installs software nor modifies or discovers
  scientific inputs.
- Output records enough resolved context to distinguish local readiness from
  cluster and scientific evidence.
- A second supported local environment reproduces the procedure, or the exact
  portability boundary is recorded.

## Canonical documentation updates

- `RUNBOOK.md` for exact setup, doctor, and recovery commands; `README.md` for
  the concise researcher route; architecture or decision owners only if the
  accepted interface changes them; and the task/roadmap owners required by
  normal integration.

## Escalation conditions

- Stop if the doctor must install dependencies, infer user data, silently pick
  machine-specific paths, or conflate local readiness with CSU, cluster,
  scientific, or biological evidence.
- Broaden review if the profile changes a public CLI, dependency, schema,
  runtime-preflight, or report-runtime contract.

## Completion record

Not started. This recovered TODO card authorizes no setup, installation,
environment change, or evidence claim.
