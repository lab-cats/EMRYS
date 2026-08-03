#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
script="$repo_root/scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh"
job="$repo_root/jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

assert_contains() {
    local path_or_text="$1"
    local expected="$2"
    local content
    if [[ -f "$path_or_text" ]]; then
        content="$(<"$path_or_text")"
    else
        content="$path_or_text"
    fi
    [[ "$content" == *"$expected"* ]] ||
        fail "Expected content to contain: $expected"
}

assert_not_exists() {
    [[ ! -e "$1" ]] || fail "Path unexpectedly exists: $1"
}

assert_exists() {
    [[ -s "$1" ]] || fail "Expected non-empty file: $1"
}

run_expect_failure() {
    local stdout_path="$1"
    local stderr_path="$2"
    shift 2
    if "$@" >"$stdout_path" 2>"$stderr_path"; then
        fail "Command unexpectedly succeeded: $*"
    fi
}

run_expect_status() {
    local expected_status="$1"
    local stdout_path="$2"
    local stderr_path="$3"
    local observed_status
    shift 3
    if "$@" >"$stdout_path" 2>"$stderr_path"; then
        observed_status=0
    else
        observed_status=$?
    fi
    [[ "$observed_status" == "$expected_status" ]] ||
        fail "Expected exit $expected_status, got $observed_status: $*"
}

assert_text_equals() {
    local path="$1"
    local expected="$2"
    local observed
    observed="$(<"$path")"
    [[ "$observed" == "$expected" ]] ||
        fail "Unexpected content in $path: $observed"
}

assert_no_owned_step07_paths() {
    local directory="$1"
    local pattern="$2"
    if find "$directory" -maxdepth 1 -name "$pattern" -print -quit |
        grep -q .; then
        fail "Invocation-owned Step 07 path remains in: $directory"
    fi
}

fake_bcftools="$test_root/fake-bcftools"
apply_fake_path="$fake_bcftools"

cat >"$fake_bcftools" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${FAKE_BCFTOOLS_LOG:-}" ]]; then
    printf '%q ' "$@" >>"$FAKE_BCFTOOLS_LOG"
    printf '\n' >>"$FAKE_BCFTOOLS_LOG"
fi

command_name="${1:-}"
shift || true

case "$command_name" in
    --version)
        printf 'bcftools 1.21-fake\n'
        ;;
    mpileup)
        orientation="unknown"
        for argument in "$@"; do
            case "$argument" in
                *.FWD_like.bam) orientation="FWD_like" ;;
                *.REV_like.bam) orientation="REV_like" ;;
            esac
        done
        if [[ "${FAKE_BCFTOOLS_FAIL_STAGE:-}" == "mpileup" ||
              "${FAKE_BCFTOOLS_FAIL_STAGE:-}" == "mpileup_${orientation}" ]]; then
            exit 41
        fi
        if [[ -n "${FAKE_BCFTOOLS_MUTATE_PATH:-}" &&
              "${FAKE_BCFTOOLS_MUTATE_ORIENTATION:-FWD_like}" == "$orientation" ]]; then
            printf '# controlled mutation\n' >>"$FAKE_BCFTOOLS_MUTATE_PATH"
        fi
        if [[ -n "${FAKE_BCFTOOLS_BARRIER_READY:-}" &&
              "$orientation" == "FWD_like" ]]; then
            printf 'ready\n' >"$FAKE_BCFTOOLS_BARRIER_READY"
            while [[ ! -e "${FAKE_BCFTOOLS_BARRIER_RELEASE:-}" ]]; do
                sleep 0.02
            done
        fi
        printf 'ORIENTATION=%s\n' "$orientation"
        ;;
    filter)
        output=""
        while [[ $# -gt 0 ]]; do
            case "$1" in
                -o)
                    output="$2"
                    shift 2
                    ;;
                *)
                    shift
                    ;;
            esac
        done
        [[ -n "$output" ]] || exit 42
        stream="$(cat)"
        orientation="${stream#ORIENTATION=}"
        orientation="${orientation%%$'\n'*}"
        if [[ "${FAKE_BCFTOOLS_FAIL_STAGE:-}" == "filter" ||
              "${FAKE_BCFTOOLS_FAIL_STAGE:-}" == "filter_${orientation}" ]]; then
            exit 43
        fi

        IFS=',' read -r -a samples <<<"${FAKE_BCFTOOLS_SAMPLES:-sample_A,sample_B}"
        {
            printf '##fileformat=VCFv4.2\n'
            printf '##INFO=<ID=AD,Number=R,Type=Integer,Description="Allele depth">\n'
            printf '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Depth">\n'
            printf '##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allele depth">\n'
            printf '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT'
            for sample in "${samples[@]}"; do
                printf '\t%s' "$sample"
            done
            printf '\n'
            if [[ "${FAKE_HEADER_ONLY:-0}" != "1" ]]; then
                printf '1\t10\t.\tA\tG\t60\tPASS\tAD=20,4\tDP:AD'
                for sample in "${samples[@]}"; do
                    printf '\t12:10,2'
                done
                printf '\n'
            fi
        } >"$output"
        ;;
    view)
        mode="${1:-}"
        path="${2:-}"
        [[ -s "$path" ]] || exit 44
        if [[ -n "${FAKE_OBSERVE_PUBLISHED_FWD:-}" &&
              "$mode" == "-h" && "$path" == "$FAKE_OBSERVE_PUBLISHED_FWD" ]]; then
            [[ -s "${FAKE_OBSERVE_PUBLISHED_REV:-}" ]] || exit 50
            [[ -s "${FAKE_OBSERVE_PUBLISHED_RECEIPT:-}" ]] || exit 51
            printf 'fwd-rev-receipt-visible-before-commit\n' \
                >"${FAKE_PUBLICATION_OBSERVATION:-/dev/null}"
        fi
        if [[ "${FAKE_FAIL_FINAL_VALIDATION:-0}" == "1" &&
              "$path" != *".tmp.vcf" ]]; then
            exit 45
        fi
        case "$mode" in
            -h) awk '/^#/' "$path" ;;
            -H) awk '!/^#/' "$path" ;;
            *) exit 46 ;;
        esac
        ;;
    query)
        [[ "${1:-}" == "-l" ]] || exit 47
        path="${2:-}"
        [[ -s "$path" ]] || exit 48
        awk -F '\t' '
            /^#CHROM/ {
                for (i = 10; i <= NF; i++) print $i
                found = 1
            }
            END { if (!found) exit 1 }
        ' "$path"
        ;;
    *)
        exit 49
        ;;
esac
FAKE
chmod +x "$fake_bcftools"

fake_bin="$test_root/fake-bin"
mkdir -p "$fake_bin"
cat >"$fake_bin/module" <<'FAKE_MODULE'
#!/usr/bin/env bash
exit 0
FAKE_MODULE
chmod +x "$fake_bin/module"

transaction_bin="$test_root/transaction-bin"
real_mv="$(command -v mv)"
mkdir -p "$transaction_bin"
cat >"$transaction_bin/mv" <<'FAKE_MV'
#!/usr/bin/env bash
set -euo pipefail

source_path="${1:-}"
destination_path="${2:-}"
[[ -n "$source_path" && -n "$destination_path" ]] || exit 64
if [[ -n "${FAKE_MV_LOG:-}" ]]; then
    printf '%s\t%s\n' "$source_path" "$destination_path" >>"$FAKE_MV_LOG"
fi
if [[ "${FAKE_MV_FAIL_RECEIPT_PUBLICATION:-0}" == "1" &&
      "$source_path" == *.outputs.tmp.tsv ]]; then
    exit 67
