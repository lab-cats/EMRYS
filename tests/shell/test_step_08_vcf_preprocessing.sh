#!/usr/bin/env bash
set -euo pipefail

# Mocked-R coverage for Step 08 shell orchestration. Semantic VCF/GTF behavior
# belongs to the separate real-R fixture suite when an R runtime is available.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
script="$repo_root/scripts/step_08_vcf_preprocessing.sh"
job="$repo_root/jobs/step_08_vcf_preprocessing.slurm"
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

assert_not_contains() {
    local path_or_text="$1"
    local unexpected="$2"
    local content
    if [[ -f "$path_or_text" ]]; then
        content="$(<"$path_or_text")"
    else
        content="$path_or_text"
    fi
    [[ "$content" != *"$unexpected"* ]] ||
        fail "Expected content not to contain: $unexpected"
}

assert_exists() {
    [[ -s "$1" ]] || fail "Expected non-empty file: $1"
}

assert_not_exists() {
    [[ ! -e "$1" ]] || fail "Path unexpectedly exists: $1"
}

assert_file_equals() {
    local path="$1"
    local expected="$2"
    [[ -f "$path" ]] || fail "Expected file: $path"
    [[ "$(<"$path")" == "$expected" ]] ||
        fail "Unexpected content in: $path"
}

run_expect_failure() {
    local stdout_path="$1"
    local stderr_path="$2"
    shift 2
    if "$@" >"$stdout_path" 2>"$stderr_path"; then
        fail "Command unexpectedly succeeded: $*"
    fi
}

assert_no_step08_scratch() {
    local output_root="$1"
    local qc_root="$2"
    local found=""

    if [[ -d "$output_root" ]]; then
        found="$(find "$output_root" -name '.*.step08.*' ! -name '*.step08.lock' -print -quit)"
    fi
    if [[ -z "$found" && -d "$qc_root" ]]; then
        found="$(find "$qc_root" -name '.*.step08.*' -print -quit)"
    fi
    [[ -z "$found" ]] || fail "Step 08 scratch path remains: $found"
}

assert_no_step08_recovery_marker() {
    local output_root="$1"
    local qc_root="$2"
    local found=""

    found="$(find "$output_root" "$qc_root" -name '*step08*recovery*' -print -quit 2>/dev/null || true)"
    [[ -z "$found" ]] || fail "Unexpected Step 08 recovery marker: $found"
}

fake_bin="$test_root/fake-bin"
mkdir -p "$fake_bin"

fake_rscript="$fake_bin/Rscript"
apply_fake_rscript="$fake_rscript"
cat >"$fake_rscript" <<'FAKE_RSCRIPT'
#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${FAKE_RSCRIPT_LOG:-}" ]]; then
    printf '%q ' "$@" >>"$FAKE_RSCRIPT_LOG"
    printf '\n' >>"$FAKE_RSCRIPT_LOG"
fi

if [[ "${1:-}" == "--version" ]]; then
    printf 'R scripting front-end version 4.fake\n'
    exit 0
fi

r_script="${1:-}"
[[ -n "$r_script" ]] || exit 70
shift

cohort_id=""
sample_manifest=""
partition_manifest=""
step07_root=""
annotation_gtf=""
sample_hash=""
partition_hash=""
annotation_hash=""
sites_output=""
inputs_output=""
summary_output=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --cohort-id) cohort_id="$2"; shift 2 ;;
        --sample-manifest) sample_manifest="$2"; shift 2 ;;
        --partition-manifest) partition_manifest="$2"; shift 2 ;;
        --step07-root) step07_root="$2"; shift 2 ;;
        --annotation-gtf) annotation_gtf="$2"; shift 2 ;;
        --sample-manifest-sha256) sample_hash="$2"; shift 2 ;;
        --partition-manifest-sha256) partition_hash="$2"; shift 2 ;;
        --annotation-gtf-sha256) annotation_hash="$2"; shift 2 ;;
        --sites-output) sites_output="$2"; shift 2 ;;
        --inputs-output) inputs_output="$2"; shift 2 ;;
        --summary-output) summary_output="$2"; shift 2 ;;
        *) exit 71 ;;
    esac
done

for value in \
    "$cohort_id" "$sample_manifest" "$partition_manifest" "$step07_root" \
    "$annotation_gtf" "$sample_hash" "$partition_hash" "$annotation_hash" \
    "$sites_output" "$inputs_output" "$summary_output"
do
    [[ -n "$value" ]] || exit 72
done

if [[ "${FAKE_RSCRIPT_FAIL:-0}" == "1" ]]; then
    exit 73
fi

hash_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    else
        shasum -a 256 "$1" | awk '{print $1}'
    fi
}

sample_ids=()
while IFS= read -r sample_id; do
    [[ -n "$sample_id" ]] && sample_ids+=("$sample_id")
done < <(awk -F '\t' 'NR > 1 { print $1 }' "$sample_manifest")
sample_count="${#sample_ids[@]}"

sites_header='partition_id	candidate_id	orientation	chromosome	position	alt_index	genomic_ref	genomic_alt	rna_ref	rna_alt	annotation_strand	gene_ids	transcript_ids	is_cds	is_five_prime_utr	is_three_prime_utr	is_exon	is_intron	qual	filter	info_alt_depth	orientation_policy'
for sample_id in "${sample_ids[@]}"; do
    sites_header+=$'\t'"DP__$sample_id"
done
for sample_id in "${sample_ids[@]}"; do
    sites_header+=$'\t'"AD__$sample_id"
done
for sample_id in "${sample_ids[@]}"; do
    sites_header+=$'\t'"AF__$sample_id"
done

inputs_header='cohort_id	partition_id	selector_type	selector_value	orientation	step07_receipt_path	step07_receipt_sha256	vcf_path	vcf_sha256	sample_manifest_sha256	partition_manifest_sha256	annotation_gtf	annotation_gtf_sha256	sample_count	declared_vcf_record_count	observed_vcf_record_count	observed_alt_allele_count	supported_snv_count	skipped_symbolic_count	skipped_non_snv_count	published_candidate_count	orientation_policy'
summary_header='cohort_id	partition_count	step07_receipt_count	input_vcf_count	sample_count	observed_vcf_record_count	observed_alt_allele_count	supported_snv_count	skipped_symbolic_count	skipped_non_snv_count	published_candidate_count	sample_manifest_sha256	partition_manifest_sha256	annotation_gtf	annotation_gtf_sha256	orientation_policy'

if [[ "${FAKE_RSCRIPT_OMIT_OUTPUT:-}" != "sites" ]]; then
    {
        if [[ "${FAKE_RSCRIPT_BAD_HEADER:-}" == "sites" ]]; then
            printf 'bad_sites_header\n'
        else
            printf '%s\n' "$sites_header"
            if [[ "${FAKE_RSCRIPT_HEADER_ONLY:-0}" != "1" ]]; then
                candidate_number=0
                while IFS=$'\t' read -r partition_id selector_type selector_value; do
                    [[ "$partition_id" == "partition_id" ]] && continue
                    [[ -n "$partition_id" ]] || continue
                    for orientation in FWD_like REV_like; do
                        candidate_number=$((candidate_number + 1))
                        candidate_id="$orientation|$selector_value|10|A>G"
                        if [[ "${FAKE_RSCRIPT_DUPLICATE_CANDIDATE:-0}" == "1" &&
                              "$candidate_number" -eq 2 ]]; then
                            candidate_id='FWD_like|1|10|A>G'
                        fi
                        annotation_strand='+'
                        rna_ref='T'
                        rna_alt='C'
                        if [[ "$orientation" == "REV_like" ]]; then
                            annotation_strand='-'
                            rna_ref='A'
                            rna_alt='G'
                        fi
                        printf '%s\t%s\t%s\t%s\t10\t1\tA\tG\t%s\t%s\t%s\tgene1\ttx1\tTRUE\tFALSE\tFALSE\tTRUE\tFALSE\t60\tPASS\t4\tlegacy_provisional_v1' \
                            "$partition_id" "$candidate_id" "$orientation" \
                            "$selector_value" "$rna_ref" "$rna_alt" \
                            "$annotation_strand"
                        for sample_id in "${sample_ids[@]}"; do
                            printf '\t10'
                        done
                        for sample_id in "${sample_ids[@]}"; do
                            printf '\t2'
                        done
                        for sample_id in "${sample_ids[@]}"; do
                            printf '\t0.2'
                        done
                        printf '\n'
                    done
                done <"$partition_manifest"
            fi
        fi
    } >"$sites_output"
