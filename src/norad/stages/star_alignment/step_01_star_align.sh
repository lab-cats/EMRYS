#!/usr/bin/env bash
# Run STAR alignment for one paired-end RNA-seq sample.
#
# The script validates inputs and prints the STAR command in dry-run mode by
# default. Passing --execute runs STAR with the same validated parameters.
set -euo pipefail

# Print the command-line contract used by local smoke tests and SLURM wrappers.
usage() {
    cat <<'USAGE'
Usage:
  src/norad/stages/star_alignment/step_01_star_align.sh \
    --sample-id SAMPLE_ID \
    --r1-fastq R1_FASTQ \
    --r2-fastq R2_FASTQ \
    --star-index STAR_INDEX_DIR \
    --output-dir OUTPUT_DIR \
    --threads THREADS \
    [--star-bin STAR_BIN] \
    [--gunzip-bin PATH] \
    [--no-clobber] \
    [--execute]

Run STAR alignment for one paired-end RNA-seq sample.

By default this script runs in dry-run mode: it validates inputs and prints the
STAR command without executing it. Add --execute to run STAR.

Required arguments:
  --sample-id     Sample identifier used in STAR output filename prefix.
  --r1-fastq      Path to read 1 FASTQ or FASTQ.GZ file.
  --r2-fastq      Path to read 2 FASTQ or FASTQ.GZ file.
  --star-index    Path to STAR genome index directory.
  --output-dir    Directory where STAR outputs will be written.
  --threads       Number of threads for STAR; must be a positive integer.

Options:
  --star-bin      STAR executable or path. Defaults to STAR on PATH.
  --gunzip-bin    gunzip executable or path used for paired .gz inputs.
                  Defaults to gunzip on PATH and is ignored for uncompressed mates.
  --no-clobber    Explicitly request the default owned, staged, create-exclusive
                  publication transaction. Accepted for wrapper clarity; there
                  is no clobbering execution mode.
  --execute       Execute STAR after validation. Without this, dry-run only.
  -h, --help      Show this help message and exit.
USAGE
}

# shellcheck source=../../libraries/argument_parsing.sh
script_dir="${BASH_SOURCE[0]%/*}"
if [[ "$script_dir" == "$BASH_SOURCE[0]" ]]; then
    script_dir="."
fi
source "$script_dir/../../libraries/argument_parsing.sh"
# shellcheck source=../../libraries/file_checks.sh
source "$script_dir/../../libraries/file_checks.sh"
# shellcheck source=../../libraries/executable_resolution.sh
source "$script_dir/../../libraries/executable_resolution.sh"
# shellcheck source=../../libraries/signal_traps.sh
source "$script_dir/../../libraries/signal_traps.sh"

# Defaults are empty so missing required arguments fail loudly below.
declare_required_arguments sample_id r1_fastq r2_fastq star_index output_dir threads
execute=false
requested_star_bin=""
requested_gunzip_bin=""

# Parse explicit paths and execution mode from the command line.
while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id) assign_option_value "$1" "${2:-}" sample_id; shift 2 ;;
        --r1-fastq) assign_option_value "$1" "${2:-}" r1_fastq; shift 2 ;;
        --r2-fastq) assign_option_value "$1" "${2:-}" r2_fastq; shift 2 ;;
        --star-index) assign_option_value "$1" "${2:-}" star_index; shift 2 ;;
        --output-dir) assign_option_value "$1" "${2:-}" output_dir; shift 2 ;;
        --threads) assign_option_value "$1" "${2:-}" threads; shift 2 ;;
        --star-bin) assign_option_value "$1" "${2:-}" requested_star_bin; shift 2 ;;
        --gunzip-bin) assign_option_value "$1" "${2:-}" requested_gunzip_bin; shift 2 ;;
        --no-clobber) shift ;;
        *)
            handle_execute_or_help "$1"
            shift
            ;;
    esac
done

# Validate required arguments and external tool availability before any work starts.
require_arguments

