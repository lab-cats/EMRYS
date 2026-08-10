#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/src/norad/evidence/canonical_bam_qc/step_02b_bam_qc.sh"

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

assert_file_equals() {
    local file="$1"
    local expected="$2"
    local expected_file="$tmp_dir/expected-file.txt"

    printf '%s' "$expected" >"$expected_file"
    if ! cmp -s "$expected_file" "$file"; then
        printf 'Expected exact content:\n' >&2
        cat "$expected_file" >&2
        printf 'Actual exact content:\n' >&2
        cat "$file" >&2
        fail "unexpected file content: $file"
    fi
}

assert_only_entries() {
    local directory="$1"
    shift
    local path
    local expected
    local matched
    local actual_count=0

    while IFS= read -r path; do
        actual_count=$((actual_count + 1))
        matched=false
        for expected in "$@"; do
            if [[ "${path##*/}" == "$expected" ]]; then
                matched=true
                break
            fi
        done
        [[ "$matched" == true ]] || fail "unexpected entry in $directory: $path"
    done < <(find "$directory" -mindepth 1 -maxdepth 1 -print)

    [[ "$actual_count" -eq "$#" ]] ||
        fail "expected $# entries in $directory; found $actual_count"
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

fake_bin="$tmp_dir/bin"
mkdir -p "$fake_bin"

samtools_log="$tmp_dir/samtools_invocations.log"
cat >"$fake_bin/samtools" <<EOF_SAMTOOLS
#!/usr/bin/env bash
set -euo pipefail

printf 'samtools invoked\n' >> "$samtools_log"
printf '%s\n' "\$@" >> "$samtools_log"

subcommand="\${1:-}"
shift || true

case "\$subcommand" in
    quickcheck)
        mode="\${FAKE_QUICKCHECK_MODE:-empty_success}"
        case "\$mode" in
            empty_success)
                exit 0
                ;;
            output_success)
                printf 'quickcheck success output\\n'
                exit 0
                ;;
            fail)
                printf 'quickcheck failure output\\n' >&2
                exit 42
                ;;
            *)
                printf 'unknown FAKE_QUICKCHECK_MODE: %s\\n' "\$mode" >&2
                exit 64
                ;;
        esac
        ;;
    flagstat)
        mode="\${FAKE_FLAGSTAT_MODE:-success}"
        case "\$mode" in
            success)
                printf '10 + 0 in total (QC-passed reads + QC-failed reads)\\n'
                printf '8 + 0 mapped (80.00%% : N/A)\\n'
                ;;
            partial_fail)
                printf 'partial flagstat output\\n'
                printf 'flagstat failure diagnostic\\n' >&2
                exit 43
                ;;
            *)
                printf 'unknown FAKE_FLAGSTAT_MODE: %s\\n' "\$mode" >&2
                exit 64
                ;;
        esac
        ;;
    *)
        printf 'fake samtools unknown subcommand: %s\\n' "\$subcommand" >&2
        exit 64
        ;;
esac
EOF_SAMTOOLS
chmod +x "$fake_bin/samtools"

export PATH="$fake_bin:$PATH"
unset FAKE_QUICKCHECK_MODE FAKE_FLAGSTAT_MODE

fixture_dir="$tmp_dir/fixtures"
mkdir -p "$fixture_dir"

bam="$fixture_dir/sample.sorted.bam"
bam_dot_bai="$bam.bai"
bam_stem_bai="${bam%.bam}.bai"
missing_bam="$fixture_dir/missing.sorted.bam"

printf 'placeholder bam\n' >"$bam"

printf 'Running syntax check...\n'
bash -n "$SCRIPT"

printf 'Running help check...\n'
help_output="$tmp_dir/help.out"
bash "$SCRIPT" --help >"$help_output"
assert_contains "$help_output" "Usage:"
assert_contains "$help_output" "--sample-id"
assert_contains "$help_output" "--bam"
assert_contains "$help_output" "--output-dir"
assert_contains "$help_output" "--execute"

printf 'Running missing argument failure check...\n'
missing_arg_output="$tmp_dir/missing_arg.out"
assert_fails "$missing_arg_output" bash "$SCRIPT" \
    --sample-id sample_missing \
    --bam "$bam"
assert_contains "$missing_arg_output" "Missing required argument: --output-dir"

