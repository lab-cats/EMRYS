"""Real Snakemake tests for static processing and admitted analysis owners."""

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
from typing import Any, Callable

import pytest

from emrys import analyses
from emrys.analyses.paired_cmh_candidate_ranking import analysis_module_v1
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.libraries.source_authority import controlled_python_argv
from emrys.orchestration.local_pilot import inspection, lifecycle, materialization
from tests.orchestration.local_pilot.fixtures import workflow as workflow_fixture
from tests.orchestration.local_pilot.test_materialization import (
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
    "emrys.analysis.rank_cohort_candidates_with_paired_CMH.v1",
    "emrys.analysis.project_candidate_scientific_context.v1",
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


def _create_clean_source_checkout(checkout: Path) -> tuple[Path, str]:
    checkout.mkdir()
    for name in (".Rprofile", "pyproject.toml", "renv.lock", "uv.lock"):
        shutil.copy2(workflow_fixture.REPO_ROOT / name, checkout)
    shutil.copytree(
        workflow_fixture.REPO_ROOT / "src" / "emrys",
        checkout / "src" / "emrys",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    shutil.copytree(
        workflow_fixture.REPO_ROOT / "workflow",
        checkout / "workflow",
    )
    subprocess.run(["git", "init", "--quiet"], cwd=checkout, check=True)
    subprocess.run(["git", "add", "--all"], cwd=checkout, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=EMRYS Fixture",
            "-c",
            "user.email=emrys-fixture@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "current package",
        ],
        cwd=checkout,
        check=True,
    )
    commit = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=checkout,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return checkout, commit


@pytest.fixture(scope="session")
def clean_source_checkout(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, str]:
    checkout = tmp_path_factory.mktemp("workflow-source") / "checkout"
    return _create_clean_source_checkout(checkout)


def _bind_source_checkout(
    built: workflow_fixture.WorkflowFixture,
    source: tuple[Path, str],
) -> None:
    checkout, commit = source
    attempt = orchestration_contracts.load_json_object(built.workflow_attempt_path)
    config = orchestration_contracts.load_json_object(built.config_path)
    config["source_checkout"] = str(checkout)
    built.config_path.write_bytes(orchestration_contracts.canonical_json_bytes(config))
    attempt["source_checkout"] = {
        "path": str(checkout),
        "commit": commit,
        "clean": True,
    }
    attempt["workflow_config"]["sha256"] = hashlib.sha256(
        built.config_path.read_bytes()
    ).hexdigest()
    built.workflow_attempt_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(attempt)
    )


@pytest.fixture()
def built(
    tmp_path: Path,
    clean_source_checkout: tuple[Path, str],
) -> workflow_fixture.WorkflowFixture:
    result = workflow_fixture.build(tmp_path / "fixture")
    _bind_source_checkout(result, clean_source_checkout)
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
        orchestration_contracts.load_json_object(built.config_path)["python_executable"]
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
        str(built.config_path),
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


def _publish_config(
    built: workflow_fixture.WorkflowFixture,
    config: dict[str, Any],
) -> None:
    payload = orchestration_contracts.canonical_json_bytes(config)
    built.config_path.write_bytes(payload)
    attempt = orchestration_contracts.load_record(
        built.workflow_attempt_path, "workflow-attempt"
    )
    attempt["workflow_config"] = {
        "path": built.config_path.relative_to(built.run_root).as_posix(),
        "sha256": orchestration_contracts.canonical_sha256(config),
    }
    built.workflow_attempt_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(attempt)
    )


