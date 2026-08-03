#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/step_03_infer_strandedness_and_orientation.sh"

# Keep this test self-contained and local-only. It uses placeholder BAM/BED
# files plus a fake infer_experiment.py, so no real biological data or RSeQC
# installation is required.

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

infer_log="$tmp_dir/infer_experiment_invocations.log"
# Fake enough of RSeQC to prove the wrapper builds the correct command and
# validates output behavior. The script under test is responsible for redirecting
# stdout to the final infer_experiment report file.
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

export PATH="$fake_bin:$PATH"

fixture_dir="$tmp_dir/fixtures"
mkdir -p "$fixture_dir"

# The real Step 03 requires only path existence for these fixtures before
# handing them to RSeQC, so tiny placeholders are enough for regression tests.
bam="$fixture_dir/sample.sorted.bam"
bam_dot_bai="$bam.bai"
bed12="$fixture_dir/genome.bed"
missing_bam="$fixture_dir/missing.sorted.bam"
missing_bed12="$fixture_dir/missing.bed"

printf 'placeholder bam\n' >"$bam"
printf 'placeholder index\n' >"$bam_dot_bai"
printf 'chr1\t0\t100\ttx1\t0\t+\t0\t100\t0\t1\t100,\t0,\n' >"$bed12"

printf 'Running syntax check...\n'
bash -n "$SCRIPT"

printf 'Running help check...\n'
help_output="$tmp_dir/help.out"
bash "$SCRIPT" --help >"$help_output"
assert_contains "$help_output" "Usage:"
assert_contains "$help_output" "--sample-id"
assert_contains "$help_output" "--input-bam"
assert_contains "$help_output" "--bed12"
assert_contains "$help_output" "--output-dir"
assert_contains "$help_output" "--infer-experiment-bin"
assert_contains "$help_output" "--execute"

printf 'Running dry-run check with path-style binary...\n'
dry_output="$tmp_dir/dry.out"
dry_output_dir="$tmp_dir/results/dry"
bash "$SCRIPT" \
    --sample-id sample_dry \
    --input-bam "$bam" \
    --bed12 "$bed12" \
    --output-dir "$dry_output_dir" \
    --infer-experiment-bin "$fake_bin/infer_experiment.py" \
    >"$dry_output"

dry_output_file="$dry_output_dir/sample_dry.infer_experiment.txt"
# Dry-run should validate inputs and print the command, but leave no results
# footprint for downstream workflow steps to mistake for completed output.
assert_not_exists "$dry_output_dir"
assert_not_exists "$dry_output_file"
[[ ! -e "$infer_log" ]] || fail "dry-run invoked infer_experiment.py"
assert_contains "$dry_output" "Mode: dry-run"
assert_contains "$dry_output" "Input BAM: $bam"
assert_contains "$dry_output" "BAM index found: $bam_dot_bai"
assert_contains "$dry_output" "BED12 annotation: $bed12"
assert_contains "$dry_output" "Output file: $dry_output_file"
assert_contains "$dry_output" "infer_experiment.py: $fake_bin/infer_experiment.py"
assert_contains "$dry_output" "-r"
assert_contains "$dry_output" "$bed12"
assert_contains "$dry_output" "-i"
assert_contains "$dry_output" "$bam"
assert_contains "$dry_output" "Dry-run only"

printf 'Running execute check with path-style binary...\n'
execute_output="$tmp_dir/execute.out"
execute_output_dir="$tmp_dir/results/execute"
bash "$SCRIPT" \
    --sample-id sample_execute \
    --input-bam "$bam" \
    --bed12 "$bed12" \
    --output-dir "$execute_output_dir" \
    --infer-experiment-bin "$fake_bin/infer_experiment.py" \
    --execute \
    >"$execute_output"

execute_output_file="$execute_output_dir/sample_execute.infer_experiment.txt"
[[ -s "$execute_output_file" ]] || fail "execute did not create non-empty infer_experiment output"
assert_contains "$execute_output_file" "This is PairEnd Data"
assert_contains "$execute_output_file" "Fraction of reads explained"
assert_contains "$infer_log" "infer_experiment.py invoked"
assert_contains "$infer_log" "-r"
assert_contains "$infer_log" "$bed12"
assert_contains "$infer_log" "-i"
assert_contains "$infer_log" "$bam"
assert_contains "$execute_output" "Mode: execute"
assert_contains "$execute_output" "RSeQC infer_experiment output preview:"
assert_contains "$execute_output" "This is PairEnd Data"

