#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/src/norad/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh"
JOB="$REPO_ROOT/src/norad/stages/fasta_sidecars/step_00c_prepare_gatk_reference.slurm"

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

write_fasta() {
    local fasta="$1"

    mkdir -p "$(dirname "$fasta")"
    {
        printf '>chrA\n'
        printf 'ACGTAC\n'
        printf '>chrB description\n'
        printf 'TTAA\n'
    } >"$fasta"
}

write_valid_sidecars() {
    local fasta="$1"
    local fai="$fasta.fai"
    local dict_dir
    local dict

    dict_dir="$(dirname "$fasta")"
    dict="$dict_dir/$(basename "${fasta%.*}").dict"

    printf 'chrA\t6\t0\t0\t0\nchrB\t4\t0\t0\t0\n' >"$fai"
    {
        printf '@HD\tVN:1.6\n'
        printf '@SQ\tSN:chrA\tLN:6\n'
        printf '@SQ\tSN:chrB\tLN:4\n'
    } >"$dict"
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

fake_bin="$tmp_dir/bin"
mkdir -p "$fake_bin"

samtools_log="$tmp_dir/samtools_invocations.log"
gatk_log="$tmp_dir/gatk_invocations.log"
java_log="$tmp_dir/java_invocations.log"

cat >"$fake_bin/java" <<EOF_JAVA
#!/usr/bin/env bash
set -euo pipefail

printf 'java invoked\\n' >> "$java_log"
printf '%s\\n' "\$@" >> "$java_log"

major="\${FAKE_JAVA_MAJOR:-17}"
printf 'openjdk version "%s.0.14" 2026-01-01\\n' "\$major" >&2
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
    --version)
        printf 'samtools 1.19.2\\n'
        ;;
    faidx)
        fasta="\${1:-}"
        if [[ -z "\$fasta" ]]; then
            printf 'fake samtools faidx expected FASTA\\n' >&2
            exit 64
        fi
        output="\$fasta.fai"
        awk '
            /^>/ {
                if (name != "") {
                    print name "\t" length_sum "\t0\t0\t0"
                }
                name = substr(\$0, 2)
                sub(/[[:space:]].*/, "", name)
                length_sum = 0
                next
            }
            {
                gsub(/[[:space:]]/, "")
                length_sum += length(\$0)
            }
            END {
                if (name != "") {
                    print name "\t" length_sum "\t0\t0\t0"
                }
            }
        ' "\$fasta" > "\$output"
        ;;
    *)
        printf 'fake samtools unknown subcommand: %s\\n' "\$subcommand" >&2
        exit 64
        ;;
esac
EOF_SAMTOOLS
chmod +x "$fake_bin/samtools"

cat >"$fake_bin/gatk" <<EOF_GATK
#!/usr/bin/env bash
set -euo pipefail

printf 'gatk invoked\\n' >> "$gatk_log"
printf '%s\\n' "\$@" >> "$gatk_log"

subcommand="\${1:-}"
shift || true

case "\$subcommand" in
    --version)
        printf '4.6.1.0\\n'
        ;;
    CreateSequenceDictionary)
        fasta=""
        output=""
        while [[ \$# -gt 0 ]]; do
            case "\$1" in
                -R)
                    fasta="\${2:-}"
                    shift 2
                    ;;
                -O)
                    output="\${2:-}"
                    shift 2
                    ;;
                *)
                    printf 'fake gatk unknown argument: %s\\n' "\$1" >&2
                    exit 64
                    ;;
            esac
        done
        if [[ -z "\$fasta" || -z "\$output" ]]; then
            printf 'fake gatk missing -R or -O\\n' >&2
            exit 64
        fi
        {
            printf '@HD\\tVN:1.6\\n'
            awk '
                /^>/ {
                    if (name != "") {
                        print "@SQ\tSN:" name "\tLN:" length_sum
                    }
                    name = substr(\$0, 2)
                    sub(/[[:space:]].*/, "", name)
                    length_sum = 0
                    next
                }
                {
                    gsub(/[[:space:]]/, "")
                    length_sum += length(\$0)
                }
                END {
                    if (name != "") {
                        print "@SQ\tSN:" name "\tLN:" length_sum
                    }
                }
            ' "\$fasta"
        } > "\$output"
        ;;
    *)
        printf 'fake gatk unknown subcommand: %s\\n' "\$subcommand" >&2
        exit 64
        ;;
