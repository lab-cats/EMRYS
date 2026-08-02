# FUT-ANALYSIS-ECO-01 — Evaluate ecosystems for each concrete analysis

State: [`UNREFINED` proposal](README.md). No implementation language, tool, or
scientific change is selected by preserving it.

## Proposal

For each named future analysis, compare R, Python, maintained command-line
tools, or an explicit hybrid against the same language-neutral module contract.

## Why preserve it

A neutral interface does not make scientific methods, libraries,
reproducibility, performance, runtime availability, or maintenance equivalent.
One global R-versus-Python decision would hide analysis-specific constraints.

## Settled boundaries

- Make one feasibility decision per concrete analysis and typed input/output
  contract; never assume ecosystem parity.
- Transpilation is not an interoperability, migration, or validation strategy.
- Compare scientific fidelity, validated implementations, dependency and
  version stability, determinism, testability, performance, memory and I/O,
  HPC availability, provenance, licensing, support, operator usability, and
  report integration.
- Valid outcomes include R, Python, a maintained external tool, a bounded
  hybrid, or an explicit infeasibility or deferral decision.
- No comparison changes current CMH science, evidence language, or runtime
  behavior without a separately approved package.

## Questions before refinement

- What exact analysis, method, typed contract, representative inputs, scale,
  and acceptance reference are being evaluated?
- Which ecosystem has a maintained scientifically appropriate implementation
  and independently reviewable validation path?
- What dependency, cluster, portability, performance, provenance, licensing,
  and long-term maintenance costs apply?
- Would wrapping an established tool be safer than reimplementation?
- What evidence would justify selection, hybridization, deferral, or rejection?

## Promotion conditions

- Name one concrete analysis and supply its scientific method, typed contract,
  safe representative inputs, scale, runtime environment, and acceptance
  reference.
- Define independent scientific and engineering comparison criteria with the
  appropriate reviewer.
- Promote only that bounded comparison as a complete TODO card, not a generic
  all-analysis language contest.
