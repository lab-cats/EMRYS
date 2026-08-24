# Artifact-adapter v1 fixture builder

`build_fixture.py` rewrites the tracked artifact inventory into a caller-owned
temporary tree and creates the smallest source accepted by each registered
adapter. The resulting paths and pipeline-like files remain untracked.

This builder is production-contract-aware test support, not an independent
oracle or public command. Its consumer is the
[artifact-adapter suite](../../test_artifact_adapters.py), and public adapter
behavior remains owned by the
[reporting README](../../../../src/norad/reporting/README.md).
