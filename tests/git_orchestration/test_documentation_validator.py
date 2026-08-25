"""Behavior locks for documentation ownership and local structure."""

from __future__ import annotations

import os
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "git_orchestration" / "validate_documentation.py"
CANONICAL_H1S = {
    "AGENTS.md": "# EMRYS safety guard",
    "README.md": "# EMRYS: Epic Molecular Read Yield System",
    "docs/architecture/README.md": "# Architecture index",
    "docs/architecture/ARCHITECTURE.md": "# Current architecture",
    "docs/architecture/FUNCTIONAL_OWNER_INVENTORY.md": "# Current functional-owner inventory",
    "docs/architecture/FUTURE_ARCHITECTURE.md": "# Future architecture",
    "docs/design/DECISIONS.md": "# Durable decisions",
    "docs/design/LOGGING_CONTRACT.md": "# Application logging contract",
    "docs/design/ORCHESTRATION_CONTRACT.md": "# Local-pilot orchestration contract",
    "docs/design/ORCHESTRATION_READINESS.md": "# Local-pilot orchestration readiness",
    "docs/design/PIPELINE_PLAN.md": "# EMRYS pipeline plan",
    "docs/design/QUESTIONS.md": "# Open questions",
    "docs/design/TEST_BASELINE.md": "# Test baseline and contract-risk index",
    "docs/operations/HANDOFF.md": "# Project handoff",
    "docs/operations/RUNBOOK.md": "# Runbook",
    "docs/operations/TROUBLESHOOTING.md": "# Troubleshooting",
    "docs/operations/WORKFLOW.md": "# Workflow kernel",
    "docs/sitemap/README.md": "# Documentation sitemap",
    "docs/tasks/README.md": "# Task planning",
    "docs/tasks/backlog_matrix.md": "# EMRYS Findings Matrix and Working Backlog",
    "src/emrys/contracts/SOURCE_TOPOLOGY.md": "# Source ownership and dependency direction",
    "src/emrys/contracts/STAGE_MAP.md": "# Semantic workflow identity and DAG",
}
SEMANTIC_OWNERS = (
    ("stage", "construct_STAR_index"),
    ("stage", "construct_FASTA_sidecars"),
    ("stage", "convert_GTF_to_BED12"),
    ("stage", "align_RNA_reads_with_STAR"),
    ("stage", "construct_canonical_BAM"),
    ("stage", "mark_BAM_duplicates_with_Picard"),
    ("stage", "split_N_cigar_reads_with_GATK"),
    ("stage", "partition_BAM_by_mechanical_read_orientation"),
    ("stage", "generate_partitioned_cohort_mpileup_VCFs"),
    ("stage", "preprocess_and_annotate_cohort_candidates"),
    ("analysis", "rank_cohort_candidates_with_paired_CMH"),
    ("analysis", "project_candidate_scientific_context"),
    ("evidence", "collect_canonical_BAM_QC_evidence"),
    ("evidence", "collect_RSeQC_paired_orientation_evidence"),
)
SOURCE_OWNER_DIRECTORIES = {
    (
        "analysis",
        "rank_cohort_candidates_with_paired_CMH",
    ): "paired_cmh_candidate_ranking",
    (
        "analysis",
        "project_candidate_scientific_context",
    ): "scientific_context_projection",
    ("evidence", "collect_canonical_BAM_QC_evidence"): "canonical_bam_qc",
    ("evidence", "collect_RSeQC_paired_orientation_evidence"): "rseqc_orientation",
    ("stage", "align_RNA_reads_with_STAR"): "star_alignment",
    ("stage", "construct_canonical_BAM"): "canonical_bam",
    ("stage", "construct_STAR_index"): "star_index",
    ("stage", "construct_FASTA_sidecars"): "fasta_sidecars",
    ("stage", "convert_GTF_to_BED12"): "gtf_to_bed12",
    ("stage", "mark_BAM_duplicates_with_Picard"): "duplicate_marking",
    (
        "stage",
        "partition_BAM_by_mechanical_read_orientation",
    ): "mechanical_orientation",
    (
        "stage",
        "generate_partitioned_cohort_mpileup_VCFs",
    ): "partitioned_cohort_mpileup",
    (
        "stage",
        "preprocess_and_annotate_cohort_candidates",
    ): "cohort_candidate_preprocessing",
    ("stage", "split_N_cigar_reads_with_GATK"): "split_n_cigar",
}
CROSS_CUTTING_DOCS = (
    "src/emrys/contracts/artifacts/README.md",
    "src/emrys/evidence/reference_provenance/README.md",
    "src/emrys/evidence/runtime_availability/README.md",
    "src/emrys/evidence/storage_inventory/README.md",
    "src/emrys/ingestion/sample_manifest_admission/README.md",
    "src/emrys/reporting/README.md",
)


