#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh"
unset EMRYS_RUN_TOKEN
export EMRYS_SHA256_PYTHON="${EMRYS_SHA256_PYTHON:-$REPO_ROOT/.venv/bin/python}"
real_sha256_python="$EMRYS_SHA256_PYTHON"

# Keep assertions small and shell-native so failures print the local fixture state.
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

assert_file_equals() {
    local path="$1"
    local expected="$2"
    local actual

    [[ -f "$path" ]] || fail "expected file does not exist: $path"
    actual="$(cat "$path")"
    [[ "$actual" == "$expected" ]] || fail "unexpected content in $path: $actual"
}

assert_fails() {
    local output_file="$1"
    shift

    if "$@" >"$output_file" 2>&1; then
        cat "$output_file" >&2
        fail "command unexpectedly succeeded: $*"
    fi
}

assert_no_step02_scratch() {
    local output_dir="$1"

    if find "$output_dir" -mindepth 1 -maxdepth 1 -name '.*step02*' | grep -q .; then
        find "$output_dir" -mindepth 1 -maxdepth 1 -name '.*step02*' >&2
        fail "step02 scratch files were not cleaned from $output_dir"
    fi
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

fake_bin="$tmp_dir/bin"
mkdir -p "$fake_bin"

samtools_log="$tmp_dir/samtools_invocations.log"

# Fake samtools stores just enough header/count metadata in text files for the
# Step 02 wrapper to exercise command construction, validation, and rollback.
cat >"$fake_bin/samtools" <<EOF_SAMTOOLS
#!/usr/bin/env bash
set -euo pipefail

printf 'samtools invoked\\n' >> "$samtools_log"
printf '%s\\n' "\$@" >> "$samtools_log"

write_fake_bam() {
    local path="\$1"
    local rg_mode="\${FAKE_RG_MODE:-valid}"
    local tagged_mode="\${FAKE_TAGGED_MODE:-all}"
    local sort_mode="\${FAKE_SORT_MODE:-coordinate}"
    local sample="\${FAKE_SAMPLE_ID:-sample_execute}"
    local total="\${FAKE_TOTAL_RECORDS:-10}"
    local tagged="\$total"

    if [[ "\$tagged_mode" == "partial" ]]; then
        tagged=5
    fi

    {
        # The wrapper validates @HD SO:coordinate and exactly one strict @RG.
        case "\$sort_mode" in
            coordinate) printf '@HD\\tVN:1.6\\tSO:coordinate\\n' ;;
            unknown) printf '@HD\\tVN:1.6\\tSO:unknown\\n' ;;
        esac

        case "\$rg_mode" in
            valid)
                printf '@RG\\tID:%s\\tSM:%s\\tLB:%s\\tPL:ILLUMINA\\n' "\$sample" "\$sample" "\$sample"
                ;;
            missing)
                ;;
            extra)
                printf '@RG\\tID:%s\\tSM:%s\\tLB:%s\\tPL:ILLUMINA\\n' "\$sample" "\$sample" "\$sample"
                printf '@RG\\tID:extra\\tSM:extra\\tLB:extra\\tPL:ILLUMINA\\n'
                ;;
            malformed)
                printf '@RG\\tID:%s\\tSM:WRONG\\tLB:%s\\tPL:ILLUMINA\\n' "\$sample" "\$sample"
                ;;
        esac

        # TOTAL/TAGGED lines let fake "samtools view -c" behave predictably.
        printf 'TOTAL:%s\\n' "\$total"
        printf 'TAGGED:%s\\n' "\$tagged"
    } > "\$path"
}

subcommand="\${1:-}"
shift || true

