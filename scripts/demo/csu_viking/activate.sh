#!/usr/bin/env bash
# Source this file once in the disposable CSU Viking presentation shell.

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
  printf 'ERROR: source this file; do not execute it.\n' >&2
  exit 2
fi
if [[ ${NORAD_DEMO_ACTIVE:-0} == 1 ]]; then
  printf 'ERROR: NORAD demo mode is already active in this shell.\n' >&2
  return 2
fi

_norad_demo_activate_dir="$(
  cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd
)" || return 2
_norad_demo_repo="$(
  cd -P -- "$_norad_demo_activate_dir/../../.." && pwd
)" || return 2

_norad_demo_python="$_norad_demo_repo/.venv/bin/python"
if [[ ! -x $_norad_demo_python ]]; then
  printf 'ERROR: demo Python is unavailable: %s\n' "$_norad_demo_python" >&2
  unset _norad_demo_activate_dir _norad_demo_repo _norad_demo_python
  return 2
fi

if [[ -z ${NORAD_DEMO_SESSION:-} ]]; then
  NORAD_DEMO_SESSION="$(date -u +%Y%m%dT%H%M%SZ)-$$"
fi
if [[ ! $NORAD_DEMO_SESSION =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$ ]]; then
  printf 'ERROR: unsafe NORAD_DEMO_SESSION: %s\n' "$NORAD_DEMO_SESSION" >&2
  unset _norad_demo_activate_dir _norad_demo_repo _norad_demo_python
  return 2
fi
export NORAD_DEMO_REPO_ROOT="$_norad_demo_repo"
export NORAD_DEMO_PYTHON="$_norad_demo_python"
export NORAD_DEMO_SESSION

export NORAD_DEMO_SEED_INPUT="${NORAD_DEMO_SEED_INPUT:-$HOME/norad-ev-pum1-inputs-v2}"
export NORAD_DEMO_SOURCE_RUN="${NORAD_DEMO_SOURCE_RUN:-$HOME/norad-ev-pum1-workspace-v2/runs/run-2730d4872dbd2098dd57a57416faaff45cd9ec439551a548319636e3c45be5b4}"
export NORAD_DEMO_SOURCE_INDEX="${NORAD_DEMO_SOURCE_INDEX:-$NORAD_DEMO_SOURCE_RUN/results/star/novogene_reference/index}"
export NORAD_DEMO_REAL_STAR="${NORAD_DEMO_REAL_STAR:-/cm/shared/apps/csu-soft-install/star/STAR/bin/Linux_x86_64_static/STAR}"

export NORAD_DEMO_INPUT_DIR="${NORAD_DEMO_INPUT_DIR:-$HOME/norad-demo-inputs-$NORAD_DEMO_SESSION}"
export NORAD_DEMO_WORKSPACE_PARENT="${NORAD_DEMO_WORKSPACE_PARENT:-$HOME/norad-demo-workspace-parent-$NORAD_DEMO_SESSION}"
export NORAD_DEMO_WORKSPACE="${NORAD_DEMO_WORKSPACE:-$NORAD_DEMO_WORKSPACE_PARENT/workspace}"
export NORAD_DEMO_LOG_DIR="${NORAD_DEMO_LOG_DIR:-$HOME/norad-demo-slurm-logs-$NORAD_DEMO_SESSION}"
export NORAD_DEMO_STATE_FILE="$NORAD_DEMO_LOG_DIR/.demo-state.json"
export NORAD_DEMO_JOB_ENV_FILE="$NORAD_DEMO_LOG_DIR/.demo-job.env"

export NORAD_SLURM_ACCOUNT="${NORAD_DEMO_SLURM_ACCOUNT:-viking-users}"
export NORAD_SLURM_PARTITION="${NORAD_DEMO_SLURM_PARTITION:-long}"
export NORAD_SLURM_QOS="${NORAD_DEMO_SLURM_QOS:-normal}"
export NORAD_SLURM_NODELIST="${NORAD_DEMO_SLURM_NODELIST:-node002}"
export NORAD_DEMO_QUALIFICATION_PARTITION="${NORAD_DEMO_QUALIFICATION_PARTITION:-short}"
export NORAD_LOG_DIR="$NORAD_DEMO_LOG_DIR"
export NORAD_WORKSPACE="$NORAD_DEMO_WORKSPACE"
export NORAD_SCRATCH_PARENT="${NORAD_DEMO_SCRATCH_PARENT:-/tmp}"
export NORAD_DEMO_ACTIVE=1
unset JOB_ID LOG_DIR

unalias norad 2>/dev/null || true
norad() {
  local attach_job=0
  if (( $# == 2 )) && [[ $1 == execute && $2 == --execute ]]; then
    attach_job=1
    unset JOB_ID LOG_DIR
  fi
  "$NORAD_DEMO_PYTHON" -I -B \
    "$NORAD_DEMO_REPO_ROOT/scripts/demo/csu_viking/demo_driver.py" "$@"
  local status=$?
  if (( status == 0 && attach_job == 1 )); then
    if [[ ! -d $NORAD_DEMO_LOG_DIR || -L $NORAD_DEMO_LOG_DIR || \
          ! -O $NORAD_DEMO_LOG_DIR || \
          $(stat -c '%a' -- "$NORAD_DEMO_LOG_DIR" 2>/dev/null) != 700 ]]; then
      printf 'ERROR: demo log directory is not a current-UID mode-700 directory.\n' >&2
      return 2
    fi
    if [[ ! -f $NORAD_DEMO_JOB_ENV_FILE || -L $NORAD_DEMO_JOB_ENV_FILE || \
          ! -O $NORAD_DEMO_JOB_ENV_FILE ]]; then
      printf 'ERROR: demo job handoff is not a current-UID real file.\n' >&2
      return 2
    fi
    if [[ $(stat -c '%a' -- "$NORAD_DEMO_JOB_ENV_FILE" 2>/dev/null) != 600 ]]; then
      printf 'ERROR: demo job handoff permissions are not 600.\n' >&2
      return 2
    fi
    local key value demo_session="" demo_job_id="" demo_log_dir=""
    local session_count=0 job_count=0 log_count=0 unknown_count=0
    while IFS='=' read -r key value; do
      case "$key" in
        SESSION) demo_session="$value"; ((session_count += 1)) ;;
        JOB_ID) demo_job_id="$value"; ((job_count += 1)) ;;
        LOG_DIR) demo_log_dir="$value"; ((log_count += 1)) ;;
        *) ((unknown_count += 1)) ;;
      esac
    done < "$NORAD_DEMO_JOB_ENV_FILE"
    if (( session_count != 1 || job_count != 1 || log_count != 1 || \
          unknown_count != 0 )) || \
       [[ $demo_session != "$NORAD_DEMO_SESSION" || \
          ! $demo_job_id =~ ^[1-9][0-9]*$ || \
          $demo_log_dir != "$NORAD_DEMO_LOG_DIR" ]]; then
      printf 'ERROR: demo job handoff identity is invalid.\n' >&2
      return 2
    fi
    export JOB_ID="$demo_job_id"
    export LOG_DIR="$demo_log_dir"
  fi
  return "$status"
}

printf '%s\n' \
  '*** NORAD CSU VIKING DEMO MODE — PRESENTATION SHORTCUTS, NOT EVIDENCE ***' \
  "session:   $NORAD_DEMO_SESSION" \
  "inputs:    $NORAD_DEMO_INPUT_DIR" \
  "workspace: $NORAD_DEMO_WORKSPACE" \
  "logs:      $NORAD_DEMO_LOG_DIR"

unset _norad_demo_activate_dir _norad_demo_repo _norad_demo_python
