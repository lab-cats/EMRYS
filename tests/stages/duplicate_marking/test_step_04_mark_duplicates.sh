#!/usr/bin/env bash
# Native scientific behavior only; task-runner tests own publication and recovery.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPT="$repo_root/src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh"
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
java_log="$tmp_dir/java.log"
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

EOF_JAVA
chmod +x "$fake_bin/java"

samtools_log="$tmp_dir/samtools.log"
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

bam="$tmp_dir/inputs/sample.bam"
printf 'BAM\n' >"$bam"
printf 'BAI\n' >"$bam.bai"
printf 'Picard\n' >"$tmp_dir/inputs/picard.jar"
mkdir "$tmp_dir/metrics"
command=(bash "$SCRIPT" --sample-id sample --input-bam "$bam"
    --output-dir "$tmp_dir/staged" --metrics-dir "$tmp_dir/metrics"
    --picard-jar "$tmp_dir/inputs/picard.jar" --java-bin "$fake_bin/java" --samtools-bin "$fake_bin/samtools")
"${command[@]}"
for path in "$tmp_dir/staged/sample.markdup.bam" "$tmp_dir/staged/sample.markdup.bam.bai" "$tmp_dir/metrics/sample.markdup.metrics.txt"; do
    [[ -s "$path" ]] || fail "missing output: $path"
done
assert_contains "$java_log" 'REMOVE_DUPLICATES=false'
assert_contains "$java_log" "TMP_DIR=$EMRYS_TASK_WORK_DIR"
assert_fails 'Picard metrics does not exist or is empty' env FAKE_JAVA_MODE=empty_metrics "${command[@]}"
assert_fails 'fake samtools quickcheck failure' env FAKE_SAMTOOLS_QUICKCHECK_EXIT=42 "${command[@]}"
assert_fails 'requires EMRYS_TASK_WORK_DIR' env -u EMRYS_TASK_WORK_DIR "${command[@]}"
printf 'Native worker checks passed.\n'
