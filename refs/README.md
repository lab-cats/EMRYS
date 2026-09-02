# Reference workspace

`refs/` holds prepared reference material and generated indexes used by
pipeline stages. Most root children are ignored because reference artifacts
are large, environment-specific, or derived; only this README is tracked.

Step `00a` owns reference-index construction, while downstream owners consume
explicit files beneath this root. Supported preparation commands are routed by
the [stage-owner index](../src/emrys/stages/README.md). Record real reference
identity, hashes, source, and release using the
[reference-provenance starter](../configs/reference_provenance.example.tsv)
before runtime promotion. A path or filename is not provenance.

## Retention and cleanup

Do not commit production references or assume ignored artifacts are safe to
delete. Before cleanup, confirm the active consumers, provenance record,
reproducibility of derived indexes, and approved storage policy. EMRYS does not
automatically repair, replace, or remove reference material.
