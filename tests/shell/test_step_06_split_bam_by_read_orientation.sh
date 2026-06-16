#!/usr/bin/env bash
# Smoke tests for Step 06 command construction, side-effect-free dry-runs,
# cleanup, and rollback using a fake local samtools executable.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/step_06_split_bam_by_read_orientation.sh"
JOB="$REPO_ROOT/jobs/step_06_split_bam_by_read_orientation.slurm"

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

assert_file_equals() {
    local path="$1"
    local expected="$2"
    local actual

    [[ -f "$path" ]] || fail "file does not exist: $path"
    actual="$(cat "$path")"
    [[ "$actual" == "$expected" ]] || fail "unexpected contents for $path: $actual"
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

    if [[ -n "\${FAKE_VIEW_B_FAIL_FLAG:-}" && "\$flag" == "\$FAKE_VIEW_B_FAIL_FLAG" ]]; then
        printf 'fake samtools view -b forced failure for flag %s\\n' "\$flag" >&2
        exit 65
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

        total=0
        for input in "\${inputs[@]}"; do
            [[ -s "\$input" ]] || { printf 'fake samtools merge input missing or empty: %s\\n' "\$input" >&2; exit 64; }
            count="\$(count_bam "\$input")"
            total=\$((total + count))
        done

        if [[ -n "\${FAKE_ZERO_MERGE_MATCH:-}" && "\$output_bam" == *"\$FAKE_ZERO_MERGE_MATCH"* ]]; then
            total=0
        fi

        {
            printf 'MERGED:%s %s\\n' "\${inputs[0]}" "\${inputs[1]}"
            printf 'COUNT:%s\\n' "\$total"
        } > "\$output_bam"
        ;;
    index)
        input_bam="\${1:-}"
        [[ -n "\$input_bam" ]] || { printf 'fake samtools index missing BAM\\n' >&2; exit 64; }
        if [[ -n "\${FAKE_INDEX_EMPTY_MATCH:-}" && "\$input_bam" == *"\$FAKE_INDEX_EMPTY_MATCH"* ]]; then
            : > "\$input_bam.bai"
        else
            printf 'fake bam index for %s\\n' "\$input_bam" > "\$input_bam.bai"
        fi
        ;;
    quickcheck)
        input_bam="\${1:-}"
        [[ -n "\$input_bam" ]] || { printf 'fake samtools quickcheck missing BAM\\n' >&2; exit 64; }
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

fail_marker="$tmp_dir/fake_mv_failed_once"
# Force only the first matching publish move to fail so rollback moves can still
# restore the previous final output set.
if [[ -n "\${FAKE_MV_FAIL_ONCE_DEST_MATCH:-}" && "\$dest" == *"\$FAKE_MV_FAIL_ONCE_DEST_MATCH"* && ! -e "\$fail_marker" ]]; then
    : > "\$fail_marker"
    printf 'fake mv forced failure for destination: %s\\n' "\$dest" >&2
    exit 67
fi

/bin/mv "\$@"
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

printf 'Running stale Step 05 path checks...\n'
stale_path_output="$tmp_dir/stale_paths.out"
if grep -E "sorted\\.md|splitncigar" "$SCRIPT" "$JOB" >"$stale_path_output"; then
    cat "$stale_path_output" >&2
    fail "Step 06 files should not use stale sorted.md or splitncigar paths"
fi
assert_not_contains "$execute_output" "sorted.md"
assert_not_contains "$execute_output" "splitncigar"

printf 'All step_06 read-orientation split smoke tests passed.\n'
