# Shared file-validation helpers for Bash pipeline stages.

is_gzip_path() {
    [[ "$1" == *.gz ]]
}

sha256_file() {
    local path="$1"

    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$path" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$path" | awk '{print $1}'
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c '
import hashlib
import sys

digest = hashlib.sha256()
with open(sys.argv[1], "rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
print(digest.hexdigest())
' "$path"
    else
        die "No SHA-256 implementation found (sha256sum, shasum, or python3)."
    fi
}

validate_nonempty_file() {
    local label="$1"
    local path="$2"
    [[ -s "$path" ]] || die "$label does not exist or is empty: $path"
}

validate_safe_id() {
    local label="$1"
    local value="$2"
    [[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] ||
        die "$label must match [A-Za-z0-9][A-Za-z0-9._-]*; got: $value"
}

validate_positive_integer() {
    local label="${1:-value}"
    local value="${2:-}"
    [[ "$value" =~ ^[1-9][0-9]*$ ]] ||
        die "$label must be a positive integer; got: $value"
}

validate_nonnegative_integer() {
    local label="${1:-value}"
    local value="${2:-}"
    [[ "$value" =~ ^(0|[1-9][0-9]*)$ ]] ||
        die "$label must be a non-negative integer; got: $value"
}

validate_exact_header() {
    local label="$1"
    local path="$2"
    local expected="$3"
    local observed

    validate_nonempty_file "$label" "$path"
    IFS= read -r observed < "$path"
    [[ "$observed" == "$expected" ]] || die "$label header is invalid: $path"
}

read_manifest_sample_ids() {
    local manifest="$1"
    local on_sample="${2:-}"

    if [[ -n "$on_sample" ]] && ! declare -F "$on_sample" >/dev/null 2>&1; then
        die "Unknown callback function: $on_sample"
    fi

    local parsed
    local status
    if parsed="$(awk -F '\t' '
        NR == 1 {
            for (i = 1; i <= NF; i++) {
                gsub(/\r$/, "", $i)
                if ($i == "sample_id") sample_column = i
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
    ' "$manifest")"; then
        :
    else
        status=$?
        return "$status"
    fi

    if [[ -n "$on_sample" ]]; then
        if [[ -z "$parsed" ]]; then
            return 0
        fi
        local sample_id
        while IFS= read -r sample_id; do
            if [[ -z "$sample_id" ]]; then
                continue
            fi
            if "$on_sample" "$sample_id"; then
                :
            else
                status=$?
                return "$status"
            fi
        done <<< "$parsed"
        return 0
    fi

    printf '%s' "$parsed"
}

read_manifest_partitions() {
    local manifest="$1"
    local on_partition="${2:-}"
    local strict_mode="${3:-0}"

    if [[ -n "$on_partition" ]] && ! declare -F "$on_partition" >/dev/null 2>&1; then
        die "Unknown callback function: $on_partition"
    fi

    local parsed
    local status
    if parsed="$(awk -F '\t' -v strict="$strict_mode" '
        NR == 1 {
            if (strict) {
                if (NF != 3 || $1 != "partition_id" ||
                    $2 != "selector_type" || $3 != "selector_value") {
                    print "partition manifest header must be exactly partition_id, selector_type, selector_value" > "/dev/stderr"
                    exit 2
                }
                next
            }
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
        strict {
            if (NF != 3) {
                printf "partition manifest row %d has %d fields; expected 3\n", NR, NF > "/dev/stderr"
                exit 3
            }
            id = $1
            type = $2
            value = $3
            gsub(/\r$/, "", id)
            gsub(/\r$/, "", type)
            gsub(/\r$/, "", value)
        }
        {
            if (!strict) {
                id = $id_column
                type = $type_column
                value = $value_column
                gsub(/\r$/, "", id)
                gsub(/\r$/, "", type)
                gsub(/\r$/, "", value)
            }

            if (!strict && id == "" && type == "" && value == "") next
            if (id == "" || type == "" || value == "") {
                if (strict) {
                    printf "partition manifest row %d has an empty value\n", NR > "/dev/stderr"
                } else {
                    printf "partition manifest row %d has an empty required value\n", NR > "/dev/stderr"
                }
                exit 3
            }
            if (!strict && id !~ /^[A-Za-z0-9][A-Za-z0-9._-]*$/) {
                printf "partition manifest row %d has unsafe partition_id: %s\n", NR, id > "/dev/stderr"
                exit 4
            }
            if (seen[id]++) {
                if (strict) {
                    printf "duplicate partition_id: %s\n", id > "/dev/stderr"
                } else {
                    printf "duplicate partition_id in partition manifest: %s\n", id > "/dev/stderr"
                }
                exit 5
            }
            if (type != "region" && type != "regions_file") {
                printf "invalid selector_type for partition %s: %s\n", id, type > "/dev/stderr"
                exit 6
            }
            print id "\t" type "\t" value
            count++
        }
        END {
            if (!count) {
                if (strict) {
                    print "partition manifest contains no partitions" > "/dev/stderr"
                } else {
                    print "partition manifest contains no partition rows" > "/dev/stderr"
                }
                exit 7
            }
        }
    ' "$manifest")"; then
        :
    else
        status=$?
        return "$status"
    fi

    if [[ -n "$on_partition" ]]; then
        if [[ -z "$parsed" ]]; then
            return 0
        fi
        local partition_id selector_type selector_value
        while IFS=$'\t' read -r partition_id selector_type selector_value; do
            if "$on_partition" "$partition_id" "$selector_type" "$selector_value"; then
                :
            else
                status=$?
                return "$status"
            fi
        done <<< "$parsed"
        return 0
    fi

    printf '%s' "$parsed"
}
