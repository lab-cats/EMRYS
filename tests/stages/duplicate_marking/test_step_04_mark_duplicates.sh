#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/src/norad/stages/duplicate_marking/step_04_mark_duplicates.sh"

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
        fail "unexpected output"
    fi
}

assert_not_exists() {
    local path="$1"

    [[ ! -e "$path" ]] || fail "path should not exist: $path"
}

assert_exit() {
    local output_file="$1"
    local expected="$2"
    shift 2

    set +e
    "$@" >"$output_file" 2>&1
    local status=$?
    set -e
    if [[ "$status" -ne "$expected" ]]; then
        cat "$output_file" >&2
        fail "expected exit $expected, got $status: $*"
    fi
}

assert_file_content() {
    local path="$1"
    local expected="$2"

    [[ -f "$path" ]] || fail "expected file: $path"
    if ! printf '%s' "$expected" | cmp -s - "$path"; then
        printf 'Expected file content:\n%s' "$expected" >&2
        printf 'Actual file content:\n' >&2
        cat "$path" >&2
        fail "unexpected file content: $path"
    fi
}

assert_empty_file() {
    local path="$1"

    [[ -f "$path" ]] || fail "expected empty file: $path"
    [[ ! -s "$path" ]] || fail "file should be empty: $path"
}

assert_no_recovery_artifacts() {
    local root="$1"
    local found
    found="$(find "$root" -mindepth 1 \( \
        -name '*.lock' -o -name '*.tmp' -o -name '*.previous' -o \
        -name '*.backup' -o -name '*.receipt' -o -name '*recovery*' \
        \) -print)"
    [[ -z "$found" ]] || {
        printf 'Unexpected recovery artifact(s):\n%s\n' "$found" >&2
        fail "producer created recovery artifacts"
    }
}

prepare_predecessor() {
    local root="$1"
    local sample="$2"

    case_output_dir="$root/markdup"
    case_metrics_dir="$root/qc"
    case_output_bam="$case_output_dir/${sample}.markdup.bam"
    case_output_bai="$case_output_bam.bai"
    case_metrics="$case_metrics_dir/${sample}.markdup.metrics.txt"
    case_unrelated="$root/unrelated.keep"
    mkdir -p "$case_output_dir" "$case_metrics_dir"
    printf 'prior bam bytes\n' >"$case_output_bam"
    printf 'prior bai bytes\n' >"$case_output_bai"
    printf 'prior metrics bytes\n' >"$case_metrics"
    printf 'unrelated bytes\n' >"$case_unrelated"
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
export TMPDIR="$tmp_dir"
unset FAKE_JAVA_MODE FAKE_JAVA_MUTATE_INPUTS \
    FAKE_SAMTOOLS_QUICKCHECK_EXIT FAKE_SAMTOOLS_INDEX_EXIT

fake_bin="$tmp_dir/bin"
mkdir -p "$fake_bin"

java_log="$tmp_dir/java_invocations.log"
samtools_log="$tmp_dir/samtools_invocations.log"

cat >"$fake_bin/java" <<EOF_JAVA
#!/usr/bin/env bash
set -euo pipefail

printf 'java invoked\\n' >> "$java_log"
printf '%s\\n' "\$@" >> "$java_log"

if [[ "\${1:-}" != "-jar" ]]; then
    printf 'fake java expected -jar as first argument\\n' >&2
    exit 64
fi

if [[ "\${3:-}" != "MarkDuplicates" ]]; then
    printf 'fake java expected MarkDuplicates command\\n' >&2
    exit 64
fi

input_bam=""
output_bam=""
metrics_file=""
for arg in "\$@"; do
    case "\$arg" in
        INPUT=*)
            input_bam="\${arg#INPUT=}"
            ;;
        OUTPUT=*)
            output_bam="\${arg#OUTPUT=}"
            ;;
        METRICS_FILE=*)
            metrics_file="\${arg#METRICS_FILE=}"
            ;;
    esac
done

if [[ -z "\$output_bam" ]]; then
    printf 'fake java missing OUTPUT argument\\n' >&2
    exit 64
fi

