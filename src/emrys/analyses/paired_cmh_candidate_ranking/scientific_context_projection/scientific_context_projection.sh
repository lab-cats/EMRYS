#!/usr/bin/env bash
# shellcheck disable=SC2154
# Internal scientific worker; the Run task runner owns publication and recovery.
set -euo pipefail
# Required argument variables are initialized by declare_required_arguments.

usage() {
    cat <<'USAGE'
Project sequence context and motif evidence for paired-CMH candidates.

Usage: src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/scientific_context_projection.sh \
  --analysis-id ANALYSIS_ID \
  --step09-all-sites STEP09_ALL_SITES \
  --step09-significant-sites STEP09_SIGNIFICANT_SITES \
  --step09-summary STEP09_SUMMARY \
  --reference-fasta REFERENCE_FASTA \
  --reference-fai REFERENCE_FAI \
  --candidate-context-output CANDIDATE_CONTEXT_OUTPUT \
  --motif-hits-output MOTIF_HITS_OUTPUT \
  --sequence-logo-output SEQUENCE_LOGO_OUTPUT \
  --motif-statistics-output MOTIF_STATISTICS_OUTPUT \
  --context-receipt-output CONTEXT_RECEIPT_OUTPUT \
  --candidate-context-final CANDIDATE_CONTEXT_FINAL \
  --motif-hits-final MOTIF_HITS_FINAL \
  --sequence-logo-final SEQUENCE_LOGO_FINAL \
  --motif-statistics-final MOTIF_STATISTICS_FINAL \
  --git-commit GIT_COMMIT \
  [--motif-catalog MOTIF_CATALOG] \
  [--rscript-bin RSCRIPT_BIN] \
  [--r-script R_SCRIPT]

Internal worker: requires an existing EMRYS_TASK_WORK_DIR supplied by the runner.
Output destinations are staging paths supplied by the runner.
  -h, --help  Show this help message and exit.
USAGE
}

script_dir="$(dirname -- "${BASH_SOURCE[0]}")"
# shellcheck source=../../../libraries/argument_parsing.sh
source "$script_dir/../../../libraries/argument_parsing.sh"
# shellcheck source=../../../libraries/executable_resolution.sh
source "$script_dir/../../../libraries/executable_resolution.sh"
# shellcheck source=../../../libraries/file_checks.sh
source "$script_dir/../../../libraries/file_checks.sh"

declare_required_arguments analysis_id step09_all_sites step09_significant_sites step09_summary reference_fasta reference_fai candidate_context_output motif_hits_output sequence_logo_output motif_statistics_output context_receipt_output candidate_context_final motif_hits_final sequence_logo_final motif_statistics_final git_commit
motif_catalog="$script_dir/resources/pum_motifs_v1.tsv"
rscript_bin=""
r_script="$script_dir/scientific_context_projection.R"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --analysis-id) assign_option_value "$1" "${2:-}" analysis_id; shift 2 ;;
        --step09-all-sites) assign_option_value "$1" "${2:-}" step09_all_sites; shift 2 ;;
        --step09-significant-sites) assign_option_value "$1" "${2:-}" step09_significant_sites; shift 2 ;;
        --step09-summary) assign_option_value "$1" "${2:-}" step09_summary; shift 2 ;;
        --reference-fasta) assign_option_value "$1" "${2:-}" reference_fasta; shift 2 ;;
        --reference-fai) assign_option_value "$1" "${2:-}" reference_fai; shift 2 ;;
        --candidate-context-output) assign_option_value "$1" "${2:-}" candidate_context_output; shift 2 ;;
        --motif-hits-output) assign_option_value "$1" "${2:-}" motif_hits_output; shift 2 ;;
        --sequence-logo-output) assign_option_value "$1" "${2:-}" sequence_logo_output; shift 2 ;;
        --motif-statistics-output) assign_option_value "$1" "${2:-}" motif_statistics_output; shift 2 ;;
        --context-receipt-output) assign_option_value "$1" "${2:-}" context_receipt_output; shift 2 ;;
        --candidate-context-final) assign_option_value "$1" "${2:-}" candidate_context_final; shift 2 ;;
        --motif-hits-final) assign_option_value "$1" "${2:-}" motif_hits_final; shift 2 ;;
        --sequence-logo-final) assign_option_value "$1" "${2:-}" sequence_logo_final; shift 2 ;;
        --motif-statistics-final) assign_option_value "$1" "${2:-}" motif_statistics_final; shift 2 ;;
        --git-commit) assign_option_value "$1" "${2:-}" git_commit; shift 2 ;;
        --motif-catalog) assign_option_value "$1" "${2:-}" motif_catalog; shift 2 ;;
        --rscript-bin) assign_option_value "$1" "${2:-}" rscript_bin; shift 2 ;;
        --r-script) assign_option_value "$1" "${2:-}" r_script; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
done
require_arguments
require_task_work_dir

row_count() {
    awk 'END { print (NR > 0 ? NR - 1 : -1) }' "$1"
}

