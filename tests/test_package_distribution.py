"""Protect EMRYS's installed-wheel contract without replaying repository tests."""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
import zipfile
from email.parser import Parser
from pathlib import Path

from tests.reporting.fixtures.artifact_run_summary_v2 import build_fixture as FIXTURE

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DEPENDENCIES = {
    "jinja2",
    "jsonschema",
    "logomaker",
    "matplotlib",
    "pyyaml",
    "referencing",
}
RUNTIME_REQUIREMENT_SPECIFIERS = {
    "jinja2": "==3.1.6",
    "jsonschema": ">=4.18.0",
    "logomaker": "==0.8.7",
    "matplotlib": "==3.11.1",
    "pyyaml": "==6.0.3",
    "referencing": ">=0.28.4",
}
RESOURCE_PATHS = (
    "emrys/contracts/schemas/artifacts/v2/artifact_record.schema.json",
    "emrys/contracts/schemas/artifacts/v1/common.schema.json",
    "emrys/contracts/schemas/artifacts/v2/run_summary.schema.json",
    "emrys/contracts/schemas/artifacts/v3/report_receipt.schema.json",
    "emrys/contracts/schemas/artifacts/v3/run_summary.schema.json",
    "emrys/contracts/schemas/artifacts/v4/report_receipt.schema.json",
    "emrys/contracts/schemas/artifacts/v5/report_receipt.schema.json",
    "emrys/contracts/schemas/orchestration/v1/project.schema.json",
    "emrys/contracts/schemas/orchestration/v2/profile.schema.json",
    "emrys/contracts/schemas/orchestration/v2/request.schema.json",
    "emrys/contracts/schemas/orchestration/v3/request.schema.json",
    "emrys/contracts/schemas/orchestration/v3/resource_config.schema.json",
    "emrys/contracts/schemas/orchestration/v3/execution_profile.schema.json",
    "emrys/orchestration/local_pilot/resources/default_execution.yaml",
    "emrys/resources/runtime/runtime_policy.tsv",
    "emrys/resources/runtime/pixi.toml",
    "emrys/resources/runtime/pixi.lock",
    "emrys/contracts/schemas/orchestration/v1/execution.schema.json",
    "emrys/contracts/schemas/orchestration/v1/reference.schema.json",
    "emrys/contracts/schemas/orchestration/v1/policy.schema.json",
    "emrys/contracts/schemas/orchestration/v1/workflow_attempt.schema.json",
    "emrys/contracts/schemas/orchestration/v1/attempt_receipt.schema.json",
    "emrys/contracts/schemas/orchestration/v2/attempt_receipt.schema.json",
    "emrys/contracts/schemas/orchestration/v1/run_lock.schema.json",
    "emrys/contracts/schemas/orchestration/v1/task_start.schema.json",
    "emrys/contracts/schemas/orchestration/v1/task_attempt.schema.json",
    "emrys/contracts/schemas/orchestration/v1/verified_task.schema.json",
    "emrys/contracts/schemas/orchestration/v1/reporting_start.schema.json",
    "emrys/contracts/schemas/orchestration/v1/verified_reporting.schema.json",
    "emrys/contracts/schemas/orchestration/v1/common.schema.json",
    "emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_common.R",
    "emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_editing_site_calling.R",
    "emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_evaluation.R",
    "emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_output.R",
    "emrys/analyses/paired_cmh_candidate_ranking/step_09_cmh_validation.R",
    "emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/scientific_context_projection.R",
    "emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/scientific_context_projection.sh",
    "emrys/analyses/paired_cmh_candidate_ranking/scientific_context_projection/resources/pum_motifs_v1.tsv",
    "emrys/reporting/styles/run_report.css",
    "emrys/reporting/templates/run_report.html.j2",
)
PUBLIC_ONBOARDING_MODULES = {
    "emrys/orchestration/local_pilot/onboarding.py",
    "emrys/orchestration/local_pilot/synthetic_fixture.py",
}
PRIVATE_RUNTIME_MODULES = {
    "emrys/stages/mechanical_orientation/producer.py",
}
LICENSE_EXPRESSION = "LicenseRef-EMRYS-Source-Available-1.0"
LICENSE_FILES = {
    "LICENSE": REPO_ROOT / "LICENSE",
    "NOTICE": REPO_ROOT / "NOTICE",
    "LICENSES/renv-MIT.txt": REPO_ROOT / "LICENSES" / "renv-MIT.txt",
}


def command_environment(*, hostile_pythonpath: bool = False) -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    if hostile_pythonpath:
        environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    return environment


def run_command(
    arguments: list[str], *, cwd: Path, hostile_pythonpath: bool = False
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        env=command_environment(hostile_pythonpath=hostile_pythonpath),
        text=True,
        capture_output=True,
        check=False,
    )