fi

partition_count="$(awk 'END { print NR - 1 }' "$partition_manifest")"
input_count=$((partition_count * 2))

if [[ "${FAKE_RSCRIPT_OMIT_OUTPUT:-}" != "inputs" ]]; then
    {
        if [[ "${FAKE_RSCRIPT_BAD_HEADER:-}" == "inputs" ]]; then
            printf 'bad_inputs_header\n'
        else
            printf '%s\n' "$inputs_header"
            input_row_number=0
            while IFS=$'\t' read -r partition_id selector_type selector_value; do
                [[ "$partition_id" == "partition_id" ]] && continue
                [[ -n "$partition_id" ]] || continue
                receipt="$step07_root/$cohort_id/$partition_id/$cohort_id.$partition_id.step07_outputs.tsv"
                receipt_hash="$(hash_file "$receipt")"
                orientations=(FWD_like REV_like)
                if [[ "${FAKE_RSCRIPT_BAD_INPUT_ORDER:-0}" == "1" &&
                      "$input_row_number" -eq 0 ]]; then
                    orientations=(REV_like FWD_like)
                fi
                for orientation in "${orientations[@]}"; do
                    input_row_number=$((input_row_number + 1))
                    vcf="$step07_root/$cohort_id/$partition_id/$cohort_id.$partition_id.$orientation.mpileup.vcf"
                    vcf_hash="$(hash_file "$vcf")"
                    declared_count="$(awk -F '\t' -v orientation="$orientation" '
                        NR > 1 && $5 == orientation { print $10; exit }
                    ' "$receipt")"
                    observed_alt_count=1
                    supported_count=1
                    symbolic_count=0
                    non_snv_count=0
                    published_count=1
                    if [[ "${FAKE_RSCRIPT_HEADER_ONLY:-0}" == "1" ]]; then
                        supported_count=0
                        non_snv_count=1
                        published_count=0
                    fi
                    if [[ "${FAKE_RSCRIPT_BAD_RECONCILIATION:-0}" == "1" &&
                          "$input_row_number" -eq 1 ]]; then
                        observed_alt_count=2
                    fi
                    if [[ "${FAKE_RSCRIPT_BAD_INPUT_HASH:-0}" == "1" &&
                          "$input_row_number" -eq 1 ]]; then
                        vcf_hash='invalid-vcf-hash'
                    fi
                    if [[ "${FAKE_RSCRIPT_BAD_INPUT_PATH:-0}" == "1" &&
                          "$input_row_number" -eq 1 ]]; then
                        vcf="$vcf.unexpected"
                    fi
                    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\tlegacy_provisional_v1' \
                        "$cohort_id" "$partition_id" "$selector_type" "$selector_value" \
                        "$orientation" "$receipt" "$receipt_hash" "$vcf" \
                        "$vcf_hash" "$sample_hash" "$partition_hash" \
                        "$annotation_gtf" "$annotation_hash" "$sample_count" \
                        "$declared_count" "$declared_count" \
                        "$observed_alt_count" "$supported_count" \
                        "$symbolic_count" "$non_snv_count" "$published_count"
                    if [[ "${FAKE_RSCRIPT_EXTRA_INPUT_FIELD:-0}" == "1" &&
                          "$input_row_number" -eq 1 ]]; then
                        printf '\textra'
                    fi
                    printf '\n'
                done
            done <"$partition_manifest"
        fi
    } >"$inputs_output"
fi

if [[ "${FAKE_RSCRIPT_OMIT_OUTPUT:-}" != "summary" ]]; then
    {
        if [[ "${FAKE_RSCRIPT_BAD_HEADER:-}" == "summary" ]]; then
            printf 'bad_summary_header\n'
        else
            printf '%s\n' "$summary_header"
            total_supported="$input_count"
            total_non_snv=0
            total_published="$input_count"
            if [[ "${FAKE_RSCRIPT_HEADER_ONLY:-0}" == "1" ]]; then
                total_supported=0
                total_non_snv="$input_count"
                total_published=0
            fi
            if [[ "${FAKE_RSCRIPT_BAD_SUMMARY:-0}" == "1" ]]; then
                total_published=$((total_published + 1))
            fi
            printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t0\t%s\t%s\t%s\t%s\t%s\t%s\tlegacy_provisional_v1\n' \
                "$cohort_id" "$partition_count" "$partition_count" "$input_count" \
                "$sample_count" "$input_count" "$input_count" \
                "$total_supported" "$total_non_snv" "$total_published" \
                "$sample_hash" "$partition_hash" "$annotation_gtf" "$annotation_hash"
        fi
    } >"$summary_output"
fi

case "${FAKE_RSCRIPT_MUTATE:-}" in
    sample) printf '\n' >>"$sample_manifest" ;;
    partition) printf '\n' >>"$partition_manifest" ;;
    annotation) printf '\n' >>"$annotation_gtf" ;;
    receipt)
        first_partition="$(awk -F '\t' 'NR == 2 { print $1; exit }' "$partition_manifest")"
        printf '\n' >>"$step07_root/$cohort_id/$first_partition/$cohort_id.$first_partition.step07_outputs.tsv"
        ;;
    vcf)
        first_partition="$(awk -F '\t' 'NR == 2 { print $1; exit }' "$partition_manifest")"
        printf '\n' >>"$step07_root/$cohort_id/$first_partition/$cohort_id.$first_partition.FWD_like.mpileup.vcf"
        ;;
    r_script) printf '\n# changed while fake R was running\n' >>"$r_script" ;;
esac
FAKE_RSCRIPT
chmod +x "$fake_rscript"

cat >"$fake_bin/module" <<'FAKE_MODULE'
#!/usr/bin/env bash
exit 0
FAKE_MODULE
chmod +x "$fake_bin/module"

cat >"$fake_bin/mv" <<'FAKE_MV'
#!/usr/bin/env bash
set -euo pipefail

destination=""
for argument in "$@"; do
    destination="$argument"
done
source="${1:-}"

if [[ -n "${FAKE_MV_LOG:-}" ]]; then
    printf '%q ' "$@" >>"$FAKE_MV_LOG"
    printf '\n' >>"$FAKE_MV_LOG"
fi

if [[ -n "${FAKE_MV_FAIL_ONCE_DEST_MATCH:-}" &&
      "$destination" == *"$FAKE_MV_FAIL_ONCE_DEST_MATCH"* &&
      ! -e "${FAKE_MV_FAIL_MARKER:?}" ]]; then
    : >"$FAKE_MV_FAIL_MARKER"
    exit 91
fi

if [[ -n "${FAKE_MV_CORRUPT_ONCE_DEST_MATCH:-}" &&
      "$destination" == *"$FAKE_MV_CORRUPT_ONCE_DEST_MATCH"* &&
      ! -e "${FAKE_MV_CORRUPT_MARKER:?}" ]]; then
    /bin/mv "$@"
    : >"$FAKE_MV_CORRUPT_MARKER"
    printf 'corrupt after publication\n' >"$destination"
    exit 0
fi

if [[ -n "${FAKE_MV_RECEIPT_FAIL_DEST_MATCH:-}" &&
      "$destination" == *"$FAKE_MV_RECEIPT_FAIL_DEST_MATCH"* &&
      ! -e "${FAKE_MV_RECEIPT_FAIL_MARKER:?}" ]]; then
    : >"$FAKE_MV_RECEIPT_FAIL_MARKER"
    exit 67
fi

if [[ -n "${FAKE_MV_SITES_RESTORE_FAIL_DEST_MATCH:-}" &&
      -e "${FAKE_MV_RECEIPT_FAIL_MARKER:?}" &&
      "$source" == *'.previous.sites.tsv' &&
      "$destination" == *"$FAKE_MV_SITES_RESTORE_FAIL_DEST_MATCH"* &&
      ! -e "${FAKE_MV_SITES_RESTORE_FAIL_MARKER:?}" ]]; then
    : >"$FAKE_MV_SITES_RESTORE_FAIL_MARKER"
    exit 68
fi

if [[ -n "${FAKE_MV_BARRIER_DEST_MATCH:-}" &&
      "$destination" == *"$FAKE_MV_BARRIER_DEST_MATCH"* ]]; then
    /bin/mv "$@"
    : >"${FAKE_MV_BARRIER_MARKER:?}"
    while [[ ! -e "${FAKE_MV_BARRIER_RELEASE:?}" ]]; do
        sleep 0.01
    done
    exit 0
