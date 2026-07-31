#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

python_bin="${REPORT_PYTHON_BIN:-$repo_root/.venv/bin/python}"
[[ -x "$python_bin" ]] ||
    fail "report test Python is unavailable: $python_bin"

tmp="$(mktemp -d "${TMPDIR:-/tmp}/norad-report-html-shell.XXXXXX")"
tmp="$(cd "$tmp" && pwd -P)"
trap 'rm -rf "$tmp"' EXIT

"$python_bin" tests/fixtures/artifact_run_summary_v1/build_fixture.py \
    --root "$tmp/fixture" >/dev/null

artifact_root="$tmp/fixture/adapter_fixture/artifacts"
artifact_receipt="$artifact_root/synthetic_run/synthetic_run.artifact_receipt.tsv"
SOURCE_DATE_EPOCH=1700000000 "$python_bin" scripts/build_run_summary.py \
    --run-id synthetic_run \
    --artifact-receipt "$artifact_receipt" \
    --output-root "$artifact_root" \
    --execute >/dev/null

run_summary="$artifact_root/synthetic_run/synthetic_run.run_summary.json"
[[ -s "$run_summary" ]] || fail "synthetic run summary was not published"

fake_quarto="$tmp/quarto"
fake_log="$tmp/quarto.log"
cat >"$fake_quarto" <<'PY'
#!/usr/bin/env python3
import sys
from pathlib import Path

log = Path(__file__).with_name("quarto.log")
with log.open("a", encoding="utf-8") as stream:
    stream.write("\t".join(sys.argv[1:]) + "\n")
if sys.argv[1:] == ["--version"]:
    print("1.9.38")
    raise SystemExit(0)
if sys.argv[1:] == ["pandoc", "--version"]:
    print("pandoc 3.8.3")
    raise SystemExit(0)
if len(sys.argv) < 2 or sys.argv[1] != "render":
    raise SystemExit(97)
output_name = sys.argv[sys.argv.index("--output") + 1]
qmd = (Path.cwd() / sys.argv[2]).read_text(encoding="utf-8")
parts = qmd.split("---", 2)
body = parts[2] if len(parts) == 3 else qmd
payload = (
    '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
    "<title>NORAD consolidated run report</title>"
    "<style>body{color:#17202a}</style></head><body>"
    + body
    + "</body></html>\n"
)
(Path.cwd() / output_name).write_text(payload, encoding="utf-8")
PY
chmod +x "$fake_quarto"

scripts/render_run_report.sh --help >"$tmp/help.out"
for option in --run-summary --output-root --quarto-bin --formats --execute; do
    grep -Fq -- "$option" "$tmp/help.out" ||
        fail "help output is missing $option"
done
grep -Fq '<repo>/.venv/bin/python' "$tmp/help.out" ||
    fail "help output does not document repository-venv preference"
grep -Fq 'explicit value is authoritative' "$tmp/help.out" ||
    fail "help output does not document explicit-Python authority"

if scripts/render_run_report.sh \
    --run-summary "$run_summary" \
    --output-root "$tmp/reports-missing" >"$tmp/missing.out" 2>&1; then
    fail "wrapper accepted a missing --quarto-bin"
fi
grep -Fq 'Missing required argument: --quarto-bin' "$tmp/missing.out" ||
    fail "missing-argument failure was not specific"

if scripts/render_run_report.sh \
    --run-summary "$run_summary" \
    --output-root "$tmp/reports-invalid" \
    --quarto-bin "$fake_quarto" \
    --formats docx >"$tmp/invalid.out" 2>&1; then
    fail "renderer accepted an unsupported format"
fi
grep -Fq -- '--formats must be html, pdf, or all' "$tmp/invalid.out" ||
    fail "unsupported-format failure was not specific"

default_root="$tmp/reports-default"
env -u PYTHON_BIN_OVERRIDE \
    scripts/render_run_report.sh \
    --run-summary "$run_summary" \
    --output-root "$default_root" \
    --quarto-bin "$fake_quarto" >"$tmp/default.out"
grep -Fq "  Python: $repo_root/.venv/bin/python" "$tmp/default.out" ||
    fail "unset override did not select the executable repository venv"
[[ ! -e "$default_root" ]] ||
    fail "default-Python dry-run created report output storage"
grep -Fxq -- '--version' "$fake_log" ||
    fail "default-Python dry-run did not reach Quarto version validation"