printf 'Running command-name binary lookup check...\n'
# Exercise the PATH-resolution branch separately from the explicit path branch.
command_name_output="$tmp_dir/command_name.out"
command_name_output_dir="$tmp_dir/results/command_name"
bash "$SCRIPT" \
    --sample-id sample_command_name \
    --input-bam "$bam" \
    --bed12 "$bed12" \
    --output-dir "$command_name_output_dir" \
    --infer-experiment-bin infer_experiment.py \
    --execute \
    >"$command_name_output"

command_name_output_file="$command_name_output_dir/sample_command_name.infer_experiment.txt"
[[ -s "$command_name_output_file" ]] || fail "command-name execute did not create output"
assert_contains "$command_name_output" "infer_experiment.py: infer_experiment.py"

printf 'Running explicit-binary arbitrary-CWD check...\n'
arbitrary_cwd="$tmp_dir/arbitrary-cwd"
mkdir -p "$arbitrary_cwd"
arbitrary_output="$tmp_dir/arbitrary.out"
arbitrary_output_dir="$tmp_dir/results/arbitrary"
(
    cd "$arbitrary_cwd"
    bash "$SCRIPT" \
        --sample-id sample_arbitrary \
        --input-bam "$bam" \
        --bed12 "$bed12" \
        --output-dir "$arbitrary_output_dir" \
        --infer-experiment-bin "$fake_bin/infer_experiment.py" \
        --execute \
        >"$arbitrary_output"
)
arbitrary_output_file="$arbitrary_output_dir/sample_arbitrary.infer_experiment.txt"
[[ -s "$arbitrary_output_file" ]] || fail "arbitrary-CWD execute did not create output"
assert_contains "$arbitrary_output" "infer_experiment.py: $fake_bin/infer_experiment.py"
assert_only_entries "$arbitrary_cwd"

printf 'Running missing BAM failure check...\n'
missing_bam_output="$tmp_dir/missing_bam.out"
assert_fails "$missing_bam_output" bash "$SCRIPT" \
    --sample-id sample_missing_bam \
    --input-bam "$missing_bam" \
    --bed12 "$bed12" \
    --output-dir "$tmp_dir/results/missing_bam" \
    --infer-experiment-bin "$fake_bin/infer_experiment.py"
assert_contains "$missing_bam_output" "BAM does not exist"

printf 'Running missing BAM index failure check...\n'
missing_index_bam="$fixture_dir/missing_index.sorted.bam"
printf 'placeholder bam\n' >"$missing_index_bam"
missing_index_output="$tmp_dir/missing_index.out"
assert_fails "$missing_index_output" bash "$SCRIPT" \
    --sample-id sample_missing_index \
    --input-bam "$missing_index_bam" \
    --bed12 "$bed12" \
    --output-dir "$tmp_dir/results/missing_index" \
    --infer-experiment-bin "$fake_bin/infer_experiment.py"
assert_contains "$missing_index_output" "BAM index does not exist"

printf 'Running missing BED12 failure check...\n'
missing_bed12_output="$tmp_dir/missing_bed12.out"
assert_fails "$missing_bed12_output" bash "$SCRIPT" \
    --sample-id sample_missing_bed12 \
    --input-bam "$bam" \
    --bed12 "$missing_bed12" \
    --output-dir "$tmp_dir/results/missing_bed12" \
    --infer-experiment-bin "$fake_bin/infer_experiment.py"
assert_contains "$missing_bed12_output" "BED12 annotation does not exist"

printf 'Running non-executable path-style binary failure check...\n'
# A path-like binary must be executable; this catches broken virtualenv installs
# more clearly than waiting for a later "permission denied" from the shell.
not_executable_bin="$tmp_dir/not_executable_infer_experiment.py"
printf '#!/usr/bin/env bash\n' >"$not_executable_bin"
nonexec_output="$tmp_dir/nonexec.out"
assert_fails "$nonexec_output" bash "$SCRIPT" \
    --sample-id sample_nonexec \
    --input-bam "$bam" \
    --bed12 "$bed12" \
    --output-dir "$tmp_dir/results/nonexec" \
    --infer-experiment-bin "$not_executable_bin"
assert_contains "$nonexec_output" "exists but is not executable"

printf 'Running output validation failure check...\n'
# RSeQC failures can include a zero exit with no useful report if the wrapper is
# misconfigured. Guard the pipeline by requiring a non-empty report file.
empty_output="$tmp_dir/empty.out"
empty_output_dir="$tmp_dir/results/empty"
assert_fails "$empty_output" env FAKE_INFER_MODE=empty_success bash "$SCRIPT" \
    --sample-id sample_empty \
    --input-bam "$bam" \
    --bed12 "$bed12" \
    --output-dir "$empty_output_dir" \
    --infer-experiment-bin "$fake_bin/infer_experiment.py" \
    --execute