case "\$subcommand" in
    sort)
        output_bam=""
        input_alignment=""
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
                    input_alignment="\$1"
                    shift
                    ;;
            esac
        done

        [[ -n "\$output_bam" ]] || { printf 'fake samtools sort missing -o output\\n' >&2; exit 64; }
        printf 'fake sorted bam\\n' > "\$output_bam"
        if [[ -n "\${FAKE_MUTATE_INPUT:-}" ]]; then
            printf 'mutated input alignment\\n' >"\$input_alignment"
        fi
        ;;
    addreplacerg)
        output_bam=""
        input_bam=""
        saw_w=false
        saw_id=false
        saw_sm=false
        saw_lb=false
        saw_pl=false

        while [[ \$# -gt 0 ]]; do
            case "\$1" in
                -o)
                    output_bam="\${2:-}"
                    shift 2
                    ;;
                -@|-m)
                    shift 2
                    ;;
                -w)
                    saw_w=true
                    shift
                    ;;
                -r)
                    case "\${2:-}" in
                        ID:*) saw_id=true ;;
                        SM:*) saw_sm=true ;;
                        LB:*) saw_lb=true ;;
                        PL:ILLUMINA) saw_pl=true ;;
                    esac
                    shift 2
                    ;;
                *)
                    input_bam="\$1"
                    shift
                    ;;
            esac
        done

        # Enforce the production contract: repeated -r arguments plus -w.
        [[ "\$saw_w" == true ]] || { printf 'fake samtools addreplacerg missing -w\\n' >&2; exit 64; }
        [[ "\$saw_id" == true && "\$saw_sm" == true && "\$saw_lb" == true && "\$saw_pl" == true ]] || {
            printf 'fake samtools addreplacerg missing repeated -r RG fields\\n' >&2
            exit 64
        }
        [[ -n "\$output_bam" && -n "\$input_bam" ]] || { printf 'fake samtools addreplacerg missing input/output\\n' >&2; exit 64; }
        write_fake_bam "\$output_bam"
        ;;
    quickcheck)
        input_bam="\${1:-}"
        [[ -n "\$input_bam" ]] || { printf 'fake samtools quickcheck missing input BAM\\n' >&2; exit 64; }
        [[ -s "\$input_bam" ]] || exit 1
        if [[ -n "\${FAKE_QUICKCHECK_FAIL_MATCH:-}" && "\$input_bam" == *"\$FAKE_QUICKCHECK_FAIL_MATCH"* ]]; then
            exit 1
        fi
        ;;
    view)
        if [[ "\${1:-}" == "-H" ]]; then
            input_bam="\${2:-}"
            grep '^@' "\$input_bam"
        elif [[ "\${1:-}" == "-c" && "\${2:-}" == "-d" ]]; then
            input_bam="\${4:-}"
            grep '^TAGGED:' "\$input_bam" | cut -d: -f2
        elif [[ "\${1:-}" == "-c" ]]; then
            input_bam="\${2:-}"
            grep '^TOTAL:' "\$input_bam" | cut -d: -f2
        else
            printf 'fake samtools unsupported view args\\n' >&2
            exit 64
        fi
        ;;
    index)
        input_bam="\${1:-}"
        [[ -n "\$input_bam" ]] || { printf 'fake samtools index missing input BAM\\n' >&2; exit 64; }
        printf 'fake bam index\\n' > "\$input_bam.bai"
        ;;
    *)
        printf 'fake samtools unknown subcommand: %s\\n' "\$subcommand" >&2
        exit 64
        ;;
esac
EOF_SAMTOOLS
chmod +x "$fake_bin/samtools"

# Faults surround real filesystem operations; the producer's publication and
# ownership helpers remain unchanged.
cat >"$fake_bin/ln" <<'EOF_LN'
#!/usr/bin/env bash
set -euo pipefail

final_path="${!#}"
if [[ "$final_path" == "${FAKE_LN_FAULT_PATH:-}" &&
      "${FAKE_LN_FAULT:-}" == fail ]]; then
    printf 'fake ln forced failure: %s\n' "$final_path" >&2
    exit 65
fi
/bin/ln "$@"
if [[ "$final_path" == "${FAKE_LN_FAULT_PATH:-}" ]]; then
    case "${FAKE_LN_FAULT:-}" in
        missing) /bin/rm -f -- "$final_path" ;;
        foreign)
            printf 'foreign final\n' >"$final_path.foreign"
            /bin/mv "$final_path.foreign" "$final_path"
            ;;
        same_bytes)
            /bin/cp "$final_path" "$final_path.foreign"
            /bin/mv "$final_path.foreign" "$final_path"
            ;;
        *) exit 64 ;;
    esac
    printf 'fake ln changed final ownership: %s\n' "$final_path" >&2
fi
EOF_LN
chmod +x "$fake_bin/ln"

cat >"$fake_bin/rm" <<'EOF_RM'
#!/usr/bin/env bash
set -euo pipefail

for argument in "$@"; do
    if [[ "$argument" == "${FAKE_RM_FAIL_PATH:-}" ]]; then
        if [[ -n "${FAKE_RM_REMOVE_FIRST_PATH:-}" ]]; then
            /bin/rm -f -- "$FAKE_RM_REMOVE_FIRST_PATH"
        fi
        printf 'fake rm forced failure: %s\n' "$argument" >&2
        exit 67
    fi
done
exec /bin/rm "$@"
EOF_RM
chmod +x "$fake_bin/rm"

cat >"$fake_bin/sha256-python" <<'EOF_SHA256_PYTHON'
#!/usr/bin/env bash
set -euo pipefail

real_python="${FAKE_SHA256_REAL_PYTHON:-}"
if [[ -z "$real_python" || ! -x "$real_python" ]]; then
    printf 'fake SHA-256 launcher requires an executable real Python\n' >&2
    exit 64
fi

hash_target=""
for argument in "$@"; do
    hash_target="$argument"
done

