"""Real Snakemake tests for the static local-CMH workflow projection."""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path

import pytest

from norad.contracts.orchestration import api as orchestration_contracts
from tests.orchestration.local_pilot.fixtures import workflow as workflow_fixture

SNAKEMAKE = workflow_fixture.REPO_ROOT / ".venv" / "bin" / "snakemake"
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
}
SLICE_RULES = {"reference_slice", "one_sample_slice", "cohort_slice"}
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
def built(tmp_path: Path) -> workflow_fixture.WorkflowFixture:
    return workflow_fixture.build(tmp_path / "fixture")


def _snakemake(
    built: workflow_fixture.WorkflowFixture,
    *arguments: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    metadata = built.root / "snakemake-metadata"
    cache = built.root / "cache"
    command = [
        str(SNAKEMAKE),
        "--snakefile",
        str(workflow_fixture.SNAKEFILE),
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


def _owner_graph(
    nodes: dict[int, str],
    edges: set[tuple[int, int]],
) -> tuple[Counter[str], set[tuple[int, int]]]:
    owners = {node_id for node_id, label in nodes.items() if label in EXECUTABLE_RULES}
    counts = Counter(nodes[node_id] for node_id in owners)
    return counts, {
        (source, target)
        for source, target in edges
        if source in owners and target in owners
    }


@pytest.mark.parametrize(
    ("target", "expected_jobs"),
    (("reference_slice", 3), ("one_sample_slice", 10), ("cohort_slice", 34)),
)
def test_real_snakemake_dry_run_has_exact_owner_job_counts(
    built: workflow_fixture.WorkflowFixture,
    target: str,
    expected_jobs: int,
) -> None:
    nodes, edges, output = _dag(built, target)
    counts, _ = _owner_graph(nodes, edges)
    assert sum(counts.values()) == expected_jobs, output
    assert "assemble_scientific_review_evidence_package" not in output
    assert "09c" not in output


def test_full_dag_has_exact_edges_and_nongating_evidence_leaves(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    nodes, edges, output = _dag(built, "cohort_slice")
    counts, owner_edges = _owner_graph(nodes, edges)
    sample_count = len(built.execution["samples"]["rows"])
    partition_count = len(built.execution["partitions"]["rows"])
    assert sum(counts.values()) == 3 + (7 * sample_count) + partition_count + 2
    assert (
        len(owner_edges)
        == (9 * sample_count + sample_count * partition_count + 2 * partition_count + 1)
        == 43
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


def test_profile_and_rule_rosters_are_exact_and_output_only_verified_state(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    listed = _snakemake(built, "--list-rules").stdout.splitlines()
    observed = {
        line.strip()
        for line in listed
        if line.strip() in EXECUTABLE_RULES | SLICE_RULES
    }
    assert observed == EXECUTABLE_RULES | SLICE_RULES
    source = workflow_fixture.SNAKEFILE.read_text(encoding="utf-8")
    literal_rules = re.findall(r"^rule ([A-Za-z0-9_]+):", source, re.MULTILINE)
    assert set(literal_rules) == EXECUTABLE_RULES | SLICE_RULES
    assert len(literal_rules) == 16
    assert "assemble_scientific_review_evidence_package" not in literal_rules
    assert "temp(" not in source
    assert "directory(" not in source
    assert "touch(" not in source
    assert "checkpoint " not in source
    assert "glob_wildcards" not in source
    assert "dynamic(" not in source
    assert source.count('state" / "verified') == 1


@pytest.mark.parametrize(
    ("target", "expected_records"),
    (("reference_slice", 3), ("one_sample_slice", 10), ("cohort_slice", 34)),
)
def test_real_snakemake_test_double_executes_each_slice_without_science_tools(
    built: workflow_fixture.WorkflowFixture,
    target: str,
    expected_records: int,
) -> None:
    completed = _snakemake(built, "--", target)
    markers = sorted(built.verified_root.glob("*/*.json"))
    assert len(markers) == expected_records, completed.stdout
    for marker in markers:
        record = orchestration_contracts.load_record(marker, "verified-task")
        assert record["run_id"] == built.execution["run_id"]
        assert record["machine_key"] == marker.parent.name
        assert marker == (
            built.verified_root
            / record["machine_key"]
            / f"{record['scope']['scope_id']}.json"
        )
        assert record["all_pass"] is True
    assert not SCIENTIFIC_BINARIES.intersection(completed.stdout.split())


def test_foreign_preexisting_verified_marker_fails_closed(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    machine_key = "norad.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    marker = built.verified_root / machine_key / f"{scope_id}.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    # A copied schema-valid record from another run is not reusable.
    donor = workflow_fixture.build(built.root.parent / "donor-fixture")
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

    machine_key = "norad.stage.construct_STAR_index.v1"
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
) -> None:
    machine_key = "norad.stage.construct_STAR_index.v1"
    scope_id = str(built.execution["reference"]["reference_id"])
    dispatch = Path(built.dispatch_paths[machine_key][scope_id])
    record = json.loads(dispatch.read_text(encoding="utf-8"))
    record["run_root"] = str((built.root / "foreign-run").resolve())
    dispatch.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "does not bind expected run_root" in failed.stdout

    rebuilt = workflow_fixture.build(built.root.parent / "second-fixture")
    config = json.loads(rebuilt.config_path.read_text(encoding="utf-8"))
    config["dispatch_paths"][machine_key]["unexpected"] = config["dispatch_paths"][
        machine_key
    ][scope_id]
    rebuilt.config_path.write_text(json.dumps(config), encoding="utf-8")
    failed = _snakemake(rebuilt, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "Dispatch scopes do not exactly match" in failed.stdout


def test_config_and_profile_snapshot_are_closed_and_content_bound(
    built: workflow_fixture.WorkflowFixture,
) -> None:
    config = json.loads(built.config_path.read_text(encoding="utf-8"))
    config["unknown"] = "not-allowed"
    built.config_path.write_text(json.dumps(config), encoding="utf-8")
    failed = _snakemake(built, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "Workflow config keys must be exactly" in failed.stdout

    rebuilt = workflow_fixture.build(built.root.parent / "snapshot-fixture")
    profile_path = rebuilt.run_root / "contract" / "profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    failed = _snakemake(rebuilt, "--dry-run", "--", "reference_slice", check=False)
    assert failed.returncode != 0
    assert "profile snapshot must use canonical JSON bytes" in failed.stdout


def test_checked_in_profile_uses_supported_v9_filename_and_local_limits() -> None:
    profile = (
        workflow_fixture.REPO_ROOT
        / "workflow"
        / "profiles"
        / "local"
        / "profile.v9+.yaml"
    )
    assert profile.is_file()
    assert profile.read_text(encoding="utf-8").splitlines() == [
        "executor: local",
        "cores: 1",
        "scheduler: greedy",
        "retries: 0",
        "keep-incomplete: true",
        "printshellcmds: true",
        "show-failed-logs: true",
    ]
