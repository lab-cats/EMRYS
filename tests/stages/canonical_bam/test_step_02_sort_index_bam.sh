#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh"
unset EMRYS_RUN_TOKEN
export EMRYS_SHA256_PYTHON="$REPO_ROOT/.venv/bin/python"

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
mv_log="$tmp_dir/mv_invocations.log"

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

cat >"$fake_bin/mv" <<EOF_MV
#!/usr/bin/env bash
set -euo pipefail

printf 'mv invoked\\n' >> "$mv_log"
printf '%s\\n' "\$@" >> "$mv_log"

src="\${1:-}"
dest="\${2:-}"

if [[ -n "\${FAKE_MV_ALWAYS_FAIL_SOURCE:-}" && "\$src" == "\$FAKE_MV_ALWAYS_FAIL_SOURCE" ]]; then
    printf 'fake mv forced persistent failure for source: %s\n' "\$src" >&2
    exit 66
fi

fail_marker="${tmp_dir}/fake_mv_failed.\${FAKE_MV_FAIL_DEST_MATCH:-none}"
# Forced mv failures are one-shot so rollback moves can still restore files.
if [[ -n "\${FAKE_MV_FAIL_DEST_MATCH:-}" && "\$dest" == *"\$FAKE_MV_FAIL_DEST_MATCH"* && ! -e "\$fail_marker" ]]; then
    printf 'failed\\n' > "\$fail_marker"
    printf 'fake mv forced failure for destination: %s\\n' "\$dest" >&2
    exit 65
fi

/bin/mv "\$@"
EOF_MV
chmod +x "$fake_bin/mv"

cat >"$fake_bin/ln" <<'EOF_LN'
#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--" ]]; then
    src="${2:-}"
    dest="${3:-}"
else
    src="${1:-}"
    dest="${2:-}"
fi

/bin/ln "$@"

if [[ -n "${FAKE_LN_MUTATE_AFTER_DEST:-}" &&
      "$dest" == "$FAKE_LN_MUTATE_AFTER_DEST" ]]; then
    printf 'mutated after final BAM publication\n' >"$src"
fi
EOF_LN
chmod +x "$fake_bin/ln"

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
    FAKE_LN_MUTATE_AFTER_DEST="$publication_mutation_bam" \
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
assert_contains "$safe_repeat_output" "--no-clobber requires both canonical outputs to be absent"
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
    --no-clobber \
    --execute
assert_contains "$mutation_output" "Input alignment changed during Step 02"
assert_not_exists "$mutation_output_dir/sample_mutation.sorted.bam"
assert_not_exists "$mutation_output_dir/sample_mutation.sorted.bam.bai"
assert_not_exists "$mutation_output_dir/.sample_mutation.step02.lock"

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
assert_contains "$lock_output" "Step 02 lock already exists"
assert_contains "$lock_output" "run_token=other-job"
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

printf 'Running inconsistent canonical pair failure check...\n'
inconsistent_output_dir="$tmp_dir/results/inconsistent"
mkdir -p "$inconsistent_output_dir"
printf 'old bam\n' >"$inconsistent_output_dir/sample_inconsistent.sorted.bam"
inconsistent_output="$tmp_dir/inconsistent.out"
assert_fails "$inconsistent_output" env FAKE_SAMPLE_ID=sample_inconsistent SLURM_JOB_ID=incon001 bash "$SCRIPT" \
    --sample-id sample_inconsistent \
    --input-alignment "$input_sam" \
    --output-dir "$inconsistent_output_dir" \
    --threads 1 \
    --execute
assert_contains "$inconsistent_output" "Canonical outputs are inconsistent"
assert_file_equals "$inconsistent_output_dir/sample_inconsistent.sorted.bam" "old bam"
assert_not_exists "$inconsistent_output_dir/sample_inconsistent.sorted.bam.bai"
assert_not_exists "$inconsistent_output_dir/.sample_inconsistent.step02.lock"
assert_no_step02_scratch "$inconsistent_output_dir"

printf 'Running backup failure rollback check...\n'
backup_output_dir="$tmp_dir/results/backup_failure"
mkdir -p "$backup_output_dir"
printf 'previous bam\n' >"$backup_output_dir/sample_backup.sorted.bam"
printf 'previous bai\n' >"$backup_output_dir/sample_backup.sorted.bam.bai"
backup_output="$tmp_dir/backup_failure.out"
# Fail while moving the old BAI to backup; the old BAM must be restored.
assert_fails "$backup_output" env FAKE_SAMPLE_ID=sample_backup FAKE_MV_FAIL_DEST_MATCH=".sample_backup.step02.backup001.previous.bam.bai" SLURM_JOB_ID=backup001 bash "$SCRIPT" \
    --sample-id sample_backup \
    --input-alignment "$input_sam" \
    --output-dir "$backup_output_dir" \
    --threads 1 \
    --execute
assert_contains "$backup_output" "fake mv forced failure"
assert_file_equals "$backup_output_dir/sample_backup.sorted.bam" "previous bam"
assert_file_equals "$backup_output_dir/sample_backup.sorted.bam.bai" "previous bai"
assert_not_exists "$backup_output_dir/.sample_backup.step02.lock"
assert_no_step02_scratch "$backup_output_dir"