if [[ -n "${FAKE_SHA256_MUTATE_WHEN_PATH:-}" &&
      "$hash_target" == "$FAKE_SHA256_MUTATE_WHEN_PATH" ]]; then
    mutation_path="${FAKE_SHA256_MUTATE_PATH:-}"
    [[ -n "$mutation_path" ]] || {
        printf 'fake SHA-256 launcher requires a mutation path\n' >&2
        exit 64
    }
    printf 'mutated after final BAM publication\n' >"$mutation_path"
fi

exec "$real_python" "$@"
EOF_SHA256_PYTHON
chmod +x "$fake_bin/sha256-python"

export PATH="$fake_bin:$PATH"

fixture_dir="$tmp_dir/fixtures"
mkdir -p "$fixture_dir"

input_sam="$fixture_dir/sample.sam"
input_bam="$fixture_dir/sample.bam"

printf '@HD\tVN:1.6\tSO:unknown\n' >"$input_sam"
printf 'placeholder bam\n' >"$input_bam"

run_step02() {
    local sample="$1"
    local input="$2"
    local output_dir="$3"
    local threads="$4"
    shift 4

    # A wrapper helper keeps the sample ID aligned between the script and fake samtools.
    env FAKE_SAMPLE_ID="$sample" SLURM_JOB_ID="${SLURM_JOB_ID:-testjob}" bash "$SCRIPT" \
        --sample-id "$sample" \
        --input-alignment "$input" \
        --output-dir "$output_dir" \
        --threads "$threads" \
        "$@"
}

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

printf 'Running default sample path-safety admission check...\n'
unsafe_output="$tmp_dir/unsafe_sample.out"
unsafe_output_dir="$tmp_dir/results/unsafe_sample"
assert_fails "$unsafe_output" bash "$SCRIPT" \
    --sample-id '../unsafe_sample' --input-alignment "$input_sam" \
    --output-dir "$unsafe_output_dir" --threads 1
assert_contains "$unsafe_output" "--sample-id must match"
assert_not_exists "$unsafe_output_dir"

printf 'Running dry-run no-output check...\n'
dry_output="$tmp_dir/dry.out"
dry_output_dir="$tmp_dir/results/dry"
env FAKE_SAMPLE_ID=sample_dry EMRYS_RUN_TOKEN=explicit-owner-02 \
    SLURM_JOB_ID=scheduler-02 bash "$SCRIPT" \
    --sample-id sample_dry \
    --input-alignment "$input_sam" \
    --output-dir "$dry_output_dir" \
    --threads 4 \
    >"$dry_output"

dry_bam="$dry_output_dir/sample_dry.sorted.bam"
assert_not_exists "$dry_output_dir"
[[ ! -e "$samtools_log" ]] || fail "dry-run invoked samtools"
assert_contains "$dry_output" "Mode: dry-run"
assert_contains "$dry_output" "Run token: explicit-owner-02"
assert_contains "$dry_output" "Lock directory: $dry_output_dir/.sample_dry.step02.lock"
assert_contains "$dry_output" ".sample_dry.step02.explicit-owner-02.sorted.tmp.bam"
assert_contains "$dry_output" ".sample_dry.step02.explicit-owner-02.rg.tmp.bam"
assert_contains "$dry_output" "addreplacerg"
assert_contains "$dry_output" "-w"
assert_contains "$dry_output" "ID:sample_dry"
assert_contains "$dry_output" "SM:sample_dry"
assert_contains "$dry_output" "LB:sample_dry"
assert_contains "$dry_output" "PL:ILLUMINA"
assert_contains "$dry_output" "$dry_bam"
assert_contains "$dry_output" "Rollback plan:"
assert_contains "$dry_output" "Dry-run only"

printf 'Running successful execute check...\n'
execute_output="$tmp_dir/execute.out"
execute_output_dir="$tmp_dir/results/execute"
SLURM_JOB_ID=exec001 run_step02 sample_execute "$input_sam" "$execute_output_dir" 2 --execute >"$execute_output"

execute_bam="$execute_output_dir/sample_execute.sorted.bam"
execute_bai="$execute_bam.bai"
[[ -s "$execute_bam" ]] || fail "execute did not create non-empty canonical BAM"
[[ -s "$execute_bai" ]] || fail "execute did not create non-empty canonical BAI"
assert_contains "$execute_bam" $'@RG\tID:sample_execute\tSM:sample_execute\tLB:sample_execute\tPL:ILLUMINA'
assert_contains "$execute_bam" "TAGGED:10"
assert_contains "$samtools_log" "addreplacerg"
assert_contains "$samtools_log" "-w"
assert_contains "$samtools_log" "ID:sample_execute"
assert_contains "$samtools_log" "SM:sample_execute"
assert_contains "$samtools_log" "LB:sample_execute"
assert_contains "$samtools_log" "PL:ILLUMINA"
assert_contains "$execute_output" "Canonical Step 02 output details:"
assert_not_exists "$execute_output_dir/.sample_execute.step02.lock"
assert_no_step02_scratch "$execute_output_dir"