esac
EOF_GATK
chmod +x "$fake_bin/gatk"

export PATH="$fake_bin:$PATH"

fixture_dir="$tmp_dir/fixtures"
reference_fasta="$fixture_dir/ref/genome.fa"
write_fasta "$reference_fasta"

printf 'Running syntax checks...\n'
bash -n "$SCRIPT"
bash -n "$JOB"

assert_contains "$JOB" 'export TMPDIR="${NORAD_TMPDIR:-/tmp}"'
assert_not_contains "$JOB" 'export TMPDIR="${TMPDIR:-/tmp}"'
assert_contains "$JOB" 'source "${NORAD_SITE_CONFIG:-configs/sites/csu.env}"'
assert_contains "$JOB" 'module load "$SAMTOOLS_MODULE"'
assert_not_contains "$JOB" 'module load "$JAVA_MODULE"'

printf 'Running help check...\n'
help_output="$tmp_dir/help.out"
bash "$SCRIPT" --help >"$help_output"
assert_contains "$help_output" "Usage:"
assert_contains "$help_output" "--reference-fasta"
assert_contains "$help_output" "--samtools-bin"
assert_contains "$help_output" "--gatk-bin"
assert_contains "$help_output" "--java-bin"
assert_contains "$help_output" "--execute"

printf 'Running missing argument failure check...\n'
missing_arg_output="$tmp_dir/missing_arg.out"
assert_fails "$missing_arg_output" bash "$SCRIPT" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java"
assert_contains "$missing_arg_output" "Missing required argument: --reference-fasta"

printf 'Running missing FASTA failure check...\n'
missing_fasta_output="$tmp_dir/missing_fasta.out"
assert_fails "$missing_fasta_output" bash "$SCRIPT" \
    --reference-fasta "$fixture_dir/missing/genome.fa" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java"
assert_contains "$missing_fasta_output" "Reference FASTA does not exist or is empty"

printf 'Running dry-run check...\n'
dry_dir="$tmp_dir/dry"
dry_fasta="$dry_dir/genome.fa"
write_fasta "$dry_fasta"
dry_output="$tmp_dir/dry.out"
bash "$SCRIPT" \
    --reference-fasta "$dry_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    >"$dry_output"

assert_not_exists "$dry_fasta.fai"
assert_not_exists "$dry_dir/genome.dict"
assert_not_exists "$dry_dir/.step_00c_prepare_gatk_reference.lock"
assert_not_exists "$samtools_log"
assert_not_exists "$gatk_log"
assert_not_exists "$java_log"
assert_contains "$dry_output" "Mode: dry-run"
assert_contains "$dry_output" "Reference FASTA: $dry_fasta"
assert_contains "$dry_output" "FASTA index: $dry_fasta.fai"
assert_contains "$dry_output" "Sequence dictionary: $dry_dir/genome.dict"
assert_contains "$dry_output" "samtools faidx command:"
assert_contains "$dry_output" "faidx"
assert_contains "$dry_output" "Temporary FASTA symlink for faidx:"
assert_contains "$dry_output" "GATK CreateSequenceDictionary command:"
assert_contains "$dry_output" "CreateSequenceDictionary"
assert_contains "$dry_output" "Validation plan:"
assert_contains "$dry_output" "Dry-run only"

printf 'Running execute creation check...\n'
execute_dir="$tmp_dir/execute"
execute_fasta="$execute_dir/genome.fa"
write_fasta "$execute_fasta"
execute_output="$tmp_dir/execute.out"
bash "$SCRIPT" \
    --reference-fasta "$execute_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    --execute \
    >"$execute_output"