fi

exec /bin/mv "$@"
FAKE_MV
chmod +x "$fake_bin/mv"

sha256_test_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    else
        shasum -a 256 "$1" | awk '{print $1}'
    fi
}

create_fixture() {
    local root="$1"
    local cohort="${2:-cohort_A}"
    local partition
    local chromosome
    local orientation
    local sample_hash
    local partition_hash
    local receipt
    local vcf

    mkdir -p "$root/step07/$cohort/p1" "$root/step07/$cohort/p2"
    printf 'sample_id\tcondition\nsample_A\tEV\nsample_B\tPUM1\n' >"$root/samples.tsv"
    printf 'partition_id\tselector_type\tselector_value\np1\tregion\t1\np2\tregion\t2\n' >"$root/partitions.tsv"
    printf '1\tsource\ttranscript\t1\t100\t.\t+\t.\tgene_id "gene1"; transcript_id "tx1";\n' >"$root/annotation.gtf"
    printf '# fake R implementation placeholder\n' >"$root/step08_impl.R"

    sample_hash="$(sha256_test_file "$root/samples.tsv")"
    partition_hash="$(sha256_test_file "$root/partitions.tsv")"
    for partition in p1 p2; do
        chromosome=1
        if [[ "$partition" == "p2" ]]; then
            chromosome=2
        fi
        for orientation in FWD_like REV_like; do
            vcf="$root/step07/$cohort/$partition/$cohort.$partition.$orientation.mpileup.vcf"
            {
                printf '##fileformat=VCFv4.2\n'
                printf '##INFO=<ID=AD,Number=R,Type=Integer,Description="Allele depth">\n'
                printf '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Depth">\n'
                printf '##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allele depth">\n'
                printf '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsample_A\tsample_B\n'
                printf '%s\t10\t.\tA\tG\t60\tPASS\tAD=20,4\tDP:AD\t10:8,2\t10:8,2\n' \
                    "$chromosome"
            } >"$vcf"
        done
        receipt="$root/step07/$cohort/$partition/$cohort.$partition.step07_outputs.tsv"
        {
            printf 'cohort_id\tpartition_id\tselector_type\tselector_value\torientation\tvcf_path\tsample_manifest_sha256\tpartition_manifest_sha256\tsample_count\tvcf_record_count\n'
            printf '%s\t%s\tregion\t%s\tFWD_like\t%s\t%s\t%s\t2\t1\n' \
                "$cohort" "$partition" "$chromosome" \
                "$root/step07/$cohort/$partition/$cohort.$partition.FWD_like.mpileup.vcf" \
                "$sample_hash" "$partition_hash"
            printf '%s\t%s\tregion\t%s\tREV_like\t%s\t%s\t%s\t2\t1\n' \
                "$cohort" "$partition" "$chromosome" \
                "$root/step07/$cohort/$partition/$cohort.$partition.REV_like.mpileup.vcf" \
                "$sample_hash" "$partition_hash"
        } >"$receipt"
    done
}

fixture="$test_root/fixture"
create_fixture "$fixture"
common_args=(
    --cohort-id cohort_A
    --sample-manifest "$fixture/samples.tsv"
    --partition-manifest "$fixture/partitions.tsv"
    --step07-root "$fixture/step07"
    --annotation-gtf "$fixture/annotation.gtf"
    --output-root "$fixture/output"
    --qc-root "$fixture/qc"
    --rscript-bin "$fake_rscript"
    --r-script "$fixture/step08_impl.R"
)

run_invalid_fake_output_case() {
    local slug="$1"
    local fake_setting="$2"
    local expected_error="$3"
    local case_root="$test_root/$slug"
    local cohort="cohort_$slug"

    create_fixture "$case_root" "$cohort"
    run_expect_failure \
        "$test_root/$slug.out" \
        "$test_root/$slug.err" \
        env \
        PATH="$fake_bin:$PATH" \
        SLURM_JOB_ID="${slug}08" \
        "$fake_setting" \
        bash "$script" \
        --cohort-id "$cohort" \
        --sample-manifest "$case_root/samples.tsv" \
        --partition-manifest "$case_root/partitions.tsv" \
        --step07-root "$case_root/step07" \
        --annotation-gtf "$case_root/annotation.gtf" \
        --output-root "$case_root/output" \
        --qc-root "$case_root/qc" \
        --rscript-bin "$fake_rscript" \
        --r-script "$case_root/step08_impl.R" \
        --execute
    assert_contains "$test_root/$slug.err" "$expected_error"
    assert_not_exists \
        "$case_root/output/$cohort/$cohort.step08_sites.tsv"
    assert_not_exists \
        "$case_root/output/$cohort/$cohort.step08_inputs.tsv"
    assert_not_exists "$case_root/qc/$cohort.step08_summary.tsv"
    assert_no_step08_scratch "$case_root/output" "$case_root/qc"
}

run_detected_input_mutation_case() {
    local slug="$1"
    local mutation="$2"
    local expected_error="$3"
    local case_root="$test_root/$slug"
    local cohort="cohort_$slug"

    create_fixture "$case_root" "$cohort"
    mkdir -p "$case_root/output" "$case_root/qc"
    printf 'unrelated output bytes\n' >"$case_root/output/unrelated.txt"
    printf 'unrelated QC bytes\n' >"$case_root/qc/unrelated.txt"
    run_expect_failure \
        "$test_root/$slug.out" \
        "$test_root/$slug.err" \
        env \
        PATH="$fake_bin:$PATH" \
        SLURM_JOB_ID="${slug}08" \
        FAKE_RSCRIPT_MUTATE="$mutation" \
        bash "$script" \
        --cohort-id "$cohort" \
        --sample-manifest "$case_root/samples.tsv" \
        --partition-manifest "$case_root/partitions.tsv" \
        --step07-root "$case_root/step07" \
        --annotation-gtf "$case_root/annotation.gtf" \
        --output-root "$case_root/output" \
        --qc-root "$case_root/qc" \
        --rscript-bin "$fake_rscript" \
        --r-script "$case_root/step08_impl.R" \
        --execute
    assert_contains "$test_root/$slug.err" "$expected_error"
    assert_not_exists "$case_root/output/$cohort/$cohort.step08_sites.tsv"
    assert_not_exists "$case_root/output/$cohort/$cohort.step08_inputs.tsv"
    assert_not_exists "$case_root/qc/$cohort.step08_summary.tsv"
    assert_file_equals "$case_root/output/unrelated.txt" "unrelated output bytes"
    assert_file_equals "$case_root/qc/unrelated.txt" "unrelated QC bytes"
    assert_no_step08_scratch "$case_root/output" "$case_root/qc"
}

help_output="$(bash "$script" --help)"
assert_contains "$help_output" "Usage:"
assert_contains "$help_output" "--step07-root"
assert_contains "$help_output" "--annotation-gtf"
assert_contains "$help_output" "--rscript-bin"
assert_contains "$help_output" "legacy_provisional_v1"

run_expect_failure "$test_root/missing.out" "$test_root/missing.err" \
    bash "$script" --sample-manifest "$fixture/samples.tsv"
assert_contains "$test_root/missing.err" "Missing required argument: --cohort-id"

printf 'Running R runtime and program preflight checks...\n'
missing_rscript_fixture="$test_root/missing-rscript"
create_fixture "$missing_rscript_fixture" cohort_missing_rscript
run_expect_failure \
    "$test_root/missing-rscript.out" \
    "$test_root/missing-rscript.err" \
    bash "$script" \
    --cohort-id cohort_missing_rscript \
    --sample-manifest "$missing_rscript_fixture/samples.tsv" \
    --partition-manifest "$missing_rscript_fixture/partitions.tsv" \
    --step07-root "$missing_rscript_fixture/step07" \
    --annotation-gtf "$missing_rscript_fixture/annotation.gtf" \
    --output-root "$missing_rscript_fixture/output" \
    --qc-root "$missing_rscript_fixture/qc" \
    --rscript-bin "$missing_rscript_fixture/absent-Rscript" \
    --r-script "$missing_rscript_fixture/step08_impl.R"
assert_contains "$test_root/missing-rscript.err" "Rscript does not exist"
assert_not_exists "$missing_rscript_fixture/output"
assert_not_exists "$missing_rscript_fixture/qc"