fi
if [[ "${FAKE_MV_SEND_TERM_AFTER_RECEIPT:-0}" == "1" &&
      "$source_path" == *.outputs.tmp.tsv ]]; then
    "$REAL_MV" "$@"
    kill -TERM "$PPID"
    exit 0
fi
if [[ "${FAKE_MV_FAIL_FWD_RESTORE:-0}" == "1" &&
      "$source_path" == *.previous.FWD_like.vcf ]]; then
    exit 68
fi
exec "$REAL_MV" "$@"
FAKE_MV
chmod +x "$transaction_bin/mv"

fixture="$test_root/fixture"
mkdir -p "$fixture/orientation/sample_A" "$fixture/orientation/sample_B"
printf 'sample_id\tcondition\nsample_A\tEV\nsample_B\tPUM1\n' >"$fixture/samples.tsv"
printf 'partition_id\tselector_type\tselector_value\n1\tregion\t1\n' >"$fixture/partitions.tsv"
printf '>1\nACGT\n' >"$fixture/reference.fa"
printf '1\t4\t3\t4\t5\n' >"$fixture/reference.fa.fai"
for sample in sample_A sample_B; do
    for orientation in FWD_like REV_like; do
        bam="$fixture/orientation/$sample/$sample.$orientation.bam"
        printf 'fake bam\n' >"$bam"
        printf 'fake bai\n' >"$bam.bai"
    done
done

common_args=(
    --cohort-id cohort_A
    --sample-manifest "$fixture/samples.tsv"
    --partition-manifest "$fixture/partitions.tsv"
    --partition-id 1
    --orientation-root "$fixture/orientation"
    --reference-fasta "$fixture/reference.fa"
    --output-root "$fixture/output"
    --bcftools-bin "$fake_bcftools"
)

help_output="$(bash "$script" --help)"
assert_contains "$help_output" "--sample-manifest"
assert_contains "$help_output" "selector_type=regions_file"
assert_contains "$help_output" "mechanical read-orientation labels"

run_expect_failure "$test_root/missing.out" "$test_root/missing.err" \
    bash "$script"
assert_contains "$test_root/missing.err" "Missing required argument: --cohort-id"

FAKE_BCFTOOLS_LOG="$test_root/dry-run.log" \
    bash "$script" "${common_args[@]}" >"$test_root/dry-run.out"
assert_contains "$test_root/dry-run.out" "Mode: dry-run"
assert_contains "$test_root/dry-run.out" "Sample count: 2"
assert_contains "$test_root/dry-run.out" "FWD_like pipeline:"
assert_contains "$test_root/dry-run.out" "FORMAT/DP"
assert_contains "$test_root/dry-run.out" "INFO/ADR"
assert_contains "$test_root/dry-run.out" "Filter expression: INFO/AD[1-]>2 & MAX(FORMAT/DP)>20"
assert_contains "$test_root/dry-run.out" "Dry-run complete; no directories or files were created."
assert_not_exists "$fixture/output"
assert_not_exists "$test_root/dry-run.log"

missing_bcftools="$test_root/does-not-exist/bcftools"
run_expect_status 1 "$test_root/missing-bcftools.out" \
    "$test_root/missing-bcftools.err" \
    bash "$script" "${common_args[@]}" --bcftools-bin "$missing_bcftools" --execute
assert_text_equals "$test_root/missing-bcftools.err" \
    "ERROR: bcftools does not exist: $missing_bcftools"
assert_not_exists "$fixture/output"

nonexecutable_bcftools="$test_root/nonexecutable-bcftools"
printf 'not executable\n' >"$nonexecutable_bcftools"
chmod 0644 "$nonexecutable_bcftools"
run_expect_status 1 "$test_root/nonexecutable-bcftools.out" \
    "$test_root/nonexecutable-bcftools.err" \
    bash "$script" "${common_args[@]}" \
    --bcftools-bin "$nonexecutable_bcftools" --execute
assert_text_equals "$test_root/nonexecutable-bcftools.err" \
    "ERROR: bcftools exists but is not executable: $nonexecutable_bcftools"
assert_not_exists "$fixture/output"

path_bcftools_dir="$test_root/path-bcftools"
arbitrary_cwd="$test_root/arbitrary-cwd"
arbitrary_fixture="$test_root/arbitrary-fixture"
mkdir -p "$path_bcftools_dir" "$arbitrary_cwd"
cp "$fake_bcftools" "$path_bcftools_dir/bcftools-by-name"
chmod +x "$path_bcftools_dir/bcftools-by-name"
cp -R "$fixture" "$arbitrary_fixture"
rm -rf "$arbitrary_fixture/output"
arbitrary_args=(
    --cohort-id cohort_path
    --sample-manifest "$arbitrary_fixture/samples.tsv"
    --partition-manifest "$arbitrary_fixture/partitions.tsv"
    --partition-id 1
    --orientation-root "$arbitrary_fixture/orientation"
    --reference-fasta "$arbitrary_fixture/reference.fa"
    --output-root "$arbitrary_fixture/output"
    --bcftools-bin bcftools-by-name
)
(
    cd "$arbitrary_cwd"
    PATH="$path_bcftools_dir:$PATH" bash "$script" "${arbitrary_args[@]}"
) >"$test_root/arbitrary-cwd.out"
assert_contains "$test_root/arbitrary-cwd.out" \
    "bcftools: $path_bcftools_dir/bcftools-by-name"
assert_not_exists "$arbitrary_fixture/output"
if find "$arbitrary_cwd" -mindepth 1 -print -quit | grep -q .; then
    fail "Arbitrary-CWD dry-run left invocation-CWD residue"
fi

FAKE_BCFTOOLS_LOG="$test_root/execute.log" \
FAKE_BCFTOOLS_SAMPLES="sample_A,sample_B" \
    bash "$script" "${common_args[@]}" --execute >"$test_root/execute.out"
output_dir="$fixture/output/cohort_A/1"
fwd_vcf="$output_dir/cohort_A.1.FWD_like.mpileup.vcf"
rev_vcf="$output_dir/cohort_A.1.REV_like.mpileup.vcf"
receipt="$output_dir/cohort_A.1.step07_outputs.tsv"
assert_exists "$fwd_vcf"
assert_exists "$rev_vcf"
assert_exists "$receipt"
assert_contains "$receipt" $'cohort_id\tpartition_id\tselector_type\tselector_value\torientation'
assert_contains "$receipt" $'cohort_A\t1\tregion\t1\tFWD_like'
assert_contains "$receipt" $'cohort_A\t1\tregion\t1\tREV_like'
[[ "$(awk 'END { print NR }' "$receipt")" == "3" ]] ||
    fail "Receipt should contain a header and two rows"
[[ "$(awk -F '\t' 'NR > 1 { total += $10 } END { print total }' "$receipt")" == "2" ]] ||
    fail "Expected one VCF record per orientation"
assert_contains "$test_root/execute.log" "mpileup"
assert_contains "$test_root/execute.log" "filter"
assert_contains "$test_root/execute.log" "query"
[[ "$(grep -o -- 'mpileup -Ou' "$test_root/execute.log" | wc -l | tr -d ' ')" == "2" ]] ||
    fail "Expected exactly two cohort mpileup invocations"
[[ "$(grep -o -- 'filter -i' "$test_root/execute.log" | wc -l | tr -d ' ')" == "2" ]] ||
    fail "Expected exactly two filter invocations"
[[ "$(grep -o -- ' -Ou ' "$test_root/execute.log" | wc -l | tr -d ' ')" == "2" ]] ||
    fail "Both mpileup invocations must stream uncompressed BCF"