[[ -s "$execute_fasta.fai" ]] || fail "execute did not create non-empty FASTA index"
[[ -s "$execute_dir/genome.dict" ]] || fail "execute did not create non-empty sequence dictionary"
assert_not_exists "$execute_dir/.step_00c_prepare_gatk_reference.lock"
assert_contains "$samtools_log" "faidx"
assert_contains "$gatk_log" "CreateSequenceDictionary"
assert_contains "$gatk_log" "-R"
assert_contains "$gatk_log" "$execute_fasta"
assert_contains "$gatk_log" "-O"
assert_contains "$java_log" "-version"
assert_contains "$execute_output" "Mode: execute"
assert_contains "$execute_output" "GATK reference sidecar output details:"
assert_contains "$execute_output" "Created missing Step 00c sidecars successfully."

printf 'Running existing valid sidecar reuse check...\n'
reuse_dir="$tmp_dir/reuse"
reuse_fasta="$reuse_dir/genome.fa"
write_fasta "$reuse_fasta"
write_valid_sidecars "$reuse_fasta"
rm -f "$samtools_log" "$gatk_log" "$java_log"
reuse_output="$tmp_dir/reuse.out"
bash "$SCRIPT" \
    --reference-fasta "$reuse_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    --execute \
    >"$reuse_output"
assert_not_exists "$samtools_log"
assert_contains "$gatk_log" "--version"
assert_contains "$java_log" "-version"
assert_contains "$reuse_output" "Existing GATK reference sidecars are already present and valid"

printf 'Running one-missing-sidecar creation check...\n'
one_missing_dir="$tmp_dir/one_missing"
one_missing_fasta="$one_missing_dir/genome.fa"
write_fasta "$one_missing_fasta"
printf 'chrA\t6\t0\t0\t0\nchrB\t4\t0\t0\t0\n' >"$one_missing_fasta.fai"
rm -f "$samtools_log" "$gatk_log" "$java_log"
one_missing_output="$tmp_dir/one_missing.out"
bash "$SCRIPT" \
    --reference-fasta "$one_missing_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    --execute \
    >"$one_missing_output"
assert_not_exists "$samtools_log"
assert_contains "$gatk_log" "CreateSequenceDictionary"
[[ -s "$one_missing_dir/genome.dict" ]] || fail "one-missing check did not create dictionary"

printf 'Running mismatched sidecar failure check...\n'
mismatch_dir="$tmp_dir/mismatch"
mismatch_fasta="$mismatch_dir/genome.fa"
write_fasta "$mismatch_fasta"
printf 'chrA\t6\t0\t0\t0\n' >"$mismatch_fasta.fai"
{
    printf '@HD\tVN:1.6\n'
    printf '@SQ\tSN:chrA\tLN:7\n'
} >"$mismatch_dir/genome.dict"
mismatch_output="$tmp_dir/mismatch.out"
assert_fails "$mismatch_output" bash "$SCRIPT" \
    --reference-fasta "$mismatch_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java"
assert_contains "$mismatch_output" "do not agree"

printf 'Running Java version failure check...\n'
java_fail_dir="$tmp_dir/java_fail"
java_fail_fasta="$java_fail_dir/genome.fa"
write_fasta "$java_fail_fasta"
java_fail_output="$tmp_dir/java_fail.out"
assert_fails "$java_fail_output" env FAKE_JAVA_MAJOR=11 bash "$SCRIPT" \
    --reference-fasta "$java_fail_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    --execute
assert_contains "$java_fail_output" "requires Java 17 or newer"
assert_not_exists "$java_fail_dir/.step_00c_prepare_gatk_reference.lock"
assert_not_exists "$java_fail_fasta.fai"
assert_not_exists "$java_fail_dir/genome.dict"

