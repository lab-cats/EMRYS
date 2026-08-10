#!/usr/bin/env bash
# Smoke tests for Step 06 command construction, side-effect-free dry-runs,
# cleanup, and rollback using a fake local samtools executable.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/src/norad/stages/mechanical_orientation/step_06_split_bam_by_read_orientation.sh"
JOB="$REPO_ROOT/src/norad/stages/mechanical_orientation/step_06_split_bam_by_read_orientation.slurm"

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
        printf 'Unexpectedly found: %s\n' "$unexpected" >&2
        printf 'Actual output:\n' >&2
        cat "$file" >&2
        fail "unexpected output"
    fi
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

assert_exits() {
    local expected_status="$1"
    local output_file="$2"
    local status
    shift 2

    set +e
    "$@" >"$output_file" 2>&1
    status=$?
    set -e
    [[ "$status" -eq "$expected_status" ]] || {
        cat "$output_file" >&2
        fail "expected exit $expected_status, got $status: $*"
    }
}

assert_file_equals() {
    local path="$1"
    local expected="$2"
    local actual

    [[ -f "$path" ]] || fail "file does not exist: $path"
    actual="$(cat "$path")"
    [[ "$actual" == "$expected" ]] || fail "unexpected contents for $path: $actual"
}

assert_line_before() {
    local file="$1"
    local first="$2"
    local second="$3"
    local first_line
    local second_line

    first_line="$(grep -nF -- "$first" "$file" | head -n 1 | cut -d: -f1)"
    second_line="$(grep -nF -- "$second" "$file" | head -n 1 | cut -d: -f1)"
    [[ -n "$first_line" ]] || fail "missing ordered line: $first"
    [[ -n "$second_line" ]] || fail "missing ordered line: $second"
    [[ "$first_line" -lt "$second_line" ]] || fail "expected '$first' before '$second' in $file"
}

assert_no_step06_scratch() {
    local output_dir="$1"
    local qc_dir="$2"

    # Foreign locks are intentionally preserved by failure tests; owned temp and
    # backup files should still be gone after every failed or successful run.
    if [[ -d "$output_dir" ]] && find "$output_dir" -name '*.step06.*' ! -name '*.step06.lock' -print | grep -q .; then
        find "$output_dir" -name '*.step06.*' ! -name '*.step06.lock' -print >&2
        fail "Step 06 scratch files remain in $output_dir"
    fi

    if [[ -d "$qc_dir" ]] && find "$qc_dir" -name '*.step06.*' -print | grep -q .; then
        find "$qc_dir" -name '*.step06.*' -print >&2
        fail "Step 06 scratch files remain in $qc_dir"
    fi
}

assert_no_step06_final_set() {
    local sample="$1"
    local output_dir="$2"
    local qc_dir="$3"

    assert_not_exists "$output_dir/${sample}.FWD_like.bam"
    assert_not_exists "$output_dir/${sample}.FWD_like.bam.bai"
    assert_not_exists "$output_dir/${sample}.REV_like.bam"
    assert_not_exists "$output_dir/${sample}.REV_like.bam.bai"
    assert_not_exists "$qc_dir/${sample}.orientation_counts.tsv"
}

assert_no_step06_attempt_marker() {
    local output_dir="$1"
    local qc_dir="$2"
    local dir

    for dir in "$output_dir" "$qc_dir"; do
        if [[ -d "$dir" ]] && find "$dir" \( -iname '*receipt*' -o -iname '*recovery*' \) -print | grep -q .; then
            find "$dir" \( -iname '*receipt*' -o -iname '*recovery*' \) -print >&2
            fail "Step 06 receipt or recovery marker remains in $dir"
        fi
    done
}

prepare_child_failure_dirs() {
    local output_dir="$1"
    local qc_dir="$2"

    mkdir -p "$output_dir" "$qc_dir"
    printf 'unrelated output bytes\n' >"$output_dir/unrelated.txt"
    printf 'unrelated qc bytes\n' >"$qc_dir/unrelated.txt"
}

assert_child_failure_state() {
    local output_dir="$1"
    local qc_dir="$2"

    assert_no_step06_final_set ABE_EV_2 "$output_dir" "$qc_dir"
    assert_not_exists "$output_dir/.ABE_EV_2.step06.lock"
    assert_file_equals "$output_dir/unrelated.txt" "unrelated output bytes"
    assert_file_equals "$qc_dir/unrelated.txt" "unrelated qc bytes"
    assert_no_step06_scratch "$output_dir" "$qc_dir"
    assert_no_step06_attempt_marker "$output_dir" "$qc_dir"
}

write_input_bam_pair() {
    local bam="$1"

    mkdir -p "$(dirname "$bam")"
    {
        printf 'INPUT_BAM\n'
        printf 'COUNT:%s\n' "${FAKE_INPUT_COUNT:-20}"
    } >"$bam"
    printf 'fake step05 split-n-cigar bai\n' >"$bam.bai"
}

run_step06() {
    local sample="$1"
    local input_bam="$2"
    local output_dir="$3"
    local qc_dir="$4"
    shift 4

    bash "$SCRIPT" \
        --sample-id "$sample" \
        --input-bam "$input_bam" \
        --output-dir "$output_dir" \
        --qc-dir "$qc_dir" \
        --threads 2 \
        --samtools-bin "$fake_bin/samtools" \
        "$@"
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

fake_bin="$tmp_dir/bin"
mkdir -p "$fake_bin"

samtools_log="$tmp_dir/samtools_invocations.log"
mv_log="$tmp_dir/mv_invocations.log"

# Fake samtools stores tiny text BAM stand-ins with COUNT metadata. That lets
# the tests validate command shape, counts math, quickcheck paths, and rollback
# without real BAM fixtures or cluster tools.
cat >"$fake_bin/samtools" <<EOF_SAMTOOLS
#!/usr/bin/env bash
set -euo pipefail

printf 'samtools invoked\\n' >> "$samtools_log"
printf '%s\\n' "\$*" >> "$samtools_log"

count_for_flag() {
    case "\$1" in
        99) printf '%s\\n' "\${FAKE_FLAG_99_COUNT:-5}" ;;
        147) printf '%s\\n' "\${FAKE_FLAG_147_COUNT:-6}" ;;
        83) printf '%s\\n' "\${FAKE_FLAG_83_COUNT:-4}" ;;
        163) printf '%s\\n' "\${FAKE_FLAG_163_COUNT:-3}" ;;
        *) printf 'fake samtools unsupported flag count: %s\\n' "\$1" >&2; exit 64 ;;
    esac
}

write_filtered_bam() {
    local flag="\$1"
    local input_bam="\$2"
    local output_bam="\$3"
    local count

    if [[ "\$flag" == "99" && "\${FAKE_MUTATE_ADMITTED_INPUTS:-0}" == "1" ]]; then
        printf 'mutated input bam\\n' >> "\$input_bam"
        printf 'mutated input bai\\n' >> "\$input_bam.bai"
    fi

    if [[ "\$flag" == "99" && "\${FAKE_FILTER_TERM_PARENT:-0}" == "1" ]]; then
        kill -TERM "\$PPID"
        kill -TERM "\$\$"
    fi

    if [[ -n "\${FAKE_FILTER_FAIL_FLAG:-}" && "\$flag" == "\$FAKE_FILTER_FAIL_FLAG" ]]; then
        printf 'fake samtools view -b forced failure for flag %s\\n' "\$flag" >&2
        exit "\${FAKE_FILTER_FAIL_STATUS:-71}"
    fi

    count="\$(count_for_flag "\$flag")"
    {
        printf 'FILTER_FLAG:%s\\n' "\$flag"
        printf 'COUNT:%s\\n' "\$count"
        printf 'INPUT:%s\\n' "\$input_bam"
    } > "\$output_bam"
}