[[ "$(grep -o -- ' -I ' "$test_root/execute.log" | wc -l | tr -d ' ')" == "2" ]] ||
    fail "Both mpileup invocations must skip indels"
[[ "$(grep -o -- ' -d 10000000 ' "$test_root/execute.log" | wc -l | tr -d ' ')" == "2" ]] ||
    fail "Both mpileup invocations must preserve the legacy maximum depth"
[[ "$(grep -o -- ' -Ov ' "$test_root/execute.log" | wc -l | tr -d ' ')" == "2" ]] ||
    fail "Both filters must emit plain VCF"
if grep -q 'call ' "$test_root/execute.log"; then
    fail "Step 07 must not invoke bcftools call"
fi
execute_log_content="$(<"$test_root/execute.log")"
assert_contains "$execute_log_content" \
    'FORMAT/DP\,FORMAT/AD\,FORMAT/ADF\,FORMAT/ADR\,FORMAT/SP\,INFO/AD\,INFO/ADF\,INFO/ADR'
assert_contains "$execute_log_content" \
    'INFO/AD\[1-\]\>2\ \&\ MAX\(FORMAT/DP\)\>20'
[[ "$execute_log_content" == *"sample_A.FWD_like.bam"*"sample_B.FWD_like.bam"* ]] ||
    fail "FWD_like BAMs must follow manifest sample order"
[[ "$execute_log_content" == *"sample_A.REV_like.bam"*"sample_B.REV_like.bam"* ]] ||
    fail "REV_like BAMs must follow manifest sample order"
awk -F '\t' '
    NR > 1 {
        if (length($7) != 64 || $7 !~ /^[0-9a-f]+$/) exit 1
        if (length($8) != 64 || $8 !~ /^[0-9a-f]+$/) exit 1
        if ($9 != 2) exit 1
    }
' "$receipt" || fail "Receipt hashes or sample counts are invalid"
assert_not_exists "$output_dir/.cohort_A.1.step07.lock"

header_fixture="$test_root/header-only"
cp -R "$fixture" "$header_fixture"
rm -rf "$header_fixture/output"
header_args=(
    --cohort-id cohort_empty
    --sample-manifest "$header_fixture/samples.tsv"
    --partition-manifest "$header_fixture/partitions.tsv"
    --partition-id 1
    --orientation-root "$header_fixture/orientation"
    --reference-fasta "$header_fixture/reference.fa"
    --output-root "$header_fixture/output"
    --bcftools-bin "$fake_bcftools"
)
FAKE_HEADER_ONLY=1 FAKE_BCFTOOLS_SAMPLES="sample_A,sample_B" \
    bash "$script" "${header_args[@]}" --execute >/dev/null
header_receipt="$header_fixture/output/cohort_empty/1/cohort_empty.1.step07_outputs.tsv"
[[ "$(awk -F '\t' 'NR > 1 { total += $10 } END { print total + 0 }' "$header_receipt")" == "0" ]] ||
    fail "Header-only VCF receipt should record zero records"

regions_fixture="$test_root/regions"
cp -R "$fixture" "$regions_fixture"
rm -rf "$regions_fixture/output"
printf '1\t0\t4\n' >"$regions_fixture/target.bed"
printf 'partition_id\tselector_type\tselector_value\ntarget\tregions_file\ttarget.bed\n' \
    >"$regions_fixture/partitions.tsv"
regions_args=(
    --cohort-id cohort_regions
    --sample-manifest "$regions_fixture/samples.tsv"
    --partition-manifest "$regions_fixture/partitions.tsv"
    --partition-id target
    --orientation-root "$regions_fixture/orientation"
    --reference-fasta "$regions_fixture/reference.fa"
    --output-root "$regions_fixture/output"
    --bcftools-bin "$fake_bcftools"
)
bash "$script" "${regions_args[@]}" >"$test_root/regions.out"
assert_contains "$test_root/regions.out" "target.bed"
assert_contains "$test_root/regions.out" "-R"
assert_contains "$test_root/regions.out" "$regions_fixture/target.bed"
assert_not_exists "$regions_fixture/output"
FAKE_BCFTOOLS_LOG="$test_root/regions-execute.log" \
FAKE_BCFTOOLS_SAMPLES="sample_A,sample_B" \
    bash "$script" "${regions_args[@]}" --execute >/dev/null
regions_receipt="$regions_fixture/output/cohort_regions/target/cohort_regions.target.step07_outputs.tsv"
[[ "$(awk -F '\t' 'NR == 2 { print $4 }' "$regions_receipt")" == "target.bed" ]] ||
    fail "Receipt must preserve the manifest-declared regions_file value"
assert_contains "$test_root/regions-execute.log" "$regions_fixture/target.bed"

compressed_regions_fixture="$test_root/compressed-regions"
cp -R "$fixture" "$compressed_regions_fixture"
rm -rf "$compressed_regions_fixture/output"
printf '1\t0\t4\n' >"$compressed_regions_fixture/target.bed"
gzip -c "$compressed_regions_fixture/target.bed" \
    >"$compressed_regions_fixture/target.bed.gz"
printf 'partition_id\tselector_type\tselector_value\ncompressed\tregions_file\ttarget.bed.gz\n' \
    >"$compressed_regions_fixture/partitions.tsv"
compressed_regions_args=(
    --cohort-id cohort_compressed
    --sample-manifest "$compressed_regions_fixture/samples.tsv"
    --partition-manifest "$compressed_regions_fixture/partitions.tsv"
    --partition-id compressed
    --orientation-root "$compressed_regions_fixture/orientation"
    --reference-fasta "$compressed_regions_fixture/reference.fa"
    --output-root "$compressed_regions_fixture/output"
    --bcftools-bin "$fake_bcftools"
)
FAKE_BCFTOOLS_LOG="$test_root/compressed-regions.log" \
FAKE_BCFTOOLS_SAMPLES="sample_A,sample_B" \
    bash "$script" "${compressed_regions_args[@]}" --execute >/dev/null
compressed_regions_receipt="$compressed_regions_fixture/output/cohort_compressed/compressed/cohort_compressed.compressed.step07_outputs.tsv"
assert_exists "$compressed_regions_receipt"
[[ "$(awk -F '\t' 'NR == 2 { print $4 }' "$compressed_regions_receipt")" == \
    "target.bed.gz" ]] ||
    fail "Receipt must preserve the compressed regions_file declaration"
assert_contains "$test_root/compressed-regions.log" \
    "$compressed_regions_fixture/target.bed.gz"

invalid_regions_fixture="$test_root/invalid-regions"
cp -R "$regions_fixture" "$invalid_regions_fixture"
rm -rf "$invalid_regions_fixture/output"
printf '1\t0\t5\n' >"$invalid_regions_fixture/target.bed"
run_expect_failure "$test_root/invalid-regions.out" "$test_root/invalid-regions.err" \
    bash "$script" \
    --cohort-id bad_regions \
    --sample-manifest "$invalid_regions_fixture/samples.tsv" \
    --partition-manifest "$invalid_regions_fixture/partitions.tsv" \
    --partition-id target \
    --orientation-root "$invalid_regions_fixture/orientation" \
    --reference-fasta "$invalid_regions_fixture/reference.fa" \
    --output-root "$invalid_regions_fixture/output" \
    --bcftools-bin "$fake_bcftools"
assert_contains "$test_root/invalid-regions.err" "invalid BED interval"
assert_contains "$test_root/invalid-regions.err" "Regions file validation failed"
assert_not_exists "$invalid_regions_fixture/output"