grep -Fxq -- $'pandoc\t--version' "$fake_log" ||
    fail "default all dry-run did not inspect bundled Pandoc"
: >"$fake_log"

bad_python="$tmp/bad-python"
cat >"$bad_python" <<'SH'
#!/usr/bin/env bash
printf 'synthetic dependency import failure\n' >&2
exit 91
SH
chmod +x "$bad_python"
bad_root="$tmp/reports-bad-python"
if PYTHON_BIN_OVERRIDE="$bad_python" \
    scripts/render_run_report.sh \
    --run-summary "$run_summary" \
    --output-root "$bad_root" \
    --quarto-bin "$fake_quarto" >"$tmp/bad-python.out" 2>&1; then
    fail "wrapper accepted an explicit Python that cannot import dependencies"
fi
grep -Fq 'cannot import required report dependencies' "$tmp/bad-python.out" ||
    fail "bad explicit Python failure did not identify dependency imports"
grep -Fq "$bad_python" "$tmp/bad-python.out" ||
    fail "bad explicit Python failure did not identify the selected executable"
grep -Fq 'synthetic dependency import failure' "$tmp/bad-python.out" ||
    fail "bad explicit Python failure omitted the import detail"
[[ ! -e "$bad_root" ]] ||
    fail "bad explicit Python created report output storage"
[[ ! -s "$fake_log" ]] ||
    fail "bad explicit Python delegated to Quarto"

dry_root="$tmp/reports-dry"
PYTHON_BIN_OVERRIDE="$python_bin" \
    scripts/render_run_report.sh \
    --run-summary "$run_summary" \
    --output-root "$dry_root" \
    --quarto-bin "$fake_quarto" \
    --formats html >"$tmp/dry.out"
grep -Fiq 'dry-run' "$tmp/dry.out" ||
    fail "wrapper did not report dry-run mode"
[[ ! -e "$dry_root" ]] ||
    fail "dry-run created report output storage"
[[ "$(wc -l <"$fake_log" | tr -d ' ')" -eq 2 ]] ||
    fail "dry-run did not perform exactly the Quarto and Pandoc version checks"
grep -Fxq -- '--version' "$fake_log" ||
    fail "dry-run did not inspect Quarto version"
grep -Fxq -- $'pandoc\t--version' "$fake_log" ||
    fail "dry-run did not inspect bundled Pandoc"

unrelated="$tmp/unrelated.tsv"
printf 'must\tremain\nunchanged\ttrue\n' >"$unrelated"
unrelated_before="$(shasum -a 256 "$unrelated" | awk '{print $1}')"
execute_root="$tmp/reports-execute"
PYTHON_BIN_OVERRIDE="$python_bin" \
    scripts/render_run_report.sh \
    --run-summary "$run_summary" \
    --output-root "$execute_root" \
    --quarto-bin "$fake_quarto" \
    --formats html \
    --execute >"$tmp/execute.out"

report="$execute_root/synthetic_run/synthetic_run.run_report.html"
summary_export="$execute_root/synthetic_run/synthetic_run.run_summary.tsv"
receipt="$execute_root/synthetic_run/synthetic_run.report_outputs.tsv"
[[ -s "$report" ]] || fail "execute mode did not publish the exact HTML path"
[[ -s "$summary_export" ]] ||
    fail "HTML mode did not publish the deterministic summary TSV"
[[ -s "$receipt" ]] ||
    fail "HTML mode did not publish the receipt last"
grep -Fq 'SCIENTIFIC REVIEW INCOMPLETE — NO BIOLOGICAL INTERPRETATION.' \
    "$report" || fail "HTML report lacks the exact incomplete-science banner"
grep -Fq 'CMH-ranked candidates' "$report" ||
    fail "HTML report lacks required candidate terminology"
grep -Fq $'render\tsynthetic_run.run_report.qmd\t--to\thtml\t--output\tsynthetic_run.run_report.html\t--no-execute' \
    "$fake_log" || fail "wrapper did not issue the exact static Quarto render"
[[ "$unrelated_before" == "$(shasum -a 256 "$unrelated" | awk '{print $1}')" ]] ||
    fail "renderer changed an unrelated file"
if find "$execute_root/synthetic_run" -maxdepth 1 \
    \( -name '*.lock' -o -name '*.tmp' -o -name '*.previous' -o -name '*_files' \) \
    -print -quit | grep -q .; then
    fail "successful render left transaction or sidecar residue"
fi