validate_receipt_payloads() {
    local context_path="$1"
    local hits_path="$2"
    local logo_path="$3"
    local statistics_path="$4"
    local receipt_path="$5"
    local context_hash hits_hash logo_hash statistics_hash
    local context_rows hits_rows logo_rows statistics_rows

    validate_nonempty_file "Candidate context" "$context_path"
    validate_nonempty_file "Motif hits" "$hits_path"
    validate_nonempty_file "Sequence logo" "$logo_path"
    validate_nonempty_file "Motif statistics" "$statistics_path"
    validate_nonempty_file "Scientific-context receipt" "$receipt_path"
    context_hash="$(sha256_file "$context_path")"
    hits_hash="$(sha256_file "$hits_path")"
    logo_hash="$(sha256_file "$logo_path")"
    statistics_hash="$(sha256_file "$statistics_path")"
    context_rows="$(row_count "$context_path")"
    hits_rows="$(row_count "$hits_path")"
    logo_rows="$(row_count "$logo_path")"
    statistics_rows="$(row_count "$statistics_path")"

    awk -F '\t' \
        -v context_hash="$context_hash" -v context_rows="$context_rows" \
        -v hits_hash="$hits_hash" -v hits_rows="$hits_rows" \
        -v logo_hash="$logo_hash" -v logo_rows="$logo_rows" \
        -v statistics_hash="$statistics_hash" -v statistics_rows="$statistics_rows" '
        NR == 1 {
            for (field = 1; field <= NF; field++) column_index[$field] = field
            required["candidate_context_sha256"] = context_hash
            required["candidate_context_row_count"] = context_rows
            required["motif_hits_sha256"] = hits_hash
            required["motif_hits_row_count"] = hits_rows
            required["sequence_logo_sha256"] = logo_hash
            required["sequence_logo_row_count"] = logo_rows
            required["motif_statistics_sha256"] = statistics_hash
            required["motif_statistics_row_count"] = statistics_rows
            for (name in required) {
                if (!(name in column_index)) {
                    printf "Scientific-context receipt is missing %s.\n", name > "/dev/stderr"
                    exit 1
                }
            }
            next
        }
        NR == 2 {
            for (name in required) {
                if ($(column_index[name]) != required[name]) {
                    printf "Scientific-context receipt %s does not reconcile.\n", name > "/dev/stderr"
                    exit 1
                }
            }
            row_count++
            next
        }
        { exit 1 }
        END { if (row_count != 1) exit 1 }
    ' "$receipt_path" || die "Scientific-context receipt does not bind its four payloads."
}

validate_safe_id "--analysis-id" "$analysis_id"
[[ "$git_commit" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]] || die "--git-commit must be a full lowercase Git object ID."
rscript_bin="$(resolve_executable_value "Rscript" "$rscript_bin" "Rscript")"
validate_nonempty_file "R projection script" "$r_script"
validate_nonempty_file "step09 all sites" "$step09_all_sites"
step09_all_sites_sha256="$(sha256_file "$step09_all_sites")"
validate_nonempty_file "step09 significant sites" "$step09_significant_sites"
step09_significant_sites_sha256="$(sha256_file "$step09_significant_sites")"
validate_nonempty_file "step09 summary" "$step09_summary"
step09_summary_sha256="$(sha256_file "$step09_summary")"
validate_nonempty_file "reference fasta" "$reference_fasta"
reference_fasta_sha256="$(sha256_file "$reference_fasta")"
validate_nonempty_file "reference fai" "$reference_fai"
reference_fai_sha256="$(sha256_file "$reference_fai")"
validate_nonempty_file "motif catalog" "$motif_catalog"
motif_catalog_sha256="$(sha256_file "$motif_catalog")"

r_command=("$rscript_bin")
if [[ "${EMRYS_LOCAL_PILOT_R:-0}" == 1 ]]; then
    r_command+=(--no-environ --no-site-file --no-restore --no-save)
fi
r_command+=(
    "$r_script"
    --analysis-id "$analysis_id"
    --step09-all-sites "$step09_all_sites"
    --step09-significant-sites "$step09_significant_sites"
    --step09-summary "$step09_summary"
    --step09-all-sites-sha256 "$step09_all_sites_sha256"
    --step09-significant-sites-sha256 "$step09_significant_sites_sha256"
    --step09-summary-sha256 "$step09_summary_sha256"
    --reference-fasta "$reference_fasta"
    --reference-fasta-sha256 "$reference_fasta_sha256"
    --reference-fai "$reference_fai"
    --reference-fai-sha256 "$reference_fai_sha256"
    --motif-catalog "$motif_catalog"
    --motif-catalog-sha256 "$motif_catalog_sha256"
    --candidate-context-output "$candidate_context_output"
    --motif-hits-output "$motif_hits_output"
    --sequence-logo-output "$sequence_logo_output"
    --motif-statistics-output "$motif_statistics_output"
    --context-receipt-output "$context_receipt_output"
    --candidate-context-final "$candidate_context_final"
    --motif-hits-final "$motif_hits_final"
    --sequence-logo-final "$sequence_logo_final"
    --motif-statistics-final "$motif_statistics_final"
    --git-commit "$git_commit"
)

print_command "${r_command[@]}"
"${r_command[@]}"
validate_receipt_payloads "$candidate_context_output" "$motif_hits_output" \
    "$sequence_logo_output" "$motif_statistics_output" "$context_receipt_output"