[[ -f "$r1_fastq" ]] || die "R1 FASTQ does not exist or is not a file: $r1_fastq"
[[ -f "$r2_fastq" ]] || die "R2 FASTQ does not exist or is not a file: $r2_fastq"
[[ -d "$star_index" ]] || die "STAR index directory does not exist: $star_index"
star_bin="$(resolve_executable_value "STAR" "$requested_star_bin" "STAR")"

validate_positive_integer "--threads" "$threads"

# STAR needs --readFilesCommand only when both FASTQ inputs are gzip-compressed.
r1_is_gz=false
r2_is_gz=false
if is_gzip_path "$r1_fastq"; then
    r1_is_gz=true
fi
if is_gzip_path "$r2_fastq"; then
    r2_is_gz=true
fi

if [[ "$r1_is_gz" != "$r2_is_gz" ]]; then
    die "Mixed FASTQ compression is not supported: R1 and R2 must both be .gz or both be uncompressed."
fi

gunzip_bin="not-required"
if [[ "$r1_is_gz" == true ]]; then
    gunzip_bin="$(resolve_executable_value \
        "gunzip" "$requested_gunzip_bin" "gunzip")"
fi

snapshot_star_index() {
    local LC_ALL=C
    local entry
    local member
    local digest
    local had_dotglob=false
    local had_nullglob=false
    local entries=()

    if shopt -q dotglob; then
        had_dotglob=true
    fi
    if shopt -q nullglob; then
        had_nullglob=true
    fi
    shopt -s dotglob nullglob
    entries=("$star_index"/*)
    if [[ "$had_dotglob" != true ]]; then
        shopt -u dotglob
    fi
    if [[ "$had_nullglob" != true ]]; then
        shopt -u nullglob
    fi

    [[ "${#entries[@]}" -gt 0 ]] ||
        die "STAR index contains no top-level files: $star_index"

    for entry in "${entries[@]}"; do
        member="${entry##*/}"
        case "$member" in
            *$'\t'*|*$'\n'*|*$'\r'*)
                die "STAR index member has an ambiguous tab or newline in its name: $entry"
                ;;
        esac
        [[ ! -L "$entry" ]] ||
            die "STAR index top-level member is a symbolic link: $entry"
        [[ -f "$entry" ]] ||
            die "STAR index top-level member is not a regular file: $entry"
        [[ -r "$entry" ]] ||
            die "STAR index top-level member is not readable: $entry"
        [[ -s "$entry" ]] ||
            die "STAR index top-level member is empty: $entry"
        digest="$(sha256_file "$entry")"
        printf '%s\t%s\n' "$member" "$digest"
    done
}

require_star_index_unchanged() {
    local boundary="$1"
    local current_snapshot

    current_snapshot="$(snapshot_star_index)"
    [[ "$current_snapshot" == "$star_index_snapshot" ]] ||
        die "STAR index membership or bytes changed $boundary."
}

validate_safe_id "--sample-id" "$sample_id"
r1_sha256="$(sha256_file "$r1_fastq")"
r2_sha256="$(sha256_file "$r2_fastq")"
star_index_snapshot="$(snapshot_star_index)"
star_index_member_count="$(printf '%s\n' "$star_index_snapshot" | wc -l | tr -d ' ')"
run_token="${NORAD_RUN_TOKEN:-${SLURM_JOB_ID:-$$}}"
validate_safe_id "Step 01 run token" "$run_token"
final_prefix="$output_dir/${sample_id}."
staging_dir="$output_dir/.${sample_id}.step01.${run_token}.staging"
staging_prefix="$staging_dir/${sample_id}."
lock_path="$output_dir/.${sample_id}.step01.lock"
lock_owner_file="$lock_path/owner"
declared_suffixes=(
    Aligned.sortedByCoord.out.bam
    Log.final.out
    Log.out
    Log.progress.out
    SJ.out.tab
)
lock_acquired=false
publication_started=false
published_count=0
publication_ambiguous=false

require_absent_declared_outputs() {
    local suffix
    for suffix in "${declared_suffixes[@]}"; do
        if [[ -e "${final_prefix}${suffix}" || -L "${final_prefix}${suffix}" ]]; then
            die "Step 01 output already exists; refusing to clobber: ${final_prefix}${suffix}"
        fi
    done
}

