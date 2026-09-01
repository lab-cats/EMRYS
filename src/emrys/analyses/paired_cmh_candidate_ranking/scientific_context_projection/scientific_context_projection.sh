#!/usr/bin/env bash
# Build one receipt-last scientific-context projection from admitted Step 09
# records and an exact indexed reference. Dry-run is the default.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=../../../libraries/argument_parsing.sh
source "$script_dir/../../../libraries/argument_parsing.sh"
# shellcheck source=../../../libraries/executable_resolution.sh
source "$script_dir/../../../libraries/executable_resolution.sh"
# shellcheck source=../../../libraries/file_checks.sh
source "$script_dir/../../../libraries/file_checks.sh"

usage() {
    cat <<'USAGE'
Usage:
  src/emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/scientific_context_projection.sh \
    --analysis-id ANALYSIS_ID \
    --step09-all-sites STEP09_ALL_SITES \
    --step09-significant-sites STEP09_SIGNIFICANT_SITES \
    --step09-summary STEP09_SUMMARY \
    --reference-fasta REFERENCE_FASTA \
    --reference-fai REFERENCE_FAI \
    --output-root OUTPUT_ROOT \
    --git-commit COMMIT \
    [--motif-catalog MOTIF_CATALOG] \
    [--rscript-bin RSCRIPT_BIN] \
    [--r-script R_SCRIPT] \
    [--no-clobber] \
    [--execute]

Project Step 09 calls into continuous genomic sequence context, exact known
PUM-motif hits, logo frequencies, and motif statistics. The owner does not
read BAMs, rerun Step 09 significance, discover motifs, or render figures.

Dry-run validates and hashes every declared input, then prints the exact R and
publication plan without creating output paths. Execute mode publishes four
payload TSVs and the context receipt last as one rollback-protected set.
USAGE
}

analysis_id=""
step09_all_sites=""
step09_significant_sites=""
step09_summary=""
reference_fasta=""
reference_fai=""
output_root=""
git_commit=""
motif_catalog="$script_dir/resources/pum_motifs_v1.tsv"
rscript_bin_arg=""
r_script="${SCIENTIFIC_CONTEXT_R_SCRIPT:-$script_dir/scientific_context_projection.R}"
no_clobber=false
execute=false

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --analysis-id) require_value "$1" "${2:-}"; analysis_id="$2"; shift 2 ;;
        --step09-all-sites) require_value "$1" "${2:-}"; step09_all_sites="$2"; shift 2 ;;
        --step09-significant-sites) require_value "$1" "${2:-}"; step09_significant_sites="$2"; shift 2 ;;
        --step09-summary) require_value "$1" "${2:-}"; step09_summary="$2"; shift 2 ;;
        --reference-fasta) require_value "$1" "${2:-}"; reference_fasta="$2"; shift 2 ;;
        --reference-fai) require_value "$1" "${2:-}"; reference_fai="$2"; shift 2 ;;
        --output-root) require_value "$1" "${2:-}"; output_root="$2"; shift 2 ;;
        --git-commit) require_value "$1" "${2:-}"; git_commit="$2"; shift 2 ;;
        --motif-catalog) require_value "$1" "${2:-}"; motif_catalog="$2"; shift 2 ;;
        --rscript-bin) require_value "$1" "${2:-}"; rscript_bin_arg="$2"; shift 2 ;;
        --r-script) require_value "$1" "${2:-}"; r_script="$2"; shift 2 ;;
        --no-clobber) no_clobber=true; shift ;;
        --execute) execute=true; shift ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
done

for required in \
    analysis_id step09_all_sites step09_significant_sites step09_summary \
    reference_fasta reference_fai output_root git_commit
do
    [[ -n "${!required}" ]] || die "Missing required argument: --${required//_/-}"
done
validate_safe_id "analysis_id" "$analysis_id"
validate_nonempty_file "Step 09 all-sites" "$step09_all_sites"
validate_nonempty_file "Step 09 significant-sites" "$step09_significant_sites"
validate_nonempty_file "Step 09 summary" "$step09_summary"
validate_nonempty_file "Reference FASTA" "$reference_fasta"
validate_nonempty_file "Reference FAI" "$reference_fai"
validate_nonempty_file "PUM motif catalog" "$motif_catalog"
validate_nonempty_file "Scientific-context R program" "$r_script"
[[ "$git_commit" =~ ^[0-9a-f]{40}([0-9a-f]{24})?$ ]] ||
    die "Source commit is not a full 40- or 64-character digest: $git_commit"