printf 'Running publish failure rollback check with previous pair...\n'
publish_output_dir="$tmp_dir/results/publish_failure"
mkdir -p "$publish_output_dir"
printf 'previous bam\n' >"$publish_output_dir/sample_publish.sorted.bam"
printf 'previous bai\n' >"$publish_output_dir/sample_publish.sorted.bam.bai"
publish_output="$tmp_dir/publish_failure.out"
# Fail after the new BAM is published but before the new BAI is published.
assert_fails "$publish_output" env FAKE_SAMPLE_ID=sample_publish FAKE_MV_FAIL_DEST_MATCH="sample_publish.sorted.bam.bai" SLURM_JOB_ID=pub001 bash "$SCRIPT" \
    --sample-id sample_publish \
    --input-alignment "$input_sam" \
    --output-dir "$publish_output_dir" \
    --threads 1 \
    --execute
assert_contains "$publish_output" "Rolling back Step 02 canonical outputs"
assert_file_equals "$publish_output_dir/sample_publish.sorted.bam" "previous bam"
assert_file_equals "$publish_output_dir/sample_publish.sorted.bam.bai" "previous bai"
assert_not_exists "$publish_output_dir/.sample_publish.step02.lock"
assert_no_step02_scratch "$publish_output_dir"

printf 'Running failure-inside-rollback characterization check...\n'
restore_failure_output_dir="$tmp_dir/results/restore_failure"
mkdir -p "$restore_failure_output_dir"
printf 'previous bam\n' >"$restore_failure_output_dir/sample_restore.sorted.bam"
printf 'previous bai\n' >"$restore_failure_output_dir/sample_restore.sorted.bam.bai"
restore_failure_output="$tmp_dir/restore_failure.out"
restore_failure_backup_bam="$restore_failure_output_dir/.sample_restore.step02.restore001.previous.bam"
# Fail final BAI publication, then fail only restoration of the prior BAM.
assert_fails "$restore_failure_output" env \
    FAKE_SAMPLE_ID=sample_restore \
    FAKE_MV_FAIL_DEST_MATCH="sample_restore.sorted.bam.bai" \
    FAKE_MV_ALWAYS_FAIL_SOURCE="$restore_failure_backup_bam" \
    SLURM_JOB_ID=restore001 \
    bash "$SCRIPT" \
    --sample-id sample_restore \
    --input-alignment "$input_sam" \
    --output-dir "$restore_failure_output_dir" \
    --threads 1 \
    --execute
assert_contains "$restore_failure_output" "fake mv forced failure for destination"
assert_contains "$restore_failure_output" "Rolling back Step 02 canonical outputs"
assert_contains "$restore_failure_output" "fake mv forced persistent failure for source"
assert_not_exists "$restore_failure_output_dir/sample_restore.sorted.bam"
assert_file_equals "$restore_failure_output_dir/sample_restore.sorted.bam.bai" "previous bai"
assert_not_exists "$restore_failure_backup_bam"
assert_not_exists "$restore_failure_backup_bam.bai"
assert_not_exists "$restore_failure_output_dir/.sample_restore.step02.lock"
assert_no_step02_scratch "$restore_failure_output_dir"

printf 'Running publish failure rollback check with no previous pair...\n'
no_previous_output_dir="$tmp_dir/results/no_previous_publish_failure"
no_previous_output="$tmp_dir/no_previous_publish_failure.out"
# With no previous pair, rollback should leave no canonical outputs at all.
assert_fails "$no_previous_output" env FAKE_SAMPLE_ID=sample_new FAKE_MV_FAIL_DEST_MATCH="sample_new.sorted.bam.bai" SLURM_JOB_ID=new001 bash "$SCRIPT" \
    --sample-id sample_new \
    --input-alignment "$input_sam" \
    --output-dir "$no_previous_output_dir" \
    --threads 1 \
    --execute
assert_contains "$no_previous_output" "Rolling back Step 02 canonical outputs"
assert_not_exists "$no_previous_output_dir/sample_new.sorted.bam"
assert_not_exists "$no_previous_output_dir/sample_new.sorted.bam.bai"
assert_not_exists "$no_previous_output_dir/.sample_new.step02.lock"
assert_no_step02_scratch "$no_previous_output_dir"

printf 'Running final validation rollback check...\n'
final_output_dir="$tmp_dir/results/final_validation_failure"
mkdir -p "$final_output_dir"
printf 'previous bam\n' >"$final_output_dir/sample_final.sorted.bam"
printf 'previous bai\n' >"$final_output_dir/sample_final.sorted.bam.bai"
final_output="$tmp_dir/final_validation_failure.out"
# Final validation failure happens after both publish moves, so backup restore is required.
assert_fails "$final_output" env FAKE_SAMPLE_ID=sample_final FAKE_QUICKCHECK_FAIL_MATCH="sample_final.sorted.bam" SLURM_JOB_ID=final001 bash "$SCRIPT" \
    --sample-id sample_final \
    --input-alignment "$input_sam" \
    --output-dir "$final_output_dir" \
    --threads 1 \
    --execute
assert_contains "$final_output" "Rolling back Step 02 canonical outputs"
assert_file_equals "$final_output_dir/sample_final.sorted.bam" "previous bam"
assert_file_equals "$final_output_dir/sample_final.sorted.bam.bai" "previous bai"
assert_not_exists "$final_output_dir/.sample_final.step02.lock"
assert_no_step02_scratch "$final_output_dir"

printf 'All step_02 canonical BAM hardening smoke tests passed.\n'