if [[ -z "\$metrics_file" ]]; then
    printf 'fake java missing METRICS_FILE argument\\n' >&2
    exit 64
fi

mkdir -p "\$(dirname "\$output_bam")" "\$(dirname "\$metrics_file")"
case "\${FAKE_JAVA_MODE:-success}" in
    success)
        printf 'fake duplicate-marked bam\\n' > "\$output_bam"
        printf 'fake picard metrics\\n' > "\$metrics_file"
        ;;
    partial_failure)
        printf 'partial picard bam\\n' > "\$output_bam"
        printf 'partial picard metrics\\n' > "\$metrics_file"
        printf 'fake Picard partial failure\\n' >&2
        exit 42
        ;;
    empty_metrics)
        printf 'fake duplicate-marked bam\\n' > "\$output_bam"
        : > "\$metrics_file"
        ;;
    *)
        printf 'unknown FAKE_JAVA_MODE: %s\\n' "\${FAKE_JAVA_MODE}" >&2
        exit 64
        ;;
esac

if [[ "\${FAKE_JAVA_MUTATE_INPUTS:-0}" == "1" ]]; then
    [[ -n "\$input_bam" ]] || exit 64
    printf 'mutated admitted input bam\\n' > "\$input_bam"
    printf 'mutated admitted input bai\\n' > "\$input_bam.bai"
fi
EOF_JAVA
chmod +x "$fake_bin/java"

cat >"$fake_bin/samtools" <<EOF_SAMTOOLS
#!/usr/bin/env bash
set -euo pipefail

printf 'samtools invoked\\n' >> "$samtools_log"
printf '%s\\n' "\$@" >> "$samtools_log"

subcommand="\${1:-}"
shift || true

case "\$subcommand" in
    quickcheck)
        input_bam="\${1:-}"
        if [[ -z "\$input_bam" ]]; then
            printf 'fake samtools quickcheck missing input BAM\\n' >&2
            exit 64
        fi
        if [[ "\${FAKE_SAMTOOLS_QUICKCHECK_EXIT:-0}" != "0" ]]; then
            printf 'fake samtools quickcheck failure\\n' >&2
            exit "\${FAKE_SAMTOOLS_QUICKCHECK_EXIT}"
        fi
        [[ -s "\$input_bam" ]]
        ;;
    index)
        input_bam="\${1:-}"
        if [[ -z "\$input_bam" ]]; then
            printf 'fake samtools index missing input BAM\\n' >&2
            exit 64
        fi
        if [[ "\${FAKE_SAMTOOLS_INDEX_EXIT:-0}" != "0" ]]; then
            printf 'partial bam index\\n' > "\$input_bam.bai"
            printf 'fake samtools index failure\\n' >&2
            exit "\${FAKE_SAMTOOLS_INDEX_EXIT}"
        fi
        printf 'fake bam index\\n' > "\$input_bam.bai"
        ;;
    *)
        printf 'fake samtools unknown subcommand: %s\\n' "\$subcommand" >&2
        exit 64
        ;;
esac
EOF_SAMTOOLS
chmod +x "$fake_bin/samtools"

fixture_dir="$tmp_dir/fixtures"
mkdir -p "$fixture_dir"

input_bam="$fixture_dir/sample.sorted.bam"
input_bai="$input_bam.bai"
picard_jar="$fixture_dir/picard.jar"
missing_bam="$fixture_dir/missing.sorted.bam"
missing_picard="$fixture_dir/missing_picard.jar"

printf 'placeholder bam\n' >"$input_bam"
printf 'placeholder index\n' >"$input_bai"
printf 'placeholder jar\n' >"$picard_jar"

printf 'Running syntax check...\n'
bash -n "$SCRIPT"

printf 'Running help check...\n'
help_output="$tmp_dir/help.out"
bash "$SCRIPT" --help >"$help_output"
assert_contains "$help_output" "Usage:"
assert_contains "$help_output" "--sample-id"
assert_contains "$help_output" "--input-bam"
assert_contains "$help_output" "--output-dir"
assert_contains "$help_output" "--metrics-dir"
assert_contains "$help_output" "--picard-jar"
assert_contains "$help_output" "--java-bin"
assert_contains "$help_output" "--samtools-bin"
assert_contains "$help_output" "--execute"

