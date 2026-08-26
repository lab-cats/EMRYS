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
    path: Path, machine_key: str, outputs: list[dict[str, object]]
) -> dict[str, object]:
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
                        "argv": ["owner", "--threads", "4"],
                        "exit_code": 0,
                    }
                },
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
        b"r99\t99\tchrSynthetic\t1\t60\t1M\t=\t1\t0\tA\tI\n"
        b"r147\t147\tchrSynthetic\t2\t60\t1M\t=\t2\t0\tC\tI\n"
        b"r83\t83\tchrSynthetic\t3\t60\t1M\t=\t3\t0\tG\tI\n"
        b"r163\t163\tchrSynthetic\t4\t60\t1M\t=\t4\t0\tT\tI\n"
        b"other\t0\tchrSynthetic\t5\t60\t1M\t*\t0\t0\tA\tI\n"
    )
    fwd_records = b"".join(input_records.splitlines(keepends=True)[:2])
    rev_records = b"".join(input_records.splitlines(keepends=True)[2:4])
    retained_token = "owner-" + "6" * 32

    def header(root_path: Path | None, token: str, orientation: str) -> bytes:
        prefix = f"{root_path}/" if root_path is not None else ""
        return (
            b"@HD\tVN:1.6\tSO:coordinate\n"
            b"@SQ\tSN:chrSynthetic\tLN:5000000\n"
            + (
                f"@PG\tID:samtools\tPN:samtools\tCL:samtools merge "
                f"{prefix}results/orientation/{sample}/.{sample}.step06."
                f"{token}.{orientation}.tmp.bam\n"
            ).encode()
        )

    records = {
        step05_bam: input_records,
        retained_fwd: fwd_records,
        retained_rev: rev_records,
        outputs["fwd_bam"]: fwd_records,
        outputs["rev_bam"]: rev_records,
    }
    headers = {
        retained_fwd: header(run_root, retained_token, "FWD_like"),
        retained_rev: header(run_root, retained_token, "REV_like"),
        outputs["fwd_bam"]: header(
            None, BENCHMARK.STEP06_TRIAL_RUN_TOKEN, "FWD_like"
        ),
        outputs["rev_bam"]: header(
            None, BENCHMARK.STEP06_TRIAL_RUN_TOKEN, "REV_like"
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
        selected = Path(command[3] if command[1:3] == ("view", "-H") else command[2])
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
            (BENCHMARK.RETAINED_CASE_BY_NAME["alignment-signatures-mib"],),
        )
        self.assertEqual(
            BENCHMARK._select_cases(suite="sample-stages", names=None),
            (
                BENCHMARK.RETAINED_CASE_BY_NAME["step02-canonical-bam"],
                BENCHMARK.RETAINED_CASE_BY_NAME["step06-mechanical-orientation"],
            ),
        )
        self.assertEqual(
            BENCHMARK._select_cases(suite="all", names=None),
            BENCHMARK.RETAINED_CASES,
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
                b"PN:samtools", b"PN:foreign-writer"
            )

            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "beyond admitted roots and run tokens"
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
                BENCHMARK.BenchmarkSetupError, "beyond admitted roots and run tokens"
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
            bad = records[outputs["fwd_bam"]].replace(b"r99\t99\t", b"r99\t0\t")
            for selected in (outputs["fwd_bam"], retained["fwd_bam"]):
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
            valid_record = records[outputs["fwd_bam"]].splitlines(keepends=True)[1]
            substituted = valid_record + valid_record
            for selected in (outputs["fwd_bam"], retained["fwd_bam"]):
                records[selected] = substituted
                indexed[selected] = substituted

            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "record membership differs"
            ):
                _run_step06_validator(fixture)

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
            runtime_samtools = runtime / "bin/samtools"
            for executable in (runtime_bash, runtime_samtools):
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
                _retained_artifact(step05_bam),
                _retained_artifact(step05_bai),
                _retained_artifact(step06_fwd_bam),
                _retained_artifact(step06_fwd_bai),
                _retained_artifact(step06_rev_bam),
                _retained_artifact(step06_rev_bai),
                _retained_artifact(step06_counts),
                "owner-" + "6" * 32,
                runtime_bash,
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
            step01_outputs = [{"role": "output_001", **_artifact(step01_bam)}]
            step02_outputs = [
                {"role": "output_001", **_artifact(step02_bam)},
                {"role": "output_002", **_artifact(step02_bai)},
            ]
            step05_outputs = [
                {"role": "output_001", **_artifact(step05_bam)},
                {"role": "output_002", **_artifact(step05_bai)},
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
                            path, BENCHMARK.STEP05_OWNER, step05_outputs
                        )
                    )
                elif index == 3:
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
            runtime_samtools = operator / "runtime/bin/samtools"
            for executable in (runtime_bash, runtime_samtools):
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
            self.assertEqual(admitted.retained_step05_bam.path, step05_bam)
            self.assertEqual(admitted.retained_step05_bai.path, step05_bai)
            self.assertEqual(admitted.retained_step06_fwd_bam.path, step06_fwd_bam)
            self.assertEqual(admitted.retained_step06_rev_bam.path, step06_rev_bam)
            self.assertEqual(admitted.retained_step06_counts.path, step06_counts)
            self.assertEqual(
                admitted.retained_step06_run_token, "owner-" + "6" * 32
            )
            self.assertEqual(admitted.runtime_bash, runtime_bash)
            self.assertEqual(admitted.runtime_samtools, runtime_samtools)
            self.assertEqual(admitted.runtime_sha256_python, Path(sys.executable))
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
            step06_outputs[4]["role"] = "wrong-role"
            owners[3] = _publish_verified_owner(
                evidence / "owner-3.json", BENCHMARK.STEP06_OWNER, step06_outputs
            )
            summary_path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "binding differs"
            ):
                BENCHMARK._admit_e2e(summary_path)
            step06_outputs[4]["role"] = "output_005"
            owners[3] = _publish_verified_owner(
                evidence / "owner-3.json", BENCHMARK.STEP06_OWNER, step06_outputs
            )
            summary_path.write_text(json.dumps(summary))
            extra_step06 = step06_counts.with_name("unexpected-step06-output")
            extra_step06.write_text("unexpected\n")
            step06_outputs.append(
                {"role": "output_006", **_artifact(extra_step06)}
            )
            owners[3] = _publish_verified_owner(
                evidence / "owner-3.json", BENCHMARK.STEP06_OWNER, step06_outputs
            )
            summary_path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(
                BENCHMARK.BenchmarkSetupError, "exact expected roster"
            ):
                BENCHMARK._admit_e2e(summary_path)
            step06_outputs.pop()
            owners[3] = _publish_verified_owner(
                evidence / "owner-3.json", BENCHMARK.STEP06_OWNER, step06_outputs
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
