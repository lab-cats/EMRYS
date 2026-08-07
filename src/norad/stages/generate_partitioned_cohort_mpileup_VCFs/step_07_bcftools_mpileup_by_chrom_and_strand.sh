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
  src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/step_07_bcftools_mpileup_by_chrom_and_strand.sh \
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

resolve_bcftools() {
    local value="${bcftools_bin_arg:-}"
    if [[ -z "$value" && -n "${BCFTOOLS_BIN_OVERRIDE:-}" ]]; then
        value="$BCFTOOLS_BIN_OVERRIDE"
    fi
    resolve_executable_value "bcftools" "$value" "bcftools"
}

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

read_sample_ids() {
    local manifest="$1"
    awk -F '\t' '
        NR == 1 {
            for (i = 1; i <= NF; i++) {
                gsub(/\r$/, "", $i)
                if ($i == "sample_id") {
                    sample_column = i
                }
            }
            if (!sample_column) {
                print "sample manifest is missing required sample_id column" > "/dev/stderr"
                exit 2
            }
            next
        }
        {
            value = $sample_column
            gsub(/\r$/, "", value)
            if (value == "") {
                empty = 1
                next
            }
            if (seen[value]++) {
                printf "duplicate sample_id in sample manifest: %s\n", value > "/dev/stderr"
                exit 3
            }
            print value
            count++
        }
        END {
            if (!count && !empty) {
                print "sample manifest contains no sample rows" > "/dev/stderr"
                exit 4
            }
            if (empty) {
                print "sample manifest contains an empty sample_id" > "/dev/stderr"
                exit 5
            }
        }
    ' "$manifest"
}

read_partition_selector() {
    local manifest="$1"
    local requested_id="$2"
    awk -F '\t' -v requested="$requested_id" '
        NR == 1 {
            for (i = 1; i <= NF; i++) {
                gsub(/\r$/, "", $i)
                if ($i == "partition_id") id_column = i
                if ($i == "selector_type") type_column = i
                if ($i == "selector_value") value_column = i
            }
            if (!id_column || !type_column || !value_column) {
                print "partition manifest requires partition_id, selector_type, selector_value" > "/dev/stderr"
                exit 2
            }
            next
        }
        {
            id = $id_column
            type = $type_column
            value = $value_column
            gsub(/\r$/, "", id)
            gsub(/\r$/, "", type)
            gsub(/\r$/, "", value)

            if (id == "" && type == "" && value == "") next
            if (id == "" || type == "" || value == "") {
                printf "partition manifest row %d has an empty required value\n", NR > "/dev/stderr"
                exit 3
            }
            if (id !~ /^[A-Za-z0-9][A-Za-z0-9._-]*$/) {
                printf "partition manifest row %d has unsafe partition_id: %s\n", NR, id > "/dev/stderr"
                exit 4
            }
            if (seen[id]++) {
                printf "duplicate partition_id in partition manifest: %s\n", id > "/dev/stderr"
                exit 5
            }
            if (type != "region" && type != "regions_file") {
                printf "invalid selector_type for partition %s: %s\n", id, type > "/dev/stderr"
                exit 6
            }
            if (id == requested) {
                selected_count++
                selected_type = type
                selected_value = value
            }
        }
        END {
            if (selected_count != 1) {
                printf "partition_id %s was not found exactly once\n", requested > "/dev/stderr"
                exit 7
            }
            print selected_type "\t" selected_value
        }
    ' "$manifest"
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

cohort_id=""
sample_manifest=""
partition_manifest=""
partition_id=""
orientation_root=""
reference_fasta=""
output_root=""
bcftools_bin_arg=""
max_depth="10000000"
filter_expression='INFO/AD[1-]>2 & MAX(FORMAT/DP)>20'
execute=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --cohort-id)
            require_value "$1" "${2:-}"
            cohort_id="$2"
            shift 2
            ;;
        --sample-manifest)
            require_value "$1" "${2:-}"
            sample_manifest="$2"
            shift 2
            ;;
        --partition-manifest)
            require_value "$1" "${2:-}"
            partition_manifest="$2"
            shift 2
            ;;
        --partition-id)
            require_value "$1" "${2:-}"
            partition_id="$2"
            shift 2
            ;;
        --orientation-root)
            require_value "$1" "${2:-}"
            orientation_root="$2"
            shift 2
            ;;
        --reference-fasta)
            require_value "$1" "${2:-}"
            reference_fasta="$2"
            shift 2
            ;;
        --output-root)
            require_value "$1" "${2:-}"
            output_root="$2"
            shift 2
            ;;
        --bcftools-bin)
            require_value "$1" "${2:-}"
            bcftools_bin_arg="$2"
            shift 2
            ;;
        --max-depth)
            require_value "$1" "${2:-}"
            max_depth="$2"
            shift 2
            ;;
        --filter-expression)
            require_value "$1" "${2:-}"
            filter_expression="$2"
            shift 2
            ;;
        --execute)
            execute=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown argument: $1. Run with --help for usage."
            ;;
    esac
