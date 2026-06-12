#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/step_02_sort_index_bam.sh"

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

samtools_log="$tmp_dir/samtools_invocations.log"
cat >"$fake_bin/samtools" <<EOF_SAMTOOLS
#!/usr/bin/env bash
set -euo pipefail

printf 'samtools invoked\n' >> "$samtools_log"
printf '%s\n' "\$@" >> "$samtools_log"

subcommand="\${1:-}"
shift || true

case "\$subcommand" in
    sort)
        output_bam=""
        while [[ \$# -gt 0 ]]; do
            case "\$1" in
                -o)
                    output_bam="\${2:-}"
                    shift 2
                    ;;
                -@)
                    shift 2
                    ;;
                *)
                    shift
                    ;;
            esac
        done

        if [[ -z "\$output_bam" ]]; then
            printf 'fake samtools sort missing -o output\n' >&2
            exit 64
        fi

        mkdir -p "\$(dirname "\$output_bam")"
        printf 'fake sorted bam\n' > "\$output_bam"
        ;;
    index)
        input_bam="\${1:-}"
        if [[ -z "\$input_bam" ]]; then
            printf 'fake samtools index missing input BAM\n' >&2
            exit 64
        fi
        printf 'fake bam index\n' > "\$input_bam.bai"
        ;;
    *)
        printf 'fake samtools unknown subcommand: %s\n' "\$subcommand" >&2
        exit 64
        ;;
esac
EOF_SAMTOOLS
chmod +x "$fake_bin/samtools"

export PATH="$fake_bin:$PATH"

fixture_dir="$tmp_dir/fixtures"
mkdir -p "$fixture_dir"

input_sam="$fixture_dir/sample.sam"
input_bam="$fixture_dir/sample.bam"

printf '@HD\tVN:1.6\tSO:unknown\n' >"$input_sam"
printf 'placeholder bam\n' >"$input_bam"

printf 'Running syntax check...\n'
bash -n "$SCRIPT"

printf 'Running help check...\n'
help_output="$tmp_dir/help.out"
bash "$SCRIPT" --help >"$help_output"
assert_contains "$help_output" "Usage:"
assert_contains "$help_output" "--sample-id"
assert_contains "$help_output" "--input-alignment"
assert_contains "$help_output" "--output-dir"
assert_contains "$help_output" "--threads"
assert_contains "$help_output" "--execute"

printf 'Running missing argument failure check...\n'
missing_arg_output="$tmp_dir/missing_arg.out"
assert_fails "$missing_arg_output" bash "$SCRIPT" \
    --sample-id sample_missing \
    --input-alignment "$input_sam" \
    --threads 1
assert_contains "$missing_arg_output" "Missing required argument: --output-dir"

printf 'Running missing input alignment failure check...\n'
missing_input_output="$tmp_dir/missing_input.out"
assert_fails "$missing_input_output" bash "$SCRIPT" \
    --sample-id sample_missing_input \
    --input-alignment "$fixture_dir/missing.sam" \
    --output-dir "$tmp_dir/results/missing_input" \
    --threads 1
assert_contains "$missing_input_output" "Input alignment does not exist"

printf 'Running invalid threads failure check...\n'
threads_output="$tmp_dir/threads.out"
assert_fails "$threads_output" bash "$SCRIPT" \
    --sample-id sample_bad_threads \
    --input-alignment "$input_sam" \
    --output-dir "$tmp_dir/results/bad_threads" \
    --threads 0
assert_contains "$threads_output" "--threads must be a positive integer"

printf 'Running SAM dry-run check...\n'
dry_output="$tmp_dir/dry.out"
dry_output_dir="$tmp_dir/results/dry"
bash "$SCRIPT" \
    --sample-id sample_dry \
    --input-alignment "$input_sam" \
    --output-dir "$dry_output_dir" \
    --threads 4 \
    >"$dry_output"

dry_bam="$dry_output_dir/sample_dry.sorted.bam"
[[ -d "$dry_output_dir" ]] || fail "dry-run did not create output directory"
[[ ! -e "$samtools_log" ]] || fail "dry-run invoked samtools"
assert_contains "$dry_output" "Mode: dry-run"
assert_contains "$dry_output" "samtools"
assert_contains "$dry_output" "sort"
assert_contains "$dry_output" "-@"
assert_contains "$dry_output" "4"
assert_contains "$dry_output" "-o"
assert_contains "$dry_output" "$dry_bam"
assert_contains "$dry_output" "$input_sam"
assert_contains "$dry_output" "index"
assert_contains "$dry_output" "Dry-run only"
assert_not_contains "$dry_output" "--execute --execute"

printf 'Running SAM execute check...\n'
execute_sam_output="$tmp_dir/execute_sam.out"
execute_sam_output_dir="$tmp_dir/results/execute_sam"
bash "$SCRIPT" \
    --sample-id sample_sam \
    --input-alignment "$input_sam" \
    --output-dir "$execute_sam_output_dir" \
    --threads 2 \
    --execute \
    >"$execute_sam_output"

execute_sam_bam="$execute_sam_output_dir/sample_sam.sorted.bam"
[[ -d "$execute_sam_output_dir" ]] || fail "SAM execute did not create output directory"
[[ -f "$execute_sam_bam" ]] || fail "SAM execute did not create sorted BAM"
[[ -f "$execute_sam_bam.bai" ]] || fail "SAM execute did not create BAM index"
assert_contains "$samtools_log" "samtools invoked"
assert_contains "$samtools_log" "sort"
assert_contains "$samtools_log" "-@"
assert_contains "$samtools_log" "2"
assert_contains "$samtools_log" "-o"
assert_contains "$samtools_log" "$execute_sam_bam"
assert_contains "$samtools_log" "$input_sam"
assert_contains "$samtools_log" "index"
assert_contains "$execute_sam_output" "Mode: execute"

printf 'Running BAM execute check...\n'
execute_bam_output="$tmp_dir/execute_bam.out"
execute_bam_output_dir="$tmp_dir/results/execute_bam"
bash "$SCRIPT" \
    --sample-id sample_bam \
    --input-alignment "$input_bam" \
    --output-dir "$execute_bam_output_dir" \
    --threads 3 \
    --execute \
    >"$execute_bam_output"

execute_bam="$execute_bam_output_dir/sample_bam.sorted.bam"
[[ -d "$execute_bam_output_dir" ]] || fail "BAM execute did not create output directory"
[[ -f "$execute_bam" ]] || fail "BAM execute did not create sorted BAM"
[[ -f "$execute_bam.bai" ]] || fail "BAM execute did not create BAM index"
assert_contains "$samtools_log" "3"
assert_contains "$samtools_log" "$execute_bam"
assert_contains "$samtools_log" "$input_bam"
assert_contains "$execute_bam_output" "Mode: execute"

printf 'All step_02 samtools sort/index smoke tests passed.\n'
