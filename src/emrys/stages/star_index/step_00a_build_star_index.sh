#!/usr/bin/env bash
# Build and publish one STAR genome index from explicit materialized references.
#
# Dry-run validates inputs and prints the exact command and publication plan
# without creating directories, locks, staging paths, or index members.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  bash src/emrys/stages/star_index/step_00a_build_star_index.sh \
    --reference-fasta REFERENCE_FASTA \
    --reference-gtf REFERENCE_GTF \
    --index-dir INDEX_DIR \
    --threads THREADS \
    --sjdb-overhang SJDB_OVERHANG \
    --genome-sa-index-nbases GENOME_SA_INDEX_NBASES \
    [--star-bin STAR_BIN] \
    [--execute]

Build and publish one STAR genome index from explicit materialized references.

By default this script runs in dry-run mode. It validates the references and
STAR executable and prints the exact staging, command, validation, and publish
plan without writing anything. Add --execute to run STAR.

Required arguments:
  --reference-fasta  Existing nonempty reference FASTA.
  --reference-gtf    Existing nonempty reference GTF.
  --index-dir        Absent final STAR index directory.
  --threads          Positive STAR thread count.
  --sjdb-overhang    Non-negative STAR splice-junction overhang.
  --genome-sa-index-nbases
                     Positive STAR genome suffix-array index length.

Options:
  --star-bin         STAR executable or path. Resolution order: argument,
                     STAR_BIN_OVERRIDE, PATH.
  --execute          Execute and publish. Without this flag, plan only.
  -h, --help         Show this help message and exit.
USAGE
}

script_dir="${BASH_SOURCE[0]%/*}"
if [[ "$script_dir" == "$BASH_SOURCE[0]" ]]; then
    script_dir="."
fi
# shellcheck source=../../libraries/argument_parsing.sh
source "$script_dir/../../libraries/argument_parsing.sh"
# shellcheck source=../../libraries/executable_resolution.sh
source "$script_dir/../../libraries/executable_resolution.sh"
# shellcheck source=../../libraries/file_checks.sh
source "$script_dir/../../libraries/file_checks.sh"
# shellcheck source=../../libraries/signal_traps.sh
source "$script_dir/../../libraries/signal_traps.sh"

declare_required_arguments \
    reference_fasta reference_gtf index_dir threads sjdb_overhang genome_sa_index_nbases
star_bin_arg=""
execute=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --reference-fasta) assign_option_value "$1" "${2:-}" reference_fasta; shift 2 ;;
        --reference-gtf) assign_option_value "$1" "${2:-}" reference_gtf; shift 2 ;;
        --index-dir) assign_option_value "$1" "${2:-}" index_dir; shift 2 ;;
        --threads) assign_option_value "$1" "${2:-}" threads; shift 2 ;;
        --sjdb-overhang) assign_option_value "$1" "${2:-}" sjdb_overhang; shift 2 ;;
        --genome-sa-index-nbases) assign_option_value "$1" "${2:-}" genome_sa_index_nbases; shift 2 ;;
        --star-bin) assign_option_value "$1" "${2:-}" star_bin_arg; shift 2 ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

require_arguments
[[ -f "$reference_fasta" && ! -L "$reference_fasta" && -s "$reference_fasta" ]] ||
    die "Reference FASTA must be a nonempty regular file, not a symlink: $reference_fasta"
[[ -f "$reference_gtf" && ! -L "$reference_gtf" && -s "$reference_gtf" ]] ||
    die "Reference GTF must be a nonempty regular file, not a symlink: $reference_gtf"
validate_positive_integer "--threads" "$threads"
validate_nonnegative_integer "--sjdb-overhang" "$sjdb_overhang"
validate_positive_integer "--genome-sa-index-nbases" "$genome_sa_index_nbases"

star_value="${star_bin_arg:-${STAR_BIN_OVERRIDE:-}}"
star_bin="$(resolve_executable_value "STAR" "$star_value" "STAR")"
reference_fasta_sha256="$(sha256_file "$reference_fasta")"
reference_gtf_sha256="$(sha256_file "$reference_gtf")"

