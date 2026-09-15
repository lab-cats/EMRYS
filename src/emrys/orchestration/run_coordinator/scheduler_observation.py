"""Standard-library-only observations of Slurm records, without Run authority."""

import os
import re
import shlex
import subprocess


TERMINAL_STATES = {
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    "TIMEOUT",
    "OUT_OF_MEMORY",
    "NODE_FAIL",
    "PREEMPTED",
    "BOOT_FAIL",
    "DEADLINE",
    "REVOKED",
}

# Base states and flags documented at slurm.schedmd.com/job_state_codes.html.
JOB_STATES = TERMINAL_STATES | {
    "PENDING",
    "RUNNING",
    "SUSPENDED",
    "COMPLETING",
    "CONFIGURING",
    "EXPEDITING",
    "LAUNCH_FAILED",
    "POWER_UP_NODE",
    "RECONFIG_FAIL",
    "REQUEUED",
    "REQUEUE_FED",
    "REQUEUE_HOLD",
    "RESIZING",
    "RESV_DEL_HOLD",
    "SIGNALING",
    "SPECIAL_EXIT",
    "STAGE_OUT",
    "STOPPED",
    "UPDATE_DB",
}


JOB_ID_RE = re.compile(r"^[1-9][0-9]*$")


class DiscoveryError(RuntimeError):
    """Raised when scheduler metadata cannot establish an exact observation."""


def command_bytes(argv, timeout=10, environment=None):
    try:
        completed = subprocess.run(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def command_text(argv, timeout=10):
    result = command_bytes(argv, timeout=timeout)
    return "" if result is None else result.decode("utf-8", "replace").strip()


def unknown_observation(diagnostic):
    return {
        "state": "UNKNOWN",
        "terminal": False,
        "source": None,
        "cluster": None,
        "diagnostic": diagnostic,
    }


def _cluster_name(value):
    return (
        isinstance(value, str)
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value) is not None
        and value.lower() != "all"
    )