bad_sample_fixture="$test_root/bad-sample"
cp -R "$fixture" "$bad_sample_fixture"
rm -rf "$bad_sample_fixture/output"
printf 'sample_id\tcondition\nsample_A\tEV\nsample_A\tPUM1\n' >"$bad_sample_fixture/samples.tsv"
run_expect_failure "$test_root/bad-sample.out" "$test_root/bad-sample.err" \
    bash "$script" \
    --cohort-id bad \
    --sample-manifest "$bad_sample_fixture/samples.tsv" \
    --partition-manifest "$bad_sample_fixture/partitions.tsv" \
    --partition-id 1 \
    --orientation-root "$bad_sample_fixture/orientation" \
    --reference-fasta "$bad_sample_fixture/reference.fa" \
    --output-root "$bad_sample_fixture/output" \
    --bcftools-bin "$fake_bcftools"
assert_contains "$test_root/bad-sample.err" "duplicate sample_id"
assert_not_exists "$bad_sample_fixture/output"

bad_partition_fixture="$test_root/bad-partition"
cp -R "$fixture" "$bad_partition_fixture"
rm -rf "$bad_partition_fixture/output"
printf 'partition_id\tselector_type\tselector_value\n1\tregion\t1\n1\tregion\t2\n' \
    >"$bad_partition_fixture/partitions.tsv"
run_expect_failure "$test_root/bad-partition.out" "$test_root/bad-partition.err" \
    bash "$script" \
    --cohort-id bad \
    --sample-manifest "$bad_partition_fixture/samples.tsv" \
    --partition-manifest "$bad_partition_fixture/partitions.tsv" \
    --partition-id 1 \
    --orientation-root "$bad_partition_fixture/orientation" \
    --reference-fasta "$bad_partition_fixture/reference.fa" \
    --output-root "$bad_partition_fixture/output" \
    --bcftools-bin "$fake_bcftools"
assert_contains "$test_root/bad-partition.err" "duplicate partition_id"

missing_partition_fixture="$test_root/missing-partition"
cp -R "$fixture" "$missing_partition_fixture"
rm -rf "$missing_partition_fixture/output"
run_expect_failure "$test_root/missing-partition.out" "$test_root/missing-partition.err" \
    bash "$script" \
    --cohort-id bad \
    --sample-manifest "$missing_partition_fixture/samples.tsv" \
    --partition-manifest "$missing_partition_fixture/partitions.tsv" \
    --partition-id absent \
    --orientation-root "$missing_partition_fixture/orientation" \
    --reference-fasta "$missing_partition_fixture/reference.fa" \
    --output-root "$missing_partition_fixture/output" \
    --bcftools-bin "$fake_bcftools"
assert_contains "$test_root/missing-partition.err" "partition_id absent was not found exactly once"
assert_not_exists "$missing_partition_fixture/output"

missing_fai_fixture="$test_root/missing-fai"
cp -R "$fixture" "$missing_fai_fixture"
rm -rf "$missing_fai_fixture/output"
rm "$missing_fai_fixture/reference.fa.fai"
run_expect_failure "$test_root/missing-fai.out" "$test_root/missing-fai.err" \
    bash "$script" \
    --cohort-id bad \
    --sample-manifest "$missing_fai_fixture/samples.tsv" \
    --partition-manifest "$missing_fai_fixture/partitions.tsv" \
    --partition-id 1 \
    --orientation-root "$missing_fai_fixture/orientation" \
    --reference-fasta "$missing_fai_fixture/reference.fa" \
    --output-root "$missing_fai_fixture/output" \
    --bcftools-bin "$fake_bcftools"
assert_contains "$test_root/missing-fai.err" "Reference FASTA index does not exist or is empty"

bad_fai_fixture="$test_root/bad-fai"
cp -R "$fixture" "$bad_fai_fixture"
rm -rf "$bad_fai_fixture/output"
printf '1\t4\t3\t4\t5\n1\t4\t3\t4\t5\n' >"$bad_fai_fixture/reference.fa.fai"
run_expect_failure "$test_root/bad-fai.out" "$test_root/bad-fai.err" \
    bash "$script" \
    --cohort-id bad \
    --sample-manifest "$bad_fai_fixture/samples.tsv" \
    --partition-manifest "$bad_fai_fixture/partitions.tsv" \
    --partition-id 1 \
    --orientation-root "$bad_fai_fixture/orientation" \
    --reference-fasta "$bad_fai_fixture/reference.fa" \
    --output-root "$bad_fai_fixture/output" \
    --bcftools-bin "$fake_bcftools"
assert_contains "$test_root/bad-fai.err" "duplicate FASTA index contig"
assert_contains "$test_root/bad-fai.err" "Reference FASTA index validation failed"

bad_selector_fixture="$test_root/bad-selector"
cp -R "$fixture" "$bad_selector_fixture"
rm -rf "$bad_selector_fixture/output"
printf 'partition_id\tselector_type\tselector_value\nbad\tregion\tchr1\n' \
    >"$bad_selector_fixture/partitions.tsv"
run_expect_failure "$test_root/bad-selector.out" "$test_root/bad-selector.err" \
    bash "$script" \
    --cohort-id bad \
    --sample-manifest "$bad_selector_fixture/samples.tsv" \
    --partition-manifest "$bad_selector_fixture/partitions.tsv" \
    --partition-id bad \
    --orientation-root "$bad_selector_fixture/orientation" \
    --reference-fasta "$bad_selector_fixture/reference.fa" \
    --output-root "$bad_selector_fixture/output" \
    --bcftools-bin "$fake_bcftools"
assert_contains "$test_root/bad-selector.err" "Region selector contig is absent"
assert_not_exists "$bad_selector_fixture/output"

missing_bai_fixture="$test_root/missing-bai"
cp -R "$fixture" "$missing_bai_fixture"
rm -rf "$missing_bai_fixture/output"
rm "$missing_bai_fixture/orientation/sample_B/sample_B.REV_like.bam.bai"
run_expect_failure "$test_root/missing-bai.out" "$test_root/missing-bai.err" \
    bash "$script" \
    --cohort-id bad \
    --sample-manifest "$missing_bai_fixture/samples.tsv" \
    --partition-manifest "$missing_bai_fixture/partitions.tsv" \
    --partition-id 1 \
    --orientation-root "$missing_bai_fixture/orientation" \
    --reference-fasta "$missing_bai_fixture/reference.fa" \
    --output-root "$missing_bai_fixture/output" \
    --bcftools-bin "$fake_bcftools"
assert_contains "$test_root/missing-bai.err" "REV_like BAI for sample_B does not exist or is empty"
assert_not_exists "$missing_bai_fixture/output"

for failure_stage in \
    mpileup_FWD_like filter_FWD_like mpileup_REV_like filter_REV_like
