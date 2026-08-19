#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/src/norad/stages/star_alignment/step_01_star_align.sh"
unset NORAD_RUN_TOKEN
export NORAD_SHA256_PYTHON="$REPO_ROOT/.venv/bin/python"

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
        fail "unexpected output present"
    fi
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
real_rm_bin="$(command -v rm)"
real_ln_bin="$(command -v ln)"
real_cp_bin="$(command -v cp)"

cat >"$fake_bin/rm" <<'EOF_RM'
#!/usr/bin/env bash
set -euo pipefail

for argument in "$@"; do
    if [[ -n "${FAIL_RM_TARGET:-}" && "$argument" == "$FAIL_RM_TARGET" ]]; then
        printf 'controlled cleanup removal failure: %s\n' "$argument" >&2
        exit 79
    fi
done
exec "$REAL_RM_BIN" "$@"
EOF_RM
chmod +x "$fake_bin/rm"
export REAL_RM_BIN="$real_rm_bin"

cat >"$fake_bin/ln" <<'EOF_LN'
#!/usr/bin/env bash
set -euo pipefail

destination="${!#}"
if [[ -n "${INJECT_LATE_FINAL_DESTINATION:-}" &&
      "$destination" == "$INJECT_LATE_FINAL_DESTINATION" ]]; then
    if [[ -n "${INJECT_REPLACE_DESTINATION:-}" ]]; then
        "$REAL_RM_BIN" -f -- "$INJECT_REPLACE_DESTINATION"
        "$REAL_CP_BIN" -- "$INJECT_REPLACE_SOURCE" "$INJECT_REPLACE_DESTINATION"
    fi
    "$REAL_CP_BIN" -- "$INJECT_LATE_FINAL_SOURCE" "$destination"
    printf 'injected late foreign Step 01 output: %s\n' "$destination" >&2
fi
exec "$REAL_LN_BIN" "$@"
EOF_LN
chmod +x "$fake_bin/ln"
export REAL_LN_BIN="$real_ln_bin"
export REAL_CP_BIN="$real_cp_bin"

