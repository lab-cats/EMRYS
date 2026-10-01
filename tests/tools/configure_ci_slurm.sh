#!/usr/bin/env bash
set -euo pipefail

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

if [[ "$#" -ne 1 ]]; then
    die "usage: configure_ci_slurm.sh ABSOLUTE_EVIDENCE_DIRECTORY"
fi
[[ "${CI:-}" == true && "${GITHUB_ACTIONS:-}" == true ]] ||
    die "this disposable scheduler setup is restricted to GitHub Actions"
[[ -n "${RUNNER_TEMP:-}" && "$RUNNER_TEMP" == /* && -d "$RUNNER_TEMP" ]] ||
    die "RUNNER_TEMP must be an existing absolute directory"

evidence_dir="$1"
[[ "$evidence_dir" == "$RUNNER_TEMP"/* && -d "$evidence_dir" &&
   ! -L "$evidence_dir" ]] ||
    die "evidence directory must be a real existing child of RUNNER_TEMP"

for command in dpkg mysql hostname munge openssl sacctmgr scancel scontrol \
    sinfo slurmctld slurmdbd slurmd squeue sudo systemctl timeout unmunge; do
    command -v "$command" >/dev/null 2>&1 ||
        die "required CI scheduler command is unavailable: $command"
done

collect_diagnostics() {
    local status="$1"
    trap - EXIT
    set +e
    slurmctld -V > "$evidence_dir/slurmctld-version.txt" 2>&1
    # shellcheck disable=SC2024 # Slurm reads its private config; the runner owns the evidence file.
    sudo -u slurm -- slurmdbd -V > "$evidence_dir/slurmdbd-version.txt" 2>&1
    slurmd -V > "$evidence_dir/slurmd-version.txt" 2>&1
    scancel -V > "$evidence_dir/scancel-version.txt" 2>&1
    mysql --version > "$evidence_dir/mysql-version.txt" 2>&1
    dpkg-query -W -f='${binary:Package}\t${Version}\n' \
        munge slurm-client slurmctld slurmdbd slurmd slurm-wlm-basic-plugins \
        slurm-wlm-mysql-plugin \
        > "$evidence_dir/debian-packages.tsv" 2>&1
    # shellcheck disable=SC2024 # Privileged read; the runner owns the destination.
    sudo cat /etc/slurm/slurm.conf > "$evidence_dir/slurm.conf" 2>&1
    # shellcheck disable=SC2024 # Privileged read; the runner owns the destination.
    sudo cat /var/log/slurm/slurmctld.log > "$evidence_dir/slurmctld.log" 2>&1
    # shellcheck disable=SC2024 # Privileged read; the runner owns the destination.
    sudo cat /var/log/slurm/slurmd.log > "$evidence_dir/slurmd.log" 2>&1
    scontrol ping > "$evidence_dir/scontrol-ping.txt" 2>&1
    scontrol show nodes -o > "$evidence_dir/scontrol-nodes.txt" 2>&1
    sinfo --all --long > "$evidence_dir/sinfo.txt" 2>&1
    timeout 5 sacctmgr --noheader --parsable2 show clusters format=Cluster \
        > "$evidence_dir/accounting-clusters.txt" 2>&1
    timeout 5 squeue --clusters=emrys-ci --noheader \
        > "$evidence_dir/cluster-scoped-squeue.txt" 2>&1
    systemctl --no-pager --full status munge slurmctld slurmd \
        > "$evidence_dir/systemd-status.txt" 2>&1
    systemctl show --property=Id,ActiveState,SubState,Result,ExecMainStatus \
        mysql slurmdbd > "$evidence_dir/accounting-systemd-state.txt" 2>&1
    # Do not upload the private slurmdbd.conf, database logs, or database journal.
    # shellcheck disable=SC2024 # Privileged read; the runner owns the destination.
    sudo journalctl --no-pager -u munge -u slurmctld -u slurmd \
        > "$evidence_dir/journal.txt" 2>&1
    exit "$status"
}

config_pending=""
finish() {
    local status="$1"
    trap - EXIT
    if [[ -n "$config_pending" ]]; then
        rm -f -- "$config_pending"
    fi
    collect_diagnostics "$status"
}
trap 'finish "$?"' EXIT

node_name="$(hostname -s)"
[[ "$node_name" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] ||
    die "runner hostname is unsafe for Slurm: $node_name"
node_probe="$(slurmd -C)"
node_record="${node_probe%%$'\n'*}"
[[ "$node_record" == "NodeName=$node_name "* ]] ||
    die "slurmd hardware probe did not describe the current runner node"
printf '%s\n' "$node_probe" > "$evidence_dir/slurmd-hardware.txt"

if [[ ! -s /etc/munge/munge.key ]]; then
    umask 077
    openssl rand -hex 512 | sudo tee /etc/munge/munge.key >/dev/null
fi
sudo chown munge:munge /etc/munge/munge.key
sudo chmod 0400 /etc/munge/munge.key

sudo install -d -o slurm -g slurm -m 0755 /var/spool/slurmctld /var/log/slurm
sudo install -d -o root -g root -m 0755 /var/spool/slurmd

config_pending="$(mktemp "$RUNNER_TEMP/emrys-slurm-conf.XXXXXX")"
{
    printf '%s\n' \
        'ClusterName=emrys-ci' \
        "SlurmctldHost=$node_name" \
        'SlurmUser=slurm' \
        'AuthType=auth/munge' \
        'CredType=cred/munge' \
        'MpiDefault=none' \
        'ProctrackType=proctrack/linuxproc' \
        'TaskPlugin=task/none' \
        'ReturnToService=2' \
        'KillWait=300' \
        'SchedulerType=sched/backfill' \
        'SelectType=select/cons_tres' \
        'SelectTypeParameters=CR_Core_Memory' \
        'JobAcctGatherType=jobacct_gather/none' \
        'AccountingStorageType=accounting_storage/slurmdbd' \
        'AccountingStorageHost=localhost' \
        'StateSaveLocation=/var/spool/slurmctld' \
        'SlurmdSpoolDir=/var/spool/slurmd' \
        'SlurmctldLogFile=/var/log/slurm/slurmctld.log' \
        'SlurmdLogFile=/var/log/slurm/slurmd.log' \
        'SlurmctldDebug=info' \
        'SlurmdDebug=info' \
        "$node_record State=UNKNOWN" \
        "PartitionName=emrys-ci Nodes=$node_name Default=YES MaxTime=INFINITE State=UP"
} > "$config_pending"
sudo install -o root -g root -m 0644 "$config_pending" /etc/slurm/slurm.conf
rm -f -- "$config_pending"
config_pending=""

# Both Slurm clients and slurmdbd read their configuration when asked only for
# their version. Install the disposable files before probing them, but do not
# change database state until every release has passed the version gate.
db_password="$(openssl rand -hex 32)"
config_pending="$(mktemp "$RUNNER_TEMP/emrys-slurmdbd-conf.XXXXXX")"
{
    printf '%s\n' \
        'AuthType=auth/munge' \
        'DbdHost=localhost' \
        'SlurmUser=slurm' \
        'StorageType=accounting_storage/mysql' \
        'StorageHost=localhost' \
        'StorageLoc=emrys_ci_slurm' \
        'StorageUser=emrys_ci_slurm' \
        "StoragePass=$db_password" \
        'LogFile=/var/log/slurm/slurmdbd.log'
} > "$config_pending"
sudo install -o slurm -g slurm -m 0600 "$config_pending" /etc/slurm/slurmdbd.conf
rm -f -- "$config_pending"
config_pending=""

# The production stop path needs a version with exact cluster-scoped scancel.
slurm_release=""
for command in scancel slurmctld slurmdbd slurmd; do
    if [[ "$command" == slurmdbd ]]; then
        version="$(sudo -u slurm -- "$command" -V)"
    else
        version="$("$command" -V)"
    fi
    [[ "$version" =~ ^slurm(-wlm)?[[:space:]]+([0-9]+\.[0-9]+\.[0-9]+)$ ]] ||
        die "cannot determine $command Slurm release"
    if [[ -z "$slurm_release" ]]; then
        slurm_release="${BASH_REMATCH[2]}"
    else
        [[ "${BASH_REMATCH[2]}" == "$slurm_release" ]] ||
            die "Slurm daemon/client releases do not match"
    fi
done
dpkg --compare-versions "$slurm_release" ge 23.11.6 ||
    die "Slurm release is below the exact-cancellation minimum"
printf '%s\n' "$slurm_release" > "$evidence_dir/qualified-slurm-release.txt"

sudo systemctl start mysql
# GitHub's disposable Ubuntu 26.04 image documents root/root for MySQL. Keep
# that public image default in a private, runner-local client file rather than
# a command argument, environment variable, log, or uploaded evidence root.
config_pending="$(mktemp "$RUNNER_TEMP/emrys-mysql-admin.XXXXXX")"
printf '[client]\nuser=root\npassword=root\n' > "$config_pending"
sudo mysql --defaults-file="$config_pending" --no-login-paths \
    --protocol=socket --batch --skip-column-names -e 'SELECT 1' \
    >/dev/null || die "documented CI image MySQL administration is unavailable"
sudo mysql --defaults-file="$config_pending" --no-login-paths \
    --protocol=socket <<SQL
CREATE DATABASE IF NOT EXISTS emrys_ci_slurm;
CREATE USER IF NOT EXISTS 'emrys_ci_slurm'@'localhost' IDENTIFIED BY '$db_password';
GRANT ALL PRIVILEGES ON emrys_ci_slurm.* TO 'emrys_ci_slurm'@'localhost';
SQL
rm -f -- "$config_pending"
config_pending=""
unset db_password

sudo systemctl restart munge
munge -n | unmunge > "$evidence_dir/munge-round-trip.txt"
sudo systemctl restart slurmdbd
accounting_ready=false
for ((attempt = 1; attempt <= 30; attempt++)); do
    if timeout 5 sacctmgr --noheader --parsable2 show clusters format=Cluster \
        >/dev/null 2>&1; then
        accounting_ready=true
        break
    fi
    sleep 1
done
[[ "$accounting_ready" == true ]] || die "CI Slurm accounting service did not become ready"
sudo sacctmgr --immediate add cluster emrys-ci >/dev/null
sudo systemctl restart slurmctld
sudo systemctl restart slurmd

ready=false
for ((attempt = 1; attempt <= 30; attempt++)); do
    state="$(sinfo --noheader --partition=emrys-ci --format='%T' 2>/dev/null || true)"
    clusters="$(timeout 5 sacctmgr --noheader --parsable2 show clusters format=Cluster 2>/dev/null || true)"
    if scontrol ping 2>/dev/null | grep -Fq 'UP' &&
       [[ "$state" =~ ^[[:space:]]*idle[[:space:]]*$ ]] &&
       grep -Fxq 'emrys-ci' <<< "$clusters" &&
       timeout 5 squeue --clusters=emrys-ci --noheader >/dev/null 2>&1; then
        ready=true
        break
    fi
    sleep 1
done
[[ "$ready" == true ]] ||
    die "single-node CI Slurm partition/accounting did not become ready"
printf 'cluster=emrys-ci\nnode=%s\nslurm_release=%s\ncontroller=up\npartition=idle\naccounting=registered\ncluster_scoped_squeue=exit_0\n' \
    "$node_name" "$slurm_release" > "$evidence_dir/qualified-readiness.txt"
printf 'CI Slurm ready: partition=emrys-ci node=%s release=%s accounting=available\n' \
    "$node_name" "$slurm_release"
