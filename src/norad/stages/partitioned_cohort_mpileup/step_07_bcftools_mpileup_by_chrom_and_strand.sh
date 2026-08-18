#!/usr/bin/env bash
# Step 07: run cohort-wide bcftools mpileup for one declared genomic partition.
#
# Dry-run mode validates all existing inputs and prints the exact FWD_like and
# REV_like pipelines, validation checks, and publication actions without
# creating output directories, locks, temporary files, VCFs, or receipts.
# Passing --execute runs both pipelines and publishes the two VCFs plus their
# receipt as one rollback-protected output set.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  src/norad/stages/partitioned_cohort_mpileup/step_07_bcftools_mpileup_by_chrom_and_strand.sh \
    --cohort-id COHORT_ID \
    --sample-manifest SAMPLE_MANIFEST \
    --partition-manifest PARTITION_MANIFEST \
    --partition-id PARTITION_ID \
    --orientation-root ORIENTATION_ROOT \
    --reference-fasta REFERENCE_FASTA \
    --output-root OUTPUT_ROOT \
    [--bcftools-bin BCFTOOLS_BIN] \
    [--max-depth MAX_DEPTH] \
    [--filter-expression EXPRESSION] \
    [--no-clobber] \
    [--execute]

Run a multi-sample mpileup for every sample in the canonical TSV sample
manifest. One invocation selects one row from the partition manifest and
produces both FWD_like and REV_like cohort VCFs.

Required arguments:
  --cohort-id          Filename-safe cohort identifier.
  --sample-manifest    TSV containing a unique, non-empty sample_id column.
  --partition-manifest TSV with partition_id, selector_type, selector_value.
  --partition-id       Filename-safe partition row to execute.
  --orientation-root   Root containing Step 06 per-sample orientation BAMs.
  --reference-fasta    Reference FASTA; <path>.fai must also exist.
  --output-root        Root for cohort/partition Step 07 outputs.

Partition selectors:
  selector_type=region       passes selector_value to bcftools mpileup -r
  selector_type=regions_file passes selector_value to bcftools mpileup -R
                             Relative files resolve from the manifest directory.

Options:
  --bcftools-bin       Executable/path. Resolution order: argument,
                      BCFTOOLS_BIN_OVERRIDE, PATH.
  --max-depth          Per-input-file mpileup depth cap (default: 10000000).
  --filter-expression  bcftools include expression (default:
                      INFO/AD[1-]>2 & MAX(FORMAT/DP)>20).
  --no-clobber         Refuse to replace an existing complete output set.
  --execute            Run bcftools and publish validated outputs.
  -h, --help           Show this help message and exit.

Dry-run is the default and writes nothing.

FWD_like and REV_like remain mechanical read-orientation labels. Step 07 does
not assign transcript strand or biological sense/antisense meaning.
USAGE
}

# shellcheck source=../../libraries/executable_resolution.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/executable_resolution.sh"
# shellcheck source=../../libraries/file_checks.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/file_checks.sh"
# shellcheck source=../../libraries/orientation.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/orientation.sh"
# shellcheck source=../../libraries/argument_parsing.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/argument_parsing.sh"
# shellcheck source=../../libraries/signal_traps.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/signal_traps.sh"

confirm_input_manifest_hashes() {
    local current_sample_hash
    local current_partition_hash

    current_sample_hash="$(sha256_file "$sample_manifest")"
    current_partition_hash="$(sha256_file "$partition_manifest")"
    [[ "$current_sample_hash" == "$sample_manifest_sha256" ]] ||
        die "Sample manifest changed during Step 07: $sample_manifest"
    [[ "$current_partition_hash" == "$partition_manifest_sha256" ]] ||
        die "Partition manifest changed during Step 07: $partition_manifest"
}

capture_no_clobber_scientific_input() {
    local label="$1"
    local path="$2"
    local digest

    validate_nonempty_file "$label" "$path"
    if ! digest="$(sha256_file "$path")"; then
        die "Could not hash $label before Step 07 execution: $path"
    fi
    scientific_input_labels+=("$label")
    scientific_input_paths+=("$path")
    scientific_input_sha256+=("$digest")
}

