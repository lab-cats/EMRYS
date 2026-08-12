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
        if [[ -n "\${FAKE_MUTATE_REFERENCE_FASTA:-}" ]]; then
            printf '>chrA\\nMUTATED\\n' >"\$fasta"
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

printf 'Running unsafe run-token rejection check...\n'
unsafe_token_dir="$tmp_dir/unsafe_token"
unsafe_token_fasta="$unsafe_token_dir/genome.fa"
write_fasta "$unsafe_token_fasta"
unsafe_token_output="$tmp_dir/unsafe_token.out"
set +e
SLURM_JOB_ID='../unsafe-token' \
bash "$SCRIPT" \
    --reference-fasta "$unsafe_token_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    >"$unsafe_token_output" 2>&1
unsafe_token_status=$?
set -e

[[ "$unsafe_token_status" -ne 0 ]] || fail "unsafe Step 00c run token unexpectedly succeeded"
assert_contains "$unsafe_token_output" "Step 00c run token must match"
assert_not_exists "$unsafe_token_fasta.fai"
assert_not_exists "$unsafe_token_dir/genome.dict"
assert_not_exists "$unsafe_token_dir/.step_00c_prepare_gatk_reference.lock"

printf 'Running older-attempt staging-residue rejection check...\n'
older_residue_dir="$tmp_dir/older_residue"
older_residue_fasta="$older_residue_dir/genome.fa"
older_residue_path="$older_residue_fasta.fai.tmp.older-attempt"
write_fasta "$older_residue_fasta"
printf 'preserve older Step 00c residue\n' >"$older_residue_path"
older_residue_output="$tmp_dir/older_residue.out"
set +e
SLURM_JOB_ID='current-attempt' \
bash "$SCRIPT" \
    --reference-fasta "$older_residue_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    >"$older_residue_output" 2>&1
older_residue_status=$?
set -e

[[ "$older_residue_status" -ne 0 ]] || fail "older Step 00c residue unexpectedly allowed a plan"
assert_contains "$older_residue_output" "Step 00c residue requires operator inspection"
assert_contains "$older_residue_path" "preserve older Step 00c residue"
assert_not_exists "$older_residue_fasta.fai"
assert_not_exists "$older_residue_dir/genome.dict"
assert_not_exists "$older_residue_dir/.step_00c_prepare_gatk_reference.lock"

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

printf 'Running reference FASTA mutation rejection check...\n'
mutation_dir="$tmp_dir/reference_mutation"
mutation_fasta="$mutation_dir/genome.fa"
mutation_lock="$mutation_dir/.step_00c_prepare_gatk_reference.lock"
mutation_run_token="reference-mutation"
write_fasta "$mutation_fasta"
mutation_output="$tmp_dir/reference_mutation.out"
set +e
FAKE_MUTATE_REFERENCE_FASTA=1 \
SLURM_JOB_ID="$mutation_run_token" \
bash "$SCRIPT" \
    --reference-fasta "$mutation_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    --execute >"$mutation_output" 2>&1
mutation_status=$?
set -e

[[ "$mutation_status" -ne 0 ]] || fail "reference mutation unexpectedly succeeded"
assert_contains "$mutation_output" "Reference FASTA changed during Step 00c"
assert_not_exists "$mutation_fasta.fai"
assert_not_exists "$mutation_dir/genome.dict"
assert_not_exists "$mutation_lock"
assert_not_exists "$mutation_fasta.fai.tmp.$mutation_run_token"
assert_not_exists "$mutation_dir/genome.dict.tmp.$mutation_run_token"
assert_not_exists "$mutation_fasta.tmp.$mutation_run_token.faidx_input"
assert_not_exists "$mutation_fasta.tmp.$mutation_run_token.faidx_input.fai"

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
real_ln_bin="$(command -v ln)"
real_cp_bin="$(command -v cp)"
real_rm_bin="$(command -v rm)"
cat >"$fake_bin/ln" <<'EOF_LN'
#!/usr/bin/env bash
set -euo pipefail

destination="${!#}"
if [[ -n "${INJECT_LATE_FINAL_DESTINATION:-}" &&
      "$destination" == "$INJECT_LATE_FINAL_DESTINATION" ]]; then
    if [[ -n "${INJECT_REPLACE_DESTINATION:-}" ]]; then
        "$REAL_RM_BIN" -f "$INJECT_REPLACE_DESTINATION"
        "$REAL_CP_BIN" "$INJECT_REPLACE_SOURCE" "$INJECT_REPLACE_DESTINATION"
    fi
    "$REAL_CP_BIN" "$INJECT_LATE_FINAL_SOURCE" "$destination"
    printf 'injected late foreign sidecar: %s\n' "$destination" >&2