printf 'Running dry-run check...\n'
dry_output="$tmp_dir/dry.out"
dry_output_dir="$tmp_dir/results/dry/markdup"
dry_metrics_dir="$tmp_dir/results/dry/qc"
bash "$SCRIPT" \
    --sample-id sample_dry \
    --input-bam "$input_bam" \
    --output-dir "$dry_output_dir" \
    --metrics-dir "$dry_metrics_dir" \
    --picard-jar "$picard_jar" \
    --java-bin "$fake_bin/java" \
    --samtools-bin "$fake_bin/samtools" \
    >"$dry_output"

dry_bam="$dry_output_dir/sample_dry.markdup.bam"
dry_bai="$dry_bam.bai"
dry_metrics="$dry_metrics_dir/sample_dry.markdup.metrics.txt"
assert_not_exists "$dry_output_dir"
assert_not_exists "$dry_metrics_dir"
assert_not_exists "$dry_bam"
assert_not_exists "$dry_bai"
assert_not_exists "$dry_metrics"
[[ ! -e "$java_log" ]] || fail "dry-run invoked java"
[[ ! -e "$samtools_log" ]] || fail "dry-run invoked samtools"
assert_contains "$dry_output" "Mode: dry-run"
assert_contains "$dry_output" "Input BAM: $input_bam"
assert_contains "$dry_output" "Input BAI: $input_bai"
assert_contains "$dry_output" "Output BAM: $dry_bam"
assert_contains "$dry_output" "Output BAI: $dry_bai"
assert_contains "$dry_output" "Metrics file: $dry_metrics"
assert_contains "$dry_output" "Java bin: $fake_bin/java"
assert_contains "$dry_output" "Picard jar: $picard_jar"
assert_contains "$dry_output" "samtools bin: $fake_bin/samtools"
assert_contains "$dry_output" "TMP_DIR: ${TMPDIR:-/tmp}"
assert_contains "$dry_output" "MarkDuplicates"
assert_contains "$dry_output" "INPUT=$input_bam"
assert_contains "$dry_output" "OUTPUT=$dry_bam"
assert_contains "$dry_output" "METRICS_FILE=$dry_metrics"
assert_contains "$dry_output" "REMOVE_DUPLICATES=false"
assert_contains "$dry_output" "TMP_DIR=${TMPDIR:-/tmp}"
assert_contains "$dry_output" "quickcheck"
assert_contains "$dry_output" "index"
assert_contains "$dry_output" "Dry-run only"

printf 'Running execute check...\n'
execute_output="$tmp_dir/execute.out"
execute_output_dir="$tmp_dir/results/execute/markdup"
execute_metrics_dir="$tmp_dir/results/execute/qc"
bash "$SCRIPT" \
    --sample-id sample_execute \
    --input-bam "$input_bam" \
    --output-dir "$execute_output_dir" \
    --metrics-dir "$execute_metrics_dir" \
    --picard-jar "$picard_jar" \
    --java-bin "$fake_bin/java" \
    --samtools-bin "$fake_bin/samtools" \
    --execute \
    >"$execute_output"

execute_bam="$execute_output_dir/sample_execute.markdup.bam"
execute_bai="$execute_bam.bai"
execute_metrics="$execute_metrics_dir/sample_execute.markdup.metrics.txt"
[[ -s "$execute_bam" ]] || fail "execute did not create non-empty markdup BAM"
[[ -s "$execute_bai" ]] || fail "execute did not create non-empty BAM index"
[[ -s "$execute_metrics" ]] || fail "execute did not create non-empty metrics file"
assert_contains "$java_log" "java invoked"
assert_contains "$java_log" "-jar"
assert_contains "$java_log" "$picard_jar"
assert_contains "$java_log" "MarkDuplicates"
assert_contains "$java_log" "INPUT=$input_bam"
assert_contains "$java_log" "OUTPUT=$execute_bam"
assert_contains "$java_log" "METRICS_FILE=$execute_metrics"
assert_contains "$java_log" "REMOVE_DUPLICATES=false"
assert_contains "$java_log" "TMP_DIR=${TMPDIR:-/tmp}"
assert_contains "$samtools_log" "samtools invoked"
assert_contains "$samtools_log" "quickcheck"
assert_contains "$samtools_log" "$execute_bam"
assert_contains "$samtools_log" "index"
assert_contains "$execute_output" "Mode: execute"
assert_contains "$execute_output" "Picard MarkDuplicates output details:"