def run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command_env = os.environ.copy()
    if env:
        command_env.update(env)
    return subprocess.run(
        command,
        cwd=cwd,
        env=command_env,
        text=True,
        capture_output=True,
        check=False,
    )


def write_fixture(root: Path) -> Path:
    repository = root / "repository"
    repository.mkdir()
    initialized = run(["git", "init", "-q", str(repository)], cwd=root)
    assert initialized.returncode == 0, initialized.stderr
    files = {
        "docs/fixture.mmd": "flowchart LR\n    A --> B\n",
    }
    files.update({path: f"{h1}\n" for path, h1 in CANONICAL_H1S.items()})
    identity_rows = [
        f"| {kind} | Fixture | `{slug}` | `emrys.{kind}.{slug}.v1` | `00` |"
        for kind, slug in SEMANTIC_OWNERS
    ]
    files["src/emrys/contracts/STAGE_MAP.md"] = (
        "# Semantic workflow identity and DAG\n\n" + "\n".join(identity_rows) + "\n"
    )
    files.update({path: "# Owner\n" for path in CROSS_CUTTING_DOCS})
    domain_by_kind = {"stage": "stages", "analysis": "analyses", "evidence": "evidence"}
    for kind, slug in SEMANTIC_OWNERS:
        domain = domain_by_kind[kind]
        source_directory = SOURCE_OWNER_DIRECTORIES.get((kind, slug), slug)
        files[f"src/emrys/{domain}/{source_directory}/README.md"] = (
            f"# `{slug}` owner\n"
        )
        files[f"src/emrys/{domain}/{source_directory}/CONTRACT.md"] = (
            f"# `{slug}` {kind} contract\n"
        )
        files[f"tests/{domain}/{source_directory}/.keep"] = "fixture\n"
    for relative, text in files.items():
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return repository