nonexec_rscript_fixture="$test_root/nonexec-rscript"
create_fixture "$nonexec_rscript_fixture" cohort_nonexec_rscript
printf '#!/usr/bin/env bash\nexit 0\n' >"$nonexec_rscript_fixture/nonexec-Rscript"
chmod 0644 "$nonexec_rscript_fixture/nonexec-Rscript"
run_expect_failure \
    "$test_root/nonexec-rscript.out" \
    "$test_root/nonexec-rscript.err" \
    bash "$script" \
    --cohort-id cohort_nonexec_rscript \
    --sample-manifest "$nonexec_rscript_fixture/samples.tsv" \
    --partition-manifest "$nonexec_rscript_fixture/partitions.tsv" \
    --step07-root "$nonexec_rscript_fixture/step07" \
    --annotation-gtf "$nonexec_rscript_fixture/annotation.gtf" \
    --output-root "$nonexec_rscript_fixture/output" \
    --qc-root "$nonexec_rscript_fixture/qc" \
    --rscript-bin "$nonexec_rscript_fixture/nonexec-Rscript" \
    --r-script "$nonexec_rscript_fixture/step08_impl.R"
assert_contains "$test_root/nonexec-rscript.err" "Rscript exists but is not executable"
assert_not_exists "$nonexec_rscript_fixture/output"
assert_not_exists "$nonexec_rscript_fixture/qc"

missing_r_program_fixture="$test_root/missing-r-program"
create_fixture "$missing_r_program_fixture" cohort_missing_r_program
run_expect_failure \
    "$test_root/missing-r-program.out" \
    "$test_root/missing-r-program.err" \
    bash "$script" \
    --cohort-id cohort_missing_r_program \
    --sample-manifest "$missing_r_program_fixture/samples.tsv" \
    --partition-manifest "$missing_r_program_fixture/partitions.tsv" \
    --step07-root "$missing_r_program_fixture/step07" \
    --annotation-gtf "$missing_r_program_fixture/annotation.gtf" \
    --output-root "$missing_r_program_fixture/output" \
    --qc-root "$missing_r_program_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$missing_r_program_fixture/absent-step08.R"
assert_contains "$test_root/missing-r-program.err" "Step 08 R script does not exist or is empty"
assert_not_exists "$missing_r_program_fixture/output"
assert_not_exists "$missing_r_program_fixture/qc"

printf 'Running Step 08 dry-run and exact-input enumeration checks...\n'
printf 'unmanifested\n' >"$fixture/step07/cohort_A/p1/unmanifested.extra.vcf"
dry_log="$test_root/dry-rscript.log"
env SLURM_JOB_ID=dry08 FAKE_RSCRIPT_LOG="$dry_log" \
    bash "$script" "${common_args[@]}" >"$test_root/dry.out"
assert_contains "$test_root/dry.out" "Mode: dry-run"
assert_contains "$test_root/dry.out" "Partition count: 2"
assert_contains "$test_root/dry.out" "Expected Step 07 VCF count: 4"
assert_contains "$test_root/dry.out" "cohort_A.p1.FWD_like.mpileup.vcf"
assert_contains "$test_root/dry.out" "cohort_A.p2.REV_like.mpileup.vcf"
assert_contains "$test_root/dry.out" "--sample-manifest-sha256"
assert_contains "$test_root/dry.out" "--annotation-gtf-sha256"
assert_contains "$test_root/dry.out" "input receipt last as commit marker"
assert_contains "$test_root/dry.out" "R was not invoked"
assert_not_contains "$test_root/dry.out" "unmanifested.extra.vcf"
assert_not_exists "$dry_log"
assert_not_exists "$fixture/output"
assert_not_exists "$fixture/qc"

printf 'Running PATH-basename Rscript from an arbitrary CWD...\n'
path_fixture="$test_root/path-rscript"
path_cwd="$test_root/path-rscript-cwd"
create_fixture "$path_fixture" cohort_path_rscript
mkdir -p "$path_cwd"
(
    cd "$path_cwd"
    env \
        PATH="$fake_bin:$PATH" \
        SLURM_JOB_ID=pathrscript08 \
        bash "$script" \
        --cohort-id cohort_path_rscript \
        --sample-manifest "$path_fixture/samples.tsv" \
        --partition-manifest "$path_fixture/partitions.tsv" \
        --step07-root "$path_fixture/step07" \
        --annotation-gtf "$path_fixture/annotation.gtf" \
        --output-root "$path_fixture/output" \
        --qc-root "$path_fixture/qc" \
        --rscript-bin Rscript \
        --r-script "$path_fixture/step08_impl.R" \
        --execute >"$test_root/path-rscript.out"
)
assert_contains "$test_root/path-rscript.out" "Rscript: $fake_rscript"
assert_exists "$path_fixture/output/cohort_path_rscript/cohort_path_rscript.step08_sites.tsv"
assert_exists "$path_fixture/output/cohort_path_rscript/cohort_path_rscript.step08_inputs.tsv"
assert_exists "$path_fixture/qc/cohort_path_rscript.step08_summary.tsv"
assert_no_step08_scratch "$path_fixture/output" "$path_fixture/qc"

printf 'Running missing declared input failure check...\n'
missing_fixture="$test_root/missing-input"
create_fixture "$missing_fixture" cohort_missing
rm "$missing_fixture/step07/cohort_missing/p2/cohort_missing.p2.REV_like.mpileup.vcf"
run_expect_failure "$test_root/missing-input.out" "$test_root/missing-input.err" \
    bash "$script" \
    --cohort-id cohort_missing \
    --sample-manifest "$missing_fixture/samples.tsv" \
    --partition-manifest "$missing_fixture/partitions.tsv" \
    --step07-root "$missing_fixture/step07" \
    --annotation-gtf "$missing_fixture/annotation.gtf" \
    --output-root "$missing_fixture/output" \
    --qc-root "$missing_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$missing_fixture/step08_impl.R"
assert_contains "$test_root/missing-input.err" "Step 07 REV_like VCF for partition p2"
assert_not_exists "$missing_fixture/output"

printf 'Running Step 07 receipt/VCF dry-run preflight checks...\n'
canonical_fixture="$test_root/canonical-path"
create_fixture "$canonical_fixture" cohort_canonical
canonical_receipt="$canonical_fixture/step07/cohort_canonical/p1/cohort_canonical.p1.step07_outputs.tsv"
awk -F '\t' -v OFS='\t' -v root="$canonical_fixture" '
    NR > 1 {
        $6 = root "/step07/cohort_canonical/p1/../p1/cohort_canonical.p1." \
             $5 ".mpileup.vcf"
    }
    { print }
' "$canonical_receipt" >"$canonical_receipt.updated"
mv "$canonical_receipt.updated" "$canonical_receipt"
bash "$script" \
    --cohort-id cohort_canonical \
    --sample-manifest "$canonical_fixture/samples.tsv" \
    --partition-manifest "$canonical_fixture/partitions.tsv" \
    --step07-root "$canonical_fixture/step07" \
    --annotation-gtf "$canonical_fixture/annotation.gtf" \
    --output-root "$canonical_fixture/output" \
    --qc-root "$canonical_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$canonical_fixture/step08_impl.R" \
    >"$test_root/canonical-path.out"
assert_contains "$test_root/canonical-path.out" "Dry-run complete"
assert_not_exists "$canonical_fixture/output"

sample_order_fixture="$test_root/preflight-sample-order"
create_fixture "$sample_order_fixture" cohort_sample_order
sample_order_vcf="$sample_order_fixture/step07/cohort_sample_order/p1/cohort_sample_order.p1.FWD_like.mpileup.vcf"
awk -F '\t' -v OFS='\t' '
    /^#CHROM/ {
        $10 = "sample_B"
        $11 = "sample_A"
    }
    { print }
' "$sample_order_vcf" >"$sample_order_vcf.updated"
mv "$sample_order_vcf.updated" "$sample_order_vcf"
run_expect_failure \
    "$test_root/preflight-sample-order.out" \
    "$test_root/preflight-sample-order.err" \
    bash "$script" \
    --cohort-id cohort_sample_order \
    --sample-manifest "$sample_order_fixture/samples.tsv" \
    --partition-manifest "$sample_order_fixture/partitions.tsv" \
    --step07-root "$sample_order_fixture/step07" \
    --annotation-gtf "$sample_order_fixture/annotation.gtf" \
    --output-root "$sample_order_fixture/output" \
    --qc-root "$sample_order_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$sample_order_fixture/step08_impl.R"
assert_contains \
    "$test_root/preflight-sample-order.err" \
    "VCF header or sample order is invalid"

