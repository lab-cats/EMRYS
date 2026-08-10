#!/usr/bin/env bash
# Step 00c: prepare and validate GATK-compatible reference FASTA sidecars.
#
# Dry-run mode validates the FASTA and prints the exact sidecar plan without
# creating directories, locks, temp files, .fai files, or .dict files. Passing
# --execute generates only missing sidecars, validates FASTA index/dictionary
# contig agreement, and publishes temp files only after validation succeeds.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  src/norad/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh \
    --reference-fasta refs/novogene_ref/genome.fa \
    [--samtools-bin SAMTOOLS_BIN] \
    [--gatk-bin GATK_BIN] \
    [--java-bin JAVA_BIN] \
    [--execute]

Prepare and validate GATK reference sidecars for one FASTA:
  <reference>.fai
  <reference basename>.dict

By default this script runs in dry-run mode: it validates existing inputs,
prints planned commands and validation checks, and writes nothing. Add
--execute to generate missing sidecars and validate outputs.

Required arguments:
  --reference-fasta  Reference FASTA path.

Options:
  --samtools-bin     samtools executable or path. Resolution order:
                     argument, SAMTOOLS_BIN_OVERRIDE, PATH.
  --gatk-bin         gatk executable or path. Resolution order:
                     argument, GATK_BIN_OVERRIDE, PATH.
  --java-bin         Java executable or path. Resolution order:
                     argument, JAVA_BIN_OVERRIDE, JAVA_HOME/bin/java, PATH.
  --execute          Execute sidecar generation after validation. Without this,
                     dry-run only.
  -h, --help         Show this help message and exit.
USAGE
}

# shellcheck source=../../libraries/executable_resolution.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/executable_resolution.sh"
# shellcheck source=../../libraries/argument_parsing.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/argument_parsing.sh"
# shellcheck source=../../libraries/signal_traps.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/signal_traps.sh"

read_fai_pairs() {
    local fai="$1"

    awk '
        BEGIN { OFS = "\t"; count = 0 }
        NF < 2 {
            printf "FAI line %d has fewer than 2 fields\n", NR > "/dev/stderr"
            exit 2
        }
        $1 == "" || $2 !~ /^[0-9]+$/ || $2 == 0 {
            printf "FAI line %d has invalid contig or length\n", NR > "/dev/stderr"
            exit 2
        }
        {
            print $1, $2
            count++
        }
        END {
            if (count == 0) {
                print "FAI contains no contigs" > "/dev/stderr"
                exit 2
            }
        }
    ' "$fai"
}

read_dict_pairs() {
    local dict="$1"

    awk '
        BEGIN { OFS = "\t"; count = 0 }
        /^@SQ/ {
            sn = ""
            ln = ""
            for (i = 1; i <= NF; i++) {
                if ($i ~ /^SN:/) {
                    sn = substr($i, 4)
                } else if ($i ~ /^LN:/) {
                    ln = substr($i, 4)
                }
            }
            if (sn == "" || ln !~ /^[0-9]+$/ || ln == 0) {
                printf "DICT @SQ line %d is missing valid SN/LN fields\n", NR > "/dev/stderr"
                exit 2
            }
            print sn, ln
            count++
        }
        END {
            if (count == 0) {
                print "DICT contains no @SQ contigs" > "/dev/stderr"
                exit 2
            }
        }
    ' "$dict"
}

validate_fai_file() {
    local fai="$1"

    [[ -s "$fai" ]] || die "FASTA index is missing or empty: $fai"
    read_fai_pairs "$fai" >/dev/null || die "FASTA index failed format validation: $fai"
}

validate_dict_file() {
    local dict="$1"

    [[ -s "$dict" ]] || die "Sequence dictionary is missing or empty: $dict"
    read_dict_pairs "$dict" >/dev/null || die "Sequence dictionary failed format validation: $dict"
}

validate_sidecar_agreement() {
    local fai="$1"
    local dict="$2"
    local fai_pairs
    local dict_pairs
    local fai_sorted
    local dict_sorted

    validate_fai_file "$fai"
    validate_dict_file "$dict"

    fai_pairs="$(read_fai_pairs "$fai")" || die "FASTA index failed format validation: $fai"
    dict_pairs="$(read_dict_pairs "$dict")" || die "Sequence dictionary failed format validation: $dict"

    fai_sorted="$(printf '%s\n' "$fai_pairs" | LC_ALL=C sort)"
    dict_sorted="$(printf '%s\n' "$dict_pairs" | LC_ALL=C sort)"

    if [[ "$fai_sorted" != "$dict_sorted" ]]; then
        printf 'FASTA index contigs/lengths:\n%s\n' "$fai_sorted" >&2
        printf 'Sequence dictionary contigs/lengths:\n%s\n' "$dict_sorted" >&2
        die "FASTA index and sequence dictionary contigs/lengths do not agree: $fai $dict"
    fi
}

