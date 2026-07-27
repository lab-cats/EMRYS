#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/step_01_star_align.sh"

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

assert_contains() {
    local file="$1"
    local expected="$2"

    if ! grep -Fq -- "$expected" "$file"; then
        printf 'Expected to find: %s\n' "$expected" >&2
        printf 'Actual output:\n' >&2
        cat "$file" >&2
        fail "missing expected output"
    fi
}

assert_not_contains() {
    local file="$1"
    local unexpected="$2"

    if grep -Fq -- "$unexpected" "$file"; then
        printf 'Did not expect to find: %s\n' "$unexpected" >&2
        printf 'Actual output:\n' >&2
        cat "$file" >&2
        fail "unexpected output present"
    fi
}

assert_nonempty_file() {
    local path="$1"

    [[ -s "$path" ]] || fail "expected nonempty file: $path"
}

assert_not_exists() {
    local path="$1"

    [[ ! -e "$path" ]] || fail "path should not exist: $path"
}

assert_fails() {
    local output_file="$1"
    shift

    if "$@" >"$output_file" 2>&1; then
        cat "$output_file" >&2
        fail "command unexpectedly succeeded: $*"
    fi
}

assert_no_step01_scratch() {
    local output_dir="$1"

    if [[ ! -d "$output_dir" ]]; then
        return 0
    fi
    if find "$output_dir" -mindepth 1 -maxdepth 1 -name '.step01.*.tmp' -print -quit | grep -q .; then
        find "$output_dir" -mindepth 1 -maxdepth 1 -name '.step01.*.tmp' >&2
        fail "Step 01 scratch paths were not cleaned from $output_dir"
    fi
}

assert_no_star_outputs() {
    local output_dir="$1"
    local sample_id="$2"
    local suffix

    for suffix in \
        Aligned.sortedByCoord.out.bam \
        Log.final.out \
        Log.out \
        Log.progress.out \
        SJ.out.tab
    do
        assert_not_exists "$output_dir/${sample_id}.${suffix}"
    done
    assert_no_step01_scratch "$output_dir"
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

fake_bin="$tmp_dir/bin"
mkdir -p "$fake_bin"

star_log="$tmp_dir/star_invocations.log"
export FAKE_STAR_LOG="$star_log"
cat >"$fake_bin/STAR" <<'EOF_STAR'
#!/usr/bin/env bash
set -euo pipefail

printf 'STAR invoked\n' >> "$FAKE_STAR_LOG"
printf '%s\n' "$@" >> "$FAKE_STAR_LOG"

output_prefix=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --outFileNamePrefix)
            output_prefix="${2:-}"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

[[ -n "$output_prefix" ]] || {
    printf 'fake STAR did not receive --outFileNamePrefix\n' >&2
    exit 64
}

write_output() {
    local suffix="$1"
    printf 'synthetic STAR output for %s\n' "$suffix" > "${output_prefix}${suffix}"
}

case "${FAKE_STAR_MODE:-success}" in
    success)
        write_output Aligned.sortedByCoord.out.bam
        write_output Log.final.out
        write_output Log.out
        write_output Log.progress.out
        write_output SJ.out.tab
        ;;
    no_outputs)
        ;;
    missing_output)
        write_output Aligned.sortedByCoord.out.bam
        write_output Log.final.out
        write_output Log.out
        write_output Log.progress.out
        ;;
    empty_output)
        write_output Aligned.sortedByCoord.out.bam
        : > "${output_prefix}Log.final.out"
        write_output Log.out
        write_output Log.progress.out
        write_output SJ.out.tab
        ;;
    fail_after_partial)
        write_output Log.out
        printf 'fake STAR forced failure\n' >&2
        exit 42
        ;;
    *)
        printf 'unsupported FAKE_STAR_MODE: %s\n' "$FAKE_STAR_MODE" >&2
        exit 64
        ;;
esac
EOF_STAR
chmod +x "$fake_bin/STAR"

cat >"$fake_bin/gunzip" <<'EOF_GUNZIP'
#!/usr/bin/env bash
printf 'fake gunzip should not be executed by smoke tests\n' >&2
exit 99
EOF_GUNZIP
chmod +x "$fake_bin/gunzip"

export PATH="$fake_bin:$PATH"

fixture_dir="$tmp_dir/fixtures"
star_index="$fixture_dir/star_index"
mkdir -p "$star_index"

r1_fastq="$fixture_dir/sample_R1.fastq"
r2_fastq="$fixture_dir/sample_R2.fastq"
r1_gz="$fixture_dir/sample_R1.fastq.gz"
r2_gz="$fixture_dir/sample_R2.fastq.gz"

printf '@r1\nACGT\n+\n!!!!\n' >"$r1_fastq"
printf '@r2\nTGCA\n+\n!!!!\n' >"$r2_fastq"
printf 'placeholder gz r1\n' >"$r1_gz"
printf 'placeholder gz r2\n' >"$r2_gz"

