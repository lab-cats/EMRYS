#!/usr/bin/env bash
# Native scientific behavior only; task-runner tests own publication and recovery.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPT="$repo_root/src/emrys/evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
fake_bin="$tmp_dir/bin"
mkdir -p "$fake_bin" "$tmp_dir/inputs" "$tmp_dir/staged" "$tmp_dir/work"
export EMRYS_SHA256_PYTHON="$repo_root/.venv/bin/python"
export EMRYS_TASK_WORK_DIR="$tmp_dir/work" TMPDIR="$tmp_dir/work"
export PATH="$fake_bin:$PATH"
fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
assert_contains() { grep -Fq -- "$2" "$1" || fail "missing $2 in $1: $(cat "$1")"; }
assert_fails() {
    local pattern="$1"; shift
    if "$@" >"$tmp_dir/failure.out" 2>&1; then fail "unexpected success: $*"; fi
    assert_contains "$tmp_dir/failure.out" "$pattern"
}
infer_log="$tmp_dir/infer_experiment.py.log"
cat >"$fake_bin/infer_experiment.py" <<EOF_INFER
#!/usr/bin/env bash
set -euo pipefail

printf 'infer_experiment.py invoked\\n' >> "$infer_log"
printf '%s\\n' "\$@" >> "$infer_log"


mode="\${FAKE_INFER_MODE:-success}"
case "\$mode" in
    success)
        printf 'This is PairEnd Data\\n'
        printf 'Fraction of reads failed to determine: 0.0100\\n'
        printf 'Fraction of reads explained by "1++,1--,2+-,2-+": 0.9700\\n'
        printf 'Fraction of reads explained by "1+-,1-+,2++,2--": 0.0200\\n'
        ;;
    empty_success)
        exit 0
        ;;
    partial_fail)
        printf 'partial RSeQC child bytes\\n'
        printf 'partial RSeQC failure diagnostic\\n' >&2
        exit 42
        ;;
    malformed_success)
        printf 'This is PairEnd Data\\n'
        printf 'nonempty malformed orientation evidence\\n'
        ;;
    fail)
        printf 'fake infer_experiment.py failure\\n' >&2
        exit 42
        ;;
    *)
        printf 'unknown FAKE_INFER_MODE: %s\\n' "\$mode" >&2
        exit 64
        ;;
esac
EOF_INFER
chmod +x "$fake_bin/infer_experiment.py"

bam="$tmp_dir/inputs/sample.bam"
bed12="$tmp_dir/inputs/annotation.bed"
printf 'BAM\n' >"$bam"
printf 'BAI\n' >"${bam%.bam}.bai"
printf 'chr1\t0\t100\ttx1\t0\t+\t0\t100\t0\t1\t100,\t0,\n' >"$bed12"
command=(bash "$SCRIPT" --sample-id sample --input-bam "$bam" --bed12 "$bed12"
    --output-dir "$tmp_dir/staged" --infer-experiment-bin "$fake_bin/infer_experiment.py")
"${command[@]}"
assert_contains "$tmp_dir/staged/sample.infer_experiment.txt" 'This is PairEnd Data'
assert_contains "$infer_log" "$bed12"
assert_contains "$infer_log" "$bam"
assert_fails 'does not exist or is empty' env FAKE_INFER_MODE=empty_success "${command[@]}"
assert_fails 'partial RSeQC failure diagnostic' env FAKE_INFER_MODE=partial_fail "${command[@]}"
# Syntax/scientific interpretation remains the independent validator's job.
FAKE_INFER_MODE=malformed_success "${command[@]}"
assert_contains "$tmp_dir/staged/sample.infer_experiment.txt" 'nonempty malformed orientation evidence'
assert_fails 'requires EMRYS_TASK_WORK_DIR' env -u EMRYS_TASK_WORK_DIR "${command[@]}"
printf 'Native worker checks passed.\n'
