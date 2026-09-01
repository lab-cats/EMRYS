"""Focused contract and discovery tests for downstream analysis modules."""

from __future__ import annotations

import json
import tomllib
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator

from emrys import analyses
from emrys.analyses.paired_cmh_candidate_ranking import analysis_module_v1

ROOT = Path(__file__).parents[2]
PROVIDER = "emrys.analyses.paired_cmh_candidate_ranking:analysis_module_v1"
PROFILE = analyses.compose_profile(
    json.loads(
        (ROOT / "workflow/contracts/local_cmh_v2.json").read_text(encoding="utf-8")
    ),
    analysis_module_v1(),
)


def _config() -> dict[str, object]:
    return {
        "control_condition": "EV",
        "treatment_condition": "PUM1",
        "target_change": "A>G",
        "min_sample_dp": 1,
        "mean_dp_threshold": 50,
        "fdr_threshold": 0.05,
        "common_or_threshold": 1.2,
        "absolute_difference_threshold": 0.005,
        "background_max_fraction": 0.01,
    }


def _context(
    samples: tuple[dict[str, object], ...] | None = None,
) -> analyses.AnalysisInputContextV1:
    return analyses.AnalysisInputContextV1(
        samples=samples
        or (
            {"sample_id": "EV_1", "condition": "EV", "replicate": "1"},
            {"sample_id": "PUM1_1", "condition": "PUM1", "replicate": "1"},
            {"sample_id": "EV_2", "condition": "EV", "replicate": "2"},
            {"sample_id": "PUM1_2", "condition": "PUM1", "replicate": "2"},
            {"sample_id": "WT_1", "condition": "WT", "replicate": "1"},
        ),
        partitions=({"partition_id": "all"},),
        reference={"fasta_sha256": "a" * 64, "gtf_sha256": "b" * 64},
    )


def _external_report(
    context: analyses.AnalysisReportContextV1,
) -> analyses.AnalysisScientificReportV1:
    boundary = "Computational demonstration only."
    return analyses.AnalysisScientificReportV1(
        boundary,
        (
            "<!doctype html><html lang='en'><title>External</title>"
            f"<main data-report-view='scientific' data-run-id='{context.run_id}'>"
            f"<h1>External analysis</h1><div class='state-banner'>{boundary}</div>"
            "</main></html>"
        ).encode(),
    )


class _EntryPoint:
    def __init__(
        self,
        name: str,
        provider: object,
        *,
        value: str = PROVIDER,
        distribution: object | None = None,
    ) -> None:
        self.name = name
        self.value = value
        self.provider = provider
        self.dist = distribution
        self.loads = 0

    def load(self) -> object:
        self.loads += 1
        if isinstance(self.provider, Exception):
            raise self.provider
        return self.provider


def _distribution(name: str = "EMRYS_RNA.Workflow", version: str = "1.2.3") -> object:
    return SimpleNamespace(metadata={"Name": name}, name=name, version=version)


def _install(monkeypatch: pytest.MonkeyPatch, *entries: _EntryPoint) -> None:
    monkeypatch.setattr(
        analyses.importlib.metadata,
        "entry_points",
        lambda *, group: entries
        if group == analyses.ANALYSIS_MODULE_ENTRY_POINT_GROUP
        else (),
    )


def test_builtin_descriptor_projects_the_current_step09_step10_tail() -> None:
    descriptor = analysis_module_v1()
    fragment = analyses.module_profile_record(descriptor)
    owners = {task.owner_key for task in descriptor.tasks}

    assert (descriptor.module_id, descriptor.module_version) == ("emrys.paired-cmh", "v1")
    assert {task.step_id for task in descriptor.tasks} == {"09", "10"}
    assert fragment["owner_tasks"] == [
        item for item in PROFILE["owner_tasks"] if item["machine_key"] in owners
    ]
    assert fragment["direct_edges"] == [
        item
        for item in PROFILE["direct_edges"]
        if item["producer"] in owners or item["consumer"] in owners
    ]
    assert fragment["artifact_templates"] == [
        item
        for item in PROFILE["artifact_templates"]
        if item["step_id"] in {"09", "10"}
    ]
    assert callable(descriptor.render_scientific_report)
    assert descriptor.implementation_package == (
        "emrys.analyses.paired_cmh_candidate_ranking"
    )
    assert set(descriptor.required_runtime_checks) >= {"python", "rscript", "bash"}


def test_selected_module_identity_is_exact_and_re_admitted() -> None:
    loaded = analyses.load_analysis_module("emrys.paired-cmh")
    identity = analyses.module_identity_record(loaded)
    policy = {"schema_version": "emrys.analysis-module-policy.v1", "module": identity}

    assert loaded.implementation_root == (
        ROOT / "src/emrys/analyses/paired_cmh_candidate_ranking"
    ).resolve()
    assert len(identity["config_schema_sha256"]) == 64
    assert len(loaded.implementation_sha256) == 64
    assert analyses.readmit_analysis_module(loaded, policy).descriptor is loaded.descriptor

    policy["module"] = {**identity, "module_version": "changed"}
    with pytest.raises(analyses.AnalysisModuleLoadError, match="persisted Run policy"):
        analyses.readmit_analysis_module(loaded, policy)