count_bam() {
    local bam="\$1"

    if grep -q '^COUNT:' "\$bam"; then
        grep '^COUNT:' "\$bam" | head -n 1 | cut -d: -f2
    else
        printf '%s\\n' "\${FAKE_INPUT_COUNT:-20}"
    fi
}

subcommand="\${1:-}"
shift || true

case "\$subcommand" in
    --version)
        printf 'samtools 1.19.2\\n'
        ;;
    view)
        count_mode=false
        bam_mode=false
        flag=""
        output_bam=""
        input_bam=""

        while [[ \$# -gt 0 ]]; do
            case "\$1" in
                -@)
                    shift 2
                    ;;
                -c)
                    count_mode=true
                    shift
                    ;;
                -b)
                    bam_mode=true
                    shift
                    ;;
                -f)
                    flag="\${2:-}"
                    shift 2
                    ;;
                -o)
                    output_bam="\${2:-}"
                    shift 2
                    ;;
                *)
                    input_bam="\$1"
                    shift
                    ;;
            esac
        done

        [[ -n "\$input_bam" ]] || { printf 'fake samtools view missing input BAM\\n' >&2; exit 64; }

        if [[ "\$count_mode" == true ]]; then
            if [[ -n "\${FAKE_COUNT_FAIL_MATCH:-}" && "\$input_bam" == *"\$FAKE_COUNT_FAIL_MATCH"* ]]; then
                printf 'fake samtools count forced failure for %s\\n' "\$input_bam" >&2
                exit "\${FAKE_COUNT_FAIL_STATUS:-74}"
            fi
            if [[ -n "\$flag" ]]; then
                count_for_flag "\$flag"
            else
                count_bam "\$input_bam"
            fi
        elif [[ "\$bam_mode" == true ]]; then
            [[ -n "\$flag" ]] || { printf 'fake samtools view -b missing -f flag\\n' >&2; exit 64; }
            [[ -n "\$output_bam" ]] || { printf 'fake samtools view -b missing -o output\\n' >&2; exit 64; }
            write_filtered_bam "\$flag" "\$input_bam" "\$output_bam"
        else
            printf 'fake samtools view unsupported arguments\\n' >&2
            exit 64
        fi
        ;;
    merge)
        output_bam=""
        inputs=()

        while [[ \$# -gt 0 ]]; do
            case "\$1" in
                -@)
                    shift 2
                    ;;
                -o)
                    output_bam="\${2:-}"
                    shift 2
                    ;;
                *)
                    inputs+=("\$1")
                    shift
                    ;;
            esac
        done

        [[ -n "\$output_bam" ]] || { printf 'fake samtools merge missing -o output\\n' >&2; exit 64; }
        [[ "\${#inputs[@]}" -eq 2 ]] || { printf 'fake samtools merge expected two inputs\\n' >&2; exit 64; }

        if [[ -n "\${FAKE_MERGE_FAIL_MATCH:-}" && "\$output_bam" == *"\$FAKE_MERGE_FAIL_MATCH"* ]]; then
            printf 'fake samtools merge forced failure for %s\\n' "\$output_bam" >&2
            exit "\${FAKE_MERGE_FAIL_STATUS:-72}"
        fi

        total=0
        for input in "\${inputs[@]}"; do
            [[ -s "\$input" ]] || { printf 'fake samtools merge input missing or empty: %s\\n' "\$input" >&2; exit 64; }
            count="\$(count_bam "\$input")"
            total=\$((total + count))
        done

        if [[ -n "\${FAKE_ZERO_MERGE_MATCH:-}" && "\$output_bam" == *"\$FAKE_ZERO_MERGE_MATCH"* ]]; then
            total=0
        fi

        if [[ -n "\${FAKE_MERGE_COUNT_MATCH:-}" && "\$output_bam" == *"\$FAKE_MERGE_COUNT_MATCH"* ]]; then
            total="\${FAKE_MERGE_COUNT:-\$total}"
        fi

        {
            printf 'MERGED:%s %s\\n' "\${inputs[0]}" "\${inputs[1]}"
            printf 'COUNT:%s\\n' "\$total"
        } > "\$output_bam"
        ;;
    index)
        input_bam="\${1:-}"
        [[ -n "\$input_bam" ]] || { printf 'fake samtools index missing BAM\\n' >&2; exit 64; }
        if [[ -n "\${FAKE_INDEX_FAIL_MATCH:-}" && "\$input_bam" == *"\$FAKE_INDEX_FAIL_MATCH"* ]]; then
            printf 'fake samtools index forced failure for %s\\n' "\$input_bam" >&2
            exit "\${FAKE_INDEX_FAIL_STATUS:-73}"
        fi
        if [[ -n "\${FAKE_INDEX_EMPTY_MATCH:-}" && "\$input_bam" == *"\$FAKE_INDEX_EMPTY_MATCH"* ]]; then
            : > "\$input_bam.bai"
        else
            printf 'fake bam index for %s\\n' "\$input_bam" > "\$input_bam.bai"
        fi
        ;;
    quickcheck)
        input_bam="\${1:-}"
        [[ -n "\$input_bam" ]] || { printf 'fake samtools quickcheck missing BAM\\n' >&2; exit 64; }
        if [[ -n "\${FAKE_FINAL_QUICKCHECK_FAIL_PATH:-}" && "\$input_bam" == "\$FAKE_FINAL_QUICKCHECK_FAIL_PATH" ]]; then
            printf 'fake final-path quickcheck forced failure for %s\\n' "\$input_bam" >&2
            exit 66
        fi
        if [[ -n "\${FAKE_QUICKCHECK_FAIL_MATCH:-}" && "\$input_bam" == *"\$FAKE_QUICKCHECK_FAIL_MATCH"* ]]; then
            printf 'fake quickcheck forced failure for %s\\n' "\$input_bam" >&2
            exit 66
        fi
        [[ -s "\$input_bam" ]]
        ;;
    *)
        printf 'fake samtools unknown subcommand: %s\\n' "\$subcommand" >&2
        exit 64
        ;;
esac
EOF_SAMTOOLS
chmod +x "$fake_bin/samtools"

cat >"$fake_bin/mv" <<EOF_MV
#!/usr/bin/env bash
set -euo pipefail

printf 'mv invoked\\n' >> "$mv_log"
printf '%s\\n' "\$*" >> "$mv_log"

dest=""
for arg in "\$@"; do
    dest="\$arg"
done

source="\${1:-}"

if [[ -n "\${FAKE_MV_BARRIER_DIR:-}" && "\$source" == *.FWD_like.tmp.bam && "\$dest" == *.FWD_like.bam ]]; then
    mkdir -p "\$FAKE_MV_BARRIER_DIR"
    : > "\$FAKE_MV_BARRIER_DIR/\${SLURM_JOB_ID:-\$\$}.ready"
    barrier_attempt=0
    while true; do
        ready_count="\$(find "\$FAKE_MV_BARRIER_DIR" -type f -name '*.ready' -print | wc -l | tr -d ' ')"
        [[ "\$ready_count" -ge 2 ]] && break
        barrier_attempt=\$((barrier_attempt + 1))
        if [[ "\$barrier_attempt" -ge 1000 ]]; then
            printf 'fake mv barrier timed out\\n' >&2
            exit 69
        fi
        sleep 0.01
    done
    if [[ "\${FAKE_MV_BARRIER_DELAY:-0}" != "0" ]]; then
        sleep "\$FAKE_MV_BARRIER_DELAY"
    fi
    if [[ -n "\${FAKE_MV_BARRIER_WAIT_FOR_FILE:-}" ]]; then
        barrier_attempt=0
        while [[ ! -e "\$FAKE_MV_BARRIER_WAIT_FOR_FILE" ]]; do
            barrier_attempt=\$((barrier_attempt + 1))
            if [[ "\$barrier_attempt" -ge 1000 ]]; then
                printf 'fake mv completion wait timed out\\n' >&2
                exit 69
            fi
            sleep 0.01
        done
    fi