def observe_job(job_id, stdout_pattern, stderr_pattern, cluster=None, *, job_name=None):
    """Observe an exact owned job/path binding; the caller owns request uniqueness."""
    if not JOB_ID_RE.fullmatch(str(job_id)) or (
        cluster is not None and not _cluster_name(cluster)
    ):
        return unknown_observation(
            "The recorded job ID or cluster cannot be queried exactly"
        )
    try:
        if job_name is not None and (
            not isinstance(job_name, str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", job_name) is None
        ):
            raise DiscoveryError("Recorded scheduler name is not one bounded name")
        extra_names = ("JobName",) if job_name is not None else ()
        expected = []
        for value in (stdout_pattern, stderr_pattern):
            if (
                not isinstance(value, str)
                or "\0" in value
                or not os.path.isabs(value)
                or os.path.abspath(value) != value
            ):
                raise DiscoveryError(
                    "Recorded scheduler paths are not absolute normalized paths"
                )
            expected.append(expand_job_path(value, job_id))
        scope = ["--local"] if cluster is None else ["--clusters=" + cluster]
        environment = {
            key: value
            for key, value in os.environ.items()
            if key != "SLURM_CLUSTERS" and not key.startswith(("SQUEUE_", "SACCT_"))
        }
        sources = (
            (
                "squeue",
                [
                    "squeue",
                    *scope,
                    "-h",
                    "-j",
                    str(job_id),
                    "-O",
                    # Like %i, JobArrayId preserves array and heterogeneous suffixes.
                    "JobArrayId:0|,UserID:0|,State:0|,Cluster:0|,STDOUT:0|,STDERR:0|,Reason:0"
                    + ("|,Name:0" if extra_names else ""),
                ],
                ("JobId", "UID", "JobState", "Cluster", "StdOut", "StdErr", "Reason")
                + extra_names,
            ),
            (
                "sacct",
                [
                    "sacct",
                    *scope,
                    "--duplicates",
                    "-X",
                    "-n",
                    "-P",
                    "-j",
                    str(job_id),
                    "--format=JobIDRaw,UID,State,Cluster,StdOut,StdErr,ExitCode"
                    + (",JobName" if extra_names else ""),
                ],
                ("JobId", "UID", "JobState", "Cluster", "StdOut", "StdErr", "ExitCode")
                + extra_names,
            ),
        )
        for source, argv, names in sources:
            reply = command_bytes(argv, environment=environment)
            if reply is None:
                raise DiscoveryError(source + " query failed or is unavailable")
            if len(reply) > 65536:
                raise DiscoveryError(source + " metadata exceeds the observation limit")
            text = reply.decode("utf-8")
            if not text and source == "squeue":
                continue
            rows = [line.split("|") for line in text.splitlines()]
            if len(rows) != 1 or len(rows[0]) != len(names):
                raise DiscoveryError(
                    source + " did not return one complete exact root record"
                )
            metadata = dict(zip(names, rows[0]))
            validate_scheduler_identity(job_id, metadata)
            if job_name is not None and metadata["JobName"] != job_name:
                raise DiscoveryError(
                    "Scheduler job name differs from the recorded request"
                )
            observed_cluster = metadata["Cluster"]
            if not _cluster_name(observed_cluster) or (
                cluster is not None and observed_cluster != cluster
            ):
                raise DiscoveryError("Scheduler cluster differs or is unconfirmed")
            for key, path in zip(("StdOut", "StdErr"), expected):
                if expand_job_path(metadata[key], job_id) != path:
                    raise DiscoveryError(
                        "Scheduler stream paths differ from the recorded request"
                    )
            state = metadata["JobState"]
            if source == "sacct" and re.fullmatch(
                r"CANCELLED by (?:0|[1-9][0-9]*)", state
            ):
                state = "CANCELLED"
            if state not in JOB_STATES:
                raise DiscoveryError(
                    "Scheduler job state is not recognized or complete"
                )
            if source == "sacct":
                validate_accounting_identity(job_id, metadata)
                exit_code = metadata["ExitCode"]
                if not re.fullmatch(
                    r"(0|[1-9][0-9]{0,2}):(0|[1-9][0-9]{0,2})", exit_code
                ) or any(
                    int(value) > limit
                    for value, limit in zip(exit_code.split(":"), (255, 127))
                ):
                    raise DiscoveryError("Accounting ExitCode is missing or malformed")
            result = {
                "state": state,
                "terminal": state in TERMINAL_STATES,
                "source": source,
                "cluster": observed_cluster,
                "diagnostic": None,
            }
            if job_name is not None:
                result["job_name"] = metadata["JobName"]
            if source == "sacct":
                result["exit_code"] = metadata["ExitCode"]
            else:
                result["reason"] = metadata["Reason"]
            return result
    except (DiscoveryError, UnicodeError) as exc:
        return unknown_observation(str(exc))


def parse_key_value_line(value):
    fields = {}
    try:
        tokens = shlex.split(value)
    except ValueError:
        return fields
    for token in tokens:
        if "=" in token:
            key, item = token.split("=", 1)
            if key in fields:
                return {}
            fields[key] = item
    return fields


def slurm_job_metadata(job_id):
    output = command_text(["scontrol", "show", "job", "-o", str(job_id)])
    if not output:
        return None
    rows = output.splitlines()
    if len(rows) != 1:
        raise DiscoveryError("Slurm did not return one exact root record")
    fields = parse_key_value_line(rows[0])
    validate_scheduler_identity(job_id, fields, owner_field="UserId")
    return fields


def slurm_accounting_metadata(job_id):
    """Return one exact root-allocation record from bounded Slurm accounting.

    Prefer scheduler-declared stream paths.  Older Slurm accounting deployments
    may reject ``StdOut``/``StdErr`` fields, so make one bounded basic-field
    fallback query for identity/state proof. Include duplicate IDs so accounting
    cannot silently select the most recent submission. Neither query searches storage.
    """
    for streams in (("StdOut", "StdErr"), ()):
        names = (
            ("JobIDRaw", "JobName", "State", "User", "UID")
            + streams
            + ("ExitCode", "Elapsed", "AllocCPUS", "NodeList")
        )
        output = command_text(
            [
                "sacct",
                "--duplicates",
                "-X",
                "-n",
                "-P",
                "-j",
                str(job_id),
                "--format=" + ",".join(names),
            ]
        )
        if not output:
            continue
        rows = [line.split("|") for line in output.splitlines()]
        roots = [row for row in rows if JOB_ID_RE.fullmatch(row[0].strip())]
        if len(roots) != 1 or len(roots[0]) != len(names):
            raise DiscoveryError(
                "Slurm accounting did not return one exact root record for job %s"
                % job_id
            )
        metadata = dict(zip(names, (value.strip() for value in roots[0])))
        metadata["JobId"] = metadata.pop("JobIDRaw")
        metadata["JobState"] = metadata.pop("State")
        validate_scheduler_identity(job_id, metadata)
        return metadata
    raise DiscoveryError("Slurm accounting metadata is unavailable for job %s" % job_id)


def validate_scheduler_identity(job_id, metadata, owner_field="UID"):
    """Prove a root ID and numeric owner, never a submission or recovery identity."""
    if not JOB_ID_RE.fullmatch(str(job_id)) or metadata.get("JobId") != str(job_id):
        raise DiscoveryError("Slurm returned metadata for a different or missing job")
    uid = str(os.getuid())
    owner = metadata.get(owner_field, "")
    if owner != uid and not (
        owner_field == "UserId" and re.fullmatch(r"[^()\s]+\(" + uid + r"\)", owner)
    ):
        raise DiscoveryError("job %s is not owned by the current UID" % job_id)
    if not normalized_job_state(metadata.get("JobState")):
        raise DiscoveryError("Slurm did not report a job state")


def expand_job_path(value, job_id):
    value = value.replace("%j", str(job_id))
    if "%" in value:
        raise DiscoveryError(
            "scheduler log path contains an unsupported Slurm placeholder: %s" % value
        )
    return value


def normalized_job_state(value):
    """Strip Slurm decorations such as ``+`` and ``CANCELLED by <uid>``."""
    return re.split(r"[+\s]", (value or "").strip(), maxsplit=1)[0]


def validate_accounting_identity(job_id, metadata):
    """Prove that one accounting record is the current user's terminal job."""
    validate_scheduler_identity(job_id, metadata)
    state_value = normalized_job_state(metadata.get("JobState"))
    if state_value not in TERMINAL_STATES:
        raise DiscoveryError(
            "job %s is not terminal; live selection requires scontrol metadata" % job_id
        )


def query_slurm(job_id, out_path=None, err_path=None):
    """Observe one owned scheduler job; ID/path reuse cannot identify a request."""
    unknown = {"terminal": False, "state": "UNKNOWN"}
    if not JOB_ID_RE.fullmatch(str(job_id)):
        return unknown
    row = command_text(
        ["squeue", "-h", "-j", str(job_id), "-o", "%i|%U|%T|%M|%L|%C|%P|%N|%R"]
    )
    try:
        if row:
            rows = row.splitlines()
            parts = [value.strip() for value in rows[0].split("|", 8)]
            if len(rows) != 1 or len(parts) != 9:
                return unknown
            metadata = dict(
                zip(
                    (
                        "JobId",
                        "UID",
                        "JobState",
                        "Elapsed",
                        "left",
                        "AllocCPUS",
                        "partition",
                        "NodeList",
                        "reason",
                    ),
                    parts,
                )
            )
            validate_scheduler_identity(job_id, metadata)
        else:
            metadata = slurm_accounting_metadata(job_id)
            validate_accounting_identity(job_id, metadata)
        if out_path or err_path:
            streams = slurm_job_metadata(job_id) if row else metadata
            if streams is None:
                return unknown
            validate_scheduler_identity(
                job_id, streams, owner_field="UserId" if row else "UID"
            )
            for key, expected in (("StdOut", out_path), ("StdErr", err_path)):
                declared = streams.get(key, "")
                if (
                    not expected
                    or not declared
                    or expand_job_path(declared, job_id) != expected
                ):
                    return unknown
    except DiscoveryError:
        return unknown
    state = normalized_job_state(metadata.get("JobState"))
    result = {"terminal": state in TERMINAL_STATES, "state": state}
    for key, field in (
        ("elapsed", "Elapsed"),
        ("left", "left"),
        ("cpus", "AllocCPUS"),
        ("partition", "partition"),
        ("node", "NodeList"),
        ("reason", "reason"),
        ("exit_code", "ExitCode"),
    ):
        if metadata.get(field):
            result[key] = metadata[field]
    if row:
        usage = command_text(
            [
                "sstat",
                "-n",
                "-P",
                "-j",
                "%s.batch" % job_id,
                "--format=JobID,AveCPU,MaxRSS,MaxDiskRead,MaxDiskWrite",
            ]
        )
        if usage:
            rows = usage.splitlines()
            fields = rows[0].split("|")
            if len(rows) == 1 and len(fields) >= 5 and fields[0] == "%s.batch" % job_id:
                result.update(
                    {
                        "ave_cpu": fields[1],
                        "max_rss": fields[2],
                        "disk_read": fields[3],
                        "disk_write": fields[4],
                    }
                )
    return result