index_parent="$(dirname -- "$index_dir")"
index_base="$(basename -- "$index_dir")"
run_token="${EMRYS_RUN_TOKEN:-${SLURM_JOB_ID:-$$}}"
validate_safe_id "STAR index run token" "$run_token"

lock_path="$index_parent/.${index_base}.step00a.lock"
lock_owner_file="$lock_path/owner"
staged_index="$index_parent/.${index_base}.step00a.${run_token}.tmp"

lock_acquired=false
staged_index_created=false
final_index_reserved=false
publication_complete=false

required_index_members=(
    genomeParameters.txt
    Genome
    SA
    SAindex
    chrLength.txt
    chrName.txt
    chrNameLength.txt
    chrStart.txt
    exonGeTrInfo.tab
    exonInfo.tab
    geneInfo.tab
    sjdbInfo.txt
    sjdbList.fromGTF.out.tab
    sjdbList.out.tab
    transcriptInfo.tab
)

validate_index_members() {
    local candidate="$1"
    local member

    [[ -d "$candidate" && ! -L "$candidate" ]] ||
        die "STAR index is not a real directory: $candidate"
    for member in "${required_index_members[@]}"; do
        [[ -f "$candidate/$member" && ! -L "$candidate/$member" && -s "$candidate/$member" ]] ||
            die "STAR index member is missing, empty, or not a regular file: $candidate/$member"
    done
}

require_exact_owned_publication() {
    local final_member staged_member member_name
    local -a final_members=()

    shopt -s dotglob nullglob
    final_members=("$index_dir"/*)
    shopt -u dotglob nullglob

    [[ "${#final_members[@]}" -eq "${#staged_members[@]}" ]] ||
        die "STAR index final member set changed during publication; preserving recovery state: $index_dir"
    for final_member in "${final_members[@]}"; do
        [[ -f "$final_member" && ! -L "$final_member" ]] ||
            die "Published STAR index contains a non-regular or foreign member: $final_member"
    done
    for staged_member in "${staged_members[@]}"; do
        member_name="${staged_member##*/}"
        [[ -f "$index_dir/$member_name" && ! -L "$index_dir/$member_name" &&
           "$index_dir/$member_name" -ef "$staged_member" ]] ||
            die "Published STAR index member no longer matches its staging anchor: $index_dir/$member_name"
    done
}

require_clean_boundary() {
    local residue

    if [[ -e "$index_dir" || -L "$index_dir" ]]; then
        die "STAR index output already exists; refusing to replace: $index_dir"
    fi
    if [[ -e "$lock_path" || -L "$lock_path" ]]; then
        die "Step 00a publication lock already exists: $lock_path"
    fi
    for residue in "$index_parent"/."$index_base".step00a.*.tmp; do
        if [[ -e "$residue" || -L "$residue" ]]; then
            die "Step 00a staging residue requires inspection: $residue"
        fi
    done
}

cleanup() {
    local status="$1"
    local rollback_ok=true
    set +e

    # Once the absent final directory has been reserved, any failure leaves a
    # visibly incomplete transaction.  Preserve that directory, the staging
    # directory, and the owned lock: removing a path here could delete bytes
    # installed by an uncoordinated writer after reservation.
    if [[ "$status" -ne 0 && "$publication_complete" != true && "$final_index_reserved" == true ]]; then
        printf 'ERROR: Step 00a publication was incomplete; preserving final, lock, and residue for inspection: %s\n' \
            "$index_dir" >&2
        return
    fi
    if [[ "$staged_index_created" == true ]]; then
        if rm -rf -- "$staged_index"; then
            staged_index_created=false
        else
            rollback_ok=false
        fi
    fi

    if [[ "$rollback_ok" == true ]]; then
        remove_owned_lock
    else
        printf 'ERROR: Step 00a rollback was incomplete; preserving lock and residue for inspection: %s\n' \
            "$lock_path" >&2
    fi
}

