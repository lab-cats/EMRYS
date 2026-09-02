"""Built-in paired-CMH computation-provider declaration."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

from emrys import analyses as module_api
from emrys.analyses.paired_cmh_candidate_ranking import producer as step09_producer
from emrys.analyses.paired_cmh_candidate_ranking import validator as step09_validator
from emrys.analyses.paired_cmh_candidate_ranking.scientific_context_projection import (
    validator as step10_validator,
)
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
        "background_max_fraction": _number(
            exclusiveMinimum=0, exclusiveMaximum=1
        ),
    },
}


def _normalize_config(
    config: Mapping[str, object], context: module_api.AnalysisInputContextV1
) -> dict[str, object]:
    config = dict(config)
    if "target_change" not in config:
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
    required = {control, treatment}
    if background is not None:
        required.add(str(background))
    if not required <= conditions:
        raise ValueError("Analysis policy conditions must exist in admitted samples")
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
    directory: str | None,
    name: str,
    kind: str,
    header: tuple[str, ...] | None = None,
    rows: int | None = None,
    *,
    adapter: str | None = None,
) -> module_api.AnalysisArtifactV1:
    extension = "pdf" if kind == "pdf" else "tsv"
    stem = name.removesuffix(f"_{extension}")
    source = (
        f"products/native/qc/validation/{step}/{{analysis_id}}.validation.tsv"
        if kind == "validation_report"
        else f"results/{directory}/{{analysis_id}}/{{analysis_id}}.{stem}.{extension}"
    )
    return module_api.AnalysisArtifactV1(
        artifact_name=name,
        adapter=adapter or f"step{step}_{name}_v1",
        source_path_template=source,
        kind=kind,
        expected_header=header,
        exact_data_rows=rows,
        allow_header_only=rows is None,
    )


_STEP09_RESULTS = (
    ("cmh_all_sites", "sample_blocks_tsv", step09.STEP09_RESULT_HEADER, None),
    (
        "cmh_significant_sites",
        "sample_blocks_tsv",
        step09.STEP09_RESULT_HEADER,
        None,
    ),
    ("cmh_summary", "tsv", step09.STEP09_SUMMARY_HEADER, 1),
    ("mutation_spectrum_tsv", "tsv", step09.STEP09_MUTATION_HEADER, None),
    ("mutation_spectrum_pdf", "pdf", None, None),
    ("depth_delta_pdf", "pdf", None, None),
)
_STEP09_OUTPUTS = tuple(
    _result("09", "editing", name, kind, header, rows)
    for name, kind, header, rows in _STEP09_RESULTS
) + (
    _result(
        "09",
        None,
        "cmh_validation",
        "validation_report",
        module_api.VALIDATION_REPORT_HEADER,
        len(step09_validator.CHECK_IDS),
        adapter="step09_validation_report_v1",
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
    _result("10", "scientific_context", name, "tsv", header, rows)
    for name, header, rows in _STEP10_RESULTS
) + (
    _result(
        "10",
        None,
        "context_validation",
        "validation_report",
        module_api.VALIDATION_REPORT_HEADER,
        len(step10_validator.CHECK_IDS),
        adapter="step10_validation_report_v1",
    ),
)

_STEP10_ROOT = Path(__file__).with_name("scientific_context_projection")
_STEP09_R_SCRIPT = Path(__file__).with_name("step_09_cmh_editing_site_calling.R")


def _flags(values: Iterable[tuple[str, object]]) -> tuple[str, ...]:
    return tuple(str(item) for name, value in values for item in (f"--{name}", value))


def _one(context: module_api.TaskPlanningContextV1, adapter: str) -> Path:
    paths = context.inputs.get(adapter, ())
    if len(paths) != 1:
        raise module_api.AnalysisTaskPlanningError(
            f"Expected one admitted {adapter} input; observed {len(paths)}"
        )
    return paths[0]


def _step09(context: module_api.TaskPlanningContextV1) -> module_api.TaskCommandPlanV1:
    sites = _one(context, "step08_sites_v1")
    inputs = _one(context, "step08_inputs_v1")
    summary08 = _one(context, "step08_summary_v1")
    outputs = context.outputs
    arguments = (
        *_flags(
            (
                ("analysis-id", context.analysis_id),
                ("cohort-id", context.cohort_id),
                ("sample-manifest", context.sample_manifest),
                ("partition-manifest", context.partition_manifest),
                ("step08-root", sites.parents[1]),
                ("output-root", outputs["step09_cmh_all_sites_v1"].parents[1]),
            )
        ),
        *_flags(
            (name, context.configuration[name.replace("-", "_")])
            for name in step09_producer.DEFAULTS
            if name != "background-condition"
        ),
        "--rscript-bin",
        context.runtime_paths["rscript"],
        "--r-script",
        str(_STEP09_R_SCRIPT),
        "--no-clobber",
        "--execute",
    )
    background = context.configuration["background_condition"]
    if background is not None:
        arguments += ("--background-condition", str(background))
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
                    ("all-sites", outputs["step09_cmh_all_sites_v1"]),
                    (
                        "significant-sites",
                        outputs["step09_cmh_significant_sites_v1"],
                    ),
                    ("summary", outputs["step09_cmh_summary_v1"]),
                    (
                        "mutation-spectrum",
                        outputs["step09_mutation_spectrum_tsv_v1"],
                    ),
                    (
                        "mutation-spectrum-pdf",
                        outputs["step09_mutation_spectrum_pdf_v1"],
                    ),
                    ("depth-delta-pdf", outputs["step09_depth_delta_pdf_v1"]),
                    ("output", outputs["step09_validation_report_v1"]),
                )
            ),
        )
    )
    return module_api.TaskCommandPlanV1(
        producer_argv=producer,
        validator_argv=validator,
        inputs=(
            module_api.TaskInputV1("sample_manifest", context.sample_manifest),
            module_api.TaskInputV1(
                "partition_manifest", context.partition_manifest
            ),
            module_api.TaskInputV1("step08_sites_v1", sites),
            module_api.TaskInputV1("step08_inputs_v1", inputs),
            module_api.TaskInputV1("step08_summary_v1", summary08),
        ),
    )


def _step10(context: module_api.TaskPlanningContextV1) -> module_api.TaskCommandPlanV1:
    all_sites = _one(context, "step09_cmh_all_sites_v1")
    significant = _one(context, "step09_cmh_significant_sites_v1")
    summary = _one(context, "step09_cmh_summary_v1")
    fai = _one(context, "step00c_reference_fai_v1")
    motif_catalog = _STEP10_ROOT / "resources/pum_motifs_v1.tsv"
    outputs = context.outputs
    arguments = (
        *_flags(
            (
                ("analysis-id", context.analysis_id),
                ("step09-all-sites", all_sites),
                ("step09-significant-sites", significant),
                ("step09-summary", summary),
                ("reference-fasta", context.reference_fasta),
                ("reference-fai", fai),
                ("output-root", outputs["step10_candidate_context_v1"].parents[1]),
                ("motif-catalog", motif_catalog),
                ("git-commit", context.source_commit),
            )
        ),
        "--rscript-bin",
        context.runtime_paths["rscript"],
        "--r-script",
        str(_STEP10_ROOT / "scientific_context_projection.R"),
        "--no-clobber",
        "--execute",
    )
    producer = context.r_owner_command(
        (
            context.runtime_paths["bash"],
            str(_STEP10_ROOT / "scientific_context_projection.sh"),
            *arguments,
        )
    )
    validator = context.validator_command(
        (
            "scientific-context-projection",
            "--receipt",
            str(outputs["step10_context_receipt_v1"]),
            "--output",
            str(outputs["step10_validation_report_v1"]),
        )
    )
    return module_api.TaskCommandPlanV1(
        producer_argv=producer,
        validator_argv=validator,
        inputs=(
            module_api.TaskInputV1("step09_cmh_all_sites_v1", all_sites),
            module_api.TaskInputV1(
                "step09_cmh_significant_sites_v1", significant
            ),
            module_api.TaskInputV1("step09_cmh_summary_v1", summary),
            module_api.TaskInputV1("reference_fasta", context.reference_fasta),
            module_api.TaskInputV1("step00c_reference_fai_v1", fai),
            module_api.TaskInputV1("motif_catalog", motif_catalog),
        ),
    )


_DESCRIPTOR = module_api.AnalysisModuleDescriptorV1(
    module_id=module_api.BUILTIN_PAIRED_CMH_MODULE_ID,
    module_version="v1",
    config_schema=_CONFIG_SCHEMA,
    normalize_config=_normalize_config,
    tasks=(
        module_api.AnalysisTaskV1(
            owner_key=_STEP09_OWNER,
            step_id="09",
            stage_memory_mb=1024,
            inputs=(
                module_api.AnalysisInputV1(
                    "emrys.stage.preprocess_and_annotate_cohort_candidates.v1",
                    ("step08_sites_v1", "step08_inputs_v1", "step08_summary_v1"),
                ),
            ),
            outputs=_STEP09_OUTPUTS,
            plan=_step09,
        ),
        module_api.AnalysisTaskV1(
            owner_key=_STEP10_OWNER,
            step_id="10",
            stage_memory_mb=1024,
            inputs=(
                module_api.AnalysisInputV1(
                    _STEP09_OWNER,
                    (
                        "step09_cmh_all_sites_v1",
                        "step09_cmh_significant_sites_v1",
                        "step09_cmh_summary_v1",
                    ),
                    "required artifact; complete Step 09 transaction barrier",
                ),
                module_api.AnalysisInputV1(
                    "emrys.stage.construct_FASTA_sidecars.v1",
                    ("step00c_reference_fai_v1",),
                    "required artifact; fan-in",
                ),
            ),
            outputs=_STEP10_OUTPUTS,
            plan=_step10,
        ),
    ),
    dependencies=(
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


__all__ = ("analysis_module_v1",)