def _dag(
    built: workflow_fixture.WorkflowFixture,
    target: str,
    *,
    snakefile: Path = workflow_fixture.SNAKEFILE,
) -> tuple[dict[int, str], set[tuple[int, int]], str]:
    completed = _snakemake(built, "--dag", "dot", "--", target, snakefile=snakefile)
    nodes = {
        int(node_id): (
            label.split("\\n", 1)[1].removeprefix("analysis_owner: ")
            if label.startswith("analysis_owner\\n")
            else label.split("\\n", 1)[0]
        )
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
        orchestration_contracts.load_json_object(built.config_path)["python_executable"]
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
                "emrys.analysis.rank_cohort_candidates_with_paired_CMH.v1",
            ): 1,
            (
                "emrys.analysis.rank_cohort_candidates_with_paired_CMH.v1",
                "emrys.analysis.project_candidate_scientific_context.v1",
            ): 1,
            (
                "construct_FASTA_sidecars",
                "emrys.analysis.project_candidate_scientific_context.v1",
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
    clean_source_checkout: tuple[Path, str],
) -> None:
    checkout, commit = clean_source_checkout
    readiness, resources, _request, workspace = _readiness(
        tmp_path / "processing-plan",
        source_root=checkout,
        source_commit=commit,
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
    config = orchestration_contracts.load_json_object(plan.config_path)
    built = workflow_fixture.WorkflowFixture(
        root=tmp_path / "processing-plan-workflow",
        run_root=plan.run_root,
        config_path=plan.config_path,
        execution=plan.run.run_binding.record,
        profile=plan.run.analysis.profile,
        dispatch_paths={
            machine_key: {
                scope_id: str(reference["path"])
                for scope_id, reference in by_scope.items()
            }
            for machine_key, by_scope in config["dispatch_paths"].items()
        },
        workflow_attempt_path=attempt_path,
    )
    built.root.mkdir()
    workflow_fixture.materialize_active_run_lock(built)

    nodes, _edges, output = _dag(built, "cohort_slice")
    owners = [label for label in nodes.values() if label in EXECUTABLE_RULES]

    assert plan.dispatch_count == len(owners) == 31, output
    assert not {
        "generate_partitioned_cohort_mpileup_VCFs",
        "preprocess_and_annotate_cohort_candidates",
        "emrys.analysis.rank_cohort_candidates_with_paired_CMH.v1",
        "emrys.analysis.project_candidate_scientific_context.v1",
    }.intersection(owners)


def test_backend_projection_accepts_successor_resource_policy_record(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    config = orchestration_contracts.load_json_object(built.config_path)
    resource_policy = config["resource_policy"]
    effective = resource_policy["effective"]
    symbolic = {
        **effective,
        "workflow_memory_mb": "allocation",
        "stage_memory_mb": {
            step_id: "workflow" for step_id in effective["stage_memory_mb"]
        },
        "reporting_memory_mb": {
            kind: "workflow" for kind in effective["reporting_memory_mb"]
        },
    }
    resource_policy["symbolic"] = symbolic
    resource_policy["symbolic_sha256"] = orchestration_contracts.canonical_sha256(
        symbolic
    )
    _publish_config(built, config)

    nodes, _, output = _dag(built, "reference_slice")

    assert sum(nodes[node] in EXECUTABLE_RULES for node in nodes) == 3, output


def test_profile_and_rule_rosters_are_exact_and_output_only_verified_state(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    listed = _snakemake(built, "--list-rules").stdout.splitlines()
    expected = (
        EXECUTABLE_RULES
        - {
            "emrys.analysis.rank_cohort_candidates_with_paired_CMH.v1",
            "emrys.analysis.project_candidate_scientific_context.v1",
        }
    ) | {"analysis_owner", *SLICE_RULES}
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
    assert built.artifact_receipt not in declared
    assert built.run_summary_receipt not in declared
    assert built.report_receipt not in declared


def _profile_checkout(
    root: Path,
    mutate: Callable[[dict[str, Any]], None],
) -> tuple[Path, str, dict[str, Any]]:
    checkout, _commit = _create_clean_source_checkout(root)
    profile_path = checkout / "workflow" / "contracts" / "local_cmh_v2.json"
    profile = analyses.compose_profile(
        orchestration_contracts.load_json_object(profile_path),
        analysis_module_v1(),
    )
    mutate(profile)
    orchestration_contracts.validate_record("profile", profile)
    profile_path.write_bytes(orchestration_contracts.canonical_json_bytes(profile))
    subprocess.run(["git", "add", str(profile_path)], cwd=checkout, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=EMRYS Fixture",
            "-c",
            "user.email=emrys-fixture@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "change workflow profile",
        ],
        cwd=checkout,
        check=True,
    )
    commit = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=checkout,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return checkout, commit, profile


def test_static_graph_rejects_schema_valid_owner_reassignment(tmp_path: Path) -> None:
    def swap_base_owners(profile: dict[str, Any]) -> None:
        by_rule = {str(task["rule_name"]): task for task in profile["owner_tasks"]}
        alignment = by_rule["align_RNA_reads_with_STAR"]
        canonical_bam = by_rule["construct_canonical_BAM"]
        alignment["machine_key"], canonical_bam["machine_key"] = (
            canonical_bam["machine_key"],
            alignment["machine_key"],
        )

    checkout, commit, profile = _profile_checkout(
        tmp_path / "owner-swap-source", swap_base_owners
    )
    rebuilt = workflow_fixture.build(
        tmp_path / "owner-swap-fixture", profile_override=profile
    )
    _bind_source_checkout(rebuilt, (checkout, commit))
    workflow_fixture.materialize_active_run_lock(rebuilt)

    failed = _snakemake(
        rebuilt,
        "--dry-run",
        "--",
        "reference_slice",
        check=False,
        snakefile=checkout / "workflow" / "Snakefile",
    )

    assert failed.returncode != 0
    assert "Processing owner tasks do not match the static base graph" in failed.stdout


def test_analysis_rule_projects_an_alternative_admitted_owner_graph(
    tmp_path: Path,
) -> None:
    old_rank = "emrys.analysis.rank_cohort_candidates_with_paired_CMH.v1"
    old_context = "emrys.analysis.project_candidate_scientific_context.v1"
    rank = "emrys.analysis.alternative_rank.v1"
    context = "emrys.analysis.alternative_context.v1"
    replacements = {old_rank: rank, old_context: context}

    def replace_analysis_graph(profile: dict[str, Any]) -> None:
        for field in ("semantic_owner_keys", "required_owner_keys"):
            profile[field] = [replacements.get(key, key) for key in profile[field]]
        for task in profile["owner_tasks"]:
            original = task["machine_key"]
            task["machine_key"] = replacements.get(original, original)
            if original in replacements:
                task["rule_name"] = (
                    task["rule_name"]
                    .replace(
                        "rank_cohort_candidates_with_paired_CMH", "alternative_rank"
                    )
                    .replace(
                        "project_candidate_scientific_context", "alternative_context"
                    )
                )
        for edge in profile["direct_edges"]:
            producer = replacements.get(edge["producer"], edge["producer"])
            consumer = replacements.get(edge["consumer"], edge["consumer"])
            if producer == rank and consumer == context:
                producer, consumer = context, rank
            elif consumer == rank:
                consumer = context
            elif consumer == context:
                consumer = rank
            edge["producer"], edge["consumer"] = producer, consumer

    checkout, commit, profile = _profile_checkout(
        tmp_path / "alternative-analysis-source", replace_analysis_graph
    )
    rebuilt = workflow_fixture.build(
        tmp_path / "alternative-analysis-fixture", profile_override=profile
    )
    _bind_source_checkout(rebuilt, (checkout, commit))
    workflow_fixture.materialize_active_run_lock(rebuilt)

    nodes, edges, output = _dag(
        rebuilt, "cohort_slice", snakefile=checkout / "workflow" / "Snakefile"
    )
    node_for = {
        label: node_id
        for node_id, label in nodes.items()
        if label
        in {
            "construct_FASTA_sidecars",
            "preprocess_and_annotate_cohort_candidates",
            rank,
            context,
        }
    }
    assert set(node_for) == {
        "construct_FASTA_sidecars",
        "preprocess_and_annotate_cohort_candidates",
        rank,
        context,
    }, output
    assert {
        (node_for["preprocess_and_annotate_cohort_candidates"], node_for[context]),
        (node_for[context], node_for[rank]),
        (node_for["construct_FASTA_sidecars"], node_for[rank]),
    } <= edges


def test_real_cohort_slice_validates_all_scientific_outputs(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    completed = _snakemake(built, "--", "cohort_slice")
    markers = sorted(built.verified_root.glob("*/*.json"))
    starts = sorted((built.run_root / "state" / "task-starts").glob("*/*.json"))
    assert len(markers) == len(starts) == 35, completed.stdout
    for marker in markers:
        record = orchestration_contracts.load_record(marker, "verified-task")
        scope_id = record["scope"]["scope_id"]
        assert record["run_id"] == built.execution["run_id"]
        assert record["machine_key"] == marker.parent.name
        assert (
            marker == built.verified_root / record["machine_key"] / f"{scope_id}.json"
        )
        assert record["all_pass"] is True
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
    assert not built.artifact_receipt.exists()
    assert not built.run_summary_receipt.exists()
    assert not built.report_receipt.exists()
    assert not SCIENTIFIC_BINARIES.intersection(completed.stdout.split())


def test_resume_reuses_every_completed_file_with_existing_engine_metadata(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    _snakemake(built, "--", "cohort_slice")
    before = _snapshot_trees(
        built.verified_root,
        built.run_root / "products" / "native",
    )
    resumed = workflow_fixture.refresh_attempt(built, sequence=1)
    machine_key = "emrys.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    resumed_config = orchestration_contracts.load_json_object(resumed.config_path)
    assert (
        resumed_config["dispatch_paths"][machine_key][scope_id]["path"]
        == (built.dispatch_paths[machine_key][scope_id])
    )
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
        rematerialize_dispatches=True,
    )
    machine_key = "emrys.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    assert (
        substituted.dispatch_paths[machine_key][scope_id]
        != built.dispatch_paths[machine_key][scope_id]
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
    assert (
        "Verified task dispatch does not match current workflow config" in failed.stdout
    )


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
        (owner / "unexpected-link.json").symlink_to(built.config_path)
    else:
        (owner / "unexpected-deep").mkdir(parents=True)

    blockers = inspection.verified_tree_blockers(
        built.run_root,
        inspection.expected_tasks(built.execution, built.profile),
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
    clean_source_checkout: tuple[Path, str],
) -> None:
    machine_key = "emrys.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    marker = built.verified_root / machine_key / f"{scope_id}.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    # A copied schema-valid record from another run is not reusable.
    donor = workflow_fixture.build(built.root.parent / "donor-fixture")
    _bind_source_checkout(donor, clean_source_checkout)
    workflow_fixture.materialize_active_run_lock(donor)
    _snakemake(donor, "--", "reference_slice")
    donor_marker = donor.verified_root / machine_key / f"{scope_id}.json"
    marker.write_bytes(donor_marker.read_bytes())
    failed = _snakemake(built, "--dry-run", "--", "cohort_slice", check=False)
    assert failed.returncode != 0
    assert "Could not admit reusable verified task" in failed.stdout
    assert "run_id does not match" in failed.stdout


def test_content_bound_verified_marker_is_reused_and_mutation_fails_closed(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    _snakemake(built, "--", "reference_slice")
    reused = _snakemake(built, "--dry-run", "--", "reference_slice")
    assert "Nothing to be done" in reused.stdout

    machine_key = "emrys.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    marker = built.verified_root / machine_key / f"{scope_id}.json"
    record = orchestration_contracts.load_record(marker, "verified-task")
    native_output = Path(record["outputs"][0]["path"])
    with native_output.open("ab") as stream:
        stream.write(b"mutated after verification\n")
    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "Could not admit reusable verified task" in failed.stdout
    assert "content binding no longer matches" in failed.stdout


def test_foreign_dispatch_binding_and_unknown_scope_fail_closed(
    built: workflow_fixture.WorkflowFixture,
    clean_source_checkout: tuple[Path, str],
) -> None:
    machine_key = "emrys.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    dispatch = Path(built.dispatch_paths[machine_key][scope_id])
    record = json.loads(dispatch.read_text(encoding="utf-8"))
    record["run_root"] = str((built.root / "foreign-run").resolve())
    dispatch.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "Dispatch bytes do not match configured SHA-256" in failed.stdout

    semantic = workflow_fixture.build(built.root.parent / "semantic-fixture")
    _bind_source_checkout(semantic, clean_source_checkout)
    workflow_fixture.materialize_active_run_lock(semantic)
    dispatch = Path(semantic.dispatch_paths[machine_key][scope_id])
    record = orchestration_contracts.load_json_object(dispatch)
    record["run_root"] = str((semantic.root / "foreign-run").resolve())
    dispatch.write_bytes(orchestration_contracts.canonical_json_bytes(record))
    config = orchestration_contracts.load_json_object(semantic.config_path)
    config["dispatch_paths"][machine_key][scope_id]["sha256"] = (
        orchestration_contracts.canonical_sha256(record)
    )
    _publish_config(semantic, config)
    failed = _snakemake(semantic, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "does not bind expected run_root" in failed.stdout

    rebuilt = workflow_fixture.build(built.root.parent / "second-fixture")
    _bind_source_checkout(rebuilt, clean_source_checkout)
    workflow_fixture.materialize_active_run_lock(rebuilt)
    config = json.loads(rebuilt.config_path.read_text(encoding="utf-8"))
    config["dispatch_paths"][machine_key]["unexpected"] = config["dispatch_paths"][
        machine_key
    ][scope_id]
    _publish_config(rebuilt, config)
    failed = _snakemake(rebuilt, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "Dispatch scopes do not exactly match" in failed.stdout


@pytest.mark.parametrize(
    ("mutation", "expected_message"),
    (
        (
            "predecessor_pending",
            "does not bind the current workflow attempt",
        ),
        ("foreign_stdout", "does not bind exact stdout_path"),
    ),
)
def test_pending_dispatch_identity_and_task_evidence_paths_fail_closed(
    built: workflow_fixture.WorkflowFixture,
    mutation: str,
    expected_message: str,
) -> None:
    machine_key = "emrys.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    config = orchestration_contracts.load_json_object(built.config_path)
    reference = config["dispatch_paths"][machine_key][scope_id]
    dispatch_path = Path(reference["path"])
    dispatch = orchestration_contracts.load_json_object(dispatch_path)
    if mutation == "predecessor_pending":
        dispatch_attempt_id = "workflow-20260812T110000Z-" + "b" * 32
        dispatch["workflow_attempt_id"] = dispatch_attempt_id
        task_root = (
            built.run_root
            / "attempts"
            / dispatch_attempt_id
            / "tasks"
            / machine_key
            / scope_id
        )
        dispatch["task_attempt_path"] = str(task_root / "task-attempt.json")
        dispatch["stdout_path"] = str(task_root / "stdout.log")
        dispatch["stderr_path"] = str(task_root / "stderr.log")
    else:
        dispatch["stdout_path"] = str(
            built.run_root / "attempts" / "foreign-stdout.log"
        )
    dispatch_path.write_bytes(orchestration_contracts.canonical_json_bytes(dispatch))
    reference["sha256"] = orchestration_contracts.canonical_sha256(dispatch)
    _publish_config(built, config)

    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)

    assert failed.returncode != 0
    assert expected_message in failed.stdout


def test_config_and_profile_snapshot_are_closed_and_content_bound(
    built: workflow_fixture.WorkflowFixture,
    clean_source_checkout: tuple[Path, str],
) -> None:
    config = json.loads(built.config_path.read_text(encoding="utf-8"))
    config["unknown"] = "not-allowed"
    built.config_path.write_text(json.dumps(config), encoding="utf-8")
    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "Workflow config keys must be exactly" in failed.stdout

    rebuilt = workflow_fixture.build(built.root.parent / "snapshot-fixture")
    _bind_source_checkout(rebuilt, clean_source_checkout)
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
    config = orchestration_contracts.load_json_object(built.config_path)
    config["python_executable"] = str(workflow_fixture.REPO_ROOT / ".venv/bin/python3")
    _publish_config(built, config)
    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "does not bind python_executable" in failed.stdout


def test_child_source_commit_is_attested_before_graph_admission(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    attempt = orchestration_contracts.load_record(
        built.workflow_attempt_path, "workflow-attempt"
    )
    attempt["source_checkout"]["commit"] = "0" * 40
    built.workflow_attempt_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(attempt)
    )

    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)

    assert failed.returncode != 0
    assert "Could not attest workflow child source identity" in failed.stdout
    assert "HEAD differs from the workflow attempt commit" in failed.stdout