def test_builtin_configuration_admission_is_canonical() -> None:
    descriptor = analysis_module_v1()
    Draft202012Validator.check_schema(descriptor.config_schema)
    assert analyses.admit_configuration(descriptor, _config(), _context()) == {
        "control_condition": "EV",
        "treatment_condition": "PUM1",
        "background_condition": None,
        "rna_ref": "A",
        "rna_alt": "G",
        "min_sample_dp": 1,
        "mean_dp_threshold": 50,
        "fdr_threshold": 0.05,
        "common_or_threshold": 1.2,
        "absolute_difference_threshold": 0.005,
        "background_max_fraction": 0.01,
    }
    legacy = _config()
    legacy.pop("target_change")
    legacy.update(rna_ref="A", rna_alt="G", background_condition="WT")
    admitted = analyses.admit_configuration(descriptor, legacy, _context())
    assert (admitted["rna_ref"], admitted["rna_alt"], admitted["background_condition"]) == (
        "A",
        "G",
        "WT",
    )


@pytest.mark.parametrize(
    ("change", "message"),
    (
        ({"unknown": "value"}, "Additional properties"),
        ({"min_sample_dp": 0}, "minimum"),
        ({"control_condition": "PUM1"}, "must differ"),
        ({"background_condition": "EV"}, "must differ"),
        ({"target_change": "A>A"}, "bases must differ"),
        ({"treatment_condition": "missing"}, "must exist"),
    ),
)
def test_builtin_configuration_rejects_invalid_intent(
    change: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        analyses.admit_configuration(
            analysis_module_v1(), {**_config(), **change}, _context()
        )


@pytest.mark.parametrize(
    "samples",
    (
        (
            {"sample_id": "EV_1", "condition": "EV", "replicate": "1"},
            {"sample_id": "PUM1_1", "condition": "PUM1", "replicate": "1"},
        ),
        (
            {"sample_id": "EV_1", "condition": "EV", "replicate": "1"},
            {"sample_id": "PUM1_1", "condition": "PUM1", "replicate": "1"},
            {"sample_id": "EV_2", "condition": "EV", "replicate": "1"},
            {"sample_id": "PUM1_2", "condition": "PUM1", "replicate": "2"},
        ),
    ),
)
def test_builtin_configuration_requires_complete_unique_strata(
    samples: tuple[dict[str, object], ...],
) -> None:
    with pytest.raises(ValueError, match="replicate|strata"):
        analyses.admit_configuration(analysis_module_v1(), _config(), _context(samples))


def test_effective_configuration_accepts_current_and_historical_envelopes() -> None:
    configuration = {"control_condition": "EV"}
    assert analyses.effective_configuration(configuration) == configuration
    assert analyses.effective_configuration(
        {
            "schema_version": "emrys.analysis-module-policy.v1",
            "configuration": configuration,
        }
    ) == configuration
    assert analyses.effective_configuration(
        {
            "schema_version": "emrys.analysis-policy.v1",
            "analysis_id": "analysis-1",
            **configuration,
        }
    ) == configuration
    with pytest.raises(ValueError, match="no configuration"):
        analyses.effective_configuration(
            {"schema_version": "emrys.analysis-module-policy.v1"}
        )
    with pytest.raises(ValueError, match="Unsupported"):
        analyses.effective_configuration({"schema_version": "future"})


def test_installed_builtin_entry_point_is_published_and_loaded() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["entry-points"][
        analyses.ANALYSIS_MODULE_ENTRY_POINT_GROUP
    ] == {"emrys.paired-cmh": PROVIDER}
    loaded = analyses.load_analysis_module("emrys.paired-cmh")
    assert loaded.descriptor is analysis_module_v1()
    assert loaded.trust == "built-in"


def test_loader_imports_only_the_exact_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = _EntryPoint(
        "emrys.paired-cmh", analysis_module_v1, distribution=_distribution()
    )
    unselected = _EntryPoint("other", AssertionError("must not load"))
    _install(monkeypatch, unselected, selected)

    loaded = analyses.load_analysis_module("emrys.paired-cmh")
    assert loaded.trust == "built-in"
    assert (selected.loads, unselected.loads) == (1, 0)


def test_loader_admits_one_external_task_without_self_attested_trust(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = analysis_module_v1()
    descriptor = replace(
        base,
        module_id="collaborator.differential",
        tasks=(base.tasks[0],),
        render_scientific_report=_external_report,
    )
    _install(
        monkeypatch,
        _EntryPoint(
            descriptor.module_id,
            lambda: descriptor,
            distribution=_distribution("collaborator-analysis", "4.0"),
        ),
    )

    loaded = analyses.load_analysis_module(descriptor.module_id)
    assert loaded.descriptor is descriptor
    assert (loaded.trust, loaded.distribution_name, loaded.distribution_version) == (
        "external",
        "collaborator-analysis",
        "4.0",
    )


def test_loader_fails_closed_before_loading_missing_or_duplicate_providers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unrelated = _EntryPoint("other", analysis_module_v1)
    _install(monkeypatch, unrelated)
    with pytest.raises(analyses.AnalysisModuleLoadError, match="not installed"):
        analyses.load_analysis_module("emrys.paired-cmh")
    assert unrelated.loads == 0

    duplicates = (
        _EntryPoint("emrys.paired-cmh", analysis_module_v1),
        _EntryPoint("emrys.paired-cmh", analysis_module_v1),
    )
    _install(monkeypatch, *duplicates)
    with pytest.raises(analyses.AnalysisModuleLoadError, match="ambiguous"):
        analyses.load_analysis_module("emrys.paired-cmh")
    assert all(entry.loads == 0 for entry in duplicates)


@pytest.mark.parametrize(
    ("provider", "message"),
    (
        (object(), "could not be loaded"),
        (RuntimeError("provider failed"), "could not be loaded"),
        (lambda: object(), "wrong descriptor type"),
    ),
)
def test_loader_rejects_invalid_providers(
    monkeypatch: pytest.MonkeyPatch, provider: object, message: str
) -> None:
    _install(monkeypatch, _EntryPoint("emrys.paired-cmh", provider))
    with pytest.raises(analyses.AnalysisModuleLoadError, match=message):
        analyses.load_analysis_module("emrys.paired-cmh")


def _replace_first_task(
    descriptor: analyses.AnalysisModuleDescriptorV1, **changes: object
) -> analyses.AnalysisModuleDescriptorV1:
    return replace(
        descriptor,
        tasks=(descriptor.tasks[0]._replace(**changes), *descriptor.tasks[1:]),
    )


@pytest.mark.parametrize(
    "mutate",
    (
        lambda value: _replace_first_task(value, step_id="11"),
        lambda value: _replace_first_task(value, stage_memory_mb=0),
        lambda value: _replace_first_task(
            value,
            outputs=tuple(
                output._replace(kind="tsv")
                if output.kind == "validation_report"
                else output
                for output in value.tasks[0].outputs
            ),
        ),
        lambda value: _replace_first_task(
            value,
            outputs=(
                value.tasks[0].outputs[0]._replace(kind="binary"),
                *value.tasks[0].outputs[1:],
            ),
        ),
        lambda value: _replace_first_task(
            value,
            outputs=(
                value.tasks[0].outputs[0]._replace(
                    source_path_template="/tmp/{analysis_id}.tsv"
                ),
                *value.tasks[0].outputs[1:],
            ),
        ),
        lambda value: replace(value, required_runtime_checks=("rscript", "rscript")),
        lambda value: replace(value, render_scientific_report=None),
    ),
)
def test_loader_rejects_unsupported_v1_shapes(
    monkeypatch: pytest.MonkeyPatch, mutate: object
) -> None:
    descriptor = mutate(analysis_module_v1())  # type: ignore[operator]
    _install(
        monkeypatch,
        _EntryPoint(
            "emrys.paired-cmh", lambda: descriptor, distribution=_distribution()
        ),
    )
    with pytest.raises(analyses.AnalysisModuleLoadError):
        analyses.load_analysis_module("emrys.paired-cmh")


@pytest.mark.parametrize(
    ("descriptor", "message"),
    (
        (replace(analysis_module_v1(), module_id="wrong.module"), "descriptor ID"),
        (
            replace(
                analysis_module_v1(),
                config_schema={"type": "not-a-json-schema-type"},
            ),
            "schema is invalid",
        ),
        (
            replace(analysis_module_v1(), implementation_package="emrys.unrelated"),
            "contain its provider",
        ),
    ),
)
def test_loader_rejects_mismatched_descriptor_contracts(
    monkeypatch: pytest.MonkeyPatch,
    descriptor: analyses.AnalysisModuleDescriptorV1,
    message: str,
) -> None:
    _install(
        monkeypatch,
        _EntryPoint(
            "emrys.paired-cmh", lambda: descriptor, distribution=_distribution()
        ),
    )
    with pytest.raises(analyses.AnalysisModuleLoadError, match=message):
        analyses.load_analysis_module("emrys.paired-cmh")


def test_loader_requires_distribution_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(monkeypatch, _EntryPoint("emrys.paired-cmh", analysis_module_v1))
    with pytest.raises(analyses.AnalysisModuleLoadError, match="no distribution"):
        analyses.load_analysis_module("emrys.paired-cmh")


def test_profile_composition_rejects_adapter_collision() -> None:
    core = json.loads(
        (ROOT / "workflow/contracts/local_cmh_v2.json").read_text(encoding="utf-8")
    )
    descriptor = analysis_module_v1()
    collision = descriptor.tasks[0].outputs[0]._replace(
        adapter=core["artifact_templates"][0]["adapter"]
    )
    descriptor = _replace_first_task(
        descriptor, outputs=(collision, *descriptor.tasks[0].outputs[1:])
    )
    with pytest.raises(analyses.AnalysisModuleLoadError, match="collide"):
        analyses.compose_profile(core, descriptor)