fi
if [[ -n "${FAIL_LN_DESTINATION:-}" && "$destination" == "$FAIL_LN_DESTINATION" ]]; then
    printf 'controlled final DICT publication failure: %s\n' "$destination" >&2
    exit 73
fi
exec "$REAL_LN_BIN" "$@"
EOF_LN
chmod +x "$fake_bin/ln"

partial_dir="$tmp_dir/partial_publication"
partial_fasta="$partial_dir/genome.fa"
partial_dict="$partial_dir/genome.dict"
partial_run_token="partial-publication"
write_fasta "$partial_fasta"
partial_output="$tmp_dir/partial_publication.out"
set +e
REAL_LN_BIN="$real_ln_bin" \
FAIL_LN_DESTINATION="$partial_dict" \
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
assert_not_exists "$partial_fasta.fai"
assert_not_exists "$partial_dict"
assert_not_exists "$partial_dir/.step_00c_prepare_gatk_reference.lock"
assert_not_exists "$partial_fasta.fai.tmp.$partial_run_token"
assert_not_exists "$partial_dict.tmp.$partial_run_token"
assert_not_exists "$partial_fasta.tmp.$partial_run_token.faidx_input"
assert_not_exists "$partial_fasta.tmp.$partial_run_token.faidx_input.fai"
assert_contains "$partial_output" "controlled final DICT publication failure"

printf 'Running late foreign FAI collision check...\n'
late_fai_dir="$tmp_dir/late_foreign_fai"
late_fai_fasta="$late_fai_dir/genome.fa"
late_fai_final="$late_fai_fasta.fai"
late_fai_dict="$late_fai_dir/genome.dict"
late_fai_source="$tmp_dir/foreign.fai"
late_fai_run_token="late-foreign-fai"
printf 'foreign-fai-bytes\n' >"$late_fai_source"
write_fasta "$late_fai_fasta"
late_fai_output="$tmp_dir/late_foreign_fai.out"
set +e
REAL_LN_BIN="$real_ln_bin" \
REAL_CP_BIN="$real_cp_bin" \
REAL_RM_BIN="$real_rm_bin" \
INJECT_LATE_FINAL_DESTINATION="$late_fai_final" \
INJECT_LATE_FINAL_SOURCE="$late_fai_source" \
SLURM_JOB_ID="$late_fai_run_token" \
bash "$SCRIPT" \
    --reference-fasta "$late_fai_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    --execute >"$late_fai_output" 2>&1
late_fai_status=$?
set -e

[[ "$late_fai_status" -ne 0 ]] || fail "late foreign FAI collision unexpectedly succeeded"
cmp -s "$late_fai_source" "$late_fai_final" || fail "late foreign FAI was overwritten or removed"
assert_not_exists "$late_fai_dict"
assert_not_exists "$late_fai_dir/.step_00c_prepare_gatk_reference.lock"
assert_not_exists "$late_fai_final.tmp.$late_fai_run_token"
assert_contains "$late_fai_output" "injected late foreign sidecar"
assert_contains "$late_fai_output" "Refusing to replace a late or foreign FASTA index"

printf 'Running cleanup-time foreign sidecar preservation check...\n'
late_pair_dir="$tmp_dir/late_foreign_pair"
late_pair_fasta="$late_pair_dir/genome.fa"
late_pair_fai="$late_pair_fasta.fai"
late_pair_dict="$late_pair_dir/genome.dict"
late_pair_foreign_fai="$tmp_dir/replacement-foreign.fai"
late_pair_foreign_dict="$tmp_dir/foreign.dict"
late_pair_run_token="late-foreign-pair"
late_pair_lock="$late_pair_dir/.step_00c_prepare_gatk_reference.lock"
printf 'replacement-foreign-fai-bytes\n' >"$late_pair_foreign_fai"
printf 'replacement-foreign-dict-bytes\n' >"$late_pair_foreign_dict"
write_fasta "$late_pair_fasta"
late_pair_output="$tmp_dir/late_foreign_pair.out"
set +e
REAL_LN_BIN="$real_ln_bin" \
REAL_CP_BIN="$real_cp_bin" \
REAL_RM_BIN="$real_rm_bin" \
INJECT_LATE_FINAL_DESTINATION="$late_pair_dict" \
INJECT_LATE_FINAL_SOURCE="$late_pair_foreign_dict" \
INJECT_REPLACE_DESTINATION="$late_pair_fai" \
INJECT_REPLACE_SOURCE="$late_pair_foreign_fai" \
SLURM_JOB_ID="$late_pair_run_token" \
bash "$SCRIPT" \
    --reference-fasta "$late_pair_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    --execute >"$late_pair_output" 2>&1