rscript_value="${rscript_bin_arg:-${RSCRIPT_BIN_OVERRIDE:-Rscript}}"
rscript_bin="$(resolve_executable_value "Rscript" "$rscript_value" "Rscript")"

step09_all_sites_sha256="$(sha256_file "$step09_all_sites")"
step09_significant_sites_sha256="$(sha256_file "$step09_significant_sites")"
step09_summary_sha256="$(sha256_file "$step09_summary")"
reference_fasta_sha256="$(sha256_file "$reference_fasta")"
reference_fai_sha256="$(sha256_file "$reference_fai")"
motif_catalog_sha256="$(sha256_file "$motif_catalog")"

analysis_dir="$output_root/$analysis_id"
final_context="$analysis_dir/$analysis_id.candidate_context.tsv"
final_hits="$analysis_dir/$analysis_id.motif_hits.tsv"
final_logo="$analysis_dir/$analysis_id.sequence_logo.tsv"
final_statistics="$analysis_dir/$analysis_id.motif_statistics.tsv"
final_receipt="$analysis_dir/$analysis_id.context_receipt.tsv"
finals=(
    "$final_context" "$final_hits" "$final_logo" "$final_statistics"
    "$final_receipt"
)

run_token="${EMRYS_RUN_TOKEN:-${SLURM_JOB_ID:-$$}}"
validate_safe_id "run token" "$run_token"
tmp_context="$analysis_dir/.$analysis_id.scientific-context.$run_token.candidate.tmp.tsv"
tmp_hits="$analysis_dir/.$analysis_id.scientific-context.$run_token.hits.tmp.tsv"
tmp_logo="$analysis_dir/.$analysis_id.scientific-context.$run_token.logo.tmp.tsv"
tmp_statistics="$analysis_dir/.$analysis_id.scientific-context.$run_token.statistics.tmp.tsv"
tmp_receipt="$analysis_dir/.$analysis_id.scientific-context.$run_token.receipt.tmp.tsv"
temps=("$tmp_context" "$tmp_hits" "$tmp_logo" "$tmp_statistics" "$tmp_receipt")
backups=()
for final in "${finals[@]}"; do
    backups+=("$analysis_dir/.$(basename "$final").$run_token.previous")
done
lock_path="$analysis_dir/.$analysis_id.scientific-context.lock"
lock_owner_tmp="$lock_path/.owner.$run_token.tmp"

confirm_inputs_unchanged() {
    [[ "$(sha256_file "$step09_all_sites")" == "$step09_all_sites_sha256" ]] ||
        die "Step 09 all-sites changed during scientific-context projection: $step09_all_sites"
    [[ "$(sha256_file "$step09_significant_sites")" == "$step09_significant_sites_sha256" ]] ||
        die "Step 09 significant-sites changed during scientific-context projection: $step09_significant_sites"
    [[ "$(sha256_file "$step09_summary")" == "$step09_summary_sha256" ]] ||
        die "Step 09 summary changed during scientific-context projection: $step09_summary"
    [[ "$(sha256_file "$reference_fasta")" == "$reference_fasta_sha256" ]] ||
        die "Reference FASTA changed during scientific-context projection: $reference_fasta"
    [[ "$(sha256_file "$reference_fai")" == "$reference_fai_sha256" ]] ||
        die "Reference FAI changed during scientific-context projection: $reference_fai"
    [[ "$(sha256_file "$motif_catalog")" == "$motif_catalog_sha256" ]] ||
        die "PUM motif catalog changed during scientific-context projection: $motif_catalog"
}

fsync_regular_files() {
    "$durability_python" -X pycache_prefix=/dev/null -I -c '
import os
import stat
import sys

flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
for path in sys.argv[1:]:
    descriptor = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError(f"not a regular file: {path}")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
' "$@" || {
        printf 'ERROR: Could not fsync scientific-context staging files.\n' >&2
        return 1
    }
}

fsync_directory() {
    local directory="$1"
    "$durability_python" -X pycache_prefix=/dev/null -I -c '
import os
import stat
import sys

path = sys.argv[1]
flags = (
    os.O_RDONLY
    | getattr(os, "O_CLOEXEC", 0)
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
)
descriptor = os.open(path, flags)
try:
    if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
        raise OSError(f"not a directory: {path}")
    os.fsync(descriptor)
finally:
    os.close(descriptor)
' "$directory" || {
        printf 'ERROR: Could not fsync scientific-context directory: %s\n' \
            "$directory" >&2
        return 1
    }
}

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
    --candidate-context-output "$tmp_context"
    --motif-hits-output "$tmp_hits"
    --sequence-logo-output "$tmp_logo"
    --motif-statistics-output "$tmp_statistics"
    --context-receipt-output "$tmp_receipt"
    --candidate-context-final "$final_context"
    --motif-hits-final "$final_hits"
    --sequence-logo-final "$final_logo"
    --motif-statistics-final "$final_statistics"
    --git-commit "$git_commit"
)