record_count_fixture="$test_root/preflight-record-count"
create_fixture "$record_count_fixture" cohort_record_count
record_count_receipt="$record_count_fixture/step07/cohort_record_count/p1/cohort_record_count.p1.step07_outputs.tsv"
awk -F '\t' -v OFS='\t' '
    NR == 2 { $10 = 2 }
    { print }
' "$record_count_receipt" >"$record_count_receipt.updated"
mv "$record_count_receipt.updated" "$record_count_receipt"
run_expect_failure \
    "$test_root/preflight-record-count.out" \
    "$test_root/preflight-record-count.err" \
    bash "$script" \
    --cohort-id cohort_record_count \
    --sample-manifest "$record_count_fixture/samples.tsv" \
    --partition-manifest "$record_count_fixture/partitions.tsv" \
    --step07-root "$record_count_fixture/step07" \
    --annotation-gtf "$record_count_fixture/annotation.gtf" \
    --output-root "$record_count_fixture/output" \
    --qc-root "$record_count_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$record_count_fixture/step08_impl.R"
assert_contains \
    "$test_root/preflight-record-count.err" \
    "VCF record count does not match its Step 07 receipt"

printf 'Running successful execute and receipt-last publication checks...\n'
execute_log="$test_root/execute-rscript.log"
mv_log="$test_root/execute-mv.log"
env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID=exec08 \
    FAKE_RSCRIPT_LOG="$execute_log" \
    FAKE_MV_LOG="$mv_log" \
    bash "$script" "${common_args[@]}" --execute >"$test_root/execute.out"

sites="$fixture/output/cohort_A/cohort_A.step08_sites.tsv"
inputs="$fixture/output/cohort_A/cohort_A.step08_inputs.tsv"
summary="$fixture/qc/cohort_A.step08_summary.tsv"
assert_exists "$sites"
assert_exists "$inputs"
assert_exists "$summary"
assert_contains "$execute_log" "$fixture/step08_impl.R"
assert_contains "$execute_log" "--sites-output"
assert_contains "$execute_log" "--inputs-output"
assert_contains "$execute_log" "--summary-output"
assert_contains "$(<"$sites")" $'DP__sample_A\tDP__sample_B\tAD__sample_A\tAD__sample_B\tAF__sample_A\tAF__sample_B'
[[ "$(awk 'END { print NR - 1 }' "$inputs")" == "4" ]] ||
    fail "Expected four manifest x orientation input rows"
[[ "$(awk 'END { print NR - 1 }' "$summary")" == "1" ]] ||
    fail "Expected one summary row"
inputs_header_observed="$(sed -n '1p' "$inputs")"
for omitted_identity in \
    rscript r_script r_package package_version \
    run_token attempt step08_sites_sha256 step08_summary_sha256
do
    assert_not_contains "$inputs_header_observed" "$omitted_identity"
done
assert_contains "$test_root/execute.out" "Step 08 execute complete"
assert_not_exists "$fixture/output/cohort_A/.cohort_A.step08.lock"
assert_no_step08_scratch "$fixture/output" "$fixture/qc"

publish_moves="$(tail -n 3 "$mv_log")"
publish_move_1="$(printf '%s\n' "$publish_moves" | sed -n '1p')"
publish_move_2="$(printf '%s\n' "$publish_moves" | sed -n '2p')"
publish_move_3="$(printf '%s\n' "$publish_moves" | sed -n '3p')"
assert_contains "$publish_move_1" "step08_sites.tsv"
assert_contains "$publish_move_2" "step08_summary.tsv"
assert_contains "$publish_move_3" "step08_inputs.tsv"

printf 'Running receipt-visible pre-commit transaction barrier check...\n'
barrier_fixture="$test_root/receipt-barrier"
barrier_marker="$test_root/receipt-barrier.marker"
barrier_release="$test_root/receipt-barrier.release"
create_fixture "$barrier_fixture" cohort_barrier
env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID=barrier08 \
    FAKE_MV_BARRIER_DEST_MATCH="cohort_barrier.step08_inputs.tsv" \
    FAKE_MV_BARRIER_MARKER="$barrier_marker" \
    FAKE_MV_BARRIER_RELEASE="$barrier_release" \
    bash "$script" \
    --cohort-id cohort_barrier \
    --sample-manifest "$barrier_fixture/samples.tsv" \
    --partition-manifest "$barrier_fixture/partitions.tsv" \
    --step07-root "$barrier_fixture/step07" \
    --annotation-gtf "$barrier_fixture/annotation.gtf" \
    --output-root "$barrier_fixture/output" \
    --qc-root "$barrier_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$barrier_fixture/step08_impl.R" \
    --execute >"$test_root/receipt-barrier.out" \
    2>"$test_root/receipt-barrier.err" &
barrier_pid=$!
barrier_seen=false
for _ in {1..500}; do
    if [[ -e "$barrier_marker" ]]; then
        barrier_seen=true
        break
    fi
    if ! kill -0 "$barrier_pid" 2>/dev/null; then
        break
    fi
    sleep 0.01
done
if [[ "$barrier_seen" != true ]]; then
    : >"$barrier_release"
    wait "$barrier_pid" 2>/dev/null || true
    fail "Receipt-publication barrier was not reached"
fi
barrier_state_error=""
[[ -s "$barrier_fixture/output/cohort_barrier/cohort_barrier.step08_sites.tsv" ]] ||
    barrier_state_error="sites table was not visible at receipt barrier"
[[ -s "$barrier_fixture/qc/cohort_barrier.step08_summary.tsv" ]] ||
    barrier_state_error="summary was not visible at receipt barrier"
[[ -s "$barrier_fixture/output/cohort_barrier/cohort_barrier.step08_inputs.tsv" ]] ||
    barrier_state_error="input receipt was not visible at receipt barrier"
[[ -d "$barrier_fixture/output/cohort_barrier/.cohort_barrier.step08.lock" ]] ||
    barrier_state_error="cohort lock was not held at receipt barrier"
: >"$barrier_release"
wait "$barrier_pid" || fail "Barrier-controlled Step 08 execution failed"
[[ -z "$barrier_state_error" ]] || fail "$barrier_state_error"
assert_contains "$test_root/receipt-barrier.out" "Step 08 execute complete"
assert_not_exists \
    "$barrier_fixture/output/cohort_barrier/.cohort_barrier.step08.lock"
assert_no_step08_scratch "$barrier_fixture/output" "$barrier_fixture/qc"

printf 'Running header-only candidate-table success check...\n'
header_fixture="$test_root/header-only"
create_fixture "$header_fixture" cohort_header
env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID=header08 \
    FAKE_RSCRIPT_HEADER_ONLY=1 \
    bash "$script" \
    --cohort-id cohort_header \
    --sample-manifest "$header_fixture/samples.tsv" \
    --partition-manifest "$header_fixture/partitions.tsv" \
    --step07-root "$header_fixture/step07" \
    --annotation-gtf "$header_fixture/annotation.gtf" \
    --output-root "$header_fixture/output" \
    --qc-root "$header_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$header_fixture/step08_impl.R" \
    --execute >/dev/null
[[ "$(awk 'END { print NR }' "$header_fixture/output/cohort_header/cohort_header.step08_sites.tsv")" == "1" ]] ||
    fail "Header-only sites table should be accepted"

printf 'Running R failure and owned cleanup check...\n'
failure_fixture="$test_root/r-failure"
create_fixture "$failure_fixture" cohort_failure
run_expect_failure "$test_root/r-failure.out" "$test_root/r-failure.err" \
    env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID=fail08 \
    FAKE_RSCRIPT_FAIL=1 \
    bash "$script" \
    --cohort-id cohort_failure \
    --sample-manifest "$failure_fixture/samples.tsv" \
    --partition-manifest "$failure_fixture/partitions.tsv" \
    --step07-root "$failure_fixture/step07" \
    --annotation-gtf "$failure_fixture/annotation.gtf" \
    --output-root "$failure_fixture/output" \
    --qc-root "$failure_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$failure_fixture/step08_impl.R" \
    --execute
assert_contains "$test_root/r-failure.err" "Step 08 R VCF preprocessing failed"
assert_not_exists "$failure_fixture/output/cohort_failure/cohort_failure.step08_sites.tsv"
assert_not_exists "$failure_fixture/output/cohort_failure/.cohort_failure.step08.lock"
assert_no_step08_scratch "$failure_fixture/output" "$failure_fixture/qc"