fi

fail_marker="\${FAKE_MV_FAIL_MARKER:-$tmp_dir/fake_mv_failed_once}"
# Force only the first matching publish move to fail so rollback moves can still
# restore the previous final output set.
if [[ -n "\${FAKE_MV_FAIL_ONCE_DEST_MATCH:-}" && "\$dest" == *"\$FAKE_MV_FAIL_ONCE_DEST_MATCH"* && ! -e "\$fail_marker" ]]; then
    : > "\$fail_marker"
    printf 'fake mv forced failure for destination: %s\\n' "\$dest" >&2
    exit 67
fi

if [[ -n "\${FAKE_MV_RESTORE_FAIL_SOURCE:-}" && "\$source" == "\$FAKE_MV_RESTORE_FAIL_SOURCE" ]]; then
    printf 'fake mv forced restore failure for source: %s\\n' "\$source" >&2
    exit "\${FAKE_MV_RESTORE_FAIL_STATUS:-68}"
fi

/bin/mv "\$@"
if [[ -n "\${FAKE_MV_COMPLETE_MARKER:-}" && "\$dest" == *.orientation_counts.tsv ]]; then
    : > "\$FAKE_MV_COMPLETE_MARKER"
fi
EOF_MV
chmod +x "$fake_bin/mv"

export PATH="$fake_bin:$PATH"

fixture_dir="$tmp_dir/fixtures"
input_bam="$fixture_dir/split_ncigar/ABE_EV_2/ABE_EV_2.split_ncigar.bam"
write_input_bam_pair "$input_bam"

printf 'Running syntax checks...\n'
bash -n "$SCRIPT"
bash -n "$JOB"

printf 'Running help check...\n'
help_output="$tmp_dir/help.out"
bash "$SCRIPT" --help >"$help_output"
assert_contains "$help_output" "Usage:"
assert_contains "$help_output" "--sample-id"
assert_contains "$help_output" "--input-bam"
assert_contains "$help_output" "--output-dir"
assert_contains "$help_output" "--qc-dir"
assert_contains "$help_output" "--threads"
assert_contains "$help_output" "--samtools-bin"
assert_contains "$help_output" "--execute"
assert_contains "$help_output" "FWD_like"
assert_contains "$help_output" "REV_like"

printf 'Running missing required argument failure check...\n'
missing_arg_output="$tmp_dir/missing_arg.out"
assert_fails "$missing_arg_output" bash "$SCRIPT" \
    --input-bam "$input_bam" \
    --output-dir "$tmp_dir/results/missing_arg/orientation" \
    --qc-dir "$tmp_dir/results/missing_arg/qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools"
assert_contains "$missing_arg_output" "Missing required argument: --sample-id"

printf 'Running missing input BAM failure check...\n'
missing_bam_output="$tmp_dir/missing_bam.out"
assert_fails "$missing_bam_output" run_step06 ABE_EV_2 "$fixture_dir/missing.split_ncigar.bam" "$tmp_dir/results/missing_bam/orientation" "$tmp_dir/results/missing_bam/qc"
assert_contains "$missing_bam_output" "Input BAM does not exist or is empty"

printf 'Running missing input BAI failure check...\n'
missing_bai_bam="$fixture_dir/split_ncigar/missing_bai/ABE_EV_2.split_ncigar.bam"
mkdir -p "$(dirname "$missing_bai_bam")"
printf 'fake bam\n' >"$missing_bai_bam"
missing_bai_output="$tmp_dir/missing_bai.out"
assert_fails "$missing_bai_output" run_step06 ABE_EV_2 "$missing_bai_bam" "$tmp_dir/results/missing_bai/orientation" "$tmp_dir/results/missing_bai/qc"
assert_contains "$missing_bai_output" "Input BAI does not exist or is empty"

printf 'Running invalid threads failure check...\n'
invalid_threads_output="$tmp_dir/invalid_threads.out"
assert_fails "$invalid_threads_output" bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$tmp_dir/results/invalid_threads/orientation" \
    --qc-dir "$tmp_dir/results/invalid_threads/qc" \
    --threads 0 \
    --samtools-bin "$fake_bin/samtools"
assert_contains "$invalid_threads_output" "--threads must be a positive integer"

printf 'Running missing explicit samtools pre-directory failure check...\n'
missing_samtools_output="$tmp_dir/missing_samtools.out"
missing_samtools_dir="$tmp_dir/results/missing_samtools/orientation/ABE_EV_2"
missing_samtools_qc="$tmp_dir/results/missing_samtools/qc/orientation"
assert_fails "$missing_samtools_output" bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$missing_samtools_dir" \
    --qc-dir "$missing_samtools_qc" \
    --threads 2 \
    --samtools-bin "$tmp_dir/missing/samtools" \
    --execute
assert_contains "$missing_samtools_output" "samtools does not exist"
assert_not_exists "$missing_samtools_dir"
assert_not_exists "$missing_samtools_qc"

printf 'Running dry-run side-effect-free check...\n'
dry_output="$tmp_dir/dry.out"
dry_output_dir="$tmp_dir/results/dry/orientation/ABE_EV_2"
dry_qc_dir="$tmp_dir/results/dry/qc/orientation"
rm -f "$samtools_log"
SLURM_JOB_ID=dry001 run_step06 ABE_EV_2 "$input_bam" "$dry_output_dir" "$dry_qc_dir" >"$dry_output"
dry_fwd_bam="$dry_output_dir/ABE_EV_2.FWD_like.bam"
dry_rev_bam="$dry_output_dir/ABE_EV_2.REV_like.bam"
dry_counts="$dry_qc_dir/ABE_EV_2.orientation_counts.tsv"
assert_not_exists "$dry_output_dir"
assert_not_exists "$dry_qc_dir"
assert_not_exists "$dry_fwd_bam"
assert_not_exists "$dry_fwd_bam.bai"
assert_not_exists "$dry_rev_bam"
assert_not_exists "$dry_rev_bam.bai"
assert_not_exists "$dry_counts"
[[ ! -e "$samtools_log" ]] || fail "dry-run invoked samtools"
assert_contains "$dry_output" "Mode: dry-run"
assert_contains "$dry_output" "Sample ID: ABE_EV_2"
assert_contains "$dry_output" "Input BAM: $input_bam"
assert_contains "$dry_output" "Input BAI: $input_bam.bai"
assert_contains "$dry_output" "FWD_like BAM: $dry_fwd_bam"
assert_contains "$dry_output" "REV_like BAM: $dry_rev_bam"
assert_contains "$dry_output" "Counts TSV: $dry_counts"
assert_contains "$dry_output" "Temporary 99 BAM: $dry_output_dir/.ABE_EV_2.step06.dry001.99.tmp.bam"
assert_contains "$dry_output" "Temporary counts TSV: $dry_qc_dir/.ABE_EV_2.step06.dry001.orientation_counts.tmp.tsv"
assert_contains "$dry_output" "samtools view -f 99 command:"
assert_contains "$dry_output" "-f 99"
assert_contains "$dry_output" "samtools view -f 147 command:"
assert_contains "$dry_output" "-f 147"
assert_contains "$dry_output" "samtools view -f 83 command:"
assert_contains "$dry_output" "-f 83"
assert_contains "$dry_output" "samtools view -f 163 command:"
assert_contains "$dry_output" "-f 163"
assert_contains "$dry_output" "samtools merge FWD_like command:"
assert_contains "$dry_output" "samtools merge REV_like command:"
assert_contains "$dry_output" "Counts commands:"
assert_contains "$dry_output" "assigned_fraction"
assert_contains "$dry_output" "Validation plan:"
assert_contains "$dry_output" "Publish plan:"
assert_contains "$dry_output" "Rollback plan:"
assert_contains "$dry_output" "Dry-run only"
assert_not_contains "$dry_output" "sorted.md"
assert_not_contains "$dry_output" "splitncigar"