do
    failure_fixture="$test_root/failure-$failure_stage"
    cp -R "$fixture" "$failure_fixture"
    rm -rf "$failure_fixture/output"
    failure_output="$failure_fixture/output/cohort_failure/1"
    mkdir -p "$failure_output"
    unrelated_path="$failure_output/unrelated.txt"
    printf 'preserve unrelated bytes\n' >"$unrelated_path"
    failure_args=(
        --cohort-id cohort_failure
        --sample-manifest "$failure_fixture/samples.tsv"
        --partition-manifest "$failure_fixture/partitions.tsv"
        --partition-id 1
        --orientation-root "$failure_fixture/orientation"
        --reference-fasta "$failure_fixture/reference.fa"
        --output-root "$failure_fixture/output"
        --bcftools-bin "$fake_bcftools"
    )
    case "$failure_stage" in
        *_FWD_like) expected_failure_orientation="FWD_like" ;;
        *_REV_like) expected_failure_orientation="REV_like" ;;
        *) fail "Unhandled fake failure stage: $failure_stage" ;;
    esac
    run_expect_status 1 "$test_root/$failure_stage.out" \
        "$test_root/$failure_stage.err" \
        env FAKE_BCFTOOLS_FAIL_STAGE="$failure_stage" \
        FAKE_BCFTOOLS_SAMPLES=sample_A,sample_B \
        bash "$script" "${failure_args[@]}" --execute
    assert_text_equals "$test_root/$failure_stage.err" \
        "ERROR: $expected_failure_orientation bcftools mpileup/filter pipeline failed."
    assert_not_exists "$failure_output/cohort_failure.1.FWD_like.mpileup.vcf"
    assert_not_exists "$failure_output/cohort_failure.1.REV_like.mpileup.vcf"
    assert_not_exists "$failure_output/cohort_failure.1.step07_outputs.tsv"
    assert_not_exists "$failure_output/.cohort_failure.1.step07.lock"
    assert_text_equals "$unrelated_path" "preserve unrelated bytes"
    assert_no_owned_step07_paths "$failure_output" \
        '.cohort_failure.1.step07.*'
done

for manifest_kind in sample partition; do
    mutation_fixture="$test_root/mutation-$manifest_kind"
    cp -R "$fixture" "$mutation_fixture"
    rm -rf "$mutation_fixture/output"
    mutation_output="$mutation_fixture/output/cohort_mutation/1"
    mkdir -p "$mutation_output"
    mutation_unrelated="$mutation_output/unrelated.txt"
    printf 'preserve mutation neighbor\n' >"$mutation_unrelated"
    case "$manifest_kind" in
        sample)
            mutation_path="$mutation_fixture/samples.tsv"
            expected_mutation_label="Sample manifest"
            ;;
        partition)
            mutation_path="$mutation_fixture/partitions.tsv"
            expected_mutation_label="Partition manifest"
            ;;
        *) fail "Unhandled manifest mutation kind: $manifest_kind" ;;
    esac
    mutation_args=(
        --cohort-id cohort_mutation
        --sample-manifest "$mutation_fixture/samples.tsv"
        --partition-manifest "$mutation_fixture/partitions.tsv"
        --partition-id 1
        --orientation-root "$mutation_fixture/orientation"
        --reference-fasta "$mutation_fixture/reference.fa"
        --output-root "$mutation_fixture/output"
        --bcftools-bin "$fake_bcftools"
    )
    run_expect_status 1 "$test_root/mutation-$manifest_kind.out" \
        "$test_root/mutation-$manifest_kind.err" \
        env FAKE_BCFTOOLS_MUTATE_PATH="$mutation_path" \
        FAKE_BCFTOOLS_SAMPLES=sample_A,sample_B \
        bash "$script" "${mutation_args[@]}" --execute
    assert_text_equals "$test_root/mutation-$manifest_kind.err" \
        "ERROR: $expected_mutation_label changed during Step 07: $mutation_path"
    assert_not_exists "$mutation_output/cohort_mutation.1.FWD_like.mpileup.vcf"
    assert_not_exists "$mutation_output/cohort_mutation.1.REV_like.mpileup.vcf"
    assert_not_exists "$mutation_output/cohort_mutation.1.step07_outputs.tsv"
    assert_not_exists "$mutation_output/.cohort_mutation.1.step07.lock"
    assert_text_equals "$mutation_unrelated" "preserve mutation neighbor"
    assert_no_owned_step07_paths "$mutation_output" \
        '.cohort_mutation.1.step07.*'
done

for stability_input in bam bai fasta fai regions_file; do
    stability_fixture="$test_root/stability-$stability_input"
    cp -R "$fixture" "$stability_fixture"
    rm -rf "$stability_fixture/output"
    printf '1\t0\t4\n' >"$stability_fixture/target.bed"
    printf 'partition_id\tselector_type\tselector_value\ntarget\tregions_file\ttarget.bed\n' \
        >"$stability_fixture/partitions.tsv"
    case "$stability_input" in
        bam)
            stability_mutation_path="$stability_fixture/orientation/sample_A/sample_A.FWD_like.bam"
            ;;
        bai)
            stability_mutation_path="$stability_fixture/orientation/sample_A/sample_A.FWD_like.bam.bai"
            ;;
        fasta) stability_mutation_path="$stability_fixture/reference.fa" ;;
        fai) stability_mutation_path="$stability_fixture/reference.fa.fai" ;;
        regions_file) stability_mutation_path="$stability_fixture/target.bed" ;;
        *) fail "Unhandled stability input: $stability_input" ;;
    esac
    stability_args=(
        --cohort-id cohort_stability
        --sample-manifest "$stability_fixture/samples.tsv"
        --partition-manifest "$stability_fixture/partitions.tsv"
        --partition-id target
        --orientation-root "$stability_fixture/orientation"
        --reference-fasta "$stability_fixture/reference.fa"
        --output-root "$stability_fixture/output"
        --bcftools-bin "$fake_bcftools"
    )
    FAKE_BCFTOOLS_MUTATE_PATH="$stability_mutation_path" \
    FAKE_BCFTOOLS_SAMPLES="sample_A,sample_B" \
        bash "$script" "${stability_args[@]}" --execute >/dev/null
    stability_output="$stability_fixture/output/cohort_stability/target"
    stability_receipt="$stability_output/cohort_stability.target.step07_outputs.tsv"
    assert_exists "$stability_output/cohort_stability.target.FWD_like.mpileup.vcf"
    assert_exists "$stability_output/cohort_stability.target.REV_like.mpileup.vcf"
    assert_exists "$stability_receipt"
    assert_contains "$stability_mutation_path" "# controlled mutation"
    assert_not_exists "$stability_output/.cohort_stability.target.step07.lock"
done

IFS= read -r stability_receipt_header <"$stability_receipt"
expected_stability_receipt_header=$'cohort_id\tpartition_id\tselector_type\tselector_value\torientation\tvcf_path\tsample_manifest_sha256\tpartition_manifest_sha256\tsample_count\tvcf_record_count'
[[ "$stability_receipt_header" == "$expected_stability_receipt_header" ]] ||
    fail "Step 07 receipt provenance fields changed unexpectedly"
for absent_identity in \
    run_token bam_sha256 bai_sha256 reference_sha256 regions_sha256 \
    bcftools maximum_depth filter_expression vcf_sha256
do
    [[ "$stability_receipt_header" != *"$absent_identity"* ]] ||
        fail "Step 07 receipt unexpectedly binds $absent_identity"
done
if grep -Fq "$fake_bcftools" "$stability_receipt" ||
   grep -Fq "$stability_fixture/reference.fa" "$stability_receipt" ||
   grep -Fq "$stability_fixture/orientation" "$stability_receipt"; then
    fail "Step 07 receipt unexpectedly records tool, reference, or BAM identity"
fi

mismatch_fixture="$test_root/mismatch"
cp -R "$fixture" "$mismatch_fixture"
rm -rf "$mismatch_fixture/output"
mismatch_args=(
    --cohort-id cohort_mismatch
    --sample-manifest "$mismatch_fixture/samples.tsv"
    --partition-manifest "$mismatch_fixture/partitions.tsv"
    --partition-id 1
    --orientation-root "$mismatch_fixture/orientation"
    --reference-fasta "$mismatch_fixture/reference.fa"
    --output-root "$mismatch_fixture/output"
    --bcftools-bin "$fake_bcftools"
)
run_expect_failure "$test_root/mismatch.out" "$test_root/mismatch.err" \
    env FAKE_BCFTOOLS_SAMPLES=sample_B,sample_A \
    bash "$script" "${mismatch_args[@]}" --execute
