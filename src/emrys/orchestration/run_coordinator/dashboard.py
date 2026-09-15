#!/usr/bin/python3
"""Responsive, read-only EMRYS/Slurm live dashboard v4.9.

This is an operational view over append-only scheduler streams. It does not
replace EMRYS inspection or completion evidence.
"""

import argparse
import importlib.util
import curses
import datetime as dt
import os
import re
import statistics
import stat
import sys
import threading
import time
import textwrap


if __package__:
    from . import scheduler_observation as _scheduler
else:
    # The Make entry point uses Python -I; load only this exact adjacent stdlib owner.
    _scheduler_spec = importlib.util.spec_from_file_location(
        "emrys_scheduler_observation",
        os.path.join(os.path.dirname(__file__), "scheduler_observation.py"),
    )
    _scheduler = importlib.util.module_from_spec(_scheduler_spec)
    _scheduler_spec.loader.exec_module(_scheduler)


STAGES = [
    (
        "00a",
        "STAR index",
        None,
        "construct_STAR_index",
        "Builds STAR's reusable genome index from the admitted FASTA and GTF. "
        "STAR converts the reference sequence, contig layout, and annotated splice "
        "junctions into the search structures required for alignment. Completing "
        "this once lets every sample use the same content-bound reference model.",
        "1 process x 2 STAR threads; sample concurrency does not apply.",
    ),
    (
        "00b",
        "GTF to BED12",
        None,
        "convert_GTF_to_BED12",
        "Converts the GTF transcript annotation into a BED12 gene model. The BED12 "
        "representation preserves exon blocks in a form that RSeQC can compare "
        "against aligned reads. That comparison is later used to verify the "
        "library-orientation evidence for each sample.",
        "1 owner process.",
    ),
    (
        "00c",
        "FASTA sidecars",
        None,
        "construct_FASTA_sidecars",
        "Creates or verifies the FASTA index and sequence-dictionary sidecars beside "
        "the reference. These files provide random-access coordinates plus a stable "
        "contig identity and order for Samtools, GATK, and the R analysis layer. The "
        "step prevents downstream tools from silently interpreting the same FASTA differently.",
        "1 owner process.",
    ),
    (
        "01",
        "STAR alignment",
        None,
        "align_RNA_reads_with_STAR",
        "Maps each paired FASTQ library to the admitted reference with STAR. STAR "
        "uses the shared index and splice-junction model to place RNA-derived reads "
        "across exons and introns. Each sample runs independently so admitted "
        "libraries can advance concurrently while preserving separate evidence.",
        "Up to 6 sample processes x 2 STAR threads (12 nominal threads).",
    ),
    (
        "02",
        "Canonical BAM",
        None,
        "construct_canonical_BAM",
        "Normalizes each STAR alignment into EMRYS's indexed canonical BAM. This "
        "establishes the stable per-sample alignment representation consumed by QC, "
        "orientation analysis, duplicate marking, and variant preparation. Downstream "
        "owners therefore bind to one validated BAM rather than tool-specific intermediates.",
        "Up to 6 sample processes x 2 configured threads.",
    ),
    (
        "02b",
        "BAM QC",
        None,
        "collect_canonical_BAM_QC_evidence",
        "Checks each canonical BAM and records its per-sample QC evidence. The owner "
        "confirms that the alignment artifact satisfies the workflow's structural and "
        "content expectations before more expensive processing begins. Its evidence "
        "makes a passing BAM an explicit prerequisite rather than an assumed input.",
        "Up to 6 sample processes.",
    ),
    (
        "03",
        "RSeQC orientation",
        None,
        "collect_RSeQC_paired_orientation_evidence",
        "Uses RSeQC to compare each paired-read alignment with the BED12 transcript "
        "model and infer library orientation. EMRYS records the observed orientation "
        "as evidence for the declared strandedness. That evidence determines how the "
        "workflow interprets directional reads in the later orientation split.",
        "Up to 6 sample processes.",
    ),
    (
        "04",
        "Picard duplicates",
        None,
        "mark_BAM_duplicates_with_Picard",
        "Runs Picard MarkDuplicates on each canonical BAM and records duplicate metrics. "
        "Duplicate observations remain represented but are explicitly flagged, which "
        "prevents amplification artifacts from masquerading as independent support. "
        "The resulting indexed BAM becomes the input to RNA-aware GATK preparation.",
        "Up to 6 sample processes; each runs one Java/Picard process.",
    ),
    (
        "05",
        "GATK SplitNCigarReads",
        None,
        "split_N_cigar_reads_with_GATK",
        "Runs GATK SplitNCigarReads on each duplicate-marked RNA alignment. The tool "
        "splits reads at intronic N-cigar junctions and normalizes the alignments into "
        "the representation expected by downstream variant processing. This bridges "
        "splice-aware RNA alignment with position-based cohort pileup analysis.",
        "Up to 6 GATK processes; JVM/native threads may exceed the nominal 12.",
    ),
    (
        "06",
        "Orientation BAM split",
        None,
        "partition_BAM_by_mechanical_read_orientation",
        "Separates each prepared BAM into forward-like and reverse-like mechanical "
        "orientation artifacts. Keeping these observations distinct preserves the "
        "directional structure needed to evaluate strand-associated signal and artifacts. "
        "Both indexed outputs must finish before that sample is ready for cohort analysis.",
        "Up to 6 sample processes x 2 configured threads.",
    ),
    (
        "07",
        "Partitioned mpileup",
        None,
        "generate_partitioned_cohort_mpileup_VCFs",
        "Generates cohort mpileup VCF evidence across the declared genomic partitions. "
        "Each partition evaluates the aligned observations from all admitted samples "
        "while retaining the workflow's orientation structure. Partitioning bounds the "
        "working set and produces validated pieces for one cohort-level candidate set.",
        "Partition owners share the 12-core workflow envelope.",
    ),
    (
        "08",
        "Candidate preprocessing",
        None,
        "preprocess_and_annotate_cohort_candidates",
        "Combines the validated partition outputs into one cohort candidate collection. "
        "It normalizes and annotates the raw site evidence, applies the declared analysis "
        "policy, and prepares stable rows for statistical testing. This is the main "
        "cohort-scale reduction between pileup generation and paired inference.",
        "1 cohort process using 2 configured threads where supported.",
    ),
    (
        "09",
        "Paired CMH ranking",
        None,
        "rank_cohort_candidates_with_paired_CMH",
        "Tests cohort candidates with the paired Cochran-Mantel-Haenszel analysis across "
        "the declared replicate strata. It compares treatment with control while "
        "preserving pairing, adjusts the resulting evidence for multiple testing, and "
        "ranks candidates under the request's scientific thresholds. The ranked cohort "
        "evidence becomes the input to scientific-context projection and reporting.",
        "1 R analysis process.",
    ),
    (
        "10",
        "Scientific context",
        None,
        "project_candidate_scientific_context",
        "Projects statistically selected candidates back into reference-sequence and "
        "transcript-annotation context. The analysis adds the surrounding features "
        "needed to interpret where each signal occurs and selects the display-ranked "
        "subset used by the scientific report. It does not turn computational evidence into biological proof.",
        "1 R analysis process.",
    ),
    (
        "REPORT",
        "Automatic reports",
        None,
        "build_artifact_index",
        "Builds the artifact index, canonical run summary, and final HTML report as "
        "three dependent reporting transactions. These products bind the verified "
        "owner outputs into an inspectable execution record. Reporting summarizes the "
        "run without replacing its underlying task evidence or validation receipts.",
        "3 dependent reporting transactions, normally sequential.",
    ),
    (
        "FINAL",
        "Aggregate target",
        None,
        "local_pipeline_slice",
        "Closes the aggregate workflow target after every scientific owner and reporting "
        "transaction succeeds. It performs no new scientific computation; its purpose "
        "is to prove that the requested pipeline slice reached its complete dependency "
        "state. Final EMRYS inspection remains the completion authority after Slurm exits.",
        "No additional scientific computation.",
    ),
]

RULE_TO_STAGE = {row[3]: row[0] for row in STAGES}
RULE_TO_STAGE.update(
    {
        "build_run_summary": "REPORT",
        "build_html_report": "REPORT",
        "cohort_slice": "FINAL",
        "emrys.analysis.rank_cohort_candidates_with_paired_CMH.v1": "09",
        "emrys.analysis.project_candidate_scientific_context.v1": "10",
    }
)
STAGE_BY_KEY = {row[0]: row for row in STAGES}
SAMPLE_STAGE_KEYS = ("01", "02", "02b", "03", "04", "05", "06")
SAMPLE_STAGES = set(SAMPLE_STAGE_KEYS)
MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}
TIMESTAMP_RE = re.compile(
    r"^\[[A-Z][a-z]{2} ([A-Z][a-z]{2})\s+(\d+) "
    r"(\d\d):(\d\d):(\d\d) (\d{4})\]$"
)
ANSI_CSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
ANSI_OSC_RE = re.compile(r"\x1b\].*?(?:\x07|\x1b\\)")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
DISCOVERY_DAYS = 7
_STREAM_WAIT_SECONDS = 1.0
_STREAM_READ_CHUNK = 64 * 1024


def _stream_identity(state):
    return state.st_dev, state.st_ino, state.st_mode, state.st_uid