printf 'Running successful execute check...\n'
execute_output="$tmp_dir/execute.out"
execute_output_dir="$tmp_dir/results/execute/orientation/ABE_EV_2"
execute_qc_dir="$tmp_dir/results/execute/qc/orientation"
rm -f "$samtools_log"
SLURM_JOB_ID=exec001 run_step06 ABE_EV_2 "$input_bam" "$execute_output_dir" "$execute_qc_dir" --execute >"$execute_output"
execute_fwd_bam="$execute_output_dir/ABE_EV_2.FWD_like.bam"
execute_rev_bam="$execute_output_dir/ABE_EV_2.REV_like.bam"
execute_counts="$execute_qc_dir/ABE_EV_2.orientation_counts.tsv"
[[ -s "$execute_fwd_bam" ]] || fail "execute did not create non-empty FWD_like BAM"
[[ -s "$execute_fwd_bam.bai" ]] || fail "execute did not create non-empty FWD_like BAI"
[[ -s "$execute_rev_bam" ]] || fail "execute did not create non-empty REV_like BAM"
[[ -s "$execute_rev_bam.bai" ]] || fail "execute did not create non-empty REV_like BAI"
[[ -s "$execute_counts" ]] || fail "execute did not create non-empty counts TSV"
assert_contains "$execute_counts" $'sample_id\tinput_records\tflag_99_records\tflag_147_records\tflag_83_records\tflag_163_records\tfwd_like_records\trev_like_records\tassigned_records\tunassigned_records\tassigned_fraction'
assert_contains "$execute_counts" $'ABE_EV_2\t20\t5\t6\t4\t3\t11\t7\t18\t2\t0.900000'
assert_contains "$samtools_log" "--version"
assert_contains "$samtools_log" "view -@ 2 -b -f 99 $input_bam -o $execute_output_dir/.ABE_EV_2.step06.exec001.99.tmp.bam"
assert_contains "$samtools_log" "view -@ 2 -b -f 147 $input_bam -o $execute_output_dir/.ABE_EV_2.step06.exec001.147.tmp.bam"
assert_contains "$samtools_log" "view -@ 2 -b -f 83 $input_bam -o $execute_output_dir/.ABE_EV_2.step06.exec001.83.tmp.bam"
assert_contains "$samtools_log" "view -@ 2 -b -f 163 $input_bam -o $execute_output_dir/.ABE_EV_2.step06.exec001.163.tmp.bam"
assert_contains "$samtools_log" "merge -@ 2 -o $execute_output_dir/.ABE_EV_2.step06.exec001.FWD_like.tmp.bam"
assert_contains "$samtools_log" "merge -@ 2 -o $execute_output_dir/.ABE_EV_2.step06.exec001.REV_like.tmp.bam"
assert_contains "$samtools_log" "index $execute_output_dir/.ABE_EV_2.step06.exec001.FWD_like.tmp.bam"
assert_contains "$samtools_log" "index $execute_output_dir/.ABE_EV_2.step06.exec001.REV_like.tmp.bam"
assert_contains "$samtools_log" "view -c $input_bam"
assert_contains "$samtools_log" "view -c -f 99 $input_bam"
assert_contains "$samtools_log" "view -c -f 147 $input_bam"
assert_contains "$samtools_log" "view -c -f 83 $input_bam"
assert_contains "$samtools_log" "view -c -f 163 $input_bam"
assert_contains "$samtools_log" "view -c $execute_output_dir/.ABE_EV_2.step06.exec001.FWD_like.tmp.bam"
assert_contains "$samtools_log" "view -c $execute_output_dir/.ABE_EV_2.step06.exec001.REV_like.tmp.bam"
assert_contains "$samtools_log" "quickcheck $execute_output_dir/.ABE_EV_2.step06.exec001.FWD_like.tmp.bam"
assert_contains "$samtools_log" "quickcheck $execute_output_dir/.ABE_EV_2.step06.exec001.REV_like.tmp.bam"
assert_contains "$samtools_log" "quickcheck $execute_fwd_bam"
assert_contains "$samtools_log" "quickcheck $execute_rev_bam"
assert_contains "$execute_output" "Mode: execute"
assert_contains "$execute_output" "Step 06 read-orientation output details:"
assert_not_exists "$execute_output_dir/.ABE_EV_2.step06.lock"
assert_no_step06_scratch "$execute_output_dir" "$execute_qc_dir"

printf 'Running basename/PATH execute from arbitrary CWD check...\n'
arbitrary_cwd="$tmp_dir/arbitrary_cwd"
arbitrary_output="$tmp_dir/arbitrary_cwd.out"
arbitrary_output_dir="$tmp_dir/results/arbitrary/orientation/ABE_EV_2"
arbitrary_qc_dir="$tmp_dir/results/arbitrary/qc/orientation"
mkdir -p "$arbitrary_cwd"
(
    cd "$arbitrary_cwd"
    SLURM_JOB_ID=path001 bash "$SCRIPT" \
        --sample-id ABE_EV_2 \
        --input-bam "$input_bam" \
        --output-dir "$arbitrary_output_dir" \
        --qc-dir "$arbitrary_qc_dir" \
        --threads 2 \
        --samtools-bin samtools \
        --execute
) >"$arbitrary_output" 2>&1
[[ -s "$arbitrary_output_dir/ABE_EV_2.FWD_like.bam" ]] || fail "arbitrary-CWD run did not publish FWD_like BAM"
[[ -s "$arbitrary_output_dir/ABE_EV_2.FWD_like.bam.bai" ]] || fail "arbitrary-CWD run did not publish FWD_like BAI"
[[ -s "$arbitrary_output_dir/ABE_EV_2.REV_like.bam" ]] || fail "arbitrary-CWD run did not publish REV_like BAM"
[[ -s "$arbitrary_output_dir/ABE_EV_2.REV_like.bam.bai" ]] || fail "arbitrary-CWD run did not publish REV_like BAI"
[[ -s "$arbitrary_qc_dir/ABE_EV_2.orientation_counts.tsv" ]] || fail "arbitrary-CWD run did not publish counts TSV"
assert_contains "$arbitrary_output" "samtools bin: $fake_bin/samtools"
if find "$arbitrary_cwd" -mindepth 1 -print | grep -q .; then
    find "$arbitrary_cwd" -mindepth 1 -print >&2
    fail "arbitrary-CWD run left invocation-directory residue"
fi
assert_not_exists "$arbitrary_output_dir/.ABE_EV_2.step06.lock"
assert_no_step06_scratch "$arbitrary_output_dir" "$arbitrary_qc_dir"
assert_no_step06_attempt_marker "$arbitrary_output_dir" "$arbitrary_qc_dir"

printf 'Running filter child exit propagation and cleanup check...\n'
filter_fail_output="$tmp_dir/filter_fail.out"
filter_fail_dir="$tmp_dir/results/filter_fail/orientation/ABE_EV_2"
filter_fail_qc="$tmp_dir/results/filter_fail/qc/orientation"
prepare_child_failure_dirs "$filter_fail_dir" "$filter_fail_qc"
assert_exits 71 "$filter_fail_output" env \
    FAKE_FILTER_FAIL_FLAG=147 \
    FAKE_FILTER_FAIL_STATUS=71 \
    SLURM_JOB_ID=filter071 \
    bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$filter_fail_dir" \
    --qc-dir "$filter_fail_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_contains "$filter_fail_output" "fake samtools view -b forced failure for flag 147"
assert_child_failure_state "$filter_fail_dir" "$filter_fail_qc"