printf 'Running coordinate-sorted input bypass check...\n'
coordinate_input="$tmp_dir/fixtures/coordinate_input.sam"
printf '@HD\tVN:1.6\tSO:coordinate\n' >"$coordinate_input"
coordinate_output="$tmp_dir/coordinate.out"
coordinate_output_dir="$tmp_dir/results/coordinate"
sort_count_before="$(grep -c '^sort$' "$samtools_log" || true)"
SLURM_JOB_ID=coordinate001 run_step02 \
    sample_coordinate "$coordinate_input" "$coordinate_output_dir" 2 --execute \
    >"$coordinate_output"
sort_count_after="$(grep -c '^sort$' "$samtools_log" || true)"
[[ "$sort_count_after" == "$sort_count_before" ]] ||
    fail "coordinate-sorted input unexpectedly invoked samtools sort"
assert_contains "$coordinate_output" \
    "Input alignment is already coordinate sorted; skipping redundant samtools sort."
[[ -s "$coordinate_output_dir/sample_coordinate.sorted.bam" ]] ||
    fail "coordinate-sorted bypass did not publish canonical BAM"
assert_no_step02_scratch "$coordinate_output_dir"

printf 'Running canonical input zero-copy reuse check...\n'
canonical_input="$tmp_dir/fixtures/canonical_input.bam"
{
    printf '@HD\tVN:1.6\tSO:coordinate\n'
    printf '@RG\tID:sample_canonical\tSM:sample_canonical\tLB:sample_canonical\tPL:ILLUMINA\n'
    printf 'TOTAL:10\n'
    printf 'TAGGED:10\n'
} >"$canonical_input"
canonical_output="$tmp_dir/canonical.out"
canonical_output_dir="$tmp_dir/results/canonical"
sort_count_before="$(grep -c '^sort$' "$samtools_log" || true)"
addreplacerg_count_before="$(grep -c '^addreplacerg$' "$samtools_log" || true)"
SLURM_JOB_ID=canonical001 run_step02 \
    sample_canonical "$canonical_input" "$canonical_output_dir" 2 --no-clobber --execute \
    >"$canonical_output"
sort_count_after="$(grep -c '^sort$' "$samtools_log" || true)"
addreplacerg_count_after="$(grep -c '^addreplacerg$' "$samtools_log" || true)"
[[ "$sort_count_after" == "$sort_count_before" ]] ||
    fail "canonical input unexpectedly invoked samtools sort"
[[ "$addreplacerg_count_after" == "$addreplacerg_count_before" ]] ||
    fail "canonical input unexpectedly invoked samtools addreplacerg"
canonical_bam="$canonical_output_dir/sample_canonical.sorted.bam"
[[ "$canonical_bam" -ef "$canonical_input" ]] ||
    fail "canonical output does not reuse the admitted input inode"
assert_contains "$canonical_output" \
    "Input alignment already satisfies the canonical BAM contract; reusing its bytes without rewriting."
assert_no_step02_scratch "$canonical_output_dir"

printf 'Running zero-copy post-publication mutation rejection check...\n'
publication_mutation_input="$tmp_dir/fixtures/publication_mutation_input.bam"
{
    printf '@HD\tVN:1.6\tSO:coordinate\n'
    printf '@RG\tID:sample_publish_race\tSM:sample_publish_race\tLB:sample_publish_race\tPL:ILLUMINA\n'
    printf 'TOTAL:10\n'
    printf 'TAGGED:10\n'
} >"$publication_mutation_input"
publication_mutation_output="$tmp_dir/publication_mutation.out"
publication_mutation_output_dir="$tmp_dir/results/publication_mutation"
publication_mutation_bam="$publication_mutation_output_dir/sample_publish_race.sorted.bam"
assert_fails "$publication_mutation_output" env \
    EMRYS_SHA256_PYTHON="$fake_bin/sha256-python" \
    FAKE_SHA256_REAL_PYTHON="$real_sha256_python" \
    FAKE_SHA256_MUTATE_WHEN_PATH="$publication_mutation_bam" \
    FAKE_SHA256_MUTATE_PATH="$publication_mutation_input" \
    FAKE_SAMPLE_ID=sample_publish_race \
    SLURM_JOB_ID=publish-race001 \
    bash "$SCRIPT" \
    --sample-id sample_publish_race \
    --input-alignment "$publication_mutation_input" \
    --output-dir "$publication_mutation_output_dir" \
    --threads 2 \
    --no-clobber \
    --execute
assert_contains "$publication_mutation_output" \
    "Canonical BAM changed after create-exclusive publication: $publication_mutation_bam"
assert_contains "$publication_mutation_output" "Rolling back Step 02 canonical outputs..."
assert_not_contains "$publication_mutation_output" \
    "Step 02 no-clobber rollback was incomplete"