capture_no_clobber_scientific_inputs() {
    local index

    [[ "$no_clobber" == true ]] || return 0

    scientific_input_labels=()
    scientific_input_paths=()
    scientific_input_sha256=()

    capture_no_clobber_scientific_input "Sample manifest" "$sample_manifest"
    capture_no_clobber_scientific_input "Partition manifest" "$partition_manifest"
    capture_no_clobber_scientific_input "Reference FASTA" "$reference_fasta"
    capture_no_clobber_scientific_input \
        "Reference FASTA index" "$reference_fasta.fai"
    if [[ "$selector_type" == "regions_file" ]]; then
        capture_no_clobber_scientific_input \
            "Regions file for partition $partition_id" "$selector_resolved"
    fi
    for index in "${!sample_ids[@]}"; do
        capture_no_clobber_scientific_input \
            "${ORIENTATIONS[0]} BAM for ${sample_ids[$index]}" \
            "${fwd_bams[$index]}"
        capture_no_clobber_scientific_input \
            "${ORIENTATIONS[0]} BAI for ${sample_ids[$index]}" \
            "${fwd_bams[$index]}.bai"
        capture_no_clobber_scientific_input \
            "${ORIENTATIONS[1]} BAM for ${sample_ids[$index]}" \
            "${rev_bams[$index]}"
        capture_no_clobber_scientific_input \
            "${ORIENTATIONS[1]} BAI for ${sample_ids[$index]}" \
            "${rev_bams[$index]}.bai"
    done

    scientific_input_expected_count=$((4 + 4 * ${#sample_ids[@]}))
    if [[ "$selector_type" == "regions_file" ]]; then
        scientific_input_expected_count=$((scientific_input_expected_count + 1))
    fi
    [[ "${#scientific_input_paths[@]}" -eq "$scientific_input_expected_count" ]] ||
        die "Internal error: Step 07 scientific-input membership snapshot is incomplete."
}

confirm_no_clobber_scientific_inputs() {
    local current_sha256
    local index

    [[ "$no_clobber" == true ]] || return 0
    [[ "${#scientific_input_labels[@]}" -eq "$scientific_input_expected_count" &&
       "${#scientific_input_paths[@]}" -eq "$scientific_input_expected_count" &&
       "${#scientific_input_sha256[@]}" -eq "$scientific_input_expected_count" ]] ||
        die "Internal error: Step 07 scientific-input membership changed during execution."

    for index in "${!scientific_input_paths[@]}"; do
        validate_nonempty_file \
            "${scientific_input_labels[$index]}" \
            "${scientific_input_paths[$index]}"
        if ! current_sha256="$(sha256_file "${scientific_input_paths[$index]}")"; then
            die "Could not rehash ${scientific_input_labels[$index]} during Step 07: ${scientific_input_paths[$index]}"
        fi
        [[ "$current_sha256" == "${scientific_input_sha256[$index]}" ]] ||
            die "${scientific_input_labels[$index]} changed during Step 07 --no-clobber execution: ${scientific_input_paths[$index]}"
    done
}

validate_fai_structure() {
    local fai="$1"
    awk -F '\t' '
        NF < 2 || $1 == "" || $2 !~ /^[1-9][0-9]*$/ {
            printf "invalid FASTA index row %d\n", NR > "/dev/stderr"
            invalid = 1
            next
        }
        seen[$1]++ {
            printf "duplicate FASTA index contig on row %d: %s\n", NR, $1 > "/dev/stderr"
            invalid = 1
        }
        END {
            if (!NR) {
                print "FASTA index contains no contig rows" > "/dev/stderr"
                invalid = 1
            }
            exit invalid
        }
    ' "$fai" || die "Reference FASTA index validation failed: $fai"
}

fai_contig_length() {
    local fai="$1"
    local contig="$2"
    awk -F '\t' -v contig="$contig" '
        $1 == contig {
            count++
            length_value = $2
        }
        END {
            if (count != 1 || length_value !~ /^[1-9][0-9]*$/) exit 1
            print length_value
        }
    ' "$fai"
}

validate_region_selector() {
    local selector="$1"
    local fai="$2"
    local region
    local contig
    local coordinates
    local contig_length
    local start
    local end
    local regions=()

    if [[ -z "$selector" ||
          "$selector" == ,* ||
          "$selector" == *, ||
          "$selector" == *,,* ]]; then
        die "Region selector contains an empty region: $selector"
    fi
    IFS=',' read -r -a regions <<< "$selector"
    [[ "${#regions[@]}" -gt 0 ]] || die "Region selector is empty."

    for region in "${regions[@]}"; do
        [[ -n "$region" ]] || die "Region selector contains an empty region: $selector"
        contig="${region%%:*}"
        [[ -n "$contig" ]] || die "Region selector contains an empty contig: $region"
        if ! contig_length="$(fai_contig_length "$fai" "$contig")"; then
            die "Region selector contig is absent or duplicated in the FASTA index: $contig"
        fi

        if [[ "$region" != *:* ]]; then
            continue
        fi

        coordinates="${region#*:}"
        if [[ "$coordinates" =~ ^[0-9]+$ ]]; then
            start="$coordinates"
            end="$coordinates"
        elif [[ "$coordinates" =~ ^([0-9]+)-([0-9]+)$ ]]; then
            start="${BASH_REMATCH[1]}"
            end="${BASH_REMATCH[2]}"
        elif [[ "$coordinates" =~ ^([0-9]+)-$ ]]; then
            start="${BASH_REMATCH[1]}"
            end="$contig_length"
        else
            die "Region selector has invalid coordinates: $region"
        fi

        if ! awk -v start="$start" -v end="$end" -v length_value="$contig_length" \
            'BEGIN { exit !(start >= 1 && end >= start && end <= length_value) }'
        then
            die "Region selector coordinates are outside FASTA bounds: $region (length $contig_length)"
        fi
    done
}

validate_regions_file_stream() {
    local fai="$1"
    local format="$2"
    awk -F '\t' -v format="$format" '
        NR == FNR {
            lengths[$1] = $2
            next
        }
        /^#/ || /^[[:space:]]*$/ {
            next
        }
        {
            sub(/\r$/, "", $NF)
            contig = $1
            if (!(contig in lengths)) {
                printf "regions file contig is absent from FASTA index: %s\n", contig > "/dev/stderr"
                invalid = 1
                next
            }

            if (format == "bed") {
                if (NF < 3 || $2 !~ /^[0-9]+$/ || $3 !~ /^[0-9]+$/ ||
                    $2 < 0 || $3 <= $2 || $3 > lengths[contig]) {
                    printf "invalid BED interval on regions file row %d\n", FNR > "/dev/stderr"
                    invalid = 1
                }
            } else if (format == "vcf") {
                if (NF < 2 || $2 !~ /^[1-9][0-9]*$/ || $2 > lengths[contig]) {
                    printf "invalid VCF position on regions file row %d\n", FNR > "/dev/stderr"
                    invalid = 1
                }
            } else {
                row_mode = (NF == 2 ? 2 : 3)
                if (mode && row_mode != mode) {
                    printf "regions file mixes position and interval rows at row %d\n", FNR > "/dev/stderr"
                    invalid = 1
                }
                mode = row_mode
                if ($2 !~ /^[1-9][0-9]*$/ || $2 > lengths[contig]) {
                    printf "invalid regions file start/position on row %d\n", FNR > "/dev/stderr"
                    invalid = 1
                }
                if (row_mode == 3 &&
                    ($3 !~ /^[1-9][0-9]*$/ || $3 < $2 || $3 > lengths[contig])) {
                    printf "invalid regions file end on row %d\n", FNR > "/dev/stderr"
                    invalid = 1
                }
            }
            data_rows++
        }
        END {
            if (!data_rows) {
                print "regions file contains no selector rows" > "/dev/stderr"
                invalid = 1
            }
            exit invalid
        }
    ' "$fai" -
}

validate_regions_file_selector() {
    local path="$1"
    local fai="$2"
    local uncompressed_path="${path%.gz}"
    local format="tab"

    case "$uncompressed_path" in
        *.bed) format="bed" ;;
        *.vcf) format="vcf" ;;
    esac

    if [[ "$path" == *.gz ]]; then
        command -v gzip >/dev/null 2>&1 ||
            die "gzip is required to validate compressed regions file: $path"
        if ! gzip -cd "$path" | validate_regions_file_stream "$fai" "$format"; then
            die "Regions file validation failed: $path"
        fi
    elif ! validate_regions_file_stream "$fai" "$format" < "$path"; then
        die "Regions file validation failed: $path"
    fi
}