printf 'Running missing BAM failure check...\n'
missing_bam_output="$tmp_dir/missing_bam.out"
assert_exit "$missing_bam_output" 1 bash "$SCRIPT" \
    --sample-id sample_missing_bam \
    --input-bam "$missing_bam" \
    --output-dir "$tmp_dir/results/missing_bam/markdup" \
    --metrics-dir "$tmp_dir/results/missing_bam/qc" \
    --picard-jar "$picard_jar" \
    --java-bin "$fake_bin/java" \
    --samtools-bin "$fake_bin/samtools"
assert_contains "$missing_bam_output" "Input BAM does not exist"

printf 'Running missing BAM index failure check...\n'
missing_index_bam="$fixture_dir/missing_index.sorted.bam"
printf 'placeholder bam\n' >"$missing_index_bam"
missing_index_output="$tmp_dir/missing_index.out"
assert_exit "$missing_index_output" 1 bash "$SCRIPT" \
    --sample-id sample_missing_index \
    --input-bam "$missing_index_bam" \
    --output-dir "$tmp_dir/results/missing_index/markdup" \
    --metrics-dir "$tmp_dir/results/missing_index/qc" \
    --picard-jar "$picard_jar" \
    --java-bin "$fake_bin/java" \
    --samtools-bin "$fake_bin/samtools"
assert_contains "$missing_index_output" "Input BAM index does not exist"

printf 'Running missing Picard jar failure check...\n'
missing_picard_output="$tmp_dir/missing_picard.out"
assert_exit "$missing_picard_output" 1 bash "$SCRIPT" \
    --sample-id sample_missing_picard \
    --input-bam "$input_bam" \
    --output-dir "$tmp_dir/results/missing_picard/markdup" \
    --metrics-dir "$tmp_dir/results/missing_picard/qc" \
    --picard-jar "$missing_picard" \
    --java-bin "$fake_bin/java" \
    --samtools-bin "$fake_bin/samtools"
assert_contains "$missing_picard_output" "Picard jar does not exist"

printf 'Running bad TMP_DIR failure check...\n'
bad_tmp_output="$tmp_dir/bad_tmp.out"
assert_exit "$bad_tmp_output" 2 env TMPDIR="$tmp_dir/missing_tmp" bash "$SCRIPT" \
    --sample-id sample_bad_tmp \
    --input-bam "$input_bam" \
    --output-dir "$tmp_dir/results/bad_tmp/markdup" \
    --metrics-dir "$tmp_dir/results/bad_tmp/qc" \
    --picard-jar "$picard_jar" \
    --java-bin "$fake_bin/java" \
    --samtools-bin "$fake_bin/samtools"
assert_contains "$bad_tmp_output" "TMP_DIR does not exist or is not a directory"

printf 'Running predecessor-bearing Picard partial failure check...\n'
prepare_predecessor "$tmp_dir/results/picard_failure" sample_picard_failure
picard_failure_output="$tmp_dir/picard_failure.out"
rm -f "$java_log" "$samtools_log"
assert_exit "$picard_failure_output" 42 env \
    FAKE_JAVA_MODE=partial_failure bash "$SCRIPT" \
    --sample-id sample_picard_failure \
    --input-bam "$input_bam" \
    --output-dir "$case_output_dir" \
    --metrics-dir "$case_metrics_dir" \
    --picard-jar "$picard_jar" \
    --java-bin "$fake_bin/java" \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_file_content "$case_output_bam" $'partial picard bam\n'