assert_file_equals "$publication_mutation_input" "mutated after final BAM publication"
assert_not_exists "$publication_mutation_bam"
assert_not_exists "$publication_mutation_bam.bai"
assert_not_exists "$publication_mutation_output_dir/.sample_publish_race.step02.lock"
assert_no_step02_scratch "$publication_mutation_output_dir"

printf 'Running orchestration-safe no-clobber checks...\n'
safe_input="$tmp_dir/fixtures/safe_input.sam"
printf '@HD\tVN:1.6\tSO:unsorted\n' >"$safe_input"
residue_output_dir="$tmp_dir/results/residue"
mkdir -p "$residue_output_dir"
residue_path="$residue_output_dir/.sample_residue.step02.older-token.sorted.tmp.bam"
printf 'preserve residue\n' >"$residue_path"
residue_output="$tmp_dir/residue.out"
assert_fails "$residue_output" env FAKE_SAMPLE_ID=sample_residue SLURM_JOB_ID=newer-token bash "$SCRIPT" \
    --sample-id sample_residue \
    --input-alignment "$safe_input" \
    --output-dir "$residue_output_dir" \
    --threads 2 \
    --no-clobber \
    --execute
assert_contains "$residue_output" "residue requires operator inspection"
assert_file_equals "$residue_path" "preserve residue"
assert_not_exists "$residue_output_dir/.sample_residue.step02.lock"
safe_output="$tmp_dir/safe.out"
safe_output_dir="$tmp_dir/results/safe"
rm -f "$samtools_log"
SLURM_JOB_ID=safe001 run_step02 sample_safe "$safe_input" "$safe_output_dir" 2 --no-clobber --execute >"$safe_output"
assert_contains "$safe_output" "No-clobber transaction: true"
assert_contains "$samtools_log" \
    "$safe_output_dir/.sample_safe.step02.safe001.rg.tmp.bam"
assert_not_contains "$samtools_log" "$safe_output_dir/sample_safe.sorted.bam"
assert_not_exists "$safe_output_dir/.sample_safe.step02.lock"
safe_repeat_output="$tmp_dir/safe_repeat.out"
assert_fails "$safe_repeat_output" env FAKE_SAMPLE_ID=sample_safe SLURM_JOB_ID=safe002 bash "$SCRIPT" \
    --sample-id sample_safe \
    --input-alignment "$safe_input" \
    --output-dir "$safe_output_dir" \
    --threads 2 \
    --no-clobber \
    --execute
assert_contains "$safe_repeat_output" "Step 02 requires both canonical outputs to be absent"
assert_file_equals "$safe_output_dir/sample_safe.sorted.bam.bai" "fake bam index"

mutation_input="$tmp_dir/fixtures/mutation_input.sam"
printf '@HD\tVN:1.6\tSO:unsorted\n' >"$mutation_input"
mutation_output="$tmp_dir/mutation.out"
mutation_output_dir="$tmp_dir/results/mutation"
assert_fails "$mutation_output" env FAKE_MUTATE_INPUT=1 FAKE_SAMPLE_ID=sample_mutation SLURM_JOB_ID=mutation001 bash "$SCRIPT" \
    --sample-id sample_mutation \
    --input-alignment "$mutation_input" \
    --output-dir "$mutation_output_dir" \
    --threads 2 \
    --execute
assert_contains "$mutation_output" "Input alignment changed during Step 02"
assert_not_exists "$mutation_output_dir/sample_mutation.sorted.bam"
assert_not_exists "$mutation_output_dir/sample_mutation.sorted.bam.bai"
assert_not_exists "$mutation_output_dir/.sample_mutation.step02.lock"

printf 'Running no-clobber publication handoff failure checks...\n'
for failed_output in bam bai; do
    for link_fault in fail missing foreign same_bytes; do
        fault_sample="sample_${failed_output}_${link_fault}"
        fault_dir="$tmp_dir/results/$fault_sample"
        fault_output="$tmp_dir/$fault_sample.out"
        fault_bam="$fault_dir/$fault_sample.sorted.bam"
        fault_bai="$fault_bam.bai"
        fault_staged_bam="$fault_dir/.$fault_sample.step02.handoff001.rg.tmp.bam"
        fault_staged_bai="$fault_staged_bam.bai"
        fault_final="$fault_bam"
        fault_staged="$fault_staged_bam"
        if [[ "$failed_output" == bai ]]; then
            fault_final="$fault_bai"
            fault_staged="$fault_staged_bai"
        fi
        assert_fails "$fault_output" env \
            FAKE_LN_FAULT_PATH="$fault_final" FAKE_LN_FAULT="$link_fault" \
            FAKE_SAMPLE_ID="$fault_sample" SLURM_JOB_ID=handoff001 bash "$SCRIPT" \
            --sample-id "$fault_sample" --input-alignment "$safe_input" \
            --output-dir "$fault_dir" --threads 2 --execute
        if [[ "$link_fault" == fail ]]; then
            assert_contains "$fault_output" "fake ln forced failure: $fault_final"
            assert_contains "$fault_output" "final path appeared during publication"
        else
            assert_contains "$fault_output" "fake ln changed final ownership: $fault_final"
            assert_contains "$fault_output" "create-exclusive publication did not preserve the staged inode"
        fi
        assert_contains "$fault_output" "Step 02 no-clobber rollback was incomplete"
        assert_contains "$fault_staged_bam" "@RG"
        assert_file_equals "$fault_staged_bai" "fake bam index"
        assert_file_equals "$fault_dir/.$fault_sample.step02.lock/owner" "run_token=handoff001"
        case "$link_fault" in
            fail|missing) assert_not_exists "$fault_final" ;;
            foreign) assert_file_equals "$fault_final" "foreign final" ;;
            same_bytes)
                cmp "$fault_final" "$fault_staged" || fail "foreign bytes changed"
                [[ ! "$fault_final" -ef "$fault_staged" ]] || fail "foreign inode was not replaced"
                ;;
        esac
        # A failed first link never publishes BAI; a failed second link rolls
        # back the provably owned BAM. Both staging anchors remain for recovery.
        if [[ "$failed_output" == bam ]]; then
            assert_not_exists "$fault_bai"
        else
            assert_not_exists "$fault_bam"
        fi
    done
