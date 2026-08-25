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

for command in hostname munge openssl scontrol sinfo slurmctld slurmd sudo systemctl unmunge; do
    command -v "$command" >/dev/null 2>&1 ||
        die "required CI scheduler command is unavailable: $command"
done

collect_diagnostics() {
    local status="$1"
    trap - EXIT
    set +e
    slurmctld -V > "$evidence_dir/slurmctld-version.txt" 2>&1
    slurmd -V > "$evidence_dir/slurmd-version.txt" 2>&1
    dpkg-query -W -f='${binary:Package}\t${Version}\n' \
        munge slurm-client slurmctld slurmd slurm-wlm-basic-plugins \
        > "$evidence_dir/debian-packages.tsv" 2>&1
    sudo cat /etc/slurm/slurm.conf > "$evidence_dir/slurm.conf" 2>&1
    scontrol ping > "$evidence_dir/scontrol-ping.txt" 2>&1
    scontrol show nodes -o > "$evidence_dir/scontrol-nodes.txt" 2>&1
    sinfo --all --long > "$evidence_dir/sinfo.txt" 2>&1
    systemctl --no-pager --full status munge slurmctld slurmd \
        > "$evidence_dir/systemd-status.txt" 2>&1
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
node_record="${node_probe%% UpTime=*}"
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
        'CryptoType=crypto/munge' \
        'MpiDefault=none' \
        'ProctrackType=proctrack/linuxproc' \
        'TaskPlugin=task/none' \
        'ReturnToService=2' \
        'SchedulerType=sched/backfill' \
        'SelectType=select/cons_tres' \
        'SelectTypeParameters=CR_Core_Memory' \
        'JobAcctGatherType=jobacct_gather/none' \
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

sudo systemctl restart munge
munge -n | unmunge > "$evidence_dir/munge-round-trip.txt"
sudo systemctl restart slurmctld
sudo systemctl restart slurmd

ready=false
for ((attempt = 1; attempt <= 30; attempt++)); do
    state="$(sinfo --noheader --partition=emrys-ci --format='%T' 2>/dev/null || true)"
    if scontrol ping 2>/dev/null | grep -Fq 'UP' &&
       [[ "$state" =~ ^[[:space:]]*idle[[:space:]]*$ ]]; then
        ready=true
        break
    fi
    sleep 1
done
[[ "$ready" == true ]] || die "single-node CI Slurm partition did not become idle"
printf 'CI Slurm ready: partition=emrys-ci node=%s\n' "$node_name"
