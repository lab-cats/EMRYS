# External scientific-evaluation checklist

This optional checklist is a non-normative research aid outside NORAD. It does
not define a pipeline step, schema, approver role, gate, status, or completion
condition. NORAD's output remains CMH-ranked computational candidates and
provenance whether or not a research team performs or records these activities.

If a team evaluates candidates, keep its records in the team's scientific work
process and reference immutable NORAD run, artifact, path, and hash identities
rather than editing native outputs or report receipts.

- **Orientation and locus sanity:** compare the mechanical `FWD_like` and
  `REV_like` evidence with assay design, library metadata, local sequence
  context, mapping quality, and known difficult regions without treating the
  mechanical labels as biological strand.
- **Annotation sanity:** inspect gene/transcript overlaps, transcript strand,
  reference/annotation release agreement, repeated or paralogous sequence, and
  whether the locus context supports the proposed interpretation.
- **Parameter sensitivity:** evaluate whether reasonable changes to depth,
  background, FDR, odds-ratio, and allele-fraction thresholds materially alter
  the candidate set or ranking; preserve each alternative as a distinct
  analysis record.
- **Leave-one-pair-out and replicate consistency:** inspect per-pair depth and
  effect direction, rerun or independently calculate leave-one-pair-out
  comparisons when scientifically useful, and identify candidates dominated by
  one replicate pair.
- **Candidate adjudication:** record the evidence considered, unresolved
  alternatives, and the researcher's candidate-level conclusion outside the
  NORAD run. A threshold-passing row alone is not a validated editing site.
- **Limitations:** record data quality, sample size, assay, reference,
  annotation, mapping, model, threshold, background, and generalizability
  limitations, including analyses that were not performed.

These notes may support a publication or later experiment, but they neither
change NORAD's computational result nor establish a biological conclusion by
themselves.