done

printf 'Running dangling final symlink refusal checks...\n'
for dangling_output in bam bai; do
    dangling_sample="sample_dangling_$dangling_output"
    dangling_dir="$tmp_dir/results/$dangling_sample"
    mkdir -p "$dangling_dir"
    dangling_bam="$dangling_dir/$dangling_sample.sorted.bam"
    dangling_bai="$dangling_bam.bai"
    dangling_final="$dangling_bam"
    dangling_other="$dangling_bai"
    if [[ "$dangling_output" == bai ]]; then
        dangling_final="$dangling_bai"
        dangling_other="$dangling_bam"
    fi
    dangling_target="$dangling_dir/missing-target"
    ln -s "$dangling_target" "$dangling_final"
    dangling_log="$tmp_dir/$dangling_sample.out"
    assert_fails "$dangling_log" env FAKE_SAMPLE_ID="$dangling_sample" \
        SLURM_JOB_ID=dangling001 bash "$SCRIPT" \
        --sample-id "$dangling_sample" --input-alignment "$safe_input" \
        --output-dir "$dangling_dir" --threads 2 --execute
    assert_contains "$dangling_log" "final path already exists; refusing to replace: $dangling_final"
    assert_contains "$dangling_log" "Step 02 no-clobber rollback was incomplete"
    [[ -L "$dangling_final" && "$(readlink "$dangling_final")" == "$dangling_target" ]] ||
        fail "publication changed a dangling final symlink"
    assert_not_exists "$dangling_target"
    assert_not_exists "$dangling_other"
    assert_contains "$dangling_dir/.$dangling_sample.step02.dangling001.rg.tmp.bam" "@RG"
    assert_file_equals "$dangling_dir/.$dangling_sample.step02.dangling001.rg.tmp.bam.bai" "fake bam index"
    assert_file_equals "$dangling_dir/.$dangling_sample.step02.lock/owner" "run_token=dangling001"
done

printf 'Running no-clobber anchor cleanup failure characterization...\n'
for anchor_fault in retained partial; do
    anchor_sample="sample_anchor_$anchor_fault"
    anchor_dir="$tmp_dir/results/$anchor_sample"
    anchor_output="$tmp_dir/$anchor_sample.out"
    anchor_bam="$anchor_dir/$anchor_sample.sorted.bam"
    anchor_bai="$anchor_bam.bai"
    anchor_staged_bam="$anchor_dir/.$anchor_sample.step02.anchor001.rg.tmp.bam"
    anchor_staged_bai="$anchor_staged_bam.bai"
    removed_anchor=""
    if [[ "$anchor_fault" == partial ]]; then
        removed_anchor="$anchor_staged_bam"
    fi
    assert_fails "$anchor_output" env \
        FAKE_RM_FAIL_PATH="$anchor_staged_bai" \
        FAKE_RM_REMOVE_FIRST_PATH="$removed_anchor" \
        FAKE_SAMPLE_ID="$anchor_sample" SLURM_JOB_ID=anchor001 bash "$SCRIPT" \
        --sample-id "$anchor_sample" --input-alignment "$safe_input" \
        --output-dir "$anchor_dir" --threads 2 --execute
    assert_contains "$anchor_output" "fake rm forced failure: $anchor_staged_bai"
    assert_file_equals "$anchor_staged_bai" "fake bam index"
    assert_not_exists "$anchor_bai"
    if [[ "$anchor_fault" == partial ]]; then
        assert_not_exists "$anchor_staged_bam"
        assert_contains "$anchor_bam" "@RG"
        assert_contains "$anchor_output" "Step 02 no-clobber rollback was incomplete"
        assert_file_equals "$anchor_dir/.$anchor_sample.step02.lock/owner" "run_token=anchor001"
    else
        # Characterized gap: rollback removes both owned finals, but persistent
        # scratch cleanup failure does not prevent release of the owned lock.
        assert_not_exists "$anchor_bam"
        assert_contains "$anchor_staged_bam" "@RG"
        assert_not_exists "$anchor_dir/.$anchor_sample.step02.lock"
        assert_not_contains "$anchor_output" "Step 02 no-clobber rollback was incomplete"
    fi
    assert_fails "$anchor_output.retry" env FAKE_SAMPLE_ID="$anchor_sample" \
        SLURM_JOB_ID=anchor002 bash "$SCRIPT" \
        --sample-id "$anchor_sample" --input-alignment "$safe_input" \
        --output-dir "$anchor_dir" --threads 2 --execute
    assert_contains "$anchor_output.retry" "residue requires operator inspection"
    assert_file_equals "$anchor_staged_bai" "fake bam index"