printf 'Running merge child exit propagation and cleanup check...\n'
merge_fail_output="$tmp_dir/merge_fail.out"
merge_fail_dir="$tmp_dir/results/merge_fail/orientation/ABE_EV_2"
merge_fail_qc="$tmp_dir/results/merge_fail/qc/orientation"
prepare_child_failure_dirs "$merge_fail_dir" "$merge_fail_qc"
assert_exits 72 "$merge_fail_output" env \
    FAKE_MERGE_FAIL_MATCH=FWD_like.tmp.bam \
    FAKE_MERGE_FAIL_STATUS=72 \
    SLURM_JOB_ID=merge072 \
    bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$merge_fail_dir" \
    --qc-dir "$merge_fail_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_contains "$merge_fail_output" "fake samtools merge forced failure"
assert_child_failure_state "$merge_fail_dir" "$merge_fail_qc"

printf 'Running index child exit propagation and cleanup check...\n'
index_fail_output="$tmp_dir/index_fail.out"
index_fail_dir="$tmp_dir/results/index_fail/orientation/ABE_EV_2"
index_fail_qc="$tmp_dir/results/index_fail/qc/orientation"
prepare_child_failure_dirs "$index_fail_dir" "$index_fail_qc"
assert_exits 73 "$index_fail_output" env \
    FAKE_INDEX_FAIL_MATCH=REV_like.tmp.bam \
    FAKE_INDEX_FAIL_STATUS=73 \
    SLURM_JOB_ID=index073 \
    bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$index_fail_dir" \
    --qc-dir "$index_fail_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_contains "$index_fail_output" "fake samtools index forced failure"
assert_child_failure_state "$index_fail_dir" "$index_fail_qc"

printf 'Running count child exit propagation and cleanup check...\n'
count_fail_output="$tmp_dir/count_fail.out"
count_fail_dir="$tmp_dir/results/count_fail/orientation/ABE_EV_2"
count_fail_qc="$tmp_dir/results/count_fail/qc/orientation"
prepare_child_failure_dirs "$count_fail_dir" "$count_fail_qc"
assert_exits 74 "$count_fail_output" env \
    FAKE_COUNT_FAIL_MATCH=FWD_like.tmp.bam \
    FAKE_COUNT_FAIL_STATUS=74 \
    SLURM_JOB_ID=count074 \
    bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$count_fail_dir" \
    --qc-dir "$count_fail_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_contains "$count_fail_output" "fake samtools count forced failure"
assert_child_failure_state "$count_fail_dir" "$count_fail_qc"

printf 'Running assigned-greater-than-input rejection check...\n'
assigned_input_bam="$fixture_dir/assigned_gt_input/ABE_EV_2.split_ncigar.bam"
FAKE_INPUT_COUNT=10 write_input_bam_pair "$assigned_input_bam"
assigned_output="$tmp_dir/assigned_gt_input.out"
assigned_dir="$tmp_dir/results/assigned_gt_input/orientation/ABE_EV_2"
assigned_qc="$tmp_dir/results/assigned_gt_input/qc/orientation"
prepare_child_failure_dirs "$assigned_dir" "$assigned_qc"
assert_fails "$assigned_output" env SLURM_JOB_ID=assigned001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$assigned_input_bam" \
    --output-dir "$assigned_dir" \
    --qc-dir "$assigned_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_contains "$assigned_output" "assigned_records exceeds input_records: 18 > 10"
assert_child_failure_state "$assigned_dir" "$assigned_qc"

printf 'Running flag-subcount/merged-count mismatch publication defect check...\n'
mismatch_output="$tmp_dir/count_mismatch.out"
mismatch_dir="$tmp_dir/results/count_mismatch/orientation/ABE_EV_2"
mismatch_qc="$tmp_dir/results/count_mismatch/qc/orientation"
mkdir -p "$mismatch_dir" "$mismatch_qc"
printf 'unrelated mismatch output bytes\n' >"$mismatch_dir/unrelated.txt"
printf 'unrelated mismatch qc bytes\n' >"$mismatch_qc/unrelated.txt"
FAKE_MERGE_COUNT_MATCH=FWD_like.tmp.bam \
FAKE_MERGE_COUNT=12 \
SLURM_JOB_ID=mismatch001 \
    run_step06 ABE_EV_2 "$input_bam" "$mismatch_dir" "$mismatch_qc" --execute >"$mismatch_output" 2>&1
mismatch_counts="$mismatch_qc/ABE_EV_2.orientation_counts.tsv"
[[ -s "$mismatch_dir/ABE_EV_2.FWD_like.bam" ]] || fail "mismatch run did not publish FWD_like BAM"
[[ -s "$mismatch_dir/ABE_EV_2.FWD_like.bam.bai" ]] || fail "mismatch run did not publish FWD_like BAI"
[[ -s "$mismatch_dir/ABE_EV_2.REV_like.bam" ]] || fail "mismatch run did not publish REV_like BAM"
[[ -s "$mismatch_dir/ABE_EV_2.REV_like.bam.bai" ]] || fail "mismatch run did not publish REV_like BAI"
assert_contains "$mismatch_counts" $'ABE_EV_2\t20\t5\t6\t4\t3\t12\t7\t19\t1\t0.950000'
assert_file_equals "$mismatch_dir/unrelated.txt" "unrelated mismatch output bytes"
assert_file_equals "$mismatch_qc/unrelated.txt" "unrelated mismatch qc bytes"
assert_contains "$mismatch_output" "Step 06 read-orientation output details:"
assert_not_exists "$mismatch_dir/.ABE_EV_2.step06.lock"
assert_no_step06_scratch "$mismatch_dir" "$mismatch_qc"
assert_no_step06_attempt_marker "$mismatch_dir" "$mismatch_qc"

printf 'Running existing foreign lock failure check...\n'
lock_dir="$tmp_dir/results/locked/orientation/ABE_EV_2"
lock_qc_dir="$tmp_dir/results/locked/qc/orientation"
mkdir -p "$lock_dir/.ABE_EV_2.step06.lock" "$lock_qc_dir"
printf 'run_token=other-job\n' >"$lock_dir/.ABE_EV_2.step06.lock/owner"
lock_output="$tmp_dir/lock.out"
assert_fails "$lock_output" env SLURM_JOB_ID=lock001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$lock_dir" \
    --qc-dir "$lock_qc_dir" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_contains "$lock_output" "Step 06 lock already exists"
assert_contains "$lock_output" "run_token=other-job"
[[ -d "$lock_dir/.ABE_EV_2.step06.lock" ]] || fail "foreign lock should remain"
assert_file_equals "$lock_dir/.ABE_EV_2.step06.lock/owner" "run_token=other-job"
assert_no_step06_scratch "$lock_dir" "$lock_qc_dir"

printf 'Running validation failure cleanup check...\n'
quickcheck_fail_output="$tmp_dir/quickcheck_fail.out"
quickcheck_fail_dir="$tmp_dir/results/quickcheck_fail/orientation/ABE_EV_2"
quickcheck_fail_qc="$tmp_dir/results/quickcheck_fail/qc/orientation"
assert_fails "$quickcheck_fail_output" env FAKE_QUICKCHECK_FAIL_MATCH="FWD_like.tmp.bam" SLURM_JOB_ID=quick001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$quickcheck_fail_dir" \
    --qc-dir "$quickcheck_fail_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_contains "$quickcheck_fail_output" "failed samtools quickcheck"
assert_not_exists "$quickcheck_fail_dir/ABE_EV_2.FWD_like.bam"
assert_not_exists "$quickcheck_fail_dir/ABE_EV_2.REV_like.bam"
assert_not_exists "$quickcheck_fail_qc/ABE_EV_2.orientation_counts.tsv"
assert_not_exists "$quickcheck_fail_dir/.ABE_EV_2.step06.lock"
assert_no_step06_scratch "$quickcheck_fail_dir" "$quickcheck_fail_qc"

