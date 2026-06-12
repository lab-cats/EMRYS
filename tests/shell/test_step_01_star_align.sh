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

assert_fails() {
    local output_file="$1"
    shift

    if "$@" >"$output_file" 2>&1; then
        cat "$output_file" >&2
        fail "command unexpectedly succeeded: $*"
    fi
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

fake_bin="$tmp_dir/bin"
mkdir -p "$fake_bin"

star_log="$tmp_dir/star_invocations.log"
cat >"$fake_bin/STAR" <<EOF_STAR
#!/usr/bin/env bash
printf 'STAR invoked\n' >> "$star_log"
printf '%s\n' "\$@" >> "$star_log"
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

[[ -d "$dry_output_dir" ]] || fail "dry-run did not create output directory"
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
assert_contains "$star_log" "$execute_output_dir/sample_002."
assert_contains "$star_log" "--outSAMtype"
assert_contains "$star_log" "BAM"
assert_contains "$star_log" "SortedByCoordinate"
assert_contains "$execute_output" "Mode: execute"

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