done

[[ -n "$cohort_id" ]] || die "Missing required argument: --cohort-id."
[[ -n "$sample_manifest" ]] || die "Missing required argument: --sample-manifest."
[[ -n "$partition_manifest" ]] || die "Missing required argument: --partition-manifest."
[[ -n "$partition_id" ]] || die "Missing required argument: --partition-id."
[[ -n "$orientation_root" ]] || die "Missing required argument: --orientation-root."
[[ -n "$reference_fasta" ]] || die "Missing required argument: --reference-fasta."
[[ -n "$output_root" ]] || die "Missing required argument: --output-root."

validate_safe_id "--cohort-id" "$cohort_id"
validate_safe_id "--partition-id" "$partition_id"
if ! [[ "$max_depth" =~ ^[1-9][0-9]*$ ]]; then
    die "--max-depth must be a positive integer; got: $max_depth"
fi
[[ -n "$filter_expression" ]] || die "--filter-expression must be non-empty."

validate_nonempty_file "Sample manifest" "$sample_manifest"
validate_nonempty_file "Partition manifest" "$partition_manifest"
validate_nonempty_file "Reference FASTA" "$reference_fasta"
validate_nonempty_file "Reference FASTA index" "$reference_fasta.fai"
validate_fai_structure "$reference_fasta.fai"

bcftools_bin="$(resolve_bcftools)"
sample_manifest_sha256="$(sha256_file "$sample_manifest")"
partition_manifest_sha256="$(sha256_file "$partition_manifest")"

if ! sample_output="$(read_sample_ids "$sample_manifest")"; then
    die "Sample manifest validation failed: $sample_manifest"
fi
sample_ids=()
while IFS= read -r sample_id; do
    [[ -n "$sample_id" ]] && sample_ids+=("$sample_id")
done <<< "$sample_output"
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
    validate_safe_id "sample_id" "$sample_id"
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
run_token="${SLURM_JOB_ID:-$$}"

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

