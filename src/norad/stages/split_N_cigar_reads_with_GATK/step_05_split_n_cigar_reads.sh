#!/usr/bin/env bash
# Step 05: run GATK SplitNCigarReads on one duplicate-marked RNA-seq BAM.
#
# Dry-run mode validates required inputs and prints resolved paths, exact tool
# commands, locking, temp paths, and validation checks without creating output
# directories, locks, temp files, BAMs, or indexes. Passing --execute runs GATK,
# validates the temporary BAM/BAI pair, and publishes final outputs only after
# validation succeeds.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  src/norad/stages/split_N_cigar_reads_with_GATK/step_05_split_n_cigar_reads.sh \
    --sample-id SAMPLE_ID \
    --input-bam INPUT_BAM \
    --reference-fasta REFERENCE_FASTA \
    --output-dir OUTPUT_DIR \
    [--gatk-bin GATK_BIN] \
    [--samtools-bin SAMTOOLS_BIN] \
    [--java-bin JAVA_BIN] \
    [--execute]

Run GATK SplitNCigarReads on one duplicate-marked RNA-seq BAM.

By default this script runs in dry-run mode: it validates required existing
inputs, prints planned commands and validation checks, and writes nothing. Add
--execute to run GATK and samtools and publish outputs after validation.

Required arguments:
  --sample-id         Sample identifier used in output filenames and RG checks.
  --input-bam         Duplicate-marked BAM from Step 04.
  --reference-fasta   Reference FASTA whose Step 00c sidecars already exist.
  --output-dir        Directory where split-N-cigar BAM and BAI are written.

Options:
  --gatk-bin          gatk executable or path. Resolution order:
                      argument, GATK_BIN_OVERRIDE, PATH.
  --samtools-bin      samtools executable or path. Resolution order:
                      argument, SAMTOOLS_BIN_OVERRIDE, PATH.
  --java-bin          Java executable or path. Resolution order:
                      argument, JAVA_BIN_OVERRIDE, JAVA_HOME/bin/java, PATH.
  --execute           Execute GATK and samtools after validation. Without this,
                      dry-run only.
  -h, --help          Show this help message and exit.
USAGE
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

# shellcheck source=../../libraries/executable_resolution.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/executable_resolution.sh"

die2() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

print_command() {
    printf '%q ' "$@"
    printf '\n'
}

require_value() {
    local option="$1"
    local value="${2:-}"

    if [[ -z "$value" || "$value" == --* ]]; then
        die "$option requires a value."
    fi
}

resolve_gatk() {
    local value="${gatk_bin_arg:-}"
    if [[ -z "$value" && -n "${GATK_BIN_OVERRIDE:-}" ]]; then
        value="$GATK_BIN_OVERRIDE"
    fi
    resolve_executable_value "GATK" "$value" "gatk"
}

resolve_samtools() {
    local value="${samtools_bin_arg:-}"
    if [[ -z "$value" && -n "${SAMTOOLS_BIN_OVERRIDE:-}" ]]; then
        value="$SAMTOOLS_BIN_OVERRIDE"
    fi
    resolve_executable_value "samtools" "$value" "samtools"
}

resolve_java() {
    local value="${java_bin_arg:-}"
    if [[ -z "$value" && -n "${JAVA_BIN_OVERRIDE:-}" ]]; then
        value="$JAVA_BIN_OVERRIDE"
    fi
    if [[ -z "$value" && -n "${JAVA_HOME:-}" && -x "${JAVA_HOME}/bin/java" ]]; then
        value="${JAVA_HOME}/bin/java"
    fi
    resolve_executable_value "Java" "$value" "java"
}

