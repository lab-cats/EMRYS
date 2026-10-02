#!/usr/bin/env bash
# Native receipt binding; the task runner owns publication and recovery.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
producer="$repo_root/src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/scientific_context_projection.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export EMRYS_SHA256_PYTHON="$repo_root/.venv/bin/python"
export EMRYS_TASK_WORK_DIR="$tmp/work" TMPDIR="$tmp/work"
unset EMRYS_LOCAL_PILOT_R
mkdir -p "$tmp/bin" "$tmp/inputs" "$tmp/staged" "$tmp/work"
printf 'all\n' >"$tmp/inputs/all.tsv"
printf 'significant\n' >"$tmp/inputs/significant.tsv"
printf 'summary\n' >"$tmp/inputs/summary.tsv"
printf '>1\nA\n' >"$tmp/inputs/reference.fa"
printf '1\t1\t3\t1\t2\n' >"$tmp/inputs/reference.fa.fai"
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
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
shift
while [[ "$#" -gt 0 ]]; do
    key="${1#--}"
    value="$2"
    case "$key" in
        candidate-context-output) context="$value" ;;
        motif-hits-output) hits="$value" ;;
        sequence-logo-output) logo="$value" ;;
        motif-statistics-output) statistics="$value" ;;
        context-receipt-output) receipt="$value" ;;
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
if [[ "${FAKE_R_BAD_RECEIPT:-0}" == 1 ]]; then
    printf 'broken\n' >"$receipt"
fi
FAKE
chmod +x "$fake_r"

command=("$producer" --analysis-id analysis
    --step09-all-sites "$tmp/inputs/all.tsv" --step09-significant-sites "$tmp/inputs/significant.tsv"
    --step09-summary "$tmp/inputs/summary.tsv" --reference-fasta "$tmp/inputs/reference.fa"
    --reference-fai "$tmp/inputs/reference.fa.fai" --rscript-bin "$fake_r"
    --git-commit unavailable)
for stem in candidate-context motif-hits sequence-logo motif-statistics; do
    command+=("--$stem-output" "$tmp/staged/$stem.tsv" "--$stem-final" "$tmp/final/$stem.tsv")
done
command+=(--context-receipt-output "$tmp/staged/receipt.tsv")
export FAKE_R_ARGS="$tmp/args"
"${command[@]}" >"$tmp/worker.log"
for stem in candidate-context motif-hits sequence-logo motif-statistics receipt; do
    [[ -s "$tmp/staged/$stem.tsv" ]] || fail "missing staged $stem"
done
[[ ! -e "$tmp/final" ]] || fail 'worker published final paths'
"$EMRYS_SHA256_PYTHON" - "$FAKE_R_ARGS" "$repo_root" "$tmp" <<'PYTHON'
import hashlib
import sys
from pathlib import Path

args = Path(sys.argv[1]).read_text().splitlines()
owner = Path(sys.argv[2]) / "src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection"
fixture = Path(sys.argv[3])
assert args[0] == str(owner / "scientific_context_projection.R"), "Wrong R script"
assert len(args[1:]) % 2 == 0, "R arguments must be flag/value pairs"
assert len(args[1::2]) == len(set(args[1::2])), "R argument flags must be unique"
inputs = {
    "--step09-all-sites": fixture / "inputs/all.tsv",
    "--step09-significant-sites": fixture / "inputs/significant.tsv",
    "--step09-summary": fixture / "inputs/summary.tsv",
    "--reference-fasta": fixture / "inputs/reference.fa",
    "--reference-fai": fixture / "inputs/reference.fa.fai",
    "--motif-catalog": owner / "resources/pum_motifs_v1.tsv",
}
expected = {
    "--candidate-context-final": str(fixture / "final/candidate-context.tsv"),
    "--motif-hits-final": str(fixture / "final/motif-hits.tsv"),
    "--sequence-logo-final": str(fixture / "final/sequence-logo.tsv"),
    "--motif-statistics-final": str(fixture / "final/motif-statistics.tsv"),
}
for flag, path in inputs.items():
    expected[flag] = str(path)
    expected[flag + "-sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
for flag, value in expected.items():
    assert args.count(flag) == 1, f"R argument {flag} must appear exactly once"
    assert args[args.index(flag) + 1] == value, f"Wrong value for R argument {flag}"
PYTHON
if FAKE_R_BAD_RECEIPT=1 "${command[@]}" >"$tmp/bad.log" 2>&1; then fail 'invalid native receipt was accepted'; fi
grep -q 'does not bind its four payloads' "$tmp/bad.log" || fail 'receipt check did not run'
printf 'Native scientific-context worker checks passed.\n'
