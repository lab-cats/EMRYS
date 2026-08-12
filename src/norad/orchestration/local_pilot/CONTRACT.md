# Local-pilot intake contract

`normalization.normalize_request` is a read-only public Python boundary. It
uses the closed safe YAML loader, resolves paths against the request directory,
reuses the public Step `08`/`09` manifest contracts, requires at least two
exact control/treatment strata, snapshots declared regular non-symlink inputs,
and validates the canonical execution contract. Duplicate keys, custom tags, merge
keys, globs, templates, environment/home interpolation, unknown fields, and
ambiguous paths fail admission. Request formatting and the optional human label
do not enter the execution identity.

Every authored file path passes one lexical policy before access. Admission
opens the file without following a final symbolic link, verifies that the open
descriptor and pathname name the same inode before and after reading, and binds
the exact descriptor bytes. Request YAML, path-based profile JSON, and sample
and partition TSV parsing consume those admitted bytes without reopening the
pathname.

The neutral `norad.contracts.orchestration.projection.project_reporting` API
deterministically derives the existing six-field artifact run contract and
explicit inventory bytes. Generated paths are run-root-relative; stationary
Step `00c` FASTA and sidecar paths may be absolute normalized external paths.
The projection does not discover files or promote reporting identity into
workflow identity.

The public `python -I -m norad validate all-pass` route reads one explicit
owner-validation report and writes nothing. It requires the exact shared
seven-column validation header, at least one well-formed check row, the
declared step and scope on every row, unique nonempty `check_id` values, and
`status=pass` for every row.

Success exits `0` and reports the absolute lexical input path, SHA-256 of the
exact parsed bytes, row count, and ordered check IDs. A malformed, mismatched,
empty, or nonpassing report exits `1`; argument-usage errors exit `2`. The
checker publishes no receipt and does not infer success from validator exit,
output presence, Snakemake metadata, or timestamps.

The internal task module consumes one closed, run-contained dispatch. It binds
the canonical execution/profile snapshots and selected owner scope; captures
the exact public producer, validator, and semantic commands; rechecks inputs,
outputs, validation report, and native receipt; publishes an immutable task
attempt on admitted success or failure; and publishes a create-exclusive
verified-task record only on complete success. Only the exact Step `00c`
FAI/dictionary pair may be stationary external outputs, and its FASTA and
parent must be canonical before producer invocation.

Snakemake schedules only verified-task records. Native artifacts, validation
reports, receipts, logs, and recovery evidence are never disposable workflow
outputs. Existing verified records are reusable only after read-only schema,
identity, content, attempt, receipt, and semantic-report revalidation.

These results are local structural/no-science workflow facts. They are not
owner-native receipts, real runtime or cluster proof, completed scientific
review, or biological validation.