late_pair_status=$?
set -e

[[ "$late_pair_status" -ne 0 ]] || fail "late foreign pair collision unexpectedly succeeded"
cmp -s "$late_pair_foreign_fai" "$late_pair_fai" || fail "cleanup removed or changed the foreign FAI"
cmp -s "$late_pair_foreign_dict" "$late_pair_dict" || fail "cleanup removed or changed the foreign DICT"
[[ -d "$late_pair_lock" ]] || fail "foreign replacement did not retain the owner lock"
assert_contains "$late_pair_lock/owner" "run_token=$late_pair_run_token"
[[ -s "$late_pair_fai.tmp.$late_pair_run_token" ]] || fail "foreign replacement did not preserve the FAI ownership anchor"
[[ -s "$late_pair_dict.tmp.$late_pair_run_token" ]] || fail "foreign replacement did not preserve the staged DICT"
assert_contains "$late_pair_output" "no longer belongs to this invocation"
assert_contains "$late_pair_output" "preserving lock and residue for inspection"

printf 'Running failed rollback preservation check...\n'
cat >"$fake_bin/rm" <<'EOF_RM'
#!/usr/bin/env bash
set -euo pipefail

for argument in "$@"; do
    if [[ -n "${FAIL_RM_TARGET:-}" && "$argument" == "$FAIL_RM_TARGET" ]]; then
        printf 'controlled rollback removal failure: %s\n' "$argument" >&2
        exit 79
    fi
done
exec "$REAL_RM_BIN" "$@"
EOF_RM
chmod +x "$fake_bin/rm"

rollback_dir="$tmp_dir/rollback_failure"
rollback_fasta="$rollback_dir/genome.fa"
rollback_dict="$rollback_dir/genome.dict"
rollback_run_token="rollback-failure"
rollback_lock="$rollback_dir/.step_00c_prepare_gatk_reference.lock"
write_fasta "$rollback_fasta"
rollback_output="$tmp_dir/rollback_failure.out"
set +e
REAL_LN_BIN="$real_ln_bin" \
FAIL_LN_DESTINATION="$rollback_dict" \
REAL_RM_BIN="$real_rm_bin" \
FAIL_RM_TARGET="$rollback_fasta.fai" \
SLURM_JOB_ID="$rollback_run_token" \
bash "$SCRIPT" \
    --reference-fasta "$rollback_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    --execute >"$rollback_output" 2>&1
rollback_status=$?
set -e

[[ "$rollback_status" -eq 73 ]] || fail "failed rollback exit was $rollback_status, expected 73"
[[ -s "$rollback_fasta.fai" ]] || fail "failed rollback did not preserve published FAI"
[[ -d "$rollback_lock" ]] || fail "failed rollback did not preserve owner lock"
assert_contains "$rollback_lock/owner" "run_token=$rollback_run_token"
[[ -s "$rollback_dict.tmp.$rollback_run_token" ]] || fail "failed rollback did not preserve staged DICT"
assert_contains "$rollback_output" "controlled rollback removal failure"
assert_contains "$rollback_output" "preserving lock and residue for inspection"

printf 'Running failed staging-cleanup preservation check...\n'
staging_cleanup_dir="$tmp_dir/staging_cleanup_failure"
staging_cleanup_fasta="$staging_cleanup_dir/genome.fa"
staging_cleanup_dict="$staging_cleanup_dir/genome.dict"
staging_cleanup_run_token="staging-cleanup-failure"
staging_cleanup_lock="$staging_cleanup_dir/.step_00c_prepare_gatk_reference.lock"
staging_cleanup_tmp_fai="$staging_cleanup_fasta.fai.tmp.$staging_cleanup_run_token"
staging_cleanup_tmp_dict="$staging_cleanup_dict.tmp.$staging_cleanup_run_token"
staging_cleanup_tmp_fasta="$staging_cleanup_fasta.tmp.$staging_cleanup_run_token.faidx_input"
write_fasta "$staging_cleanup_fasta"
staging_cleanup_output="$tmp_dir/staging_cleanup_failure.out"
set +e
FAKE_MUTATE_REFERENCE_FASTA=1 \
REAL_LN_BIN="$real_ln_bin" \
REAL_RM_BIN="$real_rm_bin" \
FAIL_RM_TARGET="$staging_cleanup_tmp_fai" \
SLURM_JOB_ID="$staging_cleanup_run_token" \
bash "$SCRIPT" \
    --reference-fasta "$staging_cleanup_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    --execute >"$staging_cleanup_output" 2>&1
