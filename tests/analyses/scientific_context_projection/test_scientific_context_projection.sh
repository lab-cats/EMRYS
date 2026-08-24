#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
producer="$repo_root/src/emrys/analyses/scientific_context_projection/scientific_context_projection.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export REAL_SHA256_PYTHON="$repo_root/.venv/bin/python"
export FSYNC_LOG="$tmp/fsync.log"
python_wrapper="$tmp/python-wrapper"
cat >"$python_wrapper" <<'PYTHON_WRAPPER'
#!/usr/bin/env bash
set -euo pipefail
case "$*" in
    *'not a regular file:'*) printf 'files\n' >>"${FSYNC_LOG:?}" ;;
    *'not a directory:'*) printf 'directory\n' >>"${FSYNC_LOG:?}" ;;
esac
exec "${REAL_SHA256_PYTHON:?}" "$@"
PYTHON_WRAPPER
chmod +x "$python_wrapper"
export EMRYS_SHA256_PYTHON="$python_wrapper"
unset EMRYS_LOCAL_PILOT_R EMRYS_RUN_TOKEN

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

expect_fail() {
    local pattern="$1"
    shift
    if "$@" >"$tmp/fail.out" 2>"$tmp/fail.err"; then
        fail "command unexpectedly succeeded: $*"
    fi
    grep -q "$pattern" "$tmp/fail.err" ||
        fail "failure did not contain '$pattern': $(cat "$tmp/fail.err")"
}

assert_no_owner_residue() {
    local directory="$1"
    local path
    for path in "$directory"/.analysis.scientific-context.* \
        "$directory"/.analysis.*.previous
    do
        [[ ! -e "$path" && ! -L "$path" ]] ||
            fail "owner residue remains: $path"
    done
}

mkdir -p "$tmp/bin" "$tmp/inputs"
printf 'all\n' >"$tmp/inputs/all.tsv"
printf 'significant\n' >"$tmp/inputs/significant.tsv"
printf 'summary\n' >"$tmp/inputs/summary.tsv"
printf '>1\nA\n' >"$tmp/inputs/reference.fa"
printf '1\t1\t3\t1\t2\n' >"$tmp/inputs/reference.fa.fai"

fake_r="$tmp/bin/fake-rscript"
cat >"$fake_r" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail
if [[ -n "${FAKE_R_MARKER:-}" ]]; then
    : >"$FAKE_R_MARKER"
fi
if [[ -n "${FAKE_R_ARGS:-}" ]]; then
    printf '%s\n' "$@" >"$FAKE_R_ARGS"
fi
r_program="$1"
: "$r_program"
shift
while [[ "$#" -gt 0 ]]; do
    key="${1#--}"
    value="$2"
    case "$key" in
        step09-summary) step09_summary="$value" ;;
        candidate-context-output) context="$value" ;;
        motif-hits-output) hits="$value" ;;
        sequence-logo-output) logo="$value" ;;
        motif-statistics-output) statistics="$value" ;;
        context-receipt-output) receipt="$value" ;;
        sequence-logo-final) final_logo="$value" ;;
    esac
    shift 2
done
printf 'candidate\nrow\n' >"$context"
printf 'hit\n' >"$hits"
printf 'logo\nrow\n' >"$logo"
printf 'statistics\nrow\n' >"$statistics"
context_hash="$(shasum -a 256 "$context" | awk '{print $1}')"
hits_hash="$(shasum -a 256 "$hits" | awk '{print $1}')"
logo_hash="$(shasum -a 256 "$logo" | awk '{print $1}')"
statistics_hash="$(shasum -a 256 "$statistics" | awk '{print $1}')"
printf '%s\n' \
    $'candidate_context_sha256\tcandidate_context_row_count\tmotif_hits_sha256\tmotif_hits_row_count\tsequence_logo_sha256\tsequence_logo_row_count\tmotif_statistics_sha256\tmotif_statistics_row_count' \
    "$context_hash"$'\t1\t'"$hits_hash"$'\t0\t'"$logo_hash"$'\t1\t'"$statistics_hash"$'\t1' \
    >"$receipt"
