# Scientific-context projection owner

Analysis `10` adds sequence and motif context to Step `09` candidates. It reads
the all-sites, significant-sites, and summary tables, FASTA/FAI, and the fixed
PUM motif catalog. Its five outputs contain candidate windows, motif hits,
logo counts, motif statistics, and a receipt for later report rendering.

Normal execution uses `emrys run` or `resume` in the
[Runbook](../../../../../docs/operations/RUNBOOK.md#project-and-run-operations).
The [shell producer](scientific_context_projection.sh) coordinates
[the R computation](scientific_context_projection.R). For standalone help
from the checkout root:

```bash
bash src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/scientific_context_projection.sh --help
emrys validate scientific-context-projection --help
```

The [contract](CONTRACT.md) defines orientation, populations, motif matching,
enrichment, and transaction recovery. This operation neither renders figures
nor infers transcript strand, binding, or validated editing sites. The output
is context for computational candidates, not biological proof.