printf 'Running malformed/missing R output checks...\n'
malformed_fixture="$test_root/malformed"
create_fixture "$malformed_fixture" cohort_malformed
run_expect_failure "$test_root/malformed.out" "$test_root/malformed.err" \
    env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID=bad08 \
    FAKE_RSCRIPT_BAD_HEADER=inputs \
    bash "$script" \
    --cohort-id cohort_malformed \
    --sample-manifest "$malformed_fixture/samples.tsv" \
    --partition-manifest "$malformed_fixture/partitions.tsv" \
    --step07-root "$malformed_fixture/step07" \
    --annotation-gtf "$malformed_fixture/annotation.gtf" \
    --output-root "$malformed_fixture/output" \
    --qc-root "$malformed_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$malformed_fixture/step08_impl.R" \
    --execute
assert_contains "$test_root/malformed.err" "input receipt header is invalid"
assert_no_step08_scratch "$malformed_fixture/output" "$malformed_fixture/qc"

omit_fixture="$test_root/omit"
create_fixture "$omit_fixture" cohort_omit
run_expect_failure "$test_root/omit.out" "$test_root/omit.err" \
    env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID=omit08 \
    FAKE_RSCRIPT_OMIT_OUTPUT=summary \
    bash "$script" \
    --cohort-id cohort_omit \
    --sample-manifest "$omit_fixture/samples.tsv" \
    --partition-manifest "$omit_fixture/partitions.tsv" \
    --step07-root "$omit_fixture/step07" \
    --annotation-gtf "$omit_fixture/annotation.gtf" \
    --output-root "$omit_fixture/output" \
    --qc-root "$omit_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$omit_fixture/step08_impl.R" \
    --execute
assert_contains "$test_root/omit.err" "Step 08 summary does not exist or is empty"
assert_no_step08_scratch "$omit_fixture/output" "$omit_fixture/qc"

printf 'Running output reconciliation, path, hash, order, and uniqueness checks...\n'
run_invalid_fake_output_case \
    bad-hash \
    FAKE_RSCRIPT_BAD_INPUT_HASH=1 \
    "stale or invalid Step 07 hash"
run_invalid_fake_output_case \
    bad-path \
    FAKE_RSCRIPT_BAD_INPUT_PATH=1 \
    "unexpected Step 07 path"
run_invalid_fake_output_case \
    bad-order \
    FAKE_RSCRIPT_BAD_INPUT_ORDER=1 \
    "does not match manifest partition/orientation order"
run_invalid_fake_output_case \
    bad-reconciliation \
    FAKE_RSCRIPT_BAD_RECONCILIATION=1 \
    "does not reconcile expanded, supported, and skipped allele counts"
run_invalid_fake_output_case \
    bad-summary \
    FAKE_RSCRIPT_BAD_SUMMARY=1 \
    "summary does not exactly reconcile"
run_invalid_fake_output_case \
    duplicate-candidate \
    FAKE_RSCRIPT_DUPLICATE_CANDIDATE=1 \
    "duplicate candidate ID"
run_invalid_fake_output_case \
    extra-field \
    FAKE_RSCRIPT_EXTRA_INPUT_FIELD=1 \
    "invalid field count"

printf 'Running admitted-input mutation checks...\n'
run_detected_input_mutation_case \
    sample-mutation \
    sample \
    "Sample manifest changed during Step 08"
run_detected_input_mutation_case \
    partition-mutation \
    partition \
    "Partition manifest changed during Step 08"
run_detected_input_mutation_case \
    annotation-mutation \
    annotation \
    "Annotation GTF changed during Step 08"
run_detected_input_mutation_case \
    receipt-mutation \
    receipt \
    "Step 07 receipt changed during Step 08"
run_detected_input_mutation_case \
    vcf-mutation \
    vcf \
    "Step 07 VCF changed during Step 08"

printf 'Running untracked R-program mutation characterization...\n'
r_program_mutation_fixture="$test_root/r-program-mutation"
create_fixture "$r_program_mutation_fixture" cohort_r_program_mutation
mkdir -p "$r_program_mutation_fixture/output" "$r_program_mutation_fixture/qc"
printf 'unrelated output bytes\n' >"$r_program_mutation_fixture/output/unrelated.txt"
printf 'unrelated QC bytes\n' >"$r_program_mutation_fixture/qc/unrelated.txt"
env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID=rprogrammutate08 \
    FAKE_RSCRIPT_MUTATE=r_script \
    bash "$script" \
    --cohort-id cohort_r_program_mutation \
    --sample-manifest "$r_program_mutation_fixture/samples.tsv" \
    --partition-manifest "$r_program_mutation_fixture/partitions.tsv" \
    --step07-root "$r_program_mutation_fixture/step07" \
    --annotation-gtf "$r_program_mutation_fixture/annotation.gtf" \
    --output-root "$r_program_mutation_fixture/output" \
    --qc-root "$r_program_mutation_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$r_program_mutation_fixture/step08_impl.R" \
    --execute >"$test_root/r-program-mutation.out"
assert_contains "$test_root/r-program-mutation.out" "Step 08 execute complete"
assert_contains \
    "$r_program_mutation_fixture/step08_impl.R" \
    "changed while fake R was running"
assert_exists \
    "$r_program_mutation_fixture/output/cohort_r_program_mutation/cohort_r_program_mutation.step08_sites.tsv"
assert_exists \
    "$r_program_mutation_fixture/output/cohort_r_program_mutation/cohort_r_program_mutation.step08_inputs.tsv"
assert_exists \
    "$r_program_mutation_fixture/qc/cohort_r_program_mutation.step08_summary.tsv"
assert_file_equals \
    "$r_program_mutation_fixture/output/unrelated.txt" \
    "unrelated output bytes"
assert_file_equals \
    "$r_program_mutation_fixture/qc/unrelated.txt" \
    "unrelated QC bytes"
assert_no_step08_scratch \
    "$r_program_mutation_fixture/output" \
    "$r_program_mutation_fixture/qc"

printf 'Running foreign lock preservation check...\n'
lock_fixture="$test_root/foreign-lock"
create_fixture "$lock_fixture" cohort_lock
lock_dir="$lock_fixture/output/cohort_lock/.cohort_lock.step08.lock"
mkdir -p "$lock_dir"
printf 'foreign owner\n' >"$lock_dir/owner"
run_expect_failure "$test_root/lock.out" "$test_root/lock.err" \
    env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID=lock08 \
    bash "$script" \
    --cohort-id cohort_lock \
    --sample-manifest "$lock_fixture/samples.tsv" \
    --partition-manifest "$lock_fixture/partitions.tsv" \
    --step07-root "$lock_fixture/step07" \
    --annotation-gtf "$lock_fixture/annotation.gtf" \
    --output-root "$lock_fixture/output" \
    --qc-root "$lock_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$lock_fixture/step08_impl.R" \
    --execute
assert_contains "$test_root/lock.err" "Step 08 lock already exists"
assert_file_equals "$lock_dir/owner" "foreign owner"

printf 'Running stale run-token path preservation check...\n'
stale_fixture="$test_root/stale"
create_fixture "$stale_fixture" cohort_stale
stale_dir="$stale_fixture/output/cohort_stale"
mkdir -p "$stale_dir"
stale_path="$stale_dir/.cohort_stale.step08.stale08.sites.tmp.tsv"
printf 'foreign scratch\n' >"$stale_path"
run_expect_failure "$test_root/stale.out" "$test_root/stale.err" \
    env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID=stale08 \
    bash "$script" \
    --cohort-id cohort_stale \
    --sample-manifest "$stale_fixture/samples.tsv" \
    --partition-manifest "$stale_fixture/partitions.tsv" \
    --step07-root "$stale_fixture/step07" \
    --annotation-gtf "$stale_fixture/annotation.gtf" \
    --output-root "$stale_fixture/output" \
    --qc-root "$stale_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$stale_fixture/step08_impl.R" \
    --execute
assert_contains "$test_root/stale.err" "Refusing to reuse an existing Step 08 scratch path"
assert_file_equals "$stale_path" "foreign scratch"
assert_not_exists "$stale_dir/.cohort_stale.step08.lock"