printf 'Running zero group validation failure cleanup check...\n'
zero_group_output="$tmp_dir/zero_group.out"
zero_group_dir="$tmp_dir/results/zero_group/orientation/ABE_EV_2"
zero_group_qc="$tmp_dir/results/zero_group/qc/orientation"
assert_fails "$zero_group_output" env FAKE_ZERO_MERGE_MATCH="REV_like" SLURM_JOB_ID=zero001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$zero_group_dir" \
    --qc-dir "$zero_group_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_contains "$zero_group_output" "rev_like_records is zero"
assert_not_exists "$zero_group_dir/.ABE_EV_2.step06.lock"
assert_no_step06_scratch "$zero_group_dir" "$zero_group_qc"

printf 'Running stale temp path failure check...\n'
stale_dir="$tmp_dir/results/stale/orientation/ABE_EV_2"
stale_qc="$tmp_dir/results/stale/qc/orientation"
mkdir -p "$stale_dir" "$stale_qc"
printf 'stale temp\n' >"$stale_dir/.ABE_EV_2.step06.stale001.99.tmp.bam"
stale_output="$tmp_dir/stale.out"
# Pre-existing scratch with the same run token must be refused and preserved for
# manual inspection; the script should not clean it as owned temp.
assert_fails "$stale_output" env SLURM_JOB_ID=stale001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$stale_dir" \
    --qc-dir "$stale_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_contains "$stale_output" "Refusing to reuse stale Step 06 path"
assert_file_equals "$stale_dir/.ABE_EV_2.step06.stale001.99.tmp.bam" "stale temp"
assert_not_exists "$stale_dir/.ABE_EV_2.step06.lock"

printf 'Running rollback preserves previous final outputs check...\n'
rollback_dir="$tmp_dir/results/rollback/orientation/ABE_EV_2"
rollback_qc="$tmp_dir/results/rollback/qc/orientation"
mkdir -p "$rollback_dir" "$rollback_qc"
printf 'previous fwd bam' >"$rollback_dir/ABE_EV_2.FWD_like.bam"
printf 'previous fwd bai' >"$rollback_dir/ABE_EV_2.FWD_like.bam.bai"
printf 'previous rev bam' >"$rollback_dir/ABE_EV_2.REV_like.bam"
printf 'previous rev bai' >"$rollback_dir/ABE_EV_2.REV_like.bam.bai"
printf 'previous counts' >"$rollback_qc/ABE_EV_2.orientation_counts.tsv"
rollback_output="$tmp_dir/rollback.out"
assert_fails "$rollback_output" env FAKE_MV_FAIL_ONCE_DEST_MATCH="ABE_EV_2.REV_like.bam" SLURM_JOB_ID=rollback001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$rollback_dir" \
    --qc-dir "$rollback_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_contains "$rollback_output" "fake mv forced failure"
assert_contains "$rollback_output" "Rolling back Step 06"
assert_file_equals "$rollback_dir/ABE_EV_2.FWD_like.bam" "previous fwd bam"
assert_file_equals "$rollback_dir/ABE_EV_2.FWD_like.bam.bai" "previous fwd bai"
assert_file_equals "$rollback_dir/ABE_EV_2.REV_like.bam" "previous rev bam"
assert_file_equals "$rollback_dir/ABE_EV_2.REV_like.bam.bai" "previous rev bai"
assert_file_equals "$rollback_qc/ABE_EV_2.orientation_counts.tsv" "previous counts"
assert_not_exists "$rollback_dir/.ABE_EV_2.step06.lock"
assert_no_step06_scratch "$rollback_dir" "$rollback_qc"

printf 'Running counts-last final publication order check...\n'
publish_order_output="$tmp_dir/publish_order.out"
publish_order_dir="$tmp_dir/results/publish_order/orientation/ABE_EV_2"
publish_order_qc="$tmp_dir/results/publish_order/qc/orientation"
rm -f "$mv_log"
SLURM_JOB_ID=order001 run_step06 ABE_EV_2 "$input_bam" "$publish_order_dir" "$publish_order_qc" --execute >"$publish_order_output"
publish_order_fwd_bam="$publish_order_dir/ABE_EV_2.FWD_like.bam"
publish_order_fwd_bai="$publish_order_fwd_bam.bai"
publish_order_rev_bam="$publish_order_dir/ABE_EV_2.REV_like.bam"
publish_order_rev_bai="$publish_order_rev_bam.bai"
publish_order_counts="$publish_order_qc/ABE_EV_2.orientation_counts.tsv"
assert_line_before "$mv_log" "$publish_order_fwd_bam" "$publish_order_fwd_bai"
assert_line_before "$mv_log" "$publish_order_fwd_bai" "$publish_order_rev_bam"
assert_line_before "$mv_log" "$publish_order_rev_bam" "$publish_order_rev_bai"
assert_line_before "$mv_log" "$publish_order_rev_bai" "$publish_order_counts"
[[ -s "$publish_order_counts" ]] || fail "counts-last run did not publish counts TSV"
assert_not_exists "$publish_order_dir/.ABE_EV_2.step06.lock"
assert_no_step06_scratch "$publish_order_dir" "$publish_order_qc"

printf 'Running incomplete final-set rejection preservation check...\n'
incomplete_dir="$tmp_dir/results/incomplete/orientation/ABE_EV_2"
incomplete_qc="$tmp_dir/results/incomplete/qc/orientation"
mkdir -p "$incomplete_dir" "$incomplete_qc"
printf 'lone prior FWD BAM bytes\n' >"$incomplete_dir/ABE_EV_2.FWD_like.bam"
printf 'unrelated incomplete output bytes\n' >"$incomplete_dir/unrelated.txt"
printf 'unrelated incomplete qc bytes\n' >"$incomplete_qc/unrelated.txt"
incomplete_output="$tmp_dir/incomplete.out"
assert_fails "$incomplete_output" env SLURM_JOB_ID=incomplete001 bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$incomplete_dir" \
    --qc-dir "$incomplete_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_contains "$incomplete_output" "Step 06 final outputs are inconsistent"
assert_file_equals "$incomplete_dir/ABE_EV_2.FWD_like.bam" "lone prior FWD BAM bytes"
assert_not_exists "$incomplete_dir/ABE_EV_2.FWD_like.bam.bai"
assert_not_exists "$incomplete_dir/ABE_EV_2.REV_like.bam"
assert_not_exists "$incomplete_dir/ABE_EV_2.REV_like.bam.bai"
assert_not_exists "$incomplete_qc/ABE_EV_2.orientation_counts.tsv"
assert_file_equals "$incomplete_dir/unrelated.txt" "unrelated incomplete output bytes"
assert_file_equals "$incomplete_qc/unrelated.txt" "unrelated incomplete qc bytes"
assert_not_exists "$incomplete_dir/.ABE_EV_2.step06.lock"
assert_no_step06_scratch "$incomplete_dir" "$incomplete_qc"
assert_no_step06_attempt_marker "$incomplete_dir" "$incomplete_qc"