validate_java_version() {
    local java_bin="$1"
    local version_output
    local version_line
    local java_major

    version_output="$("$java_bin" -version 2>&1)" || die2 "Java version check failed: $java_bin"
    version_line="$(printf '%s\n' "$version_output" | head -n 1)"

    if [[ "$version_line" =~ version\ \"1\.([0-9]+) ]]; then
        java_major="${BASH_REMATCH[1]}"
    elif [[ "$version_line" =~ version\ \"([0-9]+) ]]; then
        java_major="${BASH_REMATCH[1]}"
    else
        printf '%s\n' "$version_output" >&2
        die2 "Could not determine Java version from: $version_line"
    fi

    if (( java_major < 17 )); then
        printf '%s\n' "$version_output" >&2
        die2 "GATK SplitNCigarReads requires Java 17 or newer; found Java $java_major at $java_bin"
    fi

    printf '%s\n' "$version_output"
}

validate_gatk_version() {
    local gatk_bin="$1"

    "$gatk_bin" --version 2>&1 || die2 "GATK version check failed: $gatk_bin"
}

validate_existing_file() {
    local label="$1"
    local path="$2"

    [[ -s "$path" ]] || die "$label does not exist or is empty: $path"
}

validate_reference_sidecar() {
    local label="$1"
    local path="$2"

    if [[ ! -s "$path" ]]; then
        die "$label is missing or empty: $path. Run Step 00c before Step 05; Step 05 does not create reference sidecars."
    fi
}

sample_id=""
input_bam=""
reference_fasta=""
output_dir=""
gatk_bin_arg=""
samtools_bin_arg=""
java_bin_arg=""
execute=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --sample-id)
            require_value "$1" "${2:-}"
            sample_id="$2"
            shift 2
            ;;
        --input-bam)
            require_value "$1" "${2:-}"
            input_bam="$2"
            shift 2
            ;;
        --reference-fasta)
            require_value "$1" "${2:-}"
            reference_fasta="$2"
            shift 2
            ;;
        --output-dir)
            require_value "$1" "${2:-}"
            output_dir="$2"
            shift 2
            ;;
        --gatk-bin)
            require_value "$1" "${2:-}"
            gatk_bin_arg="$2"
            shift 2
            ;;
        --samtools-bin)
            require_value "$1" "${2:-}"
            samtools_bin_arg="$2"
            shift 2
            ;;
        --java-bin)
            require_value "$1" "${2:-}"
            java_bin_arg="$2"
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

[[ -n "$sample_id" ]] || die "Missing required argument: --sample-id."
[[ -n "$input_bam" ]] || die "Missing required argument: --input-bam."
[[ -n "$reference_fasta" ]] || die "Missing required argument: --reference-fasta."
[[ -n "$output_dir" ]] || die "Missing required argument: --output-dir."

# Step 04 publishes indexes as <bam>.bai, and Step 00c owns the reference
# sidecars. Keep Step 05 strict so missing upstream work is caught before GATK.
input_bai="$input_bam.bai"
reference_fai="$reference_fasta.fai"
reference_dir="$(dirname "$reference_fasta")"
reference_base="$(basename "$reference_fasta")"
reference_stem="${reference_base%.*}"
reference_dict="$reference_dir/${reference_stem}.dict"

# Resolve tool paths once and print the selected values in both dry-run and
# execute logs. Version checks are deferred until execute so dry-runs stay
# side-effect-free and do not invoke Java/GATK.
gatk_bin="$(resolve_gatk)"
samtools_bin="$(resolve_samtools)"
java_bin="$(resolve_java)"

run_token="${SLURM_JOB_ID:-$$}"

# Final output names are stable downstream interfaces. Temp and backup names
# include the run token so reruns and concurrent dry-run planning do not collide.
output_bam="$output_dir/${sample_id}.split_ncigar.bam"
output_bai="$output_bam.bai"
lock_path="$output_dir/.step_05_split_n_cigar_reads.lock"
lock_owner_file="$lock_path/owner"

tmp_bam="$output_dir/.${sample_id}.step05.${run_token}.split_ncigar.tmp.bam"
tmp_bai="$tmp_bam.bai"

# GATK/HTSJDK may also create an index by replacing .bam with .bai.
# Track this so failed runs do not leave confusing zero-byte sidecars.
tmp_gatk_bai="${tmp_bam%.bam}.bai"

# Do not let GATK spill internal SortingCollection temp files to node-local /tmp.
# CSU compute-node /tmp can be small; project storage has enough space.
gatk_tmp_dir="$output_dir/.${sample_id}.step05.${run_token}.gatk_tmp"

