#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/step_04_mark_duplicates.sh"

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

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

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

output_bam=""
metrics_file=""
for arg in "\$@"; do
    case "\$arg" in
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
printf 'fake duplicate-marked bam\\n' > "\$output_bam"
printf 'fake picard metrics\\n' > "\$metrics_file"
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
        [[ -s "\$input_bam" ]]
        ;;
    index)
        input_bam="\${1:-}"
        if [[ -z "\$input_bam" ]]; then
            printf 'fake samtools index missing input BAM\\n' >&2
            exit 64
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

export PATH="$fake_bin:$PATH"

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
assert_fails "$missing_bam_output" bash "$SCRIPT" \
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
assert_fails "$missing_index_output" bash "$SCRIPT" \
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
assert_fails "$missing_picard_output" bash "$SCRIPT" \
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
assert_fails "$bad_tmp_output" env TMPDIR="$tmp_dir/missing_tmp" bash "$SCRIPT" \
    --sample-id sample_bad_tmp \
    --input-bam "$input_bam" \
    --output-dir "$tmp_dir/results/bad_tmp/markdup" \
    --metrics-dir "$tmp_dir/results/bad_tmp/qc" \
    --picard-jar "$picard_jar" \
    --java-bin "$fake_bin/java" \
    --samtools-bin "$fake_bin/samtools"
assert_contains "$bad_tmp_output" "TMP_DIR does not exist or is not a directory"

printf 'All step_04 Picard MarkDuplicates smoke tests passed.\n'