empty_output_file="$empty_output_dir/sample_empty.infer_experiment.txt"
[[ ! -s "$empty_output_file" ]] || fail "empty output test unexpectedly created non-empty output"
assert_contains "$empty_output" "infer_experiment.py output is missing or empty"

printf 'Running nonempty malformed producer-success check...\n'
malformed_stdout="$tmp_dir/malformed.stdout"
malformed_stderr="$tmp_dir/malformed.stderr"
malformed_output_dir="$tmp_dir/results/malformed"
FAKE_INFER_MODE=malformed_success bash "$SCRIPT" \
    --sample-id sample_malformed \
    --input-bam "$bam" \
    --bed12 "$bed12" \
    --output-dir "$malformed_output_dir" \
    --infer-experiment-bin "$fake_bin/infer_experiment.py" \
    --execute \
    >"$malformed_stdout" 2>"$malformed_stderr"
malformed_output_file="$malformed_output_dir/sample_malformed.infer_experiment.txt"
assert_file_equals "$malformed_output_file" \
    $'This is PairEnd Data\nnonempty malformed orientation evidence\n'
assert_file_equals "$malformed_stderr" ''

printf 'Running predecessor-bearing partial child failure check...\n'
partial_stdout="$tmp_dir/partial.stdout"
partial_stderr="$tmp_dir/partial.stderr"
partial_output_dir="$tmp_dir/results/partial"
mkdir -p "$partial_output_dir"
partial_output_file="$partial_output_dir/sample_partial.infer_experiment.txt"
partial_unrelated="$partial_output_dir/unrelated.txt"
printf 'prior complete orientation report\n' >"$partial_output_file"
printf 'unrelated predecessor\n' >"$partial_unrelated"

set +e
FAKE_INFER_MODE=partial_fail bash "$SCRIPT" \
    --sample-id sample_partial \
    --input-bam "$bam" \
    --bed12 "$bed12" \
    --output-dir "$partial_output_dir" \
    --infer-experiment-bin "$fake_bin/infer_experiment.py" \
    --execute \
    >"$partial_stdout" 2>"$partial_stderr"
partial_status=$?
set -e

[[ "$partial_status" -eq 42 ]] ||
    fail "partial child exit 42 was not propagated: $partial_status"
assert_file_equals "$partial_output_file" $'partial RSeQC child bytes\n'
assert_file_equals "$partial_stderr" $'partial RSeQC failure diagnostic\n'
assert_file_equals "$partial_unrelated" $'unrelated predecessor\n'
assert_only_entries "$partial_output_dir" \
    "sample_partial.infer_experiment.txt" \
    "unrelated.txt"

printf 'Running predecessor-bearing empty-success truncation check...\n'
truncated_stdout="$tmp_dir/truncated.stdout"
truncated_stderr="$tmp_dir/truncated.stderr"
truncated_output_dir="$tmp_dir/results/truncated"
mkdir -p "$truncated_output_dir"
truncated_output_file="$truncated_output_dir/sample_truncated.infer_experiment.txt"
truncated_unrelated="$truncated_output_dir/unrelated.txt"
printf 'prior complete orientation report\n' >"$truncated_output_file"
printf 'unrelated predecessor\n' >"$truncated_unrelated"

set +e
FAKE_INFER_MODE=empty_success bash "$SCRIPT" \
    --sample-id sample_truncated \
    --input-bam "$bam" \
    --bed12 "$bed12" \
    --output-dir "$truncated_output_dir" \
    --infer-experiment-bin "$fake_bin/infer_experiment.py" \
    --execute \
    >"$truncated_stdout" 2>"$truncated_stderr"
truncated_status=$?
set -e

[[ "$truncated_status" -eq 1 ]] ||
    fail "empty child success did not become producer exit 1: $truncated_status"
[[ -f "$truncated_output_file" ]] || fail "empty child success removed the final path"
[[ ! -s "$truncated_output_file" ]] || fail "empty child success did not truncate predecessor"
assert_file_equals "$truncated_stderr" \
    "ERROR: infer_experiment.py output is missing or empty: $truncated_output_file"$'\n'
assert_file_equals "$truncated_unrelated" $'unrelated predecessor\n'
assert_only_entries "$truncated_output_dir" \
    "sample_truncated.infer_experiment.txt" \
    "unrelated.txt"

printf 'All step_03 RSeQC strandedness smoke tests passed.\n'