def _read_stream(path, offset, previous):
    """Read one captured generation through pinned directories; bytes are diagnostic."""
    if not os.path.isabs(path) or os.path.normpath(path) != path:
        raise ValueError("Stream path must be absolute and canonical")
    descriptors = []
    directories = []
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        parent = os.open(os.sep, directory_flags)
        descriptors.append(parent)
        current = os.sep
        directories.append((current, _stream_identity(os.fstat(parent))))
        for component in path.split(os.sep)[1:-1]:
            parent = os.open(component, directory_flags, dir_fd=parent)
            descriptors.append(parent)
            current = os.path.join(current, component)
            directories.append((current, _stream_identity(os.fstat(parent))))
        if os.fstat(parent).st_uid != os.getuid():
            raise ValueError("Stream directory is not owned by the current UID")
        name = os.path.basename(path)
        before = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid():
            raise ValueError("Stream must be a regular file owned by the current UID")
        descriptor = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
        )
        descriptors.append(descriptor)
        opened = os.fstat(descriptor)
        if _stream_identity(opened) != _stream_identity(before):
            raise ValueError("Stream changed while opened")
        reset = previous is None or _stream_identity(previous) != _stream_identity(
            opened
        )
        reason = "Current diagnostic bytes; content not verified"
        if previous is not None:
            if reset:
                reason += "; replaced since previous observation"
            elif opened.st_size < offset:
                reset = True
                reason += "; truncated since previous observation"
            elif opened.st_size <= previous.st_size and (
                opened.st_mtime_ns,
                opened.st_ctime_ns,
            ) != (previous.st_mtime_ns, previous.st_ctime_ns):
                reset = True
                reason += "; changed since previous observation"
        start = 0 if reset else offset
        os.lseek(descriptor, start, os.SEEK_SET)
        remaining = opened.st_size - start
        data = bytearray()
        while remaining:
            chunk = os.read(descriptor, min(remaining, _STREAM_READ_CHUNK))
            if not chunk:
                raise ValueError("Stream truncated while read")
            data.extend(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
        named = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if (
            _stream_identity(after) != _stream_identity(opened)
            or _stream_identity(named) != _stream_identity(opened)
            or after.st_size < opened.st_size
            or (
                after.st_size == opened.st_size
                and (after.st_mtime_ns, after.st_ctime_ns)
                != (opened.st_mtime_ns, opened.st_ctime_ns)
            )
            or any(
                _stream_identity(os.lstat(directory)) != identity
                for directory, identity in directories
            )
        ):
            raise ValueError("Stream or ancestor changed while read")
        return start, data, after, time.time(), reason
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


class StreamCache:
    """Full diagnostic history with one bounded-wait daemon read per stream."""

    def __init__(self, path):
        self.path = os.fspath(path)
        self.offset = 0
        self.data = bytearray()
        self.diagnostic = "Not yet read"
        self.observed_at = None
        self._state = None
        self._reader = None
        self._result = None
        self._closed = False
        self._lock = threading.Lock()

    @property
    def pending(self):
        return self._reader is not None and self._reader.is_alive()

    def _read(self):
        try:
            self._result = _read_stream(self.path, self.offset, self._state)
        except Exception as exc:
            self._result = "Unavailable: " + sanitize_text(str(exc))

    def close(self):
        """Prevent further reads without waiting for a blocked daemon."""
        with self._lock:
            self._closed = True

    def sync(self):
        with self._lock:
            if self._closed:
                self.diagnostic = (
                    "Closed; retained history is from the previous observation"
                )
                return False
            if self._reader is None:
                self._result = None
                self._reader = threading.Thread(target=self._read, daemon=True)
                self._reader.start()
            reader = self._reader
        reader.join(_STREAM_WAIT_SECONDS)
        with self._lock:
            if self._closed or self._reader is not reader:
                return False
            if reader.is_alive():
                self.diagnostic = (
                    "Read pending; retained history is from the previous observation"
                )
                return False
            result = self._result
            self._reader = None
            if not isinstance(result, tuple):
                self.data.clear()
                self.offset = 0
                self._state = None
                self.observed_at = None
                self.diagnostic = result or "Unavailable: reader did not complete"
                return False
            start, data, self._state, self.observed_at, self.diagnostic = result
            if start == 0:
                self.data.clear()
            self.data.extend(data)
            self.offset = start + len(data)
            return True

    def text(self):
        return sanitize_text(self.data.decode("utf-8", "replace"))


def sanitize_text(value):
    """Remove terminal control sequences while preserving tabs and newlines."""
    value = ANSI_OSC_RE.sub("", value)
    value = ANSI_CSI_RE.sub("", value)
    return CONTROL_RE.sub("", value)


def accounting_log_selection(job_id, log_dir, metadata=None):
    """Admit explicit historical logs after exact terminal-job accounting proof."""
    if not os.path.isabs(log_dir):
        raise _scheduler.DiscoveryError("LOG_DIR must be an absolute path")
    if metadata is None:
        metadata = _scheduler.slurm_accounting_metadata(job_id)
    _scheduler.validate_accounting_identity(job_id, metadata)
    selection = validate_log_selection(
        job_id,
        os.path.join(log_dir, "emrys-local-pilot-%s.out" % job_id),
        os.path.join(log_dir, "emrys-local-pilot-%s.err" % job_id),
    )
    selection["selection_source"] = "sacct+explicit-log-dir"
    return selection


def accounting_stream_selection(metadata, log_dir=None):
    """Admit scheduler-declared historical streams without scanning storage."""
    job_id = metadata.get("JobId", "")
    if not _scheduler.JOB_ID_RE.fullmatch(job_id):
        raise _scheduler.DiscoveryError(
            "Slurm accounting returned an invalid root job ID"
        )
    _scheduler.validate_accounting_identity(int(job_id), metadata)
    out_path = metadata.get("StdOut")
    err_path = metadata.get("StdErr")
    if not out_path or not err_path:
        raise _scheduler.DiscoveryError(
            "Slurm accounting did not report stdout/stderr for job %s" % job_id
        )
    out_path = _scheduler.expand_job_path(out_path, job_id)
    err_path = _scheduler.expand_job_path(err_path, job_id)
    if log_dir:
        if not os.path.isabs(log_dir):
            raise _scheduler.DiscoveryError("LOG_DIR must be an absolute path")
        requested = os.path.abspath(log_dir)
        if requested != os.path.dirname(
            os.path.abspath(out_path)
        ) or requested != os.path.dirname(os.path.abspath(err_path)):
            raise _scheduler.DiscoveryError(
                "LOG_DIR disagrees with scheduler-declared stdout/stderr"
            )
    selection = validate_log_selection(job_id, out_path, err_path)
    selection["selection_source"] = "sacct-stdout-stderr"
    return selection


def validate_log_selection(job_id, out_path, err_path, allow_missing=False):
    if not os.path.isabs(out_path) or not os.path.isabs(err_path):
        raise _scheduler.DiscoveryError("scheduler log paths must be absolute")
    out_path = os.path.abspath(out_path)
    err_path = os.path.abspath(err_path)
    if not re.fullmatch(
        r"emrys-local-pilot-(?:[0-9a-f]{32}-)?%s\.out" % re.escape(str(job_id)),
        os.path.basename(out_path),
    ):
        raise _scheduler.DiscoveryError(
            "stdout does not match the EMRYS wrapper contract: %s" % out_path
        )
    if os.path.basename(err_path) != os.path.basename(out_path)[:-4] + ".err":
        raise _scheduler.DiscoveryError(
            "stderr does not match the EMRYS wrapper contract: %s" % err_path
        )
    log_dir = os.path.dirname(out_path)
    if log_dir != os.path.dirname(err_path):
        raise _scheduler.DiscoveryError(
            "stdout and stderr do not share one log directory"
        )
    try:
        directory = os.lstat(log_dir)
    except OSError as exc:
        raise _scheduler.DiscoveryError(
            "log directory is unavailable: %s" % log_dir
        ) from exc
    if stat.S_ISLNK(directory.st_mode) or not stat.S_ISDIR(directory.st_mode):
        raise _scheduler.DiscoveryError(
            "log directory must be a real directory: %s" % log_dir
        )
    if directory.st_uid != os.getuid():
        raise _scheduler.DiscoveryError(
            "log directory is not owned by the current UID: %s" % log_dir
        )
    if os.path.realpath(log_dir) != log_dir:
        raise _scheduler.DiscoveryError(
            "log directory contains a symlinked path: %s" % log_dir
        )
    for path in (out_path, err_path):
        try:
            entry = os.lstat(path)
        except FileNotFoundError:
            if allow_missing:
                continue
            raise _scheduler.DiscoveryError("scheduler log is not present: %s" % path)
        except OSError as exc:
            raise _scheduler.DiscoveryError(
                "scheduler log is unavailable: %s" % path
            ) from exc
        if stat.S_ISLNK(entry.st_mode) or not stat.S_ISREG(entry.st_mode):
            raise _scheduler.DiscoveryError(
                "scheduler log must be a real regular file: %s" % path
            )
        if entry.st_uid != os.getuid() or not os.access(path, os.R_OK):
            raise _scheduler.DiscoveryError(
                "scheduler log is not owned/readable by the current UID: %s" % path
            )
    return {
        "job_id": int(job_id),
        "log_dir": log_dir,
        "out": out_path,
        "err": err_path,
    }


def scheduler_candidates():
    """Return bounded live and recent candidates with available path metadata."""
    user = str(os.getuid())
    live = _scheduler.command_text(
        [
            "squeue",
            "-h",
            "-u",
            user,
            "-o",
            "%i|%T",
        ]
    )
    live_ids = []
    for line in live.splitlines():
        job_id = line.split("|", 1)[0].strip()
        if _scheduler.JOB_ID_RE.fullmatch(job_id):
            live_ids.append(int(job_id))

    since = (dt.date.today() - dt.timedelta(days=DISCOVERY_DAYS)).isoformat()
    recent = _scheduler.command_text(
        [
            "sacct",
            "--duplicates",
            "-X",
            "-n",
            "-P",
            "-u",
            user,
            "-S",
            since,
            "--format=JobIDRaw,JobName,State,User,UID,StdOut,StdErr",
        ]
    )
    rich_accounting = bool(recent)
    if not recent:
        # Older site accounting may not expose stream fields. Preserve the
        # prior bounded ID discovery, but require scontrol to prove its paths.
        recent = _scheduler.command_text(
            [
                "sacct",
                "--duplicates",
                "-X",
                "-n",
                "-P",
                "-u",
                user,
                "-S",
                since,
                "--format=JobIDRaw,State",
            ]
        )
    recent_by_id = {}
    for line in recent.splitlines():
        fields = line.split("|")
        job_id = fields[0].strip() if fields else ""
        if not _scheduler.JOB_ID_RE.fullmatch(job_id):
            continue
        numeric_id = int(job_id)
        record = {"JobId": job_id}
        if rich_accounting and len(fields) >= 7:
            record.update(
                {
                    "JobName": fields[1].strip(),
                    "JobState": fields[2].strip(),
                    "User": fields[3].strip(),
                    "UID": fields[4].strip(),
                    "StdOut": fields[5].strip(),
                    "StdErr": fields[6].strip(),
                }
            )
        if numeric_id in recent_by_id:
            # Multiple root records for one ID are ambiguous across accounting
            # sources, even if their rendered fields happen to match.
            recent_by_id[numeric_id] = None
        else:
            recent_by_id[numeric_id] = record

    ordered = []
    for job_id in sorted(set(live_ids), reverse=True):
        ordered.append({"job_id": job_id, "accounting": None})
    for job_id in sorted(set(recent_by_id) - set(live_ids), reverse=True):
        record = recent_by_id[job_id]
        if record is not None:
            ordered.append({"job_id": job_id, "accounting": record})
    return ordered[:50]


def scheduler_candidate_ids():
    """Compatibility view of the bounded scheduler candidate roster."""
    return [candidate["job_id"] for candidate in scheduler_candidates()]


def scheduler_selection(
    job_id, log_dir=None, allow_accounting_fallback=False, accounting_metadata=None
):
    if log_dir and not os.path.isabs(log_dir):
        raise _scheduler.DiscoveryError("LOG_DIR must be an absolute path")
    metadata = _scheduler.slurm_job_metadata(job_id)
    if metadata is None:
        accounting = accounting_metadata
        if accounting is None and allow_accounting_fallback:
            accounting = _scheduler.slurm_accounting_metadata(job_id)
        if accounting is not None:
            accounting_out = accounting.get("StdOut")
            accounting_err = accounting.get("StdErr")
            if bool(accounting_out) != bool(accounting_err):
                raise _scheduler.DiscoveryError(
                    "Slurm accounting did not report a complete stdout/stderr pair "
                    "for job %s" % job_id
                )
            if accounting_out and accounting_err:
                return accounting_stream_selection(accounting, log_dir)
            if log_dir:
                return accounting_log_selection(job_id, log_dir, accounting)
            _scheduler.validate_accounting_identity(job_id, accounting)
            raise _scheduler.DiscoveryError(
                "Slurm accounting did not report stdout/stderr for job %s; "
                "pass LOG_DIR explicitly" % job_id
            )
        raise _scheduler.DiscoveryError(
            "Slurm metadata is unavailable for job %s" % job_id
        )
    _scheduler.validate_scheduler_identity(job_id, metadata, owner_field="UserId")
    state = _scheduler.normalized_job_state(metadata.get("JobState"))
    allow_missing = state in {"PENDING", "CONFIGURING"}
    scheduler_out = metadata.get("StdOut")
    scheduler_err = metadata.get("StdErr")
    if bool(scheduler_out) != bool(scheduler_err):
        raise _scheduler.DiscoveryError(
            "Slurm did not report a complete stdout/stderr pair for job %s" % job_id
        )
    if scheduler_out and scheduler_err:
        scheduler_out = _scheduler.expand_job_path(scheduler_out, job_id)
        scheduler_err = _scheduler.expand_job_path(scheduler_err, job_id)
        if log_dir:
            requested = os.path.abspath(log_dir)
            if requested != os.path.dirname(os.path.abspath(scheduler_out)):
                raise _scheduler.DiscoveryError(
                    "LOG_DIR disagrees with scheduler-declared stdout/stderr"
                )
        return validate_log_selection(
            job_id,
            scheduler_out,
            scheduler_err,
            allow_missing=allow_missing,
        )
    if not log_dir:
        raise _scheduler.DiscoveryError(
            "Slurm did not report stdout/stderr; pass JOB_ID and LOG_DIR explicitly"
        )
    return validate_log_selection(
        job_id,
        os.path.join(log_dir, "emrys-local-pilot-%s.out" % job_id),
        os.path.join(log_dir, "emrys-local-pilot-%s.err" % job_id),
        allow_missing=allow_missing,
    )


def resolve_selection(
    job_id=None, log_dir=None, out_path=None, err_path=None, offline=False
):
    """Resolve one dashboard target without scanning shared storage."""
    if job_id is not None and not _scheduler.JOB_ID_RE.fullmatch(str(job_id)):
        raise _scheduler.DiscoveryError("JOB_ID must be a positive root allocation ID")
    if bool(out_path) != bool(err_path):
        raise _scheduler.DiscoveryError("--out and --err must be supplied together")
    if out_path and err_path:
        if not offline:
            raise _scheduler.DiscoveryError("explicit --out/--err requires --offline")
        if job_id is None:
            raise _scheduler.DiscoveryError("--offline requires JOB_ID")
        return validate_log_selection(job_id, out_path, err_path)
    if offline:
        raise _scheduler.DiscoveryError("--offline requires explicit --out and --err")
    if job_id is not None:
        return scheduler_selection(
            int(job_id),
            log_dir,
            allow_accounting_fallback=True,
        )
    if log_dir:
        raise _scheduler.DiscoveryError("LOG_DIR without JOB_ID is ambiguous")
    failures = []
    for candidate in scheduler_candidates():
        job_id = candidate["job_id"]
        accounting = candidate.get("accounting")
        candidate_failures = []
        if accounting and accounting.get("StdOut") and accounting.get("StdErr"):
            try:
                return accounting_stream_selection(accounting)
            except _scheduler.DiscoveryError as exc:
                candidate_failures.append("accounting: %s" % exc)
        try:
            return scheduler_selection(job_id)
        except _scheduler.DiscoveryError as exc:
            candidate_failures.append("scontrol: %s" % exc)
        failures.append("%s: %s" % (job_id, "; ".join(candidate_failures)))
    detail = "; ".join(failures[:3])
    suffix = " (%s)" % detail if detail else ""
    raise _scheduler.DiscoveryError(
        "no recent current-user EMRYS wrapper job could be proven%s; "
        "pass JOB_ID and LOG_DIR" % suffix
    )


def parse_epoch(line):
    match = TIMESTAMP_RE.match(line)
    if not match:
        return None
    month, day, hour, minute, second, year = match.groups()
    value = dt.datetime(
        int(year), MONTHS[month], int(day), int(hour), int(minute), int(second)
    )
    return value.timestamp()


def extract_wildcard(value, name):
    match = re.search(r"(?:^|[, ]+)%s=([^, ]+)" % re.escape(name), value)
    return match.group(1) if match else None


def parse_identity(stdout_text):
    fields = {}
    patterns = {
        "run_id": r"^Run ID:\s*(.+)$",
        "run_root": r"^Run root:\s*(.+)$",
        "workspace": r"^Workspace:\s*(.+)$",
        "package_sha256": r"^Package SHA-256:\s*(.+)$",
        "attempt": r"^Workflow attempt:\s*(.+)$",
        "attempt_status": r"^(?:Attempt receipt status|Attempt status):\s*(.+)$",
        "runtime_hash": r"^Runtime profile SHA-256:\s*(.+)$",
        "workflow_cores": r"^Total workflow cores:\s*(\d{1,18})\s*$",
        "workflow_memory_mb": r"^Total workflow memory:\s*(\d{1,18})\s+MiB\s*$",
        # Retain compatibility with the completed pre-resource-policy run.
        "sample_concurrency": r"^Maximum concurrent sample tasks:\s*(\d{1,18})\s*$",
    }
    for key, pattern in patterns.items():
        matches = re.findall(pattern, stdout_text, flags=re.MULTILINE)
        if matches:
            fields[key] = matches[-1].strip()
    section_headers = {
        "Step thread allocations:": ("step_threads", "step"),
        "Stage concurrency:": ("stage_concurrency", "step"),
        "Stage memory per job:": ("stage_memory_mb", "step_memory"),
        "Reporting memory per transaction:": (
            "reporting_memory_mb",
            "reporting_memory",
        ),
    }
    parsed_sections = {name: {} for name, _ in section_headers.values()}
    current = None
    for line in stdout_text.splitlines():
        stripped = line.strip()
        if stripped in section_headers:
            current = section_headers[stripped]
            parsed_sections[current[0]] = {}
            continue
        if current is None:
            continue
        if not line.startswith((" ", "\t")):
            current = None
            continue
        section_name, section_kind = current
        if section_kind == "step":
            match = re.fullmatch(r"Step\s+([0-9]+[a-z]?):\s*(\d{1,18})", stripped)
        elif section_kind == "step_memory":
            match = re.fullmatch(r"Step\s+([0-9]+[a-z]?):\s*(\d{1,18})\s+MiB", stripped)
        else:
            match = re.fullmatch(r"([a-z][a-z0-9_]*):\s*(\d{1,18})\s+MiB", stripped)
        if match:
            parsed_sections[section_name][match.group(1)] = int(match.group(2))
    fields.update(parsed_sections)
    return fields


def counted(value, singular, plural=None):
    """Format a controller count with grammatically correct units."""
    unit = singular if int(value) == 1 else (plural or singular + "s")
    return "%s %s" % (value, unit)


def configuration_text(identity):
    concurrency = identity.get("stage_concurrency", {}).get("01")
    concurrency = concurrency or identity.get("sample_concurrency")
    threads = identity.get("step_threads", {}).get("01")
    workflow_cores = identity.get("workflow_cores")
    if concurrency and threads:
        value = "Step 01: %s x %s" % (
            counted(concurrency, "sample process", "sample processes"),
            counted(threads, "configured thread"),
        )
        if workflow_cores:
            value += " | %s" % counted(workflow_cores, "workflow core")
        return value
    if workflow_cores:
        return "%s; per-stage policy not yet reported" % counted(
            workflow_cores, "workflow core"
        )
    return "not yet reported by the EMRYS control plan"


def stage_resource_text(stage, identity, fallback):
    """Render the observed controller resource plan without inventing values."""
    stage_concurrency = identity.get("stage_concurrency", {})
    concurrency = stage_concurrency.get(stage)
    if concurrency is None and stage in SAMPLE_STAGES:
        concurrency = identity.get("sample_concurrency")
    threads = identity.get("step_threads", {})
    stage_threads = threads.get(stage)
    stage_memory = identity.get("stage_memory_mb", {}).get(stage)
    workflow_cores = identity.get("workflow_cores")

    def with_memory(value):
        if stage_memory is not None:
            return "%s. Per-job memory: %s MiB." % (value.rstrip("."), stage_memory)
        return value

    if stage == "00a" and stage_threads:
        return with_memory(
            "1 process x %s; sample concurrency does not apply."
            % counted(stage_threads, "STAR thread")
        )
    if stage == "01" and concurrency and stage_threads:
        nominal = int(concurrency) * int(stage_threads)
        return with_memory(
            "Up to %s x %s (%s)."
            % (
                counted(concurrency, "sample process", "sample processes"),
                counted(stage_threads, "STAR thread"),
                counted(nominal, "nominal thread"),
            )
        )
    if stage in {"02", "06"} and concurrency and stage_threads:
        return with_memory(
            "Up to %s x %s."
            % (
                counted(concurrency, "sample process", "sample processes"),
                counted(stage_threads, "configured thread"),
            )
        )
    if stage in {"02b", "03", "04", "05"} and concurrency:
        process, processes, detail = {
            "02b": ("sample process", "sample processes", ""),
            "03": ("sample process", "sample processes", ""),
            "04": (
                "sample Java/Picard process",
                "sample Java/Picard processes",
                "",
            ),
            "05": (
                "GATK process",
                "GATK processes",
                "; JVM/native threads may exceed the configured workflow threads",
            ),
        }[stage]
        return with_memory(
            "Up to %s%s." % (counted(concurrency, process, processes), detail)
        )
    if stage == "07" and concurrency:
        value = "Up to %s" % counted(
            concurrency, "partition process", "partition processes"
        )
        if workflow_cores:
            value += " within the %s-core workflow envelope" % workflow_cores
        return with_memory(value + ".")
    if stage == "08" and stage_threads:
        return with_memory(
            "1 cohort process using %s where supported."
            % counted(stage_threads, "configured thread")
        )
    if stage in {"00b", "00c", "09", "10"} and stage_memory is not None:
        return with_memory(fallback)
    if stage == "REPORT":
        reporting_memory = identity.get("reporting_memory_mb", {})
        if reporting_memory:
            rendered = ", ".join(
                "%s=%s MiB" % item for item in sorted(reporting_memory.items())
            )
            return "Three dependent reporting transactions: %s." % rendered
    if stage in {
        "00a",
        "00b",
        "00c",
        "01",
        "02",
        "02b",
        "03",
        "04",
        "05",
        "06",
        "07",
        "08",
        "09",
        "10",
        "REPORT",
    }:
        return "Resource plan not yet reported by the EMRYS control stream."
    return fallback


def parse_workflow(stderr_text, *, expected=None, rule_stages=None):
    """Project observed jobs; missing counts/mappings remain unknown.

    Job stats describe this Snakemake invocation, not every Task in a Run.
    Explicit expected counts are fallback context for stages absent from stats.
    """
    stage_rules = {**RULE_TO_STAGE, **(rule_stages or {})}
    expected = dict(expected or {})

    def stage_for(rule, wildcards=""):
        if rule == "analysis_owner":
            rule = extract_wildcard(wildcards, "analysis_owner")
        key = stage_rules.get(rule)
        return key if key in STAGE_BY_KEY else "?"

    counts = {}
    stats = None
    stats_header = False
    completed_jobs = set()
    done = {key: 0 for key in STAGE_BY_KEY}
    started = {}
    finished = {}
    active = {}
    recent = []
    completion_times = []
    samples = {}
    sample_order = []
    current_rule = None
    current_job = None
    log_epoch = None
    progress_done = 0
    progress_total = None
    last_completion = None
    warning = None

    for raw in stderr_text.splitlines():
        line = raw.rstrip("\r")
        if line.strip() == "Job stats:":
            stats, stats_header, counts, progress_total = {}, False, {}, None
            continue
        if stats is not None:
            stripped = line.strip()
            if re.fullmatch(r"job\s+count", stripped):
                stats_header = True
                continue
            if stats_header and re.fullmatch(r"[-\s]+", stripped):
                continue
            row = re.fullmatch(r"(\S+)\s+(\d{1,18})", stripped)
            if stats_header and row:
                rule, count = row[1], int(row[2])
                if rule == "total":
                    if count == sum(stats.values()):
                        progress_total = count
                        for name, value in stats.items():
                            key = stage_for(name)
                            if key != "?":
                                counts[key] = counts.get(key, 0) + value
                    stats = None
                elif rule in stats:
                    stats = None
                else:
                    stats[rule] = count
                continue
            stats = None
        try:
            parsed_epoch = parse_epoch(line)
        except (KeyError, ValueError, OverflowError, OSError):
            log_epoch = None
            continue
        if parsed_epoch is not None:
            log_epoch = parsed_epoch
            continue

        rule_match = re.match(r"^(?:localrule|rule)\s+([^:]+):", line)
        if rule_match:
            current_rule = rule_match.group(1)
            current_job = None
            continue

        job_match = re.match(r"^\s*jobid:\s*(\d+)", line)
        if job_match and current_rule:
            job_id = job_match.group(1)
            key = stage_for(current_rule)
            active[job_id] = {
                "rule": current_rule,
                "stage": key,
                "wildcards": "",
                "started": log_epoch,
            }
            if key != "?" and log_epoch is not None:
                started[key] = min(started.get(key, log_epoch), log_epoch)
            current_job = job_id
            current_rule = None
            continue

        wildcard_match = re.match(r"^\s*wildcards:\s*(.*)$", line)
        if wildcard_match and current_job in active:
            wildcards = wildcard_match.group(1).strip()
            info = active[current_job]
            info["wildcards"] = wildcards
            info["stage"] = stage_for(info["rule"], wildcards)
            if info["stage"] != "?" and info["started"] is not None:
                key = info["stage"]
                started[key] = min(started.get(key, info["started"]), info["started"])
            sample = extract_wildcard(wildcards, "sample_id")
            if sample and sample not in samples:
                samples[sample] = {
                    "last_stage": None,
                    "last_finished": None,
                    "history": {},
                }
                sample_order.append(sample)
            current_job = None
            continue

        finish_match = re.match(
            r"^\s*Finished jobid:\s*(\d+)\s*\(Rule:\s*([^\)]+)\)", line
        )
        if finish_match:
            job_id, rule = finish_match.groups()
            if job_id in completed_jobs:
                continue
            completed_jobs.add(job_id)
            info = active.pop(job_id, None)
            key = info["stage"] if info else stage_for(rule)
            done[key] = done.get(key, 0) + 1
            if key != "?":
                if log_epoch is not None:
                    finished[key] = max(finished.get(key, log_epoch), log_epoch)
                    last_completion = max(last_completion or log_epoch, log_epoch)
                    completion_times.append(log_epoch)
                recent.append((job_id, key, rule, log_epoch))
            if info:
                sample = extract_wildcard(info.get("wildcards", ""), "sample_id")
                if sample:
                    if sample not in samples:
                        samples[sample] = {
                            "last_stage": None,
                            "last_finished": None,
                            "history": {},
                        }
                        sample_order.append(sample)
                    samples[sample]["last_stage"] = key
                    samples[sample]["last_finished"] = log_epoch
                    if info.get("started") is not None and log_epoch is not None:
                        samples[sample]["history"][key] = max(
                            0, log_epoch - info["started"]
                        )
            continue

        progress_match = re.match(
            r"^\s*(\d{1,18}) of (\d{1,18}) steps \(\d{1,3}%\) done", line
        )
        if progress_match:
            complete, total = map(int, progress_match.groups())
            if complete <= total:
                progress_done, progress_total = complete, total
            continue

        if re.search(
            r"Error in rule|WorkflowError|Traceback|Exiting because a job execution failed",
            line,
        ):
            warning = line.strip()

    for info in active.values():
        sample = extract_wildcard(info.get("wildcards", ""), "sample_id")
        if sample and sample not in samples:
            samples[sample] = {
                "last_stage": None,
                "last_finished": None,
                "history": {},
            }
            sample_order.append(sample)

    return {
        "done": done,
        "expected": {**expected, **counts},
        "started": started,
        "finished": finished,
        "active": active,
        "recent": recent[-8:],
        "samples": samples,
        "completion_times": completion_times,
        "sample_order": sample_order,
        "progress_done": progress_done,
        "progress_total": progress_total,
        "last_completion": last_completion,
        "warning": warning,
    }


def human_size(value):
    if not value:
        return "-"
    clean = value.strip().replace("+", "")
    match = re.match(r"^([0-9.]+)([KMGT]?)$", clean)
    if not match:
        return value
    try:
        number = float(match.group(1))
    except ValueError:
        return value
    suffix = match.group(2)
    if suffix:
        number *= 1024 ** ("KMGT".index(suffix) + 1)
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    unit = 0
    while number >= 1024 and unit < len(units) - 1:
        number /= 1024
        unit += 1
    return "%.1f %s" % (number, units[unit])


def duration(seconds):
    if seconds is None or seconds < 0:
        return "-"
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days:
        return "%dd%02dh%02dm" % (days, hours, minutes)
    if hours:
        return "%dh%02dm%02ds" % (hours, minutes, seconds)
    if minutes:
        return "%dm%02ds" % (minutes, seconds)
    return "%ds" % seconds


def active_sample_info(model, sample):
    active_items = []
    for job_id, info in model["active"].items():
        if extract_wildcard(info.get("wildcards", ""), "sample_id") == sample:
            active_items.append((job_id, info))
    if not active_items:
        return None, None
    return sorted(active_items, key=lambda item: item[1].get("started") or 0)[-1]


def latest_sample_state(model, sample, now):
    _, info = active_sample_info(model, sample)
    if info:
        elapsed = duration(now - info["started"]) if info.get("started") else "-"
        return info["stage"], "RUNNING", elapsed
    sample_state = model["samples"].get(sample, {})
    history = sample_state.get("history", {})
    last = sample_state.get("last_stage")
    if "06" in history:
        return "06", "READY FOR COHORT", "-"
    if last:
        return last, "WAITING", "-"
    return "-", "PENDING", "-"


def sample_sort_key(sample):
    """Group paired libraries by trailing replicate while remaining deterministic."""
    match = re.search(r"(\d+)$", sample)
    replicate = int(match.group(1)) if match else sys.maxsize
    return replicate, sample


def peer_runtime_comparison(model, sample, now):
    _, info = active_sample_info(model, sample)
    if not info or info.get("stage") not in SAMPLE_STAGES:
        return "NOT RUNNING", "dim"
    started = info.get("started")
    if started is None or now < started:
        return "CLOCK UNAVAILABLE", "dim"
    key = info["stage"]
    peers = [
        state.get("history", {}).get(key)
        for peer, state in model["samples"].items()
        if peer != sample and state.get("history", {}).get(key) is not None
    ]
    if len(peers) < 2:
        return "WAITING FOR PEERS (%d/2 complete)" % len(peers), "dim"
    median = statistics.median(peers)
    elapsed = now - started
    ratio = elapsed / median if median > 0 else 0
    if ratio <= 1.25:
        label, style = "ON TRACK", "green"
    elif ratio <= 1.75:
        label, style = "LONGER THAN PEERS", "yellow"
    else:
        label, style = "CHECK PROGRESS", "yellow"
    return "%s (%.1fx median %s; n=%d)" % (
        label,
        ratio,
        duration(median),
        len(peers),
    ), style


def replicate_groups(model):
    groups = {}
    for sample in sorted(model["sample_order"], key=sample_sort_key):
        match = re.search(r"(\d+)$", sample)
        if match:
            groups.setdefault(match.group(1), []).append(sample)
    return [
        (replicate, samples)
        for replicate, samples in sorted(groups.items(), key=lambda item: int(item[0]))
        if len(samples) >= 2
    ]


def completion_velocity(model, now):
    times = model.get("completion_times", [])
    return tuple(
        sum(1 for value in times if 0 <= now - value <= window)
        for window in (15 * 60, 60 * 60)
    )


def init_colors():
    if os.environ.get("NO_COLOR"):
        return {
            name: 0
            for name in (
                "normal",
                "title",
                "green",
                "green_bold",
                "cyan",
                "cyan_bold",
                "yellow",
                "yellow_bold",
                "red",
                "dim",
                "border",
                "panel_title",
                "label",
                "value",
            )
        }
    curses.start_color()
    curses.use_default_colors()
    pairs = {
        "green": curses.COLOR_GREEN,
        "cyan": curses.COLOR_CYAN,
        "yellow": curses.COLOR_YELLOW,
        "red": curses.COLOR_RED,
        "magenta": curses.COLOR_MAGENTA,
    }
    attrs = {"normal": 0, "dim": curses.A_DIM}
    index = 1
    for name, color in pairs.items():
        curses.init_pair(index, color, -1)
        attrs[name] = curses.color_pair(index)
        index += 1
    attrs["title"] = attrs["cyan"] | curses.A_BOLD
    attrs["green_bold"] = attrs["green"] | curses.A_BOLD
    attrs["cyan_bold"] = attrs["cyan"] | curses.A_BOLD
    attrs["yellow_bold"] = attrs["yellow"] | curses.A_BOLD
    attrs["border"] = attrs["cyan"] | curses.A_DIM
    attrs["panel_title"] = attrs["magenta"] | curses.A_BOLD
    attrs["label"] = attrs["cyan"] | curses.A_BOLD
    attrs["value"] = curses.A_BOLD
    return attrs


def safe_add(screen, y, x, text, attr=0, limit=None):
    height, width = screen.getmaxyx()
    if y < 0 or y >= height or x < 0 or x >= width:
        return
    available = width - x - 1
    if limit is not None:
        available = min(available, limit)
    if available <= 0:
        return
    try:
        screen.addnstr(y, x, text, available, attr)
    except curses.error:
        pass


def draw_box(
    screen, y, x, height, width, title, lines, attrs, scroll=0, scrollable=False
):
    max_y, max_x = screen.getmaxyx()
    height = min(height, max_y - y)
    width = min(width, max_x - x)
    if height < 3 or width < 12:
        return
    border = attrs["border"]
    safe_add(screen, y, x, "+" + "-" * (width - 2) + "+", border, width)
    safe_add(screen, y + height - 1, x, "+" + "-" * (width - 2) + "+", border, width)
    for row in range(y + 1, y + height - 1):
        safe_add(screen, row, x, "|", border)
        safe_add(screen, row, x + width - 1, "|", border)
    safe_add(
        screen,
        y,
        x + 2,
        " %s " % title,
        attrs["panel_title"],
        width - 4,
    )
    content_height = height - 2
    overflow = len(lines) > content_height
    visible_height = content_height - 1 if overflow else content_height
    visible_height = max(1, visible_height)
    max_scroll = max(0, len(lines) - visible_height)
    start = min(max(0, scroll), max_scroll) if scrollable else 0
    visible_lines = lines[start : start + visible_height]
    for offset, item in enumerate(visible_lines):
        if isinstance(item, list):
            used = 0
            available = width - 4
            for segment in item:
                if isinstance(segment, tuple):
                    text, style = segment
                    attr = attrs.get(style, 0)
                else:
                    text, attr = segment, 0
                text = str(text)
                remaining = available - used
                if remaining <= 0:
                    break
                safe_add(
                    screen,
                    y + 1 + offset,
                    x + 2 + used,
                    text,
                    attr,
                    remaining,
                )
                used += min(len(text), remaining)
        elif isinstance(item, tuple):
            text, style = item
            attr = attrs.get(style, 0)
            safe_add(screen, y + 1 + offset, x + 2, text, attr, width - 4)
        else:
            text, attr = item, 0
            safe_add(screen, y + 1 + offset, x + 2, text, attr, width - 4)
    if overflow:
        if scrollable:
            end = min(len(lines), start + visible_height)
            arrows = ("^" if start else "-") + "/" + ("v" if end < len(lines) else "-")
            message = "[%s Up/Down] Current Work lines %d-%d of %d" % (
                arrows,
                start + 1,
                end,
                len(lines),
            )
        else:
            hidden = len(lines) - visible_height
            message = "... %d more lines; resize or use the other view" % hidden
        safe_add(
            screen,
            y + height - 2,
            x + 2,
            message,
            attrs["yellow"],
            width - 4,
        )
    return max_scroll


def wrapped(text, width, prefix=""):
    available = max(12, width - len(prefix))
    chunks = textwrap.wrap(text, available) or [""]
    return [prefix + chunks[0]] + [(" " * len(prefix)) + chunk for chunk in chunks[1:]]


def field_line(label, value, value_style="normal", indent=""):
    """Return a scan-friendly label/value line for draw_box."""
    return [
        (indent + label + ": ", "label"),
        (str(value), value_style),
    ]


def wrapped_field(label, value, width, value_style="normal", indent=""):
    """Wrap a field while keeping its label visually distinct from its value."""
    prefix = indent + label + ": "
    available = max(12, width - len(prefix))
    chunks = textwrap.wrap(str(value), available) or [""]
    lines = [[(prefix, "label"), (chunks[0], value_style)]]
    lines.extend(
        [[(" " * len(prefix), "normal"), (chunk, value_style)] for chunk in chunks[1:]]
    )
    return lines


def job_lines(slurm, identity, width, attrs):
    state = slurm.get("state", "UNKNOWN")
    state_style = (
        "yellow_bold"
        if state == "RUNNING"
        else "green_bold"
        if state == "COMPLETED"
        else "yellow"
    )
    if state in _scheduler.TERMINAL_STATES - {"COMPLETED"}:
        state_style = "red"
    lines = [
        [
            ("State: ", "label"),
            (state, state_style),
            (" | elapsed: ", "label"),
            (slurm.get("elapsed", "-"), "value"),
            (" | Slurm time left: ", "label"),
            (slurm.get("left", "-"), "value"),
        ],
        field_line(
            "Slurm placement",
            "%s CPUs | partition %s | node %s"
            % (
                slurm.get("cpus", "-"),
                slurm.get("partition", "-"),
                slurm.get("node", "-"),
            ),
            "value",
        ),
        field_line(
            "Batch per-task maxima",
            slurm.get("usage_diagnostic")
            or "RSS %s | read %s | written %s"
            % (
                human_size(slurm.get("max_rss")),
                human_size(slurm.get("disk_read")),
                human_size(slurm.get("disk_write")),
            ),
            "value",
        ),
        field_line(
            "Batch CPU / sample",
            "average task CPU time %s; as of %s"
            % (
                slurm.get("ave_cpu", "unknown"),
                slurm.get("usage_observed_at", "unknown"),
            ),
            "value",
        ),
        field_line(
            "Run", identity.get("run_id", "waiting for control stream"), "value"
        ),
        field_line(
            "Code / attempt",
            "%s | %s"
            % (identity.get("package_sha256", "-"), identity.get("attempt", "-")),
            "value",
        ),
        field_line(
            "Run root",
            identity.get("run_root", identity.get("workspace", "-")),
            "value",
        ),
    ]
    return lines


def progress_values(model):
    total = model["progress_total"]
    complete = max(model["progress_done"], sum(model["done"].values()))
    if total is not None and complete > total:
        total = None
    return complete, total, None if total is None else total - complete


def progress_line(model, width):
    complete, total, remaining = progress_values(model)
    if total is None:
        return (
            "%d Snakemake jobs observed complete | total and remaining unknown"
            % complete
        )
    bar_width = max(10, min(28, width - 48))
    filled = int((complete / total) * bar_width + 0.5) if total else 0
    bar = "[" + "#" * filled + "-" * (bar_width - filled) + "]"
    return "%s %d/%d Snakemake jobs | %d jobs remaining" % (
        bar,
        complete,
        total,
        remaining,
    )


def pipeline_lines(model, now, width, include_summary=True):
    lines = []
    if include_summary:
        lines.extend([(progress_line(model, width), "cyan"), ""])
    lines.append("STEP    STAGE                       DONE     ELAPSED      STATE")
    active_counts = {}
    for info in model["active"].values():
        active_counts[info["stage"]] = active_counts.get(info["stage"], 0) + 1
    for key, title, _, _, _, _ in STAGES:
        expected = model.get("expected", {}).get(key)
        done = model["done"].get(key, 0)
        running = active_counts.get(key, 0)
        if expected == 0 and not done and not running:
            state, style = "NOT SCHEDULED", "dim"
        elif expected is not None and done == expected and not running:
            state, style = "DONE", "green"
        elif running:
            state, style = "RUNNING (%d)" % running, "yellow_bold"
        elif done:
            state, style = "WAITING", "yellow"
        else:
            state, style = "PENDING", "dim"
        start = model["started"].get(key)
        if start is None:
            elapsed = "-"
        else:
            stop = model["finished"].get(key) if state == "DONE" else now
            elapsed = duration((stop or now) - start)
        lines.append(
            (
                "%-7s %-27s %2d/%-4s  %-12s %s"
                % (
                    key,
                    title,
                    done,
                    "?" if expected is None else expected,
                    elapsed,
                    state,
                ),
                style,
            )
        )
    return lines


def workflow_phase(model):
    groups = [
        (1, "REFERENCE PREPARATION", ("00a", "00b", "00c")),
        (2, "SAMPLE PROCESSING", ("01", "02", "02b", "03", "04", "05", "06")),
        (3, "COHORT ANALYSIS", ("07", "08", "09", "10")),
        (4, "REPORTING & FINALIZATION", ("REPORT", "FINAL")),
    ]
    expected = model.get("expected", {})
    active = {info.get("stage") for info in model["active"].values()}
    for number, title, keys in groups:
        if active.intersection(keys):
            return number, title + " (observed)"
    for number, title, keys in groups:
        if any(
            expected.get(key) is not None and model["done"].get(key, 0) < expected[key]
            for key in keys
        ):
            return number, title
    if all(
        expected.get(key) is not None and model["done"].get(key, 0) == expected[key]
        for key in STAGE_BY_KEY
    ) and any(expected.values()):
        return 4, "COMPLETE"
    return 1, "PHASE UNKNOWN"


def current_lines(model, identity, now, width, include_active=True):
    grouped = {}
    for info in model["active"].values():
        if info["stage"] == "FINAL":
            continue
        grouped.setdefault(info["stage"], []).append(info)
    lines = []
    if not grouped:
        return [
            "No scientific owner is visible: preflight, dependency transition, or finalization."
        ]
    for key in [row[0] for row in STAGES] + ["?"]:
        infos = grouped.get(key)
        if not infos:
            continue
        row = STAGE_BY_KEY.get(
            key,
            (
                key,
                "Unmapped rule",
                None,
                None,
                "No stage mapping is available for these observed jobs.",
                "Resource plan unknown.",
            ),
        )
        _, title, _, _, purpose, resources = row
        expected = model.get("expected", {}).get(key)
        done = model["done"].get(key, 0)
        waiting = (
            "unknown" if expected is None else max(0, expected - done - len(infos))
        )
        started = model["started"].get(key)
        lines.append(("Step %s - %s" % (key, title), "yellow_bold"))
        lines.extend(wrapped_field("Work", purpose, width - 4, indent="  "))
        lines.append(
            field_line(
                "Progress",
                "%d/%s complete | %d running | %s waiting"
                % (done, "?" if expected is None else expected, len(infos), waiting),
                "value",
                indent="  ",
            )
        )
        lines.append(
            field_line(
                "Time in stage",
                duration(now - started) if started else "-",
                "value",
                indent="  ",
            )
        )
        lines.extend(
            wrapped_field(
                "Resources",
                stage_resource_text(key, identity, resources),
                width - 4,
                indent="  ",
            )
        )
        units = [info.get("wildcards", "") for info in infos if info.get("wildcards")]
        if include_active and units:
            lines.extend(
                wrapped_field(
                    "Active",
                    ", ".join(units),
                    width - 4,
                    indent="  ",
                )
            )
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def sample_lines(model, now, width):
    sample_width = 20
    pipeline_width = 13
    status_width = 10
    elapsed_width = 9
    job_width = 7
    fixed = sample_width + pipeline_width + status_width + elapsed_width + job_width + 6
    stage_width = max(18, width - fixed)
    row_format = "%%-%ds %%-%ds %%-%ds %%-%ds %%%ds %%-%ds" % (
        sample_width,
        pipeline_width,
        stage_width,
        status_width,
        elapsed_width,
        job_width,
    )
    lines = [
        row_format
        % (
            "SAMPLE",
            "PIPELINE",
            "CURRENT STAGE",
            "STATUS",
            "ELAPSED",
            "JOB",
        )
    ]
    for sample in sorted(model["sample_order"], key=sample_sort_key):
        key, status, elapsed = latest_sample_state(model, sample, now)
        style = (
            "yellow_bold"
            if status == "RUNNING"
            else "green"
            if status == "READY FOR COHORT"
            else "yellow"
            if status == "WAITING"
            else "dim"
        )
        title = STAGE_BY_KEY.get(key, (None, "", None))[1]
        sample_state = model["samples"].get(sample, {})
        history = sample_state.get("history", {})
        complete = sum(1 for stage in SAMPLE_STAGE_KEYS if stage in history)
        active_job, _ = active_sample_info(model, sample)
        markers = "".join(
            "x"
            if stage in history
            else ">"
            if stage == key and status == "RUNNING"
            else "."
            for stage in SAMPLE_STAGE_KEYS
        )
        pipeline = "[%s] %d/7" % (markers, complete)
        lines.append(
            (
                row_format
                % (
                    sample,
                    pipeline,
                    "%s %s" % (key, title),
                    status,
                    elapsed,
                    active_job or "-",
                ),
                style,
            )
        )
        last = sample_state.get("last_stage")
        if last:
            last_duration = duration(history.get(last))
            last_text = "  Last: Step %s in %s" % (last, last_duration)
        else:
            last_text = "  Last: none"
        if status == "RUNNING":
            peer_text, peer_style = peer_runtime_comparison(model, sample, now)
            lines.append(
                [
                    (last_text, "dim"),
                    (" | Peer: ", "dim"),
                    (peer_text, peer_style),
                ]
            )
        else:
            lines.append((last_text, "dim"))

    pairs = replicate_groups(model)
    if pairs:
        lines.extend(["", ("PAIRED REPLICATE READINESS", "title")])
        for replicate, samples in pairs:
            members = []
            for sample in samples:
                key, status, _ = latest_sample_state(model, sample, now)
                members.append("%s=%s %s" % (sample, key, status))
            ready = all(
                "06" in model["samples"].get(sample, {}).get("history", {})
                for sample in samples
            )
            label, style = (
                ("READY", "green_bold") if ready else ("PROCESSING", "yellow_bold")
            )
            lines.append(
                [
                    (
                        "replicate_%s: %s | " % (replicate, " | ".join(members)),
                        "normal",
                    ),
                    (label, style),
                ]
            )
    if len(lines) == 1:
        lines.append("Waiting for sample jobs to appear in the scheduler log.")
    return lines


def sample_lane_window(model, width):
    """Keep one cleared stage behind the earliest uncleared sample stage."""
    keys = SAMPLE_STAGE_KEYS
    # Each stage occupies six characters plus one inter-column space. With the
    # elapsed column removed, wide panels retain all stages; narrow panels use
    # the rolling context window below.
    capacity = max(2, min(len(keys), (width - 22) // 7))
    samples = model["sample_order"]

    def cleared_for_every_sample(key):
        return bool(samples) and all(
            key in model["samples"].get(sample, {}).get("history", {})
            for sample in samples
        )

    earliest_uncleared = next(
        (index for index, key in enumerate(keys) if not cleared_for_every_sample(key)),
        len(keys),
    )
    start = max(0, earliest_uncleared - 1)
    start = min(start, max(0, len(keys) - capacity))
    return keys[start : start + capacity], keys[:start]


def sample_lane_lines(model, now, width):
    keys, hidden = sample_lane_window(model, width)
    cell_width = 6
    lane_header = " ".join("%-*s" % (cell_width, key) for key in keys)
    lines = [
        "Legend: [x] complete  [>] running  [.] pending",
    ]
    if hidden:
        lines.append(
            (
                "Earlier stages cleared by every sample: %s" % ", ".join(hidden),
                "dim",
            )
        )
    lines.extend(["", "%-22s %s" % ("SAMPLE", lane_header)])
    for sample in sorted(model["sample_order"], key=sample_sort_key):
        active_key, status, _ = latest_sample_state(model, sample, now)
        history = model["samples"].get(sample, {}).get("history", {})
        segments = [("%-22s " % sample, "normal")]
        for index, key in enumerate(keys):
            if status == "RUNNING" and active_key == key:
                marker, marker_style = ">", "yellow_bold"
            elif key in history:
                marker, marker_style = "x", "green_bold"
            else:
                marker, marker_style = ".", "dim"
            opening = "%s[" % key
            closing = "]" + " " * (cell_width - len(opening) - 2)
            segments.extend(
                [
                    (opening, "normal"),
                    (marker, marker_style),
                    (closing, "normal"),
                ]
            )
            if index < len(keys) - 1:
                segments.append((" ", "normal"))
        lines.append(segments)
    if not model["sample_order"]:
        lines.append("Waiting for sample jobs to appear in the scheduler log.")

    if model["sample_order"]:
        ready = sum(
            1
            for sample in model["sample_order"]
            if "06" in model["samples"].get(sample, {}).get("history", {})
        )
        total = model.get("expected", {}).get("06")
        readiness_style = (
            "green_bold" if total is not None and ready == total else "yellow_bold"
        )
        lines.extend(
            [
                "",
                ("COHORT HANDOFF", "panel_title"),
                [
                    ("Samples through Step 06: ", "label"),
                    (
                        "%d/%s" % (ready, "?" if total is None else total),
                        readiness_style,
                    ),
                    (" - aggregate analysis unlocks when all are ready", "dim"),
                ],
            ]
        )
        aggregate_keys = ("07", "08", "09", "10", "REPORT")
        active_counts = {}
        for info in model["active"].values():
            key = info.get("stage")
            active_counts[key] = active_counts.get(key, 0) + 1
        aggregate_segments = [("Aggregate lane: ", "label")]
        for index, key in enumerate(aggregate_keys):
            expected = model.get("expected", {}).get(key)
            if expected and model["done"].get(key, 0) == expected:
                marker, style = "x", "green_bold"
            elif active_counts.get(key, 0):
                marker, style = ">", "yellow_bold"
            else:
                marker, style = ".", "dim"
            label = "RPT" if key == "REPORT" else key
            aggregate_segments.extend(
                [
                    (label + "[", "normal"),
                    (marker, style),
                    ("]", "normal"),
                ]
            )
            if index < len(aggregate_keys) - 1:
                aggregate_segments.append(("  ", "normal"))
        lines.append(aggregate_segments)
    return lines


def compact_activity_lines(model, now, width):
    lines = []
    if model["last_completion"]:
        lines.extend(
            wrapped_field(
                "Latest owner completion",
                "%s ago" % duration(now - model["last_completion"]),
                width,
                "value",
            )
        )
    else:
        lines.append("No owner completion has appeared yet.")
    recent_15, recent_60 = completion_velocity(model, now)
    lines.extend(
        wrapped_field(
            "Owner completions (rolling)",
            "%d in the last 15m | %d in the last 60m" % (recent_15, recent_60),
            width,
            "value",
        )
    )
    lines.extend(
        (line, "dim")
        for line in wrapped(
            "Counts completed Snakemake owner jobs; this is throughput, not an ETA.",
            width,
        )
    )
    for job_id, key, rule, _ in model["recent"][-3:]:
        lines.extend(
            (line, "green")
            for line in wrapped(
                "DONE job %s | Step %s | %s" % (job_id, key, rule),
                width,
            )
        )
    if model["warning"]:
        lines.extend(
            (line, "red")
            for line in wrapped(
                "Latest error-like line: %s" % model["warning"],
                width,
            )
        )
    return lines


def short_identity(value, length=16):
    if not value:
        return "-"
    if len(value) <= length:
        return value
    return value[:length] + "..."


def overview_lines(slurm, identity, model, width):
    state = slurm.get("state", "UNKNOWN")
    state_style = (
        "yellow_bold"
        if state == "RUNNING"
        else "green_bold"
        if state == "COMPLETED"
        else "yellow"
    )
    if state in _scheduler.TERMINAL_STATES - {"COMPLETED"}:
        state_style = "red"
    phase_number, phase_title = workflow_phase(model)
    return [
        [
            ("State: ", "label"),
            (state, state_style),
            (" | elapsed: ", "label"),
            (slurm.get("elapsed", "-"), "value"),
            (" | Slurm time left: ", "label"),
            (slurm.get("left", "-"), "value"),
        ],
        (progress_line(model, width), "cyan"),
        field_line(
            "Workflow phase", "%d/4 - %s" % (phase_number, phase_title), "value"
        ),
        field_line(
            "Slurm placement / batch",
            "%s | %s CPUs | %s | %s"
            % (
                "usage unknown"
                if slurm.get("usage_diagnostic") or not slurm.get("max_rss")
                else "per-task max RSS " + human_size(slurm["max_rss"]),
                slurm.get("cpus", "-"),
                slurm.get("partition", "-"),
                slurm.get("node", "-"),
            ),
            "value",
        ),
    ]


def workflow_frontier_lines(model, now, width):
    phase_number, _ = workflow_phase(model)
    active_counts = {}
    for info in model["active"].values():
        key = info.get("stage")
        if key and key != "FINAL":
            active_counts[key] = active_counts.get(key, 0) + 1
    ordered_active = [row[0] for row in STAGES if row[0] in active_counts]
    lines = [("WORKFLOW FRONTIER", "panel_title")]
    lines.extend(
        (line, "dim")
        for line in wrapped(
            "Frontier = earliest active dependency edge. Later work may run, but the "
            "workflow cannot fully advance until this edge clears.",
            width,
        )
    )
    unmapped = [
        info["rule"]
        for info in model["active"].values()
        if info.get("stage") not in STAGE_BY_KEY
    ]
    if unmapped:
        lines.extend(wrapped_field("Unmapped active rules", ", ".join(unmapped), width))
    if not ordered_active:
        if not unmapped:
            lines.extend(
                wrapped(
                    "No scientific owner visible: preflight or dependency transition.",
                    width,
                )
            )
        return lines

    lines.extend(
        wrapped_field(
            "Active owners",
            " | ".join(
                "Step %s x%d" % (key, active_counts[key]) for key in ordered_active
            ),
            width,
            "value",
        )
    )
    frontier = ordered_active[0]
    frontier_title = STAGE_BY_KEY[frontier][1]
    lines.extend(
        wrapped_field(
            "Dependency edge",
            "Step %s - %s (earliest active stage)" % (frontier, frontier_title),
            width,
            "yellow_bold",
        )
    )

    if frontier in SAMPLE_STAGES:
        durations = [
            state.get("history", {}).get(frontier)
            for state in model["samples"].values()
            if state.get("history", {}).get(frontier) is not None
        ]
        if len(durations) >= 2:
            lines.extend(
                wrapped_field(
                    "Completed-peer baseline",
                    "median %s across %d samples"
                    % (duration(statistics.median(durations)), len(durations)),
                    width,
                    "value",
                )
            )
        ready = sum(
            1 for state in model["samples"].values() if "06" in state.get("history", {})
        )
        total = model.get("expected", {}).get("06")
        lines.extend(
            wrapped_field(
                "Cohort readiness",
                "%d/%s samples completed Step 06"
                % (ready, "?" if total is None else total),
                width,
                "value",
            )
        )
        lines.extend(
            wrapped_field(
                "Next unlock",
                "Step 07 begins after every sample clears Step 06.",
                width,
                "value",
            )
        )
    elif phase_number == 1:
        lines.extend(
            wrapped_field(
                "Next unlock",
                "Sample processing begins after reference preparation.",
                width,
                "value",
            )
        )
    elif phase_number == 3:
        lines.extend(
            wrapped_field(
                "Next unlock",
                "Reporting begins after Step 10 completes.",
                width,
                "value",
            )
        )
    else:
        lines.extend(
            wrapped_field(
                "Next unlock",
                "Final aggregate target and completion evidence.",
                width,
                "value",
            )
        )
    return lines


def provenance_activity_lines(slurm, identity, model, now, width):
    if slurm.get("terminal"):
        title, lines = activity_lines(model, slurm, identity, now)
        return title, lines
    lines = []
    lines.extend(
        wrapped_field(
            "Run", identity.get("run_id", "waiting for control stream"), width, "value"
        )
    )
    lines.extend(
        wrapped_field(
            "Code / runtime",
            "%s | %s"
            % (
                short_identity(identity.get("package_sha256"), 10),
                short_identity(identity.get("runtime_hash"), 10),
            ),
            width,
            "value",
        )
    )
    lines.extend(
        wrapped_field(
            "Attempt", short_identity(identity.get("attempt"), 34), width, "value"
        )
    )
    lines.extend(
        wrapped_field(
            "Configuration",
            configuration_text(identity),
            width,
            "value",
        )
    )
    lines.append("")
    lines.extend(workflow_frontier_lines(model, now, width))
    lines.append("")
    lines.extend(compact_activity_lines(model, now, width))
    return "FLOW, RUN ID & ACTIVITY", lines


def activity_lines(model, slurm, identity, now):
    terminal = slurm.get("terminal", False)
    if terminal:
        lines = [
            (
                "Slurm: %s | exit %s | elapsed %s"
                % (
                    slurm.get("state", "-"),
                    slurm.get("exit_code", "-"),
                    slurm.get("elapsed", "-"),
                ),
                "green" if slurm.get("state") == "COMPLETED" else "red",
            ),
            "Attempt receipt: %s" % identity.get("attempt_status", "not reported"),
            progress_line(model, 100),
            "Run root: %s" % identity.get("run_root", "-"),
        ]
        lines.append(
            "Next: run final EMRYS inspection for completion and verified result "
            "locations."
        )
        return "COMPLETION", lines

    lines = []
    if model["last_completion"]:
        lines.append(
            field_line(
                "Latest owner completion",
                "%s ago" % duration(now - model["last_completion"]),
                "value",
            )
        )
    else:
        lines.append("No owner completion has appeared yet.")
    recent_15, recent_60 = completion_velocity(model, now)
    lines.append(
        field_line(
            "Owner completions (rolling)",
            "%d in the last 15m | %d in the last 60m" % (recent_15, recent_60),
            "value",
        )
    )
    lines.append(
        ("Rolling throughput count of finished owner jobs; not an ETA.", "dim")
    )
    lines.append("")
    lines.append("RECENT COMPLETIONS")
    for job_id, key, rule, _ in model["recent"][-6:]:
        lines.append(("DONE job %s | Step %s | %s" % (job_id, key, rule), "green"))
    if not model["recent"]:
        lines.append("None yet.")
    if model["warning"]:
        lines.extend(["", ("Latest error-like line: %s" % model["warning"], "red")])
    return "ACTIVITY", lines


def render_header(screen, job_id, view, attrs):
    safe_add(screen, 0, 1, "EMRYS LIVE DASHBOARD v4.9", attrs["title"])
    safe_add(
        screen,
        0,
        27,
        "| %s | job %s | %s"
        % (view.upper(), job_id, time.strftime("%a %b %d %I:%M:%S %p %Z %Y")),
        attrs["normal"],
    )


def render_overview(
    screen, job_id, slurm, identity, model, refresh_seconds, last_sync, work_scroll
):
    screen.erase()
    height, width = screen.getmaxyx()
    attrs = render.attrs
    now = time.time()
    if height < 20 or width < 72:
        safe_add(screen, 0, 0, "EMRYS LIVE DASHBOARD v4.9", attrs["title"])
        safe_add(
            screen,
            2,
            0,
            "Terminal is too small (%dx%d). Resize to at least 72x20."
            % (width, height),
            attrs["yellow"],
        )
        screen.refresh()
        return

    render_header(screen, job_id, "overview", attrs)

    top_y = 1
    top_h = 6
    draw_box(
        screen,
        top_y,
        1,
        top_h,
        width - 2,
        "RUN OVERVIEW",
        overview_lines(slurm, identity, model, width - 6),
        attrs,
    )

    main_y = top_y + top_h
    footer_y = height - 1
    main_h = footer_y - main_y
    if width >= 140 and main_h >= 38:
        gap = 1
        left_w = (width - 3) // 2
        right_x = 1 + left_w + gap
        right_w = width - right_x - 1
        upper_h = max(19, main_h // 2)
        upper_h = min(upper_h, main_h - 8)
        lower_h = main_h - upper_h

        draw_box(
            screen,
            main_y,
            1,
            upper_h,
            left_w,
            "PIPELINE",
            pipeline_lines(model, now, left_w - 4, include_summary=False),
            attrs,
        )
        draw_box(
            screen,
            main_y,
            right_x,
            upper_h,
            right_w,
            "CURRENT WORK",
            current_lines(
                model,
                identity,
                now,
                right_w - 4,
                include_active=False,
            ),
            attrs,
            scroll=work_scroll,
            scrollable=True,
        )
        draw_box(
            screen,
            main_y + upper_h,
            1,
            lower_h,
            left_w,
            "SAMPLE LANES",
            sample_lane_lines(model, now, left_w - 4),
            attrs,
        )
        activity_title, activity = provenance_activity_lines(
            slurm, identity, model, now, right_w - 4
        )
        draw_box(
            screen,
            main_y + upper_h,
            right_x,
            lower_h,
            right_w,
            activity_title,
            activity,
            attrs,
        )
    else:
        pipeline_h = min(19, max(10, main_h // 2))
        draw_box(
            screen,
            main_y,
            1,
            pipeline_h,
            width - 2,
            "PIPELINE",
            pipeline_lines(model, now, width - 6, include_summary=False),
            attrs,
        )
        remaining_h = main_h - pipeline_h
        draw_box(
            screen,
            main_y + pipeline_h,
            1,
            remaining_h,
            width - 2,
            "CURRENT WORK",
            current_lines(
                model,
                identity,
                now,
                width - 6,
                include_active=False,
            ),
            attrs,
            scroll=work_scroll,
            scrollable=True,
        )

    age = max(0, int(time.monotonic() - last_sync))
    footer = (
        "[Up/Down/PgUp/PgDn] scroll work  [Tab] switch  [r] refresh  [q] quit | NFS-light %ss (%ss ago)"
        % (refresh_seconds, age)
    )
    safe_add(screen, footer_y, 1, footer, attrs["dim"], width - 2)
    screen.refresh()


def render_details(
    screen, job_id, slurm, identity, model, refresh_seconds, last_sync, work_scroll
):
    screen.erase()
    height, width = screen.getmaxyx()
    attrs = render.attrs
    now = time.time()
    if height < 20 or width < 72:
        safe_add(screen, 0, 0, "EMRYS LIVE DASHBOARD v4.9", attrs["title"])
        safe_add(
            screen,
            2,
            0,
            "Terminal is too small (%dx%d). Resize to at least 72x20."
            % (width, height),
            attrs["yellow"],
        )
        screen.refresh()
        return

    render_header(screen, job_id, "details", attrs)
    top_y = 1
    top_h = min(8, max(6, height // 6))
    draw_box(
        screen,
        top_y,
        1,
        top_h,
        width - 2,
        "JOB, RESOURCES & RUN IDENTITY",
        job_lines(slurm, identity, width - 6, attrs),
        attrs,
    )

    main_y = top_y + top_h
    footer_y = height - 1
    main_h = footer_y - main_y
    if width >= 140 and main_h >= 24:
        gap = 1
        left_w = min(86, max(70, int((width - 3) * 0.44)))
        right_x = 1 + left_w + gap
        right_w = width - right_x - 1

        pipeline_h = max(22, int(main_h * 0.62))
        pipeline_h = min(pipeline_h, main_h - 5)
        activity_h = main_h - pipeline_h
        draw_box(
            screen,
            main_y,
            1,
            pipeline_h,
            left_w,
            "PIPELINE",
            pipeline_lines(model, now, left_w - 4),
            attrs,
        )
        activity_title, activity = activity_lines(model, slurm, identity, now)
        draw_box(
            screen,
            main_y + pipeline_h,
            1,
            activity_h,
            left_w,
            activity_title,
            activity,
            attrs,
        )

        current_h = max(12, int(main_h * 0.50))
        current_h = min(current_h, main_h - 8)
        sample_h = main_h - current_h
        draw_box(
            screen,
            main_y,
            right_x,
            current_h,
            right_w,
            "CURRENT WORK DETAILS",
            current_lines(model, identity, now, right_w - 4),
            attrs,
            scroll=work_scroll,
            scrollable=True,
        )
        draw_box(
            screen,
            main_y + current_h,
            right_x,
            sample_h,
            right_w,
            "SAMPLE DETAILS",
            sample_lines(model, now, right_w - 4),
            attrs,
        )
    else:
        pipeline_h = min(22, max(10, main_h // 2))
        draw_box(
            screen,
            main_y,
            1,
            pipeline_h,
            width - 2,
            "PIPELINE",
            pipeline_lines(model, now, width - 6),
            attrs,
        )
        remaining_h = main_h - pipeline_h
        draw_box(
            screen,
            main_y + pipeline_h,
            1,
            remaining_h,
            width - 2,
            "CURRENT WORK DETAILS",
            current_lines(model, identity, now, width - 6),
            attrs,
            scroll=work_scroll,
            scrollable=True,
        )

    age = max(0, int(time.monotonic() - last_sync))
    footer = (
        "[Up/Down/PgUp/PgDn] scroll work  [Tab] switch  [r] refresh  [q] quit | NFS-light %ss (%ss ago)"
        % (refresh_seconds, age)
    )
    safe_add(screen, footer_y, 1, footer, attrs["dim"], width - 2)
    screen.refresh()


def render(
    screen,
    job_id,
    slurm,
    identity,
    model,
    refresh_seconds,
    last_sync,
    view,
    work_scroll,
):
    if view == "details":
        render_details(
            screen,
            job_id,
            slurm,
            identity,
            model,
            refresh_seconds,
            last_sync,
            work_scroll,
        )
    else:
        render_overview(
            screen,
            job_id,
            slurm,
            identity,
            model,
            refresh_seconds,
            last_sync,
            work_scroll,
        )


def snapshot(job_id, slurm, identity, model):
    now = time.time()
    complete, total, remaining = progress_values(model)
    print("EMRYS LIVE DASHBOARD v4.9 snapshot | job %s" % job_id)
    print(
        "State: %s | %s/%s Snakemake jobs | %s remaining"
        % (
            slurm.get("state", "UNKNOWN"),
            complete,
            "unknown" if total is None else total,
            "unknown" if remaining is None else remaining,
        )
    )
    print("Run: %s" % identity.get("run_id", "-"))
    print("Configuration: %s" % configuration_text(identity))
    for line in pipeline_lines(model, now, 80):
        print(line[0] if isinstance(line, tuple) else line)


def selected_scheduler_state(args):
    if args.offline:
        return {
            "state": "UNKNOWN",
            "terminal": False,
            "reason": "Offline; scheduler not queried",
        }
    return _scheduler.query_slurm(args.job_id, args.out, args.err)


def dashboard(screen, args):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    screen.keypad(True)
    screen.timeout(250)
    render.attrs = init_colors()

    out_cache = StreamCache(args.out)
    err_cache = StreamCache(args.err)
    slurm = {"state": "QUERYING", "terminal": False}
    identity = {}
    model = parse_workflow("")
    last_sync = -args.refresh
    force = True
    view = "overview"
    work_scroll = 0
    active_signature = ()

    while True:
        now = time.monotonic()
        if force or now - last_sync >= args.refresh:
            refresh_slurm = force or not slurm.get("terminal")
            out_cache.sync()
            err_cache.sync()
            identity = parse_identity(out_cache.text())
            model = parse_workflow(err_cache.text())
            new_signature = tuple(
                sorted(
                    (job_id, info.get("stage"), info.get("wildcards"))
                    for job_id, info in model["active"].items()
                    if info.get("stage") != "FINAL"
                )
            )
            if new_signature != active_signature:
                work_scroll = 0
                active_signature = new_signature
            if refresh_slurm:
                slurm = selected_scheduler_state(args)
            last_sync = now
            force = False
        render(
            screen,
            args.job_id,
            slurm,
            identity,
            model,
            args.refresh,
            last_sync,
            view,
            work_scroll,
        )
        key = screen.getch()
        if key in (ord("q"), ord("Q")):
            return
        if key in (ord("1"), ord("o"), ord("O")):
            view = "overview"
        elif key in (ord("2"), ord("d"), ord("D")):
            view = "details"
        elif key == 9:
            view = "details" if view == "overview" else "overview"
        elif key in (ord("r"), ord("R")):
            force = True
        elif key in (curses.KEY_UP, ord("k"), ord("K")):
            work_scroll = max(0, work_scroll - 1)
        elif key in (curses.KEY_DOWN, ord("j"), ord("J")):
            work_scroll += 1
        elif key == curses.KEY_PPAGE:
            work_scroll = max(0, work_scroll - 6)
        elif key == curses.KEY_NPAGE:
            work_scroll += 6
        elif key in (curses.KEY_HOME, ord("g")):
            work_scroll = 0
        elif key == curses.KEY_RESIZE:
            screen.erase()
        if slurm.get("terminal"):
            # Keep the completion summary visible until the operator exits.
            pass


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Responsive EMRYS/Slurm live dashboard"
    )
    parser.add_argument("job_id", nargs="?", type=int)
    parser.add_argument("log_dir", nargs="?")
    parser.add_argument("--refresh", type=int, default=30)
    parser.add_argument("--out")
    parser.add_argument("--err")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="use explicit --out/--err fixtures without scheduler metadata",
    )
    parser.add_argument("--snapshot", action="store_true")
    args = parser.parse_args(argv)
    if args.refresh < 5:
        parser.error("--refresh must be at least 5 seconds")
    env_job = os.environ.get("EMRYS_DASHBOARD_JOB_ID", "").strip()
    env_log_dir = os.environ.get("EMRYS_DASHBOARD_LOG_DIR", "").strip()
    selected_job = args.job_id if args.job_id is not None else env_job or None
    selected_log_dir = args.log_dir if args.log_dir is not None else env_log_dir or None
    try:
        selection = resolve_selection(
            selected_job,
            selected_log_dir,
            args.out,
            args.err,
            args.offline,
        )
    except _scheduler.DiscoveryError as exc:
        parser.error(str(exc))
    args.job_id = selection["job_id"]
    args.log_dir = selection["log_dir"]
    args.out = selection["out"]
    args.err = selection["err"]
    return args


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if args.snapshot:
        out_cache = StreamCache(args.out)
        err_cache = StreamCache(args.err)
        out_cache.sync()
        err_cache.sync()
        snapshot(
            args.job_id,
            selected_scheduler_state(args),
            parse_identity(out_cache.text()),
            parse_workflow(err_cache.text()),
        )
        return 0
    try:
        curses.wrapper(dashboard, args)
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