done

printf 'Running no-clobber persistent lock cleanup failure check...\n'
lock_cleanup_dir="$tmp_dir/results/lock_cleanup"
lock_cleanup_owner="$lock_cleanup_dir/.sample_lock_cleanup.step02.lock/owner"
lock_cleanup_output="$tmp_dir/lock_cleanup.out"
assert_fails "$lock_cleanup_output" env FAKE_RM_FAIL_PATH="$lock_cleanup_owner" \
    FAKE_SAMPLE_ID=sample_lock_cleanup SLURM_JOB_ID=lock-cleanup001 bash "$SCRIPT" \
    --sample-id sample_lock_cleanup --input-alignment "$safe_input" \
    --output-dir "$lock_cleanup_dir" --threads 2 --execute
assert_contains "$lock_cleanup_output" "Could not remove owned lock metadata"
assert_not_contains "$lock_cleanup_output" "Rolling back Step 02 canonical outputs"
assert_file_equals "$lock_cleanup_owner" "run_token=lock-cleanup001"
assert_contains "$lock_cleanup_dir/sample_lock_cleanup.sorted.bam" "@RG"
assert_file_equals "$lock_cleanup_dir/sample_lock_cleanup.sorted.bam.bai" "fake bam index"
assert_not_exists "$lock_cleanup_dir/.sample_lock_cleanup.step02.lock-cleanup001.rg.tmp.bam"
assert_not_exists "$lock_cleanup_dir/.sample_lock_cleanup.step02.lock-cleanup001.rg.tmp.bam.bai"

printf 'Running old predecessor backup residue refusal checks...\n'
for old_suffix in previous.bam previous.bam.bai; do
    old_dir="$tmp_dir/results/old_$old_suffix"
    mkdir -p "$old_dir"
    old_path="$old_dir/.sample_old.step02.older-token.$old_suffix"
    printf 'retained predecessor\n' >"$old_path"
    old_output="$tmp_dir/old_$old_suffix.out"
    assert_fails "$old_output" env FAKE_SAMPLE_ID=sample_old SLURM_JOB_ID=old001 bash "$SCRIPT" \
        --sample-id sample_old --input-alignment "$safe_input" \
        --output-dir "$old_dir" --threads 2 --execute
    assert_contains "$old_output" "residue requires operator inspection"
    assert_file_equals "$old_path" "retained predecessor"
    assert_not_exists "$old_dir/.sample_old.step02.lock"
    assert_not_exists "$old_dir/sample_old.sorted.bam"
    assert_not_exists "$old_dir/sample_old.sorted.bam.bai"
done

printf 'Running existing lock failure check...\n'
lock_output_dir="$tmp_dir/results/locked"
mkdir -p "$lock_output_dir/.sample_locked.step02.lock"
# A foreign lock must be reported and preserved; Step 02 must not break it.
printf 'run_token=other-job\n' >"$lock_output_dir/.sample_locked.step02.lock/owner"
printf 'old bam\n' >"$lock_output_dir/sample_locked.sorted.bam"
printf 'old bai\n' >"$lock_output_dir/sample_locked.sorted.bam.bai"
lock_output="$tmp_dir/lock.out"
assert_fails "$lock_output" env FAKE_SAMPLE_ID=sample_locked SLURM_JOB_ID=lock001 bash "$SCRIPT" \
    --sample-id sample_locked \
    --input-alignment "$input_sam" \
    --output-dir "$lock_output_dir" \
    --threads 1 \
    --execute
assert_contains "$lock_output" "residue requires operator inspection"
assert_file_equals "$lock_output_dir/.sample_locked.step02.lock/owner" "run_token=other-job"
assert_file_equals "$lock_output_dir/sample_locked.sorted.bam" "old bam"
assert_file_equals "$lock_output_dir/sample_locked.sorted.bam.bai" "old bai"
[[ -d "$lock_output_dir/.sample_locked.step02.lock" ]] || fail "foreign lock should remain"