assert_contains "$test_root/mismatch.err" "sample order does not match"
assert_not_exists "$mismatch_fixture/output/cohort_mismatch/1/cohort_mismatch.1.FWD_like.mpileup.vcf"

stale_fixture="$test_root/stale"
cp -R "$fixture" "$stale_fixture"
rm -rf "$stale_fixture/output"
stale_dir="$stale_fixture/output/cohort_stale/1"
stale_path="$stale_dir/.cohort_stale.1.step07.unit07.FWD_like.tmp.vcf"
mkdir -p "$stale_dir"
printf 'foreign scratch\n' >"$stale_path"
run_expect_failure "$test_root/stale.out" "$test_root/stale.err" \
    env SLURM_JOB_ID=unit07 FAKE_BCFTOOLS_SAMPLES=sample_A,sample_B \
    bash "$script" \
    --cohort-id cohort_stale \
    --sample-manifest "$stale_fixture/samples.tsv" \
    --partition-manifest "$stale_fixture/partitions.tsv" \
    --partition-id 1 \
    --orientation-root "$stale_fixture/orientation" \
    --reference-fasta "$stale_fixture/reference.fa" \
    --output-root "$stale_fixture/output" \
    --bcftools-bin "$fake_bcftools" \
    --execute
assert_contains "$test_root/stale.err" "Refusing to reuse an existing Step 07 scratch path"
assert_contains "$stale_path" "foreign scratch"

lock_fixture="$test_root/lock"
cp -R "$fixture" "$lock_fixture"
rm -rf "$lock_fixture/output"
lock_dir="$lock_fixture/output/cohort_lock/1/.cohort_lock.1.step07.lock"
mkdir -p "$lock_dir"
printf 'foreign\n' >"$lock_dir/owner"
run_expect_failure "$test_root/lock.out" "$test_root/lock.err" \
    env FAKE_BCFTOOLS_SAMPLES=sample_A,sample_B \
    bash "$script" \
    --cohort-id cohort_lock \
    --sample-manifest "$lock_fixture/samples.tsv" \
    --partition-manifest "$lock_fixture/partitions.tsv" \
    --partition-id 1 \
    --orientation-root "$lock_fixture/orientation" \
    --reference-fasta "$lock_fixture/reference.fa" \
    --output-root "$lock_fixture/output" \
    --bcftools-bin "$fake_bcftools" \
    --execute
assert_contains "$test_root/lock.err" "lock already exists"
assert_exists "$lock_dir/owner"

transaction_fixture="$test_root/transaction-order"
cp -R "$fixture" "$transaction_fixture"
rm -rf "$transaction_fixture/output"
transaction_args=(
    --cohort-id cohort_transaction
    --sample-manifest "$transaction_fixture/samples.tsv"
    --partition-manifest "$transaction_fixture/partitions.tsv"
    --partition-id 1
    --orientation-root "$transaction_fixture/orientation"
    --reference-fasta "$transaction_fixture/reference.fa"
    --output-root "$transaction_fixture/output"
    --bcftools-bin "$fake_bcftools"
)
transaction_dir="$transaction_fixture/output/cohort_transaction/1"
transaction_fwd="$transaction_dir/cohort_transaction.1.FWD_like.mpileup.vcf"
transaction_rev="$transaction_dir/cohort_transaction.1.REV_like.mpileup.vcf"
transaction_receipt="$transaction_dir/cohort_transaction.1.step07_outputs.tsv"
transaction_move_log="$test_root/transaction-moves.tsv"
transaction_observation="$test_root/transaction-observation.txt"
env \
    PATH="$transaction_bin:$PATH" \
    REAL_MV="$real_mv" \
    FAKE_MV_LOG="$transaction_move_log" \
    FAKE_OBSERVE_PUBLISHED_FWD="$transaction_fwd" \
    FAKE_OBSERVE_PUBLISHED_REV="$transaction_rev" \
    FAKE_OBSERVE_PUBLISHED_RECEIPT="$transaction_receipt" \
    FAKE_PUBLICATION_OBSERVATION="$transaction_observation" \
    FAKE_BCFTOOLS_SAMPLES=sample_A,sample_B \
    bash "$script" "${transaction_args[@]}" --execute >/dev/null
[[ "$(awk 'END { print NR }' "$transaction_move_log")" == "3" ]] ||
    fail "Fresh Step 07 publication must make exactly three final moves"
transaction_destinations="$(awk -F '\t' '{ print $2 }' "$transaction_move_log")"
expected_transaction_destinations="$(printf '%s\n%s\n%s' \
    "$transaction_fwd" "$transaction_rev" "$transaction_receipt")"
[[ "$transaction_destinations" == "$expected_transaction_destinations" ]] ||
    fail "Step 07 final move order must be FWD, REV, receipt"
assert_text_equals "$transaction_observation" \
    "fwd-rev-receipt-visible-before-commit"

restore_failure_fixture="$test_root/restore-failure"
cp -R "$fixture" "$restore_failure_fixture"
rm -rf "$restore_failure_fixture/output"
restore_failure_args=(
    --cohort-id cohort_restore
    --sample-manifest "$restore_failure_fixture/samples.tsv"
    --partition-manifest "$restore_failure_fixture/partitions.tsv"
    --partition-id 1
    --orientation-root "$restore_failure_fixture/orientation"
    --reference-fasta "$restore_failure_fixture/reference.fa"
    --output-root "$restore_failure_fixture/output"
    --bcftools-bin "$fake_bcftools"
)
FAKE_BCFTOOLS_SAMPLES="sample_A,sample_B" \
    bash "$script" "${restore_failure_args[@]}" --execute >/dev/null
restore_failure_dir="$restore_failure_fixture/output/cohort_restore/1"
restore_failure_fwd="$restore_failure_dir/cohort_restore.1.FWD_like.mpileup.vcf"
restore_failure_rev="$restore_failure_dir/cohort_restore.1.REV_like.mpileup.vcf"
restore_failure_receipt="$restore_failure_dir/cohort_restore.1.step07_outputs.tsv"
printf 'prior fwd bytes\n' >"$restore_failure_fwd"
printf 'prior rev bytes\n' >"$restore_failure_rev"
printf 'prior receipt bytes\n' >"$restore_failure_receipt"
restore_failure_unrelated="$restore_failure_dir/unrelated.txt"
printf 'preserve restore neighbor\n' >"$restore_failure_unrelated"
restore_token="restore67"
restore_failure_log="$test_root/restore-failure-moves.tsv"
run_expect_status 67 "$test_root/restore-failure.out" \
    "$test_root/restore-failure.err" \
    env \
    PATH="$transaction_bin:$PATH" \
    REAL_MV="$real_mv" \
    FAKE_MV_LOG="$restore_failure_log" \
    FAKE_MV_FAIL_RECEIPT_PUBLICATION=1 \
    FAKE_MV_FAIL_FWD_RESTORE=1 \
    FAKE_BCFTOOLS_SAMPLES=sample_A,sample_B \
    SLURM_JOB_ID="$restore_token" \
    bash "$script" "${restore_failure_args[@]}" --execute