star_command=(
    "$star_bin"
    --runThreadN "$threads"
    --runMode genomeGenerate
    --genomeDir "$staged_index"
    --genomeFastaFiles "$reference_fasta"
    --sjdbGTFfile "$reference_gtf"
    --sjdbOverhang "$sjdb_overhang"
    --genomeSAindexNbases "$genome_sa_index_nbases"
)

require_clean_boundary

mode="dry-run"
if [[ "$execute" == true ]]; then
    mode="execute"
fi

printf 'STAR index context\n'
printf '  Reference FASTA: %s\n' "$reference_fasta"
printf '  Reference FASTA SHA-256: %s\n' "$reference_fasta_sha256"
printf '  Reference GTF: %s\n' "$reference_gtf"
printf '  Reference GTF SHA-256: %s\n' "$reference_gtf_sha256"
printf '  Final index directory: %s\n' "$index_dir"
printf '  Staged index directory: %s\n' "$staged_index"
printf '  Lock directory: %s\n' "$lock_path"
printf '  STAR executable: %s\n' "$star_bin"
printf '  Threads: %s\n' "$threads"
printf '  sjdbOverhang: %s\n' "$sjdb_overhang"
printf '  genomeSAindexNbases: %s\n' "$genome_sa_index_nbases"
printf '  Run token: %s\n' "$run_token"
printf '  Mode: %s\n' "$mode"

printf 'STAR genomeGenerate command:\n'
print_command "${star_command[@]}"

printf 'Publication plan:\n'
printf '  1. Acquire the create-exclusive owner lock: %s\n' "$lock_path"
printf '  2. Generate into the absent staging directory: %s\n' "$staged_index"
printf '  3. Require all %s declared STAR index members to be nonempty regular files.\n' \
    "${#required_index_members[@]}"
printf '  4. Reserve the absent final directory, then link every staged member into it: %s\n' "$index_dir"
printf '  5. Require exact final/staged membership and inode ownership before commit.\n'
printf 'Failure plan:\n'
printf '  Controlled failures and trapped signals remove only owned staging/publication state; unowned or kill-residue remains blocking evidence.\n'

if [[ "$execute" != true ]]; then
    printf 'Dry-run only. Add --execute to build and publish the STAR index.\n'
    exit 0
fi

mkdir -p "$index_parent"
require_clean_boundary
set_exit_trap cleanup
acquire_lock "Step 00a"

mkdir "$staged_index"
staged_index_created=true
"${star_command[@]}"
validate_index_members "$staged_index"
[[ "$(sha256_file "$reference_fasta")" == "$reference_fasta_sha256" ]] ||
    die "Reference FASTA changed during Step 00a: $reference_fasta"
[[ "$(sha256_file "$reference_gtf")" == "$reference_gtf_sha256" ]] ||
    die "Reference GTF changed during Step 00a: $reference_gtf"

[[ ! -e "$index_dir" && ! -L "$index_dir" ]] ||
    die "STAR index output appeared during execution; refusing to replace: $index_dir"
if ! mkdir "$index_dir" 2>/dev/null; then
    die "STAR index output appeared during execution; refusing to replace: $index_dir"
fi
final_index_reserved=true

shopt -s dotglob nullglob
staged_members=("$staged_index"/*)
shopt -u dotglob nullglob
[[ "${#staged_members[@]}" -gt 0 ]] ||
    die "STAR index staging directory is empty: $staged_index"
for staged_member in "${staged_members[@]}"; do
    member_name="${staged_member##*/}"
    [[ -f "$staged_member" && ! -L "$staged_member" ]] ||
        die "STAR index staging contains a non-regular member: $staged_member"
    if ! ln -- "$staged_member" "$index_dir/$member_name"; then
        die "STAR index member appeared during publication; refusing to replace: $index_dir/$member_name"
    fi
done
validate_index_members "$index_dir"
require_exact_owned_publication
publication_complete=true

rm -f -- "${staged_members[@]}"
rmdir "$staged_index"
staged_index_created=false

remove_owned_lock

printf 'STAR index publication complete: %s\n' "$index_dir"