read_partition_selector() {
    local manifest="$1"
    local requested_id="$2"
    local selected_count=0
    local selected_type=""
    local selected_value=""
    local status=0
    read_partition_record() {
        local partition_record_id="$1"
        local partition_record_type="$2"
        local partition_record_value="$3"

        if [[ "$partition_record_id" == "$requested_id" ]]; then
            selected_count=$((selected_count + 1))
            selected_type="$partition_record_type"
            selected_value="$partition_record_value"
        fi
    }

    read_manifest_partitions "$manifest" read_partition_record || status=$?
    unset -f read_partition_record
    [[ "$status" -eq 0 ]] || return "$status"

    if [[ "$selected_count" -ne 1 ]]; then
        printf "partition_id %s was not found exactly once\n" "$requested_id" >&2
        return 7
    fi

    printf '%s\t%s\n' "$selected_type" "$selected_value"
}

validate_vcf() {
    local label="$1"
    local path="$2"
    local expected_samples="$3"
    local observed_samples

    [[ -s "$path" ]] || die "$label VCF does not exist or is empty: $path"
    "$bcftools_bin" view -h "$path" >/dev/null ||
        die "$label VCF header validation failed: $path"
    observed_samples="$("$bcftools_bin" query -l "$path")" ||
        die "$label VCF sample query failed: $path"
    if [[ "$observed_samples" != "$expected_samples" ]]; then
        printf 'ERROR: %s VCF sample order does not match the sample manifest: %s\n' "$label" "$path" >&2
        printf 'Expected samples:\n%s\n' "$expected_samples" >&2
        printf 'Observed samples:\n%s\n' "$observed_samples" >&2
        exit 1
    fi
}

vcf_record_count() {
    local path="$1"
    "$bcftools_bin" view -H "$path" | awk 'END { print NR + 0 }'
}

validate_receipt() {
    local path="$1"
    local expected_header
    local observed_header
    local row_count

    expected_header=$'cohort_id\tpartition_id\tselector_type\tselector_value\torientation\tvcf_path\tsample_manifest_sha256\tpartition_manifest_sha256\tsample_count\tvcf_record_count'
    [[ -s "$path" ]] || die "Step 07 receipt does not exist or is empty: $path"
    IFS= read -r observed_header < "$path"
    [[ "$observed_header" == "$expected_header" ]] ||
        die "Step 07 receipt header is invalid: $path"
    row_count="$(awk 'END { print NR - 1 }' "$path")"
    [[ "$row_count" == "2" ]] ||
        die "Step 07 receipt must contain exactly two data rows; got $row_count: $path"
}

declare_required_arguments \
    cohort_id sample_manifest partition_manifest partition_id \
    orientation_root reference_fasta output_root
