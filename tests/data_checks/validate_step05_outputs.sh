#!/usr/bin/env bash
set -uo pipefail

SAMTOOLS="${SAMTOOLS:-/cm/shared/apps/csu-soft-install/samtools/samtools_install/bin/samtools}"
JOB_FILE=""
OUTPUT_TSV="${OUTPUT_TSV:-results/qc/step05/step05_validation_status.tsv}"

usage() {
  cat <<'USAGE'
Usage:
  tests/data_checks/validate_step05_outputs.sh [--jobs step05_jobs.txt] [--output results/qc/step05/status.tsv] [SAMPLE_ID ...]

Output:
  By default, writes the TSV table to:
    results/qc/step05/step05_validation_status.tsv

  Override with:
    --output PATH

Read-only validation for Step 05 split-N-cigar outputs.

Default samples:
  ABE_EV_2 ABE_EV_3 ABE_EV4 ABE_PUM1_2 ABE_PUM1_3 ABE_PUM1_4

Optional job file format:
  SAMPLE_ID JOBID

Exit codes:
  0 = all checked samples PASS
  1 = one or more samples FAIL
  2 = no failures, but one or more samples are pending/running
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --jobs)
      JOB_FILE="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT_TSV="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -gt 0 ]]; then
  samples=("$@")
else
  samples=(ABE_EV_2 ABE_EV_3 ABE_EV4 ABE_PUM1_2 ABE_PUM1_3 ABE_PUM1_4)
fi

if [[ ! -x "$SAMTOOLS" ]]; then
  echo "ERROR: samtools not executable: $SAMTOOLS" >&2
  exit 1
fi

if [[ -z "$OUTPUT_TSV" ]]; then
  echo "ERROR: --output requires a nonempty path" >&2
  exit 1
fi

output_dir="$(dirname "$OUTPUT_TSV")"
mkdir -p "$output_dir" || {
  echo "ERROR: could not create output directory: $output_dir" >&2
  exit 1
}

if [[ -e "$OUTPUT_TSV" && ! -w "$OUTPUT_TSV" ]]; then
  echo "ERROR: output file exists but is not writable: $OUTPUT_TSV" >&2
  exit 1
fi

tmp_output_check="$output_dir/.validate_step05_write_check.$$"
if ! : > "$tmp_output_check"; then
  echo "ERROR: output directory is not writable: $output_dir" >&2
  exit 1
fi
rm -f "$tmp_output_check"

# Keep stdout visible while also saving a durable TSV snapshot.
exec > >(tee "$OUTPUT_TSV")

job_for_sample() {
  local sample="$1"
  if [[ -n "$JOB_FILE" && -f "$JOB_FILE" ]]; then
    awk -v s="$sample" '$1 == s {print $2; exit}' "$JOB_FILE"
  fi
}

job_state() {
  local jid="$1"
  [[ -n "$jid" ]] || { printf 'NA'; return; }

  local sq st
  sq="$(squeue -j "$jid" -h -o '%T' 2>/dev/null | head -n 1 || true)"
  if [[ -n "$sq" ]]; then
    printf '%s' "$sq"
    return
  fi

  st="$(sacct -j "$jid" --noheader --format=State 2>/dev/null | awk 'NF {print $1; exit}' || true)"
  [[ -n "$st" ]] && printf '%s' "$st" || printf 'UNKNOWN'
}

pass_count=0
pending_count=0
fail_count=0

printf 'sample_id\tjob_id\tjob_state\tbam_exists\tbai_exists\tbam_size\tbai_size\tquickcheck_ok\thd_coordinate\trg_ok\tscratch_count\tstatus\n'

for s in "${samples[@]}"; do
  dir="results/split_ncigar/$s"
  bam="$dir/$s.split_ncigar.bam"
  bai="$bam.bai"

  jid="$(job_for_sample "$s")"
  jstate="$(job_state "$jid")"

  bam_exists=no
  bai_exists=no
  bam_size=0
  bai_size=0
  quickcheck_ok=NA
  hd_coordinate=NA
  rg_ok=NA
  status=PENDING

  [[ -s "$bam" ]] && bam_exists=yes && bam_size="$(du -h "$bam" 2>/dev/null | awk '{print $1}')"
  [[ -s "$bai" ]] && bai_exists=yes && bai_size="$(du -h "$bai" 2>/dev/null | awk '{print $1}')"

  scratch_count=0
  if [[ -d "$dir" ]]; then
    scratch_count="$(find "$dir" -maxdepth 1 -name '.*step05*' -print 2>/dev/null | wc -l | tr -d ' ')"
  fi

  if [[ "$bam_exists" == yes && "$bai_exists" == yes ]]; then
    if "$SAMTOOLS" quickcheck "$bam" >/dev/null 2>&1; then
      quickcheck_ok=yes
    else
      quickcheck_ok=no
    fi

    header="$("$SAMTOOLS" view -H "$bam" 2>/dev/null || true)"

    if printf '%s\n' "$header" | grep -q '^@HD.*SO:coordinate'; then
      hd_coordinate=yes
    else
      hd_coordinate=no
    fi

    rg_lines="$(printf '%s\n' "$header" | grep '^@RG' || true)"
    rg_count="$(printf '%s\n' "$rg_lines" | sed '/^$/d' | wc -l | tr -d ' ')"

    if [[ "$rg_count" == "1" ]] \
      && [[ "$rg_lines" == *"ID:$s"* ]] \
      && [[ "$rg_lines" == *"SM:$s"* ]] \
      && [[ "$rg_lines" == *"LB:$s"* ]] \
      && [[ "$rg_lines" == *"PL:ILLUMINA"* ]]; then
      rg_ok=yes
    else
      rg_ok=no
    fi

    if [[ "$quickcheck_ok" == yes && "$hd_coordinate" == yes && "$rg_ok" == yes && "$scratch_count" == "0" ]]; then
      status=PASS
      pass_count=$((pass_count + 1))
    else
      status=FAIL
      fail_count=$((fail_count + 1))
    fi
  else
    case "$jstate" in
      RUNNING|PENDING|CONFIGURING|COMPLETING)
        status="$jstate"
        ;;
      COMPLETED)
        status=PENDING_OUTPUT_INSPECTION
        ;;
      FAILED|CANCELLED|TIMEOUT|OUT_OF_MEMORY|NODE_FAIL)
        status=FAIL
        fail_count=$((fail_count + 1))
        ;;
      *)
        status=PENDING
        ;;
    esac

    if [[ "$status" != FAIL ]]; then
      pending_count=$((pending_count + 1))
    fi
  fi

  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$s" "${jid:-NA}" "$jstate" "$bam_exists" "$bai_exists" "$bam_size" "$bai_size" \
    "$quickcheck_ok" "$hd_coordinate" "$rg_ok" "$scratch_count" "$status"
done

printf '\nSummary: PASS=%s PENDING_OR_RUNNING=%s FAIL=%s\n' "$pass_count" "$pending_count" "$fail_count" >&2

if [[ "$fail_count" -gt 0 ]]; then
  exit 1
fi

if [[ "$pending_count" -gt 0 ]]; then
  exit 2
fi

exit 0