assert_file_content "$case_output_bai" $'prior bai bytes\n'
assert_file_content "$case_metrics" $'partial picard metrics\n'
assert_file_content "$case_unrelated" $'unrelated bytes\n'
assert_contains "$picard_failure_output" "fake Picard partial failure"
assert_not_exists "$samtools_log"
assert_no_recovery_artifacts "$tmp_dir/results/picard_failure"

printf 'Running predecessor-bearing quickcheck failure check...\n'
prepare_predecessor "$tmp_dir/results/quickcheck_failure" sample_quickcheck_failure
quickcheck_failure_output="$tmp_dir/quickcheck_failure.out"
rm -f "$java_log" "$samtools_log"
assert_exit "$quickcheck_failure_output" 43 env \
    FAKE_SAMTOOLS_QUICKCHECK_EXIT=43 bash "$SCRIPT" \
    --sample-id sample_quickcheck_failure \
    --input-bam "$input_bam" \
    --output-dir "$case_output_dir" \
    --metrics-dir "$case_metrics_dir" \
    --picard-jar "$picard_jar" \
    --java-bin "$fake_bin/java" \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_file_content "$case_output_bam" $'fake duplicate-marked bam\n'
assert_file_content "$case_output_bai" $'prior bai bytes\n'
assert_file_content "$case_metrics" $'fake picard metrics\n'
assert_file_content "$case_unrelated" $'unrelated bytes\n'
assert_contains "$quickcheck_failure_output" "fake samtools quickcheck failure"
assert_contains "$samtools_log" "quickcheck"
assert_not_contains "$samtools_log" "index"
assert_no_recovery_artifacts "$tmp_dir/results/quickcheck_failure"

printf 'Running predecessor-bearing index failure check...\n'
prepare_predecessor "$tmp_dir/results/index_failure" sample_index_failure
index_failure_output="$tmp_dir/index_failure.out"
rm -f "$java_log" "$samtools_log"
assert_exit "$index_failure_output" 44 env \
    FAKE_SAMTOOLS_INDEX_EXIT=44 bash "$SCRIPT" \
    --sample-id sample_index_failure \
    --input-bam "$input_bam" \
    --output-dir "$case_output_dir" \
    --metrics-dir "$case_metrics_dir" \
    --picard-jar "$picard_jar" \
    --java-bin "$fake_bin/java" \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_file_content "$case_output_bam" $'fake duplicate-marked bam\n'
assert_file_content "$case_output_bai" $'partial bam index\n'
assert_file_content "$case_metrics" $'fake picard metrics\n'
assert_file_content "$case_unrelated" $'unrelated bytes\n'
assert_contains "$index_failure_output" "fake samtools index failure"
assert_contains "$samtools_log" "quickcheck"
assert_contains "$samtools_log" "index"
assert_no_recovery_artifacts "$tmp_dir/results/index_failure"

printf 'Running empty metrics final-check failure check...\n'
prepare_predecessor "$tmp_dir/results/empty_metrics" sample_empty_metrics
empty_metrics_output="$tmp_dir/empty_metrics.out"
rm -f "$java_log" "$samtools_log"
assert_exit "$empty_metrics_output" 1 env \
    FAKE_JAVA_MODE=empty_metrics bash "$SCRIPT" \
    --sample-id sample_empty_metrics \
    --input-bam "$input_bam" \
    --output-dir "$case_output_dir" \
    --metrics-dir "$case_metrics_dir" \
    --picard-jar "$picard_jar" \
    --java-bin "$fake_bin/java" \
    --samtools-bin "$fake_bin/samtools" \
    --execute
assert_file_content "$case_output_bam" $'fake duplicate-marked bam\n'
assert_file_content "$case_output_bai" $'fake bam index\n'
assert_empty_file "$case_metrics"
assert_file_content "$case_unrelated" $'unrelated bytes\n'
assert_contains "$empty_metrics_output" "Picard metrics file is missing or empty"
assert_no_recovery_artifacts "$tmp_dir/results/empty_metrics"

