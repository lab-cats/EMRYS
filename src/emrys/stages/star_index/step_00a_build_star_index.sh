#!/usr/bin/env bash
# shellcheck disable=SC2154
# Internal scientific worker; the Run task runner owns publication and recovery.
set -euo pipefail
# Required argument variables are initialized by declare_required_arguments.

usage() {
    cat <<'USAGE'
Build one STAR genome index.

Usage: src/emrys/stages/star_index/step_00a_build_star_index.sh \
  --reference-fasta REFERENCE_FASTA \
  --reference-gtf REFERENCE_GTF \
  --index-dir INDEX_DIR \
  --threads THREADS \
  --sjdb-overhang SJDB_OVERHANG \
  --genome-sa-index-nbases GENOME_SA_INDEX_NBASES \
  --star-bin STAR_BIN

Internal worker: requires an existing EMRYS_TASK_WORK_DIR supplied by the runner.
Output destinations are staging paths supplied by the runner.
  -h, --help  Show this help message and exit.
USAGE
}

script_dir="$(dirname -- "${BASH_SOURCE[0]}")"
# shellcheck source=../../libraries/argument_parsing.sh
source "$script_dir/../../libraries/argument_parsing.sh"
# shellcheck source=../../libraries/file_checks.sh
source "$script_dir/../../libraries/file_checks.sh"

declare_required_arguments reference_fasta reference_gtf index_dir threads sjdb_overhang genome_sa_index_nbases star_bin

while [[ $# -gt 0 ]]; do
    case "$1" in
        --reference-fasta) assign_option_value "$1" "${2:-}" reference_fasta; shift 2 ;;
        --reference-gtf) assign_option_value "$1" "${2:-}" reference_gtf; shift 2 ;;
        --index-dir) assign_option_value "$1" "${2:-}" index_dir; shift 2 ;;
        --threads) assign_option_value "$1" "${2:-}" threads; shift 2 ;;
        --sjdb-overhang) assign_option_value "$1" "${2:-}" sjdb_overhang; shift 2 ;;
        --genome-sa-index-nbases) assign_option_value "$1" "${2:-}" genome_sa_index_nbases; shift 2 ;;
        --star-bin) assign_option_value "$1" "${2:-}" star_bin; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
done
require_arguments
require_task_work_dir

validate_nonempty_file "Reference FASTA" "$reference_fasta"
validate_nonempty_file "Reference GTF" "$reference_gtf"
[[ -f "$reference_fasta" && ! -L "$reference_fasta" && -f "$reference_gtf" && ! -L "$reference_gtf" ]] ||
    die "Reference FASTA and GTF must be regular files, not symlinks."
validate_positive_integer "--threads" "$threads"
validate_positive_integer "--genome-sa-index-nbases" "$genome_sa_index_nbases"
validate_nonnegative_integer "--sjdb-overhang" "$sjdb_overhang"
require_executable "STAR" "$star_bin"
required_index_members=(
    genomeParameters.txt Genome SA SAindex chrLength.txt chrName.txt
    chrNameLength.txt chrStart.txt exonGeTrInfo.tab exonInfo.tab geneInfo.tab
    sjdbInfo.txt sjdbList.fromGTF.out.tab sjdbList.out.tab transcriptInfo.tab
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

"$star_bin" --runThreadN "$threads" --runMode genomeGenerate \
    --genomeDir "$index_dir" --genomeFastaFiles "$reference_fasta" \
    --sjdbGTFfile "$reference_gtf" --sjdbOverhang "$sjdb_overhang" \
    --genomeSAindexNbases "$genome_sa_index_nbases"
validate_index_members "$index_dir"
# STAR's additional top-level files travel with the complete index directory.
shopt -s nullglob dotglob
for member in "$index_dir"/*; do
    [[ -f "$member" && ! -L "$member" ]] ||
        die "STAR index member is not a regular file: $member"
done