report_declared_output_collisions() {
    local suffix
    local collision=false

    for suffix in "${declared_suffixes[@]}"; do
        if [[ -e "${final_prefix}${suffix}" || -L "${final_prefix}${suffix}" ]]; then
            printf '  Existing declared output: %s\n' "${final_prefix}${suffix}"
            collision=true
        fi
    done
    if [[ "$collision" == true ]]; then
        printf 'Execute would refuse to clobber the existing declared output set.\n'
    fi
}

publish_declared_output_no_replace() {
    local suffix="$1"
    local staged_path="${staging_prefix}${suffix}"
    local final_path="${final_prefix}${suffix}"
    local status

    [[ ! -L "$staged_path" && -f "$staged_path" && -s "$staged_path" ]] ||
        die "Step 01 staged output is not a nonempty regular file: $staged_path"

    # Staging and final paths share the output filesystem. Retain the staged
    # hard link as an ownership anchor until the complete final set validates.
    if ln "$staged_path" "$final_path"; then
        return 0
    else
        status=$?
        if [[ -e "$final_path" || -L "$final_path" ]]; then
            publication_ambiguous=true
            printf 'ERROR: Refusing to replace a late or foreign Step 01 output: %s\n' \
                "$final_path" >&2
        else
            printf 'ERROR: Could not create-exclusively publish Step 01 output: %s\n' \
                "$final_path" >&2
        fi
        return "$status"
    fi
}

remove_owned_published_output() {
    local suffix="$1"
    local staged_path="${staging_prefix}${suffix}"
    local final_path="${final_prefix}${suffix}"

    if [[ ! -e "$staged_path" ]]; then
        printf 'ERROR: Cannot prove ownership of published Step 01 output; staging anchor is missing: %s\n' \
            "$staged_path" >&2
        return 1
    fi
    if [[ ! -e "$final_path" ]]; then
        printf 'ERROR: Published Step 01 output disappeared before rollback; preserving recovery state: %s\n' \
            "$final_path" >&2
        return 1
    fi
    if [[ -L "$final_path" || ! -f "$final_path" || ! "$final_path" -ef "$staged_path" ]]; then
        printf 'ERROR: Published Step 01 output no longer belongs to this invocation; preserving the foreign path: %s\n' \
            "$final_path" >&2
        return 1
    fi
    if ! rm -f -- "$final_path"; then
        printf 'ERROR: Could not remove invocation-owned Step 01 output during rollback: %s\n' \
            "$final_path" >&2
        return 1
    fi
}

validate_published_output_set() {
    local suffix
    local staged_path
    local final_path

    for suffix in "${declared_suffixes[@]}"; do
        staged_path="${staging_prefix}${suffix}"
        final_path="${final_prefix}${suffix}"
        if [[ -L "$final_path" || ! -f "$final_path" || ! -s "$final_path" ||
              ! "$final_path" -ef "$staged_path" ]]; then
            publication_ambiguous=true
            die "Published Step 01 output set no longer matches its owned staging anchors: $final_path"
        fi
    done
}

cleanup_no_clobber() {
    local status="$1"
    local suffix
    local index
    local rollback_failed=false

    set +e
    if [[ "$status" -ne 0 && "$publication_started" == true ]]; then
        for ((index = 0; index < published_count; index++)); do
            suffix="${declared_suffixes[$index]}"
            if ! remove_owned_published_output "$suffix"; then
                rollback_failed=true
            fi
        done
    fi

    if [[ "$publication_ambiguous" == true ]]; then
        rollback_failed=true
    fi

    if [[ "$rollback_failed" != true &&
          ( -e "$staging_dir" || -L "$staging_dir" ) ]]; then
        if ! rm -rf -- "$staging_dir" ||
           [[ -e "$staging_dir" || -L "$staging_dir" ]]; then
            printf 'ERROR: Could not remove Step 01 staging directory during cleanup: %s\n' \
                "$staging_dir" >&2
            rollback_failed=true
        fi
    fi

    if [[ "$rollback_failed" != true && "$lock_acquired" == true ]]; then
        remove_owned_lock
        if [[ -e "$lock_path" || -L "$lock_path" ]]; then
            printf 'ERROR: Could not remove the owned Step 01 lock during cleanup: %s\n' \
                "$lock_path" >&2
            rollback_failed=true
        fi
    fi

    if [[ "$rollback_failed" == true ]]; then
        printf 'ERROR: Step 01 no-clobber cleanup was incomplete; retaining the owned lock and recovery residue: %s\n' \
            "$lock_path" >&2
    fi
}

