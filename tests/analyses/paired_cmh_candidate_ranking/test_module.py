from dataclasses import replace
from pathlib import Path

import pytest

from emrys import analyses
from emrys.analyses.paired_cmh_candidate_ranking import analysis_module_v1
from emrys.contracts.orchestration import api as orchestration_contracts


SAMPLES = tuple(
    {
        "sample_id": f"{condition}_{replicate}",
        "condition": condition,
        "replicate": str(replicate),
    }
    for replicate in (1, 2)
    for condition in ("control", "treatment")
)
CONTEXT = analyses.AnalysisInputContextV1(SAMPLES, (), {})
CONFIG = {
    "control_condition": "control",
    "treatment_condition": "treatment",
    "target_change": "A>G",
    "min_sample_dp": 1,
    "mean_dp_threshold": 10,
    "fdr_threshold": 0.05,
    "common_or_threshold": 1.2,
    "absolute_difference_threshold": 0.01,
    "background_condition": None,
    "background_max_fraction": 0.01,
}


def test_module_normalizes_the_legacy_base_pair_form() -> None:
    config = {**CONFIG, "rna_ref": "A", "rna_alt": "G"}
    config.pop("target_change")

    normalized = analysis_module_v1().normalize_config(config, CONTEXT)

    assert (normalized["rna_ref"], normalized["rna_alt"]) == ("A", "G")


@pytest.mark.parametrize(
    ("changes", "message"),
    (
        ({"treatment_condition": "control"}, "conditions must differ"),
        ({"background_condition": "control"}, "background condition must differ"),
        ({"target_change": "A>A"}, "target bases must differ"),
        ({"background_condition": "background"}, "conditions must exist"),
    ),
)
def test_module_rejects_cross_field_scientific_invalidity(
    changes: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        analysis_module_v1().normalize_config({**CONFIG, **changes}, CONTEXT)


def test_module_task_planner_includes_an_admitted_background(tmp_path: Path) -> None:
    task = analysis_module_v1().tasks[0]
    context = analyses.TaskPlanningContextV1(
        reference_id="reference",
        cohort_id="cohort",
        analysis_id="analysis",
        sample_manifest=tmp_path / "samples.tsv",
        partition_manifest=tmp_path / "partitions.tsv",
        reference_fasta=tmp_path / "reference.fa",
        reference_gtf=tmp_path / "reference.gtf",
        source_commit="0" * 40,
        configuration={
            **CONFIG,
            "rna_ref": "A",
            "rna_alt": "G",
            "background_condition": "background",
        },
        inputs={
            adapter: (tmp_path / f"{adapter}.tsv",)
            for adapter in (
                "step08_sites_v1",
                "step08_inputs_v1",
                "step08_summary_v1",
            )
        },
        outputs={
            output.adapter: tmp_path / output.artifact_name for output in task.outputs
        },
        runtime_paths={"rscript": "Rscript"},
        python_command=lambda command: command,
        r_owner_command=lambda command: command,
        validator_command=lambda command: command,
    )

    plan = task.plan(context)

    offset = plan.producer_argv.index("--background-condition")
    assert plan.producer_argv[offset : offset + 2] == (
        "--background-condition",
        "background",
    )


def test_module_dependencies_are_canonical_and_readmitted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = tmp_path / "package"
    file = tmp_path / "resource.dat"
    dependencies = (
        analyses.AnalysisDependencyV1("z_file", "file", str(file)),
        analyses.AnalysisDependencyV1(
            "r_collaborator",
            "r_namespace",
            "Collaborator",
            expected=r"^1[.]0$",
        ),
        "python",
        analyses.AnalysisDependencyV1(
            "collaborator_tool",
            "executable",
            str(tmp_path / "tool"),
            expected=r"^tool 1[.]0$",
            probe_args=("--version",),
        ),
        analyses.AnalysisDependencyV1("a_package", "package_tree", str(package)),
    )
    descriptor = replace(analysis_module_v1(), dependencies=dependencies)
    analyses._validate_descriptor(descriptor)
    provider = analyses.load_analysis_module(
        analyses.BUILTIN_PAIRED_CMH_MODULE_ID
    ).provider
    loaded = analyses.LoadedAnalysisModuleV1(descriptor, provider)
    identity = analyses.module_identity_record(loaded)
    policy = {
        "schema_version": "emrys.analysis-module-policy.v1",
        "analysis_id": "primary",
        "module": identity,
        "implementation_sha256": provider.package.sha256,
        "configuration": CONFIG,
    }
    persisted = orchestration_contracts.load_json_object_bytes(
        orchestration_contracts.canonical_json_bytes(policy),
        "test analysis policy",
    )
    orchestration_contracts.validate_record("policy", persisted)
    monkeypatch.setattr(analyses, "load_analysis_module", lambda _module_id: loaded)

    assert [item["dependency_id"] for item in identity["dependencies"]] == [
        "a_package",
        "collaborator_tool",
        "python",
        "r_collaborator",
        "z_file",
    ]
    by_id = {item["dependency_id"]: item for item in identity["dependencies"]}
    assert "target" not in by_id["collaborator_tool"]
    assert "target" not in by_id["z_file"]
    assert by_id["r_collaborator"]["target"] == "Collaborator"
    assert analyses.readmit_analysis_module(persisted) is loaded

    invalid = replace(
        descriptor,
        dependencies=(
            analyses.AnalysisDependencyV1("relative", "file", "resource.dat"),
        ),
    )
    with pytest.raises(analyses.AnalysisModuleLoadError, match="Invalid.*dependency"):
        analyses._validate_descriptor(invalid)

    reserved = replace(
        descriptor,
        dependencies=(
            analyses.AnalysisDependencyV1(
                "runtime_profile", "file", str(file)
            ),
        ),
    )
    with pytest.raises(analyses.AnalysisModuleLoadError, match="reserved"):
        analyses._validate_descriptor(reserved)
