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
from emrys.orchestration.local_pilot import inspection
from emrys.orchestration.local_pilot.reporting_boundary import (
    REPORTING_KINDS,
    publish_start,
    validate_verified,
)
from tests.orchestration.local_pilot.fixtures import workflow as workflow_fixture

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
    "rank_cohort_candidates_with_paired_CMH",
    "project_candidate_scientific_context",
}
SLICE_RULES = {"reference_slice", "one_sample_slice", "cohort_slice"}
REPORTING_RULES = {
    "build_artifact_index",
    "build_run_summary",
    "build_html_report",
}
PIPELINE_RULES = {"local_pipeline_slice"}
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
    shutil.copy2(workflow_fixture.REPO_ROOT / "pyproject.toml", checkout)
    shutil.copytree(
        workflow_fixture.REPO_ROOT / "src" / "emrys",
        checkout / "src" / "emrys",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    subprocess.run(["git", "init", "--quiet"], cwd=checkout, check=True)
    subprocess.run(
        ["git", "add", "pyproject.toml", "src/emrys"], cwd=checkout, check=True
    )
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
    snakefile: Path | None = None,
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
        str(workflow_fixture.SNAKEFILE if snakefile is None else snakefile),
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
    backup = built.root / "complete-reporting-output"
    output.replace(backup)
    expected_output = backup.read_bytes()
    interrupter = built.root / "interrupted.Snakefile"
    shell_command = (
        f"cp -p {shlex.quote(str(backup))} {shlex.quote(str(output))} && sleep 60"
    )
    interrupter.write_text(
        "rule interrupted:\n"
        f"    input: {str(built.reporting_verified('run_summary'))!r}\n"
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
                    "Snakemake exited before copying the exact reporting output "
                    f"bytes (return code {returncode})"
                )
                break
            if time.monotonic() >= deadline:
                startup_failure = (
                    "Snakemake did not copy the exact reporting output bytes "
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
    (("reference_slice", 3), ("one_sample_slice", 10), ("cohort_slice", 35)),
)
def test_real_snakemake_dry_run_has_exact_owner_job_counts(
    built: workflow_fixture.WorkflowFixture,
    target: str,
    expected_jobs: int,
) -> None:
    nodes, edges, output = _dag(built, target)
    owners = {
        node_id for node_id, label in nodes.items() if label in EXECUTABLE_RULES
    }
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
                "rank_cohort_candidates_with_paired_CMH",
            ): 1,
            (
                "rank_cohort_candidates_with_paired_CMH",
                "project_candidate_scientific_context",
            ): 1,
            (
                "construct_FASTA_sidecars",
                "project_candidate_scientific_context",
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
    resource_policy["symbolic_sha256"] = (
        orchestration_contracts.canonical_sha256(symbolic)
    )
    _publish_config(built, config)

    nodes, _, output = _dag(built, "reference_slice")

    assert sum(nodes[node] in EXECUTABLE_RULES for node in nodes) == 3, output


def test_local_pipeline_dag_adds_only_the_three_reporting_transactions(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    nodes, edges, output = _dag(built, "local_pipeline_slice")
    counts = Counter(nodes.values())
    assert sum(counts[rule] for rule in EXECUTABLE_RULES) == 35, output
    assert {rule: counts[rule] for rule in REPORTING_RULES} == {
        "build_artifact_index": 1,
        "build_run_summary": 1,
        "build_html_report": 1,
    }
    assert counts["local_pipeline_slice"] == 1
    observed_pairs = Counter((nodes[source], nodes[target]) for source, target in edges)
    assert (
        sum(
            count
            for (producer, consumer), count in observed_pairs.items()
            if producer in EXECUTABLE_RULES and consumer == "build_artifact_index"
        )
        == 35
    )
    assert observed_pairs[("build_artifact_index", "build_run_summary")] == 1
    assert observed_pairs[("build_run_summary", "build_html_report")] == 1
    assert observed_pairs[("build_html_report", "local_pipeline_slice")] == 1
    assert "assemble_scientific_review_evidence_package" not in output
    assert "09c" not in output


def test_profile_and_rule_rosters_are_exact_and_output_only_verified_state(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    listed = _snakemake(built, "--list-rules").stdout.splitlines()
    expected = EXECUTABLE_RULES | SLICE_RULES | REPORTING_RULES | PIPELINE_RULES
    observed = {line.strip() for line in listed if line.strip() in expected}
    assert observed == expected

    summary = _snakemake(
        built,
        "--summary",
        "--",
        "local_pipeline_slice",
    ).stdout
    declared = {
        Path(line.split("\t", 1)[0])
        for line in summary.splitlines()
        if line.startswith(str(built.run_root)) and "\t" in line
    }
    reporting_outputs = {
        path for path in declared if built.reporting_root in path.parents
    }
    assert reporting_outputs == {
        built.reporting_verified(kind) for kind in REPORTING_KINDS
    }
    assert built.artifact_receipt not in declared
    assert built.run_summary_receipt not in declared
    assert built.report_receipt not in declared


def test_real_local_pipeline_validates_outputs_and_reusable_reporting_ledgers(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    completed = _snakemake(built, "--", "local_pipeline_slice")
    markers = sorted(built.verified_root.glob("*/*.json"))
    starts = sorted((built.run_root / "state" / "task-starts").glob("*/*.json"))
    assert len(markers) == len(starts) == 35, completed.stdout
    for marker in markers:
        record = orchestration_contracts.load_record(marker, "verified-task")
        scope_id = record["scope"]["scope_id"]
        assert record["run_id"] == built.execution["run_id"]
        assert record["machine_key"] == marker.parent.name
        assert marker == built.verified_root / record["machine_key"] / f"{scope_id}.json"
        assert record["all_pass"] is True
        start_path = built.run_root / record["task_start_record"]["path"]
        start = orchestration_contracts.load_record(start_path, "task-start")
        assert start_path == (
            built.run_root / "state/task-starts" / record["machine_key"] / f"{scope_id}.json"
        )
        assert start["machine_key"] == record["machine_key"]
        assert start["scope"] == record["scope"]
        assert record["task_start_record"]["sha256"] == hashlib.sha256(
            start_path.read_bytes()
        ).hexdigest()
    assert built.artifact_receipt.is_file()
    assert built.run_summary_receipt.is_file()
    assert built.report_receipt.is_file()
    for kind in REPORTING_KINDS:
        start = built.reporting_start(kind)
        verified = built.reporting_verified(kind)
        assert start.is_file()
        assert verified.is_file()
        orchestration_contracts.load_record(start, "reporting-start")
        orchestration_contracts.load_record(verified, "verified-reporting")
        outcome = validate_verified(
            kind,
            built.run_root,
            built.execution,
            built.profile,
        )
        assert outcome.start_path == start
        assert outcome.verified_path == verified
    summary = json.loads(built.run_summary.read_text(encoding="utf-8"))
    assert summary["interpretation_boundary"] == (
        "computational_candidates_only_biological_validation_outside_emrys"
    )
    assert "science_status" not in summary
    assert "scientific_review" not in summary
    assert completed.stdout.count("Mode: dry-run") == 3
    assert completed.stdout.count("Mode: execute") == 3
    assert completed.stdout.count("Reporting start:") == 3
    assert completed.stdout.count("Verified reporting:") == 3
    assert "Published report transaction" in completed.stdout
    assert not SCIENTIFIC_BINARIES.intersection(completed.stdout.split())
    for receipt, kind in (
        (built.artifact_receipt, "artifact_index"),
        (built.run_summary_receipt, "run_summary"),
        (built.report_receipt, "html_report"),
    ):
        original = receipt.read_bytes()
        receipt.write_bytes(original + b"corrupt\n")
        failed = _snakemake(
            built, "--dry-run", "--", "local_pipeline_slice", check=False
        )
        assert failed.returncode != 0
        assert f"Could not admit reusable {kind} reporting ledger" in failed.stdout
        receipt.write_bytes(original)


def test_inspection_reads_legacy_reporting_after_source_checkout_advances(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from emrys.reporting import transaction_validation
    from emrys.reporting._artifact_index import api as artifact_api
    from emrys.reporting._artifact_index import records as artifact_records
    from emrys.reporting._run_summary import transaction as summary_transaction

    profile = orchestration_contracts.load_json_object(workflow_fixture.PROFILE_PATH)
    for template in profile["artifact_templates"]:
        template["source_path_template"] = str(
            template["source_path_template"]
        ).replace("products/native/", "results/", 1)
    legacy_profile = tmp_path / "legacy-profile.json"
    legacy_profile.write_bytes(orchestration_contracts.canonical_json_bytes(profile))
    monkeypatch.setattr(workflow_fixture, "PROFILE_PATH", legacy_profile)
    legacy_workflow = tmp_path / "legacy-workflow"
    shutil.copytree(workflow_fixture.REPO_ROOT / "workflow", legacy_workflow)
    (legacy_workflow / "contracts" / "local_cmh_v2.json").write_bytes(
        legacy_profile.read_bytes()
    )

    source = _create_clean_source_checkout(tmp_path / "source-checkout")
    built = workflow_fixture.build(tmp_path / "legacy-fixture")
    _bind_source_checkout(built, source)
    workflow_fixture.materialize_active_run_lock(built)
    completed = _snakemake(
        built,
        "--",
        "local_pipeline_slice",
        check=False,
        snakefile=legacy_workflow / "Snakefile",
    )
    assert completed.returncode == 0, completed.stdout

    checkout, producer_commit = source
    marker = checkout / "reader-revision.txt"
    marker.write_text("reader advanced after historical production\n", encoding="utf-8")
    subprocess.run(["git", "add", marker.name], cwd=checkout, check=True)
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
            "advance reader checkout",
        ],
        cwd=checkout,
        check=True,
    )
    reader_commit = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=checkout,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert reader_commit != producer_commit

    observed = inspection.inspect_run(built.run_root)
    assert observed.reporting_blockers == ()
    assert observed.verified_report_locations == (
        (
            "scientific-report-html",
            built.report_receipt.with_name(
                f"{built.execution['run_id']}.scientific_report.html"
            ),
        ),
        (
            "evidence-report-html",
            built.report_receipt.with_name(
                f"{built.execution['run_id']}.evidence_report.html"
            ),
        ),
    )
    assert built.report_receipt.is_relative_to(
        built.run_root / "products" / "report"
    )

    receipt = artifact_api.read_exact_tsv(
        built.artifact_receipt,
        artifact_api.ARTIFACT_RECEIPT_HEADER,
        exact_rows=1,
    )[0]
    artifact_index = Path(receipt["artifacts_index_path"])
    index_rows = artifact_api.read_exact_tsv(
        artifact_index,
        artifact_api.ARTIFACT_INDEX_HEADER,
    )
    outside_record = (tmp_path / "outside-record.json").resolve()
    outside_record.write_bytes(Path(index_rows[0]["record_path"]).read_bytes())
    index_rows[0]["record_path"] = str(outside_record)
    index_bytes = artifact_records.tsv_bytes(
        artifact_api.ARTIFACT_INDEX_HEADER,
        index_rows,
    )
    artifact_index.write_bytes(index_bytes)
    receipt["artifacts_index_sha256"] = hashlib.sha256(index_bytes).hexdigest()
    built.artifact_receipt.write_bytes(
        artifact_records.tsv_bytes(
            artifact_api.ARTIFACT_RECEIPT_HEADER,
            [receipt],
        )
    )

    outside_touches: list[str] = []
    original_snapshot_receipt = transaction_validation._snapshot_receipt

    def track_receipt_snapshot(path: Path) -> Any:
        if path == outside_record:
            outside_touches.append("receipt snapshot")
        return original_snapshot_receipt(path)

    original_snapshot_roster = transaction_validation._snapshot_bound_roster

    def track_roster(files: Any, *args: Any, **kwargs: Any) -> Any:
        admitted_files = tuple(files)
        if outside_record in admitted_files:
            outside_touches.append("bound roster")
        return original_snapshot_roster(admitted_files, *args, **kwargs)

    original_require_regular_file = summary_transaction._require_regular_file

    def track_summary_file(label: str, value: str | Path) -> Path:
        if Path(value) == outside_record:
            outside_touches.append("run-summary input")
        return original_require_regular_file(label, value)

    monkeypatch.setattr(
        transaction_validation,
        "_snapshot_receipt",
        track_receipt_snapshot,
    )
    monkeypatch.setattr(
        transaction_validation,
        "_snapshot_bound_roster",
        track_roster,
    )
    monkeypatch.setattr(
        summary_transaction,
        "_require_regular_file",
        track_summary_file,
    )
    defaults = inspection.default_inspection_ops()
    validated_kinds: list[str] = []

    def track_validation(kind: str, *args: Any, **kwargs: Any) -> Any:
        validated_kinds.append(kind)
        return defaults.validate_reporting_receipt(kind, *args, **kwargs)

    rejected = inspection.inspect_run(
        built.run_root,
        ops=inspection.InspectionOps(
            host_name=defaults.host_name,
            process_is_alive=defaults.process_is_alive,
            validate_reporting_receipt=track_validation,
        ),
    )
    assert tuple(validated_kinds) == REPORTING_KINDS
    assert outside_touches == []
    for kind in REPORTING_KINDS:
        assert any(
            f"Could not close {kind} reporting ledger" in blocker
            for blocker in rejected.reporting_blockers
        )


def test_resume_reuses_every_completed_file_with_existing_engine_metadata(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    _snakemake(built, "--", "local_pipeline_slice")
    before = _snapshot_trees(
        built.verified_root,
        built.reporting_root,
        built.run_root / "products" / "artifact-summary",
        built.run_root / "results" / "reports",
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
        "local_pipeline_slice",
    )
    assert "Nothing to be done" in completed.stdout
    assert (
        _snapshot_trees(
            resumed.verified_root,
            resumed.reporting_root,
            resumed.run_root / "products" / "artifact-summary",
            resumed.run_root / "results" / "reports",
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
        failed = _snakemake(
            built, "--dry-run", "--", "reference_slice", check=False
        )
        assert failed.returncode != 0
        assert "Unexpected verified-task" in failed.stdout


def test_resume_with_fresh_engine_metadata_runs_only_pending_reporting(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    _snakemake(built, "--", "cohort_slice")
    before = _snapshot_trees(built.verified_root)
    resumed = workflow_fixture.refresh_attempt(built, sequence=2)
    completed = _snakemake(
        resumed,
        "--rerun-triggers",
        "input",
        "--ignore-incomplete",
        "--",
        "local_pipeline_slice",
        metadata_name="fresh-resume-metadata",
    )
    assert len(list(resumed.verified_root.glob("*/*.json"))) == 35
    assert _snapshot_trees(resumed.verified_root) == before
    assert completed.stdout.count("Mode: dry-run") == 3
    assert completed.stdout.count("Mode: execute") == 3
    assert resumed.report_receipt.is_file()
    assert all(resumed.reporting_verified(kind).is_file() for kind in REPORTING_KINDS)
    assert not (resumed.workflow_attempt_path.parent / "tasks").exists()


def test_resume_reuses_completed_reporting_without_engine_metadata(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    _snakemake(built, "--", "local_pipeline_slice")
    before = _snapshot_trees(
        built.verified_root,
        built.reporting_root,
        built.run_root / "products" / "artifact-summary",
        built.run_root / "results" / "reports",
    )
    resumed = workflow_fixture.refresh_attempt(built, sequence=5)
    completed = _snakemake(
        resumed,
        "--rerun-triggers",
        "input",
        "--ignore-incomplete",
        "--",
        "local_pipeline_slice",
        metadata_name="absent-resume-metadata",
    )
    assert "Nothing to be done" in completed.stdout
    assert (
        _snapshot_trees(
            resumed.verified_root,
            resumed.reporting_root,
            resumed.run_root / "products" / "artifact-summary",
            resumed.run_root / "results" / "reports",
        )
        == before
    )
    assert not (resumed.workflow_attempt_path.parent / "tasks").exists()


def test_pinned_snakemake_requires_ignore_incomplete_for_validated_resume(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    _snakemake(built, "--", "local_pipeline_slice")
    before = _snapshot_trees(
        built.verified_root,
        built.reporting_root,
        built.run_root / "products" / "artifact-summary",
        built.run_root / "results" / "reports",
    )
    _leave_real_incomplete_marker(built, built.reporting_verified("html_report"))
    resumed = workflow_fixture.refresh_attempt(built, sequence=3)

    blocked = _snakemake(
        resumed,
        "--rerun-triggers",
        "input",
        "--",
        "local_pipeline_slice",
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
        "local_pipeline_slice",
    )
    assert "Nothing to be done" in admitted.stdout
    assert (
        _snapshot_trees(
            resumed.verified_root,
            resumed.reporting_root,
            resumed.run_root / "products" / "artifact-summary",
            resumed.run_root / "results" / "reports",
        )
        == before
    )


def test_reporting_preflight_failure_publishes_no_receipt_downstream(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    _snakemake(built, "--", "cohort_slice")
    config = json.loads(built.config_path.read_text(encoding="utf-8"))
    config["source_checkout"] = str(built.run_root)
    _publish_config(built, config)
    attempt = orchestration_contracts.load_record(
        built.workflow_attempt_path, "workflow-attempt"
    )
    attempt["source_checkout"]["path"] = str(built.run_root)
    built.workflow_attempt_path.write_bytes(
        orchestration_contracts.canonical_json_bytes(attempt)
    )
    failed = _snakemake(built, "--", "local_pipeline_slice", check=False)
    assert failed.returncode != 0
    assert "Source checkout project metadata is unavailable" in failed.stdout
    assert not built.artifact_receipt.exists()
    assert not built.run_summary_receipt.exists()
    assert not built.report_receipt.exists()
    assert not built.reporting_root.exists()


@pytest.mark.parametrize(
    ("mutation", "expected_message"),
    (
        ("entered_incomplete", "reporting start has no verified completion"),
        ("orphan_completion", "verified reporting exists without a start"),
        ("root_file", "Reporting state root must be a real directory"),
        ("root_symlink", "Reporting state root must be a real directory"),
        ("unexpected_kind", "Unexpected reporting ledger kind"),
        ("unexpected_kind_file", "Unexpected reporting ledger kind"),
        ("unexpected_kind_symlink", "Unexpected reporting ledger kind"),
        ("unexpected_ledger_child", "Unexpected reporting ledger state"),
        (
            "expected_member_symlink",
            "Reporting ledger record is not real",
        ),
        ("expected_member_directory", "Reporting ledger record is not real"),
    ),
)
def test_reporting_state_is_a_closed_complete_ledger(
    built: workflow_fixture.WorkflowFixture,
    mutation: str,
    expected_message: str,
) -> None:
    if mutation == "entered_incomplete":
        publish_start(
            kind="artifact_index",
            run_root=built.run_root,
            execution_path=built.run_root / "contract" / "normalized.json",
            profile_path=built.run_root / "contract" / "profile.json",
            workflow_attempt_path=built.workflow_attempt_path,
            workflow_config_path=built.config_path,
        )
    elif mutation == "orphan_completion":
        orphan = built.reporting_verified("artifact_index")
        orphan.parent.mkdir(parents=True)
        orphan.write_text("{}\n", encoding="utf-8")
    elif mutation == "root_file":
        built.reporting_root.write_text("not a directory\n", encoding="utf-8")
    elif mutation == "root_symlink":
        built.reporting_root.symlink_to(built.verified_root, target_is_directory=True)
    elif mutation == "unexpected_kind":
        (built.reporting_root / "unknown").mkdir(parents=True)
    elif mutation == "unexpected_kind_file":
        built.reporting_root.mkdir(parents=True)
        (built.reporting_root / "unknown").write_text("unexpected\n", encoding="utf-8")
    elif mutation == "unexpected_kind_symlink":
        built.reporting_root.mkdir(parents=True)
        (built.reporting_root / "unknown").symlink_to(built.verified_root)
    elif mutation == "unexpected_ledger_child":
        child = built.reporting_root / "artifact_index" / "nested"
        child.mkdir(parents=True)
    elif mutation == "expected_member_symlink":
        start = built.reporting_start("artifact_index")
        start.parent.mkdir(parents=True)
        start.symlink_to(built.config_path)
    else:
        built.reporting_start("artifact_index").mkdir(parents=True)

    blockers = list(inspection.state_tree_blockers(built.run_root))
    _, ledger_blockers = inspection.inspect_reporting_ledger(
        built.run_root,
        built.execution,
        built.profile,
        lambda *_arguments: pytest.fail("unexpected semantic receipt validation"),
    )
    blockers.extend(ledger_blockers)
    assert any(expected_message in blocker for blocker in blockers)

    integration_message = {
        "entered_incomplete": "is entered but incomplete",
        "expected_member_symlink": "Reporting ledger entry must be a real file",
    }.get(mutation)
    if integration_message is not None:
        failed = _snakemake(
            built,
            "--dry-run",
            "--",
            "local_pipeline_slice",
            check=False,
        )
        assert failed.returncode != 0
        assert integration_message in failed.stdout


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