printf 'Scientific-context projection:\n'
printf '  Mode: %s\n' "$([[ "$execute" == true ]] && printf execute || printf dry-run)"
printf '  Analysis ID: %s\n' "$analysis_id"
printf '  Step 09 all-sites: %s\n' "$step09_all_sites"
printf '  Step 09 significant-sites: %s\n' "$step09_significant_sites"
printf '  Step 09 summary: %s\n' "$step09_summary"
printf '  Reference FASTA / FAI: %s / %s\n' "$reference_fasta" "$reference_fai"
printf '  Motif catalog: %s\n' "$motif_catalog"
printf '  Output directory: %s\n' "$analysis_dir"
printf '  Existing-output policy: %s\n' \
    "$([[ "$no_clobber" == true ]] && printf no-clobber || printf replace-complete-set)"
printf '  Sequence policy: legacy_rna_change_oriented_genomic_v1 (mechanical; provisional)\n'
printf 'R command:\n'
print_command "${r_command[@]}"
printf 'Publication order (receipt last):\n'
printf '  %s\n' "${finals[@]}"

if [[ "$no_clobber" == true ]]; then
    require_no_owner_residue \
        "Scientific-context projection" "$analysis_dir" \
        ".${analysis_id}.scientific-context.*" \
        ".${analysis_id}.*.previous"
fi
preflight_final_count=0
for final in "${finals[@]}"; do
    [[ ! -L "$final" ]] || die "Scientific-context final path is a symlink: $final"
    [[ -e "$final" ]] && preflight_final_count=$((preflight_final_count + 1))
done
[[ "$preflight_final_count" -eq 0 || "$preflight_final_count" -eq 5 ]] ||
    die "Existing scientific-context outputs are incomplete; expected all five or none."
if [[ "$no_clobber" == true && "$preflight_final_count" -eq 5 ]]; then
    die "Refusing to replace a complete scientific-context transaction under --no-clobber."
fi
if [[ "$execute" != true ]]; then
    printf 'Dry-run only. No R process was invoked and no output path was created.\n'
    exit 0
fi

durability_python="${EMRYS_SHA256_PYTHON:-}"
if [[ -z "$durability_python" ]]; then
    durability_python="$(command -v python3 2>/dev/null || true)"