staging_cleanup_status=$?
set -e

[[ "$staging_cleanup_status" -ne 0 ]] || fail "failed staging cleanup unexpectedly succeeded"
assert_not_exists "$staging_cleanup_fasta.fai"
assert_not_exists "$staging_cleanup_dict"
[[ -s "$staging_cleanup_tmp_fai" ]] || fail "failed staging cleanup did not retain its FAI residue"
[[ -s "$staging_cleanup_tmp_dict" ]] || fail "failed staging cleanup did not retain its DICT residue"
[[ -L "$staging_cleanup_tmp_fasta" ]] || fail "failed staging cleanup did not retain its FASTA symlink residue"
[[ -d "$staging_cleanup_lock" ]] || fail "failed staging cleanup did not retain the owner lock"
assert_contains "$staging_cleanup_lock/owner" "run_token=$staging_cleanup_run_token"
assert_contains "$staging_cleanup_output" "controlled rollback removal failure"
assert_contains "$staging_cleanup_output" "rollback or cleanup was incomplete"

printf 'Running failed lock-cleanup preservation check...\n'
lock_cleanup_dir="$tmp_dir/lock_cleanup_failure"
lock_cleanup_fasta="$lock_cleanup_dir/genome.fa"
lock_cleanup_dict="$lock_cleanup_dir/genome.dict"
lock_cleanup_run_token="lock-cleanup-failure"
lock_cleanup_lock="$lock_cleanup_dir/.step_00c_prepare_gatk_reference.lock"
write_fasta "$lock_cleanup_fasta"
lock_cleanup_output="$tmp_dir/lock_cleanup_failure.out"
set +e
REAL_LN_BIN="$real_ln_bin" \
REAL_RM_BIN="$real_rm_bin" \
FAIL_RM_TARGET="$lock_cleanup_lock/owner" \
SLURM_JOB_ID="$lock_cleanup_run_token" \
bash "$SCRIPT" \
    --reference-fasta "$lock_cleanup_fasta" \
    --samtools-bin "$fake_bin/samtools" \
    --gatk-bin "$fake_bin/gatk" \
    --java-bin "$fake_bin/java" \
    --execute >"$lock_cleanup_output" 2>&1
lock_cleanup_status=$?
set -e

[[ "$lock_cleanup_status" -ne 0 ]] || fail "failed lock cleanup incorrectly reported success"
[[ -s "$lock_cleanup_fasta.fai" ]] || fail "failed lock cleanup lost the published FAI"
[[ -s "$lock_cleanup_dict" ]] || fail "failed lock cleanup lost the published DICT"
[[ -d "$lock_cleanup_lock" ]] || fail "failed lock cleanup did not retain the owner lock"
assert_contains "$lock_cleanup_lock/owner" "run_token=$lock_cleanup_run_token"
assert_not_exists "$lock_cleanup_fasta.fai.tmp.$lock_cleanup_run_token"
assert_not_exists "$lock_cleanup_dict.tmp.$lock_cleanup_run_token"
assert_not_exists "$lock_cleanup_fasta.tmp.$lock_cleanup_run_token.faidx_input"
assert_not_exists "$lock_cleanup_fasta.tmp.$lock_cleanup_run_token.faidx_input.fai"
assert_contains "$lock_cleanup_output" "Could not remove the owned Step 00c lock metadata"
assert_contains "$lock_cleanup_output" "rollback or cleanup was incomplete"

printf 'Running stale Step 05 path check...\n'
stale_output="$tmp_dir/stale.out"
if grep -F "sorted.md" "$SCRIPT" "$JOB" >"$stale_output"; then
    cat "$stale_output" >&2
    fail "Step 00c files should not use stale Step 05 sorted.md paths"
fi
assert_not_contains "$dry_output" "sorted.md"
assert_not_contains "$execute_output" "sorted.md"

printf 'All step_00c GATK reference-prep smoke tests passed.\n'
