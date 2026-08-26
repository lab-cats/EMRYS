"""Fast contract tests for the retained performance benchmark helper."""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests/tools/retained_stage_benchmark.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("retained_stage_benchmark", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BENCHMARK = _load_script()


def _artifact(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": str(path),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _retained_artifact(path: Path) -> object:
    state = path.stat(follow_symlinks=False)
    return BENCHMARK.RetainedArtifact(
        path,
        state.st_size,
        hashlib.sha256(path.read_bytes()).hexdigest(),
        state.st_dev,
        state.st_ino,
        state.st_mtime_ns,
    )


def _publish_verified_owner(
    path: Path,
    machine_key: str,
    outputs: list[dict[str, object]],
    *,
    inputs: list[dict[str, object]] | None = None,
    producer_argv: list[str] | None = None,
) -> dict[str, object]:
    provenance = []
    for role in BENCHMARK.STANDARD_TASK_INPUT_ROLES:
        artifact = path.with_name(f"{role}.json")
        artifact.write_text(role + "\n")
        provenance.append({"role": role, **_artifact(artifact)})
    path.write_text(
        json.dumps(
            {
                "schema_version": "emrys.verified-task.v1",
                "machine_key": machine_key,
                "scope": {
                    "scope_type": "sample",
                    "scope_id": BENCHMARK.RETAINED_SAMPLE_ID,
                },
                "stable_inputs_rechecked": True,
                "all_pass": True,
                "owner_run_token": "owner-" + "6" * 32,
                "commands": {
                    "producer": {
                        # The retained E2E chose two threads. Benchmark trials
                        # independently exercise their case-declared count.
                        "argv": producer_argv or ["owner", "--threads", "2"],
                        "exit_code": 0,
                    }
                },
                "inputs": [*provenance, *(inputs or [])],
                "outputs": outputs,
            }
        )
    )
    return {
        "machine_key": machine_key,
        "scope_type": "sample",
        "scope_id": BENCHMARK.RETAINED_SAMPLE_ID,
        **_artifact(path),
    }


def _step02_validator_fixture(
    root: Path,
) -> tuple[dict[str, object], Path, Path, Path, Path]:
    trial = root / "trial"
    output = trial / "output"
    (trial / "qc").mkdir(parents=True)
    output.mkdir()
    retained = root / "retained"
    retained.mkdir()
    sample = BENCHMARK.RETAINED_SAMPLE_ID
    input_bam = retained / "step01.bam"
    retained_bam = retained / "step02.bam"
    retained_bai = retained / "step02.bam.bai"
    input_bam.write_bytes(b"bam-bytes")
    retained_bam.hardlink_to(input_bam)
    retained_bai.write_bytes(b"bai-bytes")
    bam = output / f"{sample}.sorted.bam"
    bai = output / f"{sample}.sorted.bam.bai"
    bam.hardlink_to(input_bam)
    bai.write_bytes(retained_bai.read_bytes())
    samtools = root / "runtime/bin/samtools"
    samtools.parent.mkdir(parents=True)
    samtools.write_text("#!/bin/sh\n")
    samtools.chmod(0o755)
    context = {
        "sample_id": sample,
        "python": "/repo/.venv/bin/python",
        "runtime_prefix": str(samtools.parents[1]),
        "retained_step01_bam": BENCHMARK._artifact_context(
            _retained_artifact(input_bam)
        ),
        "retained_step02_bam": BENCHMARK._artifact_context(
            _retained_artifact(retained_bam)
        ),
        "retained_step02_bai": BENCHMARK._artifact_context(
            _retained_artifact(retained_bai)
        ),
    }
    return context, trial, bam, bai, samtools


def _run_step02_validator(
    context: dict[str, object], trial: Path, samtools: Path
) -> tuple[list[tuple[str, ...]], bytes]:
    calls: list[tuple[str, ...]] = []
    idxstats = b"chrSynthetic\t5000000\t2\t0\n"
    with (
        mock.patch.object(
            BENCHMARK,
            "_run_checked",
            side_effect=lambda argv, **_kwargs: calls.append(tuple(argv)),
        ),
        mock.patch.object(
            BENCHMARK.subprocess,
            "run",
            return_value=subprocess.CompletedProcess(
                [str(samtools), "idxstats"], 0, idxstats, b""
            ),
        ),
    ):
        BENCHMARK._validate_step02(context, trial)
    return calls, idxstats


def _step04_validator_fixture(root: Path) -> dict[str, object]:
    sample = BENCHMARK.RETAINED_SAMPLE_ID
    run_root, trial = root / "run", root / "trial"
    input_bam = run_root / "results/bam" / sample / f"{sample}.sorted.bam"
    input_bam.parent.mkdir(parents=True)
    input_bam.write_bytes(b"input")
    input_bai = Path(f"{input_bam}.bai")
    input_bai.write_bytes(b"index")
    retained_bam = run_root / "results/markdup" / sample / f"{sample}.markdup.bam"
    retained_bam.parent.mkdir(parents=True)
    retained_bam.write_bytes(b"retained")
    retained_bai = Path(f"{retained_bam}.bai")
    retained_bai.write_bytes(b"index")
    retained_metrics = run_root / "results/qc/markdup" / f"{sample}.markdup.metrics.txt"
    retained_metrics.parent.mkdir(parents=True)
    trial.mkdir()
    paths = BENCHMARK._step04_paths(sample)
    for key in ("output_root", "metrics_root", "scratch"):
        (trial / paths[key]).mkdir(parents=True)
    (trial / paths["report"]).parent.mkdir(parents=True)
    outputs = {key: trial / paths[key] for key in ("bam", "bai", "metrics")}
    outputs["bam"].write_bytes(b"observed")
    outputs["bai"].write_bytes(b"index")
    retained_token = "owner-" + "4" * 32
    observed_tmp = trial / paths["scratch"]
    reference_tmp = root / "retained-scratch"
    input_records = (
        b"r1\t99\tchrSynthetic\t1\t60\t1M\t=\t2\t1\tA\tI\tPG:Z:samtools\n"
        b"r1\t147\tchrSynthetic\t2\t60\t1M\t=\t1\t-1\tT\tI\tPG:Z:samtools\n"
    )
    output_records = input_records.replace(b"\t99\t", b"\t1123\t").replace(
        b"\t147\t", b"\t1171\t"
    ).replace(b"PG:Z:samtools", b"PG:Z:MarkDuplicates")

    def command(prefix: str, token: str, tmp: Path) -> str:
        base = (
            f"MarkDuplicates INPUT={run_root}/results/bam/{sample}/{sample}.sorted.bam "
            f"OUTPUT={prefix}results/markdup/{sample}/.{sample}.step04.{token}.markdup.tmp.bam "
            f"METRICS_FILE={prefix}results/qc/markdup/.{sample}.step04.{token}.metrics.tmp "
            f"REMOVE_DUPLICATES=false TMP_DIR={tmp}"
        )
        if prefix:
            return f"{base} CREATE_INDEX=true MAX_RECORDS_IN_RAM=500000 CREATE_MD5_FILE=false"
        return f"{base} MAX_RECORDS_IN_RAM=500000 CREATE_INDEX=false CREATE_MD5_FILE=false"

    body = (
        "## METRICS CLASS picard.sam.DuplicationMetrics\n"
        "LIBRARY\tUNPAIRED_READS_EXAMINED\tREAD_PAIRS_EXAMINED\t"
        "SECONDARY_OR_SUPPLEMENTARY_RDS\tUNMAPPED_READS\t"
        "UNPAIRED_READ_DUPLICATES\tREAD_PAIR_DUPLICATES\tPERCENT_DUPLICATION\n"
        f"{sample}\t0\t1\t0\t0\t0\t1\t1\n\n"
        "## HISTOGRAM java.lang.Double\nset_size\tall_sets\n1.0\t1\n"
    ).encode()

    def metrics(prefix: str, token: str, tmp: Path, stamp: str) -> bytes:
        return (
            "## htsjdk.samtools.metrics.StringHeader\n# "
            + command(prefix, token, tmp)
            + f"\n## htsjdk.samtools.metrics.StringHeader\n# Started on: {stamp}\n\n"
        ).encode() + body

    outputs["metrics"].write_bytes(
        metrics("", BENCHMARK.STEP04_TRIAL_RUN_TOKEN, observed_tmp, "observed")
    )
    retained_metrics.write_bytes(metrics(f"{run_root}/", retained_token, reference_tmp, "reference"))
    base_header = b"@HD\tVN:1.6\tSO:coordinate\n@SQ\tSN:chrSynthetic\tLN:5000000\n"
    inspections = {}
    for bam, prefix, token, tmp in (
        (outputs["bam"], "", BENCHMARK.STEP04_TRIAL_RUN_TOKEN, observed_tmp),
        (retained_bam, f"{run_root}/", retained_token, reference_tmp),
    ):
        header = base_header + (f"@PG\tID:MarkDuplicates\tPN:MarkDuplicates\tCL:{command(prefix, token, tmp)}\n").encode()
        inspections[bam] = {
            "header": header, "decoded": output_records,
            "records": BENCHMARK._sam_records(output_records, "fixture"),
            "idxstats": b"chrSynthetic\t5000000\t2\t0\n*\t0\t0\t0\n",
            "indexed": output_records,
        }
    samtools = root / "samtools"
    samtools.write_text("#!/bin/sh\n")
    samtools.chmod(0o755)
    context = {
        "sample_id": sample, "python": sys.executable, "run_root": str(run_root),
        "runtime_samtools": str(samtools),
        "runtime_sha256_python": sys.executable,
        "retained_step02_bam": BENCHMARK._artifact_context(_retained_artifact(input_bam)),
        "retained_step02_bai": BENCHMARK._artifact_context(_retained_artifact(input_bai)),
        "retained_step04_bam": BENCHMARK._artifact_context(_retained_artifact(retained_bam)),
        "retained_step04_bai": BENCHMARK._artifact_context(_retained_artifact(retained_bai)),
        "retained_step04_metrics": BENCHMARK._artifact_context(_retained_artifact(retained_metrics)),
        "retained_step04_run_token": retained_token,
    }
    return {"context": context, "trial": trial, "outputs": outputs, "input": input_records, "inspections": inspections}


def _step05_validator_fixture(root: Path) -> dict[str, object]:
    sample = BENCHMARK.RETAINED_SAMPLE_ID
    run, trial = root / "run", root / "trial"
    input_bam = run / "results/markdup" / sample / f"{sample}.markdup.bam"
    retained_bam = run / "results/split_ncigar" / sample / f"{sample}.split_ncigar.bam"
    for selected, data in ((input_bam, b"input"), (retained_bam, b"retained")):
        selected.parent.mkdir(parents=True)
        selected.write_bytes(data)
        Path(f"{selected}.bai").write_bytes(b"retained-index")
    reference = root / "reference.fa"
    reference.write_bytes(b">chrSynthetic\nA\n")
    reference_fai = Path(f"{reference}.fai")
    reference_fai.write_bytes(b"chrSynthetic\t5000000\t0\t1\t2\n")
    reference_dict = root / "reference.dict"
    reference_dict.write_bytes(b"@SQ\tSN:chrSynthetic\tLN:5000000\n")
    trial.mkdir()
    paths = BENCHMARK._step05_paths(sample)
    (trial / paths["output_root"]).mkdir(parents=True)
    (trial / paths["report"]).parent.mkdir(parents=True)
    outputs = {key: trial / paths[key] for key in ("bam", "bai")}
    outputs["bam"].write_bytes(b"observed")
    outputs["bai"].write_bytes(b"native-index-differs")
    input_records = (
        f"r1\t99\tchrSynthetic\t1\t60\t5M10N5M\t=\t20\t0\tAAAAAAAAAA\tIIIIIIIIII\tRG:Z:{sample}\tPG:Z:MarkDuplicates\n"
    ).encode()
    output_records = (
        f"r1\t99\tchrSynthetic\t1\t60\t5M\t=\t20\t0\tAAAAA\tIIIII\tRG:Z:{sample}\tPG:Z:MarkDuplicates\n"
        f"r1\t2147\tchrSynthetic\t16\t60\t5M\t=\t20\t0\tAAAAA\tIIIII\tRG:Z:{sample}\tPG:Z:MarkDuplicates\n"
    ).encode()
    base = b"@HD\tVN:1.6\tSO:coordinate\n@SQ\tSN:chrSynthetic\tLN:5000000\n@PG\tID:MarkDuplicates\tPN:MarkDuplicates\n"
    retained_token = "owner-" + "5" * 32
    gatk_program = (
        f"@PG\tID:GATK SplitNCigarReads\tPN:GATK SplitNCigarReads\tPP:MarkDuplicates\t"
        f"CL:SplitNCigarReads -O results/split_ncigar/{sample}/.{sample}.step05."
        f"{BENCHMARK.STEP05_TRIAL_RUN_TOKEN}.split_ncigar.tmp.bam\n"
    ).encode()
    observed_header = base + gatk_program + gatk_program.replace(
        b"ID:GATK SplitNCigarReads\t", b"ID:GATK SplitNCigarReads.1\t"
    )
    retained_header = observed_header.replace(
        f"results/split_ncigar/{sample}".encode(),
        f"{run}/results/split_ncigar/{sample}".encode(),
    ).replace(BENCHMARK.STEP05_TRIAL_RUN_TOKEN.encode(), retained_token.encode())
    def inspection(header: bytes, records: bytes, count: int) -> dict[str, object]:
        return {
            "header": header, "decoded": records,
            "records": BENCHMARK._sam_records(records, "fixture"),
            "idxstats": f"chrSynthetic\t5000000\t{count}\t0\n*\t0\t0\t0\n".encode(),
            "indexed": records,
        }
    inspections = {
        input_bam: inspection(base, input_records, 1),
        outputs["bam"]: inspection(observed_header, output_records, 2),
        retained_bam: inspection(retained_header, output_records, 2),
    }
    samtools = root / "samtools"
    samtools.write_text("#!/bin/sh\n")
    samtools.chmod(0o755)
    artifact = BENCHMARK._artifact_context
    context = {
        "sample_id": sample, "python": sys.executable, "run_root": str(run),
        "reference_fasta": str(reference), "runtime_samtools": str(samtools),
        "runtime_bash": str(samtools), "runtime_gatk": str(samtools), "runtime_java": str(samtools),
        "runtime_sha256_python": sys.executable,
        "retained_step04_bam": artifact(_retained_artifact(input_bam)),
        "retained_step04_bai": artifact(_retained_artifact(Path(f"{input_bam}.bai"))),
        "retained_step05_bam": artifact(_retained_artifact(retained_bam)),
        "retained_step05_bai": artifact(_retained_artifact(Path(f"{retained_bam}.bai"))),
        "retained_reference_fasta": artifact(_retained_artifact(reference)),
        "retained_reference_fai": artifact(_retained_artifact(reference_fai)),
        "retained_reference_dict": artifact(_retained_artifact(reference_dict)),
        "retained_step05_run_token": retained_token,
    }
    return {"context": context, "trial": trial, "outputs": outputs, "inspections": inspections}


def _step06_validator_fixture(root: Path) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    sample = BENCHMARK.RETAINED_SAMPLE_ID
    run_root = root / "retained-run"
    run_root.mkdir()
    step05_bam = (
        run_root
        / "results/split_ncigar"
        / sample
        / f"{sample}.split_ncigar.bam"
    )
    step05_bam.parent.mkdir(parents=True)
    step05_bam.write_bytes(b"step05-bam")
    step05_bai = Path(f"{step05_bam}.bai")
    step05_bai.write_bytes(b"step05-bai")
    retained_fwd = (
        run_root / "results/orientation" / sample / f"{sample}.FWD_like.bam"
    )
    retained_fwd.parent.mkdir(parents=True)
    retained_fwd.write_bytes(b"retained-fwd-bam")
    retained_fwd_bai = Path(f"{retained_fwd}.bai")
    retained_fwd_bai.write_bytes(b"retained-fwd-bai")
    retained_rev = retained_fwd.with_name(f"{sample}.REV_like.bam")
    retained_rev.write_bytes(b"retained-rev-bam")
    retained_rev_bai = Path(f"{retained_rev}.bai")
    retained_rev_bai.write_bytes(b"retained-rev-bai")
    counts_data = (
        b"sample_id\tinput_records\tflag_99_records\tflag_147_records\t"
        b"flag_83_records\tflag_163_records\tfwd_like_records\t"
        b"rev_like_records\tassigned_records\tunassigned_records\t"
        b"assigned_fraction\n"
        + sample.encode()
        + b"\t5\t1\t1\t1\t1\t2\t2\t4\t1\t0.800000\n"
    )
    retained_counts = (
        run_root / "results/qc/orientation" / f"{sample}.orientation_counts.tsv"
    )
    retained_counts.parent.mkdir(parents=True)
    retained_counts.write_bytes(counts_data)

    trial = root / "trial"
    trial.mkdir()
    relative = BENCHMARK._step06_paths(sample)
    for key in ("orientation_root", "counts_root"):
        (trial / relative[key]).mkdir(parents=True)
    (trial / relative["report"]).parent.mkdir(parents=True)
    outputs = {
        key: trial / relative[key]
        for key in ("fwd_bam", "fwd_bai", "rev_bam", "rev_bai", "counts")
    }
    for key, path in outputs.items():
        path.write_bytes(counts_data if key == "counts" else f"trial-{key}".encode())

    runtime = root / "runtime"
    samtools = runtime / "bin/samtools"
    samtools.parent.mkdir(parents=True)
    samtools.write_text("#!/bin/sh\n")
    samtools.chmod(0o755)
    input_records = (
        f"r99\t99\tchrSynthetic\t1\t60\t1M\t=\t1\t0\tA\tI\t"
        f"RG:Z:{sample}\tPG:Z:MarkDuplicates\n"
        f"r147\t147\tchrSynthetic\t2\t60\t1M\t=\t2\t0\tC\tI\t"
        f"RG:Z:{sample}\tPG:Z:MarkDuplicates\n"
        f"r83\t83\tchrSynthetic\t3\t60\t1M\t=\t3\t0\tG\tI\t"
        f"RG:Z:{sample}\tPG:Z:MarkDuplicates\n"
        f"r163\t163\tchrSynthetic\t4\t60\t1M\t=\t4\t0\tT\tI\t"
        f"RG:Z:{sample}\tPG:Z:MarkDuplicates\n"
        f"other\t0\tchrSynthetic\t5\t60\t1M\t*\t0\t0\tA\tI\t"
        f"RG:Z:{sample}\tPG:Z:MarkDuplicates\n"
    ).encode()
    retained_token = "owner-" + "6" * 32
    observed_aliases = {
        "rg": "11111111",
        "mark_duplicates": "22222222",
        "gatk": "A918B00",
        "gatk_1": "94BE513",
        "samtools": "55555555",
    }
    retained_aliases = {
        "rg": "AAAAAAA1",
        "mark_duplicates": "AAAAAAA2",
        "gatk": "AAAAAAA3",
        "gatk_1": "AAAAAAA4",
        "samtools": "AAAAAAA5",
    }

    def grouped_records(first: int, second: int, aliases: dict[str, str]) -> bytes:
        records = input_records.splitlines(keepends=True)
        aliased = records[second].replace(
            f"RG:Z:{sample}".encode(),
            f"RG:Z:{sample}-{aliases['rg']}".encode(),
        ).replace(
            b"PG:Z:MarkDuplicates",
            f"PG:Z:MarkDuplicates-{aliases['mark_duplicates']}".encode(),
        )
        return records[first] + aliased

    def header(
        root_path: Path | None,
        token: str,
        orientation: str,
        threads: int,
        aliases: dict[str, str],
    ) -> bytes:
        prefix = f"{root_path}/" if root_path is not None else ""
        flags = (99, 147) if orientation == "FWD_like" else (83, 163)
        orientation_root = f"{prefix}results/orientation/{sample}"
        input_bam = (
            f"{run_root}/results/split_ncigar/{sample}/{sample}.split_ncigar.bam"
        )
        merge_command = (
            f"samtools merge -@ {threads} -o {orientation_root}/.{sample}.step06."
            f"{token}.{orientation}.tmp.bam {orientation_root}/.{sample}.step06."
            f"{token}.{flags[0]}.tmp.bam {orientation_root}/.{sample}.step06."
            f"{token}.{flags[1]}.tmp.bam"
        )
        return (
            b"@HD\tVN:1.6\tSO:coordinate\n"
            b"@SQ\tSN:chrSynthetic\tLN:5000000\n"
            + (
                f"@RG\tID:{sample}\tSM:{sample}\tLB:{sample}\tPL:ILLUMINA\n"
                f"@RG\tID:{sample}-{aliases['rg']}\tSM:{sample}\tLB:{sample}"
                f"\tPL:ILLUMINA\n"
                "@PG\tID:MarkDuplicates\tPN:MarkDuplicates\n"
                "@PG\tID:GATK SplitNCigarReads\tPN:GATK SplitNCigarReads"
                "\tPP:MarkDuplicates\tCL:SplitNCigarReads --input retained.bam\n"
                "@PG\tID:GATK SplitNCigarReads.1\tPN:GATK SplitNCigarReads"
                "\tPP:MarkDuplicates\tCL:SplitNCigarReads --input retained.bam\n"
                f"@PG\tID:samtools\tPN:samtools\tPP:GATK SplitNCigarReads.1"
                f"\tCL:samtools view -@ {threads} -b -f {flags[0]} -o "
                f"{orientation_root}/.{sample}.step06.{token}.{flags[0]}.tmp.bam "
                f"{input_bam}\n"
                f"@PG\tID:MarkDuplicates-{aliases['mark_duplicates']}"
                "\tPN:MarkDuplicates\n"
                f"@PG\tID:GATK SplitNCigarReads-{aliases['gatk']}"
                "\tPN:GATK SplitNCigarReads"
                f"\tPP:MarkDuplicates-{aliases['mark_duplicates']}"
                "\tCL:SplitNCigarReads --input retained.bam\n"
                f"@PG\tID:GATK SplitNCigarReads.1-{aliases['gatk_1']}"
                "\tPN:GATK SplitNCigarReads"
                f"\tPP:MarkDuplicates-{aliases['mark_duplicates']}"
                "\tCL:SplitNCigarReads --input retained.bam\n"
                f"@PG\tID:samtools-{aliases['samtools']}\tPN:samtools"
                f"\tPP:GATK SplitNCigarReads.1-{aliases['gatk_1']}"
                f"\tCL:samtools view -@ {threads} -b -f {flags[1]} -o "
                f"{orientation_root}/.{sample}.step06.{token}.{flags[1]}.tmp.bam "
                f"{input_bam}\n"
                f"@PG\tID:samtools.1\tPN:samtools\tPP:samtools\tCL:{merge_command}\n"
                f"@PG\tID:samtools.2\tPN:samtools"
                f"\tPP:samtools-{aliases['samtools']}\tCL:{merge_command}\n"
            ).encode()
        )

    observed_fwd = grouped_records(0, 1, observed_aliases)
    observed_rev = grouped_records(2, 3, observed_aliases)
    retained_fwd_records = grouped_records(0, 1, retained_aliases)
    retained_rev_records = grouped_records(2, 3, retained_aliases)
    records = {
        step05_bam: input_records,
        retained_fwd: retained_fwd_records,
        retained_rev: retained_rev_records,
        outputs["fwd_bam"]: observed_fwd,
        outputs["rev_bam"]: observed_rev,
    }
    headers = {
        retained_fwd: header(
            run_root, retained_token, "FWD_like", 2, retained_aliases
        ),
        retained_rev: header(
            run_root, retained_token, "REV_like", 2, retained_aliases
        ),
        outputs["fwd_bam"]: header(
            None,
            BENCHMARK.STEP06_TRIAL_RUN_TOKEN,
            "FWD_like",
            4,
            observed_aliases,
        ),
        outputs["rev_bam"]: header(
            None,
            BENCHMARK.STEP06_TRIAL_RUN_TOKEN,
            "REV_like",
            4,
            observed_aliases,
        ),
    }
    idxstats = {
        selected: b"chrSynthetic\t5000000\t2\t0\n*\t0\t0\t0\n"
        for selected in (retained_fwd, retained_rev, outputs["fwd_bam"], outputs["rev_bam"])
    }
    context = {
        "sample_id": sample,
        "python": sys.executable,
        "runtime_prefix": str(runtime),
        "runtime_samtools": str(samtools),
        "runtime_sha256_python": sys.executable,
        "run_root": str(run_root),
        "retained_step05_bam": BENCHMARK._artifact_context(
            _retained_artifact(step05_bam)
        ),
        "retained_step05_bai": BENCHMARK._artifact_context(
            _retained_artifact(step05_bai)
        ),
        "retained_step06_fwd_bam": BENCHMARK._artifact_context(
            _retained_artifact(retained_fwd)
        ),
        "retained_step06_fwd_bai": BENCHMARK._artifact_context(
            _retained_artifact(retained_fwd_bai)
        ),
        "retained_step06_rev_bam": BENCHMARK._artifact_context(
            _retained_artifact(retained_rev)
        ),
        "retained_step06_rev_bai": BENCHMARK._artifact_context(
            _retained_artifact(retained_rev_bai)
        ),
        "retained_step06_counts": BENCHMARK._artifact_context(
            _retained_artifact(retained_counts)
        ),
        "retained_step06_run_token": retained_token,
        "retained_step06_threads": 2,
    }
    return {
        "context": context,
        "trial": trial,
        "outputs": outputs,
        "retained": {
            "fwd_bam": retained_fwd,
            "rev_bam": retained_rev,
        },
        "samtools": samtools,
        "records": records,
        "headers": headers,
        "idxstats": idxstats,
        "indexed": dict(records),
        "observed_aliases": observed_aliases,
    }


def _run_step06_validator(fixture: dict[str, object]) -> list[tuple[str, ...]]:
    calls: list[tuple[str, ...]] = []
    records = fixture["records"]
    headers = fixture["headers"]
    idxstats = fixture["idxstats"]
    indexed = fixture["indexed"]
    assert isinstance(records, dict)
    assert isinstance(headers, dict)
    assert isinstance(idxstats, dict)
    assert isinstance(indexed, dict)

    def capture(argv: object, *, cwd: Path) -> bytes:
        del cwd
        command = tuple(argv)
        selected = Path(command[-1] if command[1:3] == ("view", "-H") else command[2])
        if command[1] == "quickcheck":
            return b""
        if command[1:3] == ("view", "-H"):
            return headers[selected]
        if command[1] == "idxstats":
            return idxstats[selected]
        if command[1] == "view" and len(command) > 3:
            return indexed[selected]
        if command[1] == "view":
            return records[selected]
        raise AssertionError(command)

    with (
        mock.patch.object(
            BENCHMARK,
            "_run_checked",
            side_effect=lambda argv, **_kwargs: calls.append(tuple(argv)),
        ),
        mock.patch.object(BENCHMARK, "_capture_checked", side_effect=capture),
    ):
        BENCHMARK._validate_step06(fixture["context"], fixture["trial"])
    return calls


class RetainedStageBenchmarkTests(unittest.TestCase):
    def test_validation_report_names_match_public_validator_contracts(self) -> None:
        self.assertEqual(
            BENCHMARK._validation_report(Path("qc"), "sample"),
            Path("qc/sample.validation.tsv"),
        )
        self.assertEqual(
            BENCHMARK._validation_report(Path("qc"), "cohort"),
            Path("qc/cohort.validation.tsv"),
        )
        self.assertEqual(
            BENCHMARK._validation_report(Path("qc"), "cohort", "p01"),
            Path("qc/cohort__p01.validation.tsv"),
        )

    def test_indexed_bam_header_inspection_suppresses_program_injection(self) -> None:
        calls: list[tuple[str, ...]] = []
        samtools = Path("/runtime/samtools")
        bam = Path("/retained/input.bam")
        decoded = b"r1\t99\tchrSynthetic\t1\t60\t1M\t=\t1\t0\tA\tI\n"

        def capture(argv: object, *, cwd: Path) -> bytes:
            self.assertEqual(cwd, Path("/trial"))
            command = tuple(argv)
            calls.append(command)
            if command[1] == "quickcheck":
                return b""
            if command[1:3] == ("view", "-H"):
                return b"@HD\tVN:1.6\tSO:coordinate\n@SQ\tSN:chrSynthetic\tLN:10\n"
            if command[1] == "idxstats":
                return b"chrSynthetic\t10\t1\t0\n*\t0\t0\t0\n"
            if command[1] == "view":
                return decoded
            raise AssertionError(command)

        with mock.patch.object(BENCHMARK, "_capture_checked", side_effect=capture):
            BENCHMARK._inspect_indexed_bam(
                samtools, bam, cwd=Path("/trial"), label="fixture BAM"
            )

        self.assertIn(
            (str(samtools), "view", "-H", "--no-PG", str(bam)), calls
        )

    def test_step04_index_policy_position_is_normalized_but_required(self) -> None:
        first = (
            b"@PG\tID:MarkDuplicates\tCL:MarkDuplicates TMP_DIR=/scratch "
            b"CREATE_INDEX=true MAX_RECORDS_IN_RAM=500000 CREATE_MD5_FILE=false\n"
        )
        second = (
            b"@PG\tID:MarkDuplicates\tCL:MarkDuplicates TMP_DIR=/scratch "
            b"MAX_RECORDS_IN_RAM=500000 CREATE_INDEX=false CREATE_MD5_FILE=false\n"
        )
        normalized_first, _ = BENCHMARK._canonicalize_step04_command(
            first,
            roots=(),
            run_tokens=(),
            expected_tmp=b"/scratch",
            label="first",
        )
        normalized_second, _ = BENCHMARK._canonicalize_step04_command(
            second,
            roots=(),
            run_tokens=(),
            expected_tmp=b"/scratch",
            label="second",
        )
        self.assertEqual(normalized_first, normalized_second)
        unrelated_double_space = second.replace(
            b"TMP_DIR=/scratch ", b"TMP_DIR=/scratch  "
        )
        normalized_double_space, _ = BENCHMARK._canonicalize_step04_command(
            unrelated_double_space,
            roots=(),
            run_tokens=(),
            expected_tmp=b"/scratch",
            label="unrelated double space",
        )
        self.assertNotEqual(normalized_second, normalized_double_space)
        for invalid in (
            second.replace(b" CREATE_INDEX=false", b""),
            second.replace(b"CREATE_INDEX=false", b"CREATE_INDEX=maybe"),
            second.replace(
                b"CREATE_INDEX=false",
                b"CREATE_INDEX=false CREATE_INDEX=true",
            ),
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(
                    BENCHMARK.BenchmarkSetupError,
                    "omits exact TMP_DIR or CREATE_INDEX metadata",
                ):
                    BENCHMARK._canonicalize_step04_command(
                        invalid,
                        roots=(),
                        run_tokens=(),
                        expected_tmp=b"/scratch",
                        label="invalid",
                    )

    def test_manifest_is_one_paired_v2_plan_over_exact_cases(self) -> None:
        document = BENCHMARK._manifest(
            Path("/locked/python"),
            Path("/repo/tests/tools/retained_stage_benchmark.py"),
            Path("/external/context.json"),
        )

        self.assertEqual(document["schema_version"], "emrys.resource-benchmark.v2")
        cases = document["cases"]
        default_cases = BENCHMARK._select_cases(suite=None, names=None)
        self.assertEqual(
            {case["name"]: case["values"] for case in cases},
            {case.name: list(case.values) for case in default_cases},
        )
        for case in cases:
            self.assertEqual(case["repetitions"], BENCHMARK.MEASURED_REPETITIONS)
            self.assertEqual(
                case["warmup_repetitions"], BENCHMARK.WARMUP_REPETITIONS
            )
            self.assertEqual(case["baseline_variant"], "master")
            self.assertEqual(
                [variant["name"] for variant in case["variants"]],
                ["master", "head"],
            )
            self.assertEqual(case["artifact_paths"], ["{trial_dir}/parity.bin"])
            prefix = [
                "/locked/python",
                "-X",
                "pycache_prefix=/dev/null",
                "/repo/tests/tools/retained_stage_benchmark.py",
            ]
            self.assertEqual(case["setup_argv"][:5], [*prefix, "_setup"])
            self.assertEqual(case["validator_argv"][:5], [*prefix, "_validate"])
            for variant in case["variants"]:
                self.assertEqual(variant["producer_argv"][:5], [*prefix, "_produce"])

    def test_case_selection_is_closed_deduplicated_and_canonical(self) -> None:
        default = BENCHMARK._select_cases(suite=None, names=None)
        self.assertEqual(
            default,
            tuple(
                case
                for case in BENCHMARK.RETAINED_CASES
                if case.suite == BENCHMARK.DEFAULT_SUITE
            ),
        )
        self.assertEqual(
            BENCHMARK._select_cases(suite="identity", names=None),
            (
                BENCHMARK.RETAINED_CASE_BY_NAME["alignment-signatures-mib"],
                BENCHMARK.RETAINED_CASE_BY_NAME[
                    "reference-contig-membership"
                ],
            ),
        )
        reference_case = BENCHMARK.RETAINED_CASE_BY_NAME[
            "reference-contig-membership"
        ]
        self.assertEqual(reference_case.values, (1_000, 4_000, 16_000))
        self.assertEqual(reference_case.threads, 1)
        reference_manifest = BENCHMARK._manifest(
            Path("/locked/python"),
            Path("/repo/tests/tools/retained_stage_benchmark.py"),
            Path("/external/context.json"),
            (reference_case,),
        )["cases"][0]
        self.assertEqual(reference_manifest["warmup_repetitions"], 1)
        self.assertEqual(reference_manifest["repetitions"], 4)
        strict_case = BENCHMARK.RETAINED_CASE_BY_NAME[
            BENCHMARK.STRICT_TSV_CASE.CASE_NAME
        ]
        extended_case = BENCHMARK.RETAINED_CASE_BY_NAME[
            BENCHMARK.STRICT_TSV_CASE.EXTENDED_CASE_NAME
        ]
        self.assertEqual(
            strict_case.values,
            (1_000_001, 1_000_004, 1_000_016, 10_000_004),
        )
        self.assertEqual(extended_case.values, (100_000_001,))
        self.assertEqual(
            [
                len(BENCHMARK.STRICT_TSV_CASE.header_for_samples(samples))
                for samples in (1, 4, 16)
            ],
            [25, 34, 70],
        )
        strict_manifest = BENCHMARK._manifest(
            Path("/locked/python"),
            Path("/repo/tests/tools/retained_stage_benchmark.py"),
            Path("/external/context.json"),
            (strict_case,),
        )["cases"][0]
        self.assertEqual(strict_manifest["warmup_repetitions"], 1)
        self.assertEqual(strict_manifest["repetitions"], 4)
        self.assertEqual(strict_manifest["artifact_paths"], ["{trial_dir}/parity.bin"])
        self.assertEqual(
            BENCHMARK._select_cases(suite="validation-extended", names=None),
            (extended_case,),
        )
        self.assertEqual(
            BENCHMARK._select_cases(suite="sample-stages", names=None),
            (
                BENCHMARK.RETAINED_CASE_BY_NAME["step02-canonical-bam"],
                BENCHMARK.RETAINED_CASE_BY_NAME["step04-duplicate-marking"],
                BENCHMARK.RETAINED_CASE_BY_NAME["step05-split-n-cigar"],
                BENCHMARK.RETAINED_CASE_BY_NAME["step06-mechanical-orientation"],
            ),
        )
        self.assertEqual(
            BENCHMARK._select_cases(suite="all", names=None),
            tuple(
                case
                for case in BENCHMARK.RETAINED_CASES
                if case.suite
                != BENCHMARK.STRICT_TSV_CASE.EXTENDED_SUITE_NAME
            ),
        )
        self.assertEqual(
            BENCHMARK._select_cases(
                suite=None, names=("step08-uniform", "step07-partitions")
            ),
            (
                BENCHMARK.RETAINED_CASE_BY_NAME["step07-partitions"],
                BENCHMARK.RETAINED_CASE_BY_NAME["step08-uniform"],
            ),
        )
        with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "selected once"):
            BENCHMARK._select_cases(
                suite=None, names=("step08-uniform", "step08-uniform")
            )
        with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "mutually exclusive"):
            BENCHMARK._select_cases(
                suite="cohort-stages", names=("step08-uniform",)
            )

    def test_retained_owner_threads_are_positive_but_not_case_coupled(self) -> None:
        record = {
            "commands": {"producer": {"argv": ["owner", "--threads", "2"]}}
        }
        for accepted in ("2", "16"):
            with self.subTest(accepted=accepted):
                record["commands"]["producer"]["argv"][-1] = accepted
                self.assertEqual(
                    BENCHMARK._admit_owner_positive_integer_argument(
                        record, BENCHMARK.STEP06_OWNER, "--threads"
                    ),
                    int(accepted),
                )
        for invalid in ("", "0", "01", "+2", "2.0", "two"):
            with self.subTest(invalid=invalid):
                record["commands"]["producer"]["argv"][-1] = invalid
                with self.assertRaisesRegex(
                    BENCHMARK.BenchmarkSetupError, "canonical positive integer"
                ):
                    BENCHMARK._admit_owner_positive_integer_argument(
                        record, BENCHMARK.STEP06_OWNER, "--threads"
                    )

    def test_cli_case_parser_preserves_exact_values_and_fails_closed(self) -> None:
        base_arguments = [
            "--repo-root",
            "/repo",
            "--e2e-summary",
            "/evidence/e2e-summary.json",
            "--output-root",
            "/evidence/benchmark",
            "--runtime-prefix",
            "/runtime",
            "--rscript",
            "/runtime/bin/Rscript",
            "--renv-library",
            "/runtime/renv",
        ]
        for invalid in ("", " step07-partitions", "unknown-case"):
            with (
                self.subTest(invalid=invalid),
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                BENCHMARK._parser().parse_args(
                    [*base_arguments, "--case", invalid]
                )

        parsed = BENCHMARK._parser().parse_args(
            [
                *base_arguments,
                "--case",
                "step07-partitions",
                "--case",
                "step07-partitions",
            ]
        )
        self.assertEqual(
            parsed.case_names,
            ["step07-partitions", "step07-partitions"],
        )
        with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "selected once"):
            BENCHMARK._select_cases(suite=parsed.suite, names=parsed.case_names)

    def test_alignment_signature_case_binds_variant_source_and_exact_parity(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            trial = root / "trial"
            trial.mkdir()
            context = root / "context.json"
            context.write_text(
                json.dumps(
                    {"sources": {"master": str(ROOT), "head": str(ROOT)}}
                ),
                encoding="utf-8",
            )
            BENCHMARK._setup_alignment_signatures(trial, 10)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "_produce",
                    "--context",
                    str(context),
                    "--case",
                    "alignment-signatures-mib",
                    "--value",
                    "10",
                    "--variant",
                    "head",
                    "--trial-dir",
                    str(trial),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            BENCHMARK._validate_alignment_signatures(trial)
            self.assertEqual((trial / "input.bam").stat().st_size, 10 * 1024**2)
            self.assertEqual(
                (trial / "input.bam.bai").stat().st_size, 10 * 1024**2
            )
            self.assertEqual(
                (trial / "parity.bin").read_bytes(), b"\x1f\x8b\x08\x04BAI\x01"
            )

    def test_reference_contig_case_binds_variant_source_and_exact_parity(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            trial = root / "trial"
            trial.mkdir()
            context = root / "context.json"
            context.write_text(
                json.dumps(
                    {"sources": {"master": str(ROOT), "head": str(ROOT)}}
                ),
                encoding="utf-8",
            )
            BENCHMARK._setup_reference_contig_membership(trial, 1_000)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "pycache_prefix=/dev/null",
                    str(SCRIPT),
                    "_produce",
                    "--context",
                    str(context),
                    "--case",
                    "reference-contig-membership",
                    "--value",
                    "1000",
                    "--variant",
                    "head",
                    "--trial-dir",
                    str(trial),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            fasta_lines = (trial / "reference.fa").read_text(
                encoding="ascii"
            ).splitlines()
            self.assertEqual(len(fasta_lines), 2_000)
            self.assertEqual(fasta_lines[:2], [">contig-00000000", "A"])
            self.assertEqual(fasta_lines[-2:], [">contig-00000999", "A"])
            expected = "".join(
                f"contig-{index:08d}\t1\n" for index in range(1_000)
            ).encode("ascii")
            self.assertEqual((trial / "observed.tsv").read_bytes(), expected)

            BENCHMARK._validate_reference_contig_membership(trial, 1_000)
            self.assertEqual((trial / "parity.bin").read_bytes(), expected)

    def test_reference_contig_case_uses_selected_source_and_fails_closed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "selected-source"
            module = source / "src/emrys/libraries/references/contigs.py"
            module.parent.mkdir(parents=True)
            for package in (
                source / "src/emrys/__init__.py",
                source / "src/emrys/libraries/__init__.py",
                source / "src/emrys/libraries/references/__init__.py",
            ):
                package.write_text("", encoding="utf-8")
            module.write_text(
                "def parse_fasta(_path):\n"
                "    return [('selected-archive', 1)]\n",
                encoding="utf-8",
            )
            trial = root / "trial"
            trial.mkdir()
            BENCHMARK._setup_reference_contig_membership(trial, 1_000)
            context = root / "context.json"
            context.write_text(
                json.dumps(
                    {"sources": {"master": str(source), "head": str(source)}}
                ),
                encoding="utf-8",
            )
            arguments = [
                sys.executable,
                "-X",
                "pycache_prefix=/dev/null",
                str(SCRIPT),
                "_produce",
                "--context",
                str(context),
                "--case",
                "reference-contig-membership",
                "--value",
                "1000",
                "--variant",
                "head",
                "--trial-dir",
                str(trial),
            ]

            completed = subprocess.run(
                arguments, check=False, capture_output=True, text=True
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                (trial / "observed.tsv").read_bytes(), b"selected-archive\t1\n"
            )
            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "order, name, length, or count"
            ):
                BENCHMARK._validate_reference_contig_membership(trial, 1_000)

            context.write_text(
                json.dumps(
                    {
                        "sources": {
                            "master": str(source),
                            "head": str(root / "missing-source"),
                        }
                    }
                ),
                encoding="utf-8",
            )
            missing = subprocess.run(
                arguments, check=False, capture_output=True, text=True
            )
            self.assertEqual(missing.returncode, 2)
            self.assertIn("head source archive is unavailable", missing.stderr)

            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "count is not registered"
            ):
                BENCHMARK._setup_reference_contig_membership(root / "unused", 999)

    def test_reference_contig_validator_rejects_each_semantic_tamper(self) -> None:
        expected_lines = [
            f"contig-{index:08d}\t1\n".encode("ascii")
            for index in range(1_000)
        ]
        tampered = {
            "order": [expected_lines[1], expected_lines[0], *expected_lines[2:]],
            "name": [b"wrong-name\t1\n", *expected_lines[1:]],
            "length": [b"contig-00000000\t2\n", *expected_lines[1:]],
            "count": expected_lines[:-1],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for label, lines in tampered.items():
                with self.subTest(label=label):
                    trial = root / label
                    trial.mkdir()
                    (trial / "observed.tsv").write_bytes(b"".join(lines))
                    with self.assertRaisesRegex(
                        BENCHMARK.BenchmarkSetupError,
                        "order, name, length, or count",
                    ):
                        BENCHMARK._validate_reference_contig_membership(
                            trial, 1_000
                        )
                    self.assertFalse((trial / "parity.bin").exists())

    def test_partition_sweeps_cover_the_full_5mb_contig_once(self) -> None:
        for count in (1, 5, 25):
            rows = BENCHMARK._partition_rows(count, "synthetic", 5_000_000)
            self.assertEqual(len(rows), count)
            previous_end = 0
            for index, (partition, selector_type, selector) in enumerate(rows, 1):
                self.assertEqual(partition, f"p{index:02d}")
                self.assertEqual(selector_type, "region")
                contig, interval = selector.split(":", 1)
                start, end = map(int, interval.split("-"))
                self.assertEqual(contig, "synthetic")
                self.assertEqual(start, previous_end + 1)
                previous_end = end
            self.assertEqual(previous_end, 5_000_000)

    def test_step08_row_distributions_are_exact_and_scheduler_discriminating(self) -> None:
        self.assertEqual(BENCHMARK._step08_counts("step08-reread", 10_000), (5_000, 5_000))
        self.assertEqual(BENCHMARK._step08_counts("step08-reread", 100_000), (50_000, 50_000))
        uniform = BENCHMARK._step08_counts("step08-uniform", 100_000)
        skew = BENCHMARK._step08_counts("step08-skew", 100_000)
        self.assertEqual(uniform, (6_250,) * 16)
        self.assertEqual(sum(skew), 100_000)
        self.assertEqual(skew[::2], (12_000,) * 8)
        self.assertEqual(skew[1::2], (500,) * 8)
        self.assertEqual(BENCHMARK._case_threads("step08-reread"), 1)
        self.assertEqual(BENCHMARK._case_threads("step08-skew"), 2)

    def test_step07_normalization_is_narrow(self) -> None:
        trial = Path("/trials/round/master")
        source = (
            b"##fileformat=VCFv4.2\n"
            b"##bcftoolsVersion=1.21\n"
            b"##bcftoolsCommand=mpileup /trials/round/master/input; Date=x\n"
            b"##bcftools_filterVersion=1.21\n"
            b"##bcftools_filterCommand=filter -o /trials/round/master/out; Date=x\n"
            b"##bcftools_viewVersion=must-remain\n"
            b"##bcftools_pluginVersion=must-remain\n"
            b"##otherDate=must-remain\n"
            b"path=/trials/round/master/output.vcf\n"
        )

        normalized = BENCHMARK._normalize_step07(source, trial)

        self.assertNotIn(b"##bcftoolsVersion=", normalized)
        self.assertNotIn(b"##bcftoolsCommand=", normalized)
        self.assertNotIn(b"##bcftools_filterVersion=", normalized)
        self.assertNotIn(b"##bcftools_filterCommand=", normalized)
        self.assertIn(b"##bcftools_viewVersion=must-remain", normalized)
        self.assertIn(b"##bcftools_pluginVersion=must-remain", normalized)
        self.assertIn(b"##otherDate=must-remain", normalized)
        self.assertIn(b"path=<TRIAL_ROOT>/output.vcf", normalized)

    def test_realistic_symbolic_vcf_template_and_writer_preserve_number_r_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            retained = Path(directory) / "retained.vcf"
            output = Path(directory) / "fixture.vcf"
            retained.write_bytes(
                b"##fileformat=VCFv4.2\n"
                b"##ALT=<ID=*,Description=\"Represents allele(s) other than observed.\">\n"
                b"##INFO=<ID=AD,Number=R,Type=Integer,Description=\"Allele depths\">\n"
                b"##FORMAT=<ID=AD,Number=R,Type=Integer,Description=\"Allele depths\">\n"
                b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\n"
                b"x\t1\told\tA\tC,<*>\t.\tPASS\tAD=7,3,0\tDP:AD\t10:7,3,0\n"
            )

            header, template = BENCHMARK._vcf_template(retained)

            BENCHMARK._write_vcf(output, header, template, "synthetic", "ACGTACGT", 3, 3)

            lines = output.read_text(encoding="ascii").splitlines()
            self.assertIn("##INFO=<ID=AD,Number=R", "\n".join(lines))
            rows = [line for line in lines if not line.startswith("#")]
            fields = [row.split("\t") for row in rows]
            self.assertEqual([row[0] for row in fields], ["synthetic"] * 3)
            self.assertEqual([row[1] for row in fields], ["3", "4", "5"])
            self.assertEqual([row[3] for row in fields], ["G", "T", "A"])
            self.assertEqual([row[4] for row in fields], ["A,<*>", "C,<*>", "G,<*>"])
            self.assertEqual([row[2] for row in fields], ["."] * 3)
            self.assertEqual([row[7] for row in fields], ["AD=7,3,0"] * 3)
            self.assertEqual([row[9] for row in fields], ["10:7,3,0"] * 3)

            single_alt = Path(directory) / "single-alt.vcf"
            single_alt.write_bytes(retained.read_bytes().replace(b"C,<*>", b"C"))
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "concrete-SNV"):
                BENCHMARK._vcf_template(single_alt)

    def test_fasta_fixture_rejects_non_acgt_reference_bases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fasta = Path(directory) / "reference.fa"
            with mock.patch.object(BENCHMARK, "EXPECTED_CONTIG_LENGTH", 4):
                fasta.write_text(">synthetic\nACGN\n", encoding="ascii")
                with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "expected 5Mb contig"):
                    BENCHMARK._fasta(fasta)
                fasta.write_text(">synthetic\nACGT\n", encoding="ascii")
                self.assertEqual(BENCHMARK._fasta(fasta), ("synthetic", "ACGT"))

    def test_step08_fixture_is_shared_across_rounds_and_hash_admitted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            warmup = root / "warmups/step08-skew/100000/rep-01/master"
            measured = root / "trials/step08-skew/100000/rep-03/head"
            warmup.mkdir(parents=True)
            measured.mkdir(parents=True)
            samples = root / "samples.tsv"
            samples.write_text("sample_id\tx\nS\t1\n", encoding="utf-8")
            reference = root / "reference.fa"
            reference.write_text(">synthetic\nA\n", encoding="ascii")
            retained = root / "retained"
            retained.mkdir()
            primary_vcf = retained / "primary.vcf"
            primary_vcf.write_text("template\n", encoding="ascii")
            context = {
                "reference_fasta": str(reference),
                "retained_primary_vcf": str(primary_vcf),
                "sample_manifest": str(samples),
                "cohort_id": "cohort",
                "python": sys.executable,
            }
            header = [b"##fileformat=VCFv4.2\n", b"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS\n"]
            template = b"x\t1\t.\tA\tG,<*>\t.\tPASS\tAD=7,3,0\tDP:AD\t10:7,3,0".split(b"\t")

            def tiny_vcf(path: Path, *_arguments: object) -> None:
                path.write_bytes(b"fixture\n")

            with (
                mock.patch.object(BENCHMARK, "_fasta", return_value=("synthetic", "A" * 5_000_000)),
                mock.patch.object(BENCHMARK, "_vcf_template", return_value=(header, template)),
                mock.patch.object(BENCHMARK, "_write_vcf", side_effect=tiny_vcf) as writer,
            ):
                BENCHMARK._setup_step08(context, warmup, "step08-skew", 100_000)
                first_count = writer.call_count
                BENCHMARK._setup_step08(context, measured, "step08-skew", 100_000)
                self.assertEqual(writer.call_count, first_count)

            fixture = root / "fixtures/step08-skew/100000"
            self.assertEqual(first_count, 16)
            self.assertFalse((fixture / ".venv").exists())
            self.assertEqual(len((fixture / "partitions.tsv").read_text().splitlines()), 9)
            marker = json.loads((fixture / "fixture.json").read_text())
            self.assertEqual(marker["schema_version"], BENCHMARK.STEP08_FIXTURE_SCHEMA)
            self.assertEqual(marker["expected_vcf_record_count"], 100_000)
            self.assertEqual(marker["expected_supported_candidate_count"], 100_000)
            self.assertEqual(marker["expected_symbolic_alt_count"], 100_000)
            self.assertEqual(set(marker["members"]), set(BENCHMARK._step08_member_roster("cohort", BENCHMARK._step08_counts("step08-skew", 100_000))))
            receipts = sorted((fixture / "step07/cohort").glob("*/*.step07_outputs.tsv"))
            self.assertEqual(len(receipts), 8)
            declared = []
            for receipt in receipts:
                with receipt.open(encoding="utf-8", newline="") as stream:
                    rows = list(csv.DictReader(stream, dialect="excel-tab"))
                self.assertEqual([row["orientation"] for row in rows], ["FWD_like", "REV_like"])
                self.assertTrue(all(not Path(row["vcf_path"]).is_absolute() for row in rows))
                self.assertTrue(all(row["vcf_path"].startswith("step07/") for row in rows))
                declared.extend(int(row["vcf_record_count"]) for row in rows)
            self.assertEqual(declared, list(BENCHMARK._step08_counts("step08-skew", 100_000)))

            first_vcf = next((fixture / "step07/cohort").glob("*/*.vcf"))
            first_vcf.write_bytes(b"tampered\n")
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "member differs"):
                BENCHMARK._setup_step08(context, measured, "step08-skew", 100_000)

    def test_step08_validator_runs_owner_then_all_pass_and_bundles_raw_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repo = root / "repo"
            repo.mkdir()
            trial = root / "benchmark-results/trials/step08-reread/10000/rep-01/master"
            fixture = root / "benchmark-results/fixtures/step08-reread/10000"
            trial.mkdir(parents=True)
            fixture.mkdir(parents=True)
            (fixture / "partitions.tsv").write_text("partition_id\tselector_type\tselector_value\np01\tregion\ts:1-10\n")
            cohort_root = trial / "output/cohort"
            qc = trial / "qc"
            cohort_root.mkdir(parents=True)
            qc.mkdir()
            (cohort_root / "cohort.step08_sites.tsv").write_bytes(b"sites\n")
            (cohort_root / "cohort.step08_inputs.tsv").write_bytes(b"inputs\n")
            (qc / "cohort.step08_summary.tsv").write_bytes(b"summary\n")
            context = {
                "repo_root": str(repo),
                "python": "/locked/python",
                "cohort_id": "cohort",
                "sample_manifest": "/retained/samples.tsv",
                "annotation_gtf": "/retained/genes.gtf",
            }
            calls: list[tuple[str, ...]] = []

            with mock.patch.object(
                BENCHMARK,
                "_run_checked",
                side_effect=lambda argv, **_kwargs: calls.append(tuple(argv)),
            ), mock.patch.object(
                BENCHMARK, "_admit_step08_fixture", return_value=fixture
            ):
                BENCHMARK._validate_step08(
                    context, trial, "step08-reread", 10_000
                )

            self.assertIn("cohort-candidate-preprocessing", calls[0])
            self.assertIn("--execute", calls[0])
            self.assertIn("all-pass", calls[1])
            parity = (trial / "parity.bin").read_bytes()
            self.assertIn(b"sites\n", parity)
            self.assertIn(b"inputs\n", parity)
            self.assertIn(b"summary\n", parity)

    def test_step08_producer_uses_fixture_cwd_and_relative_step07_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            trial = root / "benchmark-results/trials/step08-skew/100000/rep-02/head"
            fixture = root / "benchmark-results/fixtures/step08-skew/100000"
            source = root / "source"
            trial.mkdir(parents=True)
            fixture.mkdir(parents=True)
            source.mkdir()
            captured: dict[str, object] = {}

            def run(argv: object, *, cwd: Path, environment: object) -> None:
                captured.update(argv=tuple(argv), cwd=cwd, environment=environment)

            process_environment = ModuleType("emrys.libraries.process_environment")
            process_environment.guarded_r_environment = (
                lambda *_args, **_kwargs: {"GUARDED": "1"}
            )
            modules = {
                "emrys": ModuleType("emrys"),
                "emrys.libraries": ModuleType("emrys.libraries"),
                "emrys.libraries.process_environment": process_environment,
            }
            context = {
                "renv_library": str(root / "renv"),
                "cohort_id": "cohort",
                "sample_manifest": str(root / "samples.tsv"),
                "annotation_gtf": str(root / "genes.gtf"),
                "rscript": "/runtime/Rscript",
                "python": "/repo/.venv/bin/python",
            }
            with (
                mock.patch.dict(sys.modules, modules),
                mock.patch.object(BENCHMARK, "_run_checked", side_effect=run),
            ):
                BENCHMARK._produce_step08(
                    context, trial, source, "step08-skew", 100_000, 2
                )

            argv = captured["argv"]
            self.assertEqual(captured["cwd"], fixture)
            step07_index = argv.index("--step07-root")
            self.assertEqual(argv[step07_index + 1], "step07")
            self.assertEqual(
                captured["environment"],
                {
                    "GUARDED": "1",
                    "EMRYS_SHA256_PYTHON": "/repo/.venv/bin/python",
                    "EMRYS_REQUIRE_BOUND_SHA256": "1",
                },
            )

    def test_step07_producer_binds_the_absolute_sha256_python(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repo = root / "repo"
            fixture = root / "trial/fixture"
            source = root / "source"
            runtime = root / "runtime/bin"
            repo.mkdir()
            fixture.mkdir(parents=True)
            source.mkdir()
            runtime.mkdir(parents=True)
            (runtime / "bcftools").write_text("tool")
            (runtime / "bcftools").chmod(0o755)
            (fixture / "partitions.tsv").write_text(
                "partition_id\tselector_type\tselector_value\np01\tregion\ts:1-10\n"
            )
            captured: dict[str, object] = {}

            def run(argv: object, *, cwd: Path, environment: object) -> None:
                captured.update(argv=tuple(argv), cwd=cwd, environment=environment)

            process_environment = ModuleType("emrys.libraries.process_environment")
            process_environment.sanitized_subprocess_environment = (
                lambda _environment: {"SANITIZED": "1"}
            )
            modules = {
                "emrys": ModuleType("emrys"),
                "emrys.libraries": ModuleType("emrys.libraries"),
                "emrys.libraries.process_environment": process_environment,
            }
            context = {
                "repo_root": str(repo),
                "runtime_prefix": str(runtime.parent),
                "python": "/repo/.venv/bin/python",
                "cohort_id": "cohort",
                "sample_manifest": "/retained/samples.tsv",
                "orientation_root": "/retained/orientation",
                "reference_fasta": "/retained/reference.fa",
            }
            with (
                mock.patch.dict(sys.modules, modules),
                mock.patch.object(BENCHMARK, "_run_checked", side_effect=run),
            ):
                BENCHMARK._produce_step07(context, fixture.parent, source)

            self.assertEqual(captured["cwd"], repo)
            self.assertEqual(
                captured["environment"],
                {
                    "SANITIZED": "1",
                    "EMRYS_SHA256_PYTHON": "/repo/.venv/bin/python",
                    "EMRYS_REQUIRE_BOUND_SHA256": "1",
                },
            )

    def test_step02_owner_uses_retained_input_and_stable_relative_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            trial = root / "trial"
            source = root / "source"
            owner = source / "src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh"
            samtools = root / "runtime/bin/samtools"
            input_bam = root / "retained/input.bam"
            trial.mkdir()
            owner.parent.mkdir(parents=True)
            owner.write_text("#!/bin/bash\n")
            samtools.parent.mkdir(parents=True)
            samtools.write_text("#!/bin/sh\n")
            samtools.chmod(0o755)
            input_bam.parent.mkdir()
            input_bam.write_bytes(b"retained")
            state = input_bam.stat()
            context = {
                "sample_id": BENCHMARK.RETAINED_SAMPLE_ID,
                "python": "/repo/.venv/bin/python",
                "runtime_prefix": str(samtools.parents[1]),
                "retained_step01_bam": {
                    "path": str(input_bam),
                    "size_bytes": state.st_size,
                    "sha256": hashlib.sha256(input_bam.read_bytes()).hexdigest(),
                    "device": state.st_dev,
                    "inode": state.st_ino,
                    "mtime_ns": state.st_mtime_ns,
                },
            }
            captured: dict[str, object] = {}

            def run(argv: object, *, cwd: Path, environment: object) -> None:
                captured.update(argv=tuple(argv), cwd=cwd, environment=environment)

            process_environment = ModuleType("emrys.libraries.process_environment")
            process_environment.sanitized_subprocess_environment = (
                lambda _environment: {"SANITIZED": "1"}
            )
            modules = {
                "emrys": ModuleType("emrys"),
                "emrys.libraries": ModuleType("emrys.libraries"),
                "emrys.libraries.process_environment": process_environment,
            }
            with mock.patch.object(
                BENCHMARK,
                "_sha256_file",
                side_effect=AssertionError("setup must not hash the retained BAM"),
            ):
                BENCHMARK._setup_step02(context, trial, 100_000)
            (trial / "completed-output-link").hardlink_to(input_bam)
            (trial / "completed-output-link").unlink()
            self.assertEqual(BENCHMARK._retained_step01_bam(context), input_bam)
            with (
                mock.patch.dict(sys.modules, modules),
                mock.patch.object(BENCHMARK, "_run_checked", side_effect=run),
            ):
                BENCHMARK._produce_step02(context, trial, source)

            argv = captured["argv"]
            self.assertEqual(captured["cwd"], trial)
            self.assertEqual(argv[argv.index("--output-dir") + 1], "output")
            self.assertEqual(argv[argv.index("--threads") + 1], "2")
            self.assertEqual(argv[argv.index("--input-alignment") + 1], str(input_bam))
            self.assertEqual(
                captured["environment"],
                {
                    "SANITIZED": "1",
                    "EMRYS_RUN_TOKEN": "retained-benchmark",
                    "EMRYS_SHA256_PYTHON": "/repo/.venv/bin/python",
                    "EMRYS_REQUIRE_BOUND_SHA256": "1",
                },
            )
            self.assertTrue((trial / "qc").is_dir())

    def test_step02_validator_binds_exact_pair_and_removes_large_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            context, trial, bam, bai, samtools = _step02_validator_fixture(root)

            validation_calls, idxstats = _run_step02_validator(
                context, trial, samtools
            )

            self.assertIn("canonical-bam", validation_calls[0])
            self.assertIn("all-pass", validation_calls[1])
            parity = (trial / "parity.bin").read_bytes()
            self.assertIn(hashlib.sha256(b"bam-bytes").hexdigest().encode(), parity)
            self.assertIn(hashlib.sha256(b"bai-bytes").hexdigest().encode(), parity)
            self.assertIn(idxstats, parity)
            self.assertFalse(bam.exists())
            self.assertFalse(bai.exists())
            self.assertEqual(list((trial / "output").iterdir()), [])

    def test_step02_validator_rejects_a_byte_identical_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context, trial, bam, _bai, samtools = _step02_validator_fixture(
                Path(directory).resolve()
            )
            data = bam.read_bytes()
            bam.unlink()
            bam.write_bytes(data)

            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "canonical hard-link path"
            ):
                _run_step02_validator(context, trial, samtools)

    def test_step02_validator_rejects_retained_pair_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context, trial, _bam, bai, samtools = _step02_validator_fixture(
                Path(directory).resolve()
            )
            bai.write_bytes(b"different-index")

            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "retained verified identities"
            ):
                _run_step02_validator(context, trial, samtools)

    def test_step04_validator_proves_semantics_and_rejects_shared_bad_tags(self) -> None:
        def run(fixture: dict[str, object]) -> list[tuple[str, ...]]:
            calls: list[tuple[str, ...]] = []
            with (
                mock.patch.object(
                    BENCHMARK, "_run_checked",
                    side_effect=lambda argv, **_kwargs: calls.append(tuple(argv)),
                ),
                mock.patch.object(
                    BENCHMARK, "_capture_checked", return_value=fixture["input"]
                ),
                mock.patch.object(
                    BENCHMARK, "_inspect_indexed_bam",
                    side_effect=lambda _tool, bam, **_kwargs: fixture["inspections"][bam],
                ),
            ):
                BENCHMARK._validate_step04(fixture["context"], fixture["trial"])
            return calls

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            fixture = _step04_validator_fixture(root / "pass")
            calls = run(fixture)
            self.assertIn("duplicate-marking", calls[0])
            self.assertIn("all-pass", calls[1])
            self.assertIn(b"independent-counts", (fixture["trial"] / "parity.bin").read_bytes())
            self.assertTrue(all(not path.exists() for path in fixture["outputs"].values()))

            fixture = _step04_validator_fixture(root / "bad-tags")
            for inspection in fixture["inspections"].values():
                decoded = inspection["decoded"].replace(
                    b"PG:Z:MarkDuplicates", b"PG:Z:samtools"
                )
                inspection.update(
                    decoded=decoded,
                    records=BENCHMARK._sam_records(decoded, "bad fixture"),
                    indexed=decoded,
                )
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "PG/tag transition"):
                run(fixture)

    def test_step05_validator_proves_split_semantics_index_parity_and_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _step05_validator_fixture(Path(directory).resolve())
            calls: list[tuple[str, ...]] = []
            with (
                mock.patch.object(
                    BENCHMARK, "_run_checked",
                    side_effect=lambda argv, **_kwargs: calls.append(tuple(argv)),
                ),
                mock.patch.object(
                    BENCHMARK, "_inspect_indexed_bam",
                    side_effect=lambda _tool, bam, **_kwargs: fixture["inspections"][bam],
                ),
            ):
                BENCHMARK._validate_step05(fixture["context"], fixture["trial"])
            self.assertIn("split-n-cigar", calls[0])
            self.assertIn("all-pass", calls[1])
            parity = (fixture["trial"] / "parity.bin").read_bytes()
            self.assertIn(b'"input_n_cigar_operations":1', parity)
            self.assertTrue(all(not path.exists() for path in fixture["outputs"].values()))
            output_root = BENCHMARK._step05_paths(BENCHMARK.RETAINED_SAMPLE_ID)["output_root"]
            self.assertEqual(list((fixture["trial"] / output_root).iterdir()), [])

            observed = fixture["inspections"][next(iter(fixture["outputs"].values()))]
            bad_records = observed["decoded"].replace(b"5M\t=", b"2M1N2M\t=", 1)
            observed["records"] = BENCHMARK._sam_records(bad_records, "bad output")
            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "retains an N CIGAR"
            ):
                BENCHMARK._independent_step05_semantics(
                    fixture["inspections"][Path(fixture["context"]["retained_step04_bam"]["path"])],
                    observed,
                )

    def test_step05_validator_rejects_predecessor_header_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _step05_validator_fixture(Path(directory).resolve())
            observed_bam = fixture["outputs"]["bam"]
            observed = fixture["inspections"][observed_bam]
            observed["header"] = observed["header"].replace(
                b"@PG\tID:MarkDuplicates\tPN:MarkDuplicates\n",
                b"@PG\tID:MarkDuplicates\tPN:foreign-writer\n",
                1,
            )
            with (
                mock.patch.object(BENCHMARK, "_run_checked"),
                mock.patch.object(
                    BENCHMARK,
                    "_inspect_indexed_bam",
                    side_effect=lambda _tool, bam, **_kwargs: fixture["inspections"][bam],
                ),
                self.assertRaisesRegex(
                    BENCHMARK.BenchmarkSetupError,
                    "header differs beyond admitted roots and run tokens or metadata",
                ),
            ):
                BENCHMARK._validate_step05(fixture["context"], fixture["trial"])

    def test_step05_owner_uses_retained_gatk_adapter_and_exact_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            fixture = _step05_validator_fixture(root)
            source = root / "source"
            owner = source / "src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh"
            owner.parent.mkdir(parents=True)
            owner.write_text("#!/bin/bash\n")
            runtime = root / "runtime/bin"
            runtime.mkdir(parents=True)
            for name in ("bash", "gatk-adapter", "java", "samtools", "python"):
                executable = runtime / name
                executable.write_text("#!/bin/sh\n")
                executable.chmod(0o755)
            context = fixture["context"]
            context.update(
                runtime_bash=str(runtime / "bash"),
                runtime_gatk=str(runtime / "gatk-adapter"),
                runtime_java=str(runtime / "java"),
                runtime_samtools=str(runtime / "samtools"),
                runtime_sha256_python=str(runtime / "python"),
            )
            captured: dict[str, object] = {}
            process_environment = ModuleType("emrys.libraries.process_environment")
            process_environment.gatk_subprocess_environment = (
                lambda selected, **_kwargs: {"SELECTED_JAVA": str(selected)}
            )
            modules = {
                "emrys": ModuleType("emrys"),
                "emrys.libraries": ModuleType("emrys.libraries"),
                "emrys.libraries.process_environment": process_environment,
            }
            with (
                mock.patch.dict(sys.modules, modules),
                mock.patch.object(
                    BENCHMARK, "_run_checked",
                    side_effect=lambda argv, **kwargs: captured.update(argv=tuple(argv), **kwargs),
                ),
            ):
                BENCHMARK._produce_step05(context, fixture["trial"], source)
            argv = captured["argv"]
            self.assertEqual(argv[0:2], (str(runtime / "bash"), str(owner)))
            self.assertEqual(argv[argv.index("--gatk-bin") + 1], str(runtime / "gatk-adapter"))
            self.assertEqual(argv[-2:], ("--no-clobber", "--execute"))
            self.assertEqual(
                captured["environment"]["EMRYS_RUN_TOKEN"],
                BENCHMARK.STEP05_TRIAL_RUN_TOKEN,
            )

    def test_step06_owner_binds_exact_authorities_and_relative_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            trial = root / "trial"
            source = root / "source"
            runtime = root / "runtime"
            owner = (
                source
                / "src/emrys/stages/mechanical_orientation/step_06_split_bam_by_read_orientation.sh"
            )
            owner.parent.mkdir(parents=True)
            owner.write_text("#!/bin/bash\n")
            trial.mkdir()
            for name in ("bash", "samtools", "python"):
                executable = runtime / "bin" / name
                executable.parent.mkdir(parents=True, exist_ok=True)
                executable.write_text("#!/bin/sh\n")
                executable.chmod(0o755)
            input_bam = root / "retained/sample.split_ncigar.bam"
            input_bam.parent.mkdir()
            input_bam.write_bytes(b"retained-step05-bam")
            input_bai = Path(f"{input_bam}.bai")
            input_bai.write_bytes(b"retained-step05-bai")
            context = {
                "sample_id": BENCHMARK.RETAINED_SAMPLE_ID,
                "python": str(runtime / "bin/python"),
                "runtime_prefix": str(runtime),
                "runtime_bash": str(runtime / "bin/bash"),
                "runtime_samtools": str(runtime / "bin/samtools"),
                "runtime_sha256_python": str(runtime / "bin/python"),
                "retained_step05_bam": BENCHMARK._artifact_context(
                    _retained_artifact(input_bam)
                ),
                "retained_step05_bai": BENCHMARK._artifact_context(
                    _retained_artifact(input_bai)
                ),
            }
            captured: dict[str, object] = {}

            def run(argv: object, *, cwd: Path, environment: object) -> None:
                captured.update(argv=tuple(argv), cwd=cwd, environment=environment)

            process_environment = ModuleType("emrys.libraries.process_environment")
            process_environment.sanitized_subprocess_environment = (
                lambda _environment: {"SANITIZED": "1"}
            )
            modules = {
                "emrys": ModuleType("emrys"),
                "emrys.libraries": ModuleType("emrys.libraries"),
                "emrys.libraries.process_environment": process_environment,
            }
            with mock.patch.object(
                BENCHMARK,
                "_sha256_file",
                side_effect=AssertionError("setup must not hash Step 05 inputs"),
            ):
                BENCHMARK._setup_step06(context, trial, 100_000)
            with (
                mock.patch.dict(sys.modules, modules),
                mock.patch.object(BENCHMARK, "_run_checked", side_effect=run),
            ):
                BENCHMARK._produce_step06(context, trial, source)

            argv = captured["argv"]
            self.assertEqual(argv[0], str(runtime / "bin/bash"))
            self.assertEqual(argv[1], str(owner))
            self.assertEqual(captured["cwd"], trial)
            self.assertEqual(argv[argv.index("--input-bam") + 1], str(input_bam))
            self.assertEqual(
                argv[argv.index("--output-dir") + 1],
                f"results/orientation/{BENCHMARK.RETAINED_SAMPLE_ID}",
            )
            self.assertEqual(
                argv[argv.index("--qc-dir") + 1], "results/qc/orientation"
            )
            self.assertEqual(argv[argv.index("--threads") + 1], "4")
            self.assertEqual(
                argv[argv.index("--samtools-bin") + 1],
                str(runtime / "bin/samtools"),
            )
            self.assertEqual(
                captured["environment"],
                {
                    "SANITIZED": "1",
                    "EMRYS_RUN_TOKEN": BENCHMARK.STEP06_TRIAL_RUN_TOKEN,
                    "EMRYS_SHA256_PYTHON": str(runtime / "bin/python"),
                    "EMRYS_REQUIRE_BOUND_SHA256": "1",
                },
            )

    def test_step06_validator_proves_semantics_and_removes_publication(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _step06_validator_fixture(Path(directory).resolve())

            self.assertIn(
                b"ID:GATK SplitNCigarReads-A918B00\t",
                fixture["headers"][fixture["outputs"]["fwd_bam"]],
            )

            validation_calls = _run_step06_validator(fixture)

            self.assertIn("mechanical-orientation", validation_calls[0])
            self.assertIn("all-pass", validation_calls[1])
            parity = (fixture["trial"] / "parity.bin").read_bytes()
            self.assertIn(b"independent-counts", parity)
            self.assertIn(b"0.800000", parity)
            outputs = fixture["outputs"]
            self.assertTrue(all(not path.exists() for path in outputs.values()))
            relative = BENCHMARK._step06_paths(BENCHMARK.RETAINED_SAMPLE_ID)
            self.assertEqual(list((fixture["trial"] / relative["orientation_root"]).iterdir()), [])
            self.assertEqual(list((fixture["trial"] / relative["counts_root"]).iterdir()), [])

    def test_step06_collision_shape_requires_a_proven_base(self) -> None:
        base = b"GATK SplitNCigarReads"
        generated = base + b"-A918B00"
        unrelated = b"ResearchTool-A918B00"
        known_ids = {base, generated, unrelated}

        self.assertEqual(
            BENCHMARK._step06_collision_base(generated, known_ids), base
        )
        self.assertIsNone(
            BENCHMARK._step06_collision_base(unrelated, known_ids)
        )
        self.assertIsNone(
            BENCHMARK._step06_collision_base(base + b"-A918B0000", known_ids)
        )

    def test_step06_parity_bundle_is_stable_across_trial_roots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            master = _step06_validator_fixture(root / "master")
            head = _step06_validator_fixture(root / "head")

            _run_step06_validator(master)
            _run_step06_validator(head)

            self.assertEqual(
                (master["trial"] / "parity.bin").read_bytes(),
                (head["trial"] / "parity.bin").read_bytes(),
            )

    def test_step06_validator_rejects_nonadmitted_header_difference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _step06_validator_fixture(Path(directory).resolve())
            outputs = fixture["outputs"]
            headers = fixture["headers"]
            headers[outputs["fwd_bam"]] = headers[outputs["fwd_bam"]].replace(
                b"PN:MarkDuplicates", b"PN:foreign-writer"
            )

            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError,
                "beyond admitted roots and run tokens",
            ):
                _run_step06_validator(fixture)

    def test_step06_validator_rejects_altered_collision_alias_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _step06_validator_fixture(Path(directory).resolve())
            outputs = fixture["outputs"]
            headers = fixture["headers"]
            alias = fixture["observed_aliases"]["mark_duplicates"]
            headers[outputs["fwd_bam"]] = headers[outputs["fwd_bam"]].replace(
                f"ID:MarkDuplicates-{alias}\tPN:MarkDuplicates".encode(),
                f"ID:MarkDuplicates-{alias}\tPN:foreign-writer".encode(),
            )

            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError,
                "collision alias differs beyond admitted Step 06 view metadata",
            ):
                _run_step06_validator(fixture)

    def test_step06_validator_rejects_unadmitted_thread_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _step06_validator_fixture(Path(directory).resolve())
            outputs = fixture["outputs"]
            headers = fixture["headers"]
            headers[outputs["fwd_bam"]] = headers[outputs["fwd_bam"]].replace(
                b"-@ 4", b"-@ 3"
            )

            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "admitted thread count"
            ):
                _run_step06_validator(fixture)

    def test_step06_validator_rejects_unknown_record_collision_alias(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _step06_validator_fixture(Path(directory).resolve())
            outputs = fixture["outputs"]
            records = fixture["records"]
            indexed = fixture["indexed"]
            alias = fixture["observed_aliases"]["rg"]
            bad = records[outputs["fwd_bam"]].replace(
                f"RG:Z:{BENCHMARK.RETAINED_SAMPLE_ID}-{alias}".encode(),
                f"RG:Z:{BENCHMARK.RETAINED_SAMPLE_ID}-DEADBEEF".encode(),
            )
            records[outputs["fwd_bam"]] = bad
            indexed[outputs["fwd_bam"]] = bad

            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "references an unknown RG ID"
            ):
                _run_step06_validator(fixture)

    def test_step06_validator_rejects_cross_side_run_token_leakage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _step06_validator_fixture(Path(directory).resolve())
            outputs = fixture["outputs"]
            headers = fixture["headers"]
            retained_token = fixture["context"]["retained_step06_run_token"]
            headers[outputs["fwd_bam"]] = headers[outputs["fwd_bam"]].replace(
                BENCHMARK.STEP06_TRIAL_RUN_TOKEN.encode(), retained_token.encode()
            )

            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError,
                "exact four Step 06 samtools programs",
            ):
                _run_step06_validator(fixture)

    def test_step06_validator_rejects_decoded_record_reordering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _step06_validator_fixture(Path(directory).resolve())
            outputs = fixture["outputs"]
            records = fixture["records"]
            indexed = fixture["indexed"]
            lines = records[outputs["fwd_bam"]].splitlines(keepends=True)
            records[outputs["fwd_bam"]] = b"".join(reversed(lines))
            indexed[outputs["fwd_bam"]] = records[outputs["fwd_bam"]]

            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "content or order"
            ):
                _run_step06_validator(fixture)

    def test_step06_validator_rejects_indexed_traversal_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _step06_validator_fixture(Path(directory).resolve())
            outputs = fixture["outputs"]
            fixture["indexed"][outputs["rev_bam"]] = b""

            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "indexed traversal"
            ):
                _run_step06_validator(fixture)

    def test_step06_independent_oracle_rejects_shared_bad_flag_membership(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _step06_validator_fixture(Path(directory).resolve())
            outputs = fixture["outputs"]
            retained = fixture["retained"]
            records = fixture["records"]
            indexed = fixture["indexed"]
            for selected in (outputs["fwd_bam"], retained["fwd_bam"]):
                bad = records[selected].replace(b"r99\t99\t", b"r99\t0\t")
                records[selected] = bad
                indexed[selected] = bad

            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "unaccepted flag"
            ):
                _run_step06_validator(fixture)

    def test_step06_independent_oracle_rejects_valid_flag_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _step06_validator_fixture(Path(directory).resolve())
            outputs = fixture["outputs"]
            retained = fixture["retained"]
            records = fixture["records"]
            indexed = fixture["indexed"]
            for selected in (outputs["fwd_bam"], retained["fwd_bam"]):
                valid_record = records[selected].splitlines(keepends=True)[1]
                substituted = valid_record + valid_record
                records[selected] = substituted
                indexed[selected] = substituted

            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "record membership differs"
            ):
                _run_step06_validator(fixture)

    def test_step06_independent_oracle_accepts_optional_tag_reordering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = _step06_validator_fixture(Path(directory).resolve())
            outputs = fixture["outputs"]
            retained = fixture["retained"]
            records = fixture["records"]
            indexed = fixture["indexed"]

            def reverse_optional_fields(data: bytes) -> bytes:
                rendered: list[bytes] = []
                for line in data.splitlines():
                    fields = line.split(b"\t")
                    rendered.append(
                        b"\t".join((*fields[:11], *reversed(fields[11:]))) + b"\n"
                    )
                return b"".join(rendered)

            for selected in (
                outputs["fwd_bam"],
                outputs["rev_bam"],
                retained["fwd_bam"],
                retained["rev_bam"],
            ):
                reordered = reverse_optional_fields(records[selected])
                records[selected] = reordered
                indexed[selected] = reordered

            _run_step06_validator(fixture)

    def test_step06_membership_canonicalization_keeps_tag_values_exact(self) -> None:
        first = b"r1\t99\tchr1\t1\t60\t1M\t=\t1\t0\tA\tI\tRG:Z:s1\tNM:i:0\n"
        reordered = b"r1\t99\tchr1\t1\t60\t1M\t=\t1\t0\tA\tI\tNM:i:0\tRG:Z:s1\n"
        changed = b"r1\t99\tchr1\t1\t60\t1M\t=\t1\t0\tA\tI\tNM:i:1\tRG:Z:s1\n"

        self.assertEqual(
            BENCHMARK._step06_membership_record(first, "first"),
            BENCHMARK._step06_membership_record(reordered, "reordered"),
        )
        self.assertNotEqual(
            BENCHMARK._step06_membership_record(first, "first"),
            BENCHMARK._step06_membership_record(changed, "changed"),
        )

    def test_step06_validator_rejects_counts_or_publication_residue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            fixture = _step06_validator_fixture(root)
            outputs = fixture["outputs"]
            outputs["counts"].write_bytes(
                outputs["counts"].read_bytes().replace(b"\t4\t1\t", b"\t3\t2\t")
            )
            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "counts TSV differs"
            ):
                _run_step06_validator(fixture)

            fixture = _step06_validator_fixture(root / "residue")
            relative = BENCHMARK._step06_paths(BENCHMARK.RETAINED_SAMPLE_ID)
            residue = fixture["trial"] / relative["orientation_root"] / ".residue"
            residue.write_text("stale\n")
            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "publication residue"
            ):
                _run_step06_validator(fixture)

    def test_archive_extractor_rejects_escape_and_links(self) -> None:
        def archive(member: tarfile.TarInfo, data: bytes = b"") -> bytes:
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode="w") as output:
                member.size = len(data)
                output.addfile(member, io.BytesIO(data))
            return stream.getvalue()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            safe = tarfile.TarInfo("src/example.py")
            BENCHMARK._safe_extract_archive(archive(safe, b"pass\n"), root / "safe")
            self.assertEqual((root / "safe/src/example.py").read_bytes(), b"pass\n")
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "unsafe member"):
                BENCHMARK._safe_extract_archive(
                    archive(tarfile.TarInfo("../escape"), b"bad"), root / "escape"
                )
            link = tarfile.TarInfo("link")
            link.type = tarfile.SYMTYPE
            link.linkname = "target"
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "unsafe member"):
                BENCHMARK._safe_extract_archive(archive(link), root / "link-root")

    def test_repository_guard_is_clean_ancestral_and_lock_exact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            python = root / ".venv/bin/python"
            python.parent.mkdir(parents=True)
            python.write_text("#!/bin/sh\nexit 0\n")
            python.chmod(0o755)
            baseline = "1" * 40
            head = "2" * 40
            calls: list[tuple[str, ...]] = []

            def git(_root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
                calls.append(tuple(arguments))
                if arguments[0] == "status":
                    return subprocess.CompletedProcess(arguments, 0, b"", b"")
                if arguments[0] == "rev-parse":
                    value = baseline if arguments[1].startswith("origin/master") else head
                    return subprocess.CompletedProcess(arguments, 0, f"{value}\n".encode(), b"")
                if arguments[0] == "merge-base":
                    return subprocess.CompletedProcess(arguments, 0, b"", b"")
                if arguments[0] == "show":
                    return subprocess.CompletedProcess(arguments, 0, b"same-lock\n", b"")
                raise AssertionError(arguments)

            with mock.patch.object(BENCHMARK, "_git", side_effect=git):
                admitted = BENCHMARK._admit_repository(root)

            self.assertEqual(admitted.baseline_commit, baseline)
            self.assertEqual(admitted.head_commit, head)
            self.assertIn(
                ("status", "--porcelain=v1", "--untracked-files=all"), calls
            )
            show_paths = {call[1].split(":", 1)[1] for call in calls if call[0] == "show"}
            self.assertEqual(
                show_paths,
                {
                    "uv.lock",
                    "renv.lock",
                    ".github/ci/real-tools.conda-lock.yml",
                },
            )

    def test_comparison_summary_requires_exact_complete_four_case_roster(self) -> None:
        manifest = BENCHMARK._manifest(
            Path("/locked/python"),
            Path("/repo/tests/tools/retained_stage_benchmark.py"),
            Path("/external/context.json"),
        )

        def rows() -> list[dict[str, str]]:
            selected = []
            for case in manifest["cases"]:
                for value in case["values"]:
                    for variant in case["variants"]:
                        row = {field: "1" for field in BENCHMARK.COMPARISON_SUMMARY_FIELDS}
                        row.update(
                            {
                                "case": str(case["name"]),
                                "value": str(value),
                                "baseline_variant": str(case["baseline_variant"]),
                                "variant": str(variant["name"]),
                                "required_repetitions": str(case["repetitions"]),
                                "successful_repetitions": str(case["repetitions"]),
                                "paired_repetitions": str(case["repetitions"]),
                                "warmups_valid": "yes",
                                "comparison_valid": "yes",
                                "artifact_parity": "yes",
                            }
                        )
                        selected.append(row)
            return selected

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "summary.tsv"

            def publish(selected: list[dict[str, str]]) -> None:
                with path.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(
                        stream,
                        fieldnames=BENCHMARK.COMPARISON_SUMMARY_FIELDS,
                        dialect="excel-tab",
                    )
                    writer.writeheader()
                    writer.writerows(selected)

            complete_rows = rows()
            publish(complete_rows)
            self.assertEqual(
                BENCHMARK._comparison_summary_complete(path, manifest),
                (True, "complete"),
            )
            publish(complete_rows[:-1])
            valid, detail = BENCHMARK._comparison_summary_complete(path, manifest)
            self.assertFalse(valid)
            self.assertIn("roster", detail)

            selected_manifest = BENCHMARK._manifest(
                Path("/locked/python"),
                Path("/repo/tests/tools/retained_stage_benchmark.py"),
                Path("/external/context.json"),
                (BENCHMARK.RETAINED_CASES[-1],),
            )
            publish(rows())
            valid, detail = BENCHMARK._comparison_summary_complete(
                path, selected_manifest
            )
            self.assertFalse(valid)
            self.assertIn("roster", detail)

    def test_phase_resources_require_exact_roster_and_producer_metrics(self) -> None:
        selected = (BENCHMARK.RETAINED_CASE_BY_NAME["step08-uniform"],)
        manifest = BENCHMARK._manifest(
            Path("/locked/python"),
            Path("/repo/tests/tools/retained_stage_benchmark.py"),
            Path("/external/context.json"),
            selected,
        )
        with tempfile.TemporaryDirectory() as directory:
            results = Path(directory).resolve() / "results"
            results.mkdir()
            trials_path = results / "trials.tsv"
            phase_path = results / "phase-resources.tsv"
            trial_rows: list[dict[str, str]] = []
            phase_rows: list[dict[str, str]] = []
            for case in manifest["cases"]:
                for value in case["values"]:
                    for trial_kind, count, root_name in (
                        ("warmup", case["warmup_repetitions"], "warmups"),
                        ("measured", case["repetitions"], "trials"),
                    ):
                        for repetition in range(1, count + 1):
                            for variant in case["variants"]:
                                trial = (
                                    results
                                    / root_name
                                    / case["name"]
                                    / str(value)
                                    / f"rep-{repetition:02d}"
                                    / variant["name"]
                                )
                                identity = {
                                    "case": str(case["name"]),
                                    "value": str(value),
                                    "variant": str(variant["name"]),
                                    "trial_kind": trial_kind,
                                    "repetition": str(repetition),
                                }
                                trial_rows.append(
                                    {
                                        **identity,
                                        "status": "pass",
                                        "setup_exit_code": "0",
                                        "producer_exit_code": "0",
                                        "validator_exit_code": "0",
                                        "producer_wall_seconds": "1.000000",
                                        "producer_cpu_seconds": "0.500000",
                                        "producer_max_rss_kib": "100",
                                        "producer_input_blocks": "2",
                                        "producer_output_blocks": "3",
                                        "artifact_set_sha256": "a" * 64,
                                        "artifact_match_baseline": "yes",
                                        "trial_dir": str(trial),
                                    }
                                )
                                for phase in BENCHMARK.PHASES:
                                    phase_rows.append(
                                        {
                                            "schema_version": BENCHMARK.PHASE_RESOURCE_SCHEMA,
                                            **identity,
                                            "phase": phase,
                                            "state": "passed",
                                            "exit_code": "0",
                                            "wall_seconds": "1.000000",
                                            "cpu_seconds": "0.500000",
                                            "max_rss_kib": "100",
                                            "input_blocks": "2",
                                            "output_blocks": "3",
                                            "trial_dir": str(trial),
                                        }
                                    )

            def publish(
                path: Path,
                fields: tuple[str, ...],
                rows: list[dict[str, str]],
            ) -> None:
                with path.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(
                        stream, fieldnames=fields, dialect="excel-tab"
                    )
                    writer.writeheader()
                    writer.writerows(rows)

            publish(trials_path, BENCHMARK.COMPARISON_TRIAL_FIELDS, trial_rows)
            publish(phase_path, BENCHMARK.PHASE_RESOURCE_FIELDS, phase_rows)
            self.assertEqual(
                BENCHMARK._phase_resources_complete(
                    phase_path, trials_path, manifest
                ),
                (True, "complete"),
            )

            producer = next(row for row in phase_rows if row["phase"] == "producer")
            producer["wall_seconds"] = "2.000000"
            publish(phase_path, BENCHMARK.PHASE_RESOURCE_FIELDS, phase_rows)
            valid, detail = BENCHMARK._phase_resources_complete(
                phase_path, trials_path, manifest
            )
            self.assertFalse(valid)
            self.assertIn("differ", detail)

    def test_output_root_must_be_external_to_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory).resolve() / "repo"
            repo.mkdir()
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "outside"):
                BENCHMARK._require_external_output(repo / "results/benchmark", repo)
            BENCHMARK._require_external_output(repo.parent / "benchmark", repo)

    def test_execute_context_records_the_exact_retained_primary_vcf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repo_root = root / "repo"
            repo_root.mkdir()
            summary = root / "e2e-summary.json"
            summary.write_text("{}\n")
            primary_vcf = root / "retained.primary.FWD_like.mpileup.vcf"
            primary_vcf.write_text("##fileformat=VCFv4.2\n")
            step01_bam = root / "retained.step01.bam"
            step01_bam.write_bytes(b"bam")
            step02_bam = root / "retained.step02.bam"
            step02_bai = root / "retained.step02.bam.bai"
            step02_bam.hardlink_to(step01_bam)
            step02_bai.write_bytes(b"bai")
            step04_bam = root / "retained.step04.bam"
            step04_bai = root / "retained.step04.bam.bai"
            step04_metrics = root / "retained.step04.metrics.txt"
            picard_jar = root / "picard.jar"
            for selected in (step04_bam, step04_bai, step04_metrics, picard_jar):
                selected.write_bytes(selected.name.encode())
            reference_fasta = root / "reference.fa"
            reference_fai = Path(f"{reference_fasta}.fai")
            reference_dict = root / "reference.dict"
            for selected in (reference_fasta, reference_fai, reference_dict):
                selected.write_bytes(selected.name.encode())
            step05_bam = root / "retained.step05.bam"
            step05_bai = root / "retained.step05.bam.bai"
            step05_bam.write_bytes(b"step05-bam")
            step05_bai.write_bytes(b"step05-bai")
            step06_fwd_bam = root / "retained.step06.fwd.bam"
            step06_fwd_bai = root / "retained.step06.fwd.bam.bai"
            step06_rev_bam = root / "retained.step06.rev.bam"
            step06_rev_bai = root / "retained.step06.rev.bam.bai"
            step06_counts = root / "retained.step06.counts.tsv"
            for selected in (
                step06_fwd_bam,
                step06_fwd_bai,
                step06_rev_bam,
                step06_rev_bai,
                step06_counts,
            ):
                selected.write_bytes(selected.name.encode())
            runtime = root / "runtime"
            runtime_bash = runtime / "bin/bash"
            runtime_gatk = runtime / "bin/gatk"
            runtime_java = runtime / "bin/java"
            runtime_samtools = runtime / "bin/samtools"
            for executable in (runtime_bash, runtime_gatk, runtime_java, runtime_samtools):
                executable.parent.mkdir(parents=True, exist_ok=True)
                executable.write_text("#!/bin/sh\n")
                executable.chmod(0o755)
            retained = BENCHMARK.AdmittedE2E(
                summary,
                hashlib.sha256(summary.read_bytes()).hexdigest(),
                root / "run",
                "cohort",
                root / "samples.tsv",
                root / "reference.fa",
                root / "genes.gtf",
                root / "orientation",
                primary_vcf,
                BENCHMARK.RETAINED_SAMPLE_ID,
                _retained_artifact(step01_bam),
                _retained_artifact(step02_bam),
                _retained_artifact(step02_bai),
                _retained_artifact(step04_bam),
                _retained_artifact(step04_bai),
                _retained_artifact(step04_metrics),
                "owner-" + "4" * 32,
                _retained_artifact(picard_jar),
                _retained_artifact(reference_fasta),
                _retained_artifact(reference_fai),
                _retained_artifact(reference_dict),
                _retained_artifact(step05_bam),
                _retained_artifact(step05_bai),
                "owner-" + "5" * 32,
                _retained_artifact(step06_fwd_bam),
                _retained_artifact(step06_fwd_bai),
                _retained_artifact(step06_rev_bam),
                _retained_artifact(step06_rev_bai),
                _retained_artifact(step06_counts),
                "owner-" + "6" * 32,
                2,
                runtime_bash,
                runtime_gatk,
                runtime_java,
                picard_jar,
                runtime_samtools,
                Path(sys.executable),
            )
            repository = BENCHMARK.RepositoryState(
                repo_root,
                Path(sys.executable),
                "1" * 40,
                "2" * 40,
            )
            output = root / "benchmark"

            def extract(_data: bytes, destination: Path) -> None:
                destination.mkdir(parents=True)

            def run(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
                results = Path(argv[argv.index("--output") + 1])
                results.mkdir()
                (results / "summary.tsv").write_text("summary\n")
                (results / "trials.tsv").write_text("trials\n")
                (results / "phase-resources.tsv").write_text("phases\n")
                return subprocess.CompletedProcess(argv, 0, b"", b"")

            with (
                mock.patch.object(
                    BENCHMARK,
                    "_git",
                    return_value=subprocess.CompletedProcess([], 0, b"archive", b""),
                ),
                mock.patch.object(BENCHMARK, "_safe_extract_archive", side_effect=extract),
                mock.patch.object(BENCHMARK, "_comparison_summary_complete", return_value=(True, "complete")),
                mock.patch.object(
                    BENCHMARK,
                    "_phase_resources_complete",
                    return_value=(True, "complete"),
                ),
                mock.patch.object(BENCHMARK.subprocess, "run", side_effect=run),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(
                    BENCHMARK._execute(
                        repository,
                        retained,
                        output,
                        runtime,
                        root / "Rscript",
                        root / "renv",
                        (BENCHMARK.RETAINED_CASES[-1],),
                        None,
                    ),
                    0,
                )

            context = json.loads((output / "benchmark-context.json").read_text())
            self.assertEqual(context["retained_primary_vcf"], str(primary_vcf))
            self.assertEqual(
                context["retained_step01_bam"]["path"], str(step01_bam)
            )
            self.assertEqual(
                context["retained_step02_bam"]["path"], str(step02_bam)
            )
            self.assertEqual(
                context["retained_step02_bai"]["path"], str(step02_bai)
            )
            self.assertEqual(context["retained_step04_bam"]["path"], str(step04_bam))
            self.assertEqual(context["retained_picard_jar"]["path"], str(picard_jar))
            self.assertEqual(context["retained_reference_dict"]["path"], str(reference_dict))
            self.assertEqual(
                context["retained_step05_bam"]["path"], str(step05_bam)
            )
            self.assertEqual(
                context["retained_step06_fwd_bam"]["path"], str(step06_fwd_bam)
            )
            self.assertEqual(
                context["retained_step06_counts"]["path"], str(step06_counts)
            )
            self.assertEqual(
                context["retained_step06_run_token"], "owner-" + "6" * 32
            )
            self.assertEqual(context["runtime_bash"], str(runtime_bash))
            self.assertEqual(context["runtime_gatk"], str(runtime_gatk))
            self.assertEqual(context["runtime_java"], str(runtime_java))
            self.assertEqual(context["runtime_samtools"], str(runtime_samtools))
            self.assertEqual(context["runtime_sha256_python"], sys.executable)
            self.assertNotIn("retained_step07_root", context)
            summary_document = json.loads(
                (output / "retained-stage-benchmark-summary.json").read_text()
            )
            self.assertEqual(summary_document["schema_version"], BENCHMARK.SUMMARY_SCHEMA)
            self.assertEqual(
                summary_document["selection"],
                {"suite": None, "cases": {"step08-uniform": [100_000]}},
            )
            self.assertEqual(
                summary_document["phase_resource_completeness"], "complete"
            )
            self.assertIsNotNone(summary_document["comparison_trials"])
            self.assertIsNotNone(summary_document["phase_resources"])

    def test_admit_e2e_requires_the_exact_retained_100k_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            operator = Path(directory).resolve() / "operator"
            run = operator / "workspace/runs/run-test"
            (run / "contract").mkdir(parents=True)
            (run / "results/orientation").mkdir(parents=True)
            (run / "results/mpileup").mkdir()
            inputs = operator / "synthetic-inputs"
            (inputs / "inputs/reference").mkdir(parents=True)
            samples = inputs / "samples.tsv"
            partitions = inputs / "partitions.tsv"
            fasta = inputs / "inputs/reference/reference.fa"
            gtf = inputs / "inputs/reference/genes.gtf"
            samples.write_text(
                f"sample_id\tx\n{BENCHMARK.RETAINED_SAMPLE_ID}\t1\n"
            )
            partitions.write_text("partition_id\tselector_type\tselector_value\nprimary\tregion\ts\n")
            fasta.write_text(">s\nA\n")
            Path(f"{fasta}.fai").write_text("s\t5000000\t0\t1\t2\n")
            reference_dict = fasta.with_name(f"{fasta.stem}.dict")
            reference_dict.write_text("@HD\tVN:1.6\n@SQ\tSN:s\tLN:5000000\n")
            gtf.write_text("s\tx\tgene\t1\t1\t.\t+\t.\tgene_id \"g\";\n")
            execution = {
                "analysis": {"cohort_id": "cohort"},
                "samples": {"manifest": {"path": str(samples)}},
                "partitions": {
                    "manifest": {"path": str(partitions)},
                    "rows": [{"partition_id": "primary", "selector_type": "region", "selector_value": "s"}],
                },
                "reference": {"fasta": {"path": str(fasta)}, "gtf": {"path": str(gtf)}},
            }
            (run / "contract/normalized.json").write_text(json.dumps(execution))
            evidence = operator / "evidence"
            evidence.mkdir()
            step01_bam = (
                run
                / "results/star"
                / BENCHMARK.RETAINED_SAMPLE_ID
                / f"{BENCHMARK.RETAINED_SAMPLE_ID}.Aligned.sortedByCoord.out.bam"
            )
            step01_bam.parent.mkdir(parents=True)
            step01_bam.write_bytes(b"retained-step01-bam")
            step02_bam = (
                run
                / "results/bam"
                / BENCHMARK.RETAINED_SAMPLE_ID
                / f"{BENCHMARK.RETAINED_SAMPLE_ID}.sorted.bam"
            )
            step02_bam.parent.mkdir(parents=True)
            step02_bam.hardlink_to(step01_bam)
            step02_bai = Path(f"{step02_bam}.bai")
            step02_bai.write_bytes(b"retained-step02-bai")
            picard_jar = operator / "runtime/share/picard.jar"
            picard_jar.parent.mkdir(parents=True)
            picard_jar.write_bytes(b"retained-picard-jar")
            step04_bam = (
                run / "results/markdup" / BENCHMARK.RETAINED_SAMPLE_ID
                / f"{BENCHMARK.RETAINED_SAMPLE_ID}.markdup.bam"
            )
            step04_bam.parent.mkdir(parents=True)
            step04_bam.write_bytes(b"retained-step04-bam")
            step04_bai = Path(f"{step04_bam}.bai")
            step04_bai.write_bytes(b"retained-step04-bai")
            step04_metrics = (
                run / "results/qc/markdup"
                / f"{BENCHMARK.RETAINED_SAMPLE_ID}.markdup.metrics.txt"
            )
            step04_metrics.parent.mkdir(parents=True)
            step04_metrics.write_bytes(b"retained-step04-metrics")
            step05_bam = (
                run
                / "results/split_ncigar"
                / BENCHMARK.RETAINED_SAMPLE_ID
                / f"{BENCHMARK.RETAINED_SAMPLE_ID}.split_ncigar.bam"
            )
            step05_bam.parent.mkdir(parents=True)
            step05_bam.write_bytes(b"retained-step05-bam")
            step05_bai = Path(f"{step05_bam}.bai")
            step05_bai.write_bytes(b"retained-step05-bai")
            step06_fwd_bam = (
                run
                / "results/orientation"
                / BENCHMARK.RETAINED_SAMPLE_ID
                / f"{BENCHMARK.RETAINED_SAMPLE_ID}.FWD_like.bam"
            )
            step06_fwd_bam.parent.mkdir(parents=True)
            step06_fwd_bam.write_bytes(b"retained-step06-fwd-bam")
            step06_fwd_bai = Path(f"{step06_fwd_bam}.bai")
            step06_fwd_bai.write_bytes(b"retained-step06-fwd-bai")
            step06_rev_bam = step06_fwd_bam.with_name(
                f"{BENCHMARK.RETAINED_SAMPLE_ID}.REV_like.bam"
            )
            step06_rev_bam.write_bytes(b"retained-step06-rev-bam")
            step06_rev_bai = Path(f"{step06_rev_bam}.bai")
            step06_rev_bai.write_bytes(b"retained-step06-rev-bai")
            step06_counts = (
                run
                / "results/qc/orientation"
                / f"{BENCHMARK.RETAINED_SAMPLE_ID}.orientation_counts.tsv"
            )
            step06_counts.parent.mkdir(parents=True)
            step06_counts.write_bytes(b"retained-step06-counts")
            step01_log = run / "logs/steps/01/control_pair_01.log"
            step01_log.parent.mkdir(parents=True)
            step01_log.write_bytes(b"retained-step01-log")
            step01_outputs = [
                {"role": "output_001", **_artifact(step01_bam)},
                {"role": "output_002", **_artifact(step01_log)},
            ]
            step02_outputs = [
                {"role": "output_001", **_artifact(step02_bam)},
                {"role": "output_002", **_artifact(step02_bai)},
            ]
            step04_inputs = [
                {"role": "input_001", **_artifact(step02_bam)},
                {"role": "input_002", **_artifact(step02_bai)},
                {"role": "input_003", **_artifact(picard_jar)},
            ]
            step04_outputs = [
                {"role": "output_001", **_artifact(step04_bam)},
                {"role": "output_002", **_artifact(step04_bai)},
                {"role": "output_003", **_artifact(step04_metrics)},
            ]
            step05_outputs = [
                {"role": "output_001", **_artifact(step05_bam)},
                {"role": "output_002", **_artifact(step05_bai)},
            ]
            step05_inputs = [
                {"role": "input_001", **_artifact(step04_bam)},
                {"role": "input_002", **_artifact(step04_bai)},
                {"role": "input_003", **_artifact(fasta)},
                {"role": "input_004", **_artifact(Path(f"{fasta}.fai"))},
                {"role": "input_005", **_artifact(reference_dict)},
            ]
            step06_outputs = [
                {"role": "output_001", **_artifact(step06_fwd_bam)},
                {"role": "output_002", **_artifact(step06_fwd_bai)},
                {"role": "output_003", **_artifact(step06_rev_bam)},
                {"role": "output_004", **_artifact(step06_rev_bai)},
                {"role": "output_005", **_artifact(step06_counts)},
            ]
            owners = []
            for index in range(35):
                path = evidence / f"owner-{index}.json"
                if index == 0:
                    owners.append(
                        _publish_verified_owner(
                            path, BENCHMARK.STEP01_OWNER, step01_outputs
                        )
                    )
                elif index == 1:
                    owners.append(
                        _publish_verified_owner(
                            path, BENCHMARK.STEP02_OWNER, step02_outputs
                        )
                    )
                elif index == 2:
                    owners.append(
                        _publish_verified_owner(
                            path, BENCHMARK.STEP04_OWNER, step04_outputs,
                            inputs=step04_inputs,
                        )
                    )
                elif index == 3:
                    owners.append({})
                elif index == 4:
                    owners.append(
                        _publish_verified_owner(
                            path, BENCHMARK.STEP06_OWNER, step06_outputs
                        )
                    )
                else:
                    path.write_text(str(index))
                    owners.append(_artifact(path))
            final = evidence / "attempt.json"
            final.write_text("complete")
            runtime_bash = operator / "runtime/bin/bash"
            runtime_gatk = operator / "runtime/bin/gatk"
            gatk_delegate = operator / "runtime/bin/gatk-delegate"
            gatk_runtime_python = operator / "runtime/bin/gatk-python"
            runtime_java = operator / "runtime/bin/java"
            runtime_samtools = operator / "runtime/bin/samtools"
            for executable in (
                runtime_bash, runtime_gatk, gatk_delegate, gatk_runtime_python,
                runtime_java, runtime_samtools,
            ):
                executable.parent.mkdir(parents=True, exist_ok=True)
                executable.write_text("#!/bin/sh\n")
                executable.chmod(0o755)
            runtime_profile = operator / "runtime.selected.tsv"
            runtime_profile.write_text(
                "check_id\tcheck_type\truntime_context\trequired\ttarget\t"
                "probe_args\texpected\tdescription\n"
                f"bash\ttool_version\tlocal\ttrue\t{runtime_bash}\t[]\tbash\tBash\n"
                f"samtools\ttool_version\tlocal\ttrue\t{runtime_samtools}\t[]\t"
                "samtools\tsamtools\n"
                f"sha256_python\thash_utility\tlocal\ttrue\t{sys.executable}\t[]\t"
                "sha256\tPython\n"
                f"java\ttool_version\tlocal\ttrue\t{runtime_java}\t[]\tjava\tJava\n"
                f"gatk\ttool_version\tlocal\ttrue\t{runtime_gatk}\t"
                "[\"--version\"]\tgatk\tGATK\n"
                f"picard\ttool_version_exit_1\tlocal\ttrue\t{runtime_java}\t"
                f"[\"-jar\",\"{picard_jar}\",\"MarkDuplicates\",\"--version\"]\t"
                "picard\tPicard\n"
                f"picard_jar\tpath_visibility\tlocal\ttrue\t{picard_jar}\t[]\t"
                "readable\tPicard jar\n"
            )
            step05_owner = operator / "checkout/src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh"
            step05_owner.parent.mkdir(parents=True)
            step05_owner.write_text("#!/bin/bash\n")
            step05_producer_argv = [
                str(runtime_bash), "-c", BENCHMARK.OWNER_ENVIRONMENT_BOOTSTRAP,
                "emrys-owner", "owner-" + "6" * 32, sys.executable,
                str(runtime_bash), str(step05_owner),
                "--sample-id", BENCHMARK.RETAINED_SAMPLE_ID,
                "--input-bam", str(step04_bam), "--reference-fasta", str(fasta),
                "--output-dir", str(step05_bam.parent), "--gatk-bin", str(runtime_gatk),
                "--samtools-bin", str(runtime_samtools), "--java-bin", str(runtime_java),
                "--no-clobber", "--execute",
            ]
            owners[3] = _publish_verified_owner(
                evidence / "owner-3.json",
                BENCHMARK.STEP05_OWNER,
                step05_outputs,
                inputs=step05_inputs,
                producer_argv=step05_producer_argv,
            )
            primary_vcf = run / "results/mpileup/cohort/primary/cohort.primary.FWD_like.mpileup.vcf"
            primary_vcf.parent.mkdir(parents=True)
            primary_vcf.write_text("##fileformat=VCFv4.2\n")
            summary = {
                "schema_version": BENCHMARK.E2E_SCHEMA,
                "status": "passed",
                "profile": "100000",
                "dataset_profile": "production-like-v1",
                "fixture_id": "deterministic-production-like-v1",
                "read_pairs_per_library": 100_000,
                "biological_interpretation_claimed": False,
                "operator_root": str(operator),
                "runtime_profile": _artifact(runtime_profile),
                "gatk_attestation": {
                    "adapter": _artifact(runtime_gatk),
                    "delegate": _artifact(gatk_delegate),
                    "java_home": str(runtime_java.parent.parent),
                    "runtime_java": _artifact(runtime_java),
                    "runtime_python": _artifact(gatk_runtime_python),
                    "runtime_python_launcher": str(gatk_runtime_python),
                    "version_output": "The Genome Analysis Toolkit (GATK) v4.6.1.0",
                },
                "completion": {
                    "state": "local_pipeline_complete",
                    "run_id": "run-test",
                    "run_root": str(run),
                    "verified_owner_jobs": 35,
                    "verified_owner_records": owners,
                    "step10_verified": True,
                    "artifacts": {"attempt": _artifact(final)},
                },
            }
            summary_path = operator / "e2e-summary.json"
            summary_path.write_text(json.dumps(summary))

            admitted = BENCHMARK._admit_e2e(summary_path)

            self.assertEqual(admitted.run_root, run)
            self.assertEqual(admitted.cohort_id, "cohort")
            self.assertEqual(admitted.retained_primary_vcf, primary_vcf)
            self.assertEqual(admitted.retained_step01_bam.path, step01_bam)
            self.assertEqual(admitted.retained_step02_bam.path, step02_bam)
            self.assertEqual(admitted.retained_step02_bai.path, step02_bai)
            self.assertEqual(admitted.retained_step04_bam.path, step04_bam)
            self.assertEqual(admitted.retained_step04_metrics.path, step04_metrics)
            self.assertEqual(admitted.retained_picard_jar.path, picard_jar)
            self.assertEqual(admitted.retained_step05_bam.path, step05_bam)
            self.assertEqual(admitted.retained_step05_bai.path, step05_bai)
            self.assertEqual(admitted.retained_reference_dict.path, reference_dict)
            self.assertEqual(admitted.retained_step05_run_token, "owner-" + "6" * 32)
            self.assertEqual(admitted.retained_step06_fwd_bam.path, step06_fwd_bam)
            self.assertEqual(admitted.retained_step06_rev_bam.path, step06_rev_bam)
            self.assertEqual(admitted.retained_step06_counts.path, step06_counts)
            self.assertEqual(
                admitted.retained_step06_run_token, "owner-" + "6" * 32
            )
            self.assertEqual(admitted.retained_step06_threads, 2)
            self.assertEqual(admitted.runtime_bash, runtime_bash)
            self.assertEqual(admitted.runtime_gatk, runtime_gatk)
            self.assertEqual(admitted.runtime_java, runtime_java)
            self.assertEqual(admitted.runtime_samtools, runtime_samtools)
            self.assertEqual(admitted.runtime_sha256_python, Path(sys.executable))

            def republish_step05() -> None:
                owners[3] = _publish_verified_owner(
                    evidence / "owner-3.json", BENCHMARK.STEP05_OWNER,
                    step05_outputs, inputs=step05_inputs,
                    producer_argv=step05_producer_argv,
                )
                summary_path.write_text(json.dumps(summary))

            step05_inputs[4]["role"] = "wrong-role"
            republish_step05()
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "binding differs"):
                BENCHMARK._admit_e2e(summary_path)
            step05_inputs[4]["role"] = "input_005"
            extra_step05 = step05_bai.with_name("unexpected-step05-output")
            extra_step05.write_text("unexpected\n")
            step05_outputs.append({"role": "output_003", **_artifact(extra_step05)})
            republish_step05()
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "exact expected roster"):
                BENCHMARK._admit_e2e(summary_path)
            step05_outputs.pop()
            step05_producer_argv[-2:] = ["--execute", "--no-clobber"]
            republish_step05()
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "producer argv differs"):
                BENCHMARK._admit_e2e(summary_path)
            step05_producer_argv[-2:] = ["--no-clobber", "--execute"]
            republish_step05()
            runtime_text = runtime_profile.read_text()
            runtime_profile.write_text(
                runtime_text.replace('["--version"]\tgatk\tGATK', '["version"]\tgatk\tGATK')
            )
            summary["runtime_profile"] = _artifact(runtime_profile)
            summary_path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "GATK authority probe"):
                BENCHMARK._admit_e2e(summary_path)
            runtime_profile.write_text(runtime_text)
            summary["runtime_profile"] = _artifact(runtime_profile)
            summary_path.write_text(json.dumps(summary))
            replacement_adapter = runtime_gatk.with_name("replacement-gatk")
            replacement_adapter.write_text("#!/bin/sh\n")
            replacement_adapter.chmod(0o755)
            runtime_profile.write_text(
                runtime_text.replace(str(runtime_gatk), str(replacement_adapter))
            )
            summary["runtime_profile"] = _artifact(runtime_profile)
            summary_path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "adapter differs"):
                BENCHMARK._admit_e2e(summary_path)
            runtime_profile.write_text(runtime_text)
            summary["runtime_profile"] = _artifact(runtime_profile)
            summary["profile"] = "130"
            summary_path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "exact passed retained 100k"):
                BENCHMARK._admit_e2e(summary_path)
            summary["profile"] = "100000"
            summary_path.write_text(json.dumps(summary))
            step02_outputs[0]["role"] = "wrong-role"
            owners[1] = _publish_verified_owner(
                evidence / "owner-1.json", BENCHMARK.STEP02_OWNER, step02_outputs
            )
            summary_path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "binding differs"
            ):
                BENCHMARK._admit_e2e(summary_path)
            step02_outputs[0]["role"] = "output_001"
            owners[1] = _publish_verified_owner(
                evidence / "owner-1.json", BENCHMARK.STEP02_OWNER, step02_outputs
            )
            summary_path.write_text(json.dumps(summary))
            step04_inputs[2]["role"] = "wrong-role"
            owners[2] = _publish_verified_owner(
                evidence / "owner-2.json", BENCHMARK.STEP04_OWNER, step04_outputs,
                inputs=step04_inputs,
            )
            summary_path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(BENCHMARK.BenchmarkSetupError, "binding differs"):
                BENCHMARK._admit_e2e(summary_path)
            step04_inputs[2]["role"] = "input_003"
            owners[2] = _publish_verified_owner(
                evidence / "owner-2.json", BENCHMARK.STEP04_OWNER, step04_outputs,
                inputs=step04_inputs,
            )
            summary_path.write_text(json.dumps(summary))
            step06_outputs[4]["role"] = "wrong-role"
            owners[4] = _publish_verified_owner(
                evidence / "owner-4.json", BENCHMARK.STEP06_OWNER, step06_outputs
            )
            summary_path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "binding differs"
            ):
                BENCHMARK._admit_e2e(summary_path)
            step06_outputs[4]["role"] = "output_005"
            owners[4] = _publish_verified_owner(
                evidence / "owner-4.json", BENCHMARK.STEP06_OWNER, step06_outputs
            )
            summary_path.write_text(json.dumps(summary))
            extra_step06 = step06_counts.with_name("unexpected-step06-output")
            extra_step06.write_text("unexpected\n")
            step06_outputs.append(
                {"role": "output_006", **_artifact(extra_step06)}
            )
            owners[4] = _publish_verified_owner(
                evidence / "owner-4.json", BENCHMARK.STEP06_OWNER, step06_outputs
            )
            summary_path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "exact expected roster"
            ):
                BENCHMARK._admit_e2e(summary_path)
            step06_outputs.pop()
            owners[4] = _publish_verified_owner(
                evidence / "owner-4.json", BENCHMARK.STEP06_OWNER, step06_outputs
            )
            summary_path.write_text(json.dumps(summary))
            step01_bam.write_bytes(b"changed")
            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "Step 01 BAM.*retained identity"
            ):
                BENCHMARK._admit_e2e(summary_path)

    def test_dry_run_default_does_not_create_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repo = root / "repo"
            repo.mkdir()
            runtime = root / "runtime"
            renv = root / "renv"
            runtime.mkdir()
            renv.mkdir()
            output = root / "absent-output"
            repository = BENCHMARK.RepositoryState(
                repo,
                Path("/locked/python"),
                "1" * 40,
                "2" * 40,
            )
            evidence = mock.Mock()
            arguments = argparse.Namespace(
                repo_root=repo,
                e2e_summary=root / "e2e-summary.json",
                output_root=output,
                runtime_prefix=runtime,
                rscript=root / "Rscript",
                renv_library=renv,
                suite=None,
                case_names=None,
                execute=False,
            )
            with (
                mock.patch.object(BENCHMARK, "_admit_repository", return_value=repository),
                mock.patch.object(BENCHMARK, "_admit_e2e", return_value=evidence),
                mock.patch.object(BENCHMARK, "_real_directory", side_effect=lambda path, _label: Path(path)),
                mock.patch.object(BENCHMARK, "_real_file", side_effect=lambda path, _label, **_kwargs: Path(path)),
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(BENCHMARK._orchestrate(arguments), 0)
            self.assertFalse(output.exists())

    def test_internal_producer_requires_an_explicit_variant(self) -> None:
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                BENCHMARK._internal_parser(
                    [
                        "_produce", "--context", "/context", "--case", "step08-reread",
                        "--value", "10000", "--trial-dir", "/trial",
                    ]
                )

    def test_internal_parser_rejects_an_unregistered_case_value(self) -> None:
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                BENCHMARK._internal_parser(
                    [
                        "_setup", "--context", "/context", "--case",
                        "step08-reread", "--value", "999", "--trial-dir", "/trial",
                    ]
                )


if __name__ == "__main__":
    unittest.main()