def validate(
    repository: Path,
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return run(
        [sys.executable, str(VALIDATOR), "--repo", str(repository)],
        cwd=cwd,
        env=env,
    )


def test_accepts_minimal_repository_and_reports_counts_without_writes(
    tmp_path: Path,
) -> None:
    repository = write_fixture(tmp_path)
    before = tuple(
        sorted(path.relative_to(repository) for path in repository.rglob("*"))
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert "1 Mermaid sources" in result.stdout
    assert (
        tuple(sorted(path.relative_to(repository) for path in repository.rglob("*")))
        == before
    )


def test_rejects_missing_or_mislabeled_canonical_documents(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "docs/operations/WORKFLOW.md").unlink()
    (repository / "docs/operations/RUNBOOK.md").write_text(
        "No heading.\n", encoding="utf-8"
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert "missing canonical document: docs/operations/WORKFLOW.md" in result.stderr
    assert "canonical document H1 mismatch: docs/operations/RUNBOOK.md" in result.stderr


def test_rejects_stage_map_and_owner_failures(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "src/emrys/contracts/STAGE_MAP.md").write_text(
        "# Semantic workflow identity and DAG\n\n"
        "| stage | Fixture | `STAGE-01` | `emrys.stage.STAGE-01.v1` | `00` |\n",
        encoding="utf-8",
    )
    (repository / "src/emrys/stages/star_index/CONTRACT.md").unlink()
    (repository / "src/emrys/reporting/README.md").unlink()

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert "STAGE_MAP identity roster must contain 14 unique owners" in result.stderr
    assert "missing cross-cutting owner documentation" in result.stderr


def test_rejects_missing_semantic_owner_after_valid_roster(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "src/emrys/stages/star_index/CONTRACT.md").unlink()
    shutil.rmtree(repository / "tests/stages/gtf_to_bed12")

    result = validate(repository, cwd=tmp_path)

    assert "missing semantic-owner CONTRACT.md" in result.stderr
    assert "missing mirrored test owner: tests/stages/gtf_to_bed12" in result.stderr


def test_rejects_returned_retired_docs_and_task_directories(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    retired_paths = (
        "docs/design/REFACTOR_AUDIT.md",
        "docs/operations/TASK_DELIVERY.md",
        "docs/tasks/BACKLOG.md",
        "docs/tasks/cards/README.md",
    )
    for relative in retired_paths:
        retired = repository / relative
        retired.parent.mkdir(parents=True, exist_ok=True)
        retired.write_text("# Retired\n", encoding="utf-8")
    legacy_paths = (
        repository / "docs/tasks/TODO/OLD-01.md",
        repository / "docs/tasks/cards/OLD-02.md",
    )
    for legacy in legacy_paths:
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_text("# Old\n", encoding="utf-8")

    result = validate(repository, cwd=tmp_path)

    for relative in retired_paths:
        assert f"retired documentation owner returned: {relative}" in result.stderr
    assert "retired task directory contains Markdown: docs/tasks/TODO" in result.stderr
    assert "retired task directory contains Markdown: docs/tasks/cards" in result.stderr


@pytest.mark.parametrize("kind", ("missing", "non_git", "nested"))
def test_rejects_invalid_repository_roots(tmp_path: Path, kind: str) -> None:
    if kind == "missing":
        root = tmp_path / "missing"
        expected = "ERROR: repository path is unavailable:"
    elif kind == "non_git":
        root = tmp_path / "plain"
        root.mkdir()
        expected = f"ERROR: not a Git worktree: {root}:"
    else:
        repository = write_fixture(tmp_path)
        root = repository / "nested"
        root.mkdir()
        expected = f"ERROR: repository path is not the worktree root: {root}\n"

    result = validate(root, cwd=tmp_path)

    assert result.returncode == 1
    assert result.stdout == ""
    assert (
        result.stderr == expected
        if kind == "nested"
        else result.stderr.startswith(expected)
    )


def test_fails_closed_when_git_inventory_fails(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    real_git = shutil.which("git")
    assert real_git is not None
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text(
        "#!/bin/sh\n"
        'case " $* " in\n'
        "  *\" ls-files \"*) echo 'inventory exploded' >&2; exit 17 ;;\n"
        "esac\n"
        f'exec {shlex.quote(real_git)} "$@"\n',
        encoding="utf-8",
    )
    fake_git.chmod(fake_git.stat().st_mode | stat.S_IXUSR)

    result = validate(
        repository,
        cwd=tmp_path,
        env={"PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}"},
    )

    assert result.stderr == "ERROR: could not inventory *.md: inventory exploded\n"


def test_ignores_general_markdown_links_but_rejects_bad_mermaid(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    readme = repository / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + "\n[Missing](missing.md)\n[External](https://example.test)\n",
        encoding="utf-8",
    )
    assert validate(repository, cwd=tmp_path).returncode == 0

    (repository / "docs/fixture.mmd").write_text(
        "sequenceDiagram\n```\n", encoding="utf-8"
    )
    result = validate(repository, cwd=tmp_path)
    assert "invalid Mermaid declaration: docs/fixture.mmd" in result.stderr
    assert "Markdown fence in Mermaid source: docs/fixture.mmd" in result.stderr