requested_bcftools_bin=""
max_depth="10000000"
filter_expression='INFO/AD[1-]>2 & MAX(FORMAT/DP)>20'
no_clobber=false
execute=false
scientific_input_labels=()
scientific_input_paths=()
scientific_input_sha256=()
scientific_input_expected_count=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --cohort-id) assign_option_value "$1" "${2:-}" cohort_id; shift 2 ;;
        --sample-manifest) assign_option_value "$1" "${2:-}" sample_manifest; shift 2 ;;
        --partition-manifest) assign_option_value "$1" "${2:-}" partition_manifest; shift 2 ;;
        --partition-id) assign_option_value "$1" "${2:-}" partition_id; shift 2 ;;
        --orientation-root) assign_option_value "$1" "${2:-}" orientation_root; shift 2 ;;
        --reference-fasta) assign_option_value "$1" "${2:-}" reference_fasta; shift 2 ;;
        --output-root) assign_option_value "$1" "${2:-}" output_root; shift 2 ;;
        --bcftools-bin) assign_option_value "$1" "${2:-}" requested_bcftools_bin; shift 2 ;;
        --max-depth) assign_option_value "$1" "${2:-}" max_depth; shift 2 ;;
        --filter-expression) assign_option_value "$1" "${2:-}" filter_expression; shift 2 ;;
        --no-clobber) no_clobber=true; shift ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

require_arguments

validate_safe_id "--cohort-id" "$cohort_id"
validate_safe_id "--partition-id" "$partition_id"
validate_positive_integer "--max-depth" "$max_depth"
[[ -n "$filter_expression" ]] || die "--filter-expression must be non-empty."

validate_nonempty_file "Sample manifest" "$sample_manifest"
validate_nonempty_file "Partition manifest" "$partition_manifest"
validate_nonempty_file "Reference FASTA" "$reference_fasta"
validate_nonempty_file "Reference FASTA index" "$reference_fasta.fai"
validate_fai_structure "$reference_fasta.fai"

bcftools_bin="$(
    resolve_overridable_executable \
        "bcftools" "$requested_bcftools_bin" BCFTOOLS_BIN_OVERRIDE bcftools
)"
sample_manifest_sha256="$(sha256_file "$sample_manifest")"
partition_manifest_sha256="$(sha256_file "$partition_manifest")"

append_sample_id() {
    local sample_id="$1"

    validate_safe_id "sample_id" "$sample_id"
    sample_ids+=("$sample_id")
}

sample_ids=()
if ! read_manifest_sample_ids "$sample_manifest" append_sample_id; then
    die "Sample manifest validation failed: $sample_manifest"
fi
unset -f append_sample_id
[[ "${#sample_ids[@]}" -gt 0 ]] || die "Sample manifest contains no sample IDs: $sample_manifest"
expected_samples="$(printf '%s\n' "${sample_ids[@]}")"

if ! selector_record="$(read_partition_selector "$partition_manifest" "$partition_id")"; then
    die "Partition manifest validation failed: $partition_manifest"
fi
selector_type="${selector_record%%$'\t'*}"
selector_value="${selector_record#*$'\t'}"
selector_resolved="$selector_value"
selector_args=()

