# Scientific-context policy resources

This directory holds the versioned scientific models consumed only by the
`scientific_context_projection` owner. `pum_motifs_v1.tsv` is the fixed v1
catalog: one registered PUM hypothesis, RNA consensus `UGUANA`, represented in
the extracted DNA alphabet as `TGTANA`.

The producer uses this file for exact presented-strand matching; it is not a
de novo motif library, PWM, binding claim, or general motif database. Changing
the model, adding motifs, or changing matching semantics requires explicit
scientific-policy approval and a new versioned resource/contract.