restore_failure_fwd_backup="$restore_failure_dir/.cohort_restore.1.step07.$restore_token.previous.FWD_like.vcf"
restore_failure_rev_backup="$restore_failure_dir/.cohort_restore.1.step07.$restore_token.previous.REV_like.vcf"
restore_failure_receipt_backup="$restore_failure_dir/.cohort_restore.1.step07.$restore_token.previous.outputs.tsv"
assert_not_exists "$restore_failure_fwd"
assert_text_equals "$restore_failure_fwd_backup" "prior fwd bytes"
assert_text_equals "$restore_failure_rev" "prior rev bytes"
assert_text_equals "$restore_failure_receipt" "prior receipt bytes"
assert_not_exists "$restore_failure_rev_backup"
assert_not_exists "$restore_failure_receipt_backup"
assert_text_equals "$restore_failure_unrelated" "preserve restore neighbor"
assert_not_exists "$restore_failure_dir/.cohort_restore.1.step07.lock"
assert_not_exists "$restore_failure_dir/.cohort_restore.1.step07.$restore_token.FWD_like.tmp.vcf"
assert_not_exists "$restore_failure_dir/.cohort_restore.1.step07.$restore_token.REV_like.tmp.vcf"
assert_not_exists "$restore_failure_dir/.cohort_restore.1.step07.$restore_token.outputs.tmp.tsv"
assert_contains "$restore_failure_log" \
    "$restore_failure_dir/.cohort_restore.1.step07.$restore_token.outputs.tmp.tsv"$'\t'"$restore_failure_receipt"
assert_contains "$restore_failure_log" \
    "$restore_failure_fwd_backup"$'\t'"$restore_failure_fwd"
if find "$restore_failure_dir" -maxdepth 1 -iname '*recover*' -print -quit |
    grep -q .; then
    fail "Restoration failure must not be represented as a durable recovery marker"
fi

term_fixture="$test_root/term-signal"
cp -R "$fixture" "$term_fixture"
rm -rf "$term_fixture/output"
term_args=(
    --cohort-id cohort_term
    --sample-manifest "$term_fixture/samples.tsv"
    --partition-manifest "$term_fixture/partitions.tsv"
    --partition-id 1
    --orientation-root "$term_fixture/orientation"
    --reference-fasta "$term_fixture/reference.fa"
    --output-root "$term_fixture/output"
    --bcftools-bin "$fake_bcftools"
)
FAKE_BCFTOOLS_SAMPLES="sample_A,sample_B" \
    bash "$script" "${term_args[@]}" --execute >/dev/null
term_dir="$term_fixture/output/cohort_term/1"
term_fwd="$term_dir/cohort_term.1.FWD_like.mpileup.vcf"
term_rev="$term_dir/cohort_term.1.REV_like.mpileup.vcf"
term_receipt="$term_dir/cohort_term.1.step07_outputs.tsv"
printf 'term prior fwd\n' >"$term_fwd"
printf 'term prior rev\n' >"$term_rev"
printf 'term prior receipt\n' >"$term_receipt"
term_unrelated="$term_dir/unrelated.txt"
printf 'preserve term neighbor\n' >"$term_unrelated"
term_token="term143"
term_move_log="$test_root/term-moves.tsv"
run_expect_status 143 "$test_root/term.out" "$test_root/term.err" \
    env \
    PATH="$transaction_bin:$PATH" \
    REAL_MV="$real_mv" \
    FAKE_MV_LOG="$term_move_log" \
    FAKE_MV_SEND_TERM_AFTER_RECEIPT=1 \
    FAKE_BCFTOOLS_SAMPLES=sample_A,sample_B \
    SLURM_JOB_ID="$term_token" \
    bash "$script" "${term_args[@]}" --execute
assert_text_equals "$term_fwd" "term prior fwd"
assert_text_equals "$term_rev" "term prior rev"
assert_text_equals "$term_receipt" "term prior receipt"
assert_text_equals "$term_unrelated" "preserve term neighbor"
assert_not_exists "$term_dir/.cohort_term.1.step07.lock"
assert_no_owned_step07_paths "$term_dir" \
    ".cohort_term.1.step07.$term_token.*"
assert_contains "$term_move_log" \
    "$term_dir/.cohort_term.1.step07.$term_token.outputs.tmp.tsv"$'\t'"$term_receipt"
if find "$term_dir" -maxdepth 1 -iname '*recover*' -print -quit | grep -q .; then
    fail "TERM restoration must not invent a recovery marker"
fi

concurrency_fixture="$test_root/concurrency"
cp -R "$fixture" "$concurrency_fixture"
rm -rf "$concurrency_fixture/output"
concurrency_args=(
    --cohort-id cohort_concurrent
    --sample-manifest "$concurrency_fixture/samples.tsv"
    --partition-manifest "$concurrency_fixture/partitions.tsv"
    --partition-id 1
    --orientation-root "$concurrency_fixture/orientation"
    --reference-fasta "$concurrency_fixture/reference.fa"
    --output-root "$concurrency_fixture/output"
    --bcftools-bin "$fake_bcftools"
)
concurrency_ready="$test_root/concurrency.ready"
concurrency_release="$test_root/concurrency.release"
env \
    FAKE_BCFTOOLS_BARRIER_READY="$concurrency_ready" \
    FAKE_BCFTOOLS_BARRIER_RELEASE="$concurrency_release" \
    FAKE_BCFTOOLS_SAMPLES=sample_A,sample_B \
    bash "$script" "${concurrency_args[@]}" --execute \
    >"$test_root/concurrency-first.out" 2>"$test_root/concurrency-first.err" &
concurrency_first_pid=$!
concurrency_barrier_seen=false
for _ in $(seq 1 200); do
    if [[ -e "$concurrency_ready" ]]; then
        concurrency_barrier_seen=true
        break
    fi
    sleep 0.02
done
if [[ "$concurrency_barrier_seen" != true ]]; then
    : >"$concurrency_release"
    wait "$concurrency_first_pid" || true
    fail "First same-scope producer did not reach the controlled barrier"
fi
run_expect_status 1 "$test_root/concurrency-second.out" \
    "$test_root/concurrency-second.err" \
    env FAKE_BCFTOOLS_SAMPLES=sample_A,sample_B \
    bash "$script" "${concurrency_args[@]}" --execute
concurrency_lock="$concurrency_fixture/output/cohort_concurrent/1/.cohort_concurrent.1.step07.lock"
assert_text_equals "$test_root/concurrency-second.err" \
    "ERROR: Step 07 lock already exists: $concurrency_lock"
: >"$concurrency_release"
if wait "$concurrency_first_pid"; then
    concurrency_first_status=0
else
    concurrency_first_status=$?
fi
[[ "$concurrency_first_status" == "0" ]] ||
    fail "Admitted same-scope producer exited $concurrency_first_status"
concurrency_dir="$concurrency_fixture/output/cohort_concurrent/1"
assert_exists "$concurrency_dir/cohort_concurrent.1.FWD_like.mpileup.vcf"
assert_exists "$concurrency_dir/cohort_concurrent.1.REV_like.mpileup.vcf"
assert_exists "$concurrency_dir/cohort_concurrent.1.step07_outputs.tsv"
assert_not_exists "$concurrency_lock"

rollback_fixture="$test_root/rollback"
cp -R "$fixture" "$rollback_fixture"
rm -rf "$rollback_fixture/output"
rollback_args=(
    --cohort-id cohort_rollback
    --sample-manifest "$rollback_fixture/samples.tsv"
    --partition-manifest "$rollback_fixture/partitions.tsv"
    --partition-id 1
    --orientation-root "$rollback_fixture/orientation"
    --reference-fasta "$rollback_fixture/reference.fa"
    --output-root "$rollback_fixture/output"
    --bcftools-bin "$fake_bcftools"
)
FAKE_BCFTOOLS_SAMPLES="sample_A,sample_B" \
    bash "$script" "${rollback_args[@]}" --execute >/dev/null
