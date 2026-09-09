#!/usr/bin/env bash
# Native scientific behavior only; task-runner tests own publication and recovery.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPT="$repo_root/src/emrys/stages/star_alignment/step_01_star_align.sh"
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
star_log="$tmp_dir/STAR.log"
cat >"$fake_bin/STAR" <<EOF_STAR
#!/usr/bin/env bash
printf 'STAR invoked\n' >> "$star_log"
printf '%s\n' "\$@" >> "$star_log"
status="\${STAR_EXIT_CODE:-0}"
if [[ "\$status" -eq 0 ]]; then
    prefix=""
    while [[ \$# -gt 0 ]]; do
        if [[ "\$1" == "--outFileNamePrefix" ]]; then
            prefix="\$2"
            break
        fi
        shift
    done
    [[ -n "\$prefix" ]] || exit 64
    mkdir -p "\$(dirname "\$prefix")"
    for suffix in Aligned.sortedByCoord.out.bam Log.final.out Log.out Log.progress.out SJ.out.tab; do
        printf 'fake STAR %s\n' "\$suffix" >"\${prefix}\${suffix}"
    done
    if [[ -n "\${STAR_MUTATE_INDEX_FILE:-}" ]]; then
        printf 'mutated during STAR\n' >>"\$STAR_MUTATE_INDEX_FILE"
    fi
fi
exit "\$status"
EOF_STAR
chmod +x "$fake_bin/STAR"

printf '@read\nACGT\n+\n!!!!\n' >"$tmp_dir/inputs/R1.fastq"
cp "$tmp_dir/inputs/R1.fastq" "$tmp_dir/inputs/R2.fastq"
mkdir "$tmp_dir/index"
printf 'index\n' >"$tmp_dir/index/Genome"
command=(bash "$SCRIPT" --sample-id sample --r1-fastq "$tmp_dir/inputs/R1.fastq"
    --r2-fastq "$tmp_dir/inputs/R2.fastq" --star-index "$tmp_dir/index"
    --output-dir "$tmp_dir/staged" --threads 2 --star-bin "$fake_bin/STAR")
"${command[@]}"
for suffix in Aligned.sortedByCoord.out.bam Log.final.out Log.out Log.progress.out SJ.out.tab; do
    [[ -s "$tmp_dir/staged/sample.$suffix" ]] || fail "missing STAR $suffix"
done
assert_contains "$star_log" 'SortedByCoordinate'
assert_contains "$star_log" 'ID:sample'
cp "$tmp_dir/inputs/R1.fastq" "$tmp_dir/inputs/R1.fastq.gz"
cp "$tmp_dir/inputs/R2.fastq" "$tmp_dir/inputs/R2.fastq.gz"
"${command[@]}" --r1-fastq "$tmp_dir/inputs/R1.fastq.gz" --r2-fastq "$tmp_dir/inputs/R2.fastq.gz" --gunzip-bin /usr/bin/gunzip
assert_contains "$star_log" /usr/bin/gunzip
assert_fails 'must both be gzip-compressed' "${command[@]}" --r1-fastq "$tmp_dir/inputs/R1.fastq.gz"
if STAR_EXIT_CODE=37 "${command[@]}"; then fail "STAR failure was ignored"; fi
assert_fails 'requires EMRYS_TASK_WORK_DIR' env -u EMRYS_TASK_WORK_DIR "${command[@]}"
printf 'Native worker checks passed.\n'