star_log="$tmp_dir/star_invocations.log"
cat >"$fake_bin/STAR" <<EOF_STAR
#!/usr/bin/env bash
printf 'STAR invoked\n' >> "$star_log"
printf '%s\n' "\$@" >> "$star_log"
status="\${STAR_EXIT_CODE:-0}"
if [[ "\$status" -eq 0 ]]; then
    prefix=""
    while [[ \$# -gt 0 ]]; do
        if [[ "\$1" == "--outFileNamePrefix" ]]; then
            prefix="\$2"
            break
        fi
        shift
    done
    [[ -n "\$prefix" ]] || exit 64
    mkdir -p "\$(dirname "\$prefix")"
    for suffix in Aligned.sortedByCoord.out.bam Log.final.out Log.out Log.progress.out SJ.out.tab; do
        printf 'fake STAR %s\n' "\$suffix" >"\${prefix}\${suffix}"
    done
    if [[ -n "\${STAR_MUTATE_INDEX_FILE:-}" ]]; then
        printf 'mutated during STAR\n' >>"\$STAR_MUTATE_INDEX_FILE"
    fi
fi
exit "\$status"
EOF_STAR
chmod +x "$fake_bin/STAR"

cat >"$fake_bin/gunzip" <<'EOF_GUNZIP'
#!/usr/bin/env bash
printf 'hostile PATH gunzip must not be selected when --gunzip-bin is explicit\n' >&2
exit 99
EOF_GUNZIP
chmod +x "$fake_bin/gunzip"

controlled_bin="$tmp_dir/controlled-bin"
mkdir -p "$controlled_bin"
bound_gunzip="$controlled_bin/gunzip"
cat >"$bound_gunzip" <<'EOF_BOUND_GUNZIP'
#!/usr/bin/env bash
exec /usr/bin/gunzip "$@"
EOF_BOUND_GUNZIP
chmod +x "$bound_gunzip"

export PATH="$fake_bin:$PATH"

fixture_dir="$tmp_dir/fixtures"
star_index="$fixture_dir/star_index"
mkdir -p "$star_index"
printf 'fake SA index bytes\n' >"$star_index/SA"
printf 'fake Genome index bytes\n' >"$star_index/Genome"

r1_fastq="$fixture_dir/sample_R1.fastq"
r2_fastq="$fixture_dir/sample_R2.fastq"
r1_gz="$fixture_dir/sample_R1.fastq.gz"
r2_gz="$fixture_dir/sample_R2.fastq.gz"

printf '@r1\nACGT\n+\n!!!!\n' >"$r1_fastq"
printf '@r2\nTGCA\n+\n!!!!\n' >"$r2_fastq"
printf 'placeholder gz r1\n' >"$r1_gz"
printf 'placeholder gz r2\n' >"$r2_gz"

printf 'Running syntax check...\n'
bash -n "$SCRIPT"

printf 'Running help check...\n'
help_output="$tmp_dir/help.out"
bash "$SCRIPT" --help >"$help_output"
assert_contains "$help_output" "Usage:"
assert_contains "$help_output" "--gunzip-bin"
assert_contains "$help_output" "no clobbering execution mode."
assert_contains "$help_output" "--execute"

printf 'Running dry-run check...\n'
dry_output="$tmp_dir/dry.out"
dry_output_dir="$tmp_dir/results/dry"
NORAD_RUN_TOKEN=explicit-owner-01 SLURM_JOB_ID=scheduler-01 bash "$SCRIPT" \
    --sample-id sample_001 \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$dry_output_dir" \
    --threads 4 \
    --gunzip-bin "$bound_gunzip" \
    >"$dry_output"

[[ ! -e "$dry_output_dir" ]] || fail "dry-run created output directory"
[[ ! -e "$star_log" ]] || fail "dry-run invoked STAR"
assert_contains "$dry_output" "Mode: dry-run"
assert_contains "$dry_output" "Run token: explicit-owner-01"
assert_contains "$dry_output" "gunzip bin: not-required"
assert_contains "$dry_output" "No-clobber transaction: true"
assert_contains "$dry_output" ".sample_001.step01.explicit-owner-01.staging"
assert_contains "$dry_output" "--outFileNamePrefix"
assert_contains "$dry_output" "$dry_output_dir/sample_001."
assert_contains "$dry_output" "--outSAMtype"
assert_contains "$dry_output" "BAM"
assert_contains "$dry_output" "SortedByCoordinate"
assert_contains "$dry_output" "--outSAMattrRGline"
assert_contains "$dry_output" "ID:sample_001"
assert_contains "$dry_output" "SM:sample_001"
assert_contains "$dry_output" "LB:sample_001"
assert_contains "$dry_output" "PL:ILLUMINA"
assert_not_contains "$dry_output" "--readFilesCommand"

printf 'Running occupied output dry-run report check...\n'
occupied_dry_output="$tmp_dir/occupied-dry.out"
occupied_dry_output_dir="$tmp_dir/results/occupied-dry"
occupied_dry_final="$occupied_dry_output_dir/sample_occupied.Log.out"
mkdir -p "$occupied_dry_output_dir"
printf 'preserve occupied bytes\n' >"$occupied_dry_final"
bash "$SCRIPT" \
    --sample-id sample_occupied \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$occupied_dry_output_dir" \
    --threads 2 \
    --star-bin "$fake_bin/STAR" \
    >"$occupied_dry_output"
assert_contains "$occupied_dry_output" "Existing declared output: $occupied_dry_final"
assert_contains "$occupied_dry_output" \
    "Execute would refuse to clobber the existing declared output set."
[[ "$(<"$occupied_dry_final")" == "preserve occupied bytes" ]] ||
    fail "occupied dry-run changed existing output bytes"
[[ ! -e "$star_log" ]] || fail "occupied dry-run invoked STAR"

printf 'Running execute check...\n'
execute_output="$tmp_dir/execute.out"
execute_output_dir="$tmp_dir/results/execute"
bash "$SCRIPT" \
    --sample-id sample_002 \
    --r1-fastq "$r1_gz" \
    --r2-fastq "$r2_gz" \
    --star-index "$star_index" \
    --output-dir "$execute_output_dir" \
    --threads 2 \
    --gunzip-bin "$bound_gunzip" \
    --execute \
    >"$execute_output"

[[ -d "$execute_output_dir" ]] || fail "execute did not create output directory"
[[ -e "$star_log" ]] || fail "execute did not invoke STAR"
assert_contains "$star_log" "STAR invoked"
assert_contains "$star_log" "--runThreadN"
assert_contains "$star_log" "2"
assert_contains "$star_log" "$execute_output_dir/.sample_002.step01."
assert_contains "$star_log" ".staging/sample_002."
assert_contains "$star_log" "--outSAMtype"
assert_contains "$star_log" "BAM"
assert_contains "$star_log" "SortedByCoordinate"
assert_contains "$star_log" "--outSAMattrRGline"
assert_contains "$star_log" "ID:sample_002"
assert_contains "$star_log" "SM:sample_002"
assert_contains "$star_log" "LB:sample_002"
assert_contains "$star_log" "PL:ILLUMINA"
assert_contains "$star_log" "--readFilesCommand"
assert_contains "$star_log" "$bound_gunzip"
assert_not_contains "$star_log" "$fake_bin/gunzip"
assert_contains "$execute_output" "Mode: execute"
assert_contains "$execute_output" "gunzip bin: $bound_gunzip"
assert_contains "$execute_output" "No-clobber transaction: true"
for suffix in Aligned.sortedByCoord.out.bam Log.final.out Log.out Log.progress.out SJ.out.tab; do
    [[ -s "$execute_output_dir/sample_002.$suffix" ]] ||
        fail "default execute did not publish declared output: $suffix"
done
[[ ! -e "$execute_output_dir/.sample_002.step01.lock" ]] ||
    fail "default execute left its Step 01 lock"
[[ -z "$(find "$execute_output_dir" -maxdepth 1 -name '.sample_002.step01.*.staging' -print -quit)" ]] ||
    fail "default execute left staging residue"

printf 'Running orchestration-safe no-clobber transaction check...\n'
residue_output_dir="$tmp_dir/results/residue"
mkdir -p "$residue_output_dir/.sample_residue.step01.older-token.staging"
residue_marker="$residue_output_dir/.sample_residue.step01.older-token.staging/preserve"
printf 'preserve residue\n' >"$residue_marker"
residue_output="$tmp_dir/residue.out"
assert_fails "$residue_output" env SLURM_JOB_ID=newer-token bash "$SCRIPT" \
    --sample-id sample_residue \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$residue_output_dir" \
    --threads 2 \
    --star-bin "$fake_bin/STAR" \
    --execute
assert_contains "$residue_output" "residue requires operator inspection"
[[ "$(<"$residue_marker")" == "preserve residue" ]] || fail "Step 01 removed foreign residue"
[[ ! -e "$residue_output_dir/.sample_residue.step01.lock" ]] || fail "Step 01 residue refusal created a lock"
safe_output="$tmp_dir/safe.out"
safe_output_dir="$tmp_dir/results/safe"
bash "$SCRIPT" \
    --sample-id sample_safe \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$safe_output_dir" \
    --threads 2 \
    --star-bin "$fake_bin/STAR" \
    --no-clobber \
    --execute \
    >"$safe_output"
for suffix in Aligned.sortedByCoord.out.bam Log.final.out Log.out Log.progress.out SJ.out.tab; do
    [[ -s "$safe_output_dir/sample_safe.$suffix" ]] || fail "missing declared no-clobber output: $suffix"
done
assert_contains "$safe_output" "No-clobber transaction: true"
assert_contains "$safe_output" "STAR index member count: 2"
assert_contains "$safe_output" $'STAR index member: Genome\t'
assert_contains "$safe_output" $'STAR index member: SA\t'
genome_snapshot_line="$(grep -n -F $'STAR index member: Genome\t' "$safe_output" | cut -d: -f1)"
sa_snapshot_line="$(grep -n -F $'STAR index member: SA\t' "$safe_output" | cut -d: -f1)"
[[ "$genome_snapshot_line" -lt "$sa_snapshot_line" ]] ||
    fail "STAR index snapshot was not emitted in deterministic bytewise name order"
[[ ! -e "$safe_output_dir/.sample_safe.step01.lock" ]] || fail "successful no-clobber run left lock"
[[ -z "$(find "$safe_output_dir" -maxdepth 1 -name '.sample_safe.step01.*.staging' -print -quit)" ]] ||
    fail "successful no-clobber run left staging residue"
safe_repeat_output="$tmp_dir/safe_repeat.out"
safe_repeat_snapshot="$tmp_dir/safe-repeat-snapshot"
mkdir "$safe_repeat_snapshot"
for suffix in Aligned.sortedByCoord.out.bam Log.final.out Log.out Log.progress.out SJ.out.tab; do
    cp "$safe_output_dir/sample_safe.$suffix" "$safe_repeat_snapshot/$suffix"
done
star_log_lines_before_repeat="$(wc -l < "$star_log" | tr -d ' ')"
assert_fails "$safe_repeat_output" bash "$SCRIPT" \
    --sample-id sample_safe \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$safe_output_dir" \
    --threads 2 \
    --star-bin "$fake_bin/STAR" \
    --execute
assert_contains "$safe_repeat_output" "output already exists; refusing to clobber"
[[ "$(wc -l < "$star_log" | tr -d ' ')" == "$star_log_lines_before_repeat" ]] ||
    fail "pre-existing output refusal invoked STAR"
for suffix in Aligned.sortedByCoord.out.bam Log.final.out Log.out Log.progress.out SJ.out.tab; do
    cmp -s "$safe_repeat_snapshot/$suffix" "$safe_output_dir/sample_safe.$suffix" ||
        fail "pre-existing output refusal changed declared bytes: $suffix"
done

printf 'Running no-clobber empty/ambiguous STAR-index admission checks...\n'
empty_index="$tmp_dir/fixtures/empty_star_index"
mkdir -p "$empty_index"
empty_index_output="$tmp_dir/empty_index.out"
assert_fails "$empty_index_output" bash "$SCRIPT" \
    --sample-id sample_empty_index \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$empty_index" \
    --output-dir "$tmp_dir/results/empty_index" \
    --threads 2 \
    --star-bin "$fake_bin/STAR" \
    --no-clobber
assert_contains "$empty_index_output" "STAR index contains no top-level files"

ambiguous_index="$tmp_dir/fixtures/ambiguous_star_index"
mkdir -p "$ambiguous_index"
ln -s "$star_index/Genome" "$ambiguous_index/Genome"
ambiguous_index_output="$tmp_dir/ambiguous_index.out"
assert_fails "$ambiguous_index_output" bash "$SCRIPT" \
    --sample-id sample_ambiguous_index \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$ambiguous_index" \
    --output-dir "$tmp_dir/results/ambiguous_index" \
    --threads 2 \
    --star-bin "$fake_bin/STAR" \
    --no-clobber
assert_contains "$ambiguous_index_output" "STAR index top-level member is a symbolic link"

printf 'Running no-clobber STAR-index mutation rejection check...\n'
mutation_index="$tmp_dir/fixtures/mutation_star_index"
mkdir -p "$mutation_index"
printf 'mutation Genome index bytes\n' >"$mutation_index/Genome"
printf 'mutation SA index bytes\n' >"$mutation_index/SA"
mutation_index_file="$mutation_index/Genome"
mutation_output="$tmp_dir/index_mutation.out"
mutation_output_dir="$tmp_dir/results/index_mutation"
mutation_token="index-mutation"
assert_fails "$mutation_output" env \
    STAR_MUTATE_INDEX_FILE="$mutation_index_file" \
    SLURM_JOB_ID="$mutation_token" \
    bash "$SCRIPT" \
    --sample-id sample_index_mutation \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$mutation_index" \
    --output-dir "$mutation_output_dir" \
    --threads 2 \
    --star-bin "$fake_bin/STAR" \
    --no-clobber \
    --execute
assert_contains "$mutation_output" "STAR index membership or bytes changed during Step 01"
assert_contains "$mutation_index_file" "mutated during STAR"
for suffix in Aligned.sortedByCoord.out.bam Log.final.out Log.out Log.progress.out SJ.out.tab; do
    [[ ! -e "$mutation_output_dir/sample_index_mutation.$suffix" ]] ||
        fail "index mutation published a final STAR output: $suffix"
done
[[ ! -e "$mutation_output_dir/.sample_index_mutation.step01.$mutation_token.staging" ]] ||
    fail "index mutation left owned staging residue"
[[ ! -e "$mutation_output_dir/.sample_index_mutation.step01.lock" ]] ||
    fail "index mutation left owned lock"

printf 'Running no-clobber late-final publication race check...\n'
late_sample="sample_late_final"
late_token="late-final"
late_output="$tmp_dir/late_final.out"
late_output_dir="$tmp_dir/results/late_final"
late_staging="$late_output_dir/.${late_sample}.step01.${late_token}.staging"
late_lock="$late_output_dir/.${late_sample}.step01.lock"
late_final="$late_output_dir/${late_sample}.Aligned.sortedByCoord.out.bam"
late_foreign_source="$tmp_dir/late_final_foreign_source"
printf 'late foreign BAM bytes\n' >"$late_foreign_source"
assert_fails "$late_output" env \
    INJECT_LATE_FINAL_DESTINATION="$late_final" \
    INJECT_LATE_FINAL_SOURCE="$late_foreign_source" \
    SLURM_JOB_ID="$late_token" \
    bash "$SCRIPT" \
    --sample-id "$late_sample" \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$late_output_dir" \
    --threads 2 \
    --star-bin "$fake_bin/STAR" \
    --no-clobber \
    --execute
cmp -s "$late_foreign_source" "$late_final" ||
    fail "late foreign Step 01 final was overwritten or deleted"
[[ -d "$late_staging" ]] || fail "late-final race did not preserve staging residue"
[[ -d "$late_lock" ]] || fail "late-final race did not retain the owner lock"
[[ -s "$late_staging/${late_sample}.Aligned.sortedByCoord.out.bam" ]] ||
    fail "late-final race did not retain the staged ownership anchor"
assert_contains "$late_lock/owner" "run_token=$late_token"
assert_contains "$late_output" "injected late foreign Step 01 output"
assert_contains "$late_output" "Refusing to replace a late or foreign Step 01 output"
assert_contains "$late_output" "Step 01 no-clobber cleanup was incomplete"

printf 'Running no-clobber replacement-after-publication race check...\n'
replacement_sample="sample_replaced_final"
replacement_token="replaced-final"
replacement_output="$tmp_dir/replaced_final.out"
replacement_output_dir="$tmp_dir/results/replaced_final"
replacement_staging="$replacement_output_dir/.${replacement_sample}.step01.${replacement_token}.staging"
replacement_lock="$replacement_output_dir/.${replacement_sample}.step01.lock"
replacement_first_final="$replacement_output_dir/${replacement_sample}.Aligned.sortedByCoord.out.bam"
replacement_second_final="$replacement_output_dir/${replacement_sample}.Log.final.out"
replacement_first_source="$tmp_dir/replaced_first_foreign_source"
replacement_second_source="$tmp_dir/replaced_second_foreign_source"
printf 'replacement foreign BAM bytes\n' >"$replacement_first_source"
printf 'late foreign Log.final bytes\n' >"$replacement_second_source"
assert_fails "$replacement_output" env \
    INJECT_LATE_FINAL_DESTINATION="$replacement_second_final" \
    INJECT_LATE_FINAL_SOURCE="$replacement_second_source" \
    INJECT_REPLACE_DESTINATION="$replacement_first_final" \
    INJECT_REPLACE_SOURCE="$replacement_first_source" \
    SLURM_JOB_ID="$replacement_token" \
    bash "$SCRIPT" \
    --sample-id "$replacement_sample" \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$replacement_output_dir" \
    --threads 2 \
    --star-bin "$fake_bin/STAR" \
    --no-clobber \
    --execute
cmp -s "$replacement_first_source" "$replacement_first_final" ||
    fail "replacement race deleted or changed the foreign first final"
cmp -s "$replacement_second_source" "$replacement_second_final" ||
    fail "replacement race deleted or changed the late foreign second final"
[[ -d "$replacement_staging" ]] || fail "replacement race did not preserve staging residue"
[[ -d "$replacement_lock" ]] || fail "replacement race did not retain the owner lock"
[[ -s "$replacement_staging/${replacement_sample}.Aligned.sortedByCoord.out.bam" ]] ||
    fail "replacement race did not retain the first staged ownership anchor"
[[ -s "$replacement_staging/${replacement_sample}.Log.final.out" ]] ||
    fail "replacement race did not retain the second staged ownership anchor"
assert_contains "$replacement_lock/owner" "run_token=$replacement_token"
assert_contains "$replacement_output" "Published Step 01 output no longer belongs to this invocation"
assert_contains "$replacement_output" "preserving the foreign path"
assert_contains "$replacement_output" "Step 01 no-clobber cleanup was incomplete"

printf 'Running no-clobber cleanup-failure preservation check...\n'
cleanup_sample="sample_cleanup_failure"
cleanup_token="cleanup-failure"
cleanup_output="$tmp_dir/cleanup_failure.out"
cleanup_output_dir="$tmp_dir/results/cleanup_failure"
cleanup_staging="$cleanup_output_dir/.${cleanup_sample}.step01.${cleanup_token}.staging"
cleanup_lock="$cleanup_output_dir/.${cleanup_sample}.step01.lock"
set +e
STAR_EXIT_CODE=37 \
FAIL_RM_TARGET="$cleanup_staging" \
SLURM_JOB_ID="$cleanup_token" \
bash "$SCRIPT" \
    --sample-id "$cleanup_sample" \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$cleanup_output_dir" \
    --threads 2 \
    --star-bin "$fake_bin/STAR" \
    --no-clobber \
    --execute >"$cleanup_output" 2>&1
cleanup_status=$?
set -e
[[ "$cleanup_status" -eq 37 ]] || fail "cleanup-failure run did not preserve STAR exit 37"
[[ -d "$cleanup_staging" ]] || fail "cleanup failure did not preserve Step 01 staging residue"
[[ -d "$cleanup_lock" ]] || fail "cleanup failure did not retain Step 01 owner lock"
assert_contains "$cleanup_lock/owner" "run_token=$cleanup_token"
assert_contains "$cleanup_output" "controlled cleanup removal failure"
assert_contains "$cleanup_output" "Step 01 no-clobber cleanup was incomplete"

printf 'Running child failure propagation check...\n'
failure_output="$tmp_dir/failure.out"
failure_stderr="$tmp_dir/failure.err"
failure_output_dir="$tmp_dir/results/failure"
set +e
STAR_EXIT_CODE=37 bash "$SCRIPT" \
    --sample-id sample_failure \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$failure_output_dir" \
    --threads 3 \
    --execute \
    >"$failure_output" 2>"$failure_stderr"
failure_status=$?
set -e

[[ "$failure_status" -eq 37 ]] || fail "STAR child exit 37 was not propagated"
[[ -d "$failure_output_dir" ]] || fail "child failure removed the output directory"
[[ -z "$(find "$failure_output_dir" -mindepth 1 -print -quit)" ]] || \
    fail "fake STAR child failure left unexpected output artifacts"
[[ ! -s "$failure_stderr" ]] || fail "fake STAR child failure emitted stderr"
assert_contains "$failure_output" "Mode: execute"
assert_contains "$failure_output" "STAR command:"
assert_contains "$star_log" "$failure_output_dir/.sample_failure.step01."
[[ ! -e "$failure_output_dir/.sample_failure.step01.lock" ]] ||
    fail "failed default transaction left its Step 01 lock"
[[ -z "$(find "$failure_output_dir" -maxdepth 1 -name '.sample_failure.step01.*.staging' -print -quit)" ]] ||
    fail "failed default transaction left staging residue"

printf 'Running paired gzip dry-run check...\n'
gzip_output="$tmp_dir/gzip.out"
bash "$SCRIPT" \
    --sample-id sample_gz \
    --r1-fastq "$r1_gz" \
    --r2-fastq "$r2_gz" \
    --star-index "$star_index" \
    --output-dir "$tmp_dir/results/gzip" \
    --threads 1 \
    --gunzip-bin "$bound_gunzip" \
    >"$gzip_output"

assert_contains "$gzip_output" "--readFilesCommand"
assert_contains "$gzip_output" "$bound_gunzip"
assert_not_contains "$gzip_output" "$fake_bin/gunzip"
assert_contains "$gzip_output" "-c"

printf 'Running uncompressed unused-gunzip check...\n'
unused_gunzip_output="$tmp_dir/unused_gunzip.out"
bash "$SCRIPT" \
    --sample-id sample_unused_gunzip \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$tmp_dir/results/unused_gunzip" \
    --threads 1 \
    --gunzip-bin "$tmp_dir/missing-gunzip" \
    >"$unused_gunzip_output"
assert_contains "$unused_gunzip_output" "gunzip bin: not-required"
assert_not_contains "$unused_gunzip_output" "--readFilesCommand"

printf 'Running missing explicit gunzip failure check...\n'
missing_gunzip_output="$tmp_dir/missing_gunzip.out"
assert_fails "$missing_gunzip_output" bash "$SCRIPT" \
    --sample-id sample_missing_gunzip \
    --r1-fastq "$r1_gz" \
    --r2-fastq "$r2_gz" \
    --star-index "$star_index" \
    --output-dir "$tmp_dir/results/missing_gunzip" \
    --threads 1 \
    --gunzip-bin "$tmp_dir/missing-gunzip"
assert_contains "$missing_gunzip_output" "gunzip does not exist"

printf 'Running non-executable explicit gunzip failure check...\n'
nonexec_gunzip="$tmp_dir/nonexec-gunzip"
printf '#!/usr/bin/env bash\n' >"$nonexec_gunzip"
chmod 0644 "$nonexec_gunzip"
nonexec_gunzip_output="$tmp_dir/nonexec_gunzip.out"
assert_fails "$nonexec_gunzip_output" bash "$SCRIPT" \
    --sample-id sample_nonexec_gunzip \
    --r1-fastq "$r1_gz" \
    --r2-fastq "$r2_gz" \
    --star-index "$star_index" \
    --output-dir "$tmp_dir/results/nonexec_gunzip" \
    --threads 1 \
    --gunzip-bin "$nonexec_gunzip"
assert_contains "$nonexec_gunzip_output" "gunzip exists but is not executable"

printf 'Running mixed compression failure check...\n'
mixed_output="$tmp_dir/mixed.out"
assert_fails "$mixed_output" bash "$SCRIPT" \
    --sample-id sample_mixed \
    --r1-fastq "$r1_gz" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$tmp_dir/results/mixed" \
    --threads 1
assert_contains "$mixed_output" "Mixed FASTQ compression is not supported"

printf 'Running invalid threads failure check...\n'
threads_output="$tmp_dir/threads.out"
assert_fails "$threads_output" bash "$SCRIPT" \
    --sample-id sample_bad_threads \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$tmp_dir/results/bad_threads" \
    --threads 0
assert_contains "$threads_output" "--threads must be a positive integer"

printf 'Running missing argument failure check...\n'
missing_arg_output="$tmp_dir/missing_arg.out"
assert_fails "$missing_arg_output" bash "$SCRIPT" \
    --sample-id sample_missing \
    --r1-fastq "$r1_fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --threads 1
assert_contains "$missing_arg_output" "Missing required argument: --output-dir"

printf 'Running missing FASTQ failure check...\n'
missing_fastq_output="$tmp_dir/missing_fastq.out"
assert_fails "$missing_fastq_output" bash "$SCRIPT" \
    --sample-id sample_missing_fastq \
    --r1-fastq "$fixture_dir/missing_R1.fastq" \
    --r2-fastq "$r2_fastq" \
    --star-index "$star_index" \
    --output-dir "$tmp_dir/results/missing_fastq" \
    --threads 1
assert_contains "$missing_fastq_output" "R1 FASTQ does not exist"

printf 'All step_01 STAR alignment smoke tests passed.\n'