declare_required_arguments reference_fasta
samtools_bin_arg=""
gatk_bin_arg=""
java_bin_arg=""
execute=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --reference-fasta) assign_option_value "$1" "${2:-}" reference_fasta; shift 2 ;;
        --samtools-bin) assign_option_value "$1" "${2:-}" samtools_bin_arg; shift 2 ;;
        --gatk-bin) assign_option_value "$1" "${2:-}" gatk_bin_arg; shift 2 ;;
        --java-bin) assign_option_value "$1" "${2:-}" java_bin_arg; shift 2 ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

require_arguments
[[ -s "$reference_fasta" ]] || die "Reference FASTA does not exist or is empty: $reference_fasta"

samtools_value="${samtools_bin_arg:-${SAMTOOLS_BIN_OVERRIDE:-}}"
gatk_value="${gatk_bin_arg:-${GATK_BIN_OVERRIDE:-}}"
java_value="${java_bin_arg:-${JAVA_BIN_OVERRIDE:-}}"
if [[ -z "$java_value" && -n "${JAVA_HOME:-}" && -x "${JAVA_HOME}/bin/java" ]]; then
    java_value="${JAVA_HOME}/bin/java"
fi

samtools_bin="$(resolve_executable_value "samtools" "$samtools_value" "samtools")"
gatk_bin="$(resolve_executable_value "GATK" "$gatk_value" "gatk")"
java_bin="$(resolve_executable_value "Java" "$java_value" "java")"

reference_dir="$(dirname "$reference_fasta")"
reference_base="$(basename "$reference_fasta")"
reference_stem="${reference_base%.*}"
fai_path="${reference_fasta}.fai"
dict_path="${reference_dir}/${reference_stem}.dict"

tmp_dir="${TMPDIR:-/tmp}"
run_token="${SLURM_JOB_ID:-$$}"
lock_path="${reference_dir}/.step_00c_prepare_gatk_reference.lock"
lock_owner_file="${lock_path}/owner"
tmp_fai="${fai_path}.tmp.${run_token}"
tmp_dict="${dict_path}.tmp.${run_token}"
tmp_fasta="${reference_fasta}.tmp.${run_token}.faidx_input"
tmp_fasta_fai="${tmp_fasta}.fai"
tmp_fasta_base="$(basename "$tmp_fasta")"

lock_acquired=false
tmp_fai_created=false
tmp_dict_created=false
published_fai=false
published_dict=false

samtools_faidx_command=(
    "$samtools_bin"
    faidx
    "$tmp_fasta"
)

gatk_dict_command=(
    "$gatk_bin"
    CreateSequenceDictionary
    -R "$reference_fasta"
    -O "$tmp_dict"
)

cleanup() {
    rm -f "$tmp_fai" "$tmp_dict" "$tmp_fasta" "$tmp_fasta_fai"
    remove_owned_lock
}

mode="dry-run"
if [[ "$execute" == true ]]; then
    mode="execute"
fi

fai_state="missing"
dict_state="missing"

if [[ -e "$fai_path" ]]; then
    if [[ -s "$fai_path" ]]; then
        validate_fai_file "$fai_path"
        fai_state="present and format-valid"
    else
        die "Existing FASTA index is empty: $fai_path"
    fi
fi

if [[ -e "$dict_path" ]]; then
    if [[ -s "$dict_path" ]]; then
        validate_dict_file "$dict_path"
        dict_state="present and format-valid"
    else
        die "Existing sequence dictionary is empty: $dict_path"
    fi
fi

if [[ -s "$fai_path" && -s "$dict_path" ]]; then
    validate_sidecar_agreement "$fai_path" "$dict_path"
    fai_state="present and valid"
    dict_state="present and valid"
fi

printf 'GATK reference sidecar context\n'
printf '  Reference FASTA: %s\n' "$reference_fasta"
printf '  FASTA index: %s\n' "$fai_path"
printf '  Sequence dictionary: %s\n' "$dict_path"
printf '  samtools bin: %s\n' "$samtools_bin"
printf '  GATK bin: %s\n' "$gatk_bin"
printf '  Java bin: %s\n' "$java_bin"
printf '  TMPDIR: %s\n' "$tmp_dir"
printf '  Run token: %s\n' "$run_token"
printf '  Lock directory: %s\n' "$lock_path"
printf '  Temporary FAI: %s\n' "$tmp_fai"
printf '  Temporary DICT: %s\n' "$tmp_dict"
printf '  Temporary FASTA symlink for faidx: %s\n' "$tmp_fasta"
printf '  FAI state: %s\n' "$fai_state"
printf '  DICT state: %s\n' "$dict_state"
printf '  Mode: %s\n' "$mode"

