# `collect_RSeQC_paired_orientation_evidence` owner

Operation `03` runs RSeQC `infer_experiment.py` on one BAM and BED12 annotation.
It records fractions assigned to two paired-read orientation groups or left
undetermined. These are mechanical observations, not transcript-strand or
sense/antisense conclusions; they never update manifest `strandedness`.

Inputs are the sample ID, BAM with adjacent BAI, BED12, output directory, and
RSeQC executable. The output is `<sample>.infer_experiment.txt`.

The Run includes this operation. The shell script is an internal worker;
its help describes that interface. The validator remains directly available:

```bash
bash src/emrys/evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh --help
emrys validate rseqc-orientation --help
```

The [contract](CONTRACT.md) owns exact labels, fraction tolerance, publication,
recovery, and historical behavior. Passing validation does not select a
biological interpretation or make this evidence a computational gate.

## Retained cohort and orientation observations

The former NORAD handoff at
[`ec4d9d93`](https://github.com/lab-cats/EMRYS/blob/ec4d9d93a7a36de85704227c046990d889e7725d/docs/HANDOFF.md)
retains these operator-supplied fractions. The earlier observation at
[`2d5c426b`](https://github.com/lab-cats/EMRYS/blob/2d5c426b4c1e3d30cf4533913bfe9b536c21e365/docs/HANDOFF.md)
explicitly lacks the Step 03 job ID. No exact execution date or installed-code
identity is established by these document revisions; the classifications below
are historical interpretation, not an automatic current policy.

The operational cohort contained three explicit paired strata:

| Replicate | EV | PUM1 |
|---|---|---|
| `2` | `ABE_EV_2` | `ABE_PUM1_2` |
| `3` | `ABE_EV_3` | `ABE_PUM1_3` |
| `4` | `ABE_EV4` | `ABE_PUM1_4` |

`ABE_EV4` intentionally lacks an underscore. Pairing came from manifest
metadata, never the sample names. Step 03 recorded:

| Sample | Failed | `1++,1--,2+-,2-+` | `1+-,1-+,2++,2--` |
|---|---:|---:|---:|
| `ABE_EV_2` | 0.0828 | 0.0432 | 0.8740 |
| `ABE_EV_3` | 0.0964 | 0.0420 | 0.8617 |
| `ABE_EV4` | 0.0908 | 0.0433 | 0.8658 |
| `ABE_PUM1_2` | 0.1063 | 0.0374 | 0.8562 |
| `ABE_PUM1_3` | 0.0955 | 0.0407 | 0.8639 |
| `ABE_PUM1_4` | 0.0926 | 0.0402 | 0.8672 |

All were classified reverse-stranded/first-strand-style. The hardened
`ABE_EV_2` rerun matched its earlier report; its mapping difference remains an
outlier, not an established pipeline defect. `FWD_like` and `REV_like` are
mechanical groupings, and `legacy_provisional_v1` is not a validated biological
strand model.