printf 'Running missing BAM failure check...\n'
missing_bam_output="$tmp_dir/missing_bam.out"
assert_fails "$missing_bam_output" bash "$SCRIPT" \
    --sample-id sample_missing_bam \
    --bam "$missing_bam" \
    --output-dir "$tmp_dir/results/missing_bam"
assert_contains "$missing_bam_output" "BAM does not exist"

printf 'Running missing BAM index failure check...\n'
missing_index_output="$tmp_dir/missing_index.out"
assert_fails "$missing_index_output" bash "$SCRIPT" \
    --sample-id sample_missing_index \
    --bam "$bam" \
    --output-dir "$tmp_dir/results/missing_index"
assert_contains "$missing_index_output" "BAM index does not exist"

printf 'Running dry-run check with BAM.bai index...\n'
printf 'placeholder index\n' >"$bam_dot_bai"
dry_output="$tmp_dir/dry.out"
dry_output_dir="$tmp_dir/results/dry"
bash "$SCRIPT" \
    --sample-id sample_dry \
    --bam "$bam" \
    --output-dir "$dry_output_dir" \
    >"$dry_output"

[[ -d "$dry_output_dir" ]] || fail "dry-run did not create output directory"
[[ ! -e "$samtools_log" ]] || fail "dry-run invoked samtools"
assert_contains "$dry_output" "Mode: dry-run"
assert_contains "$dry_output" "BAM index found: $bam_dot_bai"
assert_contains "$dry_output" "Quickcheck output: $dry_output_dir/sample_dry.quickcheck.txt"
assert_contains "$dry_output" "Flagstat output: $dry_output_dir/sample_dry.flagstat.txt"
assert_contains "$dry_output" "quickcheck"
assert_contains "$dry_output" "-v"
assert_contains "$dry_output" "$bam"
assert_contains "$dry_output" "flagstat"
assert_contains "$dry_output" "Dry-run only"

printf 'Running dry-run check with stem .bai index...\n'
rm "$bam_dot_bai"
printf 'placeholder stem index\n' >"$bam_stem_bai"
stem_index_output="$tmp_dir/stem_index.out"
bash "$SCRIPT" \
    --sample-id sample_stem_index \
    --bam "$bam" \
    --output-dir "$tmp_dir/results/stem_index" \
    >"$stem_index_output"
assert_contains "$stem_index_output" "BAM index found: $bam_stem_bai"

printf 'Running PATH-only missing samtools failure check...\n'
empty_bin="$tmp_dir/empty-bin"
mkdir -p "$empty_bin"
missing_samtools_output="$tmp_dir/missing_samtools.out"
missing_samtools_output_dir="$tmp_dir/results/missing_samtools"
assert_fails "$missing_samtools_output" /usr/bin/env PATH="$empty_bin" /bin/bash "$SCRIPT" \
    --sample-id sample_missing_samtools \
    --bam "$bam" \
    --output-dir "$missing_samtools_output_dir"
assert_contains "$missing_samtools_output" "samtools executable was not found on PATH"
[[ ! -e "$missing_samtools_output_dir" ]] ||
    fail "missing-samtools failure created the output directory"

printf 'Running execute check with empty quickcheck success...\n'
execute_output="$tmp_dir/execute.out"
execute_output_dir="$tmp_dir/results/execute"
bash "$SCRIPT" \
    --sample-id sample_execute \
    --bam "$bam" \
    --output-dir "$execute_output_dir" \
    --execute \
    >"$execute_output"

quickcheck_out="$execute_output_dir/sample_execute.quickcheck.txt"
flagstat_out="$execute_output_dir/sample_execute.flagstat.txt"
[[ -f "$quickcheck_out" ]] || fail "execute did not create quickcheck output"
[[ -f "$flagstat_out" ]] || fail "execute did not create flagstat output"
assert_contains "$quickcheck_out" "PASS: samtools quickcheck completed with no errors."
assert_contains "$flagstat_out" "10 + 0 in total"
assert_contains "$flagstat_out" "8 + 0 mapped"
assert_contains "$samtools_log" "quickcheck"
assert_contains "$samtools_log" "-v"
assert_contains "$samtools_log" "$bam"
assert_contains "$samtools_log" "flagstat"
assert_contains "$execute_output" "samtools flagstat output:"
assert_contains "$execute_output" "10 + 0 in total"

