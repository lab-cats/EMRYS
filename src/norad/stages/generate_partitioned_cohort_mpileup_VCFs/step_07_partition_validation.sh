#!/usr/bin/env bash
# Step 07 partition-manifest, FASTA-index, and selector validation helpers.

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

    if ! read_manifest_partitions "$manifest" read_partition_record; then
        status=$?
    fi
    unset -f read_partition_record

    if [[ "$status" -ne 0 ]]; then
        return "$status"
    fi

    if [[ "$selected_count" -ne 1 ]]; then
        printf "partition_id %s was not found exactly once\n" "$requested_id" >&2
        return 7
    fi

    printf '%s\t%s\n' "$selected_type" "$selected_value"
}