printf 'Lock acquisition action:\n'
printf 'mkdir %q\n' "$lock_path"
printf 'Lock owner write action:\n'
printf 'printf %q %q %q\n' '%s\n' "run_token=$run_token" "$lock_owner_file"

printf 'samtools faidx command:\n'
print_command "${samtools_faidx_command[@]}"

printf 'GATK CreateSequenceDictionary command:\n'
print_command "${gatk_dict_command[@]}"

printf 'Validation plan:\n'
printf '  1. Verify reference FASTA exists and is nonempty.\n'
printf '  2. Resolve samtools, GATK, and Java executables.\n'
printf '  3. Validate actual Java version is >=17 before execute-mode GATK use.\n'
printf '  4. Generate only missing sidecars into run-token temp paths.\n'
printf '  5. Validate FAI and DICT contig names and lengths agree before publishing.\n'
printf '  6. Reuse existing valid sidecars without overwriting them.\n'

if [[ "$execute" != true ]]; then
    printf 'Dry-run only. Add --execute to write missing sidecars.\n'
    exit 0
fi

[[ -d "$tmp_dir" ]] || die2 "TMPDIR does not exist or is not a directory: $tmp_dir"
[[ -w "$tmp_dir" ]] || die2 "TMPDIR is not writable: $tmp_dir"
[[ ! -e "$tmp_fai" ]] || die "Temporary FASTA index path already exists: $tmp_fai"
[[ ! -e "$tmp_dict" ]] || die "Temporary sequence dictionary path already exists: $tmp_dict"
[[ ! -e "$tmp_fasta" ]] || die "Temporary FASTA symlink path already exists: $tmp_fasta"
[[ ! -e "$tmp_fasta_fai" ]] || die "Temporary samtools FASTA index path already exists: $tmp_fasta_fai"

trap cleanup EXIT
acquire_lock "Step 00c"

validate_and_print_java \
    "GATK reference prep" \
    JAVA_BIN \
    JAVA_VERSION_OUTPUT \
    "Java version:" \
    17 \
    "Set JAVA_BIN_OVERRIDE to a Java 17 executable." \
    "$java_bin"

printf 'GATK version:\n'
"$gatk_bin" --version 2>&1 || die2 "GATK version check failed: $gatk_bin"

need_fai=false
need_dict=false

if [[ ! -e "$fai_path" ]]; then
    need_fai=true
fi

if [[ ! -e "$dict_path" ]]; then
    need_dict=true
fi

if [[ "$need_fai" == false && "$need_dict" == false ]]; then
    validate_sidecar_agreement "$fai_path" "$dict_path"
    printf 'Existing GATK reference sidecars are already present and valid; nothing to regenerate.\n'
    exit 0
fi

if [[ "$need_fai" == true ]]; then
    (
        cd "$reference_dir"
        ln -s "$reference_base" "$tmp_fasta_base"
    )
    "${samtools_faidx_command[@]}"
    mv "$tmp_fasta_fai" "$tmp_fai"
    tmp_fai_created=true
    validate_fai_file "$tmp_fai"
fi

if [[ "$need_dict" == true ]]; then
    "${gatk_dict_command[@]}"
    tmp_dict_created=true
    validate_dict_file "$tmp_dict"
fi

validation_fai="$fai_path"
validation_dict="$dict_path"

if [[ "$need_fai" == true ]]; then
    validation_fai="$tmp_fai"
fi

if [[ "$need_dict" == true ]]; then
    validation_dict="$tmp_dict"
fi

validate_sidecar_agreement "$validation_fai" "$validation_dict"

if [[ "$need_fai" == true ]]; then
    mv "$tmp_fai" "$fai_path"
    published_fai=true
fi

if [[ "$need_dict" == true ]]; then
    mv "$tmp_dict" "$dict_path"
    published_dict=true
fi

validate_sidecar_agreement "$fai_path" "$dict_path"

printf 'GATK reference sidecar output details:\n'
ls -lh "$fai_path" "$dict_path"

if [[ "$published_fai" == true || "$published_dict" == true ]]; then
    printf 'Created missing Step 00c sidecars successfully.\n'
else
    printf 'Step 00c sidecars were already valid.\n'
fi