backup_bam="$output_dir/.${sample_id}.step05.${run_token}.previous.bam"
backup_bai="$output_dir/.${sample_id}.step05.${run_token}.previous.bam.bai"

lock_acquired=false
previous_pair_present=false
backup_started=false
bam_backed_up=false
bai_backed_up=false
final_publish_complete=false

gatk_command=(
    "$gatk_bin"
    --java-options "-Djava.io.tmpdir=$gatk_tmp_dir"
    SplitNCigarReads
    --tmp-dir "$gatk_tmp_dir"
    -R "$reference_fasta"
    -I "$input_bam"
    -O "$tmp_bam"
)

index_command=(
    "$samtools_bin"
    index
    "$tmp_bam"
)

quickcheck_command=(
    "$samtools_bin"
    quickcheck
    "$tmp_bam"
)

header_command=(
    "$samtools_bin"
    view
    -H
    "$tmp_bam"
)

count_command=(
    "$samtools_bin"
    view
    -c
    "$tmp_bam"
)

tagged_count_command=(
    "$samtools_bin"
    view
    -c
    -d "RG:$sample_id"
    "$tmp_bam"
)

validate_bam_pair() {
    local bam="$1"
    local bai="$2"
    local label="$3"
    local header
    local rg_lines
    local rg_count
    local rg_line
    local total_records
    local tagged_records

    # GATK should preserve the coordinate sort and sample read group from the
    # Step 04 input. Validate those properties before anything becomes final.
    [[ -s "$bam" ]] || die "$label BAM is missing or empty: $bam"
    "$samtools_bin" quickcheck "$bam" || die "$label BAM failed samtools quickcheck: $bam"

    header="$("$samtools_bin" view -H "$bam")"
    printf '%s\n' "$header" | grep -q '^@HD.*SO:coordinate' || die "$label BAM header is not coordinate sorted"

    rg_lines="$(printf '%s\n' "$header" | grep '^@RG' || true)"
    rg_count="$(printf '%s\n' "$rg_lines" | sed '/^$/d' | wc -l | tr -d ' ')"
    [[ "$rg_count" == "1" ]] || die "$label BAM must contain exactly one @RG line; found: $rg_count"

    rg_line="$rg_lines"
    [[ "$rg_line" == *"ID:$sample_id"* ]] || die "$label @RG line is missing ID:$sample_id"
    [[ "$rg_line" == *"SM:$sample_id"* ]] || die "$label @RG line is missing SM:$sample_id"

    total_records="$("$samtools_bin" view -c "$bam")"
    [[ "$total_records" =~ ^[0-9]+$ ]] || die "$label total alignment count is not numeric: $total_records"
    [[ "$total_records" -gt 0 ]] || die "$label BAM contains no alignment records"

    tagged_records="$("$samtools_bin" view -c -d "RG:$sample_id" "$bam")"
    [[ "$tagged_records" =~ ^[0-9]+$ ]] || die "$label tagged alignment count is not numeric: $tagged_records"
    [[ "$tagged_records" -eq "$total_records" ]] || die "$label BAM has $tagged_records of $total_records records tagged RG:$sample_id"

    [[ -s "$bai" ]] || die "$label BAI is missing or empty: $bai"
}

confirm_final_pair_state() {
    # A lone BAM or BAI is unsafe: there would be no complete prior pair to
    # restore if publication failed midway.
    if [[ -e "$output_bam" && -e "$output_bai" ]]; then
        previous_pair_present=true
    elif [[ ! -e "$output_bam" && ! -e "$output_bai" ]]; then
        previous_pair_present=false
    else
        die "Step 05 final outputs are inconsistent; expected both BAM and BAI or neither: $output_bam $output_bai"
    fi
}

acquire_lock() {
    local owner="run_token=$run_token"

    # mkdir is atomic for this local/cluster filesystem pattern; never remove a
    # lock owned by a different invocation.
    if mkdir "$lock_path" 2>/dev/null; then
        printf '%s\n' "$owner" > "$lock_owner_file"
        lock_acquired=true
        return
    fi

    if [[ -f "$lock_owner_file" ]]; then
        die "Step 05 lock already exists at $lock_path; owner: $(cat "$lock_owner_file")"
    fi

    die "Step 05 lock already exists at $lock_path; owner: unknown"
}