printf 'Running incomplete stable output-set check...\n'
partial_fixture="$test_root/partial"
create_fixture "$partial_fixture" cohort_partial
partial_dir="$partial_fixture/output/cohort_partial"
mkdir -p "$partial_dir"
printf 'existing sites\n' >"$partial_dir/cohort_partial.step08_sites.tsv"
run_expect_failure "$test_root/partial.out" "$test_root/partial.err" \
    env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID=partial08 \
    bash "$script" \
    --cohort-id cohort_partial \
    --sample-manifest "$partial_fixture/samples.tsv" \
    --partition-manifest "$partial_fixture/partitions.tsv" \
    --step07-root "$partial_fixture/step07" \
    --annotation-gtf "$partial_fixture/annotation.gtf" \
    --output-root "$partial_fixture/output" \
    --qc-root "$partial_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$partial_fixture/step08_impl.R" \
    --execute
assert_contains "$test_root/partial.err" "outputs are incomplete"
assert_file_equals "$partial_dir/cohort_partial.step08_sites.tsv" "existing sites"

printf 'Running rollback of a previous complete output set...\n'
rollback_fixture="$test_root/rollback"
create_fixture "$rollback_fixture" cohort_rollback
rollback_dir="$rollback_fixture/output/cohort_rollback"
rollback_qc="$rollback_fixture/qc"
mkdir -p "$rollback_dir" "$rollback_qc"
printf 'previous sites\n' >"$rollback_dir/cohort_rollback.step08_sites.tsv"
printf 'previous inputs\n' >"$rollback_dir/cohort_rollback.step08_inputs.tsv"
printf 'previous summary\n' >"$rollback_qc/cohort_rollback.step08_summary.tsv"
run_expect_failure "$test_root/rollback.out" "$test_root/rollback.err" \
    env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID=rollback08 \
    FAKE_MV_FAIL_ONCE_DEST_MATCH="cohort_rollback.step08_summary.tsv" \
    FAKE_MV_FAIL_MARKER="$test_root/rollback-fail.marker" \
    bash "$script" \
    --cohort-id cohort_rollback \
    --sample-manifest "$rollback_fixture/samples.tsv" \
    --partition-manifest "$rollback_fixture/partitions.tsv" \
    --step07-root "$rollback_fixture/step07" \
    --annotation-gtf "$rollback_fixture/annotation.gtf" \
    --output-root "$rollback_fixture/output" \
    --qc-root "$rollback_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$rollback_fixture/step08_impl.R" \
    --execute
assert_file_equals "$rollback_dir/cohort_rollback.step08_sites.tsv" "previous sites"
assert_file_equals "$rollback_dir/cohort_rollback.step08_inputs.tsv" "previous inputs"
assert_file_equals "$rollback_qc/cohort_rollback.step08_summary.tsv" "previous summary"
assert_not_exists "$rollback_dir/.cohort_rollback.step08.lock"
assert_no_step08_scratch "$rollback_fixture/output" "$rollback_fixture/qc"

printf 'Running receipt-publication plus sites-restoration failure check...\n'
restore_failure_fixture="$test_root/restore-failure"
create_fixture "$restore_failure_fixture" cohort_restore_failure
restore_failure_dir="$restore_failure_fixture/output/cohort_restore_failure"
restore_failure_qc="$restore_failure_fixture/qc"
restore_failure_token=restorefail08
restore_failure_receipt_marker="$test_root/restore-failure-receipt.marker"
restore_failure_sites_marker="$test_root/restore-failure-sites.marker"
mkdir -p "$restore_failure_dir" "$restore_failure_qc"
printf 'previous sites\n' >"$restore_failure_dir/cohort_restore_failure.step08_sites.tsv"
printf 'previous inputs\n' >"$restore_failure_dir/cohort_restore_failure.step08_inputs.tsv"
printf 'previous summary\n' >"$restore_failure_qc/cohort_restore_failure.step08_summary.tsv"
printf 'unrelated output bytes\n' >"$restore_failure_fixture/output/unrelated.txt"
printf 'unrelated QC bytes\n' >"$restore_failure_qc/unrelated.txt"
set +e
env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID="$restore_failure_token" \
    FAKE_MV_RECEIPT_FAIL_DEST_MATCH="cohort_restore_failure.step08_inputs.tsv" \
    FAKE_MV_RECEIPT_FAIL_MARKER="$restore_failure_receipt_marker" \
    FAKE_MV_SITES_RESTORE_FAIL_DEST_MATCH="cohort_restore_failure.step08_sites.tsv" \
    FAKE_MV_SITES_RESTORE_FAIL_MARKER="$restore_failure_sites_marker" \
    bash "$script" \
    --cohort-id cohort_restore_failure \
    --sample-manifest "$restore_failure_fixture/samples.tsv" \
    --partition-manifest "$restore_failure_fixture/partitions.tsv" \
    --step07-root "$restore_failure_fixture/step07" \
    --annotation-gtf "$restore_failure_fixture/annotation.gtf" \
    --output-root "$restore_failure_fixture/output" \
    --qc-root "$restore_failure_qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$restore_failure_fixture/step08_impl.R" \
    --execute >"$test_root/restore-failure.out" \
    2>"$test_root/restore-failure.err"
restore_failure_status=$?
set -e
[[ "$restore_failure_status" -eq 67 ]] ||
    fail "Expected receipt publication exit 67; got $restore_failure_status"
[[ -e "$restore_failure_receipt_marker" ]] ||
    fail "Receipt-publication failure marker was not created"
[[ -e "$restore_failure_sites_marker" ]] ||
    fail "Sites-restoration failure marker was not created"
assert_not_exists \
    "$restore_failure_dir/cohort_restore_failure.step08_sites.tsv"
assert_file_equals \
    "$restore_failure_dir/cohort_restore_failure.step08_inputs.tsv" \
    "previous inputs"
assert_file_equals \
    "$restore_failure_qc/cohort_restore_failure.step08_summary.tsv" \
    "previous summary"
restore_failure_sites_backup="$restore_failure_dir/.cohort_restore_failure.step08.$restore_failure_token.previous.sites.tsv"
assert_file_equals "$restore_failure_sites_backup" "previous sites"
assert_not_exists \
    "$restore_failure_dir/.cohort_restore_failure.step08.$restore_failure_token.previous.inputs.tsv"
assert_not_exists \
    "$restore_failure_qc/.cohort_restore_failure.step08.$restore_failure_token.previous.summary.tsv"
assert_not_exists \
    "$restore_failure_dir/.cohort_restore_failure.step08.$restore_failure_token.sites.tmp.tsv"
assert_not_exists \
    "$restore_failure_dir/.cohort_restore_failure.step08.$restore_failure_token.inputs.tmp.tsv"
assert_not_exists \
    "$restore_failure_qc/.cohort_restore_failure.step08.$restore_failure_token.summary.tmp.tsv"
assert_not_exists \
    "$restore_failure_dir/.cohort_restore_failure.step08.lock"
assert_file_equals \
    "$restore_failure_fixture/output/unrelated.txt" \
    "unrelated output bytes"
assert_file_equals \
    "$restore_failure_qc/unrelated.txt" \
    "unrelated QC bytes"
unexpected_restore_scratch="$(
    find "$restore_failure_fixture/output" "$restore_failure_qc" \
        -name '.*.step08.*' \
        ! -path "$restore_failure_sites_backup" \
        -print -quit
)"
[[ -z "$unexpected_restore_scratch" ]] ||
    fail "Unexpected Step 08 residue after restoration failure: $unexpected_restore_scratch"
assert_no_step08_recovery_marker \
    "$restore_failure_fixture/output" \
    "$restore_failure_qc"

printf 'Running successful replacement of a previous complete output set...\n'
replace_fixture="$test_root/replace"
create_fixture "$replace_fixture" cohort_replace
replace_dir="$replace_fixture/output/cohort_replace"
replace_qc="$replace_fixture/qc"
mkdir -p "$replace_dir" "$replace_qc"
printf 'previous sites\n' >"$replace_dir/cohort_replace.step08_sites.tsv"
printf 'previous inputs\n' >"$replace_dir/cohort_replace.step08_inputs.tsv"
printf 'previous summary\n' >"$replace_qc/cohort_replace.step08_summary.tsv"
env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID=replace08 \
    bash "$script" \
    --cohort-id cohort_replace \
    --sample-manifest "$replace_fixture/samples.tsv" \
    --partition-manifest "$replace_fixture/partitions.tsv" \
    --step07-root "$replace_fixture/step07" \
    --annotation-gtf "$replace_fixture/annotation.gtf" \
    --output-root "$replace_fixture/output" \
    --qc-root "$replace_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$replace_fixture/step08_impl.R" \
    --execute >/dev/null