printf 'Running execute check with non-empty quickcheck success...\n'
nonempty_output="$tmp_dir/nonempty.out"
nonempty_output_dir="$tmp_dir/results/nonempty"
FAKE_QUICKCHECK_MODE=output_success bash "$SCRIPT" \
    --sample-id sample_nonempty \
    --bam "$bam" \
    --output-dir "$nonempty_output_dir" \
    --execute \
    >"$nonempty_output"

nonempty_quickcheck_out="$nonempty_output_dir/sample_nonempty.quickcheck.txt"
assert_contains "$nonempty_quickcheck_out" "quickcheck success output"
assert_not_contains "$nonempty_quickcheck_out" "PASS: samtools quickcheck completed with no errors."

printf 'Running predecessor-bearing quickcheck failure preservation check...\n'
failure_stdout="$tmp_dir/failure.stdout"
failure_stderr="$tmp_dir/failure.stderr"
failure_output_dir="$tmp_dir/results/failure"
mkdir -p "$failure_output_dir"
failure_quickcheck_out="$failure_output_dir/sample_failure.quickcheck.txt"
failure_flagstat_out="$failure_output_dir/sample_failure.flagstat.txt"
failure_unrelated="$failure_output_dir/unrelated.txt"
printf 'prior quickcheck\n' >"$failure_quickcheck_out"
printf 'prior flagstat\n' >"$failure_flagstat_out"
printf 'unrelated predecessor\n' >"$failure_unrelated"

set +e
FAKE_QUICKCHECK_MODE=fail bash "$SCRIPT" \
    --sample-id sample_failure \
    --bam "$bam" \
    --output-dir "$failure_output_dir" \
    --execute \
    >"$failure_stdout" 2>"$failure_stderr"
failure_status=$?
set -e

[[ "$failure_status" -eq 1 ]] ||
    fail "quickcheck child exit 42 did not become producer exit 1: $failure_status"
[[ -f "$failure_quickcheck_out" ]] || fail "quickcheck failure did not preserve quickcheck output"
assert_file_equals "$failure_quickcheck_out" $'quickcheck failure output\n'
assert_file_equals "$failure_flagstat_out" $'prior flagstat\n'
assert_file_equals "$failure_unrelated" $'unrelated predecessor\n'
assert_contains "$failure_stderr" "samtools quickcheck failed"
assert_not_contains "$failure_stderr" "quickcheck failure output"
assert_only_entries "$failure_output_dir" \
    "sample_failure.quickcheck.txt" \
    "sample_failure.flagstat.txt" \
    "unrelated.txt"

printf 'Running predecessor-bearing flagstat failure preservation check...\n'
flag_failure_stdout="$tmp_dir/flag_failure.stdout"
flag_failure_stderr="$tmp_dir/flag_failure.stderr"
flag_failure_output_dir="$tmp_dir/results/flag_failure"
mkdir -p "$flag_failure_output_dir"
flag_failure_quickcheck_out="$flag_failure_output_dir/sample_flag_failure.quickcheck.txt"
flag_failure_flagstat_out="$flag_failure_output_dir/sample_flag_failure.flagstat.txt"
flag_failure_unrelated="$flag_failure_output_dir/unrelated.txt"
printf 'prior quickcheck\n' >"$flag_failure_quickcheck_out"
printf 'prior flagstat\n' >"$flag_failure_flagstat_out"
printf 'unrelated predecessor\n' >"$flag_failure_unrelated"

set +e
FAKE_FLAGSTAT_MODE=partial_fail bash "$SCRIPT" \
    --sample-id sample_flag_failure \
    --bam "$bam" \
    --output-dir "$flag_failure_output_dir" \
    --execute \
    >"$flag_failure_stdout" 2>"$flag_failure_stderr"
flag_failure_status=$?
set -e

[[ "$flag_failure_status" -eq 43 ]] ||
    fail "flagstat child exit 43 was not propagated: $flag_failure_status"
assert_file_equals "$flag_failure_quickcheck_out" \
    $'PASS: samtools quickcheck completed with no errors.\n'
assert_file_equals "$flag_failure_flagstat_out" $'partial flagstat output\n'
assert_file_equals "$flag_failure_unrelated" $'unrelated predecessor\n'
assert_file_equals "$flag_failure_stderr" $'flagstat failure diagnostic\n'
assert_only_entries "$flag_failure_output_dir" \
    "sample_flag_failure.quickcheck.txt" \
    "sample_flag_failure.flagstat.txt" \
    "unrelated.txt"

printf 'All step_02b BAM QC smoke tests passed.\n'