remove_owned_lock() {
    if [[ "$lock_acquired" != true ]]; then
        return
    fi

    # Only the invocation that wrote the owner file may remove the lock.
    if [[ -f "$lock_owner_file" ]] && [[ "$(cat "$lock_owner_file")" == "run_token=$run_token" ]]; then
        rm -f "$lock_owner_file"
        rmdir "$lock_path" 2>/dev/null || true
        lock_acquired=false
    fi
}

rollback_publish() {
    if [[ "$backup_started" != true || "$final_publish_complete" == true ]]; then
        return
    fi

    printf 'Rolling back Step 05 split-N-cigar outputs...\n' >&2

    if [[ "$previous_pair_present" == true ]]; then
        # Restore only files that this invocation actually moved to backup.
        if [[ "$bam_backed_up" == true && -e "$backup_bam" ]]; then
            rm -f "$output_bam"
            mv "$backup_bam" "$output_bam" || true
            bam_backed_up=false
        fi

        if [[ "$bai_backed_up" == true && -e "$backup_bai" ]]; then
            rm -f "$output_bai"
            mv "$backup_bai" "$output_bai" || true
            bai_backed_up=false
        fi
    else
        rm -f "$output_bam" "$output_bai"
    fi
}

cleanup() {
    local status="$1"

    # Cleanup should be best-effort and must not mask the original failure.
    set +e

    # Rollback must run before temp/backup cleanup so previous final files can
    # still be restored after a partial publish.
    if [[ "$status" -ne 0 ]]; then
        rollback_publish
    fi

    rm -f "$tmp_bam" "$tmp_bai" "$tmp_gatk_bai"
    rm -rf "$gatk_tmp_dir"

    if [[ "$status" -eq 0 || "$backup_started" == true ]]; then
        rm -f "$backup_bam" "$backup_bai"
    fi

    remove_owned_lock
}

validate_existing_file "Input BAM" "$input_bam"
validate_existing_file "Input BAI" "$input_bai"
validate_existing_file "Reference FASTA" "$reference_fasta"
validate_reference_sidecar "Reference FASTA index" "$reference_fai"
validate_reference_sidecar "Reference sequence dictionary" "$reference_dict"

mode="dry-run"
if [[ "$execute" == true ]]; then
    mode="execute"
fi

printf 'GATK SplitNCigarReads context\n'
printf '  Sample ID: %s\n' "$sample_id"
printf '  Input BAM: %s\n' "$input_bam"
printf '  Input BAI: %s\n' "$input_bai"
printf '  Reference FASTA: %s\n' "$reference_fasta"
printf '  Reference FAI: %s\n' "$reference_fai"
printf '  Reference DICT: %s\n' "$reference_dict"
printf '  Output directory: %s\n' "$output_dir"
printf '  Output BAM: %s\n' "$output_bam"
printf '  Output BAI: %s\n' "$output_bai"
printf '  GATK bin: %s\n' "$gatk_bin"
printf '  samtools bin: %s\n' "$samtools_bin"
printf '  Java bin: %s\n' "$java_bin"
printf '  Java version check: execute mode validates selected Java is >=17\n'
printf '  Run token: %s\n' "$run_token"
printf '  Lock directory: %s\n' "$lock_path"
printf '  Lock owner file: %s\n' "$lock_owner_file"
printf '  Temporary BAM: %s\n' "$tmp_bam"
printf '  Temporary BAI: %s\n' "$tmp_bai"
printf '  Alternate GATK temporary BAI: %s\n' "$tmp_gatk_bai"
printf '  GATK temp directory: %s\n' "$gatk_tmp_dir"
printf '  Backup BAM: %s\n' "$backup_bam"
printf '  Backup BAI: %s\n' "$backup_bai"
printf '  Mode: %s\n' "$mode"

printf 'Lock acquisition action:\n'
printf 'mkdir %q\n' "$lock_path"
printf 'Lock owner write action:\n'
printf 'printf %q %q %q\n' '%s\n' "run_token=$run_token" "$lock_owner_file"

printf 'GATK SplitNCigarReads command:\n'
print_command "${gatk_command[@]}"