printf 'Running validation failure cleanup check...\n'
validation_output_dir="$tmp_dir/results/validation_failure"
validation_output="$tmp_dir/validation_failure.out"
assert_fails "$validation_output" env FAKE_SAMPLE_ID=sample_bad_rg FAKE_RG_MODE=missing SLURM_JOB_ID=val001 bash "$SCRIPT" \
    --sample-id sample_bad_rg \
    --input-alignment "$input_sam" \
    --output-dir "$validation_output_dir" \
    --threads 1 \
    --execute
assert_contains "$validation_output" "must contain exactly one @RG line"
assert_not_exists "$validation_output_dir/.sample_bad_rg.step02.lock"
assert_not_exists "$validation_output_dir/sample_bad_rg.sorted.bam"
assert_not_exists "$validation_output_dir/sample_bad_rg.sorted.bam.bai"
assert_no_step02_scratch "$validation_output_dir"

printf 'Running malformed and extra @RG validation checks...\n'
bad_rg_output="$tmp_dir/bad_rg.out"
assert_fails "$bad_rg_output" env FAKE_SAMPLE_ID=sample_malformed FAKE_RG_MODE=malformed SLURM_JOB_ID=bad001 bash "$SCRIPT" \
    --sample-id sample_malformed \
    --input-alignment "$input_sam" \
    --output-dir "$tmp_dir/results/malformed" \
    --threads 1 \
    --execute
assert_contains "$bad_rg_output" "missing SM:sample_malformed"

extra_rg_output="$tmp_dir/extra_rg.out"
assert_fails "$extra_rg_output" env FAKE_SAMPLE_ID=sample_extra FAKE_RG_MODE=extra SLURM_JOB_ID=extra001 bash "$SCRIPT" \
    --sample-id sample_extra \
    --input-alignment "$input_sam" \
    --output-dir "$tmp_dir/results/extra" \
    --threads 1 \
    --execute
assert_contains "$extra_rg_output" "must contain exactly one @RG line"

printf 'Running partial RG tagging failure check...\n'
partial_output="$tmp_dir/partial.out"
assert_fails "$partial_output" env FAKE_SAMPLE_ID=sample_partial FAKE_TAGGED_MODE=partial SLURM_JOB_ID=partial001 bash "$SCRIPT" \
    --sample-id sample_partial \
    --input-alignment "$input_sam" \
    --output-dir "$tmp_dir/results/partial" \
    --threads 1 \
    --execute
assert_contains "$partial_output" "records tagged RG:sample_partial"

printf 'Running coordinate sort validation failure check...\n'
sort_output="$tmp_dir/sort_validation.out"
assert_fails "$sort_output" env FAKE_SAMPLE_ID=sample_sort FAKE_SORT_MODE=unknown SLURM_JOB_ID=sort001 bash "$SCRIPT" \
    --sample-id sample_sort \
    --input-alignment "$input_sam" \
    --output-dir "$tmp_dir/results/sort_validation" \
    --threads 1 \
    --execute
assert_contains "$sort_output" "header is not coordinate sorted"

printf 'Running default refusal of existing complete and partial outputs...\n'
# The retired replacement/restore-loss sequence is retained in CONTRACT.md;
# current calls must preserve predecessors before invoking scientific tools.
for prior_state in pair bam bai; do
    prior_sample="sample_prior_$prior_state"
    prior_dir="$tmp_dir/results/$prior_sample"
    mkdir -p "$prior_dir"
    prior_bam="$prior_dir/$prior_sample.sorted.bam"
    prior_bai="$prior_bam.bai"
    if [[ "$prior_state" != bai ]]; then
        printf 'previous bam\n' >"$prior_bam"
    fi
    if [[ "$prior_state" != bam ]]; then
        printf 'previous bai\n' >"$prior_bai"
    fi
    prior_output="$tmp_dir/$prior_sample.out"
    tool_lines_before="$(wc -l <"$samtools_log")"
    assert_fails "$prior_output" env FAKE_SAMPLE_ID="$prior_sample" SLURM_JOB_ID=prior001 bash "$SCRIPT" \
        --sample-id "$prior_sample" --input-alignment "$input_sam" \
        --output-dir "$prior_dir" --threads 1 --execute
    assert_contains "$prior_output" "requires both canonical outputs to be absent"
    [[ "$(wc -l <"$samtools_log")" == "$tool_lines_before" ]] ||
        fail "existing output refusal invoked samtools"
    if [[ "$prior_state" != bai ]]; then
        assert_file_equals "$prior_bam" "previous bam"
    else
        assert_not_exists "$prior_bam"
    fi
    if [[ "$prior_state" != bam ]]; then
        assert_file_equals "$prior_bai" "previous bai"
    else
        assert_not_exists "$prior_bai"
    fi
    assert_no_step02_scratch "$prior_dir"
done

printf 'All step_02 canonical BAM hardening smoke tests passed.\n'