printf 'Running final-path quickcheck five-file restoration check...\n'
final_revalidation_dir="$tmp_dir/results/final_revalidation/orientation/ABE_EV_2"
final_revalidation_qc="$tmp_dir/results/final_revalidation/qc/orientation"
mkdir -p "$final_revalidation_dir" "$final_revalidation_qc"
printf 'prior final-check FWD BAM bytes\n' >"$final_revalidation_dir/ABE_EV_2.FWD_like.bam"
printf 'prior final-check FWD BAI bytes\n' >"$final_revalidation_dir/ABE_EV_2.FWD_like.bam.bai"
printf 'prior final-check REV BAM bytes\n' >"$final_revalidation_dir/ABE_EV_2.REV_like.bam"
printf 'prior final-check REV BAI bytes\n' >"$final_revalidation_dir/ABE_EV_2.REV_like.bam.bai"
printf 'prior final-check counts bytes\n' >"$final_revalidation_qc/ABE_EV_2.orientation_counts.tsv"
printf 'unrelated final-check output bytes\n' >"$final_revalidation_dir/unrelated.txt"
printf 'unrelated final-check qc bytes\n' >"$final_revalidation_qc/unrelated.txt"
final_revalidation_output="$tmp_dir/final_revalidation.out"
assert_fails "$final_revalidation_output" env \
    FAKE_FINAL_QUICKCHECK_FAIL_PATH="$final_revalidation_dir/ABE_EV_2.FWD_like.bam" \
    SLURM_JOB_ID=finalcheck001 \
    bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$final_revalidation_dir" \
    --qc-dir "$final_revalidation_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_contains "$final_revalidation_output" "fake final-path quickcheck forced failure"
assert_contains "$final_revalidation_output" "Rolling back Step 06"
assert_file_equals "$final_revalidation_dir/ABE_EV_2.FWD_like.bam" "prior final-check FWD BAM bytes"
assert_file_equals "$final_revalidation_dir/ABE_EV_2.FWD_like.bam.bai" "prior final-check FWD BAI bytes"
assert_file_equals "$final_revalidation_dir/ABE_EV_2.REV_like.bam" "prior final-check REV BAM bytes"
assert_file_equals "$final_revalidation_dir/ABE_EV_2.REV_like.bam.bai" "prior final-check REV BAI bytes"
assert_file_equals "$final_revalidation_qc/ABE_EV_2.orientation_counts.tsv" "prior final-check counts bytes"
assert_file_equals "$final_revalidation_dir/unrelated.txt" "unrelated final-check output bytes"
assert_file_equals "$final_revalidation_qc/unrelated.txt" "unrelated final-check qc bytes"
assert_not_exists "$final_revalidation_dir/.ABE_EV_2.step06.lock"
assert_no_step06_scratch "$final_revalidation_dir" "$final_revalidation_qc"
assert_no_step06_attempt_marker "$final_revalidation_dir" "$final_revalidation_qc"

printf 'Running publication-plus-restoration failure erasure check...\n'
restore_failure_dir="$tmp_dir/results/restore_failure/orientation/ABE_EV_2"
restore_failure_qc="$tmp_dir/results/restore_failure/qc/orientation"
mkdir -p "$restore_failure_dir" "$restore_failure_qc"
printf 'prior restore-failure FWD BAM bytes\n' >"$restore_failure_dir/ABE_EV_2.FWD_like.bam"
printf 'prior restore-failure FWD BAI bytes\n' >"$restore_failure_dir/ABE_EV_2.FWD_like.bam.bai"
printf 'prior restore-failure REV BAM bytes\n' >"$restore_failure_dir/ABE_EV_2.REV_like.bam"
printf 'prior restore-failure REV BAI bytes\n' >"$restore_failure_dir/ABE_EV_2.REV_like.bam.bai"
printf 'prior restore-failure counts bytes\n' >"$restore_failure_qc/ABE_EV_2.orientation_counts.tsv"
printf 'unrelated restore-failure output bytes\n' >"$restore_failure_dir/unrelated.txt"
printf 'unrelated restore-failure qc bytes\n' >"$restore_failure_qc/unrelated.txt"
restore_failure_output="$tmp_dir/restore_failure.out"
assert_exits 67 "$restore_failure_output" env \
    FAKE_MV_FAIL_ONCE_DEST_MATCH="$restore_failure_dir/ABE_EV_2.REV_like.bam" \
    FAKE_MV_FAIL_MARKER="$tmp_dir/restore_failure_publish_failed_once" \
    FAKE_MV_RESTORE_FAIL_SOURCE="$restore_failure_dir/.ABE_EV_2.step06.restore068.previous.FWD_like.bam" \
    FAKE_MV_RESTORE_FAIL_STATUS=68 \
    SLURM_JOB_ID=restore068 \
    bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$restore_failure_dir" \
    --qc-dir "$restore_failure_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_contains "$restore_failure_output" "fake mv forced failure for destination"
assert_contains "$restore_failure_output" "Rolling back Step 06"
assert_contains "$restore_failure_output" "fake mv forced restore failure for source"
assert_not_exists "$restore_failure_dir/ABE_EV_2.FWD_like.bam"
assert_file_equals "$restore_failure_dir/ABE_EV_2.FWD_like.bam.bai" "prior restore-failure FWD BAI bytes"
assert_file_equals "$restore_failure_dir/ABE_EV_2.REV_like.bam" "prior restore-failure REV BAM bytes"
assert_file_equals "$restore_failure_dir/ABE_EV_2.REV_like.bam.bai" "prior restore-failure REV BAI bytes"
assert_file_equals "$restore_failure_qc/ABE_EV_2.orientation_counts.tsv" "prior restore-failure counts bytes"
assert_file_equals "$restore_failure_dir/unrelated.txt" "unrelated restore-failure output bytes"
assert_file_equals "$restore_failure_qc/unrelated.txt" "unrelated restore-failure qc bytes"
assert_not_exists "$restore_failure_dir/.ABE_EV_2.step06.lock"
assert_no_step06_scratch "$restore_failure_dir" "$restore_failure_qc"
assert_no_step06_attempt_marker "$restore_failure_dir" "$restore_failure_qc"

printf 'Running admitted BAM/BAI mutation success check...\n'
mutation_input_bam="$fixture_dir/mutation/ABE_EV_2.split_ncigar.bam"
write_input_bam_pair "$mutation_input_bam"
mutation_output="$tmp_dir/mutation.out"
mutation_dir="$tmp_dir/results/mutation/orientation/ABE_EV_2"
mutation_qc="$tmp_dir/results/mutation/qc/orientation"
mkdir -p "$mutation_dir" "$mutation_qc"
printf 'unrelated mutation output bytes\n' >"$mutation_dir/unrelated.txt"
printf 'unrelated mutation qc bytes\n' >"$mutation_qc/unrelated.txt"
FAKE_MUTATE_ADMITTED_INPUTS=1 \
SLURM_JOB_ID=mutation001 \
    run_step06 ABE_EV_2 "$mutation_input_bam" "$mutation_dir" "$mutation_qc" --execute >"$mutation_output" 2>&1
assert_file_equals "$mutation_input_bam" $'INPUT_BAM\nCOUNT:20\nmutated input bam'
assert_file_equals "$mutation_input_bam.bai" $'fake step05 split-n-cigar bai\nmutated input bai'
[[ -s "$mutation_dir/ABE_EV_2.FWD_like.bam" ]] || fail "input-mutation run did not publish FWD_like BAM"
[[ -s "$mutation_dir/ABE_EV_2.FWD_like.bam.bai" ]] || fail "input-mutation run did not publish FWD_like BAI"
[[ -s "$mutation_dir/ABE_EV_2.REV_like.bam" ]] || fail "input-mutation run did not publish REV_like BAM"
[[ -s "$mutation_dir/ABE_EV_2.REV_like.bam.bai" ]] || fail "input-mutation run did not publish REV_like BAI"
assert_contains "$mutation_qc/ABE_EV_2.orientation_counts.tsv" $'ABE_EV_2\t20\t5\t6\t4\t3\t11\t7\t18\t2\t0.900000'
assert_file_equals "$mutation_dir/unrelated.txt" "unrelated mutation output bytes"
assert_file_equals "$mutation_qc/unrelated.txt" "unrelated mutation qc bytes"
assert_contains "$mutation_output" "Step 06 read-orientation output details:"
assert_not_exists "$mutation_dir/.ABE_EV_2.step06.lock"
assert_no_step06_scratch "$mutation_dir" "$mutation_qc"
assert_no_step06_attempt_marker "$mutation_dir" "$mutation_qc"