printf 'Running syntax check...\n'
bash -n "$SCRIPT"

printf 'Running help check...\n'
help_output="$tmp_dir/help.out"
bash "$SCRIPT" --help >"$help_output"
assert_contains "$help_output" "Usage:"
assert_contains "$help_output" "--execute"

printf 'Running dry-run check...\n'
dry_output="$tmp_dir/dry.out"
dry_output_dir="$tmp_dir/results/dry"
bash "$SCRIPT" \
    --sample-id sample_001 \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$dry_output_dir" \
    --threads 4 \
    >"$dry_output"

assert_not_exists "$dry_output_dir"
[[ ! -e "$star_log" ]] || fail "dry-run invoked STAR"
assert_contains "$dry_output" "Mode: dry-run"
assert_contains "$dry_output" "--outFileNamePrefix"
assert_contains "$dry_output" "$dry_output_dir/sample_001."
assert_contains "$dry_output" "--outSAMtype"
assert_contains "$dry_output" "BAM"
assert_contains "$dry_output" "SortedByCoordinate"
assert_not_contains "$dry_output" "--readFilesCommand"

printf 'Running execute check...\n'
execute_output="$tmp_dir/execute.out"
execute_output_dir="$tmp_dir/results/execute"
bash "$SCRIPT" \
    --sample-id sample_002 \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$execute_output_dir" \
    --threads 2 \
    --execute \
    >"$execute_output"

[[ -d "$execute_output_dir" ]] || fail "execute did not create output directory"
[[ -e "$star_log" ]] || fail "execute did not invoke STAR"
assert_contains "$star_log" "STAR invoked"
assert_contains "$star_log" "--runThreadN"
assert_contains "$star_log" "2"
assert_contains "$star_log" "--outSAMtype"
assert_contains "$star_log" "BAM"
assert_contains "$star_log" "SortedByCoordinate"
assert_contains "$execute_output" "Mode: execute"
assert_contains "$execute_output" "$execute_output_dir/sample_002."
assert_nonempty_file "$execute_output_dir/sample_002.Aligned.sortedByCoord.out.bam"
assert_nonempty_file "$execute_output_dir/sample_002.Log.final.out"
assert_nonempty_file "$execute_output_dir/sample_002.Log.out"
assert_nonempty_file "$execute_output_dir/sample_002.Log.progress.out"
assert_nonempty_file "$execute_output_dir/sample_002.SJ.out.tab"
assert_no_step01_scratch "$execute_output_dir"

printf 'Running zero-exit/no-output failure check...\n'
no_outputs_output="$tmp_dir/no_outputs.out"
no_outputs_dir="$tmp_dir/results/no_outputs"
assert_fails "$no_outputs_output" env FAKE_STAR_MODE=no_outputs bash "$SCRIPT" \
    --sample-id sample_no_outputs \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$no_outputs_dir" \
    --threads 1 \
    --execute
assert_contains "$no_outputs_output" "STAR required output is missing or empty"
assert_no_star_outputs "$no_outputs_dir" sample_no_outputs
assert_not_exists "$no_outputs_dir"

printf 'Running missing-output cleanup check...\n'
missing_output_log="$tmp_dir/missing_output.out"
missing_output_dir="$tmp_dir/results/missing_output"
assert_fails "$missing_output_log" env FAKE_STAR_MODE=missing_output bash "$SCRIPT" \
    --sample-id sample_missing_output \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$missing_output_dir" \
    --threads 1 \
    --execute
assert_contains "$missing_output_log" "STAR required output is missing or empty"
assert_no_star_outputs "$missing_output_dir" sample_missing_output
assert_not_exists "$missing_output_dir"

printf 'Running empty-output cleanup check...\n'
empty_output_log="$tmp_dir/empty_output.out"
empty_output_dir="$tmp_dir/results/empty_output"
assert_fails "$empty_output_log" env FAKE_STAR_MODE=empty_output bash "$SCRIPT" \
    --sample-id sample_empty_output \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$empty_output_dir" \
    --threads 1 \
    --execute
assert_contains "$empty_output_log" "STAR required output is missing or empty"
assert_no_star_outputs "$empty_output_dir" sample_empty_output
assert_not_exists "$empty_output_dir"

printf 'Running nonzero STAR cleanup check...\n'
star_failure_log="$tmp_dir/star_failure.out"
star_failure_dir="$tmp_dir/results/star_failure"
assert_fails "$star_failure_log" env FAKE_STAR_MODE=fail_after_partial bash "$SCRIPT" \
    --sample-id sample_star_failure \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$star_failure_dir" \
    --threads 1 \
    --execute