# Report the resolved run context so cluster logs are reproducible.
mode="dry-run"
if [[ "$execute" == true ]]; then
    mode="execute"
fi

printf 'STAR alignment context\n'
printf '  Sample ID: %s\n' "$sample_id"
printf '  R1 FASTQ: %s\n' "$r1_fastq"
printf '  R2 FASTQ: %s\n' "$r2_fastq"
printf '  STAR index: %s\n' "$star_index"
printf '  STAR bin: %s\n' "$star_bin"
printf '  gunzip bin: %s\n' "$gunzip_bin"
printf '  Output directory: %s\n' "$output_dir"
printf '  Threads: %s\n' "$threads"
printf '  R1 SHA-256: %s\n' "$r1_sha256"
printf '  R2 SHA-256: %s\n' "$r2_sha256"
printf '  STAR index member count: %s\n' "$star_index_member_count"
while IFS=$'\t' read -r member digest; do
    printf '  STAR index member: %s\t%s\n' "$member" "$digest"
done <<<"$star_index_snapshot"
printf '  No-clobber transaction: true\n'
printf '  Lock directory: %s\n' "$lock_path"
printf '  Run token: %s\n' "$run_token"
printf '  Staging directory: %s\n' "$staging_dir"
printf '  Mode: %s\n' "$mode"

# Write coordinate-sorted BAM directly to avoid large default SAM output.
command_prefix="$staging_prefix"
star_command=(
    "$star_bin"
    --runThreadN "$threads"
    --genomeDir "$star_index"
    --readFilesIn "$r1_fastq" "$r2_fastq"
    --outFileNamePrefix "$command_prefix"
    --outSAMtype BAM SortedByCoordinate
)

if [[ "$r1_is_gz" == true ]]; then
    star_command+=(--readFilesCommand "$gunzip_bin" -c)
fi

printf 'STAR command:\n'
print_command "${star_command[@]}"

printf 'Declared output set:\n'
for suffix in "${declared_suffixes[@]}"; do
    printf '  %s\n' "${final_prefix}${suffix}"
done

require_no_owner_residue \
    "Step 01" "$output_dir" ".${sample_id}.step01.*"

# Dry-run mode is the default safety path for local development and wrapper tests.
if [[ "$execute" != true ]]; then
    report_declared_output_collisions
    printf 'Dry-run only. Add --execute to run STAR.\n'
    exit 0
fi

require_absent_declared_outputs
mkdir -p "$output_dir"

[[ ! -e "$staging_dir" ]] || die "Step 01 staging directory already exists: $staging_dir"
set_exit_trap cleanup_no_clobber
acquire_lock "Step 01"
mkdir "$staging_dir"

require_star_index_unchanged "before STAR execution"
"${star_command[@]}"

for suffix in "${declared_suffixes[@]}"; do
    [[ -s "${staging_prefix}${suffix}" ]] ||
        die "STAR declared output is missing or empty: ${staging_prefix}${suffix}"
done
[[ "$(sha256_file "$r1_fastq")" == "$r1_sha256" ]] || die "R1 FASTQ changed during Step 01."
[[ "$(sha256_file "$r2_fastq")" == "$r2_sha256" ]] || die "R2 FASTQ changed during Step 01."
require_star_index_unchanged "during Step 01"
require_absent_declared_outputs

publication_started=true
for suffix in "${declared_suffixes[@]}"; do
    publish_declared_output_no_replace "$suffix"
    published_count=$((published_count + 1))
done
validate_published_output_set
rm -rf -- "$staging_dir"
publication_started=false
remove_owned_lock

printf 'STAR declared output details:\n'
for suffix in "${declared_suffixes[@]}"; do
    ls -lh "${final_prefix}${suffix}"
done
