# Ingestion owners

Ingestion admits explicitly declared external inputs before computation. The
current [`sample_manifest_admission/`](sample_manifest_admission/README.md)
owner validates sample manifests and offers a bounded paired-FASTQ diagnostic.

This package does not discover, acquire, copy, normalize, hash, or freeze data;
manage Run state; or execute workflow stages. Project onboarding and the
immutable Run lifecycle own those wider responsibilities.