assert_contains "$star_failure_log" "fake STAR forced failure"
assert_no_star_outputs "$star_failure_dir" sample_star_failure
assert_not_exists "$star_failure_dir"

printf 'Running existing-output no-clobber check...\n'
existing_output_log="$tmp_dir/existing_output.out"
existing_output_dir="$tmp_dir/results/existing_output"
mkdir -p "$existing_output_dir"
printf 'preserve this predecessor\n' \
    > "$existing_output_dir/sample_existing.Aligned.sortedByCoord.out.bam"
assert_fails "$existing_output_log" bash "$SCRIPT" \
    --sample-id sample_existing \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$existing_output_dir" \
    --threads 1 \
    --execute
assert_contains "$existing_output_log" "Refusing to overwrite existing STAR output"
assert_contains \
    "$existing_output_dir/sample_existing.Aligned.sortedByCoord.out.bam" \
    "preserve this predecessor"
assert_no_step01_scratch "$existing_output_dir"

printf 'Running broken-output-symlink no-clobber check...\n'
broken_output_log="$tmp_dir/broken_output.out"
broken_output_dir="$tmp_dir/results/broken_output"
mkdir -p "$broken_output_dir"
broken_output="$broken_output_dir/sample_broken.Aligned.sortedByCoord.out.bam"
ln -s "$broken_output_dir/missing-foreign-target.bam" "$broken_output"
assert_fails "$broken_output_log" bash "$SCRIPT" \
    --sample-id sample_broken \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$broken_output_dir" \
    --threads 1 \
    --execute
assert_contains "$broken_output_log" "Refusing to overwrite existing STAR output"
[[ -L "$broken_output" ]] || fail "broken output symlink was not preserved"
assert_not_exists "$broken_output_dir/missing-foreign-target.bam"
assert_no_step01_scratch "$broken_output_dir"

printf 'Running symlinked-output-directory rejection check...\n'
symlink_output_log="$tmp_dir/symlink_output.out"
symlink_target_dir="$tmp_dir/operator_owned_output"
symlink_output_dir="$tmp_dir/results/symlink_output"
mkdir -p "$symlink_target_dir" "$(dirname "$symlink_output_dir")"
printf 'preserve operator data\n' > "$symlink_target_dir/marker.txt"
ln -s "$symlink_target_dir" "$symlink_output_dir"
assert_fails "$symlink_output_log" bash "$SCRIPT" \
    --sample-id sample_symlink \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$symlink_output_dir" \
    --threads 1 \
    --execute
assert_contains "$symlink_output_log" "must not be a symbolic link"
assert_contains "$symlink_target_dir/marker.txt" "preserve operator data"
[[ "$(find "$symlink_target_dir" -mindepth 1 -maxdepth 1 | wc -l | tr -d ' ')" == "1" ]] \
    || fail "symlink target was modified"

printf 'Running paired gzip dry-run check...\n'
gzip_output="$tmp_dir/gzip.out"
bash "$SCRIPT" \
    --sample-id sample_gz \
    --r1-fastq "$r1_gz" \
    --r2-fastq "$r2_gz" \
    --star-index "$star_index" \
    --output-dir "$tmp_dir/results/gzip" \
    --threads 1 \
    >"$gzip_output"

assert_contains "$gzip_output" "--readFilesCommand"
assert_contains "$gzip_output" "gunzip"
assert_contains "$gzip_output" "-c"

printf 'Running mixed compression failure check...\n'
mixed_output="$tmp_dir/mixed.out"
assert_fails "$mixed_output" bash "$SCRIPT" \
    --sample-id sample_mixed \
    --r1-fastq "$r1_gz" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$tmp_dir/results/mixed" \
    --threads 1
assert_contains "$mixed_output" "Mixed FASTQ compression is not supported"

printf 'Running invalid threads failure check...\n'
threads_output="$tmp_dir/threads.out"
assert_fails "$threads_output" bash "$SCRIPT" \
    --sample-id sample_bad_threads \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$tmp_dir/results/bad_threads" \
    --threads 0
assert_contains "$threads_output" "--threads must be a positive integer"

printf 'Running missing argument failure check...\n'
missing_arg_output="$tmp_dir/missing_arg.out"
assert_fails "$missing_arg_output" bash "$SCRIPT" \
    --sample-id sample_missing \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --threads 1
assert_contains "$missing_arg_output" "Missing required argument: --output-dir"

printf 'Running missing FASTQ failure check...\n'
missing_fastq_output="$tmp_dir/missing_fastq.out"
assert_fails "$missing_fastq_output" bash "$SCRIPT" \
    --sample-id sample_missing_fastq \
    --r1-fastq "$fixture_dir/missing_R1.fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$tmp_dir/results/missing_fastq" \
    --threads 1
assert_contains "$missing_fastq_output" "R1 FASTQ does not exist"

printf 'All step_01 STAR alignment smoke tests passed.\n'