printf 'Running lock failure check...\n'
lock_dir="$tmp_dir/lock"
lock_fasta="$lock_dir/genome.fa"
write_fasta "$lock_fasta"
mkdir -p "$lock_dir/.step_00c_prepare_gatk_reference.lock"
printf 'test-owner\n' >"$lock_dir/.step_00c_prepare_gatk_reference.lock/owner"
lock_output="$tmp_dir/lock.out"
assert_fails "$lock_output" bash "$SCRIPT" \
    --reference-fasta "$lock_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    --execute
assert_contains "$lock_output" "lock already exists"
assert_contains "$lock_output" "test-owner"
assert_not_exists "$lock_fasta.fai"
assert_not_exists "$lock_dir/genome.dict"

printf 'Running partial final publication failure check...\n'
real_mv_bin="$(command -v mv)"
cat >"$fake_bin/mv" <<'EOF_MV'
#!/usr/bin/env bash
set -euo pipefail

destination="${!#}"
if [[ -n "${FAIL_MV_DESTINATION:-}" && "$destination" == "$FAIL_MV_DESTINATION" ]]; then
    printf 'controlled final DICT publication failure: %s\n' "$destination" >&2
    exit 73
fi
exec "$REAL_MV_BIN" "$@"
EOF_MV
chmod +x "$fake_bin/mv"

partial_dir="$tmp_dir/partial_publication"
partial_fasta="$partial_dir/genome.fa"
partial_dict="$partial_dir/genome.dict"
partial_run_token="partial-publication"
write_fasta "$partial_fasta"
partial_output="$tmp_dir/partial_publication.out"
set +e
REAL_MV_BIN="$real_mv_bin" \
FAIL_MV_DESTINATION="$partial_dict" \
SLURM_JOB_ID="$partial_run_token" \
bash "$SCRIPT" \
    --reference-fasta "$partial_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    --execute >"$partial_output" 2>&1
partial_status=$?
set -e

[[ "$partial_status" -eq 73 ]] || fail "partial publication exit was $partial_status, expected 73"
[[ -s "$partial_fasta.fai" ]] || fail "partial publication did not retain final FAI"
assert_not_exists "$partial_dict"
assert_not_exists "$partial_dir/.step_00c_prepare_gatk_reference.lock"
assert_not_exists "$partial_fasta.fai.tmp.$partial_run_token"
assert_not_exists "$partial_dict.tmp.$partial_run_token"
assert_not_exists "$partial_fasta.tmp.$partial_run_token.faidx_input"
assert_not_exists "$partial_fasta.tmp.$partial_run_token.faidx_input.fai"
assert_contains "$partial_output" "controlled final DICT publication failure"

printf 'Running SLURM spool-copy wrapper check...\n'
spool_dir="$tmp_dir/slurm-spool"
mkdir -p "$spool_dir"
spool_job="$spool_dir/slurm_script"
cp "$JOB" "$spool_job"

spool_output="$tmp_dir/slurm-spool.out"
set +e
SLURM_SUBMIT_DIR="$REPO_ROOT" \
REFERENCE_FASTA="$reference_fasta" \
SAMTOOLS_BIN_OVERRIDE="$fake_bin/samtools" \
GATK_BIN_OVERRIDE="$fake_bin/gatk" \
JAVA_BIN_OVERRIDE="$fake_bin/java" \
bash "$spool_job" >"$spool_output" 2>&1
spool_status=$?
set -e

if [[ "$spool_status" -ne 0 ]]; then
    cat "$spool_output" >&2
    fail "SLURM spool-copy wrapper exited $spool_status, expected 0"
fi

assert_contains "$spool_output" "Step 00c completed in dry-run mode"

printf 'Running stale Step 05 path check...\n'
stale_output="$tmp_dir/stale.out"
if grep -F "sorted.md" "$SCRIPT" "$JOB" >"$stale_output"; then
    cat "$stale_output" >&2
    fail "Step 00c files should not use stale Step 05 sorted.md paths"
fi
assert_not_contains "$dry_output" "sorted.md"
assert_not_contains "$execute_output" "sorted.md"

printf 'All step_00c GATK reference-prep smoke tests passed.\n'
