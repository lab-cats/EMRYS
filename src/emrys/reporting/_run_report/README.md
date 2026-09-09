# Run-report core owners

This private package implements the fixed HTML-report transaction used by the
Run-level reporting coordinator through [`context.prepare_context`](context.py)
and [`publication.publish_report`](publication.py). It has no
installed public command, generic report DSL, or operator recovery route.

| Module | Core responsibility |
| --- | --- |
| [`models.py`](models.py) | Immutable report-contract, provider, output, and two-view context values. |
| [`inputs.py`](inputs.py) | Explicit run-summary and installed-provider admission with stable snapshots. |
| [`context.py`](context.py) | Source/artifact roots, provider selection, outputs, predecessor state, portable result links, and cleaned renderer initialization. |
| [`view.py`](view.py) | Fixed evidence-and-operations projection and composition with the provider-owned scientific view. |
| [`validation.py`](validation.py) | Autoescaped strict Jinja environment plus CSS, security, semantic HTML, and accessibility validation. |
| [`receipt.py`](receipt.py) | Deterministic summary TSV and v4/v5 report-receipt projection/validation. |
| [`publication.py`](publication.py) | One receipt-last two-HTML transaction. |
| [`transaction.py`](transaction.py) | Lock, snapshot, durability, staging, rollback, and recovery primitives. |

The selected `emrys.analysis_reporters` provider owns bespoke scientific HTML
and its interpretation boundary. The built-in paired-CMH implementation lives
in
[`paired_cmh_candidate_ranking_report/`](../paired_cmh_candidate_ranking_report/)
and retains its computational/context admission, candidate display, figures,
and scientific projection. Those details are deliberately not duplicated in
this core package.

The core owns the Evidence and operations view, role navigation, HTML safety,
fixed output names, default/disabled/independent reporting semantics, stable
input rechecks, and receipt-last publication. Reporter/provider package
identity is bound to report-receipt v5 for explicit modules but never enters
Analysis or Run identity. Existing flat paired-CMH Runs retain run-summary v2
and report-receipt v4; explicit modules use run-summary v3 and report-receipt
v5.

`context.prepare_context` admits the coordinator's explicit source checkout and
independent artifact source root before reading report inputs. This retains the
former `report.py` admission order and error identities. The logical producer
identifier remains `emrys.reporting.report`. The artifact root governs
contract-relative paths; admitted checkout/provider identities govern
implementation evidence. Neither root is inferred from the working directory
or run-summary location.

Publication follows the shared
[publication and recovery contract](../README.md#publication-and-recovery).
Context preparation retains existing-output admission for current and historical
readers. Rendering does not rerun analysis, discover native outputs, change
scientific evidence, or establish scientific review or biological validity.