def require_success(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stdout + result.stderr


def uv_executable() -> str:
    executable = shutil.which("uv")
    assert executable is not None, "uv is required; run the documented setup"
    return executable


def build_wheel(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    for name in ("pyproject.toml", "README.md", "LICENSE", "NOTICE"):
        shutil.copy2(REPO_ROOT / name, project / name)
    shutil.copytree(REPO_ROOT / "LICENSES", project / "LICENSES")
    shutil.copytree(
        REPO_ROOT / "src",
        project / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"),
    )
    wheel_directory = tmp_path / "wheel"
    wheel_directory.mkdir()
    result = run_command(
        [
            uv_executable(),
            "build",
            "--wheel",
            "--force-pep517",
            "--offline",
            "--no-python-downloads",
            "--out-dir",
            str(wheel_directory),
            str(project),
        ],
        cwd=tmp_path,
    )
    require_success(result)
    wheels = list(wheel_directory.glob("*.whl"))
    assert len(wheels) == 1
    return wheels[0]


def normalized_requirement(requirement: str) -> str:
    return re.split(r"[ ;(<=>!~\[]", requirement, maxsplit=1)[0].lower()


def declared_requirements(requirements: list[str]) -> dict[str, str]:
    return {
        normalized_requirement(requirement): requirement.split(";", 1)[0]
        .strip()
        .lower()
        for requirement in requirements
    }


def inspect_wheel(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        members = set(archive.namelist())
        (metadata_member,) = (
            member for member in members if member.endswith(".dist-info/METADATA")
        )
        (entry_points_member,) = (
            member
            for member in members
            if member.endswith(".dist-info/entry_points.txt")
        )
        metadata = Parser().parsestr(archive.read(metadata_member).decode())
        declared = declared_requirements(metadata.get_all("Requires-Dist", []))

        assert metadata["Name"] == "emrys-rna-workflow"
        assert metadata["Version"] == "0.1.0.dev0"
        assert metadata["License-Expression"] == LICENSE_EXPRESSION
        assert set(metadata.get_all("License-File", [])) == set(LICENSE_FILES)
        assert not any(
            classifier.startswith("License ::")
            for classifier in metadata.get_all("Classifier", [])
        )
        assert metadata.get_all("Project-URL") == [
            "Repository, https://github.com/lab-cats/EMRYS",
            "Issues, https://github.com/lab-cats/EMRYS/issues",
        ]
        assert set(declared) == RUNTIME_DEPENDENCIES
        assert declared == {
            name: f"{name}{specifier}"
            for name, specifier in RUNTIME_REQUIREMENT_SPECIFIERS.items()
        }
        entry_points = archive.read(entry_points_member).decode().splitlines()
        assert "emrys = emrys.__main__:main" in entry_points
        assert "[emrys.analysis_modules]" in entry_points
        assert (
            "emrys.paired-cmh = "
            "emrys.analyses.paired_cmh_candidate_ranking:analysis_module_v1"
        ) in entry_points
        assert "[emrys.analysis_reporters]" in entry_points
        assert (
            "emrys.paired-cmh = "
            "emrys.reporting.paired_cmh_candidate_ranking_report:render_scientific_report"
        ) in entry_points
        assert set(RESOURCE_PATHS) <= members
        assert PUBLIC_ONBOARDING_MODULES <= members
        assert PRIVATE_RUNTIME_MODULES <= members
        for resource in RESOURCE_PATHS:
            assert archive.read(resource) == (REPO_ROOT / "src" / resource).read_bytes()
        license_root = metadata_member.removesuffix("METADATA") + "licenses/"
        for relative_path, source_path in LICENSE_FILES.items():
            assert (
                archive.read(license_root + relative_path) == source_path.read_bytes()
            )


def install_locked_wheel(wheel: Path, tmp_path: Path) -> tuple[Path, Path]:
    locked = tomllib.loads((REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))
    constraints = []
    for item in locked["package"]:
        if "version" not in item:
            continue
        requirement = f"{item['name']}=={item['version']}"
        markers = item.get("resolution-markers", ())
        if markers:
            requirement += "; " + " or ".join(f"({marker})" for marker in markers)
        constraints.append(requirement)
    constraints.sort()
    installer = tmp_path / "installer"
    installer.mkdir()
    (installer / "pyproject.toml").write_text(
        "[project]\n"
        'name = "emrys-wheel-smoke"\n'
        'version = "0"\n'
        'requires-python = ">=3.11"\n'
        f"dependencies = [{json.dumps(f'emrys-rna-workflow @ {wheel.as_uri()}')}]\n"
        "[tool.uv]\n"
        "constraint-dependencies = [\n"
        + "".join(f"    {json.dumps(requirement)},\n" for requirement in constraints)
        + "]\n",
        encoding="utf-8",
    )
    lock = run_command(
        [
            uv_executable(),
            "lock",
            "--no-python-downloads",
            "--project",
            str(installer),
        ],
        cwd=tmp_path,
    )
    require_success(lock)
    sync = run_command(
        [
            uv_executable(),
            "sync",
            "--locked",
            "--no-dev",
            "--no-install-project",
            "--offline",
            "--no-python-downloads",
            "--python",
            sys.executable,
            "--project",
            str(installer),
        ],
        cwd=tmp_path,
    )
    require_success(sync)
    environment_root = installer / ".venv"
    environment_python = environment_root / "bin" / "python"
    console = environment_root / "bin" / "emrys"
    assert console.is_file()
    return environment_python, console


def installed_probe(environment_python: Path, cwd: Path) -> dict[str, object]:
    probe = run_command(
        [
            str(environment_python),
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            "-c",
            (
                "import importlib.metadata, json, emrys, sys; "
                "from importlib.resources import files; "
                f"resources={RESOURCE_PATHS!r}; root=files('emrys'); "
                f"dependencies={sorted(RUNTIME_DEPENDENCIES)!r}; "
                "print(json.dumps({"
                "'module': emrys.__file__, "
                "'requirements': importlib.metadata.requires('emrys-rna-workflow'), "
                "'installed': {name: importlib.metadata.version(name) "
                "for name in dependencies}, "
                "'resources': [root.joinpath(path.removeprefix('emrys/')).is_file() "
                "for path in resources], "
                "'sys_path': sys.path}))"
            ),
        ],
        cwd=cwd,
        hostile_pythonpath=True,
    )
    require_success(probe)
    return json.loads(probe.stdout)


def test_isolated_wheel_installs_resources_and_public_commands(tmp_path: Path) -> None:
    fixture = FIXTURE.build_fixture(tmp_path / "report-fixture")
    FIXTURE.publish_run_summary(fixture)
    artifact_source_root = fixture.root
    summary = json.loads(fixture.summary_json_path.read_text(encoding="utf-8"))
    summary["provenance"]["git_commit"] = "upstream-summary-commit"
    fixture.summary_json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    wheel = build_wheel(tmp_path)
    inspect_wheel(wheel)
    environment_python, console = install_locked_wheel(wheel, tmp_path)
    arbitrary_cwd = tmp_path / "outside-checkout"
    arbitrary_cwd.mkdir()
    observed = installed_probe(environment_python, arbitrary_cwd)
    module = Path(str(observed["module"])).resolve()
    assert module.is_relative_to(environment_python.parents[1].resolve())
    assert not module.is_relative_to(REPO_ROOT.resolve())
    assert all(observed["resources"])
    assert declared_requirements(observed["requirements"]) == {
        name: f"{name}{specifier}"
        for name, specifier in RUNTIME_REQUIREMENT_SPECIFIERS.items()
    }
    assert set(observed["installed"]) == RUNTIME_DEPENDENCIES
    assert all(observed["installed"].values())
    assert str((REPO_ROOT / "src").resolve()) not in {
        str(Path(entry).resolve()) for entry in observed["sys_path"] if entry
    }
    module_help = run_command(
        [str(environment_python), "-I", "-m", "emrys", "--help"],
        cwd=arbitrary_cwd,
        hostile_pythonpath=True,
    )
    require_success(module_help)
    assert "usage: emrys" in module_help.stdout
    producer_help = run_command(
        [
            str(environment_python),
            "-I",
            "-m",
            "emrys.stages.mechanical_orientation.producer",
            "--help",
        ],
        cwd=arbitrary_cwd,
        hostile_pythonpath=True,
    )
    require_success(producer_help)
    assert "Produce one create-absent Step 06" in producer_help.stdout
    for command, usage in (
        (
            ("init", "project", "--help"),
            "usage: emrys init project",
        ),
        (("init", "manifests", "--help"), "usage: emrys init manifests"),
        (
            ("init", "synthetic", "--help"),
            "usage: emrys init synthetic",
        ),
        (
            ("runtime", "discover", "--help"),
            "usage: emrys runtime discover",
        ),
        (
            ("validate", "project", "--help"),
            "usage: emrys validate project",
        ),
        (("run", "--help"), "usage: emrys run"),
        (("resume", "--help"), "usage: emrys resume"),
        (("report", "--help"), "usage: emrys report"),
        (
            ("inspect", "run", "--help"),
            "usage: emrys inspect run",
        ),
    ):
        public_help = run_command(
            [str(environment_python), "-I", "-m", "emrys", *command],
            cwd=arbitrary_cwd,
            hostile_pythonpath=True,
        )
        require_success(public_help)
        assert usage in public_help.stdout
    console_help = run_command([str(console), "--help"], cwd=arbitrary_cwd)
    require_success(console_help)
    assert "usage: emrys" in console_help.stdout
    manifest = arbitrary_cwd / "samples.tsv"
    manifest.write_text(
        "sample_id\tr1_fastq\tr2_fastq\tstrandedness\tcondition\n"
        "sample_001\treads/R1.fastq.gz\treads/R2.fastq.gz\treverse\tcontrol\n",
        encoding="utf-8",
    )
    validation = run_command(
        [
            str(environment_python),
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            "-m",
            "emrys",
            "validate",
            "manifest",
            "--manifest",
            str(manifest),
        ],
        cwd=arbitrary_cwd,
        hostile_pythonpath=True,
    )
    require_success(validation)
    assert "Manifest validation passed." in validation.stdout
    assert "Samples: 1" in validation.stdout
    report_output_root = arbitrary_cwd / "reports"
    render_program = """
import argparse
import sys
from pathlib import Path

from emrys.reporting import report
from emrys.reporting._run_report.publication import publish_report

context = report.prepare_report(argparse.Namespace(
    source_checkout=Path(sys.argv[1]),
    artifact_source_root=Path(sys.argv[2]),
    run_summary=Path(sys.argv[3]),
    output_root=Path(sys.argv[4]),
))
publish_report(context, report.default_publication_ops())
print(context.output_receipt)
"""
    rendered = run_command(
        [
            str(environment_python),
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            "-c",
            render_program,
            str(REPO_ROOT),
            str(artifact_source_root),
            str(fixture.summary_json_path),
            str(report_output_root),
        ],
        cwd=arbitrary_cwd,
        hostile_pythonpath=True,
    )
    require_success(rendered)
    run_id = fixture.run_id
    report_directory = report_output_root / run_id
    assert str(report_directory / f"{run_id}.report_outputs.tsv") in rendered.stdout
    assert {path.name for path in report_directory.iterdir()} == {
        f"{run_id}.scientific_report.html",
        f"{run_id}.evidence_report.html",
        f"{run_id}.run_summary.tsv",
        f"{run_id}.report_outputs.tsv",
    }
    assert "Jinja2" in (report_directory / f"{run_id}.report_outputs.tsv").read_text(
        encoding="utf-8"
    )
    scientific_html = (report_directory / f"{run_id}.scientific_report.html").read_text(
        encoding="utf-8"
    )
    evidence_html = (report_directory / f"{run_id}.evidence_report.html").read_text(
        encoding="utf-8"
    )
    assert "CMH-ranked candidates" in scientific_html
    assert 'id="candidate-landscape-figure"' in scientific_html
    assert 'id="mutation-spectrum-figure"' in scientific_html
    assert 'id="condition-concordance-figure"' in scientific_html
    assert 'id="paired-sample-profile-figure"' in scientific_html
    assert 'id="location-membership-figure"' in scientific_html
    assert 'id="sequence-context-logo-figure"' in scientific_html
    assert 'id="motif-context-enrichment-figure"' in scientific_html
    assert 'id="selected-context-track-figure"' in scientific_html
    assert scientific_html.count("data:image/svg+xml;base64,") == 7
    for content in (scientific_html, evidence_html):
        assert f'href="{run_id}.scientific_report.html"' in content
        assert f'href="{run_id}.evidence_report.html#evidence-category"' in content
        assert f'href="{run_id}.evidence_report.html#operations-category"' in content
    assert "EMRYS evidence and operations report" in evidence_html
    assert "Matplotlib 3.11.1" in evidence_html
    assert "Logomaker 0.8.7" in evidence_html
    with (report_directory / f"{run_id}.report_outputs.tsv").open(
        encoding="utf-8",
        newline="",
    ) as stream:
        receipt_rows = list(csv.DictReader(stream, delimiter="\t"))
    receipt_values = {row["report_receipt_json"] for row in receipt_rows}
    assert len(receipt_values) == 1
    receipt = json.loads(receipt_values.pop())
    checkout_commit = run_command(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=REPO_ROOT,
    )
    require_success(checkout_commit)
    assert Path(receipt["input_run_summary"]["path"]).is_relative_to(
        artifact_source_root
    )
    assert not Path(receipt["input_run_summary"]["path"]).is_relative_to(REPO_ROOT)
    assert receipt["provenance"]["git_commit"] in {
        "local_build",
        checkout_commit.stdout.strip(),
    }
    assert receipt["provenance"]["git_commit"] != "upstream-summary-commit"
    wrong_checkout = run_command(
        [str(environment_python), "-I", "-m", "emrys", "--help"],
        cwd=REPO_ROOT,
        hostile_pythonpath=True,
    )
    assert wrong_checkout.returncode == 2
    assert "not the current checkout" in wrong_checkout.stderr
