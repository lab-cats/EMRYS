# FUT-SITE-02 — Portable site and container profiles

State: [`UNREFINED` proposal](README.md). It selects no container, site,
deployment mechanism, or portability claim.

## Proposal

Explore runtime profiles for sites other than CSU, including containerized or
environment-module deployments, while preserving explicit input, output,
provenance, runtime, and evidence contracts.

## Why preserve it

Portability mechanism, image policy, registry access, host-filesystem
integration, licensing, security review, accelerator requirements, and
site-specific batch behavior remain unresolved. Treating containers or site
profiles as a generic solution now would hide those operational choices.

## Potential scope

- A site-profile interface layered over the local-pilot contract.
- Container or module identity, digest or version, and provenance records.
- Explicit mounted input, output, and temporary-storage rules.
- Site-specific scheduler, network, credential, and publication boundaries.
- Reproducibility and portability comparison across supported sites.

## Settled boundaries

- A container does not prove that data, references, scheduler behavior,
  scientific results, or interpretation are portable.
- Credentials, private images, large data, and machine-specific runtime
  libraries do not belong in the repository.
- Local fixtures and dry-runs establish contract behavior only.
- This proposal authorizes no image build, registry access, dependency
  restoration, credential handling, or nonlocal execution.

## Questions before refinement

- What concrete second-site use case and runtime owner justify a profile?
- Are containers, modules, or another mechanism acceptable under that site's
  security, licensing, network, storage, and scheduler policies?
- How are image or module identity, mounted paths, temporary storage,
  credentials, provenance, and publication authority represented?
- What local, site-runtime, and cross-site evidence would support or reject a
  portability claim?

## Related work

- [`FUT-ANALYSIS-01`](../TODO/FUT-ANALYSIS-01-preprocessing-profiles-and-analysis-modules.md)
  owns typed workflow-profile and analysis-module boundaries.
- [`FUT-CLI-03`](../TODO/FUT-CLI-03-installable-norad-control-plane.md)
  owns later asset materialization and installation boundaries.
- [`FUT-DATA-02`](../TODO/FUT-DATA-02-public-reference-and-sra-acquisition.md)
  owns explicit public-input provenance.

These are refinement inputs, not dependency relationships.

## Promotion conditions

Promote only after at least one concrete second-site use case, runtime owner,
image or module policy, storage contract, security boundary, and acceptance-
evidence model are identified for a complete reviewed TODO card.
