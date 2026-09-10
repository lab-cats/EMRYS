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

The existing [Jinja template](../templates/run_report.html.j2) renders the admitted
summary, selected candidates, and figures directly. `view.py` retains scientific
number formatting and the fixed figure-roster checks; it does not create another
candidate or layout representation. Both report layouts share the template's
markup, while the provider extension still returns scientific HTML bytes.
The former alpha `render_report_view` dictionary-layout interface is retired.