cleanup() {
    local status="$1"

    if [[ "$status" -ne 0 &&
          "$backup_started" == true &&
          "$publication_committed" != true ]]; then
        if [[ "$previous_final_set_present" == true ]]; then
            if [[ -e "$backup_fwd_vcf" ]]; then
                rm -f "$final_fwd_vcf" || true
                mv "$backup_fwd_vcf" "$final_fwd_vcf" || true
            fi
            if [[ -e "$backup_rev_vcf" ]]; then
                rm -f "$final_rev_vcf" || true
                mv "$backup_rev_vcf" "$final_rev_vcf" || true
            fi
            if [[ -e "$backup_receipt" ]]; then
                rm -f "$final_receipt" || true
                mv "$backup_receipt" "$final_receipt" || true
            fi
        else
            # The final paths were confirmed absent before publication began,
            # so any of them present now belong to this failed invocation.
            rm -f "$final_fwd_vcf" "$final_rev_vcf" || true
            rm -f "$final_receipt" || true
        fi
    fi

    if [[ "$scratch_owned" == true ]]; then
        rm -f "$tmp_fwd_vcf" "$tmp_rev_vcf" "$tmp_receipt" || true
        if [[ "$status" -eq 0 ||
              "$backup_started" != true ||
              "$previous_final_set_present" != true ||
              "$publication_committed" == true ]]; then
            rm -f "$backup_fwd_vcf" "$backup_rev_vcf" "$backup_receipt" || true
        fi
    fi

    if [[ "$lock_acquired" == true ]]; then
        if [[ "$lock_owner_written" == true ]] &&
           [[ -f "$lock_owner_file" ]] &&
           grep -Fqx $'run_token\t'"$run_token" "$lock_owner_file"; then
            rm -f "$lock_owner_file" || true
            rmdir "$lock_path" 2>/dev/null || true
        elif [[ "$lock_owner_written" != true ]]; then
            rm -f "$lock_owner_file" || true
            rmdir "$lock_path" 2>/dev/null || true
        fi
    fi
}

arm_signal_traps() {
    trap 'exit 129' HUP
    trap 'exit 130' INT
    trap 'exit 143' TERM
}

on_exit() {
    local status=$?
    trap - EXIT HUP INT TERM
    cleanup "$status"
    exit "$status"
}
trap on_exit EXIT
arm_signal_traps

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

if ! "${fwd_mpileup_command[@]}" | "${fwd_filter_command[@]}"; then
    die "FWD_like bcftools mpileup/filter pipeline failed."
fi
if ! "${rev_mpileup_command[@]}" | "${rev_filter_command[@]}"; then
    die "REV_like bcftools mpileup/filter pipeline failed."
fi

confirm_input_manifest_hashes
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

if [[ "$final_count" -eq 3 ]]; then
    previous_final_set_present=true
    backup_started=true
    mv "$final_fwd_vcf" "$backup_fwd_vcf"
    mv "$final_rev_vcf" "$backup_rev_vcf"
    mv "$final_receipt" "$backup_receipt"
else
    backup_started=true
fi

mv "$tmp_fwd_vcf" "$final_fwd_vcf"
mv "$tmp_rev_vcf" "$final_rev_vcf"
mv "$tmp_receipt" "$final_receipt"

validate_vcf "Published ${ORIENTATIONS[0]}" "$final_fwd_vcf" "$expected_samples"
validate_vcf "Published ${ORIENTATIONS[1]}" "$final_rev_vcf" "$expected_samples"
validate_receipt "$final_receipt"
published_fwd_count="$(vcf_record_count "$final_fwd_vcf")"
published_rev_count="$(vcf_record_count "$final_rev_vcf")"
[[ "$published_fwd_count" == "$tmp_fwd_count" ]] ||
    die "Published ${ORIENTATIONS[0]} VCF record count changed during publication."
[[ "$published_rev_count" == "$tmp_rev_count" ]] ||
    die "Published ${ORIENTATIONS[1]} VCF record count changed during publication."

# The receipt is published last and final validation marks the transaction
# committed. Downstream stages must require the receipt rather than globbing
# any VCFs that might be visible during the short multi-file rename window.
publication_committed=true
rm -f "$backup_fwd_vcf" "$backup_rev_vcf" "$backup_receipt"

printf 'Step 07 execute complete.\n'
printf 'Published %s VCF: %s (%s records)\n' \
    "${ORIENTATIONS[0]}" \
    "$final_fwd_vcf" "$tmp_fwd_count"
printf 'Published %s VCF: %s (%s records)\n' \
    "${ORIENTATIONS[1]}" \
    "$final_rev_vcf" "$tmp_rev_count"
printf 'Published receipt: %s\n' "$final_receipt"