case "$selector_type" in
    region)
        validate_region_selector "$selector_value" "$reference_fasta.fai"
        selector_args=(-r "$selector_value")
        ;;
    regions_file)
        if [[ "$selector_value" != /* ]]; then
            partition_manifest_dir="$(cd "$(dirname "$partition_manifest")" && pwd -P)"
            selector_resolved="$partition_manifest_dir/$selector_value"
        fi
        validate_nonempty_file "Regions file for partition $partition_id" "$selector_resolved"
        validate_regions_file_selector "$selector_resolved" "$reference_fasta.fai"
        selector_args=(-R "$selector_resolved")
        ;;
    *)
        die "Internal error: unsupported selector_type: $selector_type"
        ;;
esac

fwd_bams=()
rev_bams=()
for sample_id in "${sample_ids[@]}"; do
    fwd_bam="$orientation_root/$sample_id/$sample_id.${ORIENTATIONS[0]}.bam"
    rev_bam="$orientation_root/$sample_id/$sample_id.${ORIENTATIONS[1]}.bam"
    validate_nonempty_file "${ORIENTATIONS[0]} BAM for $sample_id" "$fwd_bam"
    validate_nonempty_file "${ORIENTATIONS[0]} BAI for $sample_id" "$fwd_bam.bai"
    validate_nonempty_file "${ORIENTATIONS[1]} BAM for $sample_id" "$rev_bam"
    validate_nonempty_file "${ORIENTATIONS[1]} BAI for $sample_id" "$rev_bam.bai"
    fwd_bams+=("$fwd_bam")
    rev_bams+=("$rev_bam")
done

confirm_input_manifest_hashes
sample_count="${#sample_ids[@]}"
run_token="${NORAD_RUN_TOKEN:-${SLURM_JOB_ID:-$$}}"
validate_safe_id "Step 07 run token" "$run_token"

partition_output_dir="$output_root/$cohort_id/$partition_id"
final_fwd_vcf="$partition_output_dir/$cohort_id.$partition_id.${ORIENTATIONS[0]}.mpileup.vcf"
final_rev_vcf="$partition_output_dir/$cohort_id.$partition_id.${ORIENTATIONS[1]}.mpileup.vcf"
final_receipt="$partition_output_dir/$cohort_id.$partition_id.step07_outputs.tsv"
tmp_fwd_vcf="$partition_output_dir/.$cohort_id.$partition_id.step07.$run_token.${ORIENTATIONS[0]}.tmp.vcf"
tmp_rev_vcf="$partition_output_dir/.$cohort_id.$partition_id.step07.$run_token.${ORIENTATIONS[1]}.tmp.vcf"
tmp_receipt="$partition_output_dir/.$cohort_id.$partition_id.step07.$run_token.outputs.tmp.tsv"
backup_fwd_vcf="$partition_output_dir/.$cohort_id.$partition_id.step07.$run_token.previous.${ORIENTATIONS[0]}.vcf"
backup_rev_vcf="$partition_output_dir/.$cohort_id.$partition_id.step07.$run_token.previous.${ORIENTATIONS[1]}.vcf"
backup_receipt="$partition_output_dir/.$cohort_id.$partition_id.step07.$run_token.previous.outputs.tsv"
lock_path="$partition_output_dir/.$cohort_id.$partition_id.step07.lock"
lock_owner_file="$lock_path/owner"
validation_report="$partition_output_dir/$cohort_id.$partition_id.step07_validation.tsv"
validator_command=(
    .venv/bin/python -X pycache_prefix=/dev/null -I -m norad
    validate partitioned-cohort-mpileup
    --cohort-id "$cohort_id"
    --partition-id "$partition_id"
    --sample-manifest "$sample_manifest"
    --partition-manifest "$partition_manifest"
    --reference-fai "$reference_fasta.fai"
    --fwd-vcf "$final_fwd_vcf"
    --rev-vcf "$final_rev_vcf"
    --receipt "$final_receipt"
    --output "$validation_report"
    --execute
)
all_pass_command=(
    .venv/bin/python -X pycache_prefix=/dev/null -I -m norad
    validate all-pass
    --report "$validation_report"
    --step-id 07
    --scope-id "${cohort_id}__${partition_id}"
)

annotations='FORMAT/DP,FORMAT/AD,FORMAT/ADF,FORMAT/ADR,FORMAT/SP,INFO/AD,INFO/ADF,INFO/ADR'
fwd_mpileup_command=(
    "$bcftools_bin" mpileup
    -Ou
    -f "$reference_fasta"
    "${selector_args[@]}"
    -d "$max_depth"
    -I
    -a "$annotations"
    "${fwd_bams[@]}"
)
fwd_filter_command=(
    "$bcftools_bin" filter
    -i "$filter_expression"
    -Ov
    -o "$tmp_fwd_vcf"
    -
)
rev_mpileup_command=(
    "$bcftools_bin" mpileup
    -Ou
    -f "$reference_fasta"
    "${selector_args[@]}"
    -d "$max_depth"
    -I
    -a "$annotations"
    "${rev_bams[@]}"
)
rev_filter_command=(
    "$bcftools_bin" filter
    -i "$filter_expression"
    -Ov
    -o "$tmp_rev_vcf"
    -
)

printf 'Step 07 cohort mpileup context:\n'
printf '  Mode: %s\n' "$([[ "$execute" == true ]] && printf execute || printf dry-run)"
printf '  Run token: %s\n' "$run_token"
printf '  Cohort ID: %s\n' "$cohort_id"
printf '  Sample manifest: %s\n' "$sample_manifest"
printf '  Sample manifest SHA-256: %s\n' "$sample_manifest_sha256"
printf '  Sample count: %s\n' "$sample_count"
printf '  Samples:\n'
printf '    %s\n' "${sample_ids[@]}"
printf '  Partition manifest: %s\n' "$partition_manifest"
printf '  Partition manifest SHA-256: %s\n' "$partition_manifest_sha256"
printf '  Partition ID: %s\n' "$partition_id"
printf '  Selector declared in manifest: %s %s\n' "$selector_type" "$selector_value"
printf '  Selector resolved for execution: %s %s\n' "$selector_type" "$selector_resolved"
printf '  Reference FASTA: %s\n' "$reference_fasta"
printf '  Reference FAI: %s\n' "$reference_fasta.fai"
printf '  Orientation root: %s\n' "$orientation_root"
printf '  Output directory: %s\n' "$partition_output_dir"
printf '  %s VCF: %s\n' "${ORIENTATIONS[0]}" "$final_fwd_vcf"
printf '  %s VCF: %s\n' "${ORIENTATIONS[1]}" "$final_rev_vcf"
printf '  Receipt: %s\n' "$final_receipt"
printf '  bcftools: %s\n' "$bcftools_bin"
printf '  Maximum depth: %s\n' "$max_depth"
printf '  Filter expression: %s\n' "$filter_expression"
printf '  Existing-output policy: %s\n' \
    "$([[ "$no_clobber" == true ]] && printf no-clobber || printf replace-complete-set)"
printf '  Orientation policy: mechanical FWD_like/REV_like labels only\n'

printf '%s pipeline:\n' "${ORIENTATIONS[0]}"
print_command "${fwd_mpileup_command[@]}"
printf '  | '
print_command "${fwd_filter_command[@]}"
printf '%s pipeline:\n' "${ORIENTATIONS[1]}"
print_command "${rev_mpileup_command[@]}"
printf '  | '
print_command "${rev_filter_command[@]}"

printf 'Planned validation:\n'
printf '  bcftools view -h on both VCFs\n'
printf '  bcftools query -l must equal manifest sample order\n'
printf '  bcftools view -H record counts are written to the receipt\n'
printf '  header-only VCFs are valid\n'
printf 'Planned publication:\n'
printf '  Lock: %s\n' "$lock_path"
printf '  Temporary %s VCF: %s\n' "${ORIENTATIONS[0]}" "$tmp_fwd_vcf"
printf '  Temporary %s VCF: %s\n' "${ORIENTATIONS[1]}" "$tmp_rev_vcf"
printf '  Temporary receipt: %s\n' "$tmp_receipt"
printf '  Publish the validated VCF/VCF/receipt set with rollback protection\n'
printf 'Post-execution validator command:\n'
print_command "${validator_command[@]}"
printf 'Semantic all-pass gate:\n'
print_command "${all_pass_command[@]}"

if [[ "$no_clobber" == true ]]; then
    require_no_owner_residue \
        "Step 07" "$partition_output_dir" \
        ".${cohort_id}.${partition_id}.step07.*"
fi

if [[ "$execute" != true ]]; then
    printf 'Dry-run complete; no directories or files were created.\n'
    exit 0
fi

mkdir -p "$partition_output_dir"

lock_acquired=false
lock_owner_written=false
scratch_owned=false
previous_final_set_present=false
backup_started=false
publication_committed=false
final_count=0

release_owned_lock() {
    local unexpected

    [[ "$lock_acquired" == true ]] || return 0
    if [[ "$lock_owner_written" != true || ! -f "$lock_owner_file" ]]; then
        printf 'ERROR: Step 07 cannot prove lock ownership for release: %s\n' \
            "$lock_path" >&2
        return 1
    fi
    if ! grep -Fqx $'run_token\t'"$run_token" "$lock_owner_file"; then
        printf 'ERROR: Step 07 lock owner changed; preserving lock: %s\n' \
            "$lock_path" >&2
        return 1
    fi
    unexpected="$(
        find "$lock_path" -mindepth 1 -maxdepth 1 \
            ! -path "$lock_owner_file" -print -quit
    )" || {
        printf 'ERROR: Could not inspect Step 07 lock: %s\n' "$lock_path" >&2
        return 1
    }
    if [[ -n "$unexpected" ]]; then
        printf 'ERROR: Step 07 lock contains unexpected residue; preserving it: %s\n' \
            "$unexpected" >&2
        return 1
    fi
    rm -f "$lock_owner_file"
    if ! rmdir "$lock_path" 2>/dev/null; then
        if [[ ! -e "$lock_owner_file" && -d "$lock_path" ]]; then
            (set -o noclobber; printf 'run_token\t%s\npid\t%s\n' "$run_token" "$$" > "$lock_owner_file") \
                2>/dev/null || true
        fi
        printf 'ERROR: Could not remove Step 07 lock directory; preserving residue: %s\n' \
            "$lock_path" >&2
        return 1
    fi
    lock_acquired=false
}

cleanup() {
    local status="$1"
    local rollback_failed=false

    if [[ "$status" -ne 0 &&
          "$backup_started" == true &&
          "$publication_committed" != true ]]; then
        if [[ "$no_clobber" == true ]]; then
            remove_owned_published_file \
                "Step 07 FWD VCF" "$tmp_fwd_vcf" "$final_fwd_vcf" || rollback_failed=true
            remove_owned_published_file \
                "Step 07 REV VCF" "$tmp_rev_vcf" "$final_rev_vcf" || rollback_failed=true
            remove_owned_published_file \
                "Step 07 receipt" "$tmp_receipt" "$final_receipt" || rollback_failed=true
        elif [[ "$previous_final_set_present" == true ]]; then
            if [[ -e "$backup_fwd_vcf" ]]; then
                if ! rm -f "$final_fwd_vcf"; then
                    printf 'ERROR: Could not clear Step 07 FWD_like output before restore: %s\n' \
                        "$final_fwd_vcf" >&2
                    rollback_failed=true
                elif ! mv "$backup_fwd_vcf" "$final_fwd_vcf"; then
                    printf 'ERROR: Could not restore Step 07 FWD_like backup: %s\n' \
                        "$backup_fwd_vcf" >&2
                    rollback_failed=true
                fi
            elif [[ ! -e "$final_fwd_vcf" ]]; then
                printf 'ERROR: Step 07 rollback found neither FWD_like final nor backup.\n' >&2
                rollback_failed=true
            fi
            if [[ -e "$backup_rev_vcf" ]]; then
                if ! rm -f "$final_rev_vcf"; then
                    printf 'ERROR: Could not clear Step 07 REV_like output before restore: %s\n' \
                        "$final_rev_vcf" >&2
                    rollback_failed=true
                elif ! mv "$backup_rev_vcf" "$final_rev_vcf"; then
                    printf 'ERROR: Could not restore Step 07 REV_like backup: %s\n' \
                        "$backup_rev_vcf" >&2
                    rollback_failed=true
                fi
            elif [[ ! -e "$final_rev_vcf" ]]; then
                printf 'ERROR: Step 07 rollback found neither REV_like final nor backup.\n' >&2
                rollback_failed=true
            fi
            if [[ -e "$backup_receipt" ]]; then
                if ! rm -f "$final_receipt"; then
                    printf 'ERROR: Could not clear Step 07 receipt before restore: %s\n' \
                        "$final_receipt" >&2
                    rollback_failed=true
                elif ! mv "$backup_receipt" "$final_receipt"; then
                    printf 'ERROR: Could not restore Step 07 receipt backup: %s\n' \
                        "$backup_receipt" >&2
                    rollback_failed=true
                fi
            elif [[ ! -e "$final_receipt" ]]; then
                printf 'ERROR: Step 07 rollback found neither receipt final nor backup.\n' >&2
                rollback_failed=true
            fi
        else
            # The final paths were confirmed absent before publication began,
            # so any of them present now belong to this failed invocation.
            if ! rm -f "$final_fwd_vcf" "$final_rev_vcf" "$final_receipt"; then
                printf 'ERROR: Could not remove partially published Step 07 outputs.\n' >&2
                rollback_failed=true
            fi
        fi
    fi

    if [[ "$scratch_owned" == true &&
          ( "$rollback_failed" != true || "$no_clobber" != true ) ]]; then
        rm -f "$tmp_fwd_vcf" "$tmp_rev_vcf" "$tmp_receipt" || true
        if [[ "$rollback_failed" != true ]] &&
           [[ "$status" -eq 0 ||
              "$backup_started" != true ||
              "$previous_final_set_present" != true ||
              "$publication_committed" == true ]]; then
            rm -f "$backup_fwd_vcf" "$backup_rev_vcf" "$backup_receipt" || true
        fi
    fi

    if [[ "$rollback_failed" == true ]]; then
        printf 'ERROR: Step 07 rollback was incomplete; retaining the owned lock and backups for operator recovery: %s\n' \
            "$lock_path" >&2
    elif [[ "$lock_acquired" == true ]]; then
        if [[ "$lock_owner_written" == true ]]; then
            if ! release_owned_lock; then
                printf 'ERROR: Step 07 lock release failed; preserving lock residue: %s\n' \
                    "$lock_path" >&2
            fi
        else
            rm -f "$lock_owner_file" || true
            rmdir "$lock_path" 2>/dev/null || true
        fi
    fi
}

set_exit_trap cleanup

# Avoid the tiny stale-lock window between atomic mkdir and recording local
# ownership. EXIT cleanup remains armed if owner-file creation itself fails.
trap '' HUP INT TERM
if ! mkdir "$lock_path" 2>/dev/null; then
    arm_signal_traps
    die "Step 07 lock already exists: $lock_path"
fi
lock_acquired=true
if ! printf 'run_token\t%s\npid\t%s\n' "$run_token" "$$" > "$lock_owner_file"; then
    arm_signal_traps
    die "Could not write Step 07 lock owner file: $lock_owner_file"
fi
lock_owner_written=true

for owned_path in "$tmp_fwd_vcf" "$tmp_rev_vcf" "$tmp_receipt" "$backup_fwd_vcf" "$backup_rev_vcf" "$backup_receipt"; do
    if [[ -e "$owned_path" ]]; then
        arm_signal_traps
        die "Refusing to reuse an existing Step 07 scratch path: $owned_path"
    fi
done
scratch_owned=true
arm_signal_traps

# Inspect the stable output set only while holding the partition lock. The
# receipt is the commit marker, so an existing set must be all three files.
[[ -e "$final_fwd_vcf" ]] && final_count=$((final_count + 1))
[[ -e "$final_rev_vcf" ]] && final_count=$((final_count + 1))
[[ -e "$final_receipt" ]] && final_count=$((final_count + 1))
if [[ "$final_count" -ne 0 && "$final_count" -ne 3 ]]; then
    die "Existing Step 07 outputs are incomplete; expected all three or none in: $partition_output_dir"
fi
if [[ "$final_count" -eq 3 && "$no_clobber" == true ]]; then
    die "Refusing to replace an existing complete Step 07 output set under --no-clobber: $partition_output_dir"
fi

# Orchestration-safe execution binds the exact stationary scientific-input
# roster and bytes immediately before either bcftools pipeline can consume it.
confirm_input_manifest_hashes
capture_no_clobber_scientific_inputs

if ! "${fwd_mpileup_command[@]}" | "${fwd_filter_command[@]}"; then
    die "FWD_like bcftools mpileup/filter pipeline failed."
fi
if ! "${rev_mpileup_command[@]}" | "${rev_filter_command[@]}"; then
    die "REV_like bcftools mpileup/filter pipeline failed."
fi

confirm_input_manifest_hashes
confirm_no_clobber_scientific_inputs
validate_vcf "Published ${ORIENTATIONS[0]} temporary" "$tmp_fwd_vcf" "$expected_samples"
validate_vcf "Published ${ORIENTATIONS[1]} temporary" "$tmp_rev_vcf" "$expected_samples"
tmp_fwd_count="$(vcf_record_count "$tmp_fwd_vcf")" ||
    die "Could not count ${ORIENTATIONS[0]} VCF records."
tmp_rev_count="$(vcf_record_count "$tmp_rev_vcf")" ||
    die "Could not count ${ORIENTATIONS[1]} VCF records."
[[ "$tmp_fwd_count" =~ ^[0-9]+$ ]] || die "Invalid ${ORIENTATIONS[0]} VCF record count: $tmp_fwd_count"
[[ "$tmp_rev_count" =~ ^[0-9]+$ ]] || die "Invalid ${ORIENTATIONS[1]} VCF record count: $tmp_rev_count"

{
    printf 'cohort_id\tpartition_id\tselector_type\tselector_value\torientation\tvcf_path\tsample_manifest_sha256\tpartition_manifest_sha256\tsample_count\tvcf_record_count\n'
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$cohort_id" "$partition_id" "$selector_type" "$selector_value" \
        "${ORIENTATIONS[0]}" \
        "$final_fwd_vcf" "$sample_manifest_sha256" "$partition_manifest_sha256" \
        "$sample_count" "$tmp_fwd_count"
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$cohort_id" "$partition_id" "$selector_type" "$selector_value" \
        "${ORIENTATIONS[1]}" \
        "$final_rev_vcf" "$sample_manifest_sha256" "$partition_manifest_sha256" \
        "$sample_count" "$tmp_rev_count"
} > "$tmp_receipt"
validate_receipt "$tmp_receipt"
confirm_input_manifest_hashes
confirm_no_clobber_scientific_inputs

if [[ "$final_count" -eq 3 ]]; then
    previous_final_set_present=true
    backup_started=true
    mv "$final_fwd_vcf" "$backup_fwd_vcf"
    mv "$final_rev_vcf" "$backup_rev_vcf"
    mv "$final_receipt" "$backup_receipt"
else
    backup_started=true
fi

if [[ "$no_clobber" == true ]]; then
    publish_file_create_exclusive \
        "Step 07 FWD VCF" "$tmp_fwd_vcf" "$final_fwd_vcf"
    publish_file_create_exclusive \
        "Step 07 REV VCF" "$tmp_rev_vcf" "$final_rev_vcf"
else
    mv "$tmp_fwd_vcf" "$final_fwd_vcf"
    mv "$tmp_rev_vcf" "$final_rev_vcf"
fi

validate_vcf "Published ${ORIENTATIONS[0]}" "$final_fwd_vcf" "$expected_samples"
validate_vcf "Published ${ORIENTATIONS[1]}" "$final_rev_vcf" "$expected_samples"
published_fwd_count="$(vcf_record_count "$final_fwd_vcf")"
published_rev_count="$(vcf_record_count "$final_rev_vcf")"
[[ "$published_fwd_count" == "$tmp_fwd_count" ]] ||
    die "Published ${ORIENTATIONS[0]} VCF record count changed during publication."
[[ "$published_rev_count" == "$tmp_rev_count" ]] ||
    die "Published ${ORIENTATIONS[1]} VCF record count changed during publication."

# Make the already-validated receipt visible only after both VCFs pass their
# final structural/count checks. A later failure still enters owned rollback.
if [[ "$no_clobber" == true ]]; then
    publish_file_create_exclusive \
        "Step 07 receipt" "$tmp_receipt" "$final_receipt"
else
    mv "$tmp_receipt" "$final_receipt"
fi
validate_receipt "$final_receipt"

if [[ "$no_clobber" == true ]]; then
    require_owned_published_file \
        "Step 07 FWD VCF" "$tmp_fwd_vcf" "$final_fwd_vcf"
    require_owned_published_file \
        "Step 07 REV VCF" "$tmp_rev_vcf" "$final_rev_vcf"
    require_owned_published_file \
        "Step 07 receipt" "$tmp_receipt" "$final_receipt"
    rm -f -- "$tmp_fwd_vcf" "$tmp_rev_vcf" "$tmp_receipt"
    [[ ! -e "$tmp_fwd_vcf" && ! -L "$tmp_fwd_vcf" &&
       ! -e "$tmp_rev_vcf" && ! -L "$tmp_rev_vcf" &&
       ! -e "$tmp_receipt" && ! -L "$tmp_receipt" ]] ||
        die "Step 07 could not remove owned publication anchors."
fi

# The receipt is published last and final validation marks the transaction
# committed. Downstream stages must require the receipt rather than globbing
# any VCFs that might be visible during the short multi-file rename window.
publication_committed=true
rm -f "$backup_fwd_vcf" "$backup_rev_vcf" "$backup_receipt"
release_owned_lock

printf 'Step 07 execute complete.\n'
printf 'Published %s VCF: %s (%s records)\n' \
    "${ORIENTATIONS[0]}" \
    "$final_fwd_vcf" "$tmp_fwd_count"
printf 'Published %s VCF: %s (%s records)\n' \
    "${ORIENTATIONS[1]}" \
    "$final_rev_vcf" "$tmp_rev_count"
printf 'Published receipt: %s\n' "$final_receipt"
