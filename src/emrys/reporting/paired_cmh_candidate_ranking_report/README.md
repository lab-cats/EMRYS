# Paired-CMH scientific report

This provider reads validated paired-CMH Results and scientific context, selects
candidate displays, builds figures, and supplies the scientific view to the
[core report transaction](../_run_report/README.md). It does not recalculate
statistics or publish evidence separately. The view describes computational
candidates; it cannot establish scientific adjudication or biological validity.

`computational.py` owns the report's table representation and streamed TSV reader.
Tables keep one file snapshot and named, read-only display rows. Step 09 result
counts, headers, and summary rows come from the scientific contract validator;
report admission does not parse the two candidate tables or summary again.
Candidate selection and figures still stream the complete populations they need,
with file-identity rechecks around those reads. Large candidate and motif tables
are never copied into the display-row collection. The mutation spectrum and
Step 10's bounded figure tables are read for display after canonical validation.
The existing artifact carrier supplies its admitted file snapshot and an isolated
copy of the Step 09/10 projection checked by artifact preparation. The reporter
requires those projections, then checks source identities and the exact Step 09/10
validation-report check lists without repeating scientific admission.

The existing [Jinja template](../templates/run_report.html.j2) renders the admitted
summary, selected candidates, and figures directly. `view.py` retains scientific
number formatting and the fixed figure-roster checks; it does not create another
candidate or layout representation. Both report layouts share the template's
markup, while the provider extension still returns scientific HTML bytes.
The former alpha `render_report_view` dictionary-layout interface is retired.

The shared presentation roster displays at most nine candidates, labeled A–I,
using admitted Step 10 order or the existing FDR/effect/ID fallback. Complete
candidate tables remain linked and unchanged. The native context contract and
receipt are version 2.0.0 with limit 9; old version-1 receipts are refused intact,
not upgraded. A new immutable Run binds the new implementation. Figure policy
5.0.0 uses three columns for nine paired profiles; full identities and condition
names remain in captions, alternative text and vertical details. Numeric fragment
and panel identifiers remain stable. Long text wraps on narrow screens and fragment
navigation leaves room for the persistent computational-results banner.

The REPORT-04 caller review reused the existing selector, native contract, figure
builders, template and CSS. It removes the private duplicate profile limit and
centralizes display labels without introducing a second selector or compatibility
path. The bounded feature adds ten net product lines across eight existing files,
with no dependency or product-file growth; this quantified exception is delivered
under the user's explicitly delegated autonomous scope. Test additions and
contract/guide updates are accounted separately, with retained evidence untouched.