rollback_dir="$rollback_fixture/output/cohort_rollback/1"
rollback_fwd="$rollback_dir/cohort_rollback.1.FWD_like.mpileup.vcf"
rollback_rev="$rollback_dir/cohort_rollback.1.REV_like.mpileup.vcf"
rollback_receipt="$rollback_dir/cohort_rollback.1.step07_outputs.tsv"
printf 'previous fwd\n' >"$rollback_fwd"
printf 'previous rev\n' >"$rollback_rev"
printf 'previous receipt\n' >"$rollback_receipt"
run_expect_failure "$test_root/rollback.out" "$test_root/rollback.err" \
    env FAKE_FAIL_FINAL_VALIDATION=1 FAKE_BCFTOOLS_SAMPLES=sample_A,sample_B \
    bash "$script" "${rollback_args[@]}" --execute
assert_contains "$test_root/rollback.err" "Published FWD_like VCF header validation failed"
assert_contains "$rollback_fwd" "previous fwd"
assert_contains "$rollback_rev" "previous rev"
assert_contains "$rollback_receipt" "previous receipt"
assert_not_exists "$rollback_dir/.cohort_rollback.1.step07.lock"
if find "$rollback_dir" -maxdepth 1 -name '.cohort_rollback.1.step07.*' -print -quit |
    grep -q .; then
    fail "Rollback must clean invocation-owned scratch paths"
fi

partial_fixture="$test_root/partial"
cp -R "$fixture" "$partial_fixture"
rm -rf "$partial_fixture/output"
partial_dir="$partial_fixture/output/cohort_partial/1"
mkdir -p "$partial_dir"
printf 'existing\n' >"$partial_dir/cohort_partial.1.FWD_like.mpileup.vcf"
run_expect_failure "$test_root/partial.out" "$test_root/partial.err" \
    env FAKE_BCFTOOLS_SAMPLES=sample_A,sample_B \
    bash "$script" \
    --cohort-id cohort_partial \
    --sample-manifest "$partial_fixture/samples.tsv" \
    --partition-manifest "$partial_fixture/partitions.tsv" \
    --partition-id 1 \
    --orientation-root "$partial_fixture/orientation" \
    --reference-fasta "$partial_fixture/reference.fa" \
    --output-root "$partial_fixture/output" \
    --bcftools-bin "$fake_bcftools" \
    --execute
assert_contains "$test_root/partial.err" "outputs are incomplete"
assert_contains "$partial_dir/cohort_partial.1.FWD_like.mpileup.vcf" "existing"

primary_partitions="$repo_root/configs/step_07_partitions.primary_contigs.tsv"
pilot_partitions="$repo_root/configs/step_07_partitions.pilot.tsv"
assert_contains "$job" "configs/step_07_partitions.primary_contigs.tsv"
[[ "$(awk 'END { print NR }' "$primary_partitions")" == "26" ]] ||
    fail "Primary-contig manifest must declare 25 partitions plus its header"
assert_contains "$primary_partitions" $'MT\tregion\tMT'
[[ "$(awk 'END { print NR }' "$pilot_partitions")" == "2" ]] ||
    fail "Pilot manifest must contain exactly one partition plus its header"
assert_contains "$pilot_partitions" $'pilot_1\tregion\t1:1-100000'
wrapper_root="$test_root/wrapper"
mkdir -p "$wrapper_root/scripts"
cp "$script" "$wrapper_root/scripts/"
wrapper_filter='INFO/AD[1-]>7 & MAX(FORMAT/DP)>31'
env \
    PATH="$fake_bin:$PATH" \
    SLURM_SUBMIT_DIR="$wrapper_root" \
    EXECUTE=0 \
    COHORT_ID=wrapper_dry \
    SAMPLE_MANIFEST="$fixture/samples.tsv" \
    PARTITION_MANIFEST="$fixture/partitions.tsv" \
    PARTITION_ID=1 \
    ORIENTATION_ROOT="$fixture/orientation" \
    REFERENCE_FASTA="$fixture/reference.fa" \
    OUTPUT_ROOT="$wrapper_root/dry-output" \
    MAX_DEPTH=123 \
    FILTER_EXPRESSION="$wrapper_filter" \
    BCFTOOLS_BIN_OVERRIDE="$fake_bcftools" \
    bash "$job" >"$test_root/wrapper-dry.out"
assert_contains "$test_root/wrapper-dry.out" "Execute mode: 0"
assert_contains "$test_root/wrapper-dry.out" "Maximum depth: 123"
assert_contains "$test_root/wrapper-dry.out" "Filter expression: $wrapper_filter"
assert_contains "$test_root/wrapper-dry.out" "Step 07 completed in dry-run mode"
assert_not_exists "$wrapper_root/dry-output"

env \
    PATH="$fake_bin:$PATH" \
    SLURM_SUBMIT_DIR="$wrapper_root" \
    EXECUTE=1 \
    COHORT_ID=wrapper_exec \
    SAMPLE_MANIFEST="$fixture/samples.tsv" \
    PARTITION_MANIFEST="$fixture/partitions.tsv" \
    PARTITION_ID=1 \
    ORIENTATION_ROOT="$fixture/orientation" \
    REFERENCE_FASTA="$fixture/reference.fa" \
    OUTPUT_ROOT="$wrapper_root/execute-output" \
    BCFTOOLS_BIN_OVERRIDE="$fake_bcftools" \
    FAKE_BCFTOOLS_SAMPLES=sample_A,sample_B \
    bash "$job" >"$test_root/wrapper-execute.out"
assert_contains "$test_root/wrapper-execute.out" "Validated Step 07 cohort mpileup outputs"
assert_exists "$wrapper_root/execute-output/wrapper_exec/1/wrapper_exec.1.FWD_like.mpileup.vcf"
assert_exists "$wrapper_root/execute-output/wrapper_exec/1/wrapper_exec.1.REV_like.mpileup.vcf"
assert_exists "$wrapper_root/execute-output/wrapper_exec/1/wrapper_exec.1.step07_outputs.tsv"

wrapper_missing_root="$test_root/wrapper-missing-output"
mkdir -p "$wrapper_missing_root/scripts"
cat >"$wrapper_missing_root/scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh" <<'STUB'
#!/usr/bin/env bash
exit 0
STUB
run_expect_failure "$test_root/wrapper-missing.out" "$test_root/wrapper-missing.err" \
    env \
    PATH="$fake_bin:$PATH" \
    SLURM_SUBMIT_DIR="$wrapper_missing_root" \
    EXECUTE=1 \
    COHORT_ID=wrapper_missing \
    OUTPUT_ROOT="$wrapper_missing_root/output" \
    BCFTOOLS_BIN_OVERRIDE="$fake_bcftools" \
    bash "$job"
assert_contains "$test_root/wrapper-missing.err" "Expected FWD_like VCF does not exist or is empty"

invalid_wrapper_root="$test_root/wrapper-invalid"
mkdir -p "$invalid_wrapper_root"
run_expect_failure "$test_root/wrapper-invalid.out" "$test_root/wrapper-invalid.err" \
    env PATH="$fake_bin:$PATH" SLURM_SUBMIT_DIR="$invalid_wrapper_root" EXECUTE=2 \
    bash "$job"
assert_contains "$test_root/wrapper-invalid.err" "EXECUTE must be 0 or 1"
assert_not_exists "$invalid_wrapper_root/logs"

printf 'PASS: Step 07 cohort mpileup shell tests\n'
