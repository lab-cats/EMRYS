#!/usr/bin/env bash
# shellcheck disable=SC2154
# Internal scientific worker; the Run task runner owns publication and recovery.
set -euo pipefail
# Required argument variables are initialized by declare_required_arguments.

usage() {
    cat <<'USAGE'
Build a FASTA index and GATK sequence dictionary.

Usage: src/emrys/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh \
  --reference-fasta REFERENCE_FASTA \
  --reference-fai-output REFERENCE_FAI_OUTPUT \
  --reference-dict-output REFERENCE_DICT_OUTPUT \
  [--samtools-bin SAMTOOLS_BIN] \
  [--gatk-bin GATK_BIN] \
  [--java-bin JAVA_BIN]

Internal worker: requires an existing EMRYS_TASK_WORK_DIR supplied by the runner.
Output destinations are staging paths supplied by the runner.
  -h, --help  Show this help message and exit.
USAGE
}

script_dir="$(dirname -- "${BASH_SOURCE[0]}")"
# shellcheck source=../../libraries/argument_parsing.sh
source "$script_dir/../../libraries/argument_parsing.sh"
# shellcheck source=../../libraries/executable_resolution.sh
source "$script_dir/../../libraries/executable_resolution.sh"
# shellcheck source=../../libraries/file_checks.sh
source "$script_dir/../../libraries/file_checks.sh"
# shellcheck source=../../libraries/gatk_invocation.sh
source "$script_dir/../../libraries/gatk_invocation.sh"

declare_required_arguments reference_fasta reference_fai_output reference_dict_output
samtools_bin=""
gatk_bin=""
java_bin=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --reference-fasta) assign_option_value "$1" "${2:-}" reference_fasta; shift 2 ;;
        --reference-fai-output) assign_option_value "$1" "${2:-}" reference_fai_output; shift 2 ;;
        --reference-dict-output) assign_option_value "$1" "${2:-}" reference_dict_output; shift 2 ;;
        --samtools-bin) assign_option_value "$1" "${2:-}" samtools_bin; shift 2 ;;
        --gatk-bin) assign_option_value "$1" "${2:-}" gatk_bin; shift 2 ;;
        --java-bin) assign_option_value "$1" "${2:-}" java_bin; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
done
require_arguments
require_task_work_dir

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

validate_nonempty_file "Reference FASTA" "$reference_fasta"
java_bin="$(resolve_overridable_executable "Java" "$java_bin" "JAVA_BIN_OVERRIDE" "java" "/bin/java")"
gatk_bin="$(resolve_overridable_executable "GATK" "$gatk_bin" "GATK_BIN_OVERRIDE" "gatk")"
samtools_bin="$(resolve_overridable_executable "samtools" "$samtools_bin" "SAMTOOLS_BIN_OVERRIDE" "samtools")"
validate_and_print_java "GATK" JAVA_BIN JAVA_VERSION_OUTPUT "Java version:" 17 \
    "Set JAVA_BIN_OVERRIDE to a Java 17 executable." "$java_bin"
printf 'GATK version:\n'
invoke_gatk_with_selected_java "$java_bin" "$gatk_bin" --version 2>&1 ||
    die2 "GATK version check failed: $gatk_bin"

# samtools faidx names its output after its input; isolate that naming in scratch.
reference_path="$(cd "$(dirname -- "$reference_fasta")" && pwd)/$(basename -- "$reference_fasta")"
faidx_input="$EMRYS_TASK_WORK_DIR/faidx_input"
ln -s "$reference_path" "$faidx_input"
"$samtools_bin" faidx "$faidx_input"
mv -- "$faidx_input.fai" "$reference_fai_output"
invoke_gatk_with_selected_java "$java_bin" "$gatk_bin" CreateSequenceDictionary \
    -R "$reference_fasta" -O "$reference_dict_output"
validate_sidecar_agreement "$reference_fai_output" "$reference_dict_output"
