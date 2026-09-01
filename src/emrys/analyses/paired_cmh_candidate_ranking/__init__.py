"""Built-in paired-CMH analysis-module declaration."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

from emrys import analyses as module_api
from emrys.analyses.paired_cmh_candidate_ranking import producer as step09_producer
from emrys.analyses.paired_cmh_candidate_ranking import validator as step09_validator
from emrys.contracts.scientific_evidence import scientific_context, step09

_STEP09_OWNER = "emrys.analysis.rank_cohort_candidates_with_paired_CMH.v1"
_STEP10_OWNER = "emrys.analysis.project_candidate_scientific_context.v1"

_SAFE_ID = {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]*$"}


def _number(**bounds: object) -> dict[str, object]:
    return {"type": "number", **bounds}


_CONFIG_FIELDS = (
    "control_condition",
    "treatment_condition",
    "target_change",
    "min_sample_dp",
    "mean_dp_threshold",
    "fdr_threshold",
    "common_or_threshold",
    "absolute_difference_threshold",
    "background_max_fraction",
)
_CONFIG_SCHEMA: dict[str, object] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "EMRYS paired-CMH analysis configuration v1",
    "type": "object",
    "additionalProperties": False,
    "required": [*_CONFIG_FIELDS[:2], *_CONFIG_FIELDS[3:]],
    "oneOf": [
        {"required": ["target_change"]},
        {"required": ["rna_ref", "rna_alt"]},
    ],
    "properties": {
        "control_condition": _SAFE_ID,
        "treatment_condition": _SAFE_ID,
        "target_change": {"type": "string", "pattern": "^[ACGT]>[ACGT]$"},
        "rna_ref": {"type": "string", "pattern": "^[ACGT]$"},
        "rna_alt": {"type": "string", "pattern": "^[ACGT]$"},
        "min_sample_dp": {"type": "integer", "minimum": 1},
        "mean_dp_threshold": _number(minimum=0),
        "fdr_threshold": _number(exclusiveMinimum=0, maximum=1),
        "common_or_threshold": _number(exclusiveMinimum=1),
        "absolute_difference_threshold": _number(minimum=0, maximum=1),
        "background_condition": {"oneOf": [_SAFE_ID, {"type": "null"}]},
        "background_max_fraction": _number(exclusiveMinimum=0, exclusiveMaximum=1),
    },
}


def _normalize_config(
    config: Mapping[str, object], context: module_api.AnalysisInputContextV1
) -> dict[str, object]:
    config = dict(config)
    if "target_change" not in config and {"rna_ref", "rna_alt"} <= config.keys():
        config["target_change"] = f"{config.pop('rna_ref')}>{config.pop('rna_alt')}"
    control = str(config["control_condition"])
    treatment = str(config["treatment_condition"])
    background = config.get("background_condition")
    if control == treatment:
        raise ValueError("Paired-CMH control and treatment conditions must differ")
    if background in {control, treatment}:
        raise ValueError(
            "Paired-CMH background condition must differ from primary conditions"
        )
    rna_ref, rna_alt = str(config["target_change"]).split(">")
    if rna_ref == rna_alt:
        raise ValueError("Paired-CMH target bases must differ")
    conditions = {str(row["condition"]) for row in context.samples}
    required_conditions = {control, treatment}
    if background is not None:
        required_conditions.add(str(background))
    if not required_conditions <= conditions:
        raise ValueError(
            "Analysis policy conditions must exist in the admitted samples"
        )
    try:
        step09.paired_samples(context.samples, control, treatment)
    except step09.ContractError as exc:
        raise ValueError(str(exc)) from exc
    return {
        "control_condition": control,
        "treatment_condition": treatment,
        "background_condition": background,
        "rna_ref": rna_ref,
        "rna_alt": rna_alt,
        **{key: config[key] for key in _CONFIG_FIELDS[3:]},
    }


def _result(
    step: str,
    directory: str,
    name: str,
    kind: str,
    header: tuple[str, ...] | None = None,
    rows: int | None = None,
) -> module_api.AnalysisArtifactV1:
    extension = "pdf" if kind == "pdf" else "tsv"
    filename = name.removesuffix(f"_{extension}")
    return module_api.AnalysisArtifactV1(
        artifact_name=name,
        adapter=f"step{step}_{name}_v1",
        source_path_template=(
            f"results/{directory}/{{analysis_id}}/"
            f"{{analysis_id}}.{filename}.{extension}"
        ),
        kind=kind,
        expected_header=header,
        exact_data_rows=rows,
        allow_header_only=rows is None,
    )


_STEP09_RESULTS = (
    (
        "cmh_all_sites",
        "sample_blocks_tsv",
        step09.STEP09_RESULT_HEADER,
        None,
        "all-sites",
    ),
    (
        "cmh_significant_sites",
        "sample_blocks_tsv",
        step09.STEP09_RESULT_HEADER,
        None,
        "significant-sites",
    ),
    ("cmh_summary", "tsv", step09.STEP09_SUMMARY_HEADER, 1, "summary"),
    (
        "mutation_spectrum_tsv",
        "tsv",
        step09.STEP09_MUTATION_HEADER,
        None,
        "mutation-spectrum",
    ),
    ("mutation_spectrum_pdf", "pdf", None, None, "mutation-spectrum-pdf"),
    ("depth_delta_pdf", "pdf", None, None, "depth-delta-pdf"),
)
_STEP09_OUTPUTS = tuple(
    _result("09", "editing", name, kind, header, rows)
    for name, kind, header, rows, _flag in _STEP09_RESULTS
) + (
    module_api.AnalysisArtifactV1(
        "cmh_validation",
        "step09_validation_report_v1",
        "products/native/qc/validation/09/{analysis_id}.validation.tsv",
        "validation_report",
        expected_header=module_api.VALIDATION_REPORT_HEADER,
        exact_data_rows=len(step09_validator.CHECK_IDS),
        allow_header_only=False,
    ),
)
_STEP10_RESULTS = (
    ("candidate_context", scientific_context.CANDIDATE_CONTEXT_HEADER, None),
    ("motif_hits", scientific_context.MOTIF_HITS_HEADER, None),
    ("sequence_logo", scientific_context.SEQUENCE_LOGO_HEADER, None),
    ("motif_statistics", scientific_context.MOTIF_STATISTICS_HEADER, None),
    ("context_receipt", scientific_context.SCIENTIFIC_CONTEXT_RECEIPT_HEADER, 1),
)
_STEP10_OUTPUTS = tuple(
    _result("10", "scientific_context", name, kind, header, rows)
    for name, header, rows in _STEP10_RESULTS
    for kind in ("tsv",)
) + (
    module_api.AnalysisArtifactV1(
        "context_validation",
        "step10_validation_report_v1",
        "products/native/qc/validation/10/{analysis_id}.validation.tsv",
        "validation_report",
        expected_header=module_api.VALIDATION_REPORT_HEADER,
        exact_data_rows=len(scientific_context.VALIDATION_CHECK_IDS),
        allow_header_only=False,
    ),
)

_STEP10_ROOT = Path(__file__).resolve().parents[1] / "scientific_context_projection"
_STEP09_R_SCRIPT = Path(__file__).with_name("step_09_cmh_editing_site_calling.R")
_STEP10_R_SCRIPT = _STEP10_ROOT / "scientific_context_projection.R"


def _flags(values: Iterable[tuple[str, object]]) -> tuple[str, ...]:
    return tuple(
        str(item) for name, value in values for item in (f"--{name}", value)
    )


def _step09(context: module_api.TaskPlanningContextV1) -> module_api.TaskCommandPlanV1:
    config = module_api.effective_configuration(context.configuration)
    sites = context.artifact_path("08", context.cohort_id, "step08_sites_v1")
    inputs = context.artifact_path("08", context.cohort_id, "step08_inputs_v1")
    summary08 = context.artifact_path("08", context.cohort_id, "step08_summary_v1")
    outputs = {
        name: context.output_path(f"step09_{name}_v1")
        for name, *_rest in _STEP09_RESULTS
    }
    arguments = (
        *_flags(
            (
                ("analysis-id", context.analysis_id),
                ("cohort-id", context.cohort_id),
                ("sample-manifest", context.sample_manifest),
                ("partition-manifest", context.partition_manifest),
                ("step08-root", sites.parents[1]),
                ("output-root", outputs["cmh_all_sites"].parents[1]),
            )
        ),
        *_flags(
            (name, config[name.replace("-", "_")])
            for name in step09_producer.DEFAULTS
            if name != "background-condition"
        ),
        "--rscript-bin",
        context.runtime_path("rscript"),
        "--r-script",
        str(_STEP09_R_SCRIPT),
        "--no-clobber",
        "--execute",
    )
    if config["background_condition"] is not None:
        arguments += ("--background-condition", str(config["background_condition"]))
    producer = context.r_owner_command(
        context.python_command(
            (
                "-m",
                "emrys.analyses.paired_cmh_candidate_ranking.producer",
                *arguments,
            )
        )
    )
    validator = context.validator_command(
        (
            "paired-cmh-candidate-ranking",
            *_flags(
                (
                    ("analysis-id", context.analysis_id),
                    ("cohort-id", context.cohort_id),
                    ("sample-manifest", context.sample_manifest),
                    ("partition-manifest", context.partition_manifest),
                    ("step08-sites", sites),
                    ("step08-inputs", inputs),
                    *(
                        (flag, outputs[name])
                        for name, _kind, _header, _rows, flag in _STEP09_RESULTS
                    ),
                    (
                        "output",
                        context.output_path("step09_validation_report_v1"),
                    ),
                )
            ),
        )
    )
    return module_api.TaskCommandPlanV1(
        producer,
        validator,
        (context.sample_manifest, context.partition_manifest, sites, inputs, summary08),
    )


def _step10(context: module_api.TaskPlanningContextV1) -> module_api.TaskCommandPlanV1:
    all_sites = context.artifact_path(
        "09", context.analysis_id, "step09_cmh_all_sites_v1"
    )
    significant = context.artifact_path(
        "09", context.analysis_id, "step09_cmh_significant_sites_v1"
    )
    summary = context.artifact_path("09", context.analysis_id, "step09_cmh_summary_v1")
    fai = context.artifact_path("00c", context.reference_id, "step00c_reference_fai_v1")
    motif_catalog = _STEP10_ROOT / "resources/pum_motifs_v1.tsv"
    candidate_context = context.output_path("step10_candidate_context_v1")
    arguments = (
        *_flags(
            (
                ("analysis-id", context.analysis_id),
                ("step09-all-sites", all_sites),
                ("step09-significant-sites", significant),
                ("step09-summary", summary),
                ("reference-fasta", context.reference_fasta),
                ("reference-fai", fai),
                ("output-root", candidate_context.parents[1]),
            )
        ),
        "--rscript-bin",
        context.runtime_path("rscript"),
        "--r-script",
        str(_STEP10_R_SCRIPT),
        "--no-clobber",
        "--execute",
    )
    producer = context.r_owner_command(
        (
            context.runtime_path("bash"),
            str(_STEP10_ROOT / "scientific_context_projection.sh"),
            *arguments,
        )
    )
    validator = context.validator_command(
        (
            "scientific-context-projection",
            "--receipt",
            str(context.output_path("step10_context_receipt_v1")),
            "--output",
            str(context.output_path("step10_validation_report_v1")),
        )
    )
    return module_api.TaskCommandPlanV1(
        producer,
        validator,
        (all_sites, significant, summary, context.reference_fasta, fai, motif_catalog),
    )


def _input(
    producer: str,
    artifact: str,
    adapters: tuple[str, ...],
    semantics: str = "required artifact",
) -> module_api.AnalysisInputV1:
    return module_api.AnalysisInputV1(producer, artifact, semantics, adapters)


def _render_scientific_report(
    context: module_api.AnalysisReportContextV1,
) -> module_api.AnalysisScientificReportV1:
    """Delegate to the existing paired-CMH-specific report owner."""

    from emrys.reporting._run_report.context import (  # noqa: PLC0415
        render_paired_scientific_report,
    )

    return render_paired_scientific_report(context)


_DESCRIPTOR = module_api.AnalysisModuleDescriptorV1(
    module_id=module_api.BUILTIN_PAIRED_CMH_MODULE_ID,
    module_version="v1",
    config_schema=_CONFIG_SCHEMA,
    normalize_config=_normalize_config,
    tasks=(
        module_api.AnalysisTaskV1(
            _STEP09_OWNER,
            "rank_cohort_candidates_with_paired_CMH",
            "09",
            1024,
            (
                _input(
                    "emrys.stage.preprocess_and_annotate_cohort_candidates.v1",
                    "sites table and Step 08 input receipt",
                    ("step08_sites_v1", "step08_inputs_v1", "step08_summary_v1"),
                ),
            ),
            _STEP09_OUTPUTS,
            _step09,
        ),
        module_api.AnalysisTaskV1(
            _STEP10_OWNER,
            "project_candidate_scientific_context",
            "10",
            1024,
            (
                _input(
                    _STEP09_OWNER,
                    "all-sites, significant-sites, and summary tables",
                    (
                        "step09_cmh_all_sites_v1",
                        "step09_cmh_significant_sites_v1",
                        "step09_cmh_summary_v1",
                    ),
                    "required artifact; complete Step 09 transaction barrier",
                ),
                _input(
                    "emrys.stage.construct_FASTA_sidecars.v1",
                    "reference FAI paired with the external reference FASTA",
                    ("step00c_reference_fai_v1",),
                    "required artifact; fan-in",
                ),
            ),
            _STEP10_OUTPUTS,
            _step10,
        ),
    ),
    render_scientific_report=_render_scientific_report,
    implementation_package="emrys.analyses.paired_cmh_candidate_ranking",
    required_runtime_checks=(
        "bash",
        "python",
        "r_biostrings",
        "r_genomic_ranges",
        "r_iranges",
        "r_rsamtools",
        "renv_library",
        "renv_project",
        "rscript",
        "sha256_python",
    ),
)


def analysis_module_v1() -> module_api.AnalysisModuleDescriptorV1:
    """Return the built-in paired-CMH module descriptor."""

    return _DESCRIPTOR