printf 'GATK temp directory creation action:\n'
printf 'mkdir -p %q\n' "$gatk_tmp_dir"

printf 'GATK temp cleanup action:\n'
printf 'rm -rf %q\n' "$gatk_tmp_dir"

printf 'samtools index command:\n'
print_command "${index_command[@]}"

printf 'samtools quickcheck validation command:\n'
print_command "${quickcheck_command[@]}"

printf 'samtools header validation command:\n'
print_command "${header_command[@]}"

printf 'samtools total-record validation command:\n'
print_command "${count_command[@]}"

printf 'samtools read-group-tag validation command:\n'
print_command "${tagged_count_command[@]}"

printf 'Validation plan:\n'
printf '  1. Verify Step 04 input BAM and BAI exist and are nonempty.\n'
printf '  2. Verify Step 00c reference FASTA, .fai, and .dict exist and are nonempty.\n'
printf '  3. Resolve GATK, samtools, and Java executables.\n'
printf '  4. Validate actual Java version is >=17 before execute-mode GATK use.\n'
printf '  5. Run GATK SplitNCigarReads into a run-token temp BAM using a project-storage GATK temp directory.\n'
printf '  6. Index the temp BAM and validate quickcheck, coordinate sort, read group preservation, and nonempty BAI.\n'
printf '  7. Publish final BAM/BAI only after validation succeeds.\n'
printf '  8. Roll back previous final outputs if publication fails after backups begin.\n'

if [[ "$execute" != true ]]; then
    # Dry-runs are intentionally side-effect-free so empty result directories or
    # locks are never mistaken for real Step 05 progress.
    printf 'Dry-run only. Add --execute to run GATK SplitNCigarReads and publish Step 05 outputs.\n'
    exit 0
fi

mkdir -p "$output_dir"

# Refuse to reuse scratch names. A pre-existing temp/backup file means a prior
# run may need manual inspection before this sample is attempted again.
[[ ! -e "$tmp_bam" ]] || die "Temporary BAM path already exists: $tmp_bam"
[[ ! -e "$tmp_bai" ]] || die "Temporary BAI path already exists: $tmp_bai"
[[ ! -e "$tmp_gatk_bai" ]] || die "Alternate GATK temporary BAI path already exists: $tmp_gatk_bai"
[[ ! -e "$gatk_tmp_dir" ]] || die "GATK temp directory already exists: $gatk_tmp_dir"
[[ ! -e "$backup_bam" ]] || die "Backup BAM path already exists: $backup_bam"
[[ ! -e "$backup_bai" ]] || die "Backup BAI path already exists: $backup_bai"

on_exit() {
    local status=$?

    # Prevent recursive cleanup if a signal trap exits and then EXIT fires too.
    trap - EXIT HUP INT TERM

    cleanup "$status"
    exit "$status"
}

trap on_exit EXIT HUP INT TERM

acquire_lock
confirm_final_pair_state
mkdir -p "$gatk_tmp_dir"

printf 'Java version:\n'
validate_java_version "$java_bin"

printf 'GATK version:\n'
validate_gatk_version "$gatk_bin"

env TMPDIR="$gatk_tmp_dir" "${gatk_command[@]}"
"${index_command[@]}"
validate_bam_pair "$tmp_bam" "$tmp_bai" "Replacement"

# Backups begin the rollback-protected region. From here until final validation,
# cleanup will restore the previous complete pair or remove partial new finals.
if [[ "$previous_pair_present" == true ]]; then
    backup_started=true
    mv "$output_bam" "$backup_bam"
    bam_backed_up=true
    mv "$output_bai" "$backup_bai"
    bai_backed_up=true
else
    backup_started=true
fi

mv "$tmp_bam" "$output_bam"
mv "$tmp_bai" "$output_bai"

# Revalidate at final paths so downstream steps never consume a half-published
# or path-specific bad BAM/BAI pair.
validate_bam_pair "$output_bam" "$output_bai" "Published"
final_publish_complete=true

rm -f "$backup_bam" "$backup_bai"
bam_backed_up=false
bai_backed_up=false

printf 'GATK SplitNCigarReads output details:\n'
ls -lh "$output_bam" "$output_bai"