printf 'Running arbitrary-CWD explicit-tool execute check...\n'
arbitrary_cwd="$tmp_dir/arbitrary-cwd"
arbitrary_output_dir="$tmp_dir/results/arbitrary/markdup"
arbitrary_metrics_dir="$tmp_dir/results/arbitrary/qc"
arbitrary_output="$tmp_dir/arbitrary.out"
mkdir -p "$arbitrary_cwd"
rm -f "$java_log" "$samtools_log"
(
    cd "$arbitrary_cwd"
    bash "$SCRIPT" \
        --sample-id sample_arbitrary \
        --input-bam "$input_bam" \
        --output-dir "$arbitrary_output_dir" \
        --metrics-dir "$arbitrary_metrics_dir" \
        --picard-jar "$picard_jar" \
        --java-bin "$fake_bin/java" \
        --samtools-bin "$fake_bin/samtools" \
        --execute >"$arbitrary_output" 2>&1
)
assert_file_content "$arbitrary_output_dir/sample_arbitrary.markdup.bam" \
    $'fake duplicate-marked bam\n'
assert_file_content "$arbitrary_output_dir/sample_arbitrary.markdup.bam.bai" \
    $'fake bam index\n'
assert_file_content "$arbitrary_metrics_dir/sample_arbitrary.markdup.metrics.txt" \
    $'fake picard metrics\n'
assert_contains "$arbitrary_output" "Mode: execute"

printf 'Running missing explicit samtools pre-directory failure check...\n'
missing_samtools_output="$tmp_dir/missing_samtools.out"
missing_samtools_output_dir="$tmp_dir/results/missing_samtools/markdup"
missing_samtools_metrics_dir="$tmp_dir/results/missing_samtools/qc"
assert_exit "$missing_samtools_output" 1 bash "$SCRIPT" \
    --sample-id sample_missing_samtools \
    --input-bam "$input_bam" \
    --output-dir "$missing_samtools_output_dir" \
    --metrics-dir "$missing_samtools_metrics_dir" \
    --picard-jar "$picard_jar" \
    --java-bin "$fake_bin/java" \
    --samtools-bin "$tmp_dir/missing-tools/samtools" \
    --execute
assert_contains "$missing_samtools_output" "samtools does not exist"
assert_not_exists "$missing_samtools_output_dir"
assert_not_exists "$missing_samtools_metrics_dir"

printf 'Running admitted-input mutation defect check...\n'
mutation_root="$tmp_dir/results/input_mutation"
mutation_input="$mutation_root/input/sample.sorted.bam"
mutation_output_dir="$mutation_root/markdup"
mutation_metrics_dir="$mutation_root/qc"
mutation_output="$tmp_dir/input_mutation.out"
mkdir -p "$(dirname "$mutation_input")"
printf 'original admitted input bam\n' >"$mutation_input"
printf 'original admitted input bai\n' >"$mutation_input.bai"
printf 'unrelated bytes\n' >"$mutation_root/unrelated.keep"
rm -f "$java_log" "$samtools_log"
env FAKE_JAVA_MUTATE_INPUTS=1 bash "$SCRIPT" \
    --sample-id sample_input_mutation \
    --input-bam "$mutation_input" \
    --output-dir "$mutation_output_dir" \
    --metrics-dir "$mutation_metrics_dir" \
    --picard-jar "$picard_jar" \
    --java-bin "$fake_bin/java" \
    --samtools-bin "$fake_bin/samtools" \
    --execute >"$mutation_output" 2>&1
assert_file_content "$mutation_input" $'mutated admitted input bam\n'
assert_file_content "$mutation_input.bai" $'mutated admitted input bai\n'
assert_file_content "$mutation_output_dir/sample_input_mutation.markdup.bam" \
    $'fake duplicate-marked bam\n'
assert_file_content "$mutation_output_dir/sample_input_mutation.markdup.bam.bai" \
    $'fake bam index\n'
assert_file_content "$mutation_metrics_dir/sample_input_mutation.markdup.metrics.txt" \
    $'fake picard metrics\n'
assert_file_content "$mutation_root/unrelated.keep" $'unrelated bytes\n'
assert_contains "$mutation_output" "Picard MarkDuplicates output details:"
assert_no_recovery_artifacts "$mutation_root"

printf 'All step_04 Picard MarkDuplicates smoke tests passed.\n'