if [[ "${FAKE_R_MUTATE_INPUT:-0}" == 1 ]]; then
    printf 'mutated\n' >>"$step09_summary"
fi
if [[ "${FAKE_R_LATE_COLLISION:-0}" == 1 ]]; then
    printf 'foreign\n' >"$final_logo"
fi
FAKE
chmod +x "$fake_r"

base_command=(
    "$producer"
    --analysis-id analysis
    --step09-all-sites "$tmp/inputs/all.tsv"
    --step09-significant-sites "$tmp/inputs/significant.tsv"
    --step09-summary "$tmp/inputs/summary.tsv"
    --reference-fasta "$tmp/inputs/reference.fa"
    --reference-fai "$tmp/inputs/reference.fa.fai"
    --output-root "$tmp/output"
    --rscript-bin "$fake_r"
    --no-clobber
)

export FAKE_R_MARKER="$tmp/r-invoked"
export FAKE_R_ARGS="$tmp/r-args"
"${base_command[@]}" >"$tmp/dry-run.out"
[[ ! -e "$FAKE_R_MARKER" ]] || fail "dry-run invoked R"
[[ ! -e "$tmp/output" ]] || fail "dry-run created output root"
grep -q 'Dry-run only' "$tmp/dry-run.out" || fail "dry-run outcome was not printed"

"${base_command[@]}" --execute >"$tmp/execute.out"
output_dir="$tmp/output/analysis"
for suffix in \
    candidate_context.tsv motif_hits.tsv sequence_logo.tsv \
    motif_statistics.tsv context_receipt.tsv
do
    [[ -s "$output_dir/analysis.$suffix" ]] || fail "missing output: $suffix"
done
grep -qx -- '--candidate-context-final' "$FAKE_R_ARGS" ||
    fail "producer did not pass stable receipt-bound paths"
assert_no_owner_residue "$output_dir"
before="$(find "$output_dir" -maxdepth 1 -type f -print0 | sort -z | xargs -0 shasum -a 256)"
expect_fail 'under --no-clobber' "${base_command[@]}" --execute
after="$(find "$output_dir" -maxdepth 1 -type f -print0 | sort -z | xargs -0 shasum -a 256)"
[[ "$before" == "$after" ]] || fail "no-clobber changed a complete predecessor"

mkdir -p "$tmp/incomplete/analysis"
printf 'partial\n' >"$tmp/incomplete/analysis/analysis.candidate_context.tsv"
incomplete_command=("${base_command[@]}")
incomplete_command[14]="$tmp/incomplete"
expect_fail 'incomplete' "${incomplete_command[@]}"

rm -rf "$tmp/output"
printf 'summary\n' >"$tmp/inputs/summary.tsv"
export FAKE_R_MUTATE_INPUT=1
expect_fail 'Step 09 summary changed' "${base_command[@]}" --execute
unset FAKE_R_MUTATE_INPUT
[[ ! -e "$tmp/output/analysis/analysis.context_receipt.tsv" ]] ||
    fail "input mutation published a receipt"
assert_no_owner_residue "$tmp/output/analysis"

rm -rf "$tmp/output"
printf 'summary\n' >"$tmp/inputs/summary.tsv"
export FAKE_R_LATE_COLLISION=1
expect_fail 'already exists' "${base_command[@]}" --execute
unset FAKE_R_LATE_COLLISION
[[ "$(<"$tmp/output/analysis/analysis.sequence_logo.tsv")" == foreign ]] ||
    fail "late foreign output was removed"
[[ ! -e "$tmp/output/analysis/analysis.candidate_context.tsv" ]] ||
    fail "owned earlier publication was not rolled back"
[[ ! -e "$tmp/output/analysis/analysis.context_receipt.tsv" ]] ||
    fail "receipt was published before all payloads"
assert_no_owner_residue "$tmp/output/analysis"

[[ "$(grep -c '^files$' "$FSYNC_LOG")" -eq 2 ]] ||
    fail "expected staging fsync for the committed and rolled-back attempts"
[[ "$(grep -c '^directory$' "$FSYNC_LOG")" -eq 2 ]] ||
    fail "expected directory fsync for the commit and rollback boundaries"

printf 'Scientific-context shell transaction tests passed.\n'
