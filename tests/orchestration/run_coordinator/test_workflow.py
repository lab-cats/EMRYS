"""Real Snakemake tests for the static local-CMH workflow projection."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import shlex
import signal
import subprocess
import time
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.libraries.source_authority import controlled_python_argv
from emrys.orchestration.run_coordinator import inspection, lifecycle, materialization
from tests.orchestration.run_coordinator.fixtures import workflow as workflow_fixture
from tests.orchestration.run_coordinator.test_materialization import (
    _readiness,
    _run_candidate,
)

EXECUTABLE_RULES = {
    "construct_STAR_index",
    "convert_GTF_to_BED12",
    "construct_FASTA_sidecars",
    "align_RNA_reads_with_STAR",
    "construct_canonical_BAM",
    "collect_canonical_BAM_QC_evidence",
    "collect_RSeQC_paired_orientation_evidence",
    "mark_BAM_duplicates_with_Picard",
    "split_N_cigar_reads_with_GATK",
    "partition_BAM_by_mechanical_read_orientation",
    "generate_partitioned_cohort_mpileup_VCFs",
    "preprocess_and_annotate_cohort_candidates",
    "analysis_owner",
}
SLICE_RULES = {"reference_slice", "cohort_slice"}
SCIENTIFIC_BINARIES = {
    "STAR",
    "gatk",
    "picard",
    "infer_experiment.py",
    "bcftools",
    "samtools",
    "R",
    "Rscript",
}


@pytest.fixture()
def built(
    tmp_path: Path,
) -> workflow_fixture.WorkflowFixture:
    result = workflow_fixture.build(tmp_path / "fixture")
    workflow_fixture.materialize_active_run_lock(result)
    return result


def _snakemake(
    built: workflow_fixture.WorkflowFixture,
    *arguments: str,
    check: bool = True,
    metadata_name: str = "snakemake-metadata",
    snakefile: Path = workflow_fixture.SNAKEFILE,
) -> subprocess.CompletedProcess[str]:
    metadata = built.root / metadata_name
    cache = built.root / "cache"
    python_executable = str(
        orchestration_contracts.load_json_object(built.workflow_attempt_path)[
            "normalizer"
        ]["path"]
    )
    command = [
        *controlled_python_argv(python_executable),
        "-m",
        "snakemake",
        "--snakefile",
        str(snakefile),
        "--workflow-profile",
        "local",
        "--runtime-source-cache-path",
        str(cache / "sources"),
        "--configfile",
        str(built.workflow_attempt_path),
        "--directory",
        str(metadata),
        "--nocolor",
        *arguments,
    ]
    environment = {
        **os.environ,
        "XDG_CACHE_HOME": str(cache),
    }
    return subprocess.run(
        command,
        check=check,
        cwd=workflow_fixture.REPO_ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _publish_attempt(
    built: workflow_fixture.WorkflowFixture,
    attempt: dict[str, Any],
) -> None:
    for path, record in (
        (built.workflow_attempt_path, attempt),
        (
            built.run_root / "locks/run.lock",
            orchestration_contracts.run_lock_record(attempt),
        ),
    ):
        path.write_bytes(orchestration_contracts.canonical_json_bytes(record))


def _dag(
    built: workflow_fixture.WorkflowFixture,
    target: str,
) -> tuple[dict[int, str], set[tuple[int, int]], str]:
    completed = _snakemake(built, "--dag", "dot", "--", target)
    nodes = {
        int(node_id): label.split("\\n", 1)[0]
        for node_id, label in re.findall(
            r'^\s*(\d+)\[label = "([^"]+)"',
            completed.stdout,
            flags=re.MULTILINE,
        )
    }
    edges = {
        (int(source), int(target_id))
        for source, target_id in re.findall(
            r"^\s*(\d+) -> (\d+)", completed.stdout, flags=re.MULTILINE
        )
    }
    return nodes, edges, completed.stdout


def _snapshot_trees(*roots: Path) -> dict[Path, tuple[bytes, int]]:
    return {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for root in roots
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def _leave_real_incomplete_marker(
    built: workflow_fixture.WorkflowFixture,
    output: Path,
) -> None:
    backup = built.root / "complete-scientific-output"
    output.replace(backup)
    expected_output = backup.read_bytes()
    interrupter = built.root / "interrupted.Snakefile"
    shell_command = (
        f"cp -p {shlex.quote(str(backup))} {shlex.quote(str(output))} && sleep 60"
    )
    interrupter.write_text(
        "rule interrupted:\n"
        f"    output: {str(output)!r}\n"
        "    shell:\n"
        f"        {shell_command!r}\n",
        encoding="utf-8",
    )
    python_executable = str(
        orchestration_contracts.load_json_object(built.workflow_attempt_path)[
            "normalizer"
        ]["path"]
    )
    process = subprocess.Popen(
        [
            *controlled_python_argv(python_executable),
            "-m",
            "snakemake",
            "--snakefile",
            str(interrupter),
            "--directory",
            str(built.root / "snakemake-metadata"),
            "--cores",
            "1",
            "--keep-incomplete",
            "--nolock",
            "--nocolor",
        ],
        cwd=workflow_fixture.REPO_ROOT,
        env={**os.environ, "XDG_CACHE_HOME": str(built.root / "cache")},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    startup_failure: str | None = None
    captured_output = ""
    try:
        deadline = time.monotonic() + 30
        while not (output.is_file() and output.read_bytes() == expected_output):
            returncode = process.poll()
            if returncode is not None:
                startup_failure = (
                    "Snakemake exited before copying the exact scientific output "
                    f"bytes (return code {returncode})"
                )
                break
            if time.monotonic() >= deadline:
                startup_failure = (
                    "Snakemake did not copy the exact scientific output bytes "
                    "within 30 seconds"
                )
                break
            time.sleep(0.02)
        if startup_failure is None:
            # Give Snakemake's persistence thread time to publish the started-job
            # state before terminating the process group. The shell remains asleep.
            time.sleep(0.5)
    finally:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            captured_output, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            if process.poll() is None:
                process.kill()
            captured_output, _ = process.communicate(timeout=5)

    if startup_failure is not None:
        pytest.fail(
            f"{startup_failure}\nSnakemake output:\n"
            f"{captured_output or '<no output captured>'}"
        )
    assert process.returncode != 0


@pytest.mark.parametrize(
    ("target", "expected_jobs"),
    (("reference_slice", 3), ("cohort_slice", 35)),
)
def test_real_snakemake_dry_run_has_exact_owner_job_counts(
    built: workflow_fixture.WorkflowFixture,
    target: str,
    expected_jobs: int,
) -> None:
    nodes, edges, output = _dag(built, target)
    owners = {node_id for node_id, label in nodes.items() if label in EXECUTABLE_RULES}
    counts = Counter(nodes[node_id] for node_id in owners)
    owner_edges = {
        (source, target)
        for source, target in edges
        if source in owners and target in owners
    }
    assert sum(counts.values()) == expected_jobs, output
    assert "assemble_scientific_review_evidence_package" not in output
    assert "09c" not in output
    if target != "cohort_slice":
        return

    sample_count = len(built.execution["samples"]["rows"])
    partition_count = len(built.execution["partitions"]["rows"])
    assert sum(counts.values()) == 3 + (7 * sample_count) + partition_count + 3
    assert (
        len(owner_edges)
        == (9 * sample_count + sample_count * partition_count + 2 * partition_count + 3)
        == 45
    )
    observed_pairs = Counter(
        (nodes[source], nodes[target]) for source, target in owner_edges
    )
    assert observed_pairs == Counter(
        {
            ("construct_STAR_index", "align_RNA_reads_with_STAR"): sample_count,
            ("align_RNA_reads_with_STAR", "construct_canonical_BAM"): sample_count,
            (
                "construct_canonical_BAM",
                "collect_canonical_BAM_QC_evidence",
            ): sample_count,
            (
                "construct_canonical_BAM",
                "collect_RSeQC_paired_orientation_evidence",
            ): sample_count,
            (
                "convert_GTF_to_BED12",
                "collect_RSeQC_paired_orientation_evidence",
            ): sample_count,
            (
                "construct_canonical_BAM",
                "mark_BAM_duplicates_with_Picard",
            ): sample_count,
            (
                "mark_BAM_duplicates_with_Picard",
                "split_N_cigar_reads_with_GATK",
            ): sample_count,
            (
                "construct_FASTA_sidecars",
                "split_N_cigar_reads_with_GATK",
            ): sample_count,
            (
                "split_N_cigar_reads_with_GATK",
                "partition_BAM_by_mechanical_read_orientation",
            ): sample_count,
            (
                "partition_BAM_by_mechanical_read_orientation",
                "generate_partitioned_cohort_mpileup_VCFs",
            ): sample_count * partition_count,
            (
                "construct_FASTA_sidecars",
                "generate_partitioned_cohort_mpileup_VCFs",
            ): partition_count,
            (
                "generate_partitioned_cohort_mpileup_VCFs",
                "preprocess_and_annotate_cohort_candidates",
            ): partition_count,
            (
                "preprocess_and_annotate_cohort_candidates",
                "analysis_owner",
            ): 1,
            ("analysis_owner", "analysis_owner"): 1,
            (
                "construct_FASTA_sidecars",
                "analysis_owner",
            ): 1,
        }
    )
    evidence = {
        node_id
        for node_id, label in nodes.items()
        if label
        in {
            "collect_canonical_BAM_QC_evidence",
            "collect_RSeQC_paired_orientation_evidence",
        }
    }
    assert evidence
    assert not any(source in evidence for source, _ in owner_edges), output


def test_real_processing_plan_dry_run_closes_at_step_06(
    tmp_path: Path,
) -> None:
    readiness, resources, _request, workspace = _readiness(
        tmp_path / "processing-plan",
    )
    plan = materialization.build_attempt_plan(
        _run_candidate(readiness, resources, through="processing"),
        readiness,
        workspace,
        resources=resources,
        operation="execute",
    )
    ops = lifecycle.default_lifecycle_ops()
    materialization.admit_run(plan, ops=ops)
    materialization.publish_attempt(plan, ops=ops)
    attempt_root = plan.run_root / "attempts" / plan.workflow_attempt_id
    attempt_root.mkdir(mode=0o700)
    (attempt_root / "request.yaml").write_bytes(plan.run.analysis.source_bytes)
    attempt_path = attempt_root / "attempt.json"
    attempt_path.write_bytes(plan.attempt_record_bytes)
    built = workflow_fixture.WorkflowFixture(
        root=tmp_path / "processing-plan-workflow",
        run_root=plan.run_root,
        execution=plan.run.run_binding.record,
        profile=plan.run.analysis.profile,
        workflow_attempt_path=attempt_path,
        attempt_record_bytes=plan.attempt_record_bytes,
    )
    built.root.mkdir()
    workflow_fixture.materialize_active_run_lock(built)

    nodes, _edges, output = _dag(built, "cohort_slice")
    owners = [label for label in nodes.values() if label in EXECUTABLE_RULES]

    assert plan.task_count == len(owners) == 31, output
    assert not {
        "generate_partitioned_cohort_mpileup_VCFs",
        "preprocess_and_annotate_cohort_candidates",
        "analysis_owner",
    }.intersection(owners)


def test_backend_projection_accepts_successor_resource_policy_record(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    config = orchestration_contracts.load_json_object(built.workflow_attempt_path)
    resource_policy = config["workflow"]["resource_policy"]
    effective = resource_policy["effective"]
    symbolic = {
        **effective,
        "workflow_memory_mb": "allocation",
        "stage_memory_mb": {
            step_id: "workflow" for step_id in effective["stage_memory_mb"]
        },
    }
    resource_policy["symbolic"] = symbolic
    resource_policy["symbolic_sha256"] = orchestration_contracts.canonical_sha256(
        symbolic
    )
    _publish_attempt(built, config)

    nodes, _, output = _dag(built, "reference_slice")

    assert sum(nodes[node] in EXECUTABLE_RULES for node in nodes) == 3, output


def test_profile_and_rule_rosters_are_exact_and_output_only_verified_state(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    listed = _snakemake(built, "--list-rules").stdout.splitlines()
    expected = EXECUTABLE_RULES | SLICE_RULES
    observed = {line.strip() for line in listed if line.strip() in expected}
    assert observed == expected

    summary = _snakemake(
        built,
        "--summary",
        "--",
        "cohort_slice",
    ).stdout
    declared = {
        Path(line.split("\t", 1)[0])
        for line in summary.splitlines()
        if line.startswith(str(built.run_root)) and "\t" in line
    }
    assert len(declared) == 35
    assert built.run_summary not in declared
    assert built.report_receipt not in declared


def test_static_graph_rejects_schema_valid_owner_reassignment(tmp_path: Path) -> None:
    profile = orchestration_contracts.load_json_object(workflow_fixture.PROFILE_PATH)
    by_rule = {str(task["rule_name"]): task for task in profile["owner_tasks"]}
    alignment = by_rule["align_RNA_reads_with_STAR"]
    canonical_bam = by_rule["construct_canonical_BAM"]
    alignment["machine_key"], canonical_bam["machine_key"] = (
        canonical_bam["machine_key"],
        alignment["machine_key"],
    )
    orchestration_contracts.validate_record("profile", profile)
    rebuilt = workflow_fixture.build(
        tmp_path / "owner-swap-fixture", profile_override=profile
    )
    workflow_fixture.materialize_active_run_lock(rebuilt)

    failed = _snakemake(
        rebuilt,
        "--dry-run",
        "--",
        "reference_slice",
        check=False,
    )

    assert failed.returncode != 0
    assert "Processing owner tasks do not match the static base graph" in failed.stdout


def test_resume_reuses_every_completed_file_with_existing_engine_metadata(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    completed = _snakemake(built, "--", "cohort_slice")
    markers = sorted(built.verified_root.glob("*/*.json"))
    starts = sorted((built.run_root / "state" / "task-starts").glob("*/*.json"))
    assert len(markers) == len(starts) == 35, completed.stdout
    for marker in markers:
        marker_record = orchestration_contracts.load_record(marker, "verified-task")
        record = orchestration_contracts.load_record(
            built.run_root / marker_record["task_attempt_record"]["path"],
            "task-attempt",
        )
        scope_id = record["scope"]["scope_id"]
        assert record["run_id"] == built.execution["run_id"]
        assert record["machine_key"] == marker.parent.name
        assert (
            marker == built.verified_root / record["machine_key"] / f"{scope_id}.json"
        )
        assert record["status"] == "succeeded"
        start_path = built.run_root / record["task_start_record"]["path"]
        start = orchestration_contracts.load_record(start_path, "task-start")
        assert start_path == (
            built.run_root
            / "state/task-starts"
            / record["machine_key"]
            / f"{scope_id}.json"
        )
        assert start["machine_key"] == record["machine_key"]
        assert start["scope"] == record["scope"]
        assert (
            record["task_start_record"]["sha256"]
            == hashlib.sha256(start_path.read_bytes()).hexdigest()
        )
    assert not built.reporting_root.exists()
    assert not built.run_summary.exists()
    assert not built.report_receipt.exists()
    assert not SCIENTIFIC_BINARIES.intersection(completed.stdout.split())

    before = _snapshot_trees(
        built.verified_root,
        built.run_root / "products" / "native",
    )
    resumed = workflow_fixture.refresh_attempt(built, sequence=1)
    machine_key = "emrys.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    resumed_attempt = orchestration_contracts.load_json_object(
        resumed.workflow_attempt_path
    )
    assert resumed_attempt["tasks"][machine_key][scope_id] == {
        "workflow_attempt_record": {
            "path": built.workflow_attempt_path.relative_to(built.run_root).as_posix(),
            "sha256": hashlib.sha256(
                built.workflow_attempt_path.read_bytes()
            ).hexdigest(),
        }
    }
    completed = _snakemake(
        resumed,
        "--rerun-triggers",
        "input",
        "--ignore-incomplete",
        "--",
        "cohort_slice",
    )
    assert "Nothing to be done" in completed.stdout
    assert (
        _snapshot_trees(
            resumed.verified_root,
            resumed.run_root / "products" / "native",
        )
        == before
    )
    assert not (resumed.workflow_attempt_path.parent / "tasks").exists()


def test_resume_refuses_dispatch_substitution_for_a_valid_completed_task(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    _snakemake(built, "--", "reference_slice")
    substituted = workflow_fixture.refresh_attempt(
        built,
        sequence=4,
        rematerialize_tasks=True,
    )
    machine_key = "emrys.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    substituted_attempt = orchestration_contracts.load_json_object(
        substituted.workflow_attempt_path
    )
    assert (
        "workflow_attempt_record"
        not in substituted_attempt["tasks"][machine_key][scope_id]
    )
    failed = _snakemake(
        substituted,
        "--rerun-triggers",
        "input",
        "--ignore-incomplete",
        "--dry-run",
        "--",
        "reference_slice",
        check=False,
    )
    assert failed.returncode != 0
    assert "Verified task origin does not match the Attempt manifest" in failed.stdout


@pytest.mark.parametrize(
    "entry_kind",
    ("root_file", "root_symlink", "owner_file", "owner_symlink", "deep_directory"),
)
def test_verified_state_roster_rejects_every_unexpected_entry(
    built: workflow_fixture.WorkflowFixture,
    entry_kind: str,
) -> None:
    owner = built.verified_root / "emrys.stage.construct_STAR_index.v1"
    if entry_kind == "root_symlink":
        _snakemake(built, "--", "reference_slice")
        (built.verified_root / "unexpected-owner").symlink_to(
            owner, target_is_directory=True
        )
    elif entry_kind == "root_file":
        built.verified_root.mkdir(parents=True, exist_ok=True)
        (built.verified_root / "unexpected.json").write_text("{}\n", encoding="utf-8")
    elif entry_kind == "owner_file":
        owner.mkdir(parents=True, exist_ok=True)
        (owner / "unexpected.json").write_text("{}\n", encoding="utf-8")
    elif entry_kind == "owner_symlink":
        owner.mkdir(parents=True, exist_ok=True)
        (owner / "unexpected-link.json").symlink_to(built.workflow_attempt_path)
    else:
        (owner / "unexpected-deep").mkdir(parents=True)

    blockers = inspection.verified_tree_blockers(
        built.run_root,
        inspection.expected_tasks(
            inspection.admit_successor_run(built.run_root), built.profile
        ),
    )
    expected_message = (
        "Unexpected verified task owner state"
        if entry_kind.startswith("root_")
        else "Unexpected verified task state path"
    )
    assert len(blockers) == 1 and expected_message in blockers[0]

    if entry_kind == "root_symlink":
        failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)
        assert failed.returncode != 0
        assert "Unexpected verified task" in failed.stdout


def test_resume_reuses_completed_scientific_work_without_engine_metadata(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    _snakemake(built, "--", "cohort_slice")
    before = _snapshot_trees(
        built.verified_root,
        built.run_root / "products" / "native",
    )
    resumed = workflow_fixture.refresh_attempt(built, sequence=2)
    completed = _snakemake(
        resumed,
        "--rerun-triggers",
        "input",
        "--ignore-incomplete",
        "--",
        "cohort_slice",
        metadata_name="fresh-resume-metadata",
    )
    assert "Nothing to be done" in completed.stdout
    assert len(list(resumed.verified_root.glob("*/*.json"))) == 35
    assert (
        _snapshot_trees(
            resumed.verified_root,
            resumed.run_root / "products" / "native",
        )
        == before
    )
    assert not (resumed.workflow_attempt_path.parent / "tasks").exists()


def test_pinned_snakemake_requires_ignore_incomplete_for_scientific_resume(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    _snakemake(built, "--", "cohort_slice")
    before = _snapshot_trees(
        built.verified_root,
        built.run_root / "products" / "native",
    )
    machine_key = "emrys.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    marker = built.verified_root / machine_key / f"{scope_id}.json"
    _leave_real_incomplete_marker(built, marker)
    resumed = workflow_fixture.refresh_attempt(built, sequence=3)

    blocked = _snakemake(
        resumed,
        "--rerun-triggers",
        "input",
        "--",
        "cohort_slice",
        check=False,
    )
    assert blocked.returncode != 0
    assert "seem to be incomplete" in blocked.stdout

    admitted = _snakemake(
        resumed,
        "--rerun-triggers",
        "input",
        "--ignore-incomplete",
        "--",
        "cohort_slice",
    )
    assert "Nothing to be done" in admitted.stdout
    assert (
        _snapshot_trees(
            resumed.verified_root,
            resumed.run_root / "products" / "native",
        )
        == before
    )


def test_foreign_preexisting_verified_marker_fails_closed(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    machine_key = "emrys.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    marker = built.verified_root / machine_key / f"{scope_id}.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    # A copied schema-valid record from another run is not reusable.
    donor = workflow_fixture.build(built.root.parent / "donor-fixture")
    workflow_fixture.materialize_active_run_lock(donor)
    _snakemake(donor, "--", "reference_slice")
    donor_marker = donor.verified_root / machine_key / f"{scope_id}.json"
    marker.write_bytes(donor_marker.read_bytes())
    failed = _snakemake(built, "--dry-run", "--", "cohort_slice", check=False)
    assert failed.returncode != 0
    assert "Could not admit reusable verified task" in failed.stdout
    assert "Could not resolve task-attempt" in failed.stdout


def test_content_bound_verified_marker_is_reused_and_mutation_fails_closed(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    _snakemake(built, "--", "reference_slice")
    reused = _snakemake(built, "--dry-run", "--", "reference_slice")
    assert "Nothing to be done" in reused.stdout

    machine_key = "emrys.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    marker = built.verified_root / machine_key / f"{scope_id}.json"
    marker_record = orchestration_contracts.load_record(marker, "verified-task")
    record = orchestration_contracts.load_record(
        built.run_root / marker_record["task_attempt_record"]["path"], "task-attempt"
    )
    native_output = Path(record["outputs"][0]["path"])
    with native_output.open("ab") as stream:
        stream.write(b"mutated after verification\n")
    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "Could not admit reusable verified task" in failed.stdout
    assert "content binding no longer matches" in failed.stdout


def test_task_origin_binding_and_unknown_scope_fail_closed(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    machine_key = "emrys.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    attempt = orchestration_contracts.load_json_object(built.workflow_attempt_path)
    origin_id = "workflow-20260812T110000Z-" + "b" * 32
    origin_path = built.run_root / "attempts" / origin_id / "attempt.json"
    origin = {
        **attempt,
        "workflow_attempt_id": origin_id,
        "created_at": "2026-08-12T11:00:00Z",
    }
    origin_path.parent.mkdir(parents=True)
    origin_path.write_bytes(orchestration_contracts.canonical_json_bytes(origin))
    attempt["tasks"][machine_key][scope_id] = {
        "workflow_attempt_record": {
            "path": origin_path.relative_to(built.run_root).as_posix(),
            "sha256": "0" * 64,
        }
    }
    _publish_attempt(built, attempt)
    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "Original Attempt manifest bytes differ" in failed.stdout

    origin["workspace"] = str(built.root / "foreign-workspace")
    origin_path.write_bytes(orchestration_contracts.canonical_json_bytes(origin))
    attempt["tasks"][machine_key][scope_id]["workflow_attempt_record"]["sha256"] = (
        hashlib.sha256(origin_path.read_bytes()).hexdigest()
    )
    _publish_attempt(built, attempt)
    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "not at its exact Run path" in failed.stdout

    rebuilt = workflow_fixture.build(built.root.parent / "second-fixture")
    workflow_fixture.materialize_active_run_lock(rebuilt)
    attempt = orchestration_contracts.load_json_object(rebuilt.workflow_attempt_path)
    attempt["tasks"][machine_key]["unexpected"] = attempt["tasks"][machine_key][
        scope_id
    ]
    _publish_attempt(rebuilt, attempt)
    failed = _snakemake(rebuilt, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "Attempt task scopes do not match" in failed.stdout


def test_pending_task_cannot_execute_from_an_original_attempt(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    machine_key = "emrys.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    attempt = orchestration_contracts.load_json_object(built.workflow_attempt_path)
    origin_id = "workflow-20260812T110000Z-" + "b" * 32
    origin = {
        **attempt,
        "workflow_attempt_id": origin_id,
        "created_at": "2026-08-12T11:00:00Z",
    }
    origin_path = built.run_root / "attempts" / origin_id / "attempt.json"
    origin_path.parent.mkdir(parents=True)
    origin_path.write_bytes(orchestration_contracts.canonical_json_bytes(origin))
    attempt["tasks"][machine_key][scope_id] = {
        "workflow_attempt_record": {
            "path": origin_path.relative_to(built.run_root).as_posix(),
            "sha256": hashlib.sha256(origin_path.read_bytes()).hexdigest(),
        }
    }
    _publish_attempt(built, attempt)
    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "does not bind the current workflow attempt" in failed.stdout


def test_attempt_and_profile_snapshot_are_closed_and_content_bound(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    config = json.loads(built.workflow_attempt_path.read_text(encoding="utf-8"))
    config["unknown"] = "not-allowed"
    built.workflow_attempt_path.write_text(json.dumps(config), encoding="utf-8")
    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "Additional properties" in failed.stdout

    rebuilt = workflow_fixture.build(built.root.parent / "snapshot-fixture")
    workflow_fixture.materialize_active_run_lock(rebuilt)
    profile_path = rebuilt.run_root / "contract" / "profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    failed = _snakemake(rebuilt, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "profile snapshot must use canonical JSON bytes" in failed.stdout


def test_child_python_identity_is_bound_before_graph_admission(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    config = orchestration_contracts.load_json_object(built.workflow_attempt_path)
    config["normalizer"]["path"] = str(workflow_fixture.REPO_ROOT / ".venv/bin/python3")
    _publish_attempt(built, config)
    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert (
        "Workflow Python, Snakemake, and normalizer paths must be identical"
        in failed.stdout
    )


def test_child_installed_package_identity_is_attested_before_graph_admission(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    attempt = orchestration_contracts.load_record(
        built.workflow_attempt_path, "workflow-attempt"
    )
    attempt["installed_package"]["content_sha256"] = "0" * 64
    _publish_attempt(built, attempt)

    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)

    assert failed.returncode != 0
    assert "Could not attest workflow child source identity" in failed.stdout
    assert "Installed package differs from workflow attempt" in failed.stdout
