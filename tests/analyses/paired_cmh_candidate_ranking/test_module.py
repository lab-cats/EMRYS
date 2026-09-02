from pathlib import Path

import pytest

from emrys import analyses
from emrys.analyses.paired_cmh_candidate_ranking import analysis_module_v1


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