assert_exists "$replace_dir/cohort_replace.step08_sites.tsv"
assert_exists "$replace_dir/cohort_replace.step08_inputs.tsv"
assert_exists "$replace_qc/cohort_replace.step08_summary.tsv"
assert_not_contains \
    "$replace_dir/cohort_replace.step08_sites.tsv" \
    "previous sites"
assert_not_contains \
    "$replace_dir/cohort_replace.step08_inputs.tsv" \
    "previous inputs"
assert_not_contains \
    "$replace_qc/cohort_replace.step08_summary.tsv" \
    "previous summary"
assert_no_step08_scratch "$replace_fixture/output" "$replace_fixture/qc"

printf 'Running rollback after post-publication validation failure...\n'
post_validation_fixture="$test_root/post-validation"
create_fixture "$post_validation_fixture" cohort_post
post_validation_dir="$post_validation_fixture/output/cohort_post"
post_validation_qc="$post_validation_fixture/qc"
mkdir -p "$post_validation_dir" "$post_validation_qc"
printf 'previous sites\n' >"$post_validation_dir/cohort_post.step08_sites.tsv"
printf 'previous inputs\n' >"$post_validation_dir/cohort_post.step08_inputs.tsv"
printf 'previous summary\n' >"$post_validation_qc/cohort_post.step08_summary.tsv"
run_expect_failure \
    "$test_root/post-validation.out" \
    "$test_root/post-validation.err" \
    env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID=postvalidate08 \
    FAKE_MV_CORRUPT_ONCE_DEST_MATCH="cohort_post.step08_summary.tsv" \
    FAKE_MV_CORRUPT_MARKER="$test_root/post-validation-corrupt.marker" \
    bash "$script" \
    --cohort-id cohort_post \
    --sample-manifest "$post_validation_fixture/samples.tsv" \
    --partition-manifest "$post_validation_fixture/partitions.tsv" \
    --step07-root "$post_validation_fixture/step07" \
    --annotation-gtf "$post_validation_fixture/annotation.gtf" \
    --output-root "$post_validation_fixture/output" \
    --qc-root "$post_validation_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$post_validation_fixture/step08_impl.R" \
    --execute
assert_contains \
    "$test_root/post-validation.err" \
    "Step 08 summary header is invalid"
assert_file_equals \
    "$post_validation_dir/cohort_post.step08_sites.tsv" \
    "previous sites"
assert_file_equals \
    "$post_validation_dir/cohort_post.step08_inputs.tsv" \
    "previous inputs"
assert_file_equals \
    "$post_validation_qc/cohort_post.step08_summary.tsv" \
    "previous summary"
assert_not_exists "$post_validation_dir/.cohort_post.step08.lock"
assert_no_step08_scratch \
    "$post_validation_fixture/output" \
    "$post_validation_fixture/qc"

printf 'Running first-publication partial cleanup check...\n'
first_failure_fixture="$test_root/first-failure"
create_fixture "$first_failure_fixture" cohort_first
run_expect_failure "$test_root/first-failure.out" "$test_root/first-failure.err" \
    env \
    PATH="$fake_bin:$PATH" \
    SLURM_JOB_ID=first08 \
    FAKE_MV_FAIL_ONCE_DEST_MATCH="cohort_first.step08_summary.tsv" \
    FAKE_MV_FAIL_MARKER="$test_root/first-fail.marker" \
    bash "$script" \
    --cohort-id cohort_first \
    --sample-manifest "$first_failure_fixture/samples.tsv" \
    --partition-manifest "$first_failure_fixture/partitions.tsv" \
    --step07-root "$first_failure_fixture/step07" \
    --annotation-gtf "$first_failure_fixture/annotation.gtf" \
    --output-root "$first_failure_fixture/output" \
    --qc-root "$first_failure_fixture/qc" \
    --rscript-bin "$fake_rscript" \
    --r-script "$first_failure_fixture/step08_impl.R" \
    --execute
assert_not_exists "$first_failure_fixture/output/cohort_first/cohort_first.step08_sites.tsv"
assert_not_exists "$first_failure_fixture/output/cohort_first/cohort_first.step08_inputs.tsv"
assert_not_exists "$first_failure_fixture/qc/cohort_first.step08_summary.tsv"
assert_no_step08_scratch "$first_failure_fixture/output" "$first_failure_fixture/qc"

printf 'Running Step 08 SLURM wrapper checks...\n'
wrapper_dry="$test_root/wrapper-dry"
mkdir -p "$wrapper_dry/scripts"
cp "$script" "$wrapper_dry/scripts/"
env \
    PATH="$fake_bin:$PATH" \
    SLURM_SUBMIT_DIR="$wrapper_dry" \
    EXECUTE=0 \
    COHORT_ID=cohort_A \
    SAMPLE_MANIFEST="$fixture/samples.tsv" \
    PARTITION_MANIFEST="$fixture/partitions.tsv" \
    STEP07_ROOT="$fixture/step07" \
    ANNOTATION_GTF="$fixture/annotation.gtf" \
    OUTPUT_ROOT="$wrapper_dry/output" \
    QC_ROOT="$wrapper_dry/qc" \
    RSCRIPT_BIN_OVERRIDE="$fake_rscript" \
    STEP08_R_SCRIPT="$fixture/step08_impl.R" \
    bash "$job" >"$test_root/wrapper-dry.out"
assert_contains "$test_root/wrapper-dry.out" "Execute mode: 0"
assert_contains "$test_root/wrapper-dry.out" "Step 08 completed in dry-run mode"
assert_not_exists "$wrapper_dry/output"
assert_not_exists "$wrapper_dry/qc"

wrapper_execute="$test_root/wrapper-execute"
mkdir -p "$wrapper_execute/scripts"
cp "$script" "$wrapper_execute/scripts/"
env \
    PATH="$fake_bin:$PATH" \
    SLURM_SUBMIT_DIR="$wrapper_execute" \
    SLURM_JOB_ID=wrapper08 \
    EXECUTE=1 \
    COHORT_ID=cohort_A \
    SAMPLE_MANIFEST="$fixture/samples.tsv" \
    PARTITION_MANIFEST="$fixture/partitions.tsv" \
    STEP07_ROOT="$fixture/step07" \
    ANNOTATION_GTF="$fixture/annotation.gtf" \
    OUTPUT_ROOT="$wrapper_execute/output" \
    QC_ROOT="$wrapper_execute/qc" \
    RSCRIPT_BIN_OVERRIDE="$fake_rscript" \
    STEP08_R_SCRIPT="$fixture/step08_impl.R" \
    bash "$job" >"$test_root/wrapper-execute.out"
assert_contains "$test_root/wrapper-execute.out" "Validated Step 08 VCF preprocessing outputs"
assert_exists "$wrapper_execute/output/cohort_A/cohort_A.step08_sites.tsv"
assert_exists "$wrapper_execute/output/cohort_A/cohort_A.step08_inputs.tsv"
assert_exists "$wrapper_execute/qc/cohort_A.step08_summary.tsv"

invalid_wrapper="$test_root/wrapper-invalid"
mkdir -p "$invalid_wrapper"
run_expect_failure "$test_root/wrapper-invalid.out" "$test_root/wrapper-invalid.err" \
    env \
    PATH="$fake_bin:$PATH" \
    SLURM_SUBMIT_DIR="$invalid_wrapper" \
    EXECUTE=2 \
    bash "$job"
assert_contains "$test_root/wrapper-invalid.err" "EXECUTE must be 0 or 1"
assert_not_exists "$invalid_wrapper/logs"

wrapper_missing="$test_root/wrapper-missing"
mkdir -p "$wrapper_missing/scripts"
cat >"$wrapper_missing/scripts/step_08_vcf_preprocessing.sh" <<'WRAPPER_STUB'
#!/usr/bin/env bash
exit 0
WRAPPER_STUB
run_expect_failure "$test_root/wrapper-missing.out" "$test_root/wrapper-missing.err" \
    env \
    PATH="$fake_bin:$PATH" \
    SLURM_SUBMIT_DIR="$wrapper_missing" \
    EXECUTE=1 \
    COHORT_ID=cohort_missing_wrapper \
    OUTPUT_ROOT="$wrapper_missing/output" \
    QC_ROOT="$wrapper_missing/qc" \
    RSCRIPT_BIN_OVERRIDE="$fake_rscript" \
    STEP08_R_SCRIPT="$fixture/step08_impl.R" \
    bash "$job"
assert_contains "$test_root/wrapper-missing.err" "Expected Step 08 sites table does not exist or is empty"

printf 'PASS: Step 08 VCF preprocessing shell tests\n'