if rg -n 'restore_quarto|step_0[0-9]|bcftools|samtools|Rscript|mantelhaen' \
    scripts/render_run_report.sh | grep -v 'report-exports-v1' >/dev/null; then
    fail "public renderer wrapper contains an install or analysis invocation"
fi

missing_demo_root="$tmp/make-demo-missing"
if make --no-print-directory demo-report \
    DEMO_REPORT_ROOT="$missing_demo_root" \
    DEMO_REPORT_FORMATS=html \
    QUARTO_BIN="$tmp/missing-quarto" \
    REPORT_PYTHON_BIN="$python_bin" >"$tmp/make-demo-missing.out" 2>&1; then
    fail "demo-report accepted a missing pinned Quarto executable"
fi
grep -Fq 'Run make quarto-restore first.' "$tmp/make-demo-missing.out" ||
    fail "demo-report missing-Quarto failure omitted setup guidance"
[[ ! -e "$missing_demo_root" ]] ||
    fail "demo-report missing-Quarto failure created output storage"

invalid_demo_root="$tmp/make-demo-invalid"
if make --no-print-directory demo-report \
    DEMO_REPORT_ROOT="$invalid_demo_root" \
    DEMO_REPORT_FORMATS=docx \
    QUARTO_BIN="$fake_quarto" \
    REPORT_PYTHON_BIN="$python_bin" >"$tmp/make-demo-invalid.out" 2>&1; then
    fail "demo-report accepted an unsupported report format"
fi
grep -Fq 'DEMO_REPORT_FORMATS must be html, pdf, or all' \
    "$tmp/make-demo-invalid.out" ||
    fail "demo-report unsupported-format failure was not specific"
[[ ! -e "$invalid_demo_root" ]] ||
    fail "demo-report unsupported-format failure created output storage"

bad_python_demo_root="$tmp/make-demo-bad-python"
if make --no-print-directory demo-report \
    DEMO_REPORT_ROOT="$bad_python_demo_root" \
    DEMO_REPORT_FORMATS=html \
    QUARTO_BIN="$fake_quarto" \
    REPORT_PYTHON_BIN="$bad_python" >"$tmp/make-demo-bad-python.out" 2>&1; then
    fail "demo-report accepted Python without report dependencies"
fi
grep -Fq 'report Python dependencies are unavailable' \
    "$tmp/make-demo-bad-python.out" ||
    fail "demo-report bad-Python failure omitted dependency guidance"
[[ ! -e "$bad_python_demo_root" ]] ||
    fail "demo-report bad-Python failure created output storage"

make_demo_root="$tmp/make-demo"
for attempt in 1 2; do
    make --no-print-directory demo-report \
        DEMO_REPORT_ROOT="$make_demo_root" \
        DEMO_REPORT_FORMATS=html \
        QUARTO_BIN="$fake_quarto" \
        REPORT_PYTHON_BIN="$python_bin" >"$tmp/make-demo-$attempt.out"

    make_demo_output="$make_demo_root/reports/synthetic_run"
    make_demo_html="$make_demo_output/synthetic_run.run_report.html"
    make_demo_summary="$make_demo_output/synthetic_run.run_summary.tsv"
    make_demo_receipt="$make_demo_output/synthetic_run.report_outputs.tsv"
    [[ -s "$make_demo_html" ]] ||
        fail "demo-report attempt $attempt did not publish HTML"
    [[ -s "$make_demo_summary" ]] ||
        fail "demo-report attempt $attempt did not publish the summary TSV"
    [[ -s "$make_demo_receipt" ]] ||
        fail "demo-report attempt $attempt did not publish the receipt"
    grep -Fq 'SCIENTIFIC REVIEW INCOMPLETE — NO BIOLOGICAL INTERPRETATION.' \
        "$make_demo_html" ||
        fail "demo-report attempt $attempt lacks the evidence banner"
    grep -Fq 'CMH-ranked candidates' "$make_demo_html" ||
        fail "demo-report attempt $attempt lacks required candidate terminology"
    grep -Fq "Demo report bundle: $make_demo_output" \
        "$tmp/make-demo-$attempt.out" ||
        fail "demo-report attempt $attempt did not print its output path"
    if find "$make_demo_root" \
        \( -name '*.lock' -o -name '*.tmp' -o -name '*.previous' \
            -o -name '*_files' \) -print -quit | grep -q .; then
        fail "demo-report attempt $attempt left transaction residue"
    fi
done

printf 'PASS: static report wrapper contract\n'