printf 'Running controlled TERM cleanup and predecessor preservation check...\n'
signal_dir="$tmp_dir/results/signal/orientation/ABE_EV_2"
signal_qc="$tmp_dir/results/signal/qc/orientation"
mkdir -p "$signal_dir" "$signal_qc"
printf 'prior signal FWD BAM bytes\n' >"$signal_dir/ABE_EV_2.FWD_like.bam"
printf 'prior signal FWD BAI bytes\n' >"$signal_dir/ABE_EV_2.FWD_like.bam.bai"
printf 'prior signal REV BAM bytes\n' >"$signal_dir/ABE_EV_2.REV_like.bam"
printf 'prior signal REV BAI bytes\n' >"$signal_dir/ABE_EV_2.REV_like.bam.bai"
printf 'prior signal counts bytes\n' >"$signal_qc/ABE_EV_2.orientation_counts.tsv"
printf 'unrelated signal output bytes\n' >"$signal_dir/unrelated.txt"
printf 'unrelated signal qc bytes\n' >"$signal_qc/unrelated.txt"
signal_output="$tmp_dir/signal.out"
assert_exits 143 "$signal_output" env \
    FAKE_FILTER_TERM_PARENT=1 \
    SLURM_JOB_ID=signal001 \
    bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$signal_dir" \
    --qc-dir "$signal_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_file_equals "$signal_dir/ABE_EV_2.FWD_like.bam" "prior signal FWD BAM bytes"
assert_file_equals "$signal_dir/ABE_EV_2.FWD_like.bam.bai" "prior signal FWD BAI bytes"
assert_file_equals "$signal_dir/ABE_EV_2.REV_like.bam" "prior signal REV BAM bytes"
assert_file_equals "$signal_dir/ABE_EV_2.REV_like.bam.bai" "prior signal REV BAI bytes"
assert_file_equals "$signal_qc/ABE_EV_2.orientation_counts.tsv" "prior signal counts bytes"
assert_file_equals "$signal_dir/unrelated.txt" "unrelated signal output bytes"
assert_file_equals "$signal_qc/unrelated.txt" "unrelated signal qc bytes"
assert_not_exists "$signal_dir/.ABE_EV_2.step06.lock"
assert_no_step06_scratch "$signal_dir" "$signal_qc"
assert_no_step06_attempt_marker "$signal_dir" "$signal_qc"

printf 'Running distinct-output-lock/shared-QC collision check...\n'
collision_barrier="$tmp_dir/collision_barrier"
collision_first_complete="$collision_barrier/first.complete"
collision_a_dir="$tmp_dir/results/collision_a/orientation/ABE_EV_2"
collision_b_dir="$tmp_dir/results/collision_b/orientation/ABE_EV_2"
collision_qc="$tmp_dir/results/collision_shared/qc/orientation"
collision_a_output="$tmp_dir/collision_a.out"
collision_b_output="$tmp_dir/collision_b.out"
mkdir -p "$collision_a_dir" "$collision_b_dir" "$collision_qc"
printf 'unrelated collision A bytes\n' >"$collision_a_dir/unrelated.txt"
printf 'unrelated collision B bytes\n' >"$collision_b_dir/unrelated.txt"
printf 'unrelated collision QC bytes\n' >"$collision_qc/unrelated.txt"
env \
    FAKE_MV_BARRIER_DIR="$collision_barrier" \
    FAKE_MV_COMPLETE_MARKER="$collision_first_complete" \
    SLURM_JOB_ID=collision_a \
    bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$collision_a_dir" \
    --qc-dir "$collision_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute >"$collision_a_output" 2>&1 &
collision_a_pid=$!
env \
    FAKE_FLAG_99_COUNT=2 \
    FAKE_FLAG_147_COUNT=3 \
    FAKE_FLAG_83_COUNT=4 \
    FAKE_FLAG_163_COUNT=5 \
    FAKE_MV_BARRIER_DIR="$collision_barrier" \
    FAKE_MV_BARRIER_WAIT_FOR_FILE="$collision_first_complete" \
    SLURM_JOB_ID=collision_b \
    bash "$SCRIPT" \
    --sample-id ABE_EV_2 \
    --input-bam "$input_bam" \
    --output-dir "$collision_b_dir" \
    --qc-dir "$collision_qc" \
    --threads 2 \
    --samtools-bin "$fake_bin/samtools" \
    --execute >"$collision_b_output" 2>&1 &
collision_b_pid=$!
set +e
wait "$collision_a_pid"
collision_a_status=$?
wait "$collision_b_pid"
collision_b_status=$?
set -e
[[ "$collision_a_status" -eq 0 ]] || {
    cat "$collision_a_output" >&2
    fail "first collision run exited $collision_a_status"
}
[[ "$collision_b_status" -eq 0 ]] || {
    cat "$collision_b_output" >&2
    fail "second collision run exited $collision_b_status"
}
for path in \
    "$collision_a_dir/ABE_EV_2.FWD_like.bam" \
    "$collision_a_dir/ABE_EV_2.FWD_like.bam.bai" \
    "$collision_a_dir/ABE_EV_2.REV_like.bam" \
    "$collision_a_dir/ABE_EV_2.REV_like.bam.bai" \
    "$collision_b_dir/ABE_EV_2.FWD_like.bam" \
    "$collision_b_dir/ABE_EV_2.FWD_like.bam.bai" \
    "$collision_b_dir/ABE_EV_2.REV_like.bam" \
    "$collision_b_dir/ABE_EV_2.REV_like.bam.bai"
do
    [[ -s "$path" ]] || fail "collision run did not preserve output: $path"
done
assert_contains "$collision_a_dir/ABE_EV_2.FWD_like.bam" "COUNT:11"
assert_contains "$collision_a_dir/ABE_EV_2.REV_like.bam" "COUNT:7"
assert_contains "$collision_b_dir/ABE_EV_2.FWD_like.bam" "COUNT:5"
assert_contains "$collision_b_dir/ABE_EV_2.REV_like.bam" "COUNT:9"
assert_contains "$collision_qc/ABE_EV_2.orientation_counts.tsv" $'ABE_EV_2\t20\t2\t3\t4\t5\t5\t9\t14\t6\t0.700000'
assert_file_equals "$collision_a_dir/unrelated.txt" "unrelated collision A bytes"
assert_file_equals "$collision_b_dir/unrelated.txt" "unrelated collision B bytes"
assert_file_equals "$collision_qc/unrelated.txt" "unrelated collision QC bytes"
assert_contains "$collision_a_output" "Step 06 read-orientation output details:"
assert_contains "$collision_b_output" "Step 06 read-orientation output details:"
assert_not_exists "$collision_a_dir/.ABE_EV_2.step06.lock"
assert_not_exists "$collision_b_dir/.ABE_EV_2.step06.lock"
assert_no_step06_scratch "$collision_a_dir" "$collision_qc"
assert_no_step06_scratch "$collision_b_dir" "$collision_qc"
assert_no_step06_attempt_marker "$collision_a_dir" "$collision_qc"
assert_no_step06_attempt_marker "$collision_b_dir" "$collision_qc"

printf 'Running stale Step 05 path checks...\n'
stale_path_output="$tmp_dir/stale_paths.out"
if grep -E "sorted\\.md|splitncigar" "$SCRIPT" "$JOB" >"$stale_path_output"; then
    cat "$stale_path_output" >&2
    fail "Step 06 files should not use stale sorted.md or splitncigar paths"
fi
assert_not_contains "$execute_output" "sorted.md"
assert_not_contains "$execute_output" "splitncigar"

printf 'All step_06 read-orientation split smoke tests passed.\n'