fi
[[ -n "$durability_python" && "$durability_python" == /* &&
   -x "$durability_python" ]] ||
    die "Scientific-context durability requires an absolute executable Python launcher."

lock_owned=false
lock_owner_written=false
scratch_owned=false
publication_started=false
publication_committed=false
previous_set=false
rollback_failed=false
backed_up_count=0
published_count=0

release_lock() {
    [[ "$lock_owned" == true ]] || return 0
    if [[ "$lock_owner_written" != true || ! -f "$lock_path/owner" ]] ||
       ! grep -Fqx $'run_token\t'"$run_token" "$lock_path/owner"; then
        printf 'ERROR: Cannot prove scientific-context lock ownership: %s\n' "$lock_path" >&2
        return 1
    fi
    local unexpected
    unexpected="$(find "$lock_path" -mindepth 1 -maxdepth 1 ! -path "$lock_path/owner" -print -quit)" || return 1
    [[ -z "$unexpected" ]] || {
        printf 'ERROR: Scientific-context lock contains unexpected residue: %s\n' "$unexpected" >&2
        return 1
    }
    rm -f "$lock_path/owner" || return 1
    rmdir "$lock_path" || return 1
    lock_owned=false
}

cleanup() {
    local status=$?
    local index
    trap - EXIT HUP INT TERM
    if [[ "$publication_started" == true && "$publication_committed" != true ]]; then
        if [[ "$no_clobber" == true ]]; then
            for ((index = 0; index < published_count; index++)); do
                remove_owned_published_file \
                    "Scientific-context output" "${temps[$index]}" "${finals[$index]}" ||
                    rollback_failed=true
            done
        else
            for index in "${!finals[@]}"; do
                if [[ "$previous_set" == true && "$index" -lt "$backed_up_count" ]]; then
                    if ! rm -f "${finals[$index]}"; then
                        rollback_failed=true
                    elif ! mv "${backups[$index]}" "${finals[$index]}"; then
                        rollback_failed=true
                    fi
                elif [[ "$previous_set" != true && "$index" -lt "$published_count" ]]; then
                    rm -f "${finals[$index]}" || rollback_failed=true
                fi
            done
        fi
        fsync_directory "$analysis_dir" || rollback_failed=true
    fi
    if [[ "$scratch_owned" == true &&
          ( "$rollback_failed" != true || "$no_clobber" != true ) ]]; then
        for path in "${temps[@]}"; do rm -f "$path" || true; done
    fi
    if [[ "$publication_committed" == true ]]; then
        for path in "${backups[@]}"; do rm -f "$path" || true; done
    fi
    if [[ "$rollback_failed" == true ]]; then
        [[ "$status" -ne 0 ]] || status=1
        printf 'ERROR: Scientific-context rollback was incomplete; preserving lock and residue: %s\n' "$lock_path" >&2
    elif [[ "$lock_owned" == true ]]; then
        release_lock || status=1
    fi
    exit "$status"
}

trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
mkdir -p "$analysis_dir"
if ! mkdir "$lock_path" 2>/dev/null; then
    die "Scientific-context lock already exists: $lock_path"
fi
lock_owned=true
printf 'run_token\t%s\npid\t%s\n' "$run_token" "$$" > "$lock_owner_tmp" ||
    die "Could not write scientific-context lock metadata."
mv "$lock_owner_tmp" "$lock_path/owner" ||
    die "Could not publish scientific-context lock metadata."
lock_owner_written=true

for path in "${temps[@]}" "${backups[@]}"; do
    [[ ! -e "$path" && ! -L "$path" ]] ||
        die "Refusing to reuse scientific-context scratch path: $path"
done
scratch_owned=true
final_count=0
for final in "${finals[@]}"; do
    [[ ! -L "$final" ]] || die "Scientific-context final path is a symlink: $final"
    [[ -e "$final" ]] && final_count=$((final_count + 1))
done
[[ "$final_count" -eq 0 || "$final_count" -eq 5 ]] ||
    die "Existing scientific-context outputs are incomplete; expected all five or none."
if [[ "$final_count" -eq 5 && "$no_clobber" == true ]]; then
    die "Refusing to replace a complete scientific-context transaction under --no-clobber."
fi
[[ "$final_count" -eq 5 ]] && previous_set=true

"${r_command[@]}" || die "Scientific-context R projection failed."
confirm_inputs_unchanged
validate_receipt_payloads \
    "$tmp_context" "$tmp_hits" "$tmp_logo" "$tmp_statistics" "$tmp_receipt"
fsync_regular_files "${temps[@]}" ||
    die "Could not make scientific-context staging files durable."
tmp_hashes=()
for temp in "${temps[@]}"; do tmp_hashes+=("$(sha256_file "$temp")"); done

publication_started=true
if [[ "$previous_set" == true ]]; then
    for index in "${!finals[@]}"; do
        mv "${finals[$index]}" "${backups[$index]}"
        backed_up_count=$((backed_up_count + 1))
    done
fi
if [[ "$no_clobber" == true ]]; then
    for index in 0 1 2 3; do
        publish_file_create_exclusive \
            "Scientific-context payload" "${temps[$index]}" "${finals[$index]}"
        published_count=$((published_count + 1))
    done
    publish_file_create_exclusive \
        "Scientific-context receipt" "$tmp_receipt" "$final_receipt"
    published_count=$((published_count + 1))
else
    for index in 0 1 2 3; do
        mv "${temps[$index]}" "${finals[$index]}"
        published_count=$((published_count + 1))
    done
    mv "$tmp_receipt" "$final_receipt"
    published_count=$((published_count + 1))
fi
fsync_directory "$analysis_dir" ||
    die "Could not make receipt-last scientific-context publication durable."

validate_receipt_payloads \
    "$final_context" "$final_hits" "$final_logo" "$final_statistics" "$final_receipt"
confirm_inputs_unchanged
for index in "${!finals[@]}"; do
    [[ "$(sha256_file "${finals[$index]}")" == "${tmp_hashes[$index]}" ]] ||
        die "Published scientific-context output changed: ${finals[$index]}"
done
if [[ "$no_clobber" == true ]]; then
    for index in "${!finals[@]}"; do
        require_owned_published_file \
            "Scientific-context output" "${temps[$index]}" "${finals[$index]}"
    done
    for temp in "${temps[@]}"; do rm -f -- "$temp"; done
fi
publication_committed=true
for backup in "${backups[@]}"; do rm -f "$backup"; done
release_lock

printf 'Scientific-context execute complete. Published receipt-last transaction:\n'
printf '  %s\n' "${finals[@]}"
